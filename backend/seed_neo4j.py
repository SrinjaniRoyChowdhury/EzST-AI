"""
seed_neo4j.py
─────────────
Standalone script to seed 4 realistic demo invoices into the Neo4j
knowledge graph so the chatbot has data to answer queries against.

Run from the backend/ directory with the venv active:
    python seed_neo4j.py
"""

import asyncio
from neo4j import AsyncGraphDatabase

# ── Connection config (matches .env) ──────────────────────────────
NEO4J_URI      = "neo4j+s://a68cd587.databases.neo4j.io"
NEO4J_USER     = "a68cd587"
NEO4J_PASSWORD = "fDC7aO_osuba5n0xtYCy0HbbjGPUrZsNFigaHSPHLsI"
NEO4J_DATABASE = "a68cd587"

# ── 4 Demo Invoices ───────────────────────────────────────────────
INVOICES = [
    {
        "id": "demo-inv-001",
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-04-01",
        "grand_total": 84500.0,
        "description": "Cloud infrastructure services for Q1 2026",
        "seller_gstin": "22AAAAA0000A1Z5",
        "seller_name":  "TechNova Solutions Pvt Ltd",
        "buyer_gstin":  "BUYER_123",
        "buyer_name":   "Apex Retail Enterprises",
        "status": "pending",
    },
    {
        "id": "demo-inv-002",
        "invoice_number": "INV-2026-002",
        "invoice_date": "2026-04-03",
        "grand_total": 213750.0,
        "description": "Enterprise software licences – 15 seats, annual",
        "seller_gstin": "22AAAAA0000A1Z5",
        "seller_name":  "TechNova Solutions Pvt Ltd",
        "buyer_gstin":  "BUYER_123",
        "buyer_name":   "Apex Retail Enterprises",
        "status": "accepted",
    },
    {
        "id": "demo-inv-003",
        "invoice_number": "INV-2026-003",
        "invoice_date": "2026-04-06",
        "grand_total": 56320.0,
        "description": "IT support and maintenance – March 2026",
        "seller_gstin": "22AAAAA0000A1Z5",
        "seller_name":  "TechNova Solutions Pvt Ltd",
        "buyer_gstin":  "BUYER_123",
        "buyer_name":   "Apex Retail Enterprises",
        "status": "modified",
    },
    {
        "id": "demo-inv-004",
        "invoice_number": "INV-2026-004",
        "invoice_date": "2026-04-09",
        "grand_total": 138900.0,
        "description": "Custom dashboard development and deployment",
        "seller_gstin": "22AAAAA0000A1Z5",
        "seller_name":  "TechNova Solutions Pvt Ltd",
        "buyer_gstin":  "BUYER_123",
        "buyer_name":   "Apex Retail Enterprises",
        "status": "rejected",
    },
]


SEED_QUERY = """
MERGE (seller:Business {gstin: $seller_gstin})
  SET seller.name = $seller_name

MERGE (buyer:Business {gstin: $buyer_gstin})
  SET buyer.name = $buyer_name

MERGE (inv:Invoice {id: $id})
  SET inv.invoice_number = $invoice_number,
      inv.invoice_date   = $invoice_date,
      inv.grand_total    = $grand_total,
      inv.description    = $description,
      inv.status         = $status,
      inv.seller_gstin   = $seller_gstin,
      inv.buyer_gstin    = $buyer_gstin

MERGE (seller)-[:ISSUED]->(inv)
MERGE (inv)-[:RECEIVED_BY]->(buyer)
MERGE (seller)-[:TRANSACTS_WITH]->(buyer)
"""


async def seed():
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    async with driver.session(database=NEO4J_DATABASE) as session:
        for inv in INVOICES:
            await session.run(SEED_QUERY, inv)
            print(f"  [OK] Seeded {inv['invoice_number']} | Rs.{inv['grand_total']:,.0f} | {inv['status'].upper()}")
    await driver.close()
    print("\n[DONE] All 4 demo invoices seeded into Neo4j successfully!")


if __name__ == "__main__":
    print("[INFO] Seeding Neo4j knowledge graph with demo invoices...")
    asyncio.run(seed())
