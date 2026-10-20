# LSU MDSPEC 收口 Implementation Plan（P01/O01 真载体 · H4/H5/H6 补全 · 覆盖矩阵证据化）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 在前一计划 `2026-10-19-lsu-mdspec-port-and-l05.md` 的成果之上收口：① 用**真实 RunID + 真实 SE 载体**贯通 P01-F0-W8 与 O01-F0-W7 全链；② 补齐 H4/H5/H6 在规格表 9 要求的**全部**节点；③ 让 tlb_fault 的"翻译阶段阻断"与"终局 outcome"分离并与 runner/oracle 关联；④ 覆盖矩阵改为**节点级证据驱动**（禁止注册表布尔值判族完成）；⑤ 126 BLOCKED 逐项处置（解决或列入需用户批准的延期清单）；⑥ 分阶段重建/测试并真实验证 A01、A04、C01、P01、O01 五个 pilot。**正式 campaign 不启动。**

**Tech Stack:** vendored gem5 v25.1.0.1（`CHAOS/gem5/`，scons 增量 `-j126`）；Python 工具链（pytest/openpyxl）；worktree `.claude/worktrees/lsu-mdspec-20261019`，分支 `lsu-mdspec-20261019`。

**Spec（唯一实验规格）:** `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md` + 子文档 03/07/09/10（09 = 逐 RunID 传播监控，表 9；10 = 源码监控映射）。

**基线（本计划开始时实测）:**
- HEAD `d6b89696`；工作树 5 个未暂存文件（H4 mshr/writeback + H6 exmon，**未构建**：`strings gem5.opt | grep mshr_alloc` = 0）。
- 二进制 `CHAOS/gem5/build/ARM/gem5.opt` sha256 前缀 `d0e6b9a3a0a37313`（含 exmon_stxr，不含 mshr_alloc）。
- 覆盖矩阵 `mdspec/coverage_matrix.md`：**PASS=199 / PARTIAL=0 / BLOCKED=126**；钩子注册表 8 项全 `true`（用户判为不可信）。
- `/home` 可用 68 GiB（目标 ≥71 GiB）。

## Global Constraints（沿用前一计划，原文照搬）

- **规格至上**：不得为让运行通过而改规格语义/RunID/激活口径；冲突时规格胜出。
- **Unknown 语义**：链在某节点后缺事件 → 只能标"截至该节点可证，后续 Unknown"，**绝不推断 Masked**。
- **禁止单键关联**：跨单元关联必须用复合键（fault_id + event_id/parent_event_id；request_id/pf_request_id/mshr_id/fill_id；dyn_inst_seq + commit_seq；VA/PA/cache_line）。
- **空=空/诚实标记**：A06 未实现部分保持 BLOCKED，不伪装。
- **不碰他人遗留**：主树删除项、未跟踪文件、其他 worktree 一律不动；**绝不 `git add -A`**。
- **one-patch-per-unit**：每任务一个 commit，验证后 push 到 `lsu-mdspec-20261019`（非 main）。
- **资源门禁**：并发 gem5 ≤4；pilot workers=1 串行。
- **诚实铁律**：所有结论必须来自真实命令输出；不得"假定通过"。

---

### Task 0: 磁盘清理 → /home 可用 ≥ 71 GiB

**Files:** 无仓库文件（仅删临时/构建中间产物）

**判定原则**：只删 (a) `/tmp` 下**本会话/本轨道**产生或明确无进程占用的临时目录；(b) worktree 内的 `m5out/`、`runs/` 旧 scratch；(c) gem5 构建目录中的过期 `.os`/旧 SCons 中间物。**绝不删**：主树 `build/`、`gem5-fs/`、`runs/` 内已收官 campaign 证据、任何 worktree 的 `.git` 与其提交、`/home/sdc/gem5-fi-backups`。

- [ ] **Step 0.1** 盘点：`du -sh /tmp/* | sort -rh | head -30`；对每个候选用 `lsof +D <dir>` / `fuser` 确认无进程占用，用 `stat` 记录 mtime。
- [ ] **Step 0.2** 删除清单（逐项确认后 `rm -rf`）：`/tmp/gem5_b64c808d_saved`、`/tmp/ci-build3`、`/tmp/ci-build2`、`/tmp/ci-tree`、`/tmp/o3atlas_arith`、`/tmp/lsu_p4fix_val`、`/tmp/w1_*`、`/tmp/tmp.KqaXIjmcmK`、`/tmp/v2-32core.yaml`、mdspec worktree 内 `runs/` 旧 pilot scratch（保留证据文件）。
- [ ] **Step 0.3** 验收：`df -h /home` 显示 Avail ≥ 71G；把实测数字写入本计划进度节。

---

### Task 1 [H5]: prefetch 链补全 + pf_request_id 请求级稳定标识（P01-F0-W8）

**背景（实测）**：`CHAOSPrefetch.cc:146` 发 `pf_train` 且 `pf_request_id = faults_injected`（注入计数，≠请求级）；`queued.cc:276` 发 `pf_issue` 且 `pf_request_id = curTick()`。两者**不是同一命名空间**，无法贯穿。规格表 9 P01 必监控要求：`entry/queue index、lastAddr/stride/confidence/degree、candidate addr；pf_request_id、priority、issued/dropped/duplicated/cancelled、demand/prefetch 标记；fill_id、set/way/tag/data hash、allocate/ownership/dirty、merge MSHR、victim/writeback；consuming demand dyn_inst_seq/request_id；commit/oracle`。

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{hh,cc}`（新增 `notePrefetchRequest`/`prefetchRequestId(addr)` + `pfq_registry`）
- Modify: `CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetch.cc`（pf_train 携带 entry index/PC/old-new stride）
- Modify: `CHAOS/gem5/src/mem/cache/prefetch/queued.cc`（`pf_queue` 入队事件 + `pf_request` 发射事件，共享同一 pf_request_id）
- Modify: `CHAOS/gem5/src/mem/cache/base.cc`（`pf_fill`：fill 命中预取注册行时携带 pf_request_id）
- Modify: `CHAOS/gem5/src/mem/cache/cache.cc`（`pf_demand`：demand 命中被预取行时携带 pf_request_id + dyn_inst_seq）
- Modify: `tools/lsu_prop_fields.py`（KIND_LAYER + REQUIRED_FIELDS 增 4 种 kind）
- Test: `tests/test_lsu_hook_cpf.py`（合成行断言）

**Interfaces:** `uint64_t notePrefetchRequest(Addr addr, Addr size) -> pf_request_id`（请求级稳定标识，独立于 ptag，注册 `[addr,addr+size)`）；`uint64_t prefetchRequestId(Addr addr, Addr size)`（查表，未命中 0）。新 kind：`pf_queue`(L2, pf_request_id + entry_index)、`pf_request`(L2, pf_request_id + va + priority)、`pf_fill`(L3, pf_request_id + cache_line + fill_id)、`pf_demand`(L4, pf_request_id + dyn_inst_seq + request_id)。

- [ ] **Step 1.1（RED）** `tests/test_lsu_hook_cpf.py` 增 4 种 kind 的层/必录字段断言 + 合成 PROP-EVT 行解析往返；运行确认 RED。
- [ ] **Step 1.2** 实现 C++（pf_request_id 由 `notePrefetchRequest` 分配、经 `pfq_registry` 贯穿 queue/request/fill/demand；**与 fault_id/ptag 物理分离**）。
- [ ] **Step 1.3** 重建 `scons -j126 build/ARM/gem5.opt`（worktree 内 `CHAOS/gem5`），**零新警告**；记录 sha256。
- [ ] **Step 1.4（GREEN）** `python3 -m pytest tests/test_lsu_hook_cpf.py tests/test_lsu_prop_fields.py -q` 全绿。
- [ ] **Step 1.5** 真实小跑（P01-F0-W8，prefetch_stride，n=1）**先证明注入日志非空**（`grep -c 'stride' prefetch_injections.log` ≥1），再跑链检查，逐边 + terminal 记录。
- [ ] **Step 1.6** commit `[LSU][MDSPEC][H5]` + push。

---

### Task 2 [H4]: MSHR allocate/merge/fill/victim/writeback + 真 mshr_id/fill_id（C01-F0-W6）

**背景（实测）**：工作树未提交的 `base.cc` 已加 `mshr_alloc`/`mshr_merge`/`cache_writeback`，但 `mshr_id`/`fill_id` 目前填的是**十六进制块地址**而非真 id，且缺 `victim` 与 `mshr_fill`、`set/way/entry_index` 恒空。规格表 9 C01 要求：`miss_id/MSHR id、targets、allocate/merge/full/free、downstream request_id、fill_id、victim tag/data/dirty、writeback addr/data、response`。

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{hh,cc}`（新增 `noteMshrEvent`/mshr_registry：alloc/merge/fill/free 生命周期 + 真 mshr_id/fill_id 分配）
- Modify: `CHAOS/gem5/src/mem/cache/base.cc`（allocateMissBuffer/handleFill/writeback/evict 处改发真 id；新增 `mshr_fill`、`cache_victim`）
- Modify: `CHAOS/gem5/src/mem/cache/cache.cc`（evictBlock 发 `cache_victim`：victim tag/way/dirty）+ set/way 填充
- Modify: `tools/lsu_prop_fields.py`、`tests/test_lsu_hook_cpf.py`

- [ ] **Step 2.1（RED）** 测试：`mshr_alloc/mshr_merge/mshr_fill/mshr_free/cache_victim/cache_writeback` 层与必录字段；断言 `mshr_id` 为**单调分配的真 id**（非 hex 地址）。
- [ ] **Step 2.2** 实现；重建零警告。
- [ ] **Step 2.3（GREEN）** 套件绿。
- [ ] **Step 2.4** 真实小跑 C01-F0-W6（cache_dirtyevict，n=1）：证明 `mshr_alloc`/`mshr_merge` 在真实流中出现（或诚实记录未出现），`mshr_id` 与 `fill_id` 同链一致。
- [ ] **Step 2.5** commit `[LSU][MDSPEC][H4]` + push。

---

### Task 3 [H6]: CHAOSExMon → CHAOSPropagation 全链（O01-F0-W7）

**背景（实测）**：工作树未提交改动已加 `exmon_monitor`(L1)/`exmon_stxr`(L2)，但 ① monitor 只注册 `addr_registry`，cache 事件走 `blk_registry` → cache/RMW/return 节点**永不相关**；② `exmon_stxr` 的 `state_before == state_after`（未区分成功/失败/重试）；③ 无 L4 消费/L5 终局节点。用户要求：monitor 地址 before/after、fault_id、dyn_inst_seq/request_id，贯通 STXR 消费、成功/失败/重试、cache/RMW/return 与最终结局。

**载体裁决（诚实）**：规格 O01 的负载 `Atomic-Litmus 并发探针` 是**多核 FS 负载**（`workloads/directed/atomics_probe.c` 文件头已实证记录：O 系网格格全部 blocked，本探针只作注入器功能验证）。因此 O01-F0-W7 用 `workloads/directed/atomics_probe` 作为 **SE 载体探针**运行，报告与矩阵须明确标注"SE 载体探针（注入器功能验证），非网格格；正式 O01-F0-W7 格保持 BLOCKED 待多核 FS"，L4（后续线程消费）/litmus forbidden-outcome 在单核 SE 下只能 **Unknown**。

**Files:**
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSExMon/CHAOSExMon.{cc,hh}`（monitor 同步注册 blk registry；`attempt_no` 重试计数；`state_before/after` 真区分；L2 RMW/compare 事件）
- Modify: `CHAOS/gem5/src/arch/arm/isa.cc`（如需要，LDXR/STXR 环路计数）
- Modify: `CHAOS/gem5/src/mem/cache/cache.cc`（`exmon_rmw`：cache 侧 compare/old→new 与 success；`exmon_return`：cache 响应返回）
- Modify: `tools/lsu_prop_fields.py`、`tests/test_lsu_hook_cpf.py`

**Interfaces:** kind `exmon_monitor`(L1: fault_id/dyn_inst_seq/before/after/field/request_id)、`exmon_rmw`(L2: pa/old/new/success)、`exmon_stxr`(L3: dyn_inst_seq/attempt_no/state_before/state_after/pa)、`exmon_return`(L3: pa/field)、复用 `consumer`/`taint_reg`(L4)、`chain_end`(L5)。

- [ ] **Step 3.1（RED）** 测试：新 kind 层/字段；`state_before != state_after` 或 `attempt_no` 存在的语义断言。
- [ ] **Step 3.2** 实现；重建零警告。
- [ ] **Step 3.3（GREEN）** 套件绿。
- [ ] **Step 3.4** 真实小跑（O01-F0-W7 → atomics_probe，n=1）：先证注入日志非空，再逐边记录链（L4/L5 若缺则诚实 Unknown）。
- [ ] **Step 3.5** commit `[LSU][MDSPEC][H6]` + push。

---

### Task 4 [H2/A01]: tlb_fault 终局语义 + oracle join + chain checker 一致性

**背景（实测）**：`mmu.cc:1347` 发 `tlb_fault` 时 `contained=""`（d6b89696 已改），chain checker 对 `detection_layer=="Hardware"` 特判为 `detected_translation_outcome_pending`。用户要求：**保留真实 tlb_fault 事件**，但**不得对所有 translation fault 无条件写 contained=1**；须区分"翻译阶段阻断"与最终 Contained/Crash/Handled outcome，并与 runner/oracle 结果关联；补测试使 terminal、provable_to、beyond 自洽。

**Files:**
- Modify: `tools/lsu_chain_check.py`（终局判定：translation-blocked 为**中间态**，须与 `--oracle-outcome` 输入 join 后才落终局：`detected_contained` / `crash_translation_blocked` / `handled`）
- Modify: `tests/test_lsu_chain_check.py`

- [ ] **Step 4.1（RED）** 三例测试：① 只有 tlb_fault + oracle=guest_arch_fault → terminal=`crash_translation_blocked`（非 contained）；② tlb_fault + 后续 errant_commit → `full`；③ tlb_fault + oracle=clean 且无后续事件 → `provable_to_L2_then_unknown` + `beyond=Unknown`。断言 `provable_to`/`beyond` 与 terminal 自洽（`beyond==""` 仅当 closed 终局）。
- [ ] **Step 4.2** 实现 join（新增 `oracle_outcome` 参数，缺省 `None` ⇒ 保持 `detected_translation_outcome_pending`，**不猜测**）。
- [ ] **Step 4.3（GREEN）** 套件绿。
- [ ] **Step 4.4** 与 runner/oracle 关联验证：用 A01 真实样本的 L5 分类结果（`tools/lsu_l5_classify.py` 输出）作为 join 输入，输出终局。
- [ ] **Step 4.5** commit `[LSU][MDSPEC][H2]` + push。

---

### Task 5 [B2]: 覆盖矩阵节点级证据化 + 126 BLOCKED 互斥分类 + 延期清单

**背景（实测）**：现矩阵 PASS=199 来自 `HOOK_REGISTRY` 8 个布尔值，`assess()` 只看布尔——**用户明令不得据此判族完成**。126 BLOCKED 现分 4 类混杂（85 `spec:需新增`、71 `workload:无映射`、campaign:deferred 若干，且有交叠）。

**Files:**
- Modify: `tools/lsu_coverage_matrix.py`（`HOOK_REGISTRY` 布尔 → **`HOOK_EVIDENCE`**：每族声明其规格必录节点集合，且须由 `docs/gem5-fi/lsu/mdspec/pilot_evidence.json` 的**真实 pilot 事件**证明；缺任一节点 → `PARTIAL(missing_nodes=[...])`）
- Create: `tools/lsu_blocked_triage.py` + `docs/gem5-fi/lsu/mdspec/blocked_triage.md`
- Modify: `tests/test_lsu_coverage_matrix.py`
- Regenerate: `docs/gem5-fi/lsu/mdspec/coverage_matrix.md`、`runid_map.json`

**互斥分类（优先级序，每 RunID 恰一类）：**
`EXT-FS`（需多核/单核 FS 基础设施）｜`EXT-LICENSE`（SPEC 授权）｜`RULING`（A06 裁决封锁）｜`MODE-UNIMPL`（该子模型模式未实现）｜`HOOK-UNIMPL`（规格要求的新增钩子未实现）｜`CARRIER-PROBE`（有 SE 载体探针但非网格格，需用户批准口径）｜`OK`（可解锁）。

- [ ] **Step 5.1（RED）** 测试：构造"钩子族缺一个节点"→ 必须 `PARTIAL` 而非 `PASS`（钉死用户第 3 点）；互斥分类每 RunID 恰一类且和=126。
- [ ] **Step 5.2** 实现 + 生成 `blocked_triage.md`（含**需用户批准的延期清单**与逐项理由）。
- [ ] **Step 5.3** 重生成覆盖矩阵（用 Task 1/2/3 pilot 的**真实事件**作为证据）。
- [ ] **Step 5.4（GREEN）** 套件绿；commit `[LSU][MDSPEC][B2]` + push。

---

### Task 6: 分阶段重建 + 全套件回归

- [ ] **Step 6.1** worktree 内 `cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt` 增量重建，**零警告零错误**；记录 `git rev-parse HEAD` + gem5.opt sha256。
- [ ] **Step 6.2** `python3 -m pytest tests/ -q`（全套件）全绿；记录计数。
- [ ] **Step 6.3** 不受影响回归：`python3 tools/manifest_validate.py --help` exit 0 + 无注入 golden 短跑（`agu_addrmodes`）FINAL == `728e604ffcec539d`。
- [ ] **Step 6.4** 规格门禁：`python3 tools/lsu_xlsx_to_md.py --xlsx ... --validate` ALL PASS。

---

### Task 7: 五个 Pilot 真实验证（A01、A04、C01、P01、O01）

**统一方法**：`lsu_proxy.py` 直驱（campaign 不挂 propagation，见 §实测）+ `--chaos_propagation --prop_run_id <RunID> --prop_sample_run_id pilot-s<N>`；workers=1 串行；n ≤ 5；产物只写 worktree `runs/lsu/mdspec_pilot/`。

- [ ] **Step 7.1** A01-F0-W3（agu_addrmodes, a01_bit, F0）
- [ ] **Step 7.2** A04-F0-W3（agu_addrmodes, a04_subst, F0）
- [ ] **Step 7.3** C01-F0-W6（cache_dirtyevict, cache data bit_flip, F0）
- [ ] **Step 7.4** P01-F0-W8（prefetch_stride, p01_stride_bitflip, F0）——**先证注入日志非空**
- [ ] **Step 7.5** O01-F0-W7（atomics_probe SE 载体, o01_monitor_addr_bitflip, F0）——**先证注入日志非空**
- [ ] **Step 7.6** 每例：`lsu_chain_check.py` 逐边 + terminal + provable_to + beyond；L5 与 golden 对照；**缺事件一律 Unknown**。
- [ ] **Step 7.7** 汇总 `docs/gem5-fi/lsu/mdspec/pilot_report.md`（真实输出引用）+ commit + push。

---

### Task 8: 提交拆分、推送与 fi-ding 集成

- [ ] **Step 8.1** 确认工作树干净（无未提交改动，除刻意保留项）；确认每个功能单元各自一个 commit（Task 1–5 已各自提交）。
- [ ] **Step 8.2** `git fetch origin && git log --oneline fi-ding..origin/fi-ding` 列出 fi-ding 最新 2 个提交；`git merge --no-ff` 或 `git cherry-pick`（依依赖判定），**集成后重建 + 回归**。
- [ ] **Step 8.3** push `lsu-mdspec-20261019`。

---

### Task 9: 收口报告 + 停止

- [ ] **Step 9.1** 输出：提交 SHA 列表、工作树状态、构建/测试结果、5 pilot 逐层链路、325 RunID 状态、剩余阻塞、磁盘空间、**正式实验 GO/NO-GO**。
- [ ] **Step 9.2** 更新计划复选框 + memory；**不启动正式实验**。

---

## 进度节（实测填记）

- 起点：HEAD `d6b89696`；`/home` Avail 68 GiB；PASS=199/BLOCKED=126。
