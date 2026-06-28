"""Unit tests for gNOI probe and security posture services."""

import pytest
from pathlib import Path

from app.models import DeviceTarget
from app.services.gnoi_probe_service import GnoiProbeService
from app.services.security_posture_service import SecurityPostureService


# ── Fixture helpers ──────────────────────────────────────────────────

def _fixture_device() -> DeviceTarget:
    return DeviceTarget(device_id="test-device", host="localhost", port=50052)


# ── GnoiProbeService fixture mode ────────────────────────────────────

def test_fixture_probe_returns_structure():
    """Fixture mode returns the expected structure even without fixture file."""
    service = GnoiProbeService()
    result = service._probe_fixture(_fixture_device())

    assert result["device_id"] == "test-device"
    assert "gnoi_reachable" in result
    assert "services" in result
    assert "notes" in result

    # Factory reset must ALWAYS be intentionally disabled
    assert result["services"]["factory_reset"] == "INTENTIONALLY_DISABLED"
    # OS must always be NOT_TESTED
    assert result["services"]["os"] == "NOT_TESTED"
    # Safety note must be present
    assert any("intentionally disabled" in n.lower() for n in result["notes"])


def test_fixture_probe_loads_sandbox_fixture():
    """Loading the iosxe-sandbox fixture returns the captured data."""
    service = GnoiProbeService()
    result = service._probe_fixture(DeviceTarget(device_id="iosxe-sandbox"))

    assert result["gnoi_reachable"] is False
    assert result["services"]["certificate"] == "UNKNOWN"
    assert result["services"]["factory_reset"] == "INTENTIONALLY_DISABLED"
    assert result["services"]["os"] == "NOT_TESTED"
    assert any("gnxi" in n.lower() for n in result["notes"])


def test_fixture_probe_unknown_device_returns_defaults():
    """Unknown device returns a safe default with UNKNOWN services."""
    service = GnoiProbeService()
    result = service._probe_fixture(DeviceTarget(device_id="nonexistent-xyz"))

    assert result["gnoi_reachable"] is False
    assert result["services"]["certificate"] == "UNKNOWN"
    assert result["services"]["factory_reset"] == "INTENTIONALLY_DISABLED"
    assert any("fixture" in n.lower() for n in result["notes"])


# ── SecurityPostureService ───────────────────────────────────────────

def test_security_posture_no_gnoi_data():
    """Report works even without gNOI probe data."""
    service = SecurityPostureService()
    result = service.report("test-device", None)

    assert result["device_id"] == "test-device"
    assert result["gnmi_transport"] in ("INSECURE_LAB", "TLS")
    assert result["gnoi_certificate_support"] == "UNKNOWN"
    assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert isinstance(result["recommendations"], list)
    assert len(result["recommendations"]) > 0


def test_security_posture_with_gnoi_supported():
    """When gNOI cert is SUPPORTED, risk lowers and recommendation added."""
    service = SecurityPostureService()
    gnoi_result = {
        "services": {"certificate": "SUPPORTED"},
    }
    result = service.report("test-device", gnoi_result)

    assert result["gnoi_certificate_support"] == "SUPPORTED"
    assert any(
        "certificate-based" in r.lower() for r in result["recommendations"]
    )


def test_security_posture_with_gnoi_unsupported():
    """When gNOI cert is UNSUPPORTED, recommend enabling gNOI."""
    service = SecurityPostureService()
    gnoi_result = {
        "services": {"certificate": "UNSUPPORTED"},
    }
    result = service.report("test-device", gnoi_result)

    assert result["gnoi_certificate_support"] == "UNSUPPORTED"
    assert any(
        "gnxi enable-gnoi" in r for r in result["recommendations"]
    )


def test_security_posture_insecure_transport():
    """Insecure transport should produce relevant recommendations."""
    service = SecurityPostureService()
    result = service.report("test-device", None)

    if result["gnmi_transport"] == "INSECURE_LAB":
        assert result["risk_level"] in ("MEDIUM",)
        assert any("TLS" in r for r in result["recommendations"])


def test_security_posture_all_risk_levels_valid():
    """Smoke test: report with various inputs always produces valid output."""
    service = SecurityPostureService()
    for cert_status in ("SUPPORTED", "UNSUPPORTED", "UNKNOWN"):
        gnoi_result = {"services": {"certificate": cert_status}}
        result = service.report("dev", gnoi_result)
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")
        assert isinstance(result["recommendations"], list)
