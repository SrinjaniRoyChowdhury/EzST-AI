"""
services/invoice_analyzer.py
─────────────────────────────
Uses Gemini to:
1. Extract structured invoice data from raw OCR text
2. Validate GSTIN format, tax calculations, and field completeness
"""

from typing import Any
from app.services.gemini_client import generate_json, generate_text


EXTRACTION_SYSTEM_PROMPT = """
You are an expert Indian GST invoice parser.
Extract all invoice fields from the raw text and return a structured JSON.
Follow Indian GST invoice standards (CGST/SGST for intra-state, IGST for inter-state).
If a field is not found, use null.
"""

EXTRACTION_PROMPT_TEMPLATE = """
Extract the following fields from this invoice text and return JSON:

{{
  "invoice_number": string,
  "invoice_date": "YYYY-MM-DD",
  "seller_gstin": string,
  "seller_name": string,
  "seller_address": string,
  "buyer_gstin": string,
  "buyer_name": string,
  "buyer_address": string,
  "place_of_supply": string,
  "invoice_type": "tax_invoice" | "credit_note" | "debit_note",
  "line_items": [
    {{
      "description": string,
      "hsn_sac_code": string,
      "quantity": number,
      "unit": string,
      "unit_price": number,
      "discount": number,
      "cgst_rate": number,
      "sgst_rate": number,
      "igst_rate": number
    }}
  ],
  "subtotal": number,
  "total_cgst": number,
  "total_sgst": number,
  "total_igst": number,
  "grand_total": number,
  "due_date": "YYYY-MM-DD" or null
}}

RAW INVOICE TEXT:
{raw_text}
"""

VALIDATION_SYSTEM_PROMPT = """
You are a GST compliance checker for Indian B2B invoices.
Check the extracted invoice data for errors and return a JSON validation report.
"""

VALIDATION_PROMPT_TEMPLATE = """
Validate this invoice data for GST compliance:

{invoice_json}

Check for:
1. GSTIN format (15-char alphanumeric: 2-digit state code + PAN + 3 chars)
2. Tax calculation accuracy (CGST+SGST for intra-state, IGST for inter-state)
3. Grand total consistency
4. Mandatory fields presence
5. HSN/SAC code validity (4 or 8 digits)

Return JSON:
{{
  "is_valid": boolean,
  "confidence_score": 0.0-1.0,
  "issues": [
    {{ "field": string, "message": string, "severity": "error"|"warning" }}
  ],
  "tax_type": "intra_state" | "inter_state" | "unknown"
}}
"""


async def extract_invoice_data(raw_text: str) -> dict[str, Any]:
    """
    Parse raw OCR text into a structured invoice dictionary using Gemini.
    """
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(raw_text=raw_text[:8000])  # Token cap
    return await generate_json(prompt, system_instruction=EXTRACTION_SYSTEM_PROMPT)


async def validate_invoice_data(invoice_data: dict) -> dict[str, Any]:
    """
    Validate extracted invoice data for GST compliance.
    Returns validation report with issues and confidence score.
    """
    import json
    prompt = VALIDATION_PROMPT_TEMPLATE.format(
        invoice_json=json.dumps(invoice_data, indent=2)
    )
    return await generate_json(prompt, system_instruction=VALIDATION_SYSTEM_PROMPT)


async def detect_duplicate(
    invoice_number: str,
    seller_gstin: str,
    existing_invoices: list[dict],
) -> dict[str, Any]:
    """
    Use Gemini to detect potential duplicate invoices.
    existing_invoices: list of previously stored invoice summaries.
    """
    prompt = f"""
    New invoice: number="{invoice_number}", seller_gstin="{seller_gstin}"
    
    Existing invoices (last 100):
    {existing_invoices[:100]}
    
    Is this a duplicate? Return JSON:
    {{
      "is_duplicate": boolean,
      "confidence": 0.0-1.0,
      "matching_invoice_id": string or null,
      "reason": string
    }}
    """
    return await generate_json(prompt)


async def summarize_invoice(invoice_data: dict) -> str:
    """Generate a human-readable one-paragraph summary of the invoice."""
    import json
    prompt = f"Summarize this GST invoice in 2 sentences for a business user:\n{json.dumps(invoice_data)}"
    return await generate_text(prompt, temperature=0.3)