# LSU v3.2.5 gate (2026-11-08)

- Build: `scons -j16 build/ARM/gem5.opt` (from `CHAOS/gem5`) → exit 0, 0 errors;
  log `logs/build_v325_lp01.log`. Binary copied to the repo-root
  `build/ARM/gem5.opt` used by every tool.
- Binary SHA-256: `69a1ca9c5b1cbfb160d0502a8cad8acf7d17101625228978ec79ede588b2287d`
  (`baselines_v3_2_5/binary_v325.sha256`).
- C++ unit tests:
  - `LP01 byte-0 payload matrix (0/1/4/7/8/9/12/16): PASS`
  - `store-chain attribution (request-time) unit test: PASS`
  - `DA04 byte-enable unit test: PASS`
- Python: `pytest platform/tests/ -q` → `72 passed`.
- Unaffected workload regression: W5 `load_response` no-fault →
  `checksum=0x99c106541150be0e` (Excel golden), exit 0, no SIGSEGV.
- LP01 runner smoke (R01 context, ordinal 1): one injection, mask 0x8,
  size 8, `eligible_ordinal=1`; trace coverage COMPLETE, chain integrity
  PASS, terminal MASKED (target committed, oracle PASS), accepted=true.
- Status: LP01 IMPLEMENTED / COMPILED / UNIT_TESTED. Pilots run next;
  PROPAGATION_VERIFIED is claimed only if a pilot trace carries the
  injection→response→writeback→consumer→commit chain with matching hashes.
- DA04 consequence recorded honestly: under request-time causality the
  v3.2.4 R04 chain has zero attributable consumers and its terminal is now
  UNRESOLVED / ORACLE_FAIL_NO_CAUSAL_CONSUMER (was SDC). R04/R05 are
  rerun in Task 18; the v3.2.4 artifacts are not overwritten.
