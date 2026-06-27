"""Live adapter that retrieves interface state via OpenConfig YANG paths."""

from app.adapters.gnmi_client import GnmiClient
from app.adapters.parsers import parse_openconfig_response
from app.models import InterfaceSnapshot


class OpenConfigIOSXEAdapter:
    """Uses OpenConfig paths to fetch and normalise interface state."""

    def __init__(self, client: GnmiClient):
        self.client = client

    def discover_capabilities(self) -> dict:
        """Return gNMI capability information including supported models."""
        return self.client.capabilities()

    def get_interface_snapshot(self, interface_name: str) -> InterfaceSnapshot:
        path = f"/interfaces/interface[name={interface_name}]"
        raw_list = self.client.get(path)
        iface_data = _extract_interface_data(raw_list, interface_name)
        return parse_openconfig_response(iface_data, interface_name)


def _extract_interface_data(response: list, interface_name: str) -> dict:
    """Pull the per-interface dict from a gnmic Get response list."""
    try:
        notif = response[0]
        updates = notif["updates"]
        update = updates[0] if isinstance(updates, list) else updates
        values = update["values"]

        for key, val in values.items():
            if "interface" in key.lower() and isinstance(val, dict):
                if "interface" in val and isinstance(val["interface"], list):
                    for iface in val["interface"]:
                        if iface.get("name") == interface_name:
                            return iface
                return val

        return values
    except (KeyError, IndexError, TypeError):
        return {}
