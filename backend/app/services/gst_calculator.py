"""
services/gst_calculator.py
───────────────────────────
Server-side Indian GST calculation engine.

Rules implemented:
  • Intra-state supply  → CGST + SGST  (equal split of the GST rate)
  • Inter-state supply  → IGST only
  • State code is the first 2 digits of a 15-char GSTIN (01–37)
  • If GSTINs are missing or malformed → treat as inter-state (safe default)

Usage:
    from app.services.gst_calculator import calculate_invoice_gst
    gst = calculate_invoice_gst(extracted_data)
"""

from __future__ import annotations

from typing import Any


# ── Indian state codes ────────────────────────────────────────
VALID_STATE_CODES = {
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
    "31", "32", "33", "34", "35", "36", "37",
}

STATE_CODE_MAP = {
    "01": "Jammu & Kashmir",    "02": "Himachal Pradesh",
    "03": "Punjab",             "04": "Chandigarh",
    "05": "Uttarakhand",        "06": "Haryana",
    "07": "Delhi",              "08": "Rajasthan",
    "09": "Uttar Pradesh",      "10": "Bihar",
    "11": "Sikkim",             "12": "Arunachal Pradesh",
    "13": "Nagaland",           "14": "Manipur",
    "15": "Mizoram",            "16": "Tripura",
    "17": "Meghalaya",          "18": "Assam",
    "19": "West Bengal",        "20": "Jharkhand",
    "21": "Odisha",             "22": "Chhattisgarh",
    "23": "Madhya Pradesh",     "24": "Gujarat",
    "25": "Daman & Diu",        "26": "Dadra & Nagar Haveli",
    "27": "Maharashtra",        "28": "Andhra Pradesh (old)",
    "29": "Karnataka",          "30": "Goa",
    "31": "Lakshadweep",        "32": "Kerala",
    "33": "Tamil Nadu",         "34": "Puducherry",
    "35": "Andaman & Nicobar",  "36": "Telangana",
    "37": "Andhra Pradesh",
}


# ── State code extraction ─────────────────────────────────────

def get_state_code(gstin: str | None) -> str | None:
    """
    Extract and validate the 2-digit state code from a GSTIN.

    Returns the state code string ("07", "27", …) or None if invalid.
    """
    if not gstin or len(gstin) < 2:
        return None
    code = gstin[:2]
    return code if code in VALID_STATE_CODES else None


def determine_tax_type(seller_gstin: str | None, buyer_gstin: str | None) -> str:
    """
    Compare state codes to determine supply type.

    Returns:
        "intra_state" — seller and buyer are in the same state → CGST + SGST
        "inter_state" — different states / unknown              → IGST
    """
    seller_state = get_state_code(seller_gstin)
    buyer_state = get_state_code(buyer_gstin)

    if seller_state and buyer_state and seller_state == buyer_state:
        return "intra_state"
    return "inter_state"


# ── Per-line-item calculation ─────────────────────────────────

def calculate_line_item_gst(item: dict, tax_type: str) -> dict:
    """
    Calculate GST for a single line item.

    Input dict (from Gemini extraction):
        quantity, unit_price, discount, cgst_rate, sgst_rate, igst_rate

    Returns the item dict enriched with calculated amounts:
        taxable_amount, cgst_amount, sgst_amount, igst_amount, total_tax, line_total
    """
    qty = float(item.get("quantity") or 0)
    price = float(item.get("unit_price") or 0)
    discount = float(item.get("discount") or 0)

    # Determine GST rate from extracted data or fall back to common rate
    if tax_type == "intra_state":
        # CGST+SGST split — if Gemini extracted them separately, use those
        # Otherwise derive from igst_rate / 2
        cgst_rate = float(item.get("cgst_rate") or 0)
        sgst_rate = float(item.get("sgst_rate") or 0)
        igst_rate = 0.0

        # If only igst_rate came from Gemini (inter-state invoice misidentified), split it
        if cgst_rate == 0 and sgst_rate == 0:
            raw_igst = float(item.get("igst_rate") or 0)
            cgst_rate = raw_igst / 2
            sgst_rate = raw_igst / 2

    else:  # inter_state
        igst_rate = float(item.get("igst_rate") or 0)

        # If only CGST+SGST came from Gemini, merge into IGST
        if igst_rate == 0:
            igst_rate = float(item.get("cgst_rate") or 0) + float(item.get("sgst_rate") or 0)
        cgst_rate = 0.0
        sgst_rate = 0.0

    taxable = round((qty * price) - discount, 2)
    cgst_amt = round(taxable * cgst_rate / 100, 2)
    sgst_amt = round(taxable * sgst_rate / 100, 2)
    igst_amt = round(taxable * igst_rate / 100, 2)
    total_tax = round(cgst_amt + sgst_amt + igst_amt, 2)

    return {
        **item,
        "taxable_amount": taxable,
        "cgst_rate":      round(cgst_rate, 2),
        "sgst_rate":      round(sgst_rate, 2),
        "igst_rate":      round(igst_rate, 2),
        "cgst_amount":    cgst_amt,
        "sgst_amount":    sgst_amt,
        "igst_amount":    igst_amt,
        "total_tax":      total_tax,
        "line_total":     round(taxable + total_tax, 2),
    }


# ── Full invoice GST calculation ──────────────────────────────

def calculate_invoice_gst(extracted_data: dict[str, Any]) -> dict[str, Any]:
    """
    Run the complete GST calculation on a Gemini-extracted invoice dict.

    Returns a gst_breakdown dict:
    {
        "gst_type":       "intra_state" | "inter_state",
        "seller_state":   "Maharashtra" | None,
        "buyer_state":    "Delhi" | None,
        "line_items":     [...enriched line items with per-item tax amounts...],
        "taxable_value":  float,
        "total_cgst":     float,
        "total_sgst":     float,
        "total_igst":     float,
        "total_tax":      float,
        "grand_total":    float,
    }
    """
    seller_gstin = extracted_data.get("seller_gstin") or ""
    buyer_gstin = extracted_data.get("buyer_gstin") or ""

    tax_type = determine_tax_type(seller_gstin, buyer_gstin)

    seller_code = get_state_code(seller_gstin)
    buyer_code = get_state_code(buyer_gstin)

    raw_items: list[dict] = extracted_data.get("line_items") or []
    calculated_items = [calculate_line_item_gst(item, tax_type) for item in raw_items]

    taxable_value = round(sum(i["taxable_amount"] for i in calculated_items), 2)
    total_cgst = round(sum(i["cgst_amount"] for i in calculated_items), 2)
    total_sgst = round(sum(i["sgst_amount"] for i in calculated_items), 2)
    total_igst = round(sum(i["igst_amount"] for i in calculated_items), 2)
    total_tax = round(total_cgst + total_sgst + total_igst, 2)
    grand_total = round(taxable_value + total_tax, 2)

    return {
        "gst_type":      tax_type,
        "seller_state":  STATE_CODE_MAP.get(seller_code, None) if seller_code else None,
        "buyer_state":   STATE_CODE_MAP.get(buyer_code, None) if buyer_code else None,
        "line_items":    calculated_items,
        "taxable_value": taxable_value,
        "total_cgst":    total_cgst,
        "total_sgst":    total_sgst,
        "total_igst":    total_igst,
        "total_tax":     total_tax,
        "grand_total":   grand_total,
    }
