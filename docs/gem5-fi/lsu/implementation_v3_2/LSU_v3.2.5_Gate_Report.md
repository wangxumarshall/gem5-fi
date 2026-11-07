# LSU v3.2.5 gate (2026-11-08)

- Build: `scons -j16 build/ARM/gem5.opt` (from `CHAOS/gem5`) → exit 0, 0 errors;
  log `logs/build_v325_lp01.log`. Binary copied to the repo-root
  `build/ARM/gem5.opt` used by every tool.
- Binary SHA-256 (final, post-review fix): `6808c56e22b44eab3e189a1c51e6b90ec1c95e0c66d0c0835d205575572d7645`
  (`baselines_v3_2_5/binary_v325.sha256`). The five LP01 pilots ran on the
  earlier gate binary `69a1ca9c…`; their manifests record that binary. The
  post-review changes touch DA04 last-send causality, non-scalar/no-writeback
  hash bases, default-mask lane selection and ordinal counting; the LP01
  pilot outputs are unaffected (mask 0x8, probability 1.0, scalar 8-byte).
- C++ unit tests:
  - `LP01 byte-0 payload matrix (0/1/4/7/8/9/12/16): PASS`
  - `store-chain attribution (request-time) unit test: PASS`
  - `DA04 byte-enable unit test: PASS`
- Python: `pytest platform/tests/ -q` → `74 passed` after the review fix
  (two new hash-basis tests); the pre-review run was `72 passed`.
- Unaffected workload regression: W5 `load_response` no-fault →
  `checksum=0x99c106541150be0e` (Excel golden), exit 0, no SIGSEGV.
- LP01 runner smoke (R01 context, ordinal 1): one injection, mask 0x8,
  size 8, `eligible_ordinal=1`; trace coverage COMPLETE, chain integrity
  PASS, terminal MASKED (target committed, oracle PASS), accepted=true.
- Status: LP01 IMPLEMENTED / COMPILED / UNIT_TESTED. Pilots run next;
  PROPAGATION_VERIFIED is claimed only if a pilot trace carries the
  injection→response→writeback→consumer→commit chain with matching hashes.
- DA04 consequence after the review fix: causality is anchored at the **last
  send** (the fetching attempt). R04/R05 are rerun as SDC with 1,009 / 7,714
  causal consumers; the first-send-only intermediate verdict (UNRESOLVED) was
  wrong and is superseded. The v3.2.4 artifacts are not overwritten.

## Post-review fix pass (final)

- Important #1: `last_send_tick` recorded for every Request; request-side and
  response-side DA04 causality use it; every overlapping send emits a
  `mem_req` node (including before the store write, with
  `store_not_written_yet=1`).
- Important #2: a faulted load that skipped `completeAcc` emits
  `hash_basis=no_writeback_fault` instead of a false hash discontinuity.
- Important #3: `hash_basis=payload_equals_regval` is used only for an
  8-byte scalar destination; vector destinations use `no_scalar_regval`.
- Important #4: a random default mask selects a bit in byte 0 only; a mask
  with no byte-0 bit is rejected before the probability draw; the reported
  ordinal includes post-skip declined events.
- Verification: build exit 0; C++ tests PASS; `pytest` 74 passed; W5 no-fault
  `checksum=0x99c106541150be0e`; DA04 R04/R05 SDC reruns VALID/COMPLETE.
