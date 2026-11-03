# R6-O-UNIT — closeout status (2026-11-03)

Scope: the 10 authoritative O-F0/F5 RunIDs only. F0 seed1/2/3; F5 seed1 bounded
diagnostic. No P unit, no F1/F2/F3/F4/F6, no workload/fault substitution.

**Status: PARTIAL — F0 complete 3/3 for O01/O02/O03; O02-F5 awaits a semantic
ruling; O04/O05/O06/O07/O09 remain blocked with named evidence.**

## 1. Platform and identity

- Checkpoint: `runs/lsu/r6_o_unit/mc_boot/cpt.243414599076` (tick 243414599076,
  2-core Ruby/CHI, O3). `m5.cpt` sha256
  `86e29fcf60973a063bf9422b3da2feb08d94086b032cd5ec33b55ca5033f5328`.
- Binary: `.claude/worktrees/r6-o-unit-20261103/CHAOS/gem5/build/ARM/gem5.opt`,
  sha256 `c6cccf5b490823d216d01bd2449031aef2d892c88cec5cd291c852bbe86ca87b`.
- Build-input check: changed C++ sources (`CHAOSExMon.{cc,hh,py}`, `isa.cc`,
  `lsu_multicore_fs.py`) have mtimes 19:14–19:17, before the 19:23 build;
  `scons -n build/ARM/gem5.opt` reports **no C++ recompiles** (only
  `[VER TAGS]` + `[LINK]` pending), so the objects match the committed sources.
  Source/analysis HEAD: `f87627176cb6e048fa5f0a3611d4bdc520b53419`
  (C++ repair `f9a9756c`).
- Workload: `workloads/litmus/litmus_free`, ELF sha256
  `6823afeb57194ded0aaf0dc2d7236468d973f252dc6b76abc72adc4789f4fed6`.
- Campaigns: `campaign2_20261103` (seed1, exit 0) and
  `campaign3_seed23_20261103` (seeds 2/3, max-parallel 2, exit 0).

## 2. F0 results — all 9 seeds PASS

Every seed: oracle `Masked`, terminal `detected_contained`, admitted=True,
certified=True, chain_valid=True, violations=[], events=6, faults=1, exit=0,
gzip EOF OK, stats non-zero, not truncated.

| RunID | seed | provable_to | injection tick | monitor/status change |
|---|---|---|---|---|
| O01-F0-W7 | 1 | L2 | 267499008225 | addr `0x835e4000→0x825e4000` (bit 24) |
| O01-F0-W7 | 2 | L2 | 267498981918 | addr `0x835e4000→0x835c4000` (bit 17) |
| O01-F0-W7 | 3 | L2 | 267499420812 | addr `0x835e4000→0x20835e4000` (bit 33) |
| O02-F0-W7 | 1 | L2 | 267499008225 | state fake: addr `0x835e4000→0x835e4040` |
| O02-F0-W7 | 2 | L2 | 267498981918 | state clear: flag `1→0` |
| O02-F0-W7 | 3 | L2 | 267499420812 | state clear: flag `1→0` |
| O03-F0-W7 | 1 | L3 | 267498615618 | `would_succeed=true→forced=false`; sq_idx 1484466 |
| O03-F0-W7 | 2 | L3 | 267498836730 | forced fail; sq_idx 1484474 |
| O03-F0-W7 | 3 | L3 | 267498954279 | forced fail; sq_idx 1484480 |

Layer semantics: `exmon_stxr` carries the injector's detection stage label L3,
but the authoritative checker treats an explicit detection event as L5 and
reports `provable_to` as the deepest contiguous **structural** layer below it.
O01/O02 stop at `exmon_rmw` (L2; the store failed, no `sq_complete`), while O03
has a real `sq_complete` (L3) after the forced-fail detection event. The
injector label is not the checker layer; `chain_end` is never L5.

Seed dispersion is real: injection tick, dyn_inst_seq, and monitor corruption
(bit position / fake-vs-clear) all differ across seeds. Program output is the
golden `FINAL=6b39e7aaa74b663f`, `violations=0`, `tries cpu0=39 cpu1=16`; the
oracle is Masked because the retry loop absorbs the failed SC.

Docs: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/O0{1,2,3}-F0-W7/…-seed{1,2,3}.md`
(9 files). Independent audit: 9/9 PASS, 392 markdown links checked, 0 broken
(`runs/lsu/r6_reports/R6-O-UNIT-DOC-AUDIT.{md,json}`).

## 3. O02-F5-W7 — bounded livelock diagnostic (ruling required)

- Directory: `runs/lsu/r6_o_unit/f5_diag_20261103_r2`; report `DIAGNOSTIC.md`.
- Bounds: gem5 concurrency 1; inner `--fs-timeout 1200 s`, grace 60 s; outer
  2400 s not hit; `/home` and MemAvailable thresholds never hit.
- Outcome: **run-level oracle `Timeout` (1010/1010)**; per-fault chain
  `detected_contained`/L2, admitted=True. These are reported side by side and
  **not** promoted to Masked/containment/PASS.
- Evidence: 1010 injections; 1008/1008 consumed SC = `mismatch_fail` and STXR
  `fail_retry`; zero successful STXR after injection; guest stops at
  `LITMUS free atomic …` without FINAL; all 1010 `chain_end` share
  finalTick 267504485742. Termination was a graceful SIGINT: stats written,
  both gzip EOF complete, `truncated=False`.
- No transient rewrite, no retry cap, no workload change, no post-hoc relabel.
- Ruling needed: (a) accept as expected Timeout/livelock outcome, (b) declare
  permanent-monitor × W7 retry-loop a semantics conflict and exclude the cell,
  or (c) add an explicit livelock terminal (semantic extension, requires user
  approval). Until then this cell is UNDER_MEASURED/Timeout.

## 4. Blocked cells (specific evidence, not "multicore-fs")

| RunID | blocker | exact reason |
|---|---|---|
| O04-F0-W7 | BLOCKED_INFRA + BLOCKED_WORKLOAD | classic `BaseCache::satisfyRequest` RMW hook cannot mount on Ruby/CHI; W7 carriers execute zero LSE (`cas/swp/ldadd/...` = 0) |
| O05-F0-W7 | BLOCKED_INFRA + BLOCKED_WORKLOAD | same classic-host incompatibility; `lost`/`dup` gate on `isAtomicOp()`; W7 has zero LSE |
| O06-F0-W7 | BLOCKED_SPEC | `maybeCorruptBarrier*` never calls `registerInjection` (no fault_id); `barrier_done` has no detection/outcome and no L5 terminal; O06-b stale SN does not gate |
| O07-F0-W7 | BLOCKED_SPEC | same missing registration/terminal; only barrier-SN proxy; process-global hooks vs per-CPU InstSeqNum |
| O09-F0-W7 | BLOCKED_INFRA | `rmw_latch`/`result_old` exists but lives in classic `BaseCache`; cannot mount on Ruby/CHI; W7 needs coherent multicore |
| O09-F0-W13 | BLOCKED_WORKLOAD (+INFRA) | PARSEC source/input/build assets absent; substituting a repo probe changes cell identity (ruling required) |

Full code/binary evidence: `R6-O-UNIT-CENSUS.md`.

## 5. Evidence registration / gate snapshot

- `pilot_evidence.json` additively registers the 9 O F0 seeds; pre-fix historical
  streams are preserved under `shadowed_paths` (files not deleted).
- `test_lsu_r6_reconcile_realroot.py` snapshot updated: admitted set is now
  `T05-F0-W4 + O01/O02/O03-F0-W7`; READY remains exactly 1 (`T05-F0-W4`);
  O rows are admitted but upstream-BLOCKED (admission ≠ unlock).
- Global `R6-STATUS-TABLE` still reports O01/O02 UNPROVEN and O03 TRUNCATED
  because it scans the retained historical streams; the 9 current seeds are all
  admitted/certified. Snapshot:
  `runs/lsu/r6_reports/R6-STATUS-TABLE-20261103-o-unit.{md,json}`.

## 6. Verification

- `python3 -m pytest -q tests/`: **301 passed, 10 failed**. The same 10 failures
  reproduce on the pre-change baseline (stashed changes): A4 frozen-binary
  census (lost a1632e0f binary, CLOSED_ACCEPTED_LOSS), A-doc evidence paths to
  the missing r6-f5-noeffect binary, and the stale 39-vs-65 S-doc count/EOF
  assertions. **NEW FAIL = 0.**
- `tests/test_lsu_r6_reconcile_realroot.py`: **ALL PASS**.
- `python3 -m pytest -q tests/test_lsu_o_unit_chain.py`: **3 passed**.
- No C++ change this round beyond the already-committed `f9a9756c`; no rebuild
  needed. No admission/conservation rule was relaxed; no SKIP/XFAIL used.

## 7. Repository state

- Branch `fix/r6-o-unit-20261103`, base `bb35c522`, prior HEAD `f8762717`.
- Not merged to `origin/fi-ding`: O02-F5 semantic ruling is pending; the unit is
  explicitly **partial**, not complete.
