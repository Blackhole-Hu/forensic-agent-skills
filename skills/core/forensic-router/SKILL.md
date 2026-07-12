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
| `route_decision` | 路由决策：进入已实现路径，或 `no-compatible-skill` |
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
| 远程服务器入口 (SSH/RDP/WinRM/WebUI) | `server-forensics-router` |
| 完整服务器目录 | `server-forensics-router` |
| 混合服务器材料（镜像/目录 + Web/Database/Docker 等） | `server-forensics-router` |
| 虚拟化导出或模式不明确的服务器材料 | `server-forensics-router` |
| Docker/compose 配置 | `docker-container-forensics` |
| 数据库文件 (MySQL/Redis/PostgreSQL) | `database-server-forensics` |
| Web 应用源码/配置 | `webapp-server-forensics` |
| 固件/IoT/嵌入式 | `no-compatible-skill`（当前 Phase 无消费者） |
| 加密容器/RAID/LVM | `no-compatible-skill`（当前 Phase 无消费者） |
| PE/ELF/恶意脚本 | `no-compatible-skill`（保留静态证据，不执行样本） |
| 非常见二进制格式 | `no-compatible-skill`（当前 Phase 无消费者） |
| PCAP/网络流量 | `no-compatible-skill`（当前 Timeline 不支持 PCAP） |
| 非服务器混合类型 | 仅为当前已实现且证据支持的消费者分配多路径 |

**Evidence**: 记录路由决策和依据

`no-compatible-skill` 只属于本 Skill 的 `route_decision`。它不得写入 `route_record.route_status`、Route Step status、Handoff status 或 `execution_gate`。该决策必须保留 Artifact、分类证据和限制依据，返回 `forensic-autopilot`，且不生成到 Timeline 或不存在 Skill 的 Route Step/Handoff。

使用 `no-compatible-skill` 时，`route_basis` 必须明确写出当前 Phase 不支持的来源或目标，例如 PCAP/网络流量不属于当前 Timeline 支持范围。

远程服务器入口必须先进入 `server-forensics-router` 完成 server material classification、mode decision 和标准 route context。
本 Skill 不直接调用 `remote-server-live-response`；单一明确的 Web、Database、Docker 静态材料仍可直接进入对应的已实现领域 Skill。

### Step 3: Check Parallel Paths

混合材料中只要包含服务器镜像、完整服务器目录、远程服务器入口或虚拟化导出，就作为混合服务器材料统一进入 `server-forensics-router`，由它构建串行或并行 Route Plan，不在本 Skill 拆分为直达领域 Skill。

只有非服务器混合材料才可为当前已实现且证据支持的消费者分配并行路径。无兼容消费者的组成部分保留为 `no-compatible-skill` 限制记录，不生成伪造 Handoff。

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
**Downstream skills**: server-forensics-router, docker-container-forensics, database-server-forensics, webapp-server-forensics

## Stop Conditions

- 检材无法读取，无法获得任何 triage_notes、元数据或采样结果
- 多条候选路径互斥，且继续执行会造成错误的工作区布局或无效分析
- objective 必须人工补充，否则无法判断优先路径

> **Note**: Unknown material type is not a stop condition by itself. Preserve the Artifact and triage evidence; when no implemented consumer can be selected, return `route_decision: no-compatible-skill` to forensic-autopilot without creating a Route Step or Handoff.

## Notes

- forensic-router 不执行分析，只做路由决策
- 路由依据必须基于文件结构和内容，不凭目录名猜测
- 服务器模式选择（rebuild/remote/offline/hybrid）由 server-forensics-router 决定，不在本 skill
- `remote-server-live-response` 只由 `server-forensics-router` 或批准后的 rebuild chain 调用
