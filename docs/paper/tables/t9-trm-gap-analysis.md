# §8.4 与 Neoverse N1 TRM Table 9-1 保护基线的差距分析

> 方法：逐结构对比 N1 TRM Table 9-1（方案 §2.3 代理表）与**本仓库
> formal 实测数据揭示的 V110 实际风险分布**，标出差距与补齐建议。
> 证据等级（§1.3）：E2（gem5 O3 formal n=384）为主，E4（V110 RTL
> 推断）项全部进文末"待校准清单"，不进设计建议正文。

## 逐结构差距表

| 结构 | N1 TRM 代理保护（§2.3） | formal 实测风险 | 差距判定 | 建议补齐 | 证据 |
|---|---|---|---|---|---|
| L1D data 阵列 | secded_poison | raw 97.7% SDC → secded 后 0%（1-bit 档实测风险反转） | **代理有效** | 维持；补 2/3-bit 档（B/C 静默 384/384——SED 家族边界如实） | E2 l1d_formal×2 + l1d-ecc |
| **L1D load 回填通路** | **未覆盖（TRM 表无此行）** | **PCE 90.9% SDC** | **最大差距**：阵列 ECC 不保护 check-after-path | 回填段端到端重校验（§8.2 排序 #1） | E2 l1dfwd_formal n=384 |
| L1I data | sed | 0% SDC（stuck 两档 n=384 全 Masked） | 代理充分（指令流重取自愈） | 无需补 | E2 l1i_formal_loop |
| L1D/L2 tag | secded | tag 翻转 false-hit → SDC（6c672323 tag→SDC 实证） | 代理方向正确，false-hit 档需 invalidate-on-2bit | 2-bit 档 invalidate 策略实测验证 | E2 CHAOSCache tag 字段级 |
| iTLB/dTLB | none | pfn_to_mapped_page 活页替换 → guest Oops（0x9600004f 家族） | **代理一致（none）且风险确认** | §8.2 建议给 L1 TLB 加 parity（N1 L1 也是 none——ARM 惯例差距） | E2 FS checkpoint 84M 注入 0 SimulatorError |
| L2 TLB/walk cache | parity_interleaved | parity 模型实测：1-bit DetectedInvalidated（pfn 恢复+条目失效重走），系统继续正常 | **代理有效（行为级验证）** | 维持 | E2 ac3f977f parity 对照 |
| PRF | none | ~10% SDC / 92.7% DUE；read-trace reads>0 传播 | 代理一致；风险在 DUE 非 SDC | parity 可选（成本/收益权衡） | E2 prf-formal 网格 |
| RAT/freelist/ROB/IQ/store buffer | none | 全部 0% SDC、DUE 主导（72–100%） | **代理一致且免 SDC 保护**（§8.2 结论 2） | 无需补（DUE 由重试/RAS 消化） | E2 escape_decomposition |
| FSU 数据通路 | none（TRM 表未单列） | 13.6–18.0% 位段 SDC（t3-1 n=384×4） | 表格缺行：FSU 无保护但风险非零 | 结果 parity / sign+exp 窄校验 | E2 t3-1-fsu-formal |
| DRAM | secded | 后备字节被 L1/L2 掩盖（384 全 Masked）；ecc_logic_fault 1-bit 漏检实证（E 机理） | 代理部分有效；**ECC 逻辑自身是单点故障** | ECC 逻辑 BIST；SDEC/ChipKill 升级评估 | E2 mem formal + T5-1 对照 |
| store→load 转发 | none（TRM 表未单列） | wrong-source 37.6% SDC | 表格缺行：转发通路高风险 | 转发命中 ID 比对 + 数据 parity | E2 fwdsrc_formal |

## 结论

1. **TRM 代理表的最大盲区不是保护强度而是覆盖范围**：load 回填通路
   （90.9%）与 store→load 转发（37.6%）在 Table 9-1 中没有对应行——
   代理表的"结构粒度"粗于实测风险分布的实际粒度。
2. **none 组（乱序后端）代理判断正确**：formal 确认 DUE 主导、SDC≈0，
   该组不需要 SDC 代理保护——与 N1 TRM 惯例一致。
3. **ECC 家族边界**（B/C 静默 + E 机理）是所有 secded 行的共同差距：
   保护机制本身需要自检（BIST），这是 TRM 表粒度外的横向建议。

## 待校准清单（E4：V110 RTL 推断，不进设计建议正文）

- [ ] V110 L1D 是否真有 poison 传播（N1 的 secded_poison 行为是否同款）——需实机 RAS/EINJ 枚举（S7 deferred）
- [ ] V110 L2 TLB parity 交织几何（interleave stride）——影响 2-bit 静默率
- [ ] V110 store buffer 深度与转发 CAM 结构——影响 wrong-source 实际命中率
- [ ] V110 FSU 是否有结果 parity（部分企业核有非公开校验）
- [ ] 回填通路物理实现（fill buffer 是否有端到端校验）——PCE 90.9% 的代理与实机差距
