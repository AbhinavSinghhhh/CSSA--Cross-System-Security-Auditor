# Comprehensive Demonstration & Presentation Guide: CSSA

**Target Duration**: 7–12 minutes  
**Course**: Operating Systems + Windows/Linux Security  
**Presenter Goal**: Demonstrate the cross-platform architecture, automated defensive auditing, Wireshark packet capture & threat dissection, transparent scoring, configuration drift baselines, and executive reporting.

---

## Key Presentation Concept to Emphasize:
> *"CSSA (Cross-Platform System Security Auditor) is not a loose collection of scripts. It is a unified defensive security auditing framework where OS-specific adapters normalize disparate internals (Windows CIM/Registry/APIs vs Linux `/proc`/systemd/permissions vs macOS DSLocal/launchctl) into common data models evaluated by a centralized rule engine, transparent scoring system, and network packet threat analyzer."*

---

## 🚀 Two Ways to Deliver the Demonstration

CSSA provides **two flexible demonstration modes**:
1. **Automated CLI Walkthrough (`demo.py`)**: Runs in the terminal with colored output, stepping through all 6 security auditing stages in 15 seconds. Ideal for terminal recordings, rapid reviews, or CI/CD testing.
2. **Interactive Desktop GUI (`main.py` or `demo.py --gui`)**: The full PySide6 dark-theme desktop application with interactive tabs, filters, charts, and file dialogs.

---

## Method A: Automated CLI Demonstration (Quick 2-Minute Demo)

Run in your terminal:
```bash
# Demonstrate Windows Security Posture & Packet Threats
python3 demo.py --mode windows

# Or demonstrate Linux Server Security Posture
python3 demo.py --mode linux

# Or audit your live host machine
python3 demo.py --mode real
```

### What `demo.py` Walks Through Automatically:
1. **Stage 1 (Platform Detection)**: Identifies the host OS and initializes the appropriate adapter (`SecurityPlatformAdapter`).
2. **Stage 2 (Audit Execution & Rule Engine)**: Evaluates 13+ security rules across Identity, Network, Filesystem, Services, and System.
3. **Stage 3 (Wireshark Packet Capture & Threats)**:
   - Queries `tshark` CLI availability.
   - Dissects the bundled `fixtures/threat_sample.pcap` using the pure-Python PCAP parser.
   - Detects cleartext HTTP Basic Auth, plaintext FTP credentials, unencrypted Telnet, deprecated TLS 1.0, and LLMNR poisoning exposure.
4. **Stage 4 (Transparent Scoring)**: Breaks down category penalties and explains the 12-point category cap.
5. **Stage 5 (Baseline & Drift)**: Takes a baseline snapshot, simulates an unauthorized port opening (`0.0.0.0:4444`), and calculates configuration drift (`+ Added`).
6. **Stage 6 (Executive Reporting)**: Generates standalone HTML (`reports/demo_output/audit_report.html`) and Markdown reports.

---

## Method B: Step-by-Step Desktop GUI Demonstration (Full 8-Minute Flow)

Launch the desktop application:
```bash
python3 main.py
# or
python3 demo.py --gui
```

---

### Step 1: Application Launch & System Context
- **Action**: Show the main window upon startup. Point out the dark theme and top navigation bar.
- **What to say**:
  > *"Here is CSSA running on Python 3 and PySide6. The application is completely self-contained, lightweight, and strictly read-only. Notice the top bar displaying current mode and the sidebar organizing our audit modules."*

---

### Step 2: Live Host System Information
- **Action**: Click on **💻 System Information** in the sidebar.
- **What to say**:
  > *"CSSA queries host internals safely without requiring root or administrator elevation: operating system release, kernel version, CPU topology, RAM utilization, and storage partitions. If any metric is restricted, it gracefully reports 'Unavailable' rather than failing."*

---

### Step 3: Switch to Demo Mode (Windows / Linux)
- **Action**: In the top mode selector dropdown, choose **`DEMO — WINDOWS`**. Note the orange warning banner that appears.
- **What to say**:
  > *"To allow cross-platform demonstrations in any classroom or evaluation environment regardless of host OS, CSSA includes realistic simulated demo datasets for Windows 11, Ubuntu Linux, and macOS."*

---

### Step 4: Run the Security Audit
- **Action**: Click **🏠 Dashboard** in the sidebar, then click the red **🚀 RUN SECURITY AUDIT** button.
- **What to say**:
  > *"When we click Run Security Audit, the audit controller spins up a background worker in a separate QThread. This keeps the GUI silky smooth while rules, ports, permissions, and network packets are evaluated."*

---

### Step 5: Explain the Security Score (69/100)
- **Action**: Point to the circular score gauge (**69 / Needs Improvement**) and the category breakdown bars.
- **What to say**:
  > *"Notice the Windows system scored 69 out of 100. Our risk engine is completely explainable: it starts at 100, assigns calibrated penalties for Critical, High, and Medium findings, and enforces a 12-point cap per category so one noisy category cannot zero out the entire score."*

---

### Step 6: Review Findings & Evidence
- **Action**: Click on **🔍 Findings** in the sidebar. Select a finding (e.g., `Firewall is disabled` or `Exposed listening ports`).
- **What to say**:
  > *"Every finding provides full defensive context: rule ID, severity, technical evidence, rationale explaining the attack vector, and exact manual remediation commands. CSSA is strictly defensive: it advises the user, but never alters system settings automatically."*

---

### Step 7: Wireshark Packet Capture & Network Threat Analysis ⭐ (KEY HIGHLIGHT)
- **Action**: Click on **🦈 Packet Capture** in the sidebar.
- **What to say**:
  > *"Here is one of CSSA's most powerful capabilities: integrated network packet inspection and threat analysis. CSSA integrates with Wireshark via `tshark` for live captures, but also features a pure-Python PCAP and PCAPNG parser written from scratch with zero external C-dependencies."*
- **Action**:
  1. Show the status badge: e.g. `🦈 Wireshark Active` or `⚠️ Wireshark CLI Not Found (PCAP File Mode)`.
  2. Point out the auto-detected physical interface (Wi-Fi / Ethernet).
  3. Click **📂 Open PCAP / PCAPNG** and choose `fixtures/threat_sample.pcap`.
- **What to say**:
  > *"When we inspect this packet stream, our threat detector identifies 7 critical network vulnerabilities:
  > 1. Cleartext HTTP Basic Authentication header transmitting base64 credentials.
  > 2. Unencrypted FTP USER and PASS credentials in transit.
  > 3. Legacy Telnet traffic on port 23.
  > 4. Deprecated TLS 1.0 handshake negotiated over port 443.
  > 5. Link-Local Multicast Name Resolution (LLMNR) on UDP 5355, which exposes the system to rogue responder credential relay attacks."*
- **Action**: Click on a threat row in the table to display the evidence and decoded packet headers in the bottom drawer.

---

### Step 8: Switch to Linux Mode
- **Action**: In the top mode selector, choose **`DEMO — LINUX`** and click **🚀 RUN SECURITY AUDIT**.
- **What to say**:
  > *"Now we switch seamlessly to an Ubuntu Linux server audit. The score is 79/100 (Good), evaluating Linux-specific security controls: UFW/iptables status, world-writable files, SUID binaries, and SSH `PermitRootLogin`."*

---

### Step 9: Create a Security Baseline & Detect Drift
- **Action**:
  1. Click on **📋 Baseline** in the sidebar.
  2. Click **Create Baseline from Current** and name it `Ubuntu-Golden-State`.
  3. Explain the tracked components: listening sockets, administrator accounts, auto-start services, and firewall status.
- **What to say**:
  > *"A cornerstone of defensive auditing is baselining. We capture a trusted snapshot of system posture. When a future audit runs, CSSA performs a structural diff to detect configuration drift."*
- **Action**: Select the baseline and click **Compare with Current Audit**. Point out the diff view showing `+ Added`, `- Removed`, and `! Changed`.

---

### Step 10: Generate and Inspect the Executive Report
- **Action**: Click on **📄 Reports** in the sidebar, select **HTML Report**, and click **Export Report**.
- **What to say**:
  > *"CSSA compiles the findings into a standalone, styled executive HTML report with an executive summary, score cards, packet capture threats, baseline drift, and audit limitations."*
- **Action**: Open the exported `.html` file in a browser.

---

## 🎯 Evaluator & Viva Defense Q&A

### Q1: What makes CSSA different from simply running PowerShell or shell scripts?
> **Answer**: *"Scripts produce unstructured console output tied to a specific OS. CSSA uses the Adapter Pattern: raw Windows CIM/netsh/Registry and Linux `/proc`/systemctl output are converted into strongly-typed Python dataclasses. This allows a single rule engine, scoring algorithm, SQLite database, and UI to audit both operating systems identically."*

### Q2: How does the Wireshark packet capture feature work if Wireshark is not installed?
> **Answer**: *"CSSA uses a multi-tier strategy. If `tshark` is installed, it can capture live network packets. However, if Wireshark is not installed or the user lacks packet capture permissions, CSSA uses a built-in pure-Python PCAP/PCAPNG binary parser (`core/pcap_parser.py`) with zero C-dependencies. Users can load any capture file, and if no capture is available, the check cleanly reports `UNAVAILABLE` without crashing or imposing false penalties."*

### Q3: How is the security score calculated? Can one bad category ruin the entire score?
> **Answer**: *"The score starts at 100. Deductions are calibrated: Critical = 8 pts, High = 4 pts, Medium = 2 pts, Low = 1 pt. Crucially, each category has a maximum penalty cap of 12 points (`MAX_CATEGORY_PENALTY = 12`). This prevents one noisy category (e.g. multiple world-writable temp files) from zeroing out the entire audit score."*

### Q4: Why is CSSA strictly read-only?
> **Answer**: *"In enterprise security and academic host auditing, automated modification carries severe risk of bricking production services or introducing availability outages. CSSA adheres to the defensive auditing principle: it identifies weaknesses, presents evidence, and provides actionable remediation guidance for authorized administrators to execute manually."*
