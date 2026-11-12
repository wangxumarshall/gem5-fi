# LSU v3.3.3 — Consolidated Repair Plan

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Baseline:** HEAD `3097ad82` / source `fc608224` / binary `070d68a6…`
**Inputs:** `README_GROUND_TRUTH.md`, `reports/Agent_{A..F}_*.md`, `LSU_v3.3.3_Master_Defect_Ledger.csv` (46 issues).
**Status:** diagnosis complete; no source file, workload, frozen Excel or audit_v3_3_2 artifact was modified by the diagnosis.

---

## 0. Executive summary

The v3.3.2 data plane is largely sound, but its **classification and identity plane is not**. Three source-level defects, one control-close hazard family, and a set of tooling/provenance defects explain every non-ready context:

1. **A01-R03** is not an observer gap: the PRE hook counted a translation retry as an eligible event and injected into a by-value address that `LSQ::pushRequest` discards when `inst->translationStarted()` reuses `savedRequest` (`applied_to_request=0`). The same defect can place an A03 activation on a retry.
2. **A03** is not an evidence-free HANG: all five fault runs printed a final application checksum (`1fd794b8489219e1`, `9fc828ecfead80f9`, `bfccf156021968dd`, `191a781887e50cec`, `20057ce453d4f1e9`) different from golden `728e604ffcec539d`, while every control printed golden. The external 30 s kill only destroyed the trace trailer and the exit-time lifecycle line. A03 is an SDC/oracle-failure case with a post-oracle simulator hang.
3. **SP05** honestly reports `store_data_fnv=null` because the recorder never receives the SQ entry bytes; the bytes are available at the `lsu_unit.cc` SP05 branch.
4. **Control close paths** are safe today only because several controls omit the injector. MD04's separate `--md04_probability` defaults to 1.0; DA04/LQ04/RP01 have no global gate; SQ03/SP05 arm watchdogs at p=0.
5. **The tables** mislabel 35/60 controls as `INJECTOR_ABSENT`, report `seed`/`terminal` null, conflate the A03 log cap with the injection count, and use tautological activation fields.

No repair changes a fault's target field, bit, value, mode or duration. The only mapping change is the A01/A03 eligible-event re-census forced by the PRE-retry fix; SampleRunID and Seed stay frozen.

---

## 1. Root-cause clusters and the nine required answers

### R1 — PRE-hook retry injection (L-A01; affects A01-R03 and A03 activation)

1. **Root cause:** `LSQ::pushRequest` calls `chaosAddrPathPre->maybeCorruptPre()` before the `inst->translationStarted()` branch. On a retry, the mutated `addr`/`size` are ignored and `inst->savedRequest` is reused; the trigger nevertheless counted the retry as a new eligible event. A01-R03's trace proves it: `a01_ea_discarded; applied_to_request=0; discard_reason=saved_request_reuse`, golden response at `request_tick=15540910`, injection at `16301670` (after the request was already in flight).
2. **Why it survived:** the v3.3.2 chain checker only asked whether an injection event existed and the instruction committed; it did not ask whether the injection reached the Request. The `a01_ea_discarded` record was written but `terminal_rules.py` ignored it.
3. **Correct layer:** `CHAOS/gem5/src/cpu/o3/lsq.cc` (PRE block) with a provenance counter in `CHAOSAddrPath`.
4. **Affected:** A01 R01–R05, A03 R01–R05. Other PRE-family models (A04–A08, L01/L02, S04–S13) share the hook and must be included in the regression statement, but are outside this round's 12-model scope.
5. **Semantics:** unchanged. The EA bit-flip / stuck-at definitions are untouched; only which dynamic instruction is eligible changes.
6. **Rebuild:** yes (C++).
7. **Pilots:** re-census A01/A03; rerun all 5+5 fault/control pairs.
8. **One-shot validation:** `a01_ea_discarded` count = 0 on A01; a fault run has `register_writeback` + `errant_commit`; A01 control prints `728e604ffcec539d`; A03 activation ordinal maps to a unique instruction and the first `STUCK_APPLIED` is recorded.
9. **Approval:** yes — the A01/A03 ordinal set is a context-mapping change (seeds and SampleRunIDs unchanged).

### R2 — A03 observation, watchdog and terminal (L-A02, L-A03, L-A04, L-C01)

1. **Root cause (three layers):**
   - Fault semantics are persistent, so after the final `put_hex` the corrupted address stream breaks the guest exit path; the driver kills the process at 30 s.
   - The exit callback never runs, so `A03_STUCK_LIFECYCLE` is missing and `prop_trace.csv.gz` lacks its gzip trailer.
   - The parser looks for `checksum=0x…` but the workload prints a bare 16-hex final line, so the divergent checksum is invisible to the harness.
2. **Why it survived:** the driver was written to bound a "may not terminate" fault; it never separated "application oracle reached" from "simulator failed to exit". The report inherited the parser's blind spot.
3. **Correct layer:** `CHAOSAddrPath` (in-sim watchdog + graceful exit/flush), `tools/lsu_v332_matrix.py` (count and oracle parse), `terminal_rules.py` (terminal mapping).
4. **Affected:** A03 R01–R05.
5. **Semantics:** unchanged. The watchdog only terminates after the fault has run; it does not stop or alter the fault.
6. **Rebuild:** yes (C++ watchdog).
7. **Pilots:** all five A03 fault/control pairs.
8. **One-shot validation:** `A03_STUCK_LIFECYCLE` and `A03_WATCHDOG_EXPIRED` present; `gzip -t` passes; stdout final checksum present; terminal `SDC/ORACLE_FAIL/POST_ORACLE_SIM_HANG`; control `PASS`; `injected_applications` equals the last `FUNNEL` value, not 20000.
9. **Approval:** the terminal reclassification is evidence-based, not a design choice; record it in the decision packet. No workload change.

### R3 — SP05 store-data binding (L-A05, L-B08)

1. **Root cause:** `noteSP05Injection` is not passed `storeWBIt->data()`/`request->_size`, so `FaultStoreEntry.data_fnv` stays empty and `emitChainRecord` honestly writes null.
2. **Why it survived:** the v3.3.2 dossier flagged it as conditional, but the readiness matrix still said `SDC / DIRECT_DATAFLOW_EVIDENCE` without the qualifier.
3. **Correct layer:** `lsq_unit.cc` SP05 branch → `CHAOSPropagation::noteSP05Injection`; recording only.
4. **Affected:** SP05 R01–R05.
5. **Semantics:** unchanged (the store is still completed early; the write is still skipped).
6. **Rebuild:** yes.
7. **Pilots:** all five SP05 fault/control pairs.
8. **One-shot validation:** `store_data_fnv=<16hex>`, `data_correct=0`, `stage_outcome=CHAIN_VISIBILITY_LOST`, `sp05_write_skipped` node, reload hash `a8c7f832281a39c5`, oracle FAIL.
9. **Approval:** none beyond the workload adoption in R8.

### R4 — Control close paths (L-A06; affects all 60 controls)

1. **Root cause:** several injectors gate only on their own mode-specific selector; `probability` is not a universal disable. MD04 reads `--md04_probability` (default 1.0) independently of `--probability`. DA04/LQ04/RP01 never consult `probability`. SQ03/SP05 schedule watchdogs in the constructor even at p=0.
2. **Why it survived:** controls that omit the injector are safe, so no misfire was observed; the hazard is latent and the classification table hid it.
3. **Correct layer:** `configs/se/lsu_proxy.py` mount predicates + an `enabled` gate in each injector, checked before injection, watchdog scheduling and log open.
4. **Affected:** all controls; specifically DA04/MD04/LQ04/RP01/SQ01/SQ03/SP05.
5. **Semantics:** unchanged for fault runs; for controls it guarantees true zero.
6. **Rebuild:** yes if the gate is C++ (preferred); a config-only coupling for MD04 is not sufficient.
7. **Pilots:** all 60 controls.
8. **One-shot validation:** mounting each injector at p=0 yields `injection_count=0`, no watchdog fatal, and `MOUNTED_BUT_DISABLED`; the classification counts are 35/25/0.
9. **Approval:** no.

### R5 — RP01 watchdog evidence and parsing (L-A07, L-D01)

1. **Root cause:** the watchdog marker is in `lsq_fwd_injections.log`; the driver parses `stdout.log`. The raw `fatal` makes `summary.terminal=CRASH`, while the analysis table says `HANG_WATCHDOG`.
2. **Why it survived:** two parsers with different inputs; the propagation table was corrected post hoc but the summary was not.
3. **Correct layer:** `tools/lsu_v332_matrix.py`/`report.py`; `terminal_rules.py`.
4. **Affected:** RP01 R01–R05.
5. **Semantics:** unchanged (the skipped replay is still the fault).
6. **Rebuild:** no.
7. **Pilots:** five RP01 fault/control pairs on the new binary.
8. **One-shot validation:** every summary `terminal=HANG_WATCHDOG`, `watchdog=true`, `deadline_cycles=20000000`, `no_checksum`, with the raw fatal path recorded.
9. **Approval:** no.

### R6 — Chain-scoped propagation and identity (L-A08, L-A09, L-A10, L-C03…L-C09)

1. **Root cause:** the generator used same-`dyn_inst_seq` events only, a tautological Activation, and truncated/mixed identity fields; it treated structural structure as completeness.
2. **Why it survived:** it produced a plausible table and was never cross-checked against the raw consumer fan-out.
3. **Correct layer:** `tools/lsu_v333_propagation.py` (new) + `terminal_rules.py`.
4. **Affected:** all 60.
5. **Semantics:** none.
6. **Rebuild:** no.
7. **Pilots:** regenerate from the new runs.
8. **One-shot validation:** every row has an activation record, a first divergence, a consumer or terminal witness, a commit/squash/hang path, and an oracle/terminal; MASKED rows carry a mechanism; A01-R02 carries `UNRELATED_SQUASH_NO_ARCH_ENTRY`; A01-R03 (pre-fix) carries `INJECTION_NOT_ACTIVATED`.
9. **Approval:** no.

### R7 — Runner, seed/terminal, CSV and provenance plumbing (L-A11, L-D01…L-D16)

1. **Root cause:** multiple small tool defects (argv vs command.txt, shared output paths, dead code, null fields, missing direct-run artifacts, no lock, stale provenance).
2. **Why it survived:** the round's acceptance checked the curated tables, not the producer.
3. **Correct layer:** `tools/lsu_v332_matrix.py`, `tools/lsu_v332_report.py`, `run_pilot.py`, `manifest_validate.py`, provenance/binary copy.
4. **Affected:** all.
5. **Semantics:** none.
6. **Rebuild:** no.
7. **Pilots:** dry-run + full matrix.
8. **One-shot validation:** 0 null seeds/terminals; non-empty FaultCommand; distinct raw/final CSV; 60 mount classifications; 15 direct runs with manifests; provenance cites the v3.3.3 binary.
9. **Approval:** no.

### R8 — Workload identity and frozen-Excel representation (L-B01…L-B09, L-D05, L-D07…L-D10)

1. **Root cause:** the candidate workloads are technically sound but are not represented in the frozen workbook; the inventing rows still carry W3/W6 identities, stale goldens and the design ordinals 1–5.
2. **Why it survived:** the v3.3.2 package kept candidate data in working tables and deliberately did not edit the frozen workbook.
3. **Correct layer:** the v3.3.3 workbook generator, never the frozen file.
4. **Affected:** 30 candidate contexts (FW02/RP01/MD04/SQ01/SQ03/SP05).
5. **Semantics:** unchanged; the ELFs and goldens are frozen by SHA.
6. **Rebuild:** no.
7. **Pilots:** none beyond the matrix.
8. **One-shot validation:** 60/60 authoritative IDs/seeds preserved; 30 override rows explicit; W6/W8 goldens verified correct in v3.2.7; `sq_reload_v3212` row added; design vs executed ordinals separated.
9. **Approval:** yes — workload adoption (see the decision packet).

---

## 2. What can proceed before researcher approval

The following are approval-independent and can be implemented while the packet is pending:

- R3 (SP05 store-data binding; recording only)
- R4 (control close-path gates; no fault-run semantics change)
- R5 (RP01 parsing/normalization)
- R6 (propagation generator corrections)
- R7 (runner/report/provenance fixes)
- R8 tooling side (workbook generator scaffold; no identity freeze)

R1 (PRE retry) and R2 (A03 watchdog/terminal) are implemented in the same build but **the A01/A03 ordinal set is not frozen and the formal matrix is not run** until approval.

## 3. Build and rerun strategy

- One integrated build after R1–R7 are in the tree; save the full log; install to repo-root `build/ARM/gem5.opt`; record SHA.
- Re-census A01/A03 on that binary; verify the other ten models' eligible streams are unchanged (count-only).
- Rerun all 60 fault + 60 control pairs on that binary (4 concurrent max). The binary change invalidates the v3.3.2 evidence for provenance purposes; old evidence is retained under `audit_v3_3_2/` but not spliced into v3.3.3.
- Regenerate tables/Excel from the new runs; run regression; fresh independent acceptance.

## 4. Expected post-fix outcome (prediction, to be verified, not claimed)

- A01: five explainable terminals (SDC/SQUASHED/MASKED); R03 must have writeback/commit evidence. No context is forced to SDC.
- A03: five SDC/oracle-fail with post-oracle simulator hang, full lifecycle and a gzip-valid trace.
- FW02: 4 SDC + 1 MASKED (R03 mechanism-consistent); 5/5 controls PASS.
- FW05/LP01/DA04/SQ01: 5/5 SDC.
- SQ03: 5/5 MASKED / visibility-timing shift (4 moved + 1 lifecycle-only).
- SP05: 5/5 SDC with a complete store-data chain.
- MD04: 4 SDC + 1 MASKED (R01 inert-after-completion).
- LQ04: 5/5 MASKED (entry invalidated/restored).
- RP01: 5/5 HANG_WATCHDOG with internal watchdog and no checksum.

Any deviation is reported, not normalized.

## 5. Residual risks

- The A01/A03 re-census may produce a different N and therefore different percentile ordinals; the five contexts remain seeds-frozen but the exact instructions change. This is the main approval item.
- The PRE retry guard affects the broader PRE family; regression tests must not silently update their expectations without documenting the change.
- The A03 watchdog budget must be long enough for the workload to reach its final `put_hex` on a loaded host. The driver should derive it from the control completion tick with a safety factor and record the value.
- The SP05 store-data hash is recording-only; if the SQ entry data has already been released by the time the branch runs, the hash stays null and the row must remain `RELOAD_UNVERIFIABLE` (no fabricated value).

---

## 6. Ledger traceability

The 46 rows in `LSU_v3.3.3_Master_Defect_Ledger.csv` map to the clusters above:

| Cluster | IssueIDs |
|---|---|
| R1 | L-A01, L-A10, L-A11 |
| R2 | L-A02, L-A03, L-A04, L-C01 |
| R3 | L-A05, L-B08 |
| R4 | L-A06 |
| R5 | L-A07, L-D01 |
| R6 | L-A08, L-A09, L-C03…L-C09 |
| R7 | L-C02, L-D02…L-D16 |
| R8 | L-B01…L-B09, L-D05, L-D07…L-D10 |

`L-D17` is a positive provenance check, not a defect.

Every ledger row carries a raw evidence path; no row was created from a summary table alone.
