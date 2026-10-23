# R6 12-RunID Final Re-Judgement Table (authoritative)

- Lane: **L28** (capstone). Worktree `r6-final` @ branch `r6-final` (base `lsu-mdspec-20261019`).
- Checker used (authoritative, copied verbatim, **not hand-edited**):
  `tools/lsu_chain_check.py` from `origin/r6-gate`
  (git blob `48853de38882888d1ea15ba19671a8fe5ba22081`,
  sha256 `eba5d4a0b6120e32244e15c31b2c7f808bf43ee9d06c08ccb2120c0e2a5ea0cd`).
- Re-judge driver (copied verbatim, not hand-edited):
  `tools/lsu_r6_rejudge.py` from `origin/r6-rejudge`
  (git blob `7f1ee9d656fa0584c01cc52737b00ebfb307745f`).
- Command: `python3 tools/lsu_r6_rejudge.py --json ... --md ...`
  (roots = `/home/sdc/gem5-fi-ding/runs/lsu`).
- Stream lines are the real `PROP-EVT: kind=<k> key=value …` records; no synthetic rows.

> **Supersedes** the earlier `R6-12RUNID-TABLE.md`, which was produced against the OLD
> checker (`2191e98b`). That table is obsolete.

## Verdict summary

- Present streams: **7 / 12** (6 COMPLETE + 1 TRUNCATED). MISSING: **5 / 12**.
- `check_admission` admitted: **0 / 12**. Every present RunID is **FAIL**.
- Literal per-RunID verdicts are the `chain verdict` column below.

## The 12 rows

| RunID | stream/completeness | inj before/after | per-layer kinds L0..L5 | correlation keys | oracle | chain verdict | pass/fail |
|---|---|---|---|---|---|---|---|
| T02-F0-W4 | COMPLETE | n/a/n/a | L0:injx1/L1:tlb_lookupx1/L2:tlb_pfnx1,tlb_translate_resultx1/L3:cache_accessx32,cache_returnx32,lq_completex3,mshr_allocx18,mshr_mergex14,respx21,sq_completex1,sq_executex1,sq_writebackx1/L4:consumerx54,errant_commitx1,taint_regx3/L5:- | fault_id=1; parent_event_id=linear-contig; req_ids=['301', '301', '301', '391']; walk_ids=-; dyn_inst_seq=['301', '301', '301', '301', '391'] | Crash | NOT-ADMITTED [cross_request_edge, no_closed_chain_and_no_containment, ready_by_activated_only, ready_by_chain_end_only] terminal=provable_to_L4_then_unknown | FAIL |
| T02-F2-W4 | MISSING | — | — | — | — | MISSING | FAIL (MISSING) |
| T04-F0-W4 | COMPLETE | n/a/n/a | L0:injx1/L1:tlb_lookupx1/L2:tlb_pfnx1,tlb_translatex29,tlb_translate_resultx1/L3:cache_accessx27,cache_fillx8,cache_returnx27,lq_completex11,lsq_sendfragx29,mem_reqx29,mshr_allocx8,mshr_fillx8,mshr_freex8,mshr_mergex8,respx29,sq_completex1,sq_executex1,sq_writebackx1/L4:consumerx1296,errant_commitx1,taint_regx19/L5:- | fault_id=1; parent_event_id=linear-contig; req_ids=['301', '301', '301', '391']; walk_ids=-; dyn_inst_seq=['301', '301', '301', '301', '391'] | Crash | NOT-ADMITTED [cross_request_edge, no_closed_chain_and_no_containment, ready_by_activated_only, ready_by_chain_end_only] terminal=provable_to_L4_then_unknown | FAIL |
| T04-F2-W4 | COMPLETE | n/a/n/a | L0:injx1/L1:tlb_lookupx1/L2:tlb_pfnx1,tlb_translatex29,tlb_translate_resultx1/L3:cache_accessx27,cache_fillx8,cache_returnx27,lq_completex11,lsq_sendfragx29,mem_reqx29,mshr_allocx8,mshr_fillx8,mshr_freex8,mshr_mergex8,respx29,sq_completex1,sq_executex1,sq_writebackx1/L4:consumerx1296,errant_commitx1,taint_regx19/L5:- | fault_id=1; parent_event_id=linear-contig; req_ids=['301', '301', '301', '391']; walk_ids=-; dyn_inst_seq=['301', '301', '301', '301', '391'] | Crash | NOT-ADMITTED [cross_request_edge, no_closed_chain_and_no_containment, ready_by_activated_only, ready_by_chain_end_only] terminal=provable_to_L4_then_unknown | FAIL |
| T04-F6-W4 | COMPLETE | n/a/n/a | L0:injx1/L1:tlb_lookupx1/L2:tlb_pfnx1,tlb_translatex29,tlb_translate_resultx1/L3:cache_accessx27,cache_fillx8,cache_returnx27,lq_completex11,lsq_sendfragx29,mem_reqx29,mshr_allocx8,mshr_fillx8,mshr_freex8,mshr_mergex8,respx29,sq_completex1,sq_executex1,sq_writebackx1/L4:consumerx1296,errant_commitx1,taint_regx19/L5:- | fault_id=1; parent_event_id=linear-contig; req_ids=['301', '301', '301', '391']; walk_ids=-; dyn_inst_seq=['301', '301', '301', '301', '391'] | Crash | NOT-ADMITTED [cross_request_edge, no_closed_chain_and_no_containment, ready_by_activated_only, ready_by_chain_end_only] terminal=provable_to_L4_then_unknown | FAIL |
| T01-F0-W4 | COMPLETE | n/a/n/a | L0:injx1/L1:tlb_lookupx1/L2:tlb_pfnx1/L3:respx1,sq_completex1,sq_executex1,sq_writebackx1/L4:-/L5:tlb_translate_resultx1 | fault_id=1; parent_event_id=linear-contig; req_ids=['301', '301', '301']; walk_ids=-; dyn_inst_seq=['301', '301', '301', '301'] | Masked | NOT-ADMITTED [no_closed_chain_and_no_containment, ready_by_activated_only, ready_by_chain_end_only] terminal=detected_contained | FAIL |
| T01-F1-W4 | MISSING | — | — | — | — | MISSING | FAIL (MISSING) |
| T01-F2-W4 | MISSING | — | — | — | — | MISSING | FAIL (MISSING) |
| T03-F5-W4 | TRUNCATED | 81d75/81d75 | L0:injx1/L1:tlb_lookupx1/L2:tlb_pfnx1/L3:respx1,sq_completex1,sq_executex1,sq_writebackx1/L4:-/L5:tlb_translate_resultx1 | fault_id=1; parent_event_id=linear-contig; req_ids=['301', '301', '301']; walk_ids=-; dyn_inst_seq=['301', '301', '301', '301'] | None | NOT-ADMITTED [no_closed_chain_and_no_containment, ready_by_activated_only] terminal=detected_contained | FAIL |
| T10-F0-W4 | COMPLETE | n/a/n/a | L0:injx1/L1:tlb_lookupx1/L2:tlb_pfnx1/L3:respx1,sq_completex1,sq_executex1,sq_writebackx1/L4:-/L5:tlb_translate_resultx1 | fault_id=1; parent_event_id=linear-contig; req_ids=['301', '301', '301']; walk_ids=-; dyn_inst_seq=['301', '301', '301', '301'] | Masked | NOT-ADMITTED [no_closed_chain_and_no_containment, ready_by_activated_only, ready_by_chain_end_only] terminal=detected_contained | FAIL |
| T10-F1-W4 | MISSING | — | — | — | — | MISSING | FAIL (MISSING) |
| T10-F2-W4 | MISSING | — | — | — | — | MISSING | FAIL (MISSING) |

## Column notes (honesty)

- **injection before/after**: the L0 `inj` event's `before`/`after` fields are **blank on every
  stream** (recorded `n/a`) — an honest emitter gap surfaced by this table (the re-judge
  `forbidden` probe `l0_inj_before_after_empty` fires for T02-F0/T04-*/T01-F0/T10-F0). The
  injector ground truth is carried by the L1 witness (`tlb_lookup.post_lookup`) and the
  sibling `armtlb_injections.log`, e.g. `old_pfn: 0x81d75 -> new_pfn: 0x0` (T04-*),
  `-> 0x100000000081d75` (T01-F0/T10-F0), `last valid pfn -> 0x100040000081d75` (T02-F0),
  `stuck: 0x81d75 -> 0x81d75` (T03-F5).
- **per-layer kinds L0..L5**: `-` = no witness at that layer.
- **correlation keys**: `parent_event_id` is degenerate-linear on every stream
  (`parent = event_id-1`), so the DAG carries no semantic edge. `req_ids`/`dyn_inst_seq`
  break **L2->L4** (301 -> 391) on T02-F0 / T04-F0 / T04-F2 / T04-F6 — the checker's
  `cross_request_edge` fires.
- **oracle**: read from the sibling `chain_report.json` (runner's own classification), not re-derived.
- **chain verdict**: literal `check_admission` result. Tokens:
  `cross_request_edge`, `no_closed_chain_and_no_containment`, `ready_by_activated_only`,
  `ready_by_chain_end_only`. Terminal strings are the checker's own.

## Containment (task 4) — direct measurement

`check_admission` (as called by `lsu_r6_rejudge.py`) omits the containment bundle. Passing
`containment_from_events()` explicitly changes nothing for these 12 (all still NOT admitted),
but it **does** admit the T08 pilot when evaluated directly:

| stream | containment_from_events | admitted |
|---|---|---|
| `runs/lsu/r6_tlb_C_T08-F0-W4/T08-F0-W4/seed1` (TRUNCATED gz) | YES (layer L2, `tlb_translate_result` field `walk_refill_lost`, outcome `translation_blocked`) | **True** |
| `runs/lsu/r6_tlb_pilot2/T05-F0-W4/seed1` (COMPLETE) | None | False |
| T01-F0 / T10-F0 (COMPLETE) | None | False |

### Why T05 is rejected while T08 admits (observed checker behaviour)

Both carry an identical-shaped containment marker (`tlb_translate_result`, `contained=1`,
`detection_layer=L2`, `outcome=NoFault`/`translation_blocked`). Difference:
`containment_from_events` rejects a claim when any **deeper** observation-layer witness exists
after the contained event. T05/T01/T10 still hold their trailing lifecycle `chain_end`, whose
`_obs_layer_of` maps to **L5**, so `deeper(L5) > L2` -> claim refused. Dropping `chain_end`
from T05's event list makes `containment_from_events` return a valid bundle (verified);
T10 still refuses (it has real L3 `sq_execute/sq_writeback/resp/sq_complete` witnesses after L2,
so the fault genuinely did not stop at L2). T08 has no post-L2 witness at all -> admitted.
This is a checker semantics observation, reported as fact; no tool was edited.

## Registry / contract run (task 4)

Registry built with `tools/lsu_r6_register_evidence.py` (L17-v2 scanner) into the worktree
(`docs/gem5-fi/lsu/mdspec/pilot_evidence_r6final.json`), scanning
`/home/sdc/gem5-fi-ding/runs/lsu` with `--evidence-root /home/sdc/gem5-fi-ding`:
`pilots=94 runids=82 unmatched=6 duplicated_keys=6 truncated=19 kinds=44`.
It newly registers `T08-F0-W4` (truncated) and `T05-F0-W4` (complete) plus the complete
T-series streams. Contract run:

```
LSU_CHAIN_EVIDENCE_ROOT=/home/sdc/gem5-fi-ding python3 tools/lsu_ready_contract.py --out ...
```

Real `chain_gate` block:

```json
{
 "rule": "READY requires lsu_chain_check.check_admission admission on this RunID's pilot PROP-EVT (complete family-specific L0→L5 chain, or explicit containment with later layers N/A(contained))",
 "evidence_root": "/home/sdc/gem5-fi-ding",
 "event_cap": 4000,
 "admitted": 0,
 "unproven": 45,
 "evidence_missing": 196
}
```

### Honest reading of the contract

- `admitted` stays **0**. Registering T08/T05 evidence **cannot** change it: the chain gate is
  only evaluated for rows whose status is READY/PARTIAL, and the contract is
  `READY=0 / PARTIAL=0 / BLOCKED=325`. All 24 T-series rows are blocked upstream as
  **FS-INFRA** (FS pipeline not landed), so `chain` is `null` for them and the containment
  path is never reached. The registry's only movement was
  `L01-F0-W5: CHAIN-EVIDENCE-MISSING -> CHAIN-UNPROVEN` (still not admitted).
- **No RunID is newly admitted.** The containment machinery works (T08 admits in a direct
  call) but is unreachable through the contract while the FS-INFRA block stands.

## Remaining gaps

1. **5 RunIDs MISSING** (no stream anywhere): `T02-F2-W4`, `T01-F1-W4`, `T01-F2-W4`,
   `T10-F1-W4`, `T10-F2-W4`.
2. **1 RunID TRUNCATED**: `T03-F5-W4` (gzip EOF; `stats.txt` empty).
3. **L0 `inj` carries no before/after** on every stream (emitter gap).
4. **Cross-request splice** (req 301 -> 391) breaks the L2->L4 edge on the four enhanced
   T04/T02 streams.
5. **No family-specific L0->L5 full chain** exists on any of the 12; containment is the only
   alternative path and it is (a) unreachable via the contract (FS-INFRA) and (b) refused for
   T01/T05/T10 because a deeper witness (or the L5-mapped `chain_end`) follows the marker.
