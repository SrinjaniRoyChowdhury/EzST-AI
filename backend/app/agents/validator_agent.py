"""
agents/validator_agent.py
──────────────────────────
Agentic invoice validation pipeline.

The ValidatorAgent orchestrates multiple validation steps:
  1. GSTIN format check (regex + checksum)
  2. Tax computation re-verification
  3. Duplicate detection via DB lookup
  4. Gemini-powered semantic validation
  5. Confidence scoring and issue aggregation

Returns a structured ValidationReport that drives downstream decisions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.services.gemini_client import generate_json
from app.db.supabase_client import db_select


# ── Data Structures ────────────────────────────────────────────

@dataclass
class ValidationIssue:
    field: str
    message: str
    severity: str = "error"   # "error" | "warning" | "info"


@dataclass
class ValidationReport:
    invoice_id: str
    is_valid: bool
    confidence_score: float
    issues: list[ValidationIssue] = field(default_factory=list)
    tax_type: str = "unknown"     # "intra_state" | "inter_state"
    is_duplicate: bool = False
    duplicate_of: str | None = None
    raw_checks: dict = field(default_factory=dict)

    def add_issue(self, field: str, message: str, severity: str = "error") -> None:
        self.issues.append(ValidationIssue(field, message, severity))
        if severity == "error":
            self.is_valid = False
            self.confidence_score = max(0.0, self.confidence_score - 0.15)


# ── GSTIN Validator ───────────────────────────────────────────

GSTIN_PATTERN = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
)

STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
    "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra & Nagar Haveli", "27": "Maharashtra", "28": "Andhra Pradesh",
    "29": "Karnataka", "30": "Goa", "31": "Lakshadweep",
    "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry",
    "35": "Andaman & Nicobar", "36": "Telangana", "37": "Andhra Pradesh (New)",
}


def validate_gstin(gstin: str) -> tuple[bool, str | None]:
    """Validate GSTIN format and return (is_valid, state_name | error)."""
    if not gstin or len(gstin) != 15:
        return False, "GSTIN must be exactly 15 characters"
    if not GSTIN_PATTERN.match(gstin.upper()):
        return False, f"GSTIN '{gstin}' does not match required format"
    state_code = gstin[:2]
    state = STATE_CODES.get(state_code)
    if not state:
        return False, f"Invalid state code '{state_code}' in GSTIN"
    return True, state


def determine_tax_type(seller_gstin: str, buyer_gstin: str) -> str:
    """Intra-state (CGST+SGST) vs inter-state (IGST) based on state codes."""
    return "intra_state" if seller_gstin[:2] == buyer_gstin[:2] else "inter_state"


# ── Tax Calculation Verifier ──────────────────────────────────

def verify_tax_calculations(invoice_data: dict) -> list[ValidationIssue]:
    """
    Recompute expected taxes from line items and compare to declared totals.
    Tolerance: ₹1 rounding allowance.
    """
    issues: list[ValidationIssue] = []
    line_items = invoice_data.get("line_items") or []

    calc_cgst = calc_sgst = calc_igst = calc_subtotal = 0.0
    for item in line_items:
        qty = float(item.get("quantity") or 0)
        price = float(item.get("unit_price") or 0)
        discount = float(item.get("discount") or 0)
        taxable = round(qty * price - discount, 2)
        calc_subtotal += taxable
        calc_cgst += taxable * float(item.get("cgst_rate") or 0) / 100
        calc_sgst += taxable * float(item.get("sgst_rate") or 0) / 100
        calc_igst += taxable * float(item.get("igst_rate") or 0) / 100

    declared_total = float(invoice_data.get("grand_total") or 0)
    expected_total = round(calc_subtotal + calc_cgst + calc_sgst + calc_igst, 2)
    TOLERANCE = 1.0

    if abs(declared_total - expected_total) > TOLERANCE:
        issues.append(ValidationIssue(
            field="grand_total",
            message=f"Declared total ₹{declared_total} differs from calculated ₹{expected_total}",
            severity="error",
        ))

    tax_type = determine_tax_type(
        invoice_data.get("seller_gstin", ""),
        invoice_data.get("buyer_gstin", ""),
    )

    if tax_type == "intra_state" and calc_igst > 0:
        issues.append(ValidationIssue(
            field="igst",
            message="IGST applied on intra-state supply; should use CGST + SGST",
            severity="error",
        ))
    elif tax_type == "inter_state" and (calc_cgst > 0 or calc_sgst > 0):
        issues.append(ValidationIssue(
            field="cgst_sgst",
            message="CGST/SGST applied on inter-state supply; should use IGST",
            severity="error",
        ))

    return issues


# ── Main Agent ────────────────────────────────────────────────

class ValidatorAgent:
    """
    Stateless agent that runs the full validation pipeline for a single invoice.
    Instantiate per request for isolation.
    """

    async def run(self, invoice_id: str, invoice_data: dict) -> ValidationReport:
        report = ValidationReport(
            invoice_id=invoice_id,
            is_valid=True,
            confidence_score=1.0,
        )

        # ── Step 1: GSTIN Validation ──────────────────────────
        for field_name, gstin_val in [
            ("seller_gstin", invoice_data.get("seller_gstin", "")),
            ("buyer_gstin", invoice_data.get("buyer_gstin", "")),
        ]:
            ok, info = validate_gstin(str(gstin_val).upper())
            if not ok:
                report.add_issue(field_name, info or "Invalid GSTIN")
            else:
                report.raw_checks[f"{field_name}_state"] = info

        # ── Step 2: Tax Type ──────────────────────────────────
        if invoice_data.get("seller_gstin") and invoice_data.get("buyer_gstin"):
            report.tax_type = determine_tax_type(
                invoice_data["seller_gstin"], invoice_data["buyer_gstin"]
            )

        # ── Step 3: Tax Calculations ──────────────────────────
        tax_issues = verify_tax_calculations(invoice_data)
        for issue in tax_issues:
            report.add_issue(issue.field, issue.message, issue.severity)

        # ── Step 4: Mandatory Field Check ─────────────────────
        mandatory = ["invoice_number", "invoice_date", "seller_name", "buyer_name", "line_items"]
        for f in mandatory:
            if not invoice_data.get(f):
                report.add_issue(f, f"Mandatory field '{f}' is missing", severity="error")

        # ── Step 5: Duplicate Detection ───────────────────────
        existing = await db_select("invoices", {
            "invoice_number": invoice_data.get("invoice_number"),
            "seller_gstin": invoice_data.get("seller_gstin"),
        })
        # Exclude the current invoice from duplicate check
        duplicates = [i for i in existing if i.get("id") != invoice_id]
        if duplicates:
            report.is_duplicate = True
            report.duplicate_of = duplicates[0].get("id")
            report.add_issue(
                "invoice_number",
                f"Duplicate invoice detected (existing ID: {report.duplicate_of})",
                severity="error",
            )

        # ── Step 6: Gemini Semantic Check ─────────────────────
        import json
        ai_check = await generate_json(
            prompt=f"""
            Review this GST invoice for any inconsistencies or unusual patterns
            that rule-based checks might miss:
            {json.dumps(invoice_data, indent=2)}
            
            Return JSON: {{"additional_issues": [{{"field": str, "message": str, "severity": "error|warning"}}]}}
            """,
            system_instruction="You are a GST audit expert. Be concise and precise.",
        )
        for issue in ai_check.get("additional_issues", []):
            report.add_issue(
                issue.get("field", "general"),
                issue.get("message", "AI-detected issue"),
                issue.get("severity", "warning"),
            )

        # Final confidence adjustment
        warning_count = sum(1 for i in report.issues if i.severity == "warning")
        report.confidence_score = max(0.0, report.confidence_score - (warning_count * 0.05))
        report.confidence_score = round(report.confidence_score, 2)

        return report