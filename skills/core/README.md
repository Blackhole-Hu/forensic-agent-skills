# Core Skills

Core control loop skills that form the backbone of every forensic workflow.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `forensic-autopilot/` | Master orchestrator — chains all skills together | Draft |
| `forensic-router/` | Routes material to the correct analysis path | Draft |
| `tool-router/` | Selects execution environment (Windows/WSL/Docker/VMware/QEMU) | Draft |
| `evidence-ledger/` | Records every artifact, action, and hash | Draft |
| `answer-gate/` | Five-step validation before any conclusion | Draft |
| `report-writer/` | Structured output with evidence citations | Draft |
| `handoff/` | Session handoff between agents | Draft |

## Execution Order

```
forensic-autopilot
  → tool-router
  → file-triage
  → large-artifact-strategy (if triggered)
  → forensic-router (based on triage_notes)
  → evidence-ledger (writes throughout)
  → [domain-specific skills]
  → timeline-reconstruction (if needed)
  → answer-gate → report-writer
```

## Migration Source

Phase 1 of `docs/migration/old-skills-inventory.md`.
