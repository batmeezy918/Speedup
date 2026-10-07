"""Core state/capability model for the native Android Control Kernel."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class Capability:
    name: str
    domain: str
    provider: str
    requires_user_grant: bool = False
    notes: str = ""

@dataclass
class DeviceState:
    timestamp_ns: int
    capabilities: List[Capability] = field(default_factory=list)
    telemetry: Dict[str, Any] = field(default_factory=dict)
    observations: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class OperationRequest:
    operation: str
    domain: str
    args: Dict[str, Any] = field(default_factory=dict)
