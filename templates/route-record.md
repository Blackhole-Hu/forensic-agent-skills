# Route Record Template

Route Record 替代旧的 Route Trace，是 Phase 2 所有 skill 的统一路由记录格式。

## 结构

```yaml
schema_version: "1.0"
route_id: "route-<uuid>"
triggered_skill: <skill-name>
route_basis: [<依据1>, <依据2>]
mode_decision: <模式决策|null>
route_status: active|completed|blocked|failed|cancelled
route_plan:
  - route_step_id: "step-<uuid>"
    skill: <skill-name>
    dependency_step_ids: []
    parallel_group: null
    status: pending
handoffs:
  - handoff_id: "hof-<uuid>"
    route_id: "route-<uuid>"
    from_step_id: "step-<uuid>"
    to_step_id: "step-<uuid>"
    from: <来源 skill>
    to: <目标 skill>
    reason: <交接原因>
    artifact_refs: []
    finding_refs: []
    visited_skills: [<来源 skill>]
    hop_count: 1
    status: pending
    priority: normal
    reentry_reason: null
    new_evidence_refs: []
evidence_scope: <证据范围>
risk_level: low|medium|high
next_action: <下一步唯一动作|null>
execution_gate:
  required: false
  reason: null
  policy_ref: null
routing_policy:
  max_hops: 16
```

## 字段说明

### schema_version

契约版本，固定为 `"1.0"`。

### route_id

全局唯一的路由标识，格式 `route-<uuid>`。同一次调查中所有 skill 共享同一个 `route_id`。

### route_status

路由整体状态：
- `active`: 进行中
- `completed`: 已完成
- `blocked`: 被阻塞
- `failed`: 失败
- `cancelled`: 已取消

### route_basis

触发路由的依据列表。必须基于：
- 题面线索
- triage notes
- 文件结构
- 配置文件
- 日志内容
- 凭据/远程入口
- 镜像特征

不得凭目录名猜测。

### route_plan

路由步骤列表。每个步骤包含：

- `route_step_id`: 步骤唯一 ID（`step-<uuid>`）
- `skill`: 要调用的 skill 名称
- `dependency_step_ids`: 依赖的前置步骤 ID 列表
- `parallel_group`: 并行组标识（可空）
- `status`: 步骤状态（`pending|running|completed|blocked|failed|skipped`）

### mode_decision

仅 `server-forensics-router` 使用，取值：
- `rebuild-and-connect`: 本地重建并连接
- `remote-live`: 远程活体响应
- `offline-image`: 离线镜像分析
- `hybrid-cluster`: 混合集群模式
- `pending`: 待确定

### handoffs

跨 skill 交接记录。每个 handoff 必须包含：

- `handoff_id`: 交接唯一 ID（`hof-<uuid>`）
- `route_id`: 必须等于父 Route 的 `route_id`
- `from_step_id`: 来源步骤 ID（必须存在于 `route_plan`）
- `to_step_id`: 目标步骤 ID（必须存在于 `route_plan`）
- `from` / `to`: skill 名称
- `reason`: 交接原因（必填，非空）
- `artifact_refs`: 引用的 artifact（`artifact-<uuid>` 格式）
- `finding_refs`: 引用的 finding（`finding-<uuid>` 格式）
- `visited_skills`: 已访问的 skill 列表（uniqueItems）
- `hop_count`: 当前跳数
- `status`: 交接状态
- `priority`: 优先级
- `reentry_reason`: 重新进入原因（循环时填写）
- `new_evidence_refs`: 新增证据引用（`led-<uuid>` 格式）

### execution_gate

执行门控，仅在操作超出已批准 rebuild plan 或 policy scope 时触发：
- `required`: 是否需要门控（`true` 时 `reason` 必须为非空字符串）
- `reason`: 门控原因
- `policy_ref`: 关联的 policy 引用

### routing_policy

路由策略：
- `max_hops`: 最大跳数上限（默认 16）

### next_action

下一步唯一动作。流程结束后可为 `null`。

## 防循环规则

- 同一 `route_id` + 同一 evidence scope 不得重复进入同一 Skill
- 除非新增证据明确要求重新分析（记录 `reentry_reason` 和 `new_evidence_refs`）
- `hop_count` 上限由 `routing_policy.max_hops` 控制（默认 16）
- `visited_skills` 使用 `uniqueItems` 约束
