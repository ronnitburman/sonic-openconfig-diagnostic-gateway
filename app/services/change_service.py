"""Business logic for safe interface description changes."""

from app.models import DeviceTarget
from app.adapters import create_adapter
from app.services.audit_service import AuditService


class ChangeService:
    """Orchestrates safe gNMI Set operations with before/after verification."""

    MAX_DESCRIPTION_LENGTH = 240

    def __init__(self, audit_service: AuditService | None = None) -> None:
        self._audit = audit_service or AuditService()

    def set_description(
        self,
        device: DeviceTarget,
        interface: str,
        description: str,
        dry_run: bool = False,
    ) -> dict:
        """Change an interface description, with safety guards.

        Workflow:
          1. Read current interface state (Get).
          2. Validate the request.
          3. If dry_run → return plan only.
          4. Execute gNMI Set.
          5. Read again (Get) to verify.
          6. Write audit record.
        """
        adapter = create_adapter(device)

        # ── 1. Read current state ──────────────────────────────────
        try:
            snapshot = adapter.get_interface_snapshot(interface)
        except FileNotFoundError:
            raise  # propagate fixture-missing errors → 503
        except Exception as exc:
            raise ValueError(
                f"Unable to read interface '{interface}' on device "
                f"'{device.device_id}': {exc}"
            ) from exc

        current_description = snapshot.description or ""

        # ── 2. Validate ─────────────────────────────────────────────
        # Ensure the interface actually exists on the device.
        if snapshot.admin_status is None and snapshot.oper_status is None:
            raise ValueError(
                f"Interface '{interface}' not found on device "
                f"'{device.device_id}'. The interface may not exist."
            )

        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description exceeds maximum length of "
                f"{self.MAX_DESCRIPTION_LENGTH} characters."
            )

        if description == current_description:
            return {
                "status": "skipped",
                "dry_run": dry_run,
                "before": {"description": current_description},
                "after": {"description": current_description},
                "note": "Description unchanged — matches current value.",
            }

        # ── 3. Dry-run → plan only ──────────────────────────────────
        if dry_run:
            result = {
                "status": "planned",
                "dry_run": True,
                "before": {"description": current_description},
                "requested": {"description": description},
            }
            self._audit.record(
                action="set_interface_description",
                device_id=device.device_id,
                interface=interface,
                before={"description": current_description},
                after={"description": description},
                status="planned",
                dry_run=True,
            )
            return result

        # ── 4. Execute Set ──────────────────────────────────────────
        set_result = adapter.set_interface_description(interface, description)

        # ── 5. Read-back verification ────────────────────────────────
        try:
            verify_snapshot = adapter.get_interface_snapshot(interface)
            verified_description = verify_snapshot.description or ""
        except Exception:
            verified_description = None

        # ── 6. Build result ─────────────────────────────────────────
        result = {
            "status": "applied" if verified_description == description else "unverified",
            "dry_run": False,
            "before": {"description": current_description},
            "after": {"description": verified_description},
            "set_result": set_result,
        }

        self._audit.record(
            action="set_interface_description",
            device_id=device.device_id,
            interface=interface,
            before={"description": current_description},
            after={"description": verified_description},
            status=result["status"],
            dry_run=False,
        )

        return result
