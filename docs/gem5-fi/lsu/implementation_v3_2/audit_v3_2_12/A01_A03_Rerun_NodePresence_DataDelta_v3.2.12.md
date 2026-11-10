# A01/A03 rerun node presence and DataDelta — LSU v3.2.12 (final-candidate binary)

**Date:** 2026-11-11
**Binary:** `build/ARM/gem5.opt`, SHA256
`68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8`
(verified with `sha256sum` before the runs; this is the first vintage carrying the
`a01_ea` / `a01_fault` / `a01_consumed` / `a01_ea_discarded` / `a01_golden_req` /
`a01_golden_resp` / `a03_activation` / `a03_stream` sink emitters).
**Runs:** 14 new pilots under `pilots_v3_2_12/` — `SUPP-A01-R01C..R05C`,
`SUPP-A01-C01C/C02C`, `SUPP-A03-R01C..R05C`, `SUPP-A03-C01C/C05C` — run with
`docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`, one gem5 at a time.
The old-binary (`720eb780…`) `SUPP-A01-*` / `SUPP-A03-*` runs are untouched; this
round's records live only in the `*C` dirs, the `_v3` verdict JSONs and the rerun
records CSV. Seeds/ordinals/workload are the frozen Excel rows (seed preserved by
omitting `--seed`; no override flag in any manifest).

---

## 1. Node presence (trace-side, `trace_v31.jsonl` event counts)

| Pilot | a01_ea | a01_fault | a01_consumed | a01_ea_discarded | a01_golden_req | a01_golden_resp | a03_activation | a03_stream |
|---|---|---|---|---|---|---|---|---|
| SUPP-A01-R01C | 1 | 0 | 1 | 0 | 0 | 0 | n/a | n/a |
| SUPP-A01-R02C | 1 | 0 | 1 | 0 | 0 | 0 | n/a | n/a |
| SUPP-A01-R03C | 1 | 0 | 0 | **1** | 0 | **1** | n/a | n/a |
| SUPP-A01-R04C | 1 | 0 | 1 | 0 | 0 | 0 | n/a | n/a |
| SUPP-A01-R05C | 1 | 0 | 1 | 0 | 0 | 0 | n/a | n/a |
| SUPP-A01-C01C | 0 | 0 | 0 | 0 | 0 | 0 | n/a | n/a |
| SUPP-A01-C02C | 0 | 0 | 0 | 0 | 0 | 0 | n/a | n/a |
| SUPP-A03-R01C | n/a | n/a | n/a | n/a | n/a | n/a | **1** | **141** (ord 1–141) |
| SUPP-A03-R02C | n/a | n/a | n/a | n/a | n/a | n/a | **1** | **140** (ord 2–141) |
| SUPP-A03-R03C | n/a | n/a | n/a | n/a | n/a | n/a | **1** | **139** (ord 3–141) |
| SUPP-A03-R04C | n/a | n/a | n/a | n/a | n/a | n/a | **1** | **138** (ord 4–141) |
| SUPP-A03-R05C | n/a | n/a | n/a | n/a | n/a | n/a | **1** | **137** (ord 5–141) |
| SUPP-A03-C01C | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 |
| SUPP-A03-C05C | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 |

**Required-set verdict: no MISSING_TRACE_NODE.** Every A01 fault run carries
`a01_ea`; the R03-class replay-discard context carries `a01_ea_discarded`
(`applied_to_request=0;discard_reason=saved_request_reuse`) plus the in-run
golden-EA reference `a01_golden_resp`; every A03 fault run carries
`a03_activation` (exactly one: `tick;bit;mode`) and 137–141 `a03_stream` rows.
Controls correctly stage nothing (zero injections, `control_misfire=false`).

Honest absences (recorded, not inferred):

1. **`a01_fault` = 0 in every run (incl. the A01 crash context).** The crash of
   R01C is a simulator panic (`GenericPageTableFault::invoke` → `panic: Page table
   fault when accessing virtual address 0`), which never returns a `Fault`
   through the `LSQ::pushRequest` fault landing site, so `noteA01FaultVA` never
   fired and `a01_ea.fault_va` honestly stays `NOT_APPLICABLE`. The panic VA
   survives run-side only (`simulator_abort` node detail +
   `terminal_evidence`). This is an explanation of an inapplicable condition,
   not a MISSING_TRACE_NODE against the required set.
2. **`a01_golden_req` = 0 everywhere.** In the R03C discard shape the reused
   savedRequest (golden vaddr) was *sent* in execution attempt 1 (tick 197890)
   before the A01 chain was registered (injection at tick 204820), so
   `noteMemRequest` had no registry entry to match; the golden *response*
   (tick 205590) arrived after registration and is recorded.
3. **A03 stream `pc=0`** is `kPcUnknown` (the PRE hook does not observe the PC);
   never fabricated — the A03 injection detail records no PC field at all.

## 2. DataDelta (fault response at actual EA vs reference at golden EA, same dyn_inst_seq)

Matched controls record **zero memory nodes** (chain-scoped tracer; controls
register nothing — C01C/C02C and A03-C01C/C05C contain only
`lq_lifecycle`/`sq_lifecycle`/`forwarding_decision`), so the control-side
reference of the plan §4 Step 2 remains structurally unobservable. The new
on-chain reference (`a01_golden_resp`, `reference_only=1`) fills exactly one
dyn-seq pair. Nothing below is fabricated from cross-run adjacency; every R/F
value is an on-chain node.

| Context (dyn_seq) | F — fault run resp @ actual EA | R — reference @ golden EA | DataDelta = popcount(R XOR F) | R provenance (honest) |
|---|---|---|---|---|
| A01-R01C (seq 5) | `02fffeff7f000000` @ `7ffffefd98` | not observed | **NOT_OBSERVABLE** | crash context; no in-run golden request; control C01C records no memory nodes; no run read `7ffffefd90` at seq 5 |
| A01-R02C (seq 48) | `0000000000000000` @ `7ffffefda0` | `0000000000000000` @ `7ffffefda8` | **0 bits** | `a01_golden_resp` of SUPP-A01-R03C — same dyn_inst_seq 48, same workload; the identity join is dyn-seq (standard §2), *not* a matched control; cross-context, labeled as such |
| A01-R03C (seq 48) | no response at actual EA — `a01_ea_discarded` proves the corrupted EA never reached a Request | `0000000000000000` @ `7ffffefda8` (in-run `a01_golden_resp`, attempt 2, request_id 14) | **NOT_OBSERVABLE (no F)** | the discard is now an on-chain fact, not a silent absence |
| A01-R04C (seq 245) | `fbf7d0cc00000000` @ `7ffffefdb8` | not observed | **NOT_OBSERVABLE** | no same-dyn-seq golden-EA read exists in any run (A03 runs also corrupt `7ffffefdb0`→`7ffffefda8`) |
| A01-R05C (seq 253) | `1000000000000000` @ `7ffffefdb0` | not observed | **NOT_OBSERVABLE** | same — golden `7ffffefdb8` never read at seq 253 in any run |
| A03-R0xC crash chain (seq 1014) | no response (access faulted → panic) | n/a | **NOT_OBSERVABLE** | crash chain |
| A03-R02C stream load seq 48 | `0000000000000000` @ `7ffffefda0` | `0000000000000000` @ `7ffffefda8` (A01-R03C `a01_golden_resp`, same dyn seq) | **0 bits** (observation) | cross-model reference; recorded as observation, not verdict evidence |

The one computable DataDelta is **0** — at seq 48 the golden-EA bytes equal the
actual-EA bytes (`0000000000000000` both). Recorded honestly as MASKED-consistent;
no fishing for delta. The plan's acceptance leg "≥2 contexts with non-zero
DataDelta AND a consumer edge" is **not met on the DataDelta leg** (1 context
computable, delta 0); the consumer-edge leg **is** met in 4/5 A01 contexts (below).

## 3. Consumer-edge evidence (verified writeback→consumer hash equality)

| Pilot | writeback fnv (V) | a01_consumed input_hash | consumer seq | match |
|---|---|---|---|---|
| SUPP-A01-R01C | `f971edcd05e4ccc2` | `f971edcd05e4ccc2` | 25 | yes (== response data_fnv) |
| SUPP-A01-R02C | `a8c7f832281a39c5` | `a8c7f832281a39c5` | 50 | yes |
| SUPP-A01-R04C | `1505defdf2164c5b` | `1505defdf2164c5b` | 250 | yes |
| SUPP-A01-R05C | `987468c2d70edbd5` | `987468c2d70edbd5` | 254 | yes |
| SUPP-A01-R03C | n/a (no writeback on chain) | none | none | — (discard) |

R01C additionally carries the full on-chain value-propagation chain after the
consumer: 12 `consumer_commit` edges on ptag 1, all `consumer_input_matches_source=1`:
`0x7ffffeff02` → (seq 25, 32-bit truncation) `0xfffeff02` → (seq 31) `0x7ffff6f5a8`
→ (seq 46) `0x7ffff6f5b0` → (seq 47, load through corrupted base) `0x0`.

## 4. Crash attribution (task rule: fault VA == actual EA ⇒ DIRECT_ADDRESS_MATCH; consumer-derived ⇒ CONSUMER_DERIVED; else TEMPORAL_ASSOCIATION_ONLY)

| Pilot | panic fault VA | actual EA (on-chain) | attribution |
|---|---|---|---|
| SUPP-A01-R01C | `0` | `7ffffefd98` (a01_ea) | **TEMPORAL_ASSOCIATION_ONLY** — no direct match; the on-chain consumer chain reaches 0-valued registers (above), but the *faulting instruction* is not identity-linked on the chain (the abort node carries no dyn_inst_seq; no consumer record names it), so CONSUMER_DERIVED is not claimable under the frozen rule. Context (not verdict): matched control C01C (same seed) completes cleanly, oracle PASS — the crash is injection-dependent at the run level. |
| SUPP-A03-R01C..R05C | `0xffffffffffb73c50` | `0xffffffffffb73c50` (a03_stream, seq 1014, golden `0xffffffffffb73c58`) | **DIRECT_ADDRESS_MATCH 5/5** — first vintage where the golden/actual pair of the crashing load is an on-chain node (`a03_stream`), not a log-side line. |

## 5. Verdict classes (deterministic closure-tool output, `*_v3.json`)

Eight-field tables: `A01_verdict_v3.2.12_v3.json` / `A03_verdict_v3.2.12_v3.json`
(7 records each, keyed to binary SHA `68c6ce73…`). The grades are **identical,
field-for-field, to the old-binary records** for all 14 runs — the new binary
changed the evidence layer (the nodes above), not the frozen grading:

- **A01:** R02C/R04C/R05C `LIFECYCLE_ONLY` (full structural chain, verified
  consumer edge, oracle PASS, no provable value divergence — DataDelta 0/NOT_OBSERVABLE);
  R01C `UNRESOLVED` (CRASH, TRUNCATED record, off-chain abort); R03C `UNRESOLVED`
  (discard — now explained on-chain, still honestly no writeback/consumer);
  controls `UNRESOLVED`/`NO_INJECTION`. **Model level: zero complete chains → no
  COMPLETE_CAUSAL_CHAIN; ≥2 verified-writeback+consumer contexts exist (R02C/R04C/R05C)
  but none carries a non-zero DataDelta, so no upgrade beyond LIFECYCLE_ONLY.**
- **A03:** all five fault runs `UNRESOLVED` (CRASH, address-matched 5/5, but
  TRUNCATED records + off-chain `simulator_abort` cap causality at UNPROVEN under
  the frozen rules); controls `UNRESOLVED`/`NO_INJECTION`. **Model level: zero
  complete chains; the stream evidence (activation positions 1–5, ALREADY_STUCK
  masking population 66–68 per run) is now on-chain and verdict-eligible, but the
  crash-cut record grading remains the open standard-revision item.**

Per the fixed honest-class rule: no COMPLETE (needs ≥2 distinct contexts with
verified writeback+consumer *and* the divergent-value evidence; the only
computable DataDelta is 0), no VERIFIED_SINGLE_CONTEXT upgrade, no inference.
