# Markdown→实现覆盖矩阵（MDSPEC Phase B）

- 总数：325（RunID 唯一，表7∩表9 集合相等——B1 已证）
- **PASS=199 / PARTIAL=0 / BLOCKED=126**
- 钩子族注册表：{"H0_prop_fields": true, "H1_lsq_unified": true, "H2_tlb_trace": true, "H3_sq_trace": true, "H4_cache_ext": true, "H5_prefetch_trace": true, "H6_atomic_trace": true, "H7_lq_trace": true}

| RunID | 模型 | 单元 | 频率 | 状态 | 原因 |
|---|---|---|---|---|---|
| A01-F0-W3 | A01 | AGU | F0 | PASS |  |
| A01-F0-W9 | A01 | AGU | F0 | PASS |  |
| A01-F1-W3 | A01 | AGU | F1 | PASS |  |
| A01-F1-W9 | A01 | AGU | F1 | PASS |  |
| A01-F2-W3 | A01 | AGU | F2 | PASS |  |
| A01-F2-W9 | A01 | AGU | F2 | PASS |  |
| A02-F0-W3 | A02 | AGU | F0 | PASS |  |
| A02-F0-W9 | A02 | AGU | F0 | PASS |  |
| A02-F2-W3 | A02 | AGU | F2 | PASS |  |
| A02-F2-W9 | A02 | AGU | F2 | PASS |  |
| A03-F5-W3 | A03 | AGU | F5 | PASS |  |
| A03-F5-W10 | A03 | AGU | F5 | PASS |  |
| A04-F0-W3 | A04 | AGU | F0 | PASS |  |
| A04-F0-W0 | A04 | AGU | F0 | PASS |  |
| A04-F2-W3 | A04 | AGU | F2 | PASS |  |
| A04-F2-W0 | A04 | AGU | F2 | PASS |  |
| A04-F6-W3 | A04 | AGU | F6 | PASS |  |
| A04-F6-W0 | A04 | AGU | F6 | PASS |  |
| A05-F0-W3 | A05 | AGU | F0 | PASS |  |
| A05-F2-W3 | A05 | AGU | F2 | PASS |  |
| A05-F6-W3 | A05 | AGU | F6 | PASS |  |
| A06-F0-W3 | A06 | AGU | F0 | BLOCKED | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC § |
| A06-F0-W5 | A06 | AGU | F0 | BLOCKED | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC § |
| A06-F2-W3 | A06 | AGU | F2 | BLOCKED | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC § |
| A06-F2-W5 | A06 | AGU | F2 | BLOCKED | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC § |
| A06-F6-W3 | A06 | AGU | F6 | BLOCKED | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC § |
| A06-F6-W5 | A06 | AGU | F6 | BLOCKED | campaign:BLOCKED(load-side fixed-width completion contract + byte-enable pending; store-only path implemented — MDSPEC § |
| A07-F0-W3 | A07 | AGU | F0 | BLOCKED | campaign:deferred(R4: no clean hook); spec:需新增（当前阻塞：无clean ready/握手注入hook） |
| A07-F0-W5 | A07 | AGU | F0 | BLOCKED | campaign:deferred(R4: no clean hook); spec:需新增（当前阻塞：无clean ready/握手注入hook） |
| A07-F4-W3 | A07 | AGU | F4 | BLOCKED | campaign:deferred(R4: no clean hook); spec:需新增（当前阻塞：无clean ready/握手注入hook） |
| A07-F4-W5 | A07 | AGU | F4 | BLOCKED | campaign:deferred(R4: no clean hook); spec:需新增（当前阻塞：无clean ready/握手注入hook） |
| A07-F6-W3 | A07 | AGU | F6 | BLOCKED | campaign:deferred(R4: no clean hook); spec:需新增（当前阻塞：无clean ready/握手注入hook） |
| A07-F6-W5 | A07 | AGU | F6 | BLOCKED | campaign:deferred(R4: no clean hook); spec:需新增（当前阻塞：无clean ready/握手注入hook） |
| A08-F0-W3 | A08 | AGU | F0 | PASS |  |
| A08-F0-W5 | A08 | AGU | F0 | PASS |  |
| A08-F2-W3 | A08 | AGU | F2 | PASS |  |
| A08-F2-W5 | A08 | AGU | F2 | PASS |  |
| A08-F6-W3 | A08 | AGU | F6 | PASS |  |
| A08-F6-W5 | A08 | AGU | F6 | PASS |  |
| T01-F0-W1 | T01 | L1d-TLB | F0 | PASS |  |
| T01-F0-W4 | T01 | L1d-TLB | F0 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T01-F1-W1 | T01 | L1d-TLB | F1 | PASS |  |
| T01-F1-W4 | T01 | L1d-TLB | F1 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T01-F2-W1 | T01 | L1d-TLB | F2 | PASS |  |
| T01-F2-W4 | T01 | L1d-TLB | F2 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T02-F0-W1 | T02 | L1d-TLB | F0 | PASS |  |
| T02-F0-W4 | T02 | L1d-TLB | F0 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T02-F2-W1 | T02 | L1d-TLB | F2 | PASS |  |
| T02-F2-W4 | T02 | L1d-TLB | F2 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T03-F5-W4 | T03 | L1d-TLB | F5 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T03-F5-W9 | T03 | L1d-TLB | F5 | PASS |  |
| T04-F0-W4 | T04 | L1d-TLB | F0 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T04-F2-W4 | T04 | L1d-TLB | F2 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T04-F6-W4 | T04 | L1d-TLB | F6 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T05-F0-W4 | T05 | L1d-TLB | F0 | BLOCKED | campaign:deferred(mode unimplemented: valid/global/ASID state); spec:需新增（当前阻塞：valid/global/ASID模式未实现）; workload:规格负载名无 S |
| T05-F2-W4 | T05 | L1d-TLB | F2 | BLOCKED | campaign:deferred(mode unimplemented: valid/global/ASID state); spec:需新增（当前阻塞：valid/global/ASID模式未实现）; workload:规格负载名无 S |
| T05-F6-W4 | T05 | L1d-TLB | F6 | BLOCKED | campaign:deferred(mode unimplemented: valid/global/ASID state); spec:需新增（当前阻塞：valid/global/ASID模式未实现）; workload:规格负载名无 S |
| T06-F0-W4 | T06 | L1d-TLB | F0 | BLOCKED | campaign:deferred(mode unimplemented: permission legal-substitution); spec:需新增（当前阻塞：permission/attribute合法替换未实现）; worklo |
| T06-F2-W4 | T06 | L1d-TLB | F2 | BLOCKED | campaign:deferred(mode unimplemented: permission legal-substitution); spec:需新增（当前阻塞：permission/attribute合法替换未实现）; worklo |
| T06-F6-W4 | T06 | L1d-TLB | F6 | BLOCKED | campaign:deferred(mode unimplemented: permission legal-substitution); spec:需新增（当前阻塞：permission/attribute合法替换未实现）; worklo |
| T07-F0-W4 | T07 | L1d-TLB | F0 | BLOCKED | campaign:deferred(mode unimplemented: hit fabrication/way select); spec:需新增（当前阻塞：hit fabrication/way select未实现）; workloa |
| T07-F4-W4 | T07 | L1d-TLB | F4 | BLOCKED | campaign:deferred(mode unimplemented: hit fabrication/way select); spec:需新增（当前阻塞：hit fabrication/way select未实现）; workloa |
| T07-F6-W4 | T07 | L1d-TLB | F6 | BLOCKED | campaign:deferred(mode unimplemented: hit fabrication/way select); spec:需新增（当前阻塞：hit fabrication/way select未实现）; workloa |
| T08-F0-W4 | T08 | L1d-TLB | F0 | BLOCKED | campaign:deferred(mode unimplemented: walk pairing); spec:需新增（当前阻塞：walk/fill pairing未实现）; workload:规格负载名无 SE 载体映射（WL_BIN |
| T08-F0-W9 | T08 | L1d-TLB | F0 | BLOCKED | campaign:deferred(mode unimplemented: walk pairing); spec:需新增（当前阻塞：walk/fill pairing未实现） |
| T08-F4-W4 | T08 | L1d-TLB | F4 | BLOCKED | campaign:deferred(mode unimplemented: walk pairing); spec:需新增（当前阻塞：walk/fill pairing未实现）; workload:规格负载名无 SE 载体映射（WL_BIN |
| T08-F4-W9 | T08 | L1d-TLB | F4 | BLOCKED | campaign:deferred(mode unimplemented: walk pairing); spec:需新增（当前阻塞：walk/fill pairing未实现） |
| T08-F6-W4 | T08 | L1d-TLB | F6 | BLOCKED | campaign:deferred(mode unimplemented: walk pairing); spec:需新增（当前阻塞：walk/fill pairing未实现）; workload:规格负载名无 SE 载体映射（WL_BIN |
| T08-F6-W9 | T08 | L1d-TLB | F6 | BLOCKED | campaign:deferred(mode unimplemented: walk pairing); spec:需新增（当前阻塞：walk/fill pairing未实现） |
| S01-F0-W1 | S01 | Store Queue | F0 | PASS |  |
| S01-F0-W5 | S01 | Store Queue | F0 | PASS |  |
| S01-F1-W1 | S01 | Store Queue | F1 | PASS |  |
| S01-F1-W5 | S01 | Store Queue | F1 | PASS |  |
| S01-F2-W1 | S01 | Store Queue | F2 | PASS |  |
| S01-F2-W5 | S01 | Store Queue | F2 | PASS |  |
| S02-F0-W5 | S02 | Store Queue | F0 | PASS |  |
| S02-F0-W1 | S02 | Store Queue | F0 | PASS |  |
| S02-F2-W5 | S02 | Store Queue | F2 | PASS |  |
| S02-F2-W1 | S02 | Store Queue | F2 | PASS |  |
| S03-F5-W5 | S03 | Store Queue | F5 | PASS |  |
| S03-F5-W10 | S03 | Store Queue | F5 | PASS |  |
| S04-F0-W5 | S04 | Store Queue | F0 | PASS |  |
| S04-F0-W0 | S04 | Store Queue | F0 | PASS |  |
| S04-F2-W5 | S04 | Store Queue | F2 | PASS |  |
| S04-F2-W0 | S04 | Store Queue | F2 | PASS |  |
| S04-F6-W5 | S04 | Store Queue | F6 | PASS |  |
| S04-F6-W0 | S04 | Store Queue | F6 | PASS |  |
| S05-F0-W5 | S05 | Store Queue | F0 | PASS |  |
| S05-F0-W3 | S05 | Store Queue | F0 | PASS |  |
| S05-F2-W5 | S05 | Store Queue | F2 | PASS |  |
| S05-F2-W3 | S05 | Store Queue | F2 | PASS |  |
| S05-F6-W5 | S05 | Store Queue | F6 | PASS |  |
| S05-F6-W3 | S05 | Store Queue | F6 | PASS |  |
| S06-F0-W5 | S06 | Store Queue | F0 | PASS |  |
| S06-F0-W6 | S06 | Store Queue | F0 | PASS |  |
| S06-F2-W5 | S06 | Store Queue | F2 | PASS |  |
| S06-F2-W6 | S06 | Store Queue | F2 | PASS |  |
| S06-F6-W5 | S06 | Store Queue | F6 | PASS |  |
| S06-F6-W6 | S06 | Store Queue | F6 | PASS |  |
| S07-F0-W5 | S07 | Store Queue | F0 | PASS |  |
| S07-F4-W5 | S07 | Store Queue | F4 | PASS |  |
| S07-F6-W5 | S07 | Store Queue | F6 | PASS |  |
| S08-F0-W5 | S08 | Store Queue | F0 | PASS |  |
| S08-F2-W5 | S08 | Store Queue | F2 | PASS |  |
| S08-F6-W5 | S08 | Store Queue | F6 | PASS |  |
| S09-F0-W5 | S09 | Store Queue | F0 | PASS |  |
| S09-F2-W5 | S09 | Store Queue | F2 | PASS |  |
| S09-F6-W5 | S09 | Store Queue | F6 | PASS |  |
| S10-F0-W5 | S10 | Store Queue | F0 | BLOCKED | campaign:deferred(consumer-side: StoreSet SSID corruption event source only); spec:需新增（当前阻塞：只有StoreSet事件源，无consumer-side |
| S10-F0-W9 | S10 | Store Queue | F0 | BLOCKED | campaign:deferred(consumer-side: StoreSet SSID corruption event source only); spec:需新增（当前阻塞：只有StoreSet事件源，无consumer-side |
| S10-F2-W5 | S10 | Store Queue | F2 | BLOCKED | campaign:deferred(consumer-side: StoreSet SSID corruption event source only); spec:需新增（当前阻塞：只有StoreSet事件源，无consumer-side |
| S10-F2-W9 | S10 | Store Queue | F2 | BLOCKED | campaign:deferred(consumer-side: StoreSet SSID corruption event source only); spec:需新增（当前阻塞：只有StoreSet事件源，无consumer-side |
| S10-F5-W5 | S10 | Store Queue | F5 | BLOCKED | campaign:deferred(consumer-side: StoreSet SSID corruption event source only); spec:需新增（当前阻塞：只有StoreSet事件源，无consumer-side |
| S10-F5-W9 | S10 | Store Queue | F5 | BLOCKED | campaign:deferred(consumer-side: StoreSet SSID corruption event source only); spec:需新增（当前阻塞：只有StoreSet事件源，无consumer-side |
| S11-F0-W5 | S11 | Store Queue | F0 | PASS |  |
| S11-F0-W6 | S11 | Store Queue | F0 | PASS |  |
| S11-F4-W5 | S11 | Store Queue | F4 | PASS |  |
| S11-F4-W6 | S11 | Store Queue | F4 | PASS |  |
| S11-F6-W5 | S11 | Store Queue | F6 | PASS |  |
| S11-F6-W6 | S11 | Store Queue | F6 | PASS |  |
| C01-F0-W1 | C01 | L1d-Cache | F0 | PASS |  |
| C01-F0-W6 | C01 | L1d-Cache | F0 | PASS |  |
| C01-F1-W1 | C01 | L1d-Cache | F1 | PASS |  |
| C01-F1-W6 | C01 | L1d-Cache | F1 | PASS |  |
| C01-F2-W1 | C01 | L1d-Cache | F2 | PASS |  |
| C01-F2-W6 | C01 | L1d-Cache | F2 | PASS |  |
| C02-F0-W6 | C02 | L1d-Cache | F0 | PASS |  |
| C02-F0-W1 | C02 | L1d-Cache | F0 | PASS |  |
| C02-F2-W6 | C02 | L1d-Cache | F2 | PASS |  |
| C02-F2-W1 | C02 | L1d-Cache | F2 | PASS |  |
| C03-F5-W6 | C03 | L1d-Cache | F5 | PASS |  |
| C03-F5-W10 | C03 | L1d-Cache | F5 | PASS |  |
| C04-F0-W1 | C04 | L1d-Cache | F0 | PASS |  |
| C04-F0-W6 | C04 | L1d-Cache | F0 | PASS |  |
| C04-F1-W1 | C04 | L1d-Cache | F1 | PASS |  |
| C04-F1-W6 | C04 | L1d-Cache | F1 | PASS |  |
| C04-F2-W1 | C04 | L1d-Cache | F2 | PASS |  |
| C04-F2-W6 | C04 | L1d-Cache | F2 | PASS |  |
| C05-F0-W6 | C05 | L1d-Cache | F0 | PASS |  |
| C05-F2-W6 | C05 | L1d-Cache | F2 | PASS |  |
| C05-F6-W6 | C05 | L1d-Cache | F6 | PASS |  |
| C06-F0-W6 | C06 | L1d-Cache | F0 | PASS |  |
| C06-F2-W6 | C06 | L1d-Cache | F2 | PASS |  |
| C06-F5-W6 | C06 | L1d-Cache | F5 | PASS |  |
| C07-F0-W6 | C07 | L1d-Cache | F0 | PASS |  |
| C07-F2-W6 | C07 | L1d-Cache | F2 | PASS |  |
| C07-F5-W6 | C07 | L1d-Cache | F5 | PASS |  |
| C07-F6-W6 | C07 | L1d-Cache | F6 | PASS |  |
| C08-F0-W6 | C08 | L1d-Cache | F0 | PASS |  |
| C08-F0-W7 | C08 | L1d-Cache | F0 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| C08-F2-W6 | C08 | L1d-Cache | F2 | PASS |  |
| C08-F2-W7 | C08 | L1d-Cache | F2 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| C08-F5-W6 | C08 | L1d-Cache | F5 | PASS |  |
| C08-F5-W7 | C08 | L1d-Cache | F5 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| C08-F6-W6 | C08 | L1d-Cache | F6 | PASS |  |
| C08-F6-W7 | C08 | L1d-Cache | F6 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| C09-F0-W6 | C09 | L1d-Cache | F0 | PASS |  |
| C09-F0-W10 | C09 | L1d-Cache | F0 | PASS |  |
| C09-F2-W6 | C09 | L1d-Cache | F2 | PASS |  |
| C09-F2-W10 | C09 | L1d-Cache | F2 | PASS |  |
| C09-F6-W6 | C09 | L1d-Cache | F6 | PASS |  |
| C09-F6-W10 | C09 | L1d-Cache | F6 | PASS |  |
| C10-F0-W6 | C10 | L1d-Cache | F0 | PASS |  |
| C10-F0-W10 | C10 | L1d-Cache | F0 | PASS |  |
| C10-F3-W6 | C10 | L1d-Cache | F3 | PASS |  |
| C10-F3-W10 | C10 | L1d-Cache | F3 | PASS |  |
| C10-F5-W6 | C10 | L1d-Cache | F5 | PASS |  |
| C10-F5-W10 | C10 | L1d-Cache | F5 | PASS |  |
| C11-F0-W6 | C11 | L1d-Cache | F0 | BLOCKED | campaign:deferred(consumer-side: MSHR merge event source only); spec:需新增（当前阻塞：只有MSHR merge事件源） |
| C11-F0-W10 | C11 | L1d-Cache | F0 | BLOCKED | campaign:deferred(consumer-side: MSHR merge event source only); spec:需新增（当前阻塞：只有MSHR merge事件源） |
| C11-F2-W6 | C11 | L1d-Cache | F2 | BLOCKED | campaign:deferred(consumer-side: MSHR merge event source only); spec:需新增（当前阻塞：只有MSHR merge事件源） |
| C11-F2-W10 | C11 | L1d-Cache | F2 | BLOCKED | campaign:deferred(consumer-side: MSHR merge event source only); spec:需新增（当前阻塞：只有MSHR merge事件源） |
| C11-F4-W6 | C11 | L1d-Cache | F4 | BLOCKED | campaign:deferred(consumer-side: MSHR merge event source only); spec:需新增（当前阻塞：只有MSHR merge事件源） |
| C11-F4-W10 | C11 | L1d-Cache | F4 | BLOCKED | campaign:deferred(consumer-side: MSHR merge event source only); spec:需新增（当前阻塞：只有MSHR merge事件源） |
| C11-F6-W6 | C11 | L1d-Cache | F6 | BLOCKED | campaign:deferred(consumer-side: MSHR merge event source only); spec:需新增（当前阻塞：只有MSHR merge事件源） |
| C11-F6-W10 | C11 | L1d-Cache | F6 | BLOCKED | campaign:deferred(consumer-side: MSHR merge event source only); spec:需新增（当前阻塞：只有MSHR merge事件源） |
| C12-F0-W6 | C12 | L1d-Cache | F0 | BLOCKED | campaign:deferred(consumer-side: fill-timing event source only); spec:需新增（当前阻塞：只有fill timing事件源） |
| C12-F0-W10 | C12 | L1d-Cache | F0 | BLOCKED | campaign:deferred(consumer-side: fill-timing event source only); spec:需新增（当前阻塞：只有fill timing事件源） |
| C12-F4-W6 | C12 | L1d-Cache | F4 | BLOCKED | campaign:deferred(consumer-side: fill-timing event source only); spec:需新增（当前阻塞：只有fill timing事件源） |
| C12-F4-W10 | C12 | L1d-Cache | F4 | BLOCKED | campaign:deferred(consumer-side: fill-timing event source only); spec:需新增（当前阻塞：只有fill timing事件源） |
| C12-F6-W6 | C12 | L1d-Cache | F6 | BLOCKED | campaign:deferred(consumer-side: fill-timing event source only); spec:需新增（当前阻塞：只有fill timing事件源） |
| C12-F6-W10 | C12 | L1d-Cache | F6 | BLOCKED | campaign:deferred(consumer-side: fill-timing event source only); spec:需新增（当前阻塞：只有fill timing事件源） |
| O01-F0-W7 | O01 | 原子与同步 | F0 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| O01-F2-W7 | O01 | 原子与同步 | F2 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| O01-F6-W7 | O01 | 原子与同步 | F6 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| O02-F0-W7 | O02 | 原子与同步 | F0 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| O02-F2-W7 | O02 | 原子与同步 | F2 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| O02-F5-W7 | O02 | 原子与同步 | F5 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| O02-F6-W7 | O02 | 原子与同步 | F6 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| O03-F0-W7 | O03 | 原子与同步 | F0 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| O03-F2-W7 | O03 | 原子与同步 | F2 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| O03-F6-W7 | O03 | 原子与同步 | F6 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| O04-F0-W7 | O04 | 原子与同步 | F0 | BLOCKED | campaign:deferred(RMW data path needs cache-side SwapResp hook); spec:需新增（当前阻塞：缺RMW数据/SwapResp hook）; workload:规格负载名无 SE |
| O04-F2-W7 | O04 | 原子与同步 | F2 | BLOCKED | campaign:deferred(RMW data path needs cache-side SwapResp hook); spec:需新增（当前阻塞：缺RMW数据/SwapResp hook）; workload:规格负载名无 SE |
| O04-F6-W7 | O04 | 原子与同步 | F6 | BLOCKED | campaign:deferred(RMW data path needs cache-side SwapResp hook); spec:需新增（当前阻塞：缺RMW数据/SwapResp hook）; workload:规格负载名无 SE |
| O05-F0-W7 | O05 | 原子与同步 | F0 | BLOCKED | campaign:blocked(multicore-fs: RMW ordering needs multi-core); spec:需新增（当前阻塞：需要多核FS的RMW请求/全局可见性）; workload:规格负载名无 SE 载体映 |
| O05-F4-W7 | O05 | 原子与同步 | F4 | BLOCKED | campaign:blocked(multicore-fs: RMW ordering needs multi-core); spec:需新增（当前阻塞：需要多核FS的RMW请求/全局可见性）; workload:规格负载名无 SE 载体映 |
| O05-F6-W7 | O05 | 原子与同步 | F6 | BLOCKED | campaign:blocked(multicore-fs: RMW ordering needs multi-core); spec:需新增（当前阻塞：需要多核FS的RMW请求/全局可见性）; workload:规格负载名无 SE 载体映 |
| O06-F0-W7 | O06 | 原子与同步 | F0 | BLOCKED | campaign:blocked(multicore-fs: barrier completion needs multi-core); spec:需新增（当前阻塞：需要多核FS barrier完成跟踪）; workload:规格负载名无  |
| O06-F4-W7 | O06 | 原子与同步 | F4 | BLOCKED | campaign:blocked(multicore-fs: barrier completion needs multi-core); spec:需新增（当前阻塞：需要多核FS barrier完成跟踪）; workload:规格负载名无  |
| O06-F6-W7 | O06 | 原子与同步 | F6 | BLOCKED | campaign:blocked(multicore-fs: barrier completion needs multi-core); spec:需新增（当前阻塞：需要多核FS barrier完成跟踪）; workload:规格负载名无  |
| O07-F0-W7 | O07 | 原子与同步 | F0 | BLOCKED | campaign:blocked(multicore-fs: order-tag swap needs multi-core); spec:需新增（当前阻塞：需要多核FS order-tag/ready跟踪）; workload:规格负载名 |
| O07-F2-W7 | O07 | 原子与同步 | F2 | BLOCKED | campaign:blocked(multicore-fs: order-tag swap needs multi-core); spec:需新增（当前阻塞：需要多核FS order-tag/ready跟踪）; workload:规格负载名 |
| O07-F6-W7 | O07 | 原子与同步 | F6 | BLOCKED | campaign:blocked(multicore-fs: order-tag swap needs multi-core); spec:需新增（当前阻塞：需要多核FS order-tag/ready跟踪）; workload:规格负载名 |
| P01-F0-W2 | P01 | 数据预取器 | F0 | PASS |  |
| P01-F0-W8 | P01 | 数据预取器 | F0 | PASS |  |
| P01-F1-W2 | P01 | 数据预取器 | F1 | PASS |  |
| P01-F1-W8 | P01 | 数据预取器 | F1 | PASS |  |
| P01-F2-W2 | P01 | 数据预取器 | F2 | PASS |  |
| P01-F2-W8 | P01 | 数据预取器 | F2 | PASS |  |
| P02-F0-W8 | P02 | 数据预取器 | F0 | PASS |  |
| P02-F0-W10 | P02 | 数据预取器 | F0 | PASS |  |
| P02-F3-W8 | P02 | 数据预取器 | F3 | PASS |  |
| P02-F3-W10 | P02 | 数据预取器 | F3 | PASS |  |
| P02-F5-W8 | P02 | 数据预取器 | F5 | PASS |  |
| P02-F5-W10 | P02 | 数据预取器 | F5 | PASS |  |
| P03-F0-W8 | P03 | 数据预取器 | F0 | PASS |  |
| P03-F0-W9 | P03 | 数据预取器 | F0 | PASS |  |
| P03-F2-W8 | P03 | 数据预取器 | F2 | PASS |  |
| P03-F2-W9 | P03 | 数据预取器 | F2 | PASS |  |
| P03-F6-W8 | P03 | 数据预取器 | F6 | PASS |  |
| P03-F6-W9 | P03 | 数据预取器 | F6 | PASS |  |
| P04-F0-W2 | P04 | 数据预取器 | F0 | PASS |  |
| P04-F0-W8 | P04 | 数据预取器 | F0 | PASS |  |
| P04-F4-W2 | P04 | 数据预取器 | F4 | PASS |  |
| P04-F4-W8 | P04 | 数据预取器 | F4 | PASS |  |
| P04-F5-W2 | P04 | 数据预取器 | F5 | PASS |  |
| P04-F5-W8 | P04 | 数据预取器 | F5 | PASS |  |
| P05-F0-W8 | P05 | 数据预取器 | F0 | PASS |  |
| P05-F0-W10 | P05 | 数据预取器 | F0 | PASS |  |
| P05-F4-W8 | P05 | 数据预取器 | F4 | PASS |  |
| P05-F4-W10 | P05 | 数据预取器 | F4 | PASS |  |
| P05-F6-W8 | P05 | 数据预取器 | F6 | PASS |  |
| P05-F6-W10 | P05 | 数据预取器 | F6 | PASS |  |
| P06-F0-W6 | P06 | 数据预取器 | F0 | BLOCKED | campaign:deferred(no clean hook: prefetch-as-demand marking); spec:需新增（当前阻塞：无prefetch-as-demand/属性注入hook） |
| P06-F0-W8 | P06 | 数据预取器 | F0 | BLOCKED | campaign:deferred(no clean hook: prefetch-as-demand marking); spec:需新增（当前阻塞：无prefetch-as-demand/属性注入hook） |
| P06-F2-W6 | P06 | 数据预取器 | F2 | BLOCKED | campaign:deferred(no clean hook: prefetch-as-demand marking); spec:需新增（当前阻塞：无prefetch-as-demand/属性注入hook） |
| P06-F2-W8 | P06 | 数据预取器 | F2 | BLOCKED | campaign:deferred(no clean hook: prefetch-as-demand marking); spec:需新增（当前阻塞：无prefetch-as-demand/属性注入hook） |
| P06-F6-W6 | P06 | 数据预取器 | F6 | BLOCKED | campaign:deferred(no clean hook: prefetch-as-demand marking); spec:需新增（当前阻塞：无prefetch-as-demand/属性注入hook） |
| P06-F6-W8 | P06 | 数据预取器 | F6 | BLOCKED | campaign:deferred(no clean hook: prefetch-as-demand marking); spec:需新增（当前阻塞：无prefetch-as-demand/属性注入hook） |
| P07-F0-W6 | P07 | 数据预取器 | F0 | PASS |  |
| P07-F0-W8 | P07 | 数据预取器 | F0 | PASS |  |
| P07-F2-W6 | P07 | 数据预取器 | F2 | PASS |  |
| P07-F2-W8 | P07 | 数据预取器 | F2 | PASS |  |
| P07-F6-W6 | P07 | 数据预取器 | F6 | PASS |  |
| P07-F6-W8 | P07 | 数据预取器 | F6 | PASS |  |
| P08-F5-W8 | P08 | 数据预取器 | F5 | PASS |  |
| P08-F5-W10 | P08 | 数据预取器 | F5 | PASS |  |
| T10-F0-W1 | T10 | L1d-TLB | F0 | PASS |  |
| T10-F0-W4 | T10 | L1d-TLB | F0 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T10-F0-W11 | T10 | L1d-TLB | F0 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T10-F1-W1 | T10 | L1d-TLB | F1 | PASS |  |
| T10-F1-W4 | T10 | L1d-TLB | F1 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T10-F1-W11 | T10 | L1d-TLB | F1 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T10-F2-W1 | T10 | L1d-TLB | F2 | PASS |  |
| T10-F2-W4 | T10 | L1d-TLB | F2 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| T10-F2-W11 | T10 | L1d-TLB | F2 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| S13-F0-W1 | S13 | Store Queue | F0 | PASS |  |
| S13-F0-W5 | S13 | Store Queue | F0 | PASS |  |
| S13-F0-W11 | S13 | Store Queue | F0 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| S13-F0-W12 | S13 | Store Queue | F0 | PASS |  |
| S13-F1-W1 | S13 | Store Queue | F1 | PASS |  |
| S13-F1-W5 | S13 | Store Queue | F1 | PASS |  |
| S13-F1-W11 | S13 | Store Queue | F1 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| S13-F1-W12 | S13 | Store Queue | F1 | PASS |  |
| S13-F2-W1 | S13 | Store Queue | F2 | PASS |  |
| S13-F2-W5 | S13 | Store Queue | F2 | PASS |  |
| S13-F2-W11 | S13 | Store Queue | F2 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| S13-F2-W12 | S13 | Store Queue | F2 | PASS |  |
| L01-F0-W1 | L01 | Load Queue | F0 | PASS |  |
| L01-F0-W5 | L01 | Load Queue | F0 | PASS |  |
| L01-F0-W12 | L01 | Load Queue | F0 | PASS |  |
| L01-F1-W1 | L01 | Load Queue | F1 | PASS |  |
| L01-F1-W5 | L01 | Load Queue | F1 | PASS |  |
| L01-F1-W12 | L01 | Load Queue | F1 | PASS |  |
| L01-F2-W1 | L01 | Load Queue | F2 | PASS |  |
| L01-F2-W5 | L01 | Load Queue | F2 | PASS |  |
| L01-F2-W12 | L01 | Load Queue | F2 | PASS |  |
| L02-F0-W5 | L02 | Load Queue | F0 | PASS |  |
| L02-F0-W12 | L02 | Load Queue | F0 | PASS |  |
| L02-F2-W5 | L02 | Load Queue | F2 | PASS |  |
| L02-F2-W12 | L02 | Load Queue | F2 | PASS |  |
| L02-F6-W5 | L02 | Load Queue | F6 | PASS |  |
| L02-F6-W12 | L02 | Load Queue | F6 | PASS |  |
| L03-F0-W5 | L03 | Load Queue | F0 | PASS |  |
| L03-F0-W12 | L03 | Load Queue | F0 | PASS |  |
| L03-F4-W5 | L03 | Load Queue | F4 | PASS |  |
| L03-F4-W12 | L03 | Load Queue | F4 | PASS |  |
| L03-F6-W5 | L03 | Load Queue | F6 | PASS |  |
| L03-F6-W12 | L03 | Load Queue | F6 | PASS |  |
| L04-F0-W5 | L04 | Load Queue | F0 | BLOCKED | campaign:deferred(consumer-side: response-pairing event source only); spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射） |
| L04-F0-W11 | L04 | Load Queue | F0 | BLOCKED | campaign:deferred(consumer-side: response-pairing event source only); spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射）; wo |
| L04-F0-W12 | L04 | Load Queue | F0 | BLOCKED | campaign:deferred(consumer-side: response-pairing event source only); spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射） |
| L04-F2-W5 | L04 | Load Queue | F2 | BLOCKED | campaign:deferred(consumer-side: response-pairing event source only); spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射） |
| L04-F2-W11 | L04 | Load Queue | F2 | BLOCKED | campaign:deferred(consumer-side: response-pairing event source only); spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射）; wo |
| L04-F2-W12 | L04 | Load Queue | F2 | BLOCKED | campaign:deferred(consumer-side: response-pairing event source only); spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射） |
| L04-F6-W5 | L04 | Load Queue | F6 | BLOCKED | campaign:deferred(consumer-side: response-pairing event source only); spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射） |
| L04-F6-W11 | L04 | Load Queue | F6 | BLOCKED | campaign:deferred(consumer-side: response-pairing event source only); spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射）; wo |
| L04-F6-W12 | L04 | Load Queue | F6 | BLOCKED | campaign:deferred(consumer-side: response-pairing event source only); spec:需新增（当前阻塞：只有response-pairing事件源，无可注入/追踪映射） |
| C14-F5-W6 | C14 | L1d-Cache | F5 | BLOCKED | campaign:deferred(consumer-side: MSHR busy event source only); spec:需新增（当前阻塞：无MSHR busy注入） |
| C14-F5-W10 | C14 | L1d-Cache | F5 | BLOCKED | campaign:deferred(consumer-side: MSHR busy event source only); spec:需新增（当前阻塞：无MSHR busy注入） |
| C15-F0-W6 | C15 | L1d-Cache | F0 | BLOCKED | campaign:deferred(consumer-side: MSHR occupancy event source only); spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入） |
| C15-F0-W10 | C15 | L1d-Cache | F0 | BLOCKED | campaign:deferred(consumer-side: MSHR occupancy event source only); spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入） |
| C15-F0-W11 | C15 | L1d-Cache | F0 | BLOCKED | campaign:deferred(consumer-side: MSHR occupancy event source only); spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入）; workload:规 |
| C15-F4-W6 | C15 | L1d-Cache | F4 | BLOCKED | campaign:deferred(consumer-side: MSHR occupancy event source only); spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入） |
| C15-F4-W10 | C15 | L1d-Cache | F4 | BLOCKED | campaign:deferred(consumer-side: MSHR occupancy event source only); spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入） |
| C15-F4-W11 | C15 | L1d-Cache | F4 | BLOCKED | campaign:deferred(consumer-side: MSHR occupancy event source only); spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入）; workload:规 |
| C15-F6-W6 | C15 | L1d-Cache | F6 | BLOCKED | campaign:deferred(consumer-side: MSHR occupancy event source only); spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入） |
| C15-F6-W10 | C15 | L1d-Cache | F6 | BLOCKED | campaign:deferred(consumer-side: MSHR occupancy event source only); spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入） |
| C15-F6-W11 | C15 | L1d-Cache | F6 | BLOCKED | campaign:deferred(consumer-side: MSHR occupancy event source only); spec:需新增（当前阻塞：无MSHR occupancy/entry选择注入）; workload:规 |
| O09-F0-W7 | O09 | 原子与同步 | F0 | BLOCKED | campaign:deferred(RMW operand path needs cache-side hook); spec:需新增（当前阻塞：缺RMW operand hook）; workload:规格负载名无 SE 载体映射（WL_ |
| O09-F0-W13 | O09 | 原子与同步 | F0 | BLOCKED | campaign:deferred(RMW operand path needs cache-side hook); spec:需新增（当前阻塞：缺RMW operand hook）; workload:规格负载名无 SE 载体映射（WL_ |
| O09-F1-W7 | O09 | 原子与同步 | F1 | BLOCKED | campaign:deferred(RMW operand path needs cache-side hook); spec:需新增（当前阻塞：缺RMW operand hook）; workload:规格负载名无 SE 载体映射（WL_ |
| O09-F1-W13 | O09 | 原子与同步 | F1 | BLOCKED | campaign:deferred(RMW operand path needs cache-side hook); spec:需新增（当前阻塞：缺RMW operand hook）; workload:规格负载名无 SE 载体映射（WL_ |
| O09-F2-W7 | O09 | 原子与同步 | F2 | BLOCKED | campaign:deferred(RMW operand path needs cache-side hook); spec:需新增（当前阻塞：缺RMW operand hook）; workload:规格负载名无 SE 载体映射（WL_ |
| O09-F2-W13 | O09 | 原子与同步 | F2 | BLOCKED | campaign:deferred(RMW operand path needs cache-side hook); spec:需新增（当前阻塞：缺RMW operand hook）; workload:规格负载名无 SE 载体映射（WL_ |
| P09-F0-W6 | P09 | 数据预取器 | F0 | PASS |  |
| P09-F0-W8 | P09 | 数据预取器 | F0 | PASS |  |
| P09-F0-W13 | P09 | 数据预取器 | F0 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| P09-F4-W6 | P09 | 数据预取器 | F4 | PASS |  |
| P09-F4-W8 | P09 | 数据预取器 | F4 | PASS |  |
| P09-F4-W13 | P09 | 数据预取器 | F4 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
| P09-F6-W6 | P09 | 数据预取器 | F6 | PASS |  |
| P09-F6-W8 | P09 | 数据预取器 | F6 | PASS |  |
| P09-F6-W13 | P09 | 数据预取器 | F6 | BLOCKED | workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜） |
