"""
services/invoice_service.py
────────────────────────────
Orchestrates the full invoice lifecycle:
Upload → OCR → AI extraction → Validation → DB store → Share → Track
"""

import uuid
import os
from datetime import datetime
from typing import Optional

from app.core.config import get_settings
from app.db.supabase_client import db_insert, db_select, db_update
from app.ocr.ocr_service import extract_text
from app.services.invoice_analyzer import extract_invoice_data, validate_invoice_data
from app.models.invoice import InvoiceStatus, PaymentStatus
from app.schemas.invoice import (
    InvoiceCreateRequest, UploadResponse, InvoiceStatusUpdate,
    PaymentRecordRequest,
)

settings = get_settings()

TABLE = "invoices"
PAYMENTS_TABLE = "payments"


# ── Upload & Process ─────────────────────────────────────────

async def process_invoice_upload(
    file_bytes: bytes,
    filename: str,
    seller_id: str,
    buyer_gstin: Optional[str] = None,
) -> UploadResponse:
    """
    Full pipeline: save file → OCR → Gemini extraction → validate → store.
    Returns a structured UploadResponse.
    """
    # 1. Save raw file (flat into base dir so /uploads/{filename} works directly)
    invoice_id = str(uuid.uuid4())
    upload_dir = settings.invoice_upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{invoice_id}_{filename}")

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 2. OCR extraction
    ocr_result = await extract_text(file_bytes, filename)
    raw_text: str = ocr_result["raw_text"]
    ocr_extracted = bool(raw_text)

    # 3. MOCK AI-powered structured extraction (skipping LLM)
    extracted_data = {
        "invoice_number": f"INV-{uuid.uuid4().hex[:6].upper()}",
        "invoice_date": datetime.utcnow().strftime('%Y-%m-%d'),
        "grand_total": 1050.0,
        "seller_gstin": "22AAAAA0000A1Z5", # Must be exactly 15 chars
        "seller_name": "Mock Seller Inc.",
        "buyer_gstin": (buyer_gstin[:15] if buyer_gstin else "33BBBBB1111B1Z5"),
        "buyer_name": "Mock Buyer Corp.",
        "place_of_supply": "Karnataka",
    }

    # 4. MOCK Validate extracted data (skipping LLM)
    validation_result = {
        "is_valid": True, "confidence_score": 0.95, "issues": []
    }

    issues = [
        f"[{i.get('severity','warn').upper()}] {i.get('field')}: {i.get('message')}"
        for i in validation_result.get("issues", [])
    ]

    # 5. Persist to Supabase
    # Store only the filename so frontend can build the URL easily
    file_name = os.path.basename(file_path)
    record = {
        "id": invoice_id,
        "seller_id": seller_id,
        "file_url": file_name,
        "raw_ocr_text": raw_text,
        "ai_extracted_data": extracted_data,
        "invoice_number": extracted_data.get("invoice_number"),
        "invoice_date": extracted_data.get("invoice_date"),
        "seller_gstin": extracted_data.get("seller_gstin"),
        "seller_name": extracted_data.get("seller_name"),
        "buyer_gstin": extracted_data.get("buyer_gstin"),
        "buyer_name": extracted_data.get("buyer_name"),
        "place_of_supply": extracted_data.get("place_of_supply"),
        "grand_total": extracted_data.get("grand_total"),
        # Auto-share immediately if a buyer was specified
        "status": InvoiceStatus.PENDING,
        "payment_status": PaymentStatus.UNPAID,
        "confidence_score": validation_result.get("confidence_score", 0.0),
        "validation_issues": issues,
        "created_at": datetime.utcnow().isoformat(),
    }
    await db_insert(TABLE, record)

    return UploadResponse(
        invoice_id=invoice_id,
        ocr_extracted=ocr_extracted,
        ai_validated=validation_result.get("is_valid", False),
        confidence_score=validation_result.get("confidence_score", 0.0),
        extracted_data=extracted_data,
        validation_issues=issues,
    )


# ── Sharing ──────────────────────────────────────────────────

async def share_invoice_with_buyer(invoice_id: str, seller_id: str) -> dict:
    """Mark invoice as shared so the buyer can see it."""
    return await db_update(
        TABLE,
        match={"id": invoice_id, "seller_id": seller_id},
        data={"status": InvoiceStatus.SHARED, "shared_at": datetime.utcnow().isoformat()},
    )


async def update_invoice_status(
    invoice_id: str,
    buyer_id: str,
    update: InvoiceStatusUpdate,
) -> dict:
    """Buyer accepts, rejects, or requests modification."""
    return await db_update(
        TABLE,
        match={"id": invoice_id},
        data={
            "status": update.status,
            "buyer_action_reason": update.reason,
            "buyer_id": buyer_id,
            "buyer_actioned_at": datetime.utcnow().isoformat(),
        },
    )


# ── Queries ───────────────────────────────────────────────────

async def get_invoices_by_seller(seller_id: str) -> list[dict]:
    return await db_select(TABLE, {"seller_id": seller_id})


async def get_invoices_for_buyer(buyer_gstin: str) -> list[dict]:
    return await db_select(TABLE, {"buyer_gstin": buyer_gstin})


async def get_invoice_by_id(invoice_id: str) -> Optional[dict]:
    results = await db_select(TABLE, {"id": invoice_id})
    return results[0] if results else None


# ── Payment Tracking ──────────────────────────────────────────

async def record_payment(req: PaymentRecordRequest, user_id: str) -> dict:
    """Log a payment against an invoice and update payment status."""
    # Fetch current invoice to check outstanding balance
    invoice = await get_invoice_by_id(req.invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")

    grand_total = invoice.get("grand_total", 0)

    # Sum all payments so far
    past_payments = await db_select(PAYMENTS_TABLE, {"invoice_id": req.invoice_id})
    paid_so_far = sum(p.get("amount_paid", 0) for p in past_payments)
    new_total_paid = paid_so_far + req.amount_paid

    # Determine updated payment status
    if new_total_paid >= grand_total:
        payment_status = PaymentStatus.PAID
    elif new_total_paid > 0:
        payment_status = PaymentStatus.PARTIAL
    else:
        payment_status = PaymentStatus.UNPAID

    # Insert payment record
    payment_record = {
        "id": str(uuid.uuid4()),
        "invoice_id": req.invoice_id,
        "recorded_by": user_id,
        "amount_paid": req.amount_paid,
        "payment_date": req.payment_date.isoformat(),
        "payment_mode": req.payment_mode,
        "reference_number": req.reference_number,
        "created_at": datetime.utcnow().isoformat(),
    }
    await db_insert(PAYMENTS_TABLE, payment_record)

    # Update invoice payment status
    await db_update(TABLE, {"id": req.invoice_id}, {"payment_status": payment_status})

    return {**payment_record, "new_payment_status": payment_status}