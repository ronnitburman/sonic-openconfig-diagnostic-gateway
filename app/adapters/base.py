from typing import Protocol, runtime_checkable
from app.models import InterfaceSnapshot


@runtime_checkable
class DeviceAdapter(Protocol):
    """Protocol for device interaction — live gNMI or fixture."""

    def get_device_id(self) -> str:
        """Return the device identifier this adapter is bound to."""
        ...

    def discover_capabilities(self) -> dict:
        """Return capability information including supported models."""
        ...

    def get_interface_snapshot(self, interface_name: str) -> InterfaceSnapshot:
        """Fetch and normalize interface state."""
        ...

    def set_interface_description(
        self,
        interface_name: str,
        description: str,
    ) -> dict:
        """Set the description on an interface. Returns before/after evidence."""
        ...
