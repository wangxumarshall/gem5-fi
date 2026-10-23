# R6-CAMPAIGN — L20-v2: FS 截断证据 LOUD 化 + 2700s 预算 + 子进程回收

日期: 2026-10-23 · Lane: L20-v2 (code) · Worktree: `.claude/worktrees/r6-campaign` (branch `r6-campaign`, base `66ab98a2`)

## Goal

FS gem5 运行远超其被赋予的 timeout，被杀在写入中途 → 留下不完整传播流。三处修复
（不改 found/activated/injection 判定），一单元一提交：

1. **截断检测 LOUD**：凡是读 `prop_evt.txt[.gz]` 处（campaign finalize `write_chain_report`
   / unit pilot）检测 (a) 不完整 gzip 流 (b) 缺失/0 字节 `stats.txt`，把样本显式标记
   `evidence_truncated=True` + 响亮 reason；绝不再当作完整/有效链或静默使用。
2. **Timeout 预算**：FS 默认 `--fs-timeout` 1800 → **2700**（已知良好预算），并把**生效**
   timeout 写进 per-cell 输出/manifest（不静默降低）。
3. **子进程回收**：timeout 时真正 kill **并** reap gem5 子进程（SIGTERM→SIGKILL 进程组 +
   `wait()`），记录退出码/信号；不留孤儿占用 checkpoint/outdir。

Reproduced facts (real files, quoted):
- `runs/lsu/r6_tlb_C_T08-F0-W4/T08-F0-W4/seed1/prop_evt.txt.gz` (635 B) → `gzip.open(...).read()`
  raises `EOFError: Compressed file ended before the end-of-stream marker was reached`; `stats.txt` exists but **0 bytes**.
- `runs/lsu/r6_tlb_negative2/seed1/prop_evt.txt.gz` (238 B) → same `EOFError`; `stats.txt` **0 bytes**.
- `runs/lsu/r6_tlb_pilot2/T05-F0-W4/seed1/` → gzip **complete** (reads OK, `truncated:false`,
  exit 0, `stats.txt` 427,682 B) — a legitimate 5-event chain, NOT a truncation. Reported honestly.

Baseline suite: `suites=52 ENV=5 FAIL=13 PASS=33 SKIP=1`.

## Non-goals (explicitly frozen)
- No change to how found / activated / injection are decided (outcome/classes counts untouched).
- Do NOT edit `tools/lsu_chain_check.py`, `tools/lsu_ready_contract.py`, `tools/lsu_l5_classify.py`,
  `tools/lsu_obs_core.py`, or any C++.

## Unit 1 — truncated-evidence detector + loud marking  (commit 1)

- [ ] RED: add `tests/test_lsu_campaign_truncation.py` asserting (a) `detect_evidence_truncation`
      returns True+reason on incomplete gz and on missing/0-byte `stats.txt`; (b) `write_chain_report`
      sets `evidence_truncated=True` + `truncation_reason` + `chain_valid=False` and prefixes the
      summary loudly; (c) a complete gz + non-empty stats ⇒ `evidence_truncated=False`. Run → FAIL.
- [ ] GREEN: implement `detect_evidence_truncation(outdir)` in `tools/lsu_campaign.py`; wire into
      `write_chain_report` (new keys + loud summary + `chain_valid`); surface in per-seed entry and
      `chain_summary.md` column. Unit pilot: `run_one` folds `evidence_truncated`/reason into the
      verdict. Run → PASS.
- [ ] Prove against the REAL truncated files (T08, negative2) → loudly flagged; pilot2 → not flagged.
- [ ] Existing `test_lsu_campaign_propagation.py` [5] still passes (prefix salvage preserved).

## Unit 2 — FS timeout default 2700 + visible effective budget  (commit 2)

- [ ] RED: test asserting `--fs-timeout` default is 2700 and that the effective timeout appears in
      the per-seed entry / cell result (`timeout_seconds`). Run → FAIL.
- [ ] GREEN: change default to 2700; put `timeout_seconds` (effective) into the returned result →
      per-seed `_entry` and `cell_results.json`; print effective FS budget on the cell line. Run → PASS.

## Unit 3 — reap the gem5 child on timeout  (commit 3)

- [ ] RED: test drives the run helper with a fake `Popen` that ignores SIGTERM, asserts: timeout path
      sends SIGTERM then SIGKILL to the process group, calls `wait()` (reaped), and records exit
      code / signal. Run → FAIL.
- [ ] GREEN: add `_run_capture(cmd, timeout, out_file, err_file)` using `Popen(start_new_session=True)`;
      on `TimeoutExpired` killpg(SIGTERM) → killpg(SIGKILL) → `communicate()`/`wait()`; return
      `(exit_code, timed_out, term_signal)`. Route FS + SE paths through it. Update
      `test_lsu_campaign_propagation.py` fakes to patch `Popen`. Run → PASS.
- [ ] Regression: full `python3 tools/lsu_test_runner.py` → FAIL count ≤ baseline 13, no NEW FAIL.

## Verification (per unit)
`python3 tools/lsu_test_runner.py` (real summary quoted); targeted new test; real truncated-file proof.

## Commit / push
`[LSU][MDSPEC][R6-CAMPAIGN] <unit>` per commit; `git push -u origin r6-campaign`; summary → `runs/lsu/r6_reports/L20.md`.
