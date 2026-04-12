"""
generate_demo_invoices.py
─────────────────────────
One-shot script that:
  1. Generates 4 realistic PDF invoices (different sellers, buyers, amounts)
  2. Saves them in  backend/demo_invoices/
  3. Copies them to  backend/uploads/invoices/  so the frontend can serve them
  4. Inserts records into Supabase so they appear on the buyer dashboard
  5. Seeds Neo4j so the chatbot can answer questions about them

Run from the backend/ directory with the venv active:
    python generate_demo_invoices.py

All four invoices will have buyer_gstin = "BUYER_123" so they show up when
the buyer dashboard is filtered to that ID.
"""

import asyncio
import os
import shutil
import uuid
from datetime import datetime

# ── Third-party ───────────────────────────────────────────────────
from fpdf import FPDF
from supabase import create_client
from neo4j import AsyncGraphDatabase

# ── Config (hard-coded to match .env so the script is self-contained) ─
SUPABASE_URL  = "https://kaylywyuwgaeohfaczmm.supabase.co"
SUPABASE_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtheWx5d3l1d2dhZW9oZmFjem1tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU4MDY4ODMsImV4cCI6MjA5MTM4Mjg4M30.L3cq1ntlje5nXDo6jo_6gsbrYOH04t9ViEu1y9Ww3Ns"

NEO4J_URI      = "neo4j+s://a68cd587.databases.neo4j.io"
NEO4J_USER     = "a68cd587"
NEO4J_PASSWORD = "fDC7aO_osuba5n0xtYCy0HbbjGPUrZsNFigaHSPHLsI"
NEO4J_DATABASE = "a68cd587"

UPLOAD_DIR     = "./uploads/invoices"
DEMO_DIR       = "./demo_invoices"
BUYER_GSTIN    = "BUYER_123"
SELLER_ID      = "11111111-1111-1111-1111-111111111111"

# ── The 4 unique invoices ─────────────────────────────────────────
INVOICES = [
    {
        "id": str(uuid.uuid4()),
        "invoice_number": "INV-2026-001",
        "invoice_date":   "2026-04-01",
        "due_date":       "2026-04-30",
        "grand_total":     84500.0,
        "seller_gstin":   "22AAAAA0000A1Z5",
        "seller_name":    "TechNova Solutions Pvt Ltd",
        "seller_addr":    "42, Koramangala 5th Block, Bengaluru - 560095",
        "buyer_gstin":    BUYER_GSTIN,
        "buyer_name":     "Apex Retail Enterprises",
        "buyer_addr":     "18, Nehru Place, New Delhi - 110019",
        "place_of_supply":"Karnataka",
        "description":    "Cloud Infrastructure Services - Q1 2026",
        "items": [
            {"desc": "AWS EC2 Reserved Instances (12 mo.)", "qty": 3, "rate": 18000.0, "gst": 18},
            {"desc": "Cloud Storage (2 TB, monthly)",        "qty": 1, "rate": 12000.0, "gst": 18},
            {"desc": "CDN Bandwidth Charges",               "qty": 1,  "rate": 6500.0, "gst": 18},
        ],
        "status": "pending",
    },
    {
        "id": str(uuid.uuid4()),
        "invoice_number": "INV-2026-002",
        "invoice_date":   "2026-04-03",
        "due_date":       "2026-05-03",
        "grand_total":    213750.0,
        "seller_gstin":   "22AAAAA0000A1Z5",
        "seller_name":    "TechNova Solutions Pvt Ltd",
        "seller_addr":    "42, Koramangala 5th Block, Bengaluru - 560095",
        "buyer_gstin":    BUYER_GSTIN,
        "buyer_name":     "Apex Retail Enterprises",
        "buyer_addr":     "18, Nehru Place, New Delhi - 110019",
        "place_of_supply":"Karnataka",
        "description":    "Enterprise Software Licences - Annual Subscription",
        "items": [
            {"desc": "ERP Suite Pro (15 seats, annual)",    "qty": 15, "rate": 9000.0, "gst": 18},
            {"desc": "CRM Module Add-on (annual)",          "qty": 5,  "rate": 7500.0, "gst": 18},
            {"desc": "Security & Compliance Module",        "qty": 1,  "rate": 22500.0, "gst": 18},
        ],
        "status": "accepted",
    },
    {
        "id": str(uuid.uuid4()),
        "invoice_number": "INV-2026-003",
        "invoice_date":   "2026-04-06",
        "due_date":       "2026-04-21",
        "grand_total":     56320.0,
        "seller_gstin":   "22AAAAA0000A1Z5",
        "seller_name":    "TechNova Solutions Pvt Ltd",
        "seller_addr":    "42, Koramangala 5th Block, Bengaluru - 560095",
        "buyer_gstin":    BUYER_GSTIN,
        "buyer_name":     "Apex Retail Enterprises",
        "buyer_addr":     "18, Nehru Place, New Delhi - 110019",
        "place_of_supply":"Karnataka",
        "description":    "IT Support & Maintenance - March 2026",
        "items": [
            {"desc": "On-site Support (16 hrs @ Rs.1800/hr)", "qty": 16, "rate": 1800.0, "gst": 18},
            {"desc": "Network Firewall Configuration",         "qty": 1,  "rate": 14000.0, "gst": 18},
            {"desc": "Backup Solution Setup",                  "qty": 1,  "rate": 9600.0,  "gst": 18},
        ],
        "status": "modified",
    },
    {
        "id": str(uuid.uuid4()),
        "invoice_number": "INV-2026-004",
        "invoice_date":   "2026-04-09",
        "due_date":       "2026-05-09",
        "grand_total":    138900.0,
        "seller_gstin":   "22AAAAA0000A1Z5",
        "seller_name":    "TechNova Solutions Pvt Ltd",
        "seller_addr":    "42, Koramangala 5th Block, Bengaluru - 560095",
        "buyer_gstin":    BUYER_GSTIN,
        "buyer_name":     "Apex Retail Enterprises",
        "buyer_addr":     "18, Nehru Place, New Delhi - 110019",
        "place_of_supply":"Karnataka",
        "description":    "Custom Dashboard Development & Deployment",
        "items": [
            {"desc": "UI/UX Design (React + Figma, 40 hrs)",  "qty": 40, "rate": 1500.0, "gst": 18},
            {"desc": "Backend API Development (FastAPI)",      "qty": 30, "rate": 2000.0, "gst": 18},
            {"desc": "Deployment & CI/CD Pipeline Setup",      "qty": 1,  "rate": 18000.0, "gst": 18},
        ],
        "status": "rejected",
    },
]


# ═════════════════════════════════════════════════════════════════
# PDF GENERATOR
# ═════════════════════════════════════════════════════════════════

class InvoicePDF(FPDF):
    def header(self):
        pass  # Custom header drawn in generate_pdf

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} | EzST-AI Invoice System", align="C")


def generate_pdf(inv: dict, filepath: str):
    pdf = InvoicePDF()
    pdf.add_page()
    W = pdf.w - 40  # usable width

    # ── Header bar ────────────────────────────────────────────
    pdf.set_fill_color(213, 0, 0)
    pdf.rect(0, 0, pdf.w, 28, style="F")
    pdf.set_y(6)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "TAX INVOICE", align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "EzST-AI | Powered by AI-driven GST Compliance", align="C")
    pdf.ln(14)
    pdf.set_text_color(30, 30, 30)

    # ── Invoice meta ──────────────────────────────────────────
    pdf.set_x(20)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(W / 2, 7, f"Invoice No:  {inv['invoice_number']}")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(W / 2, 7, f"Date: {inv['invoice_date']}", align="R")
    pdf.ln(6)
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(W / 2, 6, f"Due Date:    {inv['due_date']}")
    pdf.set_font("Helvetica", "B", 10)
    status_colors = {"pending": (30, 100, 200), "accepted": (20, 160, 80),
                     "modified": (200, 130, 0), "rejected": (200, 30, 30)}
    r, g, b = status_colors.get(inv["status"], (80, 80, 80))
    pdf.set_text_color(r, g, b)
    pdf.cell(W / 2, 6, f"Status: {inv['status'].upper()}", align="R")
    pdf.set_text_color(30, 30, 30)
    pdf.ln(10)

    # ── Seller / Buyer columns ────────────────────────────────
    col = W / 2
    pdf.set_x(20)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(col - 5, 7, "  SELLER / BILLED FROM", fill=True)
    pdf.cell(5, 7, "")
    pdf.cell(col - 5, 7, "  BUYER / BILLED TO", fill=True)
    pdf.ln(7)

    def party_block(x, name, gstin, addr):
        pdf.set_x(x)
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(col - 10, 6, name, border=0)
        pdf.set_x(x)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(col - 10, 5, f"GSTIN: {gstin}\n{addr}", border=0)

    y_before = pdf.get_y()
    party_block(20, inv["seller_name"], inv["seller_gstin"], inv["seller_addr"])
    y_after_seller = pdf.get_y()
    pdf.set_y(y_before)
    party_block(20 + col + 2, inv["buyer_name"], inv["buyer_gstin"], inv["buyer_addr"])
    pdf.set_y(max(y_after_seller, pdf.get_y()) + 8)

    # ── Line items table ─────────────────────────────────────
    pdf.set_x(20)
    pdf.set_fill_color(213, 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(80, 8, "  DESCRIPTION", fill=True)
    pdf.cell(20, 8, "QTY", fill=True, align="C")
    pdf.cell(35, 8, "RATE (Rs.)", fill=True, align="R")
    pdf.cell(20, 8, "GST %", fill=True, align="C")
    pdf.cell(35, 8, "AMOUNT (Rs.)", fill=True, align="R")
    pdf.ln(8)
    pdf.set_text_color(30, 30, 30)

    subtotal = 0.0
    total_gst = 0.0
    for i, item in enumerate(inv["items"]):
        taxable = item["qty"] * item["rate"]
        gst_amt = taxable * item["gst"] / 100
        line_total = taxable + gst_amt
        subtotal += taxable
        total_gst += gst_amt

        bg = 252 if i % 2 == 0 else 245
        pdf.set_fill_color(bg, bg, bg)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(20)
        pdf.cell(80, 7, f"  {item['desc'][:48]}", fill=True)
        pdf.cell(20, 7, str(item["qty"]), fill=True, align="C")
        pdf.cell(35, 7, f"{item['rate']:,.0f}", fill=True, align="R")
        pdf.cell(20, 7, f"{item['gst']}%", fill=True, align="C")
        pdf.cell(35, 7, f"{line_total:,.0f}", fill=True, align="R")
        pdf.ln(7)

    # ── Totals ───────────────────────────────────────────────
    pdf.ln(4)
    pdf.set_x(20 + 80 + 20 + 35)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(35, 7, f"Subtotal:", align="L")
    pdf.cell(35, 7, f"Rs. {subtotal:,.0f}", align="R")
    pdf.ln(6)
    pdf.set_x(20 + 80 + 20 + 35)
    pdf.cell(35, 7, f"GST ({inv['items'][0]['gst']}%):", align="L")
    pdf.cell(35, 7, f"Rs. {total_gst:,.0f}", align="R")
    pdf.ln(1)
    pdf.set_x(18)
    pdf.set_draw_color(213, 0, 0)
    pdf.line(20 + 80 + 20 + 35, pdf.get_y() + 5, pdf.w - 20, pdf.get_y() + 5)
    pdf.ln(8)
    pdf.set_x(20 + 80 + 20 + 35)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(213, 0, 0)
    pdf.cell(35, 9, "GRAND TOTAL:", align="L")
    pdf.cell(35, 9, f"Rs. {inv['grand_total']:,.0f}", align="R")
    pdf.set_text_color(30, 30, 30)

    # ── Footer notes ─────────────────────────────────────────
    pdf.ln(14)
    pdf.set_x(20)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Place of Supply: " + inv["place_of_supply"])
    pdf.ln(6)
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(W, 5,
        "This is a computer-generated invoice. No signature required.\n"
        "Payment to be made via NEFT/RTGS to the seller's registered bank account.\n"
        "Subject to Bengaluru jurisdiction."
    )

    pdf.output(filepath)


# ═════════════════════════════════════════════════════════════════
# SUPABASE INSERT
# ═════════════════════════════════════════════════════════════════

def seed_supabase(invoices_with_filenames: list[dict]):
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    for inv in invoices_with_filenames:
        record = {
            "id":              inv["id"],
            "seller_id":       SELLER_ID,
            "invoice_number":  inv["invoice_number"],
            "invoice_date":    inv["invoice_date"],
            "grand_total":     inv["grand_total"],
            "seller_gstin":    inv["seller_gstin"],
            "seller_name":     inv["seller_name"],
            "buyer_gstin":     inv["buyer_gstin"],
            "buyer_name":      inv["buyer_name"],
            "place_of_supply": inv["place_of_supply"],
            "status":          "pending",
            "payment_status":  "unpaid",
            "file_url":        inv["file_name"],   # just the filename
            "confidence_score": 0.99,
            "validation_issues": [],
            "created_at":      datetime.utcnow().isoformat(),
        }
        try:
            client.table("invoices").insert(record).execute()
            print(f"  [Supabase] Inserted {inv['invoice_number']}")
        except Exception as e:
            # Ignore duplicate key errors so the script is safe to re-run
            if "duplicate" in str(e).lower() or "23505" in str(e):
                print(f"  [Supabase] {inv['invoice_number']} already exists, skipping.")
            else:
                print(f"  [Supabase] ERROR for {inv['invoice_number']}: {e}")


# ═════════════════════════════════════════════════════════════════
# NEO4J SEED
# ═════════════════════════════════════════════════════════════════

NEO4J_QUERY = """
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

async def seed_neo4j(invoices: list[dict]):
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    async with driver.session(database=NEO4J_DATABASE) as session:
        for inv in invoices:
            await session.run(NEO4J_QUERY, inv)
            print(f"  [Neo4j]    Seeded {inv['invoice_number']} | Rs.{inv['grand_total']:,.0f}")
    await driver.close()


# ═════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════

async def main():
    os.makedirs(DEMO_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    print("\n[STEP 1] Generating PDF invoices...")
    for inv in INVOICES:
        fname = f"{inv['id']}_{inv['invoice_number'].replace('-','')}.pdf"
        inv["file_name"] = fname

        demo_path   = os.path.join(DEMO_DIR, fname)
        upload_path = os.path.join(UPLOAD_DIR, fname)

        generate_pdf(inv, demo_path)
        shutil.copy2(demo_path, upload_path)
        print(f"  [PDF] Generated  demo_invoices/{fname}")

    print("\n[STEP 2] Seeding Supabase database...")
    seed_supabase(INVOICES)

    print("\n[STEP 3] Seeding Neo4j knowledge graph...")
    await seed_neo4j(INVOICES)

    print("\n[DONE] All 4 demo invoices are ready!")
    print(f"  PDFs stored in : {os.path.abspath(DEMO_DIR)}")
    print(f"  Upload dir     : {os.path.abspath(UPLOAD_DIR)}")
    print(f"  Buyer dashboard: open with Buyer ID = '{BUYER_GSTIN}'")


if __name__ == "__main__":
    asyncio.run(main())
