"""gNOI probe service — selects live probe or fixture based on DEVICE_MODE."""

import json
from pathlib import Path

from app.config import settings
from app.models import DeviceTarget
from app.adapters.gnoi_client import GnoiClient, GnoiClientError


FIXTURE_DIR = Path("fixtures/gnoi")


class GnoiProbeService:
    """Probes gNOI service availability without performing any operations.

    In fixture mode, reads pre-captured results from fixtures/gnoi/.
    In live mode, uses GnoiClient (grpcurl) to list gRPC services.
    """

    def probe(self, device: DeviceTarget) -> dict:
        """Determine gNOI reachability and available services.

        Returns a dict matching the API contract:
        {
            "device_id": "...",
            "gnoi_reachable": bool,
            "services": {
                "certificate": "SUPPORTED|UNSUPPORTED|UNKNOWN",
                "system": "...",
                "os": "NOT_TESTED",
                "factory_reset": "INTENTIONALLY_DISABLED"
            },
            "notes": [...]
        }
        """
        if settings.device_mode == "fixture":
            return self._probe_fixture(device)
        return self._probe_live(device)

    def _probe_fixture(self, device: DeviceTarget) -> dict:
        """Read pre-captured gNOI probe result."""
        path = FIXTURE_DIR / f"{device.device_id}.json"
        if not path.exists():
            return {
                "device_id": device.device_id,
                "gnoi_reachable": False,
                "services": {
                    "certificate": "UNKNOWN",
                    "system": "UNKNOWN",
                    "os": "NOT_TESTED",
                    "factory_reset": "INTENTIONALLY_DISABLED",
                },
                "notes": [
                    f"No gNOI fixture found for device '{device.device_id}'.",
                    "Destructive gNOI operations are intentionally disabled.",
                ],
            }

        with open(path) as f:
            fixture = json.load(f)

        # Always enforce safety constraints regardless of fixture content
        fixture["services"]["os"] = "NOT_TESTED"
        fixture["services"]["factory_reset"] = "INTENTIONALLY_DISABLED"

        notes = fixture.get("notes", [])
        if not any("intentionally disabled" in n.lower() for n in notes):
            notes.append(
                "Destructive gNOI operations (factory reset, OS install, reboot) "
                "are intentionally disabled."
            )
        fixture["notes"] = notes

        # Normalize keys expected by API
        fixture.pop("probe_timestamp", None)
        return fixture

    def _probe_live(self, device: DeviceTarget) -> dict:
        """Probe gNOI via native gRPC reflection."""
        host = device.host or settings.gnoi_host or settings.gnmi_host
        port = device.port or settings.gnoi_port or settings.gnmi_port
        username = device.username or settings.gnmi_username
        password = device.password or settings.gnmi_password
        insecure = settings.gnmi_insecure  # gNOI shares gNMI transport settings

        client = GnoiClient(
            host=host,
            port=port,
            insecure=insecure,
            username=username,
            password=password,
        )

        try:
            result = client.probe()
        except GnoiClientError:
            result = {"reachable": False, "services": {}}

        services = result.get("services", {})
        if not result["reachable"] and not services:
            services = {
                "certificate": "UNKNOWN",
                "system": "UNKNOWN",
            }

        # Explicitly mark dangerous services as disabled
        services["os"] = "NOT_TESTED"
        services["factory_reset"] = "INTENTIONALLY_DISABLED"

        notes = [
            "Destructive gNOI operations (factory reset, OS install, reboot) "
            "are intentionally disabled.",
        ]
        if services.get("certificate") == "SUPPORTED":
            notes.append(
                "Certificate Management service detected. Rotation and "
                "installation operations are NOT performed by this gateway."
            )

        return {
            "device_id": device.device_id,
            "gnoi_reachable": result["reachable"],
            "services": services,
            "notes": notes,
        }
