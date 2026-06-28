"""Security posture service — reports gRPC/gNMI/gNOI security posture."""

from app.config import settings


class SecurityPostureService:
    """Reports gRPC security posture without performing any operations."""

    def report(self, device_id: str, gnoi_probe_result: dict | None = None) -> dict:
        """Analyze gRPC/gNMI security posture.

        Args:
            device_id: The device being assessed.
            gnoi_probe_result: Optional result from GnoiProbeService.probe()
                to enrich the report with certificate availability data.

        Returns:
            {
                "device_id": "...",
                "gnmi_transport": "INSECURE_LAB" | "TLS",
                "gnoi_certificate_support": "SUPPORTED" | "UNKNOWN" | "UNSUPPORTED",
                "risk_level": "LOW" | "MEDIUM" | "HIGH",
                "recommendations": [...]
            }
        """
        gnmi_transport = (
            "INSECURE_LAB" if settings.gnmi_insecure else "TLS"
        )

        # Determine gNOI certificate support from probe results
        gnoi_cert_support = "UNKNOWN"
        if gnoi_probe_result:
            services = gnoi_probe_result.get("services", {})
            gnoi_cert_support = services.get("certificate", "UNKNOWN")

        # Risk assessment
        recommendations: list[str] = []

        if gnmi_transport == "INSECURE_LAB":
            recommendations = [
                "gNMI is using insecure transport (no TLS). "
                "This is acceptable only in lab/sandbox environments.",
                "Use TLS for production gNMI and gNOI connectivity.",
                "Validate the server certificate.",
                "Use client certificate authentication when required "
                "by the environment.",
            ]
        else:
            recommendations = [
                "gNMI transport is using TLS — this is the recommended "
                "configuration for production deployments.",
            ]

        if gnoi_cert_support == "SUPPORTED":
            recommendations.append(
                "gNOI Certificate Management is available — consider enabling "
                "certificate-based authentication for production deployments."
            )
        elif gnoi_cert_support == "UNSUPPORTED":
            recommendations.append(
                "gNOI Certificate Management is not available on this device. "
                "Enable 'gnxi enable-gnoi' in the device configuration to "
                "expose gNOI services."
            )

        # Risk level
        if gnmi_transport == "TLS" and gnoi_cert_support == "SUPPORTED":
            risk_level = "LOW"
        elif gnmi_transport == "TLS":
            risk_level = "MEDIUM"
        elif gnmi_transport == "INSECURE_LAB":
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return {
            "device_id": device_id,
            "gnmi_transport": gnmi_transport,
            "gnoi_certificate_support": gnoi_cert_support,
            "risk_level": risk_level,
            "recommendations": recommendations,
        }
