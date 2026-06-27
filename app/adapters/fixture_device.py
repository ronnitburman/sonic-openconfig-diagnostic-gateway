"""Fixture-based device adapter — reads pre-captured gNMI responses.

Used when DEVICE_MODE=fixture.  No live device required.
"""

import json
from pathlib import Path

from app.adapters.base import DeviceAdapter
from app.adapters.parsers import parse_openconfig_response, parse_cisco_native_response
from app.models import InterfaceSnapshot


FIXTURE_DIR = Path("fixtures")


class FixtureDeviceAdapter:
    """Reads pre-captured gNMI responses from fixture files."""

    def __init__(self, device_id: str, fixture_dir: str = "fixtures"):
        self._device_id = device_id
        self._fixture_dir = Path(fixture_dir)

    # ------------------------------------------------------------------
    # DeviceAdapter protocol
    # ------------------------------------------------------------------

    def get_device_id(self) -> str:
        return self._device_id

    def discover_capabilities(self) -> dict:
        cap_path = self._fixture_dir / "capabilities" / f"{self._device_id}.json"
        if not cap_path.exists():
            raise FileNotFoundError(
                f"Capabilities fixture not found: {cap_path}"
            )
        with open(cap_path) as f:
            return json.load(f)

    def get_interface_snapshot(self, interface_name: str) -> InterfaceSnapshot:
        raw = self._load_interface_fixture(interface_name)

        # Prefer OpenConfig response when available
        oc = raw.get("openconfig_response")
        if oc:
            iface_data = self._unwrap_gnmi_response(oc, interface_name)
            if iface_data:
                return parse_openconfig_response(iface_data, interface_name)

        cn = raw.get("cisco_native_response")
        if cn:
            iface_data = self._unwrap_gnmi_response(cn, interface_name)
            if iface_data:
                return parse_cisco_native_response(iface_data, interface_name)

        raise ValueError(
            f"Interface '{interface_name}' not found in fixture data. "
            f"Fixture: {self._fixture_dir}/interfaces/"
        )

    def set_interface_description(
        self, interface_name: str, description: str
    ) -> dict:
        return {
            "status": "simulated",
            "interface": interface_name,
            "before": {"description": "simulated-existing-description"},
            "after": {"description": description},
            "note": "Fixture mode — no device was changed.",
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_interface_fixture(self, interface_name: str) -> dict:
        """Load the combined raw-interface-state fixture.

        Tries the main fixture first, then falls back to individual
        per-interface JSON files.
        """
        # Primary: combined fixture
        combined = self._fixture_dir / "interfaces" / "raw-interface-state.json"
        if combined.exists():
            with open(combined) as f:
                return json.load(f)

        # Fallback: look for openconfig-<slug>.json
        slug = interface_name.replace("/", "-")
        oc_path = self._fixture_dir / "interfaces" / f"openconfig-{slug}.json"
        if oc_path.exists():
            with open(oc_path) as f:
                return {"openconfig_response": json.load(f)}

        raise FileNotFoundError(
            f"No fixture found for interface '{interface_name}'. "
            f"Checked: {combined}, {oc_path}"
        )

    @staticmethod
    def _unwrap_gnmi_response(response: list | dict, interface_name: str) -> dict | None:
        """Navigate the gNMI notification envelope to extract interface data.

        gnmic JSON format:
            [{
              "updates": [{
                "Path": "interfaces/interface[name=...]",
                "values": {"interfaces/interface": { ... }}
              }]
            }]

        Returns the ``{ ... }`` dict for the interface, or raises ValueError
        if the requested interface is not found.
        """
        try:
            if isinstance(response, list):
                notif = response[0]
            else:
                notif = response

            updates = notif["updates"]
            update = updates[0] if isinstance(updates, list) else updates
            values = update["values"]

            # "interfaces/interface" or "interfaces/interface[name=X]"
            for key, val in values.items():
                if "interface" in key.lower() and isinstance(val, dict):
                    # If it's a list of interfaces, pick the matching one
                    if "interface" in val and isinstance(val["interface"], list):
                        for iface in val["interface"]:
                            if iface.get("name") == interface_name:
                                return iface
                        raise ValueError(
                            f"Interface '{interface_name}' not found in response. "
                            f"Available: {[i.get('name') for i in val['interface']]}"
                        )
                    # Single interface — validate name matches
                    if val.get("name") == interface_name:
                        return val
                    raise ValueError(
                        f"Response contains interface '{val.get('name')}', "
                        f"but requested '{interface_name}'"
                    )

            return None  # no interface key found at all
        except (KeyError, IndexError, TypeError):
            return None
