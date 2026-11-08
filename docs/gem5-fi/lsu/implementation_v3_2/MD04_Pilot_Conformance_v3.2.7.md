# MD04 historical pilot conformance (v3.2.6 → v3.2.7)

Definition: `MD04_Definition_Freeze_v3.2.7.md` (`MD04-DEF-v2`).
New runs: `pilots_v3_2_7/MD04-R01..R05` (Excel v3.2.2, original
SampleRunID/Seed, `--preserve-sample-id`). Historical traces in
`pilots_v3_2_6/` are untouched.

## Checklist applied to each historical pilot

1. Hook at `LSQUnit::checkViolations` store branch — source v3.2.6 has the
   hook at the `M5PanicFault` return (`lsq_unit.cc:652-662` in the v3.2.7
   tree; the v3.2.6 commit `f21003da` introduced it there).
2. Real 8-byte store + eligible younger load — the old injector enforced
   `store_size==8`, `load_size>=8`, exact start address; the old log did
   not print store size/address.
3. Exactly one `M5PanicFault` return skipped — `faults_injected=1` in all
   five old logs.
4. No address/size/data change — `maybeSkipViolation` only returns true;
   the code path has no write to the access.
5. Only the target event — `eligible_ordinal` equals the Excel ordinal in
   all five old logs (under the old stream).
6. TargetPairID — absent in v3.2.6 traces.
7. Full propagation trace — present; R03's cross-attempt chain was not
   identity-verified (see `R03_Execution_Attempt_Investigation_v3.2.7.md`).
8. Terminal + oracle — present for all five.

## Frozen eligible stream (all five seeds)

`evidence_v3_2_7/MD04_eligible_stream_v327.csv` is generated from
`--md04_count_only --debug-flags=CHAOSMD04` runs. The stream is identical
for all five seeds:

| ordinal | load seq | load addr | load size | store seq | store addr | store size |
|---:|---:|---|---:|---:|---|---:|
| 1 | 518 | 0x7ffffefb90 | 8 | 514 | 0x7ffffefb90 | 8 |
| 2 | 2251 | 0x493990 | 8 | 2239 | 0x493990 | 8 |
| 3 | 17443 | 0x491990 | 8 | 17442 | 0x491990 | 8 |
| 4 | 69297 | 0x7ffffefaf8 | 16 | 69292 | 0x7ffffefaf8 | 8 |
| 5 | 69297 | 0x7ffffefaf8 | 16 | 69294 | 0x7ffffefb00 | 8 |
| 6 | 71660 | 0x4915a0 | 8 | 71652 | 0x4915a0 | 8 |

The 4-byte pair (load 2545 / store 2533) is evaluated by the debug print but
rejected by `MD04-ELIG-v1`; it does not consume an ordinal.

## Verdicts

| Pilot | Historical target | Frozen ordinal target | Verdict |
|---|---|---|---|
| R01 | 518/514 (ordinal 1) | 518/514 (ordinal 1) | **CONFORMING** (historical metadata incomplete; new run supplies it) |
| R02 | 2251/2239 (ordinal 2) | 2251/2239 (ordinal 2) | **CONFORMING** |
| R03 | 17443/17442 (ordinal 3) | 17443/17442 (ordinal 3) | **CONFORMING** (historical chain `CROSS_ATTEMPT_UNVERIFIED`; new run `CROSS_ATTEMPT_VERIFIED`) |
| R04 | 69297/69292 (ordinal 4) | 69297/69292 (ordinal 4) | **CONFORMING** (16-byte LDP covering the 8-byte store) |
| R05 | 71660/71652 (old ordinal 5) | 69297/69294 (frozen ordinal 5); old pair is now ordinal 6 | **HISTORICAL_NONCONFORMING (ordinal drift)** — the historical injection itself satisfies the eligibility rule, but its Excel EventOrdinal no longer selects it |

R05's historical trace is retained unchanged. The frozen run uses ordinal
5 (store 69294; a real 8-byte store covered by the 16-byte load's upper
half) and terminates SQUASHED, so the historical MASKED/2-consumer result
does not carry over to the frozen target.

## New runs (frozen definition)

| Pilot | TargetPairID | pair ordinal | attempts | link | consumers | oracle | terminal | coverage | chain |
|---|---|---:|---|---|---:|---|---|---|---|
| R01 | MD04-L518-S514-T733425 | 1 | 1→squash | SAME_ATTEMPT | 0 | PASS | SQUASHED | COMPLETE | PASS |
| R02 | MD04-L2251-S2239-T3391080 | 2 | 1→1 | SAME_ATTEMPT | 6 | PASS | MASKED | COMPLETE | PASS |
| R03 | MD04-L17443-S17442-T17816260 | 3 | 1→2 | CROSS_ATTEMPT_VERIFIED | 259 | PASS | MASKED | COMPLETE | PASS |
| R04 | MD04-L69297-S69292-T31073735 | 4 | 1→squash | SAME_ATTEMPT | 0 | PASS | SQUASHED | COMPLETE | PASS |
| R05 | MD04-L69297-S69294-T31074120 | 5 | 1→squash | SAME_ATTEMPT | 0 | PASS | SQUASHED | COMPLETE | PASS |

All five: exactly one injection, `store_size=8`, `load_size>=8`, real byte
overlap, younger load, `address_modified=0 size_modified=0
data_modified=0`, validator VALID, oracle PASS.

## Non-claims

- No MD04 SDC pilot exists.
- R01/R04/R05 are squashed; only R02/R03 reach the register/consumer
  chain (6 and 259 consumer instructions).
- The historical v3.2.6 traces remain the record of that binary; they are
  not rewritten or relabelled.
