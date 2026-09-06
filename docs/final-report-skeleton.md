# 鲲鹏920 SDC 故障注入 — 最终报告骨架（Phase 6.4）

> 状态：骨架 + 已有定量结论填充。生成日期 2026-09-06，HEAD 6dde51c。
> 数据源：55 campaigns / 133 cells / ~16,000 reps（formal n=384 × Wilson 95% CI）。
> 姊妹文档：findings.md（全部结论的证据链）、artifacts/meta/escape_decomposition.md（§4.1/§4.2 机读表）。

## 1. 执行摘要

- **SE 侧 15/15 微架构单元 formal 齐备**（设计文档 §2.1–2.18 中 S1–S3 范围全部完成；L3/NoC/HCCS 属 S4 后置）。
- **核心定量格局**（三带结构，全部 n=384）：
  - **SDC 带**：L1D 命中数据 97.7% [95.6,98.8] > L1D post-check（ECC 后通路）90.9% [87.6,93.4] > LSQ 错源转发 37.6% [32.8,42.6] > PRF 低位 3.9% [2.4,6.3]
  - **DUE 带**：ExMon 100% > RAT map_bitflip 95.8% > FreeList mark_free 72–77% > RAT f5 59.7% > Decode 24.1% > LSQFwd byte_flip 27.6%
  - **零风险带**（本 workload 族，上界 ~1%）：取指（L1I opcode/rn 臂 0%）、L2/DRAM 后备（0%）、执行/IQ 唤醒/BPU/RAS/Decode 主部、Mem addr_map_sub
- **保护投资排序**（occupancy 加权，§4.2 表）：l1d 5.46% > l1d_fwd 5.09% > lsq_fwd 4.45%（HIGH 三兄弟）>> physreg 0.33%（MED）。排序对加权方案鲁棒（未加权同序）。

## 2. §4.2 三类交付物

### 2.1 DFT 测试向量（对芯片厂）

| 向量 | workload | 触发条件 | 健康核预期 | 次品核签名 |
|---|---|---|---|---|
| 数据通路筛选 | l1d_reduce | 工作集驻留 L1D + load 密集 | checksum = f44d2b9cd4a173cd | 任意单字节错（97.7% 概率 checksum 不符） |
| 转发路径筛选 | fwd_checksum_kernel | store→load 转发密集 | ac70ef3a46fd0825 | 错源数据（37.6% SDC；位谱=整字替换非位翻转） |
| rename 一致性 | cholesky | O3 满窗口 | 37621bc0a633976f | rename-inconsistency panic（RAT 族 60–96% DUE） |
| FP 路径回归 | gemm_float | FP 稠密 | golden | 单 bit XOR 全 Masked——**不推荐**做筛选向量（0% 灵敏度） |

method1 已证明 libc-only MRU 可作量产筛选；上述向量的"预期 vs 签名"列直接供产线使用。

### 2.2 保护投资排序（若只能给 N 个结构加保护）

| rank | 结构 | P_SDC | 机理 | 保护建议 |
|---|---|---|---|---|
| 1 | **L1D 数据阵列** | 97.7% | A（无保护基线）→ +SECDED 后 0% | **数据级 ECC 有效**——单 bit 全纠 |
| 2 | **L1D fill→PRF 通路**（post-check） | 90.9% | **D（ECC 校验后盲区）** | **ECC 不覆盖**——需通路级 parity/重取（check-after-path） |
| 3 | **LSQ 转发源选择** | 37.6% | A（错源=合法域整字错） | 转发源 age/ID 校验 > ECC（形态定律：整字错源比位翻转危险 8 倍） |
| 4 | PRF | 3.9%（低位窗） | A | 低位段（bit0-1）parity 可覆盖 SDC 窗；高位错必崩（DUE 可检） |
| — | 取指通路（L1I） | 0% | 自掩蔽 | **无需数据级 ECC**（错误指令 squash/非法崩溃） |
| — | L2/DRAM 后备 | 0% | 掩蔽梯度 | 对缓存驻留 workload 是沉没冗余 |

**三条横断定律**（跨单元）：
1. **合法域内错误是 SDC 核心形态**——错值全程合法（错源整字/活页 pfn/低位偏移）才静默传播；域外错必崩或自愈。
2. **故障形态 > 故障位置**——同单元同位置，错源整字 vs 单 bit 差 8 倍 SDC。
3. **单元 × 形态 × workload 三维决定结局**——F5 错源 madd 100% DUE vs cholesky Masked；X3 cholesky 92.7% DUE vs reg_chain 100% SDC。

### 2.3 位谱指纹库

- 已有：PRF 位段指纹（X3 边界 bit1/bit2 无过渡带；索引/指针/路径外三画像）；LSQ byte_lane_skew rol1/rol6（core179 D1 签名复现，H5 93% 检出）。
- 待补：method3 七类转发的 sign/exp/mantissa 位谱对照（FS 侧 method2 三根因跑批后）。

### 2.4 电压/相位敏感性

- F6 wake_phase 曲线已测：madd_chain offset {1,2,4,8} 全 100% DUE 平顶、cholesky 3–8% DUE 平顶——**wake_phase 代理不捕获 method3 相位签名**（E3 边界：method3 相位在 LSU 转发时序，不在调度唤醒相位）。相位敏感性数据需 LSQFwd 侧转发相位偏移（未实现，见 §4 待办）。

## 3. §4.3 诚实边界（报告必须随附）

1. **代理模型**：gem5 v25.1 O3 是 V110 的行为代理（E3）——绝对值不可直接外推，趋势与相对排序是结论等级。C2 参数 = "Kunpeng-informed proxy"。
2. **单机执行**：全部 formal 在 cpu179（已知故障机）上跑；**第二台健康机复现（S6）未做**——所有数字的可信度等级以此为条件。
3. **workload 覆盖**：SE 侧 6 个定向 kernel 族；FS 侧为内核 boot 稳态（无 userspace 定向）。SDC 带结论对 workload 族敏感（X3 跨 workload 反转已证明）。
4. **FS oracle 限制**：fs_mode 分类 oracle = 内核存活——SDC 与 Masked 不可区分（TLB F5 活页 384/384 "Masked" 实为"0% Crash + 静默面未知"）。
5. **统计口径**：所有 P 为"该故障模型下单次注入的条件概率"，非产品 FIT；CI 为 Wilson 95%。
6. **工具正确性史**：本轮共修复 15+ 个工具 bug（comp_map 改道、采样偏差族、protection 行双计数、重入递归等）——每个已提交结论都经过伪影审计（findings.md 记录全部作废与修正）。

## 4. 未完成项（不阻塞报告主体，列为后续）

| 项 | 状态 | 阻塞 |
|---|---|---|
| method2 三根因签名对照 | 三臂注入器+O3 restore 全通，签名 pilot 待跑 | 需内核活跃消费 x10 的 workload |
| H7 PTW ECC 双臂 | 触发链 ✅，稳态全 Masked（原预期需 boot 期注入） | boot 期 checkpoint |
| LSQFwd 转发相位偏移（真 method3 相位） | 未实现 | LSQ 转发决策时序 hook |
| 位谱指纹库 method3 部分 | 未跑 | 同 method2 |
| S4 系统级（L3/NoC/HCCS） | pilot 可触发 | 设计文档本就后置 |
| 健康机复现 S6 | 未做 | 第二台机器 |
