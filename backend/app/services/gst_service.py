"""
services/gst_service.py
────────────────────────
Generates GST returns (GSTR-1, GSTR-3B) by aggregating accepted invoices.
"""

from datetime import datetime
from typing import Optional
import uuid

from app.db.supabase_client import db_insert, db_select, db_update
from app.models.gst import GSTReturnType, FilingStatus, TaxSummary
from app.models.invoice import InvoiceStatus

TABLE = "gst_returns"
INVOICES_TABLE = "invoices"


async def generate_gstr1(gstin: str, period: str) -> dict:
    """
    GSTR-1: Aggregate all outward (seller) invoices for the period.
    period format: "2024-03"
    """
    year, month = period.split("-")

    # Fetch all accepted/shared invoices for this seller in the period
    invoices = await db_select(
        INVOICES_TABLE,
        {"seller_gstin": gstin},
    )
    # Filter by month/year in Python (Supabase free tier lacks complex date filters)
    period_invoices = [
        inv for inv in invoices
        if inv.get("invoice_date", "").startswith(f"{year}-{month}")
        and inv.get("status") in {InvoiceStatus.ACCEPTED, InvoiceStatus.SHARED}
    ]

    summary = _compute_tax_summary(period_invoices)
    return_doc = {
        "id": str(uuid.uuid4()),
        "gstin": gstin,
        "return_type": GSTReturnType.GSTR1,
        "tax_period": period,
        "status": FilingStatus.DRAFT,
        "tax_summary": summary,
        "invoice_ids": [i["id"] for i in period_invoices],
        "invoice_count": len(period_invoices),
        "created_at": datetime.utcnow().isoformat(),
    }
    await db_insert(TABLE, return_doc)
    return return_doc


async def generate_gstr3b(gstin: str, period: str) -> dict:
    """
    GSTR-3B: Summary of outward + inward supplies (net tax liability).
    """
    # Outward
    outward_invoices = await db_select(INVOICES_TABLE, {"seller_gstin": gstin})
    # Inward
    inward_invoices = await db_select(INVOICES_TABLE, {"buyer_gstin": gstin})

    year, month = period.split("-")

    def _filter(inv_list: list[dict]) -> list[dict]:
        return [
            i for i in inv_list
            if i.get("invoice_date", "").startswith(f"{year}-{month}")
        ]

    outward = _filter(outward_invoices)
    inward = _filter(inward_invoices)

    outward_summary = _compute_tax_summary(outward)
    inward_summary = _compute_tax_summary(inward)

    # Net tax liability = outward tax - inward ITC
    net_summary = {
        "taxable_value": outward_summary["taxable_value"],
        "cgst": round(outward_summary["cgst"] - inward_summary["cgst"], 2),
        "sgst": round(outward_summary["sgst"] - inward_summary["sgst"], 2),
        "igst": round(outward_summary["igst"] - inward_summary["igst"], 2),
        "cess": 0.0,
    }

    return_doc = {
        "id": str(uuid.uuid4()),
        "gstin": gstin,
        "return_type": GSTReturnType.GSTR3B,
        "tax_period": period,
        "status": FilingStatus.DRAFT,
        "outward_summary": outward_summary,
        "inward_summary": inward_summary,
        "net_tax_liability": net_summary,
        "created_at": datetime.utcnow().isoformat(),
    }
    await db_insert(TABLE, return_doc)
    return return_doc


async def file_return(return_id: str, gstin: str) -> dict:
    """Mark a drafted return as filed."""
    return await db_update(
        TABLE,
        {"id": return_id, "gstin": gstin},
        {"status": FilingStatus.FILED, "filed_at": datetime.utcnow().isoformat()},
    )


async def get_returns(gstin: str) -> list[dict]:
    return await db_select(TABLE, {"gstin": gstin})


# ── Internal helpers ──────────────────────────────────────────

def _compute_tax_summary(invoices: list[dict]) -> dict:
    taxable = cgst = sgst = igst = 0.0
    for inv in invoices:
        data = inv.get("ai_extracted_data") or {}
        taxable += float(data.get("subtotal") or 0)
        cgst += float(data.get("total_cgst") or 0)
        sgst += float(data.get("total_sgst") or 0)
        igst += float(data.get("total_igst") or 0)
    return {
        "taxable_value": round(taxable, 2),
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2),
        "igst": round(igst, 2),
        "cess": 0.0,
    }