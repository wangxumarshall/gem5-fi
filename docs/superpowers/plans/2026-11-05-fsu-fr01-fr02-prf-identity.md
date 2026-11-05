# FR01/FR02 W1 PRF 身份路径审计与修复

日期：2026-11-05　分支：`fsu`

## 背景事实（本会话核实）

- 仓库根 `build/` 不存在，需重建 `CHAOS/gem5/build/ARM/gem5.opt`（`scons -j16`）。
- 此前 v8/v9/v10 “arch_frontend 证明 consumer 路径存在”的探针实际
  跑的是 `workloads/directed/neon_fp32_lane_kernel`，不是 W1
  （`run.out` 中 `readlink` 返回该路径）。因此“W1 scalar FP 没有
  consumer”从未被真实 W1 证据证实或证伪。
- 正式 `FSU-FR01-F0-W1/seed1` attempt-1/2：phys 随机目标 = 34，gen=1，
  before=0x0，链只有 L0/L1 → `not_consumed`。该 cell 从未被读。

## 单元 1：身份路径审计（只读）

- [x] 静态：ARM `FloatRegClass` 是 0 寄存器占位（`arch/arm/isa.cc:85`）；
      AA64 FP 操作数 `VectorReg` → `VecRegOp` → `VecRegClass`
      （`arch/arm/isa/operands.isa:90,427-443`）。
- [x] 动态：用真实 W1 运行取得一条 scalar FP 指令的
      arch reg → rename phys → source read → consumer → commit 身份链。
- [x] 对照：同一 phys cell 的 arch_frontend / phys 路径是否产生同一
      consumer 身份。
- [x] 产出 `docs/gem5-fi/fsu/FR01-FR02-PRF-IDENTITY-AUDIT.md`。

## 单元 2：目标选择最小修复（C++）

- [x] `inst_queue.{hh,cc}`：新增 `collectReadyPendingSourceCells()`
      （未发射、source ready、VecRegClass、非 always-ready、去重）。
- [x] `CHAOSPhysReg.py`：新增 `targetSelection` Param
      （`random_allocated` 默认 = 旧行为；`ready_consumer` = FR01/FR02）。
- [x] `CHAOSPhysReg.cc`：`ready_consumer` 时在候选集合中均匀抽一个；
      无候选 → 记录有界诊断并重试，不消耗 fault，不回退死槽。
- [x] `configs/fsu/FR01-F0-W1-seed1.json` 与 FR02 冻结配置显式写入
      `"target_selection": "ready_consumer"`（协议补充，登记到 docs）。
- [x] host 单测 / pytest 包装；`scons -j16` 通过。

## 单元 3：非正式 directed gate

- [x] 真实 W1 + `ready_consumer` 非正式 gate：fault_applied →
      operand_read（真实 scalar FP 指令）→ commit 或 overwrite 终局。
- [x] 显式 phys target 对照（同 cell）证明两路径身份一致。
- [x] 记录 `runs/fsu-gates/` 路径与压缩事件 SHA；不写 runids.json。

## 单元 4：原 seed1 处置与正式重跑

- [x] 保留 `FSU-FR01-F0-W1/seed1` attempt-1/2 `.real_outcome` 与哈希。
- [x] 按原冻结配置（target=-1, first_clock=10000）以修复后代码重跑，
      记录原实现缺陷、修复 SHA；新 attempt 独立编号。
- [x] 只有真实 consumer→commit 且审计通过才计入正式统计。

## 验证命令

```bash
cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt
python3 -m pytest -q tests/test_chaos_physreg_transient_cpp.py \
  tests/test_fsu_fr01_fr02_gate.py
build/ARM/gem5.opt ... configs/se/ooo_proxy.py --cmd workloads/directed/w1_fp_scalar_probe
python3 tools/fsu_chain_check.py <prop_evt.txt.gz> --run-id FSU-FR01-F0-W1
```
