# R6-FIXD — campaign 判定与权威状态表修复

> Lane D（独占）目标：修掉 campaign 的 3 个诚实性缺陷 + 建立**唯一权威**的逐 RunID 状态表
> （六态互不覆盖、与契约共用同一 evidence root）。
> 证据根：`LSU_CHAIN_EVIDENCE_ROOT=/home/sdc/gem5-fi-ding`（与 `ready_contract.chain_gate.evidence_root`
> 完全一致，已实测）。
> TDD：每个任务先写/跑到真实 RED，再实现到真实 GREEN；不得放宽口径换绿。
> 基线：`python3 tools/lsu_test_runner.py` FAIL=13，**NEW FAIL 必须为 0**。

## 独占文件

- `tools/lsu_campaign.py`
- `tools/lsu_ready_contract.py`
- `tools/lsu_blocked_triage.py`
- `tools/lsu_r6_status_table.py`（base 07c004e5 中不存在 → 本 lane 新建）
- 上述工具对应测试 `tests/test_lsu_*`

**不碰**：C++、`tools/lsu_chain_check.py`（Lane B）、集成分支。

---

## 任务 1（真缺陷 1）— campaign 最终结论必须实际调用 binding `check_admission`

**现状**：`write_chain_report` 只跑 `check_chain_fast`（=`check_chain`），从不调用
`lsu_chain_check.check_admission`；`chain_report.json` / `chain_summary.md` / `cell_results.json`
把**门禁会拒绝**的样本照样记为 `chain_valid: true` + 一个看着完整的 terminal/provable_to。
（同"旧 T04 假 full"一类：只有链形，没有准入门）。实测契约里 `T06/T08-F0-W4`
chain admitted=True 恰恰是**在截断流**上判的，正是缺这道门的结果。

**改法（加性，不动既有 `chain_valid` 语义以免误伤旧测试）**：
- 新增 `admission_gate(runid, events, activated, oracle_outcome, exit_code)` →
  `lsu_chain_check.check_admission(bundle)` 的紧凑结果 `{admitted, path, terminal, violations}`。
- `write_chain_report`：当流存在且有 fault（activated）时**调用** `admission_gate`，
  写 `rep["admitted"]`、`rep["admission"]`、`rep["certified"] = admitted`；
  未准入时 `summary` 前缀 `NOT ADMITTED:`（响亮）。
- `chain_summary.md` 增列 `admitted`；`cell_results.json` 每样本条目带 `admitted`，
  cell 级给 `admission_status`：`ADMITTED | GATE-REFUSED | NO-ACTIVATION | EVIDENCE-TRUNCATED`。

**RED**：`tests/test_lsu_campaign_admission.py` —— 合成一个 `check_chain` 有 fault 路径、
但 `check_admission` 必拒（activated 链内程含 `unknown` 事件）的流；
断言 `admitted is False` 且 `"NOT ADMITTED" in summary` 且 `chain_report.json` 落盘含 `admitted`。
当前实现无 `admitted` 字段 ⇒ 真实 FAIL。

**GREEN 证据**：同一测试 ALL PASS；`tests/test_lsu_campaign_truncation.py`、
`test_lsu_campaign_propagation.py`、`test_lsu_campaign_large_stream.py` 仍 PASS（回归）。

---

## 任务 2（真缺陷 2）— `attempted=0 而 activated>0` 不得打印 `activation_rate=0.0`

**现状**：`run_cell_adaptive` 末 `act_rate = (activated/attempted) if attempted else 0.0`
——`attempted=0`、`activated=3` 时打印 `0.0`（计数矛盾被静默成一个"率"）。

**改法**：分母为 0 时不得报数：
- `attempted>0` → `round(activated/attempted,4)`；
- `attempted==0 and activated==0` → `0.0`（真零）；
- `attempted==0 and activated>0` → `None` + `activation_rate_note`（"计数矛盾：attempted=0
  而 activated=N"）+ `count_contradiction=True`（响亮）。
- 同类：`activated==0` 时 `sdc_rate` 由静默 `0.0` → `None` + note。

**RED**：`tests/test_lsu_campaign_count_contradiction.py` —— 用 `run_cell_adaptive`
（monkeypatch `run_single_cell` 返回 `attempted=0, activated=3`）断言
`activation_rate is None` 且 note 非空且 `count_contradiction is True`。当前为 `0.0` ⇒ FAIL。

**GREEN**：ALL PASS + 控制台行不再出现 `activation_rate=0.0` 的假象。

---

## 任务 3（真缺陷 3）— `sample_run_id` 报告值与事件流一致

**现状**：事件流写 `--prop_sample_run_id s<seed>`（`propagation_flags`），
而 `write_chain_report` 写 `"sample_run_id": str(seed)`（= `"1"`）⇒ 报告 `"1"` vs 事件流 `"s1"`。

**改法**：`write_chain_report` 的 `sample_run_id` 统一为 `"s%d" % int(seed)`（与事件流同源）；
`chain_summary.md` 随之显示 `s1`。

**RED**：`tests/test_lsu_campaign_sample_run_id.py` —— 写一条含 `sample_run_id=s1` 的流，
断言 `rep["sample_run_id"] == "s1"` 且与流内 `sample_run_id` 字段一致。当前 `"1"` ⇒ FAIL。

**GREEN**：ALL PASS。既有 `test_lsu_campaign_large_stream.py` 只查键存在，不查值 ⇒ 不回归。

---

## 任务 4（真缺陷 4）— 建立权威六态状态表（`tools/lsu_r6_status_table.py`，新建）

**六态（互不覆盖，只能用这些）**：`NOT_RUN` · `EVIDENCE_MISSING` · `TRUNCATED` ·
`UNPROVEN` · `PILOT_READY` · `BLOCKED`。
每行**同时**给 `conditions`（六态各自独立布尔）以便表达 `TRUNCATED+UNPROVEN` 这类并存事实；
`state` 取 disk-first 优先级：
`NOT_RUN > EVIDENCE_MISSING > TRUNCATED > UNPROVEN > (PILOT_READY | BLOCKED)`。

- **NOT_RUN**：权威根下**没有任何流**（未测量）——**绝不被契约 BLOCKED 顶掉**（这是旧
  状态表"325 全短路 BLOCKED、NOT_RUN 永不出现"的直接修复）。
- **EVIDENCE_MISSING**：`pilot_evidence.json` **声称**有该 RunID/seed 样本，但文件在权威根下
  缺失/不可读（悬空引用）。
- **TRUNCATED**：有流但 gzip 读不到 EOF 或 `stats.txt` 缺失/0 字节。
- **UNPROVEN**：全流完整且有激活，但 `check_admission` 不通过（含"完整流但无激活"）。
- **PILOT_READY**：全部激活样本准入 + 无截断 + 无 Unknown + **无上游阻塞**。
- **BLOCKED**：有上游独立阻塞（FS-INFRA/RULING/LICENSE…，取契约为准）；仅当该行
  **本可达 PILOT_READY** 时才把 state 记为 BLOCKED（"规格/基础设施阻塞绝不可计为 PILOT_READY"）。
  上游阻塞**单独**记在 `upstream_block` 列，绝不吞掉 `NOT_RUN/TRUNCATED/UNPROVEN`。

**evidence root 同一且被记录**：`--evidence-root`（缺省 `$LSU_CHAIN_EVIDENCE_ROOT`，再缺省 REPO），
写进 `meta.evidence_root`；并与契约 `chain_gate.evidence_root` 比对，不一致则**响亮**告警并记录。

**RED**：`tests/test_lsu_r6_status_table.py`（合成夹具）——六态各自可达；
`X 无流` ⇒ NOT_RUN；`X 截断+未准入` ⇒ state=TRUNCATED 且 `conditions.unproven True`；
`X 上游阻塞+完整准入证据` ⇒ BLOCKED（且 `conditions.pilot_ready True` 可见）；
契约 `status=BLOCKED` 全行**不得**把 NOT_RUN 行短路掉。

**GREEN + 真实计数**：`LSU_CHAIN_EVIDENCE_ROOT=/home/sdc/gem5-fi-ding python3 tools/lsu_r6_status_table.py`
（真实 325 行）产出 `R6-STATUS-TABLE.{json,md}`，引真实状态计数；锚点：
`C01-F0-W1` = NOT_RUN、`L01-F0-W5` = TRUNCATED(+UNPROVEN) 非 PILOT_READY、
`T06/T08-F0-W4` 非 PILOT_READY 且 `upstream_block=FS-INFRA` 单列。

---

## 验收

- [x] 任务 1 RED→GREEN（admission 真调用）— commit 5208c8a5
- [x] 任务 2 RED→GREEN（计数矛盾不伪装成率）— commit 2ecb13c8
- [x] 任务 3 RED→GREEN（sample_run_id 一致）— commit f52a52eb
- [x] 任务 4 RED→GREEN（六态状态表 + 真实计数）— commit ac604e68
- [x] `python3 tools/lsu_test_runner.py` NEW FAIL = 0（基线 FAIL=13 → 现 FAIL=13，逐套件比对一致）
- [x] 各自独立提交 `[LSU][MDSPEC][R6-FIXD]`，push 到 `r6-fixd`

### 实测结论（真实输出）

- 状态表（真根）：325 行 ⇒ NOT_RUN=305 / EVIDENCE_MISSING=0 / TRUNCATED=8 /
  UNPROVEN=12 / PILOT_READY=0 / BLOCKED=0；流 total=60 complete=48 truncated=12
  activated=59 admitted=6。`evidence_root=/home/sdc/gem5-fi-ding matches_contract=True`。
- 契约重生成（同根）逐字一致：`total=325 BLOCKED=325`，
  `blocked_by_category` 含 84 个上游阻塞（FS-INFRA 24 / FS-MULTICORE 35 /
  LICENSE 12 / RULING 6 / MODE-UNIMPL 3 / UNRESOLVED 4），与状态表
  `upstream_blocked=84` 完全同源。`lsu_ready_contract.py` 无需改动。
- 真根 `BLOCKED=0` 是事实而非漏洞：所有带证据的上游阻塞行同时被截断，
  disk 事实优先；BLOCKED 的可达性由合成夹具（X06）证明。


### 套件回归（真实输出）

- 改动后：`suites=64 ENV=5 FAIL=13 PASS=45 SKIP=1`（基线 `suites=61 FAIL=13 PASS=42`；
  +3 套件 = 本 lane 新增的 3 个测试套件，均 PASS）。
- NEW FAIL 逐套件实证：在**基线 worktree r6-fixa（07c004e5，lsu_campaign.py 未改）**
  对 13 个 FAIL 套件逐个运行并与改动后比对，逐套件失败数**完全一致**
  （a07 2/2, c11 2/2, c12 2/2, c14 2/2, c15 2/2, cpf 7/7, l04 2/2, o0x 0/0,
  p06 3/3, s10 3/3, sq 4/4, campaign_propagation 4/4）⇒ NEW FAIL = 0。
