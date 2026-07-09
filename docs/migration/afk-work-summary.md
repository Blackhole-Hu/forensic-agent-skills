# AFK Work Summary

**Date**: 2026-07-09
**Branch**: `bootstrap`
**Base**: `main` (14bbef3)

---

## Completed Stages

| Stage | Description | Commit | Files |
|-------|-------------|--------|-------|
| **Stage 1** | 提交当前文档基线 | `674c276` docs: initialize migration plan and agent rules | 7 files, +468 |
| **Stage 2** | 创建项目骨架 | `9312538` chore: create repository structure | 13 files, +220 |
| **Stage 3** | 创建核心文档和模板 | `894db18` docs: add workflow standards and templates | 10 files, +635 |
| **Stage 4** | 迁移 Phase 1 核心 skill 草案 | `3d103cd` feat: add phase 1 core skill drafts | 9 files, +1031 |
| **Stage 5** | 最终自检和 AFK 总结 | `843bc7d` docs: summarize afk migration work | 1 file, +183 |

**Total**: 5 commits, 40 files changed, +2537 lines, -1 line

> **Self-reference note**: This summary file was written during Stage 5 before its own commit. The commit log below reflects the actual state after all 5 commits were created.

---

## AFK-Stage Commit Log

> This section records the AFK task commits only. Later review-fix commits may exist on the same branch.

```
843bc7d docs: summarize afk migration work
3d103cd feat: add phase 1 core skill drafts
894db18 docs: add workflow standards and templates
9312538 chore: create repository structure
674c276 docs: initialize migration plan and agent rules
14bbef3 (origin/main, main) Initial commit
```

---

## New/Modified Files

### Documentation (docs/)

| File | Purpose |
|------|---------|
| `AGENTS.md` | Agent 配置和工作流程规则 |
| `README.md` | 正式 GitHub 项目首页 |
| `.gitignore` | 增加 .reasonix/ 规则 |
| `docs/agents/domain.md` | 领域文档消费规则 + 核心词汇表 |
| `docs/agents/issue-tracker.md` | GitHub Issues 使用规范 |
| `docs/agents/triage-labels.md` | Triage label 映射 + 建议标签 |
| `docs/adr/README.md` | ADR 目录说明 |
| `docs/evidence-standard.md` | 证据标准（什么是证据、如何记录） |
| `docs/migration/old-skills-inventory.md` | 旧 skill 迁移清单（4 Phase） |
| `docs/migration/notes.md` | 迁移工作笔记和开放问题 |
| `docs/skill-authoring-guide.md` | Skill 编写规范（从 writing-great-skills 抽取） |
| `docs/workflow-model.md` | 工作流模型（链式调用、分支、证据流） |

### Templates (templates/)

| File | Purpose |
|------|---------|
| `templates/skill-template.md` | SKILL.md 起始模板 |
| `templates/evidence-ledger.md` | 证据记录模板 |
| `templates/investigation-log.md` | 调查日志模板 |
| `templates/forensic-report.md` | 取证报告模板 |
| `templates/wp-template.md` | 竞赛 WriteUp 模板 |
| `templates/answer-gate-checklist.md` | 五步校验清单 |

### Phase 1 Core Skills (skills/)

| Skill | Source | Status |
|-------|--------|--------|
| `skills/core/forensic-autopilot/SKILL.md` | competition-autopilot (抽象) | Draft |
| `skills/core/forensic-router/SKILL.md` | 新建（从 autopilot 路由逻辑提取） | Draft |
| `skills/core/tool-router/SKILL.md` | tool-router (迁移) | Draft |
| `skills/core/evidence-ledger/SKILL.md` | 新建 | Draft |
| `skills/core/answer-gate/SKILL.md` | server-answer-gate (泛化) | Draft |
| `skills/core/report-writer/SKILL.md` | iscc-wp-writer (通用规则抽取) | Draft |
| `skills/core/handoff/SKILL.md` | handoff (迁移) | Draft |
| `skills/triage/file-triage/SKILL.md` | triage-files (重命名) | Draft |
| `skills/triage/large-artifact-strategy/SKILL.md` | large-artifact-strategy (迁移) | Draft |

### Skeleton Directories (README.md only)

| Directory | Purpose |
|-----------|---------|
| `skills/server/` | Phase 2: 服务器取证链（10 个 skill 待迁移） |
| `skills/timeline/` | 时间线重建 |
| `skills/recovery/` | Phase 3: 专项恢复（5 个 skill 待迁移） |
| `skills/competition/` | Phase 4: 比赛专用输出 |
| `skills/experimental/` | 实验性 skill |
| `skills/deprecated/` | 已废弃 skill |
| `examples/` | 示例 |
| `tests/` | 测试 |
| `scripts/` | 自动化脚本 |

---

## Old Skills Referenced

| Old Skill | Used For |
|-----------|----------|
| `competition-autopilot` (655 lines) | forensic-autopilot 的调度逻辑、路由逻辑、大文件门控、误报升级门控 |
| `tool-router` | tool-router 的环境选择逻辑 |
| `server-answer-gate` | answer-gate 的五步校验逻辑 |
| `iscc-wp-writer` (README + JSON config) | report-writer 的通用报告规则 |
| `handoff` | handoff 的交接文档结构 |
| `triage-files` | file-triage 的分流逻辑和 Large Artifact Mode |
| `large-artifact-strategy` | large-artifact-strategy 的采样、签名扫描、offset map 策略 |

---

## Not Completed / Needs Follow-up

### Phase 2 — Server Forensic Chain (10 skills)

- server-forensics-router
- server-rebuild-planner
- server-rebuild-executor (needs-refactor)
- remote-server-live-response
- linux-server-forensics
- webapp-server-forensics
- database-server-forensics
- docker-container-forensics
- cluster-virtualization-forensics
- timeline-reconstruction

### Phase 3 — Uncommon Media & Recovery (5 skills)

- uncommon-media-triage
- proprietary-format-recovery
- firmware-iot-forensics
- nas-raid-encrypted-storage
- malware-forensics

### Phase 4 — Competition-Specific Output

- iscc-wp-writer (competition-specific version)
- competition-autopilot (competition-specific logic extraction)

### Documentation

- CONTEXT.md（领域词汇表，待 /domain-modeling 技能创建）
- docs/adr/（架构决策记录，待决策时创建）

---

## Questions for Human Review

### Q1: evidence-ledger 格式

**Current decision**: Dual-format — Markdown (`evidence-ledger.md`) for human review primary view, JSONL (`evidence-ledger.jsonl`) for machine validation log. Both formats record the same entries; skills write to both simultaneously. `answer-gate` prefers JSONL for structured checks; `report-writer` references Markdown for report appendices.

### Q2: forensic-router vs server-forensics-router 边界

forensic-router 是顶层路由器，server-forensics-router 是服务器专用入口。两者的关系需要确认：
- forensic-router 直接调用 server-forensics-router？
- 还是 forensic-router 做粗分类，server-forensics-router 做细分类？

**Current decision**: forensic-router 委托给 server-forensics-router

### Q3: timeline-reconstruction 第一版支持哪些数据源？

建议第一版支持：auth.log、access.log、journal、Docker logs。
第二版扩展：PCAP、文件时间戳、浏览器历史、数据库记录。

### Q4: server-rebuild-executor 需要强化的范围

旧版实现偏薄，需要强化：
- Stage 0–6 阶段划分
- Preflight 工具能力检查
- Failure Recovery 自动回退
- 日志状态文件

具体强化到什么程度？

---

## Next Steps

1. **人工审查** Phase 1 的 9 个 skill 草案，确认方向正确
2. **开始 Phase 2** 迁移服务器取证链（10 个 skill）
3. **创建 CONTEXT.md** 领域词汇表
4. **编写测试** 验证 skill 结构和证据要求
5. **开始 Phase 3** 迁移专项恢复链（5 个 skill）
6. **开始 Phase 4** 比赛专用输出
