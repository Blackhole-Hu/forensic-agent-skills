---
name: server-rebuild-executor
description: Execute server rebuild — convert images, create VM configs, boot system, verify services, and handle failures with recovery strategies.
---

# Server Rebuild Executor

## Purpose

Execute the server rebuild plan: convert disk images to target format, create VM configuration files, boot the system, verify critical services are running, and handle boot failures.

## Use When

- Rebuild plan from server-rebuild-planner is ready
- Need to convert E01/QCOW2/VHDX to VMware/QEMU format
- Server needs to be booted for forensic inspection

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `rebuild_plan` | Yes | From server-rebuild-planner |
| `server_image` | Yes | Source disk image |
| `snapshot_point` | No | When to create recovery snapshot |

## Outputs

| Output | Description |
|--------|-------------|
| `running_vm` | Booted VM ready for inspection |
| `service_status` | Status of critical services |
| `access_method` | How to access the running system |

## Workflow

### Step 1: Image Conversion

```
# E01 → RAW
python e01_convert.py "server.E01"

# RAW → VMDK
qemu-img convert -f raw -O vmdk disk.raw disk.vmdk

# QCOW2 → RAW (if needed)
qemu-img convert -f qcow2 -O raw disk.qcow2 disk.raw

# VHDX → RAW
qemu-img convert -f vhdx -O raw disk.vhdx disk.raw
```

**Evidence**: Record `source_format`, `target_format`, `output_path` in evidence ledger.

### Step 2: VM Creation

For VMware (VMX):
```
.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "10"
scsi0.present = "TRUE"
scsi0:0.present = "TRUE"
scsi0:0.fileName = "disk.vmdk"
memsize = "4096"
guestOS = "other-linux"
```

For QEMU:
```
qemu-system-x86_64 -m 4096 -smp 2 -hda disk.raw -net nic -net user
```

**Evidence**: Record `vm_config_path`, `hypervisor` in evidence ledger.

### Step 3: Boot and Verify

```
# Check boot progress
# Look for login prompt, service start messages
# Verify critical services: nginx, mysql, docker, ssh
```

Handle common boot failures:
- Kernel panic → try different guest OS type
- LVM not found → boot from rescue disk, activate LVM
- Network not up → fix /etc/network/interfaces

**Evidence**: Record `boot_status`, `running_services`, `errors` in evidence ledger.

### Step 4: Access Method

```
SSH:    ssh root@<vm_ip>         # If SSH enabled
Console: Direct VM console       # If no SSH
Web UI: http://<vm_ip>:port      # For panels (宝塔:8888, PVE:8006)
```

**Evidence**: Record `access_method`, `credentials` in evidence ledger.

## Handoff

**Passes to**: `linux-server-forensics`, `webapp-server-forensics`, `database-server-forensics`
**Data available**: Running VM, access method, service status

## Stop Conditions

- VM fails to boot after all recovery attempts
- Required services cannot be started
- Network configuration cannot be restored
- Disk corruption prevents filesystem mounting

## Notes

- Always snapshot before making changes to the running system
- PVE cluster nodes may need Ceph/etcd to start properly
- ESXi images often need /etc/shadow password reset
- 宝塔 panel: `cd /www/server/panel && python3 tools.py panel <new_password>`
