---
name: forensic-router
description: 任务/材料路由器。根据检材类型、文件结构和证据线索，选择当前已实现的 Server、领域分析或 uncommon media triage 路径，或明确返回无兼容消费者。
---

# forensic-router

## Purpose

forensic-router 是材料级路由器。接收 triage 结论和检材信息，判断应进入哪条分析路径。它是 forensic-autopilot 和具体专项 skill 之间的决策层。

本 skill 统一承担材料级最终路由；服务器模式选择仍由 `server-forensics-router` 负责。

## Use When

- forensic-autopilot 完成 intake、tool precheck 和 file-triage 后，需要决定分析路径
- forensic-router consumes `triage_notes` from file-triage to make the final path decision
- 多种材料类型混合时，需要分配多条并行路径

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `material_info` | Yes | 检材类型、大小、文件结构（来自 file-triage） |
| `objective` | Recommended | 分析目标；缺失时按 `objective_status: unknown` 做中立路由 |
| `triage_notes` | Recommended | file-triage 的分类结论 |
| `request.payload` | Recommended | 上游提供的 uncommon candidate regions、采样结果和限制；选择 uncommon 时必须通过输入完整性检查 |
| `request.context` | Recommended | 当前 Route Record、step、Finding 和 Ledger Event 引用；选择 uncommon 时必须包含当前 Route Record |

objective 缺失时按 `objective_status: unknown` 处理，根据材料结构、文件头、采样结果和已有证据进行中立路由。缺少 objective 本身不是停止条件；可以基于证据选择当前已实现路径，也可以生成 `no-compatible-skill`，不得为了获得 objective 而停止纯只读材料分类。

## Outputs

| Output | Description |
|--------|-------------|
| `route_decision` | 路由决策：进入已实现路径，或 `no-compatible-skill` |
| `route_basis` | 路由依据（文件类型、结构、线索） |
| `parallel_paths` | 如有多个路径，列出并行路径 |
| `route_context` | 包含当前 Route Record 的调用上下文 |

## Workflow

### Step 1: Analyze Material

读取 material_info 和 triage_notes，识别：
- 文件类型（镜像、压缩包、二进制、文档、PCAP、固件等）
- 文件系统类型（NTFS、EXT4、SquashFS 等）
- 线索（配置文件、日志、凭据、服务器特征）
- uncommon 候选对应的 `source_artifact_refs`、非空 `candidate_regions`、采样 Evidence 和 `analysis_limits`

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
| 与服务器、PVE、Ceph、虚拟化、VM Disk、Container rootfs 或集群拓扑有关的 RAID/LVM/LVM-thin/ZFS/btrfs | `server-forensics-router` |
| 独立加密容器、通用 RAID 或存储介质，且无服务器/虚拟化关系证据 | `no-compatible-skill`（当前 Phase 无消费者） |
| PE/ELF/恶意脚本 | `no-compatible-skill`（保留静态证据，不执行样本） |
| 至少三个重复边界、稳定字段偏移及长度/对齐闭合支持的固定记录 | `uncommon-media-triage` |
| 有重复 tag、length 不越界且 value 消耗闭合的 TLV 候选 | `uncommon-media-triage` |
| 有跨帧 ID/control/DLC/payload 关系的 CAN/CAN FD-like 候选 | `uncommon-media-triage` |
| 有多条可校验 sentence、连续 GPS 点、传感器或时间序列 Evidence | `uncommon-media-triage` |
| 有重复 page header、固定页长及 slot/record directory 的自定义数据库页候选 | `uncommon-media-triage` |
| 低—中熵且同时具有重复边界、常量字段、长度闭合、checksum 或其他独立结构 Evidence | `uncommon-media-triage` |
| unknown、单个 magic、单个时间戳、单个坐标或单独熵值 | 不足以进入 `uncommon-media-triage`；继续 bounded triage 或 `no-compatible-skill` |
| PCAP/网络流量 | `no-compatible-skill`（当前 Timeline 不支持 PCAP） |
| 浏览器历史或完整移动设备取证 | `no-compatible-skill`（当前无消费者） |
| 非服务器混合类型 | 仅为当前已实现且证据支持的消费者分配多路径 |

**Evidence**: 记录路由决策和依据

`no-compatible-skill` 只属于本 Skill 的 `route_decision`。它不得写入 `route_record.route_status`、Route Step status、Handoff status 或 `execution_gate`。该决策必须保留 Artifact、分类证据和限制依据，返回 `forensic-autopilot`，且不生成到 Timeline 或不存在 Skill 的 Route Step/Handoff。

使用 `no-compatible-skill` 时，`route_basis` 必须明确写出当前 Phase 不支持的来源或目标，例如 PCAP/网络流量不属于当前 Timeline 支持范围。

RAID/LVM/LVM-thin/ZFS/btrfs 的 `route_basis` 必须引用服务器目录、PVE/Ceph 配置、虚拟机磁盘元数据、Container rootfs、集群节点/共享存储关系或其他可复核证据，说明为何属于服务器链。没有这类关系证据的独立存储或恢复材料保持 out-of-phase，不提前实现通用 NAS/存储恢复功能。

`uncommon-media-triage` 的 `route_basis` 必须引用 Artifact、bounded sample、重复边界和至少一项独立结构验证。文件扩展名、设备名称、品牌、unknown 分类、单个 magic、单个时间戳、单个坐标、单独的低熵或高熵结果不能独立触发该路线。

#### Uncommon input gate

即使结构阈值满足，Router 也只有在以下输入检查全部通过后才能选择 `uncommon-media-triage`：

1. `request.context` 包含当前 Route Record，且 `visited_skills` 尚未包含 `uncommon-media-triage`。
2. `candidate_regions` 存在且非空。
3. 定义 `effective_source_artifact_refs`：`request.payload.source_artifact_refs` 非空时使用该列表；缺失或空数组时回退到 `request.material_info.artifact_refs`。有效列表必须非空，且每个引用都能解析到 Artifact Record。
4. 每个 region 都有非空 `region_id`、属于 `effective_source_artifact_refs` 的 `source_artifact_ref`、非空 sampling method，以及整数 `offset` 和 `length`。`offset >= 0`，`length > 0`；不得接受十六进制字符串、带单位字符串或其他文本 offset。
5. 每个 region 对应的 source Artifact Record `size` 必须是已知的非负整数；只有这样才能验证 `offset + length <= source Artifact size`。size 缺失、为 `null` 或类型无效时不得选择 uncommon，并记录 `required_next_action`。
6. `derived_artifact_ref` 非空时必须解析对应派生 Artifact Record，且其 `source_artifact_id` 等于 region 的 `source_artifact_ref`。不得新增或读取 `slice.length` 字段。
7. 所有非空显式 limit 都必须是正整数：`max_regions > 0`、`max_bytes_per_region > 0`、`max_total_bytes > 0`、`max_slice_bytes > 0`、`timeout_seconds > 0`。字段为 `null` 或缺失时不应用该项限制；非空但非整数或小于等于 0 时输入不可执行。
8. 显式 limits 按字段分别检查：region 数量不超过 `max_regions`；每个 `region.length` 不超过 `max_bytes_per_region`；所有 `region.length` 总和不超过 `max_total_bytes`；`derived_artifact_ref` 非空且 `max_slice_bytes` 生效时，使用派生 Artifact Record 的 `size` 验证 `derived Artifact Record.size <= max_slice_bytes`。派生 size 为 `null`、类型无效或 Artifact 无法解析时，不能通过 `max_slice_bytes` 输入校验。调用还必须能强制实际运行时间不超过 `timeout_seconds`；无法施加非空 timeout 时输入不可执行。
9. 任一显式限制超出时不得选择或调用 uncommon；记录具体超限字段、实际值、限制值和 `required_next_action`。
10. `analysis_limits` 可整体缺失；此时 Router 保留 payload 原状，由 uncommon 应用 `implicit-bounded-input`，只分析已提供 regions。

输入不足、Artifact 引用冲突、region 越界或显式 limit 超出时，不得创建到 uncommon 的 Route Step 或 Handoff。普通检材返回 `file-triage` 补充合法 bounded candidate region；1GB+ 检材或已经进入 Large Artifact Mode 的材料返回 `large-artifact-strategy` 补充 bounded Evidence。Router 记录缺失或冲突原因、具体超限字段和 required next action，待补充后重新做首次路由判断。

选择 uncommon 时，Router 必须把上游 `request.payload` 继续作为同一个 `request.payload` 原样传给 `forensic-autopilot`，并同时传递包含当前 Route Record 的 `request.context`；不得重新构造、删减或重命名 payload 字段。

`proprietary-format-recovery`、`firmware-iot-forensics`、`nas-raid-encrypted-storage` 和 `malware-forensics` 仍为 Pending。来自 uncommon 的对应结果只能保留在 `payload.route_candidates`；本 Skill 不为它们创建 Route Step、Handoff，不把它们加入 `visited_skills`，也不描述为已调用或已完成。

Competition-specific 请求在当前没有已实现消费者时使用 `no-compatible-skill`，不创建不存在的 Route Step 或 Handoff。

远程服务器入口必须先进入 `server-forensics-router` 完成 server material classification、mode decision 和标准 route context。
本 Skill 不直接调用 `remote-server-live-response`；单一明确的 Web、Database、Docker 静态材料仍可直接进入对应的已实现领域 Skill。

### Step 3: Check Parallel Paths

混合材料中只要包含服务器镜像、完整服务器目录、远程服务器入口或虚拟化导出，就作为混合服务器材料统一进入 `server-forensics-router`，由它构建串行或并行 Route Plan，不在本 Skill 拆分为直达领域 Skill。

只有非服务器混合材料才可为当前已实现且证据支持的消费者分配并行路径。无兼容消费者的组成部分保留为 `no-compatible-skill` 限制记录，不生成伪造 Handoff。

**Evidence**: 记录并行路径列表

### Step 4: Handoff

将路由决策传递给 forensic-autopilot，由 autopilot 调用对应的专项 skill。选择 uncommon 时同时传递原样 `request.payload` 和当前 Route Record context。

首次进入 `uncommon-media-triage` 后，只允许一次 uncommon → Router bounded re-entry，并且必须同时满足：

1. uncommon 产生了新的 Artifact 或 Finding。
2. Handoff 的 `new_evidence_refs` 非空，且每个引用都指向 uncommon 本轮产生的新 Ledger Event。
3. `reentry_reason` 明确说明新 Evidence 如何影响路由。
4. `visited_skills`、`hop_count` 和 `routing_policy.max_hops` 合法。
5. 同一 route 和 evidence scope 尚未执行过 uncommon → Router re-entry。

没有新 Evidence 时禁止 re-entry。Router 收到该 Handoff 时，`visited_skills` 已包含 `uncommon-media-triage`，因此不得再次选择 uncommon；仍无兼容消费者时返回 forensic-autopilot，由 Answer Gate 校验范围限制并生成限制报告。

## Evidence Requirements

| Field | When to Record |
|-------|---------------|
| `artifact` | 被路由的检材 |
| `command` | file/magic 命令输出 |
| `finding` | 路由决策和依据 |
| `confidence` | 路由判断的置信度 |

## Handoff

**Passes to**: forensic-autopilot（传递路由决策）
**Downstream skills**: server-forensics-router, docker-container-forensics, database-server-forensics, webapp-server-forensics, uncommon-media-triage

## Stop Conditions

- 检材无法读取，无法获得任何 triage_notes、元数据或采样结果
- 多条候选路径互斥，且继续执行会造成错误的工作区布局或无效分析

> **Note**: Unknown material type is not a stop condition by itself. Preserve the Artifact and triage evidence; when no implemented consumer can be selected, return `route_decision: no-compatible-skill` to forensic-autopilot without creating a Route Step or Handoff.
>
> Missing objective is not a stop condition. Continue neutral, read-only classification with `objective_status: unknown` and make only evidence-backed routing decisions.

## Notes

- forensic-router 不执行分析，只做路由决策
- 路由依据必须基于文件结构和内容，不凭目录名猜测
- unknown 或熵值本身不构成 uncommon-media-triage 路由依据
- 服务器模式选择（rebuild/remote/offline/hybrid）由 server-forensics-router 决定，不在本 skill
- `remote-server-live-response` 只由 `server-forensics-router` 或批准后的 rebuild chain 调用
