# FSU 实现状态（2026-11-03，W5 suite / F5 永久故障 / FR03）

> 本文件保留 2026-11-03 开工时的代码/测试阶段记录；**正式结果以 §7 为准**。
> 开工时服务器被 root 的 `kunpeng-stl-d010` 压力程序占用（loadavg ~92），
> 资源恢复后按 §5 执行；最终计数见 §7.4。

## 1. 基线

- 分支 `fsu`；开工 HEAD `016aeafd091793578fe651d2929515d1a66dfb24`。
- **本轮开工时（历史，已被 §7.4 取代）**：历史视图 18/519 seed、6/173
  RunID；活跃视图 9/240 seed、3/80 RunID。最终事实见 §7.4。
- 历史 18 个正式 seed 只读复审计通过（最终 24 个见 §7.4）。
- FSU 测试：`python3 -m pytest tests/test_fsu_*.py tests/test_chaos_fsu_*.py tests/test_chaos_vec_stuck_cpp.py -q`
  → **216 passed**（基线 125 项全部保留）。

## 2. 已完成的代码单元

| 提交 | 内容 |
|---|---|
| `40c467ad` | W5 suite 裁决文档 + suite/component/oracle schema + 计划 |
| `1f3c0350` | W5 suite 身份/runner/计数门禁 + 五程序逐元素 oracle + 五程序 dump hunk + gate 工具 |
| `189f551d` | F5 永久故障：一次安装、多 exposure、SA0/SA1、事件容量、链审计 |
| `3c8a807a` | FR03 Vec PRF 写路径重施加 + generation 隔离 + CHAOSPhysReg 钩子 |
| `096ee156` | 五程序 element_oracle meta 预注册 + gate 回填逻辑 |

### 2.1 W5 suite

- 固定顺序 `gemm → 2mm → lu → cholesky → jacobi-2d`，`program_count=5`。
- suite seed 只有 5/5 component `audit.ok && certified && element oracle` 通过
  才计 1 个 seed；component 数不进入 519/240。
- suite runner 路径：`runs/fsu/FSU-FP04-F0-W5/seed<N>/components/<program>/...`
- 五个程序已加入 canonical array dump（`--array-dump=<path>` / env），
  `FINAL` 域与语义未变；`tools/fsu_oracle.py` 做逐元素 abs/rel/ULP 比较。
- `configs/fsu/suites/polybench-fp-v1.json` 的 binary SHA / golden 数组
  已在 §7.1 gate 后回填；W5 正式 suite 已完成（见 §7.2）。

### 2.2 F5 永久故障

- `CHAOSFPU.permanentStuck`：warm-up 后首个 eligible 安装**一次**；
  后续每个 eligible 是同一 `fault_id` 的 exposure。
- `applyStuck`：SA0 `&~mask`、SA1 `|mask`，不是 XOR；多 bit 任一不同即
  activated；非目标 lane/bit 不变。
- 事件：`fault_installed`/`carrier_state`/`exposure`/L2–L5/`chain_end`；
  `exposures_total/sampled/dropped` + 首/尾 N 有界样本；预算 >190000 拒绝。
- 审计器接受 `fault_installed` 根、exposure 不独立计 fault、强制
  `stuck_after == applyStuck(correct_before)`、首个 activated 必须在 L5
  直接 parent 链。
- F5 预注册配置：gate（FP06-b SA1）+ seed1 SA0 / seed2 SA1 / seed3 固定
  mantissa；运行前固定，不看结果修改。
- **FP06-d partial-product proxy 仍为 MISSING**，未用结果位代理。

### 2.3 FR03

- 已完成（最终状态）：Vec 写路径每次写入后重施加 SA0/SA1；永久物理 cell
  跨 generation 保留，generation 只标识分配世代/暴露链；Vec 索引不再被
  legacy periodic re-apply 当 int 写入；CHAOSPhysReg FSU_PROP L0–L4 部分层
  已构建通过。
- host 单测：连续 8 次 Vec 写保持 SA0、非 XOR、free 后新 generation 仍
  卡死、generation 链重启、squash 后仍卡死、其他 cell/class 不串扰、
  reset 后清除。
- **仍缺**：L5 commit/squash/oracle/first-impact、runner 显式 CHAOSPhysReg
  路径、O3 容器级完整测试、FR03 正式 seed。
- 因此 **FR03-F5 不得运行正式 seed**，也不得借用 FP06 证据认证。

## 3. 双视图计数（本轮开工时历史记录；最终见 §7.4）

> 本节是代码阶段的历史快照，明确标注“本轮开工时”，不是当前计数。

- 本轮开工时（历史）：**18/519 seed，6/173 RunID**。
- 本轮开工时（历史）：活跃（F0/F5）**9/240 seed，3/80 RunID**。
- 本轮开工时（历史）：F0-W5 0/3；FP06-F5-W3 0/3；FR03-F5-W3 0/3。
- 最终：F0-W5 3/3、FP06-F5-W3 3/3、FP06-F5-W1 3/3（§7）；FR03 仍 BLOCKED。

## 4. 资源规则

每 10 分钟检查：

```bash
uptime
ps -eo user,pid,%cpu,cmd --sort=-%cpu | head
```

只要 `kunpeng-stl-d010` 仍高负载或 `loadavg > 16`：

- 不启动 scons / gemm5 / 大规模 native golden；
- 不终止、不暂停、不干扰该 root 进程；
- 只做代码、文档、轻量 Python/host 单测。

## 5. 资源恢复后的执行顺序（已执行；保留为复现记录）

```bash
# 0) 再次确认 loadavg <= 16 且压力进程已退出
uptime

# 1) 重建 gemm5（会重新生成 CHAOSFPU/CHAOSPhysReg params）
cd /home/sdc/gem5-fi-fsu/CHAOS/gem5
scons -j16 build/ARM/gem5.opt

# 2) 重建五个 PolyBench 二进制（新增 dump hunk）
cd /home/sdc/gem5-fi-fsu
make -C workloads/ooo polybench

# 3) W5 无故障 gate：native 3× + gemm5 B0 3×，生成 golden 并回填
python3 tools/fsu_w5_gate.py --create-golden --update-suite \
    --outdir runs/fsu-gates/W5-ELEMENT-ORACLE-GATE

# gate 必须 PASS；否则 F0-W5 保持 BLOCKED

# 4) F5 非正式 gate（不计 519）
python3 tools/fsu_seed_runner.py \
    --manifest configs/fsu/FSU-FP06-F5-W3-PERMANENT-GATE.json \
    --seed 1 --out-root runs/fsu-gates/F5-FP06-W3-PERMANENT-GATE
python3 tools/fsu_seed_audit.py \
    runs/fsu-gates/F5-FP06-W3-PERMANENT-GATE/FSU-FP06-F5-W3-PERMANENT-GATE/seed1/attempt-1

# 5) 正式 W5：seed1 五个 component 全过 → suite MD → seed2 → seed3
python3 tools/fsu_suite_runner.py --suite configs/fsu/suites/polybench-fp-v1.json \
    --run-id FSU-FP04-F0-W5 --suite-seed 1
# ... suite-seed 2 / 3 依次执行

# 6) 正式 F5：预注册 seed1/2/3
python3 tools/fsu_seed_runner.py --manifest configs/fsu/FSU-FP06-F5-W3-seed1.json --seed 1
python3 tools/fsu_seed_runner.py --manifest configs/fsu/FSU-FP06-F5-W3-seed2.json --seed 2
python3 tools/fsu_seed_runner.py --manifest configs/fsu/FSU-FP06-F5-W3-seed3.json --seed 3

# 7) 索引与审计
python3 tools/fsu_index.py
```

> 注意：第 5 步的 CLI 以 `tools/fsu_suite_runner.py --help` 为准；不得手工
> 补写传播事件或 Markdown。所有正式 seed 完成后必须以磁盘审计结果计
> 数：
> - W5 完成：历史 21/519、7/173；活跃 12/240、4/80。
> - 再完成 FP06-F5-W3：历史 24/519、8/173；活跃 15/240、5/80。

## 7. 正式实验结果（2026-11-03 20:00–21:00，负载恢复后）

### 7.1 W5 element-oracle gate

`runs/fsu-gates/W5-ELEMENT-ORACLE-GATE/`：**PASS**。五个程序 native 3× 与
gemm5 B0 3× 的 canonical array SHA-256 完全一致，逐元素 mismatch=0，
FINAL 与注册 golden 一致，suite_hash `7282decf…` 稳定。

### 7.2 F0-W5（FSU-FP04-F0-W5）COMPLETE_3_OF_3

| suite seed | gemm | 2mm | lu | cholesky | jacobi-2d | suite audit |
|---|---|---|---|---|---|---|
| 1 | admitted/SDC | admitted/SDC | admitted/SDC | admitted/MASKED | admitted/SDC | ok |
| 2 | admitted/SDC | admitted/SDC | admitted/SDC | admitted/SDC | admitted/SDC | ok |
| 3 | admitted/SDC | admitted/SDC | admitted/SDC | admitted/SDC | admitted/SDC | ok |

seed1 的 attempt-1 因 submodel=FP04-c 审计失败，证据保留；attempt-2 修正后
5/5 通过。每个 suite seed 在
`runs/fsu/COMPLETE_PROPAGATION_PATHS/FSU-FP04-F0-W5/` 只有 1 个 suite-level
Markdown，链接 5 个 component attempt。

### 7.3 FP06-F5-W3（FSU-FP06-F5-W3）COMPLETE_3_OF_3

| seed | 预注册 | mask | polarity | exposures | activated | terminal | oracle |
|---|---|---|---|---:|---:|---|---|
| 1 | FP06-a SA0 | `0x80000000` | 0 | 16,384 | 764 | full | SDC |
| 2 | FP06-b SA1 | `0x80000000` | 1 | 16,384 | 15,620 | full | SDC |
| 3 | FP06-c fixed mantissa | `0x007f8000` | 0 | 16,384 | 16,296 | full | SDC |

每 seed 只有 1 次安装、1 个 fault_id、固定 mask/polarity；`total =
sampled + dropped`；三个 attempt 独立 audit/certified 全部通过。

### 7.4 计数（磁盘权威审计结果）

- 历史视图：**50/519 seed，16/173 RunID**（FR07-F0-W1 旧 proxy attempt 保留，当前 3 seed 由真实 PRF-WB hook 认证）
- 活跃视图（F0/F5）：**41/240 seed，13/80 RunID**
- FSU 测试：**329 passed**（含 W6 gate 测试）（`tests/test_fsu_*.py tests/test_chaos_fsu_*.py
  tests/test_chaos_vec_stuck_cpp.py tests/test_chaos_physreg_generation_cpp.py`）
- 历史 18 个正式 seed + F5 6 个正式 seed 单 seed 只读审计全部 ok；
  3 个 W5 suite seed 的 suite audit 全部 ok。

### 7.6 FP06-F5-W1（FSU-FP06-F5-W1）COMPLETE_3_OF_3

gate：`runs/fsu-gates/F5-FP06-W1-v3/`（非正式，不计 519/240）
四项全部 PASS：FP32 SA0、FP64 SA1、FP32 fixed mantissa、
precision-mismatch eligible=0；gate 证据另有 opClass/regClass 过滤、
守恒、采样、chain_end、B0 config、golden/fault oracle 检查。

| seed | 预注册 | precision | mask | polarity | eligible | exposures | sampled | dropped | activated | terminal | oracle |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 1 | FP06-a | fp32 | `0x80000000` | 0 | 41,216 | 40,192 | 513 | 39,679 | 15,027 | full | SDC |
| 2 | FP06-b | fp64 | `0x8000000000000000` | 1 | 41,216 | 40,192 | 514 | 39,678 | 25,543 | full | SDC |
| 3 | FP06-c | fp32 | `0x007f8000` | 0 | 41,216 | 40,192 | 514 | 39,678 | 29,559 | full | SDC |

每 seed 一次永久安装、一个 `fault_id`、mask/polarity/precision/opClass
固定；`exposures_total = sampled + dropped`；逐 seed audit.ok/certified。

### 7.7 FR03 状态（仍不运行正式 seed；承 §7.5）

工作簿原文裁决：永久 key = reg_class + phys_index + lane/mask + polarity；
generation 只标识分配世代/暴露链，不是清除条件。已实现并构建通过：
Vec 写路径重施加、跨 generation 持久、generation 链重启、CHAOSPhysReg
FSU_PROP 部分层（L0–L4）。仍缺 L5 commit/squash/oracle/first-impact、
runner 显式 CHAOSPhysReg 路径、O3 容器级验证。FR03-F5 保持 BLOCKED。

### 7.5 FR03 状态（仍不运行正式 seed）

- 已完成：Vec 写路径重施加、永久物理 cell 跨 generation 语义、Vec 不再
  误写 int PRF、连续写/跨代/链重启/squash/reset host 单测；CHAOSPhysReg
  的 FSU_PROP L0–L4 部分层已构建通过。
- 仍未完成：L5 commit/squash/oracle/first-impact、runner 显式
  CHAOSPhysReg 路径、O3 容器级 squash/rename/free/realloc 验证。
  FR03-F5 仍 0/3，不认证。
- 因此 FR03-F5-W3 保持 BLOCKED；未借用 FP06 结果侧证据认证 FR03。
