# LSU v3.2.4 — Status Report

**Date:** 2026-11-07
**Branch:** `lsu-platform-v3.2.4`, base `7f54db8d` (v3.2.3 final)
**Binary (DA04 post-review pilot runs):** `3e9148fc380c84917ddad84603e540b2e40e217918f392eb5659d32a56668297`
**Binary (FW02/SQ01 pilot runs):** `dae736b2c627960523579482ac0e2916bd015a290afffa88cdc941dec41a6e9c`
(The review fix only changes load attribution when a faulted store is registered,
so the FW02/SQ01 verdicts are unaffected and were not rerun.)
**Scope:** DA04 implementation + five pilots; FW02 terminal fix; chain-scoped PropagationCoverage; SQ01 propagation evidence; LP01 start.

## 1. Final answers

1. **Has DA04 really completed fault injection?**
   Yes. Five pilots each injected once at `LSQ::pushRequest`; the injection log
   and trace node record `0xF -> 0xE` with real SQ entry id/generation,
   address, size and store-data hash.
2. **Did clearing bit0 actually affect the target store?**
   Yes. In R02–R05 the cache-write node shows `disabled_unchanged=1` and
   `lane0_before == lane0_after` while the packet's lane0 carried the store
   byte (`0x01`, `0xC1`, `0x77`). In R04/R05 the later load returned the old
   byte (`0xA5`), not the intended store byte, and the application checksum
   changed.
3. **Are address, size and store data unchanged?**
   Yes. All five pilots: `all_addr_unchanged=true`, `all_size_4=true`,
   `StoreDataBefore == StoreDataAfter` (same FNV hash).
4. **Was the actual memory write tracked?**
   Yes. `store_mem_write` records the physical block address, offset,
   byte-enable mask, packet data, block bytes before/after, and
   `enabled_written`/`disabled_unchanged` flags.
5. **Were later Load and Consumer tracked?**
   Yes for R04/R05: `memory_response -> register_writeback ->
   errant_commit -> consumer_commit` on the same ptag chain, with 9,064/7,714
   consumer commits. The chain requires the load to be younger than the
   store, to respond after the actual cache write, and the byte not to have
   been overwritten; R03's earlier address-only consumer was removed by this
   guard. R02/R03 have no qualifying later load; R01 was squashed.
6. **What are the five pilot terminal states?**
   R01 SQUASHED; R02 MASKED (lane not read); R03 MASKED (lane not read);
   R04 SDC; R05 SDC.
7. **Has DA04 reached PROPAGATION_VERIFIED?**
   **Yes**, on the spec's evidence bar, using R04/R05: one chain with
   injection -> store writeback -> actual cache write -> load response ->
   register writeback -> consumer commit, `chain_integrity=PASS`, and the
   DA04 mask invariant. It is not claimed from "five runs succeeded".

## 2. Deliverable checklist

| # | Deliverable | Location |
|---|---|---|
| 1 | DA04 source audit | `DA04_Source_Audit_v3.2.4.md` |
| 2 | Fault model + source mapping table | same + `DA04_Implementation_v3.2.4.md` |
| 3 | Modified C++ source | `CHAOS/gem5/src/...` (see git diff) |
| 4 | Git diff + commit info | `LSU_v3.2.4_Git_Diff.txt`, `GIT_COMMIT_v324.txt` |
| 5 | DA04 configuration | `command.txt`/`manifest.json` in each pilot |
| 6 | Five pilot logs | `pilots_v3_2_4/DA04-R0*/` |
| 7 | Five JSONL traces | `pilots_v3_2_4/DA04-R0*/trace_v31.jsonl` |
| 8 | Byte-enable before/after | `pilots_v3_2_4/DA04_PILOTS.md`, injection nodes |
| 9 | SQ drain + memory-write evidence | `store_writeback` / `store_mem_write` nodes |
| 10 | Later Load/Consumer evidence | `memory_response`/`register_writeback`/`consumer_commit` |
| 11 | Oracle results | `oracle.log`, `pilot_meta.json` |
| 12 | Unit test + build logs | `tests/test_da04_byte_enable.cc`, `logs/` |
| 13 | FW02/SQ01 Trace fix results | `LSU_v3.2.4_FW02_Rejudge.md`, `LSU_v3.2.4_SQ01_Propagation.md` |
| 14 | 12-model progress | `LSU_v3.2.4_Model_Progress.md` |
| 15 | Open issues | §5 below |

## 3. Verification actually run (quoted)

```text
DA04 byte-enable unit test: PASS
pytest tests/ -> 65 passed
scons -j16 build/ARM/gem5.opt -> exit 0
no-fault alignment baseline checksum=0x3f89eab79392ce69 (golden)
trace_validator DA04-R01..R05 -> VALID x5
```

## 4. FW02 and SQ01 fixes

- **FW02**: terminal adjudication is now chain-scoped; a target Load that
  produced a response and a register writeback but was squashed before
  commit is SQUASHED. Rejudge over stored traces: FW02-R01 and FW02-R05
  `MASKED -> SQUASHED` (`TARGET_SQUASHED_NO_COMMIT`); A01-R03
  `UNRESOLVED/None -> SQUASHED`. Re-runs in
  `pilots_v3_2_4/FW02-R01`, `FW02-R05` confirm SQUASHED, accepted.
- **PropagationCoverage**: mandatory stages are now judged only on the
  injection's own chain (same ptag or same dyn seq); cross-instruction
  stitching is rejected; the validator refuses an `injection_event_id` that
  mixes ptags. DA04 R01–R05 and FW02 R01/R05 all have
  `chain_integrity=PASS`.
- **SQ01**: re-run with ptag chain + store writeback + actual memory write.
  All five are MASKED with `STORE_COMMITTED_LANE_NOT_READ`; the corrupted
  byte is written to the cache block (`before 0x00 -> after 0x08`) but no
  later load reads it. **SQ01 is not PROPAGATION_VERIFIED** (no consumer
  edge); it remains PILOT_RUN.

## 5. Open issues / honest boundaries

1. Excel EventOrdinal 1–5 for DA04 select dynamic-loader stores that are all
   squashed. The five pilots keep Excel SampleRunID/Seed but use temporary
   clinical ordinals (1, 6, 16, 50, 200), recorded as
   `excel_identity.event_ordinal_used`. Warm-up/ROI remain unfrozen.
2. SQ01 has no consumer edge in `sq_drain`; PROPAGATION_VERIFIED requires a
   context whose load consumes the corrupted byte.
3. gem5's store-to-load forwarding ignores byte-enable; a forwarded load sees
   the intended store data. The tracer records this boundary; such a run is
   not counted as a memory-write effect.
4. `store_mem_write` addresses are physical (cache block + offset) while the
   injection address is virtual; SE translation is observable in the trace.
5. SQ01 traces are 189 MB each and are excluded from Git (sha256 sidecars);
   they are in the delivery package and on disk.
6. The 60 formal samples were not run; no other model's configuration was
   changed.

## 6. Package

`LSU_v3.2.4_DA04_Implementation_Package.zip` (repository root) contains the
docs above, the five DA04/FW02/SQ01 pilot directories (including the large
SQ01 traces), build/baseline/unit-test logs, and the git diff/provenance.
