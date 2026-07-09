# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

Edit the right-hand column to match whatever vocabulary you actually use.

## Suggested project-scoped labels

The following labels are optional — create them as needed, not all at once.

### Scope

| Label | Meaning |
|-------|---------|
| `scope:core` | Core skill framework / engine |
| `scope:triage` | Triage and routing logic |
| `scope:server` | Server forensics skills |
| `scope:timeline` | Timeline reconstruction skills |
| `scope:competition` | CTF / competition skills |
| `scope:kb` | Knowledge base and reference material |
| `scope:docs` | Documentation |

### Status

| Label | Meaning |
|-------|---------|
| `status:mvp` | Minimum viable implementation |
| `status:experimental` | Exploratory, may be discarded |

### Safety

| Label | Meaning |
|-------|---------|
| `safety:review-required` | Must be reviewed before merge — touches evidence handling, destructive ops, or external output |
