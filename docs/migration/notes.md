# Migration Notes

Working notes, open questions, and decisions made during the migration from `E:\CompetitionTools\skills`.

## Open Questions

### Q1: evidence-ledger format
The evidence-ledger is a new module not directly from an old skill. Need to decide:
- File format: JSON lines, Markdown table, or YAML?
- Storage: single file per investigation or append-only log?
- Integration: how do skills write to it (template, function call, or convention)?

**Current decision**: Markdown-based, one file per investigation, skills write entries following the template in `templates/evidence-ledger.md`.

### Q2: forensic-router vs server-forensics-router boundary
`forensic-router` is the new generic router. `server-forensics-router` is the old server-specific router. Need to clarify:
- Does forensic-router replace server-forensics-router?
- Or does forensic-router delegate to server-forensics-router for server material?

**Current decision**: forensic-router is the top-level router that delegates to domain-specific routers. server-forensics-router remains as the server-specific entry point.

### Q3: timeline-reconstruction scope
The old `server-timeline-reconstruction` only handles server logs. The new `timeline-reconstruction` should handle:
- Server logs (auth, access, journal, application)
- PCAP files
- File timestamps
- Browser history
- Database records
- Container logs

**Current decision**: Start with server log sources, add others incrementally.

### Q4: answer-gate generalization
The old `server-answer-gate` has server-specific validation. The new `answer-gate` needs:
- Generic five-step validation applicable to all forensic scenarios
- Server-specific checks as optional extensions

**Current decision**: Core five-step logic is generic. Domain-specific checks (e.g., server IP validation) are documented as examples.

## Decisions Made

### D1: writing-great-skills not migrated as skill
Converted to `docs/skill-authoring-guide.md` + `templates/skill-template.md`. Rationale: it's a reference document, not a runnable workflow.

### D2: ask-matt not retained
Routing split into `forensic-autopilot` (orchestration) and `forensic-router` (material routing). The name `ask-matt` carries no meaning in this project.

### D3: large-artifact-strategy in triage/, not kb/
It's a strategy layer invoked during triage, not a knowledge base reference.

### D4: report-writer in Phase 1, not Phase 4
Generic report output is part of the core control loop. Competition-specific templates are Phase 4.

## Blocked Items

None currently.
