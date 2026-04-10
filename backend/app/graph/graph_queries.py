"""
graph/graph_queries.py
───────────────────────
All application-level Cypher queries.
Organised by domain: Business nodes, Invoice edges, Fraud detection.
"""

from datetime import datetime
from app.graph.neo4j_client import run_query


# ═══════════════════════════════════════════════════════════════
# BUSINESS NODE OPERATIONS
# ═══════════════════════════════════════════════════════════════

async def upsert_business(gstin: str, name: str, state: str) -> dict:
    """Create or update a Business node."""
    result = await run_query(
        """
        MERGE (b:Business {gstin: $gstin})
        SET b.name = $name,
            b.state = $state,
            b.updated_at = $now
        RETURN b
        """,
        {"gstin": gstin, "name": name, "state": state, "now": datetime.utcnow().isoformat()},
    )
    return result[0] if result else {}


async def get_business_network(gstin: str, depth: int = 2) -> list[dict]:
    """
    Return all businesses connected to `gstin` up to `depth` hops.
    Useful for visualising supply-chain relationships.
    """
    return await run_query(
        """
        MATCH path = (start:Business {gstin: $gstin})-[:TRANSACTS_WITH*1..$depth]-(related:Business)
        RETURN DISTINCT related.gstin AS gstin,
                        related.name AS name,
                        length(path) AS distance
        ORDER BY distance
        """,
        {"gstin": gstin, "depth": depth},
    )


# ═══════════════════════════════════════════════════════════════
# INVOICE EDGE OPERATIONS
# ═══════════════════════════════════════════════════════════════

async def create_invoice_relationship(
    invoice_id: str,
    invoice_number: str,
    invoice_date: str,
    grand_total: float,
    seller_gstin: str,
    buyer_gstin: str,
) -> None:
    """
    Create an Invoice node and link it to seller/buyer Business nodes.
    Graph model:
        (Seller:Business)-[:ISSUED]->(Invoice)-[:RECEIVED_BY]->(Buyer:Business)
        (Seller:Business)-[:TRANSACTS_WITH]->(Buyer:Business)
    """
    await run_query(
        """
        MERGE (inv:Invoice {id: $invoice_id})
        SET inv.invoice_number = $invoice_number,
            inv.invoice_date   = $invoice_date,
            inv.grand_total    = $grand_total

        MERGE (seller:Business {gstin: $seller_gstin})
        MERGE (buyer:Business  {gstin: $buyer_gstin})

        MERGE (seller)-[:ISSUED]->(inv)
        MERGE (inv)-[:RECEIVED_BY]->(buyer)
        MERGE (seller)-[:TRANSACTS_WITH]->(buyer)
        """,
        {
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "grand_total": grand_total,
            "seller_gstin": seller_gstin,
            "buyer_gstin": buyer_gstin,
        },
    )


async def get_invoices_between(seller_gstin: str, buyer_gstin: str) -> list[dict]:
    """Fetch all invoice nodes between two businesses."""
    return await run_query(
        """
        MATCH (s:Business {gstin: $seller})-[:ISSUED]->(inv:Invoice)-[:RECEIVED_BY]->(b:Business {gstin: $buyer})
        RETURN inv.id AS id,
               inv.invoice_number AS invoice_number,
               inv.invoice_date   AS invoice_date,
               inv.grand_total    AS grand_total
        ORDER BY inv.invoice_date DESC
        """,
        {"seller": seller_gstin, "buyer": buyer_gstin},
    )


# ═══════════════════════════════════════════════════════════════
# FRAUD DETECTION QUERIES
# ═══════════════════════════════════════════════════════════════

async def detect_circular_transactions(gstin: str) -> list[dict]:
    """
    Find circular invoice chains: A→B→C→A (potential carousel fraud).
    Returns cycles involving the given GSTIN.
    """
    return await run_query(
        """
        MATCH cycle = (start:Business {gstin: $gstin})-[:TRANSACTS_WITH*2..5]->(start)
        RETURN [node IN nodes(cycle) | node.gstin] AS cycle_gstins,
               length(cycle) AS cycle_length
        LIMIT 20
        """,
        {"gstin": gstin},
    )


async def detect_high_frequency_invoicing(
    gstin: str,
    threshold: int = 50,
    days: int = 7,
) -> list[dict]:
    """
    Detect unusually high invoice volume from a single seller in a short window.
    Flags potential fake invoice generation.
    """
    since = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    return await run_query(
        """
        MATCH (s:Business {gstin: $gstin})-[:ISSUED]->(inv:Invoice)
        WHERE inv.invoice_date >= $since
        WITH s, count(inv) AS invoice_count
        WHERE invoice_count >= $threshold
        RETURN s.gstin AS gstin, s.name AS name, invoice_count
        """,
        {"gstin": gstin, "since": since, "threshold": threshold},
    )


async def find_split_invoice_pattern(
    seller_gstin: str,
    buyer_gstin: str,
    amount_threshold: float = 50000.0,
) -> list[dict]:
    """
    Detect invoice splitting: multiple small invoices on the same day
    that together exceed the threshold (possible e-way bill evasion).
    """
    return await run_query(
        """
        MATCH (s:Business {gstin: $seller})-[:ISSUED]->(inv:Invoice)-[:RECEIVED_BY]->(b:Business {gstin: $buyer})
        WITH inv.invoice_date AS date, collect(inv) AS daily_invoices, sum(inv.grand_total) AS daily_total
        WHERE daily_total >= $threshold AND size(daily_invoices) > 3
        RETURN date,
               size(daily_invoices) AS invoice_count,
               daily_total,
               [i IN daily_invoices | i.invoice_number] AS invoice_numbers
        ORDER BY daily_total DESC
        """,
        {"seller": seller_gstin, "buyer": buyer_gstin, "threshold": amount_threshold},
    )


async def get_risk_score(gstin: str) -> dict:
    """
    Compute a simple composite risk score for a business based on graph signals.
    Returns 0.0 (low risk) to 1.0 (high risk).
    """
    # Count unique buyers (many buyers = normal; too many new = suspicious)
    buyer_count_result = await run_query(
        "MATCH (s:Business {gstin: $gstin})-[:TRANSACTS_WITH]->(b:Business) RETURN count(b) AS cnt",
        {"gstin": gstin},
    )
    buyer_count = buyer_count_result[0]["cnt"] if buyer_count_result else 0

    # Count total invoices issued
    invoice_count_result = await run_query(
        "MATCH (s:Business {gstin: $gstin})-[:ISSUED]->(inv:Invoice) RETURN count(inv) AS cnt",
        {"gstin": gstin},
    )
    invoice_count = invoice_count_result[0]["cnt"] if invoice_count_result else 0

    # Circular transactions = immediate red flag
    circular = await detect_circular_transactions(gstin)

    # Naive scoring heuristic (replace with ML model in prod)
    risk = 0.0
    if circular:
        risk += 0.5
    if invoice_count > 500:
        risk += 0.2
    if buyer_count < 2 and invoice_count > 100:
        risk += 0.3   # Concentrated transactions – suspicious

    return {
        "gstin": gstin,
        "risk_score": min(round(risk, 2), 1.0),
        "signals": {
            "circular_transactions": len(circular),
            "total_invoices": invoice_count,
            "unique_buyers": buyer_count,
        },
    }