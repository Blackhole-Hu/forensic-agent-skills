# forensic-agent-skills

Evidence-driven AI agent skills for digital forensics, incident response, CTF forensics, server reconstruction, evidence tracking, and report generation.

## What This Is

A structured collection of AI agent skills (playbooks) for forensic analysis workflows. Each skill encodes a repeatable procedure — triage, acquisition, analysis, timeline reconstruction, validation, and reporting — that an AI agent can follow with human oversight.

The skills are **evidence-first**: every conclusion must cite a file, command output, log entry, hash, screenshot, or report fragment.

## What This Is Not

- Not a general-purpose coding assistant toolkit.
- Not a one-click execution framework — the skills define workflows, evidence requirements, and validation steps; concrete tools are selected by the operator or tool-router.
- Not a malware detonation framework — malware-related skills focus on forensic analysis, artifact extraction, IOC generation, and reportable findings.
- Not a replacement for forensic tools (Autopsy, Volatility, binwalk, etc.) — the skills orchestrate and validate their output.
- Not competition-specific — while born from CTF practice, the architecture targets general forensic workflows.

## Core Workflow

```
forensic-autopilot        →  orchestrate the full chain
  tool-router           →  select execution environment (Windows/WSL/Docker/VMware/QEMU)
  file-triage           →  first-pass file identification and classification
  large-artifact-strategy → handle 1GB+ images, disk dumps, encrypted containers (if triggered)
  forensic-router       →  route material to the right path based on triage_notes
  [domain-specific skills] → server / recovery / timeline / competition
  timeline-reconstruction → merge events from multiple sources (if needed)
  answer-gate           →  five-step validation before any conclusion is submitted
  report-writer         →  structured output with evidence citations

evidence-ledger is written throughout the chain and read by answer-gate/report-writer.
```

## Skill Categories

| Category | Path | Purpose |
|----------|------|---------|
| **Core** | `skills/core/` | Control loop, routing, evidence tracking, validation, output |
| **Triage** | `skills/triage/` | File classification, large artifact handling, uncommon media |
| **Domain** | `skills/domain/` | Network, disk, stego, crypto, RE, Android, cross-evidence, vehicle, AI, optimization |
| **Server** | `skills/server/` | Server forensics: rebuild, live response, Linux/Web/DB/Docker/cluster |
| **Timeline** | `skills/timeline/` | Multi-source event timeline reconstruction |
| **Recovery** | `skills/recovery/` | Proprietary formats, firmware, NAS/RAID, encryption, malware |
| **Competition** | `skills/competition/` | CTF and competition-specific output (Phase 4) |

## Recommended Entry Point

```
skills/core/forensic-autopilot/SKILL.md
```

## Migration Plan

Migrating from `E:\CompetitionTools\skills` (41 skills) in four phases. See [`docs/migration/old-skills-inventory.md`](docs/migration/old-skills-inventory.md).

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1** | Core control loop (9 modules) | Drafts created; under review |
| **Phase 1+** | Domain forensic skills (10 modules) | Drafts created |
| **Phase 2** | Server forensic chain (10 modules) | Pending |
| **Phase 3** | Uncommon media & recovery (5 modules) | Pending |
| **Phase 4** | Competition-specific output (2 modules) | Pending |

## Repository Layout

```
forensic-agent-skills/
├── AGENTS.md                          ← Agent configuration and workflow rules
├── README.md                          ← This file
├── docs/
│   ├── agents/                        ← Issue tracker, triage labels, domain docs config
│   ├── migration/                     ← Migration inventory and planning
│   └── skill-authoring-guide.md       ← How to write skills for this repo
├── templates/
│   └── skill-template.md              ← Starter template for new skills
└── skills/                            ← The skills themselves
    ├── core/
    ├── triage/
    ├── domain/
    ├── server/
    ├── timeline/
    ├── recovery/
    └── competition/
```

## Current Status

- [x] Repository bootstrapped
- [x] Agent configuration (`AGENTS.md`, `docs/agents/`)
- [x] Migration inventory (`docs/migration/old-skills-inventory.md`)
- [x] Phase 1 — Core control loop drafts
- [x] Phase 1+ — Domain forensic skills (10 skills)
- [ ] Phase 1 — Human review and refinement
- [ ] Phase 2 — Server forensic chain
- [ ] Phase 3 — Uncommon media & recovery
- [ ] Phase 4 — Competition-specific output
