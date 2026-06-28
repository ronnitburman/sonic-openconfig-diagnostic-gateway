# Phase 6 Runbook

## Prerequisites

- Phases 1-5 complete
- `source .venv/bin/activate`

---

## Start the Server

```bash
kill $(lsof -t -i:8080) 2>/dev/null
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## curl — Dry-Run Description Change (safe default)

```bash
curl -s -X POST http://localhost:8080/v1/changes/interface-description \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iosxe-sandbox",
    "interface": "GigabitEthernet0/0",
    "description": "managed-by-sonic-diagnostic",
    "dry_run": true
  }' | python3 -m json.tool
```

Expected:
```json
{
  "status": "planned",
  "dry_run": true,
  "before": {
    "description": "DO NOT TOUCH"
  },
  "requested": {
    "description": "managed-by-sonic-diagnostic"
  },
  "after": null,
  "note": null
}
```

---

## curl — Apply Description Change (fixture mode)

Fixture mode simulates the change — nothing is actually written to a device:

```bash
curl -s -X POST http://localhost:8080/v1/changes/interface-description \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iosxe-sandbox",
    "interface": "GigabitEthernet0/0",
    "description": "updated-description",
    "dry_run": false
  }' | python3 -m json.tool
```

Expected:
```json
{
  "status": "applied",
  "dry_run": false,
  "before": {
    "description": "DO NOT TOUCH"
  },
  "after": {
    "description": "updated-description"
  },
  "set_result": {
    "status": "simulated",
    "interface": "GigabitEthernet0/0",
    "before": { "description": "simulated-existing-description" },
    "after": { "description": "updated-description" },
    "note": "Fixture mode — no device was changed."
  }
}
```

## curl — Apply Description Change (live mode)

Live mode performs a real gNMI Set against the Cisco sandbox:

```bash
# Start server in live mode
cd /path/to/sonic-openconfig-diagnostic-gateway
kill $(lsof -t -i:8080) 2>/dev/null
DEVICE_MODE=live uvicorn app.main:app --host 0.0.0.0 --port 8080

# Dry-run first (safe)
curl -s -X POST http://localhost:8080/v1/changes/interface-description \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iosxe-sandbox",
    "interface": "GigabitEthernet0/0",
    "description": "managed-by-sonic",
    "dry_run": true
  }' | python3 -m json.tool
# → status: "planned", shows before + requested descriptions

# Apply the change
curl -s -X POST http://localhost:8080/v1/changes/interface-description \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iosxe-sandbox",
    "interface": "GigabitEthernet0/0",
    "description": "managed-by-sonic",
    "dry_run": false
  }' | python3 -m json.tool
# → status: "applied", set_result contains gNMI response with operation: UPDATE

# Restore original (good practice on shared sandbox)
curl -s -X POST http://localhost:8080/v1/changes/interface-description \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iosxe-sandbox",
    "interface": "GigabitEthernet0/0",
    "description": "DO NOT TOUCH",
    "dry_run": false
  }' | python3 -m json.tool
```

> **Note:** The live adapters (`OpenConfigIOSXEAdapter`, `CiscoNativeIOSXEAdapter`) use `gnmic set --update-path ... --update-value ...` to apply changes. The fixture adapter returns a simulated result.

---

## curl — Skip When Description Unchanged

```bash
curl -s -X POST http://localhost:8080/v1/changes/interface-description \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iosxe-sandbox",
    "interface": "GigabitEthernet0/0",
    "description": "DO NOT TOUCH",
    "dry_run": false
  }' | python3 -m json.tool
```

Expected: `"status": "skipped"`, with a note about the description being unchanged.

---

## curl — Error Cases

```bash
# Description too long (>240 chars)
curl -s -X POST http://localhost:8080/v1/changes/interface-description \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iosxe-sandbox",
    "interface": "GigabitEthernet0/0",
    "description": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }' | python3 -m json.tool
# → 422 validation error

# Missing required field (interface)
curl -s -X POST http://localhost:8080/v1/changes/interface-description \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox", "description": "test"}' | python3 -m json.tool
# → 422

# Unknown device (fixture mode)
curl -s -X POST http://localhost:8080/v1/changes/interface-description \
  -H "Content-Type: application/json" \
  -d '{"device_id": "ghost-device", "interface": "Eth1", "description": "test"}' | python3 -m json.tool
# → 503 "Fixture data not available for device 'ghost-device'"

# Unknown device (live mode)
curl -s -X POST http://localhost:8080/v1/changes/interface-description \
  -H "Content-Type: application/json" \
  -d '{"device_id": "ghost-device", "interface": "Eth1", "description": "test"}' | python3 -m json.tool
# → 500 if gNMI is unreachable; device_id is just a label — live mode
#   connects to whatever host/port is in .env regardless of device_id
```

---

## Verify Audit Log

Applied and planned changes write to the audit log:

```bash
cat data/audit.jsonl | python3 -m json.tool
```

Each entry contains: `timestamp`, `action`, `device_id`, `interface`, `dry_run`, `status`, `before`, `after`.

---

## Running Tests

```bash
pytest tests/integration/test_api.py -v -k "change"
```

Expected: 5 tests pass (dry_run, applied, unknown_device, too_long, missing_interface).
