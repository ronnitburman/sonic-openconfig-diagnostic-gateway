"""COUNTER-001 — Interface has recorded traffic errors or discards."""

from app.diagnostics.rules.base import DiagnosticRule
from app.models import InterfaceSnapshot, InterfaceExpectation, DiagnosticFinding


class CounterRule(DiagnosticRule):
    """Flags interfaces with non-zero error or discard counters.

    Severity escalates to HIGH when cumulative errors exceed 1 000.
    """

    rule_id = "COUNTER-001"
    severity = "MEDIUM"
    title = "Interface has recorded traffic errors"
    _HIGH_THRESHOLD = 1000

    def evaluate(
        self,
        snapshot: InterfaceSnapshot,
        expected: InterfaceExpectation,  # noqa: ARG002
    ) -> DiagnosticFinding | None:
        in_err = snapshot.in_errors or 0
        out_err = snapshot.out_errors or 0
        in_disc = snapshot.in_discards or 0
        out_disc = snapshot.out_discards or 0

        if in_err == 0 and out_err == 0 and in_disc == 0 and out_disc == 0:
            return None

        total_errors = in_err + out_err
        sev = "HIGH" if total_errors >= self._HIGH_THRESHOLD else self.severity

        return self._finding(
            evidence={
                "in_errors": snapshot.in_errors,
                "out_errors": snapshot.out_errors,
                "in_discards": snapshot.in_discards,
                "out_discards": snapshot.out_discards,
                "interface": snapshot.name,
            },
            severity=sev,
        )

    def recommendation(self) -> str:
        return (
            "Interface counters show errors or discards. Inspect link quality "
            "(CRC errors suggest physical-layer issues), check for duplex "
            "mismatch, verify MTU settings match the peer, and review error "
            "trends over time. For discards, check whether the interface is "
            "oversubscribed or QoS policies are dropping traffic."
        )
