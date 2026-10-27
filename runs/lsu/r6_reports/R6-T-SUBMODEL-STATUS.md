# T 单元复合模型子模型状态表（初始版，基于只读重验）

状态取值：NOT_IMPLEMENTED / IMPLEMENTED_NOT_ROUTED / ROUTED_NOT_RUN / CANARY_PASS / COMPLETE_3_OF_3 / BLOCKED / REVIEW_REQUIRED

> 说明：`静态实现` 来自当前源码与二进制字符串（**仅作静态证据，不等于动态覆盖**）；
> `动态注入/激活/完整链` 三列在 canary 运行前一律为 `ROUTED_NOT_RUN`，**不得**以字符串存在冒充。

| RunID | 子模型 | 静态实现 | 路由可选 | 动态注入 | 激活 | 完整链/containment | 状态 |
|---|---|---|---|---|---|---|---|
| T05-F0-W4 | valid_clear | 是 | 已验 | 已运行（injected=1） | **未激活（activated=0）** | L2 containment（admitted） | **CANARY_FAIL_NO_ACTIVATION** |
| T05-F0-W4 | valid_set | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T05-F0-W4 | global_flip | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T05-F0-W4 | asid_subst | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T05-F2-W4 | （同上四项） | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T06-F0-W4 | perm_subst | 是 | 已验 | 已运行（injected=1） | **未激活（activated=0）** | L2 containment（admitted） | **CANARY_FAIL_NO_ACTIVATION** |
| T06-F0-W4 | memtype_subst | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T06-F0-W4 | pagesize_subst | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T06-F2-W4 | （同上三项） | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T07-F0-W4 | false_hit | 是 | 已验 | 已运行（injected=1） | activated=1（计数矛盾） | 开放 L2 / Timeout，admitted=False | **CANARY_FAIL_TIMEOUT_OPEN_CHAIN** |
| T07-F0-W4 | double_hit | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T07-F0-W4 | wrong_way | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T07-F4-W4 | （同上三项） | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T08-F0-W4 | T08-a walk_pairing | 是 | 已验 | 已运行（walk_id=703） | 已激活（activated=1） | L2 containment（admitted/certified） | **CANARY_PASS (T08-a only)** |
| T08-F0-W4 | T08-b walk_fill_dup | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T08-F0-W4 | T08-c walk_done_early | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T08-F0-W4 | T08-d walk_stale_result | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T08-F4-W4 | （同上四项） | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T08-F0-W9 | （同上四项） | 是 | 不可（workload） | — | — | — | **BLOCKED_WORKLOAD_GAP** |
| T08-F4-W9 | （同上四项） | 是 | 不可（workload） | — | — | — | **BLOCKED_WORKLOAD_GAP** |
| T10-F0-W4 | （单一模型，无子模型） | 是 | 是 | 已运行 | 已激活（1） | full L5（admitted/certified） | **CANARY_PASS** |
| T10-F1-W4 | 同上 | 是 | 是 | 已运行 | 已激活（1） | full L5（admitted/certified） | **CANARY_PASS** |
| T10-F2-W4 | 同上 | 是 | 是 | 已运行 | 已激活（5） | full L5（admitted/certified） | **CANARY_PASS** |

## 口径（按裁决）

- 一次 canary 只证明**被选中的那个子模型**，不得外推。
- T08-a 单独通过 ⇒ T08-F0/F4-W4 记 **PARTIAL_SUBMODEL_PROVEN**，不得记 COMPLETE_3_OF_3。
- 四个子模型固定：T08-a walk_pairing / T08-b walk_fill_dup / T08-c walk_done_early / T08-d walk_stale_result。
- 三个 seed 若无法诚实覆盖四个子模型，必须报告规格覆盖矛盾，不得遗漏或冒充。


## 2026-10-27 代表 canary 实测更新

- 完整逐格证据与 manifest：`R6-V3-CANARY-STATUS.{md,json}`；每格 `R6-V3-CANARY-<RunID>-seed1.json`。
- T10-F0/F1/F2-W4：PASS（真实注入 + 激活 + 完整 L5 链，admitted/certified，violations=[]）。
- T05-F0-W4 valid_clear：FAIL_NO_ACTIVATION（injected=1，activated=0；L2 containment 存在但未达该子模型激活口径）。
- T06-F0-W4 perm_subst：FAIL_NO_ACTIVATION（injected=1，activated=0；L2 containment）。
- T07-F0-W4 false_hit：FAIL_TIMEOUT_OPEN_CHAIN（injected=1；5400s Timeout；开放 L2，admitted=False）。
- T08-F0-W4 T08-a：PASS（仅 T08-a；walk_id=703；tlb_walk/tlb_refill shared walk_id，refill field=lost）。
- T08 其余子模型（walk_fill_dup / walk_done_early / walk_stale_result）仍无动态覆盖 ⇒ **T08 整体不是 COMPLETE，只记 PARTIAL_SUBMODEL_PROVEN**。
- T08-W9 仍 `BLOCKED_WORKLOAD_GAP`，本轮未运行。
- 本轮未补 seed2/seed3，未启动正式实验。
