"""
agents/gst_agent.py
────────────────────
GST Assistant Agent – multi-turn conversational AI for GST queries.

Combines:
  - RAG (FAISS + knowledge base) for grounded answers
  - Gemini for intelligent response generation
  - Session management for multi-turn conversations
  - Intent detection to route to correct handler
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

from app.rag.rag_pipeline import answer_gst_question
from app.services.gemini_client import generate_json, generate_text
from app.services.gst_service import get_returns, generate_gstr1


# ── Session Store (in-memory for hackathon; use Redis in prod) ─

_sessions: dict[str, list[dict]] = {}


def get_or_create_session(session_id: str | None) -> tuple[str, list[dict]]:
    """Return (session_id, history). Creates new session if needed."""
    sid = session_id or str(uuid.uuid4())
    if sid not in _sessions:
        _sessions[sid] = []
    return sid, _sessions[sid]


def append_to_session(session_id: str, role: str, content: str) -> None:
    if session_id in _sessions:
        _sessions[session_id].append({"role": role, "content": content})
        # Keep last 20 turns to stay within token limits
        _sessions[session_id] = _sessions[session_id][-20:]


# ── Intent Detection ──────────────────────────────────────────

class QueryIntent(str, Enum):
    GENERAL_GST    = "general_gst"      # Generic GST rule question
    RETURN_STATUS  = "return_status"    # "What's my GSTR-1 status?"
    ITC_QUERY      = "itc_query"        # Input Tax Credit questions
    PENALTY_QUERY  = "penalty_query"    # Late filing, penalties
    INVOICE_HELP   = "invoice_help"     # Invoice-related questions
    UNKNOWN        = "unknown"


async def detect_intent(question: str) -> QueryIntent:
    result = await generate_json(
        prompt=f"""
        Classify this GST-related question into one category:
        Question: "{question}"
        
        Categories: general_gst, return_status, itc_query, penalty_query, invoice_help, unknown
        
        Return JSON: {{"intent": "<category>"}}
        """,
    )
    intent_str = result.get("intent", "unknown")
    try:
        return QueryIntent(intent_str)
    except ValueError:
        return QueryIntent.UNKNOWN


# ── Specialised Handlers ──────────────────────────────────────

async def handle_return_status(question: str, gstin: str | None) -> str:
    if not gstin:
        return "To check your return status, please provide your GSTIN."
    returns = await get_returns(gstin)
    if not returns:
        return f"No GST returns found for GSTIN {gstin}. You may need to generate them first."
    summary = "\n".join(
        f"- {r.get('return_type')} for {r.get('tax_period')}: {r.get('status')}"
        for r in returns[-5:]
    )
    return f"Recent GST returns for {gstin}:\n{summary}"


async def handle_penalty_query(question: str) -> str:
    return await generate_text(
        f"""
        A taxpayer asks: "{question}"
        
        Provide a clear, accurate answer about GST penalties, late fees, or interest
        based on CGST Act 2017. Include relevant section numbers where applicable.
        Be concise (max 200 words).
        """,
        temperature=0.2,
    )


# ── Main GSTAgent ─────────────────────────────────────────────

class GSTAgent:
    """
    Multi-turn GST compliance assistant.
    Maintains session state and routes questions to appropriate handlers.
    """

    async def chat(
        self,
        question: str,
        session_id: str | None = None,
        user_gstin: str | None = None,
    ) -> dict:
        """
        Process a user question and return an answer with session tracking.

        Returns:
            {
                "answer": str,
                "sources": list[str],
                "session_id": str,
                "intent": str,
            }
        """
        sid, history = get_or_create_session(session_id)
        append_to_session(sid, "user", question)

        # Detect intent to route appropriately
        intent = await detect_intent(question)

        if intent == QueryIntent.RETURN_STATUS:
            answer = await handle_return_status(question, user_gstin)
            sources = []
        elif intent == QueryIntent.PENALTY_QUERY:
            answer = await handle_penalty_query(question)
            sources = []
        else:
            # Default: RAG-powered answer for general GST questions
            rag_result = await answer_gst_question(question, session_context=history)
            answer = rag_result["answer"]
            sources = rag_result["sources"]

        append_to_session(sid, "assistant", answer)

        return {
            "answer": answer,
            "sources": sources,
            "session_id": sid,
            "intent": intent.value,
        }

    async def explain_return(self, return_type: str, period: str) -> str:
        """Generate a plain-English explanation of a GST return filing."""
        return await generate_text(
            f"Explain what {return_type} return for period {period} means "
            f"for an Indian B2B business, in simple language (max 150 words).",
            temperature=0.4,
        )

    async def suggest_itc_optimisation(self, invoice_summary: list[dict]) -> str:
        """AI-powered ITC optimisation suggestions based on recent invoices."""
        import json
        return await generate_text(
            f"""
            Based on these recent purchase invoices, suggest ITC optimisation strategies:
            {json.dumps(invoice_summary[:20], indent=2)}
            
            Focus on: blocked credits to avoid, timing of claims, reconciliation tips.
            Keep response under 300 words.
            """,
            temperature=0.3,
        )