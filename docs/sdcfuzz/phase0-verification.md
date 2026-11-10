# Phase 0 逐项核查与原生 aarch64 实测记录

日期：2026-11-10
对象：`sdcfuzz/sdcfuzz-v1.2.md` §7 Phase 0（M0）与
`docs/roadmap/roadmap.yaml` 的 5 个里程碑。
主机：`sdc-0103`，aarch64，128 核，30 GB 内存。
结论先行：**5 项交付物均存在；本仓库可执行的部分已在本机真实复跑通过；
外部证据项已核验文件/哈希/论文页面，但未在本机重跑。核查发现一处文档口径
滞后：上游实际是 20 个模板 / 8 个模块，不是方案写的 19 个 / 7 个。**

## 1. 为什么先重建 gem5

预置的 `CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt` 是 **x86-64 ELF**，
在 `sdc-0103` 的 aarch64 用户态无法执行。实际错误：

```text
OSError: [Errno 8] Exec format error:
'/home/sdc/sdc-mhw/CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt'
```

`build/ARM/gem5.opt` 是原生 aarch64，但构建于 2026-09-08，早于 ACE/IBR 代码，
字符串中不含 `rfAce`。因此本次用当前源码重建原生 aarch64 构建：

```bash
source ~/gem5-deps/env.sh
cd CHAOS/gem5
scons build/ARM/gem5.opt -j48 \
  ISA_CONSTR_CCFLAGS=-g0 ISA_EXEC_CCFLAGS=-g0 \
  --debug-fission --limit-ld-memory-usage
```

结果：`build/ARM/gem5.opt` 为 ARM aarch64 ELF，编译零错误；只出现宿主依赖
警告（tcmalloc/png/capstone 未安装），与本次改动无关。交叉编译器为
`aarch64-openEuler-linux-gcc`（脚本默认的 `aarch64-linux-gnu-gcc` 在本机不存在）。

## 2. 逐项核查

| # | 里程碑 | 台账状态 | 本次核查 | 判定 |
|---|---|---|---|---|
| 1 | D13 操作数启发式（上游） | `done-external` | 核验上游文件 sha256；**原样同步到 `sdcfuzz/upstream/d13/`**；本地 golden、确定性、gem5 与 FI 冒烟实测 | 代码/算法完整；完整 4×100 实验仍为外部记录 |
| 2 | 19 个微架构模板（上游） | `done-external` | 上游 `seeds/*.S` 实际 **20** 个、**8** 个模块；上游合规评估已指出“19/7”过时 | 交付物存在，方案数字需更正 |
| 3 | gem5-CHAOS 底座 + 生成→注入闭环 | `done-local` | 重建原生 gem5；19/19 模板 PASS；CHAOSReg 注入 1 次并分类 | **本机实测通过** |
| 4 | 4 板 446 核 Kunpeng 920 部署 | `done-external` | 核验上游论文 §6.4 表格（4 板 446 核） | 外部证据；本机不重跑 |
| 5 | sdcfuzz 论文 p2 草稿 | `done-external` | 核验上游 `docs/paper/paper2_{en,zh}.md`（57 KB / 50 KB） | 外部证据；存在 |

### 2.1 D13（上游实现已同步并本地实测）

在 `sdc-0103` 的 `/home/sdc/wangxu/silifuzz`（HEAD `707db35d`）：

```text
sha256 4143a4bdee3244452ce2747e590d6cbfbbb45117b23a3027d04a0eacc0067263
       gem5_config/workloads/sdc_probe_workload_d13.c
```

与 `docs/sdcfuzz/d13-baseline-reproduction.md` 记录的哈希一致。上游源码已
**原样同步**到本仓库 `sdcfuzz/upstream/d13/`（D13 + 随机基线 B + Apache-2.0
LICENSE，逐字节副本）。完整性核查见
`docs/sdcfuzz/d13-upstream-verification.md`；本地实测：

```text
$ bash scripts/test-d13-upstream.sh
sha256 ok: sdc_probe_workload_d13.c / sdc_probe_workload_random.c / LICENSE
D13 native: SUM=118831515424667458 CRC=dbc8bf2a
D13 native 第二次: 相同（确定性）
B native:   SUM=10721424292087689827 CRC=6728fc4a
gem5 O3:    SUM=118831515424667458 CRC=dbc8bf2a
FI smoke:   integer[29] bit_flip Mask=0x800, numFaultsInjected=1
```

复现产物 `docs/sdcfuzz/d13-repro/summary.json` 的真实数值：

| 模式 | B（随机） | D13 | D13/B | Fisher p | 判定 |
|---|---|---|---:|---:|---|
| bit-flip | 6/100 | 17/100 | 2.833× | 0.0249 | BEAT |
| structural | 5/100 | 64/100 | 12.800× | 5.63e-20 | BEAT |

**未在本轮重跑** 4×100 次上游 `sim_sweep.py`；本轮完成的是源码完整性核查、
原样同步、golden 复现、gem5 运行和单次 FI 冒烟。不把“读过文件”或“单次
FI 冒烟”说成“重新跑过 400 次实验”。

### 2.2 模板数量（发现的文档偏差）

上游 `seeds/*.S` 实际文件：

```text
c1_l2_eviction.S        c3_l3_128b.S          e1_carry_chain.S
e2_mul_extreme.S        e3_toggle_rate.S      f1_subnormal_nan.S
i1_icache_boundary.S    i2_branch_dense.S     l1_disambig.S
l2_dualagu_split.S      m1_tlb_thrash.S       m3_cross_page.S
o1_rob_full_wakeup.S    o2_mispredict_rollback.S
v1_fsu_vdroop.S         v2_alu_complex_saturation.S
v3_prf_mispredict.S     v4_lsu_cross_boundary.S
v5_lse_cross_die.S      v6_crypto_toggle.S
```

共 20 个。上游自己的
`docs/experiments/2026-09-03-scheme-compliance-assessment.md` 第 32 行明确写：

> `seeds/bin/` 实际 **20 个** `.bin`（对应 20 个 `.S`），覆盖 **8** 个弱点模块
> （E/V/M/C/O/I/L/F），scheme 写“19 个/7 个”已过时

因此 Phase 0 的交付物不是缺失，而是**路线图/论文沿用了过时数字**。本次已把
`roadmap.yaml` 的 `p0-templates` 标题与证据改成“方案写 19，实测 20”，并保留
`done-external`（本仓库无副本，未逐条复验）。

### 2.3 4 板部署（外部证据）

上游 `docs/paper/paper2_en.md` §6.4 的 Table IV：

| Board | Cores | genuine SDC (2/3/4) | runaway (5) | misbehave (6) |
|---|---:|---:|---:|---:|
| 0101 | 126 | 0 | 0 | 439 |
| 0102 | 192 | 0 | 0 | 83 |
| 0103 | 128 | 0 | 0 | 27 |
| 0201 | 96 | 0 | 10 | 621 |
| **Total** | **446** | **0** | **10** | **1170** |

这是上游论文记录的历史证据。本会话只连接了 `sdc-0103` 一台主机，无法重跑
四板分布式扫描；台账继续标 `done-external`，不冒充本机复验。

### 2.4 p2 草稿（外部证据）

上游 `docs/paper/paper2_en.md` 57088 字节、`paper2_zh.md` 49964 字节，存在且
包含摘要、方法、实验与数据可用性章节。属于外部仓库资产，本仓库无副本。

## 3. 本仓库实测（真实命令与输出）

### 3.1 单元测试

```text
$ python3 -m pytest tests/ -q
59 passed in 4.52s
```

### 3.2 19 模板 ACE/IBR 覆盖矩阵

```bash
ARM_CC=aarch64-openEuler-linux-gcc \
python3 scripts/test-template-coverage.py \
  --gem5 CHAOS/gem5/build/ARM/gem5.opt \
  --outdir m5out/coverage-matrix
```

真实输出（节选，单位为各结构自身计数器）：

```text
static contract: 19 templates, 17 op kinds, 9 metric groups
alu-add-carry    target=alu    alu=89728 rf=1338/703
mul64            target=mult   alu=8704 mult=123264 rf=1335/700
div64            target=div    alu=11264 div=81920 rf=1334/699
l1d-load-stream  target=l1d    alu=8320 l1d=3846/2 rf=3892/3896
l1i-big-body     target=l1i    alu=2629632 rf=20532/20536
branch-busy      target=alu    alu=1444352 rf=10292/10936
fp-add           target=fpadd  fpadd=81920 l1d=3/2 vec=1284/646
fp-mul           target=fpmul  fpmul=81920 l1d=11/2 vec=1284/646
fp-add: vec accesses=1930 fpadd input bits=81920
fp-mul: vec accesses=1930 fpmul input bits=81920
all 19 templates cover every mapped instruction form
matrix: m5out/coverage-matrix/coverage_matrix.json
```

这证明 19 个模板涉及的 17 类 Op 形态（含 FP 的 `fadd`/`fmul`）都有非零的
ACE/IBR 计数器；逐模板的必需指标与实测值在 `coverage_matrix.json` 中。

### 3.3 Phase 0 基线 + 故障注入闭环

```bash
ARM_CC=aarch64-openEuler-linux-gcc \
python3 scripts/test-sdcfuzz-baseline.py \
  --gem5 CHAOS/gem5/build/ARM/gem5.opt \
  --outdir m5out/phase0-verify
```

真实输出末尾：

```text
fp-add           target=fpadd activation=81920.0 ... fpadd=0.1059
fp-mul           target=fpmul activation=81920.0 ... fpmul=0.1147
reproducibility: mul64 activation stable at 123264
local heuristic: operand=0xff1b36114f09638f carry_chain=16 alu_bits=89728
fi smoke: chaos_reg faults=1 -> Masked (completed exit=0, checksum==golden ...)
phase-0 baseline: 19/19 templates PASS, FI loop Masked
```

`Masked` 是 CHAOSReg 架构状态注入在 O3 上的已知结果（在途循环使用重命名后的
物理寄存器），脚本按真实分类报告，不伪造成 SDC。

### 3.4 ACE/IBR 既有回归

```text
$ bash scripts/test-fu-ibr.sh
alu64: intAlu IBR=0.65390920, bits=8322496, cycles=16572
...
IBR width, utilization, formula, disabled, work-ID, cycle-window and
ROI-pairing checks passed

$ bash scripts/test-rf-ace.sh
RF ACE direction and formula checks passed
  chain ratio: 0.01952017  dead-write ratio: 0.00791228
  pressure ratio: 0.00793267  squash discards: 146
  bit W/X ratios: 0.01370757 / 0.01946104

$ bash scripts/test-l1-ace.sh
L1 ACE direction and formula checks passed
  reuse L1D ratio: 0.49370497  dead-write ratio: 0.00000032
  pressure ratio: 0.00353185  stream ratio: 0.00036905

$ python3 scripts/test-ace-ibr-correctness.py \
    --gem5 CHAOS/gem5/build/ARM/gem5.opt
ldr: demand reads=4099 ... cassame: demand reads=4098
IBR: 74 in-window ALU issues; 1 end-cycle issues excluded
Atomic access, mixed-width and ROI snapshot checks passed
```

说明：`test-rf-ace.sh` / `test-l1-ace.sh` 原先硬性要求 gem5 宿主编译产物是
x86-64；在原生 aarch64 宿主上这是错误假设。本次改为接受 `x86-64` 或
`ARM aarch64`，两个脚本随后在 `sdc-0103` 原生构建上通过。

### 3.5 Phase 1 新工具的真实回归

```text
$ python3 scripts/test-autousens.py --gem5 .../gem5.opt
alu: add=493760 sub=494272 and=493632 orr=494016 eor=494016
template forms: movz=495936 add_imm=493632 add_lsl=491584 fadd=491520 fmul=495488
vec: fadd=11523 fmul=11523
target l1d: chosen=['ldr', 'ldxr'] net_reads=7686
target l1d+alu: chosen=['ldr', 'movz'] l1d_net=3844 alu_net=491584
target mult: chosen=['madd'] net_mult=737088
pareto: size=12 knee=['str', 'movz', 'str'] l1d_net=1920 alu_net=123328
error handling: unknown structure and missing baseline both fail

$ bash scripts/test-sad.sh
nop  samples=3745 rob=0.132089 ...
rob  samples=25746 rob=0.344908 ...
lsq  samples=19785 lq=0.907308 sq=0.917482 ...
prf  samples=4557 intPrf=0.452601 ...
SAD window, formula, direction, disabled and cycle-mode checks passed
(cycle samples=70)
```

## 4. 结论与边界

1. **Phase 0 的 5 项交付物均存在**：D13、上游模板、gem5-CHAOS、四板部署、
   p2 草稿。本仓库能执行的部分（gem5-CHAOS + 19 模板 + 生成→注入闭环）
   在原生 aarch64 构建上真实通过。
2. **D13 已原样同步并做本地实测，但完整 4×100 实验没有重跑**：上游
   `sdcfuzz/upstream/d13/` 源码 sha256 与 `707db35d` 一致；本地完成 golden、
   确定性、gem5 基线与单次 FI 冒烟。四板 446 核扫描与 p2 草稿只核验了
   上游文件/论文表格。台账对完整实验继续用 `done-external`，不把单次冒烟
   冒充 400 次实验。
3. **发现并更正一处文档偏差**：上游实际 20 个模板 / 8 个模块，方案与论文
   仍写 19/7。已更新 `roadmap.yaml` 的 `p0-templates` 证据；本仓库的 19 条
   本地语料是支撑件，不是上游模板的逐条复刻，两者不能混为一谈。
4. **测试脚本可移植性修复**：两个 ACE 脚本原先假定 gem5 宿主产物必为
   x86-64，已改为同时接受原生 aarch64；这是本次在 `sdc-0103` 上实测暴露的
   真实问题，不是预先设计的改动。
