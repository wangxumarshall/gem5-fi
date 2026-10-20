# 49 项 MODE-UNIMPL 实现范围与顺序（未完成项如实登记）

> 用户指令（第二轮）第 3 条："继续实现 49 个 MODE-UNIMPL RunID"。
> **本次会话未实现其中任何一项**——本文件是实测得出的范围界定与实施顺序，
> 供下一步按 one-patch-per-unit 逐项落地。**不得把本文件当作完成证据。**

## 实测结论：49 项 = 9 个模型 × 各自"事件源/模式"缺口

全部 9 个模型同时满足：① 在 `lsu_campaign.MODEL_BLOCKED` 中标注 `deferred(...)`；
② **不在 `MODEL_FLAGS`**（即没有可运行的 route）；③ `configs/se/lsu_proxy.py` 中
**没有对应模式 flag**（已 grep 证实：无 c11 模式、无 mshr_busy/mshr_occupancy flag）。

| 模型 | RunID 数 | 阻塞短语 | 要做的事 | 规模 |
|---|---|---|---|---|
| C11 | 8 | consumer-side: MSHR merge event source only | MSHR merge **腐蚀注入模式**（合并目标地址翻位） | 中 |
| C12 | 6 | consumer-side: fill-timing event source only | fill 时序偏移注入模式 | 中 |
| C14 | 2 | consumer-side: MSHR busy event source only | MSHR busy 注入点 + busy 观测 | 中 |
| C15 | 6 | consumer-side: MSHR occupancy event source only | MSHR occupancy/entry 选择注入 | 大 |
| S10 | 6 | consumer-side: StoreSet SSID corruption event source only | StoreSet SSID 事件源 + 注入（gem5 无现成 StoreSet） | 大 |
| P06 | 6 | no clean hook: prefetch-as-demand marking | 预取属性标记钩子 + 注入 | 中 |
| L04 | 6 | consumer-side: response-pairing event source only | 响应配对的**可注入且可追踪**映射 | 中 |
| A07 | 6 | R4: no clean hook | AGU clean ready/握手钩子 | 大 |
| T08 | 3 | mode unimplemented: walk pairing | FS 页表遍历 walk/fill 配对（FS-only） | 大 |

## 逐项落地模板（每项 **一个 commit**，遵守 one-patch-per-unit）

1. 注入端：在对应注入器（C 系 `CHAOSCache`/S 系 `CHAOSLSQFwd`/P 系 `CHAOSPrefetch`/
   A 系 `CHAOSAddrPath`/T 系 `CHAOSArmTLB`）新增该子模型 Mode + 注入逻辑。
2. 观测端：在本轮已就位的 H0 统一流上补该子模型**特有节点**（`lsu_prop_fields.KIND_LAYER`
   + `REQUIRED_FIELDS`），必要时在 `CHAOSPropagation` 加注册表。
3. 路由：`configs/se/lsu_proxy.py` 增 flag/choices → `lsu_campaign.MODEL_FLAGS` 增
   `(family, extra)` → 从 `MODEL_BLOCKED` 删除该模型（**只有断言可跑才删**）。
4. 测试：`tests/test_lsu_hook_*.py` 契约（层/必录字段）+ 台账（`test_lsu_coverage_matrix`
   的节点集）同步。
5. 真机验证：该模型一个 RunID 真实运行，**先证注入日志非空**，再 `lsu_chain_check.py`
   逐边记录；缺事件报 Unknown。
6. 覆盖矩阵重生成 + 证据文件更新。

## 建议实施顺序（低成本高收益优先）

1. **C11（8 项，最多）**：本轮已补 `mshr_merge`/`mshr_fill`/`mshr_free` 事件源与真 `mshr_id`——
   其"只有事件源"的阻塞前提**已部分消除**，先做它性价比最高。
2. **C12（6）**：`mshr_fill`+`fill_id` 已在位，同理。
3. **L04（6）**：`resp`/`lq_complete` 已在位，只需补配对键与注入点。
4. **P06（6）**：P 系注入器与 pf_* 链已完备，只缺属性标记钩子。
5. **C14/C15（8）**：需 MSHR busy/occupancy 观测。
6. **S10 / A07 / T08（15）**：需新事件源（StoreSet / AGU clean-ready / FS walk）——
   其中 **T08 属 FS-only**，与 77 项里的 FS 延期同批更合理。

## 与 77 项的关系（避免混淆）

- 49 项 MODE-UNIMPL = **本轨道可自行实现**（不需批准，需要工时）。
- 77 项（RULING 6 + LICENSE 12 + FS-MULTICORE 35 + FS-INFRA 24）= **需您裁决**，
  见 `blockers_for_approval.md`。
- 两者互斥且完备：126 = 49 + 77。
