"""
api/routes/invoice_routes.py
──────────────────────────────
Invoice API: upload, share, accept/reject, payment tracking.

All routes require a valid Supabase JWT (via get_current_user dependency).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.security import get_current_user
from app.schemas.invoice import (
    InvoiceStatusUpdate,
    MissingInvoiceRequest,
    ModificationRequest,
    PaymentRecordRequest,
    UploadResponse,
)
from app.services.invoice_service import (
    get_invoice_by_id,
    get_invoices_by_seller,
    get_invoices_for_buyer,
    process_invoice_upload,
    record_payment,
    share_invoice_with_buyer,
    update_invoice_status,
)
from app.services.payment_service import get_overdue_invoices, get_payment_summary
from app.agents.validator_agent import ValidatorAgent
from app.graph.graph_queries import create_invoice_relationship

router = APIRouter(prefix="/invoices", tags=["Invoices"])

CurrentUser = Annotated[dict, Depends(get_current_user)]


# ── Upload ─────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    file: UploadFile = File(..., description="Invoice PDF or image"),
    buyer_gstin: str = Form(None, description="Manually entered Buyer ID (GSTIN)"),
    current_user: CurrentUser = None,
):
    """
    Upload an invoice file.
    Pipeline: Save → OCR → Gemini extraction → Validation → Store in DB + Graph
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
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="File size exceeds 10 MB limit")

    seller_id: str = current_user["sub"]
    upload_result = await process_invoice_upload(file_bytes, file.filename, seller_id, buyer_gstin)

    # Create graph relationship if extraction succeeded (non-blocking)
    extracted = upload_result.extracted_data
    if extracted.get("seller_gstin") and extracted.get("buyer_gstin"):
        try:
            await create_invoice_relationship(
                invoice_id=upload_result.invoice_id,
                invoice_number=extracted.get("invoice_number", "UNKNOWN"),
                invoice_date=extracted.get("invoice_date", ""),
                grand_total=float(extracted.get("grand_total") or 0),
                seller_gstin=extracted["seller_gstin"],
                buyer_gstin=extracted["buyer_gstin"],
            )
        except Exception as e:
            print(f"⚠️  Graph update skipped: {e}")

    return upload_result


# ── Validation ─────────────────────────────────────────────────

@router.post("/{invoice_id}/validate")
async def validate_invoice(invoice_id: str, current_user: CurrentUser = None):
    """Re-run the validator agent on an existing invoice."""
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    agent = ValidatorAgent()
    report = await agent.run(invoice_id, invoice.get("ai_extracted_data") or {})
    return report


# ── Seller: Share Invoice ──────────────────────────────────────

@router.post("/{invoice_id}/share", status_code=status.HTTP_200_OK)
async def share_invoice(invoice_id: str, current_user: CurrentUser = None):
    """Seller shares invoice with the buyer (changes status to SHARED)."""
    seller_id: str = current_user["sub"]
    updated = await share_invoice_with_buyer(invoice_id, seller_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Invoice not found or not owned by you")
    return {"message": "Invoice shared successfully", "invoice_id": invoice_id}


# ── Buyer: Accept / Reject / Request Modification ────────────

@router.patch("/{invoice_id}/status", status_code=status.HTTP_200_OK)
async def update_status(
    invoice_id: str,
    payload: InvoiceStatusUpdate,
    current_user: CurrentUser = None,
):
    """Buyer updates invoice status: accepted | rejected | modified."""
    buyer_id: str = current_user["sub"]
    updated = await update_invoice_status(invoice_id, buyer_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"message": f"Invoice status updated to '{payload.status}'", "invoice_id": invoice_id}


# ── List Invoices ─────────────────────────────────────────────

@router.get("/seller/my-invoices")
async def list_seller_invoices(current_user: CurrentUser = None):
    """Seller lists all their uploaded invoices."""
    return await get_invoices_by_seller(current_user["sub"])


@router.get("/buyer/received")
async def list_buyer_invoices(buyer_gstin: str, current_user: CurrentUser = None):
    """Buyer lists all invoices shared with them."""
    return await get_invoices_for_buyer(buyer_gstin)


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str, current_user: CurrentUser = None):
    """Get a single invoice by ID."""
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


# ── Buyer: Request Missing Invoice ────────────────────────────

@router.post("/request-missing")
async def request_missing_invoice(
    payload: MissingInvoiceRequest,
    current_user: CurrentUser = None,
):
    """Buyer flags a missing invoice from a seller."""
    from app.db.supabase_client import db_insert
    import uuid
    from datetime import datetime

    record = {
        "id": str(uuid.uuid4()),
        "buyer_id": current_user["sub"],
        "seller_gstin": payload.seller_gstin,
        "expected_invoice_number": payload.expected_invoice_number,
        "period": payload.period,
        "description": payload.description,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
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
async def get_payments(invoice_id: str, current_user: CurrentUser = None):
    """Get payment history and balance for an invoice."""
    return await get_payment_summary(invoice_id)


@router.get("/seller/overdue")
async def list_overdue_invoices(current_user: CurrentUser = None):
    """List all overdue unpaid invoices for the seller."""
    return await get_overdue_invoices(current_user["sub"])