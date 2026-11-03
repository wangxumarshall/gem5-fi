# FP04 F0-W5 / F0-W6 artifact 状态（2026-11-03）

> 结论：**FSU-FP04-F0-W5 与 F0-W6 均不得运行正式 seed**。它们是活跃
> F0 范围，但 artifact 身份未成立；不是 F1–F4 的 DEFERRED_BY_USER。

## 1. F0-W5（PolyBench-FP）

工作簿定义（主方案 :204）：

> gemm、2mm、lu、cholesky、jacobi-2d；固定规模；输出数组逐元素+容差+哈希校验；
> 每个子程序独立报告 eligible 和 activated。

### 1.1 现有真实资产（4/5）

来源：PolyBench/C 4.2.1 beta，上游 commit
`3e872547cef7e5c9909422ef1e6af03cf4e56072`；许可证 OSU Software
Distribution License（`workloads/ooo/polybench/LICENSE.txt`）。

| program | 源码 SHA-256 | 二进制 SHA-256 | 规模 | native golden |
|---|---|---|---|---|
| gemm | `4dc9e7a6…4d6fe7` | `f7262986…629e2a6` | 88³ | `116849d3adf3227b` |
| lu | `f9241eeb…9d82fd` | `f1b0cc90…46f8ea9` | 84 | `74ffe5eb77ea9257` |
| cholesky | `c0f74bb7…884828` | `fd2912c4…fc6f005` | 88 | `ea7e0d0e7c86582d` |
| jacobi-2d | `ac9e915f…e56af098` | `a1b29cf2…410ed07` | T=8,N=160 | `dc867b5f02998c1e` |
| 2mm | `31685308…7711d`（patched） | `996168f0…6ee6f3` | NI=NJ=NK=NL=72 | `41ebd3d0a77ab3d2` |

2mm 于 2026-11-03 从同一上游 commit 取得：
上游原始 source SHA `9e4d9524…62e481`，vendored patched source SHA
`31685308…7711d`，header SHA `1265ba7c…60c037`；native 3 次与 gem5 B0
3 次输出逐字节一致，`FINAL=41ebd3d0a77ab3d2`。
其余四个 native 二进制复跑与上表 golden 一致。

### 1.1.1 B0+decode 逐程序 eligible（真实 countOnly）

| program | eligible | decode rejects | census 证据 |
|---|---:|---:|---|
| gemm | 1,370,774 | 0 | `runs/fsu-gates/W5-ARTIFACT-CENSUS/gemm` |
| lu | 800,959 | 0 | `runs/fsu-gates/W5-ARTIFACT-CENSUS/lu` |
| cholesky | 810,712 | 0 | `runs/fsu-gates/W5-ARTIFACT-CENSUS/cholesky` |
| jacobi-2d | 2,099,622 | 51,458 | `runs/fsu-gates/W5-ARTIFACT-CENSUS/jacobi-2d` |
| 2mm | 1,145,697 | 20,774 | `runs/fsu-gates/W5-ARTIFACT-CENSUS/2mm` |

每个目录含真实 `config.ini`（B0 逐项校验通过）、`fpu_injections.log`、
`SHA256SUMS`；2mm 另有 gem5 golden 3 次的 `golden/`。

2mm decode-gate（不计 519）：`FSU-FP04-F0-W5-2MM-DECODE-GATE` seed1
为真实 `0x1f020401 fmadd`，scalar_vfp/fp32、match=1，完整 L0–L5、
SDC、audit 69 PASS。

### 1.2 阻塞点

1. **suite 身份未定义**：工作簿要求五个程序的 suite；现有 runner/manifest/
   事件/Markdown 只支持单二进制，无 `program_id`/`suite_hash`。
2. **3-seed 计数规则未裁决**：一个 RunID 是“每个程序 3 seed（共 15）”还是
   “suite 级 3 seed”？前者改变 519 的 RunID×3 语义，后者无法覆盖 5 个
   程序的独立 eligible/activated；需要工作簿/负责人裁决。
3. **oracle 不足**：现有只有 `FINAL=<16hex>` 精确哈希；工作簿要求
   “输出数组逐元素+容差”。没有 per-element 输出/golden 数组。
4. **activation 尚未实测**：W5 还没有正式 L0–L5 prop_evt；2mm gate 已
   证明单程序可链，但 suite 级 activation 尚未定义。
5. FP04-d（NEON lane）在这些标量 PolyBench 二进制上 eligible=0；
   不能用标量 PolyBench 宣称 FP04-d。

### 1.3 裁决

**artifact 5/5 已完成；正式 F0-W5 仍 BLOCKED**，原因是 suite/program_id/
3-seed 计数规则/逐元素 oracle 未裁决。2mm 已真实 vendoring、golden 3×、
B0+decode eligible 与单程序 gate 全部通过；但不能用单程序结果冒充
suite RunID。允许的替代只有独立 GATE（不计 519）或明确标注的
PARTIAL pilot。

## 2. F0-W6（SVD-FFT-Sparse）

工作簿要求 SVD、FFT 与稀疏线性系统组件。现有：
- `workloads/directed/svd_iterative_kernel` 真实存在，golden
  `4afb95b5b32f3820`，只代表 SVD。
- FFT：`workloads/mibench/bin/fft` 存在，但没有 FSU golden/固定输入
  oracle，未绑定 W6。
- 稀疏：`method1_controls` 的 `pure_spmv` 是代理，不是固定稀疏线性系统。

因此 W6 仍是 **PARTIAL**，不能用单个 SVD kernel 代表全部 W6；在 FFT
与稀疏组件获得真实 artifact/oracle 前不运行正式 F0-W6。

## 3. 下一步

1. 从 PolyBench/C 4.2.1 commit `3e872547…` vendoring 2mm，记录源码 SHA、
   NI/NJ/NK/NL、构建命令、native/gem5 golden。
2. 定义 `suite_id` 与 `program_id`，在 manifest/事件/Markdown/路径中固定；
   明确每个程序独立 3 seed 还是 suite 级 seed（需工作簿裁决）。
3. 为 PolyBench 增加 per-element/tolerance oracle，或明确登记 hash-only
   偏差（不得静默）。
4. 每个程序单独 census，不合并分母；FP04-d 需要独立向量化构建。
5. W6 需补 FFT 固定输入/oracle 与稀疏固定系统，或由工作簿确认单 SVD
   代表程序（当前原文不允许）。
