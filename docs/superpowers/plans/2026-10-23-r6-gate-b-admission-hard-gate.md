# R6-GATE-B: LSU formal-admission hard gate

> Executed by Agent B on worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-gate`
> (branch `r6-gate`, base `lsu-mdspec-20261019` @ `97f74786`). Plan-driven, TDD, one
> commit per unit, `[LSU][MDSPEC][R6-GATE]` prefix, push to `r6-gate` after each unit.

**Goal:** make `docs/gem5-fi/lsu/mdspec/ready_contract.json` a HARD GATE: an activated
sample is READY **only if** either

1. it has a family-specific COMPLETE L0→L5 chain on one parent-event DAG; or
2. propagation stops at some layer with an explicit containment layer + reason +
   per-layer metrics, and every later layer is justified `N/A(contained)`.

Forbidden (loud failure, never silent pass): any `Unknown` in an activated sample;
`cache_access` impersonating the TLB's L1; stitching edges across branches / requests /
reversed in time; READY because of `activated=1`, `RC=0`, or a `chain_end` alone; a
missing per-layer mandatory metric.

**Architecture.** All rules live in one new pure function
`lsu_chain_check.check_admission(bundle)` (returning named violation tokens), consumed by
`lsu_ready_contract.build_contract` through a new per-RunID chain-evidence resolver that
reads the pilot `prop_evt.txt.gz` recorded in `pilot_evidence.json`. A RunID is READY
only when coverage is PASS **and** its pilot chain is admitted. Evidence root is
`LSU_CHAIN_EVIDENCE_ROOT` (default `REPO`), because the untracked `runs/` pilot data
lives in the base worktree, not in this worktree.

**Tech stack:** Python 3 stdlib only. Tests are plain scripts run by
`tools/lsu_test_runner.py`; PASS marker `ALL PASS`, failure marker `FAILURES: [...]`.

## File ownership (only these)

`tools/lsu_chain_check.py`, `tools/lsu_ready_contract.py`, `tools/lsu_audit.py`,
`tools/lsu_blocked_triage.py`, `tools/lsu_prop_fields.py`,
`tests/test_lsu_chain_check.py`, `tests/test_lsu_ready_contract_*.py`,
`docs/gem5-fi/lsu/mdspec/R6-GATE-B-report.md`, `ready_contract.json/.md` (regenerated).
No C++, no `lsu_campaign.py`, no `lsu_runid_map.py`, no `lsu_coverage_matrix.py`.

---

### Task A — `check_admission` hard gate in `lsu_chain_check.py` (TDD)

- [ ] A.1 RED: add section `[12]` to `tests/test_lsu_chain_check.py` calling
      `CC.check_admission(bundle)` for each forbidden case; run it, quote the real
      `AttributeError`-style failure.
- [ ] A.2 Implement `GATE_VIOLATIONS`, `MANDATORY_METRICS`, `_has_unknown`,
      `_splice_detected`, `_cross_request`, `_time_reversed`, `_containment_ok`,
      `check_admission`. Re-run: quote `ALL PASS`.
- [ ] A.3 Regression: `python3 tests/test_lsu_chain_check.py` still `ALL PASS`.

### Task B — wire the gate into the contract (`lsu_ready_contract.py`)

- [ ] B.1 Add `chain_admission(runid, evidence_root)` + `CHAIN-EVIDENCE-MISSING` /
      `CHAIN-UNPROVEN` categories; READY now requires admission.
- [ ] B.2 RED→GREEN in `tests/test_lsu_ready_contract_category.py`: a fake activated
      RunID with a non-chain pilot is BLOCKED before/after; update census.
- [ ] B.3 Verify `test_lsu_ready_contract_verdict.py` and `-why.py` still PASS.

### Task C — regenerate contract + triage, report honest counts

- [ ] C.1 `python3 tools/lsu_ready_contract.py` (with `LSU_CHAIN_EVIDENCE_ROOT` set to
      the base worktree), quote READY/BLOCKED.
- [ ] C.2 `python3 tools/lsu_blocked_triage.py --contract ... --out
      docs/gem5-fi/lsu/mdspec/blocked_triage.md`, quote output.
- [ ] C.3 Full suite `python3 tools/lsu_test_runner.py`, quote summary, zero FAIL.
- [ ] C.4 `docs/gem5-fi/lsu/mdspec/R6-GATE-B-report.md`; commit + push.

## Honesty constraints

- Never relax a rule to keep READY high. A drop is expected and correct.
- Report `n/a` where a rule cannot be enforced yet, loudly.
- Quote only real command output.
