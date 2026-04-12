"""
services/chatbot_service.py
────────────────────────────
RAG chatbot: queries Neo4j for invoice context, then calls Groq LLM.
"""

from groq import Groq
from app.core.config import get_settings
from app.graph.neo4j_client import run_query

settings = get_settings()


CONTEXT_QUERY = """
MATCH (seller:Business)-[:ISSUED]->(inv:Invoice)-[:RECEIVED_BY]->(buyer:Business)
RETURN
  inv.invoice_number AS invoice_number,
  inv.invoice_date   AS invoice_date,
  inv.grand_total    AS grand_total,
  inv.description    AS description,
  inv.status         AS status,
  seller.name        AS seller_name,
  seller.gstin       AS seller_gstin,
  buyer.name         AS buyer_name,
  buyer.gstin        AS buyer_gstin
ORDER BY inv.invoice_date DESC
LIMIT 20
"""

SYSTEM_PROMPT = """You are EzST-AI, an intelligent B2B invoice and GST compliance assistant.
You have access to a knowledge graph of invoices between businesses.
Answer the user's question using the invoice data provided.
Be concise, professional, and specific — include invoice numbers and amounts where relevant.
If the question is not answerable from the provided data, say so honestly."""


async def fetch_neo4j_context() -> str:
    """Pull invoice data from Neo4j and format it as readable context."""
    try:
        records = await run_query(CONTEXT_QUERY)
        if not records:
            return "No invoice data found in the knowledge graph."

        lines = ["=== Invoice Knowledge Graph Context ==="]
        for r in records:
            lines.append(
                f"• {r['invoice_number']} | "
                f"₹{r['grand_total']:,.0f} | "
                f"{r['invoice_date']} | "
                f"Status: {(r['status'] or 'unknown').upper()} | "
                f"Seller: {r['seller_name']} ({r['seller_gstin']}) | "
                f"Buyer: {r['buyer_name']} ({r['buyer_gstin']}) | "
                f"Desc: {r['description'] or 'N/A'}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Could not fetch graph context: {e}"


async def chat_with_groq(question: str) -> str:
    """Send question + graph context to Groq and return the answer."""
    context = await fetch_neo4j_context()

    client = Groq(api_key=settings.groq_api_key)

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"{context}\n\nUser question: {question}"},
        ],
        temperature=0.3,
        max_tokens=512,
    )

    return response.choices[0].message.content
