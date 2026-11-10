# FW02 control fix VERIFIED — runner control guard + SUPP-FW02-C02 valid control

**Round:** LSU v3.2.12 propagation closure (FW02 control-misfire closeout)
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` (branch HEAD `e1b236c6`; the runner patch below is the working-tree change, uncommitted by instruction)
**Pilot binary (pinned, verified before the run):** `sha256(build/ARM/gem5.opt) = 720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070` (equals `logs_v3_2_12/binary_v3212_trace.sha256` and the C02 manifest's `gem5.binary_sha256`)
**Date:** 2026-11-10. Written by the FW02-control-fix subagent. Root cause and the misfire record: `FW02_CONTROL_FIX_v3.2.12.md` (same directory) and `FW02_SQ01_SQ03_SP05_Evidence_Audit_v3.2.12.md` §1.1.

**Result in one line:** the `run_pilot.py` FW02 control guard is in place and tested (82/82 platform tests pass, 4 of them new); the corrected control **SUPP-FW02-C02** ran with the same context/seed as C01 and is a **valid, accepted CONTROL** (`injection_count=0`, oracle PASS, `control_valid=true`, `accepted=true`, runner exit 0); the closure tool re-recorded FW02 with C02 as a valid control, with all five fault rows byte-identical to the audit's records.

---

## 1. The patch (platform/run_pilot.py, +13 lines, one branch)

`run_pilot.py` had no explicit FW02 branch: FW02 fell into the `else` arm which
unconditionally mounts `--chaos_lsqfwd --lsq_struct_mode f6_fw02 …`
(`run_pilot.py:617-620` at the audit HEAD). Because the F6_fw02 injector is
ordinal-gated and deliberately probability-independent (attach happens even at
`probability==0`, `CHAOSLSQFwd.cc:81-87,134-138`; `maybeSuppressForwarding`
never consults probability, `:1019-1071`), a mounted FW02 control is
structurally guaranteed to misfire — exactly the recorded SUPP-FW02-C01
misfire. The fix is the LQ04 precedent (`run_pilot.py:612-616`) applied to
FW02, verbatim diff:

```diff
@@ -614,6 +614,19 @@ def main(argv=None) -> int:
             # not probability-gated, so a mounted injector would still fire.
             # Omit the injector entirely; --chaos_propagation stays on.
             extra = []
+    elif args.model == "FW02":
+        extra = ["--chaos_lsqfwd", "--lsq_struct_mode", "f6_fw02",
+                 "--max_faults", "1", "--rng_seed", str(args.seed),
+                 "--lsqfwd_event_ordinal", str(sample.get("event_ordinal") or 1)]
+        if args.probability == 0.0:
+            # Matched no-fault control (v3.2.12 fix): the F6_fw02 selector is
+            # ordinal-gated, not probability-gated -- CHAOSLSQFwd attaches the
+            # F6Fw02 mode even with probability==0 and the suppression
+            # decision never consults probability, so a mounted injector
+            # would still fire (the SUPP-FW02-C01 misfire). Omit the injector
+            # entirely; --chaos_propagation stays on (same treatment as the
+            # LQ04 control branch above).
+            extra = []
     else:
         extra = ["--chaos_lsqfwd", "--lsq_struct_mode", "f6_fw02",
```

Scope guarantees:

- **FAULT runs unchanged:** the FW02 fault flags are the same list the `else`
  arm always mounted; a FAULT command still carries `--chaos_lsqfwd
  --lsq_struct_mode f6_fw02 --max_faults 1 --rng_seed <S> --lsqfwd_event_ordinal
  <N>` (asserted by test).
- **No other model touched:** every other branch (A01/A03/SQ01/DA04/MD04/LP01/
  SQ03/SP05/FW05/LQ04) and the fallback `else` arm are byte-unchanged
  (`git diff --stat`: 1 file changed, 13 insertions(+), 0 deletions).
- `--chaos_propagation`, `--prop_trace_file`, `--probability 0.0`, workload and
  CPU/variant flags stay on for the control, so the control records the same
  trace machinery as its fault family.

## 2. Test evidence (new pytest, real output)

New file `platform/tests/test_run_pilot_fw02_control_mount.py`. It drives the
real `run_pilot.main()` end to end against a stub `gem5.opt` that records its
argv and exits 0, then asserts on the command the platform persisted
(`command.txt`), the command the simulator process actually received, and the
runner's control bookkeeping. Four tests: FW02 control omits the mount, FW02
fault keeps the mount, LQ04 control precedent unchanged, SQ01 control still
mounts its probability-gated injector (other models unchanged).

Observed output (2026-11-10):

```
$ python3 -m pytest tests/test_run_pilot_fw02_control_mount.py -v
...
tests/test_run_pilot_fw02_control_mount.py::test_fw02_control_omits_the_injector_mount PASSED [ 25%]
tests/test_run_pilot_fw02_control_mount.py::test_fw02_fault_run_keeps_the_injector_mount PASSED [ 50%]
tests/test_run_pilot_fw02_control_mount.py::test_lq04_control_precedent_unchanged PASSED [ 75%]
tests/test_run_pilot_fw02_control_mount.py::test_sq01_control_still_mounts_probability_gated_injector PASSED [100%]

============================== 4 passed in 1.48s ===============================
```

Regression (whole platform suite, unaffected tests):

```
$ python3 -m pytest tests/ -q
........................................................................ [ 87%]
..........                                                               [100%]
82 passed in 3.29s
```

(78 pre-existing + 4 new; zero failures, zero skips.)

## 3. The corrected control SUPP-FW02-C02 (real run, full record)

Invocation — the RUNBOOK §4 C01 command with the new pilot-id/outdir, same
context/seed/ordinal as C01 (gem5 slot verified free, `df` 67 GiB free,
binary SHA re-checked before launch):

```bash
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py \
  --model FW02 --context-index 1 --pilot-id SUPP-FW02-C02 \
  --seed 2941542370 --event-ordinal 1 --probability 0.0 \
  --outdir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-FW02-C02 \
  --gem5 build/ARM/gem5.opt
```

Runner output tail (full JSON meta also printed by the runner):

```
  "control_misfire": false,
  "accepted": true,
  "accepted_meaning": "record validity; not a claim that the fault caused the terminal",
  "crash_evidence": null
runner exit code: 0
```

`command.txt` (recorded, and byte-equal to what the simulator received — no
injector mount, control context intact):

```
build/ARM/gem5.opt
--outdir=.../pilots_v3_2_12/SUPP-FW02-C02
.../configs/se/lsu_proxy.py
--cmd=.../implementation_v3_2/workloads/sq_forward
--cpu O3 --variant B0 --probability 0.0
--chaos_propagation --prop_trace_file prop_trace.csv.gz
```

`pilot_meta.json` (all fields quoted from the run):

| field | value |
|---|---|
| `pilot_id` / `run_role` | `SUPP-FW02-C02` / `CONTROL` |
| `seed` / `excel_identity.seed` | `2941542370` / `2941542370` (`seed_source: excel:5.60个样本执行矩阵!Seed` in the manifest) — same as C01 |
| `exit_code` (gem5 child) / runner exit | `0` / `0` |
| `injection` / `injection_count` | `{}` / **`0`** |
| `control_valid` / `control_misfire` / `accepted` | **`true`** / `false` / **`true`** |
| `oracle_pass` / `oracle_expected` | `true` / `1f4cbf14327717df` |
| `classification.oracle_outcome` | `PASS` |
| `classification.terminal_state` / reason | `UNRESOLVED` / `NO_INJECTION_EVENT` (honest control terminal, never relabeled MASKED) |
| `classification.fault_activation_status` | `NOT_TRIGGERED` |
| `classification.trace_completeness` / `record_integrity` | `COMPLETE` / `VALID` |
| `trace.validator_errors` | `[]` |
| `trace.completeness` | `trace_completeness COMPLETE`, `propagation_coverage COMPLETE`, `propagation_stages ["forwarding_decision","sq_lifecycle"]`, `events 6222`, `edges 0`, `injections 0`, `chain_reasons ["no_injection_event"]` |
| `elapsed_seconds` / `csv_rows` | `1.724` / `6222` |

`oracle.log`: `expected=1f4cbf14327717df got=1f4cbf14327717df ORACLE_PASS`
(raw checksum line `1f4cbf14327717df` also present in `stdout.log`). The
un-faulted checksum equals the FW02 family golden, consistent with the audit's
determinism analysis.

**No injection artifact exists:** `lsq_fwd_injections.log` is absent from the
C02 dir (no injector was mounted, so no suppression can fire by construction).
The workload SHA matches the frozen `sq_forward` value
`132a84f7f21be052bc1f2c9baf1c12d5bd3462aae03b1d42778c94e69b0af297`.

**Honesty note on the seed/ordinal:** with the injector omitted, `--rng_seed`
and `--lsqfwd_event_ordinal` are not passed to gem5 — they are injector-mount
flags and would have no consumer (the `FW02_CONTROL_FIX_v3.2.12.md` §3
analysis says exactly this: "the carried seed would be inert (no RNG
consumer)"). The context identity is preserved in the record: seed
`2941542370` and ordinal `1` (both Excel-sourced, same row as C01/R01) are in
`pilot_meta.json`/`manifest.json`, and the run is deterministic regardless.

**C01 preservation:** the misfire record `SUPP-FW02-C01/` is untouched —
`git status` over `pilots_v3_2_12/` shows no modification to any tracked pilot
artifact (only the new untracked `SUPP-FW02-C02/` dir). C01 remains the
evidence that FW02 is ordinal-gated, exactly as RUNBOOK §7n required.

## 4. Closure-tool re-record (C02 as a valid control; controls are not second contexts)

Re-ran the frozen closure tool over the six FW02 pilot dirs (R01–R05 + C02):

```bash
python3 tools/lsu_12model_closure.py record --model FW02 \
  --pilot-dir …/SUPP-FW02-R01 … --pilot-dir …/SUPP-FW02-R05 \
  --pilot-dir …/SUPP-FW02-C02 \
  --binary-sha 720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070 \
  --json …/audit_v3_2_12/FW02_verdict_v3.2.12.json
```

Observed output (exit 0):

```
model=FW02 pilots=6
  SUPP-FW02-R01: FinalClassification=PARTIAL ObservedTerminal=SQUASHED MaskingMechanism=NOT_APPLICABLE missing=[NO_CONSUMER_EDGE;NO_COMMIT_EVENT]
  SUPP-FW02-R02: FinalClassification=UNRESOLVED ObservedTerminal=CRASH MaskingMechanism=NOT_APPLICABLE missing=[ORACLE_MALFORMED]
  SUPP-FW02-R03: FinalClassification=VERIFIED_SINGLE_CONTEXT ObservedTerminal=MASKED MaskingMechanism=NOT_APPLICABLE missing=[none]
  SUPP-FW02-R04: FinalClassification=VERIFIED_SINGLE_CONTEXT ObservedTerminal=MASKED MaskingMechanism=NOT_APPLICABLE missing=[none]
  SUPP-FW02-R05: FinalClassification=PARTIAL ObservedTerminal=SQUASHED MaskingMechanism=NOT_APPLICABLE missing=[NO_CONSUMER_EDGE;NO_COMMIT_EVENT]
  SUPP-FW02-C02: FinalClassification=UNRESOLVED ObservedTerminal=NO_INJECTION MaskingMechanism=NOT_APPLICABLE missing=[NO_INJECTION_EVENT;TERMINAL_UNRESOLVED]
```

Integrity of the re-record (old JSON vs new, per-record diff):

- `SUPP-FW02-R01 … R05`: **IDENTICAL** — the tool is deterministic and the
  five fault verdicts are unchanged.
- `SUPP-FW02-C01`: REMOVED · `SUPP-FW02-C02`: NEW — only the control row
  changed. (The C01-era JSON remains recoverable at commit `4a63ac05`; the
  misfire's primary evidence lives in `pilots_v3_2_12/SUPP-FW02-C01/` and the
  two audit MDs, all untouched.)

C02's record fields: `RecordIntegrity=VALID`, `TraceCompleteness=COMPLETE`,
`FaultEffectPropagationCoverage=NOT_APPLICABLE`, `ObservedTerminal=NO_INJECTION`,
`ApplicationOracle=PASS`, `InjectionVerified=no`, `InjectionCount=0`,
`ActivationStatus=null`, `TerminalReason=NO_INJECTION_EVENT`,
`FinalClassification=UNRESOLVED`, `VerifiedChainCount=0`,
`MissingEvidence=NO_INJECTION_EVENT;TERMINAL_UNRESOLVED`,
`BinarySHA256=720eb780…`, `WorkloadSHA256=132a84f7…`. This is the same
valid-control shape as SQ01/SQ03/SP05's C01 rows in the audit §3 table. The
control is graded as a control — it is **not** a fault context: zero verified
chains, `NOT_APPLICABLE` coverage, and the model's context count stays five
(R01–R05).

**Follow-up flag (not done here, by scope):** the Task 16 matrix artifacts
written earlier from the C01-era verdict
(`LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv` row `FW02@720eb780`:
`InjectionVerified yes(6/6)`, `ObservedTerminal mixed(CRASH=1;MASKED=2;SQUASHED=3)`,
`FinalClassification … PARTIAL=3 …`) still embed the misfired control. They
should be regenerated from the updated `FW02_verdict_v3.2.12.json` by the
matrix owner; with C02 the row becomes `InjectionVerified mixed(yes=5;no=1)`,
`ObservedTerminal mixed(CRASH=1;MASKED=2;NO_INJECTION=1;SQUASHED=2)`,
`FinalClassification mixed(COMPLETE_CAUSAL_CHAIN=2;PARTIAL=2;UNRESOLVED=2)`.

## 5. Contrast: C01 (misfire, preserved) vs C02 (valid control)

| run | injector mounted | `lsq_fwd_injections.log` | injection_count | oracle | control_valid / accepted | runner exit | role-recorded |
|---|---|---|---|---|---|---|---|
| SUPP-FW02-C01 (pre-fix, preserved) | yes (`f6_fw02` fires at p=0 by design) | yes (t556325, L397/S383 — byte-identical to R01) | 1 | PASS | false / false (`control_misfire: true`) | 1 | yes — honest rejection, kept as evidence |
| SUPP-FW02-C02 (post-fix) | **no** | **absent** | **0** | PASS | **true / true** | 0 | yes — valid CONTROL record |
| (reference) SUPP-SQ01-C01 | yes (sq01_bit3; attach is probability-gated) | absent | 0 | PASS | true / true | 0 | yes |

## 6. Remaining scope notes (honest)

1. **DA04** sits in the same probability-independent attach list
   (`CHAOSLSQFwd.cc:82`, `Da04BeBit0`); a DA04 control run with
   `--probability 0.0` under the current runner would mount its injector and
   can misfire the same way. Per the audit's §4 note 3 it "deserves the same
   audit when its controls are next run"; deliberately NOT patched here (this
   fix is FW02-scoped and must not change other models' behavior).
2. The C02 trace is the no-fault `sq_forward` reference the FW02 audit wanted
   (`forwarding_decision` + `sq_lifecycle` stages, 6222 events, zero
   injections): the memory-response/hash reference for the store data without
   any suppression.
3. Nothing was committed (per task instruction); all deliverables live in the
   worktree: the patched runner, the new test, `SUPP-FW02-C02/`, the refreshed
   `FW02_verdict_v3.2.12.json`, and this document.
