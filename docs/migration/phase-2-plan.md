# Phase 2 服务器取证链迁移计划（修订版 v3.1）

**分支**: `phase-2-server-chain`
**日期**: 2026-07-10
**状态**: 规划已审查，待执行

---

## 一、总体迁移策略

### 1.1 迁移方式

**所有 10 个 skill 均定义为"结构化重构迁移"**，不再区分"原样迁移"和"重构迁移"。每个 skill 在迁移时必须：

1. 统一输出格式：删除 `battle summary`，改为 `investigation summary`
2. 统一路由记录：`Route Trace` 改为通用路由记录格式
3. 统一证据格式：所有 skill 产生统一的 `ledger event`
4. 统一交接格式：`handoff` 改为 `route_record.route_plan` + `route_record.handoffs`
5. 移除旧引用：所有 `competition-autopilot` 引用改为 `forensic-autopilot`，`server-answer-gate` 改为 `answer-gate`
6. 移除本地路径绑定：删除 `E:\CompetitionTools` 等硬编码路径

### 1.2 与 Phase 1 衔接原则

| Phase 1 Skill | Phase 2 衔接方式 |
|---------------|-----------------|
| `forensic-autopilot` | Step 5 (Domain Analysis) 调用 `server-forensics-router` 或直接调用专项 skill |
| `forensic-router` | 路由表定义：服务器镜像/远程入口/完整服务器目录 → `server-forensics-router`；单一明确的 compose/DB/Web → 直接路由到专项 |
| `tool-router` | `server-rebuild-executor` 的 Stage 0 (Preflight) 调用 |
| `evidence-ledger` | 所有 Phase 2 skills 产生统一 `ledger event`，由 `evidence-ledger` skill 负责持久化 |
| `answer-gate` | Phase 2 所有 skills 的最终输出流向 `answer-gate` |
| `file-triage` | `server-forensics-router` 接收 `triage_notes` 作为输入 |
| `large-artifact-strategy` | 当 `large_artifact_mode` 触发时（size threshold、image/container signature、high-cost full-scan risk），先进入此 skill |
| `report-writer` | `answer-gate` 通过后调用 |

### 1.3 Auxiliary 文件处理

- **不迁移旧 REVIEW.md**：旧 skills 的自审报告不迁移
- **从旧 CHECKLIST.md 抽取有效检查项**：写入新 skill 的 `## Quality Checklist` 章节或项目测试
- 保留 `templates/skill-template.md` 作为新 skill 模板

---

## 二、最终调用链设计

```
forensic-autopilot (Phase 1)
    ↓
tool-router (Phase 1)
    ↓
file-triage (Phase 1)
    ↓
large-artifact-strategy (Phase 1, if large_artifact_mode is triggered)
    ↓                    触发因素: size threshold | image/container signature | high-cost full-scan risk
    ↓
forensic-router (Phase 1)
    ↓
    ├── 服务器镜像 / 远程入口 / 完整服务器目录 / 混合材料 / 虚拟化导出 / 模式不明确
    │   └── server-forensics-router (Phase 2 入口)
    │       ↓
    │       ├── rebuild-and-connect mode:
    │       │   └── server-rebuild-planner → server-rebuild-executor (Stage 0-6)
    │       │       → remote-server-live-response
    │       │       → domain skills (linux / webapp / database / docker)
    │       │       → timeline-reconstruction
    │       │
    │       ├── remote-live mode:
    │       │   └── remote-server-live-response
    │       │       → domain skills
    │       │       → timeline-reconstruction
    │       │
    │       ├── offline-image mode:
    │       │   └── domain skills (linux / webapp / database / docker / cluster)
    │       │       → timeline-reconstruction
    │       │
    │       └── hybrid-cluster mode:
    │           └── cluster-virtualization-forensics
    │               → server-rebuild-planner / domain skills
    │               → timeline-reconstruction
    │
    ├── 单一明确的 compose
    │   └── docker-container-forensics
    │
    ├── 单一明确的数据库备份
    │   └── database-server-forensics
    │
    └── 单一明确的 Web 源码
        └── webapp-server-forensics
    ↓
domain skills (linux / webapp / database / docker / cluster)
    ↓
timeline-reconstruction (if temporal reconstruction is needed)
    ↓
answer-gate (Phase 1) ←── 五步校验
    ↓
report-writer (Phase 1) ←── 报告输出
```

**并行路径**：当检材包含多种类型时，可分配多条并行路径，每条路径独立执行，最后在 `timeline-reconstruction` 合并。

---

## 三、10 个 Skill 迁移表

| # | Skill 名称 | 新路径 | 迁移方式 | 重构要点 |
|---|-----------|-------|---------|---------|
| 10 | `server-forensics-router` | `skills/server/server-forensics-router/` | 结构化重构迁移 | 统一输出格式、调整使用边界、移除旧引用 |
| 11 | `server-rebuild-planner` | `skills/server/server-rebuild-planner/` | 结构化重构迁移 | 输出 `recovery_policy`、统一输出格式 |
| 12 | `server-rebuild-executor` | `skills/server/server-rebuild-executor/` | 结构化重构迁移 | Stage 0-6 重构、rebuild-status schema、recovery policy |
| 13 | `remote-server-live-response` | `skills/server/remote-server-live-response/` | 结构化重构迁移 | 凭据不记录实际值、统一输出格式 |
| 14 | `linux-server-forensics` | `skills/server/linux-server-forensics/` | 结构化重构迁移 | 定义 ownership boundary、统一输出格式 |
| 15 | `webapp-server-forensics` | `skills/server/webapp-server-forensics/` | 结构化重构迁移 | 使用 `detected_components` 数组、统一输出格式 |
| 16 | `database-server-forensics` | `skills/server/database-server-forensics/` | 结构化重构迁移 | 增加 `access_mode`、`data_paths` 为数组、统一输出格式 |
| 17 | `docker-container-forensics` | `skills/server/docker-container-forensics/` | 结构化重构迁移 | 增加 `access_mode` 四种模式、统一输出格式 |
| 18 | `cluster-virtualization-forensics` | `skills/server/cluster-virtualization-forensics/` | 结构化重构迁移 | 只负责虚拟化拓扑存储映射、统一输出格式 |
| 19 | `timeline-reconstruction` | `skills/timeline/timeline-reconstruction/` | 结构化重构迁移 + 泛化 | Phase 2 仅支持服务器日志源、扩展 timeline event 字段 |

---

## 四、统一数据契约

### 4.1 统一 Ledger Event 格式

所有 Phase 2 skills 产生统一的 `ledger event`，由 `evidence-ledger` skill 负责持久化到 `evidence-ledger.jsonl` 和 `evidence-ledger.md`。

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
  "output_refs": [],
  "finding": "<what-was-discovered|null>",
  "confidence": "high|medium|low|null",
  "next_action": "<what-to-do-next|null>"
}
```

**写入规则**：
- 每个有证据价值的命令产生一条 `command` event
- 每个关键 finding 产生一条 `finding` event
- 负面发现仅在能排除路线、回答问题或支撑结论时记录
- JSONL 与 Markdown 使用同一个 `event_id`
- `event_id` 前缀统一使用 `led-`

### 4.2 统一 Investigation Summary 格式

替代旧的 `battle summary`：

**Route Plan 渲染规则**：Investigation Summary 中展示的 Route Plan 必须由 `route_record.route_plan` 渲染，不得作为独立事实来源维护。

```markdown
## Investigation Summary

**Current Assessment**: <一句话总结当前状态>

**Key Evidence**:
1. <证据1，含路径/文件/配置/入口>
2. <证据2>
3. <证据3，可选>

**Excluded Routes** (if any): <被排除的路线及原因>

**Route Plan**:
- <下一步1>
- <下一步2，如有并行>
```

### 4.3 统一 Route Record 格式

替代旧的 `Route Trace`。路由信息（`route_plan` 和 `handoffs`）仅保存在 `route_record` 中，不在输出契约顶层重复声明。

```yaml
route_record:
  route_id: "route-<uuid>"
  triggered_skill: <skill-name>
  route_basis: array        # 触发依据列表
  mode_decision: string|null
  route_plan:
    - skill: <downstream-skill-1>
      dependency: none|<skill-name>
      parallel: false
    - skill: <downstream-skill-2>
      dependency: <skill-name>
      parallel: true
  handoffs:
    - handoff_id: "hof-<uuid>"
      route_id: "route-<uuid>"
      from: <skill-name>
      to: <skill-name>
      reason: <交接原因>
      artifact_refs: []
      finding_refs: []
      visited_skills: []
      hop_count: 0
      status: pending|accepted|completed|rejected|blocked
      priority: critical|high|normal|low
  evidence_scope: string
  risk_level: low|medium|high
  next_action: string
  execution_gate:
    required: boolean
    reason: string|null
    policy_ref: string|null
```

**防循环规则**：同一 `route_id` + 同一 evidence scope 不得重复进入同一 Skill，除非新增证据明确要求重新分析。

### 4.4 统一 Skill 输入契约（标准信封 + 专项载荷）

所有 Phase 2 skills 接收统一的请求信封，专项字段放入 `payload`：

```yaml
request:
  material_info: object     # 来自 file-triage / forensic-router
  objective: string|null    # 分析目标；可空
  objective_status: enum[explicit, inferred, unknown]
  context: object|null      # 可选，包含之前的 findings
  payload: object           # skill 专用字段（见各专项契约）
```

当 `objective_status` 为 `unknown` 时，skill 执行中立初筛和材料分类，不追问用户；只有需要回答具体问题、筛选时间范围或选择分析优先级时，才要求补充 `objective`。

### 4.5 统一 Skill 输出契约

所有 Phase 2 skills 输出以下标准格式：

```yaml
# 标准输出
investigation_summary: object  # Investigation Summary 内容
route_record: object           # Route Record 内容（包含 route_plan 和 handoffs）
findings: array                # 发现列表
ledger_events: array           # 本次产生的 ledger event 列表
artifact_refs: array           # 引用的 artifact 列表
```

路由信息（`route_plan` 和 `handoffs`）仅存在于 `route_record` 中，不在顶层重复声明。

---

## 五、server-rebuild-executor Stage 0-6

### 5.1 阶段定义

Stage 名称和字段泛化，适用于 VM、Docker、WSL 等所有 backend，不写死 VM 概念。

`execution_gate` 仅在操作超出已批准 rebuild plan 或 policy scope 时触发，与 `recovery_policy`（运行失败后如何恢复）职责分离。

| Stage | 名称 | 输入 | 输出 | execution_gate |
|-------|------|------|------|----------------|
| **Stage 0** | Plan Validation & Preflight | `rebuild_plan` from planner | `preflight_report`, `available_tools`, `missing_tools`, `recommended_backend` | 不要求 (只读) |
| **Stage 1** | Workspace & Source Preservation | `preflight_report` | `workspace_path`, `source_artifacts` | 不要求 (只读) |
| **Stage 2** | Artifact Preparation | `workspace_path`, `rebuild_plan` | `prepared_artifacts` | 仅当超出批准范围时 |
| **Stage 3** | Runtime Configuration | `prepared_artifacts`, `rebuild_plan` | `runtime_definition` | 不要求 |
| **Stage 4** | Network Configuration | `runtime_definition`, `rebuild_plan` | `network_config`, `ports_mapped` | 不要求 |
| **Stage 5** | Runtime Launch & Stabilization | `runtime_definition`, `network_config` | `runtime_instance`, `runtime_running`, `startup_log` | 仅当超出批准范围时 |
| **Stage 6** | Service Discovery, Connection Test & Handoff | `runtime_instance`, `runtime_running` | `connection_info`, `services_discovered` | 不要求 |

### 5.2 统一 Backend 枚举

```text
vmware | qemu | virtualbox | docker | wsl | manual
```

VM、Docker、WSL 的差异放进 `backend_profile`，不写死在主流程中。

### 5.3 每阶段详细说明

#### Stage 0: Plan Validation & Preflight

**输入**：
```yaml
rebuild_plan: object  # 来自 server-rebuild-planner
```

**处理**：
1. 验证 `rebuild_plan` 完整性
2. 检查工具可用性
3. 检查可用磁盘空间
4. 检查管理员权限
5. 检查虚拟化/嵌套虚拟化支持（如适用）
6. 检查网络创建能力

**输出**：
```yaml
preflight_report:
  available_tools: array
  missing_tools: array
  recommended_backend: enum[vmware, qemu, virtualbox, docker, wsl, manual]
  backend_profile: object   # backend 专用参数
  blocker: string|null
  disk_space_available: integer
  admin_privilege: boolean
  virtualization_supported: boolean
```

**Ledger Event**: 记录工具检查结果、环境状态

#### Stage 1: Workspace & Source Preservation

**输入**：
```yaml
preflight_report: object
```

**处理**：
1. 创建工作目录结构
2. 登记源检材，遵循 `large-artifact-strategy` 决定是否立即计算完整 hash
3. 建立源检材与工作产物之间的映射
4. 复制必要配置文件到 work/

**输出**：
```yaml
workspace_path: string
source_artifacts:
  - artifact_id: "artifact-<uuid>"
    path: string
    size: integer
    hash:
      algorithm: sha256
      value: string|null
      status: enum[verified, provided, deferred, unavailable]
    preservation_status: enum[original-reference, read-only-mounted, working-copy-created]
    deferred_reason: string|null   # 当 status 为 deferred 时填写
```

Hash 状态说明：
- `verified`: 已在本阶段计算并验证
- `provided`: 由外部提供（如题目附件清单）
- `deferred`: 延迟计算（大文件，遵循 large-artifact-strategy）
- `unavailable`: 无法计算（如远程入口、损坏文件）

**Ledger Event**: 记录工作目录结构、源检材登记、preservation 状态

#### Stage 2: Artifact Preparation

**输入**：
```yaml
workspace_path: string
rebuild_plan: object
```

**处理**：
1. 根据 `rebuild_plan` 和 backend 选择目标格式
2. 执行格式转换或导出（如需要）
3. 创建稀疏文件（如支持）
4. 验证准备结果

**输出**：
```yaml
prepared_artifacts:
  - artifact_id: "artifact-<uuid>"
    source_artifact_id: "artifact-<uuid>"
    path: string
    format: string          # raw|vmdk|qcow2|docker-image|wsl-distro|...
    conversion_method: string|null
    size: integer
    hash:
      algorithm: sha256
      value: string|null
      status: enum[verified, provided, deferred, unavailable]
    ready: boolean
```

**Ledger Event**: 记录准备命令、输出、验证结果

**Failure Recovery**: 按 `recovery_policy.artifact_export` 和 `recovery_policy.disk_format_conversion` 执行

#### Stage 3: Runtime Configuration

**输入**：
```yaml
prepared_artifacts: array
rebuild_plan: object
```

**处理**：
1. 根据 backend 生成配置文件（VMX / QEMU 命令 / VirtualBox 配置 / Docker Compose / WSL 配置）
2. 配置资源分配（CPU/RAM/磁盘）
3. 配置启动选项

**输出**：
```yaml
runtime_definition:
  planned_name: string      # VM name | container name | WSL distro name
  backend: enum[vmware, qemu, virtualbox, docker, wsl, manual]
  backend_profile: object   # backend 专用配置
  config_path: string
  config_type: string       # 由 backend 决定
  resources:
    cpu: integer
    ram_mb: integer
    disk_paths: array
```

**Ledger Event**: 记录配置文件内容、参数

#### Stage 4: Network Configuration

**输入**：
```yaml
runtime_definition: object
rebuild_plan: object
```

**处理**：
1. 配置网络模式（host-only/NAT/isolated）
2. 配置端口映射
3. 创建虚拟网络（如需要）

**输出**：
```yaml
network_config:
  mode: enum[host-only, nat, isolated, bridge]
  port_mapping: object
  network_created: boolean
ports_mapped: boolean
```

**Ledger Event**: 记录网络配置、端口映射

#### Stage 5: Runtime Launch & Stabilization

**输入**：
```yaml
runtime_definition: object
network_config: object
```

**处理**：
1. 启动运行时实例（VM / Docker 容器 / WSL 服务）
2. 等待启动完成
3. 检查启动日志
4. 检查服务状态

**输出**：
```yaml
runtime_instance:
  instance_id: string       # VM name | container ID | WSL distro name
  instance_type: string
  launched_at: ISO8601
runtime_running: boolean
startup_log: string
startup_errors: array
```

**Ledger Event**: 记录启动命令、输出、服务状态

**Failure Recovery**: 按 `recovery_policy.runtime_launch` 执行（backend fallback 仅在此阶段和 Stage 3 适用）

#### Stage 6: Service Discovery, Connection Test and Handoff

**输入**：
```yaml
runtime_instance: object
runtime_running: boolean
```

**处理**：
1. 扫描开放端口
2. 检测服务类型
3. 测试连接（SSH/WebUI/DB/Docker）
4. 记录连接信息
5. 准备交接给 `remote-server-live-response`

**输出**：
```yaml
connection_info:
  ssh: object|null
  webui: object|null
  db_client: object|null
  docker_exec: object|null
services_discovered: array
```

**Ledger Event**: 记录端口扫描结果、服务检测结果、连接测试结果

---

## 六、Recovery Policy

### 6.1 设计原则

**"计划内自动恢复、计划外重新规划"**：

- **计划内恢复**：planner 在 `recovery_policy` 中预定义的恢复策略，executor 自动执行
- **计划外恢复**：超出 `recovery_policy` 范围的失败，executor 记录错误并退回 planner 重新规划

### 6.2 recovery_policy 格式（按 operation 分类）

由 `server-rebuild-planner` 输出：

```yaml
recovery_policy:
  artifact_export:
    # 从 EWF 等格式导出可处理的数据
    required_capability: ewf-export
    tool_candidates:
      - ewfexport
      - xmount
    auto_retry: true
    max_attempts: 2
  disk_format_conversion:
    # 磁盘格式转换（raw → vmdk, raw → qcow2 等）
    required_capability: disk-format-conversion
    tool_candidates:
      - qemu-img
      - vboxmanage-clonemedium
    auto_retry: true
    max_attempts: 2
  runtime_configuration:
    # 生成运行时配置
    fallback_backends: ["qemu", "virtualbox"]
    auto_retry: true
    max_attempts: 1
  runtime_launch:
    # 启动运行时实例
    fallback_backends: ["qemu"]
    auto_retry: true
    max_attempts: 1
    timeout_seconds: 120
  default:
    auto_retry: false
    action: "replan"
```

**注意**：Recovery Policy 使用 `required_capability` + `tool_candidates`，实际命令由 `tool-router` 根据本机可用能力选择。`ewfexport` 和 `qemu-img` 不是等价 fallback 工具，分别归入 `artifact_export` 和 `disk_format_conversion`。Backend fallback 仅用于 `runtime_configuration` 和 `runtime_launch`。

### 6.3 Executor 行为

| 场景 | Executor 行为 |
|------|--------------|
| 错误在 `recovery_policy` 中，且 `auto_retry: true` | 自动重试，尝试 fallback tools/backends |
| 错误在 `recovery_policy` 中，且 `auto_retry: false` | 记录错误，标记 stage 失败，退回 planner |
| 错误不在 `recovery_policy` 中 | 记录错误，标记 stage 失败，退回 planner |
| 重试次数超过 `max_attempts` | 记录错误，标记 stage 失败，退回 planner |

### 6.4 rebuild-status.schema.json

**新增 `templates/rebuild-status.schema.json`**：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "schema_version", "plan_id", "route_id",
    "source_artifacts", "working_artifacts",
    "backend", "backend_profile",
    "current_stage", "overall_status",
    "stages", "recovery_policy",
    "rollback_available", "updated_at"
  ],
  "properties": {
    "schema_version": { "type": "string", "const": "1.0" },
    "plan_id": { "type": "string" },
    "route_id": { "type": "string" },
    "source_artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["artifact_id", "path"],
        "properties": {
          "artifact_id": { "type": "string" },
          "path": { "type": "string" },
          "size": { "type": "integer" },
          "hash": {
            "type": "object",
            "properties": {
              "algorithm": { "type": "string" },
              "value": { "type": ["string", "null"] },
              "status": { "type": "string", "enum": ["verified", "provided", "deferred", "unavailable"] }
            }
          },
          "preservation_status": { "type": "string", "enum": ["original-reference", "read-only-mounted", "working-copy-created"] }
        }
      }
    },
    "working_artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["artifact_id", "source_artifact_id", "path"],
        "properties": {
          "artifact_id": { "type": "string" },
          "source_artifact_id": { "type": "string" },
          "path": { "type": "string" },
          "type": { "type": "string" },
          "hash": {
            "type": "object",
            "properties": {
              "algorithm": { "type": "string" },
              "value": { "type": ["string", "null"] },
              "status": { "type": "string", "enum": ["verified", "provided", "deferred", "unavailable"] }
            }
          },
          "created_at": { "type": "string", "format": "date-time" }
        }
      }
    },
    "backend": { "type": "string", "enum": ["vmware", "qemu", "virtualbox", "docker", "wsl", "manual"] },
    "backend_profile": { "type": "object" },
    "current_stage": { "type": "integer", "minimum": 0, "maximum": 6 },
    "overall_status": { "type": "string", "enum": ["pending", "in_progress", "blocked", "partial", "completed", "failed", "rolled_back"] },
    "stages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["stage", "name", "status", "attempt", "commands"],
        "properties": {
          "stage": { "type": "integer" },
          "name": { "type": "string" },
          "status": { "type": "string", "enum": ["pending", "in_progress", "retrying", "blocked", "completed", "failed", "skipped", "rolled_back"] },
          "attempt": { "type": "integer" },
          "started_at": { "type": ["string", "null"], "format": "date-time" },
          "completed_at": { "type": ["string", "null"], "format": "date-time" },
          "commands": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "command": { "type": "string" },
                "exit_code": { "type": ["integer", "null"] },
                "stdout_path": { "type": ["string", "null"] },
                "stderr_path": { "type": ["string", "null"] }
              }
            }
          },
          "outputs": { "type": "object" },
          "evidence_event_ids": {
            "type": "array",
            "items": { "type": "string" }
          },
          "rollback_checkpoint": { "type": ["string", "null"] },
          "error_class": { "type": ["string", "null"] },
          "error_message": { "type": ["string", "null"] },
          "next_stage": { "type": ["integer", "null"] }
        }
      }
    },
    "recovery_policy": { "type": "object" },
    "rollback_available": { "type": "boolean" },
    "can_continue_on_failure": { "type": "boolean" },
    "updated_at": { "type": "string", "format": "date-time" }
  }
}
```

**与统一 Ledger 的关联**：`evidence_event_ids` 引用 `led-<uuid>` 前缀的 event ID，`artifact_id` 引用 `artifact-<uuid>` 前缀。

---

## 七、四个专项 Skill 的 Ownership Boundary

### 7.1 设计原则

**不互斥，使用 ownership boundary 和 cross-skill handoff**：

- 每个 skill 有明确的"own"（负责）和"not own"（不负责）边界
- 当需要跨层取证时，通过 `route_record.handoffs` 传递数据
- 多个 skill 可以并行执行，最后在 timeline-reconstruction 合并

### 7.2 Ownership Boundary 定义

| Skill | Own (负责) | Not Own (不负责) |
|-------|-----------|-----------------|
| **linux-server-forensics** | 宿主系统层：账号、SSH、history、cron、systemd、进程、网络、持久化、系统日志 | Web 服务配置、数据库内容、容器配置 |
| **webapp-server-forensics** | Web 服务和源码层：Nginx/Apache/IIS 配置、access.log、error.log、app.log、路由、控制器、.env、JWT secret、WebShell | 系统日志、数据库内容、容器配置 |
| **database-server-forensics** | 数据层：SQL 查询、表结构、binlog、WAL、RDB、AOF、账号、业务数据 | 系统日志、Web 访问日志、容器配置 |
| **docker-container-forensics** | 容器运行时层：compose、Dockerfile、容器日志、镜像层、volume、bind mount、.env | 系统日志、Web 访问日志、数据库内容 |

### 7.3 Handoff 格式

所有 cross-skill handoff 使用统一的 `route_record.handoffs` 格式（见第四节 4.3），包含防循环字段（`handoff_id`、`route_id`、`visited_skills`、`hop_count`）。

### 7.4 典型场景

**场景1：Docker 容器运行 Web 应用**
```
docker-container-forensics (分析 compose、发现 Web 容器)
  → handoff → webapp-server-forensics (分析 Web 服务)
  → handoff → database-server-forensics (分析数据库)
  → linux-server-forensics (分析系统日志，可并行)
  → timeline-reconstruction (合并时间线)
```

**场景2：独立 Linux 服务器**
```
linux-server-forensics (分析系统层)
  → handoff → webapp-server-forensics (如发现 Web 服务)
  → handoff → database-server-forensics (如发现数据库)
  → timeline-reconstruction (合并时间线)
```

### 7.5 Handoff 触发条件

每个专项 Skill 在其 `## Handoff Triggers` 章节定义证据触发条件。通用规则：

| 触发条件 | 来源 Skill | 目标 Skill |
|---------|-----------|-----------|
| 发现 Web 服务进程/端口/配置 | linux | webapp |
| 发现数据库进程/端口/配置 | linux | database |
| 发现容器进程/配置 | linux | docker |
| 发现数据库连接配置 | webapp | database |
| 发现容器化的 Web 服务 | docker | webapp |
| 发现容器化的数据库 | docker | database |

---

## 八、timeline-reconstruction Phase 2 数据源

### 8.1 Phase 2 支持的数据源

| 数据源类型 | 来源 | parser_id |
|-----------|------|-----------|
| auth.log / secure | Linux 系统日志 | `auth-log-parser` |
| journal | systemd 日志 | `journal-parser` |
| access.log / error.log / app.log | Web 服务日志 | `web-log-parser` |
| Docker logs | 容器日志 | `docker-log-parser` |
| binlog / WAL / AOF | 数据库事务日志 | `db-transaction-log-parser` |
| RDB | 数据库快照 | `db-snapshot-parser` |
| wtmp / btmp / lastlog | 登录记录 | `login-record-parser` |
| file mtime / ctime | 文件时间戳 | `file-time-parser` |
| PVE logs / Ceph logs | 虚拟化/存储日志 | `pve-log-parser` / `ceph-log-parser` |

### 8.2 Timeline Event 格式

```json
{
  "timeline_event_id": "tl-<uuid>",
  "original_timestamp": "原始时间戳字符串|null",
  "normalized_timestamp": "ISO8601|null",
  "timezone_offset": "+08:00|null",
  "timezone_name": "Asia/Shanghai|null",
  "timezone_assumption": "说明假设来源|null",
  "clock_skew_seconds": "整数|null",
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

**ID 前缀**：`tl-`（timeline event），`led-`（ledger event），`artifact-`（artifact）。三者不混淆。

### 8.3 Phase 2 不支持的数据源

- PCAP（Phase 3 扩展）
- 浏览器历史（Phase 3 扩展）
- Windows 事件日志（后续独立 `windows-server-forensics`）

---

## 九、各 Skill 详细迁移方案

### 9.1 server-forensics-router

**迁移方式**：结构化重构迁移

**重构要点**：
1. 统一输出格式：`investigation_summary` + `route_record`
2. 调整使用边界：
   - 必须进入：服务器镜像、远程入口、完整服务器目录、混合材料、虚拟化导出、模式不明确材料
   - 可直接路由：单一明确的 compose、数据库备份、Web 源码
3. 移除旧引用：`competition-autopilot` → `forensic-autopilot`，`server-answer-gate` → `answer-gate`
4. 路由信息仅保存在 `route_record` 中

**输入契约**：
```yaml
request:
  material_info:
    object  # 来自 file-triage / forensic-router
  objective: string|null
  objective_status: enum[explicit, inferred, unknown]
  context: object|null
  payload:
    material_type: string
    file_list: array
    hash: string
    size: integer
    triage_notes: string
```

**输出契约**：
```yaml
investigation_summary: object
route_record:
  route_id: "route-<uuid>"
  triggered_skill: "server-forensics-router"
  route_basis: array
  mode_decision: enum[rebuild-and-connect, remote-live, offline-image, hybrid-cluster, pending]
  route_plan:
    - skill: string
      dependency: string|null
      parallel: boolean
  handoffs:
    - handoff_id: "hof-<uuid>"
      route_id: "route-<uuid>"
      from: "server-forensics-router"
      to: string
      reason: string
      artifact_refs: []
      finding_refs: []
      visited_skills: ["server-forensics-router"]
      hop_count: 1
      status: pending|accepted|completed|rejected|blocked
      priority: critical|high|normal|low
  evidence_scope: string
  risk_level: enum[low, medium, high]
  next_action: string
  execution_gate:
    required: boolean
    reason: string|null
    policy_ref: string|null
findings: array
ledger_events: array
artifact_refs: array
```

---

### 9.2 server-rebuild-planner

**迁移方式**：结构化重构迁移

**重构要点**：
1. 输出 `recovery_policy`（按 operation 分类，使用 capability + tool_candidates）
2. 统一输出格式
3. 移除旧引用

**输入契约**：
```yaml
request:
  material_info: object
  objective: string|null
  objective_status: enum[explicit, inferred, unknown]
  context: object|null
  payload:
    mode_decision: string  # 来自 server-forensics-router (rebuild-and-connect)
```

**输出契约**：
```yaml
investigation_summary: object
route_record: object
rebuild_feasibility: enum[yes, no, partial, blocked]
rebuild_method: enum[vmware, qemu, virtualbox, docker, wsl, manual]
required_inputs: array
missing_inputs: array
network_mode: enum[host-only, nat, isolated, bridge]
port_mapping: object
credential_source: string
modification_plan: string
rollback_plan: string
recovery_policy: object   # 按 operation 分类（见第六节）
findings: array
ledger_events: array
artifact_refs: array
```

---

### 9.3 server-rebuild-executor

**迁移方式**：结构化重构迁移（核心重构）

**重构要点**：
1. Stage 0-6 泛化（不写死 VM）
2. `rebuild-status.schema.json`（见第六节 6.4）
3. `recovery_policy` 执行（见第六节 6.2）
4. 每阶段 ledger event

**输入契约**：
```yaml
request:
  material_info: object
  objective: string|null
  objective_status: enum[explicit, inferred, unknown]
  context: object|null
  payload:
    rebuild_plan: object  # 来自 server-rebuild-planner
```

**输出契约**：
```yaml
investigation_summary: object
route_record: object
rebuild_status: object    # 符合 rebuild-status.schema.json
runtime_running: boolean
connection_info: object   # SSH/WebUI/DB/Docker 连接信息
findings: array
ledger_events: array
artifact_refs: array
```

---

### 9.4 remote-server-live-response

**迁移方式**：结构化重构迁移

**重构要点**：
1. 凭据不记录实际值，只记录来源和方法
2. 统一输出格式

**输入契约**：
```yaml
request:
  material_info: object
  objective: string|null
  objective_status: enum[explicit, inferred, unknown]
  context: object|null
  payload:
    connection_info: object   # SSH/WebUI/DB/Docker/WinRM/RDP 连接信息
      - type: enum[ssh, webui, db-client, docker-exec, winrm, rdp, service-client]
      - host: string
      - port: integer
    credential_source: string       # 凭据来源描述
    credential_reference: string    # 凭据引用（如 "题目附件 config.yml:password 字段"），不记录实际值
    authentication_method: enum[password, key, token, certificate]
```

**输出契约**：
```yaml
investigation_summary: object
route_record: object
session_summary: string
volatile_data: array
findings: array
ledger_events: array
artifact_refs: array
```

---

### 9.5 linux-server-forensics

**迁移方式**：结构化重构迁移

**重构要点**：
1. 定义 ownership boundary（见第七节）
2. 统一输出格式

**输入契约**：
```yaml
request:
  material_info: object
  objective: string|null
  objective_status: enum[explicit, inferred, unknown]
  context: object|null
  payload:
    environment: object       # 运行环境信息
      - type: enum[rebuilt-vm, remote-live, offline-image]
      - connection_info: object|null
```

**输出契约**：
```yaml
investigation_summary: object
route_record: object       # 包含 handoffs（如有跨层发现）
suspicious_users: array
login_events: array
ssh_findings: array
privilege_events: array
persistence_points: array
command_history_findings: array
service_changes: array
findings: array
ledger_events: array
artifact_refs: array
```

**Handoff Triggers**：
- 发现 Web 服务进程/端口/配置 → webapp-server-forensics
- 发现数据库进程/端口/配置 → database-server-forensics
- 发现容器进程/配置 → docker-container-forensics

---

### 9.6 webapp-server-forensics

**迁移方式**：结构化重构迁移

**重构要点**：
1. 使用 `detected_components` 数组
2. 输入使用 `source_paths`、`config_paths`、`log_paths` 数组
3. 统一输出格式

**输入契约**：
```yaml
request:
  material_info: object
  objective: string|null
  objective_status: enum[explicit, inferred, unknown]
  context: object|null
  payload:
    environment: object
    detected_components: array    # ["nginx", "flask", "mysql", ...]
    source_paths: array           # 源码路径列表
    config_paths: array           # 配置文件路径列表
    log_paths: array              # 日志文件路径列表
```

**输出契约**：
```yaml
investigation_summary: object
route_record: object
route_map: array
secret_findings:              # 统一 secret 格式
  - secret_type: string       # jwt-secret|api-key|password|...
    redacted_value: string    # 脱敏后的值
    source_ref: string        # 来源路径
    evidence_ref: string      # led-<uuid>
access_log_findings: array
suspected_entrypoint: string|null
suspect_ip: string|null
webshell_candidate: array
source_log_crosscheck: object
findings: array
ledger_events: array
artifact_refs: array
```

---

### 9.7 database-server-forensics

**迁移方式**：结构化重构迁移

**重构要点**：
1. 增加 `access_mode`
2. `connection_info` 可空
3. `data_paths` 为数组
4. 使用 `query_result_refs` 替代内嵌 `raw_query_results`
5. 统一输出格式

**输入契约**：
```yaml
request:
  material_info: object
  objective: string|null
  objective_status: enum[explicit, inferred, unknown]
  context: object|null
  payload:
    db_type: enum[mysql, postgresql, redis, mongodb, sqlite, unknown]
    access_mode: enum[online-query, offline-directory, dump-file, transaction-log, snapshot]
    connection_info: object|null  # 在线查询时提供
    data_paths: array             # 离线分析时提供
```

`access_mode` 说明：具体是 binlog、WAL、AOF 或 RDB，由 `db_type` + `access_mode` 联合判断。

**输出契约**：
```yaml
investigation_summary: object
route_record: object
db_type: string
table_map: array
query_plan: array
query_result_refs:            # 结果引用，不内嵌原始数据
  - query_id: string
    query: string
    target: string            # 表/库
    output_path: string       # 结果文件路径
    output_hash: string       # 结果文件 hash
    row_count: integer
account_findings: array
business_data_findings: array
secret_findings:              # 统一 secret 格式
  - secret_type: string
    redacted_value: string
    source_ref: string
    evidence_ref: string
db_timeline_findings: array
findings: array
ledger_events: array
artifact_refs: array
```

---

### 9.8 docker-container-forensics

**迁移方式**：结构化重构迁移

**重构要点**：
1. 增加 `access_mode`: `live-daemon|offline-directory|image-archive|compose-project`
2. 增加 `image_archive_path` 和 `source_paths`
3. 统一 secret 格式
4. 统一输出格式

**输入契约**：
```yaml
request:
  material_info: object
  objective: string|null
  objective_status: enum[explicit, inferred, unknown]
  context: object|null
  payload:
    access_mode: enum[live-daemon, offline-directory, image-archive, compose-project]
    compose_path: string|null
    dockerfile_path: string|null
    container_ids: array|null
    image_ids: array|null
    image_archive_path: string|null    # 镜像归档路径
    offline_directory: string|null
    source_paths: array                # 相关源文件路径
```

**输出契约**：
```yaml
investigation_summary: object
route_record: object
compose_service_map: array
image_map: array
volume_map: array
bind_mount_map: array
port_map: object
secret_findings:              # 统一 secret 格式
  - secret_type: string
    redacted_value: string
    source_ref: string
    evidence_ref: string
log_findings: array
findings: array
ledger_events: array
artifact_refs: array
```

---

### 9.9 cluster-virtualization-forensics

**迁移方式**：结构化重构迁移

**重构要点**：
1. 只负责虚拟化拓扑的 RAID/ZFS/LVM/Ceph 映射
2. 独立 NAS、通用 RAID、加密存储交给未来 `nas-raid-encrypted-storage`
3. 不扩展 Windows Server（后续独立 `windows-server-forensics`）
4. 统一输出格式

**输入契约**：
```yaml
request:
  material_info: object
  objective: string|null
  objective_status: enum[explicit, inferred, unknown]
  context: object|null
  payload:
    layer_hint: string|null
```

**输出契约**：
```yaml
investigation_summary: object
route_record: object
layer_map: object         # source artifact -> disk -> partition -> storage -> VM -> service
node_map: object|null
disk_map: object|null
vm_disk_map: object|null
storage_map: object|null
real_image_found: boolean
placeholder_only: boolean
findings: array
ledger_events: array
artifact_refs: array
```

---

### 9.10 timeline-reconstruction

**迁移方式**：结构化重构迁移 + 泛化

**重构要点**：
1. Phase 2 仅支持服务器日志源（见第八节）
2. 扩展 timeline event 字段（见第八节 8.2）
3. `timeline_event_id` 使用 `tl-` 前缀，`ledger_event_refs` 使用 `led-` 前缀
4. `source_type` 与 `parser_id` 分开
5. 区分 `db-transaction-log` 与 `db-snapshot`
6. 统一输出格式

**输入契约**：
```yaml
request:
  material_info: object
  objective: string|null
  objective_status: enum[explicit, inferred, unknown]
  context: object|null
  payload:
    data_sources: array       # 数据源列表
      - type: enum[auth-log, journal, web-log, docker-log, db-transaction-log, db-snapshot, login-record, file-time, pve-log, ceph-log]
      - path: string
      - timezone: string|null
    time_range: object|null   # 时间范围过滤
```

**输出契约**：
```yaml
investigation_summary: object
route_record: object
timeline: array           # 统一时间线（见第八节 8.2 event 格式）
event_count: integer
source_count: integer
gaps: array               # 时间线中的空白
anomalies: array          # 异常事件
findings: array
ledger_events: array
artifact_refs: array
```

---

## 十、Commit 计划

| Commit # | 内容 | Skills | 理由 |
|----------|------|--------|------|
| **1** | 计划、契约和 Schema 规范 | - docs/migration/phase-2-plan.md - docs/data-contracts.md - templates/ledger-event.schema.json - templates/investigation-summary.md - templates/route-record.md - templates/rebuild-status.schema.json | 先建立规范，后续 commit 有据可依 |
| **2** | server-router + rebuild-planner | - skills/server/server-forensics-router/ - skills/server/server-rebuild-planner/ | 路由和规划入口 |
| **3** | server-rebuild-executor implementation | - skills/server/server-rebuild-executor/ | 核心执行层 |
| **4** | remote-live-response | - skills/server/remote-server-live-response/ | 活体响应层 |
| **5** | Linux/WebApp/Database/Docker | - skills/server/linux-server-forensics/ - skills/server/webapp-server-forensics/ - skills/server/database-server-forensics/ - skills/server/docker-container-forensics/ | 四个专项 skill，结构相似 |
| **6** | cluster + timeline + integration docs | - skills/server/cluster-virtualization-forensics/ - skills/timeline/timeline-reconstruction/ - docs/integration-guide.md | 最后两个 + 集成文档 |

---

## 十一、已确定的设计决定

以下问题在审查过程中已确定，不再是待确认问题：

| # | 问题 | 决定 |
|---|------|------|
| 1 | Docker 是否使用另一套 Stage | **不另建流程**。使用通用 Stage 0-6 + backend profile，Docker 差异放入 `backend_profile` |
| 2 | Recovery Policy 是否继续细化 | **按 operation + error_class 细化**。分 `artifact_export`、`disk_format_conversion`、`runtime_configuration`、`runtime_launch` |
| 3 | Timeline parser 是否拆成 Skill | **Phase 2 不拆**，作为 parser profile；后续有实际脚本再拆 |
| 4 | Cross-skill handoff 何时触发 | **每个专项 Skill 在 Handoff Triggers 章节定义证据触发条件**（见第七节 7.5） |
| 5 | Windows Server | **Phase 2 不做**，后续独立 `windows-server-forensics` |
| 6 | rebuild-status schema | **现在补齐核心字段**（见第六节 6.4） |
| 7 | 循环依赖 | **用 `route_id`、`visited_skills`、`hop_count` 控制**（见第四节 4.3） |
| 8 | 凭据记录 | **只记录 `credential_source`、`credential_reference`、`authentication_method`**，不记录实际凭据 |

---

## 十二、总结

### v3.1 修订要点完成清单

```
✅ 1.  large-artifact-strategy 触发条件泛化（size threshold | image/container signature | high-cost full-scan risk）
✅ 2.  统一标准输入信封 request: material_info/objective/objective_status/context/payload
✅ 3.  handoff status 统一为 pending|accepted|completed|rejected|blocked，新增 priority
✅ 4.  Ledger Event 增加 route_id/handoff_id/timeline_event_refs，status 扩展为 pending|in_progress|retrying|blocked|completed|failed|skipped
✅ 5.  Executor Stage 3 输出 runtime_definition，Stage 5 输出 runtime_instance + runtime_running，Stage 6 接收两者
✅ 6.  execution_gate 与 recovery_policy 分离
✅ 7.  Recovery Policy 使用 capability + tool_candidates
✅ 8.  database access_mode 改为 online-query|offline-directory|dump-file|transaction-log|snapshot，db_type 增加 unknown
✅ 9.  Commit 1 保留全部 schemas，Commit 3 改名为 server-rebuild-executor implementation
✅ 10. Investigation Summary Route Plan 必须由 route_record.route_plan 渲染
✅ 11. 标题更新为修订版 v3.1
```

### 历史修订要点（v2 → v3）

```
✅ 1.  "统一手边格式" → "统一交接格式"
✅ 2.  取消数据契约重复：route_plan/handoffs 仅在 route_record 中
✅ 3.  objective: string|null + objective_status
✅ 4.  Ledger Event 增加 event_type/parent_event_id/status/started_at/ended_at/stdout_path/stderr_path/output_refs/artifact_refs；ID 前缀 led-
✅ 5.  删除 Authorization Required；ask_before_action → execution_gate
✅ 6.  Executor Stage 0-6 泛化（prepared_artifacts/runtime_config/runtime_instance/runtime_running）
✅ 7.  统一 backend 枚举：vmware|qemu|virtualbox|docker|wsl|manual
✅ 8.  删除 10GB Hash 阈值和 source lock；引入 hash.status + preservation_status
✅ 9.  Recovery Policy 按 operation 分类
✅ 10. rebuild-status schema 完善
✅ 11. handoff 增加防循环字段
✅ 12. Timeline Event tl- 前缀、source_type 与 parser_id 分离
✅ 13. 修正专项契约
✅ 14. 待确认问题改为已确定的设计决定
✅ 15. 标题更新为修订版 v3
```

### 下一步

v3.1 通过后，执行 **Commit 1：计划、统一契约和 Schema**，然后开始迁移具体 Skill。

---

## 附录 A：Commit 1 Contract Corrections

以下修正在 Commit 1 执行时同步落实，已反映在 `docs/data-contracts.md` 和各 Schema 文件中：

1. **标准输出统一为 6 个字段**：`investigation_summary`、`route_record`、`findings`、`ledger_events`、`artifact_refs`、`payload`。所有专项结果（`runtime_running`、`session_summary`、`table_map`、`timeline` 等）全部进入 `payload`。

2. **material_info 使用 artifact_refs**：不使用单一 `hash` 和 `size`，Hash 和大小通过 Artifact 记录获取。server-forensics-router 不在 payload 中重复 material_info 字段。

3. **修正所有伪 YAML 结构**：remote-live 使用 `connections: array`，environment 使用真正的 object 字段。

4. **recovery_policy 按 operation + error_class 组织**：tool_candidates 使用 `tool` + `operation` 结构，不使用虚构的可执行文件名。

5. **rebuild-status schema 增加 deferred_reason**：hash 对象要求 `algorithm`、`value`、`status`，command 对象要求 `command`。

6. **dependency 统一为 string|null**：routing policy 增加 `max_hops`，重新进入 Skill 时记录 `reentry_reason` 和 `new_evidence_refs`。

7. **创建 4 个新 Schema**：`timeline-event.schema.json`、`route-record.schema.json`、`request-envelope.schema.json`、`response-envelope.schema.json`。timeline 输入使用 `timezone_hint`，触发条件改为 `if temporal reconstruction is needed`。

8. **planner 字段允许为空**：`network_mode` 增加 `backend-default` 和 `none`，`port_mapping`、`credential_source`、`credential_reference`、`authentication_method` 允许 null。

9. **调用链更新**：`timeline-reconstruction (if temporal reconstruction is needed)` 替代 `if multiple time sources`。

10. **新增文件清单**：
    - `docs/data-contracts.md` — 数据契约文档
    - `templates/ledger-event.schema.json`
    - `templates/route-record.schema.json`
    - `templates/request-envelope.schema.json`
    - `templates/response-envelope.schema.json`
    - `templates/timeline-event.schema.json`
    - `templates/rebuild-status.schema.json`（已更新）
    - `templates/investigation-summary.md`
    - `templates/route-record.md`
    - `templates/README.md`
