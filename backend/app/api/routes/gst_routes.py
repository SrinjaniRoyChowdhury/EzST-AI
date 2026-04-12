"""
api/routes/gst_routes.py
─────────────────────────
GST API: return generation, filing, real-time tracking, and AI chatbot.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.schemas.gst import GSTChatRequest, GSTChatResponse, GSTReturnCreateRequest
from app.services.gst_service import (
    file_return,
    generate_gstr1,
    generate_gstr3b,
    get_returns,
)
from app.agents.gst_agent import GSTAgent
from app.agents.risk_agent import RiskAgent

router = APIRouter(prefix="/gst", tags=["GST"])
CurrentUser = Annotated[dict, Depends(get_current_user)]

_gst_agent = GSTAgent()
_risk_agent = RiskAgent()


# ── GSTR-1: Outward Supply Return ────────────────────────────

@router.post("/returns/gstr1")
async def create_gstr1(payload: GSTReturnCreateRequest, current_user: CurrentUser = None):
    """
    Generate GSTR-1 (outward supplies) for a given GSTIN and period.
    Aggregates all accepted/shared invoices for that period.
    """
    result = await generate_gstr1(payload.gstin, payload.tax_period)
    return result


# ── GSTR-3B: Summary Return ───────────────────────────────────

@router.post("/returns/gstr3b")
async def create_gstr3b(payload: GSTReturnCreateRequest, current_user: CurrentUser = None):
    """
    Generate GSTR-3B (net tax liability summary) for a GSTIN and period.
    Computes outward tax minus inward ITC.
    """
    result = await generate_gstr3b(payload.gstin, payload.tax_period)
    return result


# ── File a Return ─────────────────────────────────────────────

@router.post("/returns/{return_id}/file")
async def file_gst_return(
    return_id: str,
    gstin: str,
    current_user: CurrentUser = None,
):
    """Mark a drafted return as filed."""
    updated = await file_return(return_id, gstin)
    if not updated:
        raise HTTPException(status_code=404, detail="Return not found")
    return {"message": "Return filed successfully", "return_id": return_id}


# ── List Returns (Real-Time Tracking) ────────────────────────

@router.get("/returns")
async def list_returns(gstin: str, current_user: CurrentUser = None):
    """
    Real-time tracking of all GST returns for a GSTIN.
    Shows issued, draft, and filed returns.
    """
    returns = await get_returns(gstin)
    return {
        "gstin": gstin,
        "total": len(returns),
        "returns": returns,
    }


# ── Invoice Tracking Dashboard ────────────────────────────────

@router.get("/dashboard/{gstin}")
async def gst_dashboard(gstin: str, period: str, current_user: CurrentUser = None):
    """
    Real-time summary: issued vs. received invoices, tax liability,
    ITC available, and filing status for the period.
    """
    from app.db.supabase_client import db_select

    issued = await db_select("invoices", {"seller_gstin": gstin})
    received = await db_select("invoices", {"buyer_gstin": gstin})

    def _period_filter(inv_list: list[dict], period: str) -> list[dict]:
        y, m = period.split("-")
        return [
            i for i in inv_list
            if (i.get("invoice_date") or "").startswith(f"{y}-{m}")
        ]

    period_issued = _period_filter(issued, period)
    period_received = _period_filter(received, period)

    def _sum(inv_list: list[dict], key: str) -> float:
        return round(sum(
            float((i.get("ai_extracted_data") or {}).get(key) or 0)
            for i in inv_list
        ), 2)

    return {
        "gstin": gstin,
        "period": period,
        "outward": {
            "invoice_count": len(period_issued),
            "total_taxable": _sum(period_issued, "subtotal"),
            "total_cgst": _sum(period_issued, "total_cgst"),
            "total_sgst": _sum(period_issued, "total_sgst"),
            "total_igst": _sum(period_issued, "total_igst"),
        },
        "inward": {
            "invoice_count": len(period_received),
            "itc_cgst": _sum(period_received, "total_cgst"),
            "itc_sgst": _sum(period_received, "total_sgst"),
            "itc_igst": _sum(period_received, "total_igst"),
        },
    }


# ── GST AI Chatbot ────────────────────────────────────────────

@router.post("/chat")
async def gst_chat(
    payload: GSTChatRequest,
    current_user: CurrentUser = None,
):
    """
    RAG-powered GST chatbot using Neo4j knowledge graph + Groq LLM.
    """
    from app.services.chatbot_service import chat_with_groq
    try:
        answer = await chat_with_groq(payload.question)
        return {"answer": answer, "sources": [], "session_id": payload.session_id or "default"}
    except Exception as e:
        return {"answer": f"Sorry, I encountered an error: {str(e)}", "sources": [], "session_id": "default"}


# ── Risk Analysis ─────────────────────────────────────────────

@router.get("/risk/{gstin}")
async def get_risk_report(
    gstin: str,
    counterparty_gstin: str | None = None,
    current_user: CurrentUser = None,
):
    """
    Run the Risk Detection Agent for a GSTIN.
    Returns fraud signals, risk score, and recommended actions.
    """
    report = await _risk_agent.analyse(gstin, seller_gstin=counterparty_gstin)
    return report