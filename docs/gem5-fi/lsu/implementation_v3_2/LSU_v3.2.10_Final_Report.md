# LSU v3.2.10 Final Report — LQ04 (Load Queue Entry lifetime fault)

**Date:** 2026-11-09
**Branch:** `lsu-platform-v3.2.10` (pilots at HEAD `5adbb220`)
**Scope:** LQ04 only (Excel v3.2.4 12-model matrix row 4). The other 11 models,
the 60 SampleRunIDs/RunIDs/SubTaskIDs/Seeds, `ConfigFrozen=NO`, and the
Warm-up/ROI `NEEDS_RESEARCHER_CONFIRMATION` status are unchanged.
**Companion documents:**
`LSU_v3.2.10_Baseline_Verification.md`, `LQ04_Source_Audit_v3.2.10.md`,
`LQ04_Definition_Freeze_v3.2.10.md`, `LQ04_Propagation_Audit_v3.2.10.md`,
`.superpowers/sdd/2026-11-08-lsu-v3.2.10-lq04/task-1..10-report.md`.

---

## 1. Baseline and version reconciliation

| Item | Value | Evidence |
|---|---|---|
| Baseline branch/commit | `lsu-platform-v3.2.9` @ `37692d2beffcb73fc9303ad9de4c6bb341d5de71` | Task 1 report §1 (`git rev-parse HEAD` in the v3.2.9 worktree); only `GIT_*_v329.txt` provenance files differ from its parent `ecf0fdf9` (code unchanged) |
| Baseline binary SHA256 | `303c610d2dcca81340f0feae58fc449c8550d1daac6ff965a3387efd2189a0c0` (root and `CHAOS/gem5` copies identical) | Task 1 report §1; supersedes the stale `d6e60863…` still printed in some v3.2.9 docs |
| v3.2.10 branch commits | `7f397e2f` (Task 1 docs) … `5adbb220` (Task 10 pilots), 19 commits | `git log --oneline 37692d2b..HEAD`; `git rev-list --count 37692d2b..HEAD` = 19 |
| v3.2.10 binary SHA256 | `f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694` (gem5 25.1.0.1, compiled 2026-11-09 13:36:41; root and `CHAOS/gem5` copies identical) | `logs_v3_2_10/binary_v3210.sha256`; re-hashed during the Task 11 audit |
| Build gate | exit 0, 0 lowercase `warning:` lines, 7 environmental `Warning:` lines (capstone/png/HDF5/systemc), none from LQ04 code | `logs_v3_2_10/build_lq04.log` (Task 9 report) |
| Regression | `reg_chain` exit 0, checksum `f247ef3fe6f02cfd` (expected `0xf247ef3fe6f02cfd`), no SIGSEGV/panic | `logs_v3_2_10/regression_lq04.txt` |
| No-fault anchor baseline | exit 0, `checksum=0xb097eb83f71545cb` | same file (Task 9 report step 5) |
| Workload | `workloads/lq_lifetime_ordinal`, SHA256 `fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba` | `workloads/lq_lifetime_ordinal.sha256`; re-hashed during the Task 11 audit |
| Identity authority | Excel v3.2.4 (`excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx`, SHA256 `25e13e88e2c5a2881567d58d8dc6e6407659c20016746e93ff31bf45f1967214`), sheets 3/4/5 row 4 / rows 12–16 | `LQ04_Definition_Freeze_v3.2.10.md` §1–2 |
| Excel gem5Commit | `6f98088a7144d7f6fb22d985be3023ac5658e71b` = main repo `fi-ding` HEAD (verified Task 1) | Task 1 report §1 |
| Superseded Excel cells (stale, per D3) | workload path `lq_lifetime`, binary `7c69fd27…`, oracle `1624d44faff77183` | freeze doc §2; to be transcribed in Excel v3.2.5 (Task 12) |
| pytest (v3.2.9 record) | 40 passed / 2 failed — both failures are the disk guard (free 22.9 GiB < red line 70.6 GiB) | `logs_v3_2_9/pytest_full.log`; corrected from the wrong "39 passed" claim in `LSU_v3.2.9_Final_Report.md:49` |

Pilot environment: disk 14 GiB free at pilot time (below the 70.6 GiB guard
red line), so pilots were run directly without `lsu_guard` (Task 10 report);
all ten runs completed in ~2 s each with gem5 exit 0.

---

## 2. Implementation summary

One-patch-per-unit across Tasks 2–8; diffstat `7f397e2f..1dbe2797`
(25 files, +2134/−12):

**Workload (Task 2, D3).** `workloads/lq_lifetime_ordinal{.S,.c,.golden,.sha256}`
+ `compile_lq_lifetime_ordinal.sh`. Hand-written `_start` loads five 8-byte
anchors A1–A5 from a six-entry `.data` table at `tbl+0..32` into x2–x6
(disassembly: `ldr` at PC `0x400338/0x40033c/0x400340/0x400344/0x400348`),
passes them to `main(a..e)` in x0–x4, five distinct consumer operations,
4096-byte/64-iteration loop, A5 guard, single-line `checksum=` output via raw
`write`/`exit` syscalls. Golden `checksum=0xb097eb83f71545cb`.

**Pure rules (Task 3).** `CHAOS/gem5/src/cpu/o3/CHAOSLQ04/lq04_rules.hh`
(header-only eligibility/ordinal rules) + host unit test
`tests/test_lq04_rules.cc` (41 lines; includes the squashed-branch pin).

**Side channel + boundary restore (Task 4, D2).**
`CHAOS/gem5/src/cpu/o3/lsq_unit.hh` (+54): `LSQEntry::_lq04Request` (:110),
`_lq04Corrupt` (:114), `corruptLifetime()` (:166-174, asserts
`_valid && _request != nullptr` then sets `valid=0`/`request=nullptr`),
`restoreLifetime()` (:179-188), destructor/clear safety for a stashed request
(:123-125). `lsq_unit.cc`: `lq04Restore()` (:928-944); restore before
`commitLoad()`'s `assert(front().valid())` (:947-950); `commitLoads()` pre-loop
acceptance (:981); squash-boundary restore (:1237-1238); `drainSanityCheck()`
acceptance (:366). These are the only invariant sites relaxed, exactly as D2
permits.

**CHAOSLQ04 SimObject (Task 5).** Four-piece
`CHAOSLQ04/{CHAOSLQ04.hh,CHAOSLQ04.cc,CHAOSLQ04.py,SConscript}`
(114+224+49+10 lines): self-attaches at `startup()`
(`cpu.hh:551-556` back-pointer), ordinal-gated one-shot selection
(`maybeSelect`, `--lq04_event_ordinal`, `--lq04_max_faults=1`,
`--lq04_watchdog_cycles`), writes `lq04_injections.log`.

**executeLoad injection + probes (Task 6, D1/D4/D5).**
`lsq_unit.cc:801-827`: at the end of a successful `executeLoad`, an eligible
load (entry valid, request present, not squashed, executed) is selected by
ordinal and `corruptLifetime()` fires; `noteLQ04Injection` records
before/after valid/request, occupancy, no_pop/no_reuse, data_unchanged.
`lsq_unit.cc:124-135`: response probe in the completion path records
`response_probe` with `valid_at_response`/`request_present_at_response`.
`noteRestore` records the boundary restore.

**Propagation chain binding (Task 7, D5).**
`CHAOSPropagation/{CHAOSPropagation.cc (+171), .hh (+35)}`: LQ04 registry
entries emitting `injection`, `memory_response` (sender-state association,
payload hash), `register_writeback` (payload-vs-register hash,
`data_corruption`, `value_matches_payload`), `commit`, `errant_commit` and
`consumer_commit` edges with input/output hashes; converter
`platform/tools/prop_trace_to_v31.py` (+5) and
`platform/trace_completeness.py` (+16) bindings.

**Platform wiring (Task 8).** `configs/se/lsu_proxy.py` (+40: `--chaos_lq04`
mount flags), `platform/run_pilot.py` (+84: LQ04 model entry, control
semantics, CSV columns), `platform/terminal_rules.py` (LQ04 terminal rule),
`tests/test_lq04_platform.py` (230 lines) +
`tests/data_lq04_platform/lq04_injections.log`.

**Counts.** 4 new injector files + 1 rules header; 3 LSQ/O3 source files
touched (`lsq_unit.hh`, `lsq_unit.cc`, `cpu.hh`); 4 platform files; 5 workload
files; 3 test files; 2 config-file hooks (mount flags); 8 distinct C++ hook
sites listed above.

---

## 3. Pilot and control results

Ten runs on 2026-11-09 (Task 10), binary `f3c2a442…`, workload
`fa25f785…`, config `configs/se/lsu_proxy.py --cpu O3 --variant B0`,
golden oracle `checksum=0xb097eb83f71545cb` (`oracle_source=workload_golden`).
Full per-cell audit: `LQ04_Propagation_Audit_v3.2.10.md` §2.

| Run | Seed | Ordinal | Target (seq/PC/lq_idx/gen/addr) | InjTick | RespTick | WbTick | CommitTick | RestoreTick | Edges | Oracle | Terminal |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LQ04-R01 | 1842987246 | 1 | 3 / 0x400338 / 1 / 1 / 0x41ffe8 | 80080 | 135520 | 135520 | 136290 | 136675 | 326 | PASS | MASKED |
| LQ04-R02 | 2188214204 | 2 | 4 / 0x40033c / 2 / 2 / 0x41fff0 | 80465 | 136290 | 136290 | 137060 | 137445 | 327 | PASS | MASKED |
| LQ04-R03 | 3953171871 | 3 | 5 / 0x400340 / 3 / 3 / 0x41fff8 | 133210 | 136291 | 136291 | 137445 | 137830 | 326 | PASS | MASKED |
| LQ04-R04 | 4153250964 | 4 | 6 / 0x400344 / 4 / 4 / 0x420000 | 133595 | 201740 | 201740 | 202510 | 202895 | 326 | PASS | MASKED |
| LQ04-R05 | 3410523942 | 5 | 7 / 0x400348 / 5 / 5 / 0x420008 | 133980 | 202510 | 202510 | 203280 | 203665 | 327 | PASS | MASKED |

Common to all five fault runs: one injection each; `valid 1→0`,
`request 1→0`; occupancy unchanged (2→2 for R01/R02, 5→5 for R03–R05);
`association=sender_state`; `entry_valid_at_response=0`;
`entry_request_at_response=0`; `data_unchanged=1`; `data_corruption=0`;
`value_matches_payload=1`; writeback hash == payload hash; 0 replays
(`execution_attempt_id=1`, `replay_generation=0`); 0 squashes; restore
`reason=commit` at the commit boundary; `terminal_state_reason=TARGET_COMMITTED_DATA_VALUE_PRESENT`;
`run_status=COMPLETED`; `fault_activation_status=TRIGGERED`; gem5 exit 0.

Controls (LQ04-CONTROL-R01..R05): injector not mounted (`--probability 0.0`),
zero `CHAOS_LQ04_*` lines, no `lq04_injections.log` (n/a by construction),
trace contains only lifecycle records, oracle PASS with the identical
checksum `0xb097eb83f71545cb`, gem5 exit 0; `terminal_state=UNRESOLVED /
NO_INJECTION_EVENT`; `run_pilot.py` exits 1 (`accepted=false`, record
validity requires ≥1 injection) — expected control signature.

**Grading (audit, per `LQ04_Propagation_Audit_v3.2.10.md` §5):**

| Run | RecordIntegrity | TraceCompleteness | PropagationCoverage | PROPAGATION_VERIFIED | SDC |
|---|---|---|---|---|---|
| LQ04-R01..R05 | VALID | COMPLETE | **LIFECYCLE_ONLY** | **0** | **no** |
| LQ04-CONTROL-R01..R05 | VALID | COMPLETE | PARTIAL (no injection; audit: n/a) | n/a | no (no fault) |

Controller ruling (restated): the consumer edges are real and hashed, but they
carry the **correct** payload, so the fault's corrupting effect does not
propagate; the structural chain is recorded in full, SDC is not claimed, and
the terminal is MASKED in 5/5 fault pilots with oracle PASS.

---

## 4. The ten final-report questions (explicit answers)

1. **Is the literal definition fully implementable?**
   Yes, with the two frozen conditions (gate verdict
   `IMPLEMENTABLE_WITH_CONDITIONS`). The literal field fault
   (`valid=0`, `request=nullptr` after `executeLoad`, no pop, no reuse) was
   implemented exactly (audit §2.2: `valid_before=1;valid_after=0;
   request_before=1;request_after=0;no_pop=1;no_reuse=1` in 5/5) and ran to
   completion in 5/5 pilots. Without D2's side channel the literal definition
   would abort gem5 at the commit invariant
   (`assert(front().valid())`, `lsq_unit.cc:862`/`:890`/`:343` — source audit
   answer A); D2's boundary restore (`lsq_unit.cc:947-950`) is what makes it
   completable, and it is the only mechanism added around the invariant sites
   (`:981`, `:366`).

2. **Dangling request / use-after-free?**
   No. Every `_request` reader guards (`checkSnoop` `:529/:541`,
   `checkViolations` `:656/:660`, `startStaleTranslationFlush` `:1570-1576` —
   source audit answer B), so a null `_request` is never dereferenced. The
   request is stashed in the `LSQEntry` side channel
   (`lsq_unit.hh:110`, `corruptLifetime()` `:166-174`), restored at the
   boundary (`restoreLifetime()` `:179-188` via `lq04Restore()` `:928`) and
   freed by the normal `clear()`/`freeLSQEntry()` — trace evidence: `restore`
   and `free` lifecycle records at the same tick with `reason=commit`
   (audit §2.5), 5/5 runs, gem5 exit 0, no crash evidence
   (`crash_evidence: null`). (The pure-literal variant without the side
   channel would additionally leak one `LSQRequest`; the implemented D2
   variant does not.)

3. **All five targets triggered?**
   Yes. Five distinct `(seq, pc, addr, lq_idx, gen)` tuples —
   (3,0x400338,0x41ffe8,1,1), (4,0x40033c,0x41fff0,2,2),
   (5,0x400340,0x41fff8,3,3), (6,0x400344,0x420000,4,4),
   (7,0x400348,0x420008,5,5) — one anchor Load per run
   (`fault_activation_status=TRIGGERED` 5/5; audit §2.1).

4. **Exactly once each?**
   Yes. Exactly one `CHAOS_LQ04_INJECTION` line per fault run (2-line
   `lq04_injections.log`: 1 injection + 1 restore), `injections: 1` in every
   trace summary counts, `--lq04_max_faults 1`, `all_one_injection=true`,
   ordinals 1–5 each used exactly once with `eligible_ordinal == ordinal ==
   Excel ordinal` (audit §6 checks 2–3).

5. **Response correctly bound?**
   Yes. `association=sender_state` with `entry_valid_at_response=0` and
   `entry_request_at_response=0` in 5/5 (audit §2.3): the response arrived
   while the entry was visibly invalid, was recovered through
   `pkt->senderState` (the response path never reads the LQEntry — source
   audit), and delivered the correct payload (`data_unchanged=1`). No
   response loss, no wrong binding — the Excel's hypothesized
   response-loss/mis-binding mechanism did not occur.

6. **Replay / squash?**
   None. 0 replays (`execution_attempt_id=1`, `replay_generation=0`,
   `execution_attempt_link=SAME_ATTEMPT`) and 0 squashes in 5/5; the corrupt
   window closed at the commit boundary (`CHAOS_LQ04_RESTORE … reason=commit`),
   never via squash.

7. **Wrong-data propagation?**
   No. `data_corruption=0`, `value_matches_payload=1`, writeback FNV ==
   payload FNV in 5/5; `taint_value_mismatch_records=0` and
   `consumer_input_matches_source=1` on all 326/327 consumer edges per run
   (audit §2.4, §2.6). The value that propagated is the fault-free anchor
   data.

8. **Consumer / commit?**
   The target Load committed with the correct data value in 5/5
   (`commit_status=COMMITTED`, `terminal_state_reason=TARGET_COMMITTED_DATA_VALUE_PRESENT`,
   `errant_commit` marker recorded), and its consumers committed reading
   exactly the written-back value (first consumer `mov x0,x2` @`0x40034c`
   with input `0x0102030405060708` in R01). The structural chain
   injection → memory_response → register_writeback → consumer_commit is
   complete in 5/5.

9. **Application SDC?**
   No. Oracle PASS in 5/5 fault pilots, actual `checksum=0xb097eb83f71545cb`
   == golden; the five matched zero-injection controls reproduce the same
   checksum, so the equality is not run-to-run variance. Terminal MASKED.

10. **End-to-end propagation standard met?**
    No — and this is the honest negative result the design predicted (source
    audit answer D). `PROPAGATION_VERIFIED=0` and
    `PropagationCoverage=LIFECYCLE_ONLY` per D5 and the controller ruling:
    the standard requires the fault's effect to reach a real consumer edge as
    a corrupted value; here the consumer edges carry the correct payload, so
    the fault effect is confined to the entry lifecycle (invalid interval
    injection → boundary restore). The full structural chain remains recorded
    as positive binding evidence (questions 5 and 8), not as propagation.

---

## 5. Open issues

1. **Stale Excel oracle for LQ04** — Excel v3.2.4 carries `1624d44faff77183`
   (old `lq_lifetime` workload); the pilots used the D3 workload golden
   `checksum=0xb097eb83f71545cb` via the documented `--workload` override
   (`oracle_source=workload_golden`). To be corrected in the Excel v3.2.5
   transcription (Task 12), together with the workload path/SHA cells and the
   stale sheet-4 `G4` line ranges (freeze doc §1.1).
2. **Disk below guard threshold** — 14 GiB free at pilot time vs the 70.6 GiB
   red line; pilots ran without `lsu_guard`. The two v3.2.9 pytest failures
   (40 passed / 2 failed) are the same environmental disk guard.
3. **Control exit-1 signature** — `run_pilot.py` exits 1 for zero-injection
   controls (`accepted=false`: record validity requires ≥1 injection) while
   gem5 itself exits 0 and the oracle passes. By design; documented so the
   exit code is not misread as a failed control.
4. **Seed recorded as identity, not operative parameter** — the five seeds
   are frozen Excel identity cells carried in `pilot_meta.json`; LQ04 target
   selection is ordinal-gated and deterministic (`--lq04_event_ordinal`),
   so the seed does not drive selection in these pilots. Any future
   seeded-tier selection (D4 explicitly excludes it here) would need the seed
   wired as an operative RNG parameter.
5. **Stale-translation flush skips the corrupt entry** —
   `startStaleTranslationFlush()` / `checkStaleTranslations()`
   (`lsq_unit.cc:1566-1590`) guard `entry.valid() && entry.hasRequest()`, so
   an LQ04-corrupt entry's in-flight request is not marked stale during the
   corrupt window. Documented structural limitation (source audit answer B);
   not exercised by these pilots (no squash, no translation invalidation on a
   target entry).
6. **`/tmp` scratch not part of deliverables** — the Task 9 regression and
   no-fault-baseline outdirs (`/tmp/lq04_reg`, `/tmp/lq04_base_t9`) were
   scratch; their summarized results are committed in
   `logs_v3_2_10/regression_lq04.txt`, the raw outdirs are not deliverables.
7. **Tool-vs-audit coverage label** — the trace tool records the structural
   `propagation_coverage=COMPLETE` in `pilot_meta.json`/
   `LQ04_PILOT_SUMMARY.csv`; this audit and the controller ruling grade the
   research-question coverage as `LIFECYCLE_ONLY` / `PROPAGATION_VERIFIED=0`
   (§3). The artifacts were not rewritten; Task 12's Excel v3.2.5 must use
   the audit grading, not the tool label, for the LQ04 propagation cells.

---

## 6. Verdict

LQ04 is implemented, verified and audited end-to-end under the frozen D1–D6
decisions: five one-shot ordinal-gated literal injections, five matched
controls, complete traces, clean regression and build. The literal LQ entry
lifetime fault produces **no response loss, no mis-binding, no replay, no
squash, no data corruption and no application SDC** — the terminal is MASKED
in 5/5 with the golden checksum. The fault's effect is confined to the entry
lifecycle: **RecordIntegrity VALID, TraceCompleteness COMPLETE,
PropagationCoverage LIFECYCLE_ONLY, PROPAGATION_VERIFIED=0, SDC no.** The
Excel's hypothesized "response loss / mis-binding → Replay/Commit anomaly or
SDC" mechanism is falsified for this configuration; the result is reported as
the honest negative outcome the gate analysis predicted, not as propagation.
