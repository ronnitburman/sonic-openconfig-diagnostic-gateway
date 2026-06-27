# Phase 2 Runbook

## Prerequisites

- Phase 1 complete (venv, deps, config)
- Cisco DevNet sandbox reserved and accessible
- `gnmic` installed (`brew install gnmic`)

---

## Verify gnmic Installation

```bash
gnmic version
```

Expected: version 0.46.0 or later.

---

## Configure Sandbox Credentials

Edit `.env`:

```bash
GNMI_HOST=devnetsandboxiosxec9k.cisco.com
GNMI_PORT=9339
GNMI_USERNAME=your-username
GNMI_PASSWORD=your-password
GNMI_INSECURE=false
GNMI_SKIP_VERIFY=true
```

**Important:** Never commit `.env`. It's in `.gitignore`.

---

## Verify Device Connectivity

```bash
# Test SSH (port 22 or 8181 depending on sandbox)
ssh your-username@devnetsandboxiosxec9k.cisco.com "show version | inc Version"

# Test gNMI port
nc -zv devnetsandboxiosxec9k.cisco.com 9339
```

---

## Run gNMI Capabilities

```bash
gnmic -a devnetsandboxiosxec9k.cisco.com:9339 \
  -u your-username -p 'your-password' \
  --skip-verify \
  capabilities --format json
```

The first ~20 lines should show `"version": "0.7.0"` and a `"supported-models"` array.

---

## List All Interfaces

```bash
gnmic -a devnetsandboxiosxec9k.cisco.com:9339 \
  -u your-username -p 'your-password' \
  --skip-verify \
  get --path "/interfaces" --encoding JSON_IETF --format json | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
ifaces = data[0]['updates'][0]['values']['interfaces']['interface']
for i in ifaces:
    s = i.get('state', {})
    print(f\"{i['name']:25s} admin={s.get('admin-status','?'):5s} oper={s.get('oper-status','?'):15s}\")
"
```

---

## Get Single Interface State

```bash
gnmic -a devnetsandboxiosxec9k.cisco.com:9339 \
  -u your-username -p 'your-password' \
  --skip-verify \
  get --path "/interfaces/interface[name=GigabitEthernet0/0]" \
  --encoding JSON_IETF --format json
```

---

## (Re)Capture Fixtures

If you have a new sandbox or the device state changed:

```bash
source .venv/bin/activate

# Capture capabilities
gnmic -a $GNMI_HOST:$GNMI_PORT -u $GNMI_USERNAME -p $GNMI_PASSWORD \
  --skip-verify capabilities --format json \
  > fixtures/capabilities/iosxe-sandbox.json

# Capture all interfaces
python scripts/capture_interface_fixtures.py -i GigabitEthernet0/0
```

---

## View Captured Data

```bash
# List all interfaces in the fixture
python3 -c "
import json
with open('fixtures/interfaces/raw-interface-state.json') as f:
    data = json.load(f)
notif = data['openconfig_response'][0]
ifaces = notif['updates'][0]['values']['interfaces']['interface']
for i in ifaces:
    s = i.get('state', {})
    eth = i.get('openconfig-if-ethernet:ethernet', {}).get('state', {})
    print(f\"{i['name']:25s} speed={eth.get('port-speed','?'):12s} admin={s.get('admin-status','?'):5s} oper={s.get('oper-status','?'):15s}\")
"
```

---

## Read YANG Model Reference

```bash
# Find how a field is defined
grep -A 10 "leaf oper-status" docs/yang-models/openconfig-interfaces.yang

# Find counter definitions
grep -A 3 "leaf in-errors" docs/yang-models/openconfig-interfaces.yang
```

---

## Verify Documentation

```bash
# Check supported models doc exists
head -20 docs/supported-models.md
```
