# Skill Authoring Guide

How to write and maintain skills for forensic-agent-skills. Derived from `writing-great-skills` (not migrated as a runnable skill).

## Skill Structure

Every skill lives in its own directory under `skills/<category>/<skill-name>/` and must contain:

```
<skill-name>/
├── SKILL.md          ← required: the skill playbook
├── CHECKLIST.md      ← recommended: quality checklist
├── REVIEW.md         ← recommended: self-review report
└── [assets/]         ← optional: templates, scripts, references
```

## SKILL.md Structure

Use `templates/skill-template.md` as the starting point. Required sections:

1. **YAML frontmatter** — must include `name` and `description`; runtime-specific fields such as `disable-model-invocation` are optional and must be verified against the target agent before being required by this project
2. **Purpose** — one paragraph, what this skill does
3. **Use When** — triggers and preconditions
4. **Inputs** — what the skill needs to start
5. **Outputs** — what the skill produces
6. **Workflow** — step-by-step procedure
7. **Evidence Requirements** — what must be recorded in the evidence ledger
8. **Handoff** — what passes to the next skill, and which skill(s) follow
9. **Stop Conditions** — when to halt and ask for human input

## Writing Principles

### Be Predictable

A skill should produce the same quality of output regardless of which agent runs it. Ambiguity is the enemy.

- ❌ "Check the logs for suspicious activity"
- ✅ "Read /var/log/auth.log. Filter for lines containing 'Failed password' or 'Invalid user'. Record each unique source IP, target user, and timestamp in the evidence ledger."

### Evidence First

Every step that produces a finding must record it in the evidence ledger. Don't skip negative findings.

### Small Steps

Break complex workflows into atomic steps. Each step should:
- Do one thing
- Record its evidence
- Decide the next step

### Handoff Clarity

Every skill must declare what it passes forward. Don't make downstream skills guess what data is available.

### Stop Conditions

Define when the skill should stop and ask for human input:
- Ambiguous material type
- Missing required input
- Confidence below threshold
- High-risk operation (destruction, network access, execution)

## Naming Conventions

- Skill directories: `lowercase-with-hyphens`
- SKILL.md: always uppercase
- YAML frontmatter `name` field: matches directory name
- Category placement: `core/` for universal skills, domain-specific otherwise

## Quality Checklist

Before marking a skill as complete:

- [ ] YAML frontmatter has `name` and `description`
- [ ] Purpose is one paragraph
- [ ] Use When has clear triggers
- [ ] Inputs are explicitly listed
- [ ] Workflow has numbered steps
- [ ] Evidence Requirements list all fields to record
- [ ] Handoff names the next skill(s)
- [ ] Stop Conditions are defined
- [ ] No hardcoded local paths (unless documented as example)
- [ ] Read-only default for original artifacts

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| God skill | Does too much, hard to validate | Split into smaller skills |
| Silent failure | No evidence recorded for a step | Add evidence recording to every step |
| Path binding | Hardcoded local paths | Use variables or document as example |
| Vague triggers | "Use when appropriate" | Define specific preconditions |
| Missing handoff | Downstream skill doesn't know what's available | Declare outputs explicitly |
