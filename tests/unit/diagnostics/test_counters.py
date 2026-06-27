"""Tests for COUNTER-001 — error counter rule."""

from app.diagnostics.rules.counters import CounterRule
from app.models import InterfaceSnapshot, InterfaceExpectation


def _snap(**kwargs) -> InterfaceSnapshot:
    defaults = {"name": "Gi1", "source_model": "oc"}
    return InterfaceSnapshot(**(defaults | kwargs))


# ── triggers ─────────────────────────────────────────────────────────

def test_triggers_on_input_errors():
    snap = _snap(in_errors=5, out_errors=0)
    finding = CounterRule().evaluate(snap, InterfaceExpectation())
    assert finding is not None
    assert finding.rule_id == "COUNTER-001"

def test_triggers_on_output_errors():
    snap = _snap(in_errors=0, out_errors=10)
    assert CounterRule().evaluate(snap, InterfaceExpectation()) is not None

def test_triggers_on_discards():
    snap = _snap(in_errors=0, out_errors=0, in_discards=1)
    assert CounterRule().evaluate(snap, InterfaceExpectation()) is not None

def test_escalates_to_high_on_large_error_count():
    snap = _snap(in_errors=1500, out_errors=0)
    finding = CounterRule().evaluate(snap, InterfaceExpectation())
    assert finding.severity == "HIGH"

def test_stays_medium_on_small_error_count():
    snap = _snap(in_errors=5, out_errors=0)
    finding = CounterRule().evaluate(snap, InterfaceExpectation())
    assert finding.severity == "MEDIUM"


# ── passes ───────────────────────────────────────────────────────────

def test_passes_with_zero_errors():
    snap = _snap(in_errors=0, out_errors=0, in_discards=0, out_discards=0)
    assert CounterRule().evaluate(snap, InterfaceExpectation()) is None

def test_passes_when_counters_are_none():
    """Missing counters should not trigger the rule."""
    snap = _snap(in_errors=None, out_errors=None)
    assert CounterRule().evaluate(snap, InterfaceExpectation()) is None
