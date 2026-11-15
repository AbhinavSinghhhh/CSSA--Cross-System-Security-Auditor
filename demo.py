#!/usr/bin/env python3
"""Interactive Demonstration Script for CSSA (Cross-Platform System Security Auditor).

Demonstrates the entire security auditing pipeline from CLI to GUI:
1. Platform detection & adapter architecture
2. Security audit & rule evaluation (Windows, Linux, or Live host)
3. Wireshark packet capture & network threat dissection (PCAP parsing)
4. Transparent scoring and category penalty capping
5. Baseline snapshot creation & configuration drift detection
6. Executive HTML & Markdown report generation
7. Interactive desktop GUI launch
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.auditor import Auditor
from core.baseline import BaselineManager
from core.models import AuditMode, FindingStatus, Severity
from platforms.packet_capture import audit_pcap_file, find_tshark_path
from reports.html_report import HTMLReportGenerator
from reports.markdown_report import MarkdownReportGenerator
from utils.paths import get_fixtures_dir, get_rules_dir

# ANSI Terminal Colors
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


def print_banner():
    banner = f"""
{BOLD}{CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   🛡️  CSSA — Cross-Platform System Security Auditor                          ║
║       Defensive Host-Based Auditing & Network Threat Analysis                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝{RESET}
"""
    print(banner)


def print_stage(num: int, title: str):
    print(f"\n{BOLD}{MAGENTA}── [STAGE {num}] {title.upper()} ──────────────────────────────────────────{RESET}\n")


def run_demonstration(mode: AuditMode, launch_gui: bool = False):
    print_banner()

    # ── STAGE 1: Architectural Overview & Platform Detection ──
    print_stage(1, "Architectural Overview & Platform Detection")
    auditor = Auditor(get_rules_dir(), get_fixtures_dir())
    detected_plat = auditor.detect_platform()

    print(f"  • {BOLD}Host Platform Detected:{RESET} {CYAN}{detected_plat.value.upper()}{RESET}")
    print(f"  • {BOLD}Adapter Architecture:{RESET} SecurityPlatformAdapter -> {detected_plat.value.capitalize()}SecurityAdapter")
    print(f"  • {BOLD}Philosophy:{RESET} Strictly Read-Only, Non-Destructive, Zero Credential Harvesting")
    print(f"  • {BOLD}Audit Execution Mode:{RESET} {YELLOW}{mode.value}{RESET}")

    # ── STAGE 2: Security Audit Execution & Rule Engine ──────
    print_stage(2, "Executing Security Audit & Rule Engine")
    print(f"  Running security audit in mode: {mode.value}...")
    start_time = time.time()
    audit_res = auditor.run_audit(mode)
    elapsed = time.time() - start_time
    print(f"  Audit completed in {elapsed:.3f} seconds.\n")

    sys_info = audit_res.system_info
    print(f"  • {BOLD}Target OS:{RESET} {sys_info.os_name} {sys_info.os_version} ({sys_info.architecture})")
    print(f"  • {BOLD}Host / User:{RESET} {sys_info.hostname} / {sys_info.current_user} ({sys_info.privilege_level})")
    print(f"  • {BOLD}Total Findings Evaluated:{RESET} {len(audit_res.findings)}")

    actionable = [f for f in audit_res.findings if f.status in (FindingStatus.FAIL, FindingStatus.WARNING)]
    print(f"  • {BOLD}Actionable Weaknesses:{RESET} {len(actionable)} (Critical: {audit_res.score.critical_count}, High: {audit_res.score.high_count}, Medium: {audit_res.score.medium_count}, Low: {audit_res.score.low_count})")

    if actionable:
        print(f"\n  {BOLD}Top Security Findings Detected:{RESET}")
        for idx, f in enumerate(actionable[:5], 1):
            sev_color = RED if f.severity == Severity.CRITICAL else (YELLOW if f.severity == Severity.HIGH else BLUE)
            print(f"    {idx}. [{sev_color}{f.severity.value}{RESET}] [{f.category}] {BOLD}{f.title}{RESET}")
            if f.recommendation:
                print(f"       -> Mitigation: {f.recommendation}")

    # ── STAGE 3: Wireshark Packet Capture & Network Threat Dissection ──
    print_stage(3, "Wireshark Packet Capture & Network Threat Analysis")
    tshark_path = find_tshark_path()
    if tshark_path:
        print(f"  • {BOLD}Wireshark CLI Detected:{RESET} {GREEN}{tshark_path}{RESET}")
    else:
        print(f"  • {BOLD}Wireshark CLI:{RESET} {YELLOW}Not in PATH (Pure-Python PCAP mode active){RESET}")

    sample_pcap = get_fixtures_dir() / "threat_sample.pcap"
    if sample_pcap.is_file():
        print(f"  • {BOLD}Auditing Sample PCAP File:{RESET} {sample_pcap.name}")
        pkt_audit = audit_pcap_file(sample_pcap)
        print(f"  • {BOLD}Packets Inspected:{RESET} {pkt_audit.total_packets_captured}")
        print(f"  • {BOLD}Protocols Seen:{RESET} {pkt_audit.protocols_seen}")
        print(f"  • {BOLD}Network Threats Identified:{RESET} {len(pkt_audit.threats)}\n")

        for idx, t in enumerate(pkt_audit.threats, 1):
            sev_color = RED if t.severity == Severity.CRITICAL else (YELLOW if t.severity == Severity.HIGH else CYAN)
            endpoints = f"{t.source_ip}:{t.source_port} -> {t.dest_ip}:{t.dest_port}"
            print(f"    {idx}. [{sev_color}{t.severity.value}{RESET}] {BOLD}{t.threat_type}{RESET} ({t.protocol}) over {endpoints}")
            print(f"       • Evidence: {t.evidence}")
            print(f"       • Defense:  {t.recommendation}")

    # ── STAGE 4: Transparent Scoring & Category Penalty Capping ──
    print_stage(4, "Transparent Scoring & Category Penalty Capping")
    score_obj = audit_res.score
    print(f"  • {BOLD}Base Score:{RESET} 100")
    print(f"  • {BOLD}Category Penalty Cap:{RESET} 12 points per category (prevents single noisy category domination)")
    print(f"\n  {BOLD}Category Score Breakdown:{RESET}")
    print(f"  {'Category':<22} | {'Score':<8} | {'Critical':<8} | {'High':<6} | {'Medium':<6} | {'Low':<5}")
    print("  " + "─" * 68)
    for cs in score_obj.category_scores:
        cat_color = GREEN if cs.score >= 85 else (YELLOW if cs.score >= 60 else RED)
        print(f"  {cs.category:<22} | {cat_color}{cs.score:>3}/100{RESET}   | {cs.critical_count:<8} | {cs.high_count:<6} | {cs.medium_count:<6} | {cs.low_count:<5}")

    score_val = score_obj.overall_score
    risk_color = GREEN if score_val >= 75 else (YELLOW if score_val >= 60 else RED)
    print(f"\n  {BOLD}OVERALL AUDIT SCORE:{RESET} {risk_color}{score_val}/100{RESET}  ({risk_color}{score_obj.risk_level.value}{RESET})")

    # ── STAGE 5: Baseline Creation & Configuration Drift ─────
    print_stage(5, "Baseline Creation & Configuration Drift Detection")
    baseline_items = BaselineManager.create_baseline(audit_res)
    print(f"  • Created baseline snapshot with {len(baseline_items)} tracked configuration items.")

    # Simulate drift: an unexpected listening port opened
    drifted_audit = auditor.run_audit(mode)
    from core.models import NetworkConnection, NetworkExposure
    drifted_audit.network_connections.append(
        NetworkConnection(
            local_address="0.0.0.0",
            local_port=4444,
            protocol="TCP",
            state="LISTEN",
            process_name="unauthorized_listener.exe",
            exposure=NetworkExposure.NETWORK_EXPOSED,
        )
    )

    current_items = BaselineManager.create_baseline(drifted_audit)
    diff = BaselineManager.compare_baseline(baseline_items, current_items)
    print(f"  • Configuration Drift Analysis:")
    print(f"    - {GREEN}+ Added Items:{RESET} {len(diff.added)}")
    print(f"    - {RED}- Removed Items:{RESET} {len(diff.removed)}")
    print(f"    - {YELLOW}! Modified Items:{RESET} {len(diff.changed)}")

    for add_item in diff.added[:3]:
        print(f"      {GREEN}[+] Newly Exposed:{RESET} {add_item.category} -> {add_item.key} ({add_item.details})")

    # ── STAGE 6: Executive Reporting ─────────────────────────
    print_stage(6, "Generating Executive Security Audit Reports")
    output_dir = PROJECT_ROOT / "reports" / "demo_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    html_file = output_dir / "audit_report.html"
    md_file = output_dir / "audit_report.md"

    html_gen = HTMLReportGenerator()
    html_gen.generate(audit_res, html_file, baseline_diff=diff)

    md_gen = MarkdownReportGenerator()
    md_gen.generate(audit_res, md_file, baseline_diff=diff)

    print(f"  • {BOLD}HTML Report Generated:{RESET} {GREEN}{html_file}{RESET}")
    print(f"  • {BOLD}Markdown Report Generated:{RESET} {GREEN}{md_file}{RESET}")
    print(f"  View HTML report in your browser: file://{html_file}")

    # ── STAGE 7: Interactive Desktop GUI Launch ──────────────
    if launch_gui:
        print_stage(7, "Launching Interactive Desktop GUI (PySide6)")
        print("  Starting Qt main event loop...")
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow

        app = QApplication.instance() or QApplication(sys.argv)
        win = MainWindow()
        win.show()
        sys.exit(app.exec())
    else:
        print(f"\n{BOLD}{CYAN}═══════════════════════════════════════════════════════════════════════════════{RESET}")
        print(f"{BOLD}Demonstration complete!{RESET} To launch the interactive desktop GUI, run:")
        print(f"  {GREEN}python3 demo.py --gui{RESET}   or   {GREEN}python3 main.py{RESET}")
        print(f"{BOLD}{CYAN}═══════════════════════════════════════════════════════════════════════════════{RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="CSSA Security Auditor Interactive Demonstration")
    parser.add_argument(
        "--mode",
        choices=["real", "windows", "linux", "macos"],
        default="windows",
        help="Audit mode to demonstrate (default: windows)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the PySide6 desktop GUI after running the CLI demonstration",
    )
    args = parser.parse_args()

    mode_map = {
        "real": AuditMode.REAL,
        "windows": AuditMode.DEMO_WINDOWS,
        "linux": AuditMode.DEMO_LINUX,
        "macos": AuditMode.DEMO_MACOS,
    }
    selected_mode = mode_map[args.mode]
    run_demonstration(selected_mode, launch_gui=args.gui)


if __name__ == "__main__":
    main()
