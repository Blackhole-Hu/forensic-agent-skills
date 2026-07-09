---
name: file-triage
description: 文件分流入口。对 incoming material 做第一轮只读排查：文件识别、hash 计算、分类、路由。大文件进入 Large Artifact Mode。
disable-model-invocation: false
---

# file-triage

## Purpose

file-triage 是所有检材的第一轮只读分流。识别文件类型、计算 hash、建立工作目录、分类并路由到正确的分析路径。

本 skill 从 `triage-files` 重命名而来，语义更清晰。

## Use When

- forensic-autopilot 的 Step 3（Triage）
- 用户提供新的检材需要初步分析
- 需要判断检材类型和大小以决定后续路径

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `material` | Yes | 检材路径（文件、目录、压缩包、镜像） |
| `objective` | Recommended | 分析目标（影响分类优先级） |

## Outputs

| Output | Description |
|--------|-------------|
| `material_type` | 检材类型（文件/目录/压缩包/镜像/固件/PCAP） |
| `file_list` | 文件清单（如目录或压缩包） |
| `hash` | 检材的 SHA256 hash |
| `size` | 检材大小 |
| `triage_notes` | 分类结论和路由建议 |
| `large_artifact_mode` | 是否触发大文件模式 |

## Workflow

### Step 1: Artifact Precheck

- 确认检材存在
- 读取大小和 mtime
- 判断是单文件还是目录
- 如果 >= 1GB，标记 `large_artifact_mode: true`

**Evidence**: 记录检材路径、大小、mtime

### Step 2: Hash (Conditional)

- < 1GB: 默认计算 MD5 + SHA256
- 1GB–10GB: 可计算但记录耗时
- 10GB+: 不默认完整 hash，不阻塞后续分析

**Evidence**: 记录 hash 值

### Step 3: File Identification

- 对单文件：`file` 命令识别类型
- 对目录：生成轻量 manifest，找最大文件
- 对压缩包：`7z l` 列出内容
- 对镜像：识别文件系统类型

**Evidence**: 记录 file 命令输出和文件类型

### Step 4: Classification

根据文件类型分类：

| Type | Category | Next Step |
|------|----------|-----------|
| 压缩包 (zip/tar/7z/rar) | archive | 解压后重新 triage |
| 磁盘镜像 (E01/VHD/VMDK/qcow2/raw) | disk-image | → server-forensics-router |
| 固件 (SquashFS/CramFS/JFFS2/UBIFS) | firmware | → firmware-iot-forensics |
| PE/ELF 二进制 | binary | → malware-forensics |
| PCAP/网络流量 | network | → timeline-reconstruction |
| 数据库文件 | database | → database-server-forensics |
| Web 源码/配置 | webapp | → webapp-server-forensics |
| 文本/JSON/XML/CSV | text | 直接分析 |
| 图片/音频/视频 | media | → uncommon-media-triage |
| 未知 | unknown | → forensic-router |

**Evidence**: 记录分类结果和路由建议

### Step 5: Workspace Setup

建立标准工作目录和文件：

| Directory/File | Purpose |
|----------------|---------|
| `original/` | 保存原始检材引用或只读副本 |
| `work/` | 保存分析副本、采样片段、索引 |
| `output/` | 保存导出结果 |
| `scripts/` | 保存本次调查使用的脚本 |
| `logs/` | 保存命令输出 |
| `evidence-ledger.md` | 人工审查主视图 |
| `evidence-ledger.jsonl` | 机器校验日志 |
| `investigation-log.md` | 记录调查过程 |
| `notes.md` | 记录分析笔记 |

**Evidence**: 记录工作目录结构

## Large Artifact Mode

触发条件（满足任一）：
- 单文件 >= 1GB
- 目录内存在 >= 1GB 的主文件
- 扩展名或 file 结果属于 raw/bin/img/dd/E01/vmdk/vhd/qcow2

触发后：
- 调用 `large-artifact-strategy`
- 不默认复制两份大文件
- 不默认全量 strings/xxd/hash
- 先建立 source path、size、mtime、采样、signature hits、offset map

## Evidence Requirements

| Field | When to Record |
|-------|---------------|
| `artifact` | 检材本身 |
| `source` | 检材来源路径 |
| `hash` | 检材 hash |
| `command` | file/7z/hash 命令 |
| `finding` | 文件类型、分类结果 |
| `confidence` | 分类置信度 |

## Handoff

**Passes to**: `forensic-router`（传递分类结论）、`large-artifact-strategy`（大文件）
**Data available**: material_type, file_list, hash, triage_notes

## Stop Conditions

- 检材不存在或无法读取
- 检材严重损坏，无法取得任何可用元数据、采样结果或文件头
- 用户目标缺失且无法从上下文推断

> **Note**: 无法识别常见文件类型时不停止；应记录 unknown classification，并交给 `forensic-router` 决定是否进入 `uncommon-media-triage` 或 `proprietary-format-recovery`。

## Notes

- file-triage 是只读操作，不修改原始检材
- 大文件模式下，work/ 只保存采样片段和索引，不代表完整副本
- 详见 `templates/evidence-ledger.md` 记录格式
