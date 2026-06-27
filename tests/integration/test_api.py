"""Integration tests for the REST API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Health ───────────────────────────────────────────────────────────

def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Discovery ────────────────────────────────────────────────────────

def test_discover_fixture_mode():
    resp = client.post("/v1/devices/discover", json={"device_id": "iosxe-sandbox"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["gnmi_reachable"] is True
    assert data["model_support"]["openconfig_interfaces"] is True
    assert data["recommended_adapter"] == "openconfig_iosxe"


def test_discover_unknown_device():
    resp = client.post("/v1/devices/discover", json={"device_id": "ghost-device"})
    assert resp.status_code == 503


# ── Diagnostics ──────────────────────────────────────────────────────

def test_diagnose_healthy_interface():
    resp = client.post("/v1/diagnostics/interface", json={
        "device_id": "iosxe-sandbox",
        "interface": "GigabitEthernet0/0",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_health"] == "HEALTHY"
    assert data["findings"] == []
    assert data["device_id"] == "iosxe-sandbox"
    assert data["interface"] == "GigabitEthernet0/0"
    assert data["source_model"] == "openconfig-interfaces"
    assert "report_id" in data
    assert "observed" in data
    assert data["observed"]["admin_status"] == "UP"


def test_diagnose_degraded_interface():
    """Vlan1 is admin UP / oper LOWER_LAYER_DOWN → at least LINK-001."""
    resp = client.post("/v1/diagnostics/interface", json={
        "device_id": "iosxe-sandbox",
        "interface": "Vlan1",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_health"] == "DEGRADED"
    assert len(data["findings"]) >= 1
    finding_ids = {f["rule_id"] for f in data["findings"]}
    assert "LINK-001" in finding_ids


def test_diagnose_with_expectations():
    """Explicit expectations on a DOWN interface should trigger LINK-002."""
    resp = client.post("/v1/diagnostics/interface", json={
        "device_id": "iosxe-sandbox",
        "interface": "GigabitEthernet1/0/1",
        "expected": {"enabled": True, "speed_mbps": 1000},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_health"] == "DEGRADED"
    finding_ids = {f["rule_id"] for f in data["findings"]}
    assert "LINK-002" in finding_ids  # expected enabled, but admin DOWN


def test_diagnose_validation_rejects_missing_interface():
    resp = client.post("/v1/diagnostics/interface", json={
        "device_id": "test",
        # missing "interface" → Pydantic validation error
    })
    assert resp.status_code == 422


def test_diagnose_nonexistent_interface():
    resp = client.post("/v1/diagnostics/interface", json={
        "device_id": "iosxe-sandbox",
        "interface": "NonExistent99/99/99",
    })
    assert resp.status_code in (422, 503)


def test_diagnose_unknown_device():
    resp = client.post("/v1/diagnostics/interface", json={
        "device_id": "nonexistent-device-xyz",
        "interface": "Eth1",
    })
    assert resp.status_code in (422, 503)


# ── Changes ─────────────────────────────────────────────────────────

def test_change_description_dry_run():
    """Dry-run plans a description change without applying it."""
    resp = client.post("/v1/changes/interface-description", json={
        "device_id": "iosxe-sandbox",
        "interface": "GigabitEthernet0/0",
        "description": "managed-by-sonic-diagnostic",
        "dry_run": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "planned"
    assert data["dry_run"] is True
    assert "before" in data
    assert "requested" in data
    assert data["requested"]["description"] == "managed-by-sonic-diagnostic"


def test_change_description_applied_fixture():
    """In fixture mode, applying a change is simulated but returns evidence."""
    resp = client.post("/v1/changes/interface-description", json={
        "device_id": "iosxe-sandbox",
        "interface": "GigabitEthernet0/0",
        "description": "updated-description",
        "dry_run": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("applied", "unverified")
    assert data["dry_run"] is False
    assert "before" in data
    assert "after" in data


def test_change_description_unknown_device():
    resp = client.post("/v1/changes/interface-description", json={
        "device_id": "ghost-device",
        "interface": "Eth1",
        "description": "test",
    })
    assert resp.status_code == 503


def test_change_description_too_long():
    resp = client.post("/v1/changes/interface-description", json={
        "device_id": "iosxe-sandbox",
        "interface": "GigabitEthernet0/0",
        "description": "x" * 300,  # exceeds 240 char limit
    })
    assert resp.status_code == 422


def test_change_description_missing_interface():
    resp = client.post("/v1/changes/interface-description", json={
        "device_id": "iosxe-sandbox",
        "description": "test",
        # missing "interface" → Pydantic validation error
    })
    assert resp.status_code == 422


# ── OpenAPI ──────────────────────────────────────────────────────────

def test_openapi_schema_accessible():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema["info"]["title"] == "SONiC OpenConfig Diagnostic Gateway"
    paths = list(schema["paths"].keys())
    assert "/health" in paths
    assert "/v1/devices/discover" in paths
    assert "/v1/diagnostics/interface" in paths
    assert "/v1/changes/interface-description" in paths
