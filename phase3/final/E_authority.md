# Agent E — MMU Final Formal Authority / Runner / Preflight Report

Date: 2026-11-12  
Workspace: `/home/sdc/gem5-fi-mmu-impl-v2` only. `/home/sdc/gem5-fi-mmu`
(original) was never modified. **No gem5 process was launched by this
work.** All proof below comes from `--describe` / dry-run, real traces and
real gem5 output files already on disk.

Full exact patch: `phase3/final/E_authority_tools.diff` (2284 lines; tracked
files as `git diff`, new files as `/dev/null` diffs).

---

## Post-final correction (2026-11-12, evidence closure v2)

This report documents the runner/preflight work as it stood before the final
EPAN checkpoint. Two PFN statements below are historical and must not be read
as the final authority:

- The final scoped control `runs/TEST-F1-CTRL-W10-R02/Run_Log/golden_output.txt`
  (SHA256 `66a42431eb599efc…`) records `target_pfn=0x834b2`,
  `neighbor_pfn=0x834b3`, `sentinel=0x63`, `neighbor_sentinel=0x60`.
- The final faulted trace `runs/TEST-F1-M02-R02/Trace/prop_evt.txt.gz`
  `refill_pfn_corrupt` event 4424 records `old_pfn=0x834b2`,
  `new_pfn=0x834b3`, `old_pa=0x834b2000`, `new_pa=0x834b3000`.
- The earlier scoped control `TEST-ENV-CTRL-W10` (`0x834b6`) and the older
  `--ctx all` control (`0x83480`) predate the final checkpoint and are
  superseded. The frozen authority `07_Sample_Matrix` OracleMethod for
  M02 R01–R05 now states `0x834b2->0x834b3`; see
  `tools/mmu_apply_authority_corrections.py`.

---

## 1. M02 `old_pfn` — removed the hardcoded `0x83480`

### 1.1 Root cause (measured)

`tools/mmu_formal_runner.py` passed `--mmu_m02_old_pfn 0x83480` for every
context. The real scoped R02 output shows the authoritative PFN is
`0x834b6`:

```
runs/TEST-M02-R02B/Run_Log/observed_output.txt:
W10_RESULT ctx=R02 pages=4096 alias=0x4002000000 target=0x4001100000
target_pfn=0x834b6 neighbor_pfn=0x834b7 pa=0x834b6000 pa_neigh=0x834b7000
...
```

The old value came from the legacy `--ctx all` control
(`runs/TEST-ENV-CTRL-W10`, `target_pfn=0x83480`, `sentinel=0x7d`), which
allocates the same pages in a different order than a scoped run (scoped R02:
`0x834b6`, `sentinel=0x63`). The old control is therefore **not** a valid
per-context oracle for this workload.

### 1.2 Fix (exact hunks)

Runner (`tools/mmu_formal_runner.py`):

```diff
-            "--mmu_m02_old_pfn", "0x83480", "--mmu_m02_xor_mask", "1",
+            "--mmu_m02_old_pfn", str(m02_old_pfn),
+            "--mmu_m02_xor_mask", "1",
```

```diff
+    m02_old_pfn = "0"
+    m02_source = ""
+    if model == "M02":
+        pfn_map = pf.load_w10_pfn_map(repo_root, w10_control_golden)
+        rec_p = (pfn_map.get("contexts") or {}).get(context)
+        if not rec_p or not rec_p.get("target_pfn"):
+            raise RunRefused(
+                "BLOCKED_MISSING_W10_PFN_MAPPING",
+                "no independent no-fault W10 control PFN for %s in %s%s; "
+                "run a scoped no-fault control and collect it with "
+                "tools/mmu_collect_w10_pfn.py" % (...), 5)
+        m02_old_pfn = "0x%x" % rec_p["target_pfn"]
```

The plan/manifest now records `m02_old_pfn` and `m02_old_pfn_source`
(control run + SHA256). There is **no literal `0x83480` anywhere in either
runner**; `tools/mmu_formal_preflight.py:check_runner_pfn_hardcode()` fails
any future reintroduction and is enforced for every M02 row.

`phase3/run_scripts/run_mmu_case.sh` (the real production script; there is no
`tools/run_mmu_case.sh`) was fixed the same way:

```diff
-                --mmu_m02_va "$TARGET" --mmu_m02_old_pfn 0x83480
+                --mmu_m02_va "$TARGET" --mmu_m02_old_pfn "$MMU_M02_OLD_PFN"
```

and it now refuses to run M02 without `MMU_M02_OLD_PFN` ("refusing the
legacy 0x83480"). It also gained `MMU_CTX` (scope a multi-context rcS to one
context, used to produce the independent no-fault controls) and M05 now
passes `--mmu_target_n 21` (the correct 2 MiB walk-cache width; the old
M03–M08 branch used 12).

New collector: `tools/mmu_collect_w10_pfn.py` writes
`phase3/formal/w10_pfn_map.json` from the real controls. The loader
(`mmu_formal_preflight.load_w10_pfn_map`) accepts a JSON map, a directory of
`...W10...R0x` runs, or a single golden file, and rejects:
- runs whose `command.txt` contains `--mmu_fault_enable true` /
  `--mmu_fault_model`;
- names that are not a single-context `R0x` control (this excludes the
  legacy `--ctx all` control);
- lines whose `ctx` disagrees with the run name or whose `target` VA is not
  the W10 context VA;
- lines that are not `pfn_match=1 result=PASS`.

### 1.3 Real proof (focused test)

`python3 tools/tests/test_mmu_formal_authority.py` — the M02 fixture copies
the **real** gem5 file `runs/TEST-M02-R02B/Run_Log/observed_output.txt` into
a scoped control directory (no gem5 launch):

```
PASS m02.real_file_has_834b6 -- /home/sdc/gem5-fi-mmu-impl-v2/runs/TEST-M02-R02B/Run_Log/observed_output.txt
PASS m02.resolve_R02 -- 0x834b6
PASS m02.neighbor -- 0x834b7
PASS m02.target_va -- 0x4001100000
PASS m02.runner_arg -- --mmu_fault_model M02 --mmu_fault_enable true --mmu_m02_va 0x4001100000 --mmu_m02_old_pfn 0x834b6 --mmu_m02_xor_mask 1 --mmu_m02_dram_lo 0x80000000 --mmu_m02_dram_hi 0x100000000
PASS m02.no_literal_83480
PASS m02.missing_blocks
PASS m02.rejects_faulted -- [{'source': '/tmp/.../runs/TEST-CTRL-W10-R03', 'reason': 'fault-enabled run'}]
PASS m02.rejects_all_context_control -- contexts=['R02'] runs: 1/5 contexts; rejected 1 candidate(s)
PASS m02.no_hardcoded_literal_in_tools -- M02 old_pfn is resolved from the control map, not literal
```

End-to-end `--describe` with the same real control file:

```
$ python3 tools/mmu_formal_runner.py --pilot TEST-PROBE-M02-R02 --model M02 \
    --workload W10 --context R02 --target 0x4001100000 \
    --eligible-event-index 1 --w10-control-golden /tmp/w10_ctrl_probe \
    --out-root /tmp/probe_runs --describe
status READY
old_pfn 0x834b6
source W10 control TEST-CTRL-W10-R02 sha256=f69448c34fb6c393
arg ['--mmu_m02_old_pfn', '0x834b6']
has_83480 False
```

Without a control the runner refuses (exit 5):

```
{
  "exit_code": 5,
  "message": "no independent no-fault W10 control PFN for R02 in
  /tmp/no_such_control (control map/root not found: /tmp/no_such_control); run
  a scoped no-fault control and collect it with tools/mmu_collect_w10_pfn.py",
  "run_id": "TEST-PROBE-M02-R02B",
  "run_kind": "PILOT",
  "status": "BLOCKED_MISSING_W10_PFN_MAPPING",
  "would_run": false
}
```

---

## 2. Validator — stricter M06 `DETECTED_CONTAINED`

### 2.1 Problem (measured)

The old rule accepted `DETECTED_CONTAINED` whenever
`state_consumed=1 && result_propagated=1 && commit not observed`, even with
`exception_delivered=0` and no `exception_delivery` event. Real before state:

```
TEST-M06-R03B2  term=DETECTED_CONTAINED  exc_deliv=0
TEST-M06-R04B2  term=DETECTED_CONTAINED  exc_deliv=0
TEST-M06-R05B2  term=DETECTED_CONTAINED  exc_deliv=0
```

`TEST-M06-R05B2`'s raw trace confirms the summary says `exception_delivered=0`
with no `exception_delivery` kind — there is no architectural consumer.

### 2.2 Fix (exact hunk)

```diff
+    m06_exc_event = any(_kind(e) == "exception_delivery"
+                        for e in live_evs)
+    m06_delivery_proof = bool(m06_exc_event) or (
+        m06_exc_deliv == "1" and m06_result_prop == "1")
+    m06_consumed = (m06_state_consumed == "1" or
+                    "fault_state_consumed" in observed)
...
-    elif model == "M06" and m06_exc_deliv == "1":
+    elif model == "M06" and m06_consumed and m06_delivery_proof:
         terminal_state = "DETECTED_CONTAINED"
-    elif model == "M06" and m06_state_consumed == "1" and \
-            m06_result_prop == "1" and "commit" not in observed:
-        terminal_state = "DETECTED_CONTAINED"
-    elif model == "M06" and m06_state_consumed == "1" and \
-            m06_result_prop == "0":
+    elif model == "M06" and m06_consumed and m06_result_prop == "1":
+        terminal_state = ("SQUASHED" if (observed & SQUASH_KINDS or
+                                         terminal == "squash")
+                          else "TRACE_INCOMPLETE")
+    elif model == "M06" and m06_consumed and m06_result_prop == "0":
         terminal_state = "TRACE_INCOMPLETE"
```

Accepted delivery proof: a real `exception_delivery` event **or** summary
`exception_delivered=1` together with `result_propagated=1` (the summary is
emitted by the delivery hook). The existing `terminal == "exception"` branch
still accepts an exception event whose `contained/delivered=1`. No threshold
was loosened.

### 2.3 Real proof (existing traces, no gem5)

```
$ python3 tools/mmu_formal_validate.py --run-dir runs/TEST-M06-R05B2 \
    --model M06 --workload W10 --context R05
  "OracleResult": "PASS",
  "TerminalState": "TRACE_INCOMPLETE",
  "TraceCompleteness": "COMPLETE",
```

Revalidation (written to `phase3/formal/revalidated/`, run dirs untouched):

```
TEST-M06-R01.json  term=DETECTED_CONTAINED oracle=PASS_EXPECTED_DETECTION trace=COMPLETE exc_deliv=1
TEST-M06-R02E.json term=DETECTED_CONTAINED oracle=PASS_EXPECTED_DETECTION trace=COMPLETE exc_deliv=1
TEST-M06-R03B2.json term=TRACE_INCOMPLETE oracle=PASS trace=COMPLETE exc_deliv=0
TEST-M06-R04B2.json term=TRACE_INCOMPLETE oracle=PASS trace=COMPLETE exc_deliv=0
TEST-M06-R05B2.json term=TRACE_INCOMPLETE oracle=PASS trace=COMPLETE exc_deliv=0
```

`TEST-M06-R02D` (no summary, but a real `exception_delivery` event) still
reports `DETECTED_CONTAINED`, proving the event-based path:

```
"OracleResult": "PASS_EXPECTED_DETECTION",
"TerminalState": "DETECTED_CONTAINED",
"TraceCompleteness": "TRACE_INCOMPLETE",
```

Consequence: M06 R03/R04/R05 are no longer READY. They are `BLOCKED_TRACE`
(`terminal TRACE_INCOMPLETE`) until a real delivery event exists or the
researcher approves a terminal amendment. This is recorded in
`MMU_Final_Blockers.md`; the authoritative M06 terminal set was not changed
(the separate, researcher-approved M07 context-text change is described in
§2.5).

### 2.5 M07 R03/R05 approved context text applied verbatim (second pass)

Agent C delivered the exact strings in `phase3/final/C_M07.md` §4. Agent E
applied them verbatim to the frozen authority — `07_Sample_Matrix`, the CSV
mirror and `MMU_Formal_Config.json/.yaml` — changing only:
`DynamicContext`, `TargetVA`, `AccessMode` (unchanged value), `TargetEvent`,
`TargetInstruction`, `OracleMethod`. ModelID, WorkloadID, SampleRunID, the
40-sample count, Seed/SeedPolicy/SeedSource/SampleFreezeStatus and all other
columns are unchanged. Proof:

```
csv rows 40 json 40 yaml 40
unique 40 json ids equal True yaml ids equal True
seed {'N/A_DETERMINISTIC'} {'N/A_DETERMINISTIC'}
== M07-F0-W14-S01-R03
   DynamicContext = EL0 load through an execute-only (PROT_EXEC) user mapping; ...
   AccessMode = Read
== M07-F0-W14-S01-R05
   DynamicContext = EL0 instruction fetch through a valid XN user mapping ...
   AccessMode = Execute
xlsx M07-F0-W14-S01-R03 AccessMode Read TargetVA execute-only VA 0x400d200000
xlsx M07-F0-W14-S01-R05 AccessMode Execute TargetVA XN indirect-branch code VA 0x400d600180
sheets has record: True
change log rows 12
```

Before/after/reason/approval/workload/golden/trace/final-verification are in
`phase3/final/M07_CONTEXT_CHANGES.json`, the new workbook sheet
`17_M07_Context_Change_Record` (12 column-level rows) and two new
`13_Change_Log` rows (`v2.1-M07`), plus the Markdown
`phase3/freeze/MMU_Change_Log.md`. Golden controls:
`runs/TEST-F1-M07-CTRL-R03/Run_Log/golden_output.txt` and
`runs/TEST-F1-M07-CTRL-R05/Run_Log/golden_output.txt`; trace/final
verification is explicitly **PENDING** Main's final run (no claim of
completion). A byte-identical pre-edit backup is in
`phase3/final/authority_backup/`.

---

## 3. Preflight — 40/40 with real evidence

New checks added to `tools/mmu_formal_preflight.py` (all evidence-based):

| Check | What is verified |
|---|---|
| `check_sample_id` / triple | 40 unique SampleRunIDs, ModelID/WorkloadID/ContextID against worksheets 03/05/06/07 and the CSV mirror |
| `check_seed` | Seed literal `N/A_DETERMINISTIC`, SeedPolicy `DETERMINISTIC`, SeedSource `RESEARCHER_APPROVED`, text cell |
| `check_injection_location` | Worksheet 05 `SourceFile`/`Function` exists in the **real** C++ (arm path preferred); the real hook site (or the model accessor, e.g. `mmuM02ShouldCorrupt`) is in the declared file |
| `check_w10_pfn_mapping` | M02 PFN from a real independent no-fault scoped W10 control; missing → `BLOCKED_MISSING_W10_PFN_MAPPING` |
| `check_runner_pfn_hardcode` | No literal `--mmu_m02_old_pfn 0x…` in the runner scripts |
| `check_access_mode` / variant | W10S samples keep Excel WorkloadID `W10`; internal variant `W10S-COLD-STORE` / `W10S-WARM-STORE`, `run_workload=W10S` |
| `check_build_provenance` | Pilot manifest must exist (`NO_MANIFEST` → `BLOCKED_BINARY`), `gem5_sha256` and six source hashes must equal the frozen config, the **on-disk** `gem5.opt` hash must equal the frozen/final hash, and the manifest `git_head` must be present (and equal the declared commit) |
| final binary | Read only from `phase3/final/FINAL_BINARY.sha256`; absent → explicit `PENDING_MAIN_FREEZE`, never guessed |
| `check_trace_schema` | Worksheet 09 fields (FaultID/EventID/ParentEventID/DynamicInstSeqNum/VA/PA) are present and emitted by `CHAOSPropagation.cc` and parsed by `mmu_trace_validate_v3.py` |
| `check_oracle` + `check_control_independence` | Golden oracle exists and is an independent no-fault run; for W10/W10S it must be single-context (measured allocation-history difference) |

`BLOCKED_MISSING_W10_PFN_MAPPING` was added to the status vocabulary and
precedence (after decoy, before trace). The summary/CSV also carry
`FinalBinarySHA256`, `FinalBinaryStatus`, `ActualBinarySHA256`,
`SourceCommitManifest`, `SourceCommitStatus`, `M02OldPFN`, `VariantStatus`,
`InjectionLocationStatus`, `TraceSchemaStatus`.

### 3.1 Current preflight (mid-integration, honest)

Command and real output:

```
$ python3 tools/mmu_formal_preflight.py --outdir phase3/formal \
    --summary-json phase3/formal/preflight_summary.json
{
  "samples": 40,
  "primary_counts": {"BLOCKED_BINARY": 40},
  "all_blocker_counts": {
    "BLOCKED_BINARY": 40,
    "BLOCKED_MISSING_W10_PFN_MAPPING": 5,
    "BLOCKED_ORACLE": 13,
    "BLOCKED_TRACE": 14
  },
  "final_binary_sha256": "<PENDING_MAIN_FREEZE>",
  "final_binary_status": "PENDING",
  "w10_pfn_map": {"contexts": {}, "detail": "runs: 0/5 contexts",
                  "present": false},
  "trace_schema_ok": true,
  "seed_gate_fail_count": 0,
  "triple_issues": []
}
```

Why all 40 are BLOCKED_BINARY at this instant: a C++ integration build is in
progress and the on-disk binary is now
`04d6b260c08a481df38e5d90229d2181d8e6521f294ad3e5d5cde000e07f4631`, not the
frozen `a71ce0ca…`. The preflight correctly refuses READY. Example row:

```
M01-F0-W9-S01-R02 | BLOCKED_BINARY
  prov: on-disk gem5.opt sha256=04d6b260… != frozen a71ce0ca…
  bin: PASS src: PASS commit: PASS 2a8422b42dcd | actual: MISMATCH
```

---

## 4. Preflight command sequence (after Main's final runs)

```bash
cd /home/sdc/gem5-fi-mmu-impl-v2

# 0) Main writes the frozen binary/commit (never guessed by the tools):
#    phase3/final/FINAL_BINARY.sha256
#    phase3/final/FINAL_SOURCE_COMMIT
#    and the final-run mapping phase3/formal/final_runs.json
#    { "M01/R01": {"run_id": "M01-F0-W9-S01-R01", "control_run": "..."}, ... }

# 1) Rebuild the evidence index FROM THE FINAL RUNS.  --revalidate computes
#    fresh verdicts from each real trace and writes them under
#    phase3/formal/revalidated/ (run directories are never modified).
python3 tools/mmu_build_evidence_index.py \
  --manifest phase3/formal/final_runs.json --revalidate \
  --out phase3/formal/evidence_index.json

# 2) Collect the five independent no-fault scoped W10 controls into the
#    per-context PFN map (M02 needs all five; absent contexts block).
python3 tools/mmu_collect_w10_pfn.py

# 3) Preflight (static only; never launches gem5).
python3 tools/mmu_formal_preflight.py --outdir phase3/formal \
  --summary-json phase3/formal/preflight_summary.json

# 4) Readiness CSVs + Markdown.
python3 tools/mmu_readiness_matrix.py

# 5) Build the 20-artifact package (add --refresh to re-run steps 1–4).
python3 tools/make_final_formal_package.py --refresh
```

Controls must be produced with the real no-fault path, e.g.:

```bash
MMU_CTX=R02 phase3/run_scripts/run_mmu_case.sh \
  runs/TEST-CTRL-W10-R02 TEST-CTRL-W10-R02 W10 NONE
python3 tools/mmu_collect_w10_pfn.py
```

The focused test (no gem5):

```bash
python3 tools/tests/test_mmu_formal_authority.py   # -> ALL TESTS PASS
```

### 4.1 Excel / CSV / JSON / YAML exact consistency (verified)

```
counts excel/csv/json/yaml: 40 40 40 40
ids equal: True
all 13 fields identical across xlsx/csv/json/yaml: True
seed policy: {'DETERMINISTIC'} {'DETERMINISTIC'}
binary SHA json/yaml equal: True a71ce0ca21de143d
source SHA json/yaml equal: True
workload SHA json/yaml equal: True
workloads: ['W10', 'W11', 'W12', 'W13', 'W14', 'W9'] contexts: ['R01', 'R02', 'R03', 'R04', 'R05']
```

The 13 compared fields are ModelID, WorkloadID, ContextID, DynamicContext,
TargetVA, AccessMode, TargetEvent, TargetInstruction, OracleMethod, Seed,
SeedPolicy, SeedSource, SampleFreezeStatus. W10S is not a WorkloadID (the
two store samples keep `W10`; the preflight verifies the internal variant).

---

## 5. Fields that MUST be filled after the final runs (explicit PENDING)

These are deliberately not guessed. Until they exist the preflight cannot
emit READY:

1. `phase3/final/FINAL_BINARY.sha256` — Main's post-integration binary SHA
   (the builder records `PENDING_MAIN_FREEZE` while absent).
2. `phase3/final/FINAL_SOURCE_COMMIT` — the source commit for that build.
3. `phase3/formal/final_runs.json` — mapping `Model/Context -> {run_id,
   control_run}` for the 40 formal runs (use `phase3/freeze/pilot_runs.json`
   as the schema reference).
4. `phase3/formal/w10_pfn_map.json` — five per-context target PFNs from
   independent no-fault scoped W10 controls (currently `present=false`).
5. Per-context scoped no-fault controls for M02/M06/M08 (W10) — the legacy
   `--ctx all` control is not valid for scoped runs.
6. M06 R03/R04/R05: a real `exception_delivery` (or a researcher-approved
   terminal amendment). Without it they remain `BLOCKED_TRACE`.
7. M07 R03/R05 *final verification* only: the exact approved text is now
   applied (see §2.5), but the golden/trace/final-run verification is
   PENDING Main's final binary (`phase3/final/M07_CONTEXT_CHANGES.json` marks
   it PENDING; it does not claim completion).
8. The frozen config's `gem5_sha256`/`source_sha256` must be updated to the
   final build when Main freezes it (currently they describe `a71ce0ca…`).

---

## 6. Authority inconsistencies found

1. **M02 PFN**: `0x83480` was hardcoded while the scoped R02 target is
   `0x834b6`. Fixed by data-driven resolution; never applied again.
2. **Legacy W10 control**: `runs/TEST-ENV-CTRL-W10` is an `--ctx all` run
   (`0x83480`, sentinel `0x7d`), still the default `CONTROL_ORACLE_RUNS`
   entry for M02/M06/M08. Scoped runs differ (`0x834b6`, `0x63`). The
   preflight now marks it not independent for W10/W10S; Main must produce
   per-context controls.
3. **Stale formal mapping**: `phase3/formal/pilot_runs.json` had 32 entries
   and pointed at older runs without real `gem5_sha256`; the authoritative
   `phase3/freeze/pilot_runs.json` has 34. Synced the formal copy for the
   current rebuild; Main's `final_runs.json` supersedes it.
4. **Binary drift during integration**: on-disk `gem5.opt` is
   `04d6b260…` while the frozen config says `a71ce0ca…`; the preflight
   correctly reports `BLOCKED_BINARY` (not a false READY).
5. **M06 over-claim**: R03B/R04B/R05B (and their B2 reruns) were reported
   `DETECTED_CONTAINED` with `exception_delivered=0`. Tightened to
   `TRACE_INCOMPLETE`; no Excel terminal was changed silently.
6. **Script location**: there is no `tools/run_mmu_case.sh`; the production
   script is `phase3/run_scripts/run_mmu_case.sh`. It had the same hardcoded
   M02 PFN and an M05 `--mmu_target_n 12` bug (2 MiB pages need 21). Both
   fixed.
7. **M05/W13 control PFN**: the all-context W13 control's `target_pfn`
   (`0x8355b` for R01) differs from the scoped M05 run (`0x83546`), but the
   oracle fields actually used (`sentinel=0x7d`, `decoy_sentinel=0x51`) agree.
   It is accepted as an independent control; only W10 has the measured
   sentinel/PFN coupling that requires single-context controls.
8. **M07 approved text**: Agent C delivered the exact R03/R05 strings
   (`phase3/final/C_M07.md` §4); they were applied verbatim in a second pass
   (see §2.5). No text was invented; only the final-run verification remains
   PENDING.

---

## 7. Deliverables produced by this agent

- Tool changes: `tools/mmu_formal_runner.py`,
  `tools/mmu_formal_preflight.py`, `tools/mmu_formal_validate.py`,
  `tools/mmu_build_evidence_index.py`, `tools/mmu_readiness_matrix.py`,
  `tools/mmu_collect_w10_pfn.py` (new),
  `tools/make_final_formal_package.py` (new),
  `tools/tests/test_mmu_formal_authority.py` (new),
  `phase3/run_scripts/run_mmu_case.sh`.
- Data/report outputs: `phase3/formal/evidence_index.json` (34 keys,
  revalidated), `phase3/formal/revalidated/` (53 trace-derived verdicts),
  `phase3/formal/MMU_40_Sample_DryRun.csv`,
  `phase3/formal/MMU_Context_Readiness_FINAL.csv`,
  `phase3/formal/MMU_Model_Readiness_FINAL.csv`,
  `phase3/formal/MMU_Readiness_Matrix_FINAL.md`,
  `phase3/formal/preflight_summary.json`,
  `phase3/formal/pilot_runs.json` (synced to the authoritative 34-entry map).
- Authority second pass (M07): `phase3/freeze/authority/` workbook, CSV,
  JSON and YAML; `phase3/final/M07_CONTEXT_CHANGES.json`;
  `phase3/final/M07_authority.diff`; `phase3/freeze/MMU_Change_Log.md`;
  pre-edit backup in `phase3/final/authority_backup/`.
- Package: `phase3/final/MMU_Final_Formal_Readiness_Package/` (20 required
  artifacts: `00_MANIFEST.json` + 19 content files) and
  `phase3/final/MMU_Final_Formal_Readiness_Package.zip` (+ `.sha256`).
- This report + `phase3/final/E_authority_tools.diff`.

No commit/push was made: the worktree is shared with the other agents and
Main integrates/commits (T6). The original `/home/sdc/gem5-fi-mmu` is
untouched.
