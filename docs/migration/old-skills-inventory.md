# Old Skills Migration Inventory

Source: `E:\CompetitionTools\skills` (41 skill directories)
Target: `E:\github_project\forensic-agent-skills`
Branch: `bootstrap`
Date: 2026-06-21

---

## Historical Main Workflow Chain

The project has already formed a proven main chain through competition practice:

```
competition-autopilot          ← master controller
  → tool-router                ← environment routing (Windows/WSL/Docker/VMware/QEMU)
  → triage-files               ← first-pass file triage
  → large-artifact-strategy    ← large file handling strategy
  → server-forensics-router    ← server forensics entry, mode selection
  → server-rebuild-planner     ← rebuild planning
  → server-rebuild-executor    ← rebuild execution
  → remote-server-live-response ← live server acquisition
  → domain-specific forensics  ← linux / webapp / database / docker / cluster
  → server-timeline-reconstruction ← log merging & timeline
  → server-answer-gate         ← pre-submission validation
  → wp/report writer           ← output generation
```

This chain drives the migration phasing below. Two new modules (`forensic-router`, `evidence-ledger`) are added to the core layer — they don't map 1:1 to old skills but are required by the control loop.

---

## Migration Phases

### Phase 1 — Core Control Loop

The minimum viable chain that can run an end-to-end forensic workflow. 9 modules total.

| # | Old Skill | New Path | Status | Notes |
|---|-----------|----------|--------|-------|
| 1 | `competition-autopilot` | `skills/core/forensic-autopilot/` | migrate + refactor | **总调度入口**。抽象迁移：剥离比赛专用逻辑（ISCC/特定 flag 格式），保留通用 autopilot 调度框架。比赛专用部分后续拆到 `skills/competition/`。REVIEW.md 9KB+ 需精简。 |
| 2 | — (new) | `skills/core/forensic-router/` | **create** | **任务/材料路由器**。判断材料进入 file-triage、server chain、timeline、recovery、competition 等路径。不来自单个旧 skill，从 competition-autopilot 的路由逻辑和 server-forensics-router 的模式选择中提取。 |
| 3 | `tool-router` | `skills/core/tool-router/` | migrate as-is | **执行环境路由器**。Windows / WSL / Python / Docker / VMware / QEMU 工具环境选择。含 CHECKLIST.md、REVIEW.md。 |
| 4 | — (new) | `skills/core/evidence-ledger/` | **create** | **证据记录核心**。不来自单个旧 skill，但贯穿全链路。定义 artifact 登记、hash 记录、操作日志、chain of custody 字段。所有取证 skill 写入 evidence-ledger，answer-gate 从 evidence-ledger 读取校验。 |
| 5 | `server-answer-gate` | `skills/core/answer-gate/` | migrate + generalize | **通用答案校验门**。从服务器场景提取，适用所有取证场景。保留五步校验：Question Semantics Check → Answer Format Check → Evidence Binding Check → Cross-Validation Check → Final Evidence Re-read。 |
| 6 | `iscc-wp-writer` (部分) | `skills/core/report-writer/` | extract + refactor | **通用报告输出**。从 iscc-wp-writer 抽取通用报告规则（结构化输出、证据引用、截图插入）。ISCC 专用版仍在 Phase 4。闭环的一部分，必须在 Phase 1。 |
| 7 | `handoff` | `skills/core/handoff/` | migrate as-is | 会话交接基础设施。 |
| 8 | `triage-files` | `skills/triage/file-triage/` | migrate + rename | **文件分流入口**。改名为 `file-triage`。保留 large-artifact-mode 分支逻辑。含 CHECKLIST.md、REVIEW.md。 |
| 9 | `large-artifact-strategy` | `skills/triage/large-artifact-strategy/` | migrate as-is | **大文件处理策略**。放在 `skills/triage/`，是分流阶段的核心策略层。含 CHECKLIST.md、REVIEW.md。 |

---

### Phase 2 — Server Forensic Chain

服务器取证完整链路，从重建到专项分析到时间线。

| # | Old Skill | New Path | Status | Notes |
|---|-----------|----------|--------|-------|
| 10 | `server-forensics-router` | `skills/server/server-forensics-router/` | migrate as-is | **服务器取证总入口**。模式选择：rebuild-and-connect / remote-live / offline-image / hybrid-cluster。含 CHECKLIST.md、REVIEW.md。 |
| 11 | `server-rebuild-planner` | `skills/server/server-rebuild-planner/` | migrate as-is | 重建规划。VMware/QEMU/VirtualBox/Docker 路径规划、网络策略、回滚计划。 |
| 12 | `server-rebuild-executor` | `skills/server/server-rebuild-executor/` | migrate + **needs-refactor** | **主闭环成员**，但需强化：Stage 0–6 阶段划分、Preflight 工具能力检查、Failure Recovery 自动回退、日志状态文件（记录每阶段执行状态）。当前实现偏薄。 |
| 13 | `remote-server-live-response` | `skills/server/remote-server-live-response/` | migrate as-is | **活体服务器采集入口**。SSH / WebUI / DB client / Docker exec / WinRM / RDP 连接后的低扰动、命令留痕活体采集。含 CHECKLIST.md、REVIEW.md。 |
| 14 | `linux-server-forensics` | `skills/server/linux-server-forensics/` | migrate as-is | Linux 系统层取证。账号、SSH、history、cron、systemd、持久化。 |
| 15 | `webapp-server-forensics` | `skills/server/webapp-server-forensics/` | migrate as-is | Web/API 取证。Nginx/Apache/IIS/Tomcat/Flask/Spring/PHP/Node。 |
| 16 | `database-server-forensics` | `skills/server/database-server-forensics/` | migrate as-is | 数据库取证。MySQL/PostgreSQL/Redis/MongoDB/SQLite/binlog/RDB/AOF。 |
| 17 | `docker-container-forensics` | `skills/server/docker-container-forensics/` | migrate as-is | Docker 取证。compose/image/volume/logs/env。 |
| 18 | `cluster-virtualization-forensics` | `skills/server/cluster-virtualization-forensics/` | migrate as-is | **PVE / Ceph / LVM / RAID / ZFS / btrfs / 集群虚拟化取证**。第二批重点。含 CHECKLIST.md、REVIEW.md。 |
| 19 | `server-timeline-reconstruction` | `skills/timeline/timeline-reconstruction/` | migrate + generalize | **通用时间线重建**。旧 server-timeline-reconstruction 先迁移为通用 timeline-reconstruction。服务器日志是第一种来源，后续扩展 PCAP、文件时间戳、浏览器历史、数据库记录、容器日志。不同时放在 skills/server/ 和 skills/timeline/。 |

---

### Phase 3 — Uncommon Media & Recovery Chain

非常见介质、专项恢复、固件、恶意样本。

| # | Old Skill | New Path | Status | Notes |
|---|-----------|----------|--------|-------|
| 20 | `uncommon-media-triage` | `skills/triage/uncommon-media-triage/` | migrate as-is | **非常见介质分流**。按底层结构分流（CAN/NMEA/GPS/TLV/传感器/时间序列），不按设备名分类。与 Phase 1 的 file-triage 互补。 |
| 21 | `proprietary-format-recovery` | `skills/recovery/proprietary-format-recovery/` | migrate as-is | 专有格式恢复。XOR/弱加密/known-plaintext/结构化明文恢复。 |
| 22 | `firmware-iot-forensics` | `skills/recovery/firmware-iot-forensics/` | migrate as-is | IoT/嵌入式固件静态分析。SquashFS/CramFS/JFFS2/UBIFS/uImage。 |
| 23 | `nas-raid-encrypted-storage` | `skills/recovery/nas-raid-encrypted-storage/` | migrate as-is | NAS/RAID/LVM/加密层识别与分流。BitLocker/VeraCrypt/LUKS/eCryptFS。 |
| 24 | `malware-forensics` | `skills/recovery/malware-forensics/` | migrate as-is | 恶意样本静态取证。PE/ELF/脚本/宏/勒索/IOC/YARA。 |

---

### Phase 4 — Competition-Specific Output

比赛专用输出和报告生成。

| # | Old Skill | New Path | Status | Notes |
|---|-----------|----------|--------|-------|
| 25 | `iscc-wp-writer` (比赛专用部分) | `skills/competition/iscc-wp-writer/` | split + refactor | ISCC 比赛专用版。通用报告规则已在 Phase 1 拆到 `skills/core/report-writer/`。此处保留比赛 Word 模板、D 盘路径等专用逻辑。 |
| 26 | `competition-autopilot` (比赛专用部分) | `skills/competition/` | extract later | 从 Phase 1 的 forensic-autopilot 中拆出比赛专用逻辑：flag 格式、比赛计时器、队伍协作模式等。 |

---

## Not Migrated — Skill Authoring Guide (docs, not runnable skill)

| Old Skill | New Path | Notes |
|-----------|----------|-------|
| `writing-great-skills` | `docs/skill-authoring-guide.md` + `templates/skill-template.md` | 从 writing-great-skills 抽取 skill 编写规范，**不迁移为 runnable skill**。编写规范以文档形式存放，GLOSSARY.md 内容合并到 skill-authoring-guide.md。 |

## Not Migrated — Generic Engineering Skills

以下 18 个通用工程 skill 不迁移，它们来自 `mattpocock/skills` 工程技能体系，非取证专用：

| Skill | 原因 |
|-------|------|
| `ask-matt` | 不保留名称；路由入口统一由 forensic-autopilot + forensic-router 承担 |
| `code-review` | 通用代码审查 |
| `codebase-design` | 通用架构设计 |
| `diagnosing-bugs` | 通用 bug 诊断 |
| `domain-modeling` | 通用领域建模 |
| `grill-me` | 通用设计面试（委托 /grilling） |
| `grill-with-docs` | 通用设计面试 + 文档 |
| `grilling` | 通用设计压力测试 |
| `implement` | 通用 PRD→代码 |
| `improve-codebase-architecture` | 通用架构报告 |
| `prototype` | 通用原型探索 |
| `research` | 通用外部调研 |
| `setup-matt-pocock-skills` | 已在新仓库完成配置 |
| `tdd` | 通用测试驱动 |
| `teach` | 通用教学 |
| `to-issues` | 通用 PRD→issue |
| `to-prd` | 通用对话→PRD |
| `triage` | 通用 issue 分流（非文件分流） |

---

## Target Directory Structure

```
skills/
├── core/                              ← Phase 1: 核心控制环
│   ├── forensic-autopilot/            ← 总调度入口（从 competition-autopilot 抽象）
│   ├── forensic-router/               ← 任务/材料路由器（新建）
│   ├── tool-router/                   ← 执行环境路由
│   ├── evidence-ledger/               ← 证据记录核心（新建）
│   ├── answer-gate/                   ← 通用答案校验门（五步校验）
│   ├── report-writer/                 ← 通用报告规则（从 iscc-wp-writer 抽取）
│   └── handoff/                       ← 会话交接
│
├── triage/                            ← 分流层
│   ├── file-triage/                   ← 文件分流（原 triage-files）
│   ├── large-artifact-strategy/       ← 大文件策略
│   └── uncommon-media-triage/         ← 非常见介质分流（Phase 3）
│
├── server/                            ← Phase 2: 服务器取证链
│   ├── server-forensics-router/       ← 服务器取证入口
│   ├── server-rebuild-planner/        ← 重建规划
│   ├── server-rebuild-executor/       ← 重建执行（needs-refactor）
│   ├── remote-server-live-response/   ← 活体采集
│   ├── linux-server-forensics/        ← Linux 取证
│   ├── webapp-server-forensics/       ← Web 取证
│   ├── database-server-forensics/     ← 数据库取证
│   ├── docker-container-forensics/    ← Docker 取证
│   └── cluster-virtualization-forensics/ ← PVE/Ceph/集群取证
│
├── timeline/                          ← 时间线重建
│   └── timeline-reconstruction/       ← 通用时间线（原 server-timeline-reconstruction）
│
├── recovery/                          ← Phase 3: 专项恢复
│   ├── proprietary-format-recovery/   ← 专有格式恢复
│   ├── firmware-iot-forensics/        ← 固件分析
│   ├── nas-raid-encrypted-storage/    ← NAS/RAID/加密
│   └── malware-forensics/             ← 恶意样本
│
└── competition/                       ← Phase 4: 比赛专用
    └── iscc-wp-writer/                ← ISCC WriteUp（比赛专用版）

docs/
├── skill-authoring-guide.md           ← Skill 编写规范（从 writing-great-skills 抽取）
└── migration/
    └── old-skills-inventory.md        ← 本文件

templates/
└── skill-template.md                  ← Skill 模板（从 writing-great-skills 抽取）
```

---

## Key Refactoring Notes

1. **forensic-autopilot** — 从 competition-autopilot 抽象，剥离比赛计时器、flag 格式、队伍模式等专用逻辑
2. **forensic-router** — 新建，从 competition-autopilot 路由逻辑和 server-forensics-router 模式选择中提取任务/材料路由
3. **evidence-ledger** — 新建，贯穿全链路的证据记录核心，定义 artifact 登记、hash、操作日志、chain of custody
4. **answer-gate** — 从 server-answer-gate 泛化，五步校验逻辑保持不变，适用范围扩展到所有取证场景
5. **report-writer** — 从 iscc-wp-writer 抽取通用报告规则（结构化输出、证据引用、截图插入），比赛模板后续单独维护
6. **timeline-reconstruction** — 旧 server-timeline-reconstruction 泛化为通用时间线重建，服务器日志是第一种来源，后续扩展 PCAP、文件时间戳、浏览器历史、数据库记录、容器日志
7. **server-rebuild-executor** — 需强化 Stage 0–6、Preflight、Failure Recovery、日志状态文件
8. **file-triage** — triage-files 改名，语义更清晰
9. **writing-great-skills** — 不迁移为 runnable skill，抽取为 `docs/skill-authoring-guide.md` + `templates/skill-template.md`
10. **ask-matt** — 不保留名称，路由入口统一由 forensic-autopilot + forensic-router 承担

---

## Auxiliary Files

每个取证 skill 附带的 CHECKLIST.md 和 REVIEW.md 在迁移时一并保留：

| 文件类型 | 数量 | 说明 |
|---------|------|------|
| CHECKLIST.md | 18 | 质量检查清单 |
| REVIEW.md | 18 | 自审报告 |
| 其他 .md | 26 | 模板、格式规范、词汇表 |
| 脚本/模板 | 6 | .py / .ps1 / .sh / .docx / .json（主要在 iscc-wp-writer） |
