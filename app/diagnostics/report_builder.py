"""Assembles a DiagnosticReport from a snapshot and findings."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.diagnostics.engine import DiagnosticEngine
from app.models import (
    InterfaceSnapshot,
    InterfaceExpectation,
    DiagnosticFinding,
    DiagnosticReport,
)


class ReportBuilder:
    """Runs diagnostics and produces a structured report."""

    def __init__(self, engine: DiagnosticEngine | None = None) -> None:
        self.engine = engine or DiagnosticEngine()

    # ------------------------------------------------------------------
    def build(
        self,
        snapshot: InterfaceSnapshot,
        expected: InterfaceExpectation,
        device_id: str = "unknown",
    ) -> DiagnosticReport:
        findings = self.engine.run(snapshot, expected)
        return DiagnosticReport(
            report_id=f"diag-{uuid.uuid4().hex[:8]}",
            device_id=device_id,
            interface=snapshot.name,
            overall_health=self._overall(findings),
            source_model=snapshot.source_model,
            observed=snapshot,
            findings=findings,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _overall(findings: list[DiagnosticFinding]) -> str:
        if not findings:
            return "HEALTHY"
        if any(f.severity == "HIGH" for f in findings):
            return "DEGRADED"
        return "DEGRADED"
