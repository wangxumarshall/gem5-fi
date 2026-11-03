# R6-O Unit — F0/F5 Capability Census (2026-11-03)

Scope: the 10 authoritative O-F0/F5 RunIDs only. Evidence is read-only code/binary/
stream inspection plus the two no-fault restore smokes in
`runs/lsu/r6_o_unit/smoke_restore_0{1,2}`. No blanket `blocked(multicore-fs)`
is used: every BLOCKED row below names the exact host/workload/spec reason.

Binary audited: `.../r6-c-unit-20261102/CHAOS/gem5/build/ARM/gem5.opt`,
sha256 `deecd9e3b58d493271afc93b67126128c31ecba082163dcaecf5bb958c3d848b`
(the boot/checkpoint binary). Repairs are built from this worktree and will have
a new SHA, recorded with every run.

## Platform status (measured)

- Checkpoint `runs/lsu/r6_o_unit/mc_boot/cpt.243414599076`: 2-core Ruby/CHI,
  Atomic boot, complete (`m5.cpt`, 8 pmem stores, cow, ruby cache gz); terminal
  `boot pass: checkpoint taken; exiting`; stats simTicks 245109869109.
- O3 restore smoke (no injection), twice: `nproc=2`,
  `cpuinfo processors=2`, SB histogram, atomic `violations=0`,
  `FINAL=6b39e7aaa74b663f` = `FSMC_GOLDEN_FINAL`, payload exit 0, identical
  `simTicks=24704428176` / `simInsts=59587059` in both runs, `prop_evt.txt.gz`
  has zero events and a valid gzip EOF. The platform and the replay are real.

## Authoritative table

| RunID | Model | Route | Binary symbols | Workload instruction reality | Classification | Exact reason |
|---|---|---|---|---|---|---|
| O01-F0-W7 | O01 monitor-address bitflip (03 matrix:58) | `exmon-fsmc` (lsu_campaign.py:519) + FS config flags | `CHAOSExMon::maybeCorruptMonitor` 0x313e2c0, `maybeCorrupt` 0x313f8d4; strings `o01_monitor_addr_bitflip` | `litmus_free` LDXR/STXR at 0x400230/0x400238, 0x400988/0x400990 (objdump), runtime `tries cpu0=39 cpu1=16` | **REPAIRABLE** (repair implemented, rebuild+canary pending) | Pilot stream showed the fault was injected but never activated (deferred O3 misc-reg write; 97/97 STXR success). Fixed by evaluating the SC against the corrupted monitor and by emitting a real L2→L3 consumption chain + containment witness (CHAOSExMon.cc maybeCorrupt). |
| O02-F0-W7 | O02 monitor-state corrupt (03 matrix:59) | same | same | same | **REPAIRABLE** (same repair) | Same activation defect; additionally the old stream had a false LDXR data-taint / premature errant_commit (registerPtagBlock on the load line). Removed for monitor modes; the chain is now monitor-only with an L3 containment witness. |
| O02-F5-W7 | O02 permanent (`maxFaults=0`) | same (lsu_campaign.py:1893-1898) | same | same | **UNDER_MEASUREMENT** | With the activation fix, a permanent monitor corruption makes every LDXR place a corrupted reservation, so every STXR fails and the workload's `do { ldxr; stxr } while (stx != 0)` cannot make progress — expected livelock/Timeout. If measured, this is a semantics/workload conflict requiring a ruling (the old 104-injection pilot completed only because the fault was inert). |
| O03-F0-W7 | O03 STXR status flip, routed mode `stxr_force_fail` (03 matrix:60; source map notes approximation) | `exmon-fsmc` (lsu_campaign.py:521) | `CHAOSExMon::maybeCorrupt`; strings `stxr_force_fail` | same LL/SC carrier | **REPAIRABLE** (crash fixed) | The 2026-10-23 pilot SIGABRTed (`request.hh:912` `extraDataValid()` in `STXRW64::completeAcc`): a forced failure insta-completes the store without a memory response, and the normal failure path is the only one that calls `setExtraData(0)` (isa.cc:1942). Fix mirrors it. HONEST BOUNDARY: the forced-fail path blocks this store instead of keeping the memory update fact constant (documented approximation); O03-b is not routed. |
| O04-F0-W7 | LSE RMW data/return MUX (03 matrix:61) | `cache` family → SE classic `lsu_proxy.py` (lsu_campaign.py:535) | `CHAOSCache::maybeCorruptRmw` 0x17e1b50, `BaseCache::chaosRmwCommit`; strings `rmw_mux`, `swap_oldnew` | W7 carriers have ZERO LSE (objdump `cas|swp|ldadd|ldclr|...` = 0 on litmus_free/atomic/atomic_fs/mp/sb); only `workloads/directed/lse_rmw` has 3 | **BLOCKED_INFRA + BLOCKED_WORKLOAD** | (1) The hook lives in classic `BaseCache::satisfyRequest` (base.cc:1406-1442); Ruby/CHI L1s are not classic `Cache` and execute atomics in SLICC (`CHI-cache-actions.sm:2505,3659`); `configs/fs/lsu_multicore_fs.py:51-63` states the mutual exclusion and mounts no cache injector. (2) Even on a classic SE run the W7 binaries never execute an LSE, and the hook gates on `pkt->isAtomicOp()` (CHAOSCache.cc:1087-1088). O04-b/c/d are not implemented (CHAOSCache.hh:85-94). A config/routing fix cannot satisfy the W7 cell. |
| O05-F0-W7 | RMW request/done timing (03 matrix:62) | same | same; `rmw_order`, `lost`, `dup` | same zero-LSE evidence | **BLOCKED_INFRA + BLOCKED_WORKLOAD** | Same classic-host/Ruby incompatibility; `lost`/`dup` gate on `isAtomicOp()` and the W7 carrier only issues LL/SC; O05-c (done-too-early) has no platform node (R4-9-FSMC-C:132-137). |
| O06-F0-W7 | Barrier completion (03/07:209) | `lsqfwd` family, SE only (lsu_campaign.py:547) | `CHAOSLSQFwd::maybeCorruptBarrierInsert/Release`; strings `o06a_early_done`, `o06b_done_stuck` | `litmus_free` has 20 `dmb ish` sites (objdump) | **BLOCKED_SPEC** | The landed hook never calls `registerInjection`: no `inj`/fault_id (CHAOSLSQFwd.cc:919-927, 969-977), so `_group_by_fault` discards every event (lsu_chain_check.py:207-217) and `check_admission` is false. `barrier_done` maps only to L2 and has no detection/outcome (lsu_prop_fields.py:180-184) — there is no defined L5 terminal for a barrier fault. Additionally, O06-b's "stuck" SN does not gate later ops (the hash entry is erased before the hook; mem_dep_unit.cc:443-466, 419-441) — inference from code paths, contradicts the header. Fixing this needs new chain/spec semantics, not wiring. |
| O07-F0-W7 | LSU order-tag/valid/ready proxy (03/07:212; honest proxy documented) | `lsqfwd` family, SE only (lsu_campaign.py:548) | `orderTagSubstitute` 0x119c470; strings `o07_order_tag_swap` | same DMB sites | **BLOCKED_SPEC** | Same missing fault registration/terminal as O06; O07-b/c are not distinct injected states, only the barrier-SN proxy; the barrier hooks are process-global while InstSeqNum is per-CPU, so a swap can name the other core's SN (inference from chaos_barrier_hook.hh:44-59 + CHAOSLSQFwd.cc:1043-1052). No admissible L0→L5 chain exists. |
| O09-F0-W7 | LSE RMW operand latch (03 matrix:65) | `cache` family, SE classic (lsu_campaign.py:537) | `CHAOSCache::maybeCorruptRmw`; strings `rmw_latch`, `result_old` | W7 carriers have zero LSE | **BLOCKED_INFRA** | The `rmw_latch`/`result_old` hook is real and compiled (refutes the stale "COMPILE-UNVERIFIED"), but it lives in classic `BaseCache` and cannot mount on Ruby/CHI; W7 needs the coherent multicore platform. The landed subset covers only the result/old-value face, not compare/replacement/addend (CHAOSCache.hh:76-89). |
| O09-F0-W13 | same, PARSEC workload | `cache` family | same | PARSEC absent | **BLOCKED_WORKLOAD** (+ BLOCKED_INFRA) | `find workloads gem5-fs -iname '*parsec*' -o -iname '*dedup*' -o -iname '*ferret*' -o -iname '*streamcluster*'` → 0 hits; only a disabled x86_64-only upstream test scaffold exists (CHAOS/gem5/tests/gem5/parsec_benchmarks/test_parsec.py:53-57). Substituting a repo probe would change the cell identity (spec ruling required). |

## Shared root causes found

1. **Monitor-fault activation (O01/O02).** O3 defers `setMiscReg` to commit
   (`src/cpu/o3/dyn_inst.hh:1099-1129`); the STXR's `handleLockedWrite` runs at
   issue. The pilots therefore injected but never activated the fault
   (97/97 `exmon_stxr` = `match_success`, `tries` identical to the clean
   control). Repair: evaluate the SC comparison against the corrupted monitor
   in `CHAOSExMon::maybeCorrupt` and retire the ptag after the paired SC.
2. **False data taint + L5 ordering (O01/O02).** `registerPtagBlock` on the
   load's line made the correct LDXR data taint and produced an
   `errant_commit` that is an ancestor of the STXR consumption nodes
   (`time_reversed_edge`, `cross_branch_edge`). Monitor modes now register a
   size-0 marker (never range-matches) and emit the chain they actually have.
3. **O03 forced-fail missing `extraData`** (crash). Fix mirrors isa.cc:1942.
4. **Stream size.** The old streams are 222k–225k events > `EVENT_CAP=200000`
   (`tools/lsu_prop_fields.py:65`). The current binary's consumer aggregation
   is expected to collapse them (the monitor-only chain is smaller still),
   but the `lsu_ready_contract` 4,000-event cap is a separate limit that must
   be checked per run.
5. **O06/O07/O04/O05/O09 are not "multicore-fs is missing"**: the platform now
   exists (checkpoint + O3 restore). Their blockers are chain semantics
   (O06/O07), injector-host architecture (O04/O05/O09), and workload identity
   (O09-W13).

## Not in scope

F1/F2/F3/F4/F6 are not run this round (user ruling). P unit not started.
