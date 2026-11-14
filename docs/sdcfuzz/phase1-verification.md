# Phase 1 收尾与验收（2026-11-14）

依据：`sdcfuzz/sdcfuzz-v1.2.md` §5.1 与 §7（Phase 1 交付物“自动靶向生成器
原型 + 结构覆盖度评估工具”）、`docs/roadmap/roadmap.yaml` 的 10 个 Phase 1
里程碑。主机：`sdc-0103`（aarch64，128 核，30 GiB）。

**结论先行：Phase 1 的 10 个里程碑全部有本仓库实测证据；本轮修掉 7 个会导致
“假完成”的缺口，新增 1 个 9 步一键验收闸门。** 仍未完成的是 Phase 1 之外的
能力（完整 ISA 求解、TLB/SIMD/SVE、真机 SDC 率、RL/功耗），本文明确标出，
不把它们混进 Phase 1。

## 1. 验收口径

| 里程碑 | 交付物 | 本轮证据 | 判定 |
|---|---|---|---|
| `p1-ace` RF/L1 ACE | 整数 + 向量/FP 低 64 位 RF ACE；L1I/L1D ACE | `CHAOS/gem5/src/cpu/o3/rf_ace.*`、`src/mem/cache/l1_ace.*`；`test-rf-ace.sh`、`test-l1-ace.sh` 原生 aarch64 通过 | 完成 |
| `p1-ibr` FU IBR | intAlu/intMult/intDiv/fpAdd/fpMult 输入位覆盖 | `fu_ibr.*`；`test-fu-ibr.sh` 通过 | 完成 |
| `p1-autousens` | 指令→结构映射 + 逆向靶向原型 | 16 条探针/9 结构；8 个可靶向结构逐一真实验证；`l1i` 显式拒绝 | 完成 |
| `p1-coverage` | 结构覆盖度评估工具 | `sdcfuzz/coverage.py`（含 target 指标契约）+ `coverage_report.py`（JSON/CSV/Markdown/SAD）；19 模板 9/9 结构激活 | 完成 |
| `p1-local-corpus` | 19 条本地结构语料（支撑件） | `templates.py`；19/19 PASS；非上游 19 模板的逐条复刻 | 完成 |
| `p1-local-heuristic` | 本地操作数启发式（支撑件） | `operand_heuristic.py`；15 项单测 | 完成 |
| `p1-joint-agg` | 跨结构加权聚合 | `target --structure l1d,alu`；每指令归一化；双结构净激活 > 0 | 完成 |
| `p1-nsga` | NSGA-II 多目标序列集 | `nsga2.py` + `pareto`；Pareto 非空（size=8–14），knee 真实 gem5 验证 | 完成 |
| `p1-sad` | SAD 结构激活深度 | `sad.*`；ROB/IQ/LQ/SQ/intPrf/vecPrf/FU/issue；`test-sad.sh` 通过；已接入 autousens/coverage_report | 完成 |
| `p1-gate` | 一键验收闸门 | `scripts/test-phase1.sh`；`m5out/phase1-gate/phase1_gate.json` | 完成 |

## 2. 本轮修掉的 7 个缺口

这些不是“再加一个文档”，而是会让 Phase 1 在别的机器/别的运行上失败或误报
的真实问题：

### 2.1 默认 gem5 路径指向 x86-64 二进制

`tools/autousens.py`、`sdcfuzz/evaluate.py`、`scripts/test-autousens.py` 的
默认值都是 `CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt`。该文件是 x86-64
ELF，在 `sdc-0103` 上直接：

```text
OSError: [Errno 8] Exec format error
```

修复：新增 `sdcfuzz/paths.py`，按 `GEM5_OPT` → `build/ARM/gem5.opt` →
`build/ARM_ACE_IBR_AUDIT/gem5.opt` 解析；所有 Python 工具和测试共用。
`test-rf/l1/fu` 的默认构建目录也从 `ARM_X86_HOST` 改为按 `uname -m` 选择
（aarch64 → `ARM`）。

### 2.2 ACE/IBR 回归脚本硬依赖 conda

`test-rf-ace.sh`、`test-l1-ace.sh`、`test-fu-ibr.sh` 在没有 `CONDA_PREFIX`
时 `source init-env.sh`，而本机没有 conda：

```text
ERROR: conda was not found. Initialize conda first, or edit init-env.sh.
RF_EXIT=1 / L1_EXIT=1 / IBR_EXIT=1
```

修复：优先找 conda；没有 conda 时 source `~/gem5-deps/env.sh`（本机真实的
gem5 构建环境）；两者都没有但 gem5 已存在时给出警告并复用二进制。三个脚本
随后全部通过（见第 3 节）。

### 2.3 `target l1d` 回归断言依赖 `ldr` 排名

`scripts/test-autousens.py` 原来断言 `"ldr" in chosen`。实测 `ldr` 与
`ldxr` 的 L1D 激活只差几个事件（3846 vs 3852），谁排第一取决于当次运行；
本轮第一次重跑就失败：

```text
AssertionError: ['ldxr', 'movz']
```

修复：断言改为“选中任一 load 类探针（`ldr`/`ldxr`）”，并检查对应汇编行。
这不是放宽标准，而是把断言从“某个助记符”改成“访存类覆盖”。

### 2.4 `l1i` 把 cache-line 噪声当成可靶向信号

`l1i` 只有 cache-line 级需求读；16 条短探针的循环体都在一行内，逐指令净
激活只有 0–112 事件（每指令 0.029），旧版 `target --structure l1i` 会选
`udiv` 并生成一个“靶向 l1i”的候选，实际没有可归因的 L1I 激活。

修复：`structure_map.json` 新增 `targetability`；每个结构有每指令下限
（`rf/vec` 0.25、`l1d` 0.50、五类 FU 32 输入位、`l1i` 0.10）。低于下限时
`target`/`pareto` 直接失败：

```text
structure 'l1i' is measured but not per-instruction targetable:
best probe udiv reaches 0.029 per instruction, below the floor 0.1.
This structure is line- or aggregate-granular; use the coverage matrix
instead of reverse targeting.
```

`l1i` 仍由模板矩阵测量（`l1i-big-body` 约 1.3k 需求读），不是“放弃覆盖”。

### 2.5 模板只检查 op 指标，不检查 target 指标

`l1i-big-body` 的 body 是 ALU 指令，`template_metrics()` 只要求 `rf/alu`；
即使 `l1i` 计数器为 0，旧测试也会通过。修复：`coverage.py` 新增
`TARGET_METRICS` 与 `template_target_metric()`，`coverage_failures()` 对
模板声明的 target 指标单独断言；`test-template-coverage.py` 打印
`l1i(target)=1339`。新增 3 项单测（`tests/test_sdcfuzz_coverage.py`）。

### 2.6 覆盖评估只有逐次 `evaluate`，没有汇总与 SAD

Phase 1 要求“结构覆盖度评估工具”，旧实现只有 `autousens evaluate` 单目录
重算和模板脚本的控制台输出；没有跨模板汇总，也没有把 SAD 纳入同一份报告。

修复：新增 `sdcfuzz/coverage_report.py`：

- 输入 `coverage_matrix.json`，输出 `coverage_summary.json`、
  `coverage_matrix.csv`、`coverage_summary.md`；
- 用**计数器下限**判断真实激活，避免“每个模板都有 8 次 vec 写”被算成覆盖；
- 状态区分 `targeted` / `support` / `incidental` / `unobserved`；
- 可选 `--sad-run` 解析 `.sad.ratio::*`，把 ROB/IQ/LQ/SQ/PRF/FU/issue
  占用表附在同一份报告里；
- 新增 5 项单测（`tests/test_coverage_report.py`）。

### 2.7 correctness 脚本硬编码 x86 风格的 objdump/编译器

`test-ace-ibr-correctness.py` 原来固定调用 `aarch64-linux-gnu-objdump` 与
`aarch64-linux-gnu-gcc`；本机只有 `aarch64-openEuler-linux-gcc`，objdump 在
`~/gem5-deps/py/usr/bin/` 下。闸门第一次运行因此失败：

```text
FileNotFoundError: [Errno 2] No such file or directory:
'aarch64-linux-gnu-objdump'
```

修复：编译器复用 `sdcfuzz.paths.default_cc()`；objdump 按
`aarch64-openEuler-linux-objdump` → `aarch64-linux-gnu-objdump` →
`~/gem5-deps/{usr,py/usr}/bin/aarch64-linux-gnu-objdump` 探测，并支持
`ARM_OBJDUMP` 覆盖。修复后不加任何环境变量也能通过。

## 3. 真实运行结果

### 3.1 一键闸门

```bash
bash scripts/test-phase1.sh
```

| 步骤 | 命令 | 结果 |
|---|---|---|
| pytest | 5 个 Phase 1 单测文件 | **34 passed**，rc=0 |
| autousens | 结构映射 + 8 结构靶向 + Pareto knee | 通过，rc=0 |
| templates | 19 模板 ACE/IBR 矩阵 + 汇总 | 19/19，9/9 结构，rc=0 |
| sad | ROB/IQ/LQ/SQ/PRF/FU/issue | 公式/方向/窗口/关闭通过，rc=0 |
| rf-ace | RF ACE 方向/公式/粒度 | 通过，rc=0 |
| l1-ace | L1 ACE 方向/公式/窗口 | 通过，rc=0 |
| fu-ibr | 5 类 FU IBR | 通过，rc=0 |
| correctness | 原子访问、混合宽度、ROI 快照 | 通过，rc=0 |
| coverage-report | 汇总 + SAD 表 | 通过，rc=0 |

汇总文件：`m5out/phase1-gate/phase1_gate.json`；每步日志：
`m5out/phase1-gate/<step>.log`。

### 3.2 AutoµSens（2026-11-14，60 次迭代）

```text
alu: add=493632 sub=493888 and=493504 orr=494272 eor=494016
mult: mul=737280 madd=737280
div: udiv=494080; mul=0 (noise)
l1d: ldr=3846 ldxr=3852 str=3842 (ldr per instruction=1.002)
template forms: movz=497408 add_imm=493120 add_lsl=491072 fadd=491520 fmul=495360
rf: add=11536 ldr=7700 str=7695
vec: fadd=11523 fmul=11523
target l1d: chosen=['ldxr', 'ldr'] net_reads=7681
target l1d+alu: chosen=['ldxr', 'movz'] l1d_net=3844 alu_net=491584
target mult: chosen=['madd'] net_mult=737088
target all: alu div fpadd fpmul l1d mult rf vec
pareto: size=8 knee=['add','ldxr','movz'] l1d_net=967 alu_net=246464
（另一轮 size=14 knee=['str','str','movz'] l1d_net=1920 alu_net=122688）
error handling: unknown structure, missing baseline and noise-only l1i all fail loudly
```

### 3.3 19 模板覆盖矩阵

```text
static contract: 19 templates, 17 op kinds, 9 metric groups
...
l1i-big-body     target=l1i    alu=2632192 rf=20532/20536 l1i(target)=1339
fp-add           target=fpadd  fpadd=81920 l1d=5/2 vec=1284/646
fp-mul           target=fpmul  fpmul=81920 l1d=19/2 vec=1284/646
all 19 templates cover every mapped instruction form
coverage: 9/9 structures observed; gaps={'no_targeting_template': ['rf', 'vec'],
'no_required_metric': [], 'never_observed': []}
```

`rf`/`vec` 是 `support` 指标（没有模板把它们作为 target，但被模板的必需
指标覆盖），不是缺口；`l1i` 的 target-metric 契约为 1 个模板。

### 3.4 ACE/IBR/SAD

```text
RF ACE direction and formula checks passed
  chain ratio: 0.01951995  dead-write ratio: 0.00791228
  pressure ratio: 0.00793165  squash discards: 160
  bit W/X ratios: 0.01370629 / 0.01945946

L1 ACE direction and formula checks passed
  reuse L1D ratio: 0.49329616  dead-write ratio: 0.00000030
  pressure L1D ratio: 0.00338586  stream ratio: 0.00037127

IBR width, utilization, formula, disabled, work-ID, cycle-window and ROI-pairing checks passed

SAD window, formula, direction, disabled and cycle-mode checks passed (cycle samples=70)
nop  samples=3745 rob=0.132089 ...
rob  samples=25746 rob=0.344908 ...
lsq  samples=19785 lq=0.907308 sq=0.917482 ...
prf  samples=4557 intPrf=0.452601 ...

Atomic access, mixed-width and ROI snapshot checks passed
IBR: 74 in-window ALU issues; 1 end-cycle issues excluded
```

## 4. 仍未完成 / 边界（不属于 Phase 1）

1. **完整 ISA 合法性求解**：`target`/`pareto` 只在 16 条已验证的指令片段
   空间里组合，不做任意 ARM64 指令的约束求解；设计文档里的 Microprobe 式
   “任意指令序列”仍是原型级。
2. **结构覆盖范围**：9 类结构，缺 TLB、SIMD/SVE、ROB/IQ/LSQ 的逐指令归因
   （SAD 只给 ROI 占用比例）。
3. **真机 SDC 率**：Phase 1 只做生成与结构覆盖；gem5 注入闭环在 Phase 3，
   真机 4 板 446 核是外部证据，本机未复验。
4. **RL/功耗**：Phase 2，未开始。
5. **`l1i` 不可逐指令靶向**：见 2.4；这是测量粒度限制，不是实现遗漏。

## 5. 复现命令

```bash
cd ~/sdc-mhw
source ~/gem5-deps/env.sh              # 可选；脚本会自动探测
bash scripts/test-phase1.sh            # 9 步闸门
python3 -m pytest tests/ -q            # 全量单测（69 项）
python3 scripts/test-autousens.py \
  --gem5 CHAOS/gem5/build/ARM/gem5.opt \
  --outdir m5out/autousens-verify
python3 scripts/test-template-coverage.py \
  --gem5 CHAOS/gem5/build/ARM/gem5.opt \
  --outdir m5out/coverage-verify
python3 -m sdcfuzz.coverage_report \
  --matrix m5out/coverage-verify/coverage_matrix.json \
  --outdir m5out/coverage-verify/report \
  --sad-run m5out/sad-test/rob
```

## 6. 证据文件

```text
m5out/phase1-gate/phase1_gate.json          9 步闸门汇总
m5out/phase1-gate/<step>.log                每步完整输出
m5out/phase1-verify-20261114/v2/autousens.log
m5out/phase1-verify-20261114/v2/coverage2/coverage_matrix.json
m5out/phase1-verify-20261114/v2/coverage2/coverage_summary.md
m5out/phase1-verify-20261114/v2/rf-ace.log
m5out/phase1-verify-20261114/v2/l1-fu.log
tests/test_coverage_report.py               5 项汇总/SAD 单测
tests/test_sdcfuzz_coverage.py              6 项契约单测（含 target 指标）
```
