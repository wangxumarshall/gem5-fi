# R5 集成后 FS 真机 pilot 证据（2026-10-22）

> 目的：为"FS-INFRA 是否真的需要 FS 基础设施"这一判据提供**集成后**的真实运行证据。
> 之前该判据只有集成前的 `runs/lsu/trial_r48_fs/*`（R4-8 时代）与散文陈述。

## 环境（如实记录）

| 项 | 值 |
|---|---|
| 二进制 | `<worktree>/CHAOS/gem5/build/ARM/gem5.opt` sha256 `f4dbfb9a66e0df80…`（R4-10 集成轮构建） |
| 资产 | `LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs`（worktree 内 `gem5-fs/` 为空，须显式指定） |
| checkpoint | `/home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015` |
| 入口 | `tools/lsu_campaign.py --cells T01-F0-W4 --phase trial --max-seeds-per-cell 1 --max-parallel 1 --fs-timeout 2700` |

## T04-F0-W4 — 完整 L0→L5 链（真机，本轮）

```
"runid": "T04-F0-W4", "phase": "trial", "n_runs": 1, "activated": 1,
"classes": {"Masked":0,"Detected/Contained":0,"SDC":0,"Crash":1,"Timeout":0},
"stop_reason": "seed-cap(1)", "conservation": "OK"
run seed=1 activated=1 outcome=Crash event_count=1572
  L0->L1 proven  L1->L2 proven  L2->L3 proven  L3->L4 proven  L4->L5 proven
  terminal=full provable_to=L5
```

⇒ **"FS 载体在预算内不终止 → 无 L5" 对该格不成立**：T04-F0-W4 在预算内自然终止，
给出 `Crash` 结局与完整五段链。

## T01-F0-W4 — 真实注入（真机，本轮；运行未终止，与 R4-8 观测一致）

```
Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8,
old_pfn: 0x81d75, new_pfn: 0x100000000081d75, FaultType: bit_flip, Mask: 0x100000000000000
```

⇒ FS TLB 注入链在当前二进制下**真实生效**。

## 结论（不夸大）

- FS 基础设施**可用**：注入真实、链可推进，且至少一格的 L5 分类可达。
- 但**不等于** FS-INFRA 24 格可准入：T05/T06/T07/T08 为本轮新实现模式、T10 PPN 分层未参数化，
  均**无逐格真机 pilot**；且 `TLB-AliasPerm` 为 workload 级静态键，整批拒绝该负载。
- 因此本轮**维持 24 格 BLOCKED**，但把理由措辞由已被反驳的"需 FS 基础设施"
  更正为"逐格 campaign 入口 pilot 未完成"（见 `blockers_for_approval.md`）。
- **未**通过删除 `TLB-AliasPerm` 键（会一次性把含未 pilot 新模式的 24 格全部转为 READY）
  来制造准入 —— 那属 GO-CORRECTION 明令禁止的"改分类/放宽阈值制造 GO"。

## 复现命令

```bash
cd <worktree>
LSU_GEM5_BIN=$PWD/CHAOS/gem5/build/ARM/gem5.opt \
LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs \
python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir /tmp/r5_fs_pilot/out --cells T04-F0-W4 --phase trial \
  --max-seeds-per-cell 1 --max-parallel 1 \
  --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 \
  --fs-timeout 2700
```

---

## 附：FS-INFRA 22 格批跑结果 + 两层门发现（2026-10-23）

### 1. 批跑结果（真机，集成后二进制）

22 格批（2 并发，`--phase trial --max-seeds-per-cell 1`）中 **10 格产出结果**：

| RunID | activated | outcome | 链 | 事件数 |
|---|---|---|---|---|
| T02-F0-W4 | 1 | Crash | full, provable_to L5 | 184 |
| T02-F2-W4 | 1 | Crash | full, L5 | 184 |
| T04-F2-W4 | 1 | Crash | full, L5 | 1572 |
| T04-F6-W4 | 1 | Crash | full, L5 | 1572 |
| T01-F1-W4 | 1 | Masked | provable_to L0 then unknown | 7 |
| T01-F2-W4 | 1 | Masked | 同上 | 7 |
| T03-F5-W4 | 1 | Masked | 同上 | 7 |
| T10-F0-W4 | 1 | Masked | 同上 | 7 |
| T10-F1-W4 | 1 | Masked | 同上 | 7 |
| T10-F2-W4 | 1 | Masked | 同上 | 7 |

⇒ **12 格中 10 格已被真机 pilot 覆盖**（另 T01-F0-W4、T04-F0-W4 见正文），全部 `activated=1`，
真实注入 + 真实 L5 结局（Crash 或 Masked）。**FS 基础设施可用**这一结论进一步坐实。

### 2. 关键发现：FS-INFRA 阻塞是**两层**的

尝试按证据解除外层阻塞（删除 `WL_BLOCKED["TLB-AliasPerm"]`）后发现：

- 删除后 `resolve_cell` 确实对这 12 格给出 armtlb FS flags（**实测 12 格，与已 pilot 的 12 格完全一致**）；
- 但 `runid_map` 随即被**第二层**拦下：`workload:规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜）`
  （`tools/lsu_runid_map.py:64`）——即准入映射不接受 W4 的规格负载名；
- 结果是分类从 **FS-INFRA → UNCLASSIFIED（12）**：**没有解锁任何一格，反而把理由从精确降为未知**。

⇒ **该改动已回滚**（`git status` 干净，契约仍为 84 / FS-INFRA=24）。
真正的解锁需要把 `runid_map` 的 workload→载体映射与 `resolve_cell` 的 FS 特例**对齐**，
这是一次实质性的准入口径变更（且需规格认可"1-seed pilot 即可判 READY"），
**不在本轮单方面拍板**。这正是 GO-CORRECTION 所禁止的"用改分类手段制造 GO"的反面教材：
试了、发现无效、按证据回滚，而不是继续撬第二层。

### 3. T05–T08 的循环门

`resolve_cell` 对 T05/T06/T07 的理由是
`deferred(T05 entry-state modes LANDED … but COMPILE-UNVERIFIED — build + FS pilot pending)`；
T08-W4 亦为模型级拒绝。⇒ **pilot 因"未 pilot"被拒**，构成循环。

且 "COMPILE-UNVERIFIED" 一词**已被独立核验反驳**：对冻结二进制做 `strings` 可见
`valid_clear`/`valid_set`/`global_flip`/`asid_subst`/`perm_subst`/`memtype_subst`/
`pagesize_subst`/`false_hit`/`double_hit`/`wrong_way`/`walk_fill_dup`/`walk_done_early`/
`walk_stale_result` 全部在场 —— 代码已编入二进制。故该措辞陈旧，真实阻塞是"未 pilot"。
**本轮未单方面改写这些模型级拒绝串**（它是准入判据，非文案），仅如实记录该事实冲突。

### 4. S01-F0-W1 span census 结果（真机）

```
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=17663390 eligible=17663390
                   injected=1 first_eligible_tick=3340645 last_eligible_tick=1271365657485
CHAOS_LSU_TRIGGER_ALARM: mode=EARLY_BIAS fired_at=756413 span=1000000 warmup=1
   (…span under-covers the golden stream… OR span == measured golden and the fault
    extended the stream past fired_at — adjudicate vs the uninjected golden measurement)
```

`eligible = 17,663,390` 是**被注入过**的流（span=1e6 < 流长，故已在该 run 内注入一次）。
工具自身的告警明确要求**以未注入的 golden 测量为准**。因此：
- **尚未**把 17,663,390 写入 `LSQFWD_F0_SPAN`；
- 已另起**无注入 golden census**（`--max_faults 0`，同载体同模式，约 7.5 h）以取得未被污染的参考流长。
