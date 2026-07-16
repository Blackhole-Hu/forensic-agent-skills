# Recovery Skills

Specialized recovery and analysis for uncommon formats, firmware, storage layers, and malware.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `proprietary-format-recovery/` | Bounded proprietary container/layout recovery, finite transform/key/plaintext validation, and verified carving | Implemented (Phase 3, second module) |
| `firmware-iot-forensics/` | Bounded firmware container/filesystem validation, component extraction, and static configuration analysis | Implemented (Phase 3, third module) |
| `nas-raid-encrypted-storage/` | Bounded independent NAS/RAID/volume/encryption topology validation and read-only recovery views | Implemented (Phase 3, fourth module) |
| `malware-forensics/` | Static-first sample characterization, evidence-backed capability/behavior hypotheses, and gated dynamic observation | Implemented (Phase 3, fifth module) |

## Phase 3 Status

Phase 3 is complete (5/5). `uncommon-media-triage`, `proprietary-format-recovery`, `firmware-iot-forensics`, `nas-raid-encrypted-storage`, and `malware-forensics` are Implemented.

Router is the only consumer decision point. Upstream Skills form evidence-backed candidates and never call a recovery consumer directly. Ordinary executables do not enter malware analysis without an explicit objective or independent suspicious context; sample execution remains gated. Domain consumers return to autopilot by default and may request only their bounded, evidence-backed Router re-entry.

## Migration Source

Phase 3 of `docs/migration/old-skills-inventory.md`.
