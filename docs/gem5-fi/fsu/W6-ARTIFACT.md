# W6 artifact：SVD + FFT + 稀疏线性系统（native 已完成，gem5 待主 agent）

> 日期：2026-11-04。分支 `fsu`。
> 范围：`FSU-FP04-F0-W6` / `FSU-FP06-F5-W6` 的 **artifact 准备**。
> 本文只记录真实执行过的 native 证据；**gem5 B0 / gem5 fault-run golden
> 尚未由本 agent 运行**，不得据本文声称 W6 已完成或可正式计数。

## 1. 固定 suite

`configs/fsu/suites/w6-fp-v1.json`，顺序不可调整：

```
svd → fft → sparse-cg
```

`schema`/身份校验：`tools/fsu_w6_suite.py`。`suite_hash` 覆盖：

- `suite_id` / `suite_version` / 固定顺序与数量；
- 每组件 `program_id` / `program_index` / `source_sha256` /
  `binary_sha256` / `golden_array_sha256` / `scale` / `input_id` /
  FINAL token；
- 每组件 `element_oracle.oracle_version` 与完整预注册 `meta`
  （dtype/layout/shape/count/abs_tol/rel_tol/ulp_tol）；
- compiler version/cflags、oracle version。

运行结果、attempt、状态、路径不进入 `suite_hash`。

当前：

```
suite_hash = 7af52ddcbc1ad03d71e7f683fe87c804a7ddbc0a9ed73a0a5d06e18dc43adf1a
```

（这是加入 `program_overrides` 后的 F0 `w6-fp-v1.json` 哈希；F5 见 §8。）

## 2. 组件身份（真实磁盘 SHA-256）

| component | source SHA-256 | binary SHA-256 | golden array SHA-256 | FINAL | dtype/count |
|---|---|---|---|---|---|
| svd | `2db77b5a5528268a…` | `42cfc2441b1c0a56…` | `c057a7f60984974a…` | `4afb95b5b32f3820` | fp64 / 64 |
| fft | `e801f1dc7055511f…` | `93371215ece1fcfe…` | `dde19526f0354b3a…` | `fdd819481ea73b0c` | fp32 / 1024 |
| sparse-cg | `1df074f6fe5e259b…` | `9755159759fc3b20…` | `ea5b57c3795f5b56…` | `feb0479242258ead` | fp32 / 256 |

完整 SHA 与预注册的 `abs_tol/rel_tol/ulp_tol` 在
`configs/fsu/suites/w6-fp-v1.json`；`tools/fsu_w6_suite.load_suite()`
会在加载时重算 source/binary/golden 三个 SHA，任何漂移都响亮拒绝。

## 3. 来源、许可证、构建

### 3.1 SVD（既有组件）

- `workloads/directed/svd_iterative_kernel.c`：仓库原有 Jacobi 迭代 SVD
  （N=8，10 sweeps）。
- 本次仅新增 `<gem5fi_oracle.h>` 与一次固定数组 dump；FINAL
  （对角线 double 的 FNV-1a）与 stdout 其它内容不变，仍是
  `4afb95b5b32f3820`（与 `tools/runner.py` 的
  `svditerative-golden-v1` 一致）。
- dump 域 = 完整 8×8 矩阵（fp64，row-major，64 元素），是 FINAL 域
  （对角线）的超集；这是有意的元素级 oracle 域，已在 suite meta 固定。

### 3.2 FFT（新增）

- `workloads/directed/fft_radix2_kernel.c`：自撰迭代 radix-2
  Cooley-Tukey FFT，N=1024。
- 作者/许可证：gem5-fi project contributors (2026)，原创代码，许可证与
  仓库一致（见 `CLAUDE.md`）。
- 固定输入：`re[n] = (((n*37+11) % 101) - 50) / 50`, `im[n]=0`；无
  `rand()`/时间/环境依赖。
- 输出：`out[n] = |X[n]|^2`（fp32，1024 元素），FINAL 覆盖该数组原始
  小端字节；`--array-dump` 写同一数组。

### 3.3 稀疏线性系统（新增，非 SpMV 代理）

- `workloads/directed/sparse_cg_kernel.c`：16×16 五点 Laplacian
  （N=256，SPD）上的真实共轭梯度求解器。
- 固定输入：`x_true[i] = 1 + ((i*7+3) % 11)/11`，`b = A*x_true`；
  `x0=0`，最多 400 次 CG 迭代，容差 `1e-7`；无随机/时间依赖。
- 输出：解向量 `x`（fp32，256 元素）+ `RESIDUAL=<相对残差>` +
  `FINAL=<16hex>`；`--array-dump` 写 `x`。
- native 相对残差：`2.825277123e-09`（3 次一致）。
- 明确不是 `method1_controls` 的 `pure_spmv` 代理。

### 3.4 共享 dump 头

三个组件都复用
`workloads/ooo/polybench/utilities/gem5fi_oracle.h`（PolyBench W5 的
canonical raw little-endian dump），没有第二份实现。

### 3.5 可重复构建

```bash
make -C workloads/directed w6
```

等价命令（suite `compiler.cflags` 记录同一组）：

```bash
gcc -O2 -static -Wall -Wextra \
    -I workloads/ooo/polybench/utilities \
    -o workloads/directed/<component> workloads/directed/<component>.c -lm
```

2026-11-04 实测：三个二进制分别重新编译到 `/tmp` 后与仓库内二进制
**逐字节相同**（SHA-256 完全一致），构建零 warning。

## 4. 固定输入与规模

| component | input_id | 规模 | 输出域 |
|---|---|---|---|
| svd | `svd-fixed-A-8x8-v1` | N=8，10 sweeps | 8×8 fp64 矩阵 |
| fft | `fft-radix2-N1024-fixed-v1` | N=1024 | 1024 fp32 功率谱 |
| sparse-cg | `sparse-cg-5pt-laplacian-16x16-v1` | GRID=16, N=256 | 256 fp32 解向量 |

## 5. Native golden（3× 逐字节一致）

生成/校验工具：

```bash
python3 tools/fsu_w6_golden.py --update-suite
```

每个组件运行原生二进制 3 次（`--array-dump`），要求 rc=0、FINAL 相同、
dump 字节 SHA 相同，并做一次预注册 oracle 自检（EXACT_MATCH）后才写
golden。`configs/fsu/suites/w6-fp-v1/golden/manifest.json` 记录了三
次 SHA、rc、FINAL（sparse 另记 RESIDUAL）。

实测 3× SHA（每次相同）：

| component | native 3× array SHA-256 |
|---|---|
| svd | `c057a7f60984974ab4db131468dbf4f078432f69112593eec44701a207fb531c` |
| fft | `dde19526f0354b3a61be193aae24b3c11c4cdfac70e8aa6adbac5be9d9b1f177` |
| sparse-cg | `ea5b57c3795f5b56f2f4c0c374555bd542056f2aad70cf224eabe6abe14bc8f8` |

golden 文件：`configs/fsu/suites/w6-fp-v1/golden/{svd,fft,sparse-cg}.bin`。

## 6. 数值 oracle

`tools/fsu_w6_oracle.py`：

- fp32：**直接委托** `tools/fsu_oracle.py:compare`，与 W5 同一实现，
  不存在第二套 fp32 容差代码。
- fp64：同一 OR 规则
  `abs<=abs_tol OR rel<=rel_tol OR ulp<=ulp_tol`；NaN 仅同 bit pattern
  匹配，±Inf 仅同号匹配，容差不能救非有限失配；ULP 用 64-bit
  保序整数映射。
- 预注册容差在本 suite 中固定为 `abs_tol=0.0, rel_tol=0.0, ulp_tol=0`
  （gem5 SE fplib 在本平台被证明 bit-exact）；不得在看到结果后修改。
- 工具校验 dump 长度恰为 `count * elem_size`，拒绝截断/填充。

## 7. 缺口（必须如实登记）

1. **gem5 golden 未运行**：本 agent 被禁止运行 scons/gem5。gem5 B0
   无故障 3× 与 fault-run golden 由主 agent 在组件齐全后执行。
2. **W6 gate 已准备但未真实运行**：`tools/fsu_w6_gate.py` 已实现
   `--print-commands` / `--verify-only` / 运行路径，F0 与 F5 预注册也已
   建立；但 gem5 执行与 3 seed 正式计数仍由主 agent 完成。W6 正式 seed
   计数仍为 0。
3. **SVD dump 域与 FINAL 域不同**：FINAL 只覆盖对角线 double；元素
   oracle 覆盖完整 8×8 矩阵。两者都已固定，不存在“用 dump 重算 FINAL”
   的假设。
4. **FFT twiddle 使用静态链接的 libm `cosf/sinf`**：确定性来自固定
   二进制 + 固定输入；gem5 侧逐位一致性仍需主 agent 的 B0 golden 证明。
5. **容差为 0**：若主 agent 的 gem5 B0 出现非 bit-exact（与既有
   W1/W5 结论相反），必须**先**修改预注册容差并重算 `suite_hash`，不得
   事后放宽容差。
6. 本文不把 native golden 当作 gem5 golden，也不把 W6 artifact 完成
   当作 RunID 完成。

## 8. 逐程序精度覆盖 / F0-F5 预注册 / gate

### 8.1 为什么需要 `program_overrides`

W6 三个组件精度不同：SVD 是 **fp64**（lane 64，64-bit mask），FFT 与
sparse-CG 是 **fp32**（lane 32，32-bit mask）。单一 suite injector 无法
同时通过 CHAOSFPU 的 decode_guard。因此 suite 增加
`program_overrides`（program_id -> 覆盖块）：

应用顺序（`tools/fsu_suite.resolve_program_injector`）：

```
suite.injector
  → program_overrides[pid]        # 精度/lane/bitseg/op/reg；可带 fault_mask
  → seed_plan                     # F5：只覆盖它实际声明的字段
```

- seed_plan 省略的几何字段（W6 F5 全部省略）继承 per-program override；
- seed_plan 声明的几何字段（W5 PolyBench F5）最后生效；
- F5 permanent_stuck 一律丢弃 `bitseg`：CHAOSFPU 明确 panic
  （`permanentStuck uses the explicit faultMask; bitseg is not allowed`），
  目标位由 fixed `fault_mask` 唯一决定；F0 仍保留基础 `bitseg=sign`；
- mask 优先级（最具体者胜）：
  `suite base < seed_plan.mask < program_overrides[pid].fault_mask
   < seed_plan.program_mask[pid]`；
- `program_overrides`、`seed_plan`（含 `program_mask`）全部进入
  `suite_hash`；component manifest 记录 `program_override` 与
  `effective_injector`。

### 8.2 配置

| 文件 | 用途 | suite_hash |
|---|---|---|
| `configs/fsu/suites/w6-fp-v1.json` | F0-W6 预注册（复用为 F0 artifact） | `7af52ddcbc1ad03d71e7f683fe87c804a7ddbc0a9ed73a0a5d06e18dc43adf1a` |
| `configs/fsu/suites/w6-fp-v1-f5.json` | FP06-F5-W6 预注册（3 seeds） | `2d1a8f9d84d502996724d97adc96b811f81b657fbcbdd0d1026fd34f3c406804` |

两者使用同一组真实 golden/binary/source 哈希与 golden 数组，未改动。

F5 seed_plan：

| seed | submodel | polarity | SVD mask (fp64) | fft/sparse mask (fp32) |
|---|---|---|---|---|
| 1 | FP06-a | 0 | `0x8000000000000000` | `0x80000000` |
| 2 | FP06-b | 1 | `0x8000000000000000` | `0x80000000` |
| 3 | FP06-c | 0 | `0x0007f80000000000` | `0x007f8000` |

所有 seed 的 warm-up = 1024，sample limit = 1024，
keep_first_last_n = 256。

### 8.3 gate 工具

`tools/fsu_w6_gate.py`：一个 gate suite seed 固定 3 个 component run
（svd → fft → sparse-cg），**3/3** 组件独立 `audit.ok=true` +
`certified=true` + element oracle（SDC/MASKED）才 PASS。gate 不计正式
seed（`formal_suite_seed_count = 0`），证据只允许写
`runs/fsu-gates/`。

```bash
# 只打印命令（不运行 gem5）
python3 tools/fsu_w6_gate.py --suite configs/fsu/suites/w6-fp-v1.json --print-commands
python3 tools/fsu_w6_gate.py --suite configs/fsu/suites/w6-fp-v1-f5.json \
    --print-commands --all-seeds
# 正式 gate（主 agent 构建 gem5 后执行；证据不计 seed）
python3 tools/fsu_w6_gate.py --suite configs/fsu/suites/w6-fp-v1.json \
    --outdir runs/fsu-gates/W6-F0-GATE
python3 tools/fsu_w6_gate.py --suite configs/fsu/suites/w6-fp-v1-f5.json \
    --suite-seed 1 --outdir runs/fsu-gates/W6-F5-GATE
# 复核既有证据
python3 tools/fsu_w6_gate.py --suite configs/fsu/suites/w6-fp-v1-f5.json \
    --suite-seed 1 --outdir runs/fsu-gates/W6-F5-GATE --verify-only
```

### 8.4 仍未完成

- gem5 侧的 3/3 gate、CSV/audit 证据与 F0/F5 正式 seed 全部未运行；
- F0 artifact 的 `suite.injector` 只有 `bitseg=sign`（无 fault_mask），
  正式 F0 注入的 mask/polarity 仍需主 agent 在运行清单中固定并记录；
- 未创建 `w6-fp-v1-f0.json`：F0 artifact 直接复用 `w6-fp-v1.json`，
  因为 gate 工具按 `--suite` 选择 F0/F5，不需要重复文件。
