---
name: forensic-router
description: 任务/材料路由器。根据检材类型、文件结构、题面线索，判断检材应进入哪条分析路径（server、recovery、timeline、competition 等）。
disable-model-invocation: false
---

# forensic-router

## Purpose

forensic-router 是材料级路由器。接收 triage 结论和检材信息，判断应进入哪条分析路径。它是 forensic-autopilot 和具体专项 skill 之间的决策层。

本 skill 从 `competition-autopilot` 的路由逻辑和 `server-forensics-router` 的模式选择中提取，不保留 `ask-matt` 名称。

## Use When

- forensic-autopilot 完成 intake、tool precheck 和 file-triage 后，需要决定分析路径
- forensic-router consumes `triage_notes` from file-triage to make the final path decision
- 多种材料类型混合时，需要分配多条并行路径

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `material_info` | Yes | 检材类型、大小、文件结构（来自 file-triage） |
| `objective` | Yes | 分析目标 |
| `triage_notes` | Recommended | file-triage 的分类结论 |

## Outputs

| Output | Description |
|--------|-------------|
| `route_decision` | 路由决策：进入哪条路径 |
| `route_basis` | 路由依据（文件类型、结构、线索） |
| `parallel_paths` | 如有多个路径，列出并行路径 |

## Workflow

### Step 1: Analyze Material

读取 material_info 和 triage_notes，识别：
- 文件类型（镜像、压缩包、二进制、文档、PCAP、固件等）
- 文件系统类型（NTFS、EXT4、SquashFS 等）
- 线索（配置文件、日志、凭据、服务器特征）

**Evidence**: 记录分析依据

### Step 2: Determine Primary Route

| Material Type | Route |
|---------------|-------|
| 服务器镜像 (E01/VHD/VMDK/qcow2/raw) | `server-forensics-router` |
| 远程服务器入口 (SSH/RDP/WinRM/WebUI) | `remote-server-live-response` |
| Docker/compose 配置 | `docker-container-forensics` |
| 数据库文件 (MySQL/Redis/PostgreSQL) | `database-server-forensics` |
| Web 应用源码/配置 | `webapp-server-forensics` |
| 固件/IoT/嵌入式 | `firmware-iot-forensics` |
| 加密容器/RAID/LVM | `nas-raid-encrypted-storage` |
| PE/ELF/恶意脚本 | `malware-forensics` |
| 非常见二进制格式 | `uncommon-media-triage` |
| PCAP/网络流量 | `timeline-reconstruction` |
| 混合类型 | 多路径并行 |

**Evidence**: 记录路由决策和依据

### Step 3: Check Parallel Paths

如检材包含多种类型（如服务器镜像 + Web 源码 + 数据库），分配并行路径。

**Evidence**: 记录并行路径列表

### Step 4: Handoff

将路由决策传递给 forensic-autopilot，由 autopilot 调用对应的专项 skill。

## Evidence Requirements

| Field | When to Record |
|-------|---------------|
| `artifact` | 被路由的检材 |
| `command` | file/magic 命令输出 |
| `finding` | 路由决策和依据 |
| `confidence` | 路由判断的置信度 |

## Handoff

**Passes to**: forensic-autopilot（传递路由决策）
**Downstream skills**: server-forensics-router, remote-server-live-response, docker-container-forensics, database-server-forensics, webapp-server-forensics, firmware-iot-forensics, nas-raid-encrypted-storage, malware-forensics, uncommon-media-triage, timeline-reconstruction

## Stop Conditions

- 检材类型无法识别（问用户）
- 多种可能路径且无法区分（列出选项问用户）
- 检材损坏或无法读取

## Notes

- forensic-router 不执行分析，只做路由决策
- 路由依据必须基于文件结构和内容，不凭目录名猜测
- 服务器模式选择（rebuild/remote/offline/hybrid）由 server-forensics-router 决定，不在本 skill
