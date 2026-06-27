"""Unit tests for the FixtureDeviceAdapter."""

import pytest
from app.adapters.fixture_device import FixtureDeviceAdapter
from app.models import InterfaceSnapshot


def test_fixture_adapter_loads_capabilities():
    adapter = FixtureDeviceAdapter("iosxe-sandbox")
    caps = adapter.discover_capabilities()
    assert caps is not None
    assert isinstance(caps, dict)
    assert "version" in caps
    assert "supported-models" in caps


def test_fixture_adapter_returns_snapshot():
    adapter = FixtureDeviceAdapter("iosxe-sandbox")
    snap = adapter.get_interface_snapshot("GigabitEthernet0/0")
    assert isinstance(snap, InterfaceSnapshot)
    assert snap.name == "GigabitEthernet0/0"
    assert snap.source_model == "openconfig-interfaces"
    assert snap.source_protocol == "gnmi"
    # From the real fixture: this interface is UP/UP
    assert snap.admin_status == "UP"
    assert snap.oper_status == "UP"
    assert snap.enabled is True
    assert snap.in_errors == 0
    assert snap.out_errors == 0


def test_fixture_adapter_returns_correct_speed():
    adapter = FixtureDeviceAdapter("iosxe-sandbox")
    snap = adapter.get_interface_snapshot("GigabitEthernet0/0")
    assert snap.speed_mbps == 1000  # SPEED_1GB → 1000


def test_fixture_adapter_description():
    adapter = FixtureDeviceAdapter("iosxe-sandbox")
    snap = adapter.get_interface_snapshot("GigabitEthernet0/0")
    assert snap.description == "DO NOT TOUCH"


def test_fixture_adapter_missing_interface_raises():
    adapter = FixtureDeviceAdapter("iosxe-sandbox")
    with pytest.raises(ValueError):
        adapter.get_interface_snapshot("NonExistent1/0/99")


def test_fixture_adapter_set_description_is_simulated():
    adapter = FixtureDeviceAdapter("iosxe-sandbox")
    result = adapter.set_interface_description("GigabitEthernet0/0", "test-desc")
    assert result["status"] == "simulated"
    assert result["after"]["description"] == "test-desc"
    assert "no device was changed" in result["note"].lower()


def test_fixture_adapter_get_device_id():
    adapter = FixtureDeviceAdapter("iosxe-sandbox")
    assert adapter.get_device_id() == "iosxe-sandbox"


def test_fixture_adapter_down_interface():
    """GigabitEthernet1/0/1 is admin DOWN / oper DOWN in the sandbox."""
    adapter = FixtureDeviceAdapter("iosxe-sandbox")
    adapter._load_interface_fixture = lambda _: _make_down_fixture()
    snap = adapter.get_interface_snapshot("GigabitEthernet1/0/1")
    assert snap.admin_status == "DOWN"
    assert snap.oper_status == "DOWN"


# ── helpers ──────────────────────────────────────────────────────────

def _make_down_fixture() -> dict:
    return {
        "openconfig_response": [{
            "updates": [{
                "values": {
                    "interfaces/interface": {
                        "name": "GigabitEthernet1/0/1",
                        "state": {
                            "admin-status": "DOWN",
                            "oper-status": "DOWN",
                            "counters": {},
                        },
                    }
                }
            }]
        }]
    }
