"""LINK-001 — Interface administratively up but operationally down."""

from app.diagnostics.rules.base import DiagnosticRule
from app.models import InterfaceSnapshot, InterfaceExpectation, DiagnosticFinding


class LinkStateRule(DiagnosticRule):
    """Detects admin-up / oper-down mismatches.

    Triggers regardless of ``expected`` — this is a universal health check.
    ``LOWER_LAYER_DOWN`` is treated as operationally down.
    """

    rule_id = "LINK-001"
    severity = "HIGH"
    title = "Interface administratively up but operationally down"

    # Recognised "down" operational states
    _DOWN_STATES = {"DOWN", "LOWER_LAYER_DOWN"}

    def evaluate(
        self,
        snapshot: InterfaceSnapshot,
        expected: InterfaceExpectation,  # noqa: ARG002  unused but part of the contract
    ) -> DiagnosticFinding | None:
        admin_up = snapshot.admin_status == "UP" or snapshot.enabled is True
        oper_down = (
            snapshot.oper_status in self._DOWN_STATES
            or snapshot.oper_status is None
        )

        if admin_up and oper_down:
            return self._finding({
                "admin_status": snapshot.admin_status,
                "oper_status": snapshot.oper_status,
                "interface": snapshot.name,
            })
        return None

    def recommendation(self) -> str:
        return (
            "Interface is administratively enabled but has no link. "
            "Check the far-end interface state, virtual link attachment, "
            "cable connection, and any shutdown state on the peer device. "
            "If this is expected (e.g., unconnected port in lab), consider "
            "administratively disabling the interface."
        )
