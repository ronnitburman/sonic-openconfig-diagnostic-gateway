# Phase 8 Runbook

## Prerequisites

- Phases 1–7 complete (all code working locally, 82 tests passing).
- SSH access to a SONiC VM or physical switch.
- SONiC and your Mac on the same network (or routed/VPN).
- Cisco sandbox reachable from SONiC (or use fixture mode).
- `python3` (≥3.9) on SONiC.

---

## Quick Start (Recommended Path)

### On your Mac — create & transfer the bundle

```bash
cd sonic-openconfig-diagnostic-gateway

# 1. Create deployment bundle
./scripts/bundle_for_sonic.sh

# 2. Copy to SONiC
scp sonic-gateway-bundle.tar.gz admin@<sonic-ip>:/tmp/
```

### On SONiC — extract & set up

```bash
# 3. Create target directory
sudo mkdir -p /usr/lib/sonic-openconfig-diagnostic-gateway

# 4. Extract bundle
sudo tar xzf /tmp/sonic-gateway-bundle.tar.gz -C /usr/lib/sonic-openconfig-diagnostic-gateway

# 5. Make admin the owner
sudo chown -R admin:admin /usr/lib/sonic-openconfig-diagnostic-gateway

# 6. Run setup script
cd /usr/lib/sonic-openconfig-diagnostic-gateway
bash scripts/setup_on_sonic.sh
```

If the bundle approach isn't possible, see the **Manual Transfer** section below.

---

## Manual Steps (if scripts can't be used)

### Step 1 — Verify Python on SONiC

```bash
ssh admin@<sonic-ip>
python3 --version
# Must be 3.9 or later

# Install venv and pip if missing
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip
```

### Step 2 — Transfer files

```bash
# From Mac
scp -r app/ admin@<sonic-ip>:/usr/lib/sonic-openconfig-diagnostic-gateway/
scp -r fixtures/ admin@<sonic-ip>:/usr/lib/sonic-openconfig-diagnostic-gateway/
scp pyproject.toml admin@<sonic-ip>:/usr/lib/sonic-openconfig-diagnostic-gateway/
scp .env.sonic.example admin@<sonic-ip>:/usr/lib/sonic-openconfig-diagnostic-gateway/
```

### Step 3 — Create virtual environment

```bash
# On SONiC
cd /usr/lib/sonic-openconfig-diagnostic-gateway
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### Step 4 — Configure environment

```bash
# Copy example config
cp .env.sonic.example .env

# Edit with your sandbox details
vi .env
# Set: DEVICE_MODE=live, GNMI_HOST, GNMI_USERNAME, GNMI_PASSWORD
```

### Step 5 — Start the service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## Verify Deployment

### From SONiC (local)

```bash
# Health check
curl http://localhost:8080/health
# → {"status":"ok","service":"sonic-openconfig-diagnostic-gateway"}

# Test config loads correctly
python -c "
from app.config import settings
print(f'Mode: {settings.device_mode}')
print(f'gNMI host: {settings.gnmi_host}')
print(f'gNMI insecure: {settings.gnmi_insecure}')
"

# Run diagnostics with fixture data
curl -s -X POST http://localhost:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox", "interface": "GigabitEthernet0/0"}' \
  | python3 -m json.tool
```

### From Mac (remote)

```bash
# Health check through SONiC
curl http://<sonic-ip>:8080/health

# Full diagnostic
curl -s -X POST http://<sonic-ip>:8080/v1/diagnostics/interface \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "iosxe-sandbox",
    "interface": "GigabitEthernet0/0",
    "expected": {"enabled": true, "oper_status": "UP"}
  }' | python3 -m json.tool

# Discovery (live mode)
curl -s -X POST http://<sonic-ip>:8080/v1/devices/discover \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox"}' | python3 -m json.tool

# gNOI probe
curl -s -X POST http://<sonic-ip>:8080/v1/operations/gnoi/probe \
  -H "Content-Type: application/json" \
  -d '{"device_id": "iosxe-sandbox"}' | python3 -m json.tool
```

---

## Postman Verification

1. Open Postman.
2. Create/update environment with `base_url` = `http://<sonic-ip>:8080`.
3. Import the collection from `postman/SONiC-OpenConfig-Diagnostic-Gateway.postman_collection.json`.
4. Run requests in order:
   - Health Check → 200 OK
   - Discover Device → capabilities returned
   - Diagnose Interface → diagnostic report returned
   - gNOI Probe → gNOI availability reported
   - gRPC Security Posture → risk assessment returned

---

## Live gNMI from SONiC → Cisco Sandbox

```bash
# From SONiC — test sandbox reachability
ping -c 3 <sandbox-ip>

# Test gNMI port
python3 -c "
import socket
s = socket.socket()
s.settimeout(5)
try:
    s.connect(('<sandbox-ip>', 50052))
    print('gNMI port reachable')
except Exception as e:
    print(f'gNMI port NOT reachable: {e}')
finally:
    s.close()
"

# If gnmic is available on SONiC
gnmic -a <sandbox-ip>:50052 -u admin -p admin --insecure capabilities

# Switch to live mode and restart
sed -i 's/DEVICE_MODE=fixture/DEVICE_MODE=live/' .env
# Restart uvicorn
```

---

## Firewall (if Mac can't reach SONiC:8080)

```bash
# On SONiC — check if port 8080 is open
sudo netstat -tlnp | grep 8080

# Check iptables
sudo iptables -L INPUT -n | grep 8080

# Allow port 8080 if blocked
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
```

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| `curl: (7) Failed to connect` from Mac | Is uvicorn running on SONiC? Is port 8080 open in iptables? |
| `ModuleNotFoundError: No module named 'fastapi'` | `source venv/bin/activate` not run. Repeat Step 3. |
| `Address already in use` | Port 8080 occupied. Change `APP_PORT` or kill the other process. |
| gNMI discovery fails in live mode | Verify sandbox IP, port 50052 reachable from SONiC. Test with `nc -zv`. |
| `pip install` fails (no internet) | Pre-download wheels on Mac: `pip download -d wheels/ fastapi uvicorn pydantic pydantic-settings`. Transfer and `pip install --no-index --find-links wheels/`. |
| SONiC can't reach sandbox | Check VPN, routing. Fall back to `DEVICE_MODE=fixture`. |

---

## Definition of Done

- [x] Service running on SONiC, responds to `/health`.
- [x] Mac can reach the service via `http://<sonic-ip>:8080`.
- [x] Diagnostic endpoint returns valid report (fixture mode at minimum).
- [x] Postman collection works against SONiC-hosted service.
- [x] gNMI connectivity from SONiC to Cisco sandbox verified (or fixture mode documented as fallback).
