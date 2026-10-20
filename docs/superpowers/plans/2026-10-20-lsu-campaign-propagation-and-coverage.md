# LSU 收口第二轮：campaign 全量接入 CHAOSPropagation + 定向 pilot 补证 + MODE-UNIMPL 实现

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans。复选框 `- [ ]` 逐项勾。

**Goal（用户指令 2026-10-20 第二轮）**
1. 把 CHAOSPropagation **完整接入 `tools/lsu_campaign.py`**：每个样本自动传递 `run_id`/`sample_run_id` 并产出 `prop_evt.txt.gz`；加测试；并用**正式 campaign 入口**重跑 A01、P01 各一个 smoke，证明不是直驱特例。
2. 用**定向 pilot** 补齐 Store Queue 的 `sq_execute/sq_writeback/sq_complete` 与 Cache 的 `mshr_alloc`，使 98 个 PARTIAL 按**真实证据**重新判定。
3. 继续实现 49 个 MODE-UNIMPL RunID。
4. 其余 77 个外部阻塞项单独列出供用户裁决。
5. 全部完成后停止；**不启动正式 campaign**。

**基线（本轮开始时实测）**：分支 `lsu-mdspec-20261019` HEAD `754b1b1e`，工作树干净；二进制 `CHAOS/gem5/build/ARM/gem5.opt` sha256 前缀 `746b0b91d485b00e`；覆盖矩阵 PASS=101/PARTIAL=98/BLOCKED=126；163 项 BLOCKED 分类 RULING=6/LICENSE=12/FS-MULTICORE=35/FS-INFRA=24/MODE-UNIMPL=49。

## Global Constraints（沿用）

- **规格至上 / Unknown 语义 / 禁止单键关联 / 诚实优先**：缺事件只报 Unknown，绝不推断 Masked。
- **one-patch-per-unit**：每任务一 commit，验证后 push 到 `lsu-mdspec-20261019`（非 main）。
- **不碰他人遗留**；绝不 `git add -A`；并发 gem5 ≤4。
- **构建必须显式核验成功**（上一轮教训：`scons | grep` 曾吞掉编译错误，导致 pilot 跑在陈旧二进制上）。

---

### Task 1 [CAMPAIGN]: lsu_campaign 全量接入 CHAOSPropagation

**Files:** Modify `tools/lsu_campaign.py`；Create `tests/test_lsu_campaign_propagation.py`

**Interfaces:**
- 每样本命令行追加：`--chaos_propagation --prop_run_id <RunID> --prop_sample_run_id s<seed>`（SE 与 FS 两支都要）。
- 二进制解析：`LSU_GEM5_BIN` 环境变量优先（与 `tools/lsu_runner.py` 先例一致），否则 repo-root `build/ARM/gem5.opt`；**两者皆缺 → 响亮 SystemExit**（不得静默降级）。
- 产物：每个 seed 目录下 `prop_evt.txt.gz`（gem5 `--outdir` = seed dir，`evtTraceFile` 相对 outdir）。

- [ ] **Step 1.1（RED）** 新测试：构造 cell 行 → 断言 `run_single_cell` 组装出的命令含 `--chaos_propagation`/`--prop_run_id <RunID>`/`--prop_sample_run_id s<seed>`（用 monkeypatch 拦截 subprocess / 或抽出 `build_se_cmd()` 纯函数直接断言）；断言缺二进制时 SystemExit。
- [ ] **Step 1.2** 实现（抽 `resolve_g5()` + 在两支命令上追加 propagation 标志）。
- [ ] **Step 1.3（GREEN）** `python3 -m pytest tests/test_lsu_campaign_propagation.py -q` 全绿 + 既有 suite 不回归。
- [ ] **Step 1.4** commit + push。

### Task 2 [SMOKE]: 正式入口 smoke（A01、P01）

- [ ] **Step 2.1** `LSU_GEM5_BIN=<worktree>/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir runs/lsu/mdspec_campaign_smoke --cells A01-F0-W3 --phase trial --max-seeds-per-cell 1 --max-parallel 1`
- [ ] **Step 2.2** 同法跑 `P01-F0-W8`（**先证注入日志非空**）。
- [ ] **Step 2.3** 对每样本 `prop_evt.txt.gz` 跑 `lsu_chain_check.py`，确认 `run_id`/`sample_run_id` 已写入事件行。
- [ ] **Step 2.4** 证据写入 `docs/gem5-fi/lsu/mdspec/campaign_smoke_report.md` → commit + push。

### Task 3 [EVIDENCE]: 定向 pilot 补 SQ 与 mshr_alloc，重判 98 PARTIAL

- [ ] **Step 3.1** SQ 定向 pilot：S 系 RunID（`sq_forward` 载体）真实运行，观察 `sq_execute/sq_writeback/sq_complete`；缺则如实记录并给根因。
- [ ] **Step 3.2** Cache `mshr_alloc` 定向 pilot：选 miss 路径可复现的 C 系组合（如 C 系 + 更大 working set / 冷启动），观察 `mshr_alloc`。
- [ ] **Step 3.3** 用新证据重生成 `pilot_evidence.json` + `coverage_matrix.md`（PARTIAL 按真实证据重新判定）。
- [ ] **Step 3.4** commit + push。

### Task 4 [MODE-UNIMPL]: 实现 49 个 MODE-UNIMPL RunID

- [ ] **Step 4.1** 枚举 49 项与其规格要求（表 10「先实现：」子句），按可实现性分组（可纯 SE 实现 / 需结构性改动）。
- [ ] **Step 4.2..N** 逐组实现：模式 + 钩子 + 测试 + 真实运行证据；每组一 commit。
- [ ] 不可实现/需结构性改动的项**如实列为需裁决**（不得伪装完成）。

### Task 5 [BLOCKERS]: 77 项外部阻塞单独成清单

- [ ] **Step 5.1** 从 `blocked_triage.md` 抽出 RULING(6)+LICENSE(12)+FS-MULTICORE(35)+FS-INFRA(24)=77，生成**独立裁决清单** `docs/gem5-fi/lsu/mdspec/blockers_for_approval.md`（逐项 RunID + 阻塞机理 + 解除条件 + 建议处置）。
- [ ] **Step 5.2** commit + push。

### Task 6: 收口报告 + 停止

- [ ] **Step 6.1** 报告：提交 SHA、工作树、构建/测试、两个 smoke 的逐层链、矩阵前后对比、MODE-UNIMPL 进展、77 项清单、磁盘、GO/NO-GO。
- [ ] **Step 6.2** 更新 memory；**不启动正式 campaign**。

---

## 进度节（第二轮实测）

- [x] **Task 1/2 [CAMPAIGN+SMOKE]** `c27bb782`：campaign 每样本带
      `--chaos_propagation --prop_run_id <RunID> --prop_sample_run_id s<seed>`（SE+FS 两支）；
      `resolve_g5()` 遵 `LSU_GEM5_BIN`→repo-root，皆缺则 SystemExit；测试
      `tests/test_lsu_campaign_propagation.py`（RED 已证）。**正式入口 smoke**：
      A01-F0-W3（6 事件，run_id/sample_run_id 在案，exit 134 流 truncated=True 属崩溃可存活设计）、
      P01-F0-W8（630 事件，链 full/L5，注入日志非空）——证据 `campaign_smoke_report.md`。
- [x] **Task 3 [EVIDENCE]** `fa790700`：定向 pilot 取到 **sq_writeback/sq_complete**
      （S04/S05-F0-W5），Store Queue **4/7→6/7**；**sq_execute 未观测**（疑注册/执行时序，待查）；
      **mshr_alloc 未观测**（机理实证：CHAOSCache 注入的是已 valid 的行，该行不会 miss；
      需"驱逐后再取回"）；另纠正 first_clock 单位是**周期**的误解。矩阵计数不变（101/98/126），
      PARTIAL 不因"多数节点已证"升级。证据 `targeted_pilot_sq_mshr.md`。
- [x] **Task 5 [BLOCKERS]** `6c7ea461`：77 项外部阻塞单独成 `blockers_for_approval.md`
      （RULING 6 / LICENSE 12 / FS-MULTICORE 35 / FS-INFRA 24，每类给机理+解除条件+建议+备选口径）。
- [ ] **Task 4 [MODE-UNIMPL] 未完成**：49 项全部仍 BLOCKED。实测确认 9 个模型
      （C11/C12/C14/C15/S10/P06/L04/A07/T08）既不在 `MODEL_FLAGS`、`lsu_proxy` 也无对应模式
      flag，属**真未实现**；已产出范围界定与实施顺序 `mode_unimpl_plan.md`（C11→C12→L04→P06→C14/C15→S10/A07/T08）。
      **本次会话未实现其中任何一项**——不得视为完成。
- [ ] **Task 6 收口报告**：见会话回复。
