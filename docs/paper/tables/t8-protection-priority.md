# §8.2 保护优先级排序表（formal 数据驱动版）

> 依据：本仓库 formal campaigns（n=384 标准；P_SDC/P_DUE 95% Wilson CI）
> + §8.1 逃逸分解（t6）+ occupancy 加权（artifacts/meta）。排序规则：
> `风险 = Reach × P_SDC`（conditional escape probability），保护建议
> 按"代理保护有效性 × 实现成本"给出。
> 全部为 gem5 代理条件概率，非 FIT；单机未确认（§11.3）。

## 数据驱动排序（降序）

| 优先级 | 结构 | P_SDC [CI] | P_DUE | 逃逸机理 | 现有保护 | 建议保护 | 依据 campaign |
|---|---|---|---|---|---|---|---|
| 1 | **L1D 数据通路（load 回填段）** | 90.9% [87.6,93.4] | ~0 | D（post-check 盲区） | 无（ECC 不覆盖 fill→PRF） | 回填通路端到端 SECDED/parity 重校验；或 load 数据 CRC 预测 | l1dfwd_formal_reduce n=384 |
| 2 | **L1D 数据阵列（raw）** | 97.7% [95.6,98.8] | ~0 | A（无保护基线） | 无 | 数据阵列 SECDED（实测 secded_poison 将 97.7%→0%——风险反转有效） | l1d_formal_reduce ×2 组 n=384 |
| 3 | **store→load 转发（wrong-source）** | 37.6% [32.8,42.5] | 57.4% | A | 无 | 转发命中 ID 比对（CAM 冗余）；转发数据 parity | fwdsrc_formal_fwd n=384 |
| 4 | **FSU 数据通路（FP 源/结果）** | 13.6–18.0%（位段） | ~0 | A | 无 | 结果 parity（FMA 输出一拍校验）；尾数主导谱可做窄校验 | t3-1-fsu-formal-gemm-double n=384×4 |
| 5 | **LSQ 转发（byte 级）** | 4.7% [3.0,7.3] | 27.6% | A | 无 | 转发数据 parity | lsqfwd_formal_fwd n=384 |
| 6 | **PRF（寄存器堆）** | ~10%（X3 类位段） | 92.7% 主导 | A | 无 | cell parity（读出校验）；高 ABI 角色寄存器优先 | prf-formal 网格 |
| 7 | **DRAM 后备（secded 下 2/3-bit）** | 100% 静默未消费（B/C） | — | B/C | SECDED（1-bit 纠正） | SECDED 升级 SDEC/ChipKill（2-bit 检出）+ 毒化传播（F 待补） | l1d-ecc b2/b3 n=384 |
| 8 | IQ/ROB/RAT/freelist | 0% SDC（DUE 主导 72–100%） | 高 | A（DUE 响亮） | 无（squash 恢复有效） | 无需 SDC 代理保护（DUE 可被 RAS/重试消化） | iq/freelist formals n=384 |

## 保护投资结论（§8.2）

1. **数据通路三件套（L1D 回填/L1D 阵列/转发）稳居前三**——occupancy
   加权下排序稳健（6dde51ce）：缓存保护只盖住阵列位翻转（97.7→0），
   但回填通路 90.9% 完全盲区——"给阵列加 ECC"只解决一半问题。
2. **DUE 主导结构（IQ/ROB/RAT/freelist）不需要 SDC 代理保护**——
   错误映射/队列状态破坏以崩溃形式响亮暴露（72–100% DUE），软件
   重试/RAS 上报即可；保护投资应让位于数据通路。
3. **SECDED 的边界**：1-bit 纠正有效（实测 97.7→0 风险反转），
   2/3-bit 静默（B/C 384/384）+ ECC 逻辑自身故障（E 机制对照实证）
   ——保护机制本身是单点故障，需自检（ECC 逻辑 BIST）。
4. **FP 通路**：位段差异有限（13.6–18.0%），尾数误差常被累加舍入
   吸收——窄校验（仅 sign/exp）可能已捕获大部分风险。

> 诚实边界：全部结论基于 SE 模式 gem5 代理（TLB/PTW/AGU 需 FS）；
> 单机数据未第二机复现；F 机理（毒化传播）无 formal 数据。
