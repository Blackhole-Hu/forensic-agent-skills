---
name: server-forensics-router
description: Server forensics entry point — identify virtualization platform, select analysis mode (rebuild/live/offline/hybrid), and route to appropriate server forensic skills.
---

# Server Forensics Router

## Purpose

Route server forensic evidence to the correct analysis path by identifying the virtualization platform, server role, and selecting the optimal analysis mode.

## Use When

- Server disk image (E01/VMDK/QCOW2) is present
- Virtualization platform needs identification
- Need to decide between rebuild, live response, or offline analysis

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `server_image` | Yes | Server disk image (E01/VMDK/QCOW2/VHDX) |
| `cluster_count` | No | Number of servers in cluster (default: 1) |

## Outputs

| Output | Description |
|--------|-------------|
| `platform_type` | ESXi / Hyper-V / KVM-QEMU / Docker / Bare-metal |
| `analysis_mode` | rebuild-and-connect / remote-live / offline-image / hybrid-cluster |
| `server_role` | Web / Database / Cache / Proxy / Combined |

## Workflow

### Step 1: Platform Identification

```
mmls server.E01                                    # Partition layout
fls -o $OFFSET -r server.E01 | rg "vmdk|vmx"      # → ESXi
fls -o $OFFSET -r server.E01 | rg "vhdx|avhdx"    # → Hyper-V
fls -o $OFFSET -r server.E01 | rg "qcow2|libvirt" # → KVM/QEMU
fls -o $OFFSET -r server.E01 | rg "docker|overlay2" # → Docker
```

**Evidence**: Record `platform`, `version`, `config_files` in evidence ledger.

### Step 2: Server Role Detection

```
fls -o $OFFSET -r server.E01 | rg "nginx|apache|tomcat"   # → Web
fls -o $OFFSET -r server.E01 | rg "mysql|redis|mongo"     # → Database
fls -o $OFFSET -r server.E01 | rg "docker-compose"        # → Containerized
fls -o $OFFSET -r server.E01 | rg "corosync|pacemaker"    # → HA Cluster
```

**Evidence**: Record `server_role`, `installed_services` in evidence ledger.

### Step 3: Mode Selection

| Condition | Mode | Next Skill |
|-----------|------|------------|
| Need GUI inspection, complex services | `rebuild-and-connect` | `server-rebuild-planner` |
| SSH/service access available | `remote-live` | `remote-server-live-response` |
| Static file analysis sufficient | `offline-image` | `disk-forensics` |
| Multi-node cluster | `hybrid-cluster` | `cluster-virtualization-forensics` |

**Evidence**: Record `selected_mode`, `rationale` in evidence ledger.

## Handoff

**Passes to**: `server-rebuild-planner`, `remote-server-live-response`, `disk-forensics`, `cluster-virtualization-forensics`
**Data available**: Platform type, server role, analysis mode

## Stop Conditions

- Platform cannot be identified from image
- Image is too corrupted for any analysis method

## Notes

- Emulation-first principle: servers with complex services need emulation, not static parsing
- LVM + Ceph + network = must emulate, cannot parse offline
- For single-node servers, offline analysis may suffice
- For clusters, always try to bring up all nodes together
