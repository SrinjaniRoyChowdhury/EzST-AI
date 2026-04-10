"""
agents/risk_agent.py
─────────────────────
Risk Detection Agent – combines graph analytics (Neo4j) with
Gemini reasoning to flag suspicious invoice patterns and businesses.

Risk signals detected:
  1. Circular transaction chains (carousel fraud)
  2. Invoice splitting (e-way bill evasion)
  3. High-frequency invoicing (fake invoice generation)
  4. Sudden spike in transaction volume
  5. Unverified GSTIN networks
  6. AI-powered anomaly narration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.graph.graph_queries import (
    detect_circular_transactions,
    detect_high_frequency_invoicing,
    find_split_invoice_pattern,
    get_risk_score,
)
from app.services.gemini_client import generate_text
from app.db.supabase_client import db_select


# ── Risk Levels ───────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW      = "low"       # Score 0.0–0.3
    MEDIUM   = "medium"    # Score 0.31–0.6
    HIGH     = "high"      # Score 0.61–0.8
    CRITICAL = "critical"  # Score 0.81–1.0

    @classmethod
    def from_score(cls, score: float) -> "RiskLevel":
        if score <= 0.3:  return cls.LOW
        if score <= 0.6:  return cls.MEDIUM
        if score <= 0.8:  return cls.HIGH
        return cls.CRITICAL


@dataclass
class RiskSignal:
    signal_type: str
    description: str
    severity: RiskLevel
    evidence: dict = field(default_factory=dict)


@dataclass
class RiskReport:
    gstin: str
    risk_score: float
    risk_level: RiskLevel
    signals: list[RiskSignal] = field(default_factory=list)
    ai_narrative: str = ""
    recommended_actions: list[str] = field(default_factory=list)

    def add_signal(self, signal_type: str, description: str,
                   severity: RiskLevel, evidence: dict | None = None) -> None:
        self.signals.append(RiskSignal(signal_type, description, severity, evidence or {}))


# ── Risk Agent ────────────────────────────────────────────────

class RiskAgent:
    """
    Stateless agent that evaluates fraud/compliance risk for a GSTIN.
    Run on-demand or as a scheduled background task.
    """

    async def analyse(self, gstin: str, seller_gstin: str | None = None) -> RiskReport:
        """
        Full risk analysis pipeline for a given GSTIN.

        Args:
            gstin: The business GSTIN to evaluate.
            seller_gstin: Optional counterparty GSTIN for pair-level checks.

        Returns:
            RiskReport with score, signals, and AI narrative.
        """
        # ── Base score from graph ─────────────────────────────
        graph_risk = await get_risk_score(gstin)
        base_score = float(graph_risk.get("risk_score", 0.0))
        signals_data = graph_risk.get("signals", {})

        report = RiskReport(
            gstin=gstin,
            risk_score=base_score,
            risk_level=RiskLevel.from_score(base_score),
        )

        # ── Signal 1: Circular Transactions ──────────────────
        circular = await detect_circular_transactions(gstin)
        if circular:
            for cycle in circular[:3]:  # Cap output
                report.add_signal(
                    signal_type="circular_transaction",
                    description=f"Circular invoice chain detected involving {len(cycle.get('cycle_gstins', []))} entities",
                    severity=RiskLevel.CRITICAL,
                    evidence={"cycle": cycle.get("cycle_gstins", [])},
                )
            report.risk_score = min(1.0, report.risk_score + 0.3)

        # ── Signal 2: High Frequency Invoicing ───────────────
        high_freq = await detect_high_frequency_invoicing(gstin)
        if high_freq:
            for hf in high_freq:
                report.add_signal(
                    signal_type="high_frequency_invoicing",
                    description=f"{hf.get('invoice_count')} invoices issued in 7 days (threshold: 50)",
                    severity=RiskLevel.HIGH,
                    evidence={"invoice_count": hf.get("invoice_count")},
                )
            report.risk_score = min(1.0, report.risk_score + 0.2)

        # ── Signal 3: Invoice Splitting (if counterparty known) ──
        if seller_gstin:
            splits = await find_split_invoice_pattern(seller_gstin, gstin)
            if splits:
                for split in splits[:3]:
                    report.add_signal(
                        signal_type="invoice_splitting",
                        description=(
                            f"{split.get('invoice_count')} invoices on {split.get('date')} "
                            f"totalling ₹{split.get('daily_total')} (possible e-way bill evasion)"
                        ),
                        severity=RiskLevel.HIGH,
                        evidence=split,
                    )
                report.risk_score = min(1.0, report.risk_score + 0.15)

        # ── Signal 4: DB-level anomaly check ─────────────────
        invoices = await db_select("invoices", {"seller_gstin": gstin})
        rejected_count = sum(1 for i in invoices if i.get("status") == "rejected")
        if rejected_count > 5:
            report.add_signal(
                signal_type="high_rejection_rate",
                description=f"{rejected_count} invoices have been rejected by buyers",
                severity=RiskLevel.MEDIUM,
                evidence={"rejected_count": rejected_count},
            )
            report.risk_score = min(1.0, report.risk_score + 0.1)

        # ── Final Risk Level ──────────────────────────────────
        report.risk_score = round(report.risk_score, 2)
        report.risk_level = RiskLevel.from_score(report.risk_score)

        # ── AI Narrative ──────────────────────────────────────
        report.ai_narrative = await self._generate_narrative(report)
        report.recommended_actions = await self._recommend_actions(report)

        return report

    async def _generate_narrative(self, report: RiskReport) -> str:
        """Ask Gemini to summarise the risk findings in plain English."""
        signal_text = "\n".join(
            f"- [{s.severity.upper()}] {s.signal_type}: {s.description}"
            for s in report.signals
        ) or "No specific signals detected."

        return await generate_text(
            f"""
            Summarise the following GST fraud risk signals for GSTIN {report.gstin}
            in 2–3 sentences for a compliance officer:
            
            Risk Score: {report.risk_score}/1.0 ({report.risk_level})
            Signals:
            {signal_text}
            
            Be factual. Do not speculate beyond the evidence.
            """,
            temperature=0.2,
        )

    async def _recommend_actions(self, report: RiskReport) -> list[str]:
        """Return a list of recommended compliance actions based on risk level."""
        actions_map: dict[RiskLevel, list[str]] = {
            RiskLevel.LOW: [
                "Continue regular invoice reconciliation",
                "File GST returns on time",
            ],
            RiskLevel.MEDIUM: [
                "Manually verify the last 30 invoices",
                "Cross-check ITC claims against GSTR-2A",
                "Ensure all e-way bills are generated for supplies > ₹50,000",
            ],
            RiskLevel.HIGH: [
                "Initiate internal GST audit",
                "Freeze ITC claims pending review",
                "Verify GSTIN of all counterparties",
                "Report suspicious patterns to GST compliance team",
            ],
            RiskLevel.CRITICAL: [
                "URGENT: Escalate to senior compliance officer",
                "Engage a GST practitioner immediately",
                "Do NOT process new invoices with flagged entities",
                "Prepare documentation for potential GST authority scrutiny",
                "Consider voluntary disclosure if errors were unintentional",
            ],
        }
        return actions_map.get(report.risk_level, [])