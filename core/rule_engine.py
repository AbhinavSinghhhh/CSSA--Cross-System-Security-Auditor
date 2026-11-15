"""Configurable security rule engine.

Loads rules from JSON files and evaluates them against normalised audit
data, producing Finding objects.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from core.models import (
    AuditResult,
    Finding,
    FindingStatus,
    NetworkExposure,
    Platform,
    SecurityRule,
    Severity,
    ServiceStatus,
    ServiceStartup,
)

logger = logging.getLogger(__name__)


class RuleEngine:
    """Load rules from JSON files and evaluate them against audit data."""

    def __init__(self, rules_dir: Path) -> None:
        self.rules_dir = rules_dir
        self.rules: list[SecurityRule] = []
        self._load_rules()

    # ── rule loading ──────────────────────────────────────────

    def _load_rules(self) -> None:
        self.rules = []
        if not self.rules_dir.exists():
            logger.warning("Rules directory does not exist: %s", self.rules_dir)
            return

        for file_path in sorted(self.rules_dir.glob("*.json")):
            try:
                with open(file_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                for rd in data:
                    try:
                        # Convert severity string → enum
                        if "severity" in rd and isinstance(rd["severity"], str):
                            rd["severity"] = Severity(rd["severity"])
                        rule = SecurityRule(**{
                            k: v for k, v in rd.items()
                            if k in SecurityRule.__dataclass_fields__
                        })
                        if rule.enabled:
                            self.rules.append(rule)
                    except Exception as exc:
                        logger.warning("Skipping invalid rule in %s: %s", file_path, exc)
                logger.info("Loaded %d rule(s) from %s", len(data), file_path.name)
            except Exception as exc:
                logger.error("Error loading rules from %s: %s", file_path, exc)

    # ── evaluation ────────────────────────────────────────────

    def evaluate_rules(
        self, audit: AuditResult, platform: Platform
    ) -> list[Finding]:
        """Evaluate every applicable rule and return the resulting findings."""
        findings: list[Finding] = []
        platform_str = platform.value

        for rule in self.rules:
            # Filter by platform
            if platform_str not in rule.platforms:
                continue
            try:
                result = self._evaluate(rule, audit, platform_str)
                findings.extend(result)
            except Exception as exc:
                logger.error("Error evaluating rule %s: %s", rule.rule_id, exc)

        return findings

    def _evaluate(
        self, rule: SecurityRule, data: AuditResult, platform_str: str
    ) -> list[Finding]:
        cond = rule.condition_type
        findings: list[Finding] = []

        if cond == "firewall_disabled":
            findings.extend(self._check_firewall(rule, data, platform_str))
        elif cond == "admin_user":
            findings.extend(self._check_admin_users(rule, data, platform_str))
        elif cond == "guest_enabled":
            findings.extend(self._check_guest(rule, data, platform_str))
        elif cond == "exposed_port":
            findings.extend(self._check_exposed_ports(rule, data, platform_str))
        elif cond == "high_resource_process":
            findings.extend(self._check_high_resource(rule, data, platform_str))
        elif cond == "unnecessary_service":
            findings.extend(self._check_unnecessary_services(rule, data, platform_str))
        elif cond == "weak_password_policy":
            findings.extend(self._check_password_policy(rule, data, platform_str))
        elif cond == "startup_suspicious":
            findings.extend(self._check_startup(rule, data, platform_str))
        elif cond == "root_ssh":
            findings.extend(self._check_root_ssh(rule, data, platform_str))
        elif cond == "world_writable":
            findings.extend(self._check_world_writable(rule, data, platform_str))
        elif cond == "suid_file":
            findings.extend(self._check_suid(rule, data, platform_str))
        elif cond == "broad_permissions":
            findings.extend(self._check_broad_permissions(rule, data, platform_str))
        elif cond == "sip_disabled":
            findings.extend(self._check_sip(rule, data, platform_str))
        elif cond == "gatekeeper_disabled":
            findings.extend(self._check_gatekeeper(rule, data, platform_str))
        elif cond == "filevault_disabled":
            findings.extend(self._check_filevault(rule, data, platform_str))
        elif cond == "packet_cleartext_auth":
            findings.extend(self._check_packet_cleartext_auth(rule, data, platform_str))
        elif cond == "packet_cleartext_protocol":
            findings.extend(self._check_packet_cleartext_protocol(rule, data, platform_str))
        elif cond == "packet_weak_tls":
            findings.extend(self._check_packet_weak_tls(rule, data, platform_str))
        elif cond == "packet_broadcast_poisoning":
            findings.extend(self._check_packet_broadcast_poisoning(rule, data, platform_str))
        else:
            logger.debug("Unknown condition type: %s", cond)

        return findings

    # ── packet capture checks ─────────────────────────────────

    def _check_packet_cleartext_auth(self, rule, data, plat):
        pkt_audit = getattr(data, "packet_capture", None)
        if not pkt_audit or not pkt_audit.capture_available:
            return [self._finding(rule, plat, FindingStatus.UNAVAILABLE,
                                  "Packet capture data unavailable.",
                                  "Wireshark/tshark is not installed or capture was not executed.")]
        auth_threats = [t for t in pkt_audit.threats if t.threat_type == "PLAINTEXT_AUTH"]
        if auth_threats:
            evidence = "\n".join(f"[{t.protocol}] {t.source_ip}:{t.source_port} -> {t.dest_ip}:{t.dest_port} | {t.evidence}" for t in auth_threats)
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  f"Detected {len(auth_threats)} instance(s) of cleartext credentials in network packets.",
                                  evidence)]
        return [self._finding(rule, plat, FindingStatus.PASS,
                              "No cleartext credentials observed in inspected packet traffic.", "")]

    def _check_packet_cleartext_protocol(self, rule, data, plat):
        pkt_audit = getattr(data, "packet_capture", None)
        if not pkt_audit or not pkt_audit.capture_available:
            return [self._finding(rule, plat, FindingStatus.UNAVAILABLE,
                                  "Packet capture data unavailable.",
                                  "Wireshark/tshark is not installed or capture was not executed.")]
        plain_threats = [t for t in pkt_audit.threats if t.threat_type == "CLEARTEXT_PROTOCOL"]
        if plain_threats:
            protos = ", ".join(sorted(set(t.protocol for t in plain_threats)))
            evidence = "\n".join(f"[{t.protocol}] {t.source_ip}:{t.source_port} -> {t.dest_ip}:{t.dest_port} ({t.description})" for t in plain_threats)
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  f"Unencrypted protocol traffic ({protos}) detected in packets.",
                                  evidence)]
        return [self._finding(rule, plat, FindingStatus.PASS,
                              "No insecure cleartext protocols observed in network traffic.", "")]

    def _check_packet_weak_tls(self, rule, data, plat):
        pkt_audit = getattr(data, "packet_capture", None)
        if not pkt_audit or not pkt_audit.capture_available:
            return [self._finding(rule, plat, FindingStatus.UNAVAILABLE,
                                  "Packet capture data unavailable.",
                                  "Wireshark/tshark is not installed or capture was not executed.")]
        weak_tls = [t for t in pkt_audit.threats if t.threat_type == "WEAK_TLS"]
        if weak_tls:
            vers = ", ".join(sorted(set(t.protocol for t in weak_tls)))
            evidence = "\n".join(f"[{t.protocol}] {t.source_ip}:{t.source_port} -> {t.dest_ip}:{t.dest_port} | {t.evidence}" for t in weak_tls)
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  f"Deprecated TLS/SSL versions ({vers}) negotiated in packet handshakes.",
                                  evidence)]
        return [self._finding(rule, plat, FindingStatus.PASS,
                              "All inspected TLS handshakes negotiated modern cryptographic protocols.", "")]

    def _check_packet_broadcast_poisoning(self, rule, data, plat):
        pkt_audit = getattr(data, "packet_capture", None)
        if not pkt_audit or not pkt_audit.capture_available:
            return [self._finding(rule, plat, FindingStatus.UNAVAILABLE,
                                  "Packet capture data unavailable.",
                                  "Wireshark/tshark is not installed or capture was not executed.")]
        poison_threats = [t for t in pkt_audit.threats if t.threat_type in ("LLMNR_BROADCAST", "NETBIOS_BROADCAST")]
        if poison_threats:
            evidence = "\n".join(f"[{t.protocol}] {t.source_ip} -> {t.dest_ip}:{t.dest_port} | {t.evidence}" for t in poison_threats)
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  f"Broadcast name resolution traffic ({len(poison_threats)} queries) detected, vulnerable to poisoning.",
                                  evidence)]
        return [self._finding(rule, plat, FindingStatus.PASS,
                              "No vulnerable LLMNR/NetBIOS broadcast resolution traffic observed.", "")]


    # ── individual checks ─────────────────────────────────────

    def _check_firewall(self, rule, data, plat):
        fw = data.firewall
        if not fw:
            return [self._finding(rule, plat, FindingStatus.UNAVAILABLE,
                                  "Firewall status could not be determined.", "")]
        if not fw.enabled:
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  "No active host firewall detected.",
                                  f"Provider: {fw.provider}\nDetails: {fw.details}")]
        return [self._finding(rule, plat, FindingStatus.PASS,
                              "Host firewall is active.",
                              f"Provider: {fw.provider}")]

    def _check_admin_users(self, rule, data, plat):
        admins = [u for u in data.users if u.is_admin]
        threshold = rule.condition_params.get("max_admins", 2)
        if len(admins) > threshold:
            names = ", ".join(u.username for u in admins)
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  f"Found {len(admins)} administrator accounts (threshold: {threshold}).",
                                  f"Admin accounts: {names}")]
        return [self._finding(rule, plat, FindingStatus.PASS,
                              f"Administrator count ({len(admins)}) is within threshold.",
                              "")]

    def _check_guest(self, rule, data, plat):
        guests = [u for u in data.users if u.is_guest and not u.is_disabled]
        if guests:
            names = ", ".join(u.username for u in guests)
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  "Guest account is enabled.",
                                  f"Active guest accounts: {names}")]
        return [self._finding(rule, plat, FindingStatus.PASS,
                              "Guest account is disabled or not present.", "")]

    def _check_exposed_ports(self, rule, data, plat):
        exposed = [c for c in data.network_connections
                   if c.state == "LISTEN" and c.local_address in ("0.0.0.0", "::", "")]
        if exposed:
            details = "\n".join(
                f"  {c.local_port}/{c.protocol} — {c.process_name or 'unknown'} on {c.local_address}"
                for c in exposed
            )
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  f"{len(exposed)} service(s) listening on all interfaces.",
                                  details)]
        return [self._finding(rule, plat, FindingStatus.PASS,
                              "No services exposed on all interfaces.", "")]

    def _check_high_resource(self, rule, data, plat):
        cpu_thresh = rule.condition_params.get("cpu_threshold", 80.0)
        mem_thresh = rule.condition_params.get("mem_threshold", 80.0)
        high = [p for p in data.processes
                if p.cpu_percent > cpu_thresh or p.memory_percent > mem_thresh]
        if high:
            details = "\n".join(
                f"  PID {p.pid}: {p.name} — CPU {p.cpu_percent:.1f}%, MEM {p.memory_percent:.1f}%"
                for p in high
            )
            return [self._finding(rule, plat, FindingStatus.WARNING,
                                  f"{len(high)} process(es) with high resource usage — potential anomaly.",
                                  details)]
        return []

    def _check_unnecessary_services(self, rule, data, plat):
        target_services = [s.lower() for s in rule.condition_params.get("services", [])]
        running = [s for s in data.services
                   if s.name.lower() in target_services and s.status == ServiceStatus.RUNNING]
        if running:
            names = ", ".join(s.display_name or s.name for s in running)
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  "Potentially unnecessary services are running.",
                                  f"Services: {names}")]
        return [self._finding(rule, plat, FindingStatus.PASS,
                              "No flagged unnecessary services are running.", "")]

    def _check_password_policy(self, rule, data, plat):
        min_len_req = rule.condition_params.get("min_length", 14)
        for pol in data.security_policies:
            if "password" in pol.name.lower() and "length" in pol.name.lower():
                try:
                    current = int(pol.current_value)
                    if current < min_len_req:
                        return [self._finding(rule, plat, FindingStatus.FAIL,
                                              f"Minimum password length is {current} (recommended: {min_len_req}).",
                                              f"Policy: {pol.name} = {pol.current_value}")]
                except ValueError:
                    pass
        # Also check PASS_MIN_LEN for Linux
        for pol in data.security_policies:
            if pol.name == "PASS_MIN_LEN":
                try:
                    current = int(pol.current_value)
                    if current < min_len_req:
                        return [self._finding(rule, plat, FindingStatus.FAIL,
                                              f"Minimum password length is {current} (recommended: {min_len_req}).",
                                              f"Policy: {pol.name} = {pol.current_value}")]
                except ValueError:
                    pass
        return []

    def _check_startup(self, rule, data, plat):
        suspicious_dirs = ["temp", "appdata", "tmp", ".hidden"]
        suspicious = [
            e for e in data.startup_entries
            if any(d in e.command.lower() for d in suspicious_dirs)
        ]
        if suspicious:
            details = "\n".join(
                f"  {e.name}: {e.command} (source: {e.source})"
                for e in suspicious
            )
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  f"{len(suspicious)} startup entry(s) reference suspicious directories — review recommended.",
                                  details)]
        return []

    def _check_root_ssh(self, rule, data, plat):
        for pol in data.security_policies:
            if pol.name == "PermitRootLogin":
                if pol.current_value.lower() in ("yes", "without-password", "forced-commands-only"):
                    return [self._finding(rule, plat, FindingStatus.FAIL,
                                          f"Root SSH login is potentially enabled (PermitRootLogin={pol.current_value}).",
                                          f"PermitRootLogin = {pol.current_value}")]
                else:
                    return [self._finding(rule, plat, FindingStatus.PASS,
                                          "Root SSH login is disabled.", "")]
        return []

    def _check_world_writable(self, rule, data, plat):
        ww = [f for f in data.file_permissions if f.is_world_writable]
        if ww:
            details = "\n".join(
                f"  {f.path} ({f.permissions}) — {f.reason}"
                for f in ww
            )
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  f"{len(ww)} world-writable file(s) detected.",
                                  details)]
        return []

    def _check_suid(self, rule, data, plat):
        suid = [f for f in data.file_permissions if f.is_suid or f.is_sgid]
        # Only flag non-standard SUID binaries (exclude common system ones)
        standard_suid = {"/usr/bin/passwd", "/usr/bin/sudo", "/usr/bin/su",
                         "/usr/bin/newgrp", "/usr/bin/chsh", "/usr/bin/chfn",
                         "/usr/bin/mount", "/usr/bin/umount", "/usr/bin/pkexec"}
        unusual = [f for f in suid if f.path not in standard_suid]
        if unusual:
            details = "\n".join(
                f"  {f.path} ({f.permissions}) — {f.reason}"
                for f in unusual
            )
            return [self._finding(rule, plat, FindingStatus.WARNING,
                                  f"{len(unusual)} non-standard SUID/SGID file(s) found — review recommended.",
                                  details)]
        return []

    def _check_broad_permissions(self, rule, data, plat):
        broad = [f for f in data.file_permissions
                 if f.numeric_mode == "777"
                 or "Everyone" in f.permissions
                 or (f.is_world_writable and "sensitive" in f.path.lower())]
        if broad:
            details = "\n".join(
                f"  {f.path} — {f.permissions} — {f.reason}"
                for f in broad
            )
            return [self._finding(rule, plat, FindingStatus.FAIL,
                                  f"Broad file permissions detected on {len(broad)} path(s).",
                                  details)]
        return []

    def _check_sip(self, rule, data, plat):
        for pol in data.security_policies:
            if "system integrity" in pol.name.lower() or "sip" in pol.name.lower():
                if pol.current_value.lower() != "enabled":
                    return [self._finding(rule, plat, FindingStatus.FAIL,
                                          "System Integrity Protection (SIP) is disabled.",
                                          f"SIP status: {pol.current_value}")]
                return [self._finding(rule, plat, FindingStatus.PASS,
                                      "System Integrity Protection (SIP) is enabled.",
                                      f"SIP status: {pol.current_value}")]
        return []

    def _check_gatekeeper(self, rule, data, plat):
        for pol in data.security_policies:
            if "gatekeeper" in pol.name.lower():
                if pol.current_value.lower() != "enabled":
                    return [self._finding(rule, plat, FindingStatus.FAIL,
                                          "Gatekeeper application code signing assessment is disabled.",
                                          f"Gatekeeper status: {pol.current_value}")]
                return [self._finding(rule, plat, FindingStatus.PASS,
                                      "Gatekeeper assessment is enabled.",
                                      f"Gatekeeper status: {pol.current_value}")]
        return []

    def _check_filevault(self, rule, data, plat):
        for pol in data.security_policies:
            if "filevault" in pol.name.lower():
                if pol.current_value.lower() != "enabled":
                    return [self._finding(rule, plat, FindingStatus.FAIL,
                                          "FileVault full volume disk encryption is disabled.",
                                          f"FileVault status: {pol.current_value}")]
                return [self._finding(rule, plat, FindingStatus.PASS,
                                      "FileVault full volume disk encryption is enabled.",
                                      f"FileVault status: {pol.current_value}")]
        return []

    # ── compliant title mapping ─────────────────────────────────
    COMPLIANT_TITLES = {
        "firewall_disabled": "Host Firewall is enabled and active",
        "sip_disabled": "System Integrity Protection (SIP) is enabled",
        "gatekeeper_disabled": "Gatekeeper application assessment is enabled",
        "filevault_disabled": "FileVault full-disk encryption is active",
        "admin_user": "Administrative privileges properly restricted",
        "guest_enabled": "Guest account is disabled",
        "exposed_port": "No unauthorized open network ports",
        "high_resource_process": "Process resource utilization within normal thresholds",
        "unnecessary_service": "No unnecessary or insecure services running",
        "weak_password_policy": "Password policy meets security standards",
        "startup_suspicious": "Startup and persistence mechanisms verified",
        "root_ssh": "Root SSH remote access is restricted",
        "world_writable": "No world-writable files in audited paths",
        "suid_file": "SUID/SGID executables baseline verified",
        "broad_permissions": "Sensitive filesystem permissions properly restricted",
    }

    # ── finding factory ───────────────────────────────────────

    @classmethod
    def _finding(
        cls,
        rule: SecurityRule,
        platform_str: str,
        status: FindingStatus,
        rationale: str,
        evidence: str,
    ) -> Finding:
        if status == FindingStatus.PASS:
            if rule.condition_type in cls.COMPLIANT_TITLES:
                title = cls.COMPLIANT_TITLES[rule.condition_type]
            else:
                t = rule.title
                if "is disabled" in t.lower():
                    title = t.replace(" is disabled", " is enabled").replace(" is Disabled", " is Enabled")
                elif "disabled" in t.lower():
                    title = t.replace(" disabled", " active").replace(" Disabled", " Active")
                elif "inactive" in t.lower():
                    title = t.replace(" is inactive", " is active").replace(" inactive", " active")
                elif "is enabled" in t.lower():
                    title = t.replace(" is enabled", " is disabled")
                elif "permitted" in t.lower():
                    title = t.replace(" permitted", " restricted")
                else:
                    title = f"{t} (Compliant)"
            rec = "No remediation required. Current configuration is compliant."
            desc = rationale or f"System compliant with rule: {rule.title}."
        else:
            title = rule.title
            rec = rule.recommendation
            desc = rule.description

        return Finding(
            id=str(uuid.uuid4()),
            rule_id=rule.rule_id,
            title=title,
            category=rule.category,
            severity=rule.severity,
            status=status,
            platform=platform_str,
            description=desc,
            evidence=evidence,
            rationale=rationale,
            recommendation=rec,
            timestamp=datetime.now().isoformat(),
        )
