---
name: tool-router
description: 执行环境路由器。判断应使用 Windows、WSL、Docker、VMware、QEMU 还是混合环境来执行取证工具，避免工具环境和路径混乱。
disable-model-invocation: false
---

# tool-router

## Purpose

tool-router 是执行环境路由器。根据任务类型和工具需求，选择最合适的执行环境（Windows、WSL、Docker、VMware、QEMU），避免环境冲突和路径混乱。

## Use When

- 需要执行取证工具但不确定在哪个环境
- 工具只在特定环境可用（如 binwalk 在 WSL，Autopsy 在 Windows）
- 需要隔离执行环境（如恶意样本分析在 VM）

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `task_type` | Yes | 任务类型（文件分析、固件解包、内存分析、网络分析等） |
| `tools_needed` | Recommended | 需要的工具列表 |
| `material_path` | Recommended | 检材路径（影响路径转换） |

## Outputs

| Output | Description |
|--------|-------------|
| `environment` | 选定的执行环境 |
| `path_mapping` | 路径转换规则（Windows ↔ WSL） |
| `tool_commands` | 在目标环境中执行的命令 |

## Workflow

### Step 1: Assess Tool Requirements

根据 task_type 和 tools_needed 判断工具的环境需求：

| Tool Category | Preferred Environment | Fallback |
|---------------|----------------------|----------|
| file, strings, xxd, binwalk | WSL | Windows (Git Bash) |
| 7z, exiftool | Windows | WSL |
| Autopsy, FTK Imager | Windows | — |
| Volatility | WSL/Python | Windows |
| tshark, Wireshark | Windows | WSL |
| docker, docker-compose | Docker | — |
| qemu-system, qemu-img | QEMU | VMware |
| vmrun, vmware | VMware | QEMU |
| Python scripts | WSL/Python | Windows Python |

**Evidence**: 记录工具环境需求

### Step 2: Determine Environment

选择单一环境或混合环境：
- 单一环境：所有工具在同一环境运行
- 混合环境：部分工具在 WSL，部分在 Windows，通过路径映射协作

**Evidence**: 记录环境选择决策

### Step 3: Set Up Path Mapping

如使用混合环境，建立路径映射：
- Windows → WSL: `E:\` → `/mnt/e/`
- WSL → Windows: `/mnt/e/` → `E:\`

**Evidence**: 记录路径映射规则

### Step 4: Generate Commands

为目标环境生成可执行的命令序列。

## Evidence Requirements

| Field | When to Record |
|-------|---------------|
| `artifact` | 待分析的检材 |
| `command` | 环境检测命令、工具调用命令 |
| `finding` | 环境选择结果 |
| `confidence` | 环境判断置信度 |

## Handoff

**Passes to**: forensic-autopilot（传递环境决策）
**Data available**: 环境、路径映射、命令模板

## Stop Conditions

- 所需工具在所有环境都不可用
- 环境配置损坏或无法启动
- 路径映射冲突

## Notes

- tool-router 只做环境选择，不执行分析
- 所有原始检材操作默认只读
- VM 环境用于隔离分析（恶意样本、不可信代码）
