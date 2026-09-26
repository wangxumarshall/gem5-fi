# 10 · LSU 试跑阶段（trial）结果记录

> 数据源：`runs/lsu/`（177 可跑格 × ≤5 seeds × 4 并发槽，2026-09-26）；
> 回填产物：`runs/lsu/07-expanded-matrix-backfilled.csv`（col26=试跑 / blocked 带原因）。
> **口径声明（05 r13）**：试跑 30 activated/格只用于发现注入器错误、全 Crash 或零激活单元，
> **不用于最终窄置信区间**——正式结论需筛查档 ≥385 activated/格（本文件所有数字均为试跑级）。

## 1. 网格完成度（337 格全部离开「待执行」——M5 诚实口径）

| 状态 | 格数 | 说明 |
|---|---|---|
| 试跑（数据） | **177** | 全部 SE 可跑格，L5 守恒逐格闭合 |
| blocked(fs-infra) | 108 | T 系（TLB::lookup SE 零调用，W1 ③）+ W1 MiBench/W4 TLB 负载格 |
| blocked(multicore-fs) | — | 含于上（W7 Litmus/W13 PARSEC 负载格） |
| blocked(spec-license) | — | 含于上（W11 SPEC 格） |
| deferred | 46 | S10/L04/C11/C12/C14/C15（notify-only 事件源，消费端未实现）+ A07/P06/O04/O09（无干净钩子） |
| 不适用(B0无保护) | 6 | S12/T09/C13/O08（09 §6.4，不填零） |
| **合计** | **337** | 待执行 **0** |

## 2. 试跑级结局谱（2624 activated，守恒闭合）

**Activated = 1583 Masked + 1041 Crash + 0 SDC + 0 Timeout + 0 Detected/Contained**

| 单元族 | Masked | Crash | SDC | activated | 主导结局 |
|---|---|---|---|---|---|
| A（AGU） | 40 | 242 | 0 | 282 | **Crash 86%**——EA 位翻转→未映射页（W4 预期一致） |
| S（SQ） | 100 | 733 | 0 | 833 | **Crash 88%**——S03-F5 stuck-lane 两格贡献 725（永久 lane 掩码→每次转发腐蚀→最终非法访问） |
| L（LQ） | 37 | 0 | 0 | 37 | **Masked 100%**——TC'23 LQ SDC=0 锚点复现 ✓ |
| C（L1D-Cache） | 144 | 36 | 0 | 180 | Masked 80%——行/tag/valid/dirty 单 bit 注入被回写/覆盖吸收 |
| P（预取器） | 1262 | 30 | 0 | 1292 | **Masked 98%**——P01-P03 负对照全域成立（预取错误不改架构结果，README §5.4 判据过） |

**核心试跑结论（方向性，样本量见 §4 局限）**：
1. **SE 可测格 trial 级零 SDC**（0/2624）——TC'23 的「commit 前依赖检查拦截随机翻转」在 LSU 全单元族上推广成立（试跑级上界）。
2. **结局谱按单元分化**：AGU/SQ 地址通路 → Crash 主导；LQ/Cache/预取 → Masked 主导。**SDC 风险（若有）不在 SE 单 bit 档**——结构化换值模式（S04 合法换值等）的对照格多为 F5/F6 档，本次试跑已跑但激活稀疏（见 §3）。
3. **F5 stuck 模式是 Crash 集中带**（S03-F5 两格 725 Crash、A03-F5 两格 181 Crash）——持续故障远比单发翻转致命。

## 3. 试跑职责交付：异常格清单（05 r13——试跑就是为了发现这些）

**零激活格（53/177）**——两类成因，均如实记录：
- **F1/F2/F3 事件间隔 > eligible 流总量**（注入器正确、档位与负载事件流不匹配）：如 P02-F3-W8（F3 均值 10K 事件 > prefetch_stride 的 ~131 eligible）、S13-F2-W5（SQ 事件流 < F2 均值 100K）。这些格需要更长的负载或降档——**不是注入器错误**。
- **F6 指定事件在负载中未出现**：如 C08-F6-W6（CAS-success 事件在 cache_dirtyevict 中不发生）。需要事件匹配的负载——同上，非工具错误。

**工具错误（本轮试跑实际抓到并修复的，全部已提交）**：
- golden 手误（prefetch_stride 18 字符错值 → P01 假 SDC）——28e405cc 修复+重跑 Masked 2/2
- cache 族 activated 记账缺失（分类器 fallback 不认 CHAOSCache 日志格式 → 48 格 activated=0）——6e0dcd52 修复+48 格重跑
- A03 seed 旗标吞噬——35a57ab3 修复+2 格重跑

## 4. 局限与下一步

- 每格 ≤5 seeds、30-activated 目标多数未达（stop_reason=seed-cap 如实记录）——**CI 必然宽**，本文件不给出区间结论
- 下一步 = 筛查档（≥385 activated/格）：`python3 tools/lsu_campaign.py --phase screening --screening-target 385 --max-seeds-per-cell <N>`
- F1/F2/F3 零激活格的处置需人工裁量（降档/换负载/标 blocked）——不静默跳过
- 结构化 vs 随机（三问 Q3）的配对对照在筛查档数据齐后由 `tools/lsu_meta_analysis.py` 出（试跑级见 11-meta-analysis.md 的方向性记录）
