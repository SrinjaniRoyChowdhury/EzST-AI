"""
models/invoice.py
─────────────────
Domain models for invoices, credit/debit notes, and payments.
These are plain Python dataclasses – no ORM dependency.
Supabase (Postgres) is managed via raw SQL migrations / the dashboard.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class InvoiceStatus(str, Enum):
    PENDING   = "pending"      # Seller uploaded, not yet shared
    SHARED    = "shared"       # Shared with buyer
    ACCEPTED  = "accepted"     # Buyer accepted
    REJECTED  = "rejected"     # Buyer rejected
    MODIFIED  = "modified"     # Modification requested


class InvoiceType(str, Enum):
    TAX_INVOICE = "tax_invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE  = "debit_note"
    PROFORMA    = "proforma"


class PaymentStatus(str, Enum):
    UNPAID     = "unpaid"
    PARTIAL    = "partial"
    PAID       = "paid"
    OVERDUE    = "overdue"


@dataclass
class LineItem:
    description: str
    hsn_sac_code: str
    quantity: float
    unit: str
    unit_price: float
    discount: float = 0.0
    cgst_rate: float = 0.0
    sgst_rate: float = 0.0
    igst_rate: float = 0.0

    @property
    def taxable_amount(self) -> float:
        return round((self.quantity * self.unit_price) - self.discount, 2)

    @property
    def total_tax(self) -> float:
        rate = (self.cgst_rate + self.sgst_rate + self.igst_rate) / 100
        return round(self.taxable_amount * rate, 2)

    @property
    def total_amount(self) -> float:
        return round(self.taxable_amount + self.total_tax, 2)


@dataclass
class Invoice:
    invoice_number: str
    invoice_date: datetime
    seller_gstin: str
    seller_name: str
    buyer_gstin: str
    buyer_name: str
    place_of_supply: str
    line_items: list[LineItem]
    invoice_type: InvoiceType = InvoiceType.TAX_INVOICE
    status: InvoiceStatus = InvoiceStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    id: str = field(default_factory=lambda: str(uuid4()))
    seller_id: Optional[str] = None
    buyer_id: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    file_url: Optional[str] = None
    raw_ocr_text: Optional[str] = None
    ai_extracted_data: Optional[dict] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def subtotal(self) -> float:
        return round(sum(i.taxable_amount for i in self.line_items), 2)

    @property
    def total_cgst(self) -> float:
        return round(sum(
            (i.taxable_amount * i.cgst_rate / 100) for i in self.line_items
        ), 2)

    @property
    def total_sgst(self) -> float:
        return round(sum(
            (i.taxable_amount * i.sgst_rate / 100) for i in self.line_items
        ), 2)

    @property
    def total_igst(self) -> float:
        return round(sum(
            (i.taxable_amount * i.igst_rate / 100) for i in self.line_items
        ), 2)

    @property
    def grand_total(self) -> float:
        return round(self.subtotal + self.total_cgst + self.total_sgst + self.total_igst, 2)