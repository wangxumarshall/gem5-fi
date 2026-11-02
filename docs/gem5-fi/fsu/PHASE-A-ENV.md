# FSU 阶段 A 环境清单（2026-11-02）

> 本文件所有数值均来自本机实测命令输出，采集时间 2026-11-02 10:46 CST。

## 1. Git 基线与工作区

| 项 | 值 |
|---|---|
| 远端 | `git@github.com:wangxumarshall/gem5-fi.git` |
| 基线分支 | `origin/fi-ding` |
| 基线 commit | `46ce66cdb9c22f5e591b43b97b68c7d526704211`（2026-10-30 16:36:19 +0800，`merge: R6-S repair2 doc audit`） |
| FSU 分支 | `fsu`（本地新建，起点 = 上述 commit） |
| FSU 工作区 | `/home/sdc/gem5-fi-fsu`（`git worktree`，绑定 `fsu`） |
| 原有工作区 | `/home/sdc/gem5-fi-ding`（分支 `fix/0202-six-chain-20261026`，未清理、未改动） |
| `origin/fsu` | 创建 `fsu` 分支时远端尚不存在；首次推送后建立 |

原工作区已有的未跟踪证据文件保持原样（未 `add`、未删除、未覆盖）：

```
?? docs/gem5-fi/lsu/evidence/0202/R0202-T02F2-CLEAN-OVERWRITE.csv
?? docs/gem5-fi/lsu/evidence/0202/R0202-T02F2-CLEAN-OVERWRITE.json
?? docs/gem5-fi/lsu/evidence/0202/R0202-T02F2-CLEAN-OVERWRITE.md
```

## 2. 服务器

| 项 | 值 |
|---|---|
| 主机 | `cathelper-k8s-worker2` |
| OS | openEuler 22.03 LTS（内核 `5.10.0-60.139.0.166.oe2203.aarch64`） |
| 架构 | aarch64（Kunpeng-920） |
| CPU | 96 逻辑核（2 socket × 48 core，1 thread/core） |
| 内存 | 313 GiB total；采集时 used 23 GiB，available 253 GiB，无 swap |
| `/home` 磁盘 | 1.1 TiB，已用 462 GiB，可用 512 GiB（48%） |
| `/tmp` | tmpfs 157 GiB，可用 123 GiB |
| `/proc/loadavg` | `172.93 176.69 164.59 165/1555 552481` |
| 在跑进程 | `sdcshield` 26 个；`gem5.opt` 0 个；`scons` 0 个 |

> 负载主要来自他人 `sdcshield` 任务（0202 高负载 campaign）。按任务纪律不杀、不干扰；
> 高负载期间只做文档/转换器/静态检查，不启动大规模 scons 或 gem5 campaign。

## 3. 工具链

| 工具 | 版本 |
|---|---|
| git | 2.33.0 |
| Python | 3.8.18（`/usr/local/bin/python3`） |
| openpyxl | 3.1.5 |
| pytest | 8.3.5 |
| SCons | 4.11.1.b97f32b9adab83a96af767ec1d7dc8d7a41c7c74 |
| gcc / g++ | 10.3.1 |
| gem5 目标 | `build/ARM/gem5.opt`（AArch64 宿主原生编译） |

## 4. gem5 构建现状

- 当前服务器上未找到任何 `gem5.opt` 二进制：
  `/home/sdc/gem5-fi-ding/build/ARM/gem5.opt` 不存在，`find /home/sdc -maxdepth 5 -name gem5.opt` 无结果。
- `fsu` 工作区为全新 checkout，`build/` 尚未生成。
- 结论：阶段 C 执行前必须完成一次干净构建
  `cd /home/sdc/gem5-fi-fsu/CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`
  （干净构建必须 `-j16`；且需等待机器负载下降后再执行）。

## 5. Excel 输入核查（BLOCKED）

期望文件：`gem5-fi-FSU单元故障注入方案_逐RunID传播监控.xlsx`
期望 SHA-256：`4A5B358CB6E12D93F5B25ED0B422C6100A30540C0693482C04AF904669B22CD6`

搜索记录（2026-11-02）：

| 命令 | 结果 |
|---|---|
| `find /home/sdc -name "*.xlsx"` | 仅 2 个：`docs/gem5-fi/ooo/gem5-fi-OOO单元故障注入方案.xlsx`、`docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx`；无 FSU 工作簿 |
| `find / -maxdepth 6 \( -name "*FSU*.xlsx" -o -name "*逐RunID*.xlsx" \)` | 无结果 |
| `find /home /tmp /root -iname "*fsu*" -o -iname "*传播*"` | 仅 `sdcshield` 的 `*_fsu_byteexact_*` 配置与报告，无 FSU 方案工作簿 |
| `git ls-tree -r origin/fi-ding \| grep -i -E 'fsu\|xlsx'` | 仅 LSU/OOO 工作簿，无 FSU 工作簿 |

**结论（2026-11-02 10:46 采集时）：服务器上不存在该文件，无法开始无损转换。**
不得用 LSU/OOO 工作簿替代，也不得伪造 SHA-256。需要用户提供文件或其准确路径。

### 5.1 更新（2026-11-02 10:52）：文件已提供

用户提供路径 `/home/sdc/fsu-input/`。实测：

| 项 | 值 |
|---|---|
| 文件 | `/home/sdc/fsu-input/gem5-fi-FSU单元故障注入方案_逐RunID传播监控.xlsx` |
| 大小 | 95572 bytes |
| SHA-256 | `4a5b358cb6e12d93f5b25ed0b422c6100a30540c0693482c04af904669b22cd6` |
| 与期望值 | 一致 |
| 落位 | `docs/gem5-fi/fsu/gem5-fi-FSU单元故障注入方案_逐RunID传播监控.xlsx`（chmod 444，只读） |

后续转换与校验见 `docs/gem5-fi/fsu/CONVERSION_REPORT.md`。

## 6. 构建环境更新（2026-11-02 14:07）

- 首次干净构建（默认 `python3-config` = Python 3.8.18）成功，二进制
  `de5cba558c25c16887130f70e77befb5a8b570a2d3319f8f212cbff703d6d720`，
  但运行 `configs/se/ooo_proxy.py` 时在 `from gem5.simulate.simulator import Simulator`
  处失败：`TypeError: unsupported operand type(s) for |: 'type' and 'type'`。
  根因：gem5 v25.1 stdlib 使用 PEP 604（`X | Y`），Python 3.8 不支持。
- 首次二进制嵌入 `PYVER 3.8.18`，**不作为权威运行二进制**；仅作证据保留。
- 主机存在 `/opt/python3.11/bin/python3.11`（3.11.9）；旧二进制
  `/home/sdc/gem5-fi-ding/.../gem5.opt` 嵌入 `PYVER 3.11.9`，但其源码状态不同，
  按任务要求不复用。
- 正在以 `PYTHON_CONFIG=/opt/python3.11/bin/python3.11-config scons -j4` 重新构建
  权威基线；新二进制需再次 smoke 验证后再用于任何 RunID。
