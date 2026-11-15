# Architecture

The Cross-Platform System Security Auditor (CSSA) is designed using a modular, loosely-coupled architecture that separates data extraction, normalization, and evaluation.

## 1. Adapter Pattern
Platform-specific operations are abstracted behind adapters:
- `WindowsAdapter` executes Windows-specific commands (`wmic`, `netsh`, etc.).
- `LinuxAdapter` executes Linux-specific commands (`ss`, `systemctl`, parses `/etc/passwd`).

## 2. Data Normalization Pipeline
Data extracted from various platforms is passed through the Normalizer which maps disparate data formats to common internal dataclasses (e.g., `Process`, `Service`, `NetworkPort`).

## 3. Rule Engine
The rule engine evaluates the normalized system state against JSON-defined security rules. It filters rules based on the operating system.

## 4. Scoring Methodology
A base score of 100 is adjusted based on the severity of findings:
- CRITICAL: -20
- HIGH: -10
- MEDIUM: -5
- LOW: -1
The score floor is 0.

## 5. Database
SQLite is used via an abstraction layer to persist settings, previous audits, and baselines.

## 6. Reporting
A dedicated reporting module generates HTML files from audit results and gracefully attempts PDF generation via ReportLab if available.

```text
+-----------+        +-------------+        +-------------+
|    GUI    | <----> | Application | <----> | Rule Engine |
+-----------+        |    Core     |        +-------------+
                     +-------------+               ^
                            |                      |
                            v                      |
                     +-------------+        +-------------+
                     | Data Models | <----> | Normalizer  |
                     +-------------+        +-------------+
                            ^                      ^
                            |                      |
                     +-------------+        +-------------+
                     | Windows Adp |        | Linux Adp   |
                     +-------------+        +-------------+
```
