# Evidence Standard

Every conclusion in forensic-agent-skills MUST be backed by evidence. This document defines what counts as evidence and how to record it.

## The Evidence Principle

> A finding without a cited source is not a finding.

This is the foundational rule. No exceptions.

## What Counts as Evidence

| Evidence Type | Examples | Strength |
|---------------|----------|----------|
| **File content** | Config files, source code, log excerpts | High |
| **Command output** | Shell output, tool output, hash values | High |
| **Log entries** | auth.log, access.log, journal, Docker logs | High |
| **Hash values** | MD5, SHA256 of artifacts | High (integrity) |
| **Screenshots** | GUI output, web pages, terminal capture | Medium |
| **Report fragments** | Tool-generated reports (Autopsy, Volatility) | Medium |
| **Timestamps** | File mtime, log timestamps, database records | Medium |
| **Inference** | Logical deduction from multiple evidence items | Low alone, High when chain is complete |

## Evidence Recording

All evidence is recorded in the `evidence-ledger`. Each entry must include:

| Field | Required | Description |
|-------|----------|-------------|
| `artifact` | Yes | What was examined (file path, image name, service) |
| `source` | Yes | Where it came from (disk image path, remote host, container ID) |
| `hash` | Recommended | Integrity hash of the artifact (SHA256 preferred) |
| `command` | Yes (if tool used) | Exact command or tool invocation |
| `finding` | Yes | What was discovered |
| `confidence` | Yes | `high` / `medium` / `low` |
| `next_action` | Recommended | What should happen next |

## Confidence Levels

| Level | Meaning | When to Use |
|-------|---------|-------------|
| `high` | Directly observed, reproducible | Hash match, log entry, file content |
| `medium` | Inferred from strong evidence chain | Multiple corroborating sources |
| `low` | Hypothesis, needs validation | Single indirect indicator |

## Negative Evidence

Recording what was NOT found is also evidence:
- "No backdoor found in /etc/crontab"
- "No WebShell detected in /var/www/"
- "auth.log shows no failed login attempts before 2026-01-15"

Negative evidence prevents confirmation bias and strengthens the investigation.

## Chain of Custody

For each artifact, the evidence ledger tracks:
1. **Acquisition** — how and when the artifact was obtained
2. **Handling** — what operations were performed (all read-only by default)
3. **Storage** — where working copies reside
4. **Integrity** — hash verification at each stage

## Dual-Format Design

The evidence ledger uses two complementary formats:

| Format | File | Purpose |
|--------|------|---------|
| **Markdown** | `evidence-ledger.md` | Human review primary view — readable, printable, editable |
| **JSONL** | `evidence-ledger.jsonl` | Machine validation log — structured, queryable, append-only |

- `answer-gate` **prefers JSONL** for structured validation (field completeness, cross-reference checks)
- `report-writer` **references Markdown** for human-readable report appendices
- Both formats record the same entries; skills write to both simultaneously

## Validation

The `answer-gate` skill checks (prefer JSONL, fall back to Markdown):
1. Every cited finding has at least one evidence entry
2. Evidence entries reference actual artifacts (not hallucinated paths)
3. Hash values match where claimed
4. Confidence levels are justified by evidence type
