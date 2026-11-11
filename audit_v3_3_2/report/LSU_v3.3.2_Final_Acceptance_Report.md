# LSU v3.3.2 — Final Acceptance Report

**Date:** 2026-11-11
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Final source HEAD:** `fc60822408cbb3f5af4788bd99fc82c114917367`
**Final binary SHA256:** `070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca`
**Scope:** 12 models × R01–R05 = 60 contexts; 60 fault runs + 60 matched controls.
**Final status:** **`PARTIALLY_READY`** · `12_MODEL_FORMAL_READY = NO`

---

## 1. Headline

This round moved from v3.3.1's 40/60 mapped contexts and 2/60 valid controls to:

- **60/60 contexts mapped** on the final binary (30 on frozen formal workloads,
  30 on candidate workloads awaiting researcher approval).
- **60/60 fault runs injected** (A03's persistent F5 fault is capped at
  20,000 applications by the new log cap; RP01's single skip is explicit).
- **60/60 controls with zero injection**, every one with a real artifact
  (injector absent from the command, or a mounted p=0 injector reporting
  `injected=0`), and every control oracle passing.
- **60/60 causal rows** with an observed injection identity and an honest
  terminal/evidence class (48 DIRECT_DATAFLOW, 5 HANG_PARTIAL, 5
  DIRECT_SKIP_AND_WATCHDOG, 2 INDIRECT).
- All five P0 defects have a concrete fix and dynamic evidence; the remaining
  blockers are approval/evidence gaps, not missing implementation.

**Why not READY:** 30 contexts use candidate workloads (FW02 W4-v2, RP01
partial-overlap, MD04 violation workload, and SQ01/SQ03/SP05 `sq_reload_v3212`)
that are **not approved or frozen**; `ConfigFrozen=NO`; A01-R03 is honestly
UNRESOLVED; A03's persistent fault produces partial traces (no in-simulator
watchdog); SP05's `store_data_fnv` is still null. A formal campaign therefore
must not start yet.

---

## 2. Answers to the 15 required questions

### Q1. Do all 12 models have the correct fault-injection semantics?
**Yes at the hook level, with two observation gaps.** The 12 hooks execute and
inject on the intended site (source audit `LSU_12Model_Source_Hook_Audit.csv`).
A03's semantics are now documented as **one persistent fault with five
observation points**, not five transient injections; LP01 now binds the fault
to PC/VA/dyn-inst identity. SP05's store-data hash is still null, so its
"store data → visibility" edge is partially inferential.

### Q2. Are all 60 contexts inside the correct ROI?
**Yes by the measured eligible-event definition.** ROI windows and N:
A01/A03 1040–1234 (N=195), FW02 8–67 (N=60), FW05 1–2000 (N=2000),
SQ 1006/1009/940 +127 (N=128), DA04 33–1056 (N=1024), LP01 886–17525
(N=16640), MD04 3–10 (N=8), LQ04 1–5 (N=5), RP01 1–255 (N=255).
Every absolute ordinal satisfies `start + ceil(p·N) − 1`; Agent F caught and
we fixed an FW02 offset error (R02–R05 corrected to 25/37/49/61 and rerun).

### Q3. Are R01–R05 genuinely different dynamic contexts?
**Yes.** All 60 identity tuples are distinct within their model; 0/60 collapse.
The identities include dyn-inst seq, PC, VA/PA or LQ entry, and generation.
A03's five are distinct observation points of one persistent fault (explicitly
labelled); FW05 R01/R05 reuse one buffer address but differ in dynamic
seq/iteration; LQ04 uses the five designed `_start` anchor loads.

### Q4. Which models still have target-event eligibility problems?
- **A01-R03**: injection and a complete trace, but no register-writeback
  divergence evidence → `UNRESOLVED` (not relabelled MASKED/SDC).
- **SP05**: `store_data_fnv` is null → `RELOAD_UNVERIFIABLE` qualifier even
  though all five runs show reload/consumer SDC and oracle failure.
- **A03**: the persistent stuck-at fault can corrupt control flow and hang;
  five contexts are HANG with partial logs (external 30 s bound), not complete
  traces. Activation and first-affected events are recorded.
- **RP01**: all five are HANG by the in-simulator watchdog; no SDC claim.

### Q5. Which workloads are proven by disassembly and dynamic execution?
- W4 candidate `sq_forward_w4v2`: 10 loads / 12 stores in main; full-overlap
  `str`/`ldr` and 8B-store/4B-load partial pairs; host/gem5 checksum
  `1f4cbf14327717df` (frozen W4 golden); FW02 observed 67 in-main forwards and
  ordinal-50 fault changes the oracle.
- RP01 `replay_partial_v332`: 8B store + 4B load at +6 (2B overlap); 260
  count-only eligible events, 255 in main; five percentile contexts distinct.
- MD04 `md04_violations_v332`: 8 in-main violation pairs (11 total = 2 libc +
  8 main + 1 printf); ordinal-3 probe at `load_pc=0x4005ec`.
- A01/A03 (`agu_addrmodes`), FW05 (`fw05_forward`), SQ (`sq_reload_v3212`),
  DA04 (`alignment`), LP01 (`load_response`), LQ04 (`lq_lifetime_ordinal`)
  are proven by their own disassembly/trace evidence.

### Q6. What is the final SQ01/SQ03/SP05 plan, and is it approved?
**Not approved; recommended for approval.**
- SQ01: ADOPT `sq_reload_v3212` — 5/5 SDC, `mem_write_hash ==
  reload_data_hash == consumer_hash`.
- SQ03: CONDITIONAL ADOPT — 5/5 MASKED, `CHAIN_VISIBILITY_MOVED` in 4/5 and
  `LIFECYCLE_ONLY` in 1/5; this is a visibility-timing outcome, **not SDC**.
- SP05: CONDITIONAL ADOPT — 5/5 SDC with reload/consumer/oracle failure, but
  `store_data_fnv=null` must be wired before inclusion.
The dossier is `audit_v3_3_2/sq_workload/LSU_SQ_Workload_Decision.md`.

### Q7. Does each context's chain run from injection to an application or terminal node?
**48/60 have direct dataflow evidence; 10/60 have the expected terminal-type
evidence; 2/60 are indirect.** Specifically: 36 SDC, 12 MASKED, 1 SQUASHED,
5 HANG_TIMEOUT (A03), 5 HANG_WATCHDOG (RP01), 1 UNRESOLVED. No context is
silently claimed complete.

### Q8. Which samples are SDC / Masked / Squashed / Crash / Hang?
- SDC 36: A01 3, FW02 4, FW05 5, SQ01 5, SP05 5, DA04 5, LP01 5, MD04 4.
- MASKED 12: FW02 R03, SQ03 5, MD04 R01, LQ04 5.
- SQUASHED 1: A01 R02.
- HANG 10: A03 5 (timeout/partial), RP01 5 (in-simulator watchdog).
- UNRESOLVED 1: A01 R03.
- CRASH 0 (RP01's fatal watchdog exit is classified HANG, not CRASH).

### Q9. Does every chain have a real consumer or terminal-type evidence?
Direct dataflow evidence exists for 48 contexts (consumer/commit or terminal
chain events); HANG contexts use the skip + watchdog + partial-trace evidence;
A01-R02 uses an explicit squash event; A01-R03 is the only unresolved case and
is reported as such. 16 rows have no `consumer` field because their terminal is
a hang/mask/squash, not a dataflow consumer.

### Q10. Are all 60 Fault–Control pairs strictly matched?
**Yes on the frozen binary.** Every pair has the same binary SHA
(`070d68a6…`), seed, workload, ROI ordinal and config; the only difference is
the fault switch. FW02 controls omit the injector; DA04/MD04 controls omit the
injector; RP01 controls omit `--chaos_lsqfwd`; LP01/SQ/SP05/A01/A03/FW05 mount
at p=0 as their selectors require. 60/60 pairs recorded in
`LSU_Fault_Control_Pair_Final.csv`.

### Q11. Do all controls prove zero injection?
**Yes, 60/60.** Artifacts: injector absent from `command.txt`/`config.ini`, or
`injection_count=0` plus zero injection events in the trace/log. No control
misfire was observed; every control oracle PASSed.

### Q12. Does the final binary correspond to the exact Git HEAD?
**Yes.** HEAD `fc608224…`; binary `070d68a6…`; `git diff --stat HEAD --
CHAOS/gem5/src` is empty; both build logs contain 0 `error:` lines. The final
binary is preserved at `audit_v3_3_2/binary/gem5.opt.v332-070d68a6`.

### Q13. Are Warm-up/ROI and the formal config frozen?
**No.** The measured ROI/percentile values are recorded and reproducible, but
`ConfigFrozen=NO` because the researcher has not approved the candidate
workloads, the ROI/Warm-up fields, or the SQ migration. The frozen workbook is
unchanged (`git diff 8f7a1354 -- docs/.../excel` empty).

### Q14. Are any technical problems still unresolved?
Yes; see §4. They are: A01-R03 unresolved writeback evidence; A03 partial
traces/no in-sim watchdog; SP05 `store_data_fnv` null; candidate-workload
approval; and the SQ03 "MASKED/visibility" labelling decision.

### Q15. Has the formal-experiment start condition been met?
**No.** `PARTIALLY_READY`, `12_MODEL_FORMAL_READY=NO`.

---

## 3. Gate table

| Gate | Result |
|---|---|
| Model (12/12 semantics + hooks) | PASS at hook level; A03 lifecycle documented |
| Context (60/60 valid) | PASS: 60 distinct mapped identities |
| Workload (all satisfy semantics) | 30 formal PASS; 30 candidate PENDING APPROVAL |
| Golden (all no-fault oracles) | PASS: 60/60 control oracles |
| Injection (target hit, no pollution) | PASS: 60/60 faults inject |
| Propagation (60/60 causal evidence) | 58 direct/terminal-type; A01-R03 UNRESOLVED; SP05 qualified |
| Consumer (real evidence / terminal causality) | PASS with the A01-R03 and SP05 qualifiers |
| Control (60/60 zero-injection pairs) | PASS: 60/60 |
| Binary provenance | PASS: HEAD/binary/Build log fixed |
| Config (seed/ROI/warm-up frozen) | **NO** — approval pending |
| Runner dry-run | PASS (`--dry-run` prints exact commands; guards tested) |
| Regression | PASS: 180 tests + 120 platform tests |
| Resource | PASS: 58 GiB free; ≤4 gem5 concurrency |

---

## 4. Remaining blockers (shortest path)

1. **Researcher approval for 30 candidate contexts** (FW02 W4-v2, RP01, MD04,
   SQ01/SQ03/SP05 `sq_reload_v3212`). Without it the mapping cannot be frozen
   or written into the workbook.
2. **A01-R03**: no writeback-divergence evidence. Options: accept it as
   `UNRESOLVED` for the formal run, or add a writeback observer and rerun.
3. **A03**: add an in-simulator watchdog (or accept external-timeout HANG with
   partial evidence) so the five HANG contexts have the same watchdog quality
   as RP01.
4. **SP05**: wire `store_data_fnv` (and the early-anomaly event) so
   `RELOAD_UNVERIFIABLE` becomes a complete dataflow chain.
5. **SQ03 labelling**: freeze "MASKED / visibility shift, not SDC" explicitly
   in the paper/report.
6. **Config freeze**: approve ROI/Warm-up, binary SHA, and the final manifest.

No source work is blocked; items 1, 5 and 6 are decisions, 2–4 are bounded
implementation/pilot work.

---

## 5. Verification actually run this round

- `pytest tests/ -q` → **180 passed in 95.69 s**.
- `pytest docs/.../platform/tests -q` → **120 passed in 4.05 s**.
- Standalone hook tests: `A03_STREAM_OK`, `LP01 identity record PASS`.
- Two gem5 builds, 0 `error:` lines; final binary SHA `070d68a6…`.
- 120 real gem5 runs (60 fault + 60 control) on the final binary; raw
  artifacts retained under `audit_v3_3_2/runs/`.
- Independent Agent F acceptance found the FW02 ordinal-offset bug, the stale
  provenance, and qualifier wording; all were corrected before packaging
  (see `subagent_reports/Agent_F_Independent_Acceptance_v332.md`).
