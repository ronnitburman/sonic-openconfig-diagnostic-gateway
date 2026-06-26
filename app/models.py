from pydantic import BaseModel, Field
from typing import Optional


class DeviceTarget(BaseModel):
    """Connection details for a network device."""
    device_id: str
    host: str = ""
    port: int = 50052
    username: str = ""
    password: str = ""
    insecure: bool = True
    preferred_model_family: str = "openconfig"


class InterfaceSnapshot(BaseModel):
    """Vendor-neutral interface state. All adapters MUST populate this."""
    name: str
    description: Optional[str] = None
    enabled: Optional[bool] = None
    admin_status: Optional[str] = None
    oper_status: Optional[str] = None
    speed_mbps: Optional[int] = None
    mtu: Optional[int] = None
    in_errors: Optional[int] = None
    out_errors: Optional[int] = None
    in_discards: Optional[int] = None
    out_discards: Optional[int] = None
    last_change: Optional[str] = None
    source_model: str
    source_protocol: str = "gnmi"


class InterfaceExpectation(BaseModel):
    """What the operator expects the interface to look like."""
    enabled: Optional[bool] = None
    oper_status: Optional[str] = None
    speed_mbps: Optional[int] = None


class InterfaceDiagnosticRequest(BaseModel):
    device_id: str
    interface: str
    expected: InterfaceExpectation = Field(default_factory=InterfaceExpectation)


class DiagnosticFinding(BaseModel):
    rule_id: str
    severity: str
    title: str
    evidence: dict
    recommendation: str


class DiagnosticReport(BaseModel):
    report_id: str
    device_id: str
    interface: str
    overall_health: str
    source_model: str
    observed: InterfaceSnapshot
    findings: list[DiagnosticFinding]
    generated_at: str
