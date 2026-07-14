---
name: large-artifact-strategy
description: 大体积检材处理策略。用于 1GB+ 镜像、磁盘 dump、加密容器等大文件场景，优先采用只读引用、局部采样、签名定位、offset map、分层解析。
---

# large-artifact-strategy

## Purpose

large-artifact-strategy 是大文件处理的策略层。当 file-triage 检测到 >= 1GB 的检材时，自动调用本 skill。它定义了如何在不复制、不全量扫描的前提下，安全高效地定位关键数据。

## Use When

- file-triage 检测到 >= 1GB 的检材
- 检材是磁盘镜像（E01/VHD/VMDK/qcow2/raw）
- 检材是加密容器（LUKS/BitLocker/VeraCrypt）
- 检材是固件包或大型压缩包
- 需要建立 offset map 后再决定进入哪条专项路径

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `source_artifact` | Yes | 大文件路径 |
| `size` | Yes | 文件大小 |
| `file_type` | Yes | 文件类型（来自 file-triage） |
| `objective` | Recommended | 分析目标（影响采样策略） |

## Outputs

| Output | Description |
|--------|-------------|
| `source_info` | source path、size、mtime、access mode |
| `signature_hits` | 签名命中列表 |
| `offset_map` | 关键 offset 索引 |
| `sampling_results` | 采样分析结果 |
| `route_recommendation` | 下一步专项路径建议 |
| `route_candidates` | 证据化候选路线；未实现消费者仅能记录为 Pending candidate |
| `request.payload` | 交给 Router 的 source refs、bounded regions、采样 Evidence、结构提示和可选限制 |

## Workflow

### Step 1: Source Registration

登记 source artifact，不复制：
- source path（原始路径）
- size
- mtime
- access mode（只读）
- 完整 Artifact Hash 状态；未完成完整 Hash 时使用 `deferred` 或 `unavailable` 并记录原因

**Evidence**: 记录 source_info

### Step 2: Header Sampling

读取文件头部（前 4KB–64KB）：
- 识别文件系统 header
- 识别分区表（MBR/GPT）
- 识别容器格式

**Evidence**: 记录 header 内容和识别结果

Header 或 region 的 Hash 只能记录为 sampling Evidence；只有把 slice 登记为派生 Artifact 后，该 Hash 才能作为派生 Artifact 的完整 Hash。不得把头部、region 或 slice Hash 表述为原始 Artifact 的完整 Hash。

### Step 3: Signature Scan

对关键区域做签名扫描：
- 文件头
- 文件尾
- 已知 offset（如分区表指向的位置）
- 间隔采样（每 N MB 采样一次）

**Evidence**: 记录 signature_hits

### Step 4: Offset Map

建立 offset map：
- 每个签名命中的 offset、大小、类型
- 分区边界
- 文件系统边界
- 可疑区域

**Evidence**: 记录 offset_map

### Step 5: False Positive Escalation

对每个签名命中做 header-level verification：
- `valid` — magic + 关键字段合理
- `plausible` — magic 确认，字段部分合理
- `weak_candidate` — magic 确认但字段异常
- `false_positive` — magic 确认但字段荒谬

`false_positive` 只停止对应 candidate route，不停止整个调查。继续检查其他签名、bounded sample 和可安全验证的 Hypothesis；不得把一个候选的失败扩展为整个 Artifact 的失败结论。

**Evidence**: 记录每个命中的验证结果

### Step 6: Route Recommendation

根据 offset map 和验证结果，推荐下一步：
- 发现文件系统 → 记录验证结果并交 `forensic-router`；是否导出或进入 Server 路线由现有路由规则决定
- 发现服务器特征 → `server-forensics-router`
- 发现重复边界和独立结构 Evidence → 生成至少一个边界合法的 bounded candidate region；只有 `candidate_regions` 非空时才生成 `uncommon-media-triage` 路由建议，实际 Handoff 仍经 `forensic-router`
- 发现专有 header/table/layout、XOR/key-like 或 known-plaintext Evidence → 只向 Router 提供 bounded regions 和 Artifact/Finding/Ledger Evidence，由 Router 先决定是否进入 uncommon；`large-artifact-strategy` 不创建 proprietary executable candidate，不决定、不直接调用该消费者
- 发现加密卷、固件或恶意载荷 Evidence → 只在 `route_candidates` 中分别记录 Pending `nas-raid-encrypted-storage`、`firmware-iot-forensics` 或 `malware-forensics`
- 无可识别结构 → 继续 bounded sampling；只有产生重复边界、长度闭合、checksum、稳定字段或其他独立结构 Evidence 后才建议 `uncommon-media-triage`

Pending route candidate 必须包含 candidate skill、route basis、Artifact/Finding 引用、`high|medium|low` confidence、`current_availability: pending` 和 required next action。不得为 firmware、storage 或 malware Pending Skill 创建 Route Step、Handoff、`visited_skills` 条目或已完成声明。

向 Router 提供 uncommon 候选时，`request.payload` 必须使用以下原字段名，Router 不得重新构造：

- `source_artifact_refs`
- 非空 `candidate_regions`，每项包含 source/derived Artifact 引用、非负整数 offset、正整数 length 和 sampling method
- `upstream_signature_hits`
- `upstream_sampling_results`
- `entropy_summary`
- `structure_hints`
- `analysis_limits`（存在时）

`analysis_limits` 不存在时可以省略；Router 和 uncommon 将使用 `implicit-bounded-input`，不得据此扩大已有 region 或请求新 slice。

定义 `effective_source_artifact_refs`：非空 `request.payload.source_artifact_refs` 优先；缺失或空数组时使用 `request.material_info.artifact_refs`。有效列表必须非空且每个引用都能解析到 Artifact Record。每个 candidate region 的 `source_artifact_ref` 必须属于该列表；`derived_artifact_ref` 存在时必须能解析到派生 Artifact Record，且其 `source_artifact_id` 等于 region 的 `source_artifact_ref`。

Region `offset` 只接受 `>= 0` 的整数，`length` 只接受正整数，且 `offset + length` 不得超过 source Artifact size；不得接受十六进制、带单位或其他文本 offset。任一 source 引用、region 归属、派生关系或边界检查失败时，不得生成 uncommon 路由建议；记录具体原因和 `required_next_action` 并交 Router。

**Evidence**: 记录路由建议和依据

## Evidence Requirements

| Field | When to Record |
|-------|---------------|
| `artifact` | source artifact |
| `source` | 来源路径 |
| `hash` | 原始 Artifact 只记录完整 Artifact Hash；未完成时使用 `deferred` 或 `unavailable` 并记录原因。Header/region/slice Hash 仅作为 sampling Evidence 或派生 Artifact Hash |
| `command` | signature scan / sampling 命令 |
| `finding` | 每个签名命中、验证结果 |
| `confidence` | 命中验证置信度 |
| `next_action` | 路由建议 |

## Handoff

**Passes to**: `forensic-router`（传递路由建议）
**Executable downstream selected by Router**: server-forensics-router, uncommon-media-triage
**Pending route candidates only**: firmware-iot-forensics, nas-raid-encrypted-storage, malware-forensics
**Data available**: source_info, offset_map, route_candidates，以及给 Router 原样传递的 `source_artifact_refs`, `candidate_regions`, `upstream_signature_hits`, `upstream_sampling_results`, `entropy_summary`, `structure_hints`, `analysis_limits`（存在时）

## Stop Conditions

- 文件无法读取或严重损坏
- offset map 无法建立且没有可用采样结果
- 已达到 analysis limits，继续采样需要扩大授权范围

> **Note**: 所有 header candidate 为 false positive 或暂时无法识别常见结构时，不自动停止。保留 Artifact、bounded sample、负面 Finding 和排除路线；仍有批准范围内的结构测试时继续，没有新 Evidence 时交 `forensic-router` 或 `forensic-autopilot` 记录范围限制。`large-artifact-strategy` 不得直接决定或调用 proprietary，也不得直接调用 Pending Recovery Skill。

## Prohibited Actions

- 不得默认复制 10GB+ 检材两份
- 不得默认全量 strings / xxd / 关键词扫描
- 不得默认递归 binwalk -Me
- 不得默认挂载或激活 RAID/LVM/加密容器
- 不得在 header verification 完成前进入解包/挂载路线
- 不得把 magic 命中直接当作结构确认
- 不得直接决定或调用 `proprietary-format-recovery`
- 不得为 Pending Recovery Skill 创建 Route Step 或 Handoff

## Notes

- large-artifact-strategy 是策略层，不是分析工具
- 实际的签名扫描、采样等操作由工具（binwalk、xxd、dd 等）执行
- 提供给 uncommon-media-triage 的 slice 必须 bounded，并登记 source Artifact、offset、length、sampling method 和派生 Artifact 引用
- 提供给 Router 评估 proprietary 的输入也只能是 bounded regions 和可回查 Evidence；`large-artifact-strategy` 不维护 recovery-specific 阈值
- 原始 Artifact Hash 与 sampling Hash 必须分开表述；任何局部 Hash 都不能替代 source 的完整 Hash
- 策略的核心是"先定位，再深入"，避免盲目全量扫描
