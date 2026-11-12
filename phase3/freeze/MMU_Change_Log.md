# MMU Formal Freeze — Change Log (2026-11-12)

Workspace: `/home/sdc/gem5-fi-mmu-impl-v2`. Original `/home/sdc/gem5-fi-mmu` was
not modified. No formal SampleRunID was launched.

## Authority / configuration

1. Created the frozen workbook
   `phase3/freeze/authority/gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx`
   from the read-only design package: 40 SampleRunIDs set to `FROZEN`,
   Seed set to the literal text `N/A_DETERMINISTIC` (number format `@`),
   SeedPolicy=DETERMINISTIC, SeedSource=RESEARCHER_APPROVED,
   SampleFreezeStatus=FROZEN. The source workbook is untouched.
2. Created `MMU_40_Sample_Matrix.csv`, `MMU_Formal_Config.json/.yaml`; the
   config now carries the frozen binary/source/workload SHA256 values, not
   PENDING placeholders.
3. Seed audit: no real nondeterministic source on the MMU path (LRURP,
   StridePrefetcher without RNG, TournamentBP, fixed checkpoint, fixed-VA
   static workloads; the only global-RNG consumer is the O3 SMT fetch pick
   with num_cores=1). The runner refuses any `--*seed*` gem5 flag.

## Runner / preflight / validator

4. `tools/mmu_formal_preflight.py`:
   - frozen-authority default resolution + `BLOCKED_SEED_POLICY`;
   - runtime evidence is now part of the PRIMARY status (no static-only
     READY); TraceCompleteness (not PropagationStatus) is the trace gate, so
     a legitimate SQUASHED/DETECTED_CONTAINED row is not blocked for the
     expected PARTIAL propagation;
   - build-provenance gate now hashes the REAL pilot manifest from the
     evidence index, not `runs/<formal SampleRunID>/` (which does not exist
     before the formal run), and a missing manifest is `BLOCKED_BINARY`;
   - workload resolution: live `workloads/mmu/<W>` first, except W9, whose
     canonical ASID table (220/224/228/232/236) belongs to the mmu_rev W9
     build (the live rebuild uses 234–250).
5. `tools/mmu_formal_runner.py`:
   - records `gem5_sha256`, six source SHA256 (including CHAOSPropagation),
     `workload_sha256`, control-oracle SHA256, and fails closed on a
     plan-vs-execution hash change;
   - waits for `prop_evt.txt.gz` size+mtime stability before validation,
     retries once, and records `trace_read_error`;
   - W9 and W10 rcS embed the canonical binary payloads (no stale guest-disk
     binary); W9 runs all five contexts so the authoritative ASIDs are
     assigned in order; W10 uses `--ctx R0x` with the fixed VA index.
6. `tools/mmu_trace_validate_v3.py`: fixed `UnboundLocalError` when a chain
   has no resolvable W9 ASID/W10 VA (record `ctx=""`, basis `unresolved`).
7. `tools/mmu_formal_validate.py`: removed the blanket
   "Execute => COMPLETE" shortcut that hid missing causal kinds; fixed the
   all-digit hex PA comparison in `_cross_dynamic_wrong_commit` (trace `pa`
   fields are unprefixed hex).

## C++ (one patch unit)

8. `mmu.cc` + `CHAOSPropagation.{hh,cc}`: added `mmuSeqSquashed(seq)` and
   gated the M08 one-shot on it. An already-squashed wrong-path translation
   no longer burns the injection; the first live translation of the target
   is corrupted instead. Fault site, PA-only corruption and SDC semantics
   are unchanged. Final binary `a71ce0ca…` (BUILD_RC=0,
   `phase3/freeze/build_m08_gate.log`).

## Workloads

9. W10: fixed `--ctx R0x` always using VA index 0; embedded the live binary
   in `configs/fs/mmu_w10_run.rcS`.
10. W10S: cold-mode target mmap immediately before the STRB; all printf
    moved after the store (removes the wrong-path `__strlen_asimd` target
    fill that made the store hit a stale TLB entry).
11. W13: added a fresh `+0x1000` alias consumer in the same 2 MiB region,
    accessed BEFORE the guest TLBI. The alias has a populated PTE but no
    complete TLB entry, so it resumes from the corrupted L2 partial entry
    and returns the decoy sentinel. Historical W13 binary preserved in
    `phase3/freeze/evidence/legacy_bins/mmu_w13.bak`.
12. W14: R02 uses `LDADDAL` (LSE AMO) so the translation class is genuinely
    Atomic; every context maps RW+MAP_POPULATE, touches the page, then
    mprotects to the restricted protection, so the PTE is present.
    Historical W14 binary preserved in the legacy_bins directory.
13. Base rcS templates `mmu_w10_run.rcS`, `mmu_w13_run.rcS`,
    `mmu_w14_run.rcS`, `mmu_w10s_run.rcS` embed the frozen binaries.

## Evidence handling

14. Every old run directory is preserved. Failed runs (e.g.
    `TEST-M06-R02B`, gem5 exit 124) are kept. Two stale verdicts
    (`TEST-M06-R05B`, `TEST-M08-R03`) were produced on a live gzip stream;
    their complete traces were revalidated into
    `phase3/freeze/evidence/reval/`.
15. Metadata corrections are explicit in the manifests
    (`workload_sha256_recorded_pre_fix`, `source_sha256_note`), never silent.

## Second pass — M07 R03/R05 researcher-approved context text (2026-11-12)

Exact strings delivered by Agent C in `phase3/final/C_M07.md` §4 and applied
verbatim by Agent E to the frozen authority (`07_Sample_Matrix`, the CSV
mirror and `MMU_Formal_Config.json/.yaml`). ModelID, WorkloadID, SampleRunID,
the 40-sample count, Seed, SeedPolicy, SeedSource and SampleFreezeStatus are
unchanged. A machine-readable record is in
`phase3/final/M07_CONTEXT_CHANGES.json`; the workbook carries a dedicated
`17_M07_Context_Change_Record` sheet with one row per changed column.

### M07-F0-W14-S01-R03

| Column | Before | After |
|---|---|---|
| DynamicContext | EL0 read through PROT_NONE | EL0 load through an execute-only (PROT_EXEC) user mapping; valid PAGE_EXECONLY leaf with AP[2:1] denying EL0 read and UXN=0 (requires runtime FEAT_EPAN) |
| TargetVA | PROT_NONE VA | execute-only VA 0x400d200000 |
| AccessMode | Read | Read |
| TargetEvent | target permission decision with normal grant=false | target EL0 load permission decision with normal grant=false (AP[2:1] denies EL0 read on a valid leaf) |
| TargetInstruction | EL0 store through read-only alias (primary); additional read/atomic/execute contexts. | EL0 load from execute-only mapping (valid PAGE_EXECONLY descriptor; denied by AP, not by translation) |
| OracleMethod | W14: baseline RO store faults; injected store succeeds and writable alias observes the changed value. | W14: no-fault execute-only load faults with SEGV_ACCERR on a valid AP-deny leaf; injected load returns sentinel byte 0x88; trace pte_decode L3 Page must show AP not granting EL0 read and descriptor_type=Page. |

- Reason: PROT_NONE clears PTE_VALID, so the walker raises a Translation
  fault before `checkPermissions64`; PROT_EXEC-only preserves the M07
  grant-inversion mechanism.
- Approval basis: researcher-approved 2026-11-12; exact text from Agent C.
- Workload: W14 (binary SHA256 f15dc78e...). Golden:
  `runs/TEST-F1-CTRL2-W14-R03/Run_Log/golden_output.txt` (SEGV_ACCERR on a
  VALID L3 leaf with AP=0b10, AF=1, UXN=0).
- Trace / final verification: READY. `TEST-F1B-M07-R03`
  ACTIVATED/CONSUMED/FULL/COMPLETE/SDC/FAIL; the inverted grant commits the
  EL0 load (`observed=0x88`, `injected_success=1`).

### M07-F0-W14-S01-R05

| Column | Before | After |
|---|---|---|
| DynamicContext | EL0 fetch from PROT_NONE mapping | EL0 instruction fetch through a valid XN user mapping (PROT_READ, PTE UXN=1) entered by an indirect branch (br xN, target loaded at run time from a table) |
| TargetVA | PROT_NONE VA | XN indirect-branch code VA 0x400d600180 |
| AccessMode | Execute | Execute |
| TargetEvent | target permission decision with normal grant=false | target EL0 instruction-fetch permission decision with normal grant=false (UXN=1 on a valid leaf) |
| TargetInstruction | EL0 store through read-only alias (primary); additional read/atomic/execute contexts. | EL0 indirect-branch fetch into an XN page (br xN; target from runtime table; distinct VA/code blob/consumer/marker from R04) |
| OracleMethod | W14: baseline RO store faults; injected store succeeds and writable alias observes the changed value. | W14: no-fault XN fetch faults with SEGV_ACCERR on a valid UXN=1 leaf; injected fetch executes the R05 code blob and returns marker 0x5a; trace pte_decode L3 Page must show UXN=1. |

- Reason: a valid XN mapping entered by a runtime indirect branch is a
  distinct permission-denial context from R04; the old PROT_NONE fetch was a
  translation fault and not a distinct M07 realization.
- Approval basis: researcher-approved 2026-11-12; exact text from Agent C.
- Workload: W14 (binary SHA256 f15dc78e...). Golden:
  `runs/TEST-F1-CTRL2-W14-R05/Run_Log/golden_output.txt` (SEGV_ACCERR at
  0x400d600180, UXN=1 on a VALID leaf).
- Trace / final verification: READY. `TEST-F1-M07-R05`
  ACTIVATED/CONSUMED/FULL/COMPLETE/SDC/FAIL; the inverted grant executes the
  indirect-branch target (marker 0x5a).

No authoritative row was renumbered, deleted or added.


## v2.2-FINAL — 2026-11-12 formal closure round

- Platform: one final binary `b3eb1559...` built from closure commit
  `69f0a202...` (base commit for pilot provenance `f24b6b77...`).
- Platform capability: FEAT_EPAN advertised (ID_AA64MMFR1_EL1.PAN=3) so the
  approved M07 R03 execute-only mapping is a real AP=0b10 EL0 denial. Scope
  is execute-only user mappings only; read/execute and read-only mappings
  are unchanged.
- Checkpoint: `runs/mmu_bootF1/cpt.244799013609` (digest
  `4aa1ba38...`), created on the final binary; every F1 control and pilot
  restores from it.
- Workloads: W10 per-context target VAs (733b8a80...), W10S runtime
  --target-va (fede5f3e...), W14 R03/R05 realizations (f15dc78e...).
- Evidence: 40/40 contexts re-run on the final binary with per-context
  independent no-fault controls; every trace is COMPLETE, every terminal is
  admissible (M01/M02/M04/M05/M07/M08 SDC; M03 R01-R04 SQUASHED/PASS, R05
  SDC; M06 DETECTED_CONTAINED).
- Validator corrections (evidence joins, not threshold lowering): M01 origin
  suppression ancestor, M02 insert-time walk identity, M03/M04 IFU
  injected-PA join, M05 Execute IFU path, M07 activation decision witness,
  M06 delivery requirement; translation_start is a transaction root.
- Preflight: 40/40 READY; seed literal N/A_DETERMINISTIC (0 gate failures);
  binary/source provenance PASS.

## v2.3 — 2026-11-12 evidence closure and package correction

- **No C++ change, no rebuild.** The frozen binary remains
  `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`;
  all 40 pilots and controls keep one version.
- **Strict identity chains replace `consumed_at_activation` for the five
  instruction-side contexts** (`tools/mmu_evidence_chain.py`):
  - M03 R05: candidate l2_shared entry 253/51 (ASID 236) -> fault-tagged
    lookup 253/51 -> ITLB insert -> translation_result 253/51 ->
    `lsu_request(mode=Execute)` event 299, PA 0x83543000.
  - M04 R05: activation mutates `itb:173:540`; the later
    translation_result names the same entry and emits PA 0x8353c000 ->
    `lsu_request(mode=Execute)` event 485. The C++ consumer counter is 0
    because the synthetic IFU transaction is not registered; the proof is
    the entry lifetime identity.
  - M05 R05: faulted partial insert 230 -> `fault_entry_consume` 245
    (source=230, lookup=244) -> PTW -> decoy leaf -> result 255 ->
    `lsu_request(mode=Execute)` event 256.
  - M07 R04/R05: `permission_eval` deny at the same tick/VA/mode -> activation
    inversion (the fetch row has translation_id=0) -> translation_result and
    `lsu_request(mode=Execute)` on the same transaction, events 355/356 and
    333/334. The join is a co-temporal key match, never event order.
- The validator now reports FaultActivated / FaultStateConsumed /
  PropagationComplete / TerminalState separately and never emits an empty
  `required_kinds`.
- **Authority correction:** M07 R04 TargetVA/TargetEvent/TargetInstruction/
  OracleMethod/ExpectedPropagationPath now match the frozen
  `EL0 execute from XN mapping` context (marker 0xc7); M02 R01–R05
  OracleMethod now states the final control PFN `0x834b2 -> 0x834b3`
  (event 4424). The stale Golden Control Report `0x834b6` sentence is
  corrected. SampleRunIDs, contexts, counts and `N/A_DETERMINISTIC` seeds
  are unchanged.
- **Package v2** physically includes the authoritative Excel and five causal
  slices (raw PROP-EVT lines + JSON + Markdown), five verdict JSONs and five
  pilot manifests. Each slice records the instrumentation boundary: the
  frozen binary emits no per-instruction fetch-response/decode/commit row for
  a synthetic IFU transaction; execution is proven by the guest oracle marker
  tied to the fetched PA/code page.
- Preflight: 40/40 READY; no formal SampleRunID was launched.
