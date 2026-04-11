"""
api/routes/invoice_routes.py
──────────────────────────────
Invoice API: upload, share, accept/reject/modify, payment tracking.

Key fixes vs original:
  • CurrentUser / SellerUser / BuyerUser are Annotated types with Depends baked in
  • No duplicate Depends() in default values — just use = None
  • /share POST accepts ShareInvoicePayload (buyer_email / buyer_gstin)
  • /buyer/received returns all statuses, not just SHARED
  • /modify POST dedicated endpoint for buyer modification suggestions
  • invoice_analyzer imports from groq_client
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import BuyerUser, SellerUser, CurrentUser
from app.schemas.invoice import (
    BuyerActionRequest,
    InvoiceStatusUpdate,
    MissingInvoiceRequest,
    ModificationSuggestionRequest,
    ModificationSuggestionResponse,
    PaymentRecordRequest,
    UploadResponse,
)
from app.services.invoice_service import (
    ShareInvoicePayload,
    get_invoice_by_id,
    get_invoices_by_seller,
    get_invoices_for_buyer,
    get_invoices_for_buyer_by_gstin,
    process_invoice_upload,
    record_payment,
    request_modification,
    share_invoice_with_buyer,
    update_invoice_status,
)
from app.services.payment_service import get_overdue_invoices, get_payment_summary
from app.agents.validator_agent import ValidatorAgent
from app.graph.graph_queries import create_invoice_relationship, update_invoice_status_in_graph
from app.db.supabase_storage import get_signed_url

router = APIRouter(prefix="/invoices", tags=["Invoices"])


# ── Upload ─────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    file: UploadFile = File(..., description="Invoice PDF or image"),
    current_user: CurrentUser = None,
):
    """
    Seller uploads an invoice PDF/image.

    Pipeline: Save to Supabase Storage → OCR → Groq extraction
              → Server-side GST calculation → Validation → Supabase DB + Neo4j

    NOTE: CurrentUser is Annotated[dict, Depends(get_current_user)] — auth is
          enforced by the dependency itself, not by the = None default.
    """
    ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/tiff", "image/webp"}
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not supported. Use PDF or image.",
        )

    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10 MB limit",
        )

    seller_id: str = current_user["sub"]
    upload_result = await process_invoice_upload(file_bytes, file.filename, seller_id)

    # Write to Neo4j knowledge graph with GST fields
    extracted = upload_result.extracted_data
    gst = upload_result.gst_breakdown

    if extracted.get("seller_gstin") and extracted.get("buyer_gstin"):
        await create_invoice_relationship(
            invoice_id=upload_result.invoice_id,
            invoice_number=extracted.get("invoice_number", "UNKNOWN"),
            invoice_date=extracted.get("invoice_date", ""),
            grand_total=float(extracted.get("grand_total") or 0),
            seller_gstin=extracted["seller_gstin"],
            buyer_gstin=extracted["buyer_gstin"],
            gst_type=gst.gst_type if gst else "inter_state",
            taxable_value=gst.taxable_value if gst else 0.0,
            cgst=gst.total_cgst if gst else 0.0,
            sgst=gst.total_sgst if gst else 0.0,
            igst=gst.total_igst if gst else 0.0,
        )

    return upload_result


# ── Seller: Share Invoice ──────────────────────────────────────

@router.post("/{invoice_id}/share", status_code=status.HTTP_200_OK)
async def share_invoice(
    invoice_id: str,
    payload: ShareInvoicePayload,
    current_user: SellerUser = None,
):
    """
    Seller shares invoice with a buyer.

    Provide buyer_email (preferred) or buyer_gstin in the request body.
    If neither resolves to a registered user, invoice is still shared and
    the buyer can claim it later via their GSTIN.

    Example payload:
        {"buyer_email": "buyer@company.com"}
        {"buyer_gstin": "27ABCDE1234F1Z5"}
    """
    seller_id: str = current_user["sub"]
    updated = await share_invoice_with_buyer(invoice_id, seller_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Invoice not found or not owned by you")
    return {"message": "Invoice shared successfully", "invoice_id": invoice_id}


# ── Buyer: Accept / Reject ─────────────────────────────────────

@router.patch("/{invoice_id}/status", status_code=status.HTTP_200_OK)
async def update_status(
    invoice_id: str,
    payload: InvoiceStatusUpdate,
    current_user: BuyerUser = None,
):
    """
    Buyer updates invoice status: accepted | rejected.
    For modification suggestions, use POST /{invoice_id}/modify instead.
    Ownership enforced: invoice.buyer_id must match JWT sub.

    Example payload:
        {"status": "accepted", "reason": "All details correct"}
        {"status": "rejected", "reason": "Wrong billing address"}
    """
    buyer_id: str = current_user["sub"]
    try:
        updated = await update_invoice_status(invoice_id, buyer_id, payload)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Sync status to Neo4j
    try:
        await update_invoice_status_in_graph(invoice_id, payload.status)
    except Exception as e:
        print(f"⚠️  Neo4j status sync failed for {invoice_id}: {e}")

    return {"message": f"Invoice status updated to '{payload.status}'", "invoice_id": invoice_id}


# ── Buyer: Suggest Modification ───────────────────────────────

@router.post(
    "/{invoice_id}/modify",
    response_model=ModificationSuggestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def suggest_modification(
    invoice_id: str,
    payload: ModificationSuggestionRequest,
    current_user: BuyerUser = None,
):
    """
    Buyer submits field-level modification suggestions.
    Stores to invoice_modifications table and sets invoice status → modified.

    Example payload:
        {"suggested_changes": {"grand_total": 15000}, "reason": "Tax rate mismatch"}
        {"suggested_changes": {"buyer_gstin": "27XXXXX"}, "reason": "Wrong GSTIN used"}
    """
    buyer_id: str = current_user["sub"]
    try:
        result = await request_modification(
            invoice_id=invoice_id,
            buyer_user_id=buyer_id,
            suggested_changes=payload.suggested_changes,
            reason=payload.reason,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Sync status to Neo4j
    try:
        await update_invoice_status_in_graph(invoice_id, "modified")
    except Exception as e:
        print(f"⚠️  Neo4j status sync failed for {invoice_id}: {e}")

    return ModificationSuggestionResponse(
        modification_id=result["id"],
        invoice_id=invoice_id,
        status="pending",
        message="Modification suggestion submitted. Seller will be notified.",
    )


# ── Validation ─────────────────────────────────────────────────

@router.post("/{invoice_id}/validate")
async def validate_invoice(
    invoice_id: str,
    current_user: CurrentUser = None,
):
    """Re-run the validator agent on an existing invoice."""
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    agent = ValidatorAgent()
    report = await agent.run(invoice_id, invoice.get("ai_extracted_data") or {})
    return report


# ── List Invoices ─────────────────────────────────────────────

@router.get("/seller/my-invoices")
async def list_seller_invoices(current_user: SellerUser = None):
    """Seller lists all their uploaded invoices."""
    return await get_invoices_by_seller(current_user["sub"])


@router.get("/buyer/received")
async def list_buyer_invoices(current_user: BuyerUser = None):
    """
    Buyer lists all invoices shared with them (all statuses).
    GSTIN is derived from the JWT (via user_metadata.gstin) — not a query param.
    Falls back to buyer_id match if GSTIN is not in token metadata.
    """
    buyer_id: str = current_user["sub"]
    gstin: str = current_user.get("user_metadata", {}).get("gstin", "")

    if gstin:
        invoices = await get_invoices_for_buyer_by_gstin(gstin)
        if invoices:
            return invoices

    return await get_invoices_for_buyer(buyer_id)


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    current_user: CurrentUser = None,
):
    """Get a single invoice by ID."""
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/{invoice_id}/download-url")
async def get_invoice_download_url(
    invoice_id: str,
    current_user: CurrentUser = None,
):
    """
    Generate a signed URL (1-hour TTL) for downloading the invoice file
    from Supabase Storage.
    """
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    storage_path = invoice.get("file_url")
    if not storage_path:
        raise HTTPException(status_code=404, detail="No file attached to this invoice")

    signed_url = get_signed_url(storage_path, expires_in=3600)
    return {"invoice_id": invoice_id, "download_url": signed_url, "expires_in": 3600}


# ── Buyer: Request Missing Invoice ────────────────────────────

@router.post("/request-missing")
async def request_missing_invoice(
    payload: MissingInvoiceRequest,
    current_user: BuyerUser = None,
):
    """Buyer flags a missing invoice from a seller."""
    from app.db.supabase_client import db_insert
    import uuid
    from datetime import datetime

    record = {
        "id":                      str(uuid.uuid4()),
        "buyer_id":                current_user["sub"],
        "seller_gstin":            payload.seller_gstin,
        "expected_invoice_number": payload.expected_invoice_number,
        "period":                  payload.period,
        "description":             payload.description,
        "status":                  "pending",
        "created_at":              datetime.utcnow().isoformat(),
    }
    await db_insert("missing_invoice_requests", record)
    return {"message": "Missing invoice request submitted", "request_id": record["id"]}


# ── Payment Tracking ───────────────────────────────────────────

@router.post("/payments/record")
async def record_payment_endpoint(
    payload: PaymentRecordRequest,
    current_user: CurrentUser = None,
):
    """Record a payment against an invoice."""
    return await record_payment(payload, current_user["sub"])


@router.get("/{invoice_id}/payments")
async def get_payments(
    invoice_id: str,
    current_user: CurrentUser = None,
):
    """Get payment history and balance for an invoice."""
    return await get_payment_summary(invoice_id)


@router.get("/seller/overdue")
async def list_overdue_invoices(current_user: SellerUser = None):
    """List all overdue unpaid invoices for the seller."""
    return await get_overdue_invoices(current_user["sub"])