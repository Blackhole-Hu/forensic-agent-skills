# Migration Notes

Working notes, open questions, and decisions made during the migration from `E:\CompetitionTools\skills`.

## Open Questions

### Q1: evidence-ledger format
The evidence-ledger is a new module not directly from an old skill. Need to decide:
- File format: JSON lines, Markdown table, or YAML?
- Storage: single file per investigation or append-only log?
- Integration: how do skills write to it (template, function call, or convention)?

**Current decision**: Dual-format — Markdown for human review primary view, JSONL for machine validation log. Both formats record the same entries; skills write to both simultaneously. `answer-gate` prefers JSONL for structured checks; `report-writer` references Markdown for report appendices.

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

## Phase 1 Notes

- Phase 1 currently includes SKILL.md drafts only.
- CHECKLIST.md and REVIEW.md from old skills are not yet migrated.
- They will be handled in a later quality pass.

### Q5: Frontmatter schema
- Current drafts use `disable-model-invocation` in YAML frontmatter.
- This field is used by some mattpocock skills (`ask-matt`, `setup-matt-pocock-skills`) but not all.
- Need to verify whether Reasonix recognizes this field.
- If not, replace with the supported schema or remove nonstandard fields.
