---
name: ai-forensics-workflow
description: AI-assisted digital forensics workflow using MCP plugins for PCAP analysis, APK reverse engineering, website forensics, and binary analysis with verified automation patterns.
---

# AI-Assisted Forensics Workflow

## Purpose

Leverage AI IDE tools (Trae, Claude Code, Cursor) combined with MCP plugins to perform semi-automated forensic analysis: automate PCAP traffic analysis, APK reverse engineering, website forensics, and binary analysis with verified AI prompt templates.

## Use When

- AI-assisted analysis is desired for faster triage
- MCP plugins (wireshark-mcp, jadx-mcp, r2-mcp) are available
- Repetitive forensic tasks can benefit from automation
- Quick overview is needed before deep manual analysis

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `evidence_file` | Yes | File to analyze (PCAP, APK, binary, website) |
| `analysis_type` | Yes | Type: pcap, apk, website, binary |
| `ai_tool` | No | AI tool to use (trae, claude, cursor) |

## Outputs

| Output | Description |
|--------|-------------|
| `automated_findings` | AI-identified findings with confidence |
| `attack_ips` | Identified attacker/victim IPs |
| `extracted_artifacts` | Auto-extracted files, credentials, keys |
| `verification_status` | Whether findings need manual verification |

## Workflow

### Step 1: PCAP Traffic Analysis (Verified)

AI prompt template:
```
Analyze this PCAP file:
1. Calculate SHA1 hash
2. Identify attacker and victim IPs (via statistics + TCP handshake)
3. Find uploaded trojan filename (HTTP PUT/POST)
4. Find webshell connection password
5. Trace TCP stream for first hacker command
6. Identify backdoor reverse connection IP and port
```

Verified auto-answerable: SHA1, attacker/victim IP, webshell filename/password, backdoor IP:PORT, first command.

**Evidence**: Record `ai_findings`, `confidence_level`, `manual_verification` in evidence ledger.

### Step 2: APK Reverse Analysis

MCP tool chain: jadx-mcp-server → r2-mcp → frida-mcp

AI prompt template:
```
Analyze this APK:
1. Package name and entry Activity
2. Permission list (mark dangerous ones)
3. Exported components
4. URLs, IPs, emails in source code
5. Encryption algorithms used (AES/DES/RSA/MD5/Base64)
6. Hardcoded keys, passwords, API keys
7. Native .so export functions
```

**Evidence**: Record `app_metadata`, `sensitive_findings`, `native_analysis` in evidence ledger.

### Step 3: Website Forensics

Analysis targets:
- CMS/framework identification (WordPress, ThinkPHP, Laravel)
- Admin login path discovery
- Login logic analysis (captcha bypass, SQL injection)
- Database config file location and password
- Backdoor file detection
- Recently modified files

**Evidence**: Record `cms_type`, `admin_path`, `vulnerabilities`, `backdoors` in evidence ledger.

### Step 4: Binary Reverse with MCP

MCP options: idapromcp (IDA), r2-mcp (radare2)

AI can assist with: function identification, string analysis, basic algorithm recognition. Complex custom algorithms still require manual analysis.

**Evidence**: Record `function_analysis`, `algorithm_type`, `ai_confidence` in evidence ledger.

### Step 5: Manual Verification

**Golden rule**: AI result → manual verification → confirm before submission.

| Category | AI Suitability |
|----------|---------------|
| Statistics, pattern matching, batch conversion | High — trust with verification |
| Complex encryption/decryption | Low — manual required |
| Custom protocol analysis | Low — manual required |
| Cross-evidence correlation | Medium — verify logic |

**Evidence**: Record `verification_result`, `corrections_made` in evidence ledger.

## Evidence Requirements

| Field | When to Record | Example |
|-------|---------------|---------|
| `ai_tool_used` | Each step | jadx-mcp-server + r2-mcp |
| `automated_result` | Each step | Attacker IP: 10.0.0.5 |
| `confidence` | Each finding | high / medium / low |
| `verified` | Step 5 | Confirmed by manual analysis |

## Handoff

**Passes to**: `answer-gate` (for verified conclusions)
**Data available**: AI findings, verification status, extracted artifacts

## Stop Conditions

- AI tool or MCP plugin not available
- Analysis requires background knowledge AI lacks
- Results are contradictory and cannot be reconciled
- High-stakes conclusion requires fully manual verification

## Notes

- AI excels at: statistics, pattern matching, known-format parsing, batch operations
- AI struggles with: custom encryption, proprietary protocols, logic inference
- Always verify AI-identified IPs, passwords, and file names manually
- MCP tool mapping: wireshark-mcp → tshark CLI, jadx-mcp → jadx CLI, r2-mcp → radare2 CLI
- AI is a triage accelerator, not a replacement for forensic judgment
