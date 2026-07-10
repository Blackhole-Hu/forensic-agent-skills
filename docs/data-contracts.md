# Phase 2 Data Contracts

**版本**: 1.0
**分支**: `phase-2-server-chain`
**日期**: 2026-07-10

本文档定义 Phase 2 服务器取证链的统一数据契约。所有 Schema 文件位于 `templates/` 目录。

---

## 1. 统一请求信封 (Request Envelope)

所有 Phase 2 skills 接收统一的请求结构。Schema: `templates/request-envelope.schema.json`

```yaml
request:
  material_info:
    artifact_refs: array       # artifact-<uuid> 引用列表
    material_type: string      # 文件类型分类
    triage_notes: array        # triage 结论列表
    size_summary: object|null  # 大小汇总（可空，远程入口时无）
  objective: string|null       # 分析目标；可空
  objective_status: explicit|inferred|unknown
  context: object|null         # 之前的 findings、环境信息
  payload: object              # skill 专用字段
```

### 1.1 objective_status 语义

| 值 | 含义 | Skill 行为 |
|---|------|-----------|
| `explicit` | 用户明确提供目标 | 按目标执行 |
| `inferred` | 从题面/上下文推断 | 按推断目标执行，记录推断依据 |
| `unknown` | 目标未知 | 执行中立初筛和材料分类，不追问用户 |

### 1.2 material_info 说明

- `artifact_refs` 引用 Artifact 记录中的 `artifact_id`，Hash 和大小通过 Artifact 记录获取
- 不在 `material_info` 中重复 `hash`、`size` 等字段
- 远程入口场景：`artifact_refs` 可为空，`material_type` 为 `remote-entrypoint`

---

## 2. 统一响应信封 (Response Envelope)

所有 Phase 2 skills 输出统一的响应结构。Schema: `templates/response-envelope.schema.json`

```yaml
investigation_summary: object  # 人工可读摘要
route_record: object           # 路由记录（包含 route_plan 和 handoffs）
findings: array                # 发现列表
ledger_events: array           # 本次产生的 ledger event
artifact_refs: array           # 引用的 artifact
payload: object                # skill 专用结果
```

**路由信息仅存在于 `route_record` 中**，不在顶层重复声明 `route_plan`、`handoffs`。

**Investigation Summary 中的 Route Plan 必须由 `route_record.route_plan` 渲染**，不得作为独立事实来源维护。

---

## 3. Ledger Event

贯穿全链路的证据事件。Schema: `templates/ledger-event.schema.json`

```json
{
  "event_id": "led-<uuid>",
  "event_type": "command|finding|artifact|handoff|state-transition",
  "timestamp": "ISO8601",
  "skill": "<skill-name>",
  "stage": "<stage-name|null>",
  "artifact_refs": ["artifact-<uuid>"],
  "parent_event_id": "led-<uuid>|null",
  "route_id": "route-<uuid>|null",
  "handoff_id": "hof-<uuid>|null",
  "timeline_event_refs": ["tl-<uuid>"],
  "status": "pending|in_progress|retrying|blocked|completed|failed|skipped",
  "command": "<exact-command|null>",
  "started_at": "ISO8601|null",
  "ended_at": "ISO8601|null",
  "exit_code": "<integer|null>",
  "stdout_path": "<path|null>",
  "stderr_path": "<path|null>",
  "output_artifact_refs": [],
  "finding": "<what-was-discovered|null>",
  "confidence": "high|medium|low|null",
  "next_action": "<what-to-do-next|null>"
}
```

### 写入规则

- 每个有证据价值的命令产生一条 `command` event
- 每个关键 finding 产生一条 `finding` event
- 负面发现仅在能排除路线、回答问题或支撑结论时记录
- JSONL 与 Markdown 使用同一个 `event_id`
- ID 前缀：`led-`

---

## 4. Route Record

替代旧的 Route Trace。Schema: `templates/route-record.schema.json`

```yaml
schema_version: "1.0"
route_id: "route-<uuid>"
triggered_skill: <skill-name>
route_basis: array
mode_decision: string|null
route_status: active|completed|blocked|failed|cancelled
route_plan:
  - route_step_id: "step-<uuid>"
    skill: <skill-name>
    dependency_step_ids: []      # step-<uuid> 引用
    parallel_group: string|null
    status: pending|running|completed|blocked|failed|skipped
handoffs:
  - handoff_id: "hof-<uuid>"
    route_id: "route-<uuid>"
    from_step_id: "step-<uuid>"
    to_step_id: "step-<uuid>"
    from: <skill-name>
    to: <skill-name>
    reason: string
    artifact_refs: []            # artifact-<uuid>
    finding_refs: []             # finding-<uuid>
    visited_skills: []           # uniqueItems
    hop_count: integer
    status: pending|accepted|completed|rejected|blocked
    priority: critical|high|normal|low
    reentry_reason: string|null
    new_evidence_refs: array     # led-<uuid>
evidence_scope: string
risk_level: low|medium|high
next_action: string|null
execution_gate:
  required: boolean              # true 时 reason 必须非空
  reason: string|null
  policy_ref: string|null
routing_policy:
  max_hops: 16
```

### 防循环规则

- 同一 `route_id` + 同一 evidence scope 不得重复进入同一 Skill
- 除非新增证据明确要求重新分析（记录 `reentry_reason` 和 `new_evidence_refs`）
- `hop_count` 上限由 `routing_policy.max_hops` 控制（默认 16）

---

## 5. Timeline Event

时间线重建事件。Schema: `templates/timeline-event.schema.json`

```json
{
  "timeline_event_id": "tl-<uuid>",
  "original_timestamp": "string|null",
  "normalized_timestamp": "ISO8601|null",
  "timezone_offset": "+08:00|null",
  "timezone_name": "Asia/Shanghai|null",
  "timezone_assumption": "说明假设来源|null",
  "clock_skew_seconds": "integer|null",
  "time_precision": "exact|second|minute|day|unknown",
  "source_type": "auth-log|journal|web-log|docker-log|db-transaction-log|db-snapshot|login-record|file-time|pve-log|ceph-log",
  "source_artifact_id": "artifact-<uuid>",
  "parser_id": "<parser-name>",
  "actor": "IP|用户|进程|null",
  "action": "动作",
  "target": "目标|null",
  "ledger_event_refs": ["led-<uuid>"],
  "confidence": "high|medium|low"
}
```

### ID 前缀

| 类型 | 前缀 | 示例 |
|------|------|------|
| Ledger Event | `led-` | `led-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Timeline Event | `tl-` | `tl-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Artifact | `artifact-` | `artifact-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Route | `route-` | `route-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Handoff | `hof-` | `hof-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Finding | `finding-` | `finding-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Route Step | `step-` | `step-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |

---

## 6. Rebuild Status

重建执行状态。Schema: `templates/rebuild-status.schema.json`

关键字段：

```yaml
schema_version: "1.0"
plan_id: string
route_id: string
source_artifacts:
  - artifact_id: string
    path: string
    size: integer
    hash:
      algorithm: string
      value: string|null
      status: verified|provided|deferred|unavailable
    preservation_status: original-reference|read-only-mounted|working-copy-created
    deferred_reason: string|null
backend: vmware|qemu|virtualbox|docker|wsl|manual
backend_profile: object
current_stage: 0-6
overall_status: pending|in_progress|blocked|partial|completed|failed|rolled_back
stages:
  - stage: integer
    name: string
    status: pending|in_progress|retrying|blocked|completed|failed|skipped|rolled_back
    attempt: integer
    commands:
      - command: string
        exit_code: integer|null
        stdout_path: string|null
        stderr_path: string|null
    # ... 更多字段见 Schema
recovery_policy: object
rollback_available: boolean
can_continue_on_failure: boolean
```

---

## 7. Investigation Summary

人工可读的调查摘要格式。

```markdown
## Investigation Summary

**Current Assessment**: <一句话总结当前状态>

**Key Evidence**:
1. <证据1>
2. <证据2>

**Excluded Routes** (if any): <原因>

**Route Plan**:
- <下一步1>（从 route_record.route_plan 渲染）
```

---

## 8. 各专项 Skill 的 payload 字段

### 8.1 server-forensics-router

```yaml
payload:
  mode_decision: rebuild-and-connect|remote-live|offline-image|hybrid-cluster|pending
```

### 8.2 server-rebuild-planner

```yaml
payload:
  rebuild_feasibility: yes|no|partial|blocked
  rebuild_method: vmware|qemu|virtualbox|docker|wsl|manual
  required_inputs: array
  missing_inputs: array
  network_mode: host-only|nat|isolated|bridge|backend-default|none
  port_mapping: object|null
  credential_source: string|null
  credential_reference: string|null
  authentication_method: string|null
  modification_plan: string
  rollback_plan: string
  recovery_policy: object
```

### 8.3 server-rebuild-executor

```yaml
payload:
  rebuild_status: object     # 符合 rebuild-status.schema.json
  runtime_running: boolean
  connection_info: object
```

### 8.4 remote-server-live-response

```yaml
payload:
  connections:
    - connection_id: string
      type: ssh|webui|db-client|docker-exec|winrm|rdp|service-client
      host: string
      port: integer
      service: string|null
      credential_source: string|null
      credential_reference: string|null
      authentication_method: password|key|token|certificate|interactive|none
  session_summary: string
  volatile_data: array
```

### 8.5 linux-server-forensics

```yaml
payload:
  environment:
    type: rebuilt-vm|remote-live|offline-image
    connection_info: object|null
  suspicious_users: array
  login_events: array
  ssh_findings: array
  privilege_events: array
  persistence_points: array
  command_history_findings: array
  service_changes: array
```

### 8.6 webapp-server-forensics

```yaml
payload:
  environment: object
  detected_components: array
  source_paths: array
  config_paths: array
  log_paths: array
  route_map: array
  secret_findings:
    - secret_type: string
      redacted_value: string
      source_ref: string
      evidence_ref: string
  access_log_findings: array
  suspected_entrypoint: string|null
  suspect_ip: string|null
  webshell_candidate: array
  source_log_crosscheck: object
```

### 8.7 database-server-forensics

```yaml
payload:
  db_type: mysql|postgresql|redis|mongodb|sqlite|unknown
  access_mode: online-query|offline-directory|dump-file|transaction-log|snapshot
  connection_info: object|null
  data_paths: array
  table_map: array
  query_plan: array
  query_result_refs:
    - query_id: string
      query: string
      target: string
      output_path: string
      output_hash: string
      row_count: integer
  account_findings: array
  business_data_findings: array
  secret_findings: array
  db_timeline_findings: array
```

### 8.8 docker-container-forensics

```yaml
payload:
  access_mode: live-daemon|offline-directory|image-archive|compose-project
  compose_path: string|null
  dockerfile_path: string|null
  container_ids: array|null
  image_ids: array|null
  image_archive_path: string|null
  offline_directory: string|null
  source_paths: array
  compose_service_map: array
  image_map: array
  volume_map: array
  bind_mount_map: array
  port_map: object
  secret_findings: array
  log_findings: array
```

### 8.9 cluster-virtualization-forensics

```yaml
payload:
  layer_hint: string|null
  layer_map: object
  node_map: object|null
  disk_map: object|null
  vm_disk_map: object|null
  storage_map: object|null
  real_image_found: boolean
  placeholder_only: boolean
```

### 8.10 timeline-reconstruction

```yaml
payload:
  data_sources:
    - type: auth-log|journal|web-log|docker-log|db-transaction-log|db-snapshot|login-record|file-time|pve-log|ceph-log
      path: string
      timezone_hint:
        offset: string|null
        name: string|null
        assumption: string|null
  time_range: object|null
  timeline: array
  event_count: integer
  source_count: integer
  gaps: array
  anomalies: array
```
