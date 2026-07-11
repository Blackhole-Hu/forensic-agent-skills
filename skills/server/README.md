# Server Forensics Skills

Complete server forensic chain: rebuild, live response, domain-specific analysis, and timeline.

## Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `server-forensics-router/` | Server forensics entry, mode selection | Draft |
| `server-rebuild-planner/` | Rebuild planning (VMware/QEMU/Docker) | Draft |
| `server-rebuild-executor/` | Rebuild execution (needs-refactor) | Draft |
| `remote-server-live-response/` | Live server acquisition via SSH/Docker/WinRM/RDP | Draft |
| `linux-server-forensics/` | Linux system-level forensics | Draft |
| `webapp-server-forensics/` | Web/API forensics (Nginx/Apache/PHP/Node) | Draft |
| `database-server-forensics/` | Database forensics (MySQL/Redis/PostgreSQL/MongoDB) | Draft |
| `docker-container-forensics/` | Docker container forensics | Draft |
| `cluster-virtualization-forensics/` | PVE/Ceph/LVM/RAID/ZFS/cluster forensics | Draft |

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
