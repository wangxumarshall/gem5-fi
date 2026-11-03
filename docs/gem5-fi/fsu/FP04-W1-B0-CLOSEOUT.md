# FSU-FP04-F0-W1 正式收口（真实 W1 + 指令级解码 + B0-core）

> 生成时间：2026-11-03。本文所有数值来自本机真实 gem5 运行与
> `runs/fsu/FSU-FP04-F0-W1` 的 AUTHORITATIVE 证据。

## 1. 结论

- 现有 `fp32_fma_kernel` **不满足**工作簿 W1；已新增真实
  `w1_fp_scalar_probe`，覆盖 W1 的 FP32/FP64 六类运算、特殊值、
  4 种舍入与 FPSR/FPCR 快照。
- 实现了从**真实动态 AArch64 指令编码**判定 scalar/vector、
  FP32/FP64、element width、lane 数；错误 precision/lane 的候选会被
  fail-closed 拒绝，且不消耗 eligible/ordinal。
- B0-core 已参数化并通过运行态 `config.ini` 门禁：
  ROB=40、IQ=32、fetch/decode/rename=3/3/3、dispatch=6、
  issue/wb/commit=8/8/8、PRF 128/192/48、LQ/SQ=16、
  fetchBuffer=16、squash=8。
- `FSU-FP04-F0-W1` 在 **B0-core** 下完成 3 个正式 seed：
  - 3/3 `admitted`、`certified`、`violations=[]`、`audit.ok=true`
  - 每个 seed 1 个 fault，terminal 全 `full`
  - oracle：seed1 Masked，seed2/3 SDC
  - decoded 指令分别为 `fmov` / `fmadd` / `fdiv`，均为
    `scalar_vfp`、`fp32`、element=32、lanes=1、precision_match=1、
    lane_match=1。
- 正式完成数：**15/519 → 18/519**；seed-complete RunID：
  **5/173 → 6/173**。`overall coverage_status` 仍为 **NOT_COMPLETE**。

## 2. W1 身份审计

工作簿定义（`gem5-fi-FSU单元故障注入方案_逐RunID传播监控.md:200`）：

> FP32/FP64 add/sub/mul/div/sqrt/FMA；NaN/Inf/±0/subnormal；4 种舍入；
> 位级结果和 FPSR/FPCR oracle；SE；禁止编译器把所有运算折叠为常量。

| 要求 | `fp32_fma_kernel` | `w1_fp_scalar_probe` |
|---|---|---|
| FP32/FP64 | 仅 FP32 | 均覆盖 |
| add/sub/mul/div/sqrt/FMA | 仅 FMA | 六类均覆盖 |
| NaN/Inf/±0/subnormal | 无 | 16 个特殊值 + 16 个有限值全交叉 |
| 4 种舍入 RN/RP/RM/RZ | 无 | 每轮 MSR FPCR 切换并读回 |
| FPSR/FPCR oracle | 无 | 每 op FPSR 快照；FPCR 四模式快照；联合 ARRAYHASH |
| 防常量折叠 | 基本 | volatile + barrier + `-ffp-contract=off -frounding-math -fsignaling-nans -fno-tree-vectorize` |
| 判定 | **不是 W1**，仅 FP32 FMA gate | **符合 W1** |

`w1_fp_scalar_probe`：
- 源码 SHA-256 `a6ae99154473f398eba74fc854c6f1c63ff7b1fe938b265e1cc3cf48ea07d554`
- 二进制 SHA-256 `c2b8a553bd44c87faaa3d8130d8a897097dc53c4e1627cb2b09b32a59e914754`
- 反汇编只有标量 `fadd/fsub/fmul/fdiv/fsqrt/fmadd`，无 NEON `fmla`；
  gem5 stats 中 `SimdFloat* = 0`
- native 3 次与 gem5 C3 3 次输出逐字节一致：
  `ARRAYHASH=ffe18c8279bf419d9b0aad0f5e03901874d3440506066d93ede75820f2eba183`，
  `ULP=0`，BITMISMATCH/FPSRMISMATCH/FPCRMISMATCH 全 0
- gem5 SE 实测：MRS/MSR FPCR/FPSR 可用；RN/RP/RM/RZ 位级结果与 native
  一致；IOC/DZE/OFC/UFC/IXC/IDC 可观测

诚实边界：FPCR trap-enable/RES0 位、FPSR QC/NZCV、同步 FP 异常恢复在
gem5 SE 中不可观测或为 proxy，标为 N/A；FZ/DN/IDC 已单独实测，但默认
workload 不覆盖，不能宣称。

## 3. 指令级 precision/lane 解码

- 新增纯头 `decoded_fp.hh` 与 39 条真实编码向量 host 单测。
- 标量 VFP：`(enc & 0xFE000000) == 0x1E000000`，`type[23:22]`
  00=FP32、01=FP64；FCVT/int-convert 不可靠。
- NEON FP 向量：`[28:24]=0b01110`，element width=bit22（不是
  size[23:22]，FMINNM v.4s 反例），lanes=(Q?128:64)/width。
- FP16、by-element、AdvSIMD scalar、FCADD/FCMLA、FMLAL/FMLSL、
  SVE/SME 全部 `reliable=false`。
- 真实 gem5 countOnly 验证：

| 配置 | eligible | 结果 |
|---|---:|---|
| W4 FP64/lane64 + guard | 32,771 | 接受 FP64 scalar/NEON |
| W1 FP32/lane32 + guard | 49,664 | 接受 FP32 scalar |
| W3 FP32/lane32@2 + guard | 16,384 | 接受 FP32 NEON lane2 |
| FP32 workload + manifest fp64 | 0 | precision mismatch 拒绝 |
| W4 FP64 workload + manifest fp32 | 0 | precision mismatch 拒绝 |
| NEON FP32 + lane64/offset1 | 0 | lane mismatch 拒绝 |
| scalar + lane_offset1 | 0 | 非 SIMD lane 拒绝 |
| lane_offset=4 / lane32 | rc=134 | 构造期 panic |

## 4. B0-core 平台

工作簿 B0 对应 `O3_ARM_v7a_3` 核心点。真实 B0 countOnly 的
`config.ini` 逐项实测：

| 参数 | B0-core 期望 | 实测 |
|---|---:|---:|
| fetch/decode/rename | 3/3/3 | 3/3/3 |
| dispatch | 6 | 6 |
| issue/wb/commit | 8/8/8 | 8/8/8 |
| ROB | 40 | 40 |
| IQ | 32 | 32 |
| PRF int/float/vec | 128/192/48 | 128/192/48 |
| LQ/SQ | 16/16 | 16/16 |
| fetchBuffer | 16 | 16 |
| squash | 8 | 8 |

- 未实现：完整 v7a_3 的 FP FUPool=2；B0-core 仍使用默认 FUPool。
- 历史 15 个 W4/W3 seed 均为 C3-valid，不追溯改标为 B0。
- B0 声明不符合 `config.ini` 时 runner/audit fail closed，不写
  `.done`/`AUTHORITATIVE`。

## 5. 正式 F0-W1 三 seed（B0-core）

| seed | attempt | decoded 指令 | field | oracle | terminal | audit checks | audit.json |
|---:|---|---|---|---|---|---:|---|
| 1 | attempt-2 | `0x1e270060` fmov | sign bit31 | Masked | full | 69 PASS | `c25962f19cde7a6d8181c37c7deabda73ed3175b6cc28c5663f70f0c9375560a` |
| 2 | attempt-2 | `0x1f010040` fmadd | sign bit31 | SDC | full | 69 PASS | `e961afca622d7b2531b31c6c95f2b032f99d81adede17e42e1812d0827c94fda` |
| 3 | attempt-2 | `0x1e211800` fdiv | sign bit31 | SDC | full | 69 PASS | `52ee267601914d5d43d9caf2ae7933108ffc479acbbe5aee8b8f1cfe725e126e` |

- eligible=49,664（B0 census，decode_guard）；skip=9,427 / 34,906 / 37,677
- 每个 root：`decoded_kind=scalar_vfp`、`decoded_precision=fp32`、
  `decoded_element_width=32`、`decoded_lanes=1`、
  `decoded_reliable=1`、`precision_match=1`、`lane_match=1`
- census 与 inject 的 `config.ini` 均通过 B0-core 逐项校验
- 原始 C3 attempt-1 保留并标记 SUPERSEDED，不计入 18/519

Seed Markdown：
`runs/fsu/FSU-FP04-F0-W1/seed{1,2,3}/attempt-2/FSU-FP04-F0-W1-seedN.md`
与 `runs/fsu/COMPLETE_PROPAGATION_PATHS/FSU-FP04-F0-W1/`。

## 6. 覆盖边界

- 正式 seed 18/519；RunID 6/173；其余 167 个 0/3。
- W1 workload 是真实 artifact，但每个 seed 只注入 FP32 scalar sign；
  FP64、特殊值、4 舍入与 FPSR/FPCR 仅被执行/观测，未逐 seed 注入。
- FP04-a 仅部分覆盖（FP32 scalar sign）；FP64 sign、exp/mant 字段、
  其他 lane、B0 完整 FUPool 仍未完成。
- `overall coverage_status = NOT_COMPLETE`。
