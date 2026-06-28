"""gNOI client — probes gNOI service availability via gRPC reflection.

Uses ``grpcurl`` CLI via subprocess (same pattern as GnmiClient) to
avoid protobuf compilation.  Falls back gracefully when gNOI is
unreachable — common on sandbox devices that require authentication.
"""

from __future__ import annotations

import base64
import subprocess


class GnoiClientError(Exception):
    """Raised when a gNOI probe fails at the transport layer."""


# Known gNOI service fully-qualified names
GNOI_SERVICES = {
    "certificate": "gnoi.certificate.Certificate",
    "system": "gnoi.system.System",
    "os": "gnoi.os.OS",
    "factory_reset": "gnoi.factory_reset.FactoryReset",
}


class GnoiClient:
    """Lightweight gNOI capability probe via ``grpcurl``.

    No gNOI operations are performed — this is read-only probing.
    Tries Basic auth via gRPC metadata when credentials are provided,
    but falls back gracefully on servers that require native gRPC
    call credentials (e.g. Cisco sandbox).
    """

    def __init__(
        self,
        host: str,
        port: int = 50052,
        insecure: bool = True,
        username: str = "",
        password: str = "",
    ) -> None:
        self.host = host
        self.port = port
        self.insecure = insecure
        self.username = username
        self.password = password

    def probe(self) -> dict:
        """Probe gNOI service availability.

        Returns:
            {
                "reachable": bool,
                "services": {
                    "certificate": "SUPPORTED" | "UNSUPPORTED" | "UNKNOWN",
                    ...
                }
            }
        """
        available_services = self._list_services()

        if available_services is None:
            return {
                "reachable": False,
                "services": {name: "UNKNOWN" for name in GNOI_SERVICES},
            }

        services = {}
        for name, full_name in GNOI_SERVICES.items():
            services[name] = (
                "SUPPORTED" if full_name in available_services else "UNSUPPORTED"
            )

        return {"reachable": True, "services": services}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _list_services(self) -> list[str] | None:
        """List gRPC services via grpcurl. Returns None on failure."""
        target = f"{self.host}:{self.port}"
        args = ["grpcurl"]
        if self.insecure:
            args.append("-insecure")

        # Try Basic auth via metadata header if credentials are provided.
        # Some servers require native gRPC call credentials which grpcurl
        # doesn't support — in that case this returns None gracefully.
        if self.username and self.password:
            credentials = f"{self.username}:{self.password}"
            token = base64.b64encode(credentials.encode()).decode()
            args.extend(["-H", f"authorization:Basic {token}"])

        args.extend([target, "list"])

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            return None

        if result.returncode != 0:
            return None

        return [
            line.strip()
            for line in result.stdout.strip().split("\n")
            if line.strip()
        ]
