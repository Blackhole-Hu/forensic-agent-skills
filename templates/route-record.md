# Route Record Template

Route Record 替代旧的 Route Trace，是 Phase 2 所有 skill 的统一路由记录格式。

## 结构

```yaml
route_id: "route-<uuid>"
triggered_skill: <skill-name>
route_basis: [<依据1>, <依据2>]
mode_decision: <模式决策|null>
route_plan:
  - skill: <skill-name>
    dependency: <依赖 skill|null>
    parallel: false
handoffs:
  - handoff_id: "hof-<uuid>"
    route_id: "route-<uuid>"
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
next_action: <下一步唯一动作>
execution_gate:
  required: false
  reason: null
  policy_ref: null
routing_policy:
  max_hops: 16
```

## 字段说明

### route_id

全局唯一的路由标识，格式 `route-<uuid>`。同一次调查中所有 skill 共享同一个 `route_id`。

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

### mode_decision

仅 `server-forensics-router` 使用，取值：
- `rebuild-and-connect`: 本地重建并连接
- `remote-live`: 远程活体响应
- `offline-image`: 离线镜像分析
- `hybrid-cluster`: 混合集群模式
- `pending`: 待确定

### handoffs

跨 skill 交接记录。包含防循环字段：
- `visited_skills`: 已访问的 skill 列表
- `hop_count`: 当前跳数
- `reentry_reason`: 重新进入原因（循环时填写）
- `new_evidence_refs`: 新增证据引用（循环时填写）

### execution_gate

执行门控，仅在操作超出已批准 rebuild plan 或 policy scope 时触发：
- `required`: 是否需要门控
- `reason`: 门控原因
- `policy_ref`: 关联的 policy 引用

### routing_policy

路由策略：
- `max_hops`: 最大跳数上限（默认 16）
