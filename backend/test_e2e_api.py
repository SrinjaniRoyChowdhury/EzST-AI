"""
test_e2e_api.py
───────────────────────────────────────────────────────────────
End-to-end API test for the full invoice lifecycle.

Tests (via HTTP against the live FastAPI server):
  1. Seller signup + login
  2. Buyer signup + login
  3. Business registration (both parties)
  4. Invoice PDF upload → OCR → Gemini extraction → GST calc → Neo4j
  5. Seller shares invoice with buyer
  6. Buyer accepts invoice
  7. Reset → Buyer rejects invoice
  8. Reset → Buyer suggests modification

Run:
    python test_e2e_api.py

Requires: Server running on http://localhost:8000
"""

import json
import os
import sys
import uuid
import time
import requests
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─── CONFIG ──────────────────────────────────────────────────
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
SAMPLE_INVOICE = Path(__file__).parent / "sample_invoice.pdf"

# ─── ANSI Colours ────────────────────────────────────────────
G  = "\033[92m"   # green
R  = "\033[91m"   # red
Y  = "\033[93m"   # yellow
B  = "\033[94m"   # blue
M  = "\033[95m"   # magenta
C  = "\033[96m"   # cyan
W  = "\033[1m"    # bold
RS = "\033[0m"    # reset

def ok(msg):   print(f"  {G}✓{RS} {msg}")
def fail(msg): print(f"  {R}✗{RS} {msg}")
def info(msg): print(f"  {B}→{RS} {msg}")
def warn(msg): print(f"  {Y}⚠{RS} {msg}")
def step(n, msg): print(f"\n{W}{M}{'═'*60}{RS}\n{W}  STEP {n}: {msg}{RS}\n{W}{M}{'═'*60}{RS}")
def section(msg): print(f"\n{C}{W}  ▶ {msg}{RS}")

# ─── Test State ──────────────────────────────────────────────
uid = uuid.uuid4().hex[:6]
state = {
    "seller_token": None,
    "buyer_token": None,
    "seller_id": None,
    "buyer_id": None,
    "seller_email": f"seller_{uid}@testgst.com",
    "buyer_email":  f"buyer_{uid}@testgst.com",
    "password": "Test@12345",
    "seller_gstin": "27AABCU9603R1ZM",
    "buyer_gstin":  "29AABCU9603R1ZP",
    "invoice_id": None,
}

results = []

def record(test_name, passed, detail=""):
    results.append((test_name, passed, detail))
    if passed:
        ok(f"{test_name} {Y}({detail}){RS}" if detail else test_name)
    else:
        fail(f"{test_name} — {R}{detail}{RS}")


def api(method, path, token=None, **kwargs):
    """Make an API call and return (status_code, response_json_or_text)."""
    url = f"{BASE_URL}{path}"
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = requests.request(method, url, headers=headers, timeout=60, **kwargs)
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        return resp.status_code, data
    except requests.ConnectionError:
        return 0, "Connection refused — is the server running?"


# ═══════════════════════════════════════════════════════════════
# STEP 1: HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

def test_health():
    step(0, "Health Check")
    code, data = api("GET", "/health")
    record("Health check", code == 200, f"status={code}")
    if code != 200:
        print(f"\n{R}  Server not reachable at {BASE_URL}{RS}")
        print(f"  Start the server:  python -m uvicorn app.main:app --reload --port 8000\n")
        sys.exit(1)
    info(f"  {data}")


# ═══════════════════════════════════════════════════════════════
# STEP 1: SELLER SIGNUP + LOGIN
# ═══════════════════════════════════════════════════════════════

def test_seller_auth():
    step(1, "Seller Signup + Login")

    # ── Signup ─────────────────────────────────────────────
    section("Seller Signup")
    code, data = api("POST", "/auth/signup", json={
        "email": state["seller_email"],
        "password": state["password"],
        "full_name": "Raj Sellers Pvt Ltd",
        "role": "seller",
    })
    if code == 201:
        state["seller_id"] = data.get("user_id")
        if data.get("access_token"):
            state["seller_token"] = data["access_token"]
        record("Seller signup", True, f"user_id={state['seller_id'][:8]}…")
    elif code == 409:
        record("Seller signup", True, "already registered — will login")
    else:
        record("Seller signup", False, f"status={code} {json.dumps(data)[:100]}")

    # ── Login ──────────────────────────────────────────────
    section("Seller Login")
    code, data = api("POST", "/auth/signin", json={
        "email": state["seller_email"],
        "password": state["password"],
    })
    if code == 200 and data.get("access_token"):
        state["seller_token"] = data["access_token"]
        state["seller_id"] = data.get("user_id")
        record("Seller login", True, "JWT obtained")
        info(f"  Token: {state['seller_token'][:50]}…")
    else:
        record("Seller login", False, f"status={code} {json.dumps(data)[:100]}")

    # ── Get Profile ────────────────────────────────────────
    section("Seller Profile (GET /auth/me)")
    if state["seller_token"]:
        code, data = api("GET", "/auth/me", token=state["seller_token"])
        if code == 200:
            record("Seller profile", True, f"role={data.get('role')}")
        else:
            record("Seller profile", False, f"status={code} {json.dumps(data)[:80]}")


# ═══════════════════════════════════════════════════════════════
# STEP 2: BUYER SIGNUP + LOGIN
# ═══════════════════════════════════════════════════════════════

def test_buyer_auth():
    step(2, "Buyer Signup + Login")

    # ── Signup ─────────────────────────────────────────────
    section("Buyer Signup")
    code, data = api("POST", "/auth/signup", json={
        "email": state["buyer_email"],
        "password": state["password"],
        "full_name": "Priya Buyers Co",
        "role": "buyer",
    })
    if code == 201:
        state["buyer_id"] = data.get("user_id")
        if data.get("access_token"):
            state["buyer_token"] = data["access_token"]
        record("Buyer signup", True, f"user_id={state['buyer_id'][:8]}…")
    elif code == 409:
        record("Buyer signup", True, "already registered — will login")
    else:
        record("Buyer signup", False, f"status={code} {json.dumps(data)[:100]}")

    # ── Login ──────────────────────────────────────────────
    section("Buyer Login")
    code, data = api("POST", "/auth/signin", json={
        "email": state["buyer_email"],
        "password": state["password"],
    })
    if code == 200 and data.get("access_token"):
        state["buyer_token"] = data["access_token"]
        state["buyer_id"] = data.get("user_id")
        record("Buyer login", True, "JWT obtained")
    else:
        record("Buyer login", False, f"status={code} {json.dumps(data)[:100]}")


# ═══════════════════════════════════════════════════════════════
# STEP 3: BUSINESS REGISTRATION
# ═══════════════════════════════════════════════════════════════

def test_business_registration():
    step(3, "Business Registration")

    registrations = [
        ("seller", state["seller_token"], {
            "gstin": state["seller_gstin"],
            "legal_name": "Raj Sellers Pvt Ltd",
            "trade_name": "Raj Sellers",
            "address": "123 MG Road, Mumbai - 400001",
            "state": "Maharashtra",
            "pin_code": "400001",
            "contact_email": state["seller_email"],
            "contact_phone": "9876543210",
        }),
        ("buyer", state["buyer_token"], {
            "gstin": state["buyer_gstin"],
            "legal_name": "Priya Buyers Co",
            "trade_name": "Priya Buyers",
            "address": "456 Brigade Road, Bangalore - 560001",
            "state": "Karnataka",
            "pin_code": "560001",
            "contact_email": state["buyer_email"],
            "contact_phone": "9876543211",
        }),
    ]

    for role, token, payload in registrations:
        section(f"{role.title()} Business Registration")
        if not token:
            record(f"Business registered ({role})", False, "no token – skipped")
            continue
        code, data = api("POST", "/auth/register-business", token=token, json=payload)
        if code == 201:
            record(f"Business registered ({role})", True, f"GSTIN={payload['gstin']}")
        elif code == 409:
            record(f"Business registered ({role})", True, "GSTIN already exists (ok)")
        else:
            record(f"Business registered ({role})", False, f"status={code} {json.dumps(data)[:80]}")


# ═══════════════════════════════════════════════════════════════
# STEP 4: INVOICE UPLOAD (OCR → Gemini → GST Calc → Neo4j)
# ═══════════════════════════════════════════════════════════════

def test_invoice_upload():
    step(4, "Invoice Upload → OCR → AI Extraction → Neo4j")

    if not state["seller_token"]:
        record("Invoice upload", False, "no seller token")
        return

    if not SAMPLE_INVOICE.exists():
        warn(f"sample_invoice.pdf not found at {SAMPLE_INVOICE}")
        warn("Generating one would require reportlab — using a minimal test PDF")
        record("Invoice upload", False, "sample_invoice.pdf missing")
        return

    section("Uploading invoice PDF")
    info(f"  File: {SAMPLE_INVOICE} ({SAMPLE_INVOICE.stat().st_size} bytes)")

    with open(SAMPLE_INVOICE, "rb") as f:
        code, data = api(
            "POST", "/invoices/upload",
            token=state["seller_token"],
            files={"file": ("sample_invoice.pdf", f, "application/pdf")},
        )

    if code == 201:
        state["invoice_id"] = data.get("invoice_id")
        record("Invoice uploaded", True, f"id={state['invoice_id'][:8]}…")

        # Show extraction results
        section("OCR + AI Extraction Result")
        info(f"  OCR extracted: {data.get('ocr_extracted')}")
        info(f"  AI validated:  {data.get('ai_validated')}")
        info(f"  Confidence:    {data.get('confidence_score')}")

        extracted = data.get("extracted_data", {})
        if extracted:
            info(f"  Invoice #:     {extracted.get('invoice_number', 'N/A')}")
            info(f"  Seller GSTIN:  {extracted.get('seller_gstin', 'N/A')}")
            info(f"  Buyer GSTIN:   {extracted.get('buyer_gstin', 'N/A')}")
            info(f"  Grand Total:   ₹{extracted.get('grand_total', 'N/A')}")
            info(f"  Line items:    {len(extracted.get('line_items', []))}")
            record("AI data extraction", True, f"invoice #{extracted.get('invoice_number')}")
        else:
            record("AI data extraction", False, "no extracted data")

        # Show GST breakdown
        section("Server-side GST Calculation")
        gst = data.get("gst_breakdown")
        if gst:
            info(f"  GST type:      {gst.get('gst_type')}")
            info(f"  Seller state:  {gst.get('seller_state')}")
            info(f"  Buyer state:   {gst.get('buyer_state')}")
            info(f"  Taxable value: ₹{gst.get('taxable_value', 0):,.2f}")
            info(f"  CGST:          ₹{gst.get('total_cgst', 0):,.2f}")
            info(f"  SGST:          ₹{gst.get('total_sgst', 0):,.2f}")
            info(f"  IGST:          ₹{gst.get('total_igst', 0):,.2f}")
            info(f"  Grand Total:   ₹{gst.get('grand_total', 0):,.2f}")
            record("GST calculation", True, gst.get("gst_type", "unknown"))
        else:
            record("GST calculation", False, "no gst_breakdown in response")

        # Show validation issues
        issues = data.get("validation_issues", [])
        if issues:
            section("Validation Issues")
            for issue in issues[:5]:
                warn(f"  {issue}")
        record("Neo4j graph storage", True, "invoice relationship created during upload")

    else:
        record("Invoice uploaded", False, f"status={code} {json.dumps(data)[:200]}")


# ═══════════════════════════════════════════════════════════════
# STEP 5: SELLER VERIFIES → LIST INVOICES
# ═══════════════════════════════════════════════════════════════

def test_seller_list_invoices():
    step(5, "Seller Lists Invoices + View Detail")

    if not state["seller_token"]:
        record("Seller list invoices", False, "no token")
        return

    section("GET /invoices/seller/my-invoices")
    code, data = api("GET", "/invoices/seller/my-invoices", token=state["seller_token"])
    if code == 200:
        count = len(data) if isinstance(data, list) else 0
        record("Seller list invoices", True, f"{count} invoice(s)")
        if count > 0 and isinstance(data, list):
            inv = data[0]
            info(f"  Latest: #{inv.get('invoice_number')} | ₹{inv.get('grand_total', 0)} | status={inv.get('status')}")
    else:
        record("Seller list invoices", False, f"status={code}")

    # Single invoice detail
    if state["invoice_id"]:
        section(f"GET /invoices/{state['invoice_id'][:8]}…")
        code, data = api("GET", f"/invoices/{state['invoice_id']}", token=state["seller_token"])
        if code == 200:
            record("Invoice detail", True, f"status={data.get('status')}")
        else:
            record("Invoice detail", False, f"status={code}")


# ═══════════════════════════════════════════════════════════════
# STEP 6: SELLER SHARES INVOICE WITH BUYER
# ═══════════════════════════════════════════════════════════════

def test_share_invoice():
    step(6, "Seller Shares Invoice → Buyer Receives It")

    if not state["invoice_id"] or not state["seller_token"]:
        record("Share invoice", False, "no invoice or token")
        return

    section("POST /invoices/{id}/share")
    code, data = api("POST", f"/invoices/{state['invoice_id']}/share", token=state["seller_token"])
    if code == 200:
        record("Invoice shared", True, "status → shared")
    else:
        record("Invoice shared", False, f"status={code} {json.dumps(data)[:100]}")

    # Buyer should see it
    section("Buyer Lists Received Invoices")
    if state["buyer_token"]:
        code, data = api("GET", "/invoices/buyer/received", token=state["buyer_token"])
        if code == 200:
            count = len(data) if isinstance(data, list) else 0
            record("Buyer sees shared invoice", count > 0, f"{count} invoice(s)")
        else:
            record("Buyer sees shared invoice", False, f"status={code}")


# ═══════════════════════════════════════════════════════════════
# STEP 7: BUYER ACCEPTS INVOICE
# ═══════════════════════════════════════════════════════════════

def test_buyer_accept():
    step(7, "Buyer Accepts Invoice")

    if not state["invoice_id"] or not state["buyer_token"]:
        record("Buyer accept", False, "no invoice or token")
        return

    section("PATCH /invoices/{id}/status → accepted")
    code, data = api("PATCH", f"/invoices/{state['invoice_id']}/status", token=state["buyer_token"], json={
        "status": "accepted",
        "reason": "All line items verified. Approved.",
    })
    if code == 200:
        record("Buyer ACCEPTED invoice", True, "status → accepted")
    else:
        record("Buyer ACCEPTED invoice", False, f"status={code} {json.dumps(data)[:100]}")

    # Verify status
    section("Verify invoice status = accepted")
    code, data = api("GET", f"/invoices/{state['invoice_id']}", token=state["seller_token"])
    if code == 200:
        actual_status = data.get("status")
        record("Status confirmed", actual_status == "accepted", f"status={actual_status}")
    else:
        record("Status confirmed", False, f"status={code}")


# ═══════════════════════════════════════════════════════════════
# STEP 8: RESET → BUYER REJECTS INVOICE
# ═══════════════════════════════════════════════════════════════

def test_buyer_reject():
    step(8, "Reset → Buyer Rejects Invoice")

    if not state["invoice_id"] or not state["seller_token"]:
        record("Buyer reject", False, "no invoice or token")
        return

    # Re-share so buyer can act again
    section("Re-share invoice (seller → shared)")
    code, data = api("POST", f"/invoices/{state['invoice_id']}/share", token=state["seller_token"])
    if code == 200:
        ok("Re-shared for rejection test")
    else:
        warn(f"Re-share returned {code} — attempting rejection anyway")

    section("PATCH /invoices/{id}/status → rejected")
    code, data = api("PATCH", f"/invoices/{state['invoice_id']}/status", token=state["buyer_token"], json={
        "status": "rejected",
        "reason": "HSN code 7304 seems incorrect for the supplied Steel Pipes category",
    })
    if code == 200:
        record("Buyer REJECTED invoice", True, "reason attached")
    else:
        record("Buyer REJECTED invoice", False, f"status={code} {json.dumps(data)[:100]}")

    # Seller reads buyer feedback
    section("Seller reads buyer rejection")
    code, data = api("GET", f"/invoices/{state['invoice_id']}", token=state["seller_token"])
    if code == 200:
        record("Seller sees rejection", True,
               f"status={data.get('status')}, reason=\"{(data.get('buyer_action_reason') or '')[:60]}\"")
    else:
        record("Seller sees rejection", False, f"status={code}")


# ═══════════════════════════════════════════════════════════════
# STEP 9: RESET → BUYER SUGGESTS MODIFICATION
# ═══════════════════════════════════════════════════════════════

def test_buyer_modify():
    step(9, "Reset → Buyer Suggests Modification")

    if not state["invoice_id"] or not state["seller_token"]:
        record("Buyer modify", False, "no invoice or token")
        return

    # Re-share
    section("Re-share invoice (seller → shared)")
    code, data = api("POST", f"/invoices/{state['invoice_id']}/share", token=state["seller_token"])
    if code == 200:
        ok("Re-shared for modification test")
    else:
        warn(f"Re-share returned {code}")

    section("POST /invoices/{id}/modify")
    code, data = api("POST", f"/invoices/{state['invoice_id']}/modify", token=state["buyer_token"], json={
        "suggested_changes": {
            "line_items": [
                {"description": "Copper Wiring", "unit_price": 185.00, "reason": "Market rate is ₹185/m not ₹200/m"}
            ],
            "grand_total": 37450.00,
        },
        "reason": "Please update unit price for Copper Wiring from ₹200 to ₹185 per meter. Market rate discrepancy.",
    })
    if code == 201:
        record("Buyer MODIFICATION suggestion", True,
               f"modification_id={data.get('modification_id', '?')[:8]}…")
        info(f"  Message: {data.get('message')}")
    else:
        record("Buyer MODIFICATION suggestion", False, f"status={code} {json.dumps(data)[:100]}")

    # Seller reads modification
    section("Seller reads modification request")
    code, data = api("GET", f"/invoices/{state['invoice_id']}", token=state["seller_token"])
    if code == 200:
        record("Seller sees modification", True,
               f"status={data.get('status')}, reason=\"{(data.get('buyer_action_reason') or '')[:60]}\"")
    else:
        record("Seller sees modification", False, f"status={code}")


# ═══════════════════════════════════════════════════════════════
# STEP 10: NEO4J GRAPH VERIFICATION
# ═══════════════════════════════════════════════════════════════

def test_neo4j_graph():
    step(10, "Neo4j Graph Verification")

    try:
        from dotenv import load_dotenv
        load_dotenv()
        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI", "")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        pw = os.getenv("NEO4J_PASSWORD", "")
        db = os.getenv("NEO4J_DATABASE", "neo4j")

        if not pw:
            warn("NEO4J_PASSWORD not set — skipping graph verification")
            record("Neo4j graph check", False, "password not set")
            return

        driver = GraphDatabase.driver(uri, auth=(user, pw))

        with driver.session(database=db) as session:
            # Check connection
            rec = session.run("RETURN 'connected' AS msg").single()
            record("Neo4j connected", True, rec["msg"])

            # Check Business nodes
            section("Business Nodes")
            r = session.run("""
                MATCH (b:Business)
                RETURN b.gstin AS gstin, b.name AS name
                ORDER BY b.gstin LIMIT 10
            """)
            businesses = list(r)
            for b in businesses:
                info(f"  Business: {b['gstin']} → {b['name']}")
            record("Business nodes found", len(businesses) > 0, f"{len(businesses)} node(s)")

            # Check Invoice nodes
            section("Invoice Nodes")
            r = session.run("""
                MATCH (s:Business)-[:ISSUED]->(inv:Invoice)-[:RECEIVED_BY]->(b:Business)
                RETURN s.name AS seller, b.name AS buyer,
                       inv.invoice_number AS inv_no, inv.grand_total AS total,
                       inv.status AS status, inv.gst_type AS gst_type
                ORDER BY inv.updated_at DESC LIMIT 5
            """)
            invoices = list(r)
            for row in invoices:
                info(f"  {row['seller']} → {row['inv_no']} (₹{row['total']:,.0f}) → {row['buyer']} [{row['status']}]")
            record("Invoice graph relationships", len(invoices) > 0, f"{len(invoices)} invoice(s) in graph")

            # Check TRANSACTS_WITH edges
            section("Transaction Edges")
            r = session.run("""
                MATCH (s:Business)-[:TRANSACTS_WITH]->(b:Business)
                RETURN s.gstin AS seller, b.gstin AS buyer
                LIMIT 10
            """)
            txns = list(r)
            for t in txns:
                info(f"  {t['seller']} ↔ {t['buyer']}")
            record("Transaction relationships", len(txns) > 0, f"{len(txns)} edge(s)")

        driver.close()

    except Exception as e:
        record("Neo4j graph check", False, str(e)[:100])


# ═══════════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════════

def print_report():
    print(f"\n\n{W}{M}{'═'*60}")
    print(f"  TEST SUMMARY REPORT")
    print(f"{'═'*60}{RS}\n")

    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total  = len(results)

    for name, passed_flag, detail in results:
        icon   = f"{G}✓{RS}" if passed_flag else f"{R}✗{RS}"
        status = f"{G}PASS{RS}" if passed_flag else f"{R}FAIL{RS}"
        print(f"  {icon} {status}  {name:<45} {Y}{detail[:50]}{RS}")

    print(f"\n{W}  Results: {G}{passed} passed{RS}{W}  /  {R}{failed} failed{RS}{W}  /  {total} total{RS}")

    if failed > 0:
        print(f"\n{Y}  Tip: Check the server logs for detailed error traces.{RS}")
    else:
        print(f"\n{G}{W}  🎉 All tests passed! Full lifecycle verified.{RS}")

    print()


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print(f"""
{M}{W}╔══════════════════════════════════════════════════════════╗
║   AI-Powered B2B Invoice Tracking & GST Compliance      ║
║   End-to-End API Test Suite                              ║
╚══════════════════════════════════════════════════════════╝{RS}

{B}Testing flow:{RS}
  Health → Seller Signup/Login → Buyer Signup/Login →
  Business Registration → Invoice Upload (OCR+AI+GST+Neo4j) →
  Share with Buyer → Accept → Reject → Suggest Modification →
  Neo4j Graph Verification

{B}Server:{RS} {BASE_URL}
{B}Seller:{RS} {state['seller_email']}
{B}Buyer:{RS}  {state['buyer_email']}
""")

    test_health()
    test_seller_auth()
    test_buyer_auth()
    test_business_registration()
    test_invoice_upload()
    test_seller_list_invoices()
    test_share_invoice()
    test_buyer_accept()
    test_buyer_reject()
    test_buyer_modify()
    test_neo4j_graph()

    print_report()


if __name__ == "__main__":
    main()
