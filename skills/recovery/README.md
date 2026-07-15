# Recovery Skills

Specialized recovery and analysis for uncommon formats, firmware, storage layers, and malware.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `proprietary-format-recovery/` | Bounded proprietary container/layout recovery, finite transform/key/plaintext validation, and verified carving | Implemented (Phase 3, second module) |
| `firmware-iot-forensics/` | Bounded firmware container/filesystem validation, component extraction, and static configuration analysis | Implemented (Phase 3, third module) |
| `nas-raid-encrypted-storage/` | Bounded independent NAS/RAID/volume/encryption topology validation and read-only recovery views | Implemented (Phase 3, fourth module) |
| `malware-forensics/` | Malware static analysis, IOC extraction, YARA | Pending |

## Phase 3 Status

Phase 3 is in progress (4/5). `uncommon-media-triage`, `proprietary-format-recovery`, `firmware-iot-forensics`, and `nas-raid-encrypted-storage` are Implemented. `malware-forensics` remains Pending and may not receive Route Steps or Handoffs.

Router is the only consumer decision point. Storage may enter from file/LAS Evidence or executable candidates produced by uncommon, proprietary, or firmware; upstream Skills never call it directly. Virtualization-bound storage remains in the server cluster chain. Domain consumers return to autopilot by default and may request only their bounded, evidence-backed Router re-entry.

## Migration Source

Phase 3 of `docs/migration/old-skills-inventory.md`.
