# Server Forensics Skills

Complete server forensic chain: rebuild, live response, domain-specific analysis, and timeline.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `server-forensics-router/` | Server forensics entry, mode selection | Pending (Phase 2) |
| `server-rebuild-planner/` | Rebuild planning (VMware/QEMU/Docker) | Pending |
| `server-rebuild-executor/` | Rebuild execution (needs-refactor) | Pending |
| `remote-server-live-response/` | Live server acquisition via SSH/Docker/WinRM/RDP | Pending |
| `linux-server-forensics/` | Linux system-level forensics | Pending |
| `webapp-server-forensics/` | Web/API forensics (Nginx/Apache/PHP/Node) | Pending |
| `database-server-forensics/` | Database forensics (MySQL/Redis/PostgreSQL/MongoDB) | Pending |
| `docker-container-forensics/` | Docker container forensics | Pending |
| `cluster-virtualization-forensics/` | PVE/Ceph/LVM/RAID/ZFS/cluster forensics | Pending |

## Chain

```
server-forensics-router
  → server-rebuild-planner → server-rebuild-executor
  → remote-server-live-response
  → [domain-specific forensics]
  → timeline-reconstruction → answer-gate
```

## Migration Source

Phase 2 of `docs/migration/old-skills-inventory.md`.
