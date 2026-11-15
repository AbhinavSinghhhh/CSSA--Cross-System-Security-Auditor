"""Packet threat analysis engine.

Examines parsed network packets for cleartext credentials, legacy protocols,
deprecated TLS handshakes, and broadcast poisoning vulnerabilities.
"""

from __future__ import annotations

import base64
import re
from collections import Counter
from datetime import datetime
from typing import List, Tuple

from core.models import PacketCaptureAudit, PacketThreat, Severity
from core.pcap_parser import ParsedPacket


# Regex patterns for cleartext authentication inspection
BASIC_AUTH_REGEX = re.compile(rb"Authorization:\s*Basic\s+([A-Za-z0-9+/=]+)", re.IGNORECASE)
HTTP_PASSWORD_FORM_REGEX = re.compile(rb"(?:password|passwd|pwd|user_pass)=([^&\s]+)", re.IGNORECASE)
FTP_USER_REGEX = re.compile(rb"USER\s+([^\r\n]+)", re.IGNORECASE)
FTP_PASS_REGEX = re.compile(rb"PASS\s+([^\r\n]+)", re.IGNORECASE)

SUSPICIOUS_PORTS = {
    4444: "Metasploit default listener",
    6667: "IRC network",
    3333: "Stratum / cryptocurrency mining pool",
    5555: "Android Debug Bridge over network",
    6666: "Suspected IRC / botnet control port",
}


class PacketThreatDetector:
    """Evaluates packet streams and outputs a structured PacketCaptureAudit."""

    def __init__(self) -> None:
        pass

    def analyze_packets(
        self,
        packets: list[ParsedPacket],
        source_label: str = "Packet Inspection",
        duration_seconds: int = 0,
        wireshark_path: str = "",
        pcap_path: str = "",
    ) -> PacketCaptureAudit:
        """Run defensive security checks against the supplied packets."""
        threats: list[PacketThreat] = []
        protocols_seen: Counter[str] = Counter()

        seen_threat_keys: set[str] = set()

        for pkt in packets:
            proto = pkt.protocol.upper()
            protocols_seen[proto] += 1

            ports = {pkt.src_port, pkt.dst_port}
            payload = pkt.payload

            # ── 1. Cleartext Authentication Transmission (CRITICAL) ──
            if payload:
                # Check HTTP Basic Auth
                basic_auth_match = BASIC_AUTH_REGEX.search(payload)
                if basic_auth_match:
                    encoded_val = basic_auth_match.group(1)
                    evidence_str = f"Authorization: Basic {encoded_val.decode('latin1', errors='replace')}"
                    key = f"AUTH_BASIC_{pkt.src_ip}_{pkt.dst_ip}"
                    if key not in seen_threat_keys:
                        seen_threat_keys.add(key)
                        threats.append(
                            PacketThreat(
                                timestamp=datetime.fromtimestamp(pkt.timestamp).isoformat() if pkt.timestamp else "",
                                threat_type="PLAINTEXT_AUTH",
                                protocol="HTTP",
                                source_ip=pkt.src_ip,
                                source_port=pkt.src_port,
                                dest_ip=pkt.dst_ip,
                                dest_port=pkt.dst_port,
                                severity=Severity.CRITICAL,
                                description="Cleartext HTTP Basic Authentication header detected in transit.",
                                recommendation="Migrate web services to HTTPS and disable unencrypted Basic Authentication.",
                                evidence=evidence_str,
                                packet_summary=pkt.summary,
                            )
                        )

                # Check HTTP Form Password Fields
                pwd_match = HTTP_PASSWORD_FORM_REGEX.search(payload)
                if pwd_match and (80 in ports or 8080 in ports):
                    key = f"AUTH_FORM_{pkt.src_ip}_{pkt.dst_ip}"
                    if key not in seen_threat_keys:
                        seen_threat_keys.add(key)
                        threats.append(
                            PacketThreat(
                                timestamp=datetime.fromtimestamp(pkt.timestamp).isoformat() if pkt.timestamp else "",
                                threat_type="PLAINTEXT_AUTH",
                                protocol="HTTP",
                                source_ip=pkt.src_ip,
                                source_port=pkt.src_port,
                                dest_ip=pkt.dst_ip,
                                dest_port=pkt.dst_port,
                                severity=Severity.CRITICAL,
                                description="Plaintext password transmission detected in unencrypted HTTP payload.",
                                recommendation="Enforce TLS/HTTPS on all authentication endpoints.",
                                evidence="Password field observed in HTTP body.",
                                packet_summary=pkt.summary,
                            )
                        )

                # Check FTP credentials
                ftp_user_match = FTP_USER_REGEX.search(payload)
                ftp_pass_match = FTP_PASS_REGEX.search(payload)
                if (ftp_user_match or ftp_pass_match) and 21 in ports:
                    key = f"AUTH_FTP_{pkt.src_ip}_{pkt.dst_ip}"
                    if key not in seen_threat_keys:
                        seen_threat_keys.add(key)
                        threats.append(
                            PacketThreat(
                                timestamp=datetime.fromtimestamp(pkt.timestamp).isoformat() if pkt.timestamp else "",
                                threat_type="PLAINTEXT_AUTH",
                                protocol="FTP",
                                source_ip=pkt.src_ip,
                                source_port=pkt.src_port,
                                dest_ip=pkt.dst_ip,
                                dest_port=pkt.dst_port,
                                severity=Severity.CRITICAL,
                                description="Cleartext FTP credentials transmitted over the network.",
                                recommendation="Replace unencrypted FTP with SFTP (SSH File Transfer Protocol) or FTPS.",
                                evidence="FTP USER / PASS command exchange observed.",
                                packet_summary=pkt.summary,
                            )
                        )

            # ── 2. Insecure / Cleartext Protocols (HIGH) ──
            if 23 in ports:
                key = f"TELNET_{pkt.src_ip}_{pkt.dst_ip}"
                if key not in seen_threat_keys:
                    seen_threat_keys.add(key)
                    threats.append(
                        PacketThreat(
                            timestamp=datetime.fromtimestamp(pkt.timestamp).isoformat() if pkt.timestamp else "",
                            threat_type="CLEARTEXT_PROTOCOL",
                            protocol="TELNET",
                            source_ip=pkt.src_ip,
                            source_port=pkt.src_port,
                            dest_ip=pkt.dst_ip,
                            dest_port=pkt.dst_port,
                            severity=Severity.HIGH,
                            description="Unencrypted Telnet terminal traffic detected on port 23.",
                            recommendation="Disable Telnet service and replace with secure OpenSSH.",
                            evidence=f"Traffic on port 23 between {pkt.src_ip} and {pkt.dst_ip}",
                            packet_summary=pkt.summary,
                        )
                    )

            if 21 in ports and not any(t.protocol == "FTP" and t.threat_type == "PLAINTEXT_AUTH" for t in threats):
                key = f"FTP_PLAIN_{pkt.src_ip}_{pkt.dst_ip}"
                if key not in seen_threat_keys:
                    seen_threat_keys.add(key)
                    threats.append(
                        PacketThreat(
                            timestamp=datetime.fromtimestamp(pkt.timestamp).isoformat() if pkt.timestamp else "",
                            threat_type="CLEARTEXT_PROTOCOL",
                            protocol="FTP",
                            source_ip=pkt.src_ip,
                            source_port=pkt.src_port,
                            dest_ip=pkt.dst_ip,
                            dest_port=pkt.dst_port,
                            severity=Severity.HIGH,
                            description="Unencrypted FTP communication active on port 21.",
                            recommendation="Transition to SFTP or TLS-encrypted file transfers.",
                            evidence=f"Active connection on port 21 ({pkt.src_ip} -> {pkt.dst_ip})",
                            packet_summary=pkt.summary,
                        )
                    )

            if (80 in ports or 8080 in ports) and (b"HTTP/" in payload or b"GET " in payload or b"POST " in payload):
                key = f"HTTP_PLAIN_{pkt.src_ip}_{pkt.dst_ip}"
                if key not in seen_threat_keys:
                    seen_threat_keys.add(key)
                    threats.append(
                        PacketThreat(
                            timestamp=datetime.fromtimestamp(pkt.timestamp).isoformat() if pkt.timestamp else "",
                            threat_type="CLEARTEXT_PROTOCOL",
                            protocol="HTTP",
                            source_ip=pkt.src_ip,
                            source_port=pkt.src_port,
                            dest_ip=pkt.dst_ip,
                            dest_port=pkt.dst_port,
                            severity=Severity.HIGH,
                            description="Unencrypted HTTP web traffic observed without TLS encapsulation.",
                            recommendation="Enforce HTTPS with HSTS (HTTP Strict Transport Security) headers.",
                            evidence=f"HTTP request/response payload observed on port {pkt.dst_port or pkt.src_port}",
                            packet_summary=pkt.summary,
                        )
                    )

            # ── 3. Deprecated TLS / SSL Versions (HIGH) ──
            if payload and len(payload) >= 5 and payload[0] == 22:  # TLS Handshake
                rec_ver = (payload[1], payload[2])
                ver_name = ""
                if rec_ver == (3, 0):
                    ver_name = "SSL 3.0"
                elif rec_ver == (3, 1):
                    ver_name = "TLS 1.0"
                elif rec_ver == (3, 2):
                    ver_name = "TLS 1.1"

                if ver_name:
                    key = f"WEAK_TLS_{ver_name}_{pkt.src_ip}_{pkt.dst_ip}"
                    if key not in seen_threat_keys:
                        seen_threat_keys.add(key)
                        threats.append(
                            PacketThreat(
                                timestamp=datetime.fromtimestamp(pkt.timestamp).isoformat() if pkt.timestamp else "",
                                threat_type="WEAK_TLS",
                                protocol=ver_name,
                                source_ip=pkt.src_ip,
                                source_port=pkt.src_port,
                                dest_ip=pkt.dst_ip,
                                dest_port=pkt.dst_port,
                                severity=Severity.HIGH,
                                description=f"Deprecated cryptographic protocol ({ver_name}) negotiated in TLS handshake.",
                                recommendation="Disable SSLv3, TLS 1.0, and TLS 1.1 in system crypto policies (require TLS 1.2+ / TLS 1.3).",
                                evidence=f"TLS Record Layer version 0x{rec_ver[0]:02x}{rec_ver[1]:02x} ({ver_name})",
                                packet_summary=pkt.summary,
                            )
                        )

            # ── 4. Broadcast Name Resolution Poisoning Risk (MEDIUM) ──
            if 5355 in ports:  # LLMNR
                key = f"LLMNR_{pkt.src_ip}"
                if key not in seen_threat_keys:
                    seen_threat_keys.add(key)
                    threats.append(
                        PacketThreat(
                            timestamp=datetime.fromtimestamp(pkt.timestamp).isoformat() if pkt.timestamp else "",
                            threat_type="LLMNR_BROADCAST",
                            protocol="LLMNR",
                            source_ip=pkt.src_ip,
                            source_port=pkt.src_port,
                            dest_ip=pkt.dst_ip,
                            dest_port=pkt.dst_port,
                            severity=Severity.MEDIUM,
                            description="Link-Local Multicast Name Resolution (LLMNR) broadcast traffic active.",
                            recommendation="Disable LLMNR via Group Policy or systemd-resolved to prevent credential-relay attacks (Responder).",
                            evidence=f"LLMNR multicast on UDP 5355: {pkt.summary}",
                            packet_summary=pkt.summary,
                        )
                    )

            if 137 in ports:  # NetBIOS-NS
                key = f"NETBIOS_{pkt.src_ip}"
                if key not in seen_threat_keys:
                    seen_threat_keys.add(key)
                    threats.append(
                        PacketThreat(
                            timestamp=datetime.fromtimestamp(pkt.timestamp).isoformat() if pkt.timestamp else "",
                            threat_type="NETBIOS_BROADCAST",
                            protocol="NETBIOS",
                            source_ip=pkt.src_ip,
                            source_port=pkt.src_port,
                            dest_ip=pkt.dst_ip,
                            dest_port=pkt.dst_port,
                            severity=Severity.MEDIUM,
                            description="NetBIOS Name Service broadcast queries active on local subnet.",
                            recommendation="Disable NetBIOS over TCP/IP across network adapters.",
                            evidence=f"NetBIOS-NS broadcast query on UDP 137 from {pkt.src_ip}",
                            packet_summary=pkt.summary,
                        )
                    )

            # ── 5. Suspicious Port Connections (MEDIUM) ──
            for suspicious_port, port_desc in SUSPICIOUS_PORTS.items():
                if suspicious_port in ports:
                    key = f"SUSP_PORT_{suspicious_port}_{pkt.src_ip}_{pkt.dst_ip}"
                    if key not in seen_threat_keys:
                        seen_threat_keys.add(key)
                        threats.append(
                            PacketThreat(
                                timestamp=datetime.fromtimestamp(pkt.timestamp).isoformat() if pkt.timestamp else "",
                                threat_type="SUSPICIOUS_PORT",
                                protocol=pkt.protocol,
                                source_ip=pkt.src_ip,
                                source_port=pkt.src_port,
                                dest_ip=pkt.dst_ip,
                                dest_port=pkt.dst_port,
                                severity=Severity.MEDIUM,
                                description=f"Traffic observed on unusual/suspicious port {suspicious_port} ({port_desc}).",
                                recommendation=f"Investigate process communicating on port {suspicious_port} for potential unauthorized activity.",
                                evidence=f"Connection {pkt.src_ip}:{pkt.src_port} <-> {pkt.dst_ip}:{pkt.dst_port}",
                                packet_summary=pkt.summary,
                            )
                        )

            # ── 6. Unencrypted DNS Queries (LOW / INFORMATIONAL) ──
            if 53 in ports and pkt.protocol == "DNS":
                key = f"PLAINTEXT_DNS_{pkt.src_ip}"
                if key not in seen_threat_keys and len(threats) < 25:
                    seen_threat_keys.add(key)
                    threats.append(
                        PacketThreat(
                            timestamp=datetime.fromtimestamp(pkt.timestamp).isoformat() if pkt.timestamp else "",
                            threat_type="PLAINTEXT_DNS",
                            protocol="DNS",
                            source_ip=pkt.src_ip,
                            source_port=pkt.src_port,
                            dest_ip=pkt.dst_ip,
                            dest_port=pkt.dst_port,
                            severity=Severity.LOW,
                            description="Plaintext unencrypted DNS queries transmitted over UDP port 53.",
                            recommendation="Configure DNS-over-HTTPS (DoH) or DNS-over-TLS (DoT) to safeguard DNS queries from local surveillance.",
                            evidence=pkt.summary or "Standard UDP 53 DNS query",
                            packet_summary=pkt.summary,
                        )
                    )

        # Sort threats by severity descending
        threats.sort(key=lambda t: t.severity.rank, reverse=True)

        return PacketCaptureAudit(
            capture_available=True,
            capture_source=source_label,
            duration_seconds=duration_seconds,
            total_packets_captured=len(packets),
            threats=threats,
            protocols_seen=dict(protocols_seen),
            details=f"Analyzed {len(packets)} packets. Found {len(threats)} potential security threats/anomalies.",
            wireshark_path=wireshark_path,
            pcap_path=pcap_path,
        )
