# MD04 implementation and pilots (v3.2.6)

**Binary:** `0de2564468fd710bf1df22d2336acac0ea92f7bc1ef5780178f18f497a302d7d`

## Implementation

- New SimObject `CHAOSMD04` (`CHAOS/gem5/src/cpu/o3/CHAOSMD04/`), self-attaches
  via `CPU.chaosMD04`.
- Hook in `LSQUnit::checkViolations` store branch suppresses one eligible
  same-address 8-byte store→load violation report.
- Config: `--chaos_md04 --md04_event_ordinal N --md04_max_faults 1
  --md04_probability 1.0 --md04_first_clock 0 --md04_rng_seed S`.
- Trace: `inj_md04` (site, load/store seq, addr, size, ordinal,
  `violation_report_suppressed=1`, `load_complete`), then either a normal
  response/writeback chain or a **late-bound** `register_writeback`
  (`late_binding=1`, PRF value read at injection because the response was
  already consumed). Consumers/commit use the normal chain.
- Unit test: `tests/test_md04_rules.cc` (same-address/8B, 16-byte load
  covering an 8-byte store, 4-byte reject, ordinal/maxFaults) — PASS.

## Five pilots (W7, Excel seeds; clinical ordinal = Excel ordinal)

| Pilot | load seq | store seq | addr | size | eligible ordinal | load complete at injection | consumers | oracle | terminal |
|---|---:|---:|---|---:|---:|---:|---:|---|---|
| R01 | 518 | 514 | 0x7ffffefc10 | 8 | 1 | 1 | 0 | PASS | SQUASHED |
| R02 | 2251 | 2239 | 0x493990 | 8 | 2 | 0 | 6 | PASS | MASKED |
| R03 | 17443 | 17442 | 0x491990 | 8 | 3 | 0 | 259 | PASS | MASKED |
| R04 | 69297 | 69292 | 0x7ffffefb78 | 16 | 4 | 0 | 0 | PASS | SQUASHED |
| R05 | 71660 | 71652 | 0x4915a0 | 8 | 5 | 1 | 2 | PASS | MASKED |

- In W7 the eligible stream depends on the store/load execution order; the
  per-pilot dyn seq differs from the probe-time run because the seed changes
  the schedule (recorded).
- R02/R03/R05 have complete injection→response (or late-bound writeback)→
  writeback→consumer→commit chains; R03 has 259 consumers.
- R01/R04 are squashed before commit (valid SQUASHED outcomes).
- No MD04 SDC: the stale data did not change the W7 checksum in these
  events. The model is PILOT_RUN + chain-level PROPAGATION_VERIFIED, not an
  SDC claim.

## Unfinished

- No SDC pilot; the five W7 events all pass the oracle.
- `possibleLoadViolation` (load/load) remains a separate mechanism and is not
  the MD04 target (documented correction).
- Formal 60-sample grid not run.
