# Triage Skills

First-pass classification, routing, and handling of incoming material.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `file-triage/` | File identification, hash, classification, routing | Implemented (Phase 1) |
| `large-artifact-strategy/` | Handling 1GB+ images, disk dumps, encrypted containers | Implemented (Phase 1) |
| `uncommon-media-triage/` | Evidence-based structure identification for fixed records, CAN/CAN FD-like, NMEA/GPS, TLV, sensors, time series, and custom database pages | Implemented (Phase 3, first module) |

## Relationship to Core

`file-triage` runs before `forensic-router` and produces `material_type`, `hash`, lightweight structural candidates, candidate regions, verified negatives, and `triage_notes`. For 1GB+ material, `large-artifact-strategy` adds bounded samples, signature verification and an offset map before Router makes the final path decision. `uncommon-media-triage` runs only after an evidence-backed Router decision and returns its assessments to `forensic-autopilot`, with at most one evidence-backed Router re-entry.

## Phase 3 Status

`uncommon-media-triage` is the first implemented Phase 3 module. The four Recovery skills — `proprietary-format-recovery`, `firmware-iot-forensics`, `nas-raid-encrypted-storage`, and `malware-forensics` — remain Pending. They may appear only as non-executable route candidates until their own migrations are complete.

## Migration Source

Phases 1 and 3 of `docs/migration/old-skills-inventory.md`.
