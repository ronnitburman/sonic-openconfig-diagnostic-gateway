"""Shared parsers that convert raw gNMI responses into InterfaceSnapshot.

These functions are used by both FixtureDeviceAdapter and the live
OpenConfigIOSXEAdapter / CiscoNativeIOSXEAdapter.  The parsing logic
is identical regardless of where the raw data came from.
"""

from typing import Any
from app.models import InterfaceSnapshot


# ---------------------------------------------------------------------------
# Speed enum → integer Mbps
# ---------------------------------------------------------------------------

SPEED_MAP: dict[str, int] = {
    "SPEED_10MB": 10,
    "SPEED_100MB": 100,
    "SPEED_1GB": 1000,
    "SPEED_10GB": 10000,
    "SPEED_25GB": 25000,
    "SPEED_40GB": 40000,
    "SPEED_50GB": 50000,
    "SPEED_100GB": 100000,
    "SPEED_400GB": 400000,
}


def parse_speed(speed_value: Any) -> int | None:
    """Normalize speed to integer Mbps.

    Handles:
      - None              → None
      - int               → passed through
      - "SPEED_1GB"       → 1000
      - "openconfig-if-ethernet:SPEED_1GB" → 1000  (strip prefix)
      - "1000"            → 1000  (string int)
    """
    if speed_value is None:
        return None
    if isinstance(speed_value, int):
        return speed_value

    speed_str = str(speed_value)

    # Strip namespace prefix if present  (e.g. "openconfig-if-ethernet:SPEED_1GB")
    if ":" in speed_str:
        speed_str = speed_str.split(":")[-1]

    # Try the speed map
    if speed_str in SPEED_MAP:
        return SPEED_MAP[speed_str]

    # Try direct integer parse
    try:
        return int(speed_str)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# OpenConfig response parser
# ---------------------------------------------------------------------------

def _to_int(value: Any) -> int | None:
    """Convert a gNMI counter value (often a JSON string) to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_openconfig_response(raw: dict, interface_name: str) -> InterfaceSnapshot:
    """Parse an OpenConfig  /interfaces/interface[name=X]  gNMI response.

    Expects *raw* to be the value dict found at
        response[0]["updates"][0]["values"]["interfaces/interface"]

    (The caller is responsible for unwrapping the gNMI notification envelope.)
    """
    state = raw.get("state", {}) if isinstance(raw, dict) else {}
    counters = state.get("counters", {})
    eth_state = (
        raw.get("openconfig-if-ethernet:ethernet", {}).get("state", {})
        if isinstance(raw, dict)
        else {}
    )

    # Speed lives under the ethernet augmentation
    raw_speed = eth_state.get("port-speed") or eth_state.get("negotiated-port-speed")

    return InterfaceSnapshot(
        name=interface_name,
        description=state.get("description"),
        enabled=state.get("enabled"),
        admin_status=state.get("admin-status"),
        oper_status=state.get("oper-status"),
        speed_mbps=parse_speed(raw_speed),
        mtu=_to_int(state.get("mtu")),
        in_errors=_to_int(counters.get("in-errors")),
        out_errors=_to_int(counters.get("out-errors")),
        in_discards=_to_int(counters.get("in-discards")),
        out_discards=_to_int(counters.get("out-discards")),
        last_change=state.get("last-change"),
        source_model="openconfig-interfaces",
        source_protocol="gnmi",
    )


# ---------------------------------------------------------------------------
# Cisco-native response parser
# ---------------------------------------------------------------------------

def parse_cisco_native_response(raw: dict, interface_name: str) -> InterfaceSnapshot:
    """Parse a Cisco-IOS-XE-interfaces-oper gNMI response.

    Cisco-native field names differ from OpenConfig:
      - admin-status  values are e.g. "if-state-up" / "if-state-down"
      - oper-status   values are e.g. "if-oper-up"  / "if-oper-down"
      - speed is often a plain string like "1000000000" (bps) or "1000" (Mbps)
    """
    state = raw.get("state", {}) if isinstance(raw, dict) else {}

    admin_status = state.get("admin-status")
    oper_status = state.get("oper-status")

    # Normalise Cisco-specific admin-status strings
    _admin_up = admin_status in ("if-state-up", "UP") if admin_status else None

    raw_speed = state.get("speed")

    return InterfaceSnapshot(
        name=interface_name,
        description=state.get("description"),
        enabled=_admin_up,
        admin_status=admin_status,
        oper_status=oper_status,
        speed_mbps=parse_speed(raw_speed),
        mtu=_to_int(state.get("mtu")),
        in_errors=_to_int(state.get("in-errors")),
        out_errors=_to_int(state.get("out-errors")),
        in_discards=_to_int(state.get("in-discards")),
        out_discards=_to_int(state.get("out-discards")),
        last_change=state.get("last-change"),
        source_model="cisco-native-interfaces",
        source_protocol="gnmi",
    )
