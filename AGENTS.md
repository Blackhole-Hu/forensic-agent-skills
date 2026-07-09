# AGENTS.md

## Project

forensic-agent-skills — Evidence-driven AI agent skills for digital forensics, incident response, CTF forensics, server reconstruction, evidence tracking, and report generation.

## Agent Workflow

- Always run `git status` before making changes.
- Make small, scoped changes — one concern per commit.
- Do not push without explicit user confirmation.
- Do not commit unless the current task explicitly authorizes local commits.
- Preserve evidence-first terminology: every conclusion must cite a source.
- Follow `docs/agents/domain.md` vocabulary — use project-defined terms (Artifact, Evidence Ledger, Chain of Custody, Finding, Hypothesis, Timeline, Answer Gate, Report).
- When migrating old skills, remove local path binding unless the path is clearly documented as an example.

## Agent skills

### Evidence principle

Every conclusion MUST be backed by evidence — file content, command output, log entries, hashes, screenshots, or report fragments. A finding without a cited source is not a finding.

### Issue tracker

GitHub Issues (`Blackhole-Hu/forensic-agent-skills`), external PRs not used as triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical roles: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at repo root. See `docs/agents/domain.md`.

### Migration roadmap

Four-phase migration from `E:\CompetitionTools\skills` (41 skills). See `docs/migration/old-skills-inventory.md`.

| Phase | Scope | Key skills |
|-------|-------|------------|
| **Phase 1** | Core control loop | forensic-autopilot, forensic-router, tool-router, evidence-ledger, answer-gate, report-writer, handoff, file-triage, large-artifact-strategy |
| **Phase 2** | Server forensic chain | server-forensics-router, rebuild-planner/executor, remote-live-response, linux/webapp/database/docker/cluster forensics, timeline-reconstruction |
| **Phase 3** | Uncommon media & recovery | uncommon-media-triage, proprietary-format-recovery, firmware-iot, nas-raid-encrypted, malware |
| **Phase 4** | Competition-specific output | iscc-wp-writer (competition), competition-autopilot (competition logic) |
