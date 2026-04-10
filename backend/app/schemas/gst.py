"""
schemas/gst.py
──────────────
Pydantic schemas for GST return endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.gst import GSTReturnType, FilingStatus


class TaxSummarySchema(BaseModel):
    taxable_value: float
    cgst: float
    sgst: float
    igst: float
    cess: float = 0.0


class GSTReturnCreateRequest(BaseModel):
    gstin: str = Field(min_length=15, max_length=15)
    return_type: GSTReturnType
    tax_period: str         # "2024-03"


class GSTReturnResponse(BaseModel):
    id: str
    gstin: str
    return_type: GSTReturnType
    tax_period: str
    status: FilingStatus
    tax_summary: TaxSummarySchema
    invoice_count: int
    created_at: datetime
    filed_at: Optional[datetime] = None


class GSTChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None  # For multi-turn conversation


class GSTChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    session_id: str