"""Runs all registered diagnostic rules against an interface snapshot."""

from app.models import InterfaceSnapshot, InterfaceExpectation, DiagnosticFinding
from app.diagnostics.rules.link_state import LinkStateRule
from app.diagnostics.rules.admin_state import AdminStateRule
from app.diagnostics.rules.counters import CounterRule
from app.diagnostics.rules.speed import SpeedRule


class DiagnosticEngine:
    """Orchestrates rule evaluation.

    New rules are added by appending to ``self.rules`` — no other
    changes needed.
    """

    def __init__(self) -> None:
        self.rules = [
            LinkStateRule(),
            AdminStateRule(),
            CounterRule(),
            SpeedRule(),
        ]

    def run(
        self,
        snapshot: InterfaceSnapshot,
        expected: InterfaceExpectation,
    ) -> list[DiagnosticFinding]:
        """Evaluate all rules.  Returns findings (empty list = healthy)."""
        findings: list[DiagnosticFinding] = []
        for rule in self.rules:
            finding = rule.evaluate(snapshot, expected)
            if finding is not None:
                findings.append(finding)
        return findings
