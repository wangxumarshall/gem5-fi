# Agent B — Manifest Consistency Report (LSU v3.3.3 preflight)

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch/HEAD:** `lsu-v3.3.1-context-workload-20261111` / `b8405580b09e9d85c59af0b64ed2215aba41a95a`
**Mode:** read-only. No gem5/scons was run; no runner/source/Excel was modified. Only this report was written.
**Live binary:** `build/ARM/gem5.opt` = `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`
**Live config:** `configs/se/lsu_proxy.py` = `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`

> **Contradiction with the supplied ground truth.** `audit_v3_3_3/README_GROUND_TRUTH.md:12-14`
> states final binary SHA `070d68a6…` and HEAD `3097ad82e7`; the live binary is `1126e0fd…`
> (verified by `sha256sum`) and HEAD is `b8405580…`. `README_GROUND_TRUTH.md:37-40`
> also states A01 ROI `1040–1234 (195)` and A03 ordinals `1059/1098/1137/1176/1215`;
> the v3.3.3 code, the ROI CSV and the v3.3.3 workbook all use A01 `585–713 (129)`
> and A03 `1040–1222 (183)`. Per the README's own instruction ("if you find a
> contradiction, report it with raw evidence") both are reported here; the live
> files and `LSU_v3.3.3_Final_Acceptance_Report.md:20-28,103` agree with each other,
> so the README is the stale artifact.

---

## 1. How manifests are generated (both paths)

### 1.1 run_pilot models (105/120 manifests)

Models: A01, FW02, FW05, SQ01, SQ03, SP05, DA04, LP01, MD04, LQ04 and the A03-CONTROL
leg. Call chain:

- `tools/lsu_v332_matrix.py:604 run_context()` chooses the driver. Anything that is
  not A03-fault or RP01 goes through `run_pilot_cmd()` (`:388-399`) which spawns
  `docs/.../platform/run_pilot.py`.
- `run_pilot.py:719 main()` loads the **frozen v3.2.7 workbook**
  (`run_pilot.py:48 EXCEL = ...v3.2.7.xlsx`) at `:749`, picks the sample row by
  `--context-index` (`:750-751`), then overwrites `sample["event_ordinal"]` with
  `--event-ordinal` (`:753-755`) and replaces the identity with a PILOT identity
  (`:763-766`, `run_id = PILOT-<model>`, `sub_task_id = PILOT-<model>-S01`).
- `run_pilot.py:803-819` calls `manifest.build_manifest()` and writes
  `<outdir>/manifest.json`; `run_pilot.py:1166-1226` separately writes
  `<outdir>/pilot_meta.json`.

Fields written by `manifest.py:61-141 build_manifest()`:

| Block | Fields |
|---|---|
| Identity | `schema_version`, `sample_run_id`, `run_id`, `sub_task_id`, `fault_id`, `model_id`, `seed`, `seed_source` |
| Fault | `fault.location`, `target_field`, `target_bit`, `normal_value`, `fault_value`, `injection_mode`, `injection_timing`, `target_event`, `event_ordinal` |
| Workload | `workload.path`, `path_source`, `sha256`, `oracle_expected` |
| Design | `warmup`, `roi` |
| Provenance | `gem5.binary`, `binary_sha256`, `config_script`, `config_script_sha256`, `output_dir`, `command`, `command_shell`, `environment{captured_at_utc,host,kernel,python}`, `manifest_sha256` |

Outcome fields (`injection`, `injection_count`, `injector`, `target_event_proof`,
`trace`, `classification.terminal_state`, `oracle_pass`, `run_role`, …) exist **only**
in `pilot_meta.json` (`run_pilot.py:1166-1225`), never in `manifest.json`.

### 1.2 Direct-driver models (15/120 manifests)

Models: A03 **fault** (5) and RP01 **fault + control** (10), i.e. the second and third
driver branches named in `tools/lsu_v332_matrix.py:9-15`.

- `run_context()` (`:621-646`) builds commands with `build_rp01_cmd()` (`:416-427`) or
  `build_a03_fault_cmd()` (`:402-413`), runs gem5 directly (`run_direct()`, `:575-595`),
  then calls `write_direct_artifacts()` (`:481-557`).
- `write_direct_artifacts()` writes `<outdir>/manifest.json` (`:501-521`) and
  `<outdir>/pilot_meta.json` (`:523-556`). It does **not** import `manifest.py`.

Fields written by the direct manifest (`:501-520`):

`schema`, `pilot_id`, `model`, `role`, `driver`, `binary`, `binary_sha256`,
`config`, `config_sha256`, `workload`, `workload_sha256`, `golden`, `event_ordinal`,
`seed`, `command`, `note`.

Fields written by the direct pilot_meta (`:523-556` + `extra`): `run_role`, `seed`,
`driver`, `workload`, `event_ordinal`, `exit_code`, `timed_out`, `elapsed_seconds`,
`oracle_expected`, `oracle_source`, `oracle_pass`, `checksum`, `terminal`,
`terminal_state`, `terminal_reason`, `terminal_qualifier`, `injection_count`,
`injector`, `classification`, plus A03/RP01-specific diagnostics.

### 1.3 Consequence: two incompatible schemas

| | run_pilot (105) | direct (15) |
|---|---|---|
| schema id | `lsu-run-manifest-v3.2` (`manifest.py:101`) | `LSU_V333_DIRECT_MANIFEST` (`lsu_v332_matrix.py:502`) |
| binary SHA path | `gem5.binary_sha256` | `binary_sha256` |
| config SHA path | `gem5.config_script_sha256` | `config_sha256` |
| workload ELF SHA | `workload.sha256` | `workload_sha256` |
| role | absent | `role` |
| manifest hash | `manifest_sha256` | absent |
| output dir / environment | present | absent |
| outcome fields | absent | absent |

A single consumer cannot read both without special-casing. This is root cause RC-1.

---

## 2. Field-by-field verdict (all 120 manifests)

Method: parsed every `audit_v3_3_3/runs/*/manifest.json`; a field counts as present only
if it exists and is not null/blank/`n/a`. Cross-checked against the frozen
`60_SAMPLE_MATRIX.csv`, `audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx`,
the executed `command.txt`, and the live binary/config hashes.

| Required field | run_pilot (105) | direct (15) | Verdict | Evidence |
|---|---|---|---|---|
| **ROI_Start** | 0/105 | 0/15 | **FAIL** | `manifest.py:126-127` writes only an opaque `roi` string; direct manifest has no ROI key (`lsu_v332_matrix.py:501-520`) |
| **ROI_End** | 0/105 | 0/15 | **FAIL** | same; value exists only in `tools/lsu_v332_matrix.py:58-89`, `tools/lsu_v332_report.py:47-65`, `tools/lsu_v333_workbook.py:60-71` |
| **Warmup** | 105/105 present, 0 valid | 0/15 | **FAIL (stale)** | 105 manifests literally `"warmup": "NEEDS_RESEARCHER_CONFIRMATION"`; source is v3.2.7 sheet `5.60个样本执行矩阵` WarmUp cell (verified via openpyxl) |
| **Percentile** | 0/105 | 0/15 | **FAIL** | `manifest.py` has no percentile field |
| **EligibleEventOrdinal** | 105/105 (as `fault.event_ordinal`) | 15/15 (as `event_ordinal`) | **PARTIAL** | value is correct for 95 executed fault/control commands (0 mismatches vs workbook `Executed_EventOrdinal`), but the field name does not distinguish design ordinal 1–5 from executed percentile ordinal, and 25 controls claim an ordinal that is not in their executed command (see §2.1) |
| **DynInstSeq** | 0/105 | 0/15 | **FAIL** | no key; workbook itself says `PENDING` for A03 and RP01 (`Fault_Sample_Manifest` DynInstSeq) |
| **PC** | 0/105 | 0/15 | **FAIL** | no key; workbook PC is `PENDING` for RP01 (A03 PC is recoverable from `addrpath_injections.log` but is not copied) |
| **Seed** | 105/105 | 15/15 | **PASS** | 120/120 equal the frozen `Seed` column for the corresponding model/context (0 mismatches) |
| **SampleRunID** | 0/105 frozen | 0/15 frozen | **FAIL** | `sample_run_id`/`pilot_id` is the run-dir name (`A01-R01-fault`), not the frozen `A01-F0-W1-S01-R01`; 120/120 missing the authoritative ID. `run_pilot.py:763-766` deliberately substitutes the PILOT identity and the matrix never passes `--preserve-sample-id` (`lsu_v332_matrix.py:388-399`) |
| **Role** | 0/105 | 15/15 | **PARTIAL** | direct `role` is correct for all 15; run_pilot has no role field (derivable from the run-dir suffix and from `pilot_meta.run_role`) |
| **Workload** | 105/105 | 15/15 | **PASS (content)** | 120/120 workload basename matches the workbook `Workload` column; ELF bytes match the recorded SHA |
| **ELF_SHA256** | 105/105 | 15/15 | **PASS** | `workload.sha256` / `workload_sha256`; spot-checked A01 `90a19003…`, FW02 `a08fb3a7…`, RP01 `3f880cba…` against `sha256sum` |
| **Binary_SHA256** | 105/105 | 15/15 | **PASS** | all 120 = live `1126e0fd…` |
| **Config_SHA256** | 105/105 | 15/15 | **PASS** | all 120 = live `8309da72…` |
| **InjectionEnabled** | 0/105 | 0/15 | **FAIL** | only `pilot_meta.injector.gate_enabled` exists |
| **InjectionCount** | 0/105 | 0/15 | **FAIL** | only `pilot_meta.injection_count` exists |
| **TerminalState** | 0/105 | 0/15 | **FAIL** | only `pilot_meta.classification.terminal_state` / `summary.json` |
| **OracleResult** | 0/105 | 0/15 | **FAIL** | only `pilot_meta.oracle_pass` / `classification.oracle_outcome`; RP01 fault is labelled `classification.oracle_outcome = FAIL` although there is no checksum (`no_checksum: true`), contradicting the accepted `NO_CHECKSUM` label in `LSU_v3.3.3_Final_Acceptance_Report.md:54` |
| `manifest_sha256` integrity | 40 ok / 65 stale | n/a (absent) | **FAIL** | see §2.2 |

### 2.1 Value-accuracy defects inside the fields that exist

1. **Phantom executed ordinals on 25 controls.** The 25 `INJECTOR_ABSENT` controls
   (FW02×5, LQ04×5, DA04×5, MD04×5, RP01×5) omit the injector and all its arguments
   from the executed command, yet their manifest still records `fault.event_ordinal`
   (13/25/37/49/61, 1–5, 135/340/544/749/954, 3/5/6/8/10) or direct `event_ordinal`
   (26/77/128/179/230). Evidence:
   `audit_v3_3_3/runs/FW02-R01-control/manifest.json` has `event_ordinal: 13`;
   `audit_v3_3_3/runs/FW02-R01-control/command.txt` contains no `event_ordinal` token.
   The manifest field conflates "paired design ordinal" with "argument actually passed".
2. **`run_id` is not unique.** All 10 A01 manifests share `run_id = PILOT-A01`
   (5 fault + 5 control); same for every other run_pilot model. Direct manifests have
   no `run_id` at all.
3. **`environment.captured_at_utc` is inside `manifest_sha256`.** Combined with the
   absolute `output_dir`, the hash is not reproducible if a run dir is moved/copied and
   is not a design-identity hash.

### 2.2 `manifest_sha256` is stale in 65/105 run_pilot manifests

Recomputing `sha256(canonical_json(manifest without manifest_sha256))` for all 105:

- 40 match: A01, FW05, DA04, LP01 (all runs, fault + control).
- 65 mismatch: A03-control (5), FW02 (10), LQ04 (10), MD04 (10), SP05 (10),
  SQ01 (10), SQ03 (10).
- 15 direct manifests have no hash.

Exact root cause, proven on `FW02-R01-fault`: `manifest.py:139-140` computes the hash
inside `build_manifest()`; `run_pilot.py:806-814` then mutates
`manifest["workload"]["path_source"]` to `"pilot_override (Excel path retained in
sample)"`; the hash is recomputed **only** when `args.seed != excel_seed`
(`run_pilot.py:815-818`), which is false for every matrix run (the matrix never passes
`--seed`). Recomputing the hash after restoring only that one string reproduces the
stored value exactly:

```
stored  : 434cdc80331ccef1ceb7128e0af74f37fa8c94592c4b597fba5809a78da30a03
computed: 434cdc80331ccef1ceb7128e0af74f37fa8c94592c4b597fba5809a78da30a03
MATCH
```

This is exactly the class of defect the final report claims not to have: a run manifest
integrity field that does not describe the file it is written into.

---

## 3. Config-read paths for the 12 models (and RP01's special path)

| Model | Driver | Seed source | Ordinal source | ROI source | Warmup source |
|---|---|---|---|---|---|
| A01 | run_pilot | v3.2.7 workbook row (`run_pilot.py:749-757`) | hard-coded `CONTEXTS` (`lsu_v332_matrix.py:65`) via `--event-ordinal` | hard-coded `CONTEXTS`; never passed to the runner | hard-coded flag `0` (`run_pilot.py:619-624`) |
| A03 fault | direct | hard-coded `CONTEXTS["A03"]["seeds"]` (`:66-69`) | hard-coded `CONTEXTS` `:66` | hard-coded | hard-coded flag `0` (`:410`) |
| A03 control | run_pilot | workbook row | `CONTEXTS` | hard-coded | flag `0` (`run_pilot.py:625-630`) |
| FW02 | run_pilot | workbook row | `CONTEXTS` `:70` | hard-coded | hard-coded (no warmup flag; FW02 branch `run_pilot.py:692-704`) |
| FW05 | run_pilot | workbook row | `CONTEXTS` `:72` | hard-coded | flag `0` (`run_pilot.py:678-681` has no warmup token; no warmup passed) |
| SQ01 | run_pilot | workbook row | `CONTEXTS` `:73` | hard-coded | flag `0` (`run_pilot.py:631-636`) |
| SQ03 | run_pilot | workbook row | `CONTEXTS` `:75` | hard-coded | no warmup token (`run_pilot.py:668-672`) |
| SP05 | run_pilot | workbook row | `CONTEXTS` `:77` | hard-coded | no warmup token (`run_pilot.py:673-677`) |
| DA04 | run_pilot | workbook row | `CONTEXTS` `:79` | hard-coded | flag `0` (`run_pilot.py:645-649`) |
| LP01 | run_pilot | workbook row | `CONTEXTS` `:80` | hard-coded | none (`run_pilot.py:662-667`) |
| MD04 | run_pilot | workbook row | `CONTEXTS` `:81` | hard-coded | none (`run_pilot.py:657-661`) |
| LQ04 | run_pilot | workbook row | `CONTEXTS` `:83` | hard-coded | none (`run_pilot.py:688-691`) |
| RP01 fault/control | direct | `CONTEXTS["RP01"]["seeds"]` `:85-88` | `CONTEXTS` `:85` | hard-coded | none |

Findings:

1. **ROI/warm-up/percentile are never read from the authoritative design at run time.**
   The runner never reads `audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx`
   or `audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv`; the only ROI consumer
   is the report/workbook builder. The authoritative values are duplicated in **three**
   hand-maintained Python tables: `tools/lsu_v332_matrix.py:58-89`,
   `tools/lsu_v332_report.py:47-65`, `tools/lsu_v333_workbook.py:60-71`. This violates
   the repo's "one classifier, no drift" rule. Today they agree (checked row-by-row);
   nothing prevents drift.
2. **Ordinals are hard-coded, not read.** The frozen matrix `EventOrdinal` is 1–5 and is
   ignored except as `excel_identity.event_ordinal` in pilot_meta; the executed
   percentile ordinal comes only from the `CONTEXTS` dict. The code comment
   (`tools/lsu_v332_matrix.py:54-89`) documents the re-census, but it is not machine-linked
   to the ROI CSV or workbook.
3. **Warm-up is hard-coded to 0** in the executed flags (`run_pilot.py:622,628,634,647`,
   `lsu_v332_matrix.py:410`). The v3.3.3 workbook says `WarmUp = 0`, so the value is
   currently correct but unverified at run time.
4. **Two independent command builders for RP01.** `tools/lsu_v332_matrix.py:416-427
   build_rp01_cmd()` and `run_pilot.py:705-713 build_model_extra("RP01")` encode the
   same RP01 command. The matrix bypasses run_pilot for RP01, so the run_pilot branch
   is dead code for this round; a future flag change in one will silently diverge.
5. **RP01's special path** (`tools/lsu_v332_matrix.py:621-646`): both roles are direct;
   fault uses `--chaos_lsqfwd --lsq_struct_mode rp01_skip_replay --max_faults 1
   --rng_seed <seed> --rp01_event_ordinal <ord> --rp01_watchdog_cycles 20000000`;
   control uses `--probability 0.0` and omits the injector. This is correct behavior,
   but (a) the control manifest still records the paired ordinal (see §2.1), and
   (b) the direct manifest records `golden` with a `0x` prefix (`0xf3b1c554273d23f7`)
   while A03 records it without (`728e604ffcec539d`), so a caller must normalize.
6. **The runner reads a different workbook from the authoritative one.** `run_pilot.py:48`
   points at `gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`; the v3.3.3 design
   workbook is read by `tools/lsu_v333_workbook.py` only (build-time, after the runs).

---

## 4. Will each future formal run auto-generate a unique manifest?

**No, not in the sense required for a formal campaign.** Current facts:

- 120/120 run-directory-derived IDs are unique, and 105/105 present hashes are unique.
- But 15/15 direct manifests carry no hash and no campaign/attempt discriminator.
- `run_id` is shared by 10 runs per model (`PILOT-A01` ×10, …).
- The identity is the **directory name only** (`lsu_v332_matrix.py:609`); no
  `campaign_id`, no `attempt`, no monotonic run index, no source HEAD.
- The hash covers wall-clock time and absolute paths, so it is run-instance-specific but
  not design-identity-specific and not reproducible after a copy.
- A rerun into the same base is destructive: `run_context()` does
  `rm -rf <outdir>` (`lsu_v332_matrix.py:611-612`) and the default base is the
  historical evidence tree (`:743-747`, default `audit_v3_3_3/runs`).

So a future campaign with the **documented** command (`--out-base runs/lsu/formal_v333`,
`LSU_v3.3.3_Final_Acceptance_Report.md:179-183`) will create 120 new directories and
manifests, but it will still not produce a campaign-level unique/complete identity, and
a second attempt would silently overwrite the first if the same base is reused.

### 4.1 Proposed source-level patch (do not apply now)

**New module `docs/gem5-fi/lsu/implementation_v3_2/platform/run_identity.py`**

- `load_identity_table()` reads the frozen `60_SAMPLE_MATRIX.csv` plus the v3.3.3
  workbook `Fault_Sample_Manifest`/`ROI_Context_Mapping` sheets and returns
  `{(model_id, context_id, role): RunIdentity}`.
- `RunIdentity` fields: `sample_run_id`, `run_id`, `sub_task_id`, `model_id`,
  `context_id`, `role`, `seed`, `design_event_ordinal`, `executed_event_ordinal`,
  `roi_start`, `roi_end`, `roi_n`, `percentile`, `warmup`, `workload`,
  `workload_identity_status`, `fault_config_id`.
- `validate()` asserts `roi_n == roi_end - roi_start + 1` and
  `executed_event_ordinal == roi_start + ceil(percentile*roi_n) - 1`, and that the seed
  equals the frozen seed; any mismatch raises (no defaults).
- Delete the three duplicated tables by importing this module from
  `lsu_v332_matrix.py`, `lsu_v332_report.py`, `lsu_v333_workbook.py`.

**`manifest.py`**

- `build_manifest(identity, role, campaign_id, attempt, gem5_bin, config_script, ...)`
  emits one schema (`lsu-run-manifest-v3.3`) with all fields in the §2 table:
  `identity{...}`, `trigger{design_event_ordinal, eligible_event_ordinal, roi_start,
  roi_end, roi_n, percentile, warmup}`, `target{dyn_inst_seq, pc, va, pa, lq_entry_id,
  sq_entry_id}`, `provenance{...}`, `outcome{injection_enabled, injection_count,
  terminal_state, terminal_reason, oracle_result, oracle_source}`.
- New `finalize_manifest(manifest, outcome)` adds the outcome block and computes
  `identity_sha256` (canonical design identity, excludes paths/time) and
  `manifest_sha256` (full record) **as the last operation**.
- `write_manifest()` calls `finalize_manifest()` itself so no caller can write a hash
  that does not match the bytes (fixes RC-2).
- Keep `pilot_id`/`run_id` separate from `sample_run_id`; never replace the frozen ID.

**`run_pilot.py`**

- Add `--campaign-id`, `--attempt`, `--role`, and always pass the frozen
  `--preserve-sample-id` for formal runs.
- Replace the v3.2.7 WarmUp/ROI read with `run_identity`; pass `--*_warmup_events
  <identity.warmup>` instead of the literal `0`; record the executed ordinal separately
  from the design ordinal.
- On control branches that omit the injector, set `executed_event_ordinal = null` and
  keep the paired ordinal under `design_event_ordinal` (fixes the 25 phantom ordinals).
- Refuse to overwrite an existing `manifest.json` unless `--force`.

**`tools/lsu_v332_matrix.py`**

- Add `--campaign-id`, `--attempt`, `--force`; put runs under
  `<out-base>/<campaign-id>/a<attempt>/<model>-R<ctx>-<role>`.
- Replace `rm -rf outdir` with: if it exists and `--force` is absent, abort the whole
  matrix with a clear error; if `--force`, move it to `_superseded/<utc>/` first.
- Route A03/RP01 through the same `build_manifest`/`finalize_manifest` writers (delete
  the private manifest dict in `write_direct_artifacts`).
- Emit `LSU_120Run_Campaign_Manifest.csv` (schema in §4.2) and a per-row `manifest_path`
  + `manifest_sha256`, plus a campaign header row (`campaign_id`, `attempt`, start
  time, source HEAD, binary/config SHA, expected 120 rows).
- Validate at the end: 120 unique `(campaign_id, attempt, sample_run_id, role)` rows,
  120 files, 0 hash mismatches, 0 missing outcome fields; non-zero exit otherwise.

### 4.2 Proposed `LSU_120Run_Campaign_Manifest.csv` schema

One row per run, 120 data rows + header, written after the run set; immutable per
attempt.

| Column | Type | Source |
|---|---|---|
| `campaign_id` | str | CLI |
| `attempt` | int | CLI |
| `run_index` | int | 1..120 |
| `model_id` | str | identity |
| `context_id` | str | `R01`..`R05` |
| `role` | str | `fault` / `control` |
| `sample_run_id` | str | frozen `A01-F0-W1-S01-R01` |
| `pilot_id` | str | run-dir name |
| `run_id` | str | design `RunID` |
| `sub_task_id` | str | design `SubTaskID` |
| `fault_config_id` | str | design |
| `seed` | int | frozen |
| `seed_source` | str | `excel:...` / `pilot_cli_override` |
| `design_event_ordinal` | int/null | design 1–5 |
| `executed_event_ordinal` | int/null | executed percentile ordinal |
| `roi_start` | int | authoritative ROI |
| `roi_end` | int | `roi_start + roi_n - 1` |
| `roi_n` | int | authoritative |
| `percentile` | float | 0.1/0.3/0.5/0.7/0.9 |
| `warmup` | int | authoritative (0) |
| `dyn_inst_seq` | int/null | trace injection event |
| `pc` | str/null | injection event; `PENDING` if absent |
| `va` | str/null | injection event |
| `pa` | str/null | injection event |
| `lq_entry_id` | int/null | injection event |
| `sq_entry_id` | int/null | injection event |
| `workload_path` | str | executed |
| `workload_identity_status` | str | `FORMAL` / `OVERRIDE_APPROVED` |
| `elf_sha256` | str | `sha256sum` of executed ELF |
| `golden` | str | workbook/golden file |
| `binary_path` | str | executed |
| `binary_sha256` | str | live SHA |
| `config_path` | str | executed |
| `config_sha256` | str | live SHA |
| `injection_enabled` | bool | injector gate |
| `mount_flags` | str | executed command |
| `injection_count` | int | pilot_meta/summary |
| `terminal_state` | str | adjudicated |
| `terminal_reason` | str | adjudicated |
| `oracle_result` | str | `PASS`/`FAIL`/`NO_CHECKSUM` (honest label) |
| `oracle_source` | str | `excel` / `workload_golden` / `none` |
| `exit_code` | int | process |
| `timed_out` | bool | process |
| `trace_completeness` | str | trace report |
| `fault_command` | str | executed command |
| `outdir` | str | absolute |
| `manifest_path` | str | relative |
| `manifest_sha256` | str | recomputed from written bytes |
| `identity_sha256` | str | canonical design identity |
| `captured_at_utc` | str | run start |
| `source_head` | str | `git rev-parse HEAD` |

### 4.3 Validation commands for the patch

```bash
# 1. manifest shape + self-consistent hash on a two-run smoke
python3 tools/lsu_v332_matrix.py --models A01 --roles fault,control \
  --out-base /tmp/v333_manifest_smoke --campaign-id smoke --attempt 1
python3 - <<'PY'
import json,glob,hashlib
def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False)
req=["roi_start","roi_end","warmup","percentile","eligible_event_ordinal",
     "dyn_inst_seq","pc","sample_run_id","role","injection_enabled",
     "injection_count","terminal_state","oracle_result"]
for f in glob.glob('/tmp/v333_manifest_smoke/**/manifest.json',recursive=True):
    m=json.load(open(f)); missing=[k for k in req if k not in json.dumps(m)]
    sha=m.pop('manifest_sha256')
    assert hashlib.sha256(canon(m).encode()).hexdigest()==sha, f
    assert not missing, (f,missing)
print("OK")
PY

# 2. history guard: refuse to rewrite the v3.3.3 evidence tree
sha256sum audit_v3_3_3/runs/*/manifest.json > /tmp/before.sha
python3 tools/lsu_v332_matrix.py --models A01 --roles fault --contexts 1   # default base
# expect non-zero exit + "outdir exists; use --force"; then:
sha256sum -c /tmp/before.sha

# 3. unchanged-behaviour regression
python3 -m pytest tests/test_lsu_v333_workbook.py tests/test_lsu_12model_closure.py \
  docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_manifest_oracle.py -q
```

Regression risk: additive manifest fields change every `manifest_sha256` (expected);
`test_manifest_sha_is_stable` still passes because it builds twice with the same fixed
environment. Downstream consumers read `summary.json`/`pilot_meta.json` and the
generated CSVs, not `manifest.json`, so the blast radius is the manifest validators and
the workbook builder, both of which should import the new identity module. The guard
(`--force`/archive) changes rerun semantics and must be documented in the runbook.

---

## 5. Are historical pilot manifests preserved and not backfilled?

**Files are preserved today, but the tooling has a destructive default.**

- The 120 manifests under `audit_v3_3_3/runs/` exist (120 directories; 105
  `lsu-run-manifest-v3.2`, 15 `LSU_V333_DIRECT_MANIFEST`). The pre-correction round is
  separately preserved under `audit_v3_3_3/runs_685d88f7/` (120 manifests, all
  `685d88f7` binary), confirmed by parsing both trees.
- No report/workbook step writes back into the manifests: `tools/lsu_v332_report.py`
  only reads `summary.json`/`pilot_meta.json`/logs and writes CSVs;
  `tools/lsu_v333_workbook.py` reads CSVs and writes the xlsx. No backfill found.
- **Rewrite risk (concrete).** `lsu_v332_matrix.py:743-747` defaults
  `--out-base` to `audit_v3_3_3/runs`, and `run_context()` deletes any existing run dir
  (`:611-612`). Therefore the invocation
  `python3 tools/lsu_v332_matrix.py --models all --roles fault,control` **without**
  `--out-base` deletes and rewrites all 120 historical manifests. The documented formal
  command uses `--out-base runs/lsu/formal_v333`, so it does not touch the history, but
  nothing enforces that.
- `run_pilot.py` alone does not delete a directory but overwrites `manifest.json`,
  `pilot_meta.json`, `command.txt`, `oracle.log`, `stdout/stderr`, and the trace files
  in place (`run_pilot.py:782-819,837-850,1226`), so a direct per-model rerun can mix
  old auxiliary files with a new manifest.
- Manifests that would be rewritten by a default-base rerun: all 120 under
  `audit_v3_3_3/runs/`; by a single-model direct rerun: that model's 10 dirs. The
  preserved `runs_685d88f7/` tree is not referenced by the driver and is safe.

---

## 6. Root-cause list

| ID | Root cause | Evidence | Affected |
|---|---|---|---|
| RC-1 | Two independent manifest writers with different schemas | `manifest.py:61-141` vs `lsu_v332_matrix.py:481-521` | 105 vs 15 manifests; all consumers |
| RC-2 | `manifest_sha256` computed before post-hash mutation; rehash only on seed override | `run_pilot.py:806-818`, `manifest.py:139-140` | 65/105 stale hashes; 15 missing |
| RC-3 | run_pilot builds the manifest from the frozen **v3.2.7** sample whose `WarmUp`/`ROI` are `NEEDS_RESEARCHER_CONFIRMATION`; measured ROI/percentile never enter the manifest | `run_pilot.py:48,126-127,749-757`; v3.2.7 sheet 5; `manifest.py:126-127` | 105/105 stale warmup/roi; 0/120 ROI_Start/End/Percentile |
| RC-4 | ROI/ordinal identity is hand-copied into three Python tables and warm-up is hard-coded 0; no runtime read of the v3.3.3 workbook/ROI CSV | `lsu_v332_matrix.py:58-89`, `lsu_v332_report.py:47-65`, `lsu_v333_workbook.py:60-71`, `run_pilot.py:622,628,634,647` | all 12 models; future drift |
| RC-5 | run_pilot substitutes the PILOT identity and the matrix never passes `--preserve-sample-id` | `run_pilot.py:763-766`, `lsu_v332_matrix.py:388-399` | 120/120 manifests lack the frozen SampleRunID/run_id/sub_task_id |
| RC-6 | Design-time and executed-time values share one field; controls with omitted injectors keep a phantom ordinal | `manifest.py:118`, `lsu_v332_matrix.py:514` | 25 controls |
| RC-7 | Direct-driver manifest bypasses `manifest.py`: no hash, environment, frozen identity, or outcome | `lsu_v332_matrix.py:501-520` | 15/15 direct manifests |
| RC-8 | `rm -rf` + destructive default out-base | `lsu_v332_matrix.py:611-612,743-747` | 120 historical manifests at risk |
| RC-9 | Outcome fields live only in `pilot_meta`/`summary`; RP01 HANG labelled oracle FAIL | `run_pilot.py:1166-1225`, `lsu_v332_matrix.py:548-553`, `RP01-R01-fault/pilot_meta.json` | 120 manifests; 5 RP01 faults |
| RC-10 | No real manifest validator for these manifests; `manifest_validate.py` is selftest-only and `schemas/manifest.schema.json` describes runner.py's `arm-chaos-fi/v1` format | ledger `L-D11` OPEN; `tools/manifest_validate.py`; `schemas/manifest.schema.json` | all 120 manifests |

The final acceptance report's claims that "15/15 direct runs have manifest/oracle
(verified)" and "60/60 authoritative SampleRunID/Seed copied from the frozen matrix"
(`LSU_v3.3.3_Final_Acceptance_Report.md:120-121,149`) are true at the **workbook**
level and for the **seed** column, but not for the **manifest**: the manifests carry
PILOT IDs, and 65/105 of them have an integrity hash that does not match their bytes.

---

## 7. Bottom line

The v3.3.3 runtime identity **data** (seed, executed ordinal, workload, binary/config
SHA) is consistent with the frozen design across all 120 runs (0 mismatches), which is
the strongest part of this audit. The runtime **manifest contract** is not ready for a
formal campaign: it is split across two incompatible schemas, carries no frozen
SampleRunID, no ROI bounds/percentile, no warm-up value, no DynInstSeq/PC, and no
injection/terminal/oracle outcome; its integrity hash is stale in 65/105 files and
absent in the other 15; 25 controls advertise ordinals that were not executed. A future
run will produce unique directory names but not a unique, complete, campaign-attributable
manifest, and the driver's default invocation deletes the historical v3.3.3 evidence
tree. The one-shot fix is: one `run_identity` table read from the frozen matrix +
v3.3.3 workbook, one `build/finalize/write_manifest` path used by both drivers, campaign
id/attempt in the path and record, archive-instead-of-delete, and a 120-row
`LSU_120Run_Campaign_Manifest.csv`.

## 8. Could not verify

- That the formal campaign will be launched with the documented `--out-base`
  (`runs/lsu/formal_v333`) rather than the destructive default; this is an operator
  decision, not enforced in code.
- Any gem5 execution behaviour (forbidden in Phase 1); the proposed patch was not
  applied or built.
- The A03 `DynInstSeq` and RP01 `PC`: both are literally `PENDING` in the v3.3.3
  workbook, so they cannot be backfilled honestly from the authoritative design today.
- Whether `audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx` has received
  final researcher sign-off beyond the `ConfigFrozen=YES` cell; the workbook is
  generated by `tools/lsu_v333_workbook.py`, so it is a derived artifact.
- Any manifest validation gate: `tools/manifest_validate.py` remains selftest-only
  (ledger `L-D11` OPEN) and no LSU runner calls it. The manifests in this audit were
  verified only by the independent parsing described above, not by the repo's validator.
