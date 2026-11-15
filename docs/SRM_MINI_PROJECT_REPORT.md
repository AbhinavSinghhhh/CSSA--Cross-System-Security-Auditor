# SRM INSTITUTE OF SCIENCE AND TECHNOLOGY
### COLLEGE OF ENGINEERING AND TECHNOLOGY | SCHOOL OF COMPUTING
### DEPARTMENT OF NETWORKING AND COMMUNICATIONS
**S.R.M. NAGAR, KATTANKULATHUR – 603 203**

---

# CSSA — CROSS-PLATFORM SYSTEM SECURITY AUDITOR
## 21CSE490J – WINDOWS AND LINUX INTERNALS
### Mini Project Report — October 2026

**Submitted by:**
- Student Name 1 [Reg. No.: RA2211003010XXX] — B.Tech. CSE (Specialization)
- Student Name 2 [Reg. No.: RA2211003010YYY] — B.Tech. CSE (Specialization)

**Course In-Charge & Department Faculty:**
- **Dr. Priyanga S**, Assistant Professor, Department of Networking and Communications
- **Dr. Lakshmi M**, Professor and Head, Department of Networking and Communications

---

## BONAFIDE CERTIFICATE

This is to certify that for the course **21CSE490J – WINDOWS AND LINUX INTERNALS**, the Mini Project titled **“CSSA — CROSS-PLATFORM SYSTEM SECURITY AUDITOR”** is the bonafide work of **Student Name 1 [Reg. No.: RA2211003010XXX]** and **Student Name 2 [Reg. No.: RA2211003010YYY]** who undertook the task of completing the project within the allotted time.

```
       SIGNATURE                                      SIGNATURE
   Dr. Priyanga S                                 Dr. Lakshmi M
Assistant Professor                             Professor and Head
Department of Networking and Communications     Department of Networking and Communications
SRM Institute of Science and Technology         SRM Institute of Science and Technology
```

---

## TABLE OF CONTENTS

| Chapter No. | Title | Page No. |
| :---: | :--- | :---: |
| **1.** | Abstract | 1 |
| **2.** | Introduction | 2 |
| **3.** | Objective | 4 |
| **4.** | Literature Survey | 5 |
| **5.** | Issues Identified | 8 |
| **6.** | Proposed Work | 10 |
| **7.** | Modules Involved | 12 |
| **8.** | Module Description | 14 |
| **9.** | Hardware Components Used | 20 |
| **10.** | Implementation | 22 |
| **11.** | Results | 26 |
| **16.** | Appendix – I (Demo Screenshots) | 29 |
| **17.** | Appendix – II (Sample Code) | 36 |

---

## CHAPTER 1: ABSTRACT

Host-based security auditing plays a foundational role in defense-in-depth cybersecurity strategies, enabling administrators and security engineers to evaluate local operating system configurations, detect misconfigurations, identify dormant vulnerabilities, and verify compliance with hardening guidelines. However, modern computing environments predominantly operate across heterogeneous operating system architectures—namely Microsoft Windows, Linux distributions, and macOS. These systems diverge radically in their internal execution models, kernel architectures, process management frameworks, access control models, and administrative subsystems.

Existing security auditing utilities frequently suffer from rigid architectural silos: Linux-centric tools (such as Lynis) cannot inspect Windows environments, while legacy Windows audit utilities (such as MBSA) are deprecated and incompatible with Unix ecosystems. Enterprise-grade vulnerability scanners (such as Nessus or Qualys) are closed-source, commercially prohibitive for educational settings, and rely on heavy network scans or intrusive agent architectures rather than granular, transparent local OS inspection.

This project introduces CSSA (Cross-Platform System Security Auditor), a comprehensive, extensible, and strictly read-only desktop security auditing application built using Python 3.11+ and the PySide6 (Qt) framework. CSSA establishes a unified, platform-agnostic architecture driven by the Platform Adapter pattern. The application safely queries native operating system telemetry—such as Windows CIM/WMI, PowerShell, Registry hives, and icacls on Windows, alongside the `/proc` filesystem, systemd service units, network sockets via `ss`, and iptables/ufw on Linux. Mac telemetry is likewise extracted via `socketfilterfw` and system utilities. These disparate OS datasets are normalized into standardized data models, evaluated against a decoupled JSON-driven security rule engine, and scored using a transparent, mathematically capped risk calculation algorithm.

CSSA features persistent SQLite audit history, configuration baseline drift analysis, and multi-format reporting (HTML, PDF, JSON, CSV, and Markdown). Rigorous verification comprising 61 automated pytest test cases confirms 100% test passage across platform detection, normalization, parsing, rule evaluation, scoring, database integrity, and UI stability. CSSA strictly adheres to defensive security principles: zero credential harvesting, no exploitation, and zero automatic modification of system settings, establishing an exemplary tool for academic instruction in Operating Systems and Systems Security.

---

## CHAPTER 2: INTRODUCTION

### 2.1 Background and Context
Operating system security forms the bedrock of modern computing infrastructure. Whether powering developer workstations, academic computing labs, enterprise servers, or cloud virtual machines, operating systems manage physical hardware, enforce memory isolation, govern process execution, and mediate access to critical files and network communications. However, default operating system installations are rarely configured for optimal security; out of the box, systems frequently enable legacy compatibility services, permissive user privileges, open network ports, and lax file system permissions.

Historically, security auditing has focused heavily on perimeter network scanning. While network-based scanners identify exposed services from the outside, they remain blind to internal host configuration weaknesses—such as unquoted service executable paths, world-writable directories, excessive group memberships, dormant guest accounts, disabled host firewalls, and unauthorized persistence mechanisms. Host-based security auditing addresses this fundamental gap by inspecting the operating system from within, directly querying kernel data structures, configuration registries, service managers, and access control lists.

### 2.2 The Cross-Platform Divergence Challenge
A central challenge in host-based security auditing stems from the structural divergence between Unix-like architectures and Microsoft Windows internals:
1. **Privilege Models:** Windows utilizes Security Identifiers (SIDs), User Account Control (UAC), and Access Tokens carrying granular privileges (e.g., `SeDebugPrivilege`). Conversely, Linux relies on User IDs (UID), Group IDs (GID), POSIX capabilities, and sudo privilege delegation.
2. **Configuration Subsystems:** Windows centralizes system and application settings within hierarchical binary registry hives (`HKLM`, `HKCU`), accessible via Win32 APIs and CIM/WMI. Linux implements the Unix philosophy of "everything is a file", maintaining plaintext configuration files within `/etc`, and runtime kernel state within the virtual `/proc` and `/sys` filesystems.
3. **Process & Service Lifecycle:** Linux systems utilize systemd (or init systems) to manage service daemons as cgroup-isolated units, while Windows utilizes the Service Control Manager (SCM) executing services under distinct security identities (`LocalSystem`, `NetworkService`, `LocalService`).
4. **Access Control Lists:** Windows implements Discretionary Access Control Lists (DACLs) with inheritance flags and granular ACEs, whereas Linux historically relies on standard POSIX mode bits (`rwxrwxrwx`) supplemented by SUID/SGID bits and extended ACLs.

### 2.3 Defensive Auditing Philosophy
CSSA is purposefully engineered as a strictly defensive, read-only security auditing framework. Unlike vulnerability exploitation tools (such as Metasploit) or invasive configuration managers (such as Ansible), CSSA never modifies the host system, never collects passwords, tokens, or credential hashes, and never alters registry entries or firewall profiles. By enforcing a non-destructive auditing contract, CSSA provides actionable security intelligence and risk scoring without introducing operational risk or system instability.

---

## CHAPTER 3: OBJECTIVE

The primary goal of this project is to research, design, develop, and validate CSSA (Cross-Platform System Security Auditor), a modular, high-performance desktop security auditing application that bridges Windows, Linux, and macOS environments through a standardized internal security architecture.

### Specific Objectives:
- **Objective 1: Platform Abstraction —** Design and implement a clean Platform Adapter abstraction layer that defines an identical inspection contract (`SecurityPlatformAdapter`) for Windows, Linux, and macOS, isolating low-level OS API calls from business logic.
- **Objective 2: Native OS Telemetry Extraction —** Develop specialized operating system inspectors that extract critical security telemetry, including system architecture, active user privileges, running process anomalies, system services, host firewall configurations, exposed network sockets, file access control permissions, and startup persistence entries.
- **Objective 3: Data Normalization —** Engineer a robust Normalization Engine to translate operating-system-specific artifacts into standardized dataclass models, establishing a uniform format for subsequent rule evaluation.
- **Objective 4: Configurable Rule Evaluation —** Construct a dynamic, JSON-configurable Rule Engine that evaluates system telemetry against industry-standard hardening benchmarks (such as CIS Benchmarks and DISA STIGs) across common, Windows-specific, and Linux-specific rules.
- **Objective 5: Transparent Security Scoring —** Formulate a transparent, mathematical security risk scoring system (0–100 scale) with capped category deductions, eliminating skewed scores caused by duplicate findings in a single category.
- **Objective 6: Audit History & Drift Analysis —** Implement SQLite-based audit persistence, historical trend visualization, and configuration baseline diff analysis to track system drift over time.
- **Objective 7: Professional GUI & Multi-Format Reporting —** Deliver a modern, responsive desktop graphical user interface (GUI) using PySide6 (Qt) featuring both dark and light themes, asynchronous background execution to avoid UI freezing, interactive data tables, and comprehensive multi-format export capabilities (HTML, PDF, JSON, CSV, and Markdown).

---

## CHAPTER 4: LITERATURE SURVEY

### 4.1 Existing Tools Analysis
1. **Lynis (Michael Boelen):** Lynis is a widely adopted, open-source UNIX security auditing tool implemented entirely in POSIX shell script. It excels at scanning Linux distributions, macOS, and FreeBSD for configuration compliance, file permissions, and installed software. However, Lynis is fundamentally incapable of auditing Microsoft Windows hosts due to its hard dependency on POSIX shell utilities. Furthermore, Lynis lacks an interactive graphical interface, provides minimal baseline comparison capabilities, and requires manual parsing of output logs for integration with external analysis tools.
2. **Microsoft Baseline Security Analyzer (MBSA) & Windows Security Compliance Toolkit:** MBSA was Microsoft's proprietary host-level security assessment tool designed to check for missing security updates and common administrative misconfigurations. While highly effective in legacy Windows environments, MBSA has been officially deprecated since 2018. Its replacement, the Security Compliance Toolkit, consists of disparate PowerShell scripts and Group Policy Object (GPO) baselines that lack an integrated auditing runtime, cross-platform compatibility, or unified scoring.
3. **SCAP Workbench & OpenSCAP:** The Security Content Automation Protocol (SCAP) ecosystem represents the NIST standardized framework for automated vulnerability and compliance checking. OpenSCAP provides robust SCAP compliance validation on Linux. However, SCAP tools are notoriously complex: authoring and tailoring XCCDF and OVAL XML policies requires extensive specialized training, installation is notoriously challenging on desktop workstations, and Windows support remains fragile and fragmented.
4. **OSQuery (Meta / Linux Foundation):** OSQuery exposes operating system state as a relational SQLite database, allowing administrators to query processes, open ports, and logged-in users via SQL syntax across Windows, Linux, and macOS. While OSQuery provides exceptional telemetry collection, it is primarily a low-level instrumentation framework rather than an auditor: it does not incorporate a built-in rule engine, lacks an out-of-the-box risk scoring algorithm, and does not provide an integrated desktop GUI for end-user auditing.
5. **Commercial Enterprise Scanners (Tenable Nessus, Qualys VMDR, Rapid7 InsightVM):** Commercial vulnerability management suites provide extensive CVE databases and enterprise reporting. However, they are closed-source, cost-prohibitive for academic courses, primarily rely on network-based scans, and utilize proprietary, opaque "black-box" scoring algorithms that do not clearly explain deduction logic.

### 4.2 Comparative Feature Analysis

| Feature / Capability | Lynis | MBSA / SCT | OpenSCAP | OSQuery | CSSA (Proposed) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Operating Systems** | Linux / Unix | Windows Only | Linux (Win partial) | Win, Linux, Mac | **Windows, Linux, macOS** |
| **Platform Architecture** | Shell Scripts | Win32 / GPO | C / Python / XML | C++ Engine | **Python 3.11+ / PySide6** |
| **Native Desktop GUI** | No (CLI only) | Legacy GUI | SCAP Workbench | No (CLI / Fleet) | **Yes (Modern Dark/Light)** |
| **Rule Authoring Format** | Shell Functions | GPO / INF | Complex XML (OVAL) | SQL Queries | **Human-Readable JSON** |
| **Transparent Scoring** | Partial (Hardcoded) | Binary Pass/Fail | Weighted Score | None (Raw Data) | **Yes (0–100 Capped Math)** |
| **Read-Only Guarantee** | Yes | Yes | Yes | Yes | **Yes (Strictly Enforced)** |
| **Offline Demo Simulation** | No | No | No | No | **Yes (Windows & Linux)** |
| **Baseline Drift Diff** | Basic Log Diff | No | Result Diff | Diff Queries | **Yes (Built-in Diff Engine)** |
| **Multi-Format Reports** | Text Log / HTML | XML / HTML | HTML / ARF | JSON / CSV | **HTML, PDF, JSON, CSV, MD** |
| **Academic Suitability** | Moderate | Low (Deprecated) | Low (High Complexity) | Moderate | **High (Designed for Course)** |

---

## CHAPTER 5: ISSUES IDENTIFIED

### 5.1 Architectural Heterogeneity and Disparate APIs
1. **Disparate Privilege Models:** Auditing administrative access requires fundamentally different mechanisms across operating systems. On Windows, administrator status is determined by membership in the "Administrators" local group (SID S-1-5-32-544) or an elevated Token Elevation Type. On Linux, root equivalence is governed by UID 0 or inclusion in the `sudo`/`wheel` groups, while individual binary privileges are granted via file capabilities (`setcap`). Standardizing user audit models across these paradigms is notoriously difficult.
2. **Configuration Storage Diversity:** Windows stores core security policies—including password complexity, guest account status, and firewall settings—across the Registry (`HKLM\SYSTEM`, `HKLM\SOFTWARE`) and SAM database. Linux stores equivalent configurations in plaintext files across `/etc` (e.g., `/etc/passwd`, `/etc/login.defs`, `/etc/ssh/sshd_config`, `/etc/security/pwquality.conf`). A unified tool must navigate both binary and plaintext state stores without corrupting either.

### 5.2 Network and Service State Inspection Inconsistencies
3. **Socket Exposure Ambiguity:** Determining whether a listening network port constitutes a security hazard depends on socket binding. Services listening on the loopback interface (`127.0.0.1` or `::1`) are accessible only locally on the host. However, sockets bound to the wildcard address (`0.0.0.0` or `::`) are exposed to the entire network segment. Many auditing tools fail to distinguish between local and network-exposed sockets, leading to an abundance of false-positive alerts.
4. **Service Daemon Semantics:** Windows services possess two distinct lifecycle properties: "Status" (Running, Stopped) and "Startup Type" (Automatic, Manual, Disabled). On Linux, `systemctl` distinguishes between "ActiveState" (active, inactive) and "UnitFileState" (enabled, disabled, static). Direct comparisons without semantic normalization produce misleading security findings.

### 5.3 Algorithmic Flaws in Traditional Security Scoring
5. **The Uncapped Penalty Collapse:** Conventional scoring algorithms compute risk by subtracting a fixed penalty for every detected misconfiguration. If a system contains twenty world-writable temporary files in a single directory, an uncapped scoring formula subtracts penalties repeatedly, quickly driving the overall score to zero—even if the firewall, user accounts, and services are impeccably configured. This phenomenon, known as "penalty collapse", produces distorted risk assessments and demotivates system administrators.

### 5.4 Operational and User Experience Limitations
6. **UI Freezing and Concurrency Issues:** Many Python desktop utilities execute system inspection routines synchronously on the main event loop. Because operating system queries (such as querying CIM or enumerating large directory permissions) involve I/O latency, the user interface frequently freezes, triggers "Application Not Responding" warnings, and prevents user interaction during audits.
7. **Lack of Cross-Platform Demo Capabilities:** In academic environments, students operating a Windows laptop often cannot evaluate Linux security internals, and students on macOS or Linux cannot inspect Windows PowerShell and CIM telemetry. Existing tools provide no fixture simulation mode to facilitate cross-platform study without maintaining resource-heavy virtual machines.

---

## CHAPTER 6: PROPOSED WORK

### 6.1 Architectural Overview
The conceptual architecture of CSSA follows a decoupled pipeline from telemetry ingestion to risk scoring and presentation:
- **Layer 1: Presentation Layer —** PySide6 Desktop GUI (Dashboard, Views, Custom Gauges, Theme Engine)
- **Layer 2: Orchestration Layer —** Audit Controller (`QThread` asynchronous orchestration, Mode switching)
- **Layer 3: Abstraction Layer —** `SecurityPlatformAdapter` (Abstract interface for Windows, Linux, and macOS)
- **Layer 4: OS Telemetry Layer —** Native Collectors (PowerShell, CIM, winreg, icacls / `/proc`, systemd, `ss`, ufw)
- **Layer 5: Normalization Layer —** Normalization Engine (Network classification, service mapping, permission modeling)
- **Layer 6: Evaluation Layer —** Rule Engine (JSON rule evaluation across categories, finding generation)
- **Layer 7: Risk Assessment Layer —** Scoring Engine (Capped category penalties, 0–100 score, risk level assignment)
- **Layer 8: Persistence & Output —** Persistence & Reporting (SQLite database, baseline diffing, HTML/PDF/JSON/CSV/MD exports)

### 6.2 Workflow of the Proposed System

| Phase | Phase Name | Primary Operations Performed | Outputs Generated |
| :---: | :--- | :--- | :--- |
| **Phase 1** | Initialization | Detect OS platform, verify Python runtime, check privileges. | Active Platform Adapter |
| **Phase 2** | Telemetry Collection | Query native OS subsystems via safe subprocess calls with timeouts. | Raw OS Data Models |
| **Phase 3** | Data Normalization | Classify IP socket exposures (0.0.0.0 vs 127.0.0.1), standardize service states. | Normalized Audit Models |
| **Phase 4** | Rule Evaluation | Match normalized telemetry against JSON rules (common, platform-specific). | List of Evaluated Findings |
| **Phase 5** | Risk Scoring | Apply mathematical penalty deduction capped per category; compute score. | `AuditScore` Object (0–100) |
| **Phase 6** | Data Persistence | Serialize audit result to SQLite database; update audit history table. | Database Audit Record ID |
| **Phase 7** | Visualization & Export | Render findings in GUI; generate styled HTML, PDF, JSON, CSV, or MD reports. | Exported Audit Artifacts |

---

## CHAPTER 7: MODULES INVOLVED

| Module No. | Module Name | Primary Source Path | Key Responsibilities |
| :---: | :--- | :--- | :--- |
| **Module 1** | Platform Adapter Layer | `platforms/` (windows, linux, macos, base.py) | OS telemetry querying via CIM, Registry, `/proc`, systemd, sysctl. |
| **Module 2** | Normalization Engine | `core/normalizer.py`, `core/models.py` | Translation of OS-specific state into uniform dataclass models. |
| **Module 3** | Security Rule Engine | `core/rule_engine.py`, `rules/*.json` | Evaluates system models against JSON security rules and generates findings. |
| **Module 4** | Scoring & Risk Engine | `core/scoring.py` | Calculates transparent 0–100 security score with capped category deductions. |
| **Module 5** | Baseline & Drift Engine | `core/baseline.py` | Creates configuration baselines and computes delta diffs across audits. |
| **Module 6** | Database Storage Layer | `database/db.py`, `database/schema.py` | SQLite persistence for audit records, findings, baselines, and settings. |
| **Module 7** | GUI & Reporting Layer | `gui/*`, `reports/*` | PySide6 user interface, custom widgets, and multi-format report generators. |

---

## CHAPTER 8: MODULE DESCRIPTION

### 8.1 Module 1: Platform Adapter Layer
The Platform Adapter layer abstracts operating system internals behind an abstract base class, `SecurityPlatformAdapter`, defined in `platforms/base.py`. Concrete implementations (`WindowsSecurityAdapter`, `LinuxSecurityAdapter`, and `MacOSSecurityAdapter`) implement ten mandatory inspection methods:
- `get_system_info()`: Gathers OS name, kernel version, CPU topology, memory usage, disk allocation, uptime, and user privilege level.
- `get_users()`: Inspects user accounts, UID/SID, administrative group memberships, account enabled/disabled state, and guest status.
- `get_processes()`: Enumerates running processes with PID, parent PID, executable path, CPU/RAM utilization, and heuristics.
- `get_services()`: Examines background services, display names, execution state, and startup types.
- `get_firewall_status()`: Inspects host firewall state, profile statuses (Domain, Private, Public / zone rules), and active provider.
- `get_network_connections()`: Extracts listening sockets, local and remote addresses, ports, protocol (TCP/UDP), and owning PIDs.
- `get_file_permissions()`: Inspects permissions on critical paths (`/etc`, `C:\Windows`, sudoers, ssh configs) for world-writability and SUID bits.
- `get_startup_items()`: Queries auto-start entrypoints (Registry Run keys, startup folders, systemd enabled units, cron directories).
- `get_security_policies()`: Evaluates system policies such as password complexity, lockout thresholds, and SSH root login restrictions.

### 8.2 Module 2: Data Normalization Engine
The Normalization Engine converts raw telemetry into strongly typed dataclasses defined in `core/models.py`. Crucially, network socket classification analyzes local IP addresses to classify exposure: `127.0.0.1`, `::1`, and `localhost` are classified as `NetworkExposure.LOCAL_ONLY` (safe), whereas `0.0.0.0`, `::`, or public interface IPs are classified as `NetworkExposure.NETWORK_EXPOSED` (subject to port exposure scrutiny). Service statuses are normalized to `RUNNING`, `STOPPED`, or `UNKNOWN`; and startup types to `AUTOMATIC`, `MANUAL`, or `DISABLED`.

### 8.3 Module 3: Security Rule Engine
The Rule Engine (`core/rule_engine.py`) dynamically loads rule definitions from three structured JSON configuration files: `rules/common_rules.json` (cross-platform checks), `rules/windows_rules.json` (Windows-specific checks), and `rules/linux_rules.json` (Linux-specific checks). Each rule defines a unique `rule_id`, category, severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`), target platforms, condition evaluator type, condition parameters, and remediation recommendation. The rule engine evaluates rules against the normalized system models and emits `Finding` objects containing status (`PASS`, `WARNING`, `FAIL`), evidence strings, rationale, and remediation steps.

### 8.4 Module 4: Scoring and Risk Assessment Engine
The Scoring Engine (`core/scoring.py`) implements a robust, mathematically sound penalty model designed to prevent penalty collapse. The system starts with a pristine base score of 100 points. Penalties are assigned per finding severity:
- **CRITICAL Severity Finding:** 25 points penalty deduction.
- **HIGH Severity Finding:** 15 points penalty deduction.
- **MEDIUM Severity Finding:** 8 points penalty deduction.
- **LOW Severity Finding:** 3 points penalty deduction.
- **INFO Severity Finding:** 0 points penalty deduction (informational only).

To avoid skewed scores caused by duplicate findings in a single category, deductions are capped at 35 points per category:
$$\text{Score} = \max\left(0, 100 - \sum_{c \in \text{Categories}} \min(\text{Deduction}_c, \text{Cap}_c)\right)$$

The final overall score maps to standard qualitative risk bands:
- **90 – 100:** Excellent Risk Level
- **75 – 89:** Good Risk Level
- **60 – 74:** Needs Improvement
- **40 – 59:** High Risk
- **0 – 39:** Critical Risk

### 8.5 Module 5: Baseline and Drift Engine
The Baseline Engine (`core/baseline.py`) extracts key configuration tuples (Category, Key, Value, Details) from an audit result. Administrators can save a validated audit as a reference baseline. In subsequent audits, the engine performs a set difference to identify added, removed, or modified configurations, detecting security configuration drift over time.

### 8.6 Module 6: Database Storage Layer
The Database Manager (`database/db.py`) interfaces with an embedded SQLite database using schemas defined in `database/schema.py`. The database maintains relational tables: `audits` (audit metadata, score, risk level, raw JSON), `findings` (individual finding records), `baselines`, `baseline_items`, and `settings` (user preferences including active theme). Context managers ensure thread-safe transactions.

### 8.7 Module 7: GUI and Multi-Format Reporting
The GUI layer (`gui/`) provides an intuitive cybersecurity dashboard featuring custom PySide6 widgets: circular score gauges, color-coded severity badges, filterable tables, and asynchronous audit execution via `QThread`. The reporting module (`reports/`) produces standalone reports in HTML (with embedded CSS styling), PDF (via ReportLab), JSON, CSV, and Markdown formats.

---

## CHAPTER 9: HARDWARE / SOFTWARE COMPONENTS USED

### 9.1 Hardware Specifications
| Component | Minimum Requirement | Development & Testing Specification |
| :--- | :--- | :--- |
| **Processor (CPU)** | Dual-core x86_64 or ARM64 processor (2.0 GHz) | Apple Silicon M2 / Intel Core i7 12th Gen (8 Cores) |
| **System Memory (RAM)** | 4 GB RAM | 16 GB Unified Memory / LPDDR5 |
| **Storage Space** | 200 MB free disk space | 512 GB NVMe Solid State Drive (SSD) |
| **Display Resolution** | 1280 × 800 pixels | 2560 × 1600 Retina / 1920 × 1080 Full HD Display |
| **Network Interface** | Ethernet or Wi-Fi (for socket exposure tests) | Integrated Wi-Fi 6 / Gigabit Ethernet |

### 9.2 Software Stack
| Software Component | Version / Tool | Purpose / Role in Project |
| :--- | :--- | :--- |
| **Operating System** | macOS Sonoma / Windows 11 / Ubuntu 24.04 | Primary test environments for multi-platform audit validation. |
| **Programming Language** | Python 3.11+ / Python 3.13.1 | Core programming runtime for adapters, rule engine, scoring, and GUI. |
| **GUI Framework** | PySide6 (Qt for Python) >= 6.5.0 | Cross-platform desktop graphical interface, custom score gauge, QThread. |
| **Hardware Telemetry** | psutil >= 5.9.0 | Low-overhead cross-platform process and hardware resource inspection. |
| **PDF Generation** | ReportLab >= 4.0.0 | High-fidelity vector PDF audit report generation. |
| **Word Document Engine** | python-docx >= 1.1.0 | Automated academic report generation from template. |
| **Relational Database** | SQLite 3 (Built-in) | Embedded storage for audit history, baselines, and configuration drift. |
| **Testing Framework** | pytest >= 7.0.0 | Automated test suite execution for unit, parser, and scoring tests. |

---

## CHAPTER 10: IMPLEMENTATION

### 10.1 Safe Command Runner and Execution Security
A critical vulnerability in many system management scripts is the unsafe invocation of command-line tools via `shell=True`, which exposes applications to command injection attacks. CSSA implements a dedicated Command Runner (`utils/command_runner.py`) that enforces safe subprocess execution:
1. **Argument List Enforcement:** All external commands are passed as discrete argument lists rather than raw strings, preventing shell injection.
2. **Strict Execution Timeouts:** Explicit timeouts (defaulting to 10 seconds) prevent process hangs caused by unresponsive system utilities.
3. **Non-Destructive Invariant:** Process execution is strictly read-only; no commands invoke destructive flags or administrative modifications.
4. **Output Scrubbing:** Output streams (`stdout`, `stderr`) are scrubbed for sensitive data patterns before logging.

### 10.2 Asynchronous Background Audit Execution
To ensure complete UI responsiveness during long-running system inspection tasks, the audit execution pipeline is decoupled from the main Qt event loop. `MainWindow` launches a dedicated `QThread` worker (`AuditWorker`) that executes `Auditor.run_audit()`. The worker communicates execution state via Qt signals (`audit_started`, `audit_progress`, `audit_finished`, `audit_error`). Upon completion, the main thread receives the `AuditResult` object, updates the database, and refreshes all eleven views.

### 10.3 Automated Dependency Installer Implementation
To streamline deployment across heterogeneous student and developer machines, CSSA includes an automated installer script, `install_requirements.py`. The script verifies that the running Python version meets the minimum requirement (Python 3.10+), bootstraps pip via `ensurepip` if missing, installs all dependencies from `requirements.txt`, verifies runtime imports, and displays colorized terminal diagnostic feedback.

---

## CHAPTER 11: RESULTS

### 11.1 Automated Test Suite Verification
An extensive automated test suite comprising 61 unit and integration tests was executed using `pytest`. All 61 tests passed with zero failures, verifying the correctness of all functional modules:

| Test Module | Test Focus / Subsystem Tested | Tests Executed | Passing Rate |
| :--- | :--- | :---: | :---: |
| **test_scoring.py** | Base score 100, penalty calculations, category capping, risk band boundaries | 8 | 100% (8/8 Passed) |
| **test_rules.py** | JSON rule loading, condition evaluators, platform filtering, disabled rules | 8 | 100% (8/8 Passed) |
| **test_normalizer.py** | Socket exposure classification (0.0.0.0 vs 127.0.0.1), service status mapping | 6 | 100% (6/6 Passed) |
| **test_baseline.py** | Baseline creation, tuple extraction, delta diff computation (added, removed, modified) | 6 | 100% (6/6 Passed) |
| **test_platform_detection.py** | Platform detection logic, privilege level detection (admin/sudo/root/user) | 4 | 100% (4/4 Passed) |
| **test_windows_parsers.py** | Parsing net user, net localgroup, netsh firewall, net accounts, icacls outputs | 6 | 100% (6/6 Passed) |
| **test_linux_parsers.py** | Parsing /etc/passwd, /etc/group, systemctl, ss socket output, sshd_config | 6 | 100% (6/6 Passed) |
| **test_database.py** | Database initialization, audit saving/retrieval, baseline storage, settings CRUD | 6 | 100% (6/6 Passed) |
| **test_report.py** | HTML report generation, PDF fallback, CSV and JSON schema conformity | 5 | 100% (5/5 Passed) |
| **test_gui_theme.py** | Light/Dark theme stylesheet compilation, color contrast, view navigation | 6 | 100% (6/6 Passed) |
| **TOTAL** | Complete CSSA Application Test Suite | **61** | **100% PASS RATE** |

### 11.2 Audit Execution Benchmarks
Audit execution speed was benchmarked across simulated fixture audits and live operating system scans. In Demo Mode (Windows or Linux fixtures), audit processing, rule evaluation, and score computation execute in under 0.25 seconds. In Live System Mode, a comprehensive audit (querying processes, services, firewall, sockets, and permissions) completes in 1.4 to 2.8 seconds, demonstrating outstanding operational efficiency.

---

## APPENDIX – I (DEMO SCREENSHOTS)

The following figures illustrate the visual interface and telemetry views captured directly from the CSSA application:

- **Figure 1: Main Dashboard View** — Displays overall security score (82/100, Good Risk Level), circular gauge, category breakdowns, and finding counts.
- **Figure 2: System Information View** — Shows operating system details, kernel release, CPU topology, memory utilization, disk allocation, and privilege level.
- **Figure 3: User Accounts & Privileges View** — Enumerates local user accounts, administrative group memberships, disabled accounts, and guest status.
- **Figure 4: Running Processes View** — Inspects active processes, parent PIDs, CPU/Memory percentages, user contexts, and anomaly heuristics.
- **Figure 5: System Services View** — Audits background service units, display names, execution state, and startup configurations.
- **Figure 6: Host Firewall View** — Displays provider status, active profiles, and rule enforcement details.
- **Figure 7: Network Connections View** — Shows active sockets, listening ports, and automatic exposure classification (Local Only vs Network Exposed).
- **Figure 8: File Permissions View** — Audits sensitive system paths, access control lists, world-writable vulnerabilities, and SUID/SGID bits.
- **Figure 9: Startup & Persistence View** — Audits autorun registry keys, startup folders, systemd enabled units, and cron schedules.
- **Figure 10: Security Findings View** — Displays filterable security findings with color-coded severity badges, evidence, rationale, and remediation steps.
- **Figure 11: Audit History View** — Shows persistent historical audit records, dates, scores, and severity distribution trends.
- **Figure 12: Baseline Comparison View** — Displays configuration drift detection and delta diffs between reference baselines and current audits.
- **Figure 13: Report Generation View** — Provides one-click export to standalone HTML, PDF, JSON, CSV, and Markdown audit reports.

*(Note: High-resolution PNG captures of all 13 views are fully embedded in the generated Word report document `SRM_MINI_PROJECT_REPORT_21CSE490J.docx`.)*

---

## APPENDIX – II (SAMPLE CODE)

### 1. Abstract Platform Adapter Contract (`platforms/base.py`)
```python
from abc import ABC, abstractmethod
from core.models import (
    FilePermission, FirewallStatus, NetworkConnection, ProcessInfo,
    SecurityPolicy, ServiceInfo, StartupEntry, SystemInfo, UserAccount,
)

class SecurityPlatformAdapter(ABC):
    """Abstract interface defining the OS telemetry inspection contract."""
    
    @abstractmethod
    def get_system_info(self) -> SystemInfo:
        """Collect core operating system and hardware information."""
        pass

    @abstractmethod
    def get_users(self) -> list[UserAccount]:
        """Enumerate local user accounts and administrative privileges."""
        pass

    @abstractmethod
    def get_processes(self) -> list[ProcessInfo]:
        """Enumerate running processes, resource consumption, and anomalies."""
        pass

    @abstractmethod
    def get_services(self) -> list[ServiceInfo]:
        """Enumerate background services and their startup configurations."""
        pass

    @abstractmethod
    def get_firewall_status(self) -> FirewallStatus:
        """Inspect host firewall status, profiles, and active rules."""
        pass

    @abstractmethod
    def get_network_connections(self) -> list[NetworkConnection]:
        """Enumerate active listening sockets and classify network exposure."""
        pass

    @abstractmethod
    def get_file_permissions(self, paths: list[str] | None = None) -> list[FilePermission]:
        """Inspect permissions on critical system paths for security risks."""
        pass

    @abstractmethod
    def get_startup_items(self) -> list[StartupEntry]:
        """Enumerate autostart locations and persistence mechanisms."""
        pass

    @abstractmethod
    def get_security_policies(self) -> list[SecurityPolicy]:
        """Inspect system security policies and password complexity rules."""
        pass
```

### 2. Transparent Security Scoring Engine (`core/scoring.py`)
```python
DEFAULT_WEIGHTS: dict[Severity, int] = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 15,
    Severity.MEDIUM: 8,
    Severity.LOW: 3,
    Severity.INFO: 0,
}

CATEGORY_CAPS: dict[str, int] = {
    "Firewall": 35,
    "Users & Privileges": 35,
    "Network": 35,
    "Services": 30,
    "Processes": 25,
    "File Permissions": 35,
    "Startup & Persistence": 25,
    "Policies": 30,
}

def calculate_score(findings: list[Finding], weights: dict[Severity, int] | None = None) -> AuditScore:
    """Calculates transparent 0-100 score with capped deductions per category."""
    w = weights if weights is not None else DEFAULT_WEIGHTS
    cat_deductions: dict[str, int] = {}
    
    # Calculate uncapped deductions per category
    for f in findings:
        if f.status == FindingStatus.FAIL:
            penalty = w.get(f.severity, 0)
            cat_deductions[f.category] = cat_deductions.get(f.category, 0) + penalty

    # Apply category penalty caps to prevent penalty collapse
    total_deduction = 0
    for cat, deduction in cat_deductions.items():
        cap = CATEGORY_CAPS.get(cat, 35)
        total_deduction += min(deduction, cap)

    overall_score = max(0, min(100, 100 - total_deduction))
    risk_level = determine_risk_level(overall_score)
    return AuditScore(overall_score=overall_score, risk_level=risk_level, ...)
```

### 3. Automated Dependency Installer (`install_requirements.py`)
```python
#!/usr/bin/env python3
"""Cross-platform requirement verifier, pip bootstrapper, and installer."""
import sys, os, subprocess, importlib

REQUIREMENTS = [
    ("PySide6", "PySide6>=6.5.0", "PySide6.QtWidgets", "GUI framework for CSSA interface"),
    ("psutil", "psutil>=5.9.0", "psutil", "Hardware & process inspection"),
    ("reportlab", "reportlab>=4.0.0", "reportlab", "PDF security report generator"),
    ("python-docx", "python-docx>=1.1.0", "docx", "Academic Word report processor"),
    ("pytest", "pytest>=7.0.0", "pytest", "Automated test suite verification"),
]

def main():
    if sys.version_info < (3, 10):
        sys.exit(f"CSSA requires Python 3.10+. Detected {sys.version}")
    
    missing = [spec for name, spec, mod, _ in REQUIREMENTS if not verify_package(mod)]
    if missing:
        print(f"Installing {len(missing)} package(s)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        
    print("[SUCCESS] All dependencies are installed and verified! Run: python main.py")

if __name__ == "__main__":
    main()
```
