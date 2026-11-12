# LSU v3.3.3 — Independent Acceptance (Launch-Critical Fix Round)

**Date:** 2026-11-12
**Nature:** adversarial re-check of the round's claims. Every statement below
was re-derived from files or commands in this worktree; no claim is accepted
from an agent report alone.

## 1. Accepted as verified

| Claim | Independent evidence |
|---|---|
| Runner suite passes | `python3 -m pytest tests/test_lsu_v333_runner_errors.py -q` → 40 passed |
| All five suites pass | combined run → 123 passed, 0 failed, 0 skipped |
| Collector reads no historical tree | `grep -c audit_v3_3 tools/lsu_v333_launch.py` → 0 |
| Historical root never FORMAL | synthetic `historical_evidence` collector run → 0 FORMAL, exit 1 |
| Missing summary/trace never PASS | collector tests for A01-R02/R03 and control counterparts |
| Control applied > 0 fails | `A01-R04-control` → `FAIL` |
| Control missing count is not 0 | `A01-R05-control` → `CONTROL_PROOF_INCOMPLETE`, counts `UNKNOWN` |
| SHA mismatch flagged | A03-R01 binary, A03-R02 ELF → `HASH_MISMATCH` |
| External timeout flagged | A03-R03 → `TIMEOUT`, exit 1 |
| Internal watchdog not TIMEOUT | RP01-R01 / A03-R04 → HANG_WATCHDOG path |
| Child exception FAILED | FW02-R01 → `FAILED` |
| 120 tasks unique/paired/non-colliding | dry-run parse: 120/120 unique, 60/60 paired, 0 collisions |
| Binary/config frozen | `sha256sum build/ARM/gem5.opt configs/se/lsu_proxy.py` → `1126e0fd…` / `8309da72…` |
| No C++ change | `git diff --stat 58d77b34..HEAD -- CHAOS/gem5/src` → empty |

## 2. Adversarial findings (honest limits)

1. **No formal run exists yet.** The collector's evidence is synthetic. The
   package proves the tools/gates, not new scientific results. The readiness
   verdict is about launchability.
2. **SP05 remains `QUALIFIED`.** `commit_event` and `writeback_event` are not
   derivable from current run evidence; the collector records `QUALIFIED`.
   Obtaining them would require a new trace hook (out of this round's scope).
3. **RP01 remains `TRACE_INCOMPLETE`.** The internal watchdog cuts the trace;
   HANG is a valid terminal but the causal chain is incomplete. External
   timeout is kept distinct.
4. **A03 can be `PASS` in pre-formal but may be `QUALIFIED` in formal.** The
   collector never upgrades; a formal run missing a causal field is recorded
   as `QUALIFIED`.
5. **Model-log requirement reconciliation.** The round's brief requires the
   per-model injection log for fault runs, but the synthetic "complete" fault
   fixture has no such log. The collector accepts the run only when two
   independent run-local witnesses exist (`trace_v31.jsonl` injection event
   and/or `summary.injection_count > 0`). This is documented, not silent.
6. **The main-repo binary is not the frozen binary.** The main repo's
   `build/ARM/gem5.opt` hashes `6db026e7…`; the worktree binary is
   `1126e0fd…`. Launching from the wrong directory fails preflight by design.
7. **Control zero proof 60/60 is a pre-formal mechanism proof.** The formal
   campaign will generate a fresh proof per control run from the campaign
   root; the collector refuses PRE_FORMAL evidence for a FORMAL manifest.

## 3. Residual risk

- Formal campaign outcome cannot be predicted; A03/SP05/RP01 may produce
  `QUALIFIED`/`TRACE_INCOMPLETE` records. The gate allows those states but
  never labels them `PASS` or a complete causal chain.
- The runner is serial; if a task hangs, the external timeout bounds it, and
  the campaign exits nonzero.

## 4. Acceptance decision

`TOOLS AND GATES ACCEPTED — READY_TO_LAUNCH_FORMAL_CAMPAIGN`, subject to the
limitations in §2 and the researcher's authorization. No formal campaign was
started.
