# Phase 1 Runbook

## Prerequisites

- Python 3.10+
- macOS or Linux

---

## Quick Start (first time)

```bash
cd sonic-openconfig-diagnostic-gateway

# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# Install with all dependencies
pip install -e ".[gnmi,gnoi,dev]"

# Set up config (no credentials needed for fixture mode)
cp .env.example .env
```

---

## Daily Development

```bash
source .venv/bin/activate
```

Already activated? Skip. The editable install means code changes take effect immediately.

---

## Running the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Output:
```
INFO:     Uvicorn running on http://0.0.0.0:8080
```

---

## Testing the Health Endpoint

```bash
# From another terminal
curl http://localhost:8080/health
```

Expected:
```json
{"status":"ok","service":"sonic-openconfig-diagnostic-gateway"}
```

---

## Interactive API Docs

Open in browser:
- Swagger: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
- Raw OpenAPI: http://localhost:8080/openapi.json

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# Just health test
pytest tests/unit/test_health.py -v

# With output
pytest tests/ -v -s
```

Expected: 1 test passes (more added in later phases).

---

## Verifying Configuration

```bash
python3 -c "from app.config import settings; print(f'mode={settings.device_mode}, port={settings.app_port}')"
```

Expected:
```
mode=fixture, port=8080
```

---

## Checking Dependencies

```bash
pip list | grep -E "fastapi|uvicorn|pydantic|pytest"
```

Expected: fastapi, uvicorn, pydantic, pytest all listed with versions.

---

## Stopping the Server

```bash
Ctrl+C  # in the terminal running uvicorn
```

Or:
```bash
kill $(lsof -t -i:8080)
```
