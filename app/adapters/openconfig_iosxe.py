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

    def set_interface_description(
        self, interface_name: str, description: str
    ) -> dict:
        """Set the description on an interface via gNMI Set."""
        path = f"/interfaces/interface[name={interface_name}]/config/description"
        return self.client.set([{"path": path, "value": description}])


def _extract_interface_data(response: list, interface_name: str) -> dict:
    """Pull the per-interface dict from a gnmic Get response list.

    Raises ValueError if *interface_name* is not found in the response.
    """
    try:
        notif = response[0]
        updates = notif["updates"]
        update = updates[0] if isinstance(updates, list) else updates
        values = update["values"]

        for key, val in values.items():
            if "interface" in key.lower() and isinstance(val, dict):
                # List of interfaces — find the matching one
                if "interface" in val and isinstance(val["interface"], list):
                    available = []
                    for iface in val["interface"]:
                        name = iface.get("name")
                        if name:
                            available.append(name)
                        if name == interface_name:
                            return iface
                    raise ValueError(
                        f"Interface '{interface_name}' not found in response. "
                        f"Available: {available}"
                    )
                # Single interface — validate name matches
                actual_name = val.get("name")
                if actual_name == interface_name:
                    return val
                if actual_name is None:
                    raise ValueError(
                        f"Interface '{interface_name}' not found on device "
                        f"(empty response — interface may not exist)"
                    )
                raise ValueError(
                    f"Response contains interface '{actual_name}', "
                    f"but requested '{interface_name}'"
                )

        return values
    except (KeyError, IndexError, TypeError):
        return {}
