# Domain Docs

How agent skills should consume this repo's domain documentation when exploring skill definitions, playbooks, and forensic procedures.

## Core domain vocabulary

When writing skill bodies, issue titles, ADRs, or reports, prefer these project-scoped terms:

| Term | Meaning |
|------|---------|
| **Artifact** | A file, image, disk, memory dump, log, or binary under examination |
| **Evidence Ledger** | The append-only record that tracks every artifact touched and action taken |
| **Chain of Custody** | The ordered provenance of an artifact from acquisition to conclusion |
| **Finding** | An evidence-backed conclusion with cited sources |
| **Hypothesis** | A falsifiable claim about what happened, to be tested against artifacts |
| **Timeline** | A chronologically ordered reconstruction of events from multiple evidence sources |
| **Answer Gate** | The final validation step before a conclusion is submitted |
| **Report** | The structured output that presents findings, evidence, and reasoning |

## Before exploring, read these

- **`CONTEXT.md`** at the repo root, or
- **`CONTEXT-MAP.md`** at the repo root if it exists — it points at one `CONTEXT.md` per context. Read each one relevant to the topic.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in. In multi-context repos, also check `src/<context>/docs/adr/` for context-scoped decisions.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure

Single-context repo:

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-evidence-chain-of-custody.md
│   └── 0002-skill-naming-conventions.md
└── skills/
```

## Use the glossary's vocabulary

When your output names a domain concept (in a skill body, an issue title, an ADR, or a report), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0001 (evidence chain of custody) — but worth reopening because…_
