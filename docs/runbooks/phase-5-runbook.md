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

# Unknown device (fixture mode)
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{"device_id": "ghost", "interface": "Eth1"}' | python3 -m json.tool
# → 503 "Fixture data not available for device 'ghost'. Available: ['iosxe-sandbox']"

# Non-existent interface (fixture mode)
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox", "interface": "NonExistent99/99/99"}' | python3 -m json.tool
# → 422 "Interface 'NonExistent99/99/99' not found in response. Available: [...]"
```

> **Note:** Unknown device (503) and non-existent interface (422) are now distinct error categories — the fixture adapter validates device existence before attempting interface lookup.

---

## Postman

1. Open Postman
2. Import → File → `postman/SONiC-OpenConfig-Diagnostic-Gateway.postman_collection.json`
3. Set environment variable `base_url` = `http://localhost:8080`
4. Run requests in order: Health → Discovery → Diagnostics

---

## Live Mode (requires sandbox access)

```bash
# Start with live mode — MUST cd to project root so .env is found
cd /path/to/sonic-openconfig-diagnostic-gateway
kill $(lsof -t -i:8080) 2>/dev/null
DEVICE_MODE=live uvicorn app.main:app --host 0.0.0.0 --port 8080

# Discovery should show real capabilities
curl -s -X POST http://localhost:8080/v1/devices/discover \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox"}' | python3 -m json.tool
# → gnmi_reachable: true, model_support: openconfig_interfaces + cisco_native

# Diagnostic with live data
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox", "interface": "GigabitEthernet0/0"}' | python3 -m json.tool
```

> **Important:** Always `cd` to the project root before starting the server. The `.env` file is loaded relative to the working directory. Starting from a different directory causes `gnmi_port` to default to 50052 (instead of 9339 from `.env`) and gNMI connections will fail.

---

## Running Tests

```bash
# Integration tests only
pytest tests/integration/test_api.py -v

# All tests
pytest tests/ -v
```

Expected: 64 tests pass.
