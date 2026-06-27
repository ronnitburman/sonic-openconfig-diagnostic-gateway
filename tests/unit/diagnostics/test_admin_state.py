"""Tests for LINK-002 — admin state rule."""

from app.diagnostics.rules.admin_state import AdminStateRule
from app.models import InterfaceSnapshot, InterfaceExpectation


def _snap(**kwargs) -> InterfaceSnapshot:
    defaults = {"name": "Gi1", "source_model": "oc"}
    return InterfaceSnapshot(**(defaults | kwargs))


# ── triggers ─────────────────────────────────────────────────────────

def test_triggers_when_expected_enabled_but_admin_down():
    snap = _snap(admin_status="DOWN")
    finding = AdminStateRule().evaluate(snap, InterfaceExpectation(enabled=True))
    assert finding is not None
    assert finding.rule_id == "LINK-002"

def test_triggers_when_expected_enabled_but_enabled_flag_false():
    snap = _snap(enabled=False)
    assert AdminStateRule().evaluate(snap, InterfaceExpectation(enabled=True)) is not None


# ── passes / skips ───────────────────────────────────────────────────

def test_passes_when_expected_enabled_and_admin_up():
    snap = _snap(admin_status="UP")
    assert AdminStateRule().evaluate(snap, InterfaceExpectation(enabled=True)) is None

def test_skips_when_no_expectation_set():
    snap = _snap(admin_status="DOWN")
    assert AdminStateRule().evaluate(snap, InterfaceExpectation()) is None

def test_skips_when_expected_disabled():
    """If operator expects enabled=False and it IS down, that's not a problem."""
    snap = _snap(admin_status="DOWN")
    assert AdminStateRule().evaluate(snap, InterfaceExpectation(enabled=False)) is None
