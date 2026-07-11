---
name: server-rebuild-planner
description: Plan server rebuild strategy — select virtualization platform (VMware/QEMU/VirtualBox/Docker), configure network, plan rollback, and estimate resources.
---

# Server Rebuild Planner

## Purpose

Plan the rebuild strategy for server forensic images: select target hypervisor, configure hardware parameters, plan network topology, and prepare rollback strategy.

## Use When

- Server needs to be emulated for forensic analysis
- Need to select between VMware/QEMU/VirtualBox/Docker
- Complex service dependencies require running system

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `server_image` | Yes | Server disk image |
| `platform_type` | Yes | From server-forensics-router |
| `target_hypervisor` | No | VMware/QEMU/VirtualBox (auto-select if omitted) |

## Outputs

| Output | Description |
|--------|-------------|
| `rebuild_plan` | Step-by-step rebuild instructions |
| `vm_config` | Generated VM configuration |
| `network_config` | Network topology configuration |
| `resource_estimate` | CPU/RAM/disk requirements |

## Workflow

### Step 1: Hypervisor Selection

| Platform | Best For | Config |
|----------|----------|--------|
| VMware | ESXi/VMDK images, complex multi-NIC | VMX file |
| QEMU | QCOW2/RAW, KVM native, CLI automation | qemu-system command |
| Docker | Container-based services | docker-compose.yml |
| FireEye | Quick GUI inspection, single-click | Built-in |

**Evidence**: Record `selected_hypervisor`, `rationale` in evidence ledger.

### Step 2: Hardware Configuration

```
CPU: Match original core count (or 2 minimum)
RAM: 4GB minimum, 8-16GB for vSAN/database servers
Disk: SCSI mode for server images, attach as primary boot
Network: NAT for safe isolation, Bridge for network-dependent services
```

For vSAN clusters: 3 NICs (Management, vSAN, vMotion), 3 disks per node.

**Evidence**: Record `cpu`, `ram`, `disk_config`, `network_config` in evidence ledger.

### Step 3: Network Planning

```
Safe: NAT mode — isolated, no external access
Bridge: Direct network access — use only if required
Host-Only: Host↔VM only — safest for forensic work
```

**Evidence**: Record `network_mode`, `ip_assignments` in evidence ledger.

### Step 4: Rollback Strategy

Always create snapshots before making changes:
```
VMware: snapshot before first login
QEMU: qemu-img snapshot -c baseline disk.qcow2
```

**Evidence**: Record `snapshot_name`, `rollback_plan` in evidence ledger.

## Handoff

**Passes to**: `server-rebuild-executor`
**Data available**: Rebuild plan, VM config, network config, resource estimate

## Notes

- FireEye simulate is fastest for single-click boot
- For ESXi images: convert VMDK to VMware format first
- QCOW2 backing chain must be preserved during rebuild
- Always isolate forensic VMs from production networks
