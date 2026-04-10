"""
services/invoice_service.py
────────────────────────────
Orchestrates the full invoice lifecycle:
Upload → OCR → AI extraction → GST Calculation → Validation → DB store → Share → Track

Key changes vs original:
  • Files saved to Supabase Storage (private "invoices" bucket), not local disk
  • GST is calculated server-side via gst_calculator.py (state-code based logic)
  • share_invoice_with_buyer resolves buyer_id via user_profiles → businesses join
  • update_invoice_status enforces buyer_id ownership
  • get_invoices_for_buyer uses user_id (from JWT) not a raw GSTIN param
"""

import uuid
from datetime import datetime
from typing import Optional

from app.core.config import get_settings
from app.db.supabase_client import db_insert, db_select, db_update, get_supabase_admin
from app.db.supabase_storage import upload_invoice_file
from app.ocr.ocr_service import extract_text
from app.services.invoice_analyzer import extract_invoice_data, validate_invoice_data
from app.services.gst_calculator import calculate_invoice_gst
from app.models.invoice import InvoiceStatus, PaymentStatus
from app.schemas.invoice import (
    GSTBreakdown,
    InvoiceStatusUpdate,
    UploadResponse,
    PaymentRecordRequest,
)

settings = get_settings()

TABLE = "invoices"
PAYMENTS_TABLE = "payments"
MODIFICATIONS_TABLE = "invoice_modifications"


# ── Upload & Process ─────────────────────────────────────────

async def process_invoice_upload(
    file_bytes: bytes,
    filename: str,
    seller_id: str,
) -> UploadResponse:
    """
    Full pipeline:
      1. Upload file to Supabase Storage
      2. OCR (pdfplumber → Tesseract fallback)
      3. Gemini structured extraction
      4. Server-side GST calculation (intra/inter-state)
      5. Gemini validation
      6. Persist to Supabase (invoices table)

    Returns UploadResponse with invoice_id, gst_breakdown, and validation info.
    """
    invoice_id = str(uuid.uuid4())

    # ── 1. Upload to Supabase Storage ───────────────────────
    storage_path = upload_invoice_file(file_bytes, filename, seller_id, invoice_id)

    # ── 2. OCR ───────────────────────────────────────────────
    ocr_result = await extract_text(file_bytes, filename)
    raw_text: str = ocr_result["raw_text"]
    ocr_extracted = bool(raw_text)

    # ── 3. AI-powered structured extraction ─────────────────
    extracted_data = await extract_invoice_data(raw_text) if ocr_extracted else {}

    # ── 4. Server-side GST calculation ──────────────────────
    gst_breakdown_dict: dict = {}
    gst_breakdown_schema: Optional[GSTBreakdown] = None

    if extracted_data:
        gst_breakdown_dict = calculate_invoice_gst(extracted_data)
        try:
            gst_breakdown_schema = GSTBreakdown(**gst_breakdown_dict)
        except Exception:
            gst_breakdown_schema = None  # Don't fail upload if schema parse fails

    # ── 5. Validate extracted data ───────────────────────────
    validation_result = await validate_invoice_data(extracted_data) if extracted_data else {
        "is_valid": False, "confidence_score": 0.0, "issues": []
    }

    issues = [
        f"[{i.get('severity', 'warn').upper()}] {i.get('field')}: {i.get('message')}"
        for i in validation_result.get("issues", [])
    ]

    # ── 6. Persist to Supabase ───────────────────────────────
    # Use calculated grand_total from our engine (overrides Gemini's value)
    calc_grand_total = gst_breakdown_dict.get("grand_total") or extracted_data.get("grand_total")

    record = {
        "id":                 invoice_id,
        "seller_id":          seller_id,
        "file_url":           storage_path,       # Supabase Storage path
        "raw_ocr_text":       raw_text,
        "ai_extracted_data":  extracted_data,
        "gst_breakdown":      gst_breakdown_dict,
        "invoice_number":     extracted_data.get("invoice_number"),
        "invoice_date":       extracted_data.get("invoice_date"),
        "seller_gstin":       extracted_data.get("seller_gstin"),
        "seller_name":        extracted_data.get("seller_name"),
        "buyer_gstin":        extracted_data.get("buyer_gstin"),
        "buyer_name":         extracted_data.get("buyer_name"),
        "place_of_supply":    extracted_data.get("place_of_supply"),
        "grand_total":        float(calc_grand_total) if calc_grand_total else None,
        "status":             InvoiceStatus.PENDING,
        "payment_status":     PaymentStatus.UNPAID,
        "confidence_score":   validation_result.get("confidence_score", 0.0),
        "validation_issues":  issues,
        "created_at":         datetime.utcnow().isoformat(),
    }
    await db_insert(TABLE, record)

    return UploadResponse(
        invoice_id=invoice_id,
        storage_path=storage_path,
        ocr_extracted=ocr_extracted,
        ai_validated=validation_result.get("is_valid", False),
        confidence_score=validation_result.get("confidence_score", 0.0),
        extracted_data=extracted_data,
        gst_breakdown=gst_breakdown_schema,
        validation_issues=issues,
    )


# ── Buyer Resolution ──────────────────────────────────────────

async def resolve_buyer_id_by_gstin(buyer_gstin: str) -> Optional[str]:
    """
    Look up the buyer's user_profiles.id by matching their GSTIN via
    the businesses table join:
        user_profiles.business_id → businesses.id → businesses.gstin

    Returns user_profiles.id (a UUID string) or None if not found.
    """
    client = get_supabase_admin()
    try:
        # Join user_profiles → businesses to find the user with this GSTIN
        response = (
            client
            .table("user_profiles")
            .select("id, businesses!inner(gstin)")
            .eq("businesses.gstin", buyer_gstin)
            .limit(1)
            .execute()
        )
        data = response.data or []
        if data:
            return data[0]["id"]
    except Exception as e:
        print(f"⚠️  Could not resolve buyer_id for GSTIN {buyer_gstin}: {e}")
    return None


# ── Sharing ───────────────────────────────────────────────────

async def share_invoice_with_buyer(invoice_id: str, seller_id: str) -> dict:
    """
    Mark invoice as shared with buyer.
    Resolves buyer_id from buyer_gstin via user_profiles → businesses.
    Raises ValueError if invoice not found or not owned by seller.
    """
    # Fetch invoice to get buyer_gstin
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice or invoice.get("seller_id") != seller_id:
        return {}   # Caller will raise 404

    buyer_gstin = invoice.get("buyer_gstin")
    buyer_id = None
    if buyer_gstin:
        buyer_id = await resolve_buyer_id_by_gstin(buyer_gstin)

    update_data: dict = {
        "status":    InvoiceStatus.SHARED,
        "shared_at": datetime.utcnow().isoformat(),
    }
    if buyer_id:
        update_data["buyer_id"] = buyer_id

    return await db_update(
        TABLE,
        match={"id": invoice_id, "seller_id": seller_id},
        data=update_data,
    )


# ── Buyer Actions (accept / reject / modify) ──────────────────

async def update_invoice_status(
    invoice_id: str,
    buyer_user_id: str,
    update: InvoiceStatusUpdate,
) -> dict:
    """
    Buyer accepts, rejects, or requests modification.
    Enforcement: the invoice must have buyer_id == buyer_user_id,
    and its current status must be 'shared'.
    """
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        return {}

    # Ownership check: buyer_id on the invoice must match the JWT sub
    invoice_buyer_id = invoice.get("buyer_id")
    if invoice_buyer_id and invoice_buyer_id != buyer_user_id:
        raise PermissionError("You are not the designated buyer for this invoice")

    # Status guard: can only act on a shared invoice
    if invoice.get("status") != InvoiceStatus.SHARED:
        raise ValueError(f"Invoice is not in 'shared' state (current: {invoice.get('status')})")

    return await db_update(
        TABLE,
        match={"id": invoice_id},
        data={
            "status":              update.status,
            "buyer_action_reason": update.reason,
            "buyer_id":            buyer_user_id,   # Ensure buyer_id is set
            "buyer_actioned_at":   datetime.utcnow().isoformat(),
        },
    )


async def request_modification(
    invoice_id: str,
    buyer_user_id: str,
    suggested_changes: dict,
    reason: str,
) -> dict:
    """
    Store a buyer modification suggestion and flip invoice status to 'modified'.
    """
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        return {}

    # Ownership check
    invoice_buyer_id = invoice.get("buyer_id")
    if invoice_buyer_id and invoice_buyer_id != buyer_user_id:
        raise PermissionError("You are not the designated buyer for this invoice")

    if invoice.get("status") != InvoiceStatus.SHARED:
        raise ValueError(f"Invoice is not in 'shared' state (current: {invoice.get('status')})")

    modification_id = str(uuid.uuid4())
    modification_record = {
        "id":                 modification_id,
        "invoice_id":         invoice_id,
        "requested_by":        buyer_user_id,
        "suggested_changes":   suggested_changes,
        "reason":              reason,
        "status":              "pending",
        "created_at":          datetime.utcnow().isoformat(),
    }
    await db_insert(MODIFICATIONS_TABLE, modification_record)

    # Update invoice status to reflect that modification is requested
    await db_update(
        TABLE,
        match={"id": invoice_id},
        data={
            "status":              InvoiceStatus.MODIFIED,
            "buyer_action_reason": reason,
            "buyer_id":            buyer_user_id,
            "buyer_actioned_at":   datetime.utcnow().isoformat(),
        },
    )

    return modification_record


# ── Queries ───────────────────────────────────────────────────

async def get_invoices_by_seller(seller_id: str) -> list[dict]:
    return await db_select(TABLE, {"seller_id": seller_id})


async def get_invoices_for_buyer(buyer_user_id: str) -> list[dict]:
    """
    Return all invoices shared with a buyer, identified by their user_profiles.id.
    This is derived from the JWT 'sub', not a raw GSTIN query param.
    """
    return await db_select(TABLE, {"buyer_id": buyer_user_id, "status": InvoiceStatus.SHARED})


async def get_invoices_for_buyer_by_gstin(buyer_gstin: str) -> list[dict]:
    """
    Fallback: query by GSTIN when buyer_id is not yet set (e.g. before first share).
    Returns only shared invoices.
    """
    return await db_select(TABLE, {"buyer_gstin": buyer_gstin, "status": InvoiceStatus.SHARED})


async def get_invoice_by_id(invoice_id: str) -> Optional[dict]:
    results = await db_select(TABLE, {"id": invoice_id})
    return results[0] if results else None


# ── Payment Tracking ──────────────────────────────────────────

async def record_payment(req: PaymentRecordRequest, user_id: str) -> dict:
    """Log a payment against an invoice and update payment status."""
    invoice = await get_invoice_by_id(req.invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")

    grand_total = invoice.get("grand_total", 0)

    past_payments = await db_select(PAYMENTS_TABLE, {"invoice_id": req.invoice_id})
    paid_so_far = sum(p.get("amount_paid", 0) for p in past_payments)
    new_total_paid = paid_so_far + req.amount_paid

    if new_total_paid >= grand_total:
        payment_status = PaymentStatus.PAID
    elif new_total_paid > 0:
        payment_status = PaymentStatus.PARTIAL
    else:
        payment_status = PaymentStatus.UNPAID

    payment_record = {
        "id":               str(uuid.uuid4()),
        "invoice_id":       req.invoice_id,
        "recorded_by":      user_id,
        "amount_paid":      req.amount_paid,
        "payment_date":     req.payment_date.isoformat(),
        "payment_mode":     req.payment_mode,
        "reference_number": req.reference_number,
        "created_at":       datetime.utcnow().isoformat(),
    }
    await db_insert(PAYMENTS_TABLE, payment_record)
    await db_update(TABLE, {"id": req.invoice_id}, {"payment_status": payment_status})

    return {**payment_record, "new_payment_status": payment_status}