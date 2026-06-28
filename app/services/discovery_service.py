"""Business logic for device capability discovery."""

from app.models import DeviceTarget
from app.adapters import create_adapter


class DiscoveryService:
    """Handles device capability discovery via gNMI."""

    def discover(self, device: DeviceTarget) -> dict:
        try:
            adapter = create_adapter(device)
            caps = adapter.discover_capabilities()
        except ValueError:
            raise  # validation errors (unknown device, etc.) → 422
        except Exception as exc:
            return {
                "device_id": device.device_id,
                "gnmi_reachable": False,
                "error": str(exc),
                "supported_encodings": [],
                "model_support": {
                    "openconfig_interfaces": False,
                    "cisco_native_interfaces": False,
                },
                "recommended_adapter": "none",
                "gnoi": {
                    "reachable": False,
                    "certificate_service": "unknown",
                },
            }

        model_names = [m["name"] for m in caps.get("supported-models", [])]
        oc_supported = any("openconfig-interfaces" in m for m in model_names)
        cn_supported = any("Cisco-IOS-XE-interfaces-oper" in m for m in model_names)

        recommended = (
            "openconfig_iosxe" if oc_supported
            else "cisco_native_iosxe" if cn_supported
            else "none"
        )

        return {
            "device_id": device.device_id,
            "gnmi_reachable": True,
            "supported_encodings": caps.get("supported_encodings", ["JSON_IETF"]),
            "model_support": {
                "openconfig_interfaces": oc_supported,
                "cisco_native_interfaces": cn_supported,
            },
            "recommended_adapter": recommended,
            "gnoi": {
                "reachable": False,
                "certificate_service": "unknown",
            },
        }
