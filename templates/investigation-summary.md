# Investigation Summary Template

Investigation Summary 是 Phase 2 所有 skill 的人工可读输出格式。

Route Plan **必须**由 `route_record.route_plan` 渲染，不得作为独立事实来源维护。

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

## 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| Current Assessment | Yes | 当前阶段的一句话总结 |
| Key Evidence | Yes | 1-3 条关键证据，每条包含路径/文件/配置/入口 |
| Excluded Routes | No | 仅当有被排除的路线时填写 |
| Route Plan | Yes | 从 `route_record.route_plan` 渲染 |

## 渲染规则

1. Route Plan 的内容必须与 `route_record.route_plan` 完全一致
2. 不得在 Investigation Summary 中添加 `route_record.route_plan` 不存在的步骤
3. **单一事实来源**：只能修改 `route_record.route_plan`，然后重新生成 Investigation Summary；不得直接编辑摘要中的 Route Plan
