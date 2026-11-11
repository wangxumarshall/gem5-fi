# preformal_v3_3 patch proposals — Agent D (source-hook audit, 2026-11-11)

**Nothing here is applied.** These are unified diffs against the worktree
`lsu-platform-v3.2.12` HEAD (`f1291067`-era tree) written for review only; the
audit was read-only and no source under `CHAOS/gem5/src` was touched. None of
the patches change SampleRunIDs, Excel seeds, event ordinals, or fault
semantics; all are either record-only or matched-control-only paths.

All five currently **pass `git apply --check`** against this worktree
(verified 2026-11-11; nothing was applied). They are pure unified diffs —
the rationale lives here, not in the diff files. To adopt: `git apply`, rebuild
`cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt` (repo-root
`build/ARM/gem5.opt` is the binary every tool uses), then run the validation
below. No build or gem5 run was performed for this audit (hard rule), so every
patch is UNVERIFIED beyond applicability.

## Validation commands after apply (required before adoption)

```text
# 1. build (incremental is enough; new methods are header/cc only)
cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt

# 2. RP01: one skip pilot must show a recorded squash boundary
#    (run the frozen RP01 skip pilot command, then in prop_trace.csv.gz:)
zgrep 'record=squash_reason' prop_trace.csv.gz | grep -c 'triggering_seq_recorded=1'   # >0

# 3. A03: one crash pilot must carry the in-trace crash link
zgrep 'record=crash_addr_link' prop_trace.csv.gz                                      # >=1 row
zgrep 'crash_addr_matches=1' prop_trace.csv.gz                                        # >=1 row

# 4. FW05: one pilot must bind the reload lane
zgrep 'record=reload_consumer' prop_trace.csv.gz                                      # >=1 row

# 5. A01 control: SUPP-A01-C01's exact command must stay injected=0 and
#    produce the reference chain
#    (stdout) CHAOS_LSU_TRIGGER: ... injected=0
zgrep 'family=a01_control' prop_trace.csv.gz                                          # >=1 probe row
zgrep 'kind=resp' prop_trace.csv.gz                                                   # control response node

# 6. FW02: SUPP-FW02-C01's exact command must observe but not suppress
grep CHAOS_FW02_SUMMARY lsq_fwd_injections.log                                        # suppressed=0 observed>0
# and SUPP-FW02-R01 must still suppress exactly once.

# 7. regression: frozen fault-run traces must be byte-identical to the
#    pre-patch runs (record-only patches add nodes only on control/new paths;
#    RP01/A03/FW05 add rows, so compare the pre-existing node rows).
```

| Patch file | Model | Priority | Kind | Change in one line |
|---|---|---|---|---|
| `RP01_triggering_seq.diff` | RP01 | P1 (highest value/cost) | record-only | pass `squashed_num` to `noteSquash` at both `LSQUnit::squash` sites so R02/R03 stop grading `triggering_seq=0` / `fault_victim_unproven` |
| `A03_crash_addr_link.diff` | A03 | P2 | record-only | emit `a03_fault` {fault_va, golden_ea, actual_ea, crash_addr_matches} at the existing A01 fault-VA site, linking the crash address to the last `a03_stream` row |
| `FW05_reload_consumer.diff` | FW05 | P3 | record-only | bind the first later memory-path load covering the affected lane as `fw05_reload` with true/alt hash comparison (the missing store→reload visibility leg) |
| `A01_control_memory_nodes.diff` | A01 | P4 | control-only | at probability 0.0 run the same F0 ordinal selection and register the golden EA read-only (probe/a01_ea/mem_req/resp) without mutating addr/size or counting an injection |
| `FW02_probability_guard.diff` | FW02 | P5 (correctness hardening) | control predicate | consult `probability` in `maybeSuppressForwarding`; a mounted p=0 run observes but never suppresses, removing the only known control misfire (SUPP-FW02-C01) |

## Priority order and rationale

1. **RP01** — smallest diff, pure record enrichment, directly closes the
   documented `triggering_seq=0` gap (FINAL_INDEPENDENT_AUDIT_v3.2.12.md,
   RP01 blocker 4). No behavior change at all.
2. **A03** — the persistent/activation/ALREADY_STUCK semantics are already
   conforming; only the crash-address join is offline today. This patch makes
   the join provenance part of the trace (Arm AbortFault path only; raw gem5
   panics still need the offline link — stated in the patch header).
3. **FW05** — closes the native-edge LIFECYCLE_ONLY blocker by recording the
   reload lane bytes; the classifier logic is untouched, so an audit can now
   prove or disprove memory visibility without a new binary key.
4. **A01** — the fault-run injector is conforming; the gap is the matched
   control producing no memory nodes. This patch is the most invasive of the
   five (touches the trigger, the injector, the tracer and the control-only
   flag) and only affects probability-0.0 runs.
5. **FW02** — hardening. The current project already ships a correct control
   by omitting the injector (`platform/run_pilot.py`, FW02 branch), so this is
   not needed for the frozen 12-model evidence; apply it before any future
   control sweep that mounts the injector at p=0.

## Latent control hazard noted but NOT patched

`CHAOSLSQFwd::maybeCorruptStoreByteEnable` (DA04) has no `probability` guard
and its constructor self-attaches at p=0 (`CHAOSLSQFwd.cc:128-133`), exactly
the FW02 pattern. No DA04 control pilot exists in `pilots_v3_2_12`, so the
12-model evidence is unaffected; a future DA04 p=0 control run **must** omit
the injector or apply the same guard. RP01's `maybeSkipPartialReplay` also
does not consult `probability`, but RP01 is driven by `rp01_*_mode`/ordinal
and its control story is the count-only mode (no fault action), not the
probability knob.


## Applied status (2026-11-11, v3.3.0 round)

The FW02 guard, FW05 reload node, RP01 triggering_seq, A01 control probe and
A03 crash-link diffs were applied and committed in `5541648c`, `364a6057` and
`c8fc4353` (with a follow-up 0/0-match guard in `5541648c`'s area). The W4
workload is tracked as a proposal (`c1846ae4`) and is NOT promoted to the
formal workbook. The diffs remain here as the proposed-patch record; they now
reverse-apply cleanly because the code is already in the branch.
