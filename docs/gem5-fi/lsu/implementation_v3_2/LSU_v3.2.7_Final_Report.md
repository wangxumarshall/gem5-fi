# LSU v3.2.7 — final report

**Branch:** `lsu-platform-v3.2.7` (from `5d664473`, v3.2.6 tip)
**Final binary:** `8377c011bb5916be67fa1132232440ae7f8be02351c3034624a339319a545bec`
**No 60-sample formal run was started.**

## Question 1 — Is the MD04 definition frozen?

Yes. `MD04_Definition_Freeze_v3.2.7.md` (`MD04-DEF-v2`) fixes the hook at
the store branch of `LSQUnit::checkViolations`, immediately before the
`M5PanicFault` return (`lsq_unit.cc:676-679`), with MD04-ELIG-v1:
8-byte store, younger load size ≥ 8, real byte overlap AND the same
shifted-range predicate as `checkViolations`; 16-byte LDP covering the
store included; 4-byte and disjoint addresses excluded. One selected
eligible pair per sample; no fall-through when the ordinal is absent.

## Question 2 — Are Excel and the C++ hook consistent?

For MD04, yes. Excel v3.2.2
(`excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.2.xlsx`) changes only
the five MD04 sample rows plus the MD04 row of the model/hook sheets; all
identity columns and the other 11 models are cell-identical (test
`tests/test_lsu_v322_workbook.py`, 4 passed). The new `TargetField` is
`M5PanicFault return path`; the superseded `possibleLoadViolation` is
documented in `excel/MD04_OLD_NEW_DIFF_v3.2.2.md`.

**Caveat:** the hook was never `possibleLoadViolation` in the v3.2.6 code;
the old Excel wording was the inconsistency. The C++ eligibility predicate
is now the same predicate as `checkViolations`, not an address string
comparison.

## Question 3 — Do R01–R05 all conform to the new definition?

- R01–R04: **CONFORMING**. Their target pairs keep ordinals 1–4 under the
  frozen rule; the new runs carry the full TargetPairID identity.
- R05: **HISTORICAL_NONCONFORMING (ordinal drift)**. The historical target
  71660/71652 is now eligible ordinal 6 because the frozen real-overlap
  rule adds 69297/69294 at ordinal 5. The historical trace is retained; the
  frozen R05 run uses ordinal 5 and terminates SQUASHED (the historical
  R05 was MASKED with 2 consumers; that result does not carry over).
- All five historical injections themselves satisfy the eligibility rule;
  the old traces lack TargetPairID/store size/request id, and R03's old
  chain is `CROSS_ATTEMPT_UNVERIFIED`.

## Question 4 — Does R03 have a real replay or attempt association problem?

**No replay.** `execution_attempt_id` is a CHAOS counter incremented at
the top of `executeLoad`/`executeStore` (`lsq_unit.cc:700/772`), not a
gem5 replay field. At tick 17816260 the load is issued with the D-cache
blocked (request not sent); MD04 injects; at 17822035 the same DynInst and
the same request 67 are executed again and the response arrives at
17822805. No squash, `replay_generation=0`, same seq, LQ entry 748,
generation 1235.

- Historical trace: `CROSS_ATTEMPT_UNVERIFIED` because the old injection
  did not carry `load_request_id` → coverage PARTIAL (downgraded from the
  v3.2.6 claim).
- Frozen rerun: injection request 67, LQ 748, generation 1235; response
  matches all four → `CROSS_ATTEMPT_VERIFIED`, chain PASS, coverage
  COMPLETE.

## Question 5 — Is MD04's full propagation chain verified?

Chain-level, yes, with explicit limits:

| Pilot | terminal | consumers | link |
|---|---|---|---|
| R01 | SQUASHED | 0 | SAME_ATTEMPT |
| R02 | MASKED | 6 | SAME_ATTEMPT |
| R03 | MASKED | 259 | CROSS_ATTEMPT_VERIFIED |
| R04 | SQUASHED | 0 | SAME_ATTEMPT |
| R05 | SQUASHED | 0 | SAME_ATTEMPT |

All five: one injection, oracle PASS, validator VALID, trace COMPLETE,
chain PASS. **No MD04 SDC pilot exists.** R01/R04/R05 are squashed; only
R02/R03 reach the register/consumer chain.

## Question 6 — Is FW05 implemented with five pilots?

Yes, with one workload caveat.

- `CHAOSLSQFwd::maybeSubstituteFW05`, mode `fw05_older_src`, strict
  eligibility (distinct older store, full cover, different bytes, younger
  load), trace `inj_fw05`, writeback from the PRF.
- R01 SQUASHED; R02–R05 SDC with 2001/2000/1999/1998 matched consumer
  instructions. For R02 the injection `alt_data_fnv` =
  `register_writeback` `writeback_value_fnv` = `a06ea71be9c5aa88`; the
  checksum differs from the golden (`0x549c9e0347adaf23` vs
  `0x67afad307642983e`). All five accepted.
- **Gap:** the frozen W8 `alignment` workload cannot produce an eligible
  event (probe `alt=no`; a 4-byte-store workload has no full-cover older
  store). The pilots use a pilot-only directed workload
  `workloads/fw05_forward`; each manifest records
  `path_source=pilot_override (Excel path retained in sample)`. The Excel
  WorkloadPath/Oracle were not changed. This needs a researcher decision
  before the 60-sample formal run.

## SQ03

Started, not finished: definition frozen (`SQ03_Definition_Freeze_v3.2.7.md`),
`chaos_sq03` rules + unit test PASS, `sq03_canwb` mode and the one-shot
`executeStore` hook with paired `storesToWB` increment. Smoke on
`sq_drain`: one injection at store seq 18, exit 0, checksum equals the
no-fault baseline (MASKED at that event). Trace/runner/pilots/watchdog
are still pending; `max_faults=0` is unsafe in this mode (hangs).

## Verification

- Build `scons -j126 build/ARM/gem5.opt`: exit 0, no new warnings.
- Unit tests: MD04, FW05, SQ03 all PASS.
- Platform suite: 78 passed. Workbook test: 4 passed.
- MD04 and FW05 pilot sets were rerun on the final binary; all accepted.

## Open issues

1. FW05's Excel workload (W8 alignment) cannot trigger; pilot-only
   override must be resolved before the formal run.
2. MD04 R05 historical ordinal drift; historical R03 chain unverified.
3. SQ03 trace/runner/pilots/watchdog incomplete; unbounded mode hangs.
4. Warm-up/ROI remain researcher decisions.
5. No 60-sample formal experiment has been run.
