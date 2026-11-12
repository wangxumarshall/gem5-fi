# LSU v3.3.3 — Researcher Decision Packet (one-shot)

**Date:** 2026-11-12
**Baseline:** HEAD `3097ad82` / binary `070d68a6…`
**Purpose:** one consolidated approval request for every decision that changes the formal workload/context identity or the frozen-configuration interpretation. Evidence is from the six Phase-1 reports and raw `audit_v3_3_2/` artifacts.
**Rule:** no SampleRunID or Seed changes are requested anywhere below. The frozen workbook is never overwritten.

---

## Part A — Workload adoption (30 candidate contexts)

| Model | Original design | Candidate | What is being approved |
|---|---|---|---|
| FW02 | W4 `sq_forward` | `workloads/directed/sq_forward_w4v2` | Adopt the load-preserving W4-v2; correct the in-main event count from 67 to 60 |
| RP01 | W7 `replay_dependency` | `workloads/directed/replay_partial_v332` | Adopt the partial-overlap replay workload; accept HANG_WATCHDOG as the designed terminal |
| MD04 | W7 `replay_dependency` | `workloads/directed/md04_violations_v332` | Adopt the violation-enhanced workload; re-measure the count on the final binary |
| SQ01 | W3 `sq_drain` | `docs/.../workloads/sq_reload_v3212` | Adopt the same-address reload workload |
| SQ03 | W3 `sq_drain` | `sq_reload_v3212` | Adopt; freeze the MASKED / visibility-timing-shift label (4/5 moved, 1/5 lifecycle-only) |
| SP05 | W6 `store_path` | `sq_reload_v3212` | Adopt after the `store_data_fnv` binding is verified on the new build |

### A.1 FW02 — `sq_forward_w4v2`

1. **Original problem:** frozen W4 `sq_forward` has **no data loads in `main`** (only an `ldp` stack restore), so it cannot form an in-main store→load forwarding pair. The original pilot was MASKED with no consumer.
2. **Source/disassembly evidence:** `main` contains full-overlap `str/ldr` at `0x400530/0x400538`, a sub-width 8B-store/4B-load-at-+2 pair at `0x400570/0x400574`, and pairs at `0x40061c/0x400620` and `0x400654/0x400658`. The ELF rebuilds byte-identically from the committed source (`gcc -O2 -static`); ELF SHA `a08fb3a7…`.
3. **Microarchitectural evidence:** independent census parse: ordinals 1–7 are pre-main stack/libc; ordinals 8–67 are exactly **60 in-main** eligible forwarding events (the “67 in-main” claim is inflated by 7). Five selected ordinals 13/25/37/49/61 are the 10/30/50/70/90 percentiles of ROI 8–67 (N=60). Fault runs show 4 SDC + 1 MASKED (R03); each control prints golden.
4. **Semantics preserved:** the fault is still the F6 `f6_fw02` suppressed-forward decision; the workload changes the consumer, not the hook.
5. **Five contexts:** 5/5 distinct dynamic stores/loads with the selected ordinals; commands verified.
6. **Chain closure:** 4/5 direct dataflow to the oracle; R03 MASKED is mechanism-consistent (`normal_decision=forwarded; fault_decision=suppressed; memory_path=1; replay_count=0`).
7. **Golden/oracle:** `1f4cbf14327717df`; 5/5 controls PASS; 4/5 faults FAIL; R03 PASS.
8. **ID/Seed/Excel impact:** all five keep their frozen SampleRunID/Seed; add a workload row and an `OVERRIDE_APPROVED` status; no frozen ID/seed changes.
9. **Recommendation:** **ADOPT**, correcting the prose to 60 in-main.
10. **Risk if rejected:** FW02 returns to a workload with no forwarding in main; the model cannot be part of a formal causal study.

### A.2 RP01 — `replay_partial_v332`

1. **Original problem:** frozen W7 `replay_dependency` has only full 8B overlap; the model needs a partial-overlap store→load pair to exercise `PartialAddrRangeCoverage`.
2. **Evidence:** `str` at `0x40055c`, `ldur` at `0x400560` (+6, 2-byte overlap). Count-only: 260 total eligible, **255 with `load_pc=0x400560`**, 255 distinct tuples; ROI 1–255; ordinals 26/77/128/179/230 correct. ELF SHA `3f880cba…`.
3. **Microarchitectural evidence:** all five faults fire the skip once and end at the in-simulator watchdog (`CHAOS_RP01_WATCHDOG=EXPIRED`, 20M-cycle deadline, exit 1); the five controls complete and print golden.
4. **Semantics preserved:** the fault remains “skip one `rescheduleMemInst`”; the workload creates the partial-overlap consumer.
5. **Five contexts:** all five share static PC/geometry, but are genuinely distinct dynamic executions (load_seq 16293/23229/30165/37101/44037; distinct lq idx/gen, store_seq, tick). This is a legitimate dynamic-context distinction; it must be stated.
6. **Chain closure:** HANG_WATCHDOG with a direct skip + internal watchdog + no checksum; no SDC claim. The watchdog is internal and the post-skip run produces no forward progress/checksum.
7. **Golden/oracle:** `f3b1c554273d23f7`; controls PASS; faults have no checksum by design.
8. **ID/Seed/Excel impact:** five frozen IDs/seeds retained; workload override recorded; terminal `HANG_WATCHDOG` with `watchdog=internal`.
9. **Recommendation:** **ADOPT**, with the static-PC caveat and the watchdog terminal documented.
10. **Risk if rejected:** no partial-overlap replay context; RP01 loses its designed scenario.

### A.3 MD04 — `md04_violations_v332`

1. **Original problem:** frozen W7 `replay_dependency` had only one eligible violation in the v3.3.1 census (N_ROI=1), too few for five distinct contexts.
2. **Evidence:** eight in-main violation pairs at the current PCs; the five selected ordinals 3/5/6/8/10 map to five distinct real pairs (L1/L3/L4/L6/L8). ELF SHA `dd241c30…`.
3. **Microarchitectural evidence:** the hook suppresses the violation report once; R01 is MASKED with `load_complete=1`; R02–R05 are SDC with `load_complete=0`; controls PASS.
4. **Semantics preserved:** still `SKIP_M5PANICFAULT_RETURN_ONCE` at `LSQUnit::checkViolations`.
5. **Five contexts:** 5/5 distinct pairs; ROI 3–10 (N=8); percentiles correct.
6. **Chain closure:** 4 SDC direct to oracle; R01 MASKED by inert-after-completion (not error-overwritten), documented.
7. **Golden/oracle:** `22be5ae3364d0c9f`; controls PASS.
8. **ID/Seed/Excel impact:** five frozen IDs/seeds; workload override; re-measure the 11-event split on the final binary before freezing.
9. **Recommendation:** **ADOPT**, conditional on the final-binary count re-measure and the R01 mechanism label.
10. **Risk if rejected:** too few violation events for five contexts.

### A.4 SQ01 — `sq_reload_v3212`

1. **Original problem:** W3 `sq_drain` stores to the array but reads it only once at the end; the selected lane is never consumed, so SQ01 is MASKED with `reload_seq=0`.
2. **Evidence:** `str` at `0x40053c`, `dmb ish`, same-address `ldr` at `0x400544`, consumer at `0x400550`; ELF SHA `bcab9cc5…`.
3. **Microarchitectural evidence:** 5/5 `COMPLETE_CHAIN`; `mem_write_hash == reload_data_hash == consumer_hash` (`21d2…`, `d4e5…`, `336b…`, `e0a1…`, `4cd1…`); the reload is an L1D read (`sq_entry_id=-1`, no forwarding decision); the injected byte differs from the source-derived value in exactly byte0^0x08.
4. **Semantics preserved:** still `SQEntry::_data[0] ^= 0x08`.
5. **Five contexts:** ordinals 1018/1044/1069/1095/1121; distinct store seq/addr/lq idx/gen.
6. **Chain closure:** 5/5 direct to oracle FAIL.
7. **Golden/oracle:** `7df5034c23f3e703`; controls PASS; faults FAIL 5/5.
8. **ID/Seed/Excel impact:** five frozen IDs/seeds; add the workload row; no ID/seed changes.
9. **Recommendation:** **ADOPT**.
10. **Risk if rejected:** SQ01 remains a no-consumer MASKED model.

### A.5 SQ03 — `sq_reload_v3212` (conditional)

1. **Original problem:** W3 `sq_drain` had no later load on the lane; the `_canWB` effect was lifecycle-only.
2. **Evidence:** same workload; `_canWB 0→1`, `storesToWB 0→1`, no address/size/data change; reload hash equals the unfaulted source-derived value in all five; ELF SHA `bcab9cc5…`.
3. **Microarchitectural evidence:** 4/5 contexts move the cache-block update before commit (`CHAIN_VISIBILITY_MOVED`); 1/5 (ordinal 1047) is `LIFECYCLE_ONLY` (block update after commit). In all five the reload request is after commit, so no pre-commit consumer is observable; the oracle PASSes.
4. **Semantics preserved:** yes; the fault changes visibility timing, not data.
5. **Five contexts:** ordinals 1021/1047/1072/1098/1124; distinct dynamic stores.
6. **Chain closure:** MASKED / visibility-timing shift; the 4/5 + 1/5 split is the honest result.
7. **Golden/oracle:** `7df5034c23f3e703`; controls PASS; faults PASS by design.
8. **ID/Seed/Excel impact:** five frozen IDs/seeds; label freeze required.
9. **Recommendation:** **CONDITIONAL ADOPT** — adopt only if the MASKED/visibility label and the 4/5 + 1/5 split are frozen into the paper/workbook language.
10. **Risk if rejected:** the model cannot distinguish early visibility from no effect; the richer scenario is lost.

### A.6 SP05 — `sq_reload_v3212` (conditional, unblocked by the source fix)

1. **Original problem:** W6 `store_path` has no load reading the skipped lane; SP05 was MASKED with `NO_RELOAD_OBSERVED`.
2. **Evidence:** the `sq_reload` reload reads the skipped lane; `completeStore` fires, `storesToWB 1→0`, `mem_sent=0`, `write_skipped=1`, no `store_mem_write`, reload reads zero (`a8c7f832281a39c5`), consumer observed, oracle FAIL 5/5; ELF SHA `bcab9cc5…`.
3. **Microarchitectural evidence:** 5/5; the model record currently says `store_data_fnv=null` → `RELOAD_UNVERIFIABLE` because the recorder lacks the SQ bytes.
4. **Semantics preserved:** yes; the fix is recording-only.
5. **Five contexts:** ordinals 952/978/1003/1029/1055; distinct dynamic stores.
6. **Chain closure:** complete once `store_data_fnv` is populated (`data_correct=0`, `CHAIN_VISIBILITY_LOST`) and the `sp05_write_skipped` early anomaly is emitted.
7. **Golden/oracle:** `7df5034c23f3e703`; controls PASS; faults FAIL.
8. **ID/Seed/Excel impact:** five frozen IDs/seeds; label `SDC` only after the hash is present.
9. **Recommendation:** **CONDITIONAL ADOPT**, with adoption finalized after the new-build SP05 verification.
10. **Risk if rejected:** SP05 loses its architectural consumer and remains a `RELOAD_UNVERIFIABLE`/MASKED model.

---

## Part B — Policy decisions (independent of workload choice)

### B.1 A01/A03 PRE-retry root-cause fix and ordinal re-census

- **Finding:** `LSQ::pushRequest` counts a `translationStarted()` retry as a new eligible event and injects into a by-value address that is discarded when `savedRequest` is reused. A01-R03 proves the injection never reached the request (`a01_ea_discarded; applied_to_request=0; discard_reason=saved_request_reuse`); the real request was already in flight at the golden EA.
- **Fix:** guard the PRE block with `!inst->translationStarted()` and count skipped retries. The fault definitions are untouched; only the eligible-event stream changes.
- **Consequence:** the A01/A03 ROI and five percentile ordinals must be re-censused on the fixed binary. **SampleRunID and Seed stay frozen.** The old ordinal set is retained as v3.3.2 history.
- **Approval requested:** approve the source fix and the re-census (not a workload change).
- **Risk:** A01/A03 contexts move to different dynamic instructions; other PRE-family models outside the 12-model scope are also affected and must be re-validated in their own rounds.

### B.2 A03 terminal classification

- **Finding:** all five A03 fault runs print a final application checksum; the five values (`1fd794b8489219e1`, `9fc828ecfead80f9`, `bfccf156021968dd`, `191a781887e50cec`, `20057ce453d4f1e9`) differ from golden `728e604ffcec539d`; every control prints golden. The guest then fails to exit because the persistent fault corrupts the exit path; the driver’s 30 s kill truncated the trace.
- **Proposed terminal:** `SDC` / `ORACLE_FAIL`, qualifier `POST_ORACLE_SIM_HANG`; add an in-simulator watchdog (budget derived from the control completion tick) that emits the lifecycle line, flushes the trace, and exits gracefully. If a future run reaches the watchdog with no checksum, it is `HANG_WATCHDOG`, not SDC.
- **Approval requested:** approve the terminal relabel and the watchdog (not a fault-semantics change).

### B.3 A01-R02 SQUASHED qualifier

- **Finding:** the squash record says `squash_cause=unrelated; fault_caused=0`; the faulty instruction did not enter architectural state.
- **Proposed label:** keep `SQUASHED` but add `UNRELATED_SQUASH_NO_ARCH_ENTRY`; do not claim the fault caused the squash. This satisfies the SQUASHED evidence requirement (the target instruction was squashed and did not enter architectural state) without overclaiming causality.
- **Approval requested:** approve the label.

### B.4 Config freeze

- **Finding:** the authoritative matrix has `WarmUp=NEEDS_RESEARCHER_CONFIRMATION` and `ROI=NEEDS_RESEARCHER_CONFIRMATION` for all 60 rows, and `ConfigFrozen=NO`.
- **Proposed freeze:** Warm-up = 0; ROI = the model-specific main-loop eligible window measured on the final v3.3.3 binary; executed EventOrdinal = the measured percentile ordinal; design EventOrdinal 1–5 retained as legacy metadata; final binary SHA recorded in Part C after validation.
- **Approval requested:** approve the freeze definition now; the exact final SHA is validated and recorded before the campaign.

### B.5 Executed vs design EventOrdinal

- **Finding:** the frozen matrix’s `EventOrdinal` is 1–5 for all models and its own provenance text says the C++ tiers select by seed, not ordinal; the v3.3.3 percentile design selects a measured eligible ordinal.
- **Proposed schema:** `Design_EventOrdinal` (1–5, frozen) and `Executed_EventOrdinal` (measured) as separate columns; the readiness/causal tables use the executed value.
- **Approval requested:** approve the schema.

---

## Part C — What is NOT being requested

- No SampleRunID change, no Seed change, no model merge/delete, no new model, no scope expansion.
- No edit to the frozen v3.2.7 workbook.
- No lowering of any Ready Gate criterion.
- No formal campaign start. The campaign starts only after the Ready Gate and a separate explicit authorization.

## Part D — Recommendation summary

| Item | Recommendation |
|---|---|
| FW02 W4-v2 | ADOPT (fix the 67→60 prose) |
| RP01 partial-overlap | ADOPT (document static PC + watchdog terminal) |
| MD04 violations | ADOPT (re-measure count on final binary; document R01 mechanism) |
| SQ01 `sq_reload_v3212` | ADOPT |
| SQ03 `sq_reload_v3212` | CONDITIONAL ADOPT (MASKED/visibility label + 4/5+1/5 split) |
| SP05 `sq_reload_v3212` | CONDITIONAL ADOPT (after `store_data_fnv` verification) |
| A01/A03 PRE-retry fix + re-census | APPROVE |
| A03 SDC/post-oracle-hang terminal | APPROVE |
| A01-R02 SQUASHED qualifier | APPROVE |
| Config freeze definition | APPROVE (exact SHA recorded after validation) |
| Executed vs design EventOrdinal | APPROVE |

If any item is rejected, the affected model's contexts are not frozen; all approval-independent code/tooling work continues, and the final verdict will name the rejected item as the blocker rather than silently dropping it.
