# LSU v3.3.2 — Round Log (append-only)

## 2026-11-11 Round start

- Read the v3.3.1 package README, finalization report, approval table, Agent B/E reports.
- Verified baseline HEAD `3504ec23`, binary `d3807fbe…`, 66 GiB free, 25 GiB available.
- Confirmed P0 entry points:
  - FW02: frozen W4 ELF has no data load; `workloads/directed/sq_forward_v33` exists (10 loads / 12 stores, SHA `58412423…`) and preserves the checksum `1f4cbf14327717df`.
  - RP01: `CHAOSLSQFwd::maybeSkipPartialReplay` hook at the `PartialAddrRangeCoverage` branch; frozen W7 is full 8 B overlap only.
  - MD04: `chaos_md04::isEligibleViolationPair` requires store_size=8, load_size>=8, real overlap; v3.3.1 census N_ROI=1.
  - LP01: `CHAOSPropagation::noteL1DForwardInjection` already records request/response ids and data hashes; `CHAOSL1DForward` log lacks PC/VA.
  - A03: `a03NoteEligibleLoad(dyn_seq, old_addr, addr, 3)` is called without a PC; the PRE hook accepts a defaulted `pc` argument.
  - Runner hazards: DA04 attaches at p=0; MD04 hard-codes `--md04_probability 1.0`.

## 2026-11-11 — Matrix execution and finalization

- Final binary `070d68a6…` built from HEAD source (two builds, 0 errors),
  installed at repo-root `build/ARM/gem5.opt`; v3.3.1 binary retained.
- 60/60 contexts mapped on the final binary (30 formal workloads, 30
  candidate workloads pending approval). All percentile arithmetic
  `start + ceil(p*N) - 1` validated; FW02 R02–R05 corrected and rerun.
- 60/60 fault runs injected; 60/60 controls zero-injection with real artifacts.
- Terminals: SDC 36, MASKED 12, HANG_TIMEOUT 5 (A03), HANG_WATCHDOG 5 (RP01),
  SQUASHED 1 (A01-R02), UNRESOLVED 1 (A01-R03).
- RP01 faults rerun with a 20M-cycle watchdog: all five print
  `CHAOS_RP01_WATCHDOG=EXPIRED fired=1` (exit 1), classified HANG_WATCHDOG.
- Regression: `pytest tests/ -q` 180 passed; platform 120 passed.
- Independent Agent F found the FW02 ordinal-offset bug and stale provenance;
  both fixed before packaging. Final verdict: PARTIALLY_READY.
