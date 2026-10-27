# T 单元复合模型子模型状态表（初始版，基于只读重验）

状态取值：NOT_IMPLEMENTED / IMPLEMENTED_NOT_ROUTED / ROUTED_NOT_RUN / CANARY_PASS / COMPLETE_3_OF_3 / BLOCKED / REVIEW_REQUIRED

> 说明：`静态实现` 来自当前源码与二进制字符串（**仅作静态证据，不等于动态覆盖**）；
> `动态注入/激活/完整链` 三列在 canary 运行前一律为 `ROUTED_NOT_RUN`，**不得**以字符串存在冒充。

| RunID | 子模型 | 静态实现 | 路由可选 | 动态注入 | 激活 | 完整链/containment | 状态 |
|---|---|---|---|---|---|---|---|
| T05-F0-W4 | valid_clear | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T05-F0-W4 | valid_set | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T05-F0-W4 | global_flip | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T05-F0-W4 | asid_subst | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T05-F2-W4 | （同上四项） | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T06-F0-W4 | perm_subst | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T06-F0-W4 | memtype_subst | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T06-F0-W4 | pagesize_subst | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T06-F2-W4 | （同上三项） | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T07-F0-W4 | false_hit | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T07-F0-W4 | double_hit | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T07-F0-W4 | wrong_way | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T07-F4-W4 | （同上三项） | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T08-F0-W4 | T08-a walk_pairing | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T08-F0-W4 | T08-b walk_fill_dup | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T08-F0-W4 | T08-c walk_done_early | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T08-F0-W4 | T08-d walk_stale_result | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T08-F4-W4 | （同上四项） | 是 | 待验 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T08-F0-W9 | （同上四项） | 是 | 不可（workload） | — | — | — | **BLOCKED_WORKLOAD_GAP** |
| T08-F4-W9 | （同上四项） | 是 | 不可（workload） | — | — | — | **BLOCKED_WORKLOAD_GAP** |
| T10-F0-W4 | （单一模型，无子模型） | 是 | 是 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T10-F1-W4 | 同上 | 是 | 是 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |
| T10-F2-W4 | 同上 | 是 | 是 | 未运行 | 未运行 | 未运行 | ROUTED_NOT_RUN |

## 口径（按裁决）

- 一次 canary 只证明**被选中的那个子模型**，不得外推。
- T08-a 单独通过 ⇒ T08-F0/F4-W4 记 **PARTIAL_SUBMODEL_PROVEN**，不得记 COMPLETE_3_OF_3。
- 四个子模型固定：T08-a walk_pairing / T08-b walk_fill_dup / T08-c walk_done_early / T08-d walk_stale_result。
- 三个 seed 若无法诚实覆盖四个子模型，必须报告规格覆盖矛盾，不得遗漏或冒充。
