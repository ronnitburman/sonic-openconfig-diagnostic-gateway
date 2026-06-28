"""Operations API — gNOI probe and gRPC security posture endpoints."""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import DeviceTarget
from app.services.gnoi_probe_service import GnoiProbeService
from app.services.security_posture_service import SecurityPostureService

from pydantic import BaseModel


router = APIRouter(prefix="/v1/operations", tags=["operations"])

gnoi_service = GnoiProbeService()
security_service = SecurityPostureService()


# ── Request models ──────────────────────────────────────────────────

class GnoiProbeRequest(BaseModel):
    device_id: str


class SecurityPostureRequest(BaseModel):
    device_id: str


# ── Endpoints ───────────────────────────────────────────────────────

@router.post(
    "/gnoi/probe",
    summary="Probe gNOI service availability",
)
async def probe_gnoi(request: GnoiProbeRequest):
    """Probe the target device for gNOI service availability.

    Uses gRPC service listing to detect whether gNOI services
    (Certificate, System, OS, Factory Reset) are advertised.

    **Safety:** No gNOI operations are performed. This is read-only probing.
    Destructive services (factory reset, OS) are always reported as
    intentionally disabled regardless of what the device advertises.
    """
    device = DeviceTarget(
        device_id=request.device_id,
        host=settings.gnmi_host,
        port=settings.gnoi_port or settings.gnmi_port,
        username=settings.gnmi_username,
        password=settings.gnmi_password,
        insecure=settings.gnmi_insecure,
    )

    try:
        return gnoi_service.probe(device)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"gNOI probe failed: {exc}",
        )


@router.post(
    "/grpc-security",
    summary="Report gRPC/gNMI security posture",
)
async def grpc_security(request: SecurityPostureRequest):
    """Report the security posture of the gNMI/gNOI connection.

    Analyzes:
    - Whether transport is TLS or insecure (lab)
    - Whether gNOI certificate services are available
    - Overall risk level with actionable recommendations

    Optionally runs a gNOI probe first to enrich the report with
    certificate management availability data.
    """
    device = DeviceTarget(
        device_id=request.device_id,
        host=settings.gnmi_host,
        port=settings.gnoi_port or settings.gnmi_port,
        username=settings.gnmi_username,
        password=settings.gnmi_password,
        insecure=settings.gnmi_insecure,
    )

    # Optionally probe gNOI for richer report
    gnoi_result = None
    try:
        gnoi_result = gnoi_service.probe(device)
    except Exception:
        pass  # Security report works without gNOI data

    return security_service.report(request.device_id, gnoi_result)
