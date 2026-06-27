# Phase 3 Runbook

## Prerequisites

- Phase 1 complete (venv, deps, editable install)
- Phase 2 complete (fixtures captured)

---

## Verify Editable Install

```bash
source .venv/bin/activate
python3 -c "from app.models import InterfaceSnapshot; print('OK')"
```

---

## Fixture Mode (default, no device needed)

### Get Interface Snapshot via CLI

```bash
# Healthy interface (UP/UP)
python scripts/gnmi_get_interface.py -i GigabitEthernet0/0

# Down interface (DOWN/DOWN)
python scripts/gnmi_get_interface.py -i GigabitEthernet1/0/1

# Vlan with LOWER_LAYER_DOWN
python scripts/gnmi_get_interface.py -i Vlan1

# Non-existent interface (should error)
python scripts/gnmi_get_interface.py -i NonExistent1/0/99
```

Expected output for GigabitEthernet0/0:
```json
{
  "name": "GigabitEthernet0/0",
  "description": "DO NOT TOUCH",
  "enabled": true,
  "admin_status": "UP",
  "oper_status": "UP",
  "speed_mbps": 1000,
  "in_errors": 0,
  "out_errors": 0,
  "source_model": "openconfig-interfaces",
  "source_protocol": "gnmi"
}
```

Expected for NonExistent:
```
ERROR: Interface 'NonExistent1/0/99' not found in fixture data.
```

---

## Live Mode (requires sandbox access)

```bash
# Test with live device
DEVICE_MODE=live python scripts/gnmi_get_interface.py -i GigabitEthernet0/0
```

Expected: Same structure as fixture mode but with live counter values. Timestamps will differ.

```bash
# Test discovery through adapter factory
DEVICE_MODE=live python3 -c "
from app.adapters import create_adapter
from app.models import DeviceTarget
from app.config import settings

d = DeviceTarget(
    device_id='test',
    host=settings.gnmi_host,
    port=settings.gnmi_port,
    username=settings.gnmi_username,
    password=settings.gnmi_password,
)
adapter = create_adapter(d)
print(f'Adapter: {type(adapter).__name__}')
caps = adapter.discover_capabilities()
print(f'gNMI version: {caps[\"version\"]}')
print(f'Models: {len(caps[\"supported-models\"])}')
snap = adapter.get_interface_snapshot('GigabitEthernet0/0')
print(f'Interface: {snap.name}  admin={snap.admin_status}  oper={snap.oper_status}')
"
```

---

## Running Tests

```bash
# All adapter/parser tests
pytest tests/unit/test_parsers.py tests/unit/test_fixture_adapter.py -v

# With verbose output
pytest tests/unit/test_parsers.py tests/unit/test_fixture_adapter.py -v -s

# Specific test
pytest tests/unit/test_parsers.py::test_parse_speed_all_known -v
```

Expected: 21 tests pass (13 parser + 8 fixture adapter).

---

## Testing Parsers in Isolation

```bash
python3 -c "
from app.adapters.parsers import parse_openconfig_response, parse_speed

# Test speed mapping
print('SPEED_1GB →', parse_speed('SPEED_1GB'))
print('SPEED_100GB →', parse_speed('SPEED_100GB'))
print('None →', parse_speed(None))

# Test full parser
raw = {
    'state': {
        'admin-status': 'UP',
        'oper-status': 'UP',
        'description': 'test',
        'enabled': True,
        'counters': {'in-errors': '5', 'out-errors': '2'}
    },
    'openconfig-if-ethernet:ethernet': {
        'state': {'port-speed': 'SPEED_10GB'}
    }
}
snap = parse_openconfig_response(raw, 'TestInterface')
print(f'Snapshot: {snap.name}  speed={snap.speed_mbps}Mbps  errors_in={snap.in_errors}  source={snap.source_model}')
"
```

---

## Testing the Adapter Factory

```bash
# Fixture mode
python3 -c "
from app.adapters import create_adapter
from app.models import DeviceTarget
adapter = create_adapter(DeviceTarget(device_id='iosxe-sandbox'))
print(f'Fixture adapter: {type(adapter).__name__}')
print(f'Device ID: {adapter.get_device_id()}')
caps = adapter.discover_capabilities()
print(f'Models supported: {len(caps[\"supported-models\"])}')
"
```

---

## Verifying File Structure

```bash
ls -la app/adapters/
```

Expected files:
```
__init__.py          base.py             cisco_native_iosxe.py
fixture_device.py    gnmi_client.py      openconfig_iosxe.py
parsers.py
```

---

## Checking for Import Issues

```bash
python3 -c "
from app.adapters.base import DeviceAdapter
from app.adapters.fixture_device import FixtureDeviceAdapter
from app.adapters.gnmi_client import GnmiClient
from app.adapters.openconfig_iosxe import OpenConfigIOSXEAdapter
from app.adapters.cisco_native_iosxe import CiscoNativeIOSXEAdapter
from app.adapters.parsers import parse_openconfig_response, parse_cisco_native_response, parse_speed
from app.adapters import create_adapter
print('All imports OK')
"
```
