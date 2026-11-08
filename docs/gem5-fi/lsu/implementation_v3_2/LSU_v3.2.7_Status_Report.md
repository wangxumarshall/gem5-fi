# LSU v3.2.7 — MD04 freeze + FW05 implementation status

**Branch:** `lsu-platform-v3.2.7` (from `5d664473`, v3.2.6 tip)
**Scope:** MD04 definition freeze, Excel v3.2.2, five-pilot audit and
frozen reruns, R03 attempt investigation, FW05 implementation, SQ03 start.
No 60-sample formal run.

## 1. MD04 definition (frozen)

`MD04_Definition_Freeze_v3.2.7.md` (`MD04-DEF-v2`). Hook is the
`M5PanicFault` return in the store branch of `LSQUnit::checkViolations`
(`lsq_unit.cc:676-679` in this tree); `possibleLoadViolation` is the
superseded load/load flag. Eligibility (`MD04-ELIG-v1`): 8-byte store,
younger load, `load_size>=8`, real byte overlap AND the same shifted-range
predicate as `checkViolations`; 16-byte LDP covering the store included,
4-byte and disjoint addresses excluded. One selected pair per sample; no
fall-through when the target ordinal is absent (`NOT_TRIGGERED`).

## 2. Code and trace

- `md04_rules.hh`: `isEligibleViolationPair(...)` with the real predicate;
  unit test `tests/test_md04_rules.cc` PASS.
- `CHAOSMD04`: `dep_check_shift` + `RequestPtr` threading; exit status
  `CHAOS_MD04_TARGET_STATUS`.
- Trace: `TargetPairID`, store/load seq/addr/size/PC, SQ/LQ entry and
  generation, violation tick, `eligible_violation_pair_ordinal`,
  `event_ordinal`, seed, `load_request_id`, modification flags.
- Validator: cross-attempt linkage requires (seq, LQ entry, generation,
  request id); otherwise `CROSS_ATTEMPT_UNVERIFIED` and coverage PARTIAL.

## 3. Five frozen pilots

| Pilot | Pair | ordinal | oracle | terminal | coverage | chain |
|---|---|---:|---|---|---|---|
| R01 | 518/514 | 1 | PASS | SQUASHED | COMPLETE | PASS |
| R02 | 2251/2239 | 2 | PASS | MASKED (6 consumers) | COMPLETE | PASS |
| R03 | 17443/17442 | 3 | PASS | MASKED (259 consumers) | COMPLETE | PASS |
| R04 | 69297/69292 | 4 | PASS | SQUASHED | COMPLETE | PASS |
| R05 | 69297/69294 | 5 | PASS | SQUASHED | COMPLETE | PASS |

R01–R04 are injection- and configuration-conforming. R05's historical
target (71660/71652) is now eligible ordinal 6, so the historical R05 is
`HISTORICAL_NONCONFORMING (ordinal drift)`; the frozen R05 uses ordinal 5.
The frozen eligible stream is in
`evidence_v3_2_7/MD04_eligible_stream_v327.csv`.

## 4. R03 attempt answer

`execution_attempt_id` is a CHAOS counter incremented at every
`executeLoad`/`executeStore` entry (`lsq_unit.cc:700/772`), not a gem5
replay field. R03's load was issued at tick 17816260 with the D-cache
blocked (request not sent), then re-executed at 17822035 and sent the same
request 67. No squash, no replay (`replay_generation=0`), same seq, LQ
entry 748, generation 1235. Historical trace: `CROSS_ATTEMPT_UNVERIFIED`
(no request id at injection) → PARTIAL; frozen rerun:
`CROSS_ATTEMPT_VERIFIED` → COMPLETE.

## 5. Excel v3.2.2

`excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.2.xlsx` and
`excel/60_SAMPLE_MATRIX.csv`. Only MD04 rows change (sample sheet + the
MD04 row of sheets 3/4); identity columns and all other models are
cell-identical. Old/new difference: `excel/MD04_OLD_NEW_DIFF_v3.2.2.md`.

## 6. Matrix correction

FW05's `SOURCE_AUDITED` is corrected from 0 to 1 (the v3.2.6 audit report
exists; the matrix was stale). It is **not** marked IMPLEMENTED until the
code and pilots in this branch exist.

## 7. FW05 implementation and five pilots

`FW05_Definition_Freeze_v3.2.7.md` (`FW05-DEF-v1`, option A) and
`FW05_Implementation_v3.2.7.md`. Hook: `CHAOSLSQFwd::maybeSubstituteFW05`
at the full-coverage forwarding decision; strict eligibility (distinct,
older alternative store; full coverage; different bytes; younger load).
Trace: `inj_fw05` with TargetPairID and true/alt identity; the forwarded
load's writeback is emitted from `LSQUnit::writeback()` and its PRF hash
equals `alt_data_fnv`.

Pilots: R01 SQUASHED, R02–R05 SDC with 2001/2000/1999/1998 matched
consumer instructions; oracle FAIL is the SDC outcome, not a tool failure.
All five: one injection, target proof true, validator VALID, trace
COMPLETE, chain PASS, accepted.

**Workload gap:** the frozen W8 `alignment` workload has no eligible
alt-source event (`alt=no` probe). The pilots use a pilot-only directed
workload `workloads/fw05_forward` (override recorded in each manifest);
the Excel WorkloadPath/Oracle are unchanged. This must be resolved before
the 60-sample formal run.

## 8. SQ03 start

`SQ03_Definition_Freeze_v3.2.7.md`. Implemented: `chaos_sq03` rules +
unit test PASS; `sq03_canwb` mode; `executeStore` one-shot premature
`_canWB` with paired `storesToWB` increment. Smoke: one injection at
store seq 18 on `sq_drain`, exit 0, checksum equals the no-fault baseline
(MASKED at this event). Not yet done: trace event/edges, runner wiring,
watchdog, five pilots, terminal/oracle adjudication. `max_faults=0` is
unsafe in this mode (hangs).

## 8. Explicit non-claims

- No 60-sample formal experiment.
- No MD04 SDC pilot.
- R01/R04/R05 are squashed; only R02/R03 reach the register/consumer
  chain.
- Historical v3.2.6 traces are not rewritten.
