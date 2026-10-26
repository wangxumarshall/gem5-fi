# R4-10-FSINFRA agent 报告：T05/T06/T07 模式实现 + T08-b/c/d 配对 + FS-INFRA 24 项分类

> 执行者：R4-10-FSINFRA subagent（worktree `.claude/worktrees/r4-10-fsinfra`，
> 分支 `r4-10-fsinfra`，基线 `lsu-mdspec-20261019` @ `d63a5dd8`）。
> 基线之上 2 个 commit：`3e64f291`（T05/T06/T07）、`3db770fb`（T08-b/c/d）。
> **本报告只写已实测的内容。** C++ 改动为 **COMPILE-UNVERIFIED**（本 worktree 明令
> 禁 build/禁跑正式 campaign）；真机 FS pilot 交主 agent 构建后执行。
> 本报告为**新增**文件，未改动任何共享证据（`blocked_triage.md` / `ready_contract.*`
> / `coverage_matrix.md` / `runs/` / `artifacts/` 一律未动）。

## 1. 交付的 commit

| # | SHA | 内容 |
|---|---|---|
| 1 | `3e64f291` | T05/T06/T07 表项状态/属性/CAM 模式实现（CHAOSArmTLB + tlb.cc + CHAOSPropagation `tlb_state` + config/campaign 路由 + 契约测试） |
| 2 | `3db770fb` | T08-b/c/d walk/refill 配对子模型（refill 完成钩子 + 自描述 outcome + 路由 + 契约测试） |

新增契约测试：`tests/test_lsu_hook_t05_state.py`、`tests/test_lsu_hook_t08_pairing.py`。
原计划：`docs/superpowers/plans/2026-10-22-r4-10-fsinfra-tlb-modes.md`。

## 2. 逐 RunID 四类分类（(a) 服务器侧可运行/可实现 → 已实现；(b) 缺实现；(c) 缺载体；(d) 真外部阻塞）

### FS-INFRA 24 项（blocked_triage 归为 "FS-INFRA"）

| RunID | 分类 | 证据 / 理由 | 状态 |
|---|---|---|---|
| T01-F0-W4 | **(a)** | lookup 系 `bit_flip` 早已实现；`CHAOSArmTLB.walker=None` 配置 bug 已由 R4-6.0 修复 → campaign 真机 `activated=1 sdc=0 cons=OK`（round4_findings §R4-8-FS-W1，binary `7d52bc1392a10055`）。旧 "需 FS 基础设施" 理由**已证伪** | 可运行（无需本轮改动） |
| T01-F1-W4 | **(a)** | 同 T01-F0-W4（模式 = bit_flip，carrier = fs:tlb_probe，tier=F1 由 campaign 门控） | 可运行 |
| T01-F2-W4 | **(a)** | 同上 | 可运行 |
| T02-F0-W4 | **(a)** | `bit_flip` + `--tlb_bits_to_change 2`（2-bit）已在 MODEL_FLAGS；模式同族已实现 | 可运行 |
| T02-F2-W4 | **(a)** | 同上 | 可运行 |
| T03-F5-W4 | **(a)** | `stuck_at_zero`（stuck1 按 seed parity）已在 MODEL_FLAGS；模式已实现 | 可运行 |
| T04-F0-W4 | **(a)** | `pfn_to_mapped_page`（§2.10 F5）已实现 → R4-6.0 真机 `activated=1`（§R4-8-FS-W1：T04-F0-W4 activ=1） | 可运行 |
| T04-F2-W4 | **(a)** | 同上 | 可运行 |
| T04-F6-W4 | **(a)** | 同上 | 可运行 |
| **T05-F0-W4 / T05-F2-W4 / T05-F6-W4** | **(b)→已实现** | 原 "mode unimplemented: valid/global/ASID state"。本轮 C1 在 CHAOSArmTLB 实现 `valid_clear/valid_set/global_flip/asid_subst` + `tlb_state` 节点 + 路由 | 实现完成，**待主 agent 构建** |
| **T06-F0-W4 / T06-F2-W4 / T06-F6-W4** | **(b)→已实现** | 原 "permission legal-substitution"。C1 实现 `perm_subst/memtype_subst/pagesize_subst`（合法域：取同 TLB 另一条 live 表项；PPN 不变） | 实现完成，**待构建** |
| **T07-F0-W4 / T07-F4-W4 / T07-F6-W4** | **(b)→已实现** | 原 "hit fabrication/way select"。C1 实现 `false_hit/double_hit/wrong_way`（新增 `maybeCorruptLookup`，tlb.cc 对 miss/hit 均调用） | 实现完成，**待构建** |
| T08-F0-W4 / T08-F4-W4 / T08-F6-W4 | **(a)** | `walk_pairing`（T08-a）已实现并经 R4-6-T08 真机证（F0-W4 seed1 `walk_id=703` 全判据；F6-W9 亦真机）。F4-W4/F4-W9 为 **结构性诚实零**（F4 burst interval 1e5 ≫ walk-issue 流 ~1e3，probe 行证明钩子到达、无 drop 行） | 模式/载体就绪；F4 结构性零 |
| T10-F0-W4 / T10-F1-W4 / T10-F2-W4 | **(a) + 残余(b)** | 可运行，但 campaign 现用 `bit_flip` **近似** T10；spec 的 T10-a/b/c（PPN 低/中/高位**分层**）**未参数化** → 残余 (b)。MODEL_FLAGS 已诚实注明 "approx: no banding submodel" | 可运行(近似)；banding 子模型未实现 |

### T08-W9 三项（本轮任务点名）

| RunID | 分类 | 证据 |
|---|---|---|
| T08-F0-W9 | **(a)** | R4-6-T08 真机：`arm_tlb_walk_issue_probe` + `arm_tlb_walk_issue_drop walk_id=703` + prop_evt `tlb_walk`/`tlb_refill` 同 walk_id=703/fault_id=1、refill `field=lost outcome=lost`、activated=1 |
| T08-F4-W9 | **(a)** | 结构性诚实零（见上，F4 interval 语义） |
| T08-F6-W9 | **(a)** | §R4-8-SPEC §B.3 真机：F6 首次 walk 即注入、drop `walk_id=1` 与 probe 同 tick、activated=1 |
| T08-b/c/d（模式） | **(b)→已实现** | 本轮 C4：`walk_fill_dup`（重复 refill）/`walk_done_early`（done 过早，数据正确）/`walk_stale_result`（写入上一条 walk 结果）；walk_id 配对 + refill field/outcome 自描述 |

**分类结论**：24 项 FS-INFRA 中 **15 项属 (a) 服务器侧可运行**（T01×3/T02×2/T03×1/T04×3/T10×3/T08×3），
旧 "FS-INFRA" 阻塞理由对它们**已被 R4-6.0 + R4-8-FS-W1 真机证伪**；
**9 项 (T05/T06/T07 ×3) 原属 (b)，本轮已实现**。**无一项属 (c) 缺载体或 (d) 真外部阻塞**——
carrier `fs:tlb_probe` + checkpoint `runs/lsu/fs_cpt_boot/cpt.237949797015` 均在盘上。

**残余 (b)**：T10 的 PPN 位带分层子模型（T10-a/b/c）未参数化（现为 bit_flip 近似）。

## 3. 从正式 campaign 入口逐项复证命令（主 agent 构建后）

前置：`build/ARM/gem5.opt` 已按 §4 重建；checkpoint 存在。

```bash
cd /home/sdc/gem5-fi-ding        # 主 worktree（集成后）
# (a) lookup 系 + 新 T05/T06/T07 + T08（T05/T06/T07/T08 需 --allow-blocked-models）
LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir runs/lsu/r4_10_fsinfra --phase trial --max-seeds-per-cell 3 --max-parallel 1 \
  --fs-timeout 3600 --allow-blocked-models \
  --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 \
  --cells T01-F0-W4,T03-F5-W4,T04-F0-W4,T10-F0-W4,\
T05-F0-W4,T05-F2-W4,T05-F6-W4,T06-F0-W4,T06-F2-W4,T06-F6-W4,\
T07-F0-W4,T07-F4-W4,T07-F6-W4,T08-F0-W4,T08-F6-W4
```

判据（每 cell）：
1. `armtlb_injections.log` 非空，且：
   - T01/T02/T03/T04/T10：`Site: arm_tlb_lookup_hit` + `old_pfn != new_pfn`（或 pfn_to_mapped_page 的 `new_pfn`）。
   - **T05/T06/T07**：`Site: arm_tlb_lookup_hit`（T05/T06）或 `Site: arm_tlb_lookup`（T07），
     行含 `FaultType: <子模型名>`；prop_evt 出现 `kind=tlb_state`（L2）且 `field` = 子模型名、
     `state_before/state_after` 非空。
   - **T08**：`Site: arm_tlb_walk_issue_probe` + `walk_issue_drop|refill_armed|refill` 之一；
     prop_evt 含 `kind=tlb_walk` 与 `kind=tlb_refill` 同 `walk_id`+`fault_id`，
     refill `outcome ∈ {lost, duplicated, early_done, stale}`。
2. `chain_report.json` 的 `terminal`：lookup 系期望 `provable_to` 达 L2 及以上；T08-a 期望
   `provable_to=L0`、`beyond=Unknown`（丢失 walk 的诚实终局，**不得推断 Masked**）。
3. 分类器 `activated = count_armtlb_injections()`（已排除 `_probe`/`_skipped` 诊断行）≥1。

T08-b/c/d 子模型单独复证（把 `--tlb_fault_type` 换成 `walk_fill_dup` /
`walk_done_early` / `walk_stale_result`，仍需 `--chaos_armtlb --tlb_lsu_tier F0/F4/F6`）：
```bash
build/ARM/gem5.opt --outdir=/tmp/t08b configs/se/arm_chaos_fs.py \
  --kernel gem5-fs/vmlinux --disk gem5-fs/ubuntu.img --bootloader gem5-fs/boot.arm64 \
  --cpu O3 --readfile configs/fs/tlb_probe.rcS --ckpt-first-clock \
  --chaos_armtlb --tlb_fault_type walk_fill_dup --tlb_probability 1.0 --tlb_max_faults 1 \
  --tlb_lsu_tier F0 --tlb_lsu_warmup_events 0 --tlb_lsu_span_events 1000 \
  --chaos_propagation ...
```
（或直接经 campaign：`MODEL_FLAGS` 只带默认子模型，其余子模型用上面的显式 flag 形式；
`WALK_FAULT_TYPES` 早失败门会保证缺 tier/walker 时**响亮拒绝**。）

## 4. 待主 agent 构建清单（文件 + 改动点 + 建议验证命令）

C++ 改动共 5 个文件（全部 COMPILE-UNVERIFIED）：

| 文件 | 改动点 | 风险 |
|---|---|---|
| `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh` | `FaultType` 增 10 值（T05×4/T06×3/T07×3）；族谓词 `isEntryStateFault/isAttrSubstFault/isCamFault/isWalkFamily`（walk 家族含 T08-b/c/d）；`maybeCorruptLookup` + `maybeCorruptWalkRefill` + `applyEntryFieldFault` 声明；新成员 `pending_walk_id/last_walk_pfn/last_walk_vpn/have_last_walk/stale_no_previous_notice`；`numStateFaults` 统计 | 低 |
| `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc` | 新 faultType 字符串 ↔ 枚举；ctor panic 门放宽到 walk 家族；`maybeCorrupt` 增 `isCamFault` 早退 + 状态/属性分发；`maybeDropWalkFill` 增 武装分支；新增 `maybeCorruptWalkRefill` / `applyEntryFieldFault` / `maybeCorruptLookup` | **中**（`const_cast` 取表项指针；见下） |
| `CHAOS/gem5/src/arch/arm/tlb.cc` | `TLB::lookup` 增 `maybeCorruptLookup` 调用（miss/hit 均调），返回指针可被替换 | 中 |
| `CHAOS/gem5/src/arch/arm/table_walker.cc` | `WalkUnit::insertTableEntry` 在 `mmu->insert` 前调用 `maybeCorruptWalkRefill`；返回 true 时**再 insert 一次** | 中 |
| `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{hh,cc}` | 新增 `registerTlbStateFault` + `tlb_state` 节点（L2）；`registerTlbWalkPair` refill outcome 由 mode 派生（duplicated/early_done/stale） | 低 |

**已知编译风险点（请重点核）**：
1. `CHAOSArmTLB::maybeCorruptLookup` 用 `const_cast<ArmISA::TlbEntry *>(&(*it))` 把
   `TLB::entryTable()`（const 访问器）返回的条目转可变指针。`TLB::table` 成员本身
   **非 const**，故该转换良定义；但若 tlb.hh 未来加 const 限定需复核。
   **备选**：在 `tlb.hh` 加 `Table &entryTableMutable() { return table; }`（若审阅更偏好显式访问器）。
2. `ArmISA::TlbEntry::MemoryType` / `ArmISA::GrainSize` / `Grain4KB` 的命名空间限定
   （`pagetable.hh` 内为 `gem5::ArmISA`）。
3. `maybeCorruptWalkRefill` 返回 true 时 `mmu->insert(te, ...)` 被调用两次（T08-b）——
   请确认经典 cache 的 `AssociativeCache::insert` 对同一条目重复插入不触发 assert。

建议验证命令：
```bash
cd /home/sdc/gem5-fi-ding/CHAOS/gem5 && scons -j16 build/ARM/gem5.opt   # 期望 SCONS_EXIT=0
# 核零新增 warning（基线唯一已知告警 = CHAOSCache -Wreorder，非本轮引入）
cd /home/sdc/gem5-fi-ding && sha256sum build/ARM/gem5.opt
# 回归（非 FS 路径）：
python3 tools/runner.py --config-family C0 --workload workloads/directed/reg_chain --cpu O3  # golden f247ef3fe6f02cfd
# 契约测试（Python-only，本 worktree 已全绿）：
python3 tests/test_lsu_hook_t05_state.py && python3 tests/test_lsu_hook_t08_pairing.py
```

## 5. 仍未闭环项与精确理由

- **本轮全部 24 项 FS-INFRA + T08-W9 三项均无 (c)/(d) 外部阻塞**；carrier/checkpoint 在盘上。
- 未闭环 = **纯构建 + 真机 pilot**（本 worktree 禁 build/禁跑 campaign）：
  - T05/T06/T07 的 9 格：C++ 编译 + FS pilot（3 seed）未做。
  - T08-b/c/d：同上（3 个子模型均 0 seed 真机覆盖）。
- **残余 (b)**：T10 的 PPN 位带分层子模型（T10-a/b/c）未参数化 —— 不在本轮任务范围，
  现为 `bit_flip` 近似，campaign 已诚实标注。建议后续单独一轮实现（`CHAOSArmTLB` 增
  `--tlb_bit_band low|mid|high` 之类），否则 T10 与 T01 结果不可区分。
- **诚实边界**：`T08-F4-*` 为结构性诚实零（F4 burst interval 1e5 远超 walk-issue 流
  ~1e3），非实现缺失；报告不得据此推断 Masked。
