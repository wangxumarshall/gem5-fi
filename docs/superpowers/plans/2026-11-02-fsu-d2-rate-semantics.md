# FSU D2：频率 rate 语义、W4-rate-v1 与 F3 多故障门禁

> 依据：`docs/gem5-fi/fsu/FREQUENCY_SEMANTICS.md`（D1）路径 1。
> 原则：只用 `fsu` 分支；一任务一提交；每个任务先实证再提交。
> 本计划只执行前四项（矩阵刷新、rate 语义、W4-rate-v1、F3 门禁），
> **不**启动 F1/F2/F3 的正式三 seed 批量运行。

## 0. 事实基线

- D1 已确认：短 W4 `elemwise_fma_kernel` 实测 `CHAOS_ELIGIBLE_COUNT=57347`；
  F1 首个间隔下界 500000 > 57347，必然零注入；F2 不稳定；F3 约 5–6 次。
- 当前 gem5 二进制：`CHAOS/gem5/build/ARM/gem5.opt`（仓库根 `build/ARM/gem5.opt` 不存在）。
- 当前 F0 三 seed 3/3 是既有事实，任何改动不得破坏其证据。
- F1/F2/F3 不得用 F0 语义换标签；runner 与 C++ 都必须拒绝缺少真实 ordinal 的 F1/F2/F3。

## 1. 任务 A：实施矩阵事实刷新（1 commit）

改动：
- `tools/fsu_implementation_matrix.py`
  - 保留 `BASELINE_GAPS`（历史审计事实，不删除）；
  - 新增 `current_status` 实时探测：gem5 二进制路径/存在性/SHA-256、FSU PROP 发射端、
    链审计器、三 seed runner、rate ordinal 工具、模型级测试、B0 配置差异；
  - 新增 `resolved_by_commit`（每条历史 blocker → 解决提交）；
  - 每条 RunID 同时记录 `baseline_blockers` 与 `blockers`（仅剩余缺口）；
  - summary 增加 `baseline_gap`、`current_status`、`resolved_by_commit`、
    `current_binary_sha256`、`remaining_gaps`。
- `tests/test_fsu_implementation_matrix.py` 更新 schema 断言。
- 重新生成 `IMPLEMENTATION_MATRIX.{json,csv}`、`IMPLEMENTATION_AUDIT.md`。

验证：
```bash
python3 -m pytest tests/test_fsu_implementation_matrix.py -q
python3 tools/fsu_implementation_matrix.py
```
提交：`[FSU][D2] 实施矩阵事实刷新：baseline_gap / current_status / resolved_by_commit`
推送 `origin fsu`。

## 2. 任务 B：F1/F2/F3 rate ordinal 语义（1 commit）

### B1 Python 生成器
新文件 `tools/fsu_rate_ordinals.py`：
```python
build_rate_ordinals(N, rate, jitter_pct, seed, warmup=0)
```
- SplitMix64 固定 PRNG；interval ∈ [ceil(0.5·rate), floor(1.5·rate)]；
- ordinal 为 interval 累加（从 warmup 起），严格递增、无重复、≤ N；
- 返回 generator/version/seed/rate/jitter/warmup/bounds/ordinals/intervals；
- 禁止 geometric/probability 近似。

### B2 runner
`tools/fsu_seed_runner.py`：
- manifest `injector.rate = {rate_divisor, jitter_pct, warmup}`；
- F1/F2/F3 ↔ 1e6/1e5/1e4 强校验；F0 + rate 或 F1/F2/F3 缺 rate → `ValueError`；
- census 后生成 ordinals，写 `ordinals.json` + SHA-256；
- 注入命令传 `--fpu_rate_ordinals`、warmup、rate、jitter；`max_faults=len(ordinals)`；
- 零 ordinal：保留 attempt，状态 `not_activated`，reason
  `eligible_below_first_ordinal`，不计 3/3；
- rate 模式要求实际注入数 == ordinal 数，否则失败（不得静默少注入）。

### B3 C++ 注入器
`CHAOSFPU.{hh,cc,py}`、`ooo_proxy.py`、`CHAOSPropagation.hh`：
- 新参数 `rateOrdinals`/`rateWarmup`/`fsuRateDivisor`/`fsuJitterPct`；
- 按 eligible 序号（has_fp_dest 同 census 流）精确命中 ordinal；
- F1/F2/F3 无 ordinals、F0 带 ordinals、rate 档位与 divisor 不符 → panic；
- 每个 fault 事件记录 `eligible_ordinal/eligible_total/freq/rate_divisor/
  jitter_pct/interval/ordinal_index`；每 fault 独立 fault_id + L0 root；
- rate 与 fpsr_suppress/f3_dependent 互斥（否则会漏掉 ordinal，loud reject）。

### B4 测试
`tests/test_fsu_rate_ordinals.py`：
- 三档 interval 边界；严格递增；同 seed 可重放；不同 seed 不同；
- N < 首 ordinal 零注入；N == 首 ordinal 恰好命中；
- warmup；jitter=0；rate 档位/divisor 校验；F0/F3 标签拒绝；
- POSITIVE/NEGATIVE：runner 拒绝“只改 freq 标签”。

验证：
```bash
python3 -m pytest tests/test_fsu_rate_ordinals.py tests/test_fsu_seed_runner.py -q
cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt
```
提交：`[FSU][D2] F1/F2/F3 确定性 rate ordinal 发射语义`
推送；记录新 gem5 SHA-256。

## 3. 任务 C：W4-rate-v1 与 golden/census（1 commit）

- 新源 `workloads/directed/elemwise_fma_kernel_rate_v1.c`（不覆盖短 W4）：
  `N_BASE=8192`、`REPEAT`（默认 32）个确定性块，输入 LCG 连续，FP 操作不变。
- 构建：`gcc -O2 -static -DN_BASE=8192 -DREPEAT=32 -o ...`（host aarch64）。
- 无注入 golden 至少 3 次，ARRAYHASH 逐字节一致；记录 stdout/stderr/stats SHA-256、
  运行时间与资源；golden 写入 manifest。
- countOnly 实测 N_eligible（不按线性推算）；目标 N ≥ 1,500,000；
  若不足，按预注册预算提升 REPEAT 后重建（不按 seed 结果调参）。
- 新 manifest `configs/fsu/FSU-FP04-{F1,F2,F3}-W4.json`，rate divisor 正确；
  workload identity 记为 W4-rate-v1，并记录与原 W4 的关系。
- 新文档 `docs/gem5-fi/fsu/W4-RATE-V1.md` 记录源码/构建/哈希/ROI/三次 golden/
  census/运行时/identity。

验证：
```bash
sha256sum workloads/directed/elemwise_fma_kernel_rate_v1
python3 -m pytest tests/test_fsu_workload_identity.py -q  # 若新增
```
提交：`[FSU][D2] W4-rate-v1：可配置 ROI、三次 golden 与 eligible census`
推送。

## 4. 任务 D：F3 多故障机制门禁（1 commit）

- `fsu_chain_check`：逐 fault 已独立；补充 seed 级 `fault_terminal_summary`；
  `certified` 仍要求**全部** fault admitted（一个 L5 不能自动认证其余）。
- `fsu_seed_doc`：逐 fault 展示主链/终局；run-level oracle 与每 fault terminal
  分开；保留单 fault 兼容行。
- `fsu_seed_audit`：逐 fault 重算并核对；新增“所有 injected fault 均 admitted”
  与 per-fault `fault_audit`。
- 门禁用短 W4（N=57347）+ F3（rate=1e4, jitter=50, seed=1），
  out-root `runs/fsu-gates/F3-multifault-gate`，不污染正式 173 RunID 计数。
- 门禁必须：≥1 真实 injection；每个 fault 有独立 L0–terminal 链；
  chain_report 同时保存多个 fault；Markdown 逐 fault；run oracle 独立；
  审计逐 fault；gzip 完整；stats 非空；audit.ok=true。
- 记录门禁事件链、ordinals、新 gem5 SHA-256。

验证：
```bash
python3 -m pytest tests/test_fsu_chain_check.py tests/test_fsu_seed_runner.py \
  tests/test_fsu_seed_audit.py -q
python3 tools/fsu_seed_runner.py --manifest configs/fsu/FSU-FP04-F3-W4-GATE.json \
  --seed 1 --out-root runs/fsu-gates/F3-multifault-gate
python3 tools/fsu_seed_audit.py <attempt>
```
提交：`[FSU][D2] F3 多故障门禁：逐 fault 链、审计与 run-level oracle 分离`
推送。

## 5. 任务 E：覆盖状态（1 commit）

`docs/gem5-fi/fsu/COVERAGE_STATUS.md`（矩阵 summary 同步）分别记录：
- seed_completion（当前 3/519）；
- frequency_coverage（F0 3/3 W4；F1/F2/F3 0/3，F3 仅门禁）；
- submodel_coverage（仅 FP04-c/mant_lo；sign/exp_hi/lo/mant_hi/mid/FP32/
  NEON 128-bit/FP04-d 未覆盖）；
- workload_coverage（W4 短版 + W4-rate-v1；W1/W3/W5/W6 未完成）；
- overall = NOT_COMPLETE。

## 6. 停止条件

完成 A–D（及覆盖文档 E）后停止，不启动正式 F1/F2/F3 三 seed。
下一次报告给出：新 HEAD、新 gem5 SHA-256、W4-rate-v1 SHA-256、三次 golden、
eligible_total、三档各 seed 的 ordinal 列表、F3 门禁事件链、全部测试结果、
真实 seed 总数。
