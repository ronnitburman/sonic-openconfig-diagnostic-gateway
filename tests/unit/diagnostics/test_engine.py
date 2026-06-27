"""Integration tests for the diagnostic engine and report builder."""

from app.diagnostics.engine import DiagnosticEngine
from app.diagnostics.report_builder import ReportBuilder
from app.models import InterfaceSnapshot, InterfaceExpectation


def _snap(**kwargs) -> InterfaceSnapshot:
    defaults = {
        "name": "Gi1",
        "admin_status": "UP",
        "oper_status": "UP",
        "in_errors": 0,
        "out_errors": 0,
        "source_model": "openconfig-interfaces",
    }
    return InterfaceSnapshot(**(defaults | kwargs))


# ── Engine ───────────────────────────────────────────────────────────

def test_engine_healthy_returns_no_findings():
    engine = DiagnosticEngine()
    snap = _snap()
    findings = engine.run(snap, InterfaceExpectation())
    assert findings == []


def test_engine_detects_link_down():
    engine = DiagnosticEngine()
    snap = _snap(admin_status="UP", oper_status="DOWN")
    findings = engine.run(snap, InterfaceExpectation())
    assert len(findings) >= 1
    assert any(f.rule_id == "LINK-001" for f in findings)


def test_engine_multiple_findings_possible():
    engine = DiagnosticEngine()
    snap = _snap(
        admin_status="UP",
        oper_status="DOWN",
        in_errors=5000,
        out_errors=0,
    )
    findings = engine.run(snap, InterfaceExpectation(enabled=True, speed_mbps=1000))
    # LINK-001 (up/down) + COUNTER-001 (errors) + SPEED-001 (speed unknown)
    assert len(findings) >= 2
    rule_ids = {f.rule_id for f in findings}
    assert "LINK-001" in rule_ids
    assert "COUNTER-001" in rule_ids


def test_engine_all_rules_registered():
    engine = DiagnosticEngine()
    rule_ids = {r.rule_id for r in engine.rules}
    assert rule_ids == {"LINK-001", "LINK-002", "COUNTER-001", "SPEED-001"}


# ── Report builder ───────────────────────────────────────────────────

def test_report_builder_healthy():
    builder = ReportBuilder()
    snap = _snap()
    report = builder.build(snap, InterfaceExpectation(), device_id="test-dev")
    assert report.overall_health == "HEALTHY"
    assert report.findings == []
    assert report.device_id == "test-dev"
    assert report.interface == "Gi1"
    assert report.report_id.startswith("diag-")
    assert report.generated_at  # non-empty ISO timestamp


def test_report_builder_degraded():
    builder = ReportBuilder()
    snap = _snap(admin_status="UP", oper_status="DOWN")
    report = builder.build(snap, InterfaceExpectation(), device_id="test-dev")
    assert report.overall_health == "DEGRADED"
    assert len(report.findings) >= 1
    # The observed snapshot is included verbatim
    assert report.observed == snap


def test_report_builder_high_severity_degrades():
    """A single HIGH finding should produce DEGRADED."""
    builder = ReportBuilder()
    snap = _snap(admin_status="UP", oper_status="DOWN")
    report = builder.build(snap, InterfaceExpectation(), device_id="test-dev")
    assert report.overall_health == "DEGRADED"


def test_report_builder_includes_source_model():
    builder = ReportBuilder()
    snap = _snap(source_model="openconfig-interfaces")
    report = builder.build(snap, InterfaceExpectation())
    assert report.source_model == "openconfig-interfaces"
