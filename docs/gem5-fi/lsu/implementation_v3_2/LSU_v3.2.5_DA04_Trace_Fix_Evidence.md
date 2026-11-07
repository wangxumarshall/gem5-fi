# DA04 trace fixes — v3.2.5 rerun evidence (R04/R05)

**Date:** 2026-11-08
**Binary (final rerun):** `build/ARM/gem5.opt` sha256
`6808c56e22b44eab3e189a1c51e6b90ec1c95e0c66d0c0835d205575572d7645`
**Scope:** only R04/R05 were rerun. The v3.2.4 directories were **not**
overwritten; reruns live in `pilots_v3_2_5/`.

## What changed

1. **Load memory-request events + real request time.** `noteMemRequest` emits
   a `mem_req` node for every load send overlapping a registered faulted byte,
   with `request_tick` (first send), `last_send_tick` (the send whose response
   is being observed), `store_write_tick`, `candidate`, `store_not_written_yet`
   and the LQ/SQ ids. The node timestamp is `last_send_tick`.
2. **Causality anchored at the last send.** A re-sent Request discards its
   earlier attempt; the fetching attempt is the most recent send, not the
   first. The v3.2.5 review caught that the first-send anchor alone was
   insufficient; both are now recorded and the decision uses the last send.
3. **Lossless edges.** Every synthesized ptag-order edge carries
   `edge_type=ptag_sequence` and source/destination hashes when present;
   C++ `prop_edge` rows default `edge_type` to `data`.

## R04 evidence

Command: `run_pilot.py --model DA04 --context-index 4 --preserve-sample-id
--pilot-id DA04-R04 --event-ordinal 50`.

Overlapping load sends:

| load seq | first send | last send | store write | candidate |
|---|---|---|---|---|
| 19210 (previous "consumer") | 2286900 | **17889025** | 17042410 | **1** |
| 24465 | 16934225 | 18710230 | 17042410 | 1 |
| 25523 | 10235610 | 18977420 | 17042410 | 0 (overwritten) |

The first send precedes the write by 14.7M ticks, but the **last send is
788k ticks after the write** — the earlier request was re-sent, and the
fetch that produced the response at 17,889,795 is post-write. The load is a
causal consumer.

Verdict: **SDC / ORACLE_FAIL**; **1,009** consumer commits; oracle
`3f89eab79392ce4d` vs golden `3f89eab79392ce69`. Trace: validator VALID,
completeness COMPLETE, chain PASS, every edge typed.

## R05 evidence

| load seq | first send | last send | store write | candidate |
|---|---|---|---|---|
| 19960 (previous "consumer") | 13118105 | **18004525** | 17157910 | **1** |
| 29123 | 10235225 | 19901420 | 17157910 | 1 |

Verdict: **SDC / ORACLE_FAIL**; **7,714** consumer commits; oracle
`b948f769e7d691f5` vs golden `3f89eab79392ce69`. Trace: validator VALID,
completeness COMPLETE, chain PASS.

## Correction of the intermediate v3.2.5 claim

An intermediate commit used the *first* send tick and concluded R04/R05 were
UNRESOLVED. That conclusion was wrong: re-sends exist, and the fetching send
is the last one. The evidence above supersedes it. The v3.2.4 R04/R05 SDC
verdicts stand, now with request-time evidence rather than response-time
association and with the correct R04 consumer count (1,009, not 9,064).

Open question (unchanged): SE maps different virtual addresses to the same
memory location; `mem_req` matching uses the Request VA. A later reader
through a different VA alias would not be matched. This is not needed for
R04/R05 (the matched sends are sufficient), but it is a real boundary.
