# Markdown→实现覆盖矩阵（MDSPEC Phase B，**节点级证据化**）

- 总数：325（RunID 唯一，表7∩表9 集合相等——B1 已证）
- **PASS=245 / PARTIAL=0 / BLOCKED=80**
- 判定口径（2026-10-20 证据化）：PASS = 该单元规格所需**全部节点**既已实现（kind ∈ 发射端注册表）**又**在真实 pilot 运行中出现；缺任一节点 = PARTIAL 并逐项列出。注册表布尔值**不再**作为判据。
- 节点级证据取**全部 pilot 的 kind 并集**（节点=钩子能力级证据，与注入单元解耦）；逐单元归属索引见 pilot_evidence.json 的 kinds_observed_by_unit（RunID→单元解析：精确匹配 → 行标签，见 tools/lsu_pilot_evidence.py unit_of）。
- 真实运行观测到的 kind（36）：addr_form, cache_access, cache_evict, cache_fill, cache_return, cache_writeback, chain_end, consumer, errant_commit, exmon_monitor, exmon_rmw, exmon_stxr, inj, lq_complete, lq_read, lsq_push, lsq_sendfrag, mem_req, mshr_alloc, mshr_busy, mshr_fill, mshr_free, mshr_merge, pf_demand, pf_fill, pf_issue, pf_queue, pf_train, resp, sq_complete, sq_execute, sq_writeback, ssit_consult, taint_reg, tlb_fault, tlb_translate

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
| A06-F0-W3 | A06 | AGU | F0 | BLOCKED | campaign:BLOCKED(load-side widen path + A06-b mask path landed but COMPILE-UNVERIFIED; spike (real gem5 run) pending — R4-6-A06 2026-10-22, MDSPEC §2 ruling 202 |
| A06-F0-W5 | A06 | AGU | F0 | BLOCKED | campaign:BLOCKED(load-side widen path + A06-b mask path landed but COMPILE-UNVERIFIED; spike (real gem5 run) pending — R4-6-A06 2026-10-22, MDSPEC §2 ruling 202 |
| A06-F2-W3 | A06 | AGU | F2 | BLOCKED | campaign:BLOCKED(load-side widen path + A06-b mask path landed but COMPILE-UNVERIFIED; spike (real gem5 run) pending — R4-6-A06 2026-10-22, MDSPEC §2 ruling 202 |
| A06-F2-W5 | A06 | AGU | F2 | BLOCKED | campaign:BLOCKED(load-side widen path + A06-b mask path landed but COMPILE-UNVERIFIED; spike (real gem5 run) pending — R4-6-A06 2026-10-22, MDSPEC §2 ruling 202 |
| A06-F6-W3 | A06 | AGU | F6 | BLOCKED | campaign:BLOCKED(load-side widen path + A06-b mask path landed but COMPILE-UNVERIFIED; spike (real gem5 run) pending — R4-6-A06 2026-10-22, MDSPEC §2 ruling 202 |
| A06-F6-W5 | A06 | AGU | F6 | BLOCKED | campaign:BLOCKED(load-side widen path + A06-b mask path landed but COMPILE-UNVERIFIED; spike (real gem5 run) pending — R4-6-A06 2026-10-22, MDSPEC §2 ruling 202 |
| A07-F0-W3 | A07 | AGU | F0 | PASS |  |
| A07-F0-W5 | A07 | AGU | F0 | PASS |  |
| A07-F4-W3 | A07 | AGU | F4 | PASS |  |
| A07-F4-W5 | A07 | AGU | F4 | PASS |  |
| A07-F6-W3 | A07 | AGU | F6 | PASS |  |
| A07-F6-W5 | A07 | AGU | F6 | PASS |  |
| A08-F0-W3 | A08 | AGU | F0 | PASS |  |
| A08-F0-W5 | A08 | AGU | F0 | PASS |  |
| A08-F2-W3 | A08 | AGU | F2 | PASS |  |
| A08-F2-W5 | A08 | AGU | F2 | PASS |  |
| A08-F6-W3 | A08 | AGU | F6 | PASS |  |
| A08-F6-W5 | A08 | AGU | F6 | PASS |  |
| T01-F0-W1 | T01 | L1d-TLB | F0 | PASS |  |
| T01-F0-W4 | T01 | L1d-TLB | F0 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T01-F1-W1 | T01 | L1d-TLB | F1 | PASS |  |
| T01-F1-W4 | T01 | L1d-TLB | F1 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T01-F2-W1 | T01 | L1d-TLB | F2 | PASS |  |
| T01-F2-W4 | T01 | L1d-TLB | F2 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T02-F0-W1 | T02 | L1d-TLB | F0 | PASS |  |
| T02-F0-W4 | T02 | L1d-TLB | F0 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T02-F2-W1 | T02 | L1d-TLB | F2 | PASS |  |
| T02-F2-W4 | T02 | L1d-TLB | F2 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T03-F5-W4 | T03 | L1d-TLB | F5 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T03-F5-W9 | T03 | L1d-TLB | F5 | PASS |  |
| T04-F0-W4 | T04 | L1d-TLB | F0 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T04-F2-W4 | T04 | L1d-TLB | F2 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T04-F6-W4 | T04 | L1d-TLB | F6 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T05-F0-W4 | T05 | L1d-TLB | F0 | BLOCKED | campaign:deferred(mode unimplemented: valid/global/ASID state); spec:需新增（当前阻塞：valid/global/ASID模式未实现）; workload:workload-level:blocked(fs-infra: TLB workload ne |
| T05-F2-W4 | T05 | L1d-TLB | F2 | BLOCKED | campaign:deferred(mode unimplemented: valid/global/ASID state); spec:需新增（当前阻塞：valid/global/ASID模式未实现）; workload:workload-level:blocked(fs-infra: TLB workload ne |
| T05-F6-W4 | T05 | L1d-TLB | F6 | BLOCKED | campaign:deferred(mode unimplemented: valid/global/ASID state); spec:需新增（当前阻塞：valid/global/ASID模式未实现）; workload:workload-level:blocked(fs-infra: TLB workload ne |
| T06-F0-W4 | T06 | L1d-TLB | F0 | BLOCKED | campaign:deferred(mode unimplemented: permission legal-substitution); spec:需新增（当前阻塞：permission/attribute合法替换未实现）; workload:workload-level:blocked(fs-infra: TLB  |
| T06-F2-W4 | T06 | L1d-TLB | F2 | BLOCKED | campaign:deferred(mode unimplemented: permission legal-substitution); spec:需新增（当前阻塞：permission/attribute合法替换未实现）; workload:workload-level:blocked(fs-infra: TLB  |
| T06-F6-W4 | T06 | L1d-TLB | F6 | BLOCKED | campaign:deferred(mode unimplemented: permission legal-substitution); spec:需新增（当前阻塞：permission/attribute合法替换未实现）; workload:workload-level:blocked(fs-infra: TLB  |
| T07-F0-W4 | T07 | L1d-TLB | F0 | BLOCKED | campaign:deferred(mode unimplemented: hit fabrication/way select); spec:需新增（当前阻塞：hit fabrication/way select未实现）; workload:workload-level:blocked(fs-infra: TLB w |
| T07-F4-W4 | T07 | L1d-TLB | F4 | BLOCKED | campaign:deferred(mode unimplemented: hit fabrication/way select); spec:需新增（当前阻塞：hit fabrication/way select未实现）; workload:workload-level:blocked(fs-infra: TLB w |
| T07-F6-W4 | T07 | L1d-TLB | F6 | BLOCKED | campaign:deferred(mode unimplemented: hit fabrication/way select); spec:需新增（当前阻塞：hit fabrication/way select未实现）; workload:workload-level:blocked(fs-infra: TLB w |
| T08-F0-W4 | T08 | L1d-TLB | F0 | BLOCKED | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb_refill sh |
| T08-F0-W9 | T08 | L1d-TLB | F0 | BLOCKED | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb_refill sh |
| T08-F4-W4 | T08 | L1d-TLB | F4 | BLOCKED | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb_refill sh |
| T08-F4-W9 | T08 | L1d-TLB | F4 | BLOCKED | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb_refill sh |
| T08-F6-W4 | T08 | L1d-TLB | F6 | BLOCKED | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb_refill sh |
| T08-F6-W9 | T08 | L1d-TLB | F6 | BLOCKED | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb_refill sh |
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
| S10-F0-W5 | S10 | Store Queue | F0 | PASS |  |
| S10-F0-W9 | S10 | Store Queue | F0 | PASS |  |
| S10-F2-W5 | S10 | Store Queue | F2 | PASS |  |
| S10-F2-W9 | S10 | Store Queue | F2 | PASS |  |
| S10-F5-W5 | S10 | Store Queue | F5 | PASS |  |
| S10-F5-W9 | S10 | Store Queue | F5 | PASS |  |
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
| C08-F0-W7 | C08 | L1d-Cache | F0 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| C08-F2-W6 | C08 | L1d-Cache | F2 | PASS |  |
| C08-F2-W7 | C08 | L1d-Cache | F2 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| C08-F5-W6 | C08 | L1d-Cache | F5 | PASS |  |
| C08-F5-W7 | C08 | L1d-Cache | F5 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| C08-F6-W6 | C08 | L1d-Cache | F6 | PASS |  |
| C08-F6-W7 | C08 | L1d-Cache | F6 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
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
| C11-F0-W6 | C11 | L1d-Cache | F0 | PASS |  |
| C11-F0-W10 | C11 | L1d-Cache | F0 | PASS |  |
| C11-F2-W6 | C11 | L1d-Cache | F2 | PASS |  |
| C11-F2-W10 | C11 | L1d-Cache | F2 | PASS |  |
| C11-F4-W6 | C11 | L1d-Cache | F4 | PASS |  |
| C11-F4-W10 | C11 | L1d-Cache | F4 | PASS |  |
| C11-F6-W6 | C11 | L1d-Cache | F6 | PASS |  |
| C11-F6-W10 | C11 | L1d-Cache | F6 | PASS |  |
| C12-F0-W6 | C12 | L1d-Cache | F0 | PASS |  |
| C12-F0-W10 | C12 | L1d-Cache | F0 | PASS |  |
| C12-F4-W6 | C12 | L1d-Cache | F4 | PASS |  |
| C12-F4-W10 | C12 | L1d-Cache | F4 | PASS |  |
| C12-F6-W6 | C12 | L1d-Cache | F6 | PASS |  |
| C12-F6-W10 | C12 | L1d-Cache | F6 | PASS |  |
| O01-F0-W7 | O01 | 原子与同步 | F0 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| O01-F2-W7 | O01 | 原子与同步 | F2 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| O01-F6-W7 | O01 | 原子与同步 | F6 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| O02-F0-W7 | O02 | 原子与同步 | F0 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| O02-F2-W7 | O02 | 原子与同步 | F2 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| O02-F5-W7 | O02 | 原子与同步 | F5 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| O02-F6-W7 | O02 | 原子与同步 | F6 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| O03-F0-W7 | O03 | 原子与同步 | F0 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| O03-F2-W7 | O03 | 原子与同步 | F2 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| O03-F6-W7 | O03 | 原子与同步 | F6 | BLOCKED | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不 |
| O04-F0-W7 | O04 | 原子与同步 | F0 | BLOCKED | campaign:deferred(RMW data-path hook LANDED (rmw_mux @ SwapReq commit) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pending, R4-9-FSMC); spec:需新增（ |
| O04-F2-W7 | O04 | 原子与同步 | F2 | BLOCKED | campaign:deferred(RMW data-path hook LANDED (rmw_mux @ SwapReq commit) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pending, R4-9-FSMC); spec:需新增（ |
| O04-F6-W7 | O04 | 原子与同步 | F6 | BLOCKED | campaign:deferred(RMW data-path hook LANDED (rmw_mux @ SwapReq commit) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pending, R4-9-FSMC); spec:需新增（ |
| O05-F0-W7 | O05 | 原子与同步 | F0 | BLOCKED | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; RMW-completion hook rmw_order LANDED @ SwapReq commit but COMPILE-UNVERIFIED + un-piloted, R4-9-FSMC); |
| O05-F4-W7 | O05 | 原子与同步 | F4 | BLOCKED | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; RMW-completion hook rmw_order LANDED @ SwapReq commit but COMPILE-UNVERIFIED + un-piloted, R4-9-FSMC); |
| O05-F6-W7 | O05 | 原子与同步 | F6 | BLOCKED | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; RMW-completion hook rmw_order LANDED @ SwapReq commit but COMPILE-UNVERIFIED + un-piloted, R4-9-FSMC); |
| O06-F0-W7 | O06 | 原子与同步 | F0 | BLOCKED | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; barrier-completion hook LANDED (MemDepUnit barrier-SN bookkeeping, CHAOSLSQFwd --lsqfwd_o06) but COMPI |
| O06-F4-W7 | O06 | 原子与同步 | F4 | BLOCKED | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; barrier-completion hook LANDED (MemDepUnit barrier-SN bookkeeping, CHAOSLSQFwd --lsqfwd_o06) but COMPI |
| O06-F6-W7 | O06 | 原子与同步 | F6 | BLOCKED | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; barrier-completion hook LANDED (MemDepUnit barrier-SN bookkeeping, CHAOSLSQFwd --lsqfwd_o06) but COMPI |
| O07-F0-W7 | O07 | 原子与同步 | F0 | BLOCKED | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; order-tag exchange hook LANDED (MemDepUnit barrier-SN set as the ordering-tag proxy, CHAOSLSQFwd --lsq |
| O07-F2-W7 | O07 | 原子与同步 | F2 | BLOCKED | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; order-tag exchange hook LANDED (MemDepUnit barrier-SN set as the ordering-tag proxy, CHAOSLSQFwd --lsq |
| O07-F6-W7 | O07 | 原子与同步 | F6 | BLOCKED | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; order-tag exchange hook LANDED (MemDepUnit barrier-SN set as the ordering-tag proxy, CHAOSLSQFwd --lsq |
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
| P06-F0-W6 | P06 | 数据预取器 | F0 | PASS |  |
| P06-F0-W8 | P06 | 数据预取器 | F0 | PASS |  |
| P06-F2-W6 | P06 | 数据预取器 | F2 | PASS |  |
| P06-F2-W8 | P06 | 数据预取器 | F2 | PASS |  |
| P06-F6-W6 | P06 | 数据预取器 | F6 | PASS |  |
| P06-F6-W8 | P06 | 数据预取器 | F6 | PASS |  |
| P07-F0-W6 | P07 | 数据预取器 | F0 | PASS |  |
| P07-F0-W8 | P07 | 数据预取器 | F0 | PASS |  |
| P07-F2-W6 | P07 | 数据预取器 | F2 | PASS |  |
| P07-F2-W8 | P07 | 数据预取器 | F2 | PASS |  |
| P07-F6-W6 | P07 | 数据预取器 | F6 | PASS |  |
| P07-F6-W8 | P07 | 数据预取器 | F6 | PASS |  |
| P08-F5-W8 | P08 | 数据预取器 | F5 | PASS |  |
| P08-F5-W10 | P08 | 数据预取器 | F5 | PASS |  |
| T10-F0-W1 | T10 | L1d-TLB | F0 | PASS |  |
| T10-F0-W4 | T10 | L1d-TLB | F0 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T10-F0-W11 | T10 | L1d-TLB | F0 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| T10-F1-W1 | T10 | L1d-TLB | F1 | PASS |  |
| T10-F1-W4 | T10 | L1d-TLB | F1 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T10-F1-W11 | T10 | L1d-TLB | F1 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| T10-F2-W1 | T10 | L1d-TLB | F2 | PASS |  |
| T10-F2-W4 | T10 | L1d-TLB | F2 | BLOCKED | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T10-F2-W11 | T10 | L1d-TLB | F2 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| S13-F0-W1 | S13 | Store Queue | F0 | PASS |  |
| S13-F0-W5 | S13 | Store Queue | F0 | PASS |  |
| S13-F0-W11 | S13 | Store Queue | F0 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| S13-F0-W12 | S13 | Store Queue | F0 | PASS |  |
| S13-F1-W1 | S13 | Store Queue | F1 | PASS |  |
| S13-F1-W5 | S13 | Store Queue | F1 | PASS |  |
| S13-F1-W11 | S13 | Store Queue | F1 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| S13-F1-W12 | S13 | Store Queue | F1 | PASS |  |
| S13-F2-W1 | S13 | Store Queue | F2 | PASS |  |
| S13-F2-W5 | S13 | Store Queue | F2 | PASS |  |
| S13-F2-W11 | S13 | Store Queue | F2 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
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
| L04-F0-W5 | L04 | Load Queue | F0 | PASS |  |
| L04-F0-W11 | L04 | Load Queue | F0 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| L04-F0-W12 | L04 | Load Queue | F0 | PASS |  |
| L04-F2-W5 | L04 | Load Queue | F2 | PASS |  |
| L04-F2-W11 | L04 | Load Queue | F2 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| L04-F2-W12 | L04 | Load Queue | F2 | PASS |  |
| L04-F6-W5 | L04 | Load Queue | F6 | PASS |  |
| L04-F6-W11 | L04 | Load Queue | F6 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| L04-F6-W12 | L04 | Load Queue | F6 | PASS |  |
| C14-F5-W6 | C14 | L1d-Cache | F5 | PASS |  |
| C14-F5-W10 | C14 | L1d-Cache | F5 | PASS |  |
| C15-F0-W6 | C15 | L1d-Cache | F0 | PASS |  |
| C15-F0-W10 | C15 | L1d-Cache | F0 | PASS |  |
| C15-F0-W11 | C15 | L1d-Cache | F0 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| C15-F4-W6 | C15 | L1d-Cache | F4 | PASS |  |
| C15-F4-W10 | C15 | L1d-Cache | F4 | PASS |  |
| C15-F4-W11 | C15 | L1d-Cache | F4 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| C15-F6-W6 | C15 | L1d-Cache | F6 | PASS |  |
| C15-F6-W10 | C15 | L1d-Cache | F6 | PASS |  |
| C15-F6-W11 | C15 | L1d-Cache | F6 | BLOCKED | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| O09-F0-W7 | O09 | 原子与同步 | F0 | BLOCKED | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pendin |
| O09-F0-W13 | O09 | 原子与同步 | F0 | BLOCKED | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pendin |
| O09-F1-W7 | O09 | 原子与同步 | F1 | BLOCKED | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pendin |
| O09-F1-W13 | O09 | 原子与同步 | F1 | BLOCKED | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pendin |
| O09-F2-W7 | O09 | 原子与同步 | F2 | BLOCKED | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pendin |
| O09-F2-W13 | O09 | 原子与同步 | F2 | BLOCKED | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pendin |
| P09-F0-W6 | P09 | 数据预取器 | F0 | PASS |  |
| P09-F0-W8 | P09 | 数据预取器 | F0 | PASS |  |
| P09-F0-W13 | P09 | 数据预取器 | F0 | BLOCKED | workload:workload-level:blocked(multicore-fs: W13 负载身份——PARSEC(dedup/ferret/streamcluster) **开源（不是授权障碍）但本仓库不可得**：find 实证只有 gem5 上游测试脚手架 CHAOS/gem5/tests/gem5/pa |
| P09-F4-W6 | P09 | 数据预取器 | F4 | PASS |  |
| P09-F4-W8 | P09 | 数据预取器 | F4 | PASS |  |
| P09-F4-W13 | P09 | 数据预取器 | F4 | BLOCKED | workload:workload-level:blocked(multicore-fs: W13 负载身份——PARSEC(dedup/ferret/streamcluster) **开源（不是授权障碍）但本仓库不可得**：find 实证只有 gem5 上游测试脚手架 CHAOS/gem5/tests/gem5/pa |
| P09-F6-W6 | P09 | 数据预取器 | F6 | PASS |  |
| P09-F6-W8 | P09 | 数据预取器 | F6 | PASS |  |
| P09-F6-W13 | P09 | 数据预取器 | F6 | BLOCKED | workload:workload-level:blocked(multicore-fs: W13 负载身份——PARSEC(dedup/ferret/streamcluster) **开源（不是授权障碍）但本仓库不可得**：find 实证只有 gem5 上游测试脚手架 CHAOS/gem5/tests/gem5/pa |

## 单元级节点能力（与 RunID 阻塞解耦）

| 单元 | 需要节点 | 已实现 | 真实运行已观测 | 仍缺 | 仅辅助运行观测 |
|---|---|---|---|---|---|
| AGU | 11 | 11 | 11/11 |  | — |
| L1d-Cache | 11 | 11 | 11/11 |  | — |
| L1d-TLB | 6 | 6 | 6/6 |  | — |
| Load Queue | 7 | 7 | 7/7 |  | — |
| Store Queue | 7 | 7 | 7/7 |  | — |
| 原子与同步 | 6 | 6 | 5/6 | unobserved:atomic_op | — |
| 数据预取器 | 7 | 7 | 7/7 |  | — |

## 辅助运行证据边界（矩阵单元自身运行 vs 辅助运行）

**本表为空**：没有任何单元的必需节点是「仅辅助运行可见」的——每个 PASS 单元的必需节点都由**该单元自己的矩阵运行**（含其 `<矩阵RunID>-seed<N>` 逐 seed 流）直接观测到，无需辅助运行兜底。

（机制与判据见 `tools/lsu_coverage_matrix.py::aux_run_boundary`；边界非空时此处会逐单元列出「仅辅助运行观测的必需节点 / 辅助运行 RunID / 该单元矩阵运行（均未观测到）」。）
