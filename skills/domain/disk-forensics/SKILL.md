---
name: disk-forensics
description: Disk image analysis, filesystem forensics, deleted file recovery, partition analysis, memory imaging, and timeline reconstruction using Sleuth Kit and related tools.
---

# Disk Forensics

## Purpose

Analyze disk images (E01, RAW, VMDK) to extract evidence: enumerate partitions, traverse filesystems, recover deleted files, extract artifacts from known evidence locations, and build file timelines.

## Use When

- Disk image (E01/RAW/DD/VMDK) is present in evidence
- Filesystem analysis is required (NTFS/EXT4/FAT/APFS)
- Deleted file recovery is needed
- Registry/SAM/Event Log extraction is required

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `disk_image` | Yes | Path to E01/RAW/DD/VMDK disk image |
| `offset` | No | Partition offset in sectors (from mmls) |
| `target_files` | No | Specific files or patterns to search for |

## Outputs

| Output | Description |
|--------|-------------|
| `partition_layout` | Partition table with offsets and types |
| `file_listing` | Complete recursive file listing |
| `deleted_files` | Recoverable deleted files |
| `artifacts` | Extracted evidence files (registry, logs, browser data) |
| `timeline` | MAC time timeline of file operations |

## Workflow

### Step 1: E01 Access Strategy

Choose access method based on image type:
- **NTFS/EXT4 system disk**: Mount with AIM → drive letter available → all tools work
- **Raw flash / phone image**: Use `dissect.ewf` Python library for direct read
- **Need full tool access but no drive letter**: Convert E01 to RAW via `aim_cli`

**Evidence**: Record `access_method`, `drive_letter_or_path` in evidence ledger.

### Step 2: Partition Discovery

```
mmls disk.E01                    # List partitions
mmls -t dos disk.E01             # Force MBR
mmls -t gpt disk.E01             # Force GPT
```

Record partition offsets. Typical: offset 2048 for first partition.

**Evidence**: Record `partition_count`, `offsets`, `filesystem_types` in evidence ledger.

### Step 3: Filesystem Traversal (TSK Trilogy)

```
OFFSET=2048
fsstat -o $OFFSET disk.E01       # Filesystem details
fls -o $OFFSET -r -p disk.E01    # Full recursive listing
fls -o $OFFSET -d -r disk.E01    # Deleted files only
```

**Evidence**: Record `filesystem_type`, `total_files`, `deleted_files` in evidence ledger.

### Step 4: Artifact Extraction

Priority locations by platform:

**Windows**: `/Users/*/AppData/`, `/$Recycle.Bin/`, `/Windows/System32/winevt/Logs/`, `/Windows/Prefetch/`, Registry hives (SAM, SYSTEM, NTUSER.DAT)

**Linux**: `.bash_history`, `/var/log/auth.log`, `.ssh/`, crontabs, `/etc/passwd`

```
icat -o $OFFSET disk.E01 $INODE > extracted_file
blkls -o $OFFSET disk.E01 | strings | rg -i "flag|password"
tsk_recover -e -o $OFFSET disk.E01 ./recovered/
```

**Evidence**: Record `artifact_path`, `inode`, `hash`, `content_summary` in evidence ledger.

### Step 5: Timeline Construction

```
fls -o $OFFSET -r -m / disk.E01 > bodyfile.txt
mactime -b bodyfile.txt -d > timeline.csv
```

Analyze for: suspicious file modifications, access patterns, anti-forensics traces (cipher.exe EFSTMPWP, log clearing).

**Evidence**: Record `timeline_events`, `suspicious_patterns` in evidence ledger.

### Step 6: Supplementary Analysis

- **NTFS ADS**: `fls -r disk.E01 | grep ":"`
- **USN Journal**: `$Extend\$J` — survives log clearing
- **Registry**: `impacket secretsdump` for SAM hashes
- **Browser data**: sqlite3 on History/Login Data databases
- **Memory**: Volatility if memory dump available

**Evidence**: Record `supplementary_findings` in evidence ledger.

## Evidence Requirements

| Field | When to Record | Example |
|-------|---------------|---------|
| `image_info` | Step 1 | E01, 40GB, NTFS, offset 2048 |
| `partition` | Step 2 | Slot 00: NTFS, sectors 2048-206847 |
| `file_count` | Step 3 | 45,231 files, 127 deleted |
| `artifact` | Step 4 | /Users/admin/Desktop/secret.txt |
| `hash` | Step 4 | sha256:abc123... |
| `timeline_event` | Step 5 | 2026-01-15 14:23 - file modified |

## Handoff

**Passes to**: `timeline-reconstruction` (for cross-source correlation), `answer-gate` (for conclusions)
**Data available**: Partition layout, file listings, extracted artifacts, MAC timeline

## Stop Conditions

- Image is encrypted (BitLocker/VeraCrypt/LUKS) and no key/recovery available
- Image is severely corrupted and unreadable
- Partition offset cannot be determined
- Required operation needs administrator privileges not available

## Notes

- `mmls` → `fsstat` → `fls` is the fixed three-step sequence
- Unallocated space is the most common flag hiding location
- `strings` directly on image is faster than `fls` for initial discovery
- FAT uses local timezone, NTFS uses UTC — watch for timezone issues
- For VMDK: `7z l disk.vmdk` works without mounting
- VMware snapshots: `vmss2core` converts to memory dump for Volatility
