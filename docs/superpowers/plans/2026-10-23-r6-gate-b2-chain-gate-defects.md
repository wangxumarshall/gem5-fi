# R6-GATE B2-v2: chain-gate defect fixes (D1–D5)

> Agent B2-v2, worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-gate`
> (branch `r6-gate`, base commit `2b87cd9d`). Plan-driven, TDD, one commit per
> defect unit, prefix `[LSU][MDSPEC][R6-GATE]`, push `origin r6-gate` after each.

**Inherited state.** HEAD `2b87cd9d` is the B1 hard gate (`check_admission` +
contract wiring, suite `suites=53 ENV=5 FAIL=13 PASS=34 SKIP=1 NEW FAIL=[]`).
The dead predecessor left `docs/gem5-fi/lsu/mdspec/ready_contract.json`/`.md`
modified **uncommitted**: it re-pointed `chain_gate.evidence_root` at this
worktree, so every pilot row degraded to `CHAIN-EVIDENCE-MISSING` although the
referenced PROP-EVT files really exist under
`.claude/worktrees/lsu-mdspec-20261019` (the root recorded at HEAD). Its `.md`
verdict line (real `--gate` output) is valid content; its per-row JSON rewrite is
not. Both are regenerated at the end with the honest root.

**Defects (all evidence-backed, real streams re-judged offline).**

| # | Defect | Real evidence |
|---|---|---|
| D1 | `_L5_OUTCOME_KINDS={"chain_end"}` + `_explicit_l5()` accept any `chain_end` whose `outcome` is not `run_end`/`unknown` ⇒ the lifecycle exit marker proves L5 | T04 event 1573 `chain_end detection_layer=None contained=0 outcome=errant_commit_seen corr=none` |
| D2 | `lsu_ready_contract.chain_admission` builds the bundle without `containment`/`oracle_outcome` ⇒ option (2) unreachable | T08-F0-W4 `tlb_translate_result field=walk_refill_lost detection_layer=L2 contained=1 outcome=translation_blocked` is rejected |
| D3 | `check_admission` compares request ids only between the ≤6 layer representatives | T04 `resp id=47 req=304` → `resp id=48 req=310` (direct DAG parent/child, both L3) yet `admitted=True` |
| D4 | `tlb_l1_faked_by_cache_access` is TLB-only; the generic map sends `cache_access → L1` | C01-F0-W6 path `inj→cache_access(L1)→…`; the guard is family-blind |
| D5 | The exact T04 shape must not be accepted as `full` | `check_admission(T04 real) → admitted=True, terminal=full` |

**Rulings applied.**

- L5 evidence = a *real detection event*: a non-lifecycle kind carrying a
  non-empty `detection_layer` **and** `outcome` **and** a chain-correlating
  `corr` (∈ `seq_primary|addr_fallback|origin|taint_prop`), on the fault's
  ancestry. `chain_end` is lifecycle-only (`corr=none`) and can **never** alone
  prove L5 — enforced structurally (it can no longer occupy any layer), so
  `ready_by_chain_end_only` is no longer a message-only crutch.
- Cross-request stitching is caught on the **whole chosen ancestry**, not only
  between layer representatives.
- `cache_access` may not stand in for a non-cache family's L1; conversely a
  non-cache kind may not stand in for the cache family's L1.

## File ownership (only these)

`tools/lsu_chain_check.py`, `tools/lsu_ready_contract.py`,
`tools/lsu_blocked_triage.py`, `tools/lsu_prop_fields.py`,
`tests/test_lsu_*.py`, `docs/gem5-fi/lsu/mdspec/ready_contract.json|.md`,
this plan, `docs/gem5-fi/lsu/mdspec/R6-GATE-B2-report.md`,
`runs/lsu/r6_reports/B2.md`. No C++, no `lsu_campaign.py`,
`lsu_l5_classify.py`, `lsu_obs_core.py`.

---

### Task 1 — D1 + D5: L5 must be the real detection event

- [x] 1.1 RED: `tests/test_lsu_chain_check.py` — new section `[13]`: (a) a
      `chain_end outcome=errant_commit_seen` chain is not `full`; (b) the real
      T04 stream (skip if absent) is not `full` and not admitted;
      (c) `_explicit_l5` rejects every lifecycle `chain_end` payload.
      Quote the real FAIL output.
- [x] 1.2 Implement: strict `_explicit_l5` (kind + payload + chain `corr`),
      `_layer_of` returns `None` for lifecycle `chain_end` and `L5` for a real
      detection witness, `_event_has_prefix` uses the *observation* layer.
      Update the positive-control fixtures in `[1]`, `[3]`, `[8]` and the
      contract-gate `FULL` fixture to a real detection witness.
- [x] 1.3 Re-run `tests/test_lsu_chain_check.py`,
      `tests/test_lsu_ready_contract_gate.py` → quote `ALL PASS`.
- [x] 1.4 Commit + push.

### Task 2 — D3: cross-request edges on the whole ancestry

- [x] 2.1 RED: real T04 must be rejected with `cross_request_edge`.
- [x] 2.2 Implement `_ancestry_request_breaks()`; wire into `check_admission`.
- [x] 2.3 Re-run the chain-check + gate tests → `ALL PASS`. Commit + push.

### Task 3 — D4: `cache_access` may not fake a non-cache family's L1

- [x] 3.1 RED: fixture with an atomic/LQ-family chain whose L1 witness is
      `cache_access` → `cache_access_faked_l1`; a cache-family chain whose L1 is
      not `cache_access` → `cache_l1_missing`.
- [x] 3.2 Implement family inference (`_UNIT_FAMILY` by RunID prefix) + the two
      guards; add tokens to `GATE_VIOLATIONS`.
- [x] 3.3 Re-run the chain-check + gate tests → `ALL PASS`; real C01 stays
      admitted-neutral (no regression). Commit + push.

### Task 4 — D2: containment (option 2) reachable from real evidence

- [x] 4.1 RED: `chain_admission` on the real T08/T05 pilots currently returns
      `detected_contained` terminal but `admitted=False` (no containment bundle).
- [x] 4.2 Implement `lsu_chain_check.containment_from_events()` (explicit
      contained=1 detection evidence → layer reason metrics na_layers) and
      thread `containment` + `oracle_outcome` through
      `lsu_ready_contract.chain_admission`.
- [x] 4.3 Quote the real T08/T05 admission GREEN. Commit + push.

### Task 5 — regenerate the contract, report honest counts

- [x] 5.1 Restore the honest evidence root
      (`LSU_CHAIN_EVIDENCE_ROOT=.claude/worktrees/lsu-mdspec-20261019`) and
      regenerate `ready_contract.json/.md` (+ triage md if it consumes it).
- [x] 5.2 Run the owned tests, then the full suite
      `python3 tools/lsu_test_runner.py`; confirm `NEW FAIL=[]`.
- [x] 5.3 Write `R6-GATE-B2-report.md` + `runs/lsu/r6_reports/B2.md`; commit +
      push.
