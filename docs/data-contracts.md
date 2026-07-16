# Phase 2 Data Contracts

**版本**: 1.0
**分支**: `phase-2-server-chain`
**日期**: 2026-07-10

本文档定义 Phase 2 服务器取证链的统一数据契约。所有 Schema 文件位于 `templates/` 目录。

---

## 1. 统一请求信封 (Request Envelope)

所有 Phase 2 skills 接收统一的请求结构。Schema: `templates/request-envelope.schema.json`

```yaml
schema_version: "1.0"
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
schema_version: "1.0"
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
  "schema_version": "1.0",
  "timeline_event_id": "tl-<uuid>",
  "original_timestamp": "string|null",
  "normalized_timestamp": "ISO8601|null",
  "timezone_offset": "+HH:MM|null",
  "timezone_name": "Asia/Shanghai|null",
  "timezone_assumption": "说明假设来源|null",
  "clock_skew_seconds": "integer|null",
  "time_precision": "exact|second|minute|day|unknown",
  "normalization_status": "ready|needs-review|unsupported-source",
  "derivation": "observed|inferred",
  "source_type": "auth-log|journal|web-log|docker-log|db-transaction-log|db-snapshot|login-record|file-time|pve-log|ceph-log|audit-log|package-log|service-log|cluster-log|other",
  "source_subtype": "string|null",
  "source_artifact_id": "artifact-<uuid>|null",
  "parser_id": "<parser-name>",
  "parser_version": "string|null",
  "actor": "IP|用户|进程|null",
  "action": "动作",
  "target": "目标|null",
  "artifact_refs": ["artifact-<uuid>"],
  "ledger_event_refs": ["led-<uuid>"],
  "finding_refs": ["finding-<uuid>"],
  "basis": ["string"],
  "confidence": "high|medium|low",
  "cluster_scope_id": "string|null"
}
```

约束：

1. `timeline_event_id` 必须稳定且唯一；同一候选和同一规范化输入重入时复用同一 ID。
2. `source_artifact_id` 是直接来源 Artifact；`artifact_refs` 是其他关联 Artifact，可以为空数组；`finding_refs` 可以为空数组。
3. `derivation=observed` 时，`source_artifact_id` 必须是非空 Artifact ID，不得虚构来源。
4. `derivation=inferred` 时，`source_artifact_id` 可以为 `null`，但 `basis` 或 `ledger_event_refs` 至少一项非空，并且必须说明推断依据。
5. `normalization_status=ready` 时，`normalized_timestamp` 必须非空且标准化依据可回指。
6. `normalized_timestamp=null` 时，`normalization_status` 不得为 `ready`。
7. 原始时间不得覆盖、删除或静默改写；无法解析、不支持或时区不确定的事件仍保留。
8. 缺少时区时不得默认 UTC、系统本地时区或 `+08:00`。
9. 只有 Artifact 直接记录该事件时才使用 `observed`；由跨事件关系推导的事件仍为 `inferred`，即使它关联了 Artifact。

Schema 使用互斥的 `oneOf` 分支：

- **Legacy v1.0 timeline event**：严格复现旧契约，只接受旧版 10 个 `source_type`，要求非空 `source_artifact_id`、至少一个 Ledger Event 引用，以及至少一个存在且非空的原始或标准化时间。Legacy 分支不接受 `normalization_status`、`derivation`、`source_subtype`、`artifact_refs`、`finding_refs`、`basis`、`cluster_scope_id` 或扩展后的新 `source_type`。
- **Phase 2 complete timeline event**：要求本节示例中的全部字段出现；允许 `artifact_refs`、`ledger_event_refs`、`finding_refs` 和 `basis` 为空数组，并继续执行 observed / inferred 与时间标准化条件。为保留 `missing-timestamp` 等事件，`original_timestamp` 和 `normalized_timestamp` 可以同时为 `null`，但 `normalization_status` 不得为 `ready`。

Timeline Skill 新产生的正式 Timeline Event 必须进入 Complete 分支。不得通过省略 `derivation` 和 `normalization_status` 降级为 Legacy；只添加部分新增字段也不能进入 Legacy 分支。

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

Phase 2 的 `cross_domain_candidates.skill` 只能引用当前仓库已实现且可执行的 Skill。需要后续专项分析的可疑脚本、WebShell、ELF、二进制或载荷必须保留为当前领域 Skill 的 Artifact、Finding、candidate、suspicious artifact、persistence evidence 或 blocker，并记录 scope limitation；不得创建到未实现 Skill 的 Route Step、Handoff 或可执行 cross-domain target，也不得声称专项分析已经完成。

### 8.1 server-forensics-router

```yaml
payload:
  mode_decision: rebuild-and-connect|remote-live|offline-image|hybrid-cluster|pending
```

### 8.2 server-rebuild-planner

```yaml
payload:
  plan_id: "plan-<uuid>"
  plan_status: draft|ready|blocked|rejected
  rebuild_feasibility: yes|no|partial|blocked
  selected_backend: vmware|qemu|virtualbox|docker|wsl|manual|null
  backend_selection_status: confirmed|provisional|unavailable
  backend_candidates: array
  selection_basis: array
  backend_profile: object
  required_inputs: array
  missing_inputs: array
  prepared_artifact_requirements: array
  resource_requirements: object
  network_mode: host-only|nat|isolated|bridge|backend-default|none
  port_mapping: object|null
  credential_source: string|null
  credential_reference: string|null
  authentication_method: string|null
  modification_plan: string
  rollback_plan: string
  recovery_policy: object
  execution_scope: object
  executor_handoff: object|null
```

### 8.3 server-rebuild-executor

```yaml
payload:
  plan_id: "plan-<uuid>"
  rebuild_status: object
  rebuild_status_path: "work/rebuild/rebuild-status.json"
  overall_status: pending|in_progress|blocked|partial|completed|failed|rolled_back
  current_stage: 0|1|2|3|4|5|6
  prepared_artifacts: array
  runtime_definition: object|null
  runtime_instance: object|null
  runtime_running: boolean
  network_config: object|null
  services_discovered: array
  connection_info:
    connections: array
  recovery_actions: array
  blockers: array
```

### 8.4 remote-server-live-response

```yaml
payload:
  session_id: "session-<uuid>"
  origin:
    type: rebuilt-runtime|direct-remote
    plan_id: string|null
  session_status: pending|connecting|active|partial|completed|blocked|failed
  connection_results:
    - connection_id: string
      status: preflight|reachable|connected|authenticated|blocked|failed
      authenticated: boolean|null
      client: string|null
      started_at: ISO8601
      ended_at: ISO8601|null
      error_class: string|null
      attempt_count: integer
      ledger_event_refs: array
  session_summary: string
  remote_identity: object|null
  time_observation: object|null
  volatile_data: array
  collection_artifact_refs: array
  expected_remote_footprint: array
  domain_candidates:
    - skill: string
      basis: array
      confidence: high|medium|low
      connection_ids: array
      finding_refs: array
      artifact_refs: array
  blockers: array
  effective_limits:
    max_session_seconds: integer
    max_output_bytes: integer
    connect_timeout_seconds: integer
    max_attempts_per_connection: integer
    retry_backoff_seconds: integer
```

### 8.5 linux-server-forensics

```yaml
payload:
  environment:
    type: rebuilt-vm|remote-live|offline-image
    plan_id: string|null
    session_id: string|null
  system_profile:
    hostname: string|null
    distro: string|null
    version: string|null
    kernel: string|null
    architecture: string|null
    timezone: string|null
    boot_time: string|null
  user_account_findings: array
  suspicious_users: array
  login_events: array
  ssh_findings: array
  privilege_events: array
  persistence_points: array
  command_history_findings: array
  service_changes: array
  package_findings: array
  network_config_findings: array
  log_source_map:
    - source_id: string
      source_type: auth-log|journal|login-record|audit-log|package-log|service-log|file-time|other
      path: string
      availability: present|missing|partial|unreadable
      coverage_start: string|null
      coverage_end: string|null
      timezone_hint: object|null
      artifact_ref: string|null
      gap_notes: array
  timeline_candidates:
    - candidate_id: string
      original_timestamp: string|null
      normalized_timestamp: ISO8601|null
      timezone_offset: string|null
      timezone_name: string|null
      timezone_assumption: string|null
      clock_skew_seconds: integer|null
      time_precision: exact|second|minute|day|unknown
      source_type_hint: string
      source_artifact_id: string
      parser_id: string
      actor: string|null
      action: string
      target: string|null
      ledger_event_refs: array
      confidence: high|medium|low
      normalization_status: ready|needs-review|unsupported-source
  cross_domain_candidates:
    - candidate_id: string
      skill: string
      basis: array
      confidence: high|medium|low
      connection_ids: array
      artifact_refs: array
      finding_refs: array
      targeted_collection_request:
        actions: array
        paths: array
        max_output_bytes: integer|null
        reason: string
  blockers: array
```

### 8.6 webapp-server-forensics

```yaml
payload:
  environment:
    type: remote-live|rebuilt-vm|offline-image|source-package
    plan_id: string|null
    session_id: string|null
  web_profile:
    server_software: array
    frameworks: array
    languages: array
    document_roots: array
    deployment_model: string|null
    timezone: string|null
  detected_components:
    - component_id: string
      name: string
      component_type: web-server|reverse-proxy|framework|runtime|application|waf|other
      version: string|null
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  source_paths:
    - path_id: string
      path: string
      role: document-root|source-root|public-assets|upload-directory|template-directory|dependency-directory|other
      artifact_ref: string|null
      availability: present|missing|partial|unreadable
  config_paths:
    - config_id: string
      path: string
      config_type: virtual-host|reverse-proxy|application|framework|environment|routing|security|other
      artifact_ref: string|null
      availability: present|missing|partial|unreadable
  log_source_map:
    - source_id: string
      source_type: access-log|error-log|application-log|proxy-log|waf-log|audit-log|other
      path: string
      availability: present|missing|partial|unreadable
      coverage_start: string|null
      coverage_end: string|null
      timezone_hint: object|null
      artifact_ref: string|null
      gap_notes: array
  route_map:
    - route_entry_id: string
      method: string|null
      path_pattern: string
      handler: string|null
      source_path: string|null
      authentication_required: boolean|null
      artifact_refs: array
      confidence: high|medium|low
  secret_findings:
    - secret_id: string
      secret_type: password|token|api-key|private-key|database-credential|cookie-secret|encryption-key|other
      redacted_value: string
      source_path: string
      source_artifact_id: string
      line_or_key: string|null
      exposure_context: string
      finding_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  access_log_findings:
    - finding_id: string
      original_timestamp: string|null
      normalized_timestamp: ISO8601|null
      source_ip: string|null
      forwarded_for: array
      attributed_client_ip: string|null
      method: string|null
      raw_path: string|null
      normalized_path: string|null
      status_code: integer|null
      user_agent: string|null
      request_id: string|null
      indicators: array
      redaction_applied: boolean
      normalization_steps: array
      client_ip_basis: socket-peer|trusted-proxy-chain|untrusted-forwarded|unknown
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  suspected_entrypoint:
    entrypoint_id: string
    method: string|null
    path: string|null
    route_entry_id: string|null
    source_path: string|null
    first_seen: ISO8601|null
    basis: array
    artifact_refs: array
    finding_refs: array
    ledger_event_refs: array
    confidence: high|medium|low
  suspect_ip: string|null
  suspect_ip_basis:
    - basis_type: direct-log|trusted-proxy-chain|cross-log-correlation|request-chain|other
      description: string
      artifact_refs: array
      finding_refs: array
      ledger_event_refs: array
  suspect_ip_confidence: high|medium|low|null
  webshell_candidate:
    - candidate_id: string
      path: string
      language: string|null
      source_artifact_id: string
      indicators: array
      execution_observed: boolean|null
      artifact_refs: array
      finding_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  source_log_crosscheck:
    status: matched|partial|unmatched|not-applicable
    links:
      - route_entry_id: string|null
        source_path: string|null
        log_finding_ids: array
        basis: array
    gaps: array
  timeline_candidates:
    - candidate_id: string
      original_timestamp: string|null
      normalized_timestamp: ISO8601|null
      timezone_offset: string|null
      timezone_name: string|null
      timezone_assumption: string|null
      clock_skew_seconds: integer|null
      time_precision: exact|second|minute|day|unknown
      source_type_hint: string
      source_artifact_id: string
      parser_id: string
      actor: string|null
      action: string
      target: string|null
      ledger_event_refs: array
      confidence: high|medium|low
      normalization_status: ready|needs-review|unsupported-source
  cross_domain_candidates:
    - candidate_id: string
      skill: string
      basis: array
      confidence: high|medium|low
      connection_ids: array
      artifact_refs: array
      finding_refs: array
      targeted_collection_request:
        actions: array
        paths: array
        max_output_bytes: integer|null
        reason: string
  blockers: array
```

`suspected_entrypoint` 整体允许为 null：无足够证据确定入口时不强行选择；多个候选无法收敛时保持 null 并在 findings 或 gaps 中说明。非 null 时必须包含文档中列出的全部字段。

`targeted_collection_request` 整体允许为 null：不需要补充采集时；非 null 时四个字段必须存在；只用于交给 `remote-server-live-response`。

### 8.7 database-server-forensics

```yaml
payload:
  environment:
    type: remote-live|rebuilt-vm|offline-image|artifact-package
    plan_id: string|null
    session_id: string|null
  db_profile:
    db_type: mysql|postgresql|redis|mongodb|sqlite|unknown
    version: string|null
    instance_id: string|null
    server_timezone: string|null
    charset: string|null
    collation: string|null
    read_only_status: confirmed-read-only|reported-read-only|writable|unknown
    profile_artifact_refs: array
    ledger_event_refs: array
    confidence: high|medium|low
  access_mode: online-query|offline-directory|dump-file|transaction-log|snapshot
  data_sources:
    - source_id: string
      source_type: config|data-directory|dump|snapshot|binlog|wal|redo|undo|oplog|aof|rdb|audit-log|slow-query-log|general-log|other
      path: string
      availability: present|missing|partial|unreadable
      source_artifact_id: string|null
      coverage_start: string|null
      coverage_end: string|null
      timezone_hint: object|null
      gap_notes: array
  table_map:
    - object_id: string
      database: string|null
      schema: string|null
      name: string
      object_type: table|view|collection|index|keyspace|other
      estimated_rows: integer|null
      columns_or_fields: array
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  query_plan:
    - query_id: string
      purpose: string
      db_type: mysql|postgresql|redis|mongodb|sqlite|unknown
      target_instance_scope_id: string
      target_object_scope_ids: array
      target_database: string|null
      query_template: string
      parameter_refs: array
      parser_id: string
      parsed_statement_types: array
      safety_status: pending|approved|rejected
      safety_basis: array
      expected_columns: array
      max_rows: integer
      max_bytes: integer
      timeout_seconds: integer
      attempt_count: integer
      termination_status: not-applicable|confirmed-stopped|may-still-be-running|unknown
      impact_level: low|medium|high
      status: pending|running|completed|partial|blocked|failed|skipped
  query_result_refs:
    - query_id: string
      output_artifact_id: string
      row_count: integer|null
      byte_count: integer
      truncated: boolean
      redaction_applied: boolean
      started_at: ISO8601
      ended_at: ISO8601
      ledger_event_refs: array
  account_findings:
    - account_id: string
      principal: string
      account_type: user|role|service-account|application-account|unknown
      authentication_method: string|null
      privilege_summary: array
      superuser_or_admin: boolean|null
      status: active|locked|expired|disabled|unknown
      artifact_refs: array
      finding_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  privilege_findings:
    - privilege_id: string
      principal: string
      scope: global|database|schema|table|collection|keyspace|unknown
      privilege: string
      grantable: boolean|null
      anomalous: boolean|null
      basis: array
      artifact_refs: array
      finding_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  business_data_findings:
    - finding_id: string
      data_category: account|transaction|order|message|audit|configuration|identifier|other
      database: string|null
      schema: string|null
      object_name: string
      selection_basis: array
      record_count: integer|null
      sample_artifact_id: string|null
      artifact_refs: array
      redaction_applied: boolean
      minimization_applied: boolean
      finding_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  secret_findings:
    - secret_id: string
      secret_type: password|token|api-key|connection-string|private-key|encryption-key|other
      source_path: string
      source_artifact_id: string
      key_or_field: string|null
      redacted_value: string
      exposure_context: string
      finding_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  transaction_findings:
    - transaction_id: string
      source_type: binlog|wal|redo|undo|oplog|aof|audit-log|other
      original_timestamp: string|null
      normalized_timestamp: ISO8601|null
      actor: string|null
      operation: string
      target: string|null
      transaction_identifier: string|null
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  timeline_candidates:
    - candidate_id: string
      original_timestamp: string|null
      normalized_timestamp: ISO8601|null
      timezone_offset: string|null
      timezone_name: string|null
      timezone_assumption: string|null
      clock_skew_seconds: integer|null
      time_precision: exact|second|minute|day|unknown
      source_type_hint: string
      source_artifact_id: string
      parser_id: string
      actor: string|null
      action: string
      target: string|null
      ledger_event_refs: array
      confidence: high|medium|low
      normalization_status: ready|needs-review|unsupported-source
  cross_domain_candidates:
    - candidate_id: string
      skill: string
      basis: array
      confidence: high|medium|low
      connection_ids: array
      artifact_refs: array
      finding_refs: array
      targeted_collection_request:
        actions: array
        paths: array
        max_output_bytes: integer|null
        reason: string
  effective_limits:
    max_query_rows: integer
    max_query_bytes: integer
    query_timeout_seconds: integer
    max_queries: integer
  blockers: array
```

`targeted_collection_request` 整体允许为 null。非 null 时四个字段必须存在，只用于 `remote-server-live-response`。

`read_only_status` 使用 `confirmed-read-only|reported-read-only|writable|unknown`。`reported-read-only` 不等于 `confirmed-read-only`。`writable` 不代表允许写操作。

Request Contract 中 `allowed_instances` 和 `allowed_objects` 使用结构化定义（见 SKILL.md Request Contract 章节）。`online-query` 时 `allowed_instances` 必须非空；`allowed_objects` 必须形成有限对象范围。

### 8.8 docker-container-forensics

```yaml
payload:
  environment:
    type: remote-live|rebuilt-vm|offline-image|artifact-package
    plan_id: string|null
    session_id: string|null
  access_mode: live-daemon|offline-directory|image-archive|compose-project
  docker_profile:
    engine_version: string|null
    api_version: string|null
    storage_driver: string|null
    docker_root_dir: string|null
    rootless: boolean|null
    cgroup_driver: string|null
    logging_driver: string|null
    swarm_state: inactive|active|pending|unknown
    observation_mode: live|metadata-snapshot|inferred
    observed_at: ISO8601|null
    artifact_refs: array
    ledger_event_refs: array
    confidence: high|medium|low
  archive_profile:
    archive_format: docker-save|oci-layout|oci-archive|container-export|rootfs-tar|unknown
    flattened_filesystem: boolean|null
    manifest_present: boolean|null
    config_present: boolean|null
    layer_history_available: boolean|null
    source_artifact_id: string|null
    artifact_refs: array
    ledger_event_refs: array
    confidence: high|medium|low
  source_paths:
    - source_id: string
      source_type: docker-root|container-metadata|image-archive|oci-layout|compose-file|dockerfile|volume-data|container-log|daemon-event|other
      location_type: filesystem-path|artifact|daemon-api|logical|unknown
      path: string|null
      logical_location: string|null
      availability: present|missing|partial|unreadable
      source_artifact_id: string|null
      coverage_start: string|null
      coverage_end: string|null
      timezone_hint: object|null
      gap_notes: array
  compose_service_map:
    - service_id: string
      project_name: string|null
      service_name: string
      image_ref: string|null
      build_context: string|null
      dockerfile_path: string|null
      command_summary: string|null
      environment_keys: array
      env_file_paths: array
      volume_refs: array
      network_refs: array
      port_refs: array
      depends_on: array
      resolution_status: resolved|partial|unresolved
      unresolved_variables: array
      configured_user: string|null
      privileged: boolean|null
      capabilities_added: array
      capabilities_dropped: array
      security_opt: array
      pid_mode: string|null
      network_mode: string|null
      read_only: boolean|null
      restart_policy: string|null
      docker_socket_mount: boolean|null
      secret_refs: array
      config_refs: array
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  container_map:
    - container_id: string
      name: string|null
      image_ref: string|null
      image_id: string|null
      state: created|running|paused|restarting|exited|dead|unknown
      state_observation: live|metadata-snapshot|inferred
      security_observation_status: complete|partial|unobserved
      security_gap_notes: array
      created_at: ISO8601|null
      started_at: ISO8601|null
      finished_at: ISO8601|null
      restart_policy: string|null
      privileged: boolean|null
      configured_user: string|null
      capabilities_added: array
      capabilities_dropped: array
      security_opt: array
      pid_mode: string|null
      network_mode: string|null
      readonly_rootfs: boolean|null
      docker_socket_mount: boolean|null
      mount_refs: array
      network_refs: array
      port_refs: array
      log_source_refs: array
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  image_map:
    - image_id: string
      repo_tags: array
      repo_digests: array
      created_at: ISO8601|null
      architecture: string|null
      os: string|null
      config_entrypoint: array
      config_cmd: array
      exposed_ports: array
      layer_refs: array
      identity_basis: engine-image-id|manifest-digest|repo-digest|tag-only|unknown
      source_artifact_id: string|null
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  layer_map:
    - layer_id: string
      digest: string|null
      diff_id: string|null
      parent_layer_id: string|null
      order_index: integer|null
      media_type: string|null
      size_bytes: integer|null
      source_artifact_id: string|null
      whiteout_entries: array
      opaque_directories: array
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  filesystem_changes:
    - change_id: string
      container_id: string|null
      path: string
      change_type: added|modified|deleted|opaque-directory|unknown
      change_source: image-layer|runtime-upper|volume|bind-mount|metadata|unknown
      layer_id: string|null
      source_artifact_id: string
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  volume_map:
    - volume_id: string
      name: string|null
      volume_kind: named|anonymous|tmpfs|other|unknown
      management_scope: docker-managed|external|unknown
      driver: string|null
      mountpoint: string|null
      container_ids: array
      destination_paths: array
      observation_mode: live|configured|metadata-snapshot|inferred
      basis: array
      source_artifact_id: string|null
      data_hints: array
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  bind_mount_map:
    - mount_id: string
      source_path: string
      destination_path: string
      read_only: boolean|null
      propagation: string|null
      container_ids: array
      observation_mode: live|configured|metadata-snapshot|inferred
      basis: array
      source_artifact_id: string|null
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  network_map:
    - network_id: string
      name: string|null
      driver: string|null
      scope: local|swarm|global|unknown
      internal: boolean|null
      attachable: boolean|null
      subnets: array
      gateways: array
      container_ids: array
      observation_mode: live|configured|metadata-snapshot|inferred
      basis: array
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  port_map:
    - mapping_id: string
      service_id: string|null
      container_id: string|null
      protocol: tcp|udp|sctp|unknown
      container_port: integer
      host_ip: string|null
      host_port: integer|null
      mapping_type: published|exposed-only|host-network|unknown
      observation_mode: live|configured|metadata-snapshot|inferred
      basis: array
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  log_source_map:
    - source_id: string
      container_id: string|null
      driver: json-file|local|journald|syslog|fluentd|gelf|awslogs|splunk|etwlogs|none|other
      path: string|null
      availability: present|missing|partial|remote-only|unreadable
      coverage_start: string|null
      coverage_end: string|null
      timezone_hint: object|null
      source_artifact_id: string|null
      gap_notes: array
  log_findings:
    - finding_id: string
      container_id: string|null
      original_timestamp: string|null
      normalized_timestamp: ISO8601|null
      stream: stdout|stderr|event|daemon|application|unknown
      message_redacted: string
      indicators: array
      truncated: boolean
      artifact_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  secret_findings:
    - secret_id: string
      secret_type: password|token|api-key|registry-credential|private-key|connection-string|cookie-secret|encryption-key|other
      source_path: string|null
      source_location: string
      source_artifact_id: string
      key_or_field: string|null
      redacted_value: string
      exposure_context: compose|dockerfile|environment|image-history|container-config|registry-config|log|volume|other
      finding_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  suspicious_artifacts:
    - candidate_id: string
      path: string|null
      source_location: string
      origin: image-layer|runtime-upper|volume|bind-mount|container-log|container-config|other
      source_artifact_id: string
      indicators: array
      execution_observed: boolean|null
      artifact_refs: array
      finding_refs: array
      ledger_event_refs: array
      confidence: high|medium|low
  timeline_candidates:
    - candidate_id: string
      original_timestamp: string|null
      normalized_timestamp: ISO8601|null
      timezone_offset: string|null
      timezone_name: string|null
      timezone_assumption: string|null
      clock_skew_seconds: integer|null
      time_precision: exact|second|minute|day|unknown
      source_type_hint: string
      source_artifact_id: string
      parser_id: string
      actor: string|null
      action: string
      target: string|null
      ledger_event_refs: array
      confidence: high|medium|low
      normalization_status: ready|needs-review|unsupported-source
  cross_domain_candidates:
    - candidate_id: string
      skill: string
      basis: array
      confidence: high|medium|low
      connection_ids: array
      artifact_refs: array
      finding_refs: array
      targeted_collection_request:
        actions:
          - action_id: string
            action_type: daemon-version|daemon-info|container-inspect|image-inspect|volume-inspect|network-inspect|container-logs|daemon-events|container-diff|container-copy-out|image-history|compose-config
            daemon_scope_id: string
            connection_id: string
            object_type: daemon|container|image|volume|network|compose-project
            object_ref: string|null
            source_path: string|null
            since: ISO8601|null
            until: ISO8601|null
            max_lines: integer|null
            max_objects: integer|null
            max_output_bytes: integer
            purpose: string
            impact_level: low|medium|high
            sensitive_output_expected: boolean
            capture_mode: standard-artifact|protected-raw-and-redacted-derivative|redacted-only
            expected_footprint: array
        paths:
          - action_id: string
            path_role: container-source|remote-host-source
            path: string
        max_output_bytes: integer|null
        reason: string
  effective_limits:
    max_log_lines: integer
    max_log_bytes: integer
    max_archive_files: integer
    max_archive_expanded_bytes: integer
    max_objects: integer
  blockers: array
```

`targeted_collection_request` 整体允许为 null。非 null 时四个顶层字段全部存在。

`archive_profile` 在非归档模式允许整体为 null。

`source_paths.path` 可以为 null，无真实文件路径时由 `logical_location` 提供脱敏逻辑位置。`secret_findings.source_path` 和 `suspicious_artifacts.path` 可以为 null，由 `source_location` 提供脱敏逻辑位置。`source_paths` 使用 `logical_location`，`secret_findings` 和 `suspicious_artifacts` 使用 `source_location`，两者不得混淆。

`port_map` 中 `service_id` 和 `container_id` 至少一个非 null。`observation_mode=configured` 时 `container_id` 可以为 null，用于 Compose 静态项目。`observation_mode=inferred` 时 `basis` 必须非空。

`capture_mode` 三值：`standard-artifact`（预期无敏感信息）、`protected-raw-and-redacted-derivative`（默认保护）、`redacted-only`（策略允许不保留原始输出时）。采集意外发现 Secret 时立即停止公开并重新分类。

`volume_map` 区分 `volume_kind`（named/anonymous/tmpfs/other/unknown）和 `management_scope`（docker-managed/external/unknown）。`observation_mode=configured` 来自 Compose 静态配置，不证明挂载已创建或当前生效。`basis` 记录推断依据。

`container_map` 的 `security_observation_status` 区分 complete/partial/unobserved。complete 时空数组和 false 支持负面结论；partial/unobserved 时不得输出完整负面安全结论。

### Targeted collection action

`daemon_scope_id` 与 `connection_id` 必须引用同一批准 daemon target。`action_type`、`object_type` 和 `object_ref` 必须符合 SKILL.md 定义的映射。container-logs、daemon-events、container-diff、container-copy-out 必须满足各自的时间、对象和输出限制。`action.max_output_bytes` 不得超过 request 总上限。action 限制不得超过 effective limits。`paths.action_id` 必须引用同一请求中的 action。container-source 与 remote-host-source 不得混用。`impact_level` 必须由 `expected_footprint` 支撑。

### Volume and Bind Mount

`volume_kind` 区分 named/anonymous/tmpfs/other/unknown。`management_scope` 区分 docker-managed/external/unknown。`observation_mode` 四值：live（当前 Daemon 运行态）、configured（Compose 静态配置，不证明当前挂载）、metadata-snapshot（离线元数据）、inferred（推断，basis 非空）。`mountpoint`/`source_path` 为宿主机侧；`destination_paths`/`destination_path` 为容器侧。

### Network and Port

`inferred` 时 `basis` 必须非空。`configured` 不证明当前发布或可达。`live` 必须来自当前批准 Daemon。空 `basis` 不支持网络或端口结论。

### Container Security coverage

`complete`/`partial`/`unobserved` 语义见 SKILL.md Stage 4。`partial` 时 `security_gap_notes` 非空。`complete` 才允许用空数组或 false 支撑完整负面结论。`partial`/`unobserved` 不得输出完整负面安全结论。

```yaml
request.payload.docker_scope:
  allowed_container_paths:
    - container_id: string
      path: string
      recursive: boolean
      max_depth: integer|null
```

`container-copy-out` 的 `object_ref` 必须等于其中一个 `container_id`；action 的 `source_path` 必须位于该项 `path` 范围内。null/缺失/空数组表示禁止 container-copy-out。`path` 是容器命名空间内的规范绝对路径。`recursive=false` 时只能复制明确文件；`recursive=true` 时 `max_depth` 必须为非 null 正整数，action 必须同时具有有限 `max_objects` 和 `max_output_bytes`。拒绝路径穿越、越界符号链接、设备文件、socket 和 FIFO。容器内部路径与宿主机 `allowed_paths` 不得混用。

### 8.9 cluster-virtualization-forensics

#### Request Contract

<!-- cluster-request-contract:start -->
```yaml
schema_version: "1.0"
request:
  material_info:
    artifact_refs:
      - "artifact-<uuid>"
    material_type: string
    triage_notes:
      - string
    size_summary:
      total_bytes: integer|null
      file_count: integer|null
      largest_file_bytes: integer|null
  objective: string|null
  objective_status: explicit|inferred|unknown
  context:
    route_record:
      schema_version: "1.0"
      route_id: "route-<uuid>"
      triggered_skill: string
      route_basis:
        - string
      mode_decision: string|null
      route_status: active|completed|blocked|failed|cancelled
      route_plan:
        - route_step_id: "step-<uuid>"
          skill: string
          dependency_step_ids:
            - "step-<uuid>"
          parallel_group: string|null
          status: pending|running|completed|blocked|failed|skipped
      handoffs:
        - handoff_id: "hof-<uuid>"
          route_id: "route-<uuid>"
          from_step_id: "step-<uuid>"
          to_step_id: "step-<uuid>"
          from: string
          to: string
          reason: string
          artifact_refs:
            - "artifact-<uuid>"
          finding_refs:
            - "finding-<uuid>"
          visited_skills:
            - string
          hop_count: integer
          status: pending|accepted|completed|rejected|blocked
          priority: critical|high|normal|low
          reentry_reason: string|null
          new_evidence_refs:
            - "led-<uuid>"
      evidence_scope: string
      risk_level: low|medium|high
      next_action: string|null
      execution_gate:
        required: boolean
        reason: string|null
        policy_ref: string|null
      routing_policy:
        max_hops: integer
    current_step_id: "step-<uuid>"
    artifact_refs:
      - "artifact-<uuid>"
    ledger_event_refs:
      - "led-<uuid>"
    finding_refs:
      - "finding-<uuid>"
    upstream_environment:
      plan_id: string|null
      session_id: string|null
      runtime_instance_ref: string|null
    upstream_time_observation:
      remote_timestamp: string|null
      remote_timezone: string|null
      timezone_offset: string|null
      estimated_clock_skew_seconds: integer|null
  payload:
    environment:
      origin_type: direct-remote|rebuilt-runtime|offline-artifact
      plan_id: string|null
      session_id: string|null
      connection_ids:
        - string
      root_artifact_refs:
        - "artifact-<uuid>"
      collection_artifact_refs:
        - "artifact-<uuid>"
    access_mode: live-cluster|rebuilt-cluster|offline-node-image|disk-set|artifact-package
    cluster_scope:
      analysis_scope_id: string
      platform_hints:
        - proxmox-ve|vmware-vsphere|generic-linux-virtualization|unknown
      targeted_questions:
        - string
      allowed_cluster_targets:
        - cluster_scope_id: string
          connection_id: string|null
          target_ref: string
          virtualization_platform: proxmox-ve|vmware-vsphere|generic-linux-virtualization|unknown
          endpoint_role: pve-api|ceph-cli|vcenter-api|ssh|service-client|offline-artifact|other
      allowed_node_targets:
        - cluster_scope_id: string
          node_id: string
      allowed_vm_targets:
        - cluster_scope_id: string
          vm_id: string
      allowed_container_targets:
        - cluster_scope_id: string
          container_id: string
      allowed_storage_targets:
        - cluster_scope_id: string
          storage_id: string
      allowed_disk_targets:
        - cluster_scope_id: string
          disk_id: string
      allowed_paths:
        - path_scope_id: string
          cluster_scope_id: string|null
          owner_node_id: string|null
          artifact_ref: "artifact-<uuid>|null"
          path: string
          recursive: boolean
          max_depth: integer|null
      disk_set_members:
        - cluster_scope_id: string
          member_id: string
          artifact_ref: "artifact-<uuid>"
          expected_role: system-disk|data-disk|raid-member|lvm-pv|zfs-vdev|btrfs-device|ceph-osd|unknown
          required: boolean
      stages:
        include_platform_node_mapping: boolean
        include_quorum_analysis: boolean
        include_disk_mapping: boolean
        include_storage_reconstruction: boolean
        include_distributed_storage_analysis: boolean
        include_vm_mapping: boolean
        include_snapshot_backing_analysis: boolean
        include_health_conflict_analysis: boolean
        include_timeline_candidates: boolean
        include_cross_domain_validation: boolean
      live_collection_limits:
        max_actions: integer|null
        max_output_bytes: integer|null
        max_objects_per_action: integer|null
        max_log_bytes: integer|null
        max_config_bytes: integer|null
        max_session_seconds: integer|null
      archive_limits:
        max_archive_files: integer|null
        max_archive_expanded_bytes: integer|null
      disk_limits:
        max_disk_members: integer|null
        max_bytes_sampled_per_disk: integer|null
        max_image_candidates: integer|null
      traversal_limits:
        max_depth: integer|null
        max_objects: integer|null
        max_paths: integer|null
```
<!-- cluster-request-contract:end -->

#### Response Payload

<!-- cluster-payload-contract:start -->
```yaml
payload:
  environment:
    origin_type: direct-remote|rebuilt-runtime|offline-artifact
    plan_id: string|null
    session_id: string|null
    connection_ids:
      - string
    root_artifact_refs:
      - "artifact-<uuid>"
    collection_artifact_refs:
      - "artifact-<uuid>"
    artifact_refs:
      - "artifact-<uuid>"
    ledger_event_refs:
      - "led-<uuid>"
    basis:
      - string
    confidence: high|medium|low
  access_mode: live-cluster|rebuilt-cluster|offline-node-image|disk-set|artifact-package
  cluster_profiles:
    - cluster_scope_id: string
      cluster_id: string|null
      cluster_name: string|null
      virtualization_platform: proxmox-ve|vmware-vsphere|generic-linux-virtualization|unknown
      platform_version: string|null
      control_plane_components:
        - component_id: string
          component_type: pmxcfs|corosync|pve-cluster|vcenter|vsphere-ha|libvirt|other
          component_version: string|null
          status: present|missing|partial|unknown
      distributed_storage_components:
        - component_id: string
          component_type: ceph|vsan|other
          component_version: string|null
          status: present|degraded|missing|partial|unknown
      configured_node_count: integer|null
      observed_node_count: integer|null
      observation_mode: live|configured|metadata-snapshot|inferred
      observed_at: ISO8601|null
      artifact_refs:
        - "artifact-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
  node_map:
    - cluster_scope_id: string
      node_id: string
      hostname: string|null
      platform_node_ref: string|null
      roles:
        - pve-node|vsphere-host|corosync-member|ceph-mon|ceph-mgr|ceph-osd-host|storage-node|compute-node|other
      membership_status: member|configured-member|missing|removed|unknown
      management_addresses:
        - string
      observation_mode: live|configured|metadata-snapshot|inferred
      observed_at: ISO8601|null
      artifact_refs:
        - "artifact-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
  disk_map:
    - cluster_scope_id: string
      disk_id: string
      owner_node_id: string|null
      layer_node_id: string
      device_path: string|null
      stable_identifier: string|null
      size_bytes: integer|null
      sector_size: integer|null
      member_role: system-disk|data-disk|raid-member|lvm-pv|zfs-vdev|btrfs-device|ceph-osd|unknown
      availability: present|missing|partial|unreadable|metadata-only
      observation_mode: live|configured|metadata-snapshot|inferred
      artifact_refs:
        - "artifact-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
  storage_map:
    - cluster_scope_id: string
      storage_id: string
      owner_node_ids:
        - string
      storage_type: directory|nfs|cifs|iscsi|mdraid|lvm|lvm-thin|zfs|btrfs|ceph-rbd|cephfs|vsan|other|unknown
      configured_name: string|null
      configured_path_or_target: string|null
      shared: boolean|null
      content_roles:
        - vm-disk|container-rootfs|template|iso|backup|snippet|other
      backing_layer_node_refs:
        - string
      health_status: healthy|degraded|failed|unknown|not-observed
      observation_mode: live|configured|metadata-snapshot|inferred
      artifact_refs:
        - "artifact-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
  layer_map:
    nodes:
      - cluster_scope_id: string
        layer_node_id: string
        node_type: physical-disk|partition|mdraid-array|lvm-pv|lvm-vg|lvm-lv|lvm-thin-pool|lvm-thin-volume|zfs-vdev|zfs-pool|zfs-dataset|zfs-zvol|btrfs-device|btrfs-filesystem|btrfs-subvolume|ceph-osd|ceph-pool|ceph-rbd|directory-storage|nfs-export|iscsi-target|vsan-object|qcow2-file|raw-file|vmdk-descriptor|vmdk-extent|snapshot-delta|vm-disk|container-rootfs|guest-image-candidate|missing-component|unknown
        entity_ref: string|null
        owner_node_id: string|null
        name: string|null
        location: string|null
        size_bytes: integer|null
        availability: present|missing|partial|unreadable|metadata-only|remote-reference
        identity_status: verified|correlated|ambiguous|unverified
        observation_mode: live|configured|metadata-snapshot|inferred
        observed_at: ISO8601|null
        artifact_refs:
          - "artifact-<uuid>"
        ledger_event_refs:
          - "led-<uuid>"
        basis:
          - string
        confidence: high|medium|low
    edges:
      - cluster_scope_id: string
        layer_edge_id: string
        from_layer_node_id: string
        to_layer_node_id: string
        relation: contains|partitions-into|member-of|backs|aggregates-into|allocates|hosts|stores|maps-to|configured-as|snapshot-parent-of|backing-file-of|delta-parent-of|symlink-target-of|remote-reference-to|missing-link-to|conflicts-with
        observation_mode: live|configured|metadata-snapshot|inferred
        artifact_refs:
          - "artifact-<uuid>"
        ledger_event_refs:
          - "led-<uuid>"
        basis:
          - string
        confidence: high|medium|low
    gaps:
      - cluster_scope_id: string
        gap_id: string
        expected_from_layer_node_id: string|null
        expected_to_layer_node_id: string|null
        missing_layer_type: string
        reason: member-missing|metadata-missing|content-unavailable|scope-excluded|parse-failure|unknown
        impact: informational|partial-map|blocks-image-identity|blocks-rebuild
        artifact_refs:
          - "artifact-<uuid>"
        ledger_event_refs:
          - "led-<uuid>"
        basis:
          - string
        confidence: high|medium|low
    conflicts:
      - cluster_scope_id: string
        conflict_id: string
        left_ref: string
        right_ref: string
        conflict_type: configured-vs-live|identity-mismatch|size-mismatch|membership-mismatch|backing-chain-mismatch|other
        resolution_status: unresolved|explained|resolved
        preferred_ref: string|null
        artifact_refs:
          - "artifact-<uuid>"
        ledger_event_refs:
          - "led-<uuid>"
        basis:
          - string
        confidence: high|medium|low
  vm_map:
    - cluster_scope_id: string
      workload_id: string
      owner_node_id: string|null
      object_type: vm|container|vm-template|container-template
      name: string|null
      platform: pve-qemu|pve-lxc|vsphere-vm|libvirt-vm|other|unknown
      configured_state: defined|template|disabled|unknown
      runtime_state: running|stopped|paused|suspended|unknown|not-observed
      observation_mode: live|configured|metadata-snapshot|inferred
      artifact_refs:
        - "artifact-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
  vm_disk_map:
    - cluster_scope_id: string
      vm_disk_mapping_id: string
      workload_id: string
      object_type: vm|container|vm-template|container-template
      device_slot: string|null
      storage_id: string|null
      configured_volume_ref: string|null
      terminal_layer_node_id: string
      layer_edge_refs:
        - string
      image_candidate_refs:
        - string
      disk_role: boot|system|data|efi|tpm|cloud-init|container-rootfs|other|unknown
      observation_mode: live|configured|metadata-snapshot|inferred
      artifact_refs:
        - "artifact-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
  snapshot_map:
    - cluster_scope_id: string
      snapshot_id: string
      owner_type: vm|container|vm-template|container-template|vm-disk|storage-volume
      owner_ref: string
      parent_snapshot_id: string|null
      snapshot_type: internal|external|storage-native|rbd-snapshot|zfs-snapshot|vmware-delta|pve-snapshot|unknown
      created_at: ISO8601|null
      state: configured|present|missing|partial|unknown
      layer_node_refs:
        - string
      backing_edge_refs:
        - string
      observation_mode: live|configured|metadata-snapshot|inferred
      artifact_refs:
        - "artifact-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
  quorum_findings:
    - cluster_scope_id: string
      quorum_finding_id: string
      quorum_state: quorate|not-quorate|unknown|not-applicable
      expected_votes: integer|null
      observed_votes: integer|null
      member_node_ids:
        - string
      missing_node_ids:
        - string
      split_brain_suspected: boolean|null
      observation_mode: live|configured|metadata-snapshot|inferred
      artifact_refs:
        - "artifact-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
  storage_health_findings:
    - cluster_scope_id: string
      health_finding_id: string
      target_type: mdraid|lvm|zfs|btrfs|ceph|vsan|shared-storage|other
      target_ref: string
      health_state: healthy|degraded|failed|incomplete|unknown
      missing_component_refs:
        - string
      indicators:
        - string
      observation_mode: live|configured|metadata-snapshot|inferred
      artifact_refs:
        - "artifact-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
  image_candidates:
    - cluster_scope_id: string
      candidate_id: string
      object_type: full-image|descriptor|backing-file|snapshot-delta|symlink|placeholder|metadata-only-reference|remote-logical-reference|missing-extent
      location_type: filesystem-path|artifact|logical-storage|remote-storage|unknown
      location: string
      content_availability: complete|partial|descriptor-only|metadata-only|remote-not-acquired|missing|unreadable|unknown
      identity_status: verified-content|verified-descriptor|correlated|ambiguous|unverified
      size_bytes: integer|null
      format: raw|qcow2|vmdk|vhd|vhdx|e01|rbd|zvol|lv|filesystem-tree|unknown
      backing_refs:
        - string
      layer_node_refs:
        - string
      source_artifact_id: "artifact-<uuid>|null"
      analysis_readiness: ready|limited|not-ready
      analysis_readiness_basis:
        - string
      large_artifact_status: required|pending|completed|not-required|unknown
      artifact_refs:
        - "artifact-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
  timeline_candidates:
    - cluster_scope_id: string
      candidate_id: string
      original_timestamp: string|null
      normalized_timestamp: ISO8601|null
      timezone_offset: string|null
      timezone_name: string|null
      timezone_assumption: string|null
      clock_skew_seconds: integer|null
      time_precision: exact|second|minute|day|unknown
      source_type_hint: pve-log|ceph-log|file-time|unsupported-cluster-log
      source_artifact_id: "artifact-<uuid>"
      parser_id: string
      actor: string|null
      action: string
      target: string|null
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
      normalization_status: ready|needs-review|unsupported-source
  cross_domain_candidates:
    - candidate_id: string
      cluster_scope_id: string
      skill: server-rebuild-planner|server-rebuild-executor|remote-server-live-response|linux-server-forensics|docker-container-forensics|database-server-forensics|webapp-server-forensics|timeline-reconstruction|large-artifact-strategy
      basis:
        - string
      confidence: high|medium|low
      connection_ids:
        - string
      artifact_refs:
        - "artifact-<uuid>"
      finding_refs:
        - "finding-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      dependency_step_ids:
        - "step-<uuid>"
      workload_refs:
        - cluster_scope_id: string
          workload_id: string
          object_type: vm|container|vm-template|container-template
      planner_authorization:
        planner_step_id: "step-<uuid>|null"
        plan_id: string|null
        plan_status: ready|blocked|rejected|null
      targeted_collection_request:
        actions:
          - action_id: string
            action_type: cluster-status|node-list|quorum-status|storage-config|vm-list|vm-config|container-config|ceph-status|ceph-health-detail|ceph-osd-tree|ceph-pool-list|ceph-rbd-list|lvm-metadata|mdraid-detail|zfs-status|btrfs-filesystem-show|bounded-config-copy|bounded-log-collection
            target_type: cluster|node|vm|container|storage|disk
            target_ref: string
            cluster_scope_id: string
            connection_id: string
            source_path: string|null
            allowed_path_scope_id: string|null
            since: ISO8601|null
            until: ISO8601|null
            max_objects: integer
            max_output_bytes: integer
            purpose: string
            impact_level: low|medium|high
            sensitive_output_expected: boolean
            capture_mode: standard-artifact|protected-raw-and-redacted-derivative|redacted-only
            expected_footprint:
              - string
        paths:
          - action_id: string
            path_role: remote-config-source|remote-log-source
            path: string
        max_output_bytes: integer
        reason: string
  effective_limits:
    max_actions:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_output_bytes:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_objects_per_action:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_log_bytes:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_config_bytes:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_archive_files:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_archive_expanded_bytes:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_disk_members:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_bytes_sampled_per_disk:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_image_candidates:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_depth:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_objects:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
    max_paths:
      value: integer|null
      status: resolved|unresolved|not-applicable
      basis:
        - string
  blockers:
    - blocker_id: string
      cluster_scope_id: string|null
      error_class: environment_mismatch|unsupported_platform|session_unavailable|cluster_scope_mismatch|node_scope_mismatch|vm_scope_mismatch|container_scope_mismatch|storage_scope_mismatch|root_path_invalid|disk_member_missing|metadata_missing|quorum_unknown|split_brain_suspected|raid_degraded|lvm_metadata_incomplete|zfs_metadata_incomplete|ceph_map_incomplete|distributed_storage_health_degraded|backing_chain_incomplete|image_content_unavailable|placeholder_only|large_artifact_incomplete|output_limit_exceeded|parse_failure|timezone_uncertain|evidence_conflict|targeted_collection_required|planner_authorization_missing
      scope: cluster|node|disk|storage|layer|vm|snapshot|image|timeline|collection
      target_ref: string|null
      message: string
      recoverable: boolean
      required_handoff: server-forensics-router|server-rebuild-planner|server-rebuild-executor|remote-server-live-response|linux-server-forensics|docker-container-forensics|database-server-forensics|webapp-server-forensics|timeline-reconstruction|large-artifact-strategy|null
      artifact_refs:
        - "artifact-<uuid>"
      ledger_event_refs:
        - "led-<uuid>"
      basis:
        - string
      confidence: high|medium|low
```
<!-- cluster-payload-contract:end -->

Request 与 Response 的共享不变量如下：

- `analysis_scope_id` 只标识本次分析范围；具体 Cluster 使用 `cluster_scope_id`，所有对象引用均以它参与复合键校验。
- live/rebuilt 要求当前 Session、非空 Connection 列表及属于该 Session 的目标；offline 禁止 Session、Connection 与 live Action。
- live Disk Action 只能由 `allowed_disk_targets` 批准；`disk_set_members` 和 `disk_map` 都不是 live 授权。
- bounded copy/log Action 必须经唯一 `allowed_path_scope_id` 绑定批准 Node 与路径。
- `effective_limits` 每项独立记录 `value`、`status` 和 `basis`；unresolved 限制阻断受影响操作，不得编造默认值。
- Layer Edge 固定由 provider/base/target/member 指向 consumer/snapshot/symlink representation/typed component，并按冻结端点矩阵和 DAG 规则校验。
- `analysis_readiness=ready` 仅适用于完整内容、`verified-content` 身份、完整 backing/base/extent、已完成或不需要的大检材处理，且无阻断。
- `server-rebuild-executor` 仅能在已批准的 Planner step 和有效 plan 存在时成为候选。

### 8.10 timeline-reconstruction

Timeline Reconstruction 使用统一 Request / Response Envelope，只接收上游领域 Skill 已生成的 `timeline_candidates`，不自行重新执行领域取证或建立远程 Session。

#### Request payload

```yaml
payload:
  data_sources:
    - source_id: string
      source_type_hint: string
      path: string|null
      source_artifact_id: artifact-<uuid>|null
      timezone_hint:
        offset: string|null
        name: string|null
        assumption: string|null
      parser_hint: string|null

  timeline_candidates:
    - candidate_id: string
      original_timestamp: string|null
      normalized_timestamp: ISO8601|null
      timezone_offset: string|null
      timezone_name: string|null
      timezone_assumption: string|null
      clock_skew_seconds: integer|null
      time_precision: exact|second|minute|day|unknown
      source_type_hint: string
      source_artifact_id: artifact-<uuid>|null
      parser_id: string
      actor: string|null
      action: string
      target: string|null
      ledger_event_refs:
        - led-<uuid>
      confidence: high|medium|low
      normalization_status: ready|needs-review|unsupported-source
      basis:
        - string
      cluster_scope_id: string|null
      finding_refs:
        - finding-<uuid>
      artifact_refs:
        - artifact-<uuid>

  time_range:
    start: ISO8601|null
    end: ISO8601|null
    basis:
      - string
```

输入兼容规则：

- 缺少 `basis`、`finding_refs` 或 `artifact_refs` 时使用空数组；
- 缺少 `cluster_scope_id` 时使用 `null`；
- 缺少 `normalization_status` 时使用 `needs-review`；
- 缺少 `source_artifact_id` 时使用 `null`，随后按 observed / inferred 约束处理；
- 不得根据 `normalization_status` 本身生成或推断 `basis`；
- `basis` 只能来自 Artifact 内容、Ledger Event、parser 输出、时区证据、配置文件或可复现的多事件推断关系；
- inferred candidate 同时缺少非空 `basis` 和非空 `ledger_event_refs` 时不得生成正式 Timeline Event，应记录 blocker；只有能够回指已存在事件时才记录 anomaly；
- `unsupported-cluster-log` candidate 不得丢弃。

#### Source hint mapping

| `source_type_hint` | `source_type` | `source_subtype` |
|---|---|---|
| `auth-log` | `auth-log` | `null` |
| `journal` | `journal` | `null` |
| `web-log` | `web-log` | `null` |
| `docker-log` | `docker-log` | `null` |
| `db-transaction-log` | `db-transaction-log` | `null` |
| `db-snapshot` | `db-snapshot` | `null` |
| `login-record` | `login-record` | `null` |
| `file-time` | `file-time` | `null` |
| `pve-log` | `pve-log` | `null` |
| `ceph-log` | `ceph-log` | `null` |
| `audit-log` | `audit-log` | `null` |
| `package-log` | `package-log` | `null` |
| `service-log` | `service-log` | `null` |
| `cluster-log` | `cluster-log` | `null` |
| `vsphere-log` | `cluster-log` | `vsphere` |
| `corosync-log` | `cluster-log` | `corosync` |
| `zfs-log` | `cluster-log` | `zfs` |
| `btrfs-log` | `cluster-log` | `btrfs` |
| `vsan-log` | `cluster-log` | `vsan` |
| `unsupported-cluster-log` | `cluster-log` | 有真实依据时为具体来源，否则 `unknown` |
| `other` | `other` | `null` |
| 未识别字符串 | `other` | 保留原始 hint 或 `null` |

`unsupported-cluster-log` 原状态为 `unsupported-source` 且仍无法解释时间格式时继续保持该状态；已识别原始时间但时区、偏差或解析仍需确认时可改为 `needs-review`；只有得到可信 `normalized_timestamp` 时才可改为 `ready`。不得无条件把 `unsupported-source` 改为 `needs-review`。

#### Normalization status

| `normalization_status` | 含义 | 处理 |
|---|---|---|
| `ready` | 时间已可信地标准化 | 必须保留非空 `normalized_timestamp` 和可回指依据 |
| `needs-review` | 解析、时区或偏差仍需确认 | 尝试依据化解析，失败时保留原始时间 |
| `unsupported-source` | 当前来源或格式不支持可靠解析 | 保留原始时间，`normalized_timestamp` 可以为 `null` |

`ready` 但 `normalized_timestamp=null` 时降级为 `needs-review` 并记录真实 basis 或 anomaly。缺少状态时默认 `needs-review`。状态本身不是 basis；所有时间调整、时区补充和 clock skew 修正都必须有真实依据。不得无依据假设 UTC、系统本地时区或 `+08:00`。

#### Response payload

```yaml
payload:
  data_sources:
    - source_id: string
      source_type_hint: string
      path: string|null
      source_artifact_id: artifact-<uuid>|null
      timezone_hint:
        offset: string|null
        name: string|null
        assumption: string|null
      parser_hint: string|null

  time_range:
    start: ISO8601|null
    end: ISO8601|null
    basis:
      - string

  timeline:
    - timeline_event
  event_count: integer
  source_count: integer

  gaps:
    - gap

  anomalies:
    - anomaly

  conflicts:
    - conflict
```

`event_count = len(timeline)`。`source_id` 必须唯一，`source_count` 等于 `data_sources` 中唯一 `source_id` 的数量。

#### Conflicts

```yaml
conflicts:
  - conflict_id: conflict-<uuid>
    conflict_type: timestamp-conflict|timezone-conflict|clock-skew-conflict|event-detail-conflict
    event_refs:
      - tl-<uuid>
    description: string
    resolution_status: unresolved|preserved-both|preferred-with-basis
    preferred_event_ref: tl-<uuid>|null
    artifact_refs:
      - artifact-<uuid>
    ledger_event_refs:
      - led-<uuid>
    basis:
      - string
    confidence: high|medium|low
```

`event_refs` 至少引用两个存在的 Timeline Event，冲突事件全部保留。`preferred-with-basis` 时 `preferred_event_ref` 必须非空、属于 `event_refs` 且 `basis` 非空；`unresolved` 和 `preserved-both` 时 `preferred_event_ref` 为 `null`。不得通过删除事件解决冲突。

#### Gaps

```yaml
gaps:
  - gap_id: gap-<uuid>
    gap_type: time-gap|source-gap|event-gap
    start_time: ISO8601|null
    end_time: ISO8601|null
    affected_sources:
      - string
    description: string
    impact: informational|potential-missing-evidence|blocks-timeline
    artifact_refs:
      - artifact-<uuid>
    ledger_event_refs:
      - led-<uuid>
    basis:
      - string
    confidence: high|medium|low
```

`affected_sources` 只能引用 Request 中存在的 `data_sources.source_id`。普通日志缺失不能自动证明相关事件不存在；`blocks-timeline` 必须有明确证据说明缺口阻止核心 Timeline 建立；gap 不能替代原始事件。

#### Anomalies

```yaml
anomalies:
  - anomaly_id: anomaly-<uuid>
    anomaly_type: duplicate-candidate|outlier|missing-timestamp|unparsable|other
    event_refs:
      - tl-<uuid>
    description: string
    severity: low|medium|high
    artifact_refs:
      - artifact-<uuid>
    ledger_event_refs:
      - led-<uuid>
    basis:
      - string
    confidence: high|medium|low
```

`event_refs` 必须引用已存在 Timeline Event；`duplicate-candidate` 至少引用两个事件。疑似重复、缺失时间和不可解析时间的事件全部保留，anomaly 不能作为删除理由。无法构造正式 Event 的候选只有在 anomaly 能引用已存在关联 Event 时才写 anomaly，否则写 blocker。

#### Stable merge

1. `normalized_timestamp` 非空的事件按时间升序排列。
2. 时间相同的事件保持稳定输入顺序。
3. `normalized_timestamp=null` 的事件放在末尾。
4. 不进行破坏性去重。
5. 疑似重复、冲突、unsupported source、无法解析时间和时区不确定的事件全部保留。
6. 不静默覆盖原始时间，不将 inferred 伪装成 observed。

#### Stage 0-6

| Stage | 名称 | 主要输出 |
|---|---|---|
| 0 | Input and Scope Validation | 可处理候选、blocker、引用缺失记录、来源清单 |
| 1 | Source Mapping | 已映射候选、unsupported source 说明、映射 basis |
| 2 | Time Normalization | 标准化候选、状态、时间异常及时区/偏差依据 |
| 3 | Conflict and Gap Detection | `conflicts`、`gaps` |
| 4 | Timeline Event Construction | 未排序 Timeline Event、无法构造事件的 anomaly 或 blocker |
| 5 | Stable Merge and Anomaly Detection | 排序后 `timeline`、`anomalies`、`event_count` |
| 6 | Response and Handoff | 完整 Response、必要 Handoff、route 和 execution gate 状态 |

#### Route status semantics

`route_record.route_status` 只能是 `active|completed|blocked|failed|cancelled`，不得写入 `partial` 或创建替代状态：

- Timeline 已完成但证据存在缺口、冲突或异常时使用 `completed`，并在 Investigation Summary、`gaps`、`anomalies` 和 `conflicts` 中记录不完整性；
- 已创建待处理 Handoff 且整条 Route 仍继续时使用 `active`；
- 缺少关键证据且无法继续时使用 `blocked`；
- 不可恢复的处理错误使用 `failed`；
- 只有明确取消任务时使用 `cancelled`；
- 可恢复的部分结果通过已有 Timeline payload、Finding、Handoff 和证据记录表达，不新增状态字段。

#### Evidence and handoff rules

- 每个 observed Event 必须有直接来源 Artifact；每个 inferred Event 必须有非空 basis 或 Ledger Event；
- Artifact、Ledger Event 和 Finding 引用必须来自 Request、上游输出或本任务真实生成物并可回查；
- 时间修正必须保留依据，原始 Artifact 保持只读，negative Finding 必须有证据回指；
- 普通解析失败、单条时区不确定和单个 unsupported source 不自动触发 execution gate；
- Timeline Skill 不重新执行领域取证、不自行建立远程 Session；
- 需要额外采集或重新分析时，在 `route_record.handoffs` 创建证据化 Handoff；Route 继续时使用 `route_status=active`，完成后把 Timeline 交给 `answer-gate`；
- 输出限制达到时停止扩展并保留已完成结果；可恢复 Handoff 继续 Route 时使用 `active`，缺少关键证据且无法继续时使用 `blocked`。

### 8.11 uncommon-media-triage

`uncommon-media-triage` 是 Phase 3 第一个已实现模块。它复用现有 Request Envelope、Response Envelope、Route Record、Artifact Record、Finding Record 和 Ledger Event，不定义新的 Schema。结构分析专用字段全部放在现有 `request.payload` 和 Response `payload` 中。

#### Request payload

```yaml
payload:
  source_artifact_refs:
    - artifact-<uuid>
  candidate_regions:
    - region_id: string
      source_artifact_ref: artifact-<uuid>
      derived_artifact_ref: artifact-<uuid>|null
      offset: integer
      length: integer
      sampling_method: string
  upstream_signature_hits: array
  upstream_sampling_results: array
  entropy_summary: object|null
  structure_hints: array
  requested_checks: array
  analysis_limits:                 # optional
    max_regions: integer|null
    max_bytes_per_region: integer|null
    max_total_bytes: integer|null
    max_slice_bytes: integer|null
    timeout_seconds: integer|null
```

Request 约束：

- 定义 `effective_source_artifact_refs`：非空 `request.payload.source_artifact_refs` 优先；该字段缺失或为空数组时使用 `request.material_info.artifact_refs`。空数组与缺失等价。
- `effective_source_artifact_refs` 必须非空，每个引用必须能解析到 Artifact Record；每个 region 的 `source_artifact_ref` 必须属于该列表。
- `candidate_regions` 必须存在且非空；每个 region 必须回指 source Artifact。Router 没有至少一个合法 bounded region 时不得选择 uncommon。
- `derived_artifact_ref` 非空时必须能解析到 Artifact Record，其 `source_artifact_id` 必须等于 region 的 `source_artifact_ref`。
- `offset` 必须是 `>= 0` 的整数，`length` 必须是正整数；不得接受十六进制字符串、带单位字符串或其他文本格式。source Artifact Record 的 `size` 必须是已知的非负整数，才能验证 `offset + length <= source Artifact size`；size 缺失、为 `null` 或类型无效时不得调用 uncommon，并记录 `required_next_action`。
- 1GB+ source 必须先经过 `large-artifact-strategy`，uncommon 只接收 bounded region 或派生 slice。
- `entropy_summary`、文件扩展名、设备名称、品牌、单个 magic、单个时间戳或单个坐标不能独立支持路线。
- Router 调用 uncommon 时，`request.context` 必须包含当前 Route Record；`visited_skills` 已包含 uncommon 时不得再次选择。
- `analysis_limits` 为 Recommended。缺失时只读取已提供 regions，不扩大 offset/length、不请求新 slice、不执行全文件扫描，并在 Response payload 记录 `limits_source: implicit-bounded-input`。
- 所有非空显式 limit 必须是正整数：`max_regions > 0`、`max_bytes_per_region > 0`、`max_total_bytes > 0`、`max_slice_bytes > 0`、`timeout_seconds > 0`。字段为 `null` 或缺失时，不应用该项限制；非空但非整数或小于等于 0 时不得调用 uncommon。
- 显式 `analysis_limits` 按字段分别校验：`candidate_regions` 数量 `<= max_regions`；每个 `region.length <= max_bytes_per_region`；所有 `region.length` 总和 `<= max_total_bytes`；实际运行时间 `<= timeout_seconds`。
- `max_slice_bytes` 生效且 `derived_artifact_ref` 非空时，必须解析对应派生 Artifact Record，并验证 `derived Artifact Record.size <= max_slice_bytes`。不得新增或读取 `slice.length`；派生 Artifact size 为 `null`、类型无效或 Artifact 无法解析时，不能通过该项输入校验。
- 非空 `timeout_seconds` 必须能在调用时强制执行并持续记录实际运行时间；无法强制 timeout 时不得调用 uncommon。
- 任一显式限制超出时不得开始或继续 uncommon，必须记录具体超限字段、实际值、限制值和 `required_next_action`。
- 任何 effective source 缺失、Artifact 无法解析、region 归属冲突或派生关系冲突，都禁止调用 uncommon，并记录具体原因和 `required_next_action`。

#### Request payload transfer chain

1. `file-triage` 发现结构候选时必须输出非空 `candidate_regions`，按 `effective_source_artifact_refs` 验证 source 归属和派生关系；没有合法 region 时不得建议 uncommon。
2. 1GB+ 材料由 `large-artifact-strategy` 向 Router 提供 `source_artifact_refs`、`candidate_regions`、`upstream_signature_hits`、`upstream_sampling_results`、`entropy_summary`、`structure_hints` 和存在时的 `analysis_limits`，并执行相同的 source 归属检查。
3. `forensic-router` 验证 region 非空、字段完整、来源可回查和边界合法。输入不足时返回 `file-triage` 或 `large-artifact-strategy` 补充 bounded Evidence，不创建 uncommon Route Step 或 Handoff。
4. Router 选择 uncommon 时原样保存并传递 Request payload，同时传递包含当前 Route Record 的 context。
5. `forensic-autopilot` 只执行 Router 决策，不重复结构阈值；它把 Router 批准的 payload 和 context 原样交给 `uncommon-media-triage`。
6. uncommon 对缺失或空的 `source_artifact_refs` 回退到 `request.material_info.artifact_refs`；缺少显式 limits 时应用 `implicit-bounded-input`。

#### Response payload

```yaml
payload:
  region_assessments:
    - region_id: string
      source_artifact_ref: artifact-<uuid>
      derived_artifact_ref: artifact-<uuid>|null
      offset: integer
      length: integer
      structure_type: fixed_record|tlv|can_like|can_container|nmea|gps_track|sensor_record|time_series|custom_database_page|unknown
      classification_status: valid|plausible|weak_candidate|rejected|unknown
      confidence: high|medium|low
      candidate_record_sizes: array
      candidate_schema: object|null
      key_fields: array
      boundary_evidence: array
      validation_checks: array
      counter_evidence: array
      artifact_refs:
        - artifact-<uuid>
      finding_refs:
        - finding-<uuid>
      ledger_event_refs:
        - led-<uuid>
  structure_type: string
  classification_status: valid|plausible|weak_candidate|rejected|unknown
  candidate_record_sizes: array
  candidate_schema: object|null
  key_fields: array
  boundary_evidence: array
  validation_checks: array
  counter_evidence: array
  route_candidates:
    - candidate_skill: string
      route_basis: array
      artifact_refs:
        - artifact-<uuid>
      finding_refs:
        - finding-<uuid>
      confidence: high|medium|low
      current_availability: executable|pending
      required_next_action: string
  excluded_routes: array
  sampling_requests: array
  unresolved_questions: array
  limits_source: explicit|implicit-bounded-input
```

Response 中每个 `region_assessments.offset` 必须是与 Request 对应 region 一致的非负整数；不得输出十六进制、带单位或其他文本 offset。

`uncommon-media-triage` 遇到 PCAP、浏览器历史或完整移动设备材料时，只能写入 `excluded_routes`，生成同时引用相关 Artifact 和本轮 Ledger Event 的 scope-limitation Finding，并返回 `forensic-autopilot`；只有需要消费者重评时才返回 `forensic-router`。领域 Skill 不得设置 `route_decision: no-compatible-skill`，该决策只能由 `forensic-router` 产生。

#### Classification and confidence

- `classification_status` 只表达候选结构验证状态，取值固定为 `valid|plausible|weak_candidate|rejected|unknown`。
- `confidence` 只表达 Evidence 对 Finding、region assessment 或 route candidate 的支持强度，取值固定为 `high|medium|low`。
- `classification_status` 不得写入 Finding confidence、`route_status`、Route Step status、Handoff status 或 `execution_gate`。
- `candidate_schema` 是候选解释，必须保留 Evidence、反证和未决问题；不得表示最终格式确认。

| classification_status | 判定规则 |
|---|---|
| `valid` | 核心结构约束全部通过，可跨多个记录复现，无实质反证 |
| `plausible` | 核心关系成立，但样本数量、checksum 或部分字段仍不足 |
| `weak_candidate` | 存在结构信号，但缺少第二类独立 Evidence |
| `rejected` | 边界、长度、checksum、字段关系或跨记录一致性明确失败 |
| `unknown` | Evidence 不足，既不能支持也不能排除 |

上述判定不改变 `confidence` 的含义；`high|medium|low` 仍只表达 Evidence 对 Finding、region assessment 或 route candidate 的支持强度。

#### Recovery route candidates

`proprietary-format-recovery` 当前已可执行。uncommon 只能在 `payload.route_candidates` 中生成候选，不能直接调用。route candidate 本身只包含消费者声明、路由依据、Evidence、availability、confidence 和 next action：

- `candidate_skill: proprietary-format-recovery`；
- `route_basis`、`artifact_refs` 和 `finding_refs` 非空且可回查；
- `confidence` 使用 `high|medium|low`；
- `current_availability: executable`；
- `required_next_action` 指向 Router 的完整输入与 Gate 校验。

同层顶级 transfer `payload` 才承载完整 proprietary profile：非空 `candidate_regions`、非空 `candidate_schema` 或 `upstream_structure_hints`、本轮 `ledger_event_refs`、三个 candidate arrays、`requested_checks` 和 `analysis_limits`。三个 arrays 均遵循 8.12 item profile，`candidate_usability` 只用 `executable|hint-only`；请求 candidate validation 时提供正整数 `max_candidate_checks`，缺失或为 `null` 时只允许结构恢复并设置预算 `required_next_action`。route candidate 不得嵌套或替代这份顶层 profile。

候选本身不是 proprietary Route Step、Handoff 或调用记录。uncommon 必须通过既有 bounded Router re-entry 返回 Router；只有 Router 校验完整 payload、Route context、`visited_skills`、hop、candidate usability、material Artifact、candidate check budget、limits 和 Gate 后，才能创建正式 proprietary Handoff。只有 hint-only candidates 时，必须另有无需 key/plaintext validation 的可执行布局恢复任务。

`firmware-iot-forensics` 当前已可执行。uncommon 只能生成 `current_availability: executable` 的 firmware route candidate，不能直接调用。candidate 按 8.13 附 bounded regions、结构 Evidence、Artifact、Finding 和 uncommon 本轮 Ledger Event；单个 magic、扩展名、品牌、设备名或熵值不能生成 executable candidate。只有 Router 校验最低输入、Route context、`visited_skills`、hop、limits 和 Gate 后，才能创建正式 firmware Handoff。

`nas-raid-encrypted-storage` 当前已可执行。uncommon 只有在独立 RAID/LVM/pool/多成员文件系统或加密卷具有 bounded regions、member/layer Evidence 和核心引用时，才可生成 `current_availability: executable` 的 storage candidate；PVE/Ceph/vSphere/vSAN、VM/container/snapshot/虚拟磁盘映射、已有 `cluster-virtualization-forensics` Route 或明确拥有重组任务的 server rebuild plan 仍交 server/cluster。服务器文件系统尚未暴露且 storage 是前置层时不排除该 candidate。共享字段引用 8.14；uncommon 不直接调用，由 Router 完成校验。

`malware-forensics` 当前已可执行。uncommon 只有在有效样本或 bounded payload 具有明确恶意分析目标或独立可疑上下文，并附 source/region、Hash 状态、Artifact/Finding 和本轮 Ledger Event 时，才可生成 `current_availability: executable` 的 candidate。普通 PE、ELF、脚本、宏、APK 或固件组件不自动转出；uncommon 不直接调用，由 Router 按 8.15 校验。

#### Bounded Router re-entry

bounded re-entry 只指 uncommon 发出的单向 Router 重评 Handoff：

`uncommon-media-triage` → `forensic-router`

该 Handoff 最多允许一次，并且必须同时满足：

1. uncommon 产生新的 Artifact 或 Finding；
2. Handoff 的 `new_evidence_refs` 非空，且每个引用都指向 uncommon 本轮产生的新 Ledger Event；
3. `reentry_reason` 明确说明新 Evidence 如何改变路线；
4. `visited_skills`、`hop_count` 和 `routing_policy.max_hops` 合法；
5. 同一 route 和 evidence scope 未执行过 uncommon → Router re-entry。

没有新 Evidence 时禁止 re-entry。Router 收到 Handoff 时 `visited_skills` 已包含 `uncommon-media-triage`，因此不得再次选择 uncommon；proprietary、firmware 或 storage 输入完整时可选择对应消费者并将其加入 `visited_skills`，输入不足时只能在合法 hop/visited 范围内请求 `large-artifact-strategy` 补充 bounded Evidence，否则返回 `forensic-autopilot`，且不创建半完整 Handoff。

普通路由、bounded read，以及显式 `analysis_limits` 或 `implicit-bounded-input` 内的静态结构验证使用 `execution_gate.required=false`。状态改变或授权范围扩张时使用 `execution_gate.required=true`，并填写非空 `reason`；Gate 不使用 `classification_status` 表达状态。

### 8.12 proprietary-format-recovery

`proprietary-format-recovery` 是 Phase 3 第二个已实现模块。它复用现有 Request Envelope、Response Envelope、Route Record、Artifact Record、Finding Record 和 Ledger Event，不新增 JSON Schema。它只对 Router 批准的 bounded regions 做专有容器布局恢复、有限 transform/key/plaintext 验证和已验证边界内的 carving。

#### Request payload profile

```yaml
payload:
  source_artifact_refs:
    - artifact-<uuid>
  candidate_regions:
    - region_id: string
      source_artifact_ref: artifact-<uuid>
      derived_artifact_ref: artifact-<uuid>|null
      offset: integer
      length: integer
      sampling_method: string
  upstream_region_assessments: array
  upstream_structure_hints: array
  candidate_schema: object|null
  route_basis: array
  artifact_refs:
    - artifact-<uuid>
  finding_refs:
    - finding-<uuid>
  ledger_event_refs:
    - led-<uuid>
  header_hints: array
  directory_table_hints: array
  block_table_hints: array
  index_table_hints: array
  record_boundary_hints: array
  transform_hypotheses:
    - candidate_id: string
      transform_type: string
      parameters: object
      target_region_ids:
        - string
      evidence_refs:
        - artifact-<uuid>|finding-<uuid>|led-<uuid>
      candidate_usability: executable|hint-only
  key_material_candidates:
    - candidate_id: string
      candidate_type: string
      material_artifact_ref: artifact-<uuid>|null
      fingerprint: string
      target_region_ids:
        - string
      evidence_refs:
        - artifact-<uuid>|finding-<uuid>|led-<uuid>
      candidate_usability: executable|hint-only
  known_plaintext_candidates:
    - candidate_id: string
      material_artifact_ref: artifact-<uuid>|null
      fingerprint: string
      encoding: string
      target_region_ids:
        - string
      evidence_refs:
        - artifact-<uuid>|finding-<uuid>|led-<uuid>
      candidate_usability: executable|hint-only
  counter_evidence: array
  requested_checks: array
  analysis_limits:                       # optional
    max_regions: integer|null
    max_bytes_per_region: integer|null
    max_total_bytes: integer|null
    max_slice_bytes: integer|null
    timeout_seconds: integer|null
    max_candidate_checks: integer|null
```

Request 约束：

1. `request.context` 必须包含当前 Route Record；`visited_skills` 已包含 `proprietary-format-recovery` 时 Router 不得再次选择。
2. 定义 `effective_source_artifact_refs`：非空 `source_artifact_refs` 优先；该字段缺失或为空数组时使用 `request.material_info.artifact_refs`。结果必须非空，且每个引用都能解析到 Artifact Record。
3. `candidate_regions` 必须存在且非空。每个 region 的 `source_artifact_ref` 必须属于 effective source。
4. `offset` 必须是 `>= 0` 的整数，`length` 必须是正整数；不得接受十六进制字符串、带单位字符串或其他文本格式。
5. source Artifact Record 的 `size` 必须是已知非负整数；`offset + length` 只能与对应 source size 比较且不得越界。
6. `derived_artifact_ref` 非空时必须解析到 Artifact Record，其 `source_artifact_id` 必须匹配 region source，且 Record `size` 可验证。
7. 所有 Artifact、Finding 和 Ledger Event 引用必须存在且可回查。
8. 至少存在一种 recovery-specific Evidence：header/directory/block/index/record boundary hint、upstream region assessment、candidate schema、有限 transform/key/plaintext candidate 或相应 validation Evidence。
9. 扩展名、设备名、单个 magic、单独熵值或外部资料不能独立触发该 Skill。
10. 所有非空显式 limit 字段必须是正整数。`max_regions`、`max_bytes_per_region`、`max_total_bytes`、`max_slice_bytes` 和 `timeout_seconds` 沿用 uncommon profile 的逐项验证与 timeout 规则。
11. `max_slice_bytes` 生效且 `derived_artifact_ref` 非空时，使用派生 Artifact Record 的 `size` 校验；不得新增或读取 `slice.length`。
12. 三个 candidate arrays 的 item 必须包含上述全部字段；`candidate_usability` 只能是 `executable|hint-only`。candidate ID 必须非空且在各自数组唯一，`target_region_ids` 必须非空并解析到 Request candidate region，`evidence_refs` 必须非空且可回查。
13. executable candidate 必须具有实际验证所需的数据。所有非空 `material_artifact_ref` 必须解析到 Artifact Record；只有 fingerprint、没有可解析 material Artifact 的 key/plaintext candidate 固定为 hint-only。原始 key、敏感 plaintext 和 token 只存放于受保护派生 Artifact，正文只保留引用和 fingerprint。
14. hint-only candidate 可以支持 Hypothesis、Finding 或 `required_next_action`，但不得参与自动 transform/key/plaintext validation，也不进入 candidate check 组合。
15. 一次 `candidate_check` 固定为一个实际执行组合：一个 candidate region、一个 executable transform candidate、零或一个 executable key candidate、零或一个 executable known-plaintext candidate。每执行一个不同组合，计数加一，并对应一个唯一 `check_id`。
16. 请求执行 candidate validation 时，`max_candidate_checks` 必须存在且为正整数；执行前计划组合总数和实际执行数都不得超过该值。无法证明计划组合数时不得开始候选验证。
17. `max_candidate_checks` 缺失或为 `null` 时仍可执行 header、table、layout、record boundary 和 `candidate_schema` 恢复，但不得执行 transform/key/plaintext candidate validation；设置 `required_next_action` 要求提供正整数候选检查预算。不得仅凭数组有限自动执行。

`analysis_limits` 整体缺失时记录 `limits_source: implicit-bounded-input`，只读取已提供 regions、不扩大 offset/length、不请求新 slice，并且不执行 transform/key/plaintext candidate validation。提供显式 limits 时记录 `limits_source: explicit`。任一适用显式限制无效、无法强制或实际超限时不得执行对应受限动作，并记录字段、实际值、限制值和 `required_next_action`。

#### Response payload profile

```yaml
payload:
  region_assessments: array
  format_hypotheses: array
  container_layout_candidates: array
  header_assessments: array
  directory_table_candidates: array
  block_table_candidates: array
  index_table_candidates: array
  record_boundary_candidates: array
  transform_hypotheses: array
  key_hypotheses: array
  key_verification_results: array
  known_plaintext_checks: array
  candidate_schema: object|null
  field_mappings: array
  validation_checks:
    - check_id: string
      region_id: string
      transform_candidate_id: string
      key_candidate_id: string|null
      plaintext_candidate_id: string|null
      started_at: ISO8601
      ended_at: ISO8601
      result: string
      evidence_refs:
        - artifact-<uuid>|finding-<uuid>|led-<uuid>
  counter_evidence: array
  carved_artifact_refs:
    - artifact-<uuid>
  recovered_artifact_refs:
    - artifact-<uuid>
  excluded_routes: array
  route_candidates: array
  unresolved_questions: array
  required_next_action: string|null
  limits_source: explicit|implicit-bounded-input
  recovery_status: candidate_only|structure_reproduced|key_candidate|key_verified|recovery_reproduced|rejected|unknown|bounded_checks_exhausted
```

每个实际执行的 candidate check 都必须生成一条上述 `validation_checks` 记录。`check_id` 每次执行唯一；region 和 candidate ID 必须解析到本 Request，所有被执行 candidate 的 usability 必须为 executable。candidate check 实际执行数等于本轮此类记录数；计划组合总数、实际执行数和 `max_candidate_checks` 一并记录。hint-only candidate 不得出现在这些 ID 字段中。

#### Recovery status

`recovery_status` 只允许以下八个值：

| recovery_status | 含义 |
|---|---|
| `candidate_only` | 存在恢复候选，但尚未复现结构或变换 |
| `structure_reproduced` | 布局或字段结构已在多个记录中复现 |
| `key_candidate` | 存在有限 key Hypothesis，尚未通过独立验证 |
| `key_verified` | key 在批准范围内通过至少两类独立验证，但完整恢复尚未复现 |
| `recovery_reproduced` | 恢复步骤可重复执行，输出经 parser 或独立结构检查验证 |
| `rejected` | 当前批准范围内所有相关 Hypothesis 都已明确证伪，且没有存活候选 |
| `unknown` | 输入或 Evidence 不足，或批准检查尚未全部执行 |
| `bounded_checks_exhausted` | 所有批准检查已完成，仍有无法在当前范围内验证或证伪的存活候选 |

`recovery_status` 不能写入 Finding confidence、Route Step status、Handoff status、`route_status` 或 `execution_gate`。Finding、route candidate 和 key Hypothesis 的 Evidence confidence 仍只使用 `high|medium|low`。不得扩展第九种 recovery status。

整体 `recovery_status` 每轮只能选择一个值。存在正面结果时按以下固定优先级选择最高项：

`recovery_reproduced` > `key_verified` > `structure_reproduced` > `key_candidate` > `candidate_only`

- `recovery_reproduced`：恢复步骤已复现，且输出通过 parser 或独立结构检查。
- `key_verified`：key 通过至少两类独立验证，但完整恢复尚未复现。
- `structure_reproduced`：布局或字段关系已经复现，即使仍存在未验证 key candidate。
- `key_candidate`：尚未复现结构或完整恢复，但存在存活的有限 key Hypothesis。
- `candidate_only`：仅存在恢复候选，尚无更高等级结果。

没有正面状态时才使用 fallback：所有相关 Hypothesis 均被明确证伪且无存活候选时选择 `rejected`；所有批准检查完成但仍有无法在当前范围内验证或证伪的存活候选时选择 `bounded_checks_exhausted`；输入/Evidence 不足或批准检查尚未全部执行时选择 `unknown`。单个 Hypothesis rejected 不得自动导致整体 `rejected`；单项失败必须写入 `counter_evidence`、`validation_checks` 和 `excluded_routes`。状态选择依据必须记录在 `investigation_summary` 或 `validation_checks`。

#### Key material minimum disclosure

`key_hypotheses` 每项至少包含：

```yaml
key_hypotheses:
  - candidate_id: string
    candidate_type: string
    fingerprint: string
    material_artifact_ref: artifact-<uuid>|null
    verification_status: string
    evidence_refs:
      - artifact-<uuid>|finding-<uuid>|led-<uuid>
    confidence: high|medium|low
```

- 原始 key、口令、token、个人数据和敏感明文不得默认写入 Response、Finding 或 Ledger Event 正文。
- 需要保留的原始 material 写入受保护派生 Artifact；Response 只记录 Artifact 引用和 fingerprint。
- 文件名、外部资料或单个明文命中不能独立产生 `key_verified`。
- `key_verified` 至少需要两类独立验证依据，例如 transform 后结构闭合与独立 checksum/parser 验证。

#### Bounded carving

自动 carving 只有同时满足以下条件才允许：

1. 数据块由已验证 header、directory/block/index table 或 record boundary 指向。
2. source Artifact、offset 和 length 均可回查。
3. region 完全位于已批准 `candidate_regions` 内。
4. 单个派生 Artifact Record 的 `size` 不超过适用的 `max_slice_bytes`。
5. 总读取量不超过适用的 `max_total_bytes`。
6. 输出数量和范围有限，且写入批准工作目录。
7. 每个输出生成派生 Artifact Record、Hash 和匹配的 `source_artifact_id`。
8. original Artifact 保持只读。

缺少已验证边界、需要全源 carving、批量恢复或扩大范围时必须进入 Execution Gate，不得先执行。

#### Handoff and transfer chain

正式链路固定为：

`uncommon-media-triage` → `forensic-router` → `proprietary-format-recovery`

1. uncommon 只输出 `current_availability: executable` 的 proprietary route candidate，不直接调用消费者。
2. uncommon candidate 对应的顶层 `request.payload` 必须原样保留完整 proprietary profile，包括非空 `candidate_regions`、`candidate_schema` 或 `upstream_structure_hints`、三个 candidate arrays 的完整 item profile，以及 route basis、Artifact、Finding 和 uncommon 本轮 Ledger Event 引用；`route_candidates` 项只声明消费者与 availability，不嵌套或替代该 profile。
3. uncommon 通过现有、最多一次的 bounded re-entry 返回 Router。
4. Router 是唯一消费者决策点。它验证完整 payload、Route context、`visited_skills`、hop、candidate usability、material Artifact、candidate check budget、limits 和 Gate；至少存在一个可解析 executable candidate，或存在无需 key/plaintext validation 的可执行布局恢复任务时，才创建 proprietary Route Step/Handoff 并加入 `visited_skills`。只有 hint-only candidates 时可以执行明确布局任务，但不得声明或执行 key/plaintext validation；若也无布局任务，则不创建 Handoff。
5. 首次路由且 uncommon 尚未访问时，输入不足可返回 uncommon；已完成 uncommon bounded re-entry 后不得再次选择 uncommon，只能在合法 hop/visited 范围内请求 `large-artifact-strategy` 补充 bounded Evidence，否则返回 autopilot。任何分支都不创建半完整 Handoff。
6. autopilot 只执行 Router 返回的 proprietary 决策，原样传递 payload 和 Route context，不维护 recovery-specific 阈值。
7. `large-artifact-strategy` 只提供 bounded regions 和 Evidence，不能决定或直接调用 proprietary。
8. proprietary 完成且没有新消费者时返回 autopilot，进入 Answer Gate。

#### Execution Gate boundary

在现有授权、批准工作目录、candidate regions 和适用 limits 内，下列动作使用 `execution_gate.required=false`：

- 已有 candidate region 内的 bounded read。
- header、table、offset、length 和 checksum 验证。
- Request item profile 完整、usability 为 executable、material 可解析且有显式 `max_candidate_checks` 预算的 transform/key candidates。
- Request item profile 完整、usability 为 executable、material 可解析且有显式 `max_candidate_checks` 预算的 known-plaintext candidates。
- 字节序、编码、字段 offset 和 parser 一致性验证。
- 已验证边界内的 bounded carving。
- 在批准工作目录内创建有限派生 Artifact。
- 当前 limits 内登记 Artifact、Finding 和 Ledger Event。
- 返回 Router 重评。

自动 candidate validation 必须同时满足：候选由 Request 明确提供且 usability 为 executable；material Artifact 可解析；不生成新候选；不扩展字典；不枚举 keyspace；只读批准 regions；`max_candidate_checks` 存在且为正整数；计划组合总数与实际执行数都不超过该 budget；不超过 `max_total_bytes`、`max_slice_bytes` 和 `timeout_seconds`；输出位于批准工作目录；不修改 original Artifact。`max_candidate_checks` 缺失或为 `null` 时不执行 transform/key/plaintext candidate validation，但可继续结构恢复并设置要求预算的 `required_next_action`。

下列动作必须设置 `execution_gate.required=true` 并填写非空 `reason`：

- 生成、枚举或爆破 keyspace；字典扩展或组合候选。
- 长时间恢复、长时间解密或批量 key 测试。
- 全文件扫描、全量 strings 或全源 known-plaintext 搜索。
- 超出 candidate regions 的读取。
- 大范围 carving、批量恢复或超出 analysis limits。
- 安装工具或依赖。
- 联网、在线检索或上传第三方。
- 执行程序、脚本、宏或固件；动态分析或沙箱。
- RAID/LVM 激活、解锁或 mount。
- 修改 original Artifact。
- 向未批准路径持久化恢复结果。

#### Route candidates and loop prevention

- firmware 当前已可执行。proprietary 只有生成已验证嵌套固件派生 Artifact，并附可验证 Hash/size/直接来源、container layout、Artifact/Finding 和本轮 Ledger Event 时，才可生成 `current_availability: executable` 的 firmware candidate；proprietary 不直接调用 firmware，必须通过 Router 重评。
- storage 当前已可执行。proprietary 只有生成合法嵌套存储容器、独立卷或阵列成员 Artifact，并附可回查 provenance、明确 Hash 状态、bounded regions、层级 Evidence 和本轮 Ledger Event 时，才可生成 `current_availability: executable` 的 storage candidate；大型或虚拟 Artifact 可为 `deferred|unavailable`，必须通过 Router 按 8.14 重评，不得直接调用。
- malware 当前已可执行。proprietary 只有恢复出独立样本或 payload Artifact，并附直接来源、明确 Hash 状态、有效区域、分析目标或可疑上下文及本轮 Evidence 时，才可生成 `current_availability: executable` 的 candidate；必须返回 Router 按 8.15 重评，不得直接调用。
- uncommon → Router re-entry 最多一次；Router 选择 proprietary 后加入 `visited_skills`。
- proprietary 默认返回 autopilot。只有本轮产生新 Artifact 或 Finding 时，才可最多一次返回 Router。
- proprietary → Router Handoff 必须包含非空 `reentry_reason`、非空 `new_evidence_refs`、本轮新 Ledger Event，以及合法 `hop_count` 和 `routing_policy.max_hops`。
- Router 重评后不得再次选择 `uncommon-media-triage` 或 `proprietary-format-recovery`。
- 禁止 uncommon → Router → proprietary → Router → uncommon。
- 禁止 proprietary → Router → proprietary。
- 禁止 proprietary → Router → firmware → Router → proprietary。
- 禁止 firmware → Router → firmware。
- 禁止 uncommon → Router → firmware → Router → uncommon。
- 没有其他当前可执行消费者时返回 autopilot。

### 8.13 firmware-iot-forensics

`firmware-iot-forensics` 是 Phase 3 第三个已实现模块。它复用现有 Request Envelope、Response Envelope、Route Record、Artifact Record、Finding Record 和 Ledger Event，不新增 JSON Schema。它只对 Router 批准的 source、bounded regions 和已验证派生 Artifact 做固件 container/layout/filesystem 静态分析，并在明确的 analysis/extraction limits 内执行有限提取。

#### Request payload profile

```yaml
payload:
  source_artifact_refs:
    - artifact-<uuid>
  candidate_regions: array
  route_basis: array
  artifact_refs: array
  finding_refs: array
  ledger_event_refs: array
  analysis_limits: object|null
  container_hints: array
  architecture_hints: array
  filesystem_hints: array
  partition_hints: array
  extraction_limits:                 # required for extraction
    max_depth: integer
    max_components: integer
    max_total_extracted_bytes: integer
    max_single_component_bytes: integer
    timeout_seconds: integer
```

Request 约束：

1. `request.context` 必须包含当前 Route Record；同一 route 和 evidence scope 不得再次选择已访问的 firmware Skill。
2. effective source 必须非空且可解析。二进制或 container 输入必须具有非空 bounded regions；source、offset、length、size 和派生来源关系必须合法。1GB 以上 source 先经过 `large-artifact-strategy`。
3. Artifact、Finding、Ledger Event 和 route basis 必须可回查。direct route 至少需要两类不同验证机制；扩展名、品牌、设备名、单个 magic、熵值或外部资料不计入该阈值。
4. uncommon transfer 提供 bounded regions、结构 Evidence 和本轮引用；proprietary transfer 还提供已验证嵌套固件 Artifact、直接来源、完整 Hash 和对应 Evidence。二者都只返回 Router。
5. `analysis_limits` 复用现有 bounded region profile。有限提取要求 `extraction_limits` 的五个字段全部存在且为正整数；缺少、无效或工具无法保证时，只允许静态识别并设置 `required_next_action`。
6. 有限提取必须位于批准工作目录，遵守深度、组件数、总输出大小、单组件大小和超时限制。不得路径越界、跟随链接、创建宿主机特殊文件或恢复危险权限。

#### Response payload profile

```yaml
payload:
  firmware_assessments: array
  component_inventory: array
  filesystem_candidates: array
  extracted_component_refs: array
  security_finding_refs: array
  validation_checks: array
  counter_evidence: array
  unresolved_questions: array
  required_next_action: string|null
  firmware_status: candidate_only|container_validated|layout_reproduced|filesystem_validated|extraction_reproduced|rejected|bounded_checks_exhausted|unknown
```

payload 不复制 Finding 对象。`security_finding_refs` 只能引用 Response 顶层 Finding。`component_inventory` 记录 container、partition、filesystem、bootloader、kernel、rootfs 和其他组件的层级、角色及 Evidence；每个派生 Artifact 使用现有 Artifact Record 记录直接来源和完整 Hash，并由 Ledger Event 记录产生或验证动作。

#### Firmware status

`firmware_status` 只允许以下八个值：

| firmware_status | 含义 |
|---|---|
| `candidate_only` | 只有固件候选，尚无可复现结构 |
| `container_validated` | container、header、length、checksum 或标准 parser 得到独立验证 |
| `layout_reproduced` | partition、segment、table 或组件关系可重复重建 |
| `filesystem_validated` | 文件系统由 parser 或独立几何检查验证 |
| `extraction_reproduced` | 有限提取步骤可复现，派生 Artifact 的直接来源已验证，且组件完整内容 Hash 使用 `hash.status: verified` 和非空 `hash.value` |
| `rejected` | 批准范围内所有相关 Hypothesis 均被明确证伪，且无存活候选 |
| `bounded_checks_exhausted` | 批准检查全部完成，仍有无法验证或证伪的存活候选 |
| `unknown` | 输入或 Evidence 不足，或批准检查尚未全部执行 |

每轮只选择一个由当前 Evidence 支持的最高状态。单个 parser 或 Hypothesis 失败不得导致整体 `rejected`；状态依据写入 `investigation_summary` 或 `validation_checks`。`firmware_status` 不得代替 Finding confidence、Route、Handoff 或 Execution Gate 状态。

#### Sensitive material minimum disclosure

- 原始口令、token、私钥和敏感配置不得写入正文；需要保留时写入批准路径中的受保护派生 Artifact。
- 正文只记录 Artifact 引用、fingerprint 或脱敏摘要；派生 Artifact 仍记录直接来源、完整 Hash 和 Ledger Event。

#### Handoff and transfer chain

允许的正式入口为：

`file-triage` / `large-artifact-strategy` → `forensic-router` → `firmware-iot-forensics`

`uncommon-media-triage` → `forensic-router` → `firmware-iot-forensics`

`uncommon-media-triage` → `forensic-router` → `proprietary-format-recovery` → `forensic-router` → `firmware-iot-forensics`

Router 是唯一消费者决策点。LAS 只提供 bounded regions、signature 和 Evidence；uncommon 提供结构 Evidence 与核心引用；proprietary 还提供已验证嵌套固件 Artifact。Router 验证 source、regions、Route context、limits、Gate、`visited_skills` 和 hop 后才创建完整 Handoff。firmware 完成后默认返回 autopilot。

firmware 只有本轮产生新 Artifact 或 Finding，并出现新的可执行消费者候选时，才可携带 `reentry_reason`、`new_evidence_refs`、本轮 Ledger Event 和合法 hop 最多一次返回 Router。

同一 `route_id` 和 evidence scope 中，Router 不得再次选择 `visited_skills` 中已有的 Skill。明确禁止 proprietary → Router → firmware → Router → proprietary、firmware → Router → firmware，以及 uncommon → Router → firmware → Router → uncommon。没有其他当前可执行消费者时返回 autopilot。

`nas-raid-encrypted-storage` 当前已可执行。firmware 只有实际提取出独立存储镜像、阵列成员或加密卷 Artifact，并附可回查 provenance、明确 Hash 状态、bounded regions、Finding 和本轮 Ledger Event 时，才可生成 executable storage candidate；已物化且在预算内的组件优先 verified Hash，大型、稀疏、流式或未物化 storage 视图可为 `deferred|unavailable`。必须返回 Router 按 8.14 重评，不得直接调用。firmware 只有提取出独立样本 Artifact，并具有明确恶意分析目标或独立可疑上下文时，才可生成 executable malware candidate；普通 ELF 或脚本保持 firmware 上下文，必须返回 Router 按 8.15 重评。

#### Execution Gate boundary

批准 regions、工作目录和 limits 内的只读识别、静态 parser、组件 Hash、有限提取和目标化静态读取使用 `execution_gate.required=false`。工具不能保证提取边界时不得自动提取。

下列动作必须设置 `execution_gate.required=true` 并填写非空 `reason`：

- 无界递归解包、大范围或全盘 carving、全文件 strings、超出 limits。
- 安装、联网、在线检索、第三方上传、执行固件内容或动态启动。
- 修改固件、设备写入、UART/JTAG/刷写、爆破或长时间解密。
- RAID/LVM 激活、解锁、mount、可写挂载、修改 original Artifact 或写入未批准路径。

### 8.14 nas-raid-encrypted-storage

`nas-raid-encrypted-storage` 是 Phase 3 第四个已实现模块。它复用 Request Envelope、Response Envelope、Route Record、Artifact Record、Finding Record 和 Ledger Event，不新增 JSON Schema。它处理独立 NAS、通用多成员 RAID、mdraid/LVM/ZFS/Btrfs/Storage Spaces、metadata-less RAID 候选、常见加密卷，以及服务器文件系统尚未暴露时的非平台绑定存储前置层，以 bounded、read-only 方式验证有限拓扑并生成恢复视图。

#### Core Request payload

核心字段为：

- `source_artifact_refs`：本轮批准的源 Artifact 集合。
- `member_artifact_refs`：参与成员清单，必须属于 source scope。
- `candidate_regions`：适用 metadata/header/validation regions。
- `upstream_storage_hints`、`upstream_layer_hints`、`topology_hints`：只作 Evidence-backed Hypothesis 输入。
- `key_material_refs`：Request 明确提供的受保护 key material Artifact 引用。
- `route_basis`、`artifact_refs`、`finding_refs`、`ledger_event_refs`。
- `analysis_limits` 和 `recovery_scope`。

输入完整性规则：

1. `request.context` 包含当前 Route Record；同一 route/evidence scope 不得再次选择已访问的 storage Skill。
2. source/member 引用非空且可解析，size 为已知非负整数；member 必须属于 source scope，单卷把 source 作为唯一 member，1GB 以上材料先经过 LAS。
3. `candidate_regions` 非空；region 的 source、非负整数 offset、正整数 length 和边界合法，派生 Artifact 的直接来源逐级可回查。
4. Artifact、Finding、Ledger Event 和 route basis 可回查。direct route 至少需要两类不同验证机制；单个 signature、品牌、扩展名、设备名、单项 metadata、parser 成功或外部资料不满足阈值。
5. PVE/Proxmox/Ceph、vSphere/vSAN、VM/container/snapshot/虚拟磁盘映射、已有 `cluster-virtualization-forensics` Route，或 server rebuild plan 明确拥有存储重组任务时，继续由 server/cluster 处理。仅存在尚未暴露的服务器内容不排除 storage；Router 按当前待解决层级选择消费者。
6. encrypted/compressed 只说明格式候选，不证明可恢复。parser 失败也不能直接证明加密、损坏或不可恢复。

#### Analysis limits

storage `analysis_limits` 至少支持以下正整数：

- `max_members`
- `max_topology_hypotheses`
- `max_bytes_sampled_per_member`
- `timeout_seconds`
- `max_key_candidates`

topology validation 需要前四项适用预算；key validation 还需要 `max_key_candidates`。缺失、无效、无法强制或实际超限时，不执行依赖该预算的检查，保留 candidate 并设置 `required_next_action`。候选看似有限不能替代明确预算；不得扩展成员集合、生成 key candidates 或枚举 keyspace。

#### Core Response payload

核心输出为：

- `member_inventory`
- `layer_map`
- `topology_hypotheses`
- `validated_topology`
- `volume_candidates`、`filesystem_candidates`
- `encryption_assessments`
- `assembly_manifest_artifact_ref`
- `virtual_volume_artifact_refs`
- `validation_checks`、`counter_evidence`
- `excluded_routes`、`route_candidates`
- `unresolved_questions`、`required_next_action`
- `storage_status`

`layer_map` 只表达 member → partition → RAID/pool/volume manager → encryption → filesystem 的已观察或假设关系。每个 topology Hypothesis 绑定成员集合、关键参数、支持 Evidence、counter-evidence、validation result 和 confidence；不复制 RAID 算法或 parser 内部结构。

#### Assembly-manifest Artifact

多成员虚拟卷不得任意选择一个成员作为唯一父来源。先生成 assembly-manifest Artifact，记录：

- 有序 `member_artifact_refs`、成员角色和缺失成员；
- offsets 与采用的 topology 参数；
- 使用的 Hypothesis 与 validation Evidence；
- 对应 validation Evidence 和 Ledger Event 引用。

assembly-manifest 使用现有 Artifact Record 记录完整 verified Hash，但它只是拓扑与 provenance 描述，不是虚拟卷的直接字节父 Artifact。多成员虚拟卷没有单一直接父 Artifact 时，其 `source_artifact_id` 使用 `null`；Response 的 `assembly_manifest_artifact_ref` 指向 manifest，生成 Ledger Event 的 `artifact_refs` 引用 manifest 和全部成员 Artifact，`output_artifact_refs` 引用虚拟卷 Artifact。只有确实存在已经物化的直接中间 Artifact 时，后续 Artifact 才将其写入 `source_artifact_id`。

#### Storage Artifact Hash status

- assembly-manifest 必须使用完整 `hash.status: verified` 和非空 `hash.value`。
- 已物化且处于批准读取预算内的派生文件优先使用 verified Hash。
- 大型、稀疏、流式或未物化虚拟视图允许 `hash.status: deferred|unavailable`；`deferred` 必须记录 `deferred_reason`。
- route basis 和 Finding 必须明确 Hash 状态及其限制；region Hash 或 member Hash 不得冒充虚拟卷完整 Hash。
- executable storage candidate 需要合法 Artifact Record、可回查 provenance 和明确 Hash 状态，不要求所有视图一律 verified。

#### Storage status

`storage_status` 只允许七个值：

| storage_status | 含义 |
|---|---|
| `candidate_only` | 只有存储或拓扑候选 |
| `topology_validated` | 成员和层级拓扑通过至少两类支持性检查 |
| `volume_readable` | 验证后的只读卷视图可稳定读取 |
| `recovery_reproduced` | 恢复步骤可重复，输出通过 filesystem parser 或独立结构检查 |
| `rejected` | 批准范围内所有相关 Hypothesis 均被证伪，且无存活候选 |
| `bounded_checks_exhausted` | 批准检查完成，仍有无法验证或证伪的存活候选 |
| `unknown` | 输入或 Evidence 不足，或批准检查尚未完成 |

正面优先级固定为 `recovery_reproduced > volume_readable > topology_validated > candidate_only`。单个 Hypothesis 失败不导致整体 `rejected`。每轮只选择一个值，并在 Investigation Summary 或 `validation_checks` 记录依据。`storage_status` 不替代 Finding confidence、Route、Handoff 或 Execution Gate 状态；key validation result 只写入 `encryption_assessments`。

#### Key material minimum disclosure

- 原始密码、recovery key、token 和 key material 不得写入 Response、Finding 或 Ledger Event 正文。
- 需要保留时写入批准路径中的受保护派生 Artifact；正文只记录 Artifact 引用、fingerprint、脱敏摘要和验证结果。
- 只验证 Request 明确提供、可解析且处于 `max_key_candidates` 预算内的候选。使用用户态 parser 在批准目录生成只读解密/恢复视图无需 Gate，但不得创建内核映射、mount、修改 original、系统或设备状态，并且工具必须有限、可终止。cryptsetup/device-mapper 等系统级 unlock 进入 Gate。

#### Handoff and consumer selection

允许入口为：

- `file-triage` / `large-artifact-strategy` → `forensic-router` → `nas-raid-encrypted-storage`
- `uncommon-media-triage` → `forensic-router` → `nas-raid-encrypted-storage`
- `proprietary-format-recovery` → `forensic-router` → `nas-raid-encrypted-storage`
- `firmware-iot-forensics` → `forensic-router` → `nas-raid-encrypted-storage`

Router 是唯一消费者决策点。上游只提供 candidate、bounded Evidence 和核心引用；Router 验证 input、limits、Route context、Gate、visited/hop 后创建完整 Handoff，并将 storage 加入 `visited_skills`。storage 默认返回 autopilot；只有本轮产生新 Artifact 或 Finding 且出现新的可执行消费者候选时，才可携带 `reentry_reason`、非空 `new_evidence_refs`、本轮新 Ledger Event 和合法 hop 最多一次返回 Router。

Router 按当前层级选择：平台/虚拟化拓扑交 server/cluster；独立阵列、卷或加密前置层交 storage。允许 `forensic-router` → storage → `forensic-router` → `server-forensics-router`：storage 先暴露可读卷，再由新 Artifact/Finding 判断服务器目录、应用配置、Database、Web、container、virtualization 或服务器卷上下文。普通 NAS 共享、个人磁盘、备份卷、媒体卷或通用文件系统按当前消费者能力或 Answer Gate 处理。

同一 route/evidence scope 不得再次选择已访问 Skill。明确禁止 storage → Router → storage、storage → Router → proprietary → Router → storage、uncommon → Router → storage → Router → uncommon、proprietary → Router → storage → Router → proprietary，以及 firmware → Router → storage → Router → firmware。storage 只有恢复出独立样本 Artifact，并具有明确恶意分析目标或独立可疑上下文时，才可生成 executable malware candidate；普通 executable 不自动转出，必须返回 Router 按 8.15 重评。

#### Execution Gate boundary

批准 scope、工作目录和 limits 内，工具能保证只读、有限和可终止时，bounded metadata read、有限 Hash、member/partition/layer inventory、用户态 parser、有限 topology validation、bounded filesystem check，以及使用 Request 明确提供 key material 的用户态只读解密/恢复视图使用 `execution_gate.required=false`。该视图不得创建内核映射、mount、修改 original、系统或设备状态。

以下动作必须设置 `execution_gate.required=true` 并填写非空 `reason`：

- 修改 original Artifact，或写入 RAID/LVM/ZFS/filesystem metadata。
- 内核级 RAID assembly、LVM activation、ZFS import、cryptsetup/device-mapper 系统级 unlock 或 mount。
- repair、rebuild、rewind、resilver、scrub、`fsck`、`chkdsk` 或真实设备写入。
- 无界 topology/member-order/keyspace 枚举、字典扩展、爆破、长时间解密、全盘 carving 或全量 strings。
- 安装、联网、在线检索、第三方上传、超出 limits 或写入未批准路径。

### 8.15 malware-forensics

`malware-forensics` 是 Phase 3 第五个已实现模块。它复用 Request Envelope、Response Envelope、Route Record、Artifact Record、Finding Record 和 Ledger Event，不新增 JSON Schema。它对 Router 批准的样本或 bounded payload 做目标化静态分析，并且只在 Execution Gate 已批准且隔离环境合格时协调有限动态观察。

#### Core Request payload

核心字段为：

- `source_artifact_refs`
- `candidate_regions`
- `sample_hints`、`upstream_context`、`route_basis`
- `artifact_refs`、`finding_refs`、`ledger_event_refs`
- `requested_checks`、`analysis_limits`
- `dynamic_analysis_scope`
- `protected_config_or_key_refs`

输入规则：

1. `request.context` 包含当前 Route Record；source Artifact 已登记、可读取或可定位，并有明确 size 和 Hash 状态。1GB 以上材料先经过 LAS。
2. 完整样本可以没有 `candidate_regions`。嵌入式 payload 必须有合法 source、非负整数 offset、正整数 length，且边界不超过 source size；派生来源和核心引用均可回查。
3. parser 不支持或失败不阻止 intake，只形成待验证线索。executable route 需要有效样本或可分析区域，加明确恶意分析目标或独立可疑上下文；目标只表示范围和授权，不构成恶意性 Evidence。
4. 普通 executable、扩展名、文件名、单个 magic、高熵、packer、YARA/capa 命中、杀毒标签或外部资料不能独立确认恶意，也不能让普通 firmware/storage 组件自动转出。
5. `analysis_limits` 中存在的数值必须是可强制的正整数。缺失或无法强制某项限制时，不执行依赖该限制的检查，并设置 `required_next_action`。
6. 动态范围缺失、未批准或执行环境不合格时不得运行样本；已有沙箱报告、行为日志或内存产物可以只读消费。

#### Core Response payload

核心输出为：

- `sample_assessments`
- `capability_hypotheses`
- `behavior_hypotheses`
- `configuration_artifact_refs`
- `dynamic_observations`
- `validation_checks`、`counter_evidence`
- `excluded_routes`、`route_candidates`
- `unresolved_questions`、`required_next_action`
- `malware_status`

IOC、持久化、结构异常和关键行为结论写入顶层 Finding，payload 不复制完整 Finding。结构事实、静态 capability/behavior Hypothesis 和动态 observation 必须明确区分来源；每项回指 Artifact、offset/函数/region/逻辑位置、支持与反证、Finding/Ledger 引用和 confidence。

#### Malware status

`malware_status` 只允许六个值：

| malware_status | 含义 |
|---|---|
| `candidate_only` | 已接受候选，尚未完成静态特征化 |
| `static_characterized` | 格式、结构和目标化静态检查可复现 |
| `behavior_supported` | 至少两类相互支持的 Evidence 支持行为 Hypothesis |
| `dynamic_observed` | 已取得可回查的批准动态观察，不表示已确认恶意 |
| `bounded_checks_exhausted` | 批准检查完成，仍有无法验证或证伪的问题 |
| `unknown` | 输入、Evidence 或预算不足，检查尚未完整执行 |

正面归约顺序为 `dynamic_observed > behavior_supported > static_characterized > candidate_only`。每轮只选择一个状态；单个 Hypothesis 失败只写入 `validation_checks` 和 `counter_evidence`。`malware_status` 不表达 malicious、benign、safe 或法律结论，也不替代 Finding confidence、Route、Handoff 或 Execution Gate 状态。

#### Analysis limits and evidence

- 只在批准 Artifact/regions、工作目录和 `analysis_limits` 内执行 bounded 静态检查；工具不能保证字节、条目、输出或 timeout 边界时停止对应动作。
- capability 必须回指具体特征位置；解码 strings、配置和嵌入对象记录直接来源、派生 Artifact 和生成 Ledger Event。
- YARA、capa、杀毒和 sandbox 标签只是候选 Evidence，必须由当前 Artifact 内容或独立观察互证。
- 未检查范围不得写成负面 Finding；正面 Evidence、counter-evidence、失败检查和未执行原因全部保留。

#### Sensitive material minimum disclosure

配置、凭据、token、私钥、key 和完整 C2 配置只保存在受保护 Artifact。Response、Finding、Ledger Event、stdout/stderr 和摘要只记录类型、来源、Artifact 引用、fingerprint、脱敏摘要和验证结果，不复制完整敏感值。

#### Handoff and loop prevention

允许入口为：

- `file-triage` / `large-artifact-strategy` → `forensic-router` → `malware-forensics`
- uncommon、proprietary、firmware 或 storage → `forensic-router` → `malware-forensics`

Router 是唯一消费者决策点。上游只形成 `current_availability: executable` 的 candidate 和核心引用；Router 验证 source/regions、目标或可疑上下文、Route、limits、Gate、visited/hop 后创建完整 Handoff，并将 malware 加入 `visited_skills`。server Skills 仍保留旧的非可执行 malware 路由表述，属于独立 Phase 2 清理范围；本 profile 不宣称 server → malware 旧限制已经解除。

malware 默认返回 autopilot。只有本轮产生新 Artifact 或 Finding、新 Ledger Event 和新的可执行消费者候选时，才可携带非空 `reentry_reason`、非空 `new_evidence_refs` 和合法 hop 最多一次返回 Router。原上游已在 `visited_skills` 时不得重新创建返回该消费者的 Handoff。

明确禁止 malware → Router → malware、proprietary → Router → malware → Router → proprietary、firmware → Router → malware → Router → firmware、storage → Router → malware → Router → storage，以及 uncommon → Router → malware → Router → uncommon。

#### Execution Gate boundary

批准范围内的 read-only Hash、格式/结构解析、bounded YARA/capa/FLOSS、目标化 strings/配置解码、有限反汇编/反编译、派生 Artifact 创建，以及已有 sandbox/memory 产物的只读分析使用 `execution_gate.required=false`。

以下动作必须设置 `execution_gate.required=true` 并填写非空原因：

- 执行二进制、脚本、宏、APK、payload 或解码结果。
- debugger、API hook、动态 instrumentation、运行中进程 memory dump，或启动 VM、容器、QEMU、模拟器、沙箱。
- 模拟 C2/DNS/HTTP 等网络行为、第三方上传、在线扫描或安装工具。
- 修改样本、系统、服务、注册表、持久化设置或 original Artifact。
- 长时间或无界 unpack、decompile、deobfuscation、strings、符号执行、爆破或配置枚举。

动态动作还要求非空 `dynamic_analysis_scope`、批准的隔离环境、快照/销毁/回滚能力、明确网络策略、有限运行时间和输出预算，以及样本 Hash、运行实例和 Ledger Event 绑定。默认网络为隔离、无外网；条件不完整时不得创建环境、安装 sandbox 或在宿主机执行，只设置 `required_next_action` 并返回 autopilot。
