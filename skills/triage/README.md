# Triage Skills

First-pass classification, routing, and handling of incoming material.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `file-triage/` | File identification, hash, classification, routing | Implemented (Phase 1) |
| `large-artifact-strategy/` | Handling 1GB+ images, disk dumps, encrypted containers | Implemented (Phase 1) |
| `uncommon-media-triage/` | Evidence-based structure identification for fixed records, CAN/CAN FD-like, NMEA/GPS, TLV, sensors, time series, and custom database pages | Implemented (Phase 3, first module) |

## Relationship to Core

`file-triage` runs before `forensic-router` and produces `material_type`, `hash`, lightweight structural candidates, candidate regions, verified negatives, and `triage_notes`. For 1GB+ material, `large-artifact-strategy` adds bounded samples, signature verification and an offset map before Router makes the final path decision. `uncommon-media-triage` runs only after an evidence-backed Router decision. It may return an executable proprietary candidate through at most one evidence-backed Router re-entry, but it never calls the recovery consumer directly.

## Phase 3 Status

Phase 3 is in progress (2/5). `uncommon-media-triage` and `proprietary-format-recovery` are Implemented. The executable chain is `uncommon-media-triage` → `forensic-router` → `proprietary-format-recovery`; Router remains the only consumer decision point. `firmware-iot-forensics`, `nas-raid-encrypted-storage`, and `malware-forensics` remain Pending and may appear only as non-executable route candidates.

## Migration Source

Phases 1 and 3 of `docs/migration/old-skills-inventory.md`.
