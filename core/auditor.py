"""Main audit controller — ties platform adapters, rules, scoring, and demo mode together."""

from __future__ import annotations

import json
import logging
import platform
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from core.exceptions import PlatformNotSupportedError
from core.models import (
    AuditMode,
    AuditResult,
    AuditScore,
    FilePermission,
    Finding,
    FirewallStatus,
    NetworkConnection,
    PacketCaptureAudit,
    PacketThreat,
    Platform,
    ProcessInfo,
    SecurityPolicy,
    ServiceInfo,
    ServiceStartup,
    ServiceStatus,
    StartupEntry,
    SystemInfo,
    UserAccount,
)
from core.rule_engine import RuleEngine
from core.scanner import Scanner
from core.scoring import ScoringSystem

logger = logging.getLogger(__name__)


class Auditor:
    """Top-level controller that orchestrates a full security audit."""

    def __init__(self, rules_dir: Path, fixtures_dir: Path) -> None:
        self.rules_dir = rules_dir
        self.fixtures_dir = fixtures_dir
        self.rule_engine = RuleEngine(rules_dir)
        self.scoring = ScoringSystem()

    # ── helpers ───────────────────────────────────────────────

    @staticmethod
    def detect_platform() -> Platform:
        sys_plat = platform.system().lower()
        if sys_plat == "windows":
            return Platform.WINDOWS
        elif sys_plat == "linux":
            return Platform.LINUX
        elif sys_plat == "darwin":
            return Platform.MACOS
        return Platform.UNKNOWN

    def _create_adapter(self, plat: Platform):
        """Instantiate the correct platform adapter."""
        if plat == Platform.WINDOWS:
            try:
                from platforms.windows import WindowsSecurityAdapter
                return WindowsSecurityAdapter()
            except Exception as exc:
                logger.error("Failed to load Windows adapter: %s", exc)
                raise PlatformNotSupportedError(f"Windows adapter error: {exc}")
        elif plat == Platform.LINUX:
            try:
                from platforms.linux import LinuxSecurityAdapter
                return LinuxSecurityAdapter()
            except Exception as exc:
                logger.error("Failed to load Linux adapter: %s", exc)
                raise PlatformNotSupportedError(f"Linux adapter error: {exc}")
        elif plat == Platform.MACOS:
            try:
                from platforms.macos import MacOSSecurityAdapter
                return MacOSSecurityAdapter()
            except Exception as exc:
                logger.error("Failed to load macOS adapter: %s", exc)
                raise PlatformNotSupportedError(f"macOS adapter error: {exc}")
        raise PlatformNotSupportedError(f"Unsupported platform: {plat}")

    # ── public API ────────────────────────────────────────────

    def run_audit(self, mode: AuditMode) -> AuditResult:
        """Execute a full security audit and return the scored result."""
        logger.info("Starting audit — mode=%s", mode.value)

        if mode == AuditMode.REAL:
            result = self._real_audit()
        elif mode == AuditMode.DEMO_WINDOWS:
            result = self._demo_audit(Platform.WINDOWS)
        elif mode == AuditMode.DEMO_LINUX:
            result = self._demo_audit(Platform.LINUX)
        elif mode == AuditMode.DEMO_MACOS:
            result = self._demo_audit(Platform.MACOS)
        else:
            raise ValueError(f"Unknown audit mode: {mode}")

        # Evaluate rules → findings
        plat = result.system_info.platform
        findings = self.rule_engine.evaluate_rules(result, plat)
        result.findings = findings

        # Score
        result.score = self.scoring.calculate_score(findings)

        logger.info(
            "Audit complete — score=%s  risk=%s  findings=%d",
            result.score.overall_score,
            result.score.risk_level.value,
            len(findings),
        )
        return result

    # ── real audit ────────────────────────────────────────────

    def _real_audit(self) -> AuditResult:
        plat = self.detect_platform()
        adapter = self._create_adapter(plat)
        scanner = Scanner(adapter)
        scan = scanner.scan()

        return AuditResult(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            mode=AuditMode.REAL,
            system_info=scan.get("system_info") or SystemInfo(),
            users=scan.get("users", []),
            processes=scan.get("processes", []),
            services=scan.get("services", []),
            firewall=scan.get("firewall") or FirewallStatus(),
            network_connections=scan.get("network_connections", []),
            file_permissions=scan.get("file_permissions", []),
            startup_entries=scan.get("startup_entries", []),
            security_policies=scan.get("security_policies", []),
            packet_capture=scan.get("packet_capture") or PacketCaptureAudit(),
        )

    # ── demo audit ────────────────────────────────────────────

    def _demo_audit(self, plat: Platform) -> AuditResult:
        if plat == Platform.WINDOWS:
            filename = "windows_demo.json"
            audit_mode = AuditMode.DEMO_WINDOWS
        elif plat == Platform.LINUX:
            filename = "linux_demo.json"
            audit_mode = AuditMode.DEMO_LINUX
        else:
            filename = "macos_demo.json"
            audit_mode = AuditMode.DEMO_MACOS

        fixture_path = self.fixtures_dir / filename

        logger.info("Loading demo fixture: %s", fixture_path)

        with open(fixture_path, "r", encoding="utf-8") as fh:
            data: dict[str, Any] = json.load(fh)

        return AuditResult(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            mode=audit_mode,
            system_info=self._load_system_info(data.get("system_info", {})),
            users=self._load_list(data.get("users", []), UserAccount),
            processes=self._load_list(data.get("processes", []), ProcessInfo),
            services=self._load_services(data.get("services", [])),
            firewall=self._load_firewall(data.get("firewall", {})),
            network_connections=self._load_connections(data.get("network_connections", [])),
            file_permissions=self._load_list(data.get("file_permissions", []), FilePermission),
            startup_entries=self._load_list(data.get("startup_entries", []), StartupEntry),
            security_policies=self._load_list(data.get("security_policies", []), SecurityPolicy),
            packet_capture=self._load_packet_capture(data.get("packet_capture", {})),
        )

    # ── fixture loaders ───────────────────────────────────────

    @staticmethod
    def _load_packet_capture(d: dict) -> PacketCaptureAudit:
        if not d:
            return PacketCaptureAudit()
        return PacketCaptureAudit.from_dict(d)


    @staticmethod
    def _load_system_info(d: dict) -> SystemInfo:
        d = dict(d)
        if "platform" in d:
            d["platform"] = Platform(d["platform"])
        valid = {f for f in SystemInfo.__dataclass_fields__}
        return SystemInfo(**{k: v for k, v in d.items() if k in valid})

    @staticmethod
    def _load_list(items: list[dict], cls):
        result = []
        valid = {f for f in cls.__dataclass_fields__}
        for item in items:
            try:
                filtered = {k: v for k, v in item.items() if k in valid}
                result.append(cls(**filtered))
            except Exception as exc:
                logger.warning("Skipping invalid %s record: %s", cls.__name__, exc)
        return result

    @staticmethod
    def _load_services(items: list[dict]) -> list[ServiceInfo]:
        result = []
        for item in items:
            try:
                d = dict(item)
                if "status" in d and isinstance(d["status"], str):
                    try:
                        d["status"] = ServiceStatus(d["status"])
                    except ValueError:
                        d["status"] = ServiceStatus.UNKNOWN
                if "startup_type" in d and isinstance(d["startup_type"], str):
                    try:
                        d["startup_type"] = ServiceStartup(d["startup_type"])
                    except ValueError:
                        d["startup_type"] = ServiceStartup.UNKNOWN
                valid = {f for f in ServiceInfo.__dataclass_fields__}
                result.append(ServiceInfo(**{k: v for k, v in d.items() if k in valid}))
            except Exception as exc:
                logger.warning("Skipping invalid service: %s", exc)
        return result

    @staticmethod
    def _load_firewall(d: dict) -> FirewallStatus:
        valid = {f for f in FirewallStatus.__dataclass_fields__}
        return FirewallStatus(**{k: v for k, v in d.items() if k in valid})

    @staticmethod
    def _load_connections(items: list[dict]) -> list[NetworkConnection]:
        from core.models import NetworkExposure
        result = []
        for item in items:
            try:
                d = dict(item)
                if "exposure" in d and isinstance(d["exposure"], str):
                    try:
                        d["exposure"] = NetworkExposure(d["exposure"])
                    except ValueError:
                        d["exposure"] = NetworkExposure.UNKNOWN
                valid = {f for f in NetworkConnection.__dataclass_fields__}
                result.append(NetworkConnection(**{k: v for k, v in d.items() if k in valid}))
            except Exception as exc:
                logger.warning("Skipping invalid connection: %s", exc)
        return result
