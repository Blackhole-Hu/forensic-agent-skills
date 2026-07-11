---
name: optimization-strategy
description: Competition optimization strategies for large-file low-density forensic scenarios — clue-driven search, layered scanning, suspect path reconstruction, parallel processing, and time allocation.
---

# Optimization Strategy

## Purpose

Optimize forensic analysis efficiency in competition scenarios with large disk images (50-200GB+) where flags occupy 1-2 files among millions. Replace brute-force scanning with clue-driven, layered, and parallel strategies.

## Use When

- Competition involves large disk images (>1GB)
- Multiple evidence sources need coordinated analysis
- Time-constrained environment (typically 4 hours)
- Need to maximize coverage with minimum time investment

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `evidence_sources` | Yes | List of all evidence files and sizes |
| `challenge_list` | Yes | Competition questions with keywords |
| `time_budget` | No | Available analysis time (default: 4 hours) |

## Outputs

| Output | Description |
|--------|-------------|
| `prioritized_findings` | Findings ranked by relevance |
| `time_allocation` | Time spent per evidence source |
| `coverage_report` | What was analyzed and what was skipped |

## Workflow

### Step 1: Clue-Driven Targeting

Read all challenges first, map keywords to likely file locations:

| Keyword | Likely Location |
|---------|----------------|
| Email/mail | .pst, .ost, thunderbird/, outlook/ |
| Browser history | History, places.sqlite, Login Data |
| Chat | WeChat/, QQ/, Telegram/, signal/ |
| Password | /etc/shadow, SAM, NTUSER.DAT |
| VPN/proxy | clash/, v2ray/, shadowsocks/ |
| AI/model | config/, settings/, llm_cache.db |
| Photo EXIF | Pictures/, DCIM/, Screenshots/ |
| Encrypted | .enc, .gpg, VeraCrypt, .7z/.rar |

Do NOT scan the entire image. Navigate directly to target paths.

**Evidence**: Record `keyword_mapping`, `target_paths` in evidence ledger.

### Step 2: Layered Scanning (Hit-and-Stop)

```
Level 0 (5s):    strings DISK | rg "flag|ctf"           — covers 30%
Level 1 (30s):   Targeted search tool on specific paths  — covers 50%
Level 2 (2min):  Forensic platform load + emulated system — covers 15%
Level 3 (10min): Deep icat extraction + hex analysis     — covers 5%

Rule: Stop at Level N once flag is found.
```

**Evidence**: Record `scan_level`, `time_spent`, `findings` in evidence ledger.

### Step 3: Suspect Path Reconstruction

Don't search for the flag. Reconstruct what the suspect did:
1. Browser history → what they searched for
2. Shell history → what commands they executed
3. Recent files → what they opened/edited
4. Downloads → what tools they downloaded
5. Found tool → reverse tool logic → decrypt target file

**Evidence**: Record `suspect_actions`, `tool_chain`, `reconstructed_path` in evidence ledger.

### Step 4: Parallel Processing

```
# Parallel PCAP analysis
ls *.pcap | xargs -P 8 -I {} tshark -r {} -Y http

# Parallel file scanning
smart_hunter.py -c ./case/ -w 16   # 16 threads
```

Never process evidence sources serially when they can be parallelized.

**Evidence**: Record `parallel_tasks`, `wall_time_saved` in evidence ledger.

### Step 5: Multi-Source Correlation

```
Step 1: Run evidence_linker.py for cross-reference matching
  - Same email → same person
  - Same IP → same network
  - Same file hash → copy/transfer
  - .enc + .key → encrypted file + key

Step 2: Start from easiest evidence
  Phone > Computer > Server > Encrypted container

Step 3: Extracted passwords/keys → apply to other sources

Step 4: Build unified timeline
```

**Evidence**: Record `cross_references`, `password_reuse`, `unified_timeline` in evidence ledger.

### Step 6: Emulation-First Principle

For complete system images with OS:
- Emulate first → GUI inspection → 10x faster than static analysis
- Desktop files, app settings, browser history all visible immediately

**Evidence**: Record `emulation_result`, `gui_findings` in evidence ledger.

## Time Allocation (4-hour competition)

```
0:00-0:05  Read all challenges, mark keywords
0:05-0:15  Run targeted scan tool on all sources
0:15-0:30  strings batch scan + cross-reference linking
0:30-1:30  Load forensic platform + emulation + manual analysis of hits
1:30-3:00  Deep analysis (reverse / decrypt / database)
3:00-3:30  Review and supplement
3:30-4:00  Finalize and write report
```

## Evidence Requirements

| Field | When to Record | Example |
|-------|---------------|---------|
| `scan_level_used` | Step 2 | Level 1 — 30s targeted search |
| `time_spent` | Each step | 12 minutes on disk analysis |
| `coverage_pct` | End | 85% of challenges addressed |
| `parallel_speedup` | Step 4 | 8x parallel, 45s saved |

## Handoff

**Passes to**: `answer-gate` (for final conclusions), `report-writer` (for output)
**Data available**: Prioritized findings, time allocation, coverage report

## Stop Conditions

- All challenge keywords have been addressed
- Time budget exhausted
- Diminishing returns — remaining evidence unlikely to yield new findings

## Notes

- Config files (.conf, .json, .yaml) have higher flag density than documents
- Databases (.db, .sqlite) are more valuable than text files
- Always read challenge descriptions carefully — the answer location is often hinted
- Never assume you know which app contains the answer — list all first
- Browser download history often reveals where suspects got their tools
- When a file is incomplete, check other evidence sources for the complete version
