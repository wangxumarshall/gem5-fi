# MMU Pre-Formal Closure — Final Readiness

Date: 2026-11-11
Final binary: `CHAOS/gem5/build/ARM/gem5.opt`
SHA256 `3ec51b2cbfe1cbd743862eb4b260bb05da9bebc3b8e63e75578662b2ad3359e6`
Build: `phase3_build_closure_final.log`, `BUILD_RC=0`, 0 errors, no warnings in
the changed files.
No formal sample was executed; all runs are TEST-ID pilots/controls.

## 1. Context matrix (real final-binary evidence)

| Model | R01 | R02 | R03 | R04 | R05 | Readiness |
|---|---|---|---|---|---|---|
| M01 | PASS (SDC) | phase2_2 (reused) | phase2_2 (reused) | phase2_2 (reused) | phase2_2 (reused) | **READY** (reused 5/5 + final R01) |
| M02 | PASS (SDC) | phase2_2 (reused) | phase2_2 (reused) | phase2_2 (reused) | phase2_2 (reused) | **READY** (reused 5/5 + final R01) |
| M03 | PASS (SQUASHED) | PASS (SQUASHED) | PASS (SQUASHED) | PASS (SQUASHED) | PASS (SDC/FAIL) | **READY** |
| M04 | PASS (SDC) | PASS (SDC) | PASS (SDC) | PASS (SDC) | PASS (SDC) | **READY** |
| M05 | PARTIAL (MASKED) | PARTIAL (MASKED) | PARTIAL (trace truncated) | PARTIAL (trace truncated) | PARTIAL (trace truncated) | **PARTIAL** |
| M06 | PASS (CONTAINED) | NOT_RUN (no cold walk) | PASS (CONTAINED) | PASS (CONTAINED) | PARTIAL (trace incompl.) | **PARTIAL** |
| M07 | PASS (SDC) | NOT_RUN (Atomic hook gap) | NOT_RUN (PROT_NONE hook gap) | PASS (SDC) | NOT_RUN (PROT_NONE hole) | **PARTIAL** |
| M08 | PASS (SDC) | PARTIAL (speculative) | PARTIAL (speculative) | PARTIAL (speculative) | PASS (SDC, W10S) | **PARTIAL** |

`PASS` means: activation, real consumption/propagation where the model has a
consumer, a complete trace, an allowed terminal, and the correct oracle
result. See `evidence_index.json` and each run's `Validation/verdict.json`.

## 2. Model outcomes (what is actually proven)

### M03 — READY
`TEST-M03-R01..R05`, W11 handshake (`mprotect`-forced re-lookup). Every
context activates on a real `l2_shared` foreign-ASID candidate (requester
ASID 238, candidate ASID 236, candidate PFN 0x83544). R01-R04 squash the
false-hit load (allowed terminal, guest masked). R05 (ITLB) executes the
foreign code page: `observed=0xa5`, TerminalState=SDC, oracle FAIL.

### M04 — READY
`TEST-M04-FR01..FR05`, W12. Fail-closed decoy validation against the
per-context scoped control (`0x83557`). All five contexts:
resident entry `0x8353e → 0x83557`, alias lineage
`dtb:82:3276 → l2_shared:900:11`, guest observes the decoy sentinel
(`0x51`), TerminalState=SDC, Propagation=FULL, Trace=COMPLETE. R05 fixes the
ITLB sequence gate and executes the decoy code page.

### M05 — PARTIAL (real finding)
`TEST-M05-R01..R05`, W13. Activation uses the workload-owned decoy VA
(`0x4010200000`) and substitutes the L2 next-table base
(`0x81c4d000 → 0x81c1f000`). The guest `mprotect` range TLBI then invalidates
the corrupted partial entry (events 828/829, page_size_n=21) before the
target access; later partial hits use a clean re-inserted entry. R01/R02 are
ACTIVATED_MASKED / NOT_CONSUMED with COMPLETE traces; R03-R05 traces are
truncated on disk (validator TRACE_INCOMPLETE). No SDC is claimed.

### M06 — PARTIAL
`TEST-M06-R01/R03B/R04B` are DETECTED_CONTAINED with separated evidence:
`fault_state_consumed` (Invalid decode) → `fault_result_propagated`
(TranslationLL) → `exception_delivery` (Data abort, OS/EL1) → squash;
the PTE re-read is clean (`...c3`, Page). R02 (W10S cold store) does not
walk: an earlier Read already filled the TLB, so the store hits and M06
never sees an L3 descriptor. R05's trace is truncated. No SDC is claimed.

### M07 — PARTIAL
R01 (RO store) and R04 (XN execute) activate and produce SDC
(`shared_changed=1`; JIT code `0xc7` executed). R02 (Atomic), R03
(PROT_NONE read) and R05 (PROT_NONE fetch) produce no `checkPermissions64`
decision: the atomic store denial and PROT_NONE faults are generated before
the hook site (walker/AP/XN). R05's trace is truncated.

### M08 — PARTIAL
R01 (`observed=0x51`) and R05/W10S (`target=0x7d`, neighbor alias `0xab`,
`m08_redirect_signature=1`) are SDC with the TLB entry unchanged
(`old_pfn == new_pfn`) and only the request PA changed. R02-R04 activate but
the injected request does not reach the consumed load (speculative
translation), so the traces are TRACE_INCOMPLETE. No SDC is claimed there.

## 3. 40-sample preflight

`phase3/formal/final/MMU_40_Sample_DryRun.csv`:
- 40 samples, 0 triple issues.
- Static checks (hook/workload/context/config/trace/oracle) all pass.
- Runtime evidence columns carry the real verdicts above.
- Remaining blockers, exactly the researcher-owned ones:
  - **BLOCKED_SAMPLE_ID_NOT_FROZEN: 40/40** (SampleIDStatus is
    PROPOSED_NOT_FROZEN; the runner refuses before any formal run).
  - **BLOCKED_MISSING_SEED: 40/40** (Seed = NEEDS_AUTHORITATIVE_EXCEL; no
    seed was generated or defaulted).

## 4. MMU_FORMAL_READINESS

**PARTIAL.** M01-M04 are READY. M05-M08 have real, evidence-backed partial
coverage. Formal READY cannot be claimed until:
1. The researcher freezes all 40 SampleRunIDs.
2. The researcher decides the seed semantics (`N/A_DETERMINISTIC` is
   recommended; see `Seed_Semantics_Audit.md`).
3. M05 R03-R05 traces are re-captured without truncation (workload/trace
   flush), M06 R02 gets a true cold-write walk, M07 R02/R03/R05 get a hook at
   the pre-`checkPermissions64` permission-fault site, and M08 R02-R04 are
   re-targeted to a non-speculative consumed translation.
4. The authoritative Excel ExpectedTerminalStates for M06 is updated to
   include SQUASHED (proposal in `phase3/m06/M06_TERMINAL_PROPOSAL.md`).

## 5. Real findings that changed the plan

- Scoped W12 controls changed the decoy PFN (`0x83557`, not the `--all`
  value `0x83575`); fail-closed validation caught it.
- W10 `--ctx R0x` still uses loop index 0, so scoped W10 runs always target
  `0x4001000000`; the correct formal shape is `--ctx all` + per-context
  target VA (used for M06/M08 R02-R05).
- M05's intended leaf-only TLBI is not what Linux `mprotect` emits; the range
  TLBI kills the partial entry, containing the fault.
- M07's hook only covers the AP read-only/write path; PROT_NONE/XN faults are
  raised earlier.
- M08's first completed translation can be speculative; the consumed load may
  use a different translation.
