# Templates

Phase 2 数据契约和模板文件。

## Schema 文件

| 文件 | 说明 |
|------|------|
| `ledger-event.schema.json` | 统一证据事件格式 |
| `route-record.schema.json` | 统一路由记录格式 |
| `request-envelope.schema.json` | 统一请求信封格式 |
| `response-envelope.schema.json` | 统一响应信封格式 |
| `timeline-event.schema.json` | 时间线事件格式 |
| `rebuild-status.schema.json` | 重建执行状态格式 |

## 模板文件

| 文件 | 说明 |
|------|------|
| `investigation-summary.md` | Investigation Summary 渲染规则 |
| `route-record.md` | Route Record 字段说明 |

## ID 前缀规范

| 类型 | 前缀 | 示例 |
|------|------|------|
| Ledger Event | `led-` | `led-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Timeline Event | `tl-` | `tl-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Artifact | `artifact-` | `artifact-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Route | `route-` | `route-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Handoff | `hof-` | `hof-a1b2c3d4-e5f6-7890-abcd-ef1234567890` |

## 使用方式

1. Skill 执行时产生 Ledger Event，由 `evidence-ledger` 持久化
2. Skill 输出遵循 Response Envelope 格式
3. 路由信息仅在 Route Record 中维护
4. Investigation Summary 中的 Route Plan 从 Route Record 渲染
5. Timeline Event 由 `timeline-reconstruction` 产生，引用 Ledger Event
