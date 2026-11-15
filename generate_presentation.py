import os
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

PROJECT_DIR = Path('/Users/abhinavsingh/PROJECT/windows and linux internal/cross_platform_security_auditor')
OUTPUT_DIR = PROJECT_DIR / 'docs'
OUTPUT_PPTX = OUTPUT_DIR / 'CSSA_Project_Presentation_21CSE490J.pptx'
ROOT_PPTX = Path('/Users/abhinavsingh/PROJECT/windows and linux internal/CSSA_Project_Presentation_21CSE490J.pptx')
SCREENSHOTS_DIR = OUTPUT_DIR / 'screenshots'
LOGO_PATH = OUTPUT_DIR / 'image1.jpeg'

# Color Palette
NAVY_DARK = RGBColor(15, 32, 67)       # #0F2043 (Slide background / Title cards)
NAVY_HEADER = RGBColor(15, 52, 96)     # #0F3460 (Header bars, main cards)
TEAL_ACCENT = RGBColor(0, 168, 181)    # #00A8B5 (Cyan accents, subheadings)
SLATE_GRAY = RGBColor(100, 116, 139)   # #64748B (Secondary labels)
CHARCOAL = RGBColor(30, 41, 59)        # #1E293B (Body text)
WHITE = RGBColor(255, 255, 255)
LIGHT_BG = RGBColor(248, 250, 252)     # #F8FAFC (Slide background)
CARD_BG = RGBColor(255, 255, 255)      # Pure white cards
BORDER_COLOR = RGBColor(226, 232, 240) # #E2E8F0 (Card border)
GREEN_ACCENT = RGBColor(16, 185, 129)  # #10B981 (Pass / Good)
RED_ACCENT = RGBColor(239, 68, 68)     # #EF4444 (Critical / Fail)

FONT_HEADING = "Times New Roman"
FONT_BODY = "Times New Roman"

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="21CSE490J — WINDOWS AND LINUX INTERNALS"):
        # Header banner
        header_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.15))
        header_bar.fill.solid()
        header_bar.fill.fore_color.rgb = NAVY_HEADER
        header_bar.line.fill.background()

        # Accent strip
        accent_strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(1.15), prs.slide_width, Inches(0.06))
        accent_strip.fill.solid()
        accent_strip.fill.fore_color.rgb = TEAL_ACCENT
        accent_strip.line.fill.background()

        # Category / Breadcrumb
        tx_box_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.12), Inches(9.5), Inches(0.3))
        tf_cat = tx_box_cat.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.name = FONT_HEADING
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = TEAL_ACCENT

        # Title Text
        tx_box_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.38), Inches(9.5), Inches(0.65))
        tf_title = tx_box_title.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.name = FONT_HEADING
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = WHITE

        # SRM Logo in header if available
        if LOGO_PATH.exists():
            slide.shapes.add_picture(str(LOGO_PATH), Inches(10.6), Inches(0.15), width=Inches(2.0))

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=BORDER_COLOR):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.5)
        else:
            card.line.fill.background()
        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, NAVY_DARK)

    # Accent decorative bars
    top_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = TEAL_ACCENT
    top_bar.line.fill.background()

    # SRM Logo on Title Slide
    if LOGO_PATH.exists():
        s1.shapes.add_picture(str(LOGO_PATH), Inches(4.8), Inches(0.65), width=Inches(3.7))

    # Course Label
    tx_box = s1.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(11.333), Inches(0.45))
    tf = tx_box.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "21CSE490J – WINDOWS AND LINUX INTERNALS | MINI PROJECT"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACCENT

    # Main Project Title
    tx_box = s1.shapes.add_textbox(Inches(0.8), Inches(2.6), Inches(11.733), Inches(1.1))
    tf = tx_box.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "CSSA: Cross-Platform System Security Auditor"
    p.font.name = FONT_HEADING
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = WHITE

    # Subtitle
    tx_box = s1.shapes.add_textbox(Inches(1.0), Inches(3.65), Inches(11.333), Inches(0.55))
    tf = tx_box.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "A Defensive, Read-Only Security Telemetry, Packet Threat & Risk Scoring Framework"
    p.font.name = FONT_BODY
    p.font.size = Pt(15)
    p.font.italic = True
    p.font.color.rgb = RGBColor(203, 213, 225)

    # Presenters Card
    add_card(s1, 1.2, 4.45, 6.8, 2.3, bg_color=RGBColor(26, 46, 85), border_color=TEAL_ACCENT)
    tx_box = s1.shapes.add_textbox(Inches(1.4), Inches(4.55), Inches(6.4), Inches(2.1))
    tf = tx_box.text_frame
    p = tf.paragraphs[0]
    p.text = "PRESENTED BY:"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACCENT

    students = [
        "• Abhinav Singh (RA2312703010024)",
        "• Anant Jodha (RA2312703010002)",
        "• Abhishek Ranjan (RA231103010295)"
    ]
    for s in students:
        p2 = tf.add_paragraph()
        p2.text = s
        p2.font.name = FONT_BODY
        p2.font.size = Pt(13)
        p2.font.bold = True
        p2.font.color.rgb = WHITE

    p_deg = tf.add_paragraph()
    p_deg.text = "B.Tech. Computer Science and Engineering"
    p_deg.font.name = FONT_BODY
    p_deg.font.size = Pt(11)
    p_deg.font.color.rgb = RGBColor(148, 163, 184)

    # Guides Card
    add_card(s1, 8.3, 4.45, 3.8, 2.3, bg_color=RGBColor(26, 46, 85), border_color=TEAL_ACCENT)
    tx_box = s1.shapes.add_textbox(Inches(8.5), Inches(4.55), Inches(3.4), Inches(2.1))
    tf = tx_box.text_frame
    p = tf.paragraphs[0]
    p.text = "UNDER THE GUIDANCE OF:"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACCENT

    p_g1 = tf.add_paragraph()
    p_g1.text = "Dr. Priyanga S"
    p_g1.font.name = FONT_BODY
    p_g1.font.size = Pt(13)
    p_g1.font.bold = True
    p_g1.font.color.rgb = WHITE

    p_g1_d = tf.add_paragraph()
    p_g1_d.text = "Assistant Professor, Dept. of NWC"
    p_g1_d.font.name = FONT_BODY
    p_g1_d.font.size = Pt(11)
    p_g1_d.font.color.rgb = RGBColor(148, 163, 184)

    p_g2 = tf.add_paragraph()
    p_g2.text = "Dr. Lakshmi M"
    p_g2.font.name = FONT_BODY
    p_g2.font.size = Pt(13)
    p_g2.font.bold = True
    p_g2.font.color.rgb = WHITE

    p_g2_d = tf.add_paragraph()
    p_g2_d.text = "Professor & Head, Dept. of NWC"
    p_g2_d.font.name = FONT_BODY
    p_g2_d.font.size = Pt(11)
    p_g2_d.font.color.rgb = RGBColor(148, 163, 184)

    # =========================================================================
    # SLIDE 2: PRESENTATION OUTLINE
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, LIGHT_BG)
    add_header(s2, "Presentation Outline & Agenda")

    agenda_items = [
        ("01", "Problem Statement & Motivation", "OS architectural heterogeneity, existing tooling silos, and educational gaps."),
        ("02", "Project Objectives", "Clean adapter abstraction, native telemetry, packet inspection, and transparent scoring."),
        ("03", "Literature Survey & Gaps", "Comparative analysis: Lynis, MBSA, OpenSCAP, OSQuery vs. CSSA."),
        ("04", "Architecture & Design", "Decoupled 9-tier pipeline, Platform Adapter pattern, and normalized data models."),
        ("05", "OS Internals Telemetry", "Deep inspection across Windows (CIM, Registry) & Linux (/proc, systemd, ss)."),
        ("06", "Wireshark / tshark Engine", "Dual-tier live packet capture, BPF filters, and pure-Python PCAP threat parser."),
        ("07", "Rule Engine & Normalization", "Decoupled JSON security benchmarks, condition evaluators, and finding models."),
        ("08", "Transparent Scoring Model", "Mathematical penalty deductions, solving penalty collapse via category capping."),
        ("09", "GUI Walkthrough & Demos", "Visual inspection of Dashboard, telemetry tabs, and live packet inspection."),
        ("10", "Baseline Drift & Reporting", "Configuration drift detection, delta diffing, and HTML/PDF/Markdown exports."),
        ("11", "Results & Verification", "Full automated test suite verification (80/80 passed), execution benchmarks."),
        ("12", "Conclusion & Future Work", "Defensive security guarantees, academic takeaways, and roadmap.")
    ]

    for idx, (num, title, desc) in enumerate(agenda_items):
        col = idx // 6
        row = idx % 6
        left = 0.8 + col * 6.0
        top = 1.45 + row * 0.95
        add_card(s2, left, top, 5.7, 0.85, bg_color=CARD_BG)

        # Number badge
        badge = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left + 0.15), Inches(top + 0.15), Inches(0.65), Inches(0.55))
        badge.fill.solid()
        badge.fill.fore_color.rgb = NAVY_HEADER
        badge.line.fill.background()
        tf_b = badge.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.alignment = PP_ALIGN.CENTER
        p_b.text = num
        p_b.font.name = FONT_HEADING
        p_b.font.size = Pt(14)
        p_b.font.bold = True
        p_b.font.color.rgb = WHITE

        # Text box
        tx_box = s2.shapes.add_textbox(Inches(left + 0.9), Inches(top + 0.08), Inches(4.6), Inches(0.7))
        tf = tx_box.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.name = FONT_HEADING
        p1.font.size = Pt(12)
        p1.font.bold = True
        p1.font.color.rgb = NAVY_DARK

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_BODY
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = SLATE_GRAY

    # =========================================================================
    # SLIDE 3: PROBLEM STATEMENT & MOTIVATION
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, LIGHT_BG)
    add_header(s3, "Problem Statement & Project Motivation")

    # Card 1: Architectural Divergence
    add_card(s3, 0.8, 1.45, 5.6, 5.5)
    tx = s3.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(5.2), Inches(5.1))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "1. Operating System Divergence"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    pts1 = [
        ("Privilege Disparity: ", "Windows governs administrative tokens via SIDs, UAC, and token elevation types; Linux uses POSIX UIDs, sudo groups, and kernel capabilities."),
        ("Configuration Silos: ", "Windows stores security configurations inside binary registry hives (HKLM, SAM, CIM); Linux maintains plaintext configs across /etc."),
        ("Service Semantics: ", "Windows Service Control Manager (SCM) uses Status & Startup Type; Linux systemd uses ActiveState and UnitFileState."),
        ("Access Control: ", "Windows relies on Discretionary ACLs (DACLs) with inheritance; Linux enforces octal mode bits (rwx) and SUID/SGID bits.")
    ]
    for prefix, body in pts1:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = prefix
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(11.5)
        r1.font.color.rgb = CHARCOAL
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(11.5)
        r2.font.color.rgb = SLATE_GRAY

    # Card 2: Existing Tooling Deficiencies
    add_card(s3, 6.8, 1.45, 5.7, 5.5)
    tx = s3.shapes.add_textbox(Inches(7.0), Inches(1.6), Inches(5.3), Inches(5.1))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "2. Limitations of Existing Tools"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    pts2 = [
        ("Rigid Platform Locks: ", "Lynis is 100% shell-scripted (Linux only); MBSA and Security Compliance Toolkit are Windows-only and officially deprecated."),
        ("Black-Box Scoring: ", "Commercial tools (Nessus, Qualys) use opaque proprietary risk scores without mathematical deduction transparency."),
        ("Penalty Collapse: ", "Traditional scoring subtracts fixed penalties repeatedly, driving scores to zero for multiple minor file misconfigurations."),
        ("No Unified Packet Visibility: ", "Host configuration auditors ignore in-flight cleartext traffic; packet capture tools ignore host configuration baselines."),
        ("Academic Gap: ", "Students lack a non-invasive, cross-platform auditor supporting offline simulation (Windows/Linux demo fixtures).")
    ]
    for prefix, body in pts2:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = prefix
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(11.5)
        r1.font.color.rgb = CHARCOAL
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(11.5)
        r2.font.color.rgb = SLATE_GRAY

    # =========================================================================
    # SLIDE 4: PROJECT OBJECTIVES
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, LIGHT_BG)
    add_header(s4, "Project Objectives & Design Goals")

    objs = [
        ("Platform Abstraction", "Implement an abstract base adapter (SecurityPlatformAdapter) enforcing uniform querying contracts across Windows, Linux, and macOS.", "platforms/base.py"),
        ("Native OS Inspection", "Safely extract real OS telemetry (users, processes, services, firewall, sockets, permissions, startup) without destructive actions.", "platforms/{os}/"),
        ("Data Normalization", "Standardize disparate OS data into strongly typed dataclasses (e.g. 0.0.0.0 vs 127.0.0.1 socket exposure classification).", "core/normalizer.py"),
        ("Packet Threat Inspection", "Embed Wireshark's tshark CLI & pure-Python PCAP parser to detect plaintext credentials and legacy SSL/TLS handshakes.", "platforms/packet_capture.py"),
        ("Configurable Rule Engine", "Evaluate system state against JSON security rules modeled on CIS Benchmarks with customizable conditions and remediation advice.", "core/rule_engine.py"),
        ("Transparent Scoring", "Calculate 0–100 security score with category penalty capping (max 35 pts/cat) to eliminate 'penalty collapse'.", "core/scoring.py"),
        ("Baseline Drift & History", "Track security posture drift across time using SQLite audit records and delta diff comparison.", "core/baseline.py"),
        ("Modern Desktop GUI", "Deliver a responsive PySide6 interface with asynchronous QThread background audits and multi-format reporting (HTML, PDF, MD).", "gui/ & reports/")
    ]

    for idx, (title, desc, code_ref) in enumerate(objs):
        row = idx // 4
        col = idx % 4
        left = 0.8 + col * 2.95
        top = 1.5 + row * 2.65
        add_card(s4, left, top, 2.8, 2.4)

        tx = s4.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.15), Inches(2.5), Inches(2.1))
        tf = tx.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = f"{idx+1}. {title}"
        p.font.name = FONT_HEADING
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = NAVY_HEADER

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_BODY
        p2.font.size = Pt(10)
        p2.font.color.rgb = CHARCOAL

        p3 = tf.add_paragraph()
        p3.text = f"Ref: {code_ref}"
        p3.font.name = FONT_BODY
        p3.font.size = Pt(9)
        p3.font.italic = True
        p3.font.color.rgb = TEAL_ACCENT

    # =========================================================================
    # SLIDE 5: LITERATURE SURVEY & COMPARATIVE ANALYSIS
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, LIGHT_BG)
    add_header(s5, "Literature Survey: Comparative Feature Matrix")

    # Table of comparison
    comp_headers = ["Auditing Capability", "Lynis", "MBSA / SCT", "OpenSCAP", "OSQuery", "CSSA (Our Work)"]
    comp_data = [
        ["Target Operating Systems", "Linux / Unix Only", "Windows Only", "Linux (Win partial)", "Win, Linux, Mac", "Windows, Linux, macOS"],
        ["Execution Architecture", "Shell Scripts", "Win32 / GPO", "C / Python / XML", "C++ Daemon", "Python 3.11+ / PySide6"],
        ["Graphical User Interface", "No (CLI only)", "Deprecated GUI", "SCAP Workbench", "No (CLI / Fleet)", "Yes (Modern Dark/Light)"],
        ["Rule Configuration", "Shell Functions", "GPO Templates", "Complex OVAL XML", "SQL Query Files", "Human-Readable JSON"],
        ["Score Calculation", "Hardcoded Index", "Binary Pass/Fail", "Weighted Score", "None (Raw Data)", "Yes (0–100 Capped Math)"],
        ["Packet Threat Analysis", "No", "No", "No", "No", "Yes (Wireshark / tshark)"],
        ["Read-Only Guarantees", "Yes", "Yes", "Yes", "Yes", "Yes (Strict Invariant)"],
        ["Offline Demo Simulation", "No", "No", "No", "No", "Yes (Win/Linux Fixtures)"],
        ["Baseline Drift Diffing", "Basic Log Diff", "No", "Result Diff", "Diff Queries", "Yes (Built-in Diff Engine)"],
        ["Multi-Format Reports", "Text Log / HTML", "XML / HTML", "HTML / ARF", "JSON / CSV", "HTML, PDF, JSON, CSV, MD"]
    ]

    t_shape = s5.shapes.add_table(len(comp_data) + 1, len(comp_headers), Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.3))
    table = t_shape.table

    # Column widths
    col_widths = [2.5, 1.4, 1.4, 1.6, 1.6, 3.233]
    for c_idx, w in enumerate(col_widths):
        table.columns[c_idx].width = Inches(w)

    for i, title in enumerate(comp_headers):
        cell = table.rows[0].cells[i]
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_HEADER if i < 5 else TEAL_ACCENT
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = WHITE

    for r_idx, row in enumerate(comp_data):
        for c_idx, val in enumerate(row):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.fill.solid()
            if c_idx == 5:
                cell.fill.fore_color.rgb = RGBColor(236, 253, 245) # Light green highlight for CSSA
            elif r_idx % 2 == 1:
                cell.fill.fore_color.rgb = RGBColor(241, 245, 249)
            else:
                cell.fill.fore_color.rgb = WHITE
            
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(10)
            if c_idx == 5:
                p.font.bold = True
                p.font.color.rgb = NAVY_DARK
            else:
                p.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 6: SYSTEM ARCHITECTURE
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, LIGHT_BG)
    add_header(s6, "CSSA System Architecture: 9-Tier Decoupled Pipeline")

    arch_layers = [
        ("Layer 1: Presentation Layer", "PySide6 (Qt 6) Desktop GUI: Dashboard, Telemetry Views, Custom Score Gauge, Theme Engine", TEAL_ACCENT),
        ("Layer 2: Orchestration Layer", "Audit Controller: Asynchronous QThread worker, Mode Switching (Real Host vs Demo Fixtures)", NAVY_HEADER),
        ("Layer 3: Abstraction Contract", "SecurityPlatformAdapter: Abstract Base Class defining standard interface for all platforms", NAVY_DARK),
        ("Layer 4: Platform Adapters", "Windows Adapter (CIM, Registry, icacls) | Linux Adapter (/proc, systemd, ss, ufw) | macOS Adapter", NAVY_HEADER),
        ("Layer 5: Network Traffic Layer", "Packet Capture Engine: Wireshark / tshark CLI BPF captures + Pure-Python PCAP binary dissector", TEAL_ACCENT),
        ("Layer 6: Normalization Layer", "Data Normalizer: Maps raw OS state to unified dataclasses (socket exposure, service lifecycle)", NAVY_DARK),
        ("Layer 7: Evaluation Layer", "Configurable Rule Engine: Evaluates normalized state against CIS/DISA JSON rule benchmarks", NAVY_HEADER),
        ("Layer 8: Risk Assessment Layer", "Scoring Engine: Calculates 0–100 score with category penalty capping to prevent penalty collapse", TEAL_ACCENT),
        ("Layer 9: Storage & Reporting", "Persistence & Export: SQLite thread-safe database, baseline drift engine, HTML/PDF/JSON reports", NAVY_DARK)
    ]

    for idx, (layer_title, layer_desc, color) in enumerate(arch_layers):
        top = 1.45 + idx * 0.62
        # Layer Card
        bar = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(top), Inches(11.333), Inches(0.56))
        bar.fill.solid()
        bar.fill.fore_color.rgb = WHITE
        bar.line.color.rgb = color
        bar.line.width = Pt(1.5)

        # Left tag
        tag = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.05), Inches(top + 0.05), Inches(2.6), Inches(0.46))
        tag.fill.solid()
        tag.fill.fore_color.rgb = color
        tag.line.fill.background()
        tf_t = tag.text_frame
        p_t = tf_t.paragraphs[0]
        p_t.alignment = PP_ALIGN.CENTER
        p_t.text = layer_title
        p_t.font.name = FONT_HEADING
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = WHITE

        # Description text
        tx = s6.shapes.add_textbox(Inches(3.8), Inches(top + 0.06), Inches(8.3), Inches(0.45))
        tf = tx.text_frame
        p = tf.paragraphs[0]
        p.text = layer_desc
        p.font.name = FONT_BODY
        p.font.size = Pt(10.5)
        p.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 7: WINDOWS INTERNALS INSPECTION
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, LIGHT_BG)
    add_header(s7, "Operating System Internals: Microsoft Windows")

    win_subsystems = [
        ("System & CPU Telemetry", "Get-CimInstance Win32_OperatingSystem / Win32_Processor", "Queries OS build, architecture, system uptime, and CPU hardware topology without legacy WMIC.", "platforms/windows/system.py"),
        ("User Accounts & Groups", "net localgroup Administrators / Get-LocalUser", "Identifies qualified administrators, disabled accounts, guest status, and excessive group memberships.", "platforms/windows/users.py"),
        ("Services & SCM State", "Get-Service | Select-Object Name,Status,StartType", "Audits background services, unquoted service binary paths, and unauthorized automatic service startups.", "platforms/windows/services.py"),
        ("Host Firewall Profiles", "netsh advfirewall show allprofiles", "Inspects Domain, Private, and Public profile statuses and total count of active firewall filtering rules.", "platforms/windows/firewall.py"),
        ("Network Socket Bindings", "Get-NetTCPConnection -State Listen / netstat -ano", "Extracts listening ports, maps owning PIDs to process names, and classifies wildcard 0.0.0.0 exposure.", "platforms/windows/network.py"),
        ("NTFS Access Control (ACLs)", "icacls <path> / Get-Acl", "Queries NTFS Discretionary ACLs on System32 and Program Files to detect permissive 'Everyone' write access.", "platforms/windows/permissions.py"),
        ("Autoruns & Persistence", "reg.exe query HKLM\\...\\Run / Get-ScheduledTask", "Inspects Run / RunOnce registry persistence keys and active scheduled background tasks.", "platforms/windows/startup.py"),
        ("Local Security Policies", "net accounts / auditpol /get /category:Logon/Logoff", "Audits password age, minimum password length, account lockout thresholds, and logon event logging.", "platforms/windows/policies.py")
    ]

    for idx, (title, cmd, desc, code_path) in enumerate(win_subsystems):
        row = idx // 2
        col = idx % 2
        left = 0.8 + col * 5.95
        top = 1.45 + row * 1.38
        add_card(s7, left, top, 5.75, 1.25)

        tx = s7.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.08), Inches(5.45), Inches(1.1))
        tf = tx.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = f"{title}  [{code_path}]"
        p1.font.name = FONT_HEADING
        p1.font.size = Pt(11.5)
        p1.font.bold = True
        p1.font.color.rgb = NAVY_HEADER

        p2 = tf.add_paragraph()
        p2.text = f"Command: {cmd}"
        p2.font.name = "Consolas"
        p2.font.size = Pt(9.5)
        p2.font.bold = True
        p2.font.color.rgb = TEAL_ACCENT

        p3 = tf.add_paragraph()
        p3.text = desc
        p3.font.name = FONT_BODY
        p3.font.size = Pt(9.5)
        p3.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 8: LINUX INTERNALS INSPECTION
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, LIGHT_BG)
    add_header(s8, "Operating System Internals: GNU/Linux")

    linux_subsystems = [
        ("Kernel & Virtual Filesystems", "/proc/cpuinfo, /proc/meminfo, /etc/os-release", "Directly queries kernel memory, CPU cores, uptime, and distribution info without spawning shell interpreters.", "platforms/linux/system.py"),
        ("Users & Privilege Models", "/etc/passwd, /etc/group (wheel/sudo/root)", "Enumerates UIDs, shells (/bin/bash vs /nologin), tests shadow boundary, and identifies sudo privilege members.", "platforms/linux/users.py"),
        ("Systemd Unit Management", "systemctl list-units --type=service --all", "Inspects unit ActiveState (active/inactive) and UnitFileState (enabled/disabled) across background daemons.", "platforms/linux/services.py"),
        ("Packet Filtering & Firewalls", "ufw status / nft list ruleset / iptables -L -n", "Multi-backend firewall detection supporting modern nftables, Ubuntu UFW, and legacy iptables rulesets.", "platforms/linux/firewall.py"),
        ("Socket Telemetry (iproute2)", "ss -tulnp", "High-performance netlink socket query identifying listening ports, bound addresses, and owning PID/process names.", "platforms/linux/network.py"),
        ("POSIX Modes & SUID Bits", "stat -c \"%a %U %G\" / find / -perm -4000", "Audits permissions on /etc/shadow, /etc/sudoers, and identifies high-risk SUID root executable binaries.", "platforms/linux/permissions.py"),
        ("Scheduled Tasks & Crons", "systemctl list-unit-files / /etc/cron.* / crontab", "Audits enabled boot services, system-wide cron spool directories, and user-level crontab persistence.", "platforms/linux/startup.py"),
        ("SSH & Password Policies", "/etc/ssh/sshd_config / /etc/login.defs", "Audits PermitRootLogin, PasswordAuthentication, PASS_MAX_DAYS, PASS_MIN_LEN, and default system UMASK.", "platforms/linux/policies.py")
    ]

    for idx, (title, cmd, desc, code_path) in enumerate(linux_subsystems):
        row = idx // 2
        col = idx % 2
        left = 0.8 + col * 5.95
        top = 1.45 + row * 1.38
        add_card(s8, left, top, 5.75, 1.25)

        tx = s8.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.08), Inches(5.45), Inches(1.1))
        tf = tx.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = f"{title}  [{code_path}]"
        p1.font.name = FONT_HEADING
        p1.font.size = Pt(11.5)
        p1.font.bold = True
        p1.font.color.rgb = NAVY_HEADER

        p2 = tf.add_paragraph()
        p2.text = f"Interface / Cmd: {cmd}"
        p2.font.name = "Consolas"
        p2.font.size = Pt(9.5)
        p2.font.bold = True
        p2.font.color.rgb = TEAL_ACCENT

        p3 = tf.add_paragraph()
        p3.text = desc
        p3.font.name = FONT_BODY
        p3.font.size = Pt(9.5)
        p3.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 9: WIRESHARK & TSHARK PACKET THREAT ENGINE
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, LIGHT_BG)
    add_header(s9, "Network Threat Engine: Wireshark / tshark Integration")

    # Left: Architecture
    add_card(s9, 0.8, 1.45, 5.7, 5.5)
    tx = s9.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(5.3), Inches(5.2))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Dual-Tier Packet Capture Engine"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    pts_pcap = [
        ("Tier 1 — TShark CLI Engine: ", "Executes headless live capture via 'tshark -i <iface> -a duration:N -c N -w temp.pcap' with custom Berkeley Packet Filters (BPF)."),
        ("Tier 2 — Pure-Python PCAP Parser: ", "Autonomous binary dissector (core/pcap_parser.py) reading PCAP (0xa1b2c3d4) & PCAPNG (0x0a0d0d0a) structures via struct.unpack without external C dependencies."),
        ("Zero-Crash Fallback: ", "If Wireshark is not installed, the audit engine gracefully falls back to synthetic or user-supplied PCAP analysis without throwing unhandled exceptions."),
        ("CLI & Standalone Entry: ", "platforms/packet_capture.py provides standalone terminal usage: --version, -D (list interfaces), --live, and -r <file.pcap>.")
    ]
    for prefix, body in pts_pcap:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = prefix
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = CHARCOAL
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(11)
        r2.font.color.rgb = SLATE_GRAY

    # Right: Threats Detected
    add_card(s9, 6.8, 1.45, 5.7, 5.5)
    tx = s9.shapes.add_textbox(Inches(7.0), Inches(1.6), Inches(5.3), Inches(5.2))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Inspected Network Threat Signatures"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    threats = [
        ("Plaintext Authentication (HIGH)", "Detects cleartext 'Authorization: Basic', FTP 'USER'/'PASS' commands, and unencrypted Telnet credential transmissions.", RED_ACCENT),
        ("Deprecated SSL/TLS Protocols (HIGH)", "Dissects TLS Record layer to detect SSL 2.0 (0x0200), SSL 3.0 (0x0300), TLS 1.0 (0x0301), and TLS 1.1 (0x0302) vulnerable to POODLE & BEAST attacks.", RED_ACCENT),
        ("Broadcast Name Resolution Poisoning (MEDIUM)", "Detects LLMNR (port 5355) and NetBIOS-NS (port 137) broadcast traffic vulnerable to adversary credential relay attacks (Responder).", TEAL_ACCENT),
        ("Security Score Integration", "Detected packet threats trigger automated rule evaluations in rule_engine.py and directly apply category-capped deductions to the overall audit score.", NAVY_HEADER)
    ]
    for title, desc, color in threats:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = f"• {title}\n"
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(11.5)
        r1.font.color.rgb = color
        r2 = p.add_run()
        r2.text = desc
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10.5)
        r2.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 10: RULE ENGINE & NORMALIZATION
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, LIGHT_BG)
    add_header(s10, "Normalization Pipeline & Configurable Rule Engine")

    # Card 1: Normalization
    add_card(s10, 0.8, 1.45, 5.7, 5.5)
    tx = s10.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(5.3), Inches(5.2))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Data Normalization Engine"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    norm_pts = [
        ("Socket Exposure Normalization: ", "Classifies socket bindings into NetworkExposure.LOCAL_ONLY (127.0.0.1, ::1) vs NetworkExposure.NETWORK_EXPOSED (0.0.0.0, ::, LAN IPs) to eliminate false-positive port alerts."),
        ("Service Lifecycle Normalization: ", "Translates Windows SCM status & Linux systemd ActiveState to ServiceStatus (RUNNING, STOPPED, UNKNOWN) and ServiceStartup (AUTOMATIC, MANUAL, DISABLED)."),
        ("Strongly Typed Dataclasses: ", "Encapsulates all telemetry into 14 immutable dataclass models (SystemInfo, UserAccount, ProcessInfo, NetworkConnection, FirewallStatus, FilePermission, etc.).")
    ]
    for prefix, body in norm_pts:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = prefix
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = CHARCOAL
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(11)
        r2.font.color.rgb = SLATE_GRAY

    # Card 2: Rule Engine
    add_card(s10, 6.8, 1.45, 5.7, 5.5)
    tx = s10.shapes.add_textbox(Inches(7.0), Inches(1.6), Inches(5.3), Inches(5.2))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "JSON Security Rule Engine"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    rules_pts = [
        ("Rule Categories: ", "23 active production rules separated into common_rules.json (cross-platform), windows_rules.json, linux_rules.json, and macos_rules.json."),
        ("Condition Evaluators: ", "Implements dynamic evaluators for firewall_disabled, port_exposed, admin_count_exceeded, root_ssh_permitted, unquoted_service_path, packet_threats_present, etc."),
        ("Actionable Output: ", "Each rule emits structured Finding objects containing Severity, Category, Status (PASS/WARNING/FAIL), Evidence, Rationale, and Remediation steps."),
        ("Zero Code Changes: ", "Administrators can tune thresholds (e.g. max_admin_users) or add new CIS compliance checks simply by modifying JSON files.")
    ]
    for prefix, body in rules_pts:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = prefix
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = CHARCOAL
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(11)
        r2.font.color.rgb = SLATE_GRAY

    # =========================================================================
    # SLIDE 11: TRANSPARENT SCORING & PENALTY CAPPING
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, LIGHT_BG)
    add_header(s11, "Mathematical Scoring Model: Preventing Penalty Collapse")

    # Card 1: The Math
    add_card(s11, 0.8, 1.45, 5.7, 5.5)
    tx = s11.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(5.3), Inches(5.2))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "1. Severity Deductions & Capping"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    p_m1 = tf.add_paragraph()
    p_m1.text = "Base Score: 100 Points (Pristine System)"
    p_m1.font.name = FONT_HEADING
    p_m1.font.size = Pt(12)
    p_m1.font.bold = True
    p_m1.font.color.rgb = GREEN_ACCENT

    deductions = [
        ("CRITICAL Finding: ", "25 points deduction", RED_ACCENT),
        ("HIGH Finding: ", "15 points deduction", RED_ACCENT),
        ("MEDIUM Finding: ", "8 points deduction", TEAL_ACCENT),
        ("LOW Finding: ", "3 points deduction", SLATE_GRAY),
        ("INFO Finding: ", "0 points deduction", SLATE_GRAY)
    ]
    for label, val, col in deductions:
        p = tf.add_paragraph()
        r = p.add_run()
        r.text = f"• {label}"
        r.font.name = FONT_HEADING
        r.font.bold = True
        r.font.size = Pt(11)
        r.font.color.rgb = col
        r2 = p.add_run()
        r2.text = val
        r2.font.name = FONT_BODY
        r2.font.size = Pt(11)

    p_sol = tf.add_paragraph()
    p_sol.text = "\nThe Penalty Collapse Solution:"
    p_sol.font.name = FONT_HEADING
    p_sol.font.size = Pt(12)
    p_sol.font.bold = True
    p_sol.font.color.rgb = NAVY_HEADER

    p_sol_t = tf.add_paragraph()
    p_sol_t.text = "To prevent duplicate findings in one category (e.g. 15 world-writable tmp files) from reducing the score to zero, each category deduction is capped at 35 points: Total Deduction = Σ min(CatDeduction, 35)."
    p_sol_t.font.name = FONT_BODY
    p_sol_t.font.size = Pt(10.5)
    p_sol_t.font.color.rgb = CHARCOAL

    # Card 2: Risk Bands Table
    add_card(s11, 6.8, 1.45, 5.7, 5.5)
    tx = s11.shapes.add_textbox(Inches(7.0), Inches(1.6), Inches(5.3), Inches(1.0))
    tf = tx.text_frame
    p = tf.paragraphs[0]
    p.text = "2. Qualitative Risk Level Bands"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    bands_headers = ["Score Range", "Risk Level Band", "Posture Assessment"]
    bands_data = [
        ["90 – 100", "EXCELLENT", "Strong defensive posture; minimal risk."],
        ["75 – 89", "GOOD", "Solid security baseline; minor tuning recommended."],
        ["60 – 74", "NEEDS IMPROVEMENT", "Notable misconfigurations requiring review."],
        ["40 – 59", "HIGH RISK", "Significant exposures (firewall disabled, exposed ports)."],
        ["0 – 39", "CRITICAL RISK", "Severe systemic vulnerabilities requiring immediate fix."]
    ]

    t_bands = s11.shapes.add_table(6, 3, Inches(7.0), Inches(2.6), Inches(5.3), Inches(4.0)).table
    t_bands.columns[0].width = Inches(1.3)
    t_bands.columns[1].width = Inches(1.6)
    t_bands.columns[2].width = Inches(2.4)

    for i, title in enumerate(bands_headers):
        cell = t_bands.rows[0].cells[i]
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_HEADER
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = WHITE

    for r_idx, row in enumerate(bands_data):
        for c_idx, val in enumerate(row):
            cell = t_bands.rows[r_idx + 1].cells[c_idx]
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(241, 245, 249) if r_idx % 2 == 1 else WHITE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if c_idx < 2 else PP_ALIGN.LEFT
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(9.5)
            if c_idx == 1:
                p.font.bold = True
                p.font.color.rgb = GREEN_ACCENT if r_idx < 2 else (TEAL_ACCENT if r_idx == 2 else RED_ACCENT)
            else:
                p.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 12: GUI WALKTHROUGH — DASHBOARD
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, LIGHT_BG)
    add_header(s12, "Interactive GUI: Main Security Dashboard")

    # Embed Screenshot
    dash_img = SCREENSHOTS_DIR / "01_dashboard.png"
    if dash_img.exists():
        s12.shapes.add_picture(str(dash_img), Inches(0.8), Inches(1.5), width=Inches(7.2))

    # Right Card: Feature Highlights
    add_card(s12, 8.2, 1.5, 4.333, 5.4)
    tx = s12.shapes.add_textbox(Inches(8.4), Inches(1.7), Inches(3.9), Inches(5.0))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Dashboard Key Capabilities"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    dash_features = [
        ("Circular Score Gauge: ", "Custom vector Qt paint widget dynamically coloring according to risk band (Green/Yellow/Red)."),
        ("Live Audit Trigger: ", "Executes full audit in the background via QThread worker without causing main UI freezing."),
        ("Mode Selector Dropdown: ", "Switch instantly between REAL SYSTEM audit and simulated DEMO - WINDOWS (68/100) or DEMO - LINUX (82/100) fixtures."),
        ("Category Breakdown: ", "Cards display pass/warning/fail ratios across Firewall, Users, Network, Services, and Permissions."),
        ("Finding Counters: ", "Immediate counts of Critical, High, Medium, and Low severity issues.")
    ]
    for prefix, body in dash_features:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = prefix
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = CHARCOAL
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = SLATE_GRAY

    # =========================================================================
    # SLIDE 13: GUI WALKTHROUGH — FINDINGS & TELEMETRY
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, LIGHT_BG)
    add_header(s13, "GUI Walkthrough: Findings & Detailed Telemetry")

    # Embed Screenshot
    find_img = SCREENSHOTS_DIR / "10_findings.png"
    if find_img.exists():
        s13.shapes.add_picture(str(find_img), Inches(0.8), Inches(1.5), width=Inches(7.2))

    # Right Card: Telemetry features
    add_card(s13, 8.2, 1.5, 4.333, 5.4)
    tx = s13.shapes.add_textbox(Inches(8.4), Inches(1.7), Inches(3.9), Inches(5.0))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Audit Findings & Inspection"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    find_features = [
        ("Filterable Security Findings: ", "Filter findings by severity badge (Critical, High, Medium, Low) or search by keyword."),
        ("Remediation Advice: ", "Selecting any finding displays exact technical evidence, security rationale, and step-by-step remediation."),
        ("Packet Capture View: ", "Select interface, define BPF filters (e.g. 'tcp port 80'), run live tshark captures, and view detected threats."),
        ("Process & Service Views: ", "Examines active processes, PIDs, memory utilization, and background service unit configurations."),
        ("Firewall & Sockets: ", "Visualizes active profiles and listening ports with automated 'Network Exposed' warnings.")
    ]
    for prefix, body in find_features:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = prefix
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = CHARCOAL
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = SLATE_GRAY

    # =========================================================================
    # SLIDE 14: BASELINE DRIFT & REPORTING
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, LIGHT_BG)
    add_header(s14, "Baseline Drift Analysis & Multi-Format Reporting")

    # Embed Screenshot
    base_img = SCREENSHOTS_DIR / "12_baseline.png"
    if base_img.exists():
        s14.shapes.add_picture(str(base_img), Inches(0.8), Inches(1.5), width=Inches(7.2))

    # Right Card: Baseline & Reports
    add_card(s14, 8.2, 1.5, 4.333, 5.4)
    tx = s14.shapes.add_textbox(Inches(8.4), Inches(1.7), Inches(3.9), Inches(5.0))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Drift Detection & Reporting"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    base_features = [
        ("Configuration Baselines: ", "Save any verified audit state as an organizational baseline stored in SQLite relational tables."),
        ("Delta Diff Engine: ", "Performs set-difference comparisons to detect added, removed, or modified configurations across audits."),
        ("Audit History Tracking: ", "Maintains persistent records of past audits, score trajectories, and severity distributions."),
        ("Multi-Format Export: ", "Generate self-contained executive reports with one click: HTML5 (responsive styling), high-res PDF, JSON, CSV, and GitHub Markdown.")
    ]
    for prefix, body in base_features:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = prefix
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = CHARCOAL
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = SLATE_GRAY

    # =========================================================================
    # SLIDE 15: RESULTS & VERIFICATION
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, LIGHT_BG)
    add_header(s15, "Experimental Verification: Test Suite & Performance")

    # Table of tests
    test_headers = ["Subsystem / Test Module", "Subsystem Verification Focus", "Tests Run", "Pass Rate"]
    test_data = [
        ["test_packet_capture.py", "PCAP parser, tshark CLI, plaintext auth, TLS dissection, BPF", "13", "100% Passed"],
        ["test_scoring.py", "Base 100, severity penalties, category capping, risk band boundaries", "8", "100% Passed"],
        ["test_rules.py", "JSON rule loading, condition evaluators, platform filtering, disabled rules", "8", "100% Passed"],
        ["test_windows_parsers.py", "Parsing net user, localgroup, netsh firewall, net accounts, icacls", "7", "100% Passed"],
        ["test_macos_parsers.py", "macOS SIP, Gatekeeper, FileVault, firewall, services, processes", "7", "100% Passed"],
        ["test_linux_parsers.py", "Parsing /etc/passwd, /etc/group, systemctl, ss sockets, sshd_config", "5", "100% Passed"],
        ["test_normalizer.py", "Socket exposure classification (0.0.0.0 vs 127.0.0.1), service status", "6", "100% Passed"],
        ["test_baseline.py", "Baseline creation, tuple extraction, delta diffing (added/removed/modified)", "6", "100% Passed"],
        ["test_database.py", "SQLite initialization, audit saving/retrieval, baseline storage, settings", "6", "100% Passed"],
        ["test_report.py", "HTML report generation, PDF fallback, CSV, JSON, Markdown exports", "6", "100% Passed"],
        ["test_platform_detection.py", "Platform detection logic, privilege level detection (admin/sudo/root)", "5", "100% Passed"],
        ["test_gui_integration.py", "PySide6 widget updates, theme compilation, async view refresh", "3", "100% Passed"],
        ["OVERALL TEST SUITE", "Comprehensive automated pytest test suite verification", "80", "100% (80/80)"]
    ]

    t_tests = s15.shapes.add_table(len(test_data) + 1, 4, Inches(0.8), Inches(1.5), Inches(8.0), Inches(5.4)).table
    t_tests.columns[0].width = Inches(2.2)
    t_tests.columns[1].width = Inches(3.6)
    t_tests.columns[2].width = Inches(0.9)
    t_tests.columns[3].width = Inches(1.3)

    for i, title in enumerate(test_headers):
        cell = t_tests.rows[0].cells[i]
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_HEADER
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = WHITE

    for r_idx, row in enumerate(test_data):
        for c_idx, val in enumerate(row):
            cell = t_tests.rows[r_idx + 1].cells[c_idx]
            cell.fill.solid()
            if r_idx == len(test_data) - 1:
                cell.fill.fore_color.rgb = RGBColor(220, 252, 231) # Green for overall
            elif r_idx % 2 == 1:
                cell.fill.fore_color.rgb = RGBColor(241, 245, 249)
            else:
                cell.fill.fore_color.rgb = WHITE
            
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx < 2 else PP_ALIGN.CENTER
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(9)
            if r_idx == len(test_data) - 1 or c_idx == 3:
                p.font.bold = True
                p.font.color.rgb = GREEN_ACCENT if c_idx == 3 else NAVY_DARK
            else:
                p.font.color.rgb = CHARCOAL

    # Right Card: Performance benchmarks
    add_card(s15, 9.0, 1.5, 3.533, 5.4)
    tx = s15.shapes.add_textbox(Inches(9.2), Inches(1.7), Inches(3.1), Inches(5.0))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Audit Execution Benchmarks"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    benchmarks = [
        ("Simulated Demo Audit: ", "< 0.25 seconds execution time for full Windows or Linux fixture evaluation."),
        ("Live Host System Audit: ", "1.4 to 2.8 seconds execution time querying all live OS subsystems."),
        ("TShark Live Capture: ", "Strictly bounded (e.g. 5–10s duration) without hanging."),
        ("Memory Footprint: ", "Low overhead (< 85 MB RAM usage during active Qt rendering).")
    ]
    for prefix, body in benchmarks:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = prefix
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = CHARCOAL
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = SLATE_GRAY

    # =========================================================================
    # SLIDE 16: CONCLUSION & DEFENSIVE GUARANTEES
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16, NAVY_DARK)

    # Accent decorative bar
    top_bar = s16.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = TEAL_ACCENT
    top_bar.line.fill.background()

    # Title
    tx = s16.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.333), Inches(0.8))
    tf = tx.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "Conclusion & Defensive Security Invariants"
    p.font.name = FONT_HEADING
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE

    # Card 1: Key Achievements
    add_card(s16, 1.2, 1.9, 5.2, 4.8, bg_color=RGBColor(26, 46, 85), border_color=TEAL_ACCENT)
    tx = s16.shapes.add_textbox(Inches(1.4), Inches(2.1), Inches(4.8), Inches(4.4))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Summary of Contributions"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACCENT

    achieve = [
        ("Cross-Platform Unity: ", "Bridges Windows CIM/Registry and Linux /proc/systemd under an identical auditing abstraction."),
        ("Defensive Invariant: ", "Strictly read-only; zero credential harvesting, zero penetration testing, and zero automatic system modification."),
        ("Network Threat Visibility: ", "Integrated Wireshark/tshark live capture and binary PCAP dissection for cleartext credentials and legacy TLS."),
        ("Transparent Scoring: ", "Mathematically eliminates penalty collapse through category capping."),
        ("Academic Excellence: ", "Designed specifically for Windows & Linux Internals courses with built-in demo simulation modes.")
    ]
    for prefix, body in achieve:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = prefix
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = WHITE
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10.5)
        r2.font.color.rgb = RGBColor(203, 213, 225)

    # Card 2: Future Scope & Q&A
    add_card(s16, 6.8, 1.9, 5.3, 4.8, bg_color=RGBColor(26, 46, 85), border_color=TEAL_ACCENT)
    tx = s16.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(4.9), Inches(4.4))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Future Scope & Q&A"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACCENT

    future = [
        ("Remote Agentless Auditing: ", "Execute scans across remote hosts via safe SSH key authentication and WinRM."),
        ("eBPF Kernel Probing: ", "Integrate extended Berkeley Packet Filter (eBPF) tracing for real-time privilege escalation monitoring on Linux."),
        ("SIEM Integration: ", "Stream normalized audit records to Splunk, ELK, or Wazuh via Syslog / CEF."),
        ("Compliance Mapping: ", "Direct automated mapping to NIST 800-53 and ISO 27001 control matrices.")
    ]
    for prefix, body in future:
        p = tf.add_paragraph()
        r1 = p.add_run()
        r1.text = prefix
        r1.font.name = FONT_HEADING
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = WHITE
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10.5)
        r2.font.color.rgb = RGBColor(203, 213, 225)

    p_qa = tf.add_paragraph()
    p_qa.text = "\nTHANK YOU!\nQuestions & Answers"
    p_qa.alignment = PP_ALIGN.CENTER
    p_qa.font.name = FONT_HEADING
    p_qa.font.size = Pt(18)
    p_qa.font.bold = True
    p_qa.font.color.rgb = TEAL_ACCENT

    # Save presentation
    OUTPUT_PPTX.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT_PPTX))
    import shutil
    shutil.copyfile(str(OUTPUT_PPTX), str(ROOT_PPTX))

    print(f"Successfully generated PowerPoint presentation!")
    print(f"File 1: {OUTPUT_PPTX} ({OUTPUT_PPTX.stat().st_size} bytes)")
    print(f"File 2: {ROOT_PPTX} ({ROOT_PPTX.stat().st_size} bytes)")

if __name__ == '__main__':
    create_presentation()
