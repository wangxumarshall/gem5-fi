# LSU 正式实验准入 — R6 计划（严格链 / TLB 完整观测 / 硬门禁 / BLOCKED 攻关）

> 依据：用户 2026-10-23 指令（`/superpowers:executing-plans` 参数）+ 权威规格
> `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md` 及子文档 -03/-07/-09/-10。
> 集成分支 `lsu-mdspec-20261019`，worktree `.claude/worktrees/lsu-mdspec-20261019`。
> 目标**不是**把 BLOCKED 降到 0，而是让每个正式 RunID 产出**真实、完整、可审计**的传播路径与逐层指标。

## 现场恢复（2026-10-23 09:2x 实测）

| 项 | 实测 |
|---|---|
| 主 checkout | `/home/sdc/gem5-fi-ding`@`fi-ding`，脏（69 删/176 未跟踪）——**本轮不落主树** |
| 集成分支 | `lsu-mdspec-20261019`@`97f74786`，与 origin 同步（0/0） |
| 已合入 | `317c71bf` R6-CHECK（family-aware DAG 链证明）；`97f74786` R6-ROUTE（T05–T08 trial-only 证据路由） |
| C++ 待合 | worktree `r6-tlb-hooks`：C++ 改动**未提交**（CHAOSArmTLB.cc+.hh / mmu.cc / CHAOSPropagation.cc+.hh，+306/-31）；静态契约 `tests/test_lsu_hook_tlb_observation.py` 17/17 PASS |
| 运行中构建 | scons -j16 in `r6-tlb-hooks/CHAOS/gem5`（PID 2675756，08:43 起） |
| S01 census | 未见进行中进程；`runs/lsu/golden/w1_all` 只有 10-10/10-11 的 g1..g3 —— **需定位 10-22 17:44 启动的 span census 产物** |
| 契约 | 325 = READY 241 / BLOCKED 84（RULING 6 · FS-INFRA 24 · MODE-UNIMPL 3 · UNRESOLVED 4 · FS-MULTICORE 35 · LICENSE 12） |
| 门禁二进制 | `f4dbfb9a66e0df80`（R4-10 集成轮）；pytest 21 passed；套件 PASS 50 / SKIP 1 |
| 资源 | Mem 29 GiB（avail 11，构建中）；/home 71 GiB free；/tmp tmpfs 13 GiB free；126 CPU |

## 停止条件（用户定义，全部满足才停；随后**不启动正式实验**）

1. 所有可实现 hook/路由/观测点已实现、编译、测试；
2. 325 RunID 全部重新审计；
3. 每个可执行实验有完整族专用链，或有明确可审计 containment 路径；
4. 所有 activated 样本无 Unknown；
5. 每层关键指标与 before/after 满足 MD/Excel 要求；
6. 正式启动命令经机器校验（无 trial/dry-run/少量 seed）；
7. 工作树干净，有效代码与证据已提交并推送；
8. 独立审查 subagent 复核通过；
9. 权威准入达正式条件，外部/规格裁决项**不被隐瞒**。

## 资源纪律（硬约束）

- 代码修补 subagent 3–4 并行（各独占 worktree + 互不重叠文件所有权）。
- **统一 ARM 构建只允许一个**，`-j16`（上限 `-j24`）。
- SE pilot：先 16 并发 → 稳定后 24–32。FS pilot：先 6 并发 → 仅当 MemAvailable > 10 GiB 且 swap 不增长才 8。**禁止按 126 核启动**。
- FS 产物写 `/home/sdc/gem5-fi-ding/runs/lsu/...`（**不写 /tmp**，tmpfs 15 GiB），及时压缩事件文件。
- 每 30 s 记录 load/MemAvailable/swap/各 gem5 RSS/磁盘。MemAvailable < 8 GiB 或 swap 持续增长 → 立即降并发。
- 不跑 stress-ng / 无意义 CPU backfill。

## 文件所有权（互不重叠）

| 所有者 | 独占路径 |
|---|---|
| Agent A（`r6-tlb-hooks`） | `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/*`, `CHAOS/gem5/src/arch/arm/mmu.cc`, `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/*`, `tests/test_lsu_hook_tlb_observation.py` |
| Agent B（`r6-gate`） | `tools/lsu_ready_contract.py`, `tools/lsu_chain_check.py`, `tools/lsu_audit.py`, `tools/lsu_blocked_triage.py`, `tools/lsu_prop_fields.py`, `tests/test_lsu_ready_contract*.py`, `tests/test_lsu_chain_check.py`, `tests/test_lsu_audit*.py` |
| Agent C（`r6-blocked`） | `tools/lsu_fsmc_verdict.py`, `tools/lsu_fs_infra*.py`, `tools/lsu_unit_pilot.py`, `docs/gem5-fi/lsu/mdspec/R6-BLOCKED-*.md`, `runs/lsu/r6_*` |
| Agent D（`r6-pilot`） | `tools/lsu_pilot_runner.sh`(新), `runs/lsu/r6_pilot_*`, `docs/gem5-fi/lsu/mdspec/R6-PILOT-*.md` |
| 主 agent | 集成、统一构建、准入重算、最终裁决、本计划文件 |

## 任务

- [x] **T0 现场恢复**：worktree/分支/进程/构建/census 定位（见上表）
- [ ] **T1 Agent A**：完成并审查 TLB C++ 完整观测链（L0–L5 逐层、fault_id/parent_event_id/request_id/walk_id/dyn_inst_seq 连续、containment_layer/reason、chain_end 不得单独充当 L5、覆盖 T01–T10 尤其 T05–T08）
- [ ] **T2 Agent B**：正式准入硬门禁（族专用完整链 或 明确 containment+N/A；禁 Unknown；禁 cache_access 冒充 TLB L1；禁跨分支拼接；禁仅凭 activated/RC/chain_end 判 READY；逐层必录指标缺失响亮失败）
- [ ] **T3 Agent C**：BLOCKED 可执行项（FS-INFRA 24 / MODE-UNIMPL 3 / FS-MULTICORE W7 / S01-S02 census），并单独列出不可伪造项（LICENSE 12 / PARSEC-W13 6 / C08 classic-cache-Ruby 4 / A06 SHRINK 6 / S10-F2 2）及其准确解除条件（不得移出 325 分母）
- [ ] **T4 Agent D**：多核与 pilot 调度（独立 outdir/guard/锁/清单；每 pilot 产 cell_results+原始事件流+chain_report+逐层指标+完整性结论；缺链即停同类批）
- [ ] **T5 集成**：串行合入 A → B →（C/D 产物）→ 统一构建 → 少量负向/真实 pilot → 全量 T 系列并行重跑 → 重审计 325
- [ ] **T6 终审**：独立 subagent 复核 + 权威准入 + 报告（不启动正式实验）

## T2′ 强制回归（用户 2026-10-23 追加，**硬性**）

旧检查器曾把 5 个 RunID 误判为完整链，它们**不得继续视为 full**：

`T02-F0-W4 · T02-F2-W4 · T04-F0-W4 · T04-F2-W4 · T04-F6-W4`

误判根因：旧检查器用后续 `cache_access`/`cache_return` 冒充 TLB 的 L1/L2，并把
`corr=none`、`detection_layer=None`、`outcome=run_end` 的 `chain_end` 当成 L5。

TLB 观测 hook 与严格链检查器修复完成后，必须用**新编译的统一二进制**重跑这 5 个，
外加此前链不完整的 7 个：`T01-F0-W4 · T01-F1-W4 · T01-F2-W4 · T03-F5-W4 · T10-F0-W4 · T10-F1-W4 · T10-F2-W4`。

每个 RunID 必须证明**同一 fault_id 在同一条 parent_event_id DAG 路径**上的：

`L0 inj → L1 tlb_lookup（真实 entry/way 及 VPN/ASID/valid-global/PPN/权限/memory type/page size 的 before/after）→ L2 tlb_translate_result（权限/对齐检查后的 PA 或 Fault）→ L3 LSQ request 及 cache/memory 请求响应 → L4 PRF/store 落点、异常或架构可见差异 → L5 与前述污染直接关联的 commit/squash/oracle/detection 结局`

硬性要求：
- 禁止用 `cache_access` 充当 TLB L1；
- 禁止跨请求或跨 DAG 分支拼接边；
- 普通 `chain_end` 不能证明 L5；
- `Crash` 必须记录实际检测点、`detection_layer`、`outcome`，并与污染链关联；
- `Masked` 必须记录明确的 containment 层和原因；
- 不允许 `Unknown`；
- 每层必录指标缺失即失败。

**交付**：12 个 RunID 逐项表格 —— RunID · 注入值 before/after · 各层事件 · 关联键 · 最终结局 · chain verdict · 证据路径。
12 项**全部**通过严格门禁后，才能解除对应 FS-INFRA 阻塞。
不得仅凭 `activated=1`、`RC=0` 或旧 `chain_report` 宣布通过。

## 实时 lane 表（2026-10-23 10:5x 建立，主 agent 维护）

| lane | 主题 | worktree | 负责文件 | RunID | 状态 | 超时 | 输出目录 | 验证 | 待集成 commit |
|---|---|---|---|---|---|---|---|---|---|
| L1 | TLB hook：补 L0 before/after + L5=真实检测事件 | r6-tlb-hooks | CHAOSArmTLB/*, mmu.cc, CHAOSPropagation/*, tests/test_lsu_hook_tlb_observation.py | T02-F0-W4 | 运行中 | 600s | runs/lsu/r6_tlb_A_* | — | 待定 |
| L2 | TLB L0→L5 字段/关联键完整性审计 | 无（只读） | — | 全部既有流 | 运行中 | — | runs/lsu/r6_reports/L2.md | — | — |
| L3 | T05 分析 + T06 pilot | 无（outdir） | — | T05-F0-W4, T06-F0-W4 | 运行中 | 600s | runs/lsu/r6_tlb_D_* | — | — |
| L4 | T07 分析 + T09 pilot | 无（outdir） | — | T07-F0-W4, T09-F0-W4 | 运行中 | 600s | runs/lsu/r6_tlb_E_* | — | — |
| L5 | T08-F0-W4 pilot | 无（outdir） | — | T08-F0-W4 | 运行中 | 600s | runs/lsu/r6_tlb_C_T08-F0-W4 | — | — |
| L6 | Golden 无注入对照修复+验证 | r6-pilot | golden 入口 | NEGATIVE-GOLDEN | 运行中 | 900s | runs/lsu/r6_golden_* | — | 待定 |
| L7 | Load Queue hook 审计 | 无（只读） | — | — | 运行中 | — | runs/lsu/r6_reports/L7.md | — | — |
| L8 | Store Queue hook 审计 | 无（只读） | — | — | 运行中 | — | runs/lsu/r6_reports/L8.md | — | — |
| L9 | LSQ/commit 路径 hook 审计 | 无（只读） | — | — | 运行中 | — | runs/lsu/r6_reports/L9.md | — | — |
| L10 | Cache/内存响应路径 hook 审计 | 无（只读） | — | — | 运行中 | — | runs/lsu/r6_reports/L10.md | — | — |
| L11 | 异常/Crash/Hang/SDC oracle 审计 | 无（只读） | — | — | 运行中 | — | runs/lsu/r6_reports/L11.md | — | — |
| L12 | RunID/seed/correlation 跨层一致性 | 无（只读） | — | — | 运行中 | — | runs/lsu/r6_reports/L12.md | — | — |
| L13 | 契约/负向/回归 全套件 | r6-gate(只跑) | — | — | 运行中 | — | runs/lsu/r6_reports/L13.md | — | — |
| L14 | 325 BLOCKED 根因聚类 | 无（只读） | — | — | **完成** | — | runs/lsu/r6_reports/L14.md | 已回收 | 无 |
| L15 | 正式批量调度/断点恢复/目录隔离 | r6-blocked | tools/lsu_r6_schedule.sh, R6-BATCH-PLAN.md | — | 运行中 | — | 同上 | — | 待定 |
| L16 | 独立 reviewer（只认真实产物） | 无（只读） | — | — | 运行中 | — | runs/lsu/r6_reports/L16.md | — | — |
| L22 | FS-MULTICORE W7 多核 FS pilot（4 个 routable 格 + 负对照） | r6-multicore | configs/fs/lsu_multicore_fs.py, tools/lsu_fsmc_verdict.py （本轮均未改） | O01-F0-W7, O02-F0-W7, O02-F5-W7, O03-F0-W7 | **完成** | 2700s | runs/lsu/r6_mc_* | 见 L22.md §3 | 无（仅文档） |
| B2 | checker：L5=真实检测事件语义 | r6-gate | tools/lsu_chain_check.py 等 | — | 待派 | — | — | — | — |

## 进度 / Ruling 记录

（本文件即 ledger；每条完成项追加一行，含 commit SHA 与真实测试命令输出。）

- 2026-10-23 T0 完成：现场如上表。`r6-chain-checker`/`r6-tlb-routing` 分支 tip 未 merge 但内容等价于已合入的 `317c71bf`/`97f74786`（同 commit message、同文件集）→ 视为已集成。
- 2026-10-23 T2 完成（Agent B，`r6-gate`@`2b87cd9d`，已推送）：新增 `check_admission` 硬门禁（11 条响亮规则 token），READY **241→0 / BLOCKED 325**（CHAIN-UNPROVEN 43 · CHAIN-EVIDENCE-MISSING 198 · RULING 6 · LICENSE 12 · FS-MULTICORE 35 · FS-INFRA 24 · MODE-UNIMPL 3 · UNRESOLVED 4）。全套件 `FAIL=13` 与基线逐一相同（`NEW FAIL=[]`）。
  **Ruling**：READY=0 由“无 pilot 证据”主导（198 行），是“未证明”而非“已证伪”；契约新增分类以区分“外部阻塞”与“待取证”，不得据 READY=0 宣称这些 RunID 被外部因素阻塞。代价若错判：可能低估可准入面。
- 2026-10-23 用户追加 T2′ 强制回归（12 RunID，见上）→ 优先级高于原 T3/T4。

### T04-F0-W4 实测（主 agent 亲验，2026-10-23 10:4x，`runs/lsu/r6_tlb_pilot2/T04-F0-W4/seed1/`）

事件流是**单条线性 DAG**（`parent_event_id` = 前一 `event_id`），共 1574 事件：

```
0 inj            field=pfn_to_mapped_page  va=ffffffc009483fa8  dyn_inst_seq=301  corr=origin
                 ⚠ before= / after= 均为空  ← L0 before/after 缺
1 tlb_lookup     way=7 entry_index=0 field=post_lookup before=81d75 after=0
                 state_before=vpn=…;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8   ✓ L1 真实
3 tlb_translate_result  pa=fa8 before=81d75fa8 after=fa8 outcome=NoFault  ✓ L2 真实（effective_pa_changed）
4..100           sq_execute/sq_writeback/cache_access/mem_req/resp/lq_complete  ✓ L3
100 lq_complete / 101 taint_reg(arch_reg=0,dyn_inst_seq=391)  ✓ L4
102 errant_commit corr=taint_prop dyn_inst_seq=391  ⚠ detection_layer= / outcome= 均空 ← 真实检测点未记录
1573 chain_end   detection_layer=None contained=0 outcome=errant_commit_seen corr=none  ← 生命周期件
```

旧 `chain_report.json` 判 `full`，但边是 `inj→cache_access`（cache 冒充 TLB L1）、`cache_access→cache_return`（冒充 L2）、`taint_reg→chain_end`（生命周期件当 L5）。**这与用户描述完全一致。**

**Ruling（2026-10-23）**：L5 证据 = **真实检测事件**，即把 `errant_commit` 充实为携带 `detection_layer` + `outcome` + 与链关联的 `corr`，并以它作为 L5；`chain_end` 永远只作生命周期件、**不得**充当 L5。依据：用户"chain_end 只能是生命周期事件，不能单独充当 L5" × "Crash 必须记录实际检测点、detection_layer、outcome，并与污染链关联"，且 L5 定义为"commit/squash/oracle/detection 结局"（`errant_commit` 正是 commit 结局）。代价若错判：checker 需再改一次映射与测试。
第二条：`inj`（L0）必须携带注入字段的 before/after（当前为空）。

### L22 实测：FS-MULTICORE W7 多核 FS pilot（2026-10-23，`runs/lsu/r6_reports/L22.md`）

4 个 routable 格（`CARRIER_ROUTED_PENDING_RUN`）各跑一条真实 `trial` 样本 + 一条无注入负对照
（`runs/lsu/r6_mc_{clean_control,O01-F0-W7,O02-F0-W7,O02-F5-W7,O03-F0-W7}`，2 核 Ruby/CHI 检查点
`/tmp/r4-8-fsmc/mc_boot/cpt.243414599076`，`--fs-timeout 2700`）：

- 负对照 `prop_evt` 仅表头（248 B），`FINAL=6b39e7aaa74b663f` **== FSMC_GOLDEN_FINAL**（golden 正确）。
- `O01-F0-W7` / `O02-F0-W7`：activated=1，链 **222 057 事件**（inj→addr_form→exmon_monitor→rmw/stxr→taint_reg→errant_commit→chain_end），`FINAL=golden` / violations=0 ⇒ Masked。**控制对照成立**。
- `O02-F5-W7`：activated=**104**（F5 的"永久"语义真机成立），224 701 事件，`FINAL=golden` ⇒ Masked。
- `O03-F0-W7`：activated=1，**随后 gem5 硬断言中止** —— `src/mem/request.hh:912 Request::getExtraData(): extraDataValid() failed`，栈顶 `ArmISAInst::STXRW64::completeAcc`。载荷先跑完、中止发生在其后；**样本不可用作干净结论**，且 `classify_fsmc_run` 只读 guest terminal ⇒ 该格被记成 `Masked`（**分类器看不到载荷完成后的 gem5 中止**）。
- **L5 未充实**：本轮 multicore 链的 `errant_commit` 同样 `detection_layer=`/`outcome=` 为空（与上方 T04 裁决同病），`chain_end` 仍出现。⇒ 上面第二条 Ruling **对 multicore FS 链同样适用**（`inj` 的 before/after 本轮 multicore 链**已**携带：`event_id=0 ... before=835e9df0 after=1000835e9df0`）。
- **工具缺陷（非本 lane 可修，`tools/lsu_campaign.py` 禁改）**：`write_chain_report` 对 ~222k 事件链不可扩展 —— gem5 结束后 campaign 已消耗 >25 min CPU 仍未写出 `cell_results.json`/`chain_report.json`（O03 因 0 事件瞬时完成）。原始逐样本证据完整可用。

**覆盖**：35 个 FS-MULTICORE RunID 中 **4 已覆盖 / 31 未覆盖**（31 = F2/F6 档位 6 + C08 宿主 4 + O04–O07/O09 模型 15 + W13 负载身份 6）。**不宣称 PASS**：3 个干净样本的 oracle 全为 Masked，O03 被污染，L5 未充实。
`tools/lsu_fsmc_verdict.py` 与 `configs/fs/lsu_multicore_fs.py` **本轮未改**（改裁决枚举会破坏其 pin 住的计数断言，且无新枚举表达"已取样但未充实 L5"）。

