"""LINK-002 — Interface unexpectedly administratively disabled."""

from app.diagnostics.rules.base import DiagnosticRule
from app.models import InterfaceSnapshot, InterfaceExpectation, DiagnosticFinding


class AdminStateRule(DiagnosticRule):
    """Detects when the operator expects the interface to be enabled,
    but it is administratively shut down.

    Only evaluates when ``expected.enabled`` is explicitly set to ``True``.
    """

    rule_id = "LINK-002"
    severity = "MEDIUM"
    title = "Interface unexpectedly administratively disabled"

    def evaluate(
        self,
        snapshot: InterfaceSnapshot,
        expected: InterfaceExpectation,
    ) -> DiagnosticFinding | None:
        # Skip if the operator didn't set an expectation
        if expected.enabled is not True:
            return None

        admin_down = (
            snapshot.admin_status == "DOWN"
            or snapshot.enabled is False
        )

        if admin_down:
            return self._finding({
                "expected_enabled": True,
                "observed_admin_status": snapshot.admin_status,
                "observed_enabled": snapshot.enabled,
                "interface": snapshot.name,
            })
        return None

    def recommendation(self) -> str:
        return (
            "The interface is expected to be administratively enabled but is "
            "currently disabled. Verify intended administrative state against "
            "change-control records. If re-enabling is approved, use "
            "'no shutdown' or equivalent to bring the interface up."
        )
