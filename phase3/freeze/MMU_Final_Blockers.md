# MMU Final Blockers (2026-11-12)

Frozen binary: `a71ce0ca21de143d9aa5ab05e29d9bee86dff213576941a3191a256f1d842024`
Workspace: `/home/sdc/gem5-fi-mmu-impl-v2` (original workspace untouched).
No formal SampleRunID was launched. Every run below is a TEST-ID pilot.

## Blockers that prevent `MMU_FORMAL_READINESS = READY`

### B1 — M07 R03 (PROT_NONE read) is a translation fault, not a permission decision
- Run `TEST-M07-R03B` (final binary, new W14 that maps RW+touch then
  `mprotect(PROT_NONE)`): `ActivationStatus=NO_ELIGIBLE_EVENT`,
  `TerminalState=NO_ELIGIBLE_EVENT`, trace has no `permission_eval`.
- Root cause: arm64 `PAGE_NONE` clears `PTE_VALID`
  (`/usr/src/kernels/5.10.../arch/arm64/include/asm/pgtable-prot.h:84`), so
  the walker raises `TranslationLL` before `MMU::checkPermissions64`.
  M07 inverts an *existing permission grant decision*; with an invalid
  descriptor there is no such decision to invert. Fabricating one would be a
  different fault model.
- Minimal fix (requires researcher approval because it changes the
  protection class in the R03 context): map the page `PROT_EXEC`
  (execute-only, `PAGE_EXECONLY`: valid, AP=00, UXN=0) and perform the EL0
  load. The load then reaches `checkPermissions64` and is denied by AP,
  which is the same M07 mechanism. No C++ change is needed.
- Do not mark `NO_ELIGIBLE_EVENT` as PASS.

### B2 — M07 R05 (PROT_NONE fetch) has no distinct M07 realization
- `TEST-M07-R05` / `TEST-M07-R05B`-class runs: the PROT_NONE fetch walks an
  invalid descriptor (`pte_value=0`, `descriptor_type=Invalid`), i.e. a
  Translation fault. The only valid-descriptor execute denial is XN, which
  is exactly R04 (already COMPLETE/SDC).
- A walker-side "grant inversion" for an invalid descriptor would have to
  invent a valid translation, which is not M07.
- Minimal fix: researcher decision to (a) repurpose R05 as a distinct valid
  permission class (e.g. a second XN VA with a different consumer), or
  (b) accept R05 as a duplicate of R04 and record it as
  `BLOCKED_CONTEXT`. The authoritative Excel must not be changed silently.

### B3 — M05 R05 (Execute) has a real guest SDC but an incomplete trace
- `TEST-M05-R05B` (new W13 alias-code consumer): the guest observed
  `0x51` (decoy) instead of `0x7d`, so the architectural fault is real, but
  `TraceCompleteness=PARTIAL/TRACE_INCOMPLETE` because the Execute-mode
  lookup has no inst-seq transaction: no `partial_entry_insert`,
  `translation_result`, or `lsu_request` events are emitted for the fetch.
- Minimal fix (observability only, no fault-semantics change): open a
  synthetic per-miss transaction for Execute-mode lookups when
  `hasInstSeqNum()==false`, so the fetch walk can be tagged and joined.
  This is the fix sketched in `phase3/freeze/agents/A_M05_M06.md` §1.7.
  It needs a new build and a rerun of R05.
- Do not accept the SDC on the guest output alone.

### B4 — M04 SDC proof lacks a committed wrong-PA witness
- `TEST-M04-FR01..FR05`: the guest reads the decoy sentinel (`0x51`) and the
  control differs, so the architectural SDC is real, but the fault-tagged
  trace branch ends in `squash` (FR01) or only has entry-lifetime reuses
  (FR05); `_cross_dynamic_wrong_commit()` returns false (no committed
  access carrying the injected PA across the squash).
- Current validator terminal `SDC` relies on entry-lifetime consumption +
  oracle diff. A stricter reading of "traceable propagation chain" wants a
  commit/writeback witness for the injected PA.
- Minimal fix: either add a committed-consumer trace join for the replayed
  instruction (observability) or document M04 as `SDC` with a
  `TRACE_PARTIAL` caveat. Do not silently claim COMPLETE propagation.

### B5 — Historical M01–M04 evidence is not on the frozen binary
- M01/M02 five-context evidence: Phase 2.1 (`bea5f813`), M01/M02 R01 only in
  phase2_2; M03 R01/R02 on `6dca2195`; M04 FR01–FR05 on `3ec51b2c`; controls
  on older binaries. None is on `a71ce0ca` and no historical manifest records
  a binary SHA.
- The new preflight emits `BLOCKED_BINARY`/`BLOCKED_SOURCE` for such rows.
- Minimal fix: rerun the affected contexts on `a71ce0ca` (the runner now
  records `gem5_sha256`, `source_sha256`, `workload_sha256`), or freeze an
  explicit source-invariance argument for models untouched by this round's
  C++ (M01–M04 paths do not execute the M08 gate). The task's own rule
  requires the final binary for all models, so reruns are the clean answer.

### B6 — Pending reruns on the frozen binary
At the time of writing, these were still in progress or not rerun:
M06 R03/R04/R05, M07 R05, M08 R01/R05, M01/M02 five contexts, M03 R01/R02,
M04 controls. Their old verdicts remain in `runs/` untouched; do not treat
them as frozen-binary evidence.

## What is already proven on the frozen binary

- M05 R01–R04: ACTIVATED / CONSUMED / COMPLETE / SDC / FAIL, with a real
  partial-entry hit on the substituted base (`pfn=0x81c1f000`) and a decoy
  PTE read (see `TEST-M05-R01B..R04B`).
- M06 R01/R02: ACTIVATED / CONSUMED / COMPLETE / DETECTED_CONTAINED /
  PASS_EXPECTED_DETECTION. R02 now performs a real cold **Write** L0..L3
  walk (the prior wrong-path `__strlen_asimd` fill was removed).
- M07 R01/R02/R04: ACTIVATED / CONSUMED / COMPLETE / SDC / FAIL. R02 uses
  `LDADDAL` (LSE AMO) and changes the read-only shared value
  (`shared_changed=1`).
- M08 R02–R04: ACTIVATED / CONSUMED / COMPLETE / SQUASHED / PASS. The M08
  one-shot now skips an already-squashed translation (R02 moved from the
  dead seq 99901600 to the live seq 206159145 and carried PA
  `0x834b7000` into the LSU; the guest observed the clean value).

## Additional findings from the final regression runs

### B7 — M02 R02 target PFN is hardcoded and no longer matches
`TEST-M02-R02B` (frozen binary, scoped R02, target VA 0x4001100000) ended
`NO_ELIGIBLE_EVENT`. The guest's W10 target PFN is `0x834b6`
(`target_pfn=0x834b6`), but `tools/mmu_formal_runner.py` still passes
`--mmu_m02_old_pfn 0x83480` (the PFN of the historical control run). The M02
refill hook therefore never matches. Minimal fix: resolve `old_pfn` from the
independent W10 control/manifest at plan time (the preflight already parses
`target_pfn` for W12 decoys) instead of a constant. This is a runner/config
fix, not a model change. Do not mark the sample PASS.

### B8 — W9/M01 ASID assignment is process-order dependent
The canonical M01 ASIDs 220/224/228/232/236 are produced only when the
guest-disk `/root/mmu_w9` is run directly for all five contexts. Embedding
the binary and decoding it in the rcS forks extra shell processes that move
the workload to ASIDs 234/238/242/246/250
(measured `TEST-M01-R02C`/`R02D`), so the M01 target ASID is unreachable.
`TEST-M01-R02E` uses the historical shape (`/root/mmu_w9` loop) and is
READY: ASIDs 220–236, `ctx=R02 observed=0xaa result=FAIL`,
`TerminalState=SQUASHED, OracleResult=FAIL`. The executed guest binary is
the disk copy; the host canonical source-identical build is
`workloads/mmu_rev/W9/Binary/mmu_w9` SHA256 `ec5256…` (recorded in the
manifest/config). A future formal runner should either pin the disk image
hash or place the frozen W9 binary in the image at build time.

### B9 — M03/M04 evidence is not on the frozen binary
All five M03 and all five M04 contexts have real per-context evidence, but
they ran on `6dca2195…`/`3ec51b2c…`, not on the frozen `a71ce0ca…`. The
preflight reports `BLOCKED_BINARY` for all ten. Minimal fix: rerun the ten
contexts on `a71ce0ca…` (the runner now records the hashes). The M03 R05
`Execute` COMPLETE shortcut was removed, so a rerun may also require the
Execute trace transaction (B3) if the fetch path still lacks causal kinds.

### B10 — Controls are independent but mostly on older binaries
The per-context W12 controls, the W11 closure control, the W13/W10S/W10
controls, and the W14 control were run on older binaries. Their no-fault
golden values are architecture-level sentinels and remain valid as
independent oracles, but a stricter freeze should rerun one control per
workload on `a71ce0ca…`. This is recorded, not hidden.
