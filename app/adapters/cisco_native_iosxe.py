"""Live adapter that retrieves interface state via Cisco-IOS-XE YANG paths.

Used when OpenConfig models are not available on the target device.
"""

from app.adapters.gnmi_client import GnmiClient
from app.adapters.openconfig_iosxe import _extract_interface_data
from app.adapters.parsers import parse_cisco_native_response
from app.models import InterfaceSnapshot


class CiscoNativeIOSXEAdapter:
    """Uses Cisco-IOS-XE-interfaces-oper paths for interface state."""

    def __init__(self, client: GnmiClient):
        self.client = client

    def discover_capabilities(self) -> dict:
        """Return gNMI capability information including supported models."""
        return self.client.capabilities()

    def get_interface_snapshot(self, interface_name: str) -> InterfaceSnapshot:
        # Cisco-native paths use the module name as origin — however,
        # many IOS XE builds reject origin-based paths.  If that fails
        # the caller gets a GnmiClientError which bubbles up as 503.
        path = f"Cisco-IOS-XE-interfaces-oper:/interfaces/interface[name={interface_name}]"
        raw_list = self.client.get(path)
        iface_data = _extract_interface_data(raw_list, interface_name)
        return parse_cisco_native_response(iface_data, interface_name)
