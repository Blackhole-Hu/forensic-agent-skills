---
name: cross-evidence
description: Cross-evidence correlation across multiple forensic images — tracing password chains, data propagation, chat migration, download trails, and multi-device timeline reconstruction.
---

# Cross-Evidence Correlation

## Purpose

Correlate evidence across multiple forensic images (phone, computer, server) to trace data propagation, identify shared credentials, reconstruct cross-device operations, and build unified timelines. Core principle: wherever cross-device information appears, transmission traces must exist somewhere.

## Use When

- Multiple forensic images from the same case exist
- Same data (passwords, files, chat records) appears in multiple sources
- Need to trace data transfer between devices
- Multi-device timeline reconstruction is required

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `evidence_list` | Yes | List of all forensic images/sources |
| `target_data` | No | Specific data to trace across sources |
| `known_identities` | No | Known usernames, emails, IPs to correlate |

## Outputs

| Output | Description |
|--------|-------------|
| `propagation_chains` | How data moved between devices |
| `shared_credentials` | Password/credential patterns across devices |
| `unified_timeline` | Combined chronological event list |
| `cross_references` | Matching IPs, usernames, file hashes across sources |

## Workflow

### Step 1: Inventory All Sources

List all IPs, usernames, file hashes, and passwords found across all evidence. Cross-match for overlaps.

**Evidence**: Record `ip_list`, `username_list`, `hash_list`, `password_patterns` in evidence ledger.

### Step 2: Trace Credential Chains

Same suspect tends to use password patterns:
```
Pattern example: 4letters + 1symbol + 8digit_date
  steghide:   JHTJ@202605
  VeraCrypt:  JHTJ！@#￥A313
  Hidden VC:  JHTJ@20260512
```

Search all sources for the same password prefix to find the full pattern.

**Evidence**: Record `password_prefix`, `full_passwords`, `pattern_rule` in evidence ledger.

### Step 3: Trace Data Propagation

Common propagation paths:
- **Database backup**: Server `autobackup.sh` → scp → suspect's computer download
- **Chat migration**: App A (first half) → App B (second half) — search for app name transitions
- **File transfer**: Browser download → local storage → encrypted container
- **Sync**: Cloud sync creates copies across devices

Verify: compare SHA256 hashes across sources to confirm identical files.

**Evidence**: Record `source_device`, `target_device`, `transfer_method`, `file_hash` in evidence ledger.

### Step 4: Multi-Device Timeline

Reconstruct operations across devices:
```
Server:    2026-05-11 init → 05-12 deploy guard script → 05-14 last backup
Computer:  2026-05-12 16:36 install app → 16:48 download data
Phone:     2026-05-12 15:35 contact dealer → 16:33 switch app → 16:48 download
```

Cross-validate: if phone download time ≈ computer chat time → same event, high confidence.

**Evidence**: Record `event_time`, `device`, `action`, `cross_validation` in evidence ledger.

### Step 5: Post-Competition Search

Search for writeups and solutions:
```
site:mp.weixin.qq.com "competition_name" "wp" OR "writeup"
site:github.com "competition_name" forensics
site:blog.csdn.net electronic forensics CTF writeup 2025
```

**Evidence**: Record `search_results`, `reference_solutions` in evidence ledger.

## Evidence Requirements

| Field | When to Record | Example |
|-------|---------------|---------|
| `ip_match` | Step 1 | 10.0.0.5 appears in phone + server |
| `credential_pattern` | Step 2 | Prefix "JHTJ" in 3 different apps |
| `file_hash_match` | Step 3 | SHA256:abc in server backup = computer download |
| `timeline_event` | Step 4 | 2026-05-12 16:48 — data transfer confirmed |
| `propagation_path` | Step 3 | Server → scp → Computer → USB → Phone |

## Handoff

**Passes to**: `timeline-reconstruction` (for unified timeline), `answer-gate` (for conclusions)
**Data available**: Propagation chains, shared credentials, cross-device timeline

## Stop Conditions

- Only one forensic image available (no cross-correlation possible)
- Evidence sources have no identifiable common identifiers
- Timestamps across devices are not synchronized enough for correlation

## Notes

- **Iron rule**: Cross-device information always leaves transmission traces
- Always list ALL sources first before assuming — answers may be in unexpected locations
- Password patterns are the strongest cross-evidence link
- SHA256 hash comparison is definitive proof of file identity
- Check backup scripts, cron jobs, and sync configurations for propagation paths
- When a file is incomplete on one source, search other sources for the complete version
