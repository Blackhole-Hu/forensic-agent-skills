# Workflow Model

How forensic-agent-skills organizes work into a structured chain.

## The Chain Model

Every forensic investigation follows a chain of skills. Each skill:
- Receives input from the previous skill (or the user)
- Performs its work with explicit evidence requirements
- Produces output for the next skill
- Records actions in the evidence ledger

```
User / Competition Input
    ↓
forensic-autopilot          ← orchestrate the full chain
    ↓
tool-router                 ← select execution environment
    ↓
file-triage                 ← classify and hash incoming material
    ↓
large-artifact-strategy     ← handle 1GB+ files, disk images, containers (if triggered)
    ↓
forensic-router             ← route material to the correct path based on triage_notes
    ↓
[domain-specific skills]    ← server / recovery / timeline / competition
    ↓
timeline-reconstruction     ← merge events from multiple sources (if needed)
    ↓
answer-gate                 ← five-step validation
    ↓
report-writer               ← structured output
    ↓
User / Submission
```

## Branching

The chain is not strictly linear. `forensic-router` can branch into multiple paths:

| Material Type | Path |
|---------------|------|
| Server image / VM dump | server-forensics-router → rebuild → domain forensics |
| Remote server access | remote-server-live-response → domain forensics |
| Binary / firmware | firmware-iot-forensics |
| Encrypted container | nas-raid-encrypted-storage |
| Malware sample | malware-forensics |
| Uncommon media | uncommon-media-triage |
| CTF challenge | competition-specific path |

Multiple paths can run in parallel for a single investigation.

## Evidence Flow

The `evidence-ledger` is a **side-channel** that runs throughout the entire chain, not a linear step. Every skill writes to it as it operates; `answer-gate` and `report-writer` read from it at the end.

```
evidence-ledger
├── artifact: <what was examined>
├── source: <where it came from>
├── hash: <integrity verification>
├── command: <what was executed>
├── finding: <what was discovered>
├── confidence: <high/medium/low>
└── next_action: <what to do next>
```

The `answer-gate` reads from the evidence ledger to validate conclusions.

## Handoff Rules

Each skill's SKILL.md must declare:
- **Handoff**: what it passes to the next skill
- **Next Skill**: which skill(s) can follow
- **Stop Conditions**: when to halt and ask for human input

See `templates/skill-template.md` for the full structure.
