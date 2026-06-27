"""SPEED-001 — Observed interface speed differs from expected speed."""

from app.diagnostics.rules.base import DiagnosticRule
from app.models import InterfaceSnapshot, InterfaceExpectation, DiagnosticFinding


class SpeedRule(DiagnosticRule):
    """Flags interfaces whose actual speed doesn't match the expectation.

    Only evaluates when ``expected.speed_mbps`` is explicitly set.
    When observed speed is unavailable, the rule still triggers —
    the operator asked for speed verification but we cannot verify.
    """

    rule_id = "SPEED-001"
    severity = "MEDIUM"
    title = "Interface speed differs from expected value"

    def evaluate(
        self,
        snapshot: InterfaceSnapshot,
        expected: InterfaceExpectation,
    ) -> DiagnosticFinding | None:
        if expected.speed_mbps is None:
            return None

        if snapshot.speed_mbps is None:
            return self._finding({
                "expected_speed_mbps": expected.speed_mbps,
                "observed_speed_mbps": None,
                "note": "Observed speed unavailable — cannot verify.",
                "interface": snapshot.name,
            })

        if snapshot.speed_mbps != expected.speed_mbps:
            return self._finding({
                "expected_speed_mbps": expected.speed_mbps,
                "observed_speed_mbps": snapshot.speed_mbps,
                "difference_mbps": expected.speed_mbps - snapshot.speed_mbps,
                "interface": snapshot.name,
            })

        return None

    def recommendation(self) -> str:
        return (
            "The observed interface speed does not match the expected speed. "
            "Check auto-negotiation settings on both ends. Verify that the "
            "peer interface supports the desired speed. If using fixed speed "
            "configuration, ensure both sides are consistently set."
        )
