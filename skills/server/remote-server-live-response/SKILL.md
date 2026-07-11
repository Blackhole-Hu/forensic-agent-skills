---
name: remote-server-live-response
description: Live server forensic acquisition via SSH, WebUI, database clients, Docker exec, WinRM, and RDP — memory capture, log collection, and artifact extraction.
---

# Remote Server Live Response

## Purpose

Perform live forensic acquisition on running servers via remote access: capture memory, collect logs, extract configurations, dump databases, and acquire volatile evidence that would be lost in offline analysis.

## Use When

- Server is running and accessible via SSH/WebUI/DB client
- Volatile evidence (memory, active connections, running processes) needs capture
- Offline analysis is insufficient for service-dependent artifacts

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `server_address` | Yes | IP address and access port |
| `access_method` | Yes | SSH / WebUI / DB client / Docker exec / WinRM |
| `credentials` | Yes | Login credentials |
| `target_artifacts` | No | Specific artifacts to collect |

## Outputs

| Output | Description |
|--------|-------------|
| `memory_dump` | RAM capture (if possible) |
| `log_bundle` | Collected log files |
| `config_bundle` | Extracted configurations |
| `process_snapshot` | Running processes and connections |
| `db_dump` | Database export |

## Workflow

### Step 1: Establish Connection

```
SSH:      ssh -o StrictHostKeyChecking=no root@<ip>
WebUI:    curl -k https://<ip>:8888          # 宝塔
DB:       mysql -h <ip> -u root -p            # MySQL
Docker:   docker -H tcp://<ip>:2375 exec <id> # Remote Docker
WinRM:    evil-winrm -i <ip> -u <user> -p <pass>
RDP:      xfreerdp /v:<ip> /u:<user> /p:<pass>
```

**Evidence**: Record `connection_method`, `server_ip`, `login_time` in evidence ledger.

### Step 2: Volatile Evidence Capture

```
# Memory (if LiME available)
ssh root@server "lime-load -o /tmp/mem.lime"

# Running processes
ssh root@server "ps auxf > /tmp/processes.txt"

# Network connections
ssh root@server "ss -tlnp > /tmp/connections.txt"

# Active sessions
ssh root@server "w > /tmp/sessions.txt"
```

**Evidence**: Record `memory_hash`, `process_list`, `network_state` in evidence ledger.

### Step 3: Configuration Extraction

```
# System
ssh root@server "cat /etc/passwd /etc/shadow /etc/hosts /etc/fstab"

# Services
ssh root@server "cat /etc/nginx/nginx.conf"
ssh root@server "cat /etc/mysql/my.cnf"
ssh root@server "cat /etc/redis/redis.conf"

# Docker
ssh root@server "docker inspect $(docker ps -q)"
ssh root@server "docker-compose -f /app/docker-compose.yml config"
```

**Evidence**: Record `config_files`, `service_configs`, `credentials_found` in evidence ledger.

### Step 4: Log Collection

```
ssh root@server "tar czf /tmp/logs.tar.gz /var/log/"
ssh root@server "journalctl --no-pager > /tmp/journal.txt"
```

**Evidence**: Record `log_files`, `log_size`, `time_range` in evidence ledger.

### Step 5: Database Dump

```
ssh root@server "mysqldump --all-databases > /tmp/all_db.sql"
ssh root@server "pg_dumpall > /tmp/pg_all.sql"
ssh root@server "redis-cli BGSAVE && cp /var/lib/dump.rdb /tmp/"
```

**Evidence**: Record `db_type`, `db_dump_hash`, `table_count` in evidence ledger.

## Handoff

**Passes to**: `linux-server-forensics` (for system analysis), `database-server-forensics` (for DB analysis)
**Data available**: Memory dump, logs, configs, database dumps, process snapshots

## Stop Conditions

- SSH access denied or key-based auth required
- Memory capture fails (insufficient permissions, no LiME)
- Server becomes unresponsive during acquisition

## Notes

- Capture volatile evidence first (memory, processes, connections) before static
- Database dumps are often the most valuable evidence
- Docker environment variables frequently contain passwords and API keys
- 宝塔 panel default port: 8888, admin path: /bt/
