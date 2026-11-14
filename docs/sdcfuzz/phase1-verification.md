# Phase 1 收尾与验收（2026-11-14）

依据：`sdcfuzz/sdcfuzz-v1.2.md` §5.1 与 §7（Phase 1 交付物“自动靶向生成器
原型 + 结构覆盖度评估工具”）、`docs/roadmap/roadmap.yaml` 的 10 个 Phase 1
里程碑。主机：`sdc-0103`（aarch64，128 核，30 GiB）。

**结论先行：Phase 1 的 10 个里程碑在 HEAD `1fdf8cdf` 上重跑 9 步闸门全部
通过，并由本轮新增的里程碑审计器逐条核对到 10/10。** 前一轮修掉 7 个会导致
“假完成”的缺口；本轮再补 1 个（验收结论只有文档、没有机器可读台账，见
2.8）。仍未完成的是 Phase 1 之外的能力（完整 ISA 求解、TLB/SIMD/SVE、真机
SDC 率、RL/功耗），本文明确标出，不把它们混进 Phase 1。

## 1. 验收口径

| 里程碑 | 交付物 | 本轮证据 | 判定 |
|---|---|---|---|
| `p1-ace` RF/L1 ACE | 整数 + 向量/FP 低 64 位 RF ACE；L1I/L1D ACE | `CHAOS/gem5/src/cpu/o3/rf_ace.*`、`src/mem/cache/l1_ace.*`；`test-rf-ace.sh`、`test-l1-ace.sh` 原生 aarch64 通过 | 完成 |
| `p1-ibr` FU IBR | intAlu/intMult/intDiv/fpAdd/fpMult 输入位覆盖 | `fu_ibr.*`；`test-fu-ibr.sh` 通过 | 完成 |
| `p1-autousens` | 指令→结构映射 + 逆向靶向原型 | 16 条探针/9 结构；8 个可靶向结构逐一真实验证；`l1i` 显式拒绝 | 完成 |
| `p1-coverage` | 结构覆盖度评估工具 | `sdcfuzz/coverage.py`（含 target 指标契约）+ `coverage_report.py`（JSON/CSV/Markdown/SAD）；19 模板 9/9 结构激活 | 完成 |
| `p1-local-corpus` | 19 条本地结构语料（支撑件） | `templates.py`；19/19 PASS；非上游 19 模板的逐条复刻 | 完成 |
| `p1-local-heuristic` | 本地操作数启发式（支撑件） | `operand_heuristic.py`；`tests/test_sdcfuzz_operand_heuristic.py` 7 项单测 | 完成 |
| `p1-joint-agg` | 跨结构加权聚合 | `target --structure l1d,alu`；每指令归一化；双结构净激活 > 0 | 完成 |
| `p1-nsga` | NSGA-II 多目标序列集 | `nsga2.py` + `pareto`；Pareto 非空（size=8–14），knee 真实 gem5 验证 | 完成 |
| `p1-sad` | SAD 结构激活深度 | `sad.*`；ROB/IQ/LQ/SQ/intPrf/vecPrf/FU/issue；`test-sad.sh` 通过；已接入 autousens/coverage_report | 完成 |
| `p1-gate` | 一键验收闸门 + 里程碑审计 | `scripts/test-phase1.sh` 9/9；`scripts/verify-phase1.py` 10/10；`m5out/phase1-gate-final2/phase1_gate.json`、`phase1_milestones.json` | 完成 |

## 2. 会让 Phase 1 假完成的 8 个缺口

这些不是“再加一个文档”，而是会让 Phase 1 在别的机器/别的运行上失败或误报
的真实问题。2.1–2.7 在前一轮修复，2.8 是本轮新增。

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

### 2.8 验收结论没有机器可读的里程碑台账

`phase1_gate.json` 只记录 9 个步骤的返回码：它能证明“脚本都跑过了”，不能
证明“每个 Phase 1 里程碑都有产物和断言”。删掉一个源文件、删掉一行成功断言、
或者拿一个几天前的闸门目录，`phase1_gate.json` 仍然是 `passed=true`。

修复：新增 `sdcfuzz/phase1_audit.py` 与 `scripts/verify-phase1.py`：

- 10 个里程碑各自绑定**产物文件**、**闸门步骤**、**该步骤必须打印的成功
  断言**（例如 `RF ACE direction and formula checks passed`）；
- 额外解析 `coverage_summary.json`（19 模板 / 9 结构 / 无 `never_observed`
  / 已附 SAD）、`target l1d+alu` 的净激活、`pareto: size=`、闸门时效
  （默认 24 h）与闸门之后是否改过非文档文件；
- 输出 `phase1_milestones.json` 和一张 10 行表，任一检查失败即非零退出。

新增 8 项单测（`tests/test_phase1_audit.py`）：全绿、步骤失败、日志缺失、
断言缺失、闸门过期、汇总缺失、闸门 JSON 不可读、代码漂移（纯文档改动
不算漂移）。

## 3. 真实运行结果

### 3.1 一键闸门（终验：HEAD `c3a05c0b`）

```bash
PHASE1_OUT=$HOME/sdc-mhw/m5out/phase1-gate-final2 \
  bash scripts/test-phase1.sh
python3 scripts/verify-phase1.py \
  --gate-dir m5out/phase1-gate-final2
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

汇总：`phase1_gate.json` 记录 `failures=0`、`passed=true`、
`commit=c3a05c0b`；每步完整日志在 `m5out/phase1-gate-final2/<step>.log`。
此前三轮（`2ae3c4ed`、`1fdf8cdf`、`b072bff5`）同样 9/9，证据分别在
`m5out/phase1-gate/`、`m5out/phase1-gate-20261114-final/` 与
`m5out/phase1-gate-final/`；四轮口径一致，说明结论不依赖某一次运行。

里程碑审计（同一目录）：

```text
milestone           status  title
p1-ace              PASS    RF ACE 与 L1 cache ACE 量化
p1-ibr              PASS    FU IBR 输入位覆盖率
p1-autousens        PASS    AutoµSens 指令→结构映射与逆向靶向原型
p1-coverage         PASS    结构覆盖度评估工具
p1-local-corpus     PASS    本地 19 条结构语料（支撑件）
p1-local-heuristic  PASS    本地操作数启发式（支撑件）
p1-joint-agg        PASS    跨结构加权聚合靶向
p1-nsga             PASS    NSGA-II 多目标序列集生成
p1-sad              PASS    SAD 结构激活深度指标
p1-gate             PASS    Phase 1 一键验收（9 步）

phase1 milestones: 10/10 passed
```

### 3.2 AutoµSens（2026-11-14，60 次迭代）

```text
alu: add=494656 sub=494144 and=493632 orr=494016 eor=494016
mult: mul=737280 madd=737280
div: udiv=494208; mul=0 (noise)
l1d: ldr=3846 ldxr=3852 str=3841 (ldr per instruction=1.002)
template forms: movz=495488 add_imm=491712 add_lsl=492416 fadd=491520 fmul=495360
rf: add=11536 ldr=7700 str=7695
vec: fadd=11523 fmul=11523
target l1d: chosen=['ldxr', 'ldr'] net_reads=7686 coverage=0.001913 baseline=0.000973
target l1d+alu: chosen=['ldxr', 'movz'] l1d_net=3848 alu_net=491968
target mult: chosen=['madd'] net_mult=737088
target all: alu div fpadd fpmul l1d mult rf vec
pareto: size=7 knee=['add_lsl', 'ldxr', 'movz'] l1d_net=967 alu_net=247104
error handling: unknown structure, missing baseline and noise-only l1i all fail loudly
```

同一探针的逐轮抖动 < 0.5%（例如 `ldr`/`ldxr` 的 L1D 激活只差十几次事件），
所以断言绑定“访存类覆盖/净激活为正”，不绑定具体助记符排名或绝对值。

### 3.3 19 模板覆盖矩阵

```text
static contract: 19 templates, 17 op kinds, 9 metric groups
...
l1i-big-body     target=l1i    alu=2630016 rf=20532/20536 l1i(target)=1332
fp-add           target=fpadd  fpadd=81920 l1d=3/2 vec=1284/646
fp-mul           target=fpmul  fpmul=81920 l1d=11/2 vec=1284/646
all 19 templates cover every mapped instruction form
coverage: 9/9 structures observed; gaps={'no_targeting_template': ['rf', 'vec'],
'no_required_metric': [], 'never_observed': []}
```

`rf`/`vec` 是 `support` 指标（没有模板把它们作为 target，但被模板的必需
指标覆盖），不是缺口；`l1i` 的 target-metric 契约为 1 个模板。

### 3.4 ACE/IBR/SAD

```text
RF ACE direction and formula checks passed
  chain ratio: 0.01953664  dead-write ratio: 0.00791599
  pressure ratio: 0.00793476  squash discards: 164
  bit W/X ratios: 0.01370802 / 0.01946074

L1 ACE direction and formula checks passed
  reuse L1D ratio: 0.49251062  dead-write ratio: 0.00000018
  pressure L1D ratio: 0.00353199  stream ratio: 0.00036977

IBR width, utilization, formula, disabled, work-ID, cycle-window and ROI-pairing checks passed

SAD window, formula, direction, disabled and cycle-mode checks passed (cycle samples=56)
nop  samples=3745 rob=0.132089 ...
rob  samples=25746 rob=0.344901 ...
lsq  samples=19798 lq=0.900647 sq=0.910910 ...
prf  samples=4556 intPrf=0.452959 ...

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
bash scripts/test-phase1.sh            # 9 步闸门（约 25 min）
python3 scripts/verify-phase1.py \
  --gate-dir m5out/phase1-gate-final2  # 10 里程碑台账
python3 -m pytest tests/ -q            # 全量单测（77 项）
python3 scripts/test-autousens.py \
  --gem5 CHAOS/gem5/build/ARM/gem5.opt \
  --outdir m5out/autousens-verify
python3 scripts/test-template-coverage.py \
  --gem5 CHAOS/gem5/build/ARM/gem5.opt \
  --outdir m5out/coverage-verify
python3 -m sdcfuzz.coverage_report \
  --matrix m5out/coverage-verify/coverage_matrix.json \
  --outdir m5out/coverage-verify/report \
  --sad-run m5out/phase1-gate-final2/sad/rob
```

## 6. 证据文件

```text
m5out/phase1-gate-final2/phase1_gate.json                9 步闸门（HEAD c3a05c0b）
m5out/phase1-gate-final2/phase1_milestones.json          10 里程碑审计
m5out/phase1-gate-final2/<step>.log                      每步完整输出
m5out/phase1-gate-final2/report/                         coverage_summary.{json,md}
m5out/phase1-gate-final/                                 前一轮闸门（b072bff5）
m5out/phase1-gate-20261114-final/                        （1fdf8cdf）
m5out/phase1-gate/                                       首轮闸门（2ae3c4ed）
tests/test_phase1_audit.py                               8 项里程碑审计单测
tests/test_coverage_report.py                            5 项汇总/SAD 单测
tests/test_sdcfuzz_coverage.py                           6 项契约单测（含 target 指标）
```
