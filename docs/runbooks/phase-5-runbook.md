# Phase 5 Runbook

## Prerequisites

- Phases 1-4 complete
- `source .venv/bin/activate`

---

## Start the Server

```bash
# Kill any previous instance
kill $(lsof -t -i:8080) 2>/dev/null

# Start
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## Interactive Docs

Open in browser:
- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc

Swagger lets you execute requests directly from the browser.

---

## curl — Health Check

```bash
curl http://localhost:8080/health
```

```json
{"status":"ok","service":"sonic-openconfig-diagnostic-gateway"}
```

---

## curl — Device Discovery (fixture mode)

```bash
curl -s -X POST http://localhost:8080/v1/devices/discover \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox"}' | python3 -m json.tool
```

---

## curl — Diagnose Healthy Interface

```bash
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox", "interface": "GigabitEthernet0/0"}' | python3 -m json.tool
```

Expected: `overall_health: "HEALTHY"`, `findings: []`.

---

## curl — Diagnose Degraded Interface (Vlan1)

```bash
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox", "interface": "Vlan1"}' | python3 -m json.tool
```

Expected: `overall_health: "DEGRADED"`, findings include `LINK-001`.

---

## curl — Diagnose with Expectations

```bash
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iosxe-sandbox",
    "interface": "GigabitEthernet1/0/1",
    "expected": {"enabled": true, "oper_status": "UP", "speed_mbps": 1000}
  }' | python3 -m json.tool
```

Expected: findings include `LINK-002` (expected enabled, but admin DOWN) and possibly `SPEED-001`.

---

## curl — Error Cases

```bash
# Missing required field
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{"device_id": "test"}' | python3 -m json.tool
# → 422 validation error

# Unknown device
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{"device_id": "ghost", "interface": "Eth1"}' | python3 -m json.tool
# → 422 or 503

# Non-existent interface
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox", "interface": "NonExistent99/99/99"}' | python3 -m json.tool
# → 422
```

---

## Postman

1. Open Postman
2. Import → File → `postman/SONiC-OpenConfig-Diagnostic-Gateway.postman_collection.json`
3. Set environment variable `base_url` = `http://localhost:8080`
4. Run requests in order: Health → Discovery → Diagnostics

---

## Live Mode (requires sandbox access)

```bash
# Start with live mode
DEVICE_MODE=live uvicorn app.main:app --host 0.0.0.0 --port 8080

# Discovery should show real capabilities
curl -s -X POST http://localhost:8080/v1/devices/discover \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox"}'

# Diagnostic with live data
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox", "interface": "GigabitEthernet0/0"}'
```

---

## Running Tests

```bash
# Integration tests only
pytest tests/integration/test_api.py -v

# All tests
pytest tests/ -v
```

Expected: 64 tests pass.
