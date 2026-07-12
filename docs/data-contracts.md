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
