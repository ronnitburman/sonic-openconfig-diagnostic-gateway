# Phase 7 Runbook

## Prerequisites

- Phases 1-6 complete
- `source .venv/bin/activate`

---

## Start the Server

```bash
kill $(lsof -t -i:8080) 2>/dev/null
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## curl — gNOI Probe (fixture mode)

```bash
curl -s -X POST http://localhost:8080/v1/operations/gnoi/probe \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox"}' | python3 -m json.tool
```

Expected:
```json
{
  "device_id": "iosxe-sandbox",
  "gnoi_reachable": false,
  "services": {
    "certificate": "UNKNOWN",
    "system": "UNKNOWN",
    "os": "NOT_TESTED",
    "factory_reset": "INTENTIONALLY_DISABLED"
  },
  "notes": [
    "Captured from Cisco IOS XE sandbox — gNOI is not enabled.",
    "The sandbox has 'no gnxi enable-gnoi' in its running config.",
    "gNOI service reflection is unavailable on this device.",
    "Destructive operations are intentionally disabled."
  ]
}
```

**Key:** `factory_reset` is ALWAYS `INTENTIONALLY_DISABLED` — this is enforced at the service layer regardless of what the fixture or device reports.

---

## curl — gRPC Security Posture

```bash
curl -s -X POST http://localhost:8080/v1/operations/grpc-security \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox"}' | python3 -m json.tool
```

Expected:
```json
{
  "device_id": "iosxe-sandbox",
  "gnmi_transport": "TLS",
  "gnoi_certificate_support": "UNKNOWN",
  "risk_level": "MEDIUM",
  "recommendations": [
    "gNMI transport is using TLS — this is the recommended configuration for production deployments.",
    "gNOI Certificate Management is not available on this device. Enable 'gnxi enable-gnoi' in the device configuration to expose gNOI services."
  ]
}
```

If `GNMI_INSECURE=true` in `.env`, the response changes to:
```json
{
  "gnmi_transport": "INSECURE_LAB",
  "risk_level": "MEDIUM",
  "recommendations": [
    "gNMI is using insecure transport (no TLS). This is acceptable only in lab/sandbox environments.",
    "Use TLS for production gNMI and gNOI connectivity.",
    "Validate the server certificate.",
    "Use client certificate authentication when required by the environment."
  ]
}
```

---

## curl — Error Cases

```bash
# Missing required field
curl -s -X POST http://localhost:8080/v1/operations/gnoi/probe \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
# → 422

# Unknown device (fixture mode — returns defaults, not an error)
curl -s -X POST http://localhost:8080/v1/operations/gnoi/probe \
  -H "Content-Type: application/json" \
  -d '{"device_id": "ghost-device"}' | python3 -m json.tool
# → 200 with gnoi_reachable: false and UNKNOWN services
```

---

## Live Mode (requires sandbox access + grpcurl)

```bash
# Ensure grpcurl is installed
which grpcurl || brew install grpcurl

# Start with live mode
DEVICE_MODE=live \
GNMI_HOST=sandbox-iosxe.cisco.com \
GNMI_INSECURE=false \
GNMI_SKIP_VERIFY=true \
uvicorn app.main:app --host 0.0.0.0 --port 8080

# gNOI probe against live device
curl -s -X POST http://localhost:8080/v1/operations/gnoi/probe \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox"}' | python3 -m json.tool
```

**Expected on C9000 sandbox:** `gnoi_reachable: false` — the sandbox has `no gnxi enable-gnoi` in its config, so gNOI is explicitly disabled. This is honest reporting, not a bug.

---

## Running Tests

```bash
# All operations-related tests
pytest tests/unit/test_operations.py tests/integration/test_api.py -v -k "gnoi or security"

# Full suite
pytest tests/ -v
```

Expected: 82 tests pass (8 new for Phase 7).
