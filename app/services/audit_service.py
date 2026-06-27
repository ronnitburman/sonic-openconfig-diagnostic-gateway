"""Audit service — writes structured, append-only audit records."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings


class AuditService:
    """Writes JSON Lines audit records to a local file."""

    def __init__(self, audit_path: str | None = None) -> None:
        self._path = Path(audit_path or settings.audit_log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        action: str,
        device_id: str,
        interface: str,
        before: dict,
        after: dict,
        status: str,
        dry_run: bool = False,
    ) -> dict:
        """Write a single audit entry and return it."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "device_id": device_id,
            "interface": interface,
            "dry_run": dry_run,
            "status": status,
            "before": before,
            "after": after,
        }

        # Append as a single JSON line
        with open(self._path, "a") as fh:
            fh.write(json.dumps(entry) + "\n")

        return entry
