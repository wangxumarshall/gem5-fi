# Upstream D13 workload (vendored verbatim)

本目录是上游 sdcfuzz 仓库 D13 实验的**原样副本**，不是本仓库重写的
`operand_heuristic.py`。目的：严格按技术路线文档的 D13 口径验证和复跑，
避免把本地启发式误称为 D13。

## 来源

| 项 | 值 |
|---|---|
| 上游仓库 | `git@github.com:wangxumarshall/sdcfuzz.git` |
| 上游提交 | `707db35da507bbe7c086ee3760ea3b3260aaf930` |
| 源路径（D13） | `gem5_config/workloads/sdc_probe_workload_d13.c` |
| 源路径（B/随机基线） | `gem5_config/workloads/sdc_probe_workload_random.c` |
| 上游重复副本 | `seeds/gem5/sdc_probe_workload_d13.c`（与 D13 源文件 sha256 相同） |
| 许可证 | Apache License 2.0（见 `LICENSE`） |

## SHA-256（同步时实测）

```text
4143a4bdee3244452ce2747e590d6cbfbbb45117b23a3027d04a0eacc0067263  sdc_probe_workload_d13.c
fb461f72675c194b5a93aeeeab55f73f6fba5ad6cf4830146bc935d1c169c1be  sdc_probe_workload_random.c
cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30  LICENSE
```

## 文档语义（D13）

`docs/sdcfuzz/d13-baseline-reproduction.md` 与 `sdcfuzz/sdcfuzz-v1.2.md`
描述的 D13 是：

1. 每次生成两个随机 64 位候选 A、B；
2. 对 A 做定向变异：异或随机 mask、+1、循环左移、再与 `~A` 异或；
3. 用 `popcount(x ^ (x + 1))`（尾部连续 1 的长度，进位链代理）比较
   “变异后的 A”和“随机 B”，保留较大者；
4. 同时保留若干纯随机操作数，维持覆盖广度；
5. 在 workload 内每次迭代重新选择。

对应代码见本目录 `sdc_probe_workload_d13.c`：

- `rng_u64()`：固定种子 LCG，两个 32 位拼 64 位；
- `targeted_mutate()`：`a ^ mask`、`+1`、循环左移 1、`^= ~a`；
- `pick_high_toggle()`：`popcount64(a_mut ^ (a_mut + 1))` vs
  `popcount64(b ^ (b + 1))`，选较大者；
- `carry_chain()`：4 个定向选择 + 4 个纯随机操作数；
- `main()`：`ITERS=200`，每轮调用 `carry_chain/toggle_rate/lsu_cross`。

## 构建与运行

```bash
aarch64-openEuler-linux-gcc -static -O2 -o sdc_probe_workload_d13 \
  sdcfuzz/upstream/d13/sdc_probe_workload_d13.c
./sdc_probe_workload_d13
# SUM=118831515424667458 CRC=dbc8bf2a
```

随机基线 B：

```bash
aarch64-openEuler-linux-gcc -static -O2 -o sdc_probe_workload_random \
  sdcfuzz/upstream/d13/sdc_probe_workload_random.c
./sdc_probe_workload_random
# SUM=10721424292087689827 CRC=6728fc4a
```

在 gem5 中运行（本仓库原生 `build/ARM/gem5.opt`）：

```bash
CHAOS/gem5/build/ARM/gem5.opt --outdir=m5out/d13-upstream \
  configs/se/arm_chaos.py --cpu=O3 \
  --cmd=sdcfuzz/upstream/d13/bin/sdc_probe_workload_d13
```

一键验证（哈希、编译、本地运行、gem5 运行、FI 冒烟）：

```bash
source ~/gem5-deps/env.sh
ARM_CC=aarch64-openEuler-linux-gcc bash scripts/test-d13-upstream.sh
```

## 边界

- 本目录只同步 **D13 算法 workload** 和 **B 随机基线**；上游完整的
  `sim_sweep.py`/`two_level_taishan.py` 实验编排仍是外部资产，不在本目录。
- D13 的 4×100 次 bit/struct 实验记录见
  `docs/sdcfuzz/d13-baseline-reproduction.md`；本目录的一键验证只做
  workload 完整性、golden 复现和单次 FI 冒烟，不冒充 400 次实验。
- `sdcfuzz/operand_heuristic.py` 是另一个主机侧启发式，**不是 D13**；
  不要把两者混用为同一对照臂。
