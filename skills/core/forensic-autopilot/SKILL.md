---
name: forensic-autopilot
description: 总调度入口。接收用户输入（检材、目标），自动编排完整的取证分析链路：路由、分流、专项分析、时间线、校验、报告。只在高风险动作前询问用户。
---

# forensic-autopilot

## Purpose

forensic-autopilot 是取证工作流的总调度入口。用户只需提供检材和目标，autopilot 自动完成路径规划、工具选择、初筛、专项分析、证据记录和答案输出。

本 skill 保留通用取证调度框架。Phase 3 当前已实现 `uncommon-media-triage` 与 `proprietary-format-recovery`；firmware、storage 和 malware 三个 Recovery Skill 仍为 Pending。

## Use When

- 用户提供检材（文件、镜像、目录、远程入口）和目标（找什么、回答什么）
- 用户说"分析这个"、"看看这个镜像"、"帮我查一下"
- 用户提供目标不完整时，先使用当前通用取证链做中立、只读的证据化处理；没有已实现消费者的专项需求按 `no-compatible-skill` 处理

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `material` | Yes | 检材路径或描述（文件、目录、压缩包、镜像、远程入口） |
| `objective` | Recommended | 目标（找什么、回答什么）。若可从题面推断则不追问 |

## Outputs

| Output | Description |
|--------|-------------|
| `evidence-ledger` | 完整的证据记录 |
| `findings` | 结论列表，每条绑定证据 |
| `report` | 结构化报告（通过 report-writer 生成） |

## Workflow

### Step 1: Intake

- 接收检材和目标
- 确认检材存在（文件存在、远程可达）
- 推断目标（如可从题面/上下文推断）

**Evidence**: 记录检材路径、类型、大小、mtime

### Step 2: Tool Precheck

- 调用 `tool-router` 检查执行环境可用性（Windows/WSL/Docker/VMware/QEMU）
- 确认所需工具已安装、路径可达
- 建立路径映射规则（如需要）

**Evidence**: 记录环境检查结果

### Step 3: File Triage

- 调用 `file-triage` 做只读初筛：文件识别、hash、分类
- 如检材 >= 1GB，调用 `large-artifact-strategy`
- 产出 `material_type`、`hash`、`triage_notes`；存在结构候选时同时产出 bounded `candidate_regions` 和相关采样 Evidence
- 记录 triage 结论到 evidence-ledger

**Evidence**: 记录文件类型、hash、triage 分类结果

### Step 4: Route

- 调用 `forensic-router`，基于 Step 3 的 `triage_notes` 做最终路径决策
- 判断检材应进入当前已实现的 Server、领域分析、`uncommon-media-triage` 或 `proprietary-format-recovery` 路径，或返回 `no-compatible-skill`
- 只有 Router 通过对应输入完整性检查并返回 uncommon 或 proprietary 决策时，才允许调用该 Skill
- 分配并行路径（如需要）
- `route_decision: no-compatible-skill` 表示当前仓库没有兼容消费者；它不是 Route Record、Route Step、Handoff 或 execution gate 的状态值
- `uncommon-media-triage` 与 `proprietary-format-recovery` 是当前已实现的 Phase 3 消费者
- `firmware-iot-forensics`、`nas-raid-encrypted-storage` 和 `malware-forensics` 仍未实现，不创建相关 Route Step 或 Handoff

**Evidence**: 记录路由决策和依据

### Step 5: Domain Analysis

- 根据 forensic-router 的路由结果，进入对应的专项 skill：
  - 服务器镜像、远程服务器入口、完整服务器目录、混合服务器材料、虚拟化导出和模式不明确的服务器材料 → `server-forensics-router`
  - 单一明确的 Web、Database 或 Docker 静态材料 → forensic-router 选定的已实现领域 Skill
  - forensic-router 返回 `uncommon-media-triage` → 调用 `uncommon-media-triage`
  - forensic-router 返回 `proprietary-format-recovery` → 调用 `proprietary-format-recovery`
- 调用 uncommon 或 proprietary 时，原样传递 Router 批准的 Request payload 和包含当前 Route Record 的 Route context；不得重新构造、删减、重命名或丢弃字段
- 结构与 recovery-specific 判断阈值只由 `forensic-router` 和对应领域 Skill 维护；autopilot 不重复判断、不生成或扩展 transform/key/plaintext candidates
- 当前仓库没有兼容消费者时，保留 Artifact、分类证据和限制说明，不调用不存在的领域 Skill
- 多条路径可并行

**Evidence**: 每个专项 skill 写入自己的 findings

### Step 5a: No Compatible Skill

当 `forensic-router.route_decision` 为 `no-compatible-skill`：

1. 不重复路由，不进入 Timeline，不创建到不存在 Skill 的 Route Step 或 Handoff。
2. 记录带 Artifact 和 Ledger Event 引用的 blocker 或 scope-limitation Finding，说明当前仓库不支持该来源或分析目标。
3. 将限制和现有证据交给 `answer-gate`；校验后允许 `report-writer` 输出限制报告。
4. 不把 unsupported source 描述为已完成分析，也不把 `no-compatible-skill` 写入 `route_status`、Route Step status、Handoff status 或 `execution_gate`。

### Step 5b: Bounded Uncommon Re-entry

`uncommon-media-triage` 需要 Router 重评时，只允许一次从 uncommon 发出的单向 `uncommon-media-triage` → `forensic-router` bounded re-entry：

1. uncommon 必须产生新的 Artifact 或 Finding。
2. Handoff 的 `new_evidence_refs` 必须非空，并且每个引用都指向 uncommon 本轮产生的新 Ledger Event。
3. `reentry_reason` 必须说明新 Evidence 如何改变候选路线。
4. `visited_skills`、`hop_count` 和 `routing_policy.max_hops` 必须合法。
5. 同一 route 和 evidence scope 最多执行一次 uncommon → Router re-entry。
6. 没有新 Evidence 时禁止 re-entry。
7. Router 重评时 `visited_skills` 已包含 uncommon，因此不得再次进入 uncommon；仍无兼容消费者时进入 Step 5a，由 Answer Gate 校验范围限制并生成限制报告。

不得形成 `forensic-router` → uncommon → Router → uncommon 的循环。

### Step 5c: Bounded Proprietary Re-entry

`proprietary-format-recovery` 默认返回 autopilot。没有新消费者时直接进入 Answer Gate；只有本轮产生新 Artifact 或 Finding 时，才允许最多一次 proprietary → Router re-entry：

1. `reentry_reason` 非空，说明新 Evidence 如何改变消费者候选。
2. `new_evidence_refs` 非空，每项都指向 proprietary 本轮新 Ledger Event。
3. Handoff 包含本轮新 Ledger Event，以及合法 `hop_count` 和 `routing_policy.max_hops`。
4. Router 重评后不得再次选择 `uncommon-media-triage` 或 `proprietary-format-recovery`。
5. 没有其他当前可执行消费者时返回 autopilot，不重复路由。

不得形成 uncommon → Router → proprietary → Router → uncommon，也不得形成 proprietary → Router → proprietary。autopilot 不自行改变这些消费者决策。

### Step 6: Timeline

- 仅当已实现的领域 Skill 产生兼容 `timeline_candidates` 且需要多源关联时，调用 `timeline-reconstruction`
- PCAP/网络流量和 `no-compatible-skill` 不进入当前 Timeline

**Evidence**: 记录合并后的时间线

### Step 7: Validate

- 调用 `answer-gate` 做五步校验
- 对已进入兼容领域 Skill 且存在明确新证据路径的结果，校验不通过时返回 Step 5 补充证据
- 对 `no-compatible-skill`，Answer Gate 只校验证据引用、范围限制和未完成声明；无兼容消费者不是重新路由理由，不返回 Step 5，保留 limitation 并进入 Step 8 输出限制报告

**Evidence**: 记录校验结果

### Step 8: Report

- 调用 `report-writer` 生成结构化报告
- 输出 findings、evidence、timeline、conclusions

**Evidence**: 报告本身即为最终产物

## Evidence Requirements

| Field | When to Record |
|-------|---------------|
| `artifact` | 每个被检查的文件/服务/容器 |
| `source` | 检材来源（磁盘镜像路径、远程主机、容器 ID） |
| `hash` | 检材和关键文件的完整性 hash |
| `command` | 每次工具调用 |
| `finding` | 每个发现 |
| `confidence` | 每个 finding 的置信度 |
| `next_action` | 下一步计划 |

## Handoff

**Passes to**: `tool-router` → `file-triage` → `large-artifact-strategy` (if triggered) → `forensic-router` → domain skills、`uncommon-media-triage` 或 `proprietary-format-recovery` → `answer-gate` → `report-writer`
**Data available**: evidence-ledger 中的所有记录；调用 uncommon 或 proprietary 时还包括 Router 批准的原始 Request payload 和当前 Route Record context

## Stop Conditions

- 检材类型未知本身不是停止条件：继续只读 triage，并把 Artifact、文件头、采样结果和分类证据交给 `forensic-router`；无兼容消费者时使用 `route_decision: no-compatible-skill`
- 不因 unknown material 自动追问用户；只有继续处理必然越出授权范围、破坏证据，或无法在互斥高风险动作间安全选择时才停止
- 连续两个阶段无新证据时，更新 Investigation Summary 和 Route Record，执行 evidence-backed route reassessment；仍有安全路径时创建明确 Handoff，只有无安全路径时停止
- 需要修改原始检材、改写运行中系统状态，或执行不在当前任务范围内的外部网络操作时停止并请求授权

## Notes

- 本 skill 是抽象调度框架，不维护领域专项阈值
- Phase 3 当前为部分实施状态；`uncommon-media-triage` 和 `proprietary-format-recovery` 可执行
- firmware、storage 和 malware 三个 Recovery Skill 仍为 Pending，只能作为 route candidate，不得创建实际 Handoff
- 当前没有兼容消费者时按 `no-compatible-skill` 记录证据和范围限制
- 大体积检材（>= 1GB）必须先走 large-artifact-strategy，不默认全量扫描
