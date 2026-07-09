---
name: forensic-autopilot
description: 总调度入口。接收用户输入（检材、目标），自动编排完整的取证分析链路：路由、分流、专项分析、时间线、校验、报告。只在高风险动作前询问用户。
disable-model-invocation: true
---

# forensic-autopilot

## Purpose

forensic-autopilot 是取证工作流的总调度入口。用户只需提供检材和目标，autopilot 自动完成路径规划、工具选择、初筛、专项分析、证据记录和答案输出。

本 skill 从 `competition-autopilot` 抽象而来，剥离了比赛专用逻辑（flag 格式、比赛计时器、队伍模式），保留通用调度框架。比赛专用部分在 `skills/competition/`。

## Use When

- 用户提供检材（文件、镜像、目录、远程入口）和目标（找什么、回答什么）
- 用户说"分析这个"、"看看这个镜像"、"帮我查一下"
- 比赛场景中提供题目附件和目标

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
- 产出 `material_type`、`hash`、`triage_notes`
- 记录 triage 结论到 evidence-ledger

**Evidence**: 记录文件类型、hash、triage 分类结果

### Step 4: Route

- 调用 `forensic-router`，基于 Step 3 的 `triage_notes` 做最终路径决策
- 判断检材应进入哪条分析路径（server/recovery/timeline/competition 等）
- 分配并行路径（如需要）

**Evidence**: 记录路由决策和依据

### Step 5: Domain Analysis

- 根据 forensic-router 的路由结果，进入对应的专项 skill：
  - 服务器镜像 → `server-forensics-router`
  - 固件/IoT → `firmware-iot-forensics`
  - 加密容器 → `nas-raid-encrypted-storage`
  - 恶意样本 → `malware-forensics`
  - 非常见介质 → `uncommon-media-triage`
- 多条路径可并行

**Evidence**: 每个专项 skill 写入自己的 findings

### Step 6: Timeline

- 如有多个时间源，调用 `timeline-reconstruction` 合并事件时间线

**Evidence**: 记录合并后的时间线

### Step 7: Validate

- 调用 `answer-gate` 做五步校验
- 校验不通过则返回 Step 5 补充证据

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

**Passes to**: `tool-router` → `file-triage` → `large-artifact-strategy` (if triggered) → `forensic-router` → domain skills → `answer-gate` → `report-writer`
**Data available**: evidence-ledger 中的所有记录

## Stop Conditions

- 检材类型无法判断（问用户）
- 需要高风险操作权限（执行前、网络连接、文件修改）
- 连续两个 phase 无新证据（输出 battle summary，建议路线切换）
- 超过合理时间无进展

## Notes

- 本 skill 是抽象调度框架，不包含比赛专用逻辑
- 比赛场景请使用 `skills/competition/` 下的专用 skill
- 大体积检材（>= 1GB）必须先走 large-artifact-strategy，不默认全量扫描
