"""POST /v1/changes/interface-description — safe description change endpoint."""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import DeviceTarget
from app.services.change_service import ChangeService

from pydantic import BaseModel, Field


router = APIRouter(prefix="/v1/changes", tags=["changes"])
service = ChangeService()


class DescriptionChangeRequest(BaseModel):
    device_id: str
    interface: str
    description: str = Field(..., max_length=240)
    dry_run: bool = True

    model_config = {"extra": "forbid"}


class DescriptionChangeResponse(BaseModel):
    status: str
    dry_run: bool
    before: dict
    after: dict | None = None
    requested: dict | None = None
    set_result: dict | None = None
    note: str | None = None


@router.post(
    "/interface-description",
    response_model=DescriptionChangeResponse,
    summary="Set interface description (safe, audited)",
)
async def set_interface_description(request: DescriptionChangeRequest):
    """Change an interface description with safety guards.

    - **dry_run=true** (default): Plan the change without applying it.
    - **dry_run=false**: Apply the change, verify, and audit.

    The workflow reads current state → validates → optionally applies →
    reads back → returns before/after evidence.
    """
    device = DeviceTarget(
        device_id=request.device_id,
        host=settings.gnmi_host,
        port=settings.gnmi_port,
        username=settings.gnmi_username,
        password=settings.gnmi_password,
    )

    try:
        result = service.set_description(
            device=device,
            interface=request.interface,
            description=request.description,
            dry_run=request.dry_run,
        )
        return result

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
        raise HTTPException(
            status_code=500,
            detail=f"Description change failed: {exc}",
        )
