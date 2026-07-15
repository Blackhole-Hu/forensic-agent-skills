# Triage Skills

First-pass classification, routing, and handling of incoming material.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `file-triage/` | File identification, hash, classification, routing | Implemented (Phase 1) |
| `large-artifact-strategy/` | Handling 1GB+ images, disk dumps, encrypted containers | Implemented (Phase 1) |
| `uncommon-media-triage/` | Evidence-based structure identification for fixed records, CAN/CAN FD-like, NMEA/GPS, TLV, sensors, time series, and custom database pages | Implemented (Phase 3, first module) |

## Relationship to Core

`file-triage` runs before `forensic-router` and produces `material_type`, `hash`, lightweight structural candidates, candidate regions, verified negatives, and `triage_notes`. For 1GB+ material, `large-artifact-strategy` adds bounded samples, signature verification and an offset map before Router makes the final path decision; LAS only supplies bounded regions, member candidates, signatures and Evidence, and never decides or calls firmware or storage. `uncommon-media-triage` runs only after an evidence-backed Router decision. It may return an executable proprietary, firmware, or independent-storage candidate through at most one evidence-backed Router re-entry, but it never calls a recovery consumer directly.

## Phase 3 Status

Phase 3 is in progress (4/5). `uncommon-media-triage`, `proprietary-format-recovery`, `firmware-iot-forensics`, and `nas-raid-encrypted-storage` are Implemented. Router remains the only consumer decision point. Independent storage may be selected after file/LAS Evidence or an executable uncommon, proprietary, or firmware candidate; PVE/Ceph/VM/container/snapshot storage stays in the server cluster chain. `malware-forensics` remains Pending and may appear only as a non-executable route candidate.

## Migration Source

Phases 1 and 3 of `docs/migration/old-skills-inventory.md`.
