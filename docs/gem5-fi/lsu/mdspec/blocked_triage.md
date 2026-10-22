# 84 BLOCKED 逐项裁决（互斥分类）

- 分类来源：ready_contract.json（权威契约；契约总数 {'READY': 241, 'BLOCKED': 84}）
- BLOCKED 总数：84（守恒校验通过：Σ 分类 == 总数）
- 分类统计：RULING=6 / LICENSE=12 / FS-MULTICORE=35 / FS-INFRA=24 / MODE-UNIMPL=3 / HOOK-UNIMPL=0 / UNRESOLVED=4 / PLATFORM-DEFECT=0 / UNCLASSIFIED=0 / OK=0

## 互斥类别定义

| 类别 | 含义 | 解除条件 |
|---|---|---|
| RULING | 模型级裁决封锁（A06 load 侧 / byte-enable） | §2.c 路径 spike 验证 + 测试 |
| LICENSE | SPEC CPU2017 授权缺失（W11） | 取得授权 |
| FS-MULTICORE | 需多核 FS（litmus/PARSEC 语义） | 多核 FS 基础设施落地 |
| FS-INFRA | 需 FS 基础设施（TLB 翻译负载） | FS checkpoint 流水线 |
| MODE-UNIMPL | 规格表 10 标注『先实现』的子模型模式 | 实现该模式 + 测试 |
| HOOK-UNIMPL | 钩子/载体缺口（无模式标注） | 补钩子或补 SE 载体映射 |
| OK | 无上述阻塞（应为 0） | — |

## 需用户批准的延期清单

以下类别**在可预见范围内无法由本轨道单方面解除**，需批准延期：

- **LICENSE**（12 个）：C15-F0-W11, C15-F4-W11, C15-F6-W11, L04-F0-W11, L04-F2-W11, L04-F6-W11, S13-F0-W11, S13-F1-W11, S13-F2-W11, T10-F0-W11, T10-F1-W11, T10-F2-W11
- **FS-MULTICORE**（35 个）：C08-F0-W7, C08-F2-W7, C08-F5-W7, C08-F6-W7, O01-F0-W7, O01-F2-W7, O01-F6-W7, O02-F0-W7, O02-F2-W7, O02-F5-W7, O02-F6-W7, O03-F0-W7, O03-F2-W7, O03-F6-W7, O04-F0-W7, O04-F2-W7, O04-F6-W7, O05-F0-W7, O05-F4-W7, O05-F6-W7, O06-F0-W7, O06-F4-W7, O06-F6-W7, O07-F0-W7, O07-F2-W7, O07-F6-W7, O09-F0-W13, O09-F0-W7, O09-F1-W13, O09-F1-W7, O09-F2-W13, O09-F2-W7, P09-F0-W13, P09-F4-W13, P09-F6-W13
- **FS-INFRA**（24 个）：T01-F0-W4, T01-F1-W4, T01-F2-W4, T02-F0-W4, T02-F2-W4, T03-F5-W4, T04-F0-W4, T04-F2-W4, T04-F6-W4, T05-F0-W4, T05-F2-W4, T05-F6-W4, T06-F0-W4, T06-F2-W4, T06-F6-W4, T07-F0-W4, T07-F4-W4, T07-F6-W4, T08-F0-W4, T08-F4-W4, T08-F6-W4, T10-F0-W4, T10-F1-W4, T10-F2-W4
- **RULING**（6 个）：A06-F0-W3, A06-F0-W5, A06-F2-W3, A06-F2-W5, A06-F6-W3, A06-F6-W5
- **UNRESOLVED**（4 个）：S01-F0-W1, S02-F0-W1, S10-F2-W5, S10-F2-W9

可自行解除（不需批准，但需实现工作）：
- MODE-UNIMPL（3 个）：见下表逐项理由

## 逐项明细

| RunID | 单元 | 模型 | 互斥类别 | 理由 |
|---|---|---|---|---|
| A06-F0-W3 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| A06-F0-W5 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| A06-F2-W3 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| A06-F2-W5 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| A06-F6-W3 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| A06-F6-W5 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| C08-F0-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| C08-F2-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| C08-F5-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| C08-F6-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| C15-F0-W11 | L1d-Cache | C15 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| C15-F4-W11 | L1d-Cache | C15 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| C15-F6-W11 | L1d-Cache | C15 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| L04-F0-W11 | Load Queue | L04 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| L04-F2-W11 | Load Queue | L04 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| L04-F6-W11 | Load Queue | L04 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| O01-F0-W7 | 原子与同步 | O01 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O01-F2-W7 | 原子与同步 | O01 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O01-F6-W7 | 原子与同步 | O01 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O02-F0-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O02-F2-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O02-F5-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O02-F6-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O03-F0-W7 | 原子与同步 | O03 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O03-F2-W7 | 原子与同步 | O03 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O03-F6-W7 | 原子与同步 | O03 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O04-F0-W7 | 原子与同步 | O04 | FS-MULTICORE | campaign:deferred(RMW data-path hook LANDED (rmw_mux @ SwapReq commit) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pending, R4-9-FSMC)  |
| O04-F2-W7 | 原子与同步 | O04 | FS-MULTICORE | campaign:deferred(RMW data-path hook LANDED (rmw_mux @ SwapReq commit) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pending, R4-9-FSMC)  |
| O04-F6-W7 | 原子与同步 | O04 | FS-MULTICORE | campaign:deferred(RMW data-path hook LANDED (rmw_mux @ SwapReq commit) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pending, R4-9-FSMC)  |
| O05-F0-W7 | 原子与同步 | O05 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; RMW-completion hook rmw_order LANDED @ SwapReq commit and COMPILED (build OK) but un-piloted |
| O05-F4-W7 | 原子与同步 | O05 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; RMW-completion hook rmw_order LANDED @ SwapReq commit and COMPILED (build OK) but un-piloted |
| O05-F6-W7 | 原子与同步 | O05 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; RMW-completion hook rmw_order LANDED @ SwapReq commit and COMPILED (build OK) but un-piloted |
| O06-F0-W7 | 原子与同步 | O06 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; barrier-completion hook LANDED (MemDepUnit barrier-SN bookkeeping, CHAOSLSQFwd --lsqfwd_o06) |
| O06-F4-W7 | 原子与同步 | O06 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; barrier-completion hook LANDED (MemDepUnit barrier-SN bookkeeping, CHAOSLSQFwd --lsqfwd_o06) |
| O06-F6-W7 | 原子与同步 | O06 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; barrier-completion hook LANDED (MemDepUnit barrier-SN bookkeeping, CHAOSLSQFwd --lsqfwd_o06) |
| O07-F0-W7 | 原子与同步 | O07 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; order-tag exchange hook LANDED (MemDepUnit barrier-SN set as the ordering-tag proxy, CHAOSLS |
| O07-F2-W7 | 原子与同步 | O07 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; order-tag exchange hook LANDED (MemDepUnit barrier-SN set as the ordering-tag proxy, CHAOSLS |
| O07-F6-W7 | 原子与同步 | O07 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; order-tag exchange hook LANDED (MemDepUnit barrier-SN set as the ordering-tag proxy, CHAOSLS |
| O09-F0-W13 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| O09-F0-W7 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| O09-F1-W13 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| O09-F1-W7 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| O09-F2-W13 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| O09-F2-W7 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| P09-F0-W13 | 数据预取器 | P09 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: W13 负载身份——PARSEC(dedup/ferret/streamcluster) **开源（不是授权障碍）但本仓库不可得**：find 实证只有 gem5 上游测试脚手架 CHAOS/gem5/tes |
| P09-F4-W13 | 数据预取器 | P09 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: W13 负载身份——PARSEC(dedup/ferret/streamcluster) **开源（不是授权障碍）但本仓库不可得**：find 实证只有 gem5 上游测试脚手架 CHAOS/gem5/tes |
| P09-F6-W13 | 数据预取器 | P09 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: W13 负载身份——PARSEC(dedup/ferret/streamcluster) **开源（不是授权障碍）但本仓库不可得**：find 实证只有 gem5 上游测试脚手架 CHAOS/gem5/tes |
| S01-F0-W1 | Store Queue | S01 | UNRESOLVED | PASS |
| S02-F0-W1 | Store Queue | S02 | UNRESOLVED | PASS |
| S10-F2-W5 | Store Queue | S10 | UNRESOLVED | PASS |
| S10-F2-W9 | Store Queue | S10 | UNRESOLVED | PASS |
| S13-F0-W11 | Store Queue | S13 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| S13-F1-W11 | Store Queue | S13 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| S13-F2-W11 | Store Queue | S13 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| T01-F0-W4 | L1d-TLB | T01 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T01-F1-W4 | L1d-TLB | T01 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T01-F2-W4 | L1d-TLB | T01 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T02-F0-W4 | L1d-TLB | T02 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T02-F2-W4 | L1d-TLB | T02 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T03-F5-W4 | L1d-TLB | T03 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T04-F0-W4 | L1d-TLB | T04 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T04-F2-W4 | L1d-TLB | T04 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T04-F6-W4 | L1d-TLB | T04 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T05-F0-W4 | L1d-TLB | T05 | FS-INFRA | campaign:deferred(T05 entry-state modes LANDED (valid_clear/valid_set/global_flip/asid_subst) but COMPILE-UNVERIFIED — build + FS pilot pending, R4-10 |
| T05-F2-W4 | L1d-TLB | T05 | FS-INFRA | campaign:deferred(T05 entry-state modes LANDED (valid_clear/valid_set/global_flip/asid_subst) but COMPILE-UNVERIFIED — build + FS pilot pending, R4-10 |
| T05-F6-W4 | L1d-TLB | T05 | FS-INFRA | campaign:deferred(T05 entry-state modes LANDED (valid_clear/valid_set/global_flip/asid_subst) but COMPILE-UNVERIFIED — build + FS pilot pending, R4-10 |
| T06-F0-W4 | L1d-TLB | T06 | FS-INFRA | campaign:deferred(T06 attribute legal-substitution modes LANDED (perm_subst/memtype_subst/pagesize_subst) but COMPILE-UNVERIFIED — build + FS pilot pe |
| T06-F2-W4 | L1d-TLB | T06 | FS-INFRA | campaign:deferred(T06 attribute legal-substitution modes LANDED (perm_subst/memtype_subst/pagesize_subst) but COMPILE-UNVERIFIED — build + FS pilot pe |
| T06-F6-W4 | L1d-TLB | T06 | FS-INFRA | campaign:deferred(T06 attribute legal-substitution modes LANDED (perm_subst/memtype_subst/pagesize_subst) but COMPILE-UNVERIFIED — build + FS pilot pe |
| T07-F0-W4 | L1d-TLB | T07 | FS-INFRA | campaign:deferred(T07 CAM/way-select modes LANDED (false_hit/double_hit/wrong_way) but COMPILE-UNVERIFIED — build + FS pilot pending, R4-10) ; spec:需新 |
| T07-F4-W4 | L1d-TLB | T07 | FS-INFRA | campaign:deferred(T07 CAM/way-select modes LANDED (false_hit/double_hit/wrong_way) but COMPILE-UNVERIFIED — build + FS pilot pending, R4-10) ; spec:需新 |
| T07-F6-W4 | L1d-TLB | T07 | FS-INFRA | campaign:deferred(T07 CAM/way-select modes LANDED (false_hit/double_hit/wrong_way) but COMPILE-UNVERIFIED — build + FS pilot pending, R4-10) ; spec:需新 |
| T08-F0-W4 | L1d-TLB | T08 | FS-INFRA | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb |
| T08-F0-W9 | L1d-TLB | T08 | MODE-UNIMPL | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb |
| T08-F4-W4 | L1d-TLB | T08 | FS-INFRA | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb |
| T08-F4-W9 | L1d-TLB | T08 | MODE-UNIMPL | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb |
| T08-F6-W4 | L1d-TLB | T08 | FS-INFRA | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb |
| T08-F6-W9 | L1d-TLB | T08 | MODE-UNIMPL | campaign:walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 (R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 + tlb_walk/tlb |
| T10-F0-W11 | L1d-TLB | T10 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| T10-F0-W4 | L1d-TLB | T10 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T10-F1-W11 | L1d-TLB | T10 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| T10-F1-W4 | L1d-TLB | T10 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
| T10-F2-W11 | L1d-TLB | T10 | LICENSE | workload:workload-level:blocked(spec-license: SPEC CPU2017 needs a license) |
| T10-F2-W4 | L1d-TLB | T10 | FS-INFRA | workload:workload-level:blocked(fs-infra: TLB workload needs FS) |
