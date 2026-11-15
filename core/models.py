"""Core data models for CSSA.

All platform adapters normalize their data into these common models
so the rule engine and UI can work platform-independently.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ──────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────

class Severity(str, Enum):
    """Finding severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    @property
    def rank(self) -> int:
        """Numeric rank for sorting (higher = more severe)."""
        return {
            Severity.CRITICAL: 5,
            Severity.HIGH: 4,
            Severity.MEDIUM: 3,
            Severity.LOW: 2,
            Severity.INFO: 1,
        }[self]

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.rank < other.rank


class FindingStatus(str, Enum):
    """Status of a security finding after evaluation."""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNAVAILABLE = "UNAVAILABLE"


class RiskLevel(str, Enum):
    """Overall risk classification bands."""
    EXCELLENT = "Excellent"
    GOOD = "Good"
    NEEDS_IMPROVEMENT = "Needs Improvement"
    HIGH_RISK = "High Risk"
    CRITICAL_RISK = "Critical Risk"


class Platform(str, Enum):
    """Supported operating-system platforms."""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


class ServiceStatus(str, Enum):
    """Service runtime status."""
    RUNNING = "Running"
    STOPPED = "Stopped"
    UNKNOWN = "Unknown"


class ServiceStartup(str, Enum):
    """Service startup type."""
    AUTOMATIC = "Automatic"
    MANUAL = "Manual"
    DISABLED = "Disabled"
    UNKNOWN = "Unknown"


class NetworkExposure(str, Enum):
    """Network exposure classification for a listening port."""
    LOCAL_ONLY = "LOCAL ONLY"
    NETWORK_EXPOSED = "NETWORK EXPOSED"
    UNKNOWN = "UNKNOWN"


class AuditMode(str, Enum):
    """Whether the audit uses real or demo data."""
    REAL = "REAL SYSTEM"
    DEMO_WINDOWS = "DEMO — WINDOWS"
    DEMO_LINUX = "DEMO — LINUX"
    DEMO_MACOS = "DEMO — MACOS"


# ──────────────────────────────────────────────
# Data Models
# ──────────────────────────────────────────────

@dataclass
class SystemInfo:
    """Normalized system information."""
    os_name: str = "Unavailable"
    os_version: str = "Unavailable"
    kernel_version: str = "Unavailable"
    architecture: str = "Unavailable"
    hostname: str = "Unavailable"
    current_user: str = "Unavailable"
    privilege_level: str = "Unavailable"
    uptime: str = "Unavailable"
    boot_time: str = "Unavailable"
    cpu_info: str = "Unavailable"
    cpu_count: int = 0
    total_memory_gb: float = 0.0
    available_memory_gb: float = 0.0
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    disk_free_gb: float = 0.0
    platform: Platform = Platform.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        d = {k: v for k, v in self.__dict__.items()}
        d["platform"] = self.platform.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SystemInfo:
        data = dict(data)
        if "platform" in data:
            data["platform"] = Platform(data["platform"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class UserAccount:
    """Normalized local user account."""
    username: str
    uid: str = ""
    gid: str = ""
    groups: list[str] = field(default_factory=list)
    is_admin: bool = False
    is_disabled: bool = False
    is_guest: bool = False
    home_directory: str = ""
    shell: str = ""
    description: str = ""
    last_login: str = "Unavailable"

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserAccount:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ProcessInfo:
    """Normalized process information."""
    pid: int
    name: str
    exe_path: str = ""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    parent_pid: int = 0
    username: str = ""
    start_time: str = ""
    status: str = ""
    cmdline: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessInfo:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ServiceInfo:
    """Normalized service information."""
    name: str
    display_name: str = ""
    status: ServiceStatus = ServiceStatus.UNKNOWN
    startup_type: ServiceStartup = ServiceStartup.UNKNOWN
    description: str = ""
    executable: str = ""
    user: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["status"] = self.status.value
        d["startup_type"] = self.startup_type.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServiceInfo:
        data = dict(data)
        if "status" in data and isinstance(data["status"], str):
            data["status"] = ServiceStatus(data["status"])
        if "startup_type" in data and isinstance(data["startup_type"], str):
            data["startup_type"] = ServiceStartup(data["startup_type"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class FirewallStatus:
    """Normalized firewall status."""
    enabled: bool = False
    provider: str = "Unknown"
    profiles: dict[str, bool] = field(default_factory=dict)
    rules_count: int = 0
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FirewallStatus:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class NetworkConnection:
    """Normalized network connection / listening port."""
    local_address: str
    local_port: int
    protocol: str = "TCP"
    remote_address: str = ""
    remote_port: int = 0
    state: str = "LISTEN"
    pid: int = 0
    process_name: str = ""
    exposure: NetworkExposure = NetworkExposure.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["exposure"] = self.exposure.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetworkConnection:
        data = dict(data)
        if "exposure" in data and isinstance(data["exposure"], str):
            data["exposure"] = NetworkExposure(data["exposure"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PacketThreat:
    """Normalized security threat or anomaly identified in captured network traffic."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = ""
    threat_type: str = "UNKNOWN"
    protocol: str = "TCP"
    source_ip: str = ""
    source_port: int = 0
    dest_ip: str = ""
    dest_port: int = 0
    severity: Severity = Severity.MEDIUM
    description: str = ""
    recommendation: str = ""
    evidence: str = ""
    packet_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["severity"] = self.severity.value if isinstance(self.severity, Severity) else str(self.severity)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PacketThreat:
        data = dict(data)
        if "severity" in data and isinstance(data["severity"], str):
            try:
                data["severity"] = Severity(data["severity"])
            except ValueError:
                data["severity"] = Severity.MEDIUM
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PacketCaptureAudit:
    """Normalized packet capture session summary and threat findings."""
    capture_available: bool = False
    capture_source: str = "Unavailable"
    duration_seconds: int = 0
    total_packets_captured: int = 0
    threats: list[PacketThreat] = field(default_factory=list)
    protocols_seen: dict[str, int] = field(default_factory=dict)
    details: str = ""
    wireshark_path: str = ""
    pcap_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["threats"] = [t.to_dict() if hasattr(t, "to_dict") else t for t in self.threats]
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PacketCaptureAudit:
        data = dict(data)
        if "threats" in data and isinstance(data["threats"], list):
            data["threats"] = [
                PacketThreat.from_dict(t) if isinstance(t, dict) else t
                for t in data["threats"]
            ]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})



@dataclass
class FilePermission:
    """Normalized file permission information."""
    path: str
    owner: str = ""
    group: str = ""
    permissions: str = ""
    numeric_mode: str = ""
    is_suid: bool = False
    is_sgid: bool = False
    is_world_writable: bool = False
    risk: str = ""
    reason: str = ""
    acl_entries: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FilePermission:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class StartupEntry:
    """Normalized startup / persistence entry."""
    name: str
    location: str = ""
    command: str = ""
    user: str = ""
    enabled: bool = True
    source: str = ""
    risk: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StartupEntry:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SecurityPolicy:
    """A single security policy check result."""
    name: str
    category: str = ""
    current_value: str = ""
    recommended_value: str = ""
    compliant: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SecurityPolicy:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ──────────────────────────────────────────────
# Security Rule
# ──────────────────────────────────────────────

@dataclass
class SecurityRule:
    """A configurable security rule definition."""
    rule_id: str
    title: str
    description: str = ""
    category: str = ""
    severity: Severity = Severity.INFO
    platforms: list[str] = field(default_factory=lambda: ["windows", "linux"])
    condition_type: str = ""
    condition_params: dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["severity"] = self.severity.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SecurityRule:
        data = dict(data)
        if "severity" in data and isinstance(data["severity"], str):
            data["severity"] = Severity(data["severity"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ──────────────────────────────────────────────
# Finding
# ──────────────────────────────────────────────

@dataclass
class Finding:
    """A security finding produced by the rule engine."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    title: str = ""
    category: str = ""
    severity: Severity = Severity.INFO
    status: FindingStatus = FindingStatus.PASS
    platform: str = ""
    description: str = ""
    evidence: str = ""
    rationale: str = ""
    recommendation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["severity"] = self.severity.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Finding:
        data = dict(data)
        if "severity" in data and isinstance(data["severity"], str):
            data["severity"] = Severity(data["severity"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = FindingStatus(data["status"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ──────────────────────────────────────────────
# Scores
# ──────────────────────────────────────────────

@dataclass
class CategoryScore:
    """Score for a single audit category."""
    category: str
    score: int = 100
    max_score: int = 100
    findings_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CategoryScore:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AuditScore:
    """Overall audit score with category breakdowns."""
    overall_score: int = 100
    risk_level: RiskLevel = RiskLevel.EXCELLENT
    category_scores: list[CategoryScore] = field(default_factory=list)
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["risk_level"] = self.risk_level.value if isinstance(self.risk_level, RiskLevel) else str(self.risk_level)
        d["category_scores"] = [cs.to_dict() if hasattr(cs, "to_dict") else cs for cs in self.category_scores]
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditScore:
        data = dict(data)
        if "risk_level" in data and isinstance(data["risk_level"], str):
            try:
                data["risk_level"] = RiskLevel(data["risk_level"])
            except ValueError:
                data["risk_level"] = RiskLevel.EXCELLENT
        if "category_scores" in data and isinstance(data["category_scores"], list):
            data["category_scores"] = [
                CategoryScore.from_dict(cs) if isinstance(cs, dict) else cs
                for cs in data["category_scores"]
            ]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ──────────────────────────────────────────────
# Audit Result (aggregate)
# ──────────────────────────────────────────────

@dataclass
class AuditResult:
    """Complete result of a security audit."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    mode: AuditMode = AuditMode.REAL
    system_info: SystemInfo = field(default_factory=SystemInfo)
    users: list[UserAccount] = field(default_factory=list)
    processes: list[ProcessInfo] = field(default_factory=list)
    services: list[ServiceInfo] = field(default_factory=list)
    firewall: FirewallStatus = field(default_factory=FirewallStatus)
    network_connections: list[NetworkConnection] = field(default_factory=list)
    file_permissions: list[FilePermission] = field(default_factory=list)
    startup_entries: list[StartupEntry] = field(default_factory=list)
    security_policies: list[SecurityPolicy] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    score: AuditScore = field(default_factory=AuditScore)
    packet_capture: PacketCaptureAudit = field(default_factory=PacketCaptureAudit)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "mode": self.mode.value if isinstance(self.mode, AuditMode) else str(self.mode),
            "system_info": self.system_info.to_dict() if hasattr(self.system_info, "to_dict") else self.system_info,
            "users": [u.to_dict() if hasattr(u, "to_dict") else u for u in self.users],
            "processes": [p.to_dict() if hasattr(p, "to_dict") else p for p in self.processes],
            "services": [s.to_dict() if hasattr(s, "to_dict") else s for s in self.services],
            "firewall": self.firewall.to_dict() if hasattr(self.firewall, "to_dict") else self.firewall,
            "network_connections": [n.to_dict() if hasattr(n, "to_dict") else n for n in self.network_connections],
            "file_permissions": [f.to_dict() if hasattr(f, "to_dict") else f for f in self.file_permissions],
            "startup_entries": [e.to_dict() if hasattr(e, "to_dict") else e for e in self.startup_entries],
            "security_policies": [p.to_dict() if hasattr(p, "to_dict") else p for p in self.security_policies],
            "findings": [f.to_dict() if hasattr(f, "to_dict") else f for f in self.findings],
            "score": self.score.to_dict() if hasattr(self.score, "to_dict") else self.score,
            "packet_capture": self.packet_capture.to_dict() if hasattr(self.packet_capture, "to_dict") else self.packet_capture,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditResult:
        data = dict(data)
        if "mode" in data and isinstance(data["mode"], str):
            try:
                data["mode"] = AuditMode(data["mode"])
            except ValueError:
                data["mode"] = AuditMode.REAL
        if "system_info" in data and isinstance(data["system_info"], dict):
            data["system_info"] = SystemInfo.from_dict(data["system_info"])
        if "users" in data and isinstance(data["users"], list):
            data["users"] = [UserAccount.from_dict(u) if isinstance(u, dict) else u for u in data["users"]]
        if "processes" in data and isinstance(data["processes"], list):
            data["processes"] = [ProcessInfo.from_dict(p) if isinstance(p, dict) else p for p in data["processes"]]
        if "services" in data and isinstance(data["services"], list):
            data["services"] = [ServiceInfo.from_dict(s) if isinstance(s, dict) else s for s in data["services"]]
        if "firewall" in data and isinstance(data["firewall"], dict):
            data["firewall"] = FirewallStatus.from_dict(data["firewall"])
        if "network_connections" in data and isinstance(data["network_connections"], list):
            data["network_connections"] = [NetworkConnection.from_dict(n) if isinstance(n, dict) else n for n in data["network_connections"]]
        if "file_permissions" in data and isinstance(data["file_permissions"], list):
            data["file_permissions"] = [FilePermission.from_dict(f) if isinstance(f, dict) else f for f in data["file_permissions"]]
        if "startup_entries" in data and isinstance(data["startup_entries"], list):
            data["startup_entries"] = [StartupEntry.from_dict(e) if isinstance(e, dict) else e for e in data["startup_entries"]]
        if "security_policies" in data and isinstance(data["security_policies"], list):
            data["security_policies"] = [SecurityPolicy.from_dict(p) if isinstance(p, dict) else p for p in data["security_policies"]]
        if "findings" in data and isinstance(data["findings"], list):
            data["findings"] = [Finding.from_dict(f) if isinstance(f, dict) else f for f in data["findings"]]
        if "score" in data and isinstance(data["score"], dict):
            data["score"] = AuditScore.from_dict(data["score"])
        if "packet_capture" in data and isinstance(data["packet_capture"], dict):
            data["packet_capture"] = PacketCaptureAudit.from_dict(data["packet_capture"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ──────────────────────────────────────────────
# Baseline
# ──────────────────────────────────────────────

@dataclass
class BaselineItem:
    """A single item stored in a baseline snapshot."""
    category: str
    key: str
    value: str
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaselineItem:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class BaselineDiff:
    """Differences between a baseline and the current audit."""
    added: list[BaselineItem] = field(default_factory=list)
    removed: list[BaselineItem] = field(default_factory=list)
    changed: list[tuple[BaselineItem, BaselineItem]] = field(default_factory=list)
