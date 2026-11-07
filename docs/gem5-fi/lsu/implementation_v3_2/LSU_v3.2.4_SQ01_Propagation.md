# SQ01 — v3.2.4 propagation evidence (re-run)

**Date:** 2026-11-07
**Model:** SQ01 (store data byte0 bit3 flip, F0), workload `sq_drain`
**New pilots:** `pilots_v3_2_4/SQ01-R01..R05` (historical `pilots_v3_2_3/SQ01-*` untouched)

## What was added

v3.2.3 recorded only `injection -> sq_lifecycle`; that is not a real
propagation edge to the memory. v3.2.4 adds:

- a ptag chain for the SQ01 injection (`inj_store_data` now allocates a ptag
  and registers the faulted store);
- the real SQ drain node (`store_writeback`, with the SQ entry id/generation
  and the store data hash);
- the actual cache block update (`store_mem_write`, before/after bytes and
  the byte-enable mask);
- later-load matching by request VA (if a load reads the corrupted byte it
  joins the same chain with `memory_response`/`register_writeback`/consumers).

## Results (all five pilots, real output)

| Pilot | dyn seq | SQ idx/gen | injection | store_writeback | store_mem_write | later Load/Consumer | Terminal |
|---|---|---|---|---|---|---|---|
| SQ01-R01 | 18 | 1/1 | `0x0 -> 0x8` | `be=0xff`, data `0800000000000000` | before `0000000000000000` -> after `0800000000000000` | none | MASKED |
| SQ01-R02 | 19 | 2/2 | `0xf0 -> 0xf8` | `be=0xff`, data `f805400000000000` | before `0000...` -> after `f805400000000000` | none | MASKED |
| SQ01-R03 | 23 | 3/3 | `0x0 -> 0x8` | `be=0xff`, data `0800000000000000` | before `0000...` -> after `0800...` | none | MASKED |
| SQ01-R04 | 24 | 4/4 | `0x0 -> 0x8` | `be=0xff`, data `0800000000000000` | before `0000...` -> after `0800...` | none | MASKED |
| SQ01-R05 | 28 | 5/5 | `0x0 -> 0x8` | `be=0xff`, data `0800000000000000` | before `0000...` -> after `0800...` | none | MASKED |

All five: `accepted=true`; `propagation_coverage=COMPLETE` for the SQ01
MASKED profile `injection -> store_writeback -> store_mem_write`;
`chain_integrity=PASS`; oracle PASS; terminal reason
`STORE_COMMITTED_LANE_NOT_READ`.

Honest reading: the corrupted store data **is** written to the cache block
(the `store_mem_write` before/after bytes differ at the faulted byte), so the
v3.2.3 "no real propagation" complaint is fixed for the store→memory edge.
No later load in `sq_drain` reads that byte before it is overwritten, so the
chain stops at the store and **SQ01 is not marked PROPAGATION_VERIFIED**.
That requires a workload/context whose load consumes the corrupted byte;
the model remains PILOT_RUN.

## Gates

- Historical v3.2.3 pilots are preserved (different directory, different
  pilot ids `SQ01-R0N-v324`).
- Traces are 189 MB each (> the 100 MB Git limit): kept on disk and in the
  delivery package, with sha256 sidecars (`trace_v31.jsonl.sha256`).
