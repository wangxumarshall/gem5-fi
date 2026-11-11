# Agent E — Fault/Control Pairing, Seed, Config Freeze & Hidden-Mount Audit

**Round:** LSU pre-formal finalization v3.3.0 (2026-11-11)
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch / HEAD:** `lsu-preformal-v3.3.0-20261111` @ `9e3d104c7a35eb73d1190981676eacea3dad25` (clean; only untracked scratch + plan file)
**Scope:** 12 models × 60 contexts (R01–R05). 74-model work excluded.
**Mode:** read-only. No gem5/scons run, no campaign. Evidence from on-disk pilot dirs, manifests, logs, Excel, git, `sha256sum`, `df`/`free`/`pgrep`, and `run_pilot.py --help` / `lsu_guard.py --help`.
**Deliverables:** `LSU_Fault_Control_Pair_Audit.csv` (68 rows), `LSU_Formal_Config_Freeze_Checklist.csv` (35 rows), this file.

---

## 0. Bottom line

- **Controls:** 25 valid control runs, **1 invalid (historical misfire, `SUPP-FW02-C01`)**, 0 attempted-but-missing dirs. But context coverage is only **18/60** — 42 contexts have **no matched control** (all of DA04/FW05/LP01/MD04, and R02–R05 for FW02/SP05/SQ01/SQ03, R03–R05 for A01, R02–R04 for A03).
- **Config freeze: NOT frozen.** `ConfigFrozen=NO` on all 60 rows, warm-up/ROI `NEEDS_RESEARCHER_CONFIRMATION` on all 60, only 20/60 are `PILOT_ONLY_NOT_FORMAL`, 40/60 `BLOCKED_NO_HOOK`.
- **Evidence is spread over 4 different gem5 binaries and 3 different `lsu_proxy.py` versions.** Only A01/A03 (C-suffixed reruns) and RP01 evidence is on the formal-baseline binary `68c6ce73`; the binary used for FW02/SP05/SQ01/SQ03 (`720eb780`) and for FW05/LP01/MD04/DA04 (`e527f26a`) **is no longer on disk**. 6 models carry a stale config script.
- **Hidden-mount risk:** DA04's selector has **no probability gate** (same misfire class as FW02-C01) and MD04 is driven by a separate `--md04_probability` that `run_pilot.py` hard-codes to 1.0. Neither DA04 nor MD04 has a control today.

---

## 1. Control pairing (Task A)

### 1.1 Inventory of control runs (26 dirs)

| Model | Control dirs | Binary | Role fields | Injected | Verdict |
|---|---|---|---|---|---|
| A01 | `SUPP-A01-C01`, `-C01C`, `-C02`, `-C02C` | 720eb780 / **68c6ce73** (C) | CONTROL, `control_valid=true` | `CHAOS_LSU_TRIGGER … injected=0` | VALID |
| A03 | `SUPP-A03-C01`, `-C01C`, `-C05`, `-C05C` | 720eb780 / **68c6ce73** (C) | CONTROL, `control_valid=true` | `CHAOS_LSU_TRIGGER … injected=0` | VALID |
| FW02 | `SUPP-FW02-C01` | 720eb780 | CONTROL, `control_valid=false`, `control_misfire=true` | **1** (`lsq_fwd_injections.log`, Tick 556325) | **INVALID_MISFIRE** |
| FW02 | `SUPP-FW02-C02` | 720eb780 | CONTROL, `control_valid=true` | injector omitted, `injection_count=0` | VALID |
| SP05 | `SUPP-SP05-C01`, `-C01B` | 720eb780 | CONTROL, `control_valid=true` | `CHAOS_SP05_STATUS … injected=0` | VALID |
| SQ01 | `SUPP-SQ01-C01`, `-C01B` | 720eb780 | CONTROL, `control_valid=true` | `CHAOS_LSU_TRIGGER … injected=0` | VALID |
| SQ03 | `SUPP-SQ03-C01`, `-C01B` | 720eb780 | CONTROL, `control_valid=true` | `CHAOS_SQ03_STATUS … injected=0` | VALID |
| LQ04 | `LQ04-CONTROL-R01..R05` | f3c2a442 | role unset (older schema), `accepted=false` | injector omitted, `injection {events:[],injected:0}` | VALID (structural) |
| RP01 | `RP01-CONTROL-R01..R05` | **68c6ce73** | role unset | injector omitted, `injection_count=0` | VALID (structural) |
| DA04, FW05, LP01, MD04 | — | — | — | — | MISSING |

**Tally:** VALID = 25 runs; INVALID_MISFIRE = 1; MISSING (contexts with no control) = 42 of 60. No control dir was found partially written or with a corrupt manifest.

### 1.2 Zero-injection verification (not merely `--probability 0.0`)

Every valid control was checked for an actual zero-injection artifact:

- **A01/A03:** `stdout.log`: `CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0/F5 attempted=0 eligible=0 injected=0`; `pilot_meta.injection={}`.
- **SP05:** `lsq_fwd_injections.log`: `CHAOS_SP05_STATUS: selected=0 fired=0 injected=0 eligible=0` (log exists because the probability-gated injector is mounted, but it no-ops).
- **SQ03:** `CHAOS_SQ03_STATUS: fired=0 injected=0 eligible=0`.
- **SQ01:** `CHAOS_LSU_TRIGGER … injected=0` (no `lsq_fwd_injections.log`).
- **FW02-C02 / LQ04 / RP01:** the injector is **not mounted** (`config.ini` has only `board.chaos_propagation`), `injection_count=0`, `injection={events:[],injected:0}`. This is the strongest form of control (no injection path exists).

### 1.3 SUPP-FW02-C01 historical misfire — re-audited and confirmed

Confirmed directly from the preserved record (`pilots_v3_2_12/SUPP-FW02-C01/`):

- `pilot_meta.json`: `run_role=CONTROL`, `injection_count=1`, `control_valid=false`, `control_misfire=true`, `accepted=false`.
- `lsq_fwd_injections.log`: `Tick: 556325 … FaultType: f6_fw02_suppress … faults_injected: 1`, identical to `SUPP-FW02-R01`.
- Root cause (source-verified): `CHAOSLSQFwd` attaches at `probability==0` for the `F6Fw02` mode (`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:81-87,134-138`), and `maybeSuppressForwarding` never consults probability (`:1019-1071`). Hence `--probability 0.0` had **zero effect**.
- **The valid control pattern is to omit the injector** — exactly what `SUPP-FW02-C02` does (`run_pilot.py:617-629`, the LQ04 precedent). C02: injector omitted, `injection_count=0`, `control_valid=true`, `accepted=true`, runner exit 0, `NO_INJECTION_EVENT`. C01 is retained as honest evidence and must not be overwritten.

### 1.4 Matching quality (binary / workload / input / config / seed / ROI / dynamic context)

- **Workload & input:** every fault/control pair in a model uses the same workload ELF; all 12 workload SHA256 values were re-hashed from disk and match the manifests. All workloads are self-contained (`InputHash = N/A / 无（内建输入）`).
- **Seed / ordinal:** all 45 present fault pilots and all 26 controls match their Excel seed; matched controls reuse the fault context's seed and event ordinal (e.g. A01-C01C↔R01C ord 1; A03-C05C↔R05C ord 5; SP05-C01B↔R01B ord 940).
- **Binary:** pairs match each other (fault == control within a model), but **only the A01/A03 C-suffixed reruns and RP01 are on the formal-baseline binary `68c6ce73`**. FW02/SP05/SQ01/SQ03 pairs are on `720eb780`; FW05/LP01/MD04/DA04 on `e527f26a`; LQ04 on `f3c2a442`. `720eb780` and `e527f26a` are not present anywhere under `*/build/ARM/gem5.opt`, so those pairs are non-reproducible from disk.
- **Config:** A01/A03/FW02/SP05/SQ01/SQ03 = `01f912de` (current); FW05/LP01/MD04/DA04 = `2e1de853` (v3.2.11-era commit `ee1f00dc`); LQ04 = `9b270dbe` (v3.2.10-era commit `89f9569a`); RP01 manifest omits the config SHA.
- **Warm-up/ROI:** fault and control agree, but both are `NEEDS_RESEARCHER_CONFIRMATION` — unfrozen.
- **Dynamic context:** same seed+ordinal by construction; byte-level trace equivalence is **not** assertable for omitted-injector controls (e.g. FW02 C02 trace rows 6222 vs R01 6229; SP05/SQ01/SQ03 control 8011 vs fault 8014–8018) because the injection edge is absent. The LQ04 and RP01 controls are documented determinism replications (RP01: identical checksum `0x59fc61c040618747` across all five seeds).

CSV `LSU_Fault_Control_Pair_Audit.csv` holds one row per context (60) plus 8 supplementary control runs (alternates + the FW02-C01 misfire).

---

## 2. Formal config-freeze checklist (Task B)

35 checklist rows in `LSU_Formal_Config_Freeze_Checklist.csv`. Gate tally: **PASS 20 · FAIL 3 · BLOCKED 8 · NEEDS_APPROVAL 4**.

### PASS (verified this round)

- Branch/HEAD pinned; worktree clean.
- **Formal binary `68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8`** present on both `build/ARM/gem5.opt` and `CHAOS/gem5/build/ARM/gem5.opt`, matches `logs_v3_2_12/binary_v3212_final_candidate.sha256` and the `GIT_COMMIT_v3212.txt` FINAL block.
- Regression under the final binary: `reg_chain` O3 checksum `f247ef3fe6f02cfd`, exit 0, no SIGSEGV; W1–W8 9/9 PASS.
- Propagation tracer present (RP01 ran `--chaos_propagation` under `68c6ce73`).
- 60 SampleRunIDs, 60 unique seeds; Excel sheet-5 identity identical to v3.2.6.
- All existing seeds match Excel; all 12 workload ELFs match on-disk SHA.
- Resources: **disk 66 GiB free (81 % used)**, MemAvailable 25.3 GiB, SwapFree 11.4 GiB, **0 gem5 processes**, guard experiment slots 0/4.
- Timeout 900 s on all rows; watchdog cycles mounted for LQ04/SQ03/SP05/RP01.
- No-fault references exist (FW05 strict baselines R01–R05 PASS; LQ04/RP01 no-injector controls); RP01 count-only preflight 5×5 PASS.
- Platform test suite present (16 modules, including the 4-check FW02 control-mount test).

### FAIL

1. **`gem5Commit` in Excel sheet 5 = `6f98088a…`** — an ATLAS-diagrams commit, not the current code HEAD; stale provenance field on all 60 rows.
2. **Design paths stale** — `WorkloadPath`/`ConfigScript` point at `lsu-platform-v3.2` (55 rows) / `lsu-platform-v3.2.10` (5 rows), not this worktree.
3. **Config identity mismatch** — FW05/LP01/MD04/DA04 (`2e1de853`) and LQ04 (`9b270dbe`) built with older `lsu_proxy.py`; RP01 manifest has no config SHA.

### BLOCKED

- **Pilot binaries not uniform** and two (`720eb780`, `e527f26a`) absent from disk.
- **Warm-up/ROI unfrozen** (also NEEDS_APPROVAL).
- **Runner has no `--dry-run`** (`run_pilot.py --help`; only 11 of 12 models in `--model` — RP01 is driven separately).
- **`lsu_guard.py gate` returned `ok=false`** — "磁盘用量不可读（GUARD_DIR 所在盘）" on first sample (GUARD_DIR directory existence/timing); `status` afterwards read 65.9 GiB free. Gate must be re-run with a valid `GUARD_DIR` before launch.
- Preflight/execution/decision not formal-ready: 40 `BLOCKED_NO_HOOK`, 40 `NOT_RUN`, 35 `NEEDS_USER_DECISION`.
- Control coverage 18/60; fault pilots missing 6 (FW05-R01, MD04-R01/R04, DA04-R01/R02/R03).

### NEEDS_APPROVAL

- Warm-up/ROI values (all 60 `NEEDS_RESEARCHER_CONFIRMATION`).
- `ConfigFrozen` (all 60 `NO`).
- 35 open decision rows.
- Whether RP01's separate driver is acceptable in the formal runner.

**ConfigFrozen flag: NO (0/60). The configuration is not frozen and cannot be frozen until warm-up/ROI are set, the stale config/binary evidence is reconciled (re-run under `68c6ce73` + `01f912de` or an explicit researcher waiver), and the `gem5Commit`/path fields are corrected.**

---

## 3. Workbook identity check (Task C)

- **v3.2.6 vs v3.2.7, sheet `5.60个样本执行矩阵`:** 60 rows each, headers identical, **0 differences** in `SampleRunID / Seed / FaultModelID / RunID / SubTaskID`; no rows added or removed. The 60 identities and seeds are unchanged.
- **No v3.2.11 workbook exists.** The latest workbook is `…-v3.2.7.xlsx`; v3.2.8–v3.2.12 changes are recorded as additional sheets (`17.v3.2.9变更记录`, `18.v3.2.10变更记录`, `19.v3.2.11变更记录`, `20.v3.2.11传播链审计`, `21.v3.2.12变更记录`, `22.v3.2.12传播链闭包矩阵`). A v3.2.6 → v3.2.11 workbook diff is therefore not possible; the honest comparison is v3.2.6 → v3.2.7 (authoritative), which is unchanged.
- `60_SAMPLE_MATRIX.csv` agrees with Excel sheet 5 on `SampleRunID/Seed` (0 mismatches).
- Note: the design's `BinarySHA256` column actually carries the **workload ELF** SHA (e.g. `90a19003…`), and `BinaryPath` points at the workload. The gem5 simulator binary SHA is not in the matrix and must be sourced from `logs_v3_2_12/`.

---

## 4. Hidden injector mounts / mutation semantics (Task D)

`mutation_enabled` has **no occurrences** in `configs/`, `CHAOS/gem5/src/`, or the platform — it is not a live mount semantic in this tree. The real hazard is the ordinal-gated `CHAOSLSQFwd` attach list.

`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:81-87` attaches the injector when `probability > 0` **or** `struct_mode ∈ {F6Fw02, Da04BeBit0, Sq03CanWB, Sp05Complete, Fw05OlderSrc, Rp01CountOnly, Rp01SkipReplay}`. Whether a `--probability 0.0` control is safe depends on each selector's own gate:

| Model | Mode | Attaches at p=0? | Selector consults probability? | Control risk with p=0 |
|---|---|---|---|---|
| FW02 | `f6_fw02` | yes (`:134-138`) | **no** (`:1019-1071`) | **FIRES — confirmed misfire (C01)** |
| DA04 | `da04_be_bit0` | yes (`:128-133`) | **no** (`maybeCorruptStoreByteEnable`, `:972-1017`) | **FIRES if mounted — latent, no control yet** |
| FW05 | `fw05_older_src` | yes (`:81-87`) | yes — `probability<=0 → return false` (`:794`) | safe (no control exists) |
| SQ03 | `sq03_canwb` | yes | yes — `:734` | safe (verified injected=0) |
| SP05 | `sp05_complete` | yes | yes — `:538,576` | safe (verified injected=0) |
| SQ01 | `sq01_bit3` | no (hook blocked, `lsq_unit.cc:2120`) | attach-level | safe (verified injected=0) |
| RP01 | `rp01_skip_replay` | yes (`:201-206`) | ordinal-gated | safe only because controls omit the injector |
| MD04 | `--chaos_md04` | n/a | `maybeMD04` gates on **`--md04_probability`** (`CHAOSMD04.cc:77`), and `lsu_proxy.py:1094` / `run_pilot.py:578` pass **1.0 always** | **RISK: a `--probability 0.0` control via `run_pilot` still sets md04 probability 1.0** |
| LP01 | `--chaos_l1dfwd` | only if `probability>0` (`CHAOSL1DForward.cc:23`) | yes — `:73` | safe at p=0 (no control exists) |
| A01/A03 | `--chaos_addrpath` | only if `probability>0` (`CHAOSAddrPath.cc:35`) | yes — `:122` | safe (verified injected=0) |

**Conclusions for the main agent:**

1. DA04 must get the FW02/LQ04-style "omit the injector when `--probability 0.0`" branch in `run_pilot.py` **before** its controls are run, or its control will misfire exactly like FW02-C01.
2. MD04's control path is worse than a probability gate: `run_pilot.py` hard-codes `--md04_probability 1.0`, so the global `--probability 0.0` is ignored. Any MD04 control must either omit `--chaos_md04` entirely or add a control guard that also sets `--md04_probability 0.0`.
3. FW05, LP01, RP01 require no code change to run a safe control (probability-gated or injector-omitted), but none exist yet.
4. Do not rely on `--probability 0.0` as a control guarantee for any `CHAOSLSQFwd` mode in the attach list; always verify `injected=0` in the log/config.ini.

---

## 5. Recommended next actions (for the main agent, not executed here)

1. Decide ConfigFreeze policy: re-run all 12 models under `68c6ce73` + `01f912de`, or obtain a researcher waiver for the older-binary evidence (and record the binary/config split explicitly).
2. Set warm-up/ROI and flip `ConfigFrozen=YES` (researcher decision).
3. Add `run_pilot.py` control guards for DA04 (omit mount) and MD04 (force `--md04_probability 0.0` when `--probability 0.0`); add a `--dry-run` mode.
4. Add matched controls for the 42 uncovered contexts (at minimum one per model, ideally per context).
5. Correct the Excel `gem5Commit` and stale worktree paths; source the gem5 binary SHA from `logs_v3_2_12/`.
6. Re-run `lsu_guard.py gate` with a valid `GUARD_DIR` until `ok=true` before formal launch.

---

## 6. Environment snapshot (2026-11-11 ~10:27 CST)

- Disk `/home`: 354 G total, 270 G used, **66 G free (81 %)**; `lsu_guard status` `disk_free_gib=65.9`.
- MemAvailable **25.3 GiB**, SwapFree **11.4 GiB**, load 2.71.
- gem5 processes: **none** (`pgrep -a gem5.opt`). Guard experiment slots: **0/4**.
- `lsu_guard.py gate --json`: `ok=false` ("磁盘用量不可读") at first sample; `status` later read the disk OK — treat as a GUARD_DIR initialisation issue, not a real disk shortfall.
