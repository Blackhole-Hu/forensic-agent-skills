# Triage Skills

First-pass classification, routing, and handling of incoming material.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `file-triage/` | File identification, hash, classification, routing | Implemented (Phase 1) |
| `large-artifact-strategy/` | Handling 1GB+ images, disk dumps, encrypted containers | Implemented (Phase 1) |
| `uncommon-media-triage/` | Evidence-based structure identification for fixed records, CAN/CAN FD-like, NMEA/GPS, TLV, sensors, time series, and custom database pages | Implemented (Phase 3, first module) |

## Relationship to Core

`file-triage` runs before `forensic-router` and produces `material_type`, `hash`, lightweight structural candidates, candidate regions, verified negatives, and `triage_notes`. For 1GB+ material, `large-artifact-strategy` adds bounded samples, signature verification and an offset map before Router makes the final path decision; LAS only supplies bounded regions, signatures and Evidence, and never decides or calls the firmware consumer. `uncommon-media-triage` runs only after an evidence-backed Router decision. It may return an executable proprietary or firmware candidate through at most one evidence-backed Router re-entry, but it never calls either recovery consumer directly.

## Phase 3 Status

Phase 3 is in progress (3/5). `uncommon-media-triage`, `proprietary-format-recovery`, and `firmware-iot-forensics` are Implemented. Router remains the only consumer decision point. Firmware may be selected directly after file/LAS Evidence, after uncommon Router re-entry, or after proprietary produces a verified nested firmware Artifact and returns to Router. `nas-raid-encrypted-storage` and `malware-forensics` remain Pending and may appear only as non-executable route candidates.

## Migration Source

Phases 1 and 3 of `docs/migration/old-skills-inventory.md`.
