# R6-T-BLOCKED-REVALIDATION — 13 个 BLOCKED_INFRA T RunID 的现行树复核

> 生成日期：2026-10-27（只读调查；未运行 gem5 / campaign / scons，未修改任何证据、XLSX、workbook）。
> 本文件的所有结论均以「file:line」或「实际命令 + 真实输出」为锚点；未重跑仿真，因此所有 RUNNABLE 判定是**静态路由 + 二进制符号 + 磁盘证据**三重判定的结果，不是一次新的真机运行。

## 0. 树与二进制身份（先说清楚“现行树”是哪一棵）

| 对象 | 路径 / 值 | 证据 |
|---|---|---|
| 当前调查树（tools/docs） | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019`（branch `lsu-mdspec-20261019`，HEAD `de81266c`） | `git -C … rev-parse HEAD` |
| 主树（runs/ + gem5-fs/） | `/home/sdc/gem5-fi-ding`（branch `fi-ding`，HEAD `6f98088a`） | `git -C /home/sdc/gem5-fi-ding rev-parse HEAD` |
| 任务指定的“当前二进制” | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`，位于 `.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`（1,145,680,944 B，源码 head `d1543872`） | `sha256sum` + `runs/lsu/r6_n8_bin_identity.txt` |
| 本 worktree 自建二进制 | `e8052842…`（`CHAOS/gem5/build/ARM/gem5.opt`，2026-10-25 09:22，1,145,673,848 B） | `sha256sum` |

> 诚实说明：R6 权威证据与本文的“当前二进制”指 `20fda…`（`runs/lsu/r6_n8_bin_identity.txt` 明确 `BIN_SHA=20fda699…`、`binary_source_head=d1543872`）。worktree 内另有 `e805…` 构建，两者不是同一产物；本文只对 `20fda…` 做符号级审计。

FS 资产：worktree 的 `gem5-fs/` 是**空目录**；真实资产在主树 `/home/sdc/gem5-fi-ding/gem5-fs/`（`vmlinux` 237 MB、`ubuntu.img` 2.36 GB、`boot.arm64`），运行时必须 `LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs`（`tools/lsu_campaign.py:71-86,130-137`；`runs/lsu/r6_n8_T10-F0-W1_s1/manifest.json` 的 `cmd` 即采用该约定）。B0 检查点 `runs/lsu/fs_cpt_boot/cpt.237949797015` 存在于主树。

## 1. 结论摘要（分类计数）

| 分类 | 数量 | RunID |
|---|---:|---|
| `ALREADY_RUNNABLE` | **3** | T10-F0-W4, T10-F1-W4, T10-F2-W4 |
| `TOOLING_GAP` | **8** | T05-F0-W4, T05-F2-W4, T06-F0-W4, T06-F2-W4, T07-F0-W4, T07-F4-W4, T08-F0-W4, T08-F4-W4 |
| `WORKLOAD_GAP` | **2** | T08-F0-W9, T08-F4-W9 |
| `CODE_GAP` | 0 | — |
| `OBSERVATION_GAP` | 0（作为“主分类”） | —（T05-F2/T06-F2/T07-F4/T08-F4 另有残余观测缺口，见 §5） |
| `SPEC_DECISION_REQUIRED` | 0（作为“主分类”） | —（T08-W9 的负载替换本身即需裁决，见 §7 STOP） |
| `BLOCKED_EXTERNAL` | 0 | — |
| `OUT_OF_SCOPE` | 0 | — |
| **合计** | **13** | |

一句话：**没有任何一格是 CODE_GAP**。`20fda…` 二进制已包含全部 T05/T06/T07/T08/T10 故障模型符号与 site 字符串；T05–T08 的“阻塞”来自 `tools/lsu_campaign.py` 的陈旧 `MODEL_BLOCKED`/`EVIDENCE_PILOT_MODELS` 门（T05–T08 仅在 `--phase trial` 或 `--allow-blocked-models` 下放行），T10 的“阻塞”只存在于 runid_map/coverage/CSV 的陈旧状态文本。

---

## 2. 矩阵定义（XLSX 回填行，逐格）

来源：`artifacts/lsu-trial/07-expanded-matrix-backfilled.csv`（主树与 worktree 内容一致；`runs/lsu/r6_matrix_325.csv` 亦同）。列索引：1=RunID，5=故障类型，6=故障模型，7=频率，9=负载，11=触发条件，26=记录状态（0-based）。

| RunID | CSV 行 | 模型/单元 | 故障类型 | 故障子模型（列6） | 频率 | 设计负载（列9） | CSV 列26 现行状态 |
|---|---|---|---|---|---|---|---|
| T05-F0-W4 | 110 (`56`) | T05 / L1d-TLB | 状态 | valid清零/伪造、global翻转、ASID替换（每运行一种） | F0 | TLB-AliasPerm | `blocked(fs-infra: TLB workload needs FS)` |
| T05-F2-W4 | 112 (`57`) | T05 / L1d-TLB | 状态 | 同上 | F2 | TLB-AliasPerm | 同上 |
| T06-F0-W4 | 116 (`59`) | T06 / L1d-TLB | 换值 | permission/memory-type/page-size 合法替换 | F0 | TLB-AliasPerm | 同上 |
| T06-F2-W4 | 118 (`60`) | T06 / L1d-TLB | 换值 | 同上 | F2 | TLB-AliasPerm | 同上 |
| T07-F0-W4 | 122 (`62`) | T07 / L1d-TLB | 状态 | false hit / double hit / wrong-way | F0 | TLB-AliasPerm | 同上 |
| T07-F4-W4 | 124 (`63`) | T07 / L1d-TLB | 状态 | 同上 | F4 | TLB-AliasPerm | 同上 |
| T08-F0-W4 | 128 (`65`) | T08 / L1d-TLB | 时序 | 丢失/重复/提前done/旧walk结果 | F0 | TLB-AliasPerm | 同上 |
| T08-F0-W9 | 130 (`66`) | T08 / L1d-TLB | 时序 | 同上 | F0 | **GAP/Graph500 子集（BFS/SSSP/PageRank）** | `blocked(fs-infra: TLB::lookup zero-call in SE, W1 ③)` |
| T08-F4-W4 | 132 (`67`) | T08 / L1d-TLB | 时序 | 同上 | F4 | TLB-AliasPerm | `blocked(fs-infra: TLB workload needs FS)` |
| T08-F4-W9 | 134 (`68`) | T08 / L1d-TLB | 时序 | 同上 | F4 | **GAP/Graph500 子集** | `blocked(fs-infra: TLB::lookup zero-call in SE, W1 ③)` |
| T10-F0-W4 | 524 (`263`) | T10 / L1d-TLB | 单比特翻转 | PPN 低/中/高分段单 bit | F0 | TLB-AliasPerm | `blocked(fs-infra: TLB workload needs FS)` |
| T10-F1-W4 | 530 (`266`) | T10 / L1d-TLB | 单比特翻转 | 同上 | F1 | TLB-AliasPerm | 同上 |
| T10-F2-W4 | 536 (`269`) | T10 / L1d-TLB | 单比特翻转 | 同上 | F2 | TLB-AliasPerm | 同上 |

`docs/gem5-fi/lsu/mdspec/runid_map.json` 的 13 条 entry 与上表一致（`model_id/freq/fault_type/submodels/workload/status=BLOCKED`），其中：
- T05/T06/T07 的 `status_reasons[0]` = `campaign:deferred(... modes LANDED ... but COMPILE-UNVERIFIED — build + FS pilot pending, R4-10)`；`[1]` = `spec:需新增（…未实现）`（这句话与源码事实相反，见 §4）。
- T08 的 `status_reasons[0]` = `campaign:walk_pairing (T08-a) landed AND real-run proven …`。
- T10 的 `status_reasons` 只有 `workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' …)`，**没有 model-level 阻塞**。
- T08-W9/W4-W9 在 `docs/gem5-fi/lsu/mdspec/coverage_matrix.md:75,77` 仍记 `BLOCKED`，理由文本却是 “walk_pairing landed AND real-run proven”。

`docs/gem5-fi/lsu/mdspec/coverage_matrix.md` 对应行：
- `:65-67` T05-F0/F2 与 T05-F6（F6 不在本 13 格内）均为 `BLOCKED`，理由 “modes LANDED … COMPILE-UNVERIFIED”。
- `:68-70` T06 同上；`:71-73` T07 同上。
- `:74-79` T08-F0-W4/W9、F4-W4/W9、F6 均 `BLOCKED`，理由 “walk_pairing (T08-a) landed AND real-run proven …”。
- `:259-267` T10：**W1 三格 `PASS`，W4 三格 `BLOCKED`，理由均为 `workload-level:blocked(fs-infra: TLB workload needs FS)`**。

`docs/gem5-fi/lsu/mdspec/ready_contract.json`（`meta.source = runid_map.json + coverage_matrix.md + lsu_campaign.resolve_cell + R6-FREQUENCY-POLICY.json`，`status.BLOCKED=325`）：
- 13 格 `upstream_status=BLOCKED`；T05–T08-W4 与 T10-W4 的 `upstream_category=FS-INFRA`；**T08-F0-W9 / T08-F4-W9 的 `upstream_category=MODE-UNIMPL`**（与 CSV 的 “fs-infra” 标签不一致）。
- `chain.admitted`：T05-F0-W4 = **true**（`terminal=detected_contained`，0 violation）；T06-F0-W4、T07-F0-W4、T08-F0-W4、T08-F0-W9、T10-F0-W4 = false（各自列明 `no_closed_chain_and_no_containment` / `containment_on_unclosed_stream` 等）；T05-F2/F06-F2/T07-F4/T08-F4/W9-F4/T10-F1/F2 = `n_samples=0`（无 pilot）。

---

## 3. resolve_cell / campaign 路由（现行树实测）

命令（只 import 路由函数，不运行 gem5）：

```bash
python3 - <<'EOF'
import sys, csv
sys.path.insert(0,'/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/tools')
import lsu_campaign as LC
...
print(LC.resolve_cell(row))                       # 默认
print(LC.resolve_cell(row, evidence_pilot=True))  # 运行器在 --phase trial 下自动采用
EOF
```

真实输出（摘要）：

| RunID | 默认 `resolve_cell` | `evidence_pilot=True`（trial 自动） | golden |
|---|---|---|---|
| T05-F0-W4 | **BLOCKED** `deferred(T05 entry-state modes LANDED … COMPILE-UNVERIFIED …)` | **RUNNABLE**, `fs:tlb_probe`, `--tlb_fault_type valid_clear` | `b6d81b360a5672d80c27430f39153e2c` |
| T05-F2-W4 | BLOCKED（同上） | **RUNNABLE**, `valid_clear --tlb_lsu_tier F2` | 同上 |
| T06-F0-W4 | **BLOCKED** `deferred(T06 attribute legal-substitution … COMPILE-UNVERIFIED …)` | **RUNNABLE**, `--tlb_fault_type perm_subst` | 同上 |
| T06-F2-W4 | BLOCKED（同上） | **RUNNABLE**, `perm_subst --tlb_lsu_tier F2` | 同上 |
| T07-F0-W4 | **BLOCKED** `deferred(T07 CAM/way-select … COMPILE-UNVERIFIED …)` | **RUNNABLE**, `--tlb_fault_type false_hit` | 同上 |
| T07-F4-W4 | BLOCKED（同上） | **RUNNABLE**, `false_hit --tlb_lsu_tier F4` | 同上 |
| T08-F0-W4 | **BLOCKED** `walk_pairing (T08-a) landed AND real-run proven … Block retained: … deletion is an integration decision` | **RUNNABLE**, `walk_pairing --tlb_lsu_tier F0 --tlb_lsu_warmup_events 0 --tlb_lsu_span_events 1000` | 同上 |
| T08-F0-W9 | BLOCKED（同上） | **RUNNABLE**, 与 W4 完全相同的 flags（workload 不参与） | 同上 |
| T08-F4-W4 | BLOCKED（同上） | **RUNNABLE**, `walk_pairing --tlb_lsu_tier F4 …` | 同上 |
| T08-F4-W9 | BLOCKED（同上） | **RUNNABLE**, 与 W4 完全相同的 flags | 同上 |
| T10-F0-W4 | **RUNNABLE** `fs:tlb_probe` | RUNNABLE（同） | 同上 |
| T10-F1-W4 | **RUNNABLE** `fs:tlb_probe` | RUNNABLE（同） | 同上 |
| T10-F2-W4 | **RUNNABLE** `fs:tlb_probe` | RUNNABLE（同） | 同上 |

路由关键代码：
- 模型级阻塞：`tools/lsu_campaign.py:1591-1594`（`pilot_only = evidence_pilot and model in EVIDENCE_PILOT_MODELS`）；`EVIDENCE_PILOT_MODELS = {"T05","T06","T07","T08"}`（`:581`）。
- trial 自动放行条件：`tools/lsu_campaign.py:2500-2502`（`evidence_pilot=(args.phase == "trial" and model in EVIDENCE_PILOT_MODELS)`）。**screening/formal 阶段不会自动放行**；需要显式 `--allow-blocked-models`（`:2759`）。
- T05/T06/T07/T08 的 faultType 映射：`:563-565`（valid_clear / perm_subst / false_hit）、`:558`（walk_pairing）。
- armtlb FS 分支：`:1604-1641`；F 档位：lookup 模式 F1–F6 追加 `--tlb_lsu_tier`（`:735-742`），F0 保持 legacy（无 tier flag）；walk 家族（T08）无论 F0/F4 都追加 `--tlb_lsu_tier <F> --tlb_lsu_warmup_events 0 --tlb_lsu_span_events 1000`（`:1615-1623`，常量 `:600-601`）。
- workload 级 `TLB-AliasPerm` 键：`tools/lsu_campaign.py:314-315`；对 `ARMTLB_MODELS`（`:570` 附近）`continue` 放行到 FS 分支（`:1568-1584`）。
- FS 载波：`FS_CARRIER_RC = REPO / "configs/fs/tlb_probe.rcS"`（`:749`）。

**运行器实际构造的命令**（`run_single_cell`, `:2517-2542`；以 T05-F2-W4 为例，逐字拼接自 resolve_cell 输出）：

```
<g5> --outdir <out>/seed1 configs/fs/lsu_b0_fs.py \
  --restore-checkpoint runs/lsu/fs_cpt_boot/cpt.237949797015 \
  --kernel <LSU_FS_DIR>/vmlinux --disk <LSU_FS_DIR>/ubuntu.img --bootloader <LSU_FS_DIR>/boot.arm64 \
  --cpu O3 --readfile <REPO>/configs/fs/tlb_probe.rcS --ckpt-first-clock \
  --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 \
  --tlb_fault_type valid_clear --tlb_lsu_tier F2 \
  --tlb_rng_seed <seed> --chaos_propagation --prop_run_id T05-F2-W4 --prop_sample_run_id s<seed>
```

（`<g5>` = `20fda…`；`<REPO>` = 当前 worktree。T05-F0/T06-F0/T07-F0 无 `--tlb_lsu_tier`；T08 的 walk flags 见上表；T10-F1/F2 为 `--tlb_fault_type bit_flip --tlb_lsu_tier F1/F2`。）

---

## 4. 故障模型 / C++ 发射器审计（现行源码 + 20fda 二进制）

### 4.1 源码：所有要求的 FaultType 均已实现并可到达

`CHAOS/gem5/src/arch/arm/CHAOSArmTLB/`（worktree 版本，与二进制源码树 `r6-f5-noeffect` 的 FaultType 集合相同）：

- `stringToFaultType`：`CHAOSArmTLB.cc:231-256` — 包含 `valid_clear / valid_set / global_flip / asid_subst`（L244-247）、`perm_subst / memtype_subst / pagesize_subst`（L249-251）、`false_hit / double_hit / wrong_way`（L253-255）、`walk_fill_dup / walk_done_early / walk_stale_result`（L240-242）、`walk_pairing`（L238）。
- 分类谓词：`CHAOSArmTLB.hh:203-222`（`isEntryStateFault` / `isAttrSubstFault` / `isCamFault` / `isWalkFamily`）。
- T05/T06 发射：`CHAOSArmTLB.cc:593-594`（`isEntryStateFault(chosen) || isAttrSubstFault(chosen)` → `applyEntryFieldFault`）；case 实现 `:836-935`（ValidClear/ValidSet/GlobalFlip/AsidSubst/PermSubst/MemTypeSubst/PageSizeSubst）。
- T07 发射：`maybeCorruptLookup` `:967-1080`（FalseHit/DoubleHit/WrongWay）。
- T08 发射：`maybeDropWalkFill` `:292-395`（`arm_tlb_walk_issue_probe` / `arm_tlb_walk_issue_drop` / `arm_tlb_walk_refill_armed`）、`maybeCorruptWalkRefill` `:729+`（`arm_tlb_walk_refill` / `arm_tlb_walk_refill_stale`）。
- 挂点：`src/arch/arm/tlb.cc:172,183`（`maybeCorrupt` / `maybeCorruptLookup`）、`src/arch/arm/table_walker.cc:337,2637`（`maybeDropWalkFill` / `maybeCorruptWalkRefill`）。**命中/缺失两条路径都调用了 T07 hook。**
- Site 字符串（日志/传播节点）：`:173 arm_tlb_lookup_tier`、`:314 arm_tlb_walk_issue_probe`、`:350 arm_tlb_walk_stale_no_previous`、`:364 arm_tlb_walk_refill_armed`、`:388 arm_tlb_walk_issue_drop`、`:643/:705 arm_tlb_lookup_hit`、`:764 arm_tlb_walk_refill_stale`、`:795 arm_tlb_walk_refill`、`:1051 arm_tlb_lookup`。

### 4.2 二进制 `20fda…` 的符号证据（真实命令 + 输出）

```bash
timeout 420 strings -a -n 6 .claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt > /tmp/r6bin.strings
# exit=0, 2,128,362 lines
grep -E '^arm_tlb_|Site: arm_tlb' /tmp/r6bin.strings | sort -u
```

真实输出（关键行）：

```
, Site: arm_tlb_lookup
, Site: arm_tlb_lookup_hit
, Site: arm_tlb_lookup_hit_skipped
, Site: arm_tlb_lookup_tier
, Site: arm_tlb_walk_issue_drop
, Site: arm_tlb_walk_issue_probe
, Site: arm_tlb_walk_refill
, Site: arm_tlb_walk_refill_armed
, Site: arm_tlb_walk_refill_stale
, Site: arm_tlb_walk_stale_no_previous
```

```bash
grep -xE 'valid_clear|valid_set|global_flip|asid_subst|perm_subst|memtype_subst|pagesize_subst|false_hit|double_hit|wrong_way|walk_pairing|walk_fill_dup|walk_done_early|walk_stale_result|bit_flip|stuck_at_zero|stuck_at_one|pfn_to_mapped_page' /tmp/r6bin.strings | sort -u
```

真实输出：**全部 18 个模式名均在二进制中**（`valid_clear valid_set global_flip asid_subst perm_subst memtype_subst pagesize_subst false_hit double_hit wrong_way walk_pairing walk_fill_dup walk_done_early walk_stale_result bit_flip stuck_at_zero stuck_at_one pfn_to_mapped_page`）。

```bash
grep -F 'CHAOS_LSU_TIER_CAP' /tmp/r6bin.strings | head
```

真实输出：`CHAOS_LSU_TIER_CAP: requested=`（能力标记已编译进二进制；源码契约见 `src/cpu/o3/chaos_lsu_tier_cap.hh:1-96`）。

**结论：不存在 CODE_GAP。** T05/T06/T07/T08 的“mode unimplemented / compile-unverified”叙述与当前二进制事实不符。

---

## 5. 逐 RunID 复核

历史证据根：主树 `runs/lsu/`（R6 权威根）；另注 worktree `runs/lsu/r4_t6_pilot2/` 的 T08-F0-W9（**不在**权威根内，`R6-STATUS-TABLE` 已如实标注）。

### 5.1 T05-F0-W4 — `TOOLING_GAP`

- 路由：默认 BLOCKED（`lsu_campaign.py:1591-1594`，`MODEL_BLOCKED["T05"]`）；trial 自动 RUNNABLE（`evidence_pilot`），screening 需 `--allow-blocked-models`。
- 命令：见 §3（`--tlb_fault_type valid_clear`，F0 legacy，无 tier flag）。
- 负载：设计负载 TLB-AliasPerm，**无任何可执行体**（`ls /workloads/directed | grep -i tlb` 输出 `NO TLB-AliasPerm binary`），由 FS 载波 `configs/fs/tlb_probe.rcS`（存在，1623 B）承载；这是 `lsu_campaign.py:744-749` 的既定设计，不是本格新增的替换。
- 模式：FS（`configs/fs/lsu_b0_fs.py` + B0 cpt）。
- 频率：F0 = legacy 单次（`--tlb_max_faults 1 --tlb_probability 1.0`），无 tier 标记；与 F2 真正不同（F2 有 `--tlb_lsu_tier F2`）。
- Ready contract：`chain.admitted=true`（`terminal=detected_contained`），但 `upstream_status=BLOCKED / FS-INFRA`。
- 历史证据：`runs/lsu/r6_tlb_pilot2/T05-F0-W4/cell_results.json` = `activated=1, Masked=1`，`seed1/armtlb_injections.log`：`Site: arm_tlb_lookup_hit, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear`；另有 `r6_tlb_pilot/out`、`r6_tlb_verify/out`（截断，`R6-STATUS-TABLE` 记 `2/3 流截断`）。该历史运行使用的是旧 worktree 二进制（`readfile=.../r6-tlb-hooks/configs/fs/tlb_probe.rcS`），不是 `20fda…`。
- 根因：`MODEL_BLOCKED` 的 “COMPILE-UNVERIFIED — build + FS pilot pending” 前提已被当前二进制（含全部符号）与 pilot（activated=1）证伪；阻塞纯属工具侧陈旧门。

### 5.2 T05-F2-W4 — `TOOLING_GAP`（残余：无观测）

- 路由/命令：同 5.1，但追加 `--tlb_lsu_tier F2`（F2 与 F0 真正不同）。
- 模式/负载/载波：同 5.1。
- Ready contract：`n_samples=0`（无 pilot），`chain.admitted=false`。
- 历史证据：`R6-STATUS-TABLE` → `state=NOT_RUN, samples=0`；`R6-FSINFRA-EVIDENCE.md` §“无逐格 FS pilot 产物的行（8）”明确列出 `T05-F2-W4`。
- 根因：同一陈旧 `MODEL_BLOCKED`；此外尚无该格观测（观测缺口是残余，不是主阻塞）。

### 5.3 T06-F0-W4 — `TOOLING_GAP`

- 路由：默认 BLOCKED（`MODEL_BLOCKED["T06"]`）；evidence-pilot RUNNABLE。
- 命令：`--tlb_fault_type perm_subst`（F0 legacy）。
- 源码：`PermSubst` case `CHAOSArmTLB.cc:869-886`；二进制含 `perm_subst`（§4.2）。
- 历史证据：`runs/lsu/r6_tlb_D_T06-F0-W4/T06-F0-W4/cell_results.json` = `activated=1, Timeout=1`（流截断）；`seed1/armtlb_injections.log`：`old_perm_subst: 2, new_perm_subst: 0, FaultType: perm_subst`。旧二进制（`r6-tlb-hooks`）。
- Ready contract：`chain.admitted=false`（`containment_on_unclosed_stream` + `no_closed_chain_and_no_containment`）。
- 根因：同 5.1 的陈旧 `MODEL_BLOCKED["T06"]`。

### 5.4 T06-F2-W4 — `TOOLING_GAP`（残余：无观测）

- 命令：`--tlb_fault_type perm_subst --tlb_lsu_tier F2`。
- 历史证据：`R6-STATUS-TABLE` → `NOT_RUN`；`R6-FSINFRA-EVIDENCE.md` 列为“无逐格 pilot”。
- 根因：同 5.3。

### 5.5 T07-F0-W4 — `TOOLING_GAP`

- 命令：`--tlb_fault_type false_hit`（F0 legacy）。
- 源码：`maybeCorruptLookup` `CHAOSArmTLB.cc:967-1080`；`FalseHit` case `:1042` 附近；二进制含 `false_hit`。
- 历史证据：`runs/lsu/r6_tlb_pilot2/T07-F0-W4/cell_results.json` = `activated=1, Timeout=1`（截断）；`armtlb_injections.log`：`Site: arm_tlb_lookup, CAM: miss -> hit, FaultType: false_hit`。旧二进制。
- Ready contract：`admitted=false`，`terminal=provable_to_L2_then_unknown`。
- 根因：陈旧 `MODEL_BLOCKED["T07"]`。

### 5.6 T07-F4-W4 — `TOOLING_GAP`（残余：无观测）

- 命令：`--tlb_fault_type false_hit --tlb_lsu_tier F4`。
- 历史证据：`NOT_RUN`；`R6-FSINFRA-EVIDENCE.md` 列为“无逐格 pilot”。
- 根因：同 5.5。

### 5.7 T08-F0-W4 — `TOOLING_GAP`

- 命令：`--tlb_fault_type walk_pairing --tlb_lsu_tier F0 --tlb_lsu_warmup_events 0 --tlb_lsu_span_events 1000`。
- 源码：`maybeDropWalkFill` `CHAOSArmTLB.cc:292-395`；`table_walker.cc:337` 调用；二进制含 `arm_tlb_walk_issue_drop` 等。
- 历史证据：`runs/lsu/r6_tlb_C_T08-F0-W4/T08-F0-W4/cell_results.json` = `activated=1, Timeout=1`（截断）；`seed1/armtlb_injections.log`：`arm_tlb_walk_issue_probe walk_id=1` → `arm_tlb_walk_issue_drop walk_id=703`（即 T08-a lost walk）。`R4-8-FS-W1-report.md` §4.3 另有 walk_id=703 配对记录。
- Ready contract：`admitted=false`（`containment_on_unclosed_stream`，流未 `chain_end` 收口）。
- 根因：`MODEL_BLOCKED["T08"]` 的“Block retained … deletion is an integration decision”。这不是代码缺失（模式已在二进制内且真机跑通），而是**工具/准入裁定**层面的保留；最小修复域属 campaign/准入，不是 C++。

### 5.8 T08-F4-W4 — `TOOLING_GAP`（残余：无观测）

- 命令：`--tlb_fault_type walk_pairing --tlb_lsu_tier F4 --tlb_lsu_warmup_events 0 --tlb_lsu_span_events 1000`。
- 频率：F4 与 F0 真正不同（F4 走真实 tier；F0 的 walk 家族也带 `--tlb_lsu_tier F0`，但 F0 是单次均匀抽取）。
- 历史证据：`NOT_RUN`。`R6-FSINFRA-EVIDENCE.md` 列为“无逐格 pilot”。注意 `runid_map` / `R6-FSINFRA-EVIDENCE.md` 的 `spec_landed` 记录里有一句 “F4-W9 honest zero, structurally (burst interval 1e5 eligible events >> ~1e3 walk-issue stream)”，这是**旧的 F4-W9 证据陈述**，不能等同为 F4-W4 的观测。
- 根因：同 5.7。

### 5.9 T08-F0-W9 — `WORKLOAD_GAP`（STOP）

- 矩阵设计负载：**GAP/Graph500 子集（BFS/SSSP/PageRank）**（CSV 行 130，列9；`runs/lsu/r6_matrix_325.csv` 同）。
- 路由实际：`resolve_cell` 在 `family == "armtlb"` 分支**不读取 workload**（`lsu_campaign.py:1604-1641`），一律返回 `--readfile configs/fs/tlb_probe.rcS`。因此 W9 与 W4 的 flags **逐字节相同**（仅 `--prop_run_id` 不同）。
- 当前运行到底用了什么：worktree 的非权威 pilot `.claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t6_pilot2/T08-F0-W9/seed1/config.ini` 实际写的是
  `readfile=.../configs/fs/tlb_probe.rcS`、`faultType=walk_pairing`、`lsuTier=F0`；
  `armtlb_injections.log` 为 `arm_tlb_walk_issue_drop walk_id=703`。
  **即：W9 没有跑 GAP/Graph500，而是跑了 tlb_probe 载波。**
- GAP 可执行体：`workloads/directed/gap_bfs` 存在（ELF aarch64 static，`file` 输出确认），但那是 **SE** 载体；T08 的 `TLB::lookup` 注入是 **FS-only**（`CHAOSArmTLB.py:56-59` 注释：SE 走 `translateSe`，不调用 `TLB::lookup` — W1 ③）。FS 镜像中没有 GAP 可执行体，所以 GAP 在 FS 不可达。
- 结论：W9 的设计负载无法被当前平台诚实表达；任何修复都必须“改 XLSX 负载定义 / 替换负载 / 改平台语义”之一 → 按任务规则 **STOP，不提出修复**。

### 5.10 T08-F4-W9 — `WORKLOAD_GAP`（STOP）

- 与 5.9 同因（只是 tier 改为 F4）；`R6-STATUS-TABLE` 中该格 `upstream_category=MODE-UNIMPL`，但 runid_map 的 `spec_landed` 又写 “walk_pairing implemented”。当前没有任何权威运行；`R6-FSINFRA-EVIDENCE.md` 将其列入“无逐格 pilot”。
- STOP：同 5.9。

### 5.11 T10-F0-W4 — `ALREADY_RUNNABLE`

- 路由：**默认即 RUNNABLE**（`T10` 在 `MODEL_FLAGS`，`lsu_campaign.py:549`；`TLB-AliasPerm` 对 `ARMTLB_MODELS` 放行）。
- 命令：`--tlb_fault_type bit_flip`（F0 legacy；无 tier flag），载波 `configs/fs/tlb_probe.rcS`。
- 频率：F0 与 F1/F2 真正不同（F1/F2 有 `--tlb_lsu_tier`）。
- 历史证据：`runs/lsu/r6_tlb_E_T10-F0-W4`（Timeout=1，截断）与 `runs/lsu/r6_tlb_F_T10-F0-W4`（Masked=1，完整；`armtlb_injections.log`：`old_pfn: 0x81d75, new_pfn: 0x100000000081d75, FaultType: bit_flip`）。旧二进制。`R6-12RUNID-TABLE.md` 第 10 行记 T10-F0-W4 `COMPLETE / detected_contained / provable_to_L3 / admitted=False`。
- 阻塞的真相：CSV/coverage 的 `blocked(fs-infra: TLB workload needs FS)` 是**纯陈旧状态**；当前 `resolve_cell` 已返回 RUNNABLE，`runid_map` 的 `status_reasons` 也自认该 workload 键是 `refuted(stale workload-level claim ...)`。

### 5.12 T10-F1-W4 — `ALREADY_RUNNABLE`

- 路由：默认 RUNNABLE；`--tlb_fault_type bit_flip --tlb_lsu_tier F1`。
- 能力标记：同模型的 T10-F1-W1 在 `20fda…` 上真实打印
  `CHAOS_LSU_TIER_CAP: requested=F1 effective=F1 lookup_tier_enabled=1`
  （`runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/run.out`），且 `cell_results.json` 有完整链（`terminal=full`）；`R6-AUTHORITATIVE-EVIDENCE.md:66-68` 记 3 seeds `COMPLETE_L5`。
- 历史 W4 证据：`R5-FS-PILOT-EVIDENCE.md §1`（activated=1, Masked）；权威根无流（`R6-12RUNID-TABLE.md` 第 11 行 `MISSING`）。
- 阻塞真相：同 5.11（陈旧 status）。修复=重新排期/刷新状态，无需代码。

### 5.13 T10-F2-W4 — `ALREADY_RUNNABLE`

- 路由：默认 RUNNABLE；`--tlb_fault_type bit_flip --tlb_lsu_tier F2`。
- 能力标记：`CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`（`runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/run.out`）；`R6-AUTHORITATIVE-EVIDENCE.md:69-71` 记 3 seeds `COMPLETE_L5 / COMPLETE_CONTAINED_L4`。
- 历史 W4 证据：`R5-FS-PILOT-EVIDENCE.md §1`（activated=1, Masked）；权威根无流。
- 阻塞真相：同 5.11。

---

## 6. 根因分组（A–E）

### A. T05 entry-state（T05-F0-W4, T05-F2-W4）— TOOLING_GAP
- 共享根因：`MODEL_BLOCKED["T05"]`（`tools/lsu_campaign.py`）+ runid_map/coverage 的 `campaign:deferred(... COMPILE-UNVERIFIED)` 状态。源码 case 与二进制符号齐备（§4），T05-F0 pilot 真机 activated=1。
- 不是 spec/负载问题：TLB-AliasPerm→tlb_probe 是既定的 T 系列载波（`lsu_campaign.py:744-749`）。

### B. T06 attribute-substitution（T06-F0-W4, T06-F2-W4）— TOOLING_GAP
- 共享根因：`MODEL_BLOCKED["T06"]` + 同一陈旧状态。`perm_subst` 已实现并真机注入过（`old_perm_subst 2 → new_perm_subst 0`）。

### C. T07 CAM/way-select（T07-F0-W4, T07-F4-W4）— TOOLING_GAP
- 共享根因：`MODEL_BLOCKED["T07"]` + 同一陈旧状态。`false_hit` 已实现并真机注入过（`CAM: miss -> hit`）。

### D. T08 page-walk（T08-F0-W4, T08-F4-W4 = TOOLING_GAP；T08-F0-W9, T08-F4-W9 = WORKLOAD_GAP/STOP）
- W4：仅 `MODEL_BLOCKED["T08"]` + `T08-b/c/d` 覆盖裁定（“deletion is an integration decision”）。T08-a 已实现、二进制有符号、真机 walk_id=703 配对。
- W9：设计负载 GAP/Graph500；现行路由用 `tlb_probe.rcS` 替代，W9 与 W4 flags 逐字节相同（§5.9）。这是**负载语义替换**，必须裁决 → STOP。

### E. T10 W4 vs W1（T10-F0/F1/F2-W4）— ALREADY_RUNNABLE
- **W1 为什么“完成”而 W4 被标阻塞**：`T10` 是 `armtlb` 家族，`resolve_cell` 对 **W1 与 W4 都走同一条 FS 分支**（`:1604`），**根本不读 W1/W4 的负载字段**；两者唯一的差别是频率档位。实际证据：`runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/config.ini` 的 `readfile=.../configs/fs/tlb_probe.rcS`（不是 MiBench），`faultType=bit_flip`。W1 之所以完成，是因为它在 R6 排期里被选中执行（`r6_n8`），而 W4 三格从未进入权威排期；CSV/coverage 把 W4 标成 `blocked(fs-infra: TLB workload needs FS)`，而当前 `resolve_cell` 对 W4 三格均返回 RUNNABLE。
- 因此：**W4 的阻塞是纯陈旧 route/status**，不是物理/代码/负载差异。`T10-F0-W4` 已有旧二进制真机结果；`F1/F2-W4` 只差一次排期（同模型的 W1 已在 `20fda…` 证明 F1/F2 tier 真实生效）。

---

## 7. 频率档位审计

| 家族/模式 | F0 | F1/F2/F4 | 是否真正不同 | 证据 |
|---|---|---|---|---|
| T05/T06/T07/T10 lookup | legacy：`--tlb_max_faults 1 --tlb_probability 1.0`，无 tier flag | `--tlb_lsu_tier <F>` | **是** | `lsu_campaign.py:735-742,1615-1640` |
| T08 walk | `--tlb_lsu_tier F0 --tlb_lsu_warmup_events 0 --tlb_lsu_span_events 1000` | `--tlb_lsu_tier F1..F6`（同 warmup/span） | **是** | `lsu_campaign.py:587-601,1615-1623` |
| 运行时证明 | `CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0` | `requested=F1 effective=F1 lookup_tier_enabled=1`；`F2 → F2 / 1` | **是** | `runs/lsu/r6_n8_T10-F{0,1,2}-W1_s1/.../seed1/run.out` |

> 结论：现行树**没有**把 F2/F4 退化成 F0；R6-FTIER + R6-FIXCPP 的 lookup tier 门已在 `20fda…` 真实生效。唯一的历史污染是：旧的 T 系列 pilot（T05-F0/T06-F0/T07-F0/T08-F0/T10-F0）都在旧二进制上，且旧二进制没有这个能力标记；它们只能作为 F0 证据，不能外推到 F2/F4。

---

## 8. 历史 pilot 证据清点（“unregistered/非权威”部分）

| RunID | 磁盘证据 | 是否在权威根 `runs/lsu/` | 二进制时代 | 结论 |
|---|---|---|---|---|
| T05-F0-W4 | `runs/lsu/r6_tlb_pilot2/T05-F0-W4`（activated=1, Masked=1）；`r6_tlb_pilot/out`、`r6_tlb_verify/out`（截断） | 是（但流截断/旧） | 旧（r6-tlb-hooks） | 可作 pilot，不构成 20fda formal |
| T05-F2-W4 | 无 | — | — | 未观测 |
| T06-F0-W4 | `runs/lsu/r6_tlb_D_T06-F0-W4`（activated=1, Timeout=1） | 是（截断） | 旧 | pilot |
| T06-F2-W4 | 无 | — | — | 未观测 |
| T07-F0-W4 | `runs/lsu/r6_tlb_pilot2/T07-F0-W4`（activated=1, Timeout=1） | 是（截断） | 旧 | pilot |
| T07-F4-W4 | 无 | — | — | 未观测 |
| T08-F0-W4 | `runs/lsu/r6_tlb_C_T08-F0-W4`（activated=1, Timeout=1）；`r6_tlb_verify/out` | 是（截断） | 旧 | pilot；walk_id=703 |
| T08-F4-W4 | 无 | — | — | 未观测 |
| T08-F0-W9 | `.claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t6_pilot2/T08-F0-W9`（activated=1, Timeout=1；`tlb_probe.rcS`，**非 GAP**） | **否**（worktree 草稿根；`R6-STATUS-TABLE` 已标 `outside runs root`） | 未记录（非 20fda） | 不可作为 W9/GAP 证据 |
| T08-F4-W9 | 无 | — | — | 未观测 |
| T10-F0-W4 | `runs/lsu/r6_tlb_E_T10-F0-W4`（Timeout=1）、`r6_tlb_F_T10-F0-W4`（Masked=1, 完整） | 是 | 旧 | pilot；`R6-12RUNID-TABLE` 已重判 |
| T10-F1-W4 | `R5-FS-PILOT-EVIDENCE.md §1`（activated=1） | 否（文档锚点） | 旧 | pilot |
| T10-F2-W4 | `R5-FS-PILOT-EVIDENCE.md §1`（activated=1） | 否（文档锚点） | 旧 | pilot |

`R6-AUTHORITATIVE-EVIDENCE.{md,json}`（20fda 权威根）只覆盖 **T10-F0/F1/F2-W1**，**不包含任何 W4 格**（`python3` 计数：13 个 RunID 在 JSON 中出现 0 次）。

---

## 9. 最小修复集（按“单一文件域”归属）

> 以下只是**提案**；本次不实现、不提交。所有修复都不改 XLSX 实验定义、不改 FaultType、不改负载语义、不替换负载。

### FIX-1 — campaign 路由门（域：`tools/lsu_campaign.py`）
- 目标：让 T05/T06/T07/T08（8 格中的 6 个非 W9 格）在 screening/formal 也能走已落地的证据路径，而不是只在 `--phase trial` 自动放行。
- 具体：把 `EVIDENCE_PILOT_MODELS` 的放行条件从“仅 trial”扩展为“trial + screening（或由显式 formal allowlist 控制）”，或把 `MODEL_BLOCKED["T05"/"T06"/"T07"]` 中已被证伪的 “COMPILE-UNVERIFIED” 条目删除/改写；`T08` 的 “deletion is an integration decision” 保留到裁定（见 STOP-2）。
- 依据：`tools/lsu_campaign.py:1591-1594, 2500-2502, 581`；二进制符号（§4.2）；pilot（§5.1/5.3/5.5/5.7）。

### FIX-2 — 台账/状态重生成（域：`tools/lsu_runid_map.py` → `docs/gem5-fi/lsu/mdspec/{runid_map.json,coverage_matrix.md,ready_contract.json}`）
- 目标：清除 13 格的陈旧 `blocked(fs-infra: TLB workload needs FS)` / `COMPILE-UNVERIFIED` / `MODE-UNIMPL` 状态，使 coverage 与 `resolve_cell` 的事实一致。
- 具体：在 FIX-1 之后重跑 `lsu_runid_map.py` + `lsu_coverage_matrix.py` + ready-contract 生成；`T10-W4` 三格应从 workload-blocked 改为 runnable；`T05–T08-W4` 应从 “mode unimplemented” 改为 “landed, evidence pending/available”。
- 依据：`coverage_matrix.md:65-79,259-267`；`runid_map.json` 的 `status_reasons`（自认 stale）；`resolve_cell` 实测（§3）。

### FIX-3 — 排期/批处理（域：`tools/lsu_r6_schedule.sh` + `docs/gem5-fi/lsu/mdspec/R6-BATCH-PLAN.md`）
- 目标：把 **T10-F0/F1/F2-W4** 与 FIX-1 放行后的 **T05/T06/T07/T08-W4** 真正纳入下一批 authority 运行；使用 `LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs`（worktree 无 `gem5-fs/`）与 `20fda…` 二进制。
- 依据：`R6-BATCH-PLAN.md` §1（`--phase screening`、`--fs-timeout 2700`、`LSU_GEM5_BIN`/`LSU_FS_DIR` 约定）；`runs/lsu/r6_n8_T10-F0-W1_s1/manifest.json`（同形命令）。
- 对 T10-W4：**无需任何代码改动**，只需排期；`ALREADY_RUNNABLE`。

### 运维前置（不是代码修复）
- FS 资产必须通过 `LSU_FS_DIR` 指向主树（`tools/lsu_campaign.py:71-86,130-137`；`gem5-fs/` 在主树存在、worktree 为空）。

---

## 10. STOP（不提出修复的组）

> 边界说明：W4 的 `TLB-AliasPerm → tlb_probe.rcS` 载波替换是**既有的 T 系列设计**（T01–T04 的已跑格也走同一载波，`lsu_campaign.py:744-749`），本报告的 FIX 集不触碰它；若 spec owner 认为该既成替换本身也需要重新裁决，则 W4 组同样应转入 STOP（本报告不替该决定背书）。

### STOP-1 — T08-F0-W9 / T08-F4-W9（GAP/Graph500）
- 设计负载是 GAP/Graph500；GAP 只有 SE 可执行体（`workloads/directed/gap_bfs`），而 T08 的 TLB 注入是 FS-only（`CHAOSArmTLB.py:56-59`；SE 不调 `TLB::lookup`）。FS 载波永远是 `tlb_probe.rcS`，所以 W9 与 W4 的 flags 逐字节相同（§5.9），W9 的“GAP”条件在现平台不可表达。
- 任何修复都需“改 XLSX 负载定义 / 替换为另一负载 / 改 FS 平台语义”，按任务规则 **STOP**。由 spec owner 裁决：接受“W9=W4 同载波”并改写定义，或提供 GAP 的 FS 可执行体/新载波。

### STOP-2 — T08-F0-W4 / T08-F4-W4 的 `T08-b/c/d` 覆盖裁定（非阻塞修复，但属准入决定）
- 矩阵的 T08 时序模型包含四个子模型；campaign 每格默认只跑 `walk_pairing`（T08-a，`lsu_campaign.py:558`）。若 RunID 被要求覆盖全部子模型，则需 spec/准入裁定“单默认子模型是否足够”；这不属于可以静默替换的工程修复，故列为决策项（不阻断 T08-a 的 W4 运行）。

---

## 11. 复现命令（只读）

```bash
# 1) 13 格矩阵行
python3 -c "import csv; ...  # 见本文 §2（读取 artifacts/lsu-trial/07-expanded-matrix-backfilled.csv）"

# 2) 现行路由（不运行 gem5）
python3 - <<'EOF'
import sys, csv
sys.path.insert(0,'/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/tools')
import lsu_campaign as LC
rows=list(csv.reader(open('/home/sdc/gem5-fi-ding/artifacts/lsu-trial/07-expanded-matrix-backfilled.csv',encoding='utf-8')))
for r in rows[1:]:
    if r[1].startswith(('T05','T06','T07','T08','T10')):
        print(r[1], LC.resolve_cell(r)[0] is not None, LC.resolve_cell(r, evidence_pilot=True)[0] is not None)
EOF

# 3) 二进制符号
timeout 420 strings -a -n 6 .claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt > /tmp/r6bin.strings
grep -xE 'valid_clear|perm_subst|false_hit|walk_pairing' /tmp/r6bin.strings
grep -F 'Site: arm_tlb_walk_issue_drop' /tmp/r6bin.strings

# 4) 能力标记（已在盘上的 20fda 运行）
grep -h 'CHAOS_LSU_TIER_CAP' runs/lsu/r6_n8_T10-F{0,1,2}-W1_s1/T10-F*-W1/seed1/run.out

# 5) 历史 pilot
cat runs/lsu/r6_tlb_pilot2/T05-F0-W4/seed1/armtlb_injections.log
cat runs/lsu/r6_tlb_D_T06-F0-W4/T06-F0-W4/seed1/armtlb_injections.log
cat .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t6_pilot2/T08-F0-W9/seed1/armtlb_injections.log
grep readfile .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t6_pilot2/T08-F0-W9/seed1/config.ini
```

---

## 12. 诚实边界

1. 本次**没有运行 gem5**；`ALREADY_RUNNABLE` / `TOOLING_GAP` 是静态路由 + 二进制符号 + 磁盘证据的判定，不代表新一轮运行一定产生完整 L5 链。
2. 现有 T05/T06/T07/T08/T10-W4 pilot 全部来自旧二进制（`r6-tlb-hooks` / `7d52bc…`），**不是** `20fda…`；它们只证明“模式可发射/可激活”，不证明 `20fda…` 下的 formal 结果。
3. `20fda…` 的源码树（`d1543872`）与当前 worktree HEAD（`de81266c`）不是父子关系（`git merge-base --is-ancestor` 返回非祖先）；本文的“源码已实现”同时核对了**当前 worktree 源码**与**二进制源码树的 FaultType 集合**（相同），但未做逐字节等价性证明。
4. T08-W9 的 GAP 负载在 SE 也不可用（TLB 注入 SE 不触发）；这不是“换 SE 就能跑”的问题。
5. `ready_contract.json` 的 `status.BLOCKED=325` 是上游台账口径；`chain.admitted` 是另一条正交证据轴。本文同时报告两者，不把任一方当作“可运行”的唯一依据。
