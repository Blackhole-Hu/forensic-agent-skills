# Triage Skills

First-pass classification, routing, and handling of incoming material.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `file-triage/` | File identification, hash, classification, routing | Draft |
| `large-artifact-strategy/` | Handling 1GB+ images, disk dumps, encrypted containers | Draft |
| `uncommon-media-triage/` | Structure-based routing for CAN/NMEA/GPS/TLV/sensor data | Pending (Phase 3) |

## Relationship to Core

Triage skills are called by `forensic-autopilot` early in the chain, before `forensic-router`. `file-triage` produces `material_type`, `hash`, and `triage_notes`; `forensic-router` then uses `triage_notes` to make the final path decision.

## Migration Source

Phases 1 and 3 of `docs/migration/old-skills-inventory.md`.
