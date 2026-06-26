# SONiC OpenConfig Diagnostic Gateway

A Python-based network diagnostic gateway that runs as a packaged service inside a custom SONiC image. It exposes a northbound REST API, connects southbound to Cisco IOS XE devices using gNMI/gNOI, normalizes OpenConfig and Cisco-native YANG responses, and returns evidence-backed diagnostic reports.

## Prerequisites

- Python 3.10+
- virtualenv (or Python's built-in `venv`)

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd sonic-openconfig-diagnostic-gateway

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -e ".[gnmi,gnoi,dev]"

# 4. Set up environment configuration
cp .env.example .env

# 5. Start the service
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Verify

```bash
curl http://localhost:8080/health
# {"status":"ok","service":"sonic-openconfig-diagnostic-gateway"}
```

## Run Tests

```bash
pytest tests/ -v
```

## Documentation

- [Project Plan](PROJECT_PLAN.md)
- [Architecture](docs/architecture.md) (coming soon)
- [Phase Plans](docs/plans/)
