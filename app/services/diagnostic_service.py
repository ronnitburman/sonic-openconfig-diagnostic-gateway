"""Orchestrates adapter retrieval + diagnostic evaluation."""

from app.models import DeviceTarget, InterfaceDiagnosticRequest, DiagnosticReport
from app.adapters import create_adapter
from app.diagnostics.report_builder import ReportBuilder


class DiagnosticService:
    """Runs interface diagnostics end-to-end."""

    def __init__(self) -> None:
        self.report_builder = ReportBuilder()

    def diagnose(
        self,
        device: DeviceTarget,
        request: InterfaceDiagnosticRequest,
    ) -> DiagnosticReport:
        adapter = create_adapter(device)

        try:
            snapshot = adapter.get_interface_snapshot(request.interface)
        except (ValueError, FileNotFoundError):
            raise
        except Exception as exc:
            raise ValueError(f"Failed to retrieve interface state: {exc}") from exc

        return self.report_builder.build(
            snapshot=snapshot,
            expected=request.expected,
            device_id=request.device_id,
        )
