# 上游 D13 实现完整性核查与本地同步

日期：2026-11-10
目的：严格按 `sdcfuzz/sdcfuzz-v1.2.md` 与
`docs/sdcfuzz/d13-baseline-reproduction.md` 的 D13 口径，核查上游实现是否
完整，并把上游代码原样同步到本仓库。**本仓库的
`sdcfuzz/operand_heuristic.py` 不是 D13**，只是本地对照启发式，本文不再把
两者混用。

## 1. 来源与同步内容

| 项 | 值 |
|---|---|
| 上游仓库 | `git@github.com:wangxumarshall/sdcfuzz.git` |
| 上游提交 | `707db35da507bbe7c086ee3760ea3b3260aaf930` |
| D13 源路径 | `gem5_config/workloads/sdc_probe_workload_d13.c` |
| 随机基线 B 源路径 | `gem5_config/workloads/sdc_probe_workload_random.c` |
| 上游重复副本 | `seeds/gem5/sdc_probe_workload_d13.c`，与 D13 源文件 sha256 相同 |
| 本地同步目录 | `sdcfuzz/upstream/d13/` |
| 许可证 | Apache License 2.0（`sdcfuzz/upstream/d13/LICENSE`） |

同步时实测 sha256：

```text
4143a4bdee3244452ce2747e590d6cbfbbb45117b23a3027d04a0eacc0067263  sdc_probe_workload_d13.c
fb461f72675c194b5a93aeeeab55f73f6fba5ad6cf4830146bc935d1c169c1be  sdc_probe_workload_random.c
cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30  LICENSE
```

同步方式是 `cp` 原文件，未修改任何字节；`scripts/test-d13-upstream.sh` 每次
运行都会重新校验这三个哈希，防止后续被误改。

## 2. 文档语义 vs 代码逐项核查

文档描述的 D13（`sdcfuzz-v1.2.md` §3.3 / §5.2、
`d13-baseline-reproduction.md` §1）与代码对应关系：

| 文档语义 | 代码证据（`sdcfuzz/upstream/d13/sdc_probe_workload_d13.c`） | 判定 |
|---|---|---|
| 每次生成两个随机 64 位候选 A、B | `pick_high_toggle(rng_u64(), rng_u64())`；`rng_u64()` 用固定种子 LCG 拼两个 32 位 | 完整 |
| 对 A 施加定向变异：异或随机 mask | `targeted_mutate()`：`a ^ mask` | 完整 |
| `+1` | `a_mut += 1` | 完整 |
| 循环左移 | `a_mut = (a_mut << 1) \| (a_mut >> 63)` | 完整 |
| 再与 `~A` 异或（差异放大） | `a_mut ^= ~a` | 完整 |
| 用 `popcount(x ^ (x + 1))` 作为进位链代理比较 | `a_eval = a_mut ^ (a_mut + 1)`；`b_eval = b ^ (b + 1)`；`popcount64` | 完整 |
| 保留变异值或随机 B 中较大者 | `if (popcount64(a_eval) >= popcount64(b_eval)) return a_mut; else return b;` | 完整 |
| 同时保留若干纯随机操作数，维持覆盖广度 | `carry_chain()` 中 `x5..x8` 为 `rng_u64()`；`toggle_rate()`/`lsu_cross()` 也保留纯随机项 | 完整 |
| 每次迭代重新选择 | `main()` 每轮调用 `carry_chain/toggle_rate/lsu_cross`，内部重新抽随机值 | 完整 |
| workload 输出/可判定 | `ITERS=200`；输出 `SUM=... CRC=...` | 完整 |

### 2.1 结论：D13 算法本身是完整的

上游文件不是“半成品”：随机候选、定向变异、`popcount(x^(x+1))` 选择、
纯随机保留、200 轮 workload 都在同一文件内，且能独立编译、自洽输出 golden。
`ITERS=200`、固定 RNG 种子、无命令行参数是**上游 workload 的设计选择**，
不是 D13 逻辑缺失；实验编排（故障钟采样、bit/struct 模式、100 次重复）在
上游 `sim_sweep.py`/`two_level_taishan.py` 中，不在这个 `.c` 文件里。

### 2.2 边界：实验编排没有全部同步

本地只同步 D13 算法 workload 和 B 随机基线。上游完整的
`tools/sdc_experiment/sim_sweep.py`、`gem5_config/configs/two_level_taishan.py`
等实验编排仍是外部资产；本仓库的 `scripts/test-d13-upstream.sh` 用本仓库
原生 gem5 config 做 golden/FI 冒烟，不声称复刻 4×100 次实验。

## 3. 本地实跑结果

### 3.1 原生 aarch64

```text
$ aarch64-openEuler-linux-gcc -static -O2 -o ... sdc_probe_workload_d13.c
$ ./sdc_probe_workload_d13
SUM=118831515424667458 CRC=dbc8bf2a
$ ./sdc_probe_workload_d13        # 第二次，确定性
SUM=118831515424667458 CRC=dbc8bf2a

$ ./sdc_probe_workload_random
SUM=10721424292087689827 CRC=6728fc4a

$ sha256sum ...
4143a4bd...  sdc_probe_workload_d13.c
fb461f72...  sdc_probe_workload_random.c
cfc7749b...  LICENSE
```

D13 的 golden 与上游 `tools/sdc_experiment/gem5_env.py` 记录的
`SUM=118831515424667458 CRC=dbc8bf2a` 完全一致；B 的 golden 与
`gem5_env.py` 的 `SUM=10721424292087689827 CRC=6728fc4a` 一致。

### 3.2 gem5 O3 基线

```bash
CHAOS/gem5/build/ARM/gem5.opt --outdir=m5out/d13-upstream/gem5-baseline \
  configs/se/arm_chaos.py --cpu=O3 \
  --cmd=m5out/d13-upstream/bin/sdc_probe_workload_d13
```

真实输出包含：

```text
SUM=118831515424667458 CRC=dbc8bf2a
```

另外用上游 `gem5_config/configs/two_level_taishan.py --mode baseline`
在同一原生 gem5 上也复现了同一 golden：

```bash
# 在上游 /home/sdc/wangxu/silifuzz 下，用本仓库原生 gem5
/home/sdc/sdc-mhw/CHAOS/gem5/build/ARM/gem5.opt \
  --outdir=/tmp/d13-gem5-baseline \
  gem5_config/configs/two_level_taishan.py \
  --binary gem5_config/workloads/sdc_probe_workload_d13 \
  --mode baseline
# SUM=118831515424667458 CRC=dbc8bf2a
```

这说明同步的 workload 与上游 TaiShan 配置/预编译 golden 一致，不只是“能在
本仓库 config 下跑”。

### 3.3 CHAOSReg 单次注入冒烟

```bash
CHAOS/gem5/build/ARM/gem5.opt --outdir=m5out/d13-upstream/gem5-fi \
  configs/se/arm_chaos.py --cpu=O3 \
  --cmd=m5out/d13-upstream/bin/sdc_probe_workload_d13 \
  --chaos_reg --probability=1.0 --max_faults=1 \
  --first_clock=1000 --rng_seed=42
```

真实结果：

```text
Cycle: 1000, CPU: board.processor.cores.core, Thread: 0,
Register: integer[29], FaultType: bit_flip, Mask: 0x800, Width: 64
board.chaos_reg.numFaultsInjected  1
guest output: SUM=118831515424667458 CRC=dbc8bf2a
```

这一次注入被 Masked（输出仍等于 golden）。这只证明 D13 能进入 CHAOS
单故障闭环，不声称这次一定产生 SDC；SDC 检出率仍以上游 4×100 实验为准。

## 4. 一键验证

```bash
source ~/gem5-deps/env.sh
ARM_CC=aarch64-openEuler-linux-gcc GEM5_OPT=CHAOS/gem5/build/ARM/gem5.opt \
  bash scripts/test-d13-upstream.sh
```

真实输出：

```text
[verify] vendored upstream D13 provenance
sha256 ok: sdc_probe_workload_d13.c
sha256 ok: sdc_probe_workload_random.c
sha256 ok: LICENSE
[build] D13 and B baseline (aarch64-openEuler-linux-gcc)
[run] D13 native golden
SUM=118831515424667458 CRC=dbc8bf2a
[run] D13 native determinism
[run] B baseline native golden
SUM=10721424292087689827 CRC=6728fc4a
[run] D13 under native gem5 (O3, no injection)
[run] D13 CHAOSReg single-injection smoke
Cycle: 1000, ... FaultType: bit_flip, Mask: 0x800, Width: 64
D13 provenance, golden output, determinism, gem5 baseline and FI smoke passed
```

静态完整性检查：

```text
$ python3 -m pytest tests/test_d13_upstream.py -q
3 passed
```

## 5. 与本地启发式的边界（必须保留）

| 项 | 上游 D13 | 本地 `operand_heuristic.py` |
|---|---|---|
| 位置 | `sdcfuzz/upstream/d13/`（原样） | `sdcfuzz/operand_heuristic.py` |
| 运行位置 | guest 内（workload 运行时） | host 侧 Python |
| 随机源 | 固定种子 LCG，guest 内 | SplitMix64 候选池 |
| 选择依据 | `popcount(x^(x+1))` + 定向变异 | 进位链/翻转密度/固定值惩罚 |
| 用途 | D13 对照臂 | 可选对照，不是 D13 |

`tests/test_sdcfuzz_operand_heuristic.py` 中的别名也已从 `d13` 改为
`heuristic`，避免测试代码继续把本地启发式称为 D13。
