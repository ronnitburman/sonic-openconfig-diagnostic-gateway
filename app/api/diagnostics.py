"""POST /v1/diagnostics/interface — interface diagnostic endpoint."""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import DeviceTarget, InterfaceDiagnosticRequest, DiagnosticReport
from app.services.diagnostic_service import DiagnosticService

router = APIRouter(prefix="/v1/diagnostics", tags=["diagnostics"])
service = DiagnosticService()


@router.post(
    "/interface",
    response_model=DiagnosticReport,
    summary="Diagnose an interface",
)
async def diagnose_interface(request: InterfaceDiagnosticRequest):
    """Run diagnostic checks against an interface.

    Retrieves interface state via gNMI (or fixture), normalizes it into a
    vendor-neutral snapshot, and evaluates all registered diagnostic rules.

    Returns a structured report with overall health and per-rule findings.
    """
    device = DeviceTarget(
        device_id=request.device_id,
        host=settings.gnmi_host,
        port=settings.gnmi_port,
        username=settings.gnmi_username,
        password=settings.gnmi_password,
    )

    try:
        return service.diagnose(device, request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Fixture data not available for device '{request.device_id}'. "
                f"Ensure fixture files exist or switch DEVICE_MODE to 'live'. "
                f"Details: {exc}"
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Diagnostic failed: {exc}")
