# LSU v3.2.6 — LP01 trace closure + MD04 implementation

**Branch:** `lsu-platform-v3.2.6` (from `bca94be7`, v3.2.5 tip)
**Final binary:** `0de2564468fd710bf1df22d2336acac0ea92f7bc1ef5780178f18f497a302d7d`
**Scope:** LP01 consumer-edge closure; generic PRF-value writeback hashes;
DA04 end-to-end chain; MD04 implementation + five pilots. No 60-sample run.

## 1. LP01 consumer-edge closure

`noteCommit` now emits a real `register_dataflow` edge only when
`consumer_input_fnv == source value hash`. Mismatches emit
`taint_value_mismatch` (hash, phys/arch reg, reason) and never re-taint.
Operand records and unique consumer instructions are reported separately.
Coverage counts matched `consumer_commit` only.

| Pilot | old records | old matches | old mismatch | new records | new instructions | new mismatch |
|---|---:|---:|---:|---:|---:|---:|
| R01 | 183 | 129 | 54 | 110 | 96 | 45 |
| R02 | 1 | 1 | 0 | 1 | 1 | 0 |
| R03 | 6 | 3 | 3 | 3 | 3 | 3 |
| R04 | 1 | 1 | 0 | 1 | 1 | 0 |
| R05 | 6 | 3 | 3 | 3 | 3 | 3 |

All five v3.2.6 pilots: one injection, MASKED (oracle PASS), validator VALID,
coverage COMPLETE, chain PASS. Old v3.2.5 traces untouched.

**Hash-continuity root cause:** for size<8 the packet payload is not the
register value (endianness/extension). The tracer now emits
`register_writeback` after `completeAcc`, reading the actual PRF value. This
removed DA04's 4-byte false mismatch (`payload a514af81` vs register
`0x81af14a5`) and makes the consumer input match the source hash.

## 2. DA04 end-to-end chain (R04/R05)

R04: byte-enable `0xF→0xE` (seq 13832) → SQ writeback → cache block update
(tick 17,042,410, lane0 `0xA5→0xA5`, disabled lane unchanged) → load
`mem_req` (seq 19210, request 35, first send 2,286,900, **last send
17,889,025**, candidate=1) → response (`a514af81`, tick 17,889,795) →
actual PRF writeback (`0x81af14a5`, fnv `a959f41d27dbce18`, payload fnv
`d9a56276a6025898`, `hash_basis=regval_extension`) → **1,009 matched
consumers** → commit → oracle FAIL (`3f89eab79392ce4d`) → SDC.

R05: analogous; last send 18,004,525 > store write 17,157,910; **7,714
matched consumers**; oracle FAIL (`b948f769e7d691f5`) → SDC.

Both: 0 hash mismatches, validator VALID, coverage COMPLETE, chain PASS.
Edges: R04 1,018 (1,009 register + 9 ptag; 0 missing type); R05 7,724.

## 3. MD04 implementation and pilots

Definition (source-corrected): the W7 store→younger-load detection is the
`M5PanicFault` return in `checkViolations` (`lsq_unit.cc:655`), not the
load/load `possibleLoadViolation(true)` flag. MD04-CFG01 suppresses one real
same-address 8-byte store alias report (16-byte LDP covering an 8-byte store
included; 4-byte pairs excluded). New `CHAOSMD04`, hook, config, unit test,
trace (`inj_md04`, late-bound writeback when the response was already
consumed), converter/completeness/terminal/runner support.

| Pilot | load seq | store seq | addr | size | ordinal | consumers | oracle | terminal |
|---|---:|---:|---|---:|---:|---:|---|---|
| R01 | 518 | 514 | 0x7ffffefc10 | 8 | 1 | 0 | PASS | SQUASHED |
| R02 | 2251 | 2239 | 0x493990 | 8 | 2 | 6 | PASS | MASKED |
| R03 | 17443 | 17442 | 0x491990 | 8 | 3 | 259 | PASS | MASKED |
| R04 | 69297 | 69292 | 0x7ffffefb78 | 16 | 4 | 0 | PASS | SQUASHED |
| R05 | 71660 | 71652 | 0x4915a0 | 8 | 5 | 2 | PASS | MASKED |

MD04 is IMPLEMENTED / COMPILED / UNIT_TESTED / PILOT_RUN / chain-level
PROPAGATION_VERIFIED. No MD04 SDC.

## 4. Final-v3.2.5-binary smoke

`pilots_v3_2_6/SMOKE_LP01-R01_final_binary` ran on the v3.2.5 final binary
`6808c56e…`: one injection, MASKED, coverage COMPLETE, chain PASS, manifest
binary SHA recorded.

## 5. Verification

- Build `scons -j16` exit 0.
- `tests/test_md04_rules.cc` PASS; LP01 matrix PASS; store-chain PASS; DA04
  byte-enable PASS.
- `pytest platform/tests/ -q` → 74 passed.
- All v3.2.6 traces: validator VALID.

## 6. Explicit non-claims

- LP01: five MASKED pilots, no SDC pilot.
- DA04: R04/R05 SDC; R01–R03 not rerun (their generation is unchanged by
  the load-side writeback hash; no claim is made about new traces).
- MD04: no SDC pilot; 3 traced chains, 2 squashed.
- Formal 60-sample experiment not run; warm-up/ROI not frozen.
