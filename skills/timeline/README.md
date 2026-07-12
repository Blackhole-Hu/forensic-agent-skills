# Timeline Skills

Phase 2 server-scoped event timeline reconstruction.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `timeline-reconstruction/` | Phase 2 server scope: merge Linux, Web, Database, Docker, PVE, Ceph, cluster/virtualization, and file-time events | Completed |

`Completed` refers to the Phase 2 server-forensics scope described above.

## Design Principle

Timeline-reconstruction uses a generic architecture that can support future source families, but the current completed implementation is limited to the Phase 2 server scope: Linux, Web, Database, Docker, PVE, Ceph, cluster/virtualization, and file-time events.

PCAP, browser history, mobile-device, and other non-server sources are not implemented in this phase and must not be treated as currently supported inputs.

## Migration Source

`server-timeline-reconstruction` from Phase 2, generalized.
