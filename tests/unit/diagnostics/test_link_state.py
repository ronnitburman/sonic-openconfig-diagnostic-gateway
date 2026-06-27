"""Tests for LINK-001 — link state rule."""

from app.diagnostics.rules.link_state import LinkStateRule
from app.models import InterfaceSnapshot, InterfaceExpectation


def _snap(**kwargs) -> InterfaceSnapshot:
    defaults = {"name": "Gi1", "source_model": "oc"}
    return InterfaceSnapshot(**(defaults | kwargs))


# ── triggers ─────────────────────────────────────────────────────────

def test_triggers_when_admin_up_oper_down():
    snap = _snap(admin_status="UP", oper_status="DOWN")
    finding = LinkStateRule().evaluate(snap, InterfaceExpectation())
    assert finding is not None
    assert finding.rule_id == "LINK-001"
    assert finding.severity == "HIGH"

def test_triggers_when_enabled_true_oper_down():
    snap = _snap(enabled=True, oper_status="DOWN")
    assert LinkStateRule().evaluate(snap, InterfaceExpectation()) is not None

def test_triggers_when_oper_status_is_lower_layer_down():
    """Vlan1 on the C9000 sandbox shows LOWER_LAYER_DOWN."""
    snap = _snap(admin_status="UP", oper_status="LOWER_LAYER_DOWN")
    assert LinkStateRule().evaluate(snap, InterfaceExpectation()) is not None

def test_triggers_when_oper_status_is_none():
    """Missing oper-status is treated as down."""
    snap = _snap(admin_status="UP", oper_status=None)
    assert LinkStateRule().evaluate(snap, InterfaceExpectation()) is not None


# ── passes ───────────────────────────────────────────────────────────

def test_passes_when_both_up():
    snap = _snap(admin_status="UP", oper_status="UP")
    assert LinkStateRule().evaluate(snap, InterfaceExpectation()) is None

def test_passes_when_admin_down_oper_down():
    snap = _snap(admin_status="DOWN", oper_status="DOWN")
    assert LinkStateRule().evaluate(snap, InterfaceExpectation()) is None

def test_passes_when_both_down_using_enabled_flag():
    snap = _snap(enabled=False, oper_status="DOWN")
    assert LinkStateRule().evaluate(snap, InterfaceExpectation()) is None
