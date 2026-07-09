# Timeline Skills

Multi-source event timeline reconstruction.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `timeline-reconstruction/` | Merge events from server logs, PCAP, file timestamps, browser history, DB records, container logs | Draft (Phase 1/2) |

## Design Principle

Timeline-reconstruction is a **generic** skill, not server-specific. Server logs are the first source type; the skill expands to accept PCAP, file timestamps, browser history, database records, and container logs as additional sources.

## Migration Source

`server-timeline-reconstruction` from Phase 2, generalized.
