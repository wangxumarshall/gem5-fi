# DA04 trace fixes — v3.2.5 rerun evidence (R04/R05)

**Date:** 2026-11-08
**Binary:** `build/ARM/gem5.opt` sha256 `69a1ca9c5b1cbfb160d0502a8cad8acf7d17101625228978ec79ede588b2287d`
**Scope:** only R04/R05 were rerun (the other three pilots are unaffected by
the trace-hook changes). The v3.2.4 directories were **not** overwritten; the
reruns live in `pilots_v3_2_5/`.

## What changed

1. **Load memory-request events + real request time.** `noteMemRequest` now
   emits a `mem_req` node for every load whose range overlaps a registered
   faulted store byte, with `request_tick=`, `store_write_tick=`,
   `request_before_store_write=`, `candidate=`, `lq_entry_id` and `sq_id`.
   The JSONL timestamp of that node is the request tick, not the response tick.
2. **Causality anchored at the request tick.** `mayConsumeFaultByte` takes the
   load's request tick; a load that left the LSQ before the store's cache write
   cannot have observed the fault byte.
3. **Lossless edges.** Every synthesized ptag-order edge now carries
   `edge_type=ptag_sequence` and the source/destination hashes when present;
   C++ `prop_edge` rows default `edge_type` to `data` instead of null.

## R04 evidence

Command shape: `run_pilot.py --model DA04 --context-index 4
--preserve-sample-id --pilot-id DA04-R04 --event-ordinal 50`.

Overlapping load requests (all `candidate=0`):

| load seq | request tick | store write tick | request before write? |
|---|---|---|---|
| 19210 (previous "consumer") | 2286900 | 17042410 | **yes** |
| 24465 | 16934225 | 17042410 | yes |
| 25523 | 10235610 | 17042410 | yes |

The v3.2.4 chain used the seq-19210 response (tick 17889795), which arrives
after the write but whose **request left 14.7M ticks earlier** than the write.
That is precisely the response-time false positive the user identified.

New verdict: **UNRESOLVED / `ORACLE_FAIL_NO_CAUSAL_CONSUMER`**; 0 consumer
commits; oracle FAIL (`3f89eab79392ce4d` vs golden `3f89eab79392ce69`).
Trace: validator VALID, completeness COMPLETE (UNRESOLVED profile), chain PASS.
Edges: 5, `missing_type=0`.

## R05 evidence

Overlapping load requests (all `candidate=0`):

| load seq | request tick | store write tick | request before write? |
|---|---|---|---|
| 19960 (previous "consumer") | 13118105 | 17157910 | **yes** |
| 29123 | 10235225 | 17157910 | yes |

New verdict: **UNRESOLVED / `ORACLE_FAIL_NO_CAUSAL_CONSUMER`**; 0 consumers;
oracle FAIL (`b948f769e7d691f5` vs golden `3f89eab79392ce69`). Trace:
validator VALID, completeness COMPLETE (UNRESOLVED), chain PASS. Edges: 4,
`missing_type=0`.

## Honest consequence

The v3.2.4 claim that R04/R05 are SDC **does not survive request-time
causality**. The checksum still changes, but no traced load causally consumed
the faulted byte, so the failure is not attributable to the injected fault
through the observed chain. R04/R05 are therefore **UNRESOLVED**, not SDC.

Open question (recorded, not hidden): SE maps different virtual addresses to
the same memory location, and `mem_req` matching uses the Request VA. A later
reader through a different VA alias would not be matched. This does not
restore the retracted claim; it marks where a future PA-based matcher would
be needed.
