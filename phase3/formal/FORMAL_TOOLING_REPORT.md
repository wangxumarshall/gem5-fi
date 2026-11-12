# Phase-3 Formal MMU Experiment Tooling Report

Status date: 2026-11-10 (live workspace snapshot).
No gem5 process was launched by this task. No seed was generated, hashed,
timestamped or defaulted.

## 1. Deliverables

| File | Purpose |
|---|---|
| `tools/mmu_formal_preflight.py` | 40-sample authoritative cross-check + live-tree readiness dry-run |
| `tools/mmu_formal_runner.py` | Formal (authoritative Excel, seed-gated) and PILOT (deterministic eligible-event) runner |
| `tools/mmu_formal_validate.py` | Terminal-aware M01-M08 validator built on the v4 parser |
| `phase3/formal/MMU_40_Sample_DryRun.csv` | Per-sample machine-readable dry-run |
| `phase3/formal/MMU_40_Sample_DryRun.md` | Per-sample human-readable dry-run |
| `phase3/formal/Missing_Seed_Report.md` | Seed-gap report with all other checks tallied per sample |
| `phase3/formal/preflight_summary.json` | Machine-readable summary (hook/workload evidence included) |

`tools/mmu_formal_validate.py` is a new file on disk (the earlier dry-run
claim of validator support is now backed by the actual implementation).

## 2. Usage

### 2.1 Preflight / dry-run (never runs gem5)

```bash
cd /home/sdc/gem5-fi-mmu-impl-v2
python3 tools/mmu_formal_preflight.py --dry-run
# optional: --outdir phase3/formal --summary-json phase3/formal/preflight_summary.json
```

Inputs (read-only): the authoritative Excel, `MMU_Sample_Matrix.csv` and
`MMU_Final_Experiment_Config.json` under
`/home/sdc/mmu_phase1_work/design/MMU_Final_Design_Package/`.

Status vocabulary is exactly:

```
READY, BLOCKED_MISSING_SEED, BLOCKED_HOOK, BLOCKED_WORKLOAD,
BLOCKED_CONTEXT, BLOCKED_TRACE, BLOCKED_ORACLE, BLOCKED_CONFIG
```

Primary-status precedence (implemented in `STATUS_PRECEDENCE`):

```
HOOK > WORKLOAD > CONTEXT > CONFIG > TRACE > ORACLE > SEED
```

Every sample also carries an `all_blockers` column. A missing seed never
stops the other checks and never suppresses another blocker.

### 2.2 Formal runner (seed-gated)

```bash
python3 tools/mmu_formal_runner.py --sample M08-F0-W10-S01-R01 --describe
python3 tools/mmu_formal_runner.py --sample M08-F0-W10-S01-R01
```

* Reads ModelID/WorkloadID/ContextID/ROI/target event/Seed from the Excel.
* Validates the triple against worksheets 03/05/06/07.
* Refuses a formal sample whose workload rcS cannot isolate its ContextID
  (`BLOCKED_CONTEXT`, exit 5).
* If the Seed cell is missing/placeholder (`NEEDS_AUTHORITATIVE_EXCEL`), it
  refuses with **exit 3 / BLOCKED_MISSING_SEED** before any other check.
  There is no default/random/hashed/timestamped fallback.
* Writes `runs/<SampleRunID>/` with a fresh `mmu_template.img` copy, and
  refuses to overwrite a non-empty run directory (exit 4).
* Derives a **single-context rcS** under the run directory (`rcS.scoped`) from
  the real workload script (`--ctx all`/`--all` -> `--ctx <SampleRunID
  context>`, or a per-context W9 script). The workload rcS normally runs all
  five contexts, but the MMU fault latch is one-shot: without this scoping,
  every R02-R05 sample would inject into the first context. The source rcS is
  never modified.
* Captures `command.txt`, gem5 exit code, `board.terminal`, `config.ini/json`,
  `prop_evt.txt.gz`, `prop_trace.csv.gz`, the `W9..W14_RESULT` golden lines and
  a SHA256 manifest.
* Automatically invokes `tools/mmu_formal_validate.py` and stores
  `Validation/verdict.json` and `Validation/verdict.md`.

Exit codes: 0 success, 2 usage/triple, 3 missing seed, 4 output exists,
5 other BLOCKED_* precondition, 6 gem5/validator failure.

**Seed semantics gap:** the authoritative package defines no seed semantics
for the MMU injectors (worksheet 12 B10). The runner therefore records the
authoritative seed in `sample_manifest.json` with
`seed_used_by_gem5=false`. It never substitutes a value. This is an open
design item, not silently invented behaviour.

### 2.3 PILOT runner (no seed, deterministic eligible event)

```bash
python3 tools/mmu_formal_runner.py --pilot TEST-M05-P3-R01 \
  --model M05 --workload W13 --context R01 \
  --target 0x4010000000 --eligible-event-index 1 --describe
```

PILOT runs are labelled `run_kind=PILOT`, `formal=false` and `seed=""` in the
manifest; they cannot be mistaken for formal samples. They still use a fresh
disk copy, refuse overwrite, capture the same artifacts and run the validator.

### 2.4 Validator

```bash
python3 tools/mmu_formal_validate.py --run-dir runs/<RUN-ID> \
  --model M08 --workload W10 --context R01 \
  --report-json .../verdict.json --report-md .../verdict.md
```

It imports `mmu_trace_validate_v4.py` (which imports v3) for parsing, event
access, parent-edge helpers and, for M01/M02, the v3 chain evaluation and the
v4 M02 entry-lineage audit. Parsing is not duplicated.

Emitted fields (exact top-level keys):

```
ActivationStatus, FaultConsumptionStatus, PropagationStatus,
TraceCompleteness, MissingCausalEdges, TerminalState, OracleResult,
fault_id, activation_event_id, consumption_event_id
```

plus `RecordIntegrity`, `OracleEvidence`, `parse_skipped`, `trace_read_error`
and a `Details` block with the evidence/proof basis.

Model-specific realities encoded:

* **M06** — exception path. `pte_decode` + local `descriptor_before/after`
  (bit0 1→0) and `descriptor_type=Invalid` are the causal evidence. No LSU
  request and no normal commit are required. A Translation Fault/containment
  is an expected terminal.
* **M03** — fabricated hit. The consuming lookup must be a hit bound to a real
  entry identity (`candidate_entry_id/generation`) with a foreign ASID
  (`candidate_asid != asid`); otherwise the oracle diff is `NOT_OBSERVED`.
* **M04/M05** — persistent entry faults. Consumption/reuse is keyed by
  `(tlb_instance, entry_id, generation)`; M05 additionally requires the L2
  partial next-table substitution (`next_table_pa_before != after`) and a
  later partial hit.
* **M08** — request-PA-only fault. `old_pa != new_pa` with `old_pfn == new_pfn`
  (TLB entry unchanged) and a consumer carrying the new PA.
* **M07** — permission inversion `false -> true`; the pre-activation
  `permission_eval` is associated by the same `translation_id`, never by tick
  proximity.
* **M01/M02** — v3/v4 chain rules and the v4 lineage audit are retained
  unchanged; M01 additionally requires arm + matching suppressed TLBI(s) +
  same-entry lookup + disarm.

Context scoping: the validator selects the fault chain by explicit identity,
not "first fault in the file": W9/M01 by context ASID (220/224/228/232/236),
W10/W12/W13/W14 by the context's target VA, and W11 by the target VA (the model
is one-shot; more than one activation at that VA is reported as
`scope_ambiguous_multi_fault`) plus explicit ancestor closure. Run-level
`mmu_fault_unactivated`/`mmu_fault_summary` rows are kept as context-independent
evidence.

Honesty rules: a broken/truncated trace forces `TRACE_INCOMPLETE`; a missing
parent edge or kind is listed in `MissingCausalEdges`; `SDC` requires both an
oracle diff and a trace causal proof; otherwise the result stays
`TRACE_INCOMPLETE` / `NOT_OBSERVED`. If no fault activated, `OracleResult` is
`NOT_OBSERVED` (never `PASS`, which would be mistaken for a passed sample).

## 3. 40-sample dry-run result (real run)

Command actually run:

```bash
python3 tools/mmu_formal_preflight.py --dry-run \
  --summary-json phase3/formal/preflight_summary.json
```

Real tallies:

```json
{
  "samples": 40,
  "primary_counts": {"BLOCKED_MISSING_SEED": 40},
  "all_blocker_counts": {"BLOCKED_MISSING_SEED": 40},
  "triple_issues": []
}
```

* Exactly **40** unique SampleRunIDs and **40** unique
  ModelID/WorkloadID/ContextID triples.
* All 40 triples match worksheets 03/05/06/07 and the CSV mirror
  (`triple_issues=[]`).
* All 8 model hooks are present in the live C++ (grep evidence recorded in the
  dry-run MD).
* Trace support is verified against the file on disk: the preflight requires
  `tools/mmu_formal_validate.py` to exist and to contain the model profile; it
  no longer relies on a hard-coded capability claim.
* All workloads W9, W10, W10S, W11, W12, W13, W14 are present and runnable
  (binary + rcS + checkpoint + disk template + ROI).
* No sample has a hook/workload/context/config/trace/oracle blocker at this
  snapshot. The **only** blocker is the missing authoritative seed.

### 3.1 Transient ROI finding (recorded, then resolved by the live tree)

An earlier snapshot of `phase3/run_scripts/run_mmu_case.sh` used one generic
`W11|W12|W13|W14` ROI of `0x4000000000..0x4009000000`. That excluded
W13's target `0x4010000000` and W14's targets
(`0x400C000000..0x400D600000`), producing a transient dry-run tally of
`BLOCKED_CONFIG=10` (M05×5 + M07×5). The coordinator confirmed these are not
real blockers; the live run script now carries the verified per-workload
ranges and the re-run reports **0** config blockers. The ranges used are:

| Workload | Verified ROI |
|---|---|
| W9 | `0x4000000000..0x4000100000` |
| W10 | `0x4001000000..0x4001500000` |
| W10S | `0x4001400000..0x4001700000` |
| W11 | `0x4004000000..0x4007000000` |
| W12 | `0x4008000000..0x400B000000` |
| W13 | `0x4010000000..0x4010400000` |
| W14 | `0x400C000000..0x400E000000` |

### 3.2 Model parameters encoded from the verified workload facts

Preflight records these in each sample's `ConfigDetail`; the runner passes
them explicitly:

| Model | target_n | instance / walk | other |
|---|---|---|---|
| M01 | 12 | — | W9 VA + context ASID (220/224/228/232/236) |
| M02 | 12 | — | old PFN 0x83480, xor 1, DRAM guard |
| M03 | 12 | — | data VA 0x4004000000 (R01-R04), code VA 0x4005000000 (R05) |
| M04 | 12 | `dtb` (R01-R04), `itb` (R05) | decoy PFN from W12 control run (auto until pinned) |
| M05 | 21 | `l2_shared`, walk level 2 | `fault_persistence=entry_lifetime` |
| M06 | 12 | walk level 3 | — |
| M07 | 12 | — | `fault_persistence=one_shot` |
| M08 | 12 | — | mode Read (R01-R04), Write (R05) |

## 4. Seed report

`phase3/formal/Missing_Seed_Report.md` is generated from the real Excel.

* Missing authoritative seeds: **40 / 40**.
* Every `07_Sample_Matrix.Seed` cell currently reads
  `NEEDS_AUTHORITATIVE_EXCEL`.
* No sample is formally runnable until the authoritative Excel supplies a
  seed. Closing the seed gap alone is sufficient at this snapshot (no other
  blocker remains), but the seed-semantics gap (where the seed enters gem5)
  must also be defined before formal execution.

Runner refusal verified:

```text
$ python3 tools/mmu_formal_runner.py --sample M08-F0-W10-S01-R01
status: BLOCKED_MISSING_SEED, exit_code: 3, seed_cell: NEEDS_AUTHORITATIVE_EXCEL
```

`--describe` returns the same exit 3 and `would_run=false`, so a dry-run
cannot accidentally execute a formal sample.

## 5. Validator verification (real traces, no gem5)

Real Phase-2/Phase-3 traces already on disk were used. No artifacts were
modified.

| Run | Model/Context | Activation | Consumption | Propagation | Trace | Terminal | Oracle |
|---|---|---|---|---|---|---|---|
| `phase2_2/runs/M01_FINAL` | M01/R01 | ACTIVATED | CONSUMED | FULL | COMPLETE | SDC | FAIL |
| `phase2_2/runs/M02_R04` | M02/R04 | ACTIVATED | CONSUMED | FULL | COMPLETE | SDC | FAIL |
| `runs/TEST-M08-P3-R01` | M08/R01 | ACTIVATED | CONSUMED | FULL | COMPLETE | SDC | FAIL |
| `runs/TEST-M07-P3B-R01` | M07/R01 | ACTIVATED | CONSUMED | FULL | COMPLETE | SDC | FAIL |
| `runs/TEST-M06-P3-R01` | M06/R01 | ACTIVATED | CONSUMED | PARTIAL | COMPLETE | SQUASHED | PASS |
| `runs/TEST-M03-P3-R01` | M03/R01 | NO_ELIGIBLE_EVENT | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | NO_ELIGIBLE_EVENT | NOT_OBSERVED |

Evidence highlights (from the validator JSON):

* M01: `l2_shared entry 623:10 survived 2 matching TLBI(s), was consumed by
  lookup event 263, then disarmed`; `W9_RESULT ... observed=0xaa` → SDC.
* M02: faulted insert consumed by a later lookup with matching entry
  lineage; `W10_RESULT ... observed=0x51` → SDC.
* M08: `request PA 0x83480000 -> 0x83481000 with TLB pfn unchanged (0x83480);
  consumer event 4312 carries the new PA`; `observed=0x51` → SDC.
* M06: `L3 descriptor bit0 cleared (0x60000083480fc3 -> 0x60000083480fc2) and
  decoded Invalid`; the trace terminal is `SQUASHED`, so propagation is
  PARTIAL even though the trace evidence is complete.
* M07 (P3B, R01): `permission grant false -> true`; the W14 oracle shows
  `shared_changed=1`, `injected_success=1`, `result=FAIL` → SDC.
* M03 (R01): the run-level trace contains only
  `mmu_fault_unactivated reason=no_eligible_target_event` — no M03 activation
  at all. The validator reports `NO_ELIGIBLE_EVENT` and does not claim a
  fault effect. Engineering follow-up: the hook scans the *same* TLB instance
  (`dtb`) for a foreign-ASID candidate; the W11 pilot evidently left no
  candidate there. This is a workload/hook eligibility issue, not a validator
  issue.

### 5.1 M06 terminal-set finding

Worksheet 07 lists M06's expected terminals as
`DETECTED_CONTAINED, CRASH, INJECTION_NOT_ACTIVATED, HANG/TIMEOUT,
TRACE_INCOMPLETE`; the real M06 pilot terminal is `SQUASHED`. The validator
reports the observed terminal unchanged and flags
`terminal_expected_by_model=false` in `Details`; it does **not** rewrite the
design's terminal set. This is recorded for the design owner. It likely means
the M06 pilot hit a speculative (squashed) walk; a context that forces the
architectural Translation Fault may be needed for the DETECTED_CONTAINED arm.

### 5.2 Profile self-tests (synthetic, clearly not evidence)

Because M04/M05 pilot traces were still being written when this report was
produced, the validator was also exercised on minimal synthetic PROP-EVT
streams (in `/tmp`, not repo artifacts) that follow the real event contracts:

| Model | Result |
|---|---|
| M03 | ACTIVATED/CONSUMED/FULL/COMPLETE/SDC/FAIL |
| M04 | ACTIVATED/CONSUMED/FULL/COMPLETE/SDC/FAIL |
| M05 | ACTIVATED/CONSUMED/FULL/COMPLETE/SDC/FAIL |
| M06 | ACTIVATED/CONSUMED/FULL/COMPLETE/DETECTED_CONTAINED/PASS_EXPECTED_DETECTION |
| M07 | ACTIVATED/CONSUMED/FULL/COMPLETE/SDC/FAIL |
| M08 | ACTIVATED/CONSUMED/FULL/COMPLETE/SDC/FAIL |

Negative tests were also run: M03 without a real candidate identity yields
`OracleResult=NOT_OBSERVED` and `TerminalState=TRACE_INCOMPLETE` (never SDC);
M06 without an exception event requires no LSU/commit and stays
`PARTIAL/TRACE_INCOMPLETE`; a live/truncated gzip is reported as
`TRACE_INCOMPLETE` with `trace_read_error` instead of crashing.

## 6. Blockers and findings

| ID | Finding | Consequence / proposed minimal action |
|---|---|---|
| FOR-MISMATCH-01 | The brief's `gem5-fi-MMU-Final-Experiment-Plan.xlsx` does not exist; the package ships `gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx`. | Tools accept both, prefer the requested name if it appears, and record which was used. No design change. |
| FOR-SEED-01 | All 40 authoritative Seed cells are `NEEDS_AUTHORITATIVE_EXCEL`. | Formal execution blocked (exit 3). Needs authoritative seeds. No seed was invented. |
| FOR-SEED-02 | No seed semantics are defined for the MMU injectors (worksheet 12 B10). | Runner records the seed but does not pass it to gem5 (`seed_used_by_gem5=false`). Define the mapping before formal runs. |
| FOR-ROI-01 | The earlier generic W11-W14 ROI excluded W13/W14 target VAs. | Resolved in the live run script with per-workload verified ranges; preflight now uses them. |
| FOR-M05-01 | M05 requires 2 MiB (n=21) L2 partial pages, `l2_shared`, walk level 2, `entry_lifetime`; the legacy generic script default is n=12. | Formal runner passes the verified values; preflight records them. |
| FOR-M06-01 | A real M06 pilot terminals as `SQUASHED`, which is outside its worksheet-07 expected terminal set. | Reported, not rewritten. Design owner should confirm the speculative-walk arm vs the architectural Translation Fault arm. |
| FOR-CTX-01 | The W9-W14 rcS executes all five contexts, but the MMU fault latch is one-shot. Without scoping, R02-R05 formal samples would inject into the first context. | The runner now derives a single-context `rcS.scoped` per run; the validator scopes by ASID/VA and reports ambiguity. No source config change. |
| FOR-M03-01 | M03 R01 pilot produced `no_eligible_target_event` (no activation). | The same-instance (`dtb`) foreign-ASID candidate was absent. Engineering follow-up on the M03 workload/hook eligibility; validator honestly reports NO_ELIGIBLE_EVENT. |
| FOR-M03/M07-01 | M07-P3-R01 was still running; M04/M05 pilots not yet available at report time. | Validator handles truncated gzip honestly (`TRACE_INCOMPLETE`); re-run when the coordinator provides the completed trace paths. |
| FOR-ASSETS-01 | W11/W12/W13/W14/W10S hooks/workloads/rcS landed while this task was running. | Preflight is a live snapshot; re-run it after concurrent work settles. |

## 7. Reproduce the verification

```bash
cd /home/sdc/gem5-fi-mmu-impl-v2

# 1) 40-sample dry-run (no gem5)
python3 tools/mmu_formal_preflight.py --dry-run \
  --summary-json phase3/formal/preflight_summary.json

# 2) formal seed refusal (exit 3)
python3 tools/mmu_formal_runner.py --sample M08-F0-W10-S01-R01

# 3) pilot command construction, no execution
python3 tools/mmu_formal_runner.py --pilot TEST-M05-DESC \
  --model M05 --workload W13 --context R01 --target 0x4010000000 \
  --eligible-event-index 1 --describe

# 4) validator on existing real traces
python3 tools/mmu_formal_validate.py --run-dir phase2_2/runs/M01_FINAL \
  --model M01 --workload W9 --context R01 --report-json /tmp/m01.json
python3 tools/mmu_formal_validate.py --run-dir runs/TEST-M08-P3-R01 \
  --model M08 --workload W10 --context R01 --target-va 0x4001000000 \
  --target-mode Read --report-json /tmp/m08.json
```
