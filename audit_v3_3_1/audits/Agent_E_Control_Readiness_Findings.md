# Agent E — Fault-Control Readiness (LSU v3.3.1)

**Round:** LSU v3.3.1 context/workload finalization (2026-11-11)
**Worktree (only worktree used):** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**HEAD:** `8f7a1354c36e9511505940dd27f59df66cb1b328` (branch `fix/r6-s-w1-continuation-20261101` in the parent repo; this worktree is clean at start)
**Mode:** read-only. No gem5 / scons executed. Evidence from on-disk pilot dirs, `config.ini`, `pilot_meta.json`, `manifest.json`, `command.txt`, `stdout.log`, `lsq_fwd_injections.log`, source grep, `sha256sum`, and CSV parsing.
**Deliverables:**
- `audit_v3_3_1/controls/LSU_60Context_Control_Readiness.csv` — 60 rows × 18 columns.
- this file.

Costs: 26 control directories inspected, 60 contexts mapped, 20 raw zero-injection artifacts quoted.

---

## 0. Bottom line

| Status | Count | Meaning |
|---|---|---|
| **READY** | **2** | Valid zero-injection control on the current baseline binary `d3807fbe` (A01-R02, FW02-R01). The control is behaviourally ordinal-free, so the ROI/percentile re-map needs only event re-extraction, not a re-run. |
| **NEEDS_REDO** | **16** | A valid zero-injection control exists, but it is on a superseded binary and/or config, and/or records an old event ordinal. Must be re-run on the next baseline. |
| **MISSING** | **42** | No matched control at all; only a no-fault baseline or nothing. |
| **INVALID (context-level)** | **0** | The one invalid run (`SUPP-FW02-C01`) is an *alternate* control for FW02-R01; that context's matched control is valid. It is retained and must never be reused. |

- **Control redo count = 58** control runs (16 re-run + 42 create) + **60 fault runs** re-selected at the new percentile ordinal = **118 runs**. Only 2 control traces are reusable (A01-R02, FW02-R01).
- **Zero-injection artifacts re-verified for all 18 existing controls** (quoted in §2). Every claim of "control" is backed by a real `injected=0` / `injection_count=0` / injector-absent artifact, not by `--probability 0.0`.
- **Hidden-mount verdicts:** DA04 **HIGH**, MD04 **HIGH**, FW02 **MITIGATED** (fixed by commit `364a6057` + `run_pilot.py:621-629`), RP01 **MEDIUM**, all other models **LOW** (§4).
- **ROI/percentile re-map:** it invalidates the *recorded ordinal context* of all 18 existing controls; the zero-injection property itself is ordinal-independent, so the 2 final-binary ordinal-free controls survive (§5).
- **Config is NOT frozen:** binary baseline split (`68c6ce73` vs current `d3807fbe`), stale config SHAs, stale absolute paths, stale Excel `gem5Commit`, warm-up/ROI unfrozen (§6).

---

## 1. Baseline binary and config identity (verified this round)

Commands actually run:

```
sha256sum build/ARM/gem5.opt CHAOS/gem5/build/ARM/gem5.opt
find . -name 'gem5.opt' -type f -exec sha256sum {} \;
```

Real output:

```
d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2  build/ARM/gem5.opt
d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2  CHAOS/gem5/build/ARM/gem5.opt
```

There is **exactly one binary** in the worktree, SHA `d3807fbe…`, and it is the v3.3 final candidate (`audit_v3_3_1/v33_package/A_Report/LSU_v3.3_BINARY_PROVENANCE.md`, `BINARY_SHA256_v3.3.txt`). The evidence binaries `68c6ce73`, `720eb780`, `e527f26a`, `f3c2a442`, `0de25644`, `8377c011`, `3e9148fc` are **not on disk** — the pairs on those SHAs are historical-only and cannot be reproduced from this worktree.

---

## 2. Per-context control pairing and zero-injection evidence

### 2.1 Existing controls (18 contexts) — quoted artifacts

| Context | Control | Binary | Zero-injection artifact (verbatim) | Verdict |
|---|---|---|---|---|
| A01-R01 | `SUPP-A01-C01C` | 68c6ce73 | `CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=0 eligible=0 injected=0` | valid |
| A01-R02 | `V33F-A01-C02` | **d3807fbe** | `CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=0 eligible=2 injected=0`; trace `COMPLETE`, oracle pass, exit 0 | valid, final binary |
| A03-R01 | `SUPP-A03-C01C` | 68c6ce73 | `CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F5 attempted=0 eligible=0 injected=0` | valid |
| A03-R05 | `SUPP-A03-C05C` | 68c6ce73 | `CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F5 attempted=0 eligible=0 injected=0` | valid |
| LQ04-R01…R05 | `LQ04-CONTROL-R01…R05` | f3c2a442 | `pilot_meta.injection = {"events": [], "injected": 0}`, `injection_count=0`; `config.ini` has only `board.chaos_propagation` (injector absent) | valid structural |
| SQ01-R01 | `SUPP-SQ01-C01` | 720eb780 | `CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=0 eligible=0 injected=0` | valid |
| SQ03-R01 | `SUPP-SQ03-C01` | 720eb780 | `CHAOS_SQ03_STATUS: fired=0 injected=0 eligible=0` | valid |
| SP05-R01 | `SUPP-SP05-C01` | 720eb780 | `CHAOS_SP05_STATUS: selected=0 fired=0 injected=0 eligible=0 target_seq=0` | valid |
| FW02-R01 | `V33F-FW02-C01` | **d3807fbe** | command omits `--chaos_lsqfwd`; `injection={}`, `injection_count=0`; cross-check `V33G-FW02-MOUNTED-P0`: `CHAOS_FW02_SUMMARY: observed=6 suppressed=0` | valid, final binary |
| RP01-R01…R05 | `RP01-CONTROL-R01…R05` | 68c6ce73 | `manifest.fault = "n/a (control: no injector attached)", event_ordinal=null`; `injection_count=0`; no `lsq_fwd_injections.log` | valid structural |

Source of each row: the control directory under
`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/` (or `pilots_v3_2_10/` for LQ04) and `audit_v3_3_1/v33_package/E_Evidence/runs/` for the V33F/V33G runs.

### 2.2 The only invalid control — `SUPP-FW02-C01`

`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-FW02-C01/`:

- `pilot_meta.json`: `run_role=CONTROL`, `injection_count=1`, `control_valid=false`, `control_misfire=true`, `accepted=false`.
- `lsq_fwd_injections.log`: `Tick: 556325 … FaultType: f6_fw02_suppress … faults_injected: 1` — identical to the fault `SUPP-FW02-R01`.

This is the pre-guard misfire. It is **INVALID_MISFIRE** and must never be reused, overwritten, or regraded.

### 2.3 Matching quality (ELF / input / seed / context / config / binary)

- **Same ELF:** yes for all 18 pairs. v3.3.0 audit (`audit_v3_3_1/v33_package/B_Audits/Agent_E_Config_Control_Findings.md` §1.4) re-hashed all 12 workload ELFs. Example: A01/A03 `agu_addrmodes` = `90a19003…`; LQ04 `lq_lifetime_ordinal` = `fa25f785…`; FW02 `sq_forward` = `132a84f7…`.
- **Same input:** `n/a` for every row — workloads are self-contained (Excel `InputHash` = `N/A` / `无（内建输入）`).
- **Same seed:** verified per row; the CSV `SameSeed` column is `YES` for all 18 existing controls.
- **Same context (old ordinal):** yes by construction; `SameContext=YES_OLD_ORDINAL` (or `ORDINAL_NULL` for RP01). This is superseded by the percentile re-map (§5).
- **Same config:** A01/A03/FW02/SQ01/SQ03/SP05 = `01f912de` (current). LQ04 = `9b270dbe` (NO). RP01 manifest omits the config SHA (UNVERIFIED).
- **Same binary:** pairs match each other, but only A01-R02 and FW02-R01 match the current baseline `d3807fbe`.

---

## 3. Exact redo list

### 3.1 NEEDS_REDO (16 contexts) — control exists, re-run on the current baseline

`A01-R01`, `A03-R01`, `A03-R05`, `LQ04-R01`, `LQ04-R02`, `LQ04-R03`, `LQ04-R04`, `LQ04-R05`, `SQ01-R01`, `SQ03-R01`, `SP05-R01`, `RP01-R01`, `RP01-R02`, `RP01-R03`, `RP01-R04`, `RP01-R05`.

### 3.2 MISSING (42 contexts) — create a matched control

- `A01-R03, R04, R05` (3)
- `A03-R02, R03, R04` (3)
- `SQ01-R02, R03, R04, R05` (4)
- `SQ03-R02, R03, R04, R05` (4)
- `SP05-R02, R03, R04, R05` (4)
- `FW02-R02, R03, R04, R05` (4)
- `FW05-R01, R02, R03, R04, R05` (5)
- `LP01-R01, R02, R03, R04, R05` (5)
- `MD04-R01, R02, R03, R04, R05` (5)
- `DA04-R01, R02, R03, R04, R05` (5)

Sum 42.

### 3.3 READY (2 contexts) — reusable trace, re-extract new event only

- `A01-R02` — `V33F-A01-C02`, trace `COMPLETE`, binary `d3807fbe`, seed `1113826800`, injector mounted at p=0 with `injected=0`.
- `FW02-R01` — `V33F-FW02-C01`, injector omitted, binary `d3807fbe`, seed `2941542370`.

**Fault-side redo (all 60):** Decision A re-selects each context at `k(p)=ceil(p*N_ROI)` inside the ROI. Every fault run must be re-executed at the new ordinal on the same binary/seed/ELF. Even the two READY controls need their event re-extracted from the (complete) trace at the new ordinal.

---

## 4. Hidden-mount audit and safe control pattern per model

Source: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`, `.../CHAOSMD04/CHAOSMD04.cc`, `.../CHAOSL1DForward/CHAOSL1DForward.cc`, `.../CHAOSAddrPath/CHAOSAddrPath.cc`, `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`, `.../run_replay_pilot.py`, `configs/se/lsu_proxy.py`.

| Model | Mode | Attaches at p=0? | Selector reads probability? | run_pilot control guard | Evidence | Risk | Safe control pattern |
|---|---|---|---|---|---|---|---|
| A01 | `CHAOSAddrPath` `a01_bit3_load` | no (`:35` log only at p>0) | yes (`:122`) | none needed | `injected=0` (C01C/C02C) | LOW | `--probability 0.0` mounted, or omit |
| A03 | `CHAOSAddrPath` `a03_bit3_stuck0_load` F5 | no (`:35`) | yes (`:122`) | none needed | `injected=0` (C01C/C05C) | LOW | `--probability 0.0` mounted, or omit |
| LQ04 | `CHAOSLQ04` ordinal | yes | ordinal-gated | `run_pilot.py:612-616` omits `--chaos_lq04` | `injection {events:[],injected:0}` | LOW | omit injector |
| SQ01 | `sq01_bit3` | no (hook blocked) | attach-level | none needed | `CHAOS_LSU_TRIGGER injected=0` | LOW | p=0 mounted |
| SQ03 | `sq03_canwb` | yes | yes (`:734`) | none needed | `CHAOS_SQ03_STATUS fired=0 injected=0` | LOW | p=0 mounted |
| SP05 | `sp05_complete` | yes | yes (`:538`, `:576`) | none needed | `CHAOS_SP05_STATUS selected=0 fired=0 injected=0` | LOW | p=0 mounted |
| FW02 | `f6_fw02` | yes (`:134-138`) | **yes after `364a6057` (`:1030`); no before** | `run_pilot.py:621-629` omits `--chaos_lsqfwd` | `V33G-FW02-MOUNTED-P0: observed=6 suppressed=0`; historic C01 `injected=1` | **MITIGATED** | omit injector (preferred); else rely on `:1030` and verify `suppressed=0`, no `fw02_decision` rows |
| FW05 | `fw05_older_src` | yes | yes (`:794` returns at `probability<=0`) | none | no control exists | LOW | p=0 mounted |
| LP01 | `CHAOSL1DForward` | no (`:23` log only at p>0) | yes (`:73`) | none | no control exists | LOW | p=0 (injector not attached) |
| MD04 | `CHAOSMD04` | n/a | gates on **`--md04_probability`** (`CHAOSMD04.cc:77`), bound from `args.md04_probability` (`lsu_proxy.py:1094`) | **NONE**; `run_pilot.py:576-581` hard-codes `--md04_probability 1.0` | no control; latent | **HIGH** | omit `--chaos_md04`, or add a control branch forcing `--md04_probability 0.0`; verify `injected=0` |
| DA04 | `da04_be_bit0` | **yes** (`CHAOSLSQFwd.cc:128-133`) | **NO** (`maybeCorruptStoreByteEnable`, `:972-1022`) | **NONE**; `run_pilot.py:568-574` has no p=0 branch | no control; latent misfire class = FW02-C01 | **HIGH** | omit `--chaos_lsqfwd` entirely; verify no `lsq_fwd_injections.log` / `injected=0` |
| RP01 | `rp01_count_only` / `rp01_skip_replay` | yes (`:201-206`) | ordinal-gated | separate driver; `run_replay_pilot.py:64` hard-codes `--probability 1.0` | `RP01-CONTROL-*` omit injector | MEDIUM | omit `--chaos_lsqfwd`; verify no `lsq_fwd_injections.log` |

**Verdicts:** FW02's historical p=0 misfire is closed *in both* layers (source guard + runner omit branch); the empirical mounted-p0 artifact proves it. DA04 and MD04 remain **open hazards**: a `--probability 0.0` control would fire. Do **not** launch any DA04/MD04 control until the runner guard lands.

---

## 5. ROI / percentile re-map — what it invalidates

Approved decision (`docs/superpowers/plans/2026-11-11-lsu-v331-context-workload-finalization.md:12-14`): R01–R05 = 10/30/50/70/90 % of the model-specific *eligible-event stream inside the ROI*, `k(p)=ceil(p*N_ROI)`, nearest-rank.

- Every existing control records an **old** `event_ordinal` (1–5, or model-specific 940–1013 etc.) in `pilot_meta.json` / `manifest.json`. After the re-map, that ordinal no longer names the new context → the **recorded matched-context claim is invalid**.
- The **zero-injection property is ordinal-independent** (`injected=0`, or the injector is absent). Therefore a control trace stays valid as a no-fault baseline **iff** (a) it is on the current baseline binary and (b) its trace is `COMPLETE` so the new event can be re-extracted.
- Applying that test: only **A01-R02** and **FW02-R01** survive (both `d3807fbe`, both ordinal-free in behaviour). The other **16** controls are on superseded binaries → **NEEDS_REDO**.
- The **fault runs are all invalidated** by the re-map: all 60 must be re-selected at `k(p)` on the same binary/seed/ELF/input.
- The census/percentile outputs are not yet generated (`audit_v3_3_1/roi/census/` and `audit_v3_3_1/roi/percentile/` are empty), so the new ordinals are not yet known — no control can be *confirmed* matched to a new context until T2/T3 land.

---

## 6. Config inconsistencies found

1. **Binary baseline split.** `LSU_Formal_Config_Freeze_Checklist.csv` G1 rows pin `68c6ce73`, while the V3.3 rows and the on-disk binary are `d3807fbe`. Evidence: `sha256sum build/ARM/gem5.opt` → `d3807fbe…`; checklist rows `G1-Binary|baseline binary SHA256` vs `V3.3|Final binary SHA256`.
2. **Pilot evidence non-uniform and partly absent.** 68c6ce73 (A01/A03/RP01), 720eb780 (SQ01/SQ03/SP05/FW02), f3c2a442 (LQ04), 0de25644 (LP01/MD04/part DA04), 8377c011 (FW05), 3e9148fc (DA04 R01–R03) — none of these besides `d3807fbe` exist on disk. Pairs on missing binaries are non-reproducible.
3. **Config script SHA drift.** FW05/LP01/MD04/DA04 built with `2e1de853` (v3.2.11-era `ee1f00dc`); LQ04 with `9b270dbe` (v3.2.10-era `89f9569a`); RP01 manifest omits the config SHA; current is `01f912de`.
4. **Stale absolute paths.** LQ04 control `command.txt`/`manifest.json` point at worktree `lsu-platform-v3.2.10`; Excel `WorkloadPath`/`ConfigScript` point at `lsu-platform-v3.2` (55 rows) and `lsu-platform-v3.2.10` (5 rows).
5. **Stale Excel `gem5Commit`.** `6f98088a7144d7f6fb22d985be3023ac5658e71b` (an ATLAS-diagrams commit) on all 60 rows — not the code HEAD.
6. **Warm-up / ROI unfrozen.** `WarmUpGate` = `NOT_FROZEN (NEEDS_RESEARCHER_CONFIRMATION)` on all 60; `ConfigFrozen=NO` on all 60. No run encodes a frozen ROI window (`run_pilot.py` only passes `--*_warmup_events 0`).
7. **Runner gaps.** `run_pilot.py` has no `--dry-run`; `--model` covers 11 of 12 (RP01 uses a separate driver); DA04/MD04 lack p=0 control branches.
8. **`--probability 0.0` is not a control guarantee.** `SUPP-FW02-C01` proves the global probability did not gate the F6_fw02 selector on `720eb780`.

---

## 7. Minimum control plan for the next pilot round

1. **Pin one baseline.** Rebuild from current HEAD (includes `364a6057`), record SHA in `audit_v3_3_1/report/PROVENANCE.md`; every control and fault run must use it. Do not reuse `68c6ce73`/`720eb780`/`f3c2a442`.
2. **Land two runner patches (one commit each).**
   - DA04: add a p=0 branch that omits `--chaos_lsqfwd` (copy `run_pilot.py:612-616` / `:621-629`).
   - MD04: at p=0 omit `--chaos_md04` (or force `--md04_probability 0.0`).
   These are prerequisites: without them DA04/MD04 controls will misfire.
3. **Record config SHA everywhere**, especially the RP01 manifests.
4. **Run 60 controls**, one per context, at the *same seed/ELF/input/config* as the fault:
   - A01/A03: `--probability 0.0` + `--chaos_addrpath` (p=0 is gated).
   - SQ01/SQ03/SP05/FW05: `--probability 0.0` + `--chaos_lsqfwd` (selectors gate p=0).
   - LQ04/FW02: omit the injector (runner branch); FW02 must show `suppressed=0`.
   - LP01: `--probability 0.0` (injector does not attach).
   - DA04: omit `--chaos_lsqfwd`; MD04: omit `--chaos_md04`; RP01: omit `--chaos_lsqfwd`.
5. **Gate every control on a real artifact.** Accept only if (a) the injector is absent from `config.ini`, or (b) an `injected=0` / `injection_count=0` line is present, and (c) `pilot_meta.injection.events == []`. Reject anything with injection events.
6. **Re-run the 60 faults** at the new `k(p)` ordinal on the pinned binary. Keep the historical chains on their own SHAs; never stitch across binaries.
7. **Never reuse** `SUPP-FW02-C01` (INVALID_MISFIRE). Retain it unmodified as honest evidence.
8. **Minimum viable subset if resources are capped:** one control per model (12) for a smoke check, but the formal gate requires 60/60 context-matched controls.

---

## 8. Method / commands actually run

- `sha256sum build/ARM/gem5.opt CHAOS/gem5/build/ARM/gem5.opt`
- `find . -name 'gem5.opt' -type f -exec sha256sum {} \;`
- Python `csv`/`json` scans over `pilot_meta.json`, `manifest.json`, `config.ini`, `stdout.log`, `lsq_fwd_injections.log` for all 26 control dirs.
- `grep -n 'probability' CHAOS/gem5/src/cpu/o3/{CHAOSLSQFwd,CHAOSMD04,CHAOSL1DForward,CHAOSAddrPath}/*.cc`
- `grep -n 'md04_probability|da04|probability == 0' docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`
- `git log -S 'consults probability and SUPP-FW02-C01 misfires' -- CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc` → `364a6057` (Wed Nov 11 12:36:24 2026).

No gem5 binary was executed and no tracked file was modified.
