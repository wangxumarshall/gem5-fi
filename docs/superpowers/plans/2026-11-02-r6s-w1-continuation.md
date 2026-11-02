# R6-S W1 接续收口计划（2026-11-02）

## 背景（已固定事实，不再调查）

- 分支 `fix/r6-s-w1-continuation-20261101`，起点 HEAD `d8f5489f`。
- 权威二进制 `binaries/gem5.opt-6db026e7`，SHA-256
  `6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`（源 `43d1bb08`）。
- S01/S02 W1 census：`S01=17669290`、`S02=17669123`（`w1census/S0{1,2}-w1/manifest.json`）。
- `S01-F1-W1 seed1` canary 已合格（`w1canary/S01-F1-W1_s1`：terminal=full、provable_to=L5、
  admitted/certified=true、truncated=false、violations=[]、gzip EOF×2、stats=268008 B、oracle=Crash）。
  该样本直接计作 seed1，不重跑。
- 旧二进制产生的 S01-F1 seed1/seed2 与 S01-F2/S02-F2 seed1 均截断，只作失败对照。
- 剩余 14 个 seed 待跑（5 RunID × 3 − canary）：
  S01-F0 1/2/3、S01-F1 2/3、S01-F2 1/2/3、S02-F0 1/2/3、S02-F2 1/2/3。

## Task 1 — 修复并行调度器（一个 commit）

根因：bash 5.2.15 + `set -u` 下，`declare -A RUNNING` 未初始化时
`${#RUNNING[@]}` 触发 “RUNNING: 未绑定的变量”，队列在启动任何 worker 前退出
（`r6s_w1_parallel.sh:187`，已用 `/tmp/t.sh` 实测复现）。

修复点：

- [ ] `declare -A RUNNING=()` + 显式 `RUNNING_N` 计数器（不再依赖空数组长度）。
- [ ] worker 在到达 MAXJOBS 时被回收后立即 grade（旧版只对最后一波 grade，其余记录丢失）。
- [ ] `S01-F1-W1#1` 从 canary 目录 grade 并跳过重跑（PRESEED）。
- [ ] 所有路径可由 `R6S_W1_*` 覆盖，便于用假 launcher 验证调度逻辑。

文件：`tools/r6_s_w1_parallel.sh`、`tests/test_r6_s_w1_parallel.py`。

验证（必须引用真实输出）：

```bash
bash -n tools/r6_s_w1_parallel.sh
./tools/r6_s_w1_parallel.sh --dry-run          # ALLOCATION_OK, 15 unique
python3 -m pytest tests/test_r6_s_w1_parallel.py \
  tests/test_r6_s_w1_par_seed.py tests/test_r6_s_w1_seed_launcher.py -q
python3 -m pytest tests/test_lsu_campaign_span_extra.py \
  tests/test_lsu_addrpath_f0_span.py tests/test_lsu_campaign_sample_run_id.py \
  tests/test_lsu_campaign_seed_start.py tests/test_lsu_campaign_reap.py -q
```

## Task 2 — 启动 14 个剩余 seed（无 commit）

```bash
tmux new-session -d -s r6s-w1-parallel \
  "bash -lc '/home/sdc/gem5-fi-ding-cleanup-20261029/r6s_w1_parallel.sh \
   >> /home/sdc/gem5-fi-ding-cleanup-20261029/r6s-w1-parallel.log 2>&1'"
```

- MAXJOBS=8；门禁 MemAvailable≥12 GiB、/home≥30 GiB、swap 下降≤2 GiB、SHA 不漂移；每 seed 12 h。
- 每 seed 独立目录/锁/manifest：`runs/lsu/r6_s_repair2/w1e/<RunID>_s<seed>`。
- 失败保留现场；不重跑已合格样本。

- [ ] 队列 `R6S_W1_PARALLEL_DONE` 出现，14 个 `.done` / `.exit_code` / manifest FINISHED。
- [ ] 运行期间 `pgrep` 证明 gem5 并发 ≤ 8，无 OOM。

## Task 2b — EVENT_CAP 误判修复（2026-11-02 实测发现，一个 commit）

S01-F2-W1 的流经 `gzip -t` 验证完整（1,480,644 行），但 `EVENT_CAP=200000`
把“完整流超出分析上限”与“gzip 截断”混为一谈，campaign 因此标
`EVIDENCE-TRUNCATED` 并拒绝认证。新增离线 regrade：

- [ ] `tools/regrade_r6_w1_event_cap.py`：先证明 gzip EOF + stats 非空，统计真实
      event 数 n，用 cap=n+1 重跑**同一** `write_chain_report`（同一 parser/checker/
      admission gate）；只有 `truncated=False`、`evidence_truncated=False`、
      `event_count==n`、`admitted=True`、`certified=True` 才写回。
- [ ] 原件备份 `.pre-capregrade-20261102`；manifest 增加 `chain_regrade`
      provenance（含原文件 SHA-256）；raw 证据不改。
- [ ] 实测：S01-F2-W1 s1（1,479,991 events/71 faults）与 s3（1,545,241/70）
      均由 EVIDENCE-TRUNCATED 变为 admitted/certified，独立证据审计 PASS。

## Task 3 — 逐 seed 证据审计（一个 commit）

新增独立审计器 `tools/audit_r6_w1_evidence.py`（只读原始证据，不复用 runner 的判断）：

- [ ] 对 15 个样本（14 新 + canary）核对：manifest status/exit、binary SHA、gzip EOF×2、
      stats 非零、admission_status=ADMITTED、admitted/certified/truncated/violations、
      chain_report 的 terminal/provable_to/oracle、事件总数、L0 funnel injected/activated。
- [ ] 每个证据文件输出 SHA-256；对每个 fault 校验 `path_event_ids` 在原始事件流中存在且
      `parent_event_id` 链闭合、tick 单调。
- [ ] 输出 `R6S_W1_EVIDENCE_AUDIT.jsonl` + 摘要 Markdown；**任何不满足项必须记为 FAIL，
      不得升格为 PASS**。

## Task 4 — 15 份传播链文档（一个 commit）

新增 `tools/gen_r6_w1_lsqfwd_docs.py`（LSQFwd 事件域，不能照搬 S13 AddrPath 生成器）：

- [ ] 每 seed 逐 fault 提取：注入记录（`lsq_fwd_injections.log` 的 Cycle/Site/FaultType/
      Vaddr/FwdSize/ByteOffset/Mask/StoreSeq/LoadSeq）、L0→L5 事件序列与层边证明、
      consumer/squash 统计、终局字段。
- [ ] 全量流不做逐行转录（LSQFwd 单 seed 事件量级 1e5–1e6）；改为：事件种类 census +
      全流 SHA-256 + 每 fault 规范路径逐事件转录 + 诚实边界。
- [ ] staging → 独立审计 `tools/audit_r6_w1_docs.py`（重读原始流逐项比对，0 错误）
      → 原子部署到 `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/S01|S02/<RunID>/<RunID>-seedN.md`。
- [ ] oracle 与 chain terminal 冲突时并列记录，不调和、不改写。

## Task 5 — 索引/统计更新（一个 commit）

基于 `update_s13_w1_indexes.py` 泛化为 `tools/update_r6_w1_indexes.py`：

- [ ] EVIDENCE 相对软链接（已存在则保留）、CATALOG.tsv 行、INDEX.md S 表、
      INDEX.json、STATUS/R6-S-UNIT-STATUS.json、RESULTS/README、S 最终报告。
- [ ] 仅把审计 PASS 的 seed 计入合格数；FAIL 样本单列。
- [ ] 所有旧 TIMEOUT/截断证据保留，不删除、不覆盖。

## Task 6 — 回归与台账（一个 commit）

- [ ] 全量 `python3 -m pytest tests -q`：与基线 `c42f7966` 的 9 项既有失败逐项对照，
      **NEW FAIL = 0**；新增 W1 测试全绿。
- [ ] 更新 `R6S_W1_CONTINUATION_PROGRESS.md` 台账与 memory，记录真实结局与剩余缺口。
- [ ] 每个 commit 验证后推送 `origin/fix/r6-s-w1-continuation-20261101`（不推 main）。

## 诚实约束

- 只报告实测输出；未完成/失败项写 `n/a` 或 FAIL，不写推测。
- 不删除任何旧证据；不改写 oracle 或 chain 判定。
- 不启动 F6 / W11 / trigger-reachability blocked 项。
