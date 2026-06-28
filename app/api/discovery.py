"""POST /v1/devices/discover — capability discovery endpoint."""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import DeviceTarget
from app.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/v1/devices", tags=["discovery"])
service = DiscoveryService()


@router.post("/discover", summary="Discover device capabilities via gNMI")
async def discover_device(device: DeviceTarget):
    """Probe a device's gNMI capabilities — supported YANG models, encodings,
    recommended adapter, and gNOI availability."""
    # Fill connection details from settings — same pattern as diagnostics endpoint.
    # DeviceTarget defaults (port=50052, etc.) are truthy and would shadow .env
    # values if we used a simple `or` fallback, so always pull from settings.
    device.host = device.host or settings.gnmi_host
    device.port = settings.gnmi_port
    device.username = device.username or settings.gnmi_username
    device.password = device.password or settings.gnmi_password

    try:
        result = service.discover(device)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Fixture data not available for device '{device.device_id}'. "
                f"Ensure fixture files exist or switch DEVICE_MODE to 'live'. "
                f"Details: {exc}"
            ),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {exc}")

    if not result.get("gnmi_reachable"):
        raise HTTPException(
            status_code=503,
            detail=f"Device '{device.device_id}' not reachable via gNMI. "
                   f"Check DEVICE_MODE, host, and credentials.",
        )

    return result
