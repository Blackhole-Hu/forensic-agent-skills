---
name: cluster-virtualization-forensics
description: Cluster and virtualization platform forensics — PVE/ESXi cluster analysis, Ceph/LVM storage, RAID reconstruction, vSAN, and multi-node server correlation.
---

# Cluster & Virtualization Forensics

## Purpose

Analyze clustered server environments: Proxmox VE (PVE), ESXi clusters, Ceph storage, LVM/RAID/ZFS volumes, vSAN, and multi-node server architectures. Reconstruct cluster topology and extract evidence from distributed storage.

## Use When

- PVE/ESXi cluster with multiple nodes needs analysis
- Ceph/LVM/RAID/ZFS storage needs reconstruction
- vSAN cluster with distributed storage
- Multi-node architecture needs topology mapping

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `cluster_images` | Yes | List of server disk images (one per node) |
| `storage_type` | No | ceph / lvm / raid / zfs / vsan (auto-detect if omitted) |

## Outputs

| Output | Description |
|--------|-------------|
| `cluster_topology` | Node roles, network planes, service distribution |
| `storage_config` | Storage pool configuration and mounts |
| `vm_inventory` | List of virtual machines across all nodes |
| `reconstructed_data` | Data recovered from distributed storage |

## Workflow

### Step 1: Cluster Role Identification

```
# For each server image, identify role:
fls -o $OFFSET -r server.E01 | rg "corosync|pacemaker"    # HA cluster
fls -o $OFFSET -r server.E01 | rg "pve|proxmox"           # PVE cluster
fls -o $OFFSET -r server.E01 | rg "esxcli|vmware"         # ESXi cluster
fls -o $OFFSET -r server.E01 | rg "ceph|osd|mon"          # Ceph storage
fls -o $OFFSET -r server.E01 | rg "kubernetes|k8s|etcd"   # K8s cluster
```

**Evidence**: Record `node_roles`, `cluster_name`, `node_count` in evidence ledger.

### Step 2: PVE Cluster Recovery

```
# 1. Build VMs for each node, mount disk01 (system) + disk02 (Ceph)
# 2. Fix network: /etc/network/interfaces (ens36 → vmbr0)
# 3. Assign old IPs: ip addr add <old_ip>/24 dev vmbr0
# 4. Start Ceph: ceph-mon, ceph-osd
# 5. Start VMs: qm start 100 --memory 1024 --cores 1 --kvm 0
# 6. Export RBD: qemu-nbd → mount LVM
```

**Evidence**: Record `pve_version`, `cluster_config`, `vm_list` in evidence ledger.

### Step 3: Storage Reconstruction

```
# LVM
pvs; vgs; lvs                  # List physical/logical volumes
vgchange -ay                    # Activate volume groups

# RAID
mdadm --assemble --scan         # Auto-assemble RAID arrays
mdadm --detail /dev/md0

# ZFS
zpool import                    # Import ZFS pools
zfs list

# Ceph
ceph osd tree                   # OSD topology
ceph health detail              # Cluster health
```

**Evidence**: Record `storage_topology`, `volume_list`, `raid_level` in evidence ledger.

### Step 4: vSAN Analysis (if applicable)

```
vSAN architecture per ESXi node:
  Disk 1: System (VMFSOS)
  Disk 2: Cache (vSAN Cache)
  Disk 3: Data (vSAN Data)

Network planes:
  Management: 192.168.x.0/24
  vSAN:       192.168.y.0/24
  vMotion:    192.168.z.0/24

Key info: cluster name, disk groups, VM count, license key
```

**Evidence**: Record `vsan_config`, `disk_groups`, `network_planes` in evidence ledger.

### Step 5: VM Inventory and Data Extraction

```
# PVE
qm list                         # List VMs
qm config <vmid>                # VM config

# ESXi
vim-cmd vmsvc/getallvms         # List VMs
vim-cmd vmsvc/get.summary <id>  # VM details

# K8s
kubectl get pods -A             # List all pods
kubectl get secrets -A          # Extract secrets
```

**Evidence**: Record `vm_inventory`, `vm_configs`, `secrets` in evidence ledger.

## Handoff

**Passes to**: `database-server-forensics` (for DB in VMs), `answer-gate` (for conclusions)
**Data available**: Cluster topology, storage config, VM inventory, extracted data

## Notes

- PVE cluster recovery: corosync.conf contains cluster name and node list
- Ceph: all nodes must be online for full data access
- vSAN: 3 NICs required (Management, vSAN, vMotion) — configure carefully
- LVM: activate with `vgchange -ay` before mounting
- RAID: mdadm requires all member disks — use XOR recovery for missing disk
- Always emulate server clusters — static parsing cannot handle distributed storage
