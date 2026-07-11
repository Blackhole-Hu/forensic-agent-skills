---
name: docker-container-forensics
description: Docker container forensics — container inspection, image layer analysis, environment variable extraction, log analysis, and compose configuration review.
---

# Docker Container Forensics

## Purpose

Analyze Docker containers and images for forensic evidence: inspect container configurations, analyze image layers, extract environment variables (often contain secrets), review container logs, and examine docker-compose configurations.

## Use When

- Docker containers are present in server evidence
- Container environment variables need extraction
- Image layer analysis is needed for hidden data
- Docker-compose configuration reveals service architecture

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `docker_root` | Yes | Docker data directory (/var/lib/docker/) or running Docker host |
| `target_container` | No | Specific container ID or name |

## Outputs

| Output | Description |
|--------|-------------|
| `container_configs` | Container configurations with env vars |
| `image_layers` | Filesystem changes per image layer |
| `container_logs` | Container stdout/stderr logs |
| `compose_config` | Docker-compose service definitions |

## Workflow

### Step 1: Container Discovery

```
# List all containers (running + stopped)
docker ps -a --no-trunc

# List all images
docker images --no-trunc

# From disk image
fls -o $OFFSET -r server.E01 | rg "docker|container"
fls -o $OFFSET -r server.E01 | rg "overlay2"
```

**Evidence**: Record `container_list`, `image_list`, `docker_version` in evidence ledger.

### Step 2: Configuration Inspection

```
# Full container config (contains env vars with passwords)
docker inspect <container_id> | python3 -m json.tool

# Environment variables — frequently contain secrets
docker inspect <container_id> --format '{{.Config.Env}}'

# From disk: extract config.v2.json
icat -o $OFFSET server.E01 <inode> | python3 -m json.tool
```

Focus on: `Env` array (DB_PASSWORD, API_KEY, SECRET_KEY, MYSQL_ROOT_PASSWORD).

**Evidence**: Record `env_variables`, `secrets_found`, `port_mappings` in evidence ledger.

### Step 3: Image Layer Analysis

```
# Image history (shows build steps, ARG/ENV values)
docker history <image_id> --no-trunc

# Each layer contains filesystem changes
# /var/lib/docker/overlay2/<id>/diff/
# Deleted files may still exist in earlier layers
```

**Evidence**: Record `build_history`, `layer_changes`, `hidden_files` in evidence ledger.

### Step 4: Log Collection

```
# Container logs
docker logs <container_id> 2>&1 > container_logs.txt

# Log files on disk
ls /var/lib/docker/containers/<id>/
cat /var/lib/docker/containers/<id>/<id>-json.log
```

**Evidence**: Record `log_entries`, `error_messages`, `access_patterns` in evidence ledger.

### Step 5: Compose Analysis

```
# Find docker-compose files
find / -name "docker-compose*.yml" -o -name "docker-compose*.yaml"

# Read compose config
cat docker-compose.yml | python3 -m json.tool

# Extract service dependencies, networks, volumes, secrets
```

**Evidence**: Record `service_topology`, `network_config`, `volume_mounts`, `compose_secrets` in evidence ledger.

## Handoff

**Passes to**: `linux-server-forensics` (for host analysis), `database-server-forensics` (for DB containers)
**Data available**: Container configs, environment secrets, image layers, compose topology

## Notes

- Docker environment variables are the #1 source of hardcoded passwords
- `docker history --no-trunc` reveals ARG/ENV values from build time
- Overlay2 layers: deleted files in later layers still exist in earlier layers
- docker-compose.yml often reveals full service architecture (Web + DB + Cache)
- Container logs in /var/lib/docker/containers/<id>/ contain all stdout/stderr
