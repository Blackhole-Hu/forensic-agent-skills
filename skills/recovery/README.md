# Recovery Skills

Specialized recovery and analysis for uncommon formats, firmware, storage layers, and malware.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `proprietary-format-recovery/` | Bounded proprietary container/layout recovery, finite transform/key/plaintext validation, and verified carving | Implemented (Phase 3, second module) |
| `firmware-iot-forensics/` | IoT/embedded firmware static analysis | Pending |
| `nas-raid-encrypted-storage/` | NAS/RAID/LVM/encryption layer identification | Pending |
| `malware-forensics/` | Malware static analysis, IOC extraction, YARA | Pending |

## Phase 3 Status

Phase 3 is in progress (2/5). `uncommon-media-triage` and `proprietary-format-recovery` are Implemented. `firmware-iot-forensics`, `nas-raid-encrypted-storage`, and `malware-forensics` remain Pending and may not receive Route Steps or Handoffs.

The executable recovery chain is `uncommon-media-triage` → `forensic-router` → `proprietary-format-recovery`. Router is the only consumer decision point; proprietary recovery returns to autopilot by default and may request at most one evidence-backed Router re-entry.

## Migration Source

Phase 3 of `docs/migration/old-skills-inventory.md`.
