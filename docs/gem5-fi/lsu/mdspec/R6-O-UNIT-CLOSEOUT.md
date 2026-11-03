# R6-O-UNIT — closeout status (2026-11-03)

Scope: the 10 authoritative O-F0/F5 RunIDs only. F0 seed1/2/3; F5 seed1 bounded
diagnostic. No P unit, no F1/F2/F3/F4/F6, no workload/fault substitution.

**Status: PARTIAL_BLOCKED_6_OF_10_RUNIDS — F0 complete 3/3 for O01/O02/O03
(9 seeds); O02-F5 seed1/2/3 accepted as authorized bounded
`Timeout`/`guest_livelock` diagnostics (not COMPLETE/PASS); O04/O05/O06/O07/O09
remain blocked with named evidence. The authoritative 10 RunIDs are NOT all
3/3 and this document does not claim so.**

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

## 3. O02-F5-W7 — authorized bounded Timeout/livelock diagnostics (3 seeds)

User ruling 2026-11-03: a sustained retry/no-progress episode terminated at a
pre-set observation bound is a legitimate result — `run_outcome=Timeout`, with
`diagnosis=guest_livelock` only on sufficient causal evidence; never rewritten
as Masked/Crash/contained; generic admission unchanged (no other Timeout is
auto-certified).

| seed | dir | injections | consumed | contained L2 | unresolved L1 | squash | pending | outcome | acceptance |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `f5_diag_20261103_r2` | 1010 | 1008 | 1008 | 2 | 2 | 0 | Timeout | AUTHORIZED_TIMEOUT_LIVELOCK |
| 2 | `f5_diag_20261103_seed23` | 70,861 | 70,859 | 70,859 | 2 | 2 | 0 | Timeout | AUTHORIZED_TIMEOUT_LIVELOCK |
| 3 | `f5_diag_20261103_seed3` | 64,403 | 64,401 | 64,401 | 2 | 2 | 0 | Timeout | AUTHORIZED_TIMEOUT_LIVELOCK |

All seeds: 0 successful STXR after injection; stable ~5,994-tick retry cadence;
guest stops at `LITMUS free atomic …` with no FINAL; both cores active; host
speed 91.5–94.8% of golden; graceful SIGINT at 1200 s with complete stats and
raw gzip EOF. The 2 unresolved faults per seed are LDXRs squashed at
`load_queue_uncommitted` (fault 2/15), not pending and not contained. Per-seed
diagnostic docs (not COMPLETE seeds, not in COMPLETE counts):
`runs/lsu/R6_O_F5_DIAGNOSTIC_DOCS/O02-F5-W7-seed{1,2,3}.md`; full per-fault
ledgers `seed{1,2,3}-faults.json`.

Analyzer-cap defect (seed2/3): raw `prop_evt.txt.gz` was complete (425,164 /
386,417 events) but `lsu_prop_fields.read_stream` caps at `EVENT_CAP=200000` and
the campaign mislabeled that as “incomplete gzip … killed mid-write”. Minimal
fix: `detect_evidence_truncation` now re-checks raw gzip EOF and reports
`analysis capped at EVENT_CAP` (still marks chain evidence truncated; never
treats the capped prefix as complete). `tools/lsu_o_f5_livelock_accept.py`
recomputes the full chain from the raw stream and records
`COMPLETE_RAW_ANALYSIS_CAPPED`. Seed2 was not rerun; seed3 was launched
separately after the campaign stopped early, with identical semantics/bounds.
Negative tests cover raw truncation, Timeout without causal evidence, a pending
fault, a successful STXR after injection, chain_end not at the boundary, and
non-Timeout outcomes.

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
- The 3 O02-F5 diagnostic seeds are **deliberately not registered** in
  `pilot_evidence.json`: registering them would let the generic chain gate treat
  a Timeout as an ordinary pilot sample. Their acceptance lives in the separate
  `acceptance.json` axis and in `R6_O_F5_DIAGNOSTIC_DOCS`; the F5 cells remain
  outside COMPLETE counts.
- `test_lsu_r6_reconcile_realroot.py` snapshot updated: admitted set is now
  `T05-F0-W4 + O01/O02/O03-F0-W7`; READY remains exactly 1 (`T05-F0-W4`);
  O rows are admitted but upstream-BLOCKED (admission ≠ unlock).
- Global `R6-STATUS-TABLE` still reports O01/O02 UNPROVEN and O03 TRUNCATED
  because it scans the retained historical streams; the 9 current seeds are all
  admitted/certified. Snapshot:
  `runs/lsu/r6_reports/R6-STATUS-TABLE-20261103-o-unit.{md,json}`.

## 6. Verification

- `python3 -m pytest -q tests/`: **309 passed, 10 failed**. The same 10 failures
  reproduce on the pre-change baseline (A4 frozen-binary census / lost a1632e0f
  binary, CLOSED_ACCEPTED_LOSS; A-doc evidence paths to the missing
  r6-f5-noeffect binary; stale 39-vs-65 S-doc count/EOF assertions).
  **NEW FAIL = 0.**
- `tests/test_lsu_r6_reconcile_realroot.py`: **ALL PASS** (READY still only
  T05-F0-W4; O admitted rows remain upstream-BLOCKED).
- `python3 -m pytest -q tests/test_lsu_o_unit_chain.py`: **3 passed**.
- `python3 -m pytest -q tests/test_lsu_o_f5_livelock_accept.py`: **8 passed**,
  including negative tests for raw truncation, no-causal Timeout, pending fault,
  successful STXR after injection, chain_end not at the boundary, non-Timeout,
  plus analysis-cap-vs-raw-truncation.
- `tests/test_lsu_campaign_truncation.py`: **ALL PASS**, including the new
  `analysis capped + raw gzip complete` case.
- No C++ change this round beyond the already-committed `f9a9756c`; no rebuild
  needed. No admission/conservation rule was relaxed; no SKIP/XFAIL used.

## 7. Repository state

- Branch `fix/r6-o-unit-20261103`, base `bb35c522`; before this F5 round HEAD
  was `5d23b4d7` (F0 docs/evidence). F5 tooling/docs commits
  `7ea5c714`, `63480802`, `2be26f67` were pushed and fast-forwarded (non-force)
  into `origin/fi-ding` after the divergence check; the branch and
  `origin/fi-ding` point at the same commit chain.
- The global `R6-STATUS-TABLE` still shows O02-F5-W7 as UNPROVEN/BLOCKED and
  O01/O02 as UNPROVEN / O03 as TRUNCATED because it scans retained historical
  pre-fix streams and does not accept Timeout diagnostics. This is intentional:
  the separate authorized acceptance does not modify generic admission.
- The unit is explicitly **partial**: the authoritative 10 RunIDs are not all
  3/3; 6 RunIDs remain BLOCKED with named evidence. F0 (9 seeds) and the F5
  three-seed authorized diagnostics are the completed work.
