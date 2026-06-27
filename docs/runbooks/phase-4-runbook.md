# Phase 4 Runbook

## Prerequisites

- Phase 3 complete (adapters working, fixtures available)
- `source .venv/bin/activate`

---

## Running All Diagnostic Tests

```bash
pytest tests/unit/diagnostics/ -v
```

Expected: 32 tests pass (7 link_state + 5 admin_state + 7 counters + 5 speed + 8 engine).

---

## Running One Rule's Tests

```bash
# LINK-001
pytest tests/unit/diagnostics/test_link_state.py -v

# LINK-002
pytest tests/unit/diagnostics/test_admin_state.py -v

# COUNTER-001
pytest tests/unit/diagnostics/test_counters.py -v

# SPEED-001
pytest tests/unit/diagnostics/test_speed.py -v

# Engine + Report Builder
pytest tests/unit/diagnostics/test_engine.py -v
```

---

## End-to-End with Fixture Data

```bash
python3 << 'EOF'
from app.adapters.fixture_device import FixtureDeviceAdapter
from app.diagnostics.report_builder import ReportBuilder
from app.models import InterfaceExpectation

adapter = FixtureDeviceAdapter("iosxe-sandbox")
builder = ReportBuilder()

# Test each interface type
for iface in ["GigabitEthernet0/0", "Vlan1", "GigabitEthernet1/0/1"]:
    snap = adapter.get_interface_snapshot(iface)
    report = builder.build(snap, InterfaceExpectation(), device_id="test")
    print(f"{iface:25s} health={report.overall_health:8s}  findings={len(report.findings)}")
    for f in report.findings:
        print(f"  → {f.rule_id} [{f.severity}] {f.title}")
    print()
EOF
```

Expected:
```
GigabitEthernet0/0          health=HEALTHY   findings=0

Vlan1                       health=DEGRADED  findings=1
  → LINK-001 [HIGH] Interface administratively up but operationally down

GigabitEthernet1/0/1        health=DEGRADED  findings=1
  → LINK-001 [HIGH] Interface administratively up but operationally down
```

---

## Testing with Expectations

```bash
python3 << 'EOF'
from app.adapters.fixture_device import FixtureDeviceAdapter
from app.diagnostics.report_builder import ReportBuilder
from app.models import InterfaceExpectation
import json

adapter = FixtureDeviceAdapter("iosxe-sandbox")
builder = ReportBuilder()

# Test: operator expects enabled, speed=1000 on a DOWN interface
snap = adapter.get_interface_snapshot("GigabitEthernet1/0/1")
report = builder.build(
    snap,
    InterfaceExpectation(enabled=True, speed_mbps=1000),
    device_id="test"
)
print(json.dumps(report.model_dump(), indent=2))
EOF
```

Expected: LINK-002 (expected enabled but admin DOWN) and SPEED-001 (speed unknown/mismatch).

---

## Interactive Rule Testing

```bash
python3 << 'EOF'
from app.diagnostics.rules.link_state import LinkStateRule
from app.diagnostics.rules.admin_state import AdminStateRule
from app.diagnostics.rules.counters import CounterRule
from app.diagnostics.rules.speed import SpeedRule
from app.models import InterfaceSnapshot, InterfaceExpectation

# Craft a snapshot to test specific scenarios
snap = InterfaceSnapshot(
    name="TestInterface",
    admin_status="UP",
    oper_status="DOWN",
    in_errors=1500,
    out_errors=200,
    speed_mbps=100,
    source_model="openconfig-interfaces",
)

expected = InterfaceExpectation(enabled=True, speed_mbps=1000)

for rule in [LinkStateRule(), AdminStateRule(), CounterRule(), SpeedRule()]:
    finding = rule.evaluate(snap, expected)
    if finding:
        print(f"❌ {rule.rule_id} [{finding.severity}] {finding.title}")
    else:
        print(f"✅ {rule.rule_id} passed (no finding)")
EOF
```

---

## Verify Rule Registration

```bash
python3 -c "
from app.diagnostics.engine import DiagnosticEngine
engine = DiagnosticEngine()
print(f'Registered rules: {[r.rule_id for r in engine.rules]}')
"
```

Expected:
```
Registered rules: ['LINK-001', 'LINK-002', 'COUNTER-001', 'SPEED-001']
```

---

## Full Test Suite

```bash
pytest tests/ -v --tb=short
```

Expected: 54 tests pass (22 from Phase 1-3 + 32 from Phase 4).
