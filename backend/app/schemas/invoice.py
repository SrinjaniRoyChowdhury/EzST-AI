"""
schemas/invoice.py
──────────────────
Pydantic v2 schemas for API request/response validation.
Keeps domain models separate from API contracts.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator
from app.models.invoice import InvoiceStatus, InvoiceType, PaymentStatus


# ── GST Breakdown ─────────────────────────────────────────────

class GSTLineItem(BaseModel):
    """Single line item enriched with calculated GST amounts."""
    description:    Optional[str]   = None
    hsn_sac_code:   Optional[str]   = None
    quantity:       Optional[float] = None
    unit:           Optional[str]   = None
    unit_price:     Optional[float] = None
    discount:       float           = 0.0
    taxable_amount: float           = 0.0
    cgst_rate:      float           = 0.0
    sgst_rate:      float           = 0.0
    igst_rate:      float           = 0.0
    cgst_amount:    float           = 0.0
    sgst_amount:    float           = 0.0
    igst_amount:    float           = 0.0
    total_tax:      float           = 0.0
    line_total:     float           = 0.0


class GSTBreakdown(BaseModel):
    """Complete per-invoice GST calculation result."""
    gst_type:      str                    # "intra_state" | "inter_state"
    seller_state:  Optional[str]   = None
    buyer_state:   Optional[str]   = None
    line_items:    list[GSTLineItem] = []
    taxable_value: float           = 0.0
    total_cgst:    float           = 0.0
    total_sgst:    float           = 0.0
    total_igst:    float           = 0.0
    total_tax:     float           = 0.0
    grand_total:   float           = 0.0


# ── Line Item ────────────────────────────────────────────────

class LineItemSchema(BaseModel):
    description: str
    hsn_sac_code: str
    quantity: float = Field(gt=0)
    unit: str
    unit_price: float = Field(gt=0)
    discount: float = Field(default=0.0, ge=0)
    cgst_rate: float = Field(default=0.0, ge=0)
    sgst_rate: float = Field(default=0.0, ge=0)
    igst_rate: float = Field(default=0.0, ge=0)


# ── Invoice Create ────────────────────────────────────────────

class InvoiceCreateRequest(BaseModel):
    invoice_number: str
    invoice_date: datetime
    seller_gstin: str = Field(min_length=15, max_length=15)
    buyer_gstin: str = Field(min_length=15, max_length=15)
    buyer_name: str
    place_of_supply: str
    line_items: list[LineItemSchema]
    invoice_type: InvoiceType = InvoiceType.TAX_INVOICE
    due_date: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator("seller_gstin", "buyer_gstin")
    @classmethod
    def validate_gstin(cls, v: str) -> str:
        import re
        pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid GSTIN format: {v}")
        return v


# ── Invoice Response ──────────────────────────────────────────

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    invoice_date: datetime
    seller_gstin: str
    seller_name: str
    buyer_gstin: str
    buyer_name: str
    place_of_supply: str
    invoice_type: InvoiceType
    status: InvoiceStatus
    payment_status: PaymentStatus
    subtotal: float
    total_cgst: float
    total_sgst: float
    total_igst: float
    grand_total: float
    file_url: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime


# ── Status Update ─────────────────────────────────────────────

class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus
    reason: Optional[str] = None   # Required when rejecting / requesting modification


# ── Buyer Action (unified) ─────────────────────────────────────

class BuyerActionRequest(BaseModel):
    """
    Unified payload for buyer actions on a shared invoice.
    status: accepted | rejected | modified
    reason: mandatory when status is rejected or modified
    suggested_changes: populated when status is modified
    """
    status: InvoiceStatus
    reason: Optional[str]   = None
    suggested_changes: Optional[dict[str, Any]] = None

    @field_validator("status")
    @classmethod
    def allowed_buyer_statuses(cls, v: InvoiceStatus) -> InvoiceStatus:
        allowed = {InvoiceStatus.ACCEPTED, InvoiceStatus.REJECTED, InvoiceStatus.MODIFIED}
        if v not in allowed:
            raise ValueError(f"Buyer can only set status to: accepted, rejected, modified. Got: {v}")
        return v

# ── Modification Request ──────────────────────────────────────

class ModificationRequest(BaseModel):
    invoice_id: str
    fields_to_change: dict          # {"line_items": [...], "notes": "..."}
    reason: str


# ── Payment Tracking ─────────────────────────────────────────

class PaymentRecordRequest(BaseModel):
    invoice_id: str
    amount_paid: float = Field(gt=0)
    payment_date: datetime
    payment_mode: str               # "NEFT", "RTGS", "UPI", "Cheque"
    reference_number: Optional[str] = None


# ── Missing Invoice Request ───────────────────────────────────

class MissingInvoiceRequest(BaseModel):
    seller_gstin: str
    expected_invoice_number: Optional[str] = None
    period: str                      # "2024-03"
    description: str


# ── Upload Response ───────────────────────────────────────────

class UploadResponse(BaseModel):
    invoice_id:        str
    storage_path:      str                        # Supabase Storage path for the file
    ocr_extracted:     bool
    ai_validated:      bool
    confidence_score:  float
    extracted_data:    dict
    gst_breakdown:     Optional[GSTBreakdown] = None
    validation_issues: list[str] = []


# ── Modification Suggestion ───────────────────────────────────

class ModificationSuggestionRequest(BaseModel):
    """
    Buyer requests changes to specific invoice fields.
    suggested_changes: field-level dict, e.g.:
        {"grand_total": 15000, "line_items": [{...}]}
    """
    suggested_changes: dict[str, Any]
    reason: str


class ModificationSuggestionResponse(BaseModel):
    modification_id: str
    invoice_id:      str
    status:          str           # "pending"
    message:         str