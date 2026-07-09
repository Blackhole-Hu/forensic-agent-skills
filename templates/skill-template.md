---
name: <skill-name>
description: <one-line description>
---

# <Skill Name>

## Purpose

<One paragraph: what this skill does and why it exists.>

## Use When

- <Trigger condition 1>
- <Trigger condition 2>
- <Precondition: what must be true before invoking>

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `<input-1>` | Yes | <description> |
| `<input-2>` | No | <description> |

## Outputs

| Output | Description |
|--------|-------------|
| `<output-1>` | <description> |
| `<output-2>` | <description> |

## Workflow

### Step 1: <Step Name>

<Description of what to do.>

**Evidence**: Record `<field>` in evidence ledger.

### Step 2: <Step Name>

<Description of what to do.>

**Evidence**: Record `<field>` in evidence ledger.

### Step N: <Final Step>

<Description of final action.>

## Evidence Requirements

| Field | When to Record | Example |
|-------|---------------|---------|
| `artifact` | Every step that examines something | `/var/log/auth.log` |
| `source` | Where the artifact came from | `disk-image-001.raw` |
| `hash` | When integrity matters | `sha256:abc123...` |
| `command` | When a tool is invoked | `grep 'Failed' /var/log/auth.log` |
| `finding` | When something is discovered | `3 failed SSH attempts from 10.0.0.5` |
| `confidence` | For every finding | `high` / `medium` / `low` |
| `next_action` | When the finding affects workflow | `Investigate IP 10.0.0.5` |

## Handoff

**Passes to**: `<next-skill-1>`, `<next-skill-2>`
**Data available**: <what the next skill can read from the evidence ledger>

## Stop Conditions

- <When to stop and ask for human input>
- <Ambiguous situation>
- <Missing required data>
- <High-risk operation>

## Notes

<Additional context, references, or caveats.>
