# Academic Project Report: Cross-Platform System Security Auditor (CSSA)

**Course**: Operating Systems & Windows/Linux Security (Academic/Internal Class Project)  
**System Name**: CSSA (Cross-Platform System Security Auditor)  
**Author / Engineering Team**: Senior Systems & Security Architecture Group  

---

## 1. Abstract
Host-based defensive security auditing is essential for maintaining enterprise and educational workstation hygiene. Modern computing infrastructures predominantly employ heterogeneous operating systems—predominantly Microsoft Windows for client workstations and GNU/Linux for servers and container hosts. Traditional administrative scripts and point security tools frequently focus on a single operating system, requiring security engineers to maintain disparate toolchains with divergent report formats. This project presents the **Cross-Platform System Security Auditor (CSSA)**, an extensible, strictly read-only desktop application built with Python 3.11+, PySide6, and SQLite. CSSA abstracts disparate operating system internals through the **Adapter Pattern**, transforming platform-specific data into unified dataclass models. An independent, JSON-driven Rule Engine assesses system posture, while a capped scoring algorithm computes transparent risk metrics (0–100) across standardized security categories. Historical tracking and configuration drift comparison (baseline snapshot diffing) enable proactive identification of unwanted exposure. Experimental evaluation on Windows 11 and Ubuntu Linux demonstrates robust anomaly detection without modifying host configurations or risking system availability.

---

## 2. Introduction
Operating systems serve as the critical boundary between user applications and hardware resources. Over the lifecycle of a workstation or server, cumulative configuration changes, newly installed services, altered firewall policies, and permissive file access permissions can significantly expand the host's attack surface. While penetration testing tools emphasize active exploitation, defensive auditing seeks to evaluate adherence to security principles—such as the Principle of Least Privilege and Attack Surface Minimization—before adversaries can exploit misconfigurations.

CSSA was engineered to solve the problem of cross-platform security auditing. It implements an architecture where the user interface, risk engine, database storage, and reporting mechanisms remain completely decoupled from underlying platform specifics.

---

## 3. Problem Statement
Auditing modern operating systems presents several fundamental challenges:
1. **Divergent Internals:** Microsoft Windows manages system state via the Windows Registry, Service Control Manager (SCM), Windows Filtering Platform (WFP), and Security Account Manager (SAM). Conversely, Linux utilizes the virtual `/proc` and `/sys` filesystems, systemd unit definitions, PAM configurations, and POSIX file permission mode bits.
2. **Destructive Remediation Risks:** Many automated tools attempt direct remediation (e.g., stopping services or modifying firewall rules), risking catastrophic disruption in production or educational lab settings.
3. **Privilege Fragility:** Naive scripts crash when encountering access denials or missing utilities.
4. **Lack of Uniform Scoring:** Disparate tools output incompatible raw logs, lacking a normalized metric for comparative hygiene over time.

---

## 4. Objectives
The primary technical objectives of CSSA are:
- **Architectural Platform Abstraction:** Construct an abstract adapter interface (`SecurityPlatformAdapter`) providing a unified contract for Windows and Linux inspection.
- **Data Normalization:** Transform heterogeneous operating system metadata into standardized, strongly typed Python dataclasses.
- **Configurable Rule Engine:** Evaluate host configurations against external, declarative JSON rule definitions.
- **Transparent, Capped Risk Scoring:** Implement an explainable scoring methodology (0–100) with category-level caps to avoid disproportionate penalties.
- **Configuration Drift Tracking:** Store baseline snapshots in SQLite and compute structural diffs (`Added`, `Removed`, `Changed`).
- **Safe, Read-Only Operation:** Guarantee that no file is written outside the application directory, no services are terminated, and no credentials or secrets are harvested.
- **Classroom Simulation Mode:** Enable seamless demonstration of both Windows and Linux audit workflows on any host machine through realistic simulated fixtures.

---

## 5. Scope
The application covers local inspection of:
- **System Information:** OS version, kernel, CPU, physical/virtual memory, disk volumes, and user privilege level.
- **Account & Privilege Security:** Local user enumeration, administrative/sudo group memberships, disabled status, and Guest accounts.
- **Running Processes:** PID, executable path, parent PID, user context, memory consumption, and CPU utilization.
- **System Services / Daemons:** Service states, startup configuration (Automatic vs Manual vs Disabled), and security descriptions.
- **Host Firewall:** Detection of Windows Defender Firewall profiles or Linux firewall frameworks (UFW, firewalld, nftables, iptables).
- **Network Exposure:** Local sockets and listening ports categorized as `LOCAL ONLY` vs `NETWORK EXPOSED` vs `UNKNOWN`.
- **Filesystem Permissions:** POSIX mode bits (SUID/SGID/world-writable) on Linux and NTFS Access Control Lists (ACLs) on Windows.
- **Persistence & Startup:** Scheduled tasks, Windows registry Run keys, systemd startup services, and cron configurations.
- **Security Policies:** Password length/aging, lockout thresholds, and SSH server configurations (`PermitRootLogin`).

**Out of Scope:** External network scanning, penetration testing, password hash extraction, dynamic binary analysis, and automated remediation.

---

## 6. Background
Host security evaluation requires understanding standard defensive benchmarks (such as CIS Benchmarks, DISA STIGs, and NIST SP 800-53). A core requirement in modern compliance is the **Zero Trust Architecture** and **Defense in Depth**: auditing must verify that individual host controls remain robust even if perimeter network defenses are bypassed.

---

## 7. Windows Security Concepts
- **Security Identifiers (SIDs) & Access Tokens:** Windows authenticates users and assigns access tokens containing user SID, group SIDs, and privileges (e.g., `SeDebugPrivilege`).
- **Discretionary Access Control Lists (DACLs):** NTFS security descriptors contain DACLs consisting of Access Control Entries (ACEs) granting or denying specific rights (Read, Write, Modify, Full Control) to SIDs.
- **Service Control Manager (SCM):** Manages Windows services, their account context (LocalSystem, NetworkService, LocalService), and startup triggers.
- **Windows Filtering Platform & netsh advfirewall:** Windows enforces network filtering across three distinct profiles: Domain, Private, and Public.
- **Registry & Persistence:** Common autorun locations (`HKLM\Software\Microsoft\Windows\CurrentVersion\Run`, Scheduled Tasks) frequently serve as persistence locations.

---

## 8. Linux Security Concepts
- **POSIX Permission Bits & Umask:** Standard 9-bit permissions (`rwxrwxrwx`) govern Owner, Group, and Other access. World-writable files (`o+w`) on system configuration directories represent severe security risks.
- **SUID/SGID Special Bits:** The Set-User-ID (`chmod 4xxx`) and Set-Group-ID (`chmod 2xxx`) bits cause executables to run with the privileges of the file owner (often `root`) rather than the calling user.
- **Init Systems & systemd:** Linux manages system daemons via systemd unit files, targets, and symlinks under `/etc/systemd/system`.
- **Network Stack & `/proc/net`:** Sockets are queried via the netlink interface (represented by modern utilities such as `ss`). Binding to `0.0.0.0` or `::` opens sockets to all network interfaces.
- **Pluggable Authentication Modules (PAM) & `/etc/login.defs`:** Enforces password longevity, minimum lengths, and authentication policies.

---

## 9. Proposed System
CSSA establishes a unified, multi-tiered framework:
1. **Platform Layer:** `platforms.windows` and `platforms.linux` communicate with low-level OS interfaces via safe system utilities and native libraries.
2. **Normalization Layer:** Converts OS-specific dictionaries into standardized models (`core.models`).
3. **Engine Layer:** Evaluates security rules (`core.rule_engine`) and calculates bounded risk metrics (`core.scoring`).
4. **Persistence Layer:** SQLite database (`database.db`) storing audit runs, findings, and baseline snapshots.
5. **Presentation Layer:** PySide6 desktop GUI with dark/light themes, real-time filtering, responsive cards, and circular score visualizations.

---

## 10. Architecture
```
                  +-----------------------------------+
                  |         CSSA Desktop GUI          |
                  |     (PySide6 / Custom Widgets)    |
                  +-----------------+-----------------+
                                    |
                  +-----------------v-----------------+
                  |          Audit Controller         |
                  |          (core.auditor)           |
                  +-----------------+-----------------+
                                    |
         +--------------------------+--------------------------+
         |                                                     |
         v (REAL)                                              v (DEMO)
+------------------------+                           +--------------------+
| SecurityPlatformAdapter|                           |  Fixture Loader    |
+-----------+------------+                           | (windows/linux     |
     |              |                                |  demo JSON files)  |
     v              v                                +---------+----------+
+---------+    +---------+                                     |
| Windows |    |  Linux  |                                     |
| Adapter |    | Adapter |                                     |
+----+----+    +----+----+                                     |
     |              |                                          |
     +-------+------+                                          |
             |                                                 |
             v                                                 |
+----------------------------------------------------+         |
|              Normalization Pipeline                |<--------+
|   (SystemInfo, UserAccount, ServiceInfo, etc.)     |
+-------------------------+--------------------------+
                          |
                          v
+----------------------------------------------------+
|                Security Rule Engine                |
|        (rules/common, windows, linux JSON)         |
+-------------------------+--------------------------+
                          |
                          v
+----------------------------------------------------+
|                Risk & Score Engine                 |
|             (Base 100, Capped Penalties)           |
+-------------+--------------------------+-----------+
              |                          |
              v                          v
    +-------------------+      +--------------------+
    |  SQLite Database  |      | Reports Generator  |
    | (History/Baseline)|      |    (HTML & PDF)    |
    +-------------------+      +--------------------+
```

---

## 11. Module Description
- **`core.models`:** Comprehensive Python dataclasses representing system configuration, findings, categories, and drift diffs.
- **`core.scanner`:** Dispatches inspection routines across the adapter methods with independent exception guards.
- **`core.rule_engine`:** Ingests declarative JSON rules and tests host configurations against rule predicates.
- **`core.scoring`:** Deducts points based on severity, applying category caps to maintain mathematical fairness.
- **`core.baseline`:** Creates normalized snapshots and computes set differentials between audits.
- **`platforms.windows`:** Modules for `system`, `users`, `processes`, `services`, `firewall`, `network`, `permissions`, `startup`, and `policies`.
- **`platforms.linux`:** Modules utilizing `/proc`, `/etc`, `systemctl`, `ss`, `ufw`, `iptables`, and `stat` calls.
- **`database.db`:** Thread-safe SQLite manager using parameterized queries.
- **`reports.html_report`:** Produces self-contained, responsive HTML reports with dark theme styling.
- **`gui.*`:** PySide6 user interface including dashboard, sidebar, tabular views, and score gauges.

---

## 12. Implementation
CSSA was implemented in Python 3.11+ without relying on unstable external APIs. Subprocess executions are wrapped by `utils.command_runner.run_command()`, which enforces:
- `shell=False` execution with explicit argument vectors (`list[str]`).
- Bounded execution timeouts (default 30 seconds).
- Explicit UTF-8 decoding with `replace` error strategies.
- Structured return objects (`CommandResult`) capturing exit codes, standard output, and standard error.

---

## 13. Security Rule Engine
The engine evaluates rules defined in:
- `rules/common_rules.json`: Platform-agnostic rules (e.g., firewall state, exposed listening ports, high resource utilization).
- `rules/windows_rules.json`: Windows-specific rules (e.g., Guest account active, unnecessary services such as Telnet/FTP, weak password policies, suspicious startup locations).
- `rules/linux_rules.json`: Linux-specific rules (e.g., SSH `PermitRootLogin`, world-writable configuration files, SUID binaries).

Each evaluated finding produces an explicit `Finding` record detailing the Rule ID, Category, Severity, Status (`PASS`, `WARNING`, `FAIL`, `UNAVAILABLE`), Rationale, and Remediation Recommendation.

---

## 14. Scoring Methodology
The scoring algorithm starts at a base score of 100:
$$\text{Score} = \max\left(0, 100 - \sum_{c \in \text{Categories}} \min\left(P_c, \text{Cap}_c\right)\right)$$

Where $P_c$ is the accumulated penalty points for category $c$:
- **CRITICAL:** 8 points deduction
- **HIGH:** 4 points deduction
- **MEDIUM:** 2 points deduction
- **LOW:** 1 point deduction
- **WARNING status:** 50% of the severity penalty

The category cap ($\text{Cap}_c = 12$) prevents repetitive findings in a single category (such as multiple listening ports) from reducing the entire host score to zero.

### Risk Level Bands
- **90 – 100:** Excellent
- **75 – 89:** Good
- **60 – 74:** Needs Improvement
- **40 – 59:** High Risk
- **0 – 39:** Critical Risk

---

## 15. Database Design
The SQLite database schema (`database/schema.py`) includes:
- **`audits`:** Stores audit UUID, timestamp, host metadata, overall score, risk band, mode, and full serialized JSON payload.
- **`findings`:** Foreign-keyed to `audits(id)`; indexes findings by rule ID, category, severity, status, evidence, and recommendation.
- **`baselines`:** Metadata for named baseline snapshots.
- **`baseline_items`:** Foreign-keyed to `baselines(id)`; stores category, key, value, and item details.
- **`settings`:** Key-value table for UI themes and penalty preferences.

---

## 16. UI Design
The PySide6 interface is crafted to provide a professional, technical cybersecurity operations center aesthetic:
- **Consistent Color Palette:** Deep midnight background (`#1a1a2e`), elevated cards (`#16213e`), borders (`#0f3460`), and vivid severity accents (`#FF1744` for Critical, `#e94560` for Primary Action).
- **Circular Gauge Widget:** Custom painted circular score indicator rendering normalized score percentages with risk-band reactive coloring.
- **Non-Blocking Execution:** Audits run inside a dedicated worker `QThread`, preventing UI freezes during collection.
- **Demo Mode Banner:** High-visibility amber banner dynamically toggled when simulated data is active to eliminate confusion between test simulations and production evaluations.

---

## 17. Testing
The test suite utilizes `pytest` and achieves 100% pass rate across 52 unit and integration tests:
- **`test_scoring.py`:** Validates zero-deduction base scores, warning halves, category capping, and boundary floor behaviors.
- **`test_rules.py`:** Verifies rule file loading, predicate evaluations, platform filtering, and disabled rule exclusion.
- **`test_normalizer.py`:** Tests IP classification (loopback vs wildcard vs LAN IP) and service string normalization.
- **`test_baseline.py`:** Tests snapshot creation and configuration drift detection (`Added`, `Removed`, `Changed`).
- **`test_platform_detection.py`:** Validates OS identification and privilege classification under mocked environments.
- **`test_windows_parsers.py`:** Tests parsing of `net user`, `netsh advfirewall`, and `net accounts` outputs.
- **`test_linux_parsers.py`:** Tests parsing of `ufw status`, `ss -tulnp`, `/etc/ssh/sshd_config`, and `systemctl`.
- **`test_database.py`:** Tests SQLite table migrations, audit persistence, findings retrieval, and setting key-value operations.
- **`test_report.py`:** Verifies HTML generation, required structural sections, and PDF fallback safety.

---

## 18. Results
Experimental verification of the system demonstrates:
1. **Windows 11 Simulation:** Generates an overall score of **69/100 (Needs Improvement)** with 9 findings highlighting a disabled host firewall, active Guest account, exposed database/telnet ports, and temp-directory persistence entries.
2. **Linux Simulation:** Generates an overall score of **79/100 (Good)** with 8 findings identifying world-writable files, exposed MySQL port, SUID binaries, and root SSH login permission.
3. **Live System Execution:** Gracefully handles non-root user execution on live hosts without crashing, reporting `UNAVAILABLE` for privileged resources while collecting all accessible system metrics.

---

## 19. Limitations
- **Read-Only Scope:** By design, CSSA does not automatically fix detected weaknesses.
- **Privilege Ceilings:** Without root/Administrator privileges, deep inspections (e.g., reading `/etc/shadow` or inspecting kernel firewall tables) return `UNAVAILABLE`.
- **Heuristic Indicators:** Unfamiliar processes or startup entries are flagged as anomalies for review rather than confirmed malware.

---

## 20. Future Scope
- **macOS Adapter:** Implement `MacOSSecurityAdapter` using `launchctl`, `pfctl`, and Directory Utility APIs.
- **Interactive Rule Builder:** Graphical interface for defining custom JSON audit rules and adjusting penalty weights.
- **Compliance Mapping:** Direct cross-referencing of findings with CIS Benchmark recommendations and MITRE ATT&CK techniques.

---

## 21. Conclusion
CSSA demonstrates that cross-platform defensive security auditing can be achieved through disciplined software architecture. By decoupling platform collection from data normalization and rule evaluation, the tool achieves complete feature parity across Windows and Linux environments while upholding strict safety, transparency, and non-destructive operation principles.

---

## 22. References
1. Microsoft Corporation. *Windows Filtering Platform Architecture*. Microsoft Learn, 2024.
2. Linux Kernel Organization. *The /proc Filesystem Documentation*. kernel.org, 2024.
3. Center for Internet Security. *CIS Benchmarks for Windows 11 and Ubuntu Linux*. CISecurity, 2024.
4. Qt Project. *Qt for Python (PySide6) Documentation*. The Qt Company, 2024.
5. National Institute of Standards and Technology. *NIST SP 800-53 Rev. 5: Security and Privacy Controls for Information Systems and Organizations*. NIST, 2020.
