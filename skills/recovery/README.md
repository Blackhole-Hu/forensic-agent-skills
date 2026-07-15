# Recovery Skills

Specialized recovery and analysis for uncommon formats, firmware, storage layers, and malware.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `proprietary-format-recovery/` | Bounded proprietary container/layout recovery, finite transform/key/plaintext validation, and verified carving | Implemented (Phase 3, second module) |
| `firmware-iot-forensics/` | Bounded firmware container/filesystem validation, component extraction, and static configuration analysis | Implemented (Phase 3, third module) |
| `nas-raid-encrypted-storage/` | NAS/RAID/LVM/encryption layer identification | Pending |
| `malware-forensics/` | Malware static analysis, IOC extraction, YARA | Pending |

## Phase 3 Status

Phase 3 is in progress (3/5). `uncommon-media-triage`, `proprietary-format-recovery`, and `firmware-iot-forensics` are Implemented. `nas-raid-encrypted-storage` and `malware-forensics` remain Pending and may not receive Route Steps or Handoffs.

Router is the only consumer decision point. Executable firmware routes are `file-triage` / `large-artifact-strategy` → `forensic-router` → `firmware-iot-forensics`, `uncommon-media-triage` → `forensic-router` → `firmware-iot-forensics`, and `uncommon-media-triage` → `forensic-router` → `proprietary-format-recovery` → `forensic-router` → `firmware-iot-forensics`. Domain consumers return to autopilot by default and may request only their bounded, evidence-backed Router re-entry.

## Migration Source

Phase 3 of `docs/migration/old-skills-inventory.md`.
