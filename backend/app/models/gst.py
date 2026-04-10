"""
models/gst.py
─────────────
GST return filing models (GSTR-1, GSTR-2A, GSTR-3B basics).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class GSTReturnType(str, Enum):
    GSTR1  = "GSTR-1"    # Outward supplies (seller)
    GSTR2A = "GSTR-2A"   # Auto-populated inward supplies
    GSTR3B = "GSTR-3B"   # Monthly summary return


class FilingStatus(str, Enum):
    DRAFT     = "draft"
    SUBMITTED = "submitted"
    FILED     = "filed"
    REVISED   = "revised"


@dataclass
class TaxSummary:
    taxable_value: float
    cgst: float
    sgst: float
    igst: float
    cess: float = 0.0

    @property
    def total_tax(self) -> float:
        return round(self.cgst + self.sgst + self.igst + self.cess, 2)

    @property
    def total_amount(self) -> float:
        return round(self.taxable_value + self.total_tax, 2)


@dataclass
class GSTReturn:
    gstin: str
    return_type: GSTReturnType
    tax_period: str          # "2024-03" (YYYY-MM)
    tax_summary: TaxSummary
    invoice_ids: list[str] = field(default_factory=list)
    status: FilingStatus = FilingStatus.DRAFT
    id: str = field(default_factory=lambda: str(uuid4()))
    filed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None