"""Adapter factory — picks the right DeviceAdapter based on config and capabilities."""

from app.adapters.base import DeviceAdapter
from app.adapters.fixture_device import FixtureDeviceAdapter
from app.adapters.gnmi_client import GnmiClient, GnmiClientError
from app.adapters.openconfig_iosxe import OpenConfigIOSXEAdapter
from app.adapters.cisco_native_iosxe import CiscoNativeIOSXEAdapter
from app.config import settings
from app.models import DeviceTarget


def create_adapter(device: DeviceTarget) -> DeviceAdapter:
    """Create the appropriate adapter for *device*.

    Fixture mode (DEVICE_MODE=fixture):
        Returns a FixtureDeviceAdapter — no network required.

    Live mode (DEVICE_MODE=live):
        Connects via gNMI, discovers capabilities, and selects either
        OpenConfigIOSXEAdapter or CiscoNativeIOSXEAdapter.
    """
    # ── Fixture mode ──────────────────────────────────────────────
    if settings.device_mode == "fixture":
        return FixtureDeviceAdapter(device.device_id)

    # ── Live mode ─────────────────────────────────────────────────
    host = device.host or settings.gnmi_host
    port = device.port or settings.gnmi_port
    username = device.username or settings.gnmi_username
    password = device.password or settings.gnmi_password

    client = GnmiClient(
        host=host,
        port=port,
        username=username,
        password=password,
        insecure=settings.gnmi_insecure if device.insecure is None else device.insecure,
        skip_verify=settings.gnmi_skip_verify,
    )

    # Discover capabilities to decide which adapter to use
    try:
        caps = client.capabilities()
    except GnmiClientError:
        raise RuntimeError(
            f"gNMI Capabilities failed for {host}:{port}. "
            f"Check DEVICE_MODE, credentials, and network connectivity."
        )

    model_names = [m["name"] for m in caps.get("supported-models", [])]

    has_openconfig = any("openconfig-interfaces" in m for m in model_names)
    has_cisco_native = any("Cisco-IOS-XE-interfaces-oper" in m for m in model_names)

    if has_openconfig:
        return OpenConfigIOSXEAdapter(client)

    if has_cisco_native:
        return CiscoNativeIOSXEAdapter(client)

    raise RuntimeError(
        f"No supported interface YANG model found on {host}:{port}. "
        f"Available models include: {model_names[:10]}..."
    )
