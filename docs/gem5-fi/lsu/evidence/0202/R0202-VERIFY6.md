# R0202-VERIFY6 — 0202 六链 seed-1 重建验证报告

**结论（先给结果）**：六个 seed-1 RunID 在同一 freeze 下**全部真实 activated**并通过严格
计数守恒；**5 个 PASS**（完整连续 parent-event 的 L0→L5 链，终点为真实 `errant_commit`，
非 `chain_end`），**1 个 NOT-ACCEPTED**（`T02-F2-W4`），原因已定位到两条独立的流结构事实
并以仓库严格门禁复现。**未启动 seeds 2–3、30 样本 pilot、385 screening、325 正式格或任何
其他 RunID。**

机器可读：`R0202-VERIFY6.json`（全字段、含完整 selected ancestry）、`R0202-VERIFY6.csv`。
原始证据根：`runs/lsu/0202_verify6_20261026T221213/`（11 MB，未提交）。

## 1. 六行总表

| ITEM | RunID | 频率 | seed | attempted | eligible | injected | applied/activated | 守恒 | 结局 | stream | terminal | admitted | 判定 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ITEM-041 | T01-F0-W4 | F0 | 7626208423775840535 | 133699 | 13 | 1 | 1 | OK | Crash | 完整 | full L5 | True | **PASS** |
| ITEM-047 | T02-F0-W4 | F0 | 1482588217842860401 | 358838 | 6 | 1 | 1 | OK | Crash | 完整 | full L5 | True | **PASS** |
| ITEM-049 | T02-F2-W4 | F2 | 14201167915699637708 | 258283 | 258283 | 2 | 2 | OK | Crash | 完整 | provable_to_L4 | False | **NOT-ACCEPTED** |
| ITEM-052 | T04-F0-W4 | F0 | 957792015410033221 | 88831806 | 46 | 1 | 1 | OK | Crash* | 完整 | full L5 | True | **PASS** |
| ITEM-053 | T04-F2-W4 | F2 | 1505523022015170976 | 182561 | 170030 | 2 | 2 | OK | Crash | 完整 | full L5 | True | **PASS** |
| ITEM-054 | T04-F6-W4 | F6 | 16867864092875579733 | 85114887 | 1 | 1 | 1 | OK | Crash* | 完整 | full L5 | True | **PASS** |

`*` T04-F0-W4 / T04-F6-W4 的**分类标签**为 Crash，但其**真实终止方式是预算内优雅超时**
（guest 在 errant_commit 之后挂死、控制台 0 字节），见 §7 诚实限制 H2。二者链本身在
`errant_commit` 处已闭合。

严格口径：六例 `truncated=False`、`unknown=0`、`chain_end` 存在、`stats.txt` 非零
（360–386 KB）、`activated≥1`、`injected == applied == activated`、无跨样本/跨 request 拼链
未被拦下的情形（违反项零或已由门禁指名，见 §6）。

## 2. 环境与资源画像（0202 实测）

详见 `ENVIRONMENT-LOCK-0202.md`。要点：`cathelper-k8s-worker2`、openEuler **22.03**、
aarch64 Kunpeng-920 64 核 / 2 NUMA、376 GiB RAM、`/home` 792 GiB 可用；
**swap 出厂禁用** ⇒ 见 §7 H1。构建期与运行期 60 s 采样，最低 `MemAvailable` 358.8 GiB，
`SwapFree` 恒 16 GiB，无持续换页、无 blocked 进程、无 OOM。并发：编译 `-j8` 单实例；
gem5 峰值并发 2（硬上限 4）。全程仅终止本任务自有 PID/PGID。

## 3. Freeze 身份（六个 canary 全部引用同一份）

| 项 | 值 |
|---|---|
| 分支 / HEAD | `fix/0202-six-chain-20261026` / `0b8afd0fd6da8c9aa94c5a9cf3d25d9b43280db3` |
| 基线包含 | `git merge-base --is-ancestor 3f3eb617 HEAD` = 0 |
| 二进制 | `CHAOS/gem5/build/ARM/gem5.opt`，SHA256 `a99031a86e8e108b9278af53044d873a8262ea20d73bd7d94c6dba1300b49e0a`，1,245,098,072 B，aarch64 ELF |
| 构建 | `PYTHON_CONFIG=/opt/python3.11/bin/python3.11-config scons -j8 build/ARM/gem5.opt`，exit 0，0 error |
| checkpoint | `runs/lsu/0202_fs_cpt_boot_20261026T193235/cpt.239515184727`（真实 cpt.<tick>），文件清单 SHA256 `4a991958…` |
| golden | oracle `b6d81b360a5672d80c27430f39153e2c`，两次无注入运行均 `ok=10/10` |
| 工具/配置 SHA | 见 `0202-FREEZE-MANIFEST.md`（含 `lsu_runner.py` `522d355e…` 等 12 个工具 + 4 个配置） |

## 4. 逐 RunID 事实

命令（六例同形，仅 ITEM/flags/seed 不同；完整命令行见 JSON `command` 字段）：

```
<gem5.opt> --outdir <run-dir> configs/fs/lsu_b0_fs.py
  --kernel gem5-fs/vmlinux --disk gem5-fs/ubuntu.img --bootloader gem5-fs/boot.arm64
  --cpu O3 --restore-checkpoint …/cpt.239515184727 --readfile configs/fs/tlb_probe.rcS
  --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0
  --tlb_max_faults 1 <类型旗标> [--tlb_lsu_tier F2|F6] --tlb_rng_seed <seed>
  --chaos_propagation --prop_run_id <RUNID> --prop_sample_run_id s<seed>
```

| RunID | wall | exit | monitor_reason | 输出根（绝对） |
|---|---|---|---|---|
| T01-F0-W4 | 20 s | 0 | target-exited | `…/0202_verify6_20261026T221213/runs/engineering/ITEM-041_engineering_s0` |
| T02-F0-W4 | 26 s | 0 | target-exited | 同上 `ITEM-047_engineering_s0` |
| T02-F2-W4 | 22 s | 0 | target-exited | 同上 `ITEM-049_engineering_s0` |
| T04-F0-W4 | 2734 s | 0 | max-seconds-reached（SIGINT 优雅收口） | 同上 `ITEM-052_engineering_s0` |
| T04-F2-W4 | 20 s | 0 | target-exited | 同上 `ITEM-053_engineering_s0` |
| T04-F6-W4 | 2733 s | 0 | max-seconds-reached（SIGINT 优雅收口） | 同上 `ITEM-054_engineering_s0` |

注入（`armtlb_injections.log`，真实值）：
- **T01-F0**：VPN tag 单 bit，`old_pfn 0x81cf1 → 0x200081cf1`，`Mask 0x200000000`（bit 33）。
- **T02-F0**：PPN 双 bit，`0x81cf1 → 0x40000000081ce1`，`Mask 0x40000000000010`（bit 4 & 42）。
- **T02-F2**：真实 F2 多次注入（2 次），`0x81cf1 → 0x80000091cf1` 等。
- **T04-F0**：PPN 换值到**另一 live 映射页**，`0xffbce → 0x81cf1`，`candidates: 1`。
- **T04-F2**：`0x81cf1 → 0x81ce6`、`0x81ce6 → 0x81cf2`，`candidates: 30`。
- **T04-F6**：同 T04-F0 同一首命中点（F6 = 指定事件首现注入一次）。

T04 合法性（任务要求）：源/目标 `pfn != 0`、页大小一致、异帧且候选来自**当次运行的 live
映射表**（谓词 `chaos_tlb_pfn.hh:isSelectablePfnTarget`，单测
`tests/chaos_tlb_pfn_candidate_test.cc`）。六例无一选择 PFN 0 或陈旧页。

## 5. L0→L5 代表事件与完整 ancestry

**T01-F0-W4**（PASS）：`inj(0,corr=origin) → tlb_lookup(1) → tlb_pfn(2) → sq_execute(5) →
taint_reg(65) → errant_commit(236, det=L5, outcome=errant_commit)`；ancestry 深度 17，
根即 `inj`（0→1→2→3→4→…→236 连续父子）。

**T02-F0-W4**（PASS）：`inj(0) → tlb_lookup(1) → tlb_pfn(2) → cache_access(3) →
taint_reg(89) → errant_commit(277, det=L5)`；经由 `addr_fallback` 关联桥（req 0→35），
checker 判定为合法 request 迁移；深度 18。

**T04-F0-W4**（PASS）：`inj(0) → tlb_lookup(1) → tlb_pfn(2) → lq_read(5) → taint_reg(20) →
errant_commit(21, det=L5)`；深度 22。

**T04-F6-W4**（PASS）：同 T04-F0 形状（同一首命中点），`errant_commit(21, det=L5)`；深度 22。

**T04-F2-W4**（PASS）：fault 1 `inj(0) → tlb_lookup(1) → tlb_pfn(2) → sq_execute(4) →
taint_reg(34) → errant_commit(51, det=L5)`；fault 2 `detected_contained`。深度 22。

**T02-F2-W4**（NOT-ACCEPTED）：fault 1 与 fault 2 均
`provable_to_L4_then_unknown`（L0→L4 全 proven，`L4->L5 missing`）；详见 §6。

完整逐步 ancestry（event_id/kind/request_id/corr/parent_event_id/tick）在 JSON 的
`selected_ancestry` 与 `chain_per_fault[fid].path_events`。

## 6. 严格门禁结果

**逐样本**（`tools/lsu_chain_check.py` 的 `check_chain` + `check_admission`，含
campaign 同源的 `containment_from_events` 推导）：

- T01-F0-W4：`admitted=True, path=full_chain, terminal=full, layers=[L0…L5], violations=[]`
- T02-F0-W4：同上 `full_chain`
- T04-F0-W4：`full_chain`（`exit=0` 优雅超时，链仍在 `errant_commit` 闭合）
- T04-F2-W4：`full_chain`（fault 1）
- T04-F6-W4：`full_chain`
- **T02-F2-W4：`admitted=False`**，violations：
  `cross_branch_edge`（fault 1 的 `errant_commit(32, det=L5)` 与其 L4 见证 `taint_reg(22)`
  分属 event 4 的两个子分支 ⇒ 无单一 DAG 路径覆盖 L4→L5——**"不把侧向 fan-out 当主路径"** 生效）；
  `no_closed_chain_and_no_containment`、`ready_by_activated_only`、`ready_by_rc0`、
  `ready_by_chain_end_only`（fault 2 的含住主张只写在**生命周期** `chain_end`
  （kind=chain_end, corr=none, outcome=detected_contained）上 ⇒ 依规则不构成检测/含住证据）。

**全局**（`tools/lsu_ready_contract.py`，输出 `ready_contract_0202.{out,json,md}`）：
`total=325 READY=0 BLOCKED=325`，`verdict=NO-GO`，`chain_gate recorded=325/325 admitted=0
evaluated=64`。这是**仓库对全 325 格的门禁**，在无 0101 历史 `runs/` 证据的前提下必然
BLOCKED（`CHAIN-EVIDENCE-MISSING=197` 即缺 pilot 证据根）；它不评价本次六个 seed-1 canary，
两者口径不同，不混用。

频率非坍缩证据（要求项）：
- T02-F2-W4 `CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1` + funnel `tier=F2`；
- T04-F2-W4 同上；T04-F6-W4 `requested=F6 effective=F6 lookup_tier_enabled=1` + `tier=F6`；
- F0 三例 `effective=F0 lookup_tier_enabled=0`（legacy 路径，另有被动 F0 funnel）。
F6 语义：`eligible=1 injected=1`（首次命中即一次），与 F0（`eligible=46 injected=1`）与
F2（多次）在 summary 层面可区分。

## 7. 本任务所做的修复（每个 = 独立 commit + 测试 + 真实输出）

| # | commit | 内容 | 自验证 |
|---|---|---|---|
| U1 | `a659c656` | `lsu_runner` FS checkpoint 显式化（`--fs-checkpoint`/env；身份与命令同源；分歧响亮拒绝） | `test_lsu_runner_fs_checkpoint.py` ALL PASS；dry-run 命令携带真实新 cpt + 真 SHA；SE hello `reg_chain` exit 0 且 oracle `f247ef3fe6f02cfd` == golden |
| U2 | `b250a6df` | armtlb **F 档路由**：F1–F6 追加 `--tlb_lsu_tier`（复用 `LC._armtlb_lookup_tier_flags`），否则 F2/F6 必然坍缩为 F0 | `test_lsu_runner_ftier_no_collapse.py` ALL PASS（27 项，含六命令两两互异） |
| U3 | `ef61d827` | FS timeout 1800 → **2700**（实测 golden wall 2274 s > 1800；对齐 campaign 已知良好预算） | `test_lsu_campaign_timeout.py` 等 ALL PASS |
| U4 | `e055a7e3` | armtlb **挂载传播流**（`LC.propagation_flags`），否则零链证据 | dry-run 出现 `--chaos_propagation …`；相关套件 PASS |
| U5 | `0b8afd0f` | 守卫超时 **先 SIGINT** 再升级（`graceful_terminate`），消除 Timeout 证据截断 | `test_lsu_guard_graceful_timeout.py` ALL PASS；实测两例由 `exit=-15/truncated=True/stats=0` 变为 `exit=0/truncated=False/stats=360604B` |

U1–U5 全部为 Python/工具层，**gem5 二进制未变**（C++ 零改动）；但 U2/U3/U4/U5 改变运行
语义，故 freeze 更新并**在新 freeze 下重跑全部六个 canary**（首轮结果作废，未合并统计）。
首轮旧目录 `runs/lsu/0202_verify6_20261026T195447/` 保留为被排除证据，未删除。

## 8. 诚实限制与未决项

- **H1（环境偏离，已披露）**：本机 swap 出厂禁用，使 `lsu_guard.py gate` 拒绝一切运行。
  未绕过门禁：新开 16 GiB swapfile `/home/swapfile.0202`（未写 fstab，可逆）。
- **H2（分类标签与真实终止方式不一致）**：T04-F0-W4 / T04-F6-W4 由预算优雅超时终止
  （`monitor_reason=max-seconds-reached`, `graceful=true`），但 `lsu_l5_classify` 未收到
  `--timed-out`（`lsu_runner` 不转发该事实）⇒ 标签为 Crash。同理，T02-F2/T04-F2 的
  guest **内核 panic** 被标成 `crash_kind=simulator_assert`（其正则 `|panic|` 命中
  `arm_chaos_fs` 自身的 "KERNEL PANIC under fault" 提示行）。两处均**只影响标签，
  不影响链判定**；已如实并列记录，未改分类器语义。
- **H3（FS 非比特可复现）**：同一 manifest/seed/checkpoint 下 T02-F2-W4 两轮的前两次注入
  tick 与掩码完全一致，第 3 次起发散（`eligible` 566811 vs 258283、`injected` 5 vs 2）。
  无注入 golden oracle 稳定。**FS 观测不得声称 run-to-run 比特复现。**
- **H4（工具链）**：本机 GCC 10.3.1（gem5 官方支持 11–14.2，仅告警）；gem5 v25.1 实际要求
  **Python ≥3.10**（PEP 604 运行时求值），故源码编译 CPython 3.11.9 至 `/opt/python3.11`
  后重建。首建（Python 3.8）二进制 `70aab844…` 无法运行任何配置，已作废且从未用于 canary。
- **H5（T02-F2-W4 为多注入簇）**：F2 按定义每 ~100k eligible events 注入一次；本样本
  2 次注入的**两条链都止于 L4**，且没有合法的非生命周期含住事件。示波：注入后 guest 早期
  崩溃（本样本），后续传播未在预算内闭合。

### DECISION REQUEST DR-0202-1（T02-F2-W4 多注入样本的准入口径）

**事实**：仓库存在**三个互不一致的 fault 选择器**（同一事件流上）：`check_admission`
用"最长可证路径"、`containment_from_events` 用"事件最多"、`lsu_campaign` 报告顶层 terminal
用"sorted 第一个"。经全仓检索（含 `tests/`、`mdspec/`、`完整任务执行清单.md`、R6 裁决文档），
**多 fault 样本的准入口径在代码、测试与文档中均未定义**；既有规则只有"禁止跨 fault 拼接"
与"所有已激活**样本**都必须通过"（样本级 `all()`），从未定义单一样本内多 fault 的判定。
F1–F4 被文档规定为 **run-level cluster**（事件级仅作传播记录），与该样本级链门禁存在张力。

**本次未做**：没有为了让 T02-F2-W4 通过而改动 checker、选择器或含住推导（那属于"放宽
checker/选择性丢弃"）。严格门禁的 `admitted=False` 原样记录。

**请裁决（三选一）**：
1. **一致性修复**：令 `containment_from_events` 与 `check_admission` 使用**同一 fault**
   （现为不同 fault，属内部不一致）。注意：这**可能**使 T02-F2-W4 变为 `contained` 准入——
   若接受，需同时确认"多注入中部分 fault 逃逸、部分含住"时样本级结论如何表述。
2. **全 fault 闭合**：要求样本内**每个** fault 都闭合，否则样本不通过（则 T02-F2-W4 保持
   NOT-ACCEPTED，需换 seed 或接受该 RunID 在本 freeze 下不可准入）。
3. **F2 run-level 口径**：F1–F4 按 run-level cluster 判定（结局归因整次运行的故障序列，
   事件级链仅作传播记录），据此为 F2 定义独立准入规则。

在此之前，`T02-F2-W4` 记为 **NOT-ACCEPTED（待裁决）**，不计入任何通过数。

## 9. 停止状态

- 已完成：六个 seed-1 canary 全部真实 activated；5 例严格准入通过；1 例因上述结构事实与
  未决口径未通过。
- **未启动**：seeds 2–3、30 样本 pilot、385 screening、confirmatory、325 格 formal，或任何
  其他 RunID。调试/工程运行均标 `engineering` phase 且与正式统计隔离。
- 待用户裁决 `DR-0202-1` 后方可判定 `T02-F2-W4` 的处置（换 seed 或采纳某口径）。
