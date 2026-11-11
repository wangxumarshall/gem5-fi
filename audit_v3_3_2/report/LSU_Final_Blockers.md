# LSU v3.3.2 — Final Blockers (shortest path to READY)

**Status: PARTIALLY_READY · 12_MODEL_FORMAL_READY = NO**

No implementation blocker prevents a formal campaign on the 30 frozen-workload
contexts; the blockers below are decisions plus three bounded evidence gaps.

## B1 — Candidate workloads need researcher approval (30 contexts)

FW02 (`sq_forward_w4v2`), RP01 (`replay_partial_v332`), MD04
(`md04_violations_v332`) and SQ01/SQ03/SP05 (`sq_reload_v3212`) are implemented
and dynamically proven but are not approved or written into the frozen workbook.
Without approval they cannot be frozen as the formal workload identity.

Decision needed: ADOPT / REJECT each candidate, and authorize the corresponding
workload/ELF/golden/ordinal update.

## B2 — A01-R03 is UNRESOLVED

Injection and a complete 9-event chain exist, but there is no register-writeback
value-divergence evidence (`UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE`).
Options: (a) accept UNRESOLVED for the formal run and report it as such, or
(b) add a writeback observer to the A01 chain and rerun R03. Do not relabel it
MASKED or SDC.

## B3 — A03 uses external timeout, not an in-simulator watchdog

The persistent bit-3 stuck-at fault can corrupt control flow; all five contexts
end as HANG after a 30 s wall bound with partial logs and the
`A03_LOG_CAPPED` marker. Activation and first-affected rows are recorded.
Adding an A03 watchdog (one bounded source change + rebuild) would give the same
watchdog quality as RP01.

## B4 — SP05 store-data hash is null

All five SP05 contexts show reload/consumer SDC and oracle failure, but the
chain records `store_data_fnv=null` and `stage_outcome=RELOAD_UNVERIFIABLE`.
Wire `store_data_fnv` (and the early-anomaly event) before calling the
store-data → visibility chain complete.

## B5 — SQ03 must be labelled a visibility shift, not SDC

SQ03 is MASKED in all five contexts; 4/5 show `CHAIN_VISIBILITY_MOVED` and 1/5
`LIFECYCLE_ONLY`. The paper/report must state "visibility-timing change, not
software-visible SDC". The oracle was not and must not be modified.

## B6 — Config/ROI/Warm-up freeze

`ConfigFrozen=NO`. Approve the ROI windows, percentile ordinals, Warm-up
fields, final binary SHA `070d68a6…`, and the final manifest before the
campaign. The frozen Excel is unchanged (`git diff 8f7a1354 -- …/excel` empty).

## What can start immediately after B1+B6

The 30 frozen-workload contexts (A01, A03, FW05, DA04, LQ04) can enter a
formal campaign with the recorded controls once the config is frozen; A01-R03
must be accepted as UNRESOLVED or fixed first.
