---
name: server-rebuild-executor
description: 执行已由 server-rebuild-planner 生成并批准的服务器重建计划。用于服务器镜像、虚拟机磁盘、Docker/WSL 服务或手工后端需要按 Stage 0-6 完成能力预检、工作副本准备、运行配置、网络配置、启动稳定、服务发现、状态落盘和计划内失败恢复的场景。
---

# server-rebuild-executor

## Purpose

将 server-rebuild-planner 输出的 rebuild_plan 转换为可审计的 Stage 0-6 执行过程。严格在 execution_scope 与 recovery_policy 内执行，持续更新 rebuild-status.json，成功后交给 remote-server-live-response；计划外动作或恢复失败时返回 planner 重新规划。

## Use When
- planner 已输出 plan_id、可执行的 rebuild_plan 和非空 executor_handoff
- plan_status: ready，且 feasibility 为 yes 或可降级执行的 partial
- 需要启动 VMware、QEMU、VirtualBox、Docker、WSL 或已定义的 manual 流程
- 需要重建状态持久化、阶段恢复和可复现连接交接

## Do Not Use When
- 尚未判断是否应重建：先调用 server-rebuild-planner
- planner 输出 plan_status: blocked|rejected 或 executor_handoff: null
- 路线为 remote-live 或 offline-image
- PVE/Ceph/多节点存储拓扑尚未由 cluster-virtualization-forensics 映射
- 需要 Linux、Web、Database 或 Docker 的深度取证；这些属于下游 domain skills
- 需要修改 rebuild plan、扩大 execution scope 或生成最终报告

## Request Contract

遵循 templates/request-envelope.schema.json。request.payload 至少包含：

~~~yaml
rebuild_plan: object
tool_capability_report: object|null
~~~

rebuild_plan 是 planner 响应 payload 的不可变包装，必须包含 plan_id、plan_status、rebuild_feasibility、selected_backend、backend_selection_status、backend_profile、prepared_artifact_requirements、resource_requirements、network_mode、port_mapping、recovery_policy、execution_scope、凭据引用和 executor_handoff。source artifacts 使用 request.material_info.artifact_refs；request.context 必须携带上游 route_record，且 plan_id、route_id 和 handoff 一致。

拒绝 selected_backend: null、backend_selection_status: unavailable 或与 plan_id 不一致的 handoff。实际凭据值不进入请求副本、状态文件、命令行、日志或 Ledger Event。

## Response Contract

遵循 templates/response-envelope.schema.json。专项结果只放在 payload：

~~~yaml
schema_version: "1.0"
investigation_summary: object
route_record: object
findings: array
ledger_events: array
artifact_refs: array
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
~~~

route_plan 与 handoffs 只存在于 route_record。成功时创建到 remote-server-live-response 的 route step 和 handoff；超出计划时创建返回 server-rebuild-planner 的 reentry handoff，`handoff.status` 为 `pending`，`route_status` 保持 `active`，并记录 `reentry_reason` 和 `new_evidence_refs`。

## Planner–Executor Boundary
| Planner owns | Executor owns |
|---|---|
| feasibility、backend 候选、资源、网络和凭据来源规划 | 验证计划与能力并执行已批准动作 |
| recovery_policy 与 execution_scope | 计划内 retry/fallback 和状态持久化 |
| 生成 plan_id 与 executor handoff | 沿用 plan_id，不改写规划 |
| 计划外重新规划 | 阻断、留证并 handoff 回 planner |

Executor 不把“已规划”写成“已执行”，不把“能启动”写成“已稳定”，不把配置推测写成恢复事实。

## State Files and Workspace

使用案件工作区内的相对路径：

~~~text
work/rebuild/rebuild-status.json
work/rebuild/rebuild-status.json.tmp
logs/rebuild/
output/rebuild/
~~~

初始化时创建包含 Stage 0-6 的状态对象。每次状态转换后：

1. 将完整新状态写入临时文件。
2. 验证其符合 templates/rebuild-status.schema.json。
3. 以同一文件系统内的原子替换更新正式文件。
4. 将旧错误、stdout、stderr 和 attempt 详情保留在 logs/rebuild/，不得静默抹除。

完成的 Stage 必须至少引用一个 evidence_event_id；Stage 编号和名称固定对应，且 0-6 唯一、完整。

## Resume and Idempotency

1. `rebuild-status.json` 不存在：初始化包含 Stage 0-6 的新状态。
2. 文件存在且 `plan_id`、`route_id` 一致：
   - 先验证 Schema；
   - 验证 completed Stage 的 `evidence_event_ids` 和输出 Artifact；
   - 从第一个未完成 Stage 继续；
   - 不重新执行已完成 Stage；
   - runtime 已存在时先查询实际状态，不重复启动。
3. 文件存在但 `plan_id` 或 `route_id` 不一致：
   - 冲突的旧状态文件保持不变，不得为了记录 blocked 而改写；
   - 本次 Response 的 `overall_status` 设置为 `blocked`；
   - 生成 finding 和 `state-transition` Ledger Event 记录冲突；
   - 返回 planner。
4. 文件损坏：
   - 原文件保留为带时间戳的损坏副本；
   - 不静默重建；
   - 阻断并报告。
5. Retry 必须增加 `attempt`，并保留历史日志和错误信息。

## State Transition Table

### Stage 状态

~~~text
pending → in_progress → completed
in_progress → retrying → in_progress
in_progress → blocked | failed
~~~

`completed` 不得无条件回到 `pending`。

### Overall 状态

~~~text
pending → in_progress
in_progress → completed | partial | blocked | failed | rolled_back
partial | blocked | failed → rolled_back
~~~

`partial|blocked|failed → rolled_back` 仅在 rollback 位于 `execution_scope`、存在有效 checkpoint，且所有批准的 rollback 操作成功后允许。

### Stage Rollback 状态

~~~text
completed | blocked | failed → rolled_back
~~~

仅限该 Stage 创建了可逆工作状态。源检材引用和纯审计 Stage 不标为 `rolled_back`。

`current_stage` 在 Stage 开始前更新。

### 状态变化流程

每次状态变化：

1. 先生成 `state-transition` Ledger Event；
2. 再使用临时文件和原子替换更新 `rebuild-status.json`。

## Stage 0-6 Workflow

### Stage 0 — Plan Validation & Preflight

**Preconditions**

- plan_status: ready
- plan_id、route ID、executor handoff 和 source artifact refs 一致
- Recovery Policy 符合 templates/recovery-policy.schema.json

**Actions**

1. 验证 backend、network mode、Stage 和 operation 均在 execution_scope 内。
2. 验证 source Artifact Record 存在，路径和 preservation 状态可解析。
3. 检查 CPU、RAM、工作磁盘空间、所需权限和网络创建能力。
4. 读取 tool_capability_report；缺失、过期、字段不完整或结论不明确时调用 tool-router 重新检查。
5. 即使报告对象存在，也必须核对目标 backend、运行程序、格式工具和必需 capability 的状态确为 available，才能将 backend 视为 confirmed。
6. 对 VM 后端检查虚拟化和嵌套虚拟化；对 Docker 检查 daemon/compose；对 WSL 检查发行版导入与运行能力。
7. 只验证 credential_reference 可解析，不读取或记录实际凭据。

**Outputs**
- preflight_report 至少包含 checked_at、recommended_backend、backend_profile、available_tools、missing_tools、available_capabilities、missing_capabilities、disk_space_available、admin_privilege、virtualization_supported、network_capabilities 和 blocker
- 经直接能力检查 confirmed 的目标 backend

**Completion criterion**

目标 backend 的所有必需 capability 均有直接检查结果，资源满足要求，且执行未越出 scope；否则本 Stage 为 blocked。

**Evidence**

为每个有证据价值的检查输出 command/finding event，并用 state-transition event 完成 Stage 0。

**Failure and recovery**

- 目标 backend 不可用或结果不明确：overall_status: blocked，handoff 回 planner；Stage 0 不执行 runtime fallback。
- 缺失能力或 scope 越界：overall_status: blocked，handoff 回 planner。
- 不因 capability report “存在”而推断工具可用。

### Stage 1 — Workspace & Source Preservation

**Preconditions**

- Stage 0 completed
- 案件工作区和 source artifact refs 可用

**Actions**

1. 建立 work/rebuild、logs/rebuild 和 output/rebuild。
2. 从既有 Artifact Record 登记 source artifacts，不重新发明 Artifact ID。
3. 建立 source → working artifact 映射，但尚未执行未批准的复制或转换。
4. 按 large-artifact-strategy 决定 Hash 状态：verified|provided|deferred|unavailable；不使用固定大小阈值。
5. 使用 original-reference|read-only-mounted|working-copy-created 描述 preservation 状态；不要把普通 lock 文件称为只读锁。

**Outputs**
- workspace_path、完整 source_artifacts、source → working map、可用空间和 rollback checkpoint

**Completion criterion**

每个 source artifact 均可追溯到既有 Artifact Record，Hash 状态和 preservation 状态明确，且源检材未被默认修改。

**Evidence**

记录 workspace、Artifact 引用、Hash 决策和 preservation finding。

**Failure and recovery**

源不存在、Artifact 引用断裂或空间不足时阻断；不得通过删除已有成果或更改源检材来绕过。

### Stage 2 — Artifact Preparation

**Preconditions**

- Stage 1 completed
- 所需 operation 位于 execution_scope.approved_operations

**Actions**

按计划分别处理 artifact access/export、disk format conversion、image extraction、working copy creation 和 backend-specific preparation。每个 operation 先由 tool-router 依据 capability 选择实际工具。

- ewfexport export：从 EWF 导出
- xmount mount：提供只读访问，不等价于导出产物
- qemu-img convert：磁盘格式转换，不假定可直接读取 E01
- VBoxManage clonemedium：仅在其格式与 operation 适用时使用

仅准备计划需要的磁盘或服务材料；支持时可使用 sparse 输出，但必须验证逻辑大小、实际占用和后端兼容性。

**Outputs**
- 每个新工作产物的 Artifact Record
- prepared_artifacts 与 source artifact 映射
- output Hash 状态和验证 finding
- 同步投影到 rebuild_status.working_artifacts，包含 type、hash 和非空 created_at

**Completion criterion**
每个 required prepared artifact 均存在、可读、映射到 source artifact，并通过计划指定的格式或完整性验证。

**Evidence**

- command event 使用 `output_artifact_refs` 引用其产出的 Artifact；
- artifact event 使用非空 `artifact_refs` 引用涉及的 Artifact；
- finding event 引用相关 Artifact 和对应的 command Ledger Event。

产物 ID 不得只写入 `output_artifact_refs` 而省略 `artifact_refs`。

**Failure and recovery**

仅按相同 operation 的 error_class 重试或换工具。不得把 export、mount 和 conversion 互相当作等价 fallback；超出 policy 时返回 planner。

### Stage 3 — Runtime Configuration

**Preconditions**

- Stage 2 completed
- prepared artifacts 满足 backend profile

**Actions**

生成 runtime_definition，不要提前创建 runtime_instance：

~~~yaml
runtime_definition:
  planned_name: string
  backend: vmware|qemu|virtualbox|docker|wsl|manual
  config_artifact_ref: "artifact-<uuid>"
  config_path: string
  config_type: string
  resources:
    cpu: integer
    ram_mb: integer
    disk_paths: array
  prepared_artifact_refs: array
  startup_method: string
  backend_profile: object
~~~

**Completion criterion**

配置产物存在并可解析，资源、磁盘和启动方法与 rebuild plan 一致，尚未声称实例已启动。

**Evidence**

配置文件作为 Artifact；生成命令、参数验证和配置摘要分别进入 Ledger。

**Failure and recovery**

仅在 runtime_configuration policy 中选择 fallback backend，且该 backend 同时位于 execution_scope.fallback_backends。切换后必须重新验证 Stage 2 输出兼容性；不兼容则阻断并重新规划。

### Stage 4 — Network Configuration

**Preconditions**

- Stage 3 completed
- network mode 位于 execution_scope.approved_network_modes

**Actions**

- 支持 host-only|nat|isolated|bridge|backend-default|none。
- bridge 仅在 scope 明确包含时使用。
- none 不创建网络；backend-default 记录后端实际采用的配置。
- 端口映射只用于适用的 backend。
- 记录网络创建、变更和验证命令。

**Outputs**

- network_config
- port_mapping、ports_mapped: boolean 与验证 finding

**Completion criterion**

实际网络模式和端口映射已验证且未越出 scope；none 和 backend-default 也有明确结果。

**Failure and recovery**

不得静默切换到 bridge、NAT 或其他未批准模式。计划外模式设置 execution gate 并 handoff 回 planner；在修订后的计划进入前不得继续执行。

### Stage 5 — Runtime Launch & Stabilization

**Preconditions**

- Stage 4 completed
- runtime definition、network config 和 startup logs 路径就绪

**Actions**

1. 执行启动命令并记录 stdout/stderr。
2. 按 backend profile 等待稳定；使用有上限的 timeout 和健康检查。
3. 启动成功后才生成：

~~~yaml
runtime_instance:
  instance_id: string
  instance_type: string
  launched_at: ISO8601
runtime_running: boolean
startup_log: string              # 捕获日志的相对路径，不内嵌日志正文
startup_log_artifact_ref: "artifact-<uuid>"
startup_errors: array
~~~

4. 保存 startup log 为 Artifact。
5. 只执行 policy 允许的 retry 或 backend fallback。

**Completion criterion**

运行实例可被后端查询，健康/稳定检查有直接输出，runtime_running 与实际状态一致；超时不算成功。

**Retry behavior**

- Stage 状态改为 retrying，attempt 增加。
- Retry event 使用 parent_event_id 关联最初失败 event。
- 每次 attempt 保留独立 stdout/stderr。
- 超过 max_attempts 后阻断或失败，不无条件切换 backend。

### Stage 6 — Service Discovery, Connection Test & Handoff

**Preconditions**

- Stage 5 completed
- runtime_running: true

**Actions**

1. 在批准范围内发现端口和服务。
2. 执行低影响连接测试，记录命令与结果。
3. 生成不含实际凭据的 connection records：

~~~yaml
connections:
  - connection_id: string
    type: ssh|webui|db-client|docker-exec|winrm|rdp|service-client
    host: string
    port: integer
    service: string|null
    credential_source: string|null
    credential_reference: string|null
    authentication_method: password|key|token|certificate|interactive|none
~~~

4. 将服务、入口和验证 finding 关联到 Artifact 和 Ledger。
5. 在 route_record.route_plan 中创建或完成 remote-server-live-response step，并生成 handoff。

**凭据和认证边界**

Stage 6 默认只做低影响、非认证确认：

- TCP 连接
- 服务 Banner
- HTTP health check
- 明确的端口映射
- 后端运行状态

认证后的取证采集交给 `remote-server-live-response`。

必须使用 Secret 时：

- 通过 `credential_reference` 即时解析
- 不放进命令行参数
- 不写入 `rebuild-status.json`
- 不写入 Ledger
- 不出现在 stdout 或 stderr
- 使用 stdin、环境变量、Secret Store 或受限临时文件
- 使用后清理临时 Secret 材料

**服务发现范围**

只允许以下目标：

- `runtime_instance` 自身地址
- `localhost`
- host-only 地址
- 明确的 `port_mapping`

不得执行无范围的子网扫描。

**Completion criterion**

至少一个服务或已证实的“未发现服务”结果有直接证据；所有连接记录均来自实际发现，handoff 通过 route/finding/artifact refs 可追溯。

**Failure and recovery**

不得伪造 connection info。服务未发现时保留 Stage 0-5 产物并设置 partial|blocked|failed；仅当既有 route_record 已包含批准的离线步骤时才能交接离线分析，否则 handoff 回 planner。

## Backend Profiles
| Backend | Capability checks | Configuration and launch evidence |
|---|---|---|
| VMware | Workstation、vmrun start/stop/status、需要时的 vmware-vdiskmanager、nested virtualization | VMX/config Artifact；按 plan 为多节点配置 system + data/OSD disks；记录 host-only/NAT 与 vmrun 输出 |
| QEMU | qemu-system-* 负责运行，qemu-img 只负责格式；验证 Windows/WSL 可用性和性能 | 完整启动参数、PID/monitor/serial log、状态查询；PVE 多节点网络复杂时不得盲目采用 WSL2 QEMU/KVM |
| VirtualBox | VBoxManage、嵌套虚拟化及 PVE/Ceph 兼容性检查 | 注册/config/startvm/状态输出；兼容性未验证时保持 provisional |
| Docker | daemon、Compose、image/load/build 能力按 plan 验证 | resolved Compose config、容器 ID、health/log output |
| WSL | import/distro/run 能力；仅用于 rootfs/distro 或适合 WSL 的应用 | distro 名、导入 Artifact、服务启动和端口证据 |
| manual | 明确人工步骤与产物引用 | 每一步命令/截图/日志均进入 Ledger；不得宣称未验证成功 |

### PVE/Ceph Multi-node Profile

仅在 planner/backend profile 已明确多节点顺序与 scope 时执行：

1. 按 node1 → node2 → node3 或 plan 指定顺序启动。
2. 对每个节点先验证系统、网络和 SSH，再检查 PVE WebUI。
3. 再按计划检查 Ceph MON、MGR、OSD，最后才考虑业务 VM 或 RBD 交接。
4. 不自动修复 Ceph，不重置密码，不修改 /etc/network/interfaces，不启动未批准的 VM。
5. 任一节点失败时保留已完成节点的状态与证据；按 policy retry，计划外拓扑变更 handoff 回 server-rebuild-planner，由 planner 决定是否在新 route plan 中先调用 cluster-virtualization-forensics 重新映射。

## Recovery Policy Execution
对失败先分类为 operation + error_class：

1. 找不到对应策略：使用 default，通常为 replan。
2. auto_retry: true 且未超过 max_attempts：执行同 operation 的候选工具或同阶段重试。
3. Backend fallback 仅允许用于 runtime configuration/launch，且必须同时存在于 policy 与 scope。
4. 所有 retry/fallback 记录 recovery action、parent event、attempt 和输出路径。
5. 超出 policy 或 scope：Stage 转为 blocked|failed，不得扩权执行。

计划内自动恢复不得修改源检材、删除已有成果、改变未批准网络模式或引入未登记输入。

## Failure Classification Matrix

错误分类名称必须与 `recovery_policy` 中的 `operation.error_class` 完全一致：

| Stage | operation | error_class | recovery_policy 引用 |
|-------|-----------|-------------|---------------------|
| 2 | `artifact_export` | `export_tool_failure` | `artifact_export.export_tool_failure` |
| 2 | `disk_format_conversion` | `unsupported_format` | `disk_format_conversion.unsupported_format` |
| 2 | `disk_format_conversion` | `tool_failure` | `disk_format_conversion.tool_failure` |
| 3 | `runtime_configuration` | `config_generation_failure` | `runtime_configuration.config_generation_failure` |
| 5 | `runtime_launch` | `startup_timeout` | `runtime_launch.startup_timeout` |
| 1, 4, 6 | 无匹配 operation | — | `recovery_policy.default` → replan |

## Rollback and Cleanup

- 只处理当前 `plan_id` 创建的 working artifacts 和 runtime；
- 不修改或删除 source artifacts；
- 不删除 Ledger、日志和失败证据；
- `rollback_available` 只有存在有效 checkpoint 且操作可逆时才为 `true`；
- rollback 完成后 `overall_status = rolled_back`；
- 每个 rollback 操作生成 command、artifact/finding 和 state-transition Ledger Event；
- 删除已有工作成果超出 `execution_scope` 时触发 `execution_gate`。

## Evidence Requirements

| Event type | Required use |
|---|---|
| command | 能力检查、导出/转换、配置、网络、启动、发现和连接测试 |
| artifact | 工作副本、转换产物、配置、启动日志及其他派生制品 |
| finding | 能力、验证、服务发现、失败分类和排除路线 |
| state-transition | 每次 Stage 状态变化、retry、fallback、blocked/failed/completed |
| handoff | 成功交给 live-response，或计划外返回 planner |

遵循 templates/ledger-event.schema.json：

- command event 必须含非空 command、started_at，完成后补 ended_at、exit_code 和 stdout/stderr。
- artifact event 必须含非空 artifact_refs；新制品使用 source_artifact_id 关联来源。
- finding event 必须含 finding、confidence，并用 artifact_refs/route_id 绑定当前证据范围；Finding Record 再用 evidence_refs 引用对应 Ledger Event。
- state-transition event 必须含固定 Stage name。
- retry event 使用 parent_event_id；handoff event 使用 route_id 与 handoff_id。

事件由 evidence-ledger 持久化到 JSONL 和 Markdown；Executor 只产生事件对象。

## Route and Handoff Rules

### Success

- 将 executor step 标为 completed。
- 新增或激活 remote-server-live-response step，并用 dependency_step_ids 指向 executor step。
- Handoff 使用 from_step_id、to_step_id、artifact/finding refs、visited skills 和 hop count。
- connection info 只包含入口元数据和凭据引用。

### Partial or blocked

需要重新规划时：

- executor `step.status` 设置为 `blocked` 或 `failed`
- planner reentry `step.status` 设置为 `pending`
- `handoff.status` 设置为 `pending`
- `route_status` 保持 `active`
- `reentry_reason` 记录 `operation` 和 `error_class`
- `new_evidence_refs` 引用本轮 Ledger Event

保留所有可复用 Artifact 与 completed Stage。防循环规则继续使用同一 route ID、visited skills、hop count 和 max hops。

只有以下情况 `route_status` 才为 `blocked`：

- 没有允许的 replan 路径
- `hop_count` 超限
- `execution_gate` 未解决
- 缺少任何可继续输入

每次返回 planner 都必须明确 `reentry_reason`、`handoff.status` 和 `route_status`。

## Execution Gate

仅在拟执行动作超出 execution_scope 时设置 required: true：

- Stage 或 operation 未获批准
- Backend 不在 approved/fallback 列表
- Network mode 未获批准
- 需要修改源检材
- 需要删除已有工作产物
- 需要使用 plan 中没有的新输入

blocked、失败或普通远程连接本身不等于 execution gate。Gate 未解决时不得执行越界动作；保留状态并返回 planner。

## Stop Conditions
- plan/handoff/route ID 不一致
- plan 不是 ready，或 feasibility 不允许执行
- source Artifact 无法解析或关键输入缺失
- 所需能力不可用，且无 policy/scope 同时允许的 fallback
- 可用空间不足或状态文件无法安全持久化
- 所需操作会修改源检材，而 scope 不允许
- route hop 超限或 handoff 会形成无新证据的循环

## Failure Reporting

失败时不得只输出错误句。至少记录：

- plan_id、route ID、Stage、attempt 和 error class
- 精确命令（脱敏后）、exit code、stdout/stderr paths
- 已完成 Stages 与可复用 Artifacts
- Recovery Policy 匹配结果和已尝试动作
- 当前 overall_status、can_continue_on_failure 和 blocker
- 下一步为 retry、planner replan，或 route_record 中已批准的替代步骤

不得把凭据、token、private key 或未脱敏 secret 写入失败日志。

## Investigation Summary

~~~markdown
## Investigation Summary

**Current Assessment**: <plan_id> 已执行至 Stage <n>，状态 <overall_status>

**Key Evidence**:
1. <能力/产物/启动或服务发现证据>
2. <状态与恢复证据>

**Excluded Routes** (if any): <排除的 backend/路线及依据>

**Route Plan**:
- <从 route_record.route_plan 渲染，不独立维护>
~~~

## Quality Checklist

- [ ] Frontmatter 只有 name 与 description
- [ ] 输入/输出使用当前 Request/Response Envelope
- [ ] Planner 的 plan_id、route ID、policy 和 scope 未被改写
- [ ] Stage 0-6 唯一、完整，编号与名称符合 Schema
- [ ] backend 只有在具体能力均验证 available 后才 confirmed
- [ ] State 更新采用临时文件、Schema 校验和原子替换
- [ ] completed Stage 至少引用一个 Ledger Event
- [ ] 不使用固定文件大小阈值决定 Hash
- [ ] 不把 EWF export、mount 和 format conversion 视为等价 operation
- [ ] runtime instance 只在 Stage 5 成功启动后创建
- [ ] bridge 和 backend fallback 同时受 policy 与 scope 约束
- [ ] Retry 增加 attempt 并用 parent event 关联失败
- [ ] 不记录实际凭据或未脱敏 secret
- [ ] 不自动修复 Ceph、重置密码或启动未批准 VM
- [ ] connection info 来自实际服务发现，不得伪造
- [ ] 成功 handoff 到 live-response；计划外失败返回 planner
- [ ] 所有结论绑定 Artifact、Ledger Event 或命令输出
- [ ] 不硬编码本机路径，不修改原始检材
- [ ] Resume 按 plan_id/route_id 一致性和 Schema 验证决定续跑或阻断
- [ ] State Transition 按临时文件、原子替换和 Ledger Event 流程执行
- [ ] Failure Classification 与 recovery_policy operation/error_class 完全一致
- [ ] Rollback 不修改源检材、Ledger、日志或失败证据
- [ ] 凭据不进入命令行、状态文件、Ledger 或日志
- [ ] 服务发现只扫描 runtime_instance、localhost、host-only 或已映射端口
