"""
services/payment_service.py
─────────────────────────────
Payment tracking and reconciliation against invoices.
"""

from datetime import datetime, timedelta
from app.db.supabase_client import db_select, db_update
from app.models.invoice import PaymentStatus

INVOICES_TABLE = "invoices"
PAYMENTS_TABLE = "payments"


async def get_payment_summary(invoice_id: str) -> dict:
    """Return payment history and outstanding balance for an invoice."""
    invoices = await db_select(INVOICES_TABLE, {"id": invoice_id})
    if not invoices:
        return {}

    invoice = invoices[0]
    grand_total = float(invoice.get("grand_total") or 0)

    payments = await db_select(PAYMENTS_TABLE, {"invoice_id": invoice_id})
    total_paid = sum(float(p.get("amount_paid", 0)) for p in payments)
    outstanding = round(grand_total - total_paid, 2)

    return {
        "invoice_id": invoice_id,
        "grand_total": grand_total,
        "total_paid": round(total_paid, 2),
        "outstanding": outstanding,
        "payment_status": invoice.get("payment_status"),
        "payments": payments,
    }


async def get_overdue_invoices(seller_id: str) -> list[dict]:
    """Find all unpaid/partial invoices past their due date."""
    invoices = await db_select(INVOICES_TABLE, {"seller_id": seller_id})
    now = datetime.utcnow()
    overdue = []
    for inv in invoices:
        due_date_str = inv.get("due_date")
        payment_status = inv.get("payment_status")
        if not due_date_str or payment_status == PaymentStatus.PAID:
            continue
        try:
            due_date = datetime.fromisoformat(due_date_str)
            if due_date < now:
                overdue.append(inv)
                # Mark as overdue in DB
                await db_update(
                    INVOICES_TABLE,
                    {"id": inv["id"]},
                    {"payment_status": PaymentStatus.OVERDUE},
                )
        except ValueError:
            continue
    return overdue


async def get_payment_analytics(seller_id: str, days: int = 30) -> dict:
    """
    High-level analytics for the seller dashboard.
    Returns totals for the last `days` days.
    """
    invoices = await db_select(INVOICES_TABLE, {"seller_id": seller_id})
    since = datetime.utcnow() - timedelta(days=days)

    recent = [
        i for i in invoices
        if datetime.fromisoformat(i.get("created_at", "2000-01-01")) > since
    ]

    total_invoiced = sum(float(i.get("grand_total") or 0) for i in recent)
    total_paid = sum(
        float(i.get("grand_total") or 0)
        for i in recent if i.get("payment_status") == PaymentStatus.PAID
    )

    return {
        "period_days": days,
        "invoice_count": len(recent),
        "total_invoiced": round(total_invoiced, 2),
        "total_paid": round(total_paid, 2),
        "outstanding": round(total_invoiced - total_paid, 2),
        "collection_rate": round((total_paid / total_invoiced * 100) if total_invoiced else 0, 1),
    }