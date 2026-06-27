"""Tests for SPEED-001 — speed mismatch rule."""

from app.diagnostics.rules.speed import SpeedRule
from app.models import InterfaceSnapshot, InterfaceExpectation


def _snap(**kwargs) -> InterfaceSnapshot:
    defaults = {"name": "Gi1", "source_model": "oc"}
    return InterfaceSnapshot(**(defaults | kwargs))


# ── triggers ─────────────────────────────────────────────────────────

def test_triggers_on_mismatch():
    snap = _snap(speed_mbps=100)
    finding = SpeedRule().evaluate(snap, InterfaceExpectation(speed_mbps=1000))
    assert finding is not None
    assert finding.rule_id == "SPEED-001"
    assert finding.evidence["difference_mbps"] == 900

def test_triggers_when_observed_speed_is_none():
    """Cannot verify speed → still trigger (operator asked us to check)."""
    snap = _snap(speed_mbps=None)
    finding = SpeedRule().evaluate(snap, InterfaceExpectation(speed_mbps=1000))
    assert finding is not None
    assert finding.evidence["observed_speed_mbps"] is None


# ── passes / skips ───────────────────────────────────────────────────

def test_passes_on_match():
    snap = _snap(speed_mbps=1000)
    assert SpeedRule().evaluate(snap, InterfaceExpectation(speed_mbps=1000)) is None

def test_skips_when_no_expectation():
    snap = _snap(speed_mbps=100)
    assert SpeedRule().evaluate(snap, InterfaceExpectation()) is None

def test_skips_when_speed_expectation_is_none():
    snap = _snap(speed_mbps=1000)
    assert SpeedRule().evaluate(snap, InterfaceExpectation(speed_mbps=None)) is None
