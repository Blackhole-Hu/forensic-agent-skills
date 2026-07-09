---
name: large-artifact-strategy
description: 大体积检材处理策略。用于 1GB+ 镜像、磁盘 dump、加密容器等大文件场景，优先采用只读引用、局部采样、签名定位、offset map、分层解析。
disable-model-invocation: false
---

# large-artifact-strategy

## Purpose

large-artifact-strategy 是大文件处理的策略层。当 file-triage 检测到 >= 1GB 的检材时，自动调用本 skill。它定义了如何在不复制、不全量扫描的前提下，安全高效地定位关键数据。

## Use When

- file-triage 检测到 >= 1GB 的检材
- 检材是磁盘镜像（E01/VHD/VMDK/qcow2/raw）
- 检材是加密容器（LUKS/BitLocker/VeraCrypt）
- 检材是固件包或大型压缩包
- 需要建立 offset map 后再决定进入哪条专项路径

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `source_artifact` | Yes | 大文件路径 |
| `size` | Yes | 文件大小 |
| `file_type` | Yes | 文件类型（来自 file-triage） |
| `objective` | Recommended | 分析目标（影响采样策略） |

## Outputs

| Output | Description |
|--------|-------------|
| `source_info` | source path、size、mtime、access mode |
| `signature_hits` | 签名命中列表 |
| `offset_map` | 关键 offset 索引 |
| `sampling_results` | 采样分析结果 |
| `route_recommendation` | 下一步专项路径建议 |

## Workflow

### Step 1: Source Registration

登记 source artifact，不复制：
- source path（原始路径）
- size
- mtime
- access mode（只读）

**Evidence**: 记录 source_info

### Step 2: Header Sampling

读取文件头部（前 4KB–64KB）：
- 识别文件系统 header
- 识别分区表（MBR/GPT）
- 识别容器格式

**Evidence**: 记录 header 内容和识别结果

### Step 3: Signature Scan

对关键区域做签名扫描：
- 文件头
- 文件尾
- 已知 offset（如分区表指向的位置）
- 间隔采样（每 N MB 采样一次）

**Evidence**: 记录 signature_hits

### Step 4: Offset Map

建立 offset map：
- 每个签名命中的 offset、大小、类型
- 分区边界
- 文件系统边界
- 可疑区域

**Evidence**: 记录 offset_map

### Step 5: False Positive Escalation

对每个签名命中做 header-level verification：
- `valid` — magic + 关键字段合理
- `plausible` — magic 确认，字段部分合理
- `weak_candidate` — magic 确认但字段异常
- `false_positive` — magic 确认但字段荒谬

**false_positive 必须立即停止该路线。**

**Evidence**: 记录每个命中的验证结果

### Step 6: Route Recommendation

根据 offset map 和验证结果，推荐下一步：
- 发现文件系统 → 按需局部挂载或导出
- 发现加密层 → `nas-raid-encrypted-storage`
- 发现固件结构 → `firmware-iot-forensics`
- 发现服务器特征 → `server-forensics-router`
- 无可识别结构 → `uncommon-media-triage` 或 `proprietary-format-recovery`

**Evidence**: 记录路由建议和依据

## Evidence Requirements

| Field | When to Record |
|-------|---------------|
| `artifact` | source artifact |
| `source` | 来源路径 |
| `hash` | 如 < 10GB 可计算头部 hash |
| `command` | signature scan / sampling 命令 |
| `finding` | 每个签名命中、验证结果 |
| `confidence` | 命中验证置信度 |
| `next_action` | 路由建议 |

## Handoff

**Passes to**: `forensic-router`（传递路由建议）
**Downstream skills**: firmware-iot-forensics, nas-raid-encrypted-storage, server-forensics-router, uncommon-media-triage, proprietary-format-recovery
**Data available**: source_info, signature_hits, offset_map

## Stop Conditions

- 文件无法读取或严重损坏
- 所有 candidate routes 都验证失败（header verification 全部为 false_positive）
- offset map 无法建立且没有可用采样结果

> **Note**: 无法识别常见结构时不停止。应路由到 `uncommon-media-triage` 或 `proprietary-format-recovery` 进行进一步分析。

## Prohibited Actions

- 不得默认复制 10GB+ 检材两份
- 不得默认全量 strings / xxd / 关键词扫描
- 不得默认递归 binwalk -Me
- 不得默认挂载或激活 RAID/LVM/加密容器
- 不得在 header verification 完成前进入解包/挂载路线
- 不得把 magic 命中直接当作结构确认

## Notes

- large-artifact-strategy 是策略层，不是分析工具
- 实际的签名扫描、采样等操作由工具（binwalk、xxd、dd 等）执行
- 策略的核心是"先定位，再深入"，避免盲目全量扫描
