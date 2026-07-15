# forensic-agent-skills

Evidence-driven AI agent skills for digital forensics, incident response, CTF forensics, server reconstruction, evidence tracking, and report generation.

## What This Is

A structured collection of AI agent skills (playbooks) for forensic analysis workflows. Each skill encodes a repeatable procedure — triage, acquisition, analysis, timeline reconstruction, validation, and reporting — that an AI agent can follow with human oversight.

The skills are **evidence-first**: every conclusion must cite a file, command output, log entry, hash, screenshot, or report fragment.

## What This Is Not

- Not a general-purpose coding assistant toolkit.
- Not a one-click execution framework — the skills define workflows, evidence requirements, and validation steps; concrete tools are selected by the operator or tool-router.
- Not a malware detonation framework — malware-specific recovery remains Pending in Phase 3 and is not a current executable capability.
- Not a replacement for forensic tools (Autopsy, Volatility, binwalk, etc.) — the skills orchestrate and validate their output.
- Not competition-specific — while born from CTF practice, the architecture targets general forensic workflows.

## Core Workflow

```
forensic-autopilot        →  orchestrate the full chain
  tool-router           →  select execution environment (Windows/WSL/Docker/VMware/QEMU)
  file-triage           →  first-pass file identification and classification
  large-artifact-strategy → handle 1GB+ images, disk dumps, encrypted containers (if triggered)
  forensic-router       →  route material to the right path based on triage_notes
  uncommon-media-triage →  identify evidence-backed uncommon record structures (if triggered)
  forensic-router re-entry  →  validate uncommon recovery candidate and select the consumer
  proprietary-format-recovery → reproduce bounded proprietary layouts/transforms (only after Router decision)
  firmware-iot-forensics → validate firmware containers/filesystems and perform bounded static extraction (only after Router decision)
  [implemented consumers] → server, current Web/Database/Docker, uncommon media triage, proprietary recovery, and firmware static analysis
  timeline-reconstruction → merge supported server-source events (if needed)
  no-compatible-skill   →  preserve evidence and report planned/unsupported scope
  answer-gate           →  five-step validation before any conclusion is submitted
  report-writer         →  structured output with evidence citations

evidence-ledger is written throughout the chain and read by answer-gate/report-writer.
```

Current executable scope is Core, Triage (including `uncommon-media-triage`), Server, server-scoped Timeline, bounded `proprietary-format-recovery`, and bounded static `firmware-iot-forensics`. Phase 3 is in progress (3/5): uncommon media triage, proprietary format recovery, and firmware IoT forensics are Implemented; storage and malware recovery remain Pending. Firmware can be selected directly by Router when two independent validation mechanisms support the route, or after evidence-backed uncommon/proprietary Router re-entry. Competition remains a planned migration phase and is not a current runtime target.

## Skill Categories

| Category | Path | Purpose |
|----------|------|---------|
| **Core** | `skills/core/` | Control loop, routing, evidence tracking, validation, output |
| **Triage** | `skills/triage/` | File classification, large artifact handling, and uncommon media structure identification |
| **Server** | `skills/server/` | Server forensics: rebuild, live response, Linux/Web/DB/Docker/cluster |
| **Timeline** | `skills/timeline/` | Server-scoped event timeline reconstruction |
| **Recovery** | `skills/recovery/` | Phase 3 bounded proprietary recovery and firmware static analysis (Implemented); NAS/RAID, encryption, and malware modules (Pending) |
| **Competition** | `skills/competition/` | Planned Phase 4: CTF and competition-specific output |

## Recommended Entry Point

```
skills/core/forensic-autopilot/SKILL.md
```

## Migration Plan

Migrating 41 legacy skills in four phases. See [`docs/migration/old-skills-inventory.md`](docs/migration/old-skills-inventory.md) for the source inventory and mapping.

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1** | Core control loop (9 modules) | Completed |
| **Phase 2** | Server forensic chain (10 modules) | Completed |
| **Phase 3** | Uncommon media & recovery (5 modules) | In progress (3/5) |
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
    ├── server/
    ├── timeline/
    ├── recovery/                       ← proprietary recovery and firmware Implemented; two Phase 3 modules Pending
    └── competition/                    ← planned Phase 4; not yet executable
```

## Current Status

- [x] Repository bootstrapped
- [x] Agent configuration (`AGENTS.md`, `docs/agents/`)
- [x] Migration inventory (`docs/migration/old-skills-inventory.md`)
- [x] Phase 1 — Core control loop and review
- [x] Phase 2 — Server forensic chain
- [ ] Phase 3 — Uncommon media & recovery — In progress (3/5)
- [ ] Phase 4 — Competition-specific output
