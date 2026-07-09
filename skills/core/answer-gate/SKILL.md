---
name: answer-gate
description: 通用答案校验门。在提交任何结论前执行五步校验：Question Semantics、Answer Format、Evidence Binding、Cross-Validation、Final Evidence Re-read。
disable-model-invocation: false
---

# answer-gate

## Purpose

answer-gate 是提交前的最后一道校验。它从 evidence-ledger 读取所有证据，对即将提交的答案执行五步校验，确保结论有据可依、格式正确、无自相矛盾。

本 skill 从 `server-answer-gate` 泛化而来，五步校验逻辑适用于所有取证场景，不仅限于服务器。

## Use When

- 准备提交答案、flag、结论前（必经步骤）
- forensic-autopilot 的 Step 7（Validate）
- 任何 skill 准备输出最终结论前

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `question` | Yes | 原始问题或目标 |
| `proposed_answer` | Yes | 拟提交的答案 |
| `evidence_ledger` | Yes | 完整的证据记录（优先读取 `evidence-ledger.jsonl`；JSONL 不存在时回退到 `evidence-ledger.md`） |

## Outputs

| Output | Description |
|--------|-------------|
| `verdict` | `pass` / `needs_fix` / `not_locally_reproduced` |
| `check_results` | 每步校验的结果 |
| `issues` | 发现的问题列表（如有） |

## Workflow

### Check 1: Question Semantics

- [ ] 我理解问题在问什么
- [ ] 我的答案直接回答了问题（不是相关但不同的问题）
- [ ] 我没有假设问题或证据中不存在的信息
- [ ] 答案格式匹配要求（IP、域名、时间戳、flag 等）

**Evidence**: 记录语义校验结果

### Check 2: Answer Format

- [ ] 答案匹配预期格式（IPv4、email、ISO 时间戳、flag{...} 等）
- [ ] 无多余空格、换行或格式残留
- [ ] 大小写正确（flag、密码、hash）
- [ ] 数值在正确单位/范围内

**Evidence**: 记录格式校验结果

### Check 3: Evidence Binding

- [ ] 答案的每个组成部分至少有一条 evidence entry
- [ ] evidence entry 引用真实存在的 artifact（非幻觉路径）
- [ ] 能指向支持每个答案组件的具体命令输出或文件内容
- [ ] hash 值在声称完整性的地方匹配

**Evidence**: 记录每个答案组件对应的 evidence entry

### Check 4: Cross-Validation

- [ ] 没有与本次调查中其他 finding 矛盾
- [ ] 时间线事件一致（没有把未来事件当过去引用）
- [ ] 多个证据源在重叠处一致
- [ ] 负面发现不与正面发现矛盾

**Evidence**: 记录交叉验证结果

### Check 5: Final Evidence Re-read

- [ ] 重新阅读了支持答案的原始 artifact
- [ ] 证据内容与我的理解一致（无误读）
- [ ] 没有选择性忽略矛盾证据
- [ ] confidence level 有依据

**Evidence**: 记录最终复核结果

### Final Verdict

- **PASS**: 五步全部通过，可提交
- **NEEDS FIX**: 一步或多步失败，返回补充证据
- **NOT LOCALLY REPRODUCED**: 无法在本地验证，需人工审查

## Evidence Requirements

| Field | When to Record |
|-------|---------------|
| `artifact` | 被校验的答案和相关证据 |
| `finding` | 每步校验结果 |
| `confidence` | 校验结论置信度 |

## Handoff

**Passes to**: `report-writer`（校验通过后）或返回 domain skill（校验失败后补充证据）
**Data available**: 校验结果和发现的问题

## Stop Conditions

- 校验失败且无法自动修复（返回 forensic-autopilot 补充分析）
- 答案无法在本地复现（标记为 not_locally_reproduced）
- 发现证据矛盾（需要人工审查）

## Notes

- answer-gate 是强制步骤，不可跳过
- 五步校验逻辑适用于所有场景（服务器、CTF、固件、恶意样本等）
- 详见 `templates/answer-gate-checklist.md`
