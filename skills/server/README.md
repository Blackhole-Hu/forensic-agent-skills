# Server Forensics Skills

Phase 2 server forensic chain under active migration.

See `docs/data-contracts.md` for unified request/response contracts and `templates/` for JSON schemas.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `server-forensics-router/` | Server forensics entry, mode selection | Completed |
| `server-rebuild-planner/` | Rebuild planning (feasibility, backend, recovery policy) | Completed |
| `server-rebuild-executor/` | Rebuild execution (Stage 0-6) | Completed |
| `remote-server-live-response/` | Live server acquisition via SSH/Docker/WinRM/RDP | Completed |
| `linux-server-forensics/` | Linux system-level forensics | Completed |
| `webapp-server-forensics/` | Web/API forensics (Nginx/Apache/PHP/Node) | Completed |
| `database-server-forensics/` | Database forensics (MySQL/Redis/PostgreSQL/MongoDB) | Completed |
| `docker-container-forensics/` | Docker container forensics | Pending |
| `cluster-virtualization-forensics/` | PVE/Ceph/virtualization topology and storage mapping | Pending |
| `timeline-reconstruction/` | Multi-source event timeline reconstruction | Pending (in `skills/timeline/`) |

## Chain

```
forensic-autopilot
  → forensic-router → server-forensics-router
    → rebuild-and-connect: server-rebuild-planner → server-rebuild-executor
    → remote-live: remote-server-live-response
    → offline-image: domain skills
    → hybrid-cluster: cluster-virtualization-forensics → rebuild
  → domain-specific skills (linux / webapp / database / docker)
  → timeline-reconstruction → answer-gate
```

## Contracts

All skills use the unified `request-envelope.schema.json` and `response-envelope.schema.json`. Route information is maintained only in `route_record`.

## Migration Source

Phase 2 of `docs/migration/old-skills-inventory.md`.
