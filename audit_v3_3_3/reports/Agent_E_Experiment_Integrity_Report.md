# Agent E — Fault/Control, Excel, Runner & Provenance Integrity Report (LSU v3.3.3)

Audit date: 2026-11-11. Read-only audit; no source/config/workload/Excel/evidence file was modified. The only file written is this report.

Repo root (all relative paths below resolve here):
`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`

## Scope

The 60 fault runs and 60 matched controls under `audit_v3_3_2/runs/`, their authoritative
SampleRunID/Seed identity (`docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv`,
`gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`), the producing runner/config
(`docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`, `configs/se/lsu_proxy.py`),
the tools (`tools/lsu_v332_matrix.py`, `tools/lsu_v332_report.py`,
`tools/lsu_v332_supplement.py`), and binary/config/workload provenance.

## Commands actually run (all read-only)

```
cat/Read  audit_v3_3_3/README_GROUND_TRUTH.md                        (full)
python3 /tmp/e_audit/analyze.py      # parse 120 command.txt + summary.json + pilot_meta.json + manifest.json
python3 /tmp/e_audit/full.py         # per-pair seed/ordinal/ELF/binary/config/mount/injection comparison
python3 /tmp/e_audit/gen_tables.py   # generated the 60-row pairing and classification tables below
sha256sum build/ARM/gem5.opt configs/se/lsu_proxy.py audit_v3_3_2/binary/* <every --cmd ELF>
git status --short ; git ls-files tools/ ; git rev-parse HEAD ; git diff fc608224..HEAD -- tools/lsu_v332_matrix.py
python3 (openpyxl read-only) gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx, LSU_Formal_Experiment_Config.xlsx
python3 (csv) 60_SAMPLE_MATRIX.csv, LSU_Fault_Control_Pair_Final.csv, ..._Final_J.csv,
              LSU_60Context_ROI_Percentile_Mapping.csv
grep/tail on every control stdout/stderr/model log; per-trace scan of issue/`injection_status`
grep -n on CHAOSLSQFwd.cc, CHAOSAddrPath.cc, CHAOSL1DForward.cc, CHAOSMD04.cc, CHAOSLQ04.py
```

## Files inspected (key)

- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py` (1111 lines)
- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/configs/se/lsu_proxy.py` (1277 lines)
- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/tools/lsu_v332_matrix.py` (357)
- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/tools/lsu_v332_report.py` (331)
- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/tools/lsu_v332_supplement.py` (202)
- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`
- `.../CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc`
- `.../CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.cc`
- `.../CHAOS/gem5/src/cpu/o3/CHAOSMD04/CHAOSMD04.cc`, `CHAOSMD04.py`
- `.../CHAOS/gem5/src/cpu/o3/CHAOSLQ04/CHAOSLQ04.py`
- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv`
- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`
- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final.csv`
- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/audit_v3_3_2/roi/LSU_60Context_ROI_Percentile_Mapping.csv`
- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/audit_v3_3_2/report/PROVENANCE.md`
- All 120 `audit_v3_3_2/runs/<MODEL>-R<NN>-{fault,control}/` directories.

---

## 1. Pairing integrity (60 pairs)

### 1.1 Machine-checked pair matrix

Legend: `Seed F=C` is the seed present in both commands (mounted controls) or the intended
seed recovered from `pilot_meta.json` / `summary.json` (omitted-injector controls).
`Ord F/C` is the injector event-ordinal flag; `—` means the control legitimately omits the
injector and therefore its ordinal flag. `ELF sha` is computed live from the `--cmd=` path
(fault == control). `target seq in control trace` counts occurrences of the fault's
first-injection `dyn_inst_seq` in the paired control trace.

| Run | Seed F=C | Ord F/C | ELF sha (F=C) | bin sha | Mount F / C | target seq in control trace | ver |
|---|---|---|---|---|---|---|---|
| A01-R01 | 2108120075 | 1059/1059 | YES (90a1900377d2) | 070d68a6 | Y / Y | 5 | PASS |
| A01-R02 | 1113826800 | 1098/1098 | YES (90a1900377d2) | 070d68a6 | Y / Y | 5 | PASS |
| A01-R03 | 1302709433 | 1137/1137 | YES (90a1900377d2) | 070d68a6 | Y / Y | 4 | PASS |
| A01-R04 | 2194451614 | 1176/1176 | YES (90a1900377d2) | 070d68a6 | Y / Y | 5 | PASS |
| A01-R05 | 3228552887 | 1215/1215 | YES (90a1900377d2) | 070d68a6 | Y / Y | 5 | PASS |
| A03-R01 | 663646247 | 1059/1059 | YES (90a1900377d2) | 070d68a6 | Y / Y | n/a (no trace) | PASS* |
| A03-R02 | 1626885462 | 1098/1098 | YES (90a1900377d2) | 070d68a6 | Y / Y | n/a (no trace) | PASS* |
| A03-R03 | 110775855 | 1137/1137 | YES (90a1900377d2) | 070d68a6 | Y / Y | n/a (no trace) | PASS* |
| A03-R04 | 2766846323 | 1176/1176 | YES (90a1900377d2) | 070d68a6 | Y / Y | n/a (no trace) | PASS* |
| A03-R05 | 1156093484 | 1215/1215 | YES (90a1900377d2) | 070d68a6 | Y / Y | n/a (no trace) | PASS* |
| FW02-R01 | 2941542370 | 13/— | YES (a08fb3a7b8bb) | 070d68a6 | Y / N | 3 | PASS |
| FW02-R02 | 2129071279 | 25/— | YES (a08fb3a7b8bb) | 070d68a6 | Y / N | 3 | PASS |
| FW02-R03 | 1336081385 | 37/— | YES (a08fb3a7b8bb) | 070d68a6 | Y / N | 3 | PASS |
| FW02-R04 | 527667424 | 49/— | YES (a08fb3a7b8bb) | 070d68a6 | Y / N | 3 | PASS |
| FW02-R05 | 3622278636 | 61/— | YES (a08fb3a7b8bb) | 070d68a6 | Y / N | 3 | PASS |
| FW05-R01 | 1025137124 | 200/200 | YES (0cf405092e33) | 070d68a6 | Y / Y | 3 | PASS |
| FW05-R02 | 1653118510 | 600/600 | YES (0cf405092e33) | 070d68a6 | Y / Y | 3 | PASS |
| FW05-R03 | 2442802213 | 1000/1000 | YES (0cf405092e33) | 070d68a6 | Y / Y | 3 | PASS |
| FW05-R04 | 899944922 | 1400/1400 | YES (0cf405092e33) | 070d68a6 | Y / Y | 3 | PASS |
| FW05-R05 | 2836530945 | 1800/1800 | YES (0cf405092e33) | 070d68a6 | Y / Y | 3 | PASS |
| SQ01-R01 | 591611458 | 1018/1018 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SQ01-R02 | 576447973 | 1044/1044 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SQ01-R03 | 1257175390 | 1069/1069 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SQ01-R04 | 3116972755 | 1095/1095 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SQ01-R05 | 172636228 | 1121/1121 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SQ03-R01 | 2214819981 | 1021/1021 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SQ03-R02 | 1486471869 | 1047/1047 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SQ03-R03 | 3102670938 | 1072/1072 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SQ03-R04 | 3974203372 | 1098/1098 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SQ03-R05 | 729970077 | 1124/1124 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SP05-R01 | 1489155957 | 952/952 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SP05-R02 | 1290498198 | 978/978 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SP05-R03 | 2768710389 | 1003/1003 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SP05-R04 | 2741073922 | 1029/1029 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| SP05-R05 | 4098160626 | 1055/1055 | YES (bcab9cc5e1e4) | 070d68a6 | Y / Y | 2 | PASS |
| DA04-R01 | 4185444934 | 135/— | YES (89ff937a73a0) | 070d68a6 | Y / N | 2 | PASS |
| DA04-R02 | 2627302015 | 340/— | YES (89ff937a73a0) | 070d68a6 | Y / N | 2 | PASS |
| DA04-R03 | 3592849939 | 544/— | YES (89ff937a73a0) | 070d68a6 | Y / N | 2 | PASS |
| DA04-R04 | 3815557835 | 749/— | YES (89ff937a73a0) | 070d68a6 | Y / N | 2 | PASS |
| DA04-R05 | 2016743094 | 954/— | YES (89ff937a73a0) | 070d68a6 | Y / N | 2 | PASS |
| LP01-R01 | 1349924126 | 2549/2549 | YES (3779e8ced41a) | 070d68a6 | Y / Y | 2 | PASS |
| LP01-R02 | 2648660520 | 5877/5877 | YES (3779e8ced41a) | 070d68a6 | Y / Y | 2 | PASS |
| LP01-R03 | 2021175746 | 9205/9205 | YES (3779e8ced41a) | 070d68a6 | Y / Y | 2 | PASS |
| LP01-R04 | 3894776903 | 12533/12533 | YES (3779e8ced41a) | 070d68a6 | Y / Y | 2 | PASS |
| LP01-R05 | 1604604537 | 15861/15861 | YES (3779e8ced41a) | 070d68a6 | Y / Y | 2 | PASS |
| MD04-R01 | 2595563470 | 3/— | YES (dd241c3097e6) | 070d68a6 | Y / N | 2 | PASS |
| MD04-R02 | 811948497 | 5/— | YES (dd241c3097e6) | 070d68a6 | Y / N | 2 | PASS |
| MD04-R03 | 2545691512 | 6/— | YES (dd241c3097e6) | 070d68a6 | Y / N | 2 | PASS |
| MD04-R04 | 2149193331 | 8/— | YES (dd241c3097e6) | 070d68a6 | Y / N | 2 | PASS |
| MD04-R05 | 1008734674 | 10/— | YES (dd241c3097e6) | 070d68a6 | Y / N | 2 | PASS |
| LQ04-R01 | 1842987246 | 1/— | YES (fa25f785a482) | 070d68a6 | Y / N | 2 | PASS |
| LQ04-R02 | 2188214204 | 2/— | YES (fa25f785a482) | 070d68a6 | Y / N | 2 | PASS |
| LQ04-R03 | 3953171871 | 3/— | YES (fa25f785a482) | 070d68a6 | Y / N | 2 | PASS |
| LQ04-R04 | 4153250964 | 4/— | YES (fa25f785a482) | 070d68a6 | Y / N | 2 | PASS |
| LQ04-R05 | 3410523942 | 5/— | YES (fa25f785a482) | 070d68a6 | Y / N | 2 | PASS |
| RP01-R01 | 3135797961 | 26/— | YES (3f880cba7b6d) | 070d68a6 | Y / N | n/a (no trace) | PASS* |
| RP01-R02 | 226489823 | 77/— | YES (3f880cba7b6d) | 070d68a6 | Y / N | n/a (no trace) | PASS* |
| RP01-R03 | 1735144973 | 128/— | YES (3f880cba7b6d) | 070d68a6 | Y / N | n/a (no trace) | PASS* |
| RP01-R04 | 2455796178 | 179/— | YES (3f880cba7b6d) | 070d68a6 | Y / N | n/a (no trace) | PASS* |
| RP01-R05 | 3984724524 | 230/— | YES (3f880cba7b6d) | 070d68a6 | Y / N | n/a (no trace) | PASS* |

`PASS*` = pair-internal identity checks pass, but the evidence root has no trace for that pair
(see §3/E-13); dynamic-context equality rests on the identical command/workload/seed, not on
per-instruction trace evidence.

### 1.2 What was compared and the result

| Property | Result |
|---|---|
| Binary SHA (summary.json) | 120/120 = `070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca` (one distinct value) |
| Binary+config SHA (manifest.json) | 105 manifests, 1 distinct binary SHA and 1 distinct config SHA (`01f912de…bf6e5`); 15 runs have no manifest (A03 fault ×5, RP01 ×10) |
| Config script SHA vs live `configs/se/lsu_proxy.py` | 105/105 manifests equal to live `01f912de3388aaf420aa69d5dd55098ddfb97851faf0269a6b009fcc389bf6e5` |
| Seed, pair-internal | 60/60 equal at the intended-identity level; 35/60 are literal flag equality (`--rng_seed`/`--addrpath_rng_seed`/`--l1dfwd_rng_seed`/`--md04_rng_seed` in both commands); 25/60 controls omit the injector and therefore its seed flag, but `pilot_meta.excel_identity.seed` (or `summary.seed` for RP01) equals the fault seed |
| Seed vs frozen workbook | 60/60 fault seeds equal `60_SAMPLE_MATRIX.csv`; 60/60 control intended seeds equal the same rows |
| Event ordinal, pair-internal | 35/60 literal equality; 25/60 control omits the flag by design (injector absent). The intended ordinal is still recorded in every `summary.json` (`ordinal`) |
| ELF path and ELF SHA, pair-internal | 60/60 equal (computed live from `--cmd=`) |
| ELF SHA vs frozen sample | 30/60 DO NOT equal the frozen `BinarySHA256` (FW02, SQ01, SQ03, SP05, MD04, RP01 — the six candidate-workload models, 5 contexts each); 30/60 equal (A01, A03, FW05, DA04, LP01, LQ04) |
| Input | No external input for any workload; frozen CSV records `无（内建输入）`; all runs execute a self-contained static ELF |
| CPU / variant | 120/120 commands are `--cpu O3 --variant B0`; paired `config.ini` dumps contain no CPU-parameter difference |
| Warm-up / span flags | Equal where present. DA04 is the only pair family with explicit flags (`--lsqfwd_warmup_events 0 --lsqfwd_span_events 10`): they are present on fault and n/a on control because the injector is omitted. Manifest `warmup`/`roi` = `NEEDS_RESEARCHER_CONFIRMATION` for every run_pilot run; ROI is not encoded in any command. `n/a` (not frozen) |
| Target dynamic context | A01: control `CHAOS_LSU_TRIGGER … eligible=N` equals the fault ordinal exactly, for all five contexts (1059/1098/1137/1176/1215). For the other nine models with traces: the fault's first-injection `dyn_inst_seq` occurs 2–5 times in the paired control trace (50/50 pairs found). A03 and RP01: `n/a`, no trace |

### 1.3 Mismatch list (every non-equal field)

1. **ELF identity vs the frozen sample (30 contexts, severity high).** The run's `--cmd=`
   ELF differs from the frozen row's `BinarySHA256`/`WorkloadPath` for six models, while the
   frozen SampleRunID and Seed are reused unchanged:

   | Model | Frozen workload / ELF SHA | Executed workload / ELF SHA | Contexts |
   |---|---|---|---|
   | FW02 | sq_forward / `132a84f7…0af297` | sq_forward_w4v2 / `a08fb3a7…4fe76e2` | R01–R05 |
   | SQ01 | sq_drain / `d423539c…186f188f` | sq_reload_v3212 / `bcab9cc5…d178de6` | R01–R05 |
   | SQ03 | sq_drain / `d423539c…186f188f` | sq_reload_v3212 / `bcab9cc5…d178de6` | R01–R05 |
   | SP05 | store_path / `906b3798…dc55fbcf` | sq_reload_v3212 / `bcab9cc5…d178de6` | R01–R05 |
   | MD04 | replay_dependency / `ca15390f…1d838f4` | md04_violations_v332 / `dd241c30…f95c43` | R01–R05 |
   | RP01 | replay_dependency / `ca15390f…1d838f4` | replay_partial_v332 / `3f880cba…8fa42e42` | R01–R05 |

   Evidence: `audit_v3_3_2/runs/<M>-R<NN>-fault/command.txt`, `manifest.json`
   (`workload.sha256`), and `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv`
   (columns `WorkloadPath`, `BinarySHA256`). These are exactly the 30
   `CANDIDATE_PENDING_APPROVAL` rows in the curated control table.
2. **`summary.json` seed is null in 110/120 runs.** Only the 10 RP01 runs carry a seed.
   Root cause in §3/E-02. `pilot_meta.json` carries the correct seed for 105 runs.
3. **`summary.json` terminal is null in 97/120 runs.** The terminal exists in
   `pilot_meta.classification.terminal_state`; the stored summaries were produced before the
   driver's terminal fallback took effect (the committed driver has the fallback; the
   evidence does not). Concrete: `A01-R01-fault: summary.terminal=null`, while
   `pilot_meta.classification.terminal_state=SDC`.
4. **RP01 terminal disagreement.** `summary.json` says `CRASH`; the curated CSV says
   `HANG_WATCHDOG`. Raw evidence is `audit_v3_3_2/runs/RP01-R01-fault/stderr.log`:
   `CHAOS_RP01_WATCHDOG_EXPIRED tick=7700000000 injected=1 eligible=26` and the log line
   `CHAOS_RP01_WATCHDOG=EXPIRED fired=1 injected=1 eligible=26`. `HANG_WATCHDOG` is correct;
   the matrix parses stdout only. See E-06.
5. **Controls carry a fault identity in the trace.** e.g.
   `audit_v3_3_2/runs/A01-R01-control/trace_v31.jsonl` line 1 has
   `"fault_id":"A01-CFG01","run_id":"PILOT-A01","sub_task_id":"PILOT-A01-S01"`.
   A no-fault control should not be labelled with the fault config ID. See E-15.
6. **Ordinal flag absent in controls for the five omitted-injector models.**
   FW02/DA04/MD04/LQ04/RP01 controls have no `--*_event_ordinal`. This is by design
   (`run_pilot.build_model_extra` returns `[]` at p=0), not a defect, but it means the
   control cannot be shown to have selected the same ordinal event; only the intended
   ordinal in `summary.json` ties it to the pair.
7. **A03 `injection_count=20000` is a log cap, not 20,000 faults.** Evidence:
   `audit_v3_3_2/runs/A03-R01-fault/addrpath_injections.log` last line
   `A03_LOG_CAPPED: cap=20000 faults_injected=20000 tick=165742115`. A03 is an F5
   persistent stuck-at model that applies at every eligible event. Every other fault run
   records `injection_count=1`. See E-21.

---

## 2. Zero-injection proof and control classification

### 2.1 Authoritative classification (the curated table's all-`INJECTOR_ABSENT` is wrong)

Definitions used:
- **INJECTOR_ABSENT** — no injector SimObject is instantiated (`--chaos_*` injector flag missing from the executed gem5 argv).
- **MOUNTED_BUT_DISABLED** — the injector SimObject is instantiated (and, unless noted, attached), and every injection path contains an explicit `probability <= 0` early return, so the hook is inert.
- **MOUNTED_BUT_SUPPRESSED** — instantiated/attached and the hook computes a suppression decision (ordinal/window/max-faults) but declines. **No control falls in this class.**

Result: **35 MOUNTED_BUT_DISABLED, 25 INJECTOR_ABSENT, 0 MOUNTED_BUT_SUPPRESSED.**
The current curated table's `ControlZeroProof=INJECTOR_ABSENT` for 60/60 is wrong for exactly
the 35 mounted controls.

| Run | injector flags in control argv | summary inj | trace inj events | injector log last line | class | sub-mode / gate |
|---|---|---|---|---|---|---|
| A01-R01…R05-control | chaos_propagation, chaos_addrpath | 0 | 0 | (no injector log) | MOUNTED_BUT_DISABLED | CHAOSAddrPath attached at startup; `maybeCorruptPre`/`maybeCorrupt` early-return at p<=0 (CHAOSAddrPath.cc:250, :122) |
| A03-R01…R05-control | chaos_propagation, chaos_addrpath | 0 | 0 | (no injector log) | MOUNTED_BUT_DISABLED | same; F5 tier, no probe path. stdout: `CHAOS_LSU_TRIGGER … eligible=0 injected=0` |
| FW02-R01…R05-control | chaos_propagation | 0 | 0 | (no injector log) | INJECTOR_ABSENT | runner omits `--chaos_lsqfwd` (run_pilot.py:611-620) |
| FW05-R01…R05-control | chaos_propagation, chaos_lsqfwd | 0 | 0 | `lsq_fwd_injections.log` empty | MOUNTED_BUT_DISABLED | attached (ctor attach list); FW05 hook gates p<=0 (CHAOSLSQFwd.cc:794) |
| SQ01-R01…R05-control | chaos_propagation, chaos_lsqfwd | 0 | 0 | (no injector log) | MOUNTED_BUT_DISABLED | SimObject constructed and `lsuTrigger` created, but `cpu->lsqFwd` is NOT set: the attach block excludes `sq01_bit3` (CHAOSLSQFwd.cc:81-127). stdout: `CHAOS_LSU_TRIGGER … eligible=0 injected=0` |
| SQ03-R01…R05-control | chaos_propagation, chaos_lsqfwd | 0 | 0 | `CHAOS_SQ03_STATUS: fired=0 injected=0 eligible=0` | MOUNTED_BUT_DISABLED | attached; `maybeSetCanWB` gates p<=0 (CHAOSLSQFwd.cc:734). **Watchdog armed at 5e8 cycles (line 155)** |
| SP05-R01…R05-control | chaos_propagation, chaos_lsqfwd | 0 | 0 | `CHAOS_SP05_STATUS: selected=0 fired=0 injected=0 eligible=0 …` | MOUNTED_BUT_DISABLED | attached; `maybeSelectSP05`/`maybeCompleteSP05` gate p<=0 (lines 538, 576). **Watchdog armed (line 178)** |
| DA04-R01…R05-control | chaos_propagation | 0 | 0 | (no injector log) | INJECTOR_ABSENT | runner omits `--chaos_lsqfwd` (run_pilot.py:556-563); DA04 has no probability gate (CHAOSLSQFwd.cc:972-989) |
| LP01-R01…R05-control | chaos_propagation, chaos_l1dfwd | 0 | 0 | (no injector log) | MOUNTED_BUT_DISABLED | CHAOSL1DForward attaches at `startup()` (line 158); `maybeCorrupt` gates p<=0 (line 74) |
| MD04-R01…R05-control | chaos_propagation | 0 | 0 | (no injector log) | INJECTOR_ABSENT | runner omits `--chaos_md04` (run_pilot.py:569-575); `md04_probability` defaults to 1.0 (lsu_proxy.py:491) |
| LQ04-R01…R05-control | chaos_propagation | 0 | 0 | (no injector log) | INJECTOR_ABSENT | runner omits `--chaos_lq04` (run_pilot.py:601-606); CHAOSLQ04 has no probability parameter |
| RP01-R01…R05-control | chaos_propagation | 0 | NO_TRACE | (no injector log) | INJECTOR_ABSENT | matrix base omits `--chaos_lsqfwd` at p=0 (lsu_v332_matrix.py:225-236); watchdog not scheduled |

All 60 rows in machine form are in the audit log produced by
`python3 /tmp/e_audit/gen_tables.py`; the five contexts within each model row above have
identical flags, class and sub-mode (verified individually for all 60).

### 2.2 Zero-injection proof — method and paths

For every control the following five independent checks were run and all passed:

1. `summary.json → injection_count == 0` — 60/60.
2. `pilot_meta.json → injection_count == 0`, `accepted == true`, `control_valid == true`,
   `control_misfire == false` — 55/55 control runs that have a pilot_meta (the other 5 are
   RP01, which has no pilot_meta).
3. `summary.trace_completeness.fault_activation_status == "NOT_TRIGGERED"` — 55/55 where present.
4. `trace_v31.jsonl` scan for `event_type in {injection, injection_nochange}` — **0 events**
   in all 55 control traces; the `injection_status` histogram over 1,384,799 event records is
   `{NOT_APPLICABLE: 1,384,799}` plus 55 non-event (summary) records. No trace carries
   `INJECTED`/`APPLIED`.
5. Model evidence:
   - A01 controls: `CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=0 eligible=N injected=0` with N = 1059/1098/1137/1176/1215.
   - A03 controls: `CHAOS_LSU_TRIGGER: … tier=F5 attempted=0 eligible=0 injected=0`.
   - LP01 controls: no `l1d_fwd_injections.log` is created at p=0.0 (CHAOSL1DForward.cc:24).
   - SQ01 controls: `CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd … injected=0`.
   - SQ03 controls: `CHAOS_SQ03_STATUS: fired=0 injected=0 eligible=0` (all five).
   - SP05 controls: `CHAOS_SP05_STATUS: selected=0 fired=0 injected=0 eligible=0` (all five).
   - FW05 controls: `lsq_fwd_injections.log` exists but is empty (0 bytes) in all five.
   - FW02/DA04/MD04/LQ04/RP01 controls: no injector log file exists at all.
   - A scan of all control `stdout.log`, `stderr.log`, and injector logs for
     `fired=1|injected=[1-9]|selected=1|SKIP_REPLAY|faults_injected: [1-9]` returns **no
     matches** (excluding the echoed `command line:`).
6. Oracle / exit: `summary.oracle == true` and `exit_code == 0` for 55/55 with a summary
   oracle; RP01 controls have `oracle=true`, `exit_code=0`, `rp01.checksum=f3b1c554273d23f7`
   (all five).

Only remaining weakness: RP01 controls have no `trace_v31.jsonl` and no `manifest.json`
(evidence gap E-13), so checks 3–4 are `n/a` for those five and the proof rests on
`summary.injection_count=0` plus zero `RP01_ELIGIBLE`/`RP01_SKIP_REPLAY` lines in stdout.

---

## 3. Close-path defects (DA04 / MD04 / RP01 / indirect)

### 3.1 DA04 — does `--probability 0.0` disable the injection path? Is the control omitting the injector?

- `CHAOSLSQFwd::maybeCorruptStoreByteEnable` has **no probability check at all**
  (CHAOSLSQFwd.cc:972-1017). The constructor explicitly attaches the injector in DA04 mode
  even at probability 0: `if (struct_mode == StructMode::Da04BeBit0) { if (!cpu->lsqFwd) cpu->lsqFwd = this; if (max_faults == 0) max_faults = 1; }` (CHAOSLSQFwd.cc:128-133).
- The legacy `corrupt()` hook does return at `probability <= 0.0` (line 313), but DA04 mode
  returns before it (line 341), so that gate does not protect DA04.
- **Therefore `--probability 0.0` alone does NOT disable DA04.** The only correct control is
  to omit the injector.
- The control does omit it: `audit_v3_3_2/runs/DA04-R01-control/command.txt` (and all R02–R05)
  has only `--chaos_propagation`, no `--chaos_lsqfwd`, no `--lsq_struct_mode`, no ordinal.
  `run_pilot.build_model_extra` DA04 branch returns `[]` when `control` (run_pilot.py:556-563).
- Verified: no `lsq_fwd_injections.log` exists in any DA04 control; summary injection_count=0.

**Verdict: DA04 control is correct today, but it is correct by omission, not by a runner/config
interlock.** If someone mounts `--chaos_lsqfwd --lsq_struct_mode da04_be_bit0 --probability 0.0`
the control will inject. This is a latent hazard (E-09).

### 3.2 MD04 — `--md04_probability` is a separate knob; latent control hazard

- `configs/se/lsu_proxy.py:491`: `--md04_probability` default **1.0**, independent of the
  generic `--probability` (line 215, default 1.0).
- `configs/se/lsu_proxy.py:1092-1094`: `CHAOSMD04(cpu=cpu0, probability=args.md04_probability, …)` — the injector's gate is the md04 knob only.
- `CHAOSMD04::maybeInject` consults `probability` (CHAOSMD04.cc:77 and :111) and the ordinal
  via `shouldInject` (line 106), but never the generic `--probability`.
- Therefore mounting `--chaos_md04` with `--probability 0.0` and no `--md04_probability`
  leaves `md04_probability=1.0`: the injector will fire on the selected eligible pair and the
  "control" will inject. **Confirmed by source; no live run exhibits it because the current
  MD04 control omits `--chaos_md04` entirely** (`audit_v3_3_2/runs/MD04-R01-control/command.txt`).
- The runner currently protects the control: `run_pilot.build_model_extra` MD04 branch returns
  `[]` when `control` (run_pilot.py:569-575).

**Proposed exact one-shot fix (defense in depth, two lines):**
1. `configs/se/lsu_proxy.py`: make the effective MD04 probability the minimum of the two
   gates. At the mount (line 1092), use
   `probability=(args.md04_probability if args.probability > 0.0 else 0.0)`.
   (Optionally also change `--md04_probability` default to `None` at line 491 and resolve
   `None → args.probability`.)
2. `run_pilot.py` `build_model_extra` MD04 fault branch: pass
   `--md04_probability str(probability)` instead of the hard-coded `"1.0"`, so the two knobs
   can never diverge for fault runs either.
Validation: `python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py --model MD04 --context-index 1 --pilot-id MD04-R01-control --outdir /tmp/md04c --probability 0.0 --dry-run` then inspect the generated argv; plus a unit assertion that `md04_probability` in the config.ini of any p=0 run is 0.0.
Approval: N (already the intended control semantics; no frozen fault-run command changes if
the fault branch keeps its explicit 1.0 value).

### 3.3 RP01 control — omission vs suppression; can the watchdog fire?

- The RP01 path is driven directly by `tools/lsu_v332_matrix.py`, not `run_pilot.py`
  (`run_pilot.MODELS` does not contain RP01). The base argv is built at
  `lsu_v332_matrix.py:225-236` and appends the RP01 injector only for `role == "fault"`.
- Control argv (`audit_v3_3_2/runs/RP01-R01-control/command.txt`) has `--probability 0.0`
  and **no** `--chaos_lsqfwd`, no `--rp01_event_ordinal`, no `--rp01_watchdog_cycles`.
- `CHAOSLSQFwd` is therefore never instantiated; `rp01_watchdog_event` is only scheduled
  inside the `Rp01CountOnly || Rp01SkipReplay` constructor block (CHAOSLSQFwd.cc:199-216), so
  no watchdog event exists. `mightSkipPartialReplay` is never reachable (`cpu->lsqFwd` null).
- Evidence: stdout of every RP01 control contains **0** `RP01_ELIGIBLE` and **0**
  `RP01_SKIP_REPLAY` lines; `summary.rp01 = {eligible:0, skips:0, watchdog:false, checksum:f3b1…}`;
  the process exits 0 and the oracle passes.

**Verdict: RP01 control is a genuine INJECTOR_ABSENT control with no watchdog. Correct.**
The fault side does fire the internal watchdog (`stderr.log: fatal: CHAOS_RP01_WATCHDOG_EXPIRED
tick=7700000000 injected=1 eligible=26`), which is the intended RP01 terminal, but see E-06
for the `CRASH` mislabel.

### 3.4 Other indirect control paths

| Model | Control path | Live misfire risk | Class |
|---|---|---|---|
| A01 | SimObject attached; `maybeCorruptPre` p<=0 branch calls `probeA01Control` (observation only) | none | DISABLED |
| A03 | attached; `maybeCorruptPre` p<=0 returns before trigger | none | DISABLED |
| LP01 | attached at `startup()`; `maybeCorrupt` p<=0 | none | DISABLED |
| SQ01 | constructed but not attached (`cpu->lsqFwd` null); trigger object still created and prints an exit summary | none, but silent | DISABLED (not attached) |
| SQ03 / SP05 | attached; p<=0 gate in mode functions; **watchdog armed at 5e8 cycles regardless of probability** | none in a completing control; a hung control would die with `CHAOS_SQ03/SP05_WATCHDOG_EXPIRED` and be classified as a simulator error, masking the real control failure | DISABLED (watchdog hazard) |
| FW05 | attached; p<=0 gate | none | DISABLED |
| DA04 / FW02 / LQ04 / MD04 / RP01 | omitted | none today; DA04/LQ04/RP01/MD04 have no in-injector global-probability gate (latent) | ABSENT |

(`FW02` was hardened in-injector at CHAOSLSQFwd.cc:1030; `SQ01` remains ungated at
CHAOSLSQFwd.cc:934-947 but is unreachable because it is not attached.)

---

## 4. Runner / tool integrity

### 4.1 Git status and tracking of the producing code

```
$ git status --short
?? .tmp_lsu_conc/
?? audit_v3_3_1/v33_package/
?? audit_v3_3_2/binary/
?? audit_v3_3_2/pkg/
?? audit_v3_3_2/roi/census_v332/
?? audit_v3_3_2/sq_workload/evidence/contexts/
?? audit_v3_3_2/sq_workload/evidence/establish/
?? audit_v3_3_2/sq_workload/evidence/original/
?? audit_v3_3_2/sq_workload/evidence/original_comparison.json
?? audit_v3_3_3/
$ git status --short tools/ docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py configs/se/lsu_proxy.py
(empty)
$ git ls-files | grep -E 'lsu_v332|run_pilot|lsu_proxy'
configs/se/lsu_proxy.py
docs/.../platform/run_pilot.py
tools/lsu_v332_matrix.py
tools/lsu_v332_report.py
tools/lsu_v332_supplement.py
```

The v3.3.2 report's claim that the driver was modified/untracked is **stale**: all three
tools are tracked and the working tree is clean. HEAD is `3097ad82e7066f18fc35cf64dcb612a05c1fc021`;
`fc608224` exists and `git rev-list --count fc608224..HEAD == 3`. Those three commits are
RESULTS/EVIDENCE/PACKAGE, but the RESULTS commit `e7d30c99` also edits
`tools/lsu_v332_matrix.py` (+19/−?). `git diff fc608224..HEAD -- tools/lsu_v332_matrix.py`
shows the FW02 ordinal correction (18/30/42/54 → 13/25/37/49/61), the LQ04 workload, the RP01
timeout/watchdog change (90→300 s, 5e8→2e7 cycles), the terminal fallback and the `--out-csv`
path fix. The executed FW02 commands contain ordinal 25, so the runs used the HEAD version.

### 4.2 Defects (file:line, root cause, one-shot fix)

**E-01 (D, high) — `ControlZeroProof` is structurally wrong.**
`tools/lsu_v332_report.py:195-205`:
```python
cmd = " ".join(s.get("cmd") or [])            # run_pilot argv, not gem5 argv
if not cmd and (outdir / "command.txt").exists(): ...
injector_absent = ("--chaos_lsqfwd" not in cmd and "--chaos_md04" not in cmd
                   and "--chaos_addrpath" not in cmd)
proof = ("INJECTOR_ABSENT" if (inj == 0 and injector_absent) else
         "MOUNTED_P0_INJECTED_0" if inj == 0 else "MISFIRE")
```
`summary.cmd` is the **run_pilot driver argv** (`python3 run_pilot.py --model … --probability 0.0`),
so it never contains any `--chaos_*` flag; `command.txt` is only read when `cmd` is empty,
which never happens. Result: `injector_absent=True` for all 60 controls. The check also omits
`--chaos_l1dfwd` and `--chaos_lq04`, so even reading the right file would misclassify LP01.
**One-shot fix:** always read `outdir/command.txt` (the executed gem5 argv); test the full set
`{"--chaos_addrpath","--chaos_lsqfwd","--chaos_l1dfwd","--chaos_md04","--chaos_lq04",…}`;
emit the three authoritative classes from §2.1 plus the gate source. Validation:
`python3 tools/lsu_v332_report.py` then assert 35 `MOUNTED_BUT_DISABLED` / 25 `INJECTOR_ABSENT`.

**E-02 (D, high) — seed missing from the run summary of 110/120 runs.**
`tools/lsu_v332_matrix.py:211` sets `seed = spec.get("seeds", [None]*5)[ctx-1]`, and only RP01
has a `seeds` list. The seed known to `run_pilot` (`pilot_meta.seed`,
`pilot_meta.excel_identity.seed`, or the injector `--*rng_seed` flag) is never copied into
`summary.json`. This produced `LSU_Fault_Control_Pair_Final_J.csv` with 60 blank seeds and the
"blank A03 seeds" symptom in the raw matrix table. **Fix:** after the run, read
`pilot_meta.json → seed` (fallback: parse the model's rng flag from `command.txt`) and write
`summary.seed` + `summary.seed_source` in the matrix. Validation: rerun the parser and assert
60/60 non-null seeds equal the frozen values.

**E-03 (D, high) — matrix and report write the same CSV path.**
`tools/lsu_v332_matrix.py:41` default `SUMMARY_CSV = audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final.csv`;
`tools/lsu_v332_report.py:326` also writes that exact path, with a different 20-column schema.
The leftover `audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final_J.csv` (15 columns, 60 blank
seeds, 55 blank terminals, 30 blank workloads) is the matrix's raw output saved under a `_J`
name. A rerun of the matrix will silently replace the curated table. **Fix:** change the
matrix default to `LSU_Fault_Control_Pair_Raw.csv` (or require `--out-csv`), and have the
report be the sole writer of the curated name. Validation: `git grep -n "Pair_Final.csv" tools/`.

**E-04 (D, high) — 30 contexts reuse the frozen SampleRunID/Seed with a different workload ELF.**
Root cause: the candidate workoverrides are in `CONTEXTS` (matrix:53-71) and passed via
`--workload` (matrix:169-170); the frozen row is never rewritten or flagged beyond
`CANDIDATE_PENDING_APPROVAL` in the curated table. **Fix (source-level, not CSV):** emit a
distinct identity status `WORKLOAD_OVERRIDE_PENDING_APPROVAL` and record
`FrozenSampleRunID`, `FrozenWorkloadSHA256`, `ExecutedWorkloadSHA256`, so the Excel can show
both. Do not silently reuse the frozen ID as if the sample were unchanged. Approval: **Y**
(researcher must approve the candidate workloads or reissue the frozen rows).

**E-05 (D, medium) — `FaultCommand` always blank by dead code.**
`tools/lsu_v332_report.py:324`: `"FaultCommand": (c.get("command", "") if False else "")`.
The `if False` branch guarantees an empty 60/60 column (`grep` on the curated CSV: 60 blanks).
**Fix:** `"FaultCommand": f.get("cmd_shell") or (f["outdir"] + "/command.txt")`; populate from
the executed `command.txt`. Validation: assert 60/60 non-empty and equal to the file contents.

**E-06 (D, medium) — RP01 `summary.terminal=CRASH` vs true `HANG_WATCHDOG`.**
`tools/lsu_v332_matrix.py:140-159` (`parse_rp01_stdout`) scans only `stdout.log` for
`CHAOS_RP01_WATCHDOG`, but the fatal message and the `CHAOS_RP01_WATCHDOG=EXPIRED` line go to
`stderr.log`/`lsq_fwd_injections.log`; `summary.terminal` therefore falls to `CRASH` on
exit_code 1. `tools/lsu_v332_report.py:91-94` does scan stderr/log and gets it right, hence
the disagreement. **Fix:** scan stdout+stderr+`lsq_fwd_injections.log` in the matrix; add a
`watchdog_expired` boolean to `summary.rp01`. Validation: RP01 summaries report
`terminal=HANG_WATCHDOG, watchdog=true` for all five faults.

**E-07 (D, medium) — provenance values are stale.**
`audit_v3_3_2/report/PROVENANCE.md` and `audit_v3_3_2/LSU_Formal_Experiment_Config.xlsx`
(`Provenance` sheet) state binary size `1149044528`; the live and archived binaries are
**1,149,140,984** bytes (`stat -c '%s' build/ARM/gem5.opt audit_v3_3_2/binary/gem5.opt.v332-070d68a6`).
The workbook also states `Final HEAD = fc608224…` while the repo HEAD is `3097ad82…`. The SHA
values themselves are correct. **Fix:** generate these two numbers from `stat`/`git rev-parse`
at package time; add `config_sha256`, `build_log_sha256`, and `source_head`. Validation:
`grep -c 1149044528` returns 0.

**E-08 (A, high latent) — MD04 control hazard** — see §3.2. File lines:
`configs/se/lsu_proxy.py:491,1092-1094`; `CHAOSMD04.cc:77,106,111`.

**E-09 (A, high latent) — DA04/LQ04/RP01 have no global-probability gate.**
DA04: `CHAOSLSQFwd.cc:972-989`; LQ04: `CHAOSLQ04.py` has no probability param and
`CHAOSLQ04.cc:58` self-attaches; RP01: `CHAOSLSQFwd.cc:625-726` has no probability check
(it is gated only by ordinal and by being mounted). The runner omits all three for controls,
so no live misfire, but a direct config invocation at `--probability 0.0` injects.
**One-shot fix:** a single mount predicate in `configs/se/lsu_proxy.py`: for the ordinal-gated
modes (`da04_be_bit0`, `f6_fw02`, `sq03_canwb`, `sp05_complete`, `fw05_older_src`,
`rp01_skip_replay`, CHAOSLQ04, CHAOSMD04) instantiate only when `args.probability > 0.0`
(plus the MD04 min-gate from §3.2). Validation: a config-level unit test that instantiates
with `--probability 0.0` and asserts the `board.chaos_*` child is absent.

**E-10 (A, medium latent) — SQ03/SP05 arm a watchdog in the p=0 control.**
`CHAOSLSQFwd.cc:149-161` (SQ03) and `:171-198` (SP05) schedule the watchdog unconditionally
inside the struct-mode block. If a control hangs, it aborts with
`CHAOS_SQ03_WATCHDOG_EXPIRED`/`CHAOS_SP05_WATCHDOG_EXPIRED` (fatal, exit 1), which the runner
classifies as a simulator error rather than a control failure. **Fix:** guard the scheduling
with `if (probability > 0.0f && p.sq03WatchdogCycles)` (and the SP05 equivalent), or omit the
injector in the control. Validation: a p=0 dry-run/config dump shows no
`xxxWatchdogCycles` scheduling path; a unit test on the constructor.

**E-11 (A, medium) — SQ01 control is "disabled by non-attachment".**
`CHAOSLSQFwd.cc:81-127`: the block that creates the log, the stats and sets `cpu->lsqFwd` is
entered only for `probability > 0` or a fixed set of ordinal modes that excludes `sq01_bit3`.
The control thus constructs the SimObject and the `ChaOSLsuTrigger` (which prints an exit
summary with `eligible=0`) but never registers the hook. This is safe but opaque; it also
means the SQ01 control does not exercise the same attachment path as the fault. **Fix:** make
the control omit `--chaos_lsqfwd` (same treatment as FW02/DA04) or add `Sq01Bit3` to the
injector's explicit p=0 gate (`maybeCorruptStoreData` at line 939 has none) and remove the
silent non-attachment. Prefer omission for consistency with §2.1.

**E-12 (D, high) — the runner records no injector-mount/gate classification.**
`run_pilot.py:1049-1104` (`meta` dict) has no `injector_mount`, `injector_attached`,
`probability`, or `gate` fields. Every downstream table has to guess (E-01 proves it guesses
wrongly). **Fix:** add to `pilot_meta.json`:
```json
"injector": {"simobject":"CHAOSAddrPath","mounted":true,"attached":true,
             "global_probability":0.0,"mode":"a01_bit3_load","gate":"probability<=0 at CHAOSAddrPath.cc:250"}
```
and have `lsu_v332_report.py` read it. Validation: 60 controls produce a classification that
matches §2.1 without parsing logs.

**E-13 (D, medium) — 15/120 runs bypass `run_pilot` and lack manifest/pilot_meta/trace.**
A03 fault (5) and RP01 fault+control (10). Evidence: `manifest.json`, `pilot_meta.json` and
`trace_v31.jsonl` are absent from exactly those 15 directories. RP01 controls also have no
trace, so their zero-injection proof is weaker (§2.2). **Fix:** add RP01 to
`run_pilot.MODELS` with a `build_model_extra` branch and a trace-preserving timeout, or extend
the direct path in `lsu_v332_matrix.py:225-244` to run the `prop_trace_to_v31` conversion and
write a minimal manifest with the binary/config/workload SHAs. Validation: all 120 dirs contain
the five required artifacts.

**E-14 (D, medium) — runner/config drift.** `run_pilot.py:56-57` `MODELS` omits RP01;
`run_pilot.py:60-73` `_workload_for` still maps the stock names (`sq_forward`, `sq_drain`,
`store_path`, `replay_dependency`) that the matrix then overrides; `run_pilot.py:48` `EXCEL`
points to `…Plan-v3.2.4.xlsx`, not the authoritative v3.2.7 workbook. Seeds happen to be
identical (verified: 60/60), but the identity source is not the authoritative file.
**Fix:** add RP01, make `_workload_for` return the executed name (or delete it and require
`--workload`), and point `EXCEL` at v3.2.7 (or add an `--excel` argument with a default and
record its SHA in the manifest).

**E-15 (D, medium) — trace identity is provisional and controls carry a fault ID.**
`run_pilot.py:673-676` deliberately sets `sample_run_id=pilot_id`, `run_id=PILOT-<model>`,
`sub_task_id=PILOT-<model>-S01`; `run_pilot.py:944-952` passes `fault_id=sample.fault_config_id
or model`. Control traces therefore show `"fault_id":"A01-CFG01"` (verified first line of
`A01-R01-control/trace_v31.jsonl`). **Fix for formal v3.3.3:** pass `--preserve-sample-id`
(or unconditionally use the frozen identity), and for controls write
`fault_id="NO_FAULT"` + `matched_fault_id="A01-CFG01"`. Validation: every trace's
`sample_run_id` equals the authoritative `A01-F0-W1-S01-R01`-style ID; controls show
`NO_FAULT`.

**E-16 (D, low) — no concurrency guard.**
`lsu_v332_matrix.py:215-217` `rm -rf`s the outdir and both tools write fixed paths; two
concurrent invocations (or two agents) can delete each other's run and interleave CSV writes.
**Fix:** a lockfile per outdir/CSV or a `--require-empty` flag, and write CSVs via
`<name>.tmp` + `os.replace`. Validation: a two-process test leaves both runs intact.

**E-17 (D, low) — A03 fault count is a log cap.**
`A03-R01-fault/summary.json` `injection_count=20000` mirrors
`addrpath_injections.log:A03_LOG_CAPPED: cap=20000`. It is not a per-fault count.
**Fix:** add `injection_count_capped:true`, `log_cap:20000`, and `injection_policy:"F5_PERSISTENT"`.

**E-18 (D, low) — `summary.injection_events` is null for FW02-family runs.**
`lsu_v332_matrix.py:294` reads `meta.injection.events`, but the FW02 `_fw02_summary` returns
`{observed,suppressed,load_seq,store_seq}` with no `events` key. **Fix:** read `suppressed`
for FW02 or add `events` to the runner's FW02 injection dict.

### 4.3 Runner dispatch map (verified)

| Model | Flag(s) emitted by the producing driver | SimObject | Mode |
|---|---|---|---|
| A01 | `--chaos_addrpath --agu_pre_mode a01_bit3_load --addrpath_lsu_tier F0` | CHAOSAddrPath | A01 bit-3 load EA flip |
| A03 | `--chaos_addrpath … a03_bit3_stuck0_load --addrpath_lsu_tier F5 --addrpath_max_faults 0` | CHAOSAddrPath | F5 persistent stuck-at |
| FW02 | `--chaos_lsqfwd --lsq_struct_mode f6_fw02` | CHAOSLSQFwd | suppress forwarding |
| FW05 | `--chaos_lsqfwd --lsq_struct_mode fw05_older_src` | CHAOSLSQFwd | wrong older source |
| SQ01 | `--chaos_lsqfwd --lsq_struct_mode sq01_bit3 --lsqfwd_lsu_tier F0` | CHAOSLSQFwd | SQ data bit-3 |
| SQ03 | `--chaos_lsqfwd --lsq_struct_mode sq03_canwb` | CHAOSLSQFwd | canWB 0→1 |
| SP05 | `--chaos_lsqfwd --lsq_struct_mode sp05_complete` | CHAOSLSQFwd | premature complete |
| DA04 | `--chaos_lsqfwd --lsq_struct_mode da04_be_bit0 --lsqfwd_lsu_tier F0` | CHAOSLSQFwd | byte-enable 0xF→0xE |
| LP01 | `--chaos_l1dfwd --l1dfwd_fault_mask 0x8` | CHAOSL1DForward | load-response byte-lane 0 |
| MD04 | `--chaos_md04 --md04_first_clock 0 --md04_probability 1.0` | CHAOSMD04 | dependency violation miss |
| LQ04 | `--chaos_lq04 --lq04_event_ordinal N` | CHAOSLQ04 | LQ lifetime corruption |
| RP01 | `--chaos_lsqfwd --lsq_struct_mode rp01_skip_replay --rp01_event_ordinal N` | CHAOSLSQFwd | skip partial-replay reschedule |

Dispatch is correct for all 12 models: the flag→SimObject mapping in `configs/se/lsu_proxy.py`
(`if args.chaos_addrpath:` line 1119; `if args.chaos_lsqfwd:` line 883; `if args.chaos_l1dfwd:`
line 1071; `if args.chaos_md04:` line 1091; `if args.chaos_lq04:` line 912) matches the
driver. Only RP01 is outside `run_pilot` (E-13/E-14).

---

## 5. Authoritative identity (SampleRunID / Seed)

Source: `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv` and workbook v3.2.7
sheet `5.60个样本执行矩阵`. The two files are **byte-for-byte consistent** for
SampleRunID/Seed/FaultModelID/EventOrdinal (0 differences across 60 rows; verified
programmatically). All 60 rows are present; no missing SampleRunID.

The mapping from the working `V332-<model>-R<ctx>` IDs is exact and 1:1 by `(model, RNN)`.
The authoritative `-S0X` sub-task suffix differs per model (S01/S02); `RunID` is the
`-W<n>` prefix.

| Model | R01 | R02 | R03 | R04 | R05 | Seeds (R01…R05) | Frozen workload / ELF SHA | Executed workload / ELF SHA | Status |
|---|---|---|---|---|---|---|---|---|---|
| A01 | A01-F0-W1-S01-R01 | A01-F0-W1-S01-R02 | A01-F0-W1-S01-R03 | A01-F0-W1-S01-R04 | A01-F0-W1-S01-R05 | 2108120075, 1113826800, 1302709433, 2194451614, 3228552887 | agu_addrmodes / `90a1900377d2…` | agu_addrmodes / same | MATCH |
| A03 | A03-F5-W1-S01-R01 | A03-F5-W1-S01-R02 | A03-F5-W1-S01-R03 | A03-F5-W1-S01-R04 | A03-F5-W1-S01-R05 | 663646247, 1626885462, 110775855, 2766846323, 1156093484 | agu_addrmodes / `90a1900377d2…` | agu_addrmodes / same | MATCH |
| FW02 | FW02-F6-W4-S01-R01 | …-R02 | …-R03 | …-R04 | …-R05 | 2941542370, 2129071279, 1336081385, 527667424, 3622278636 | sq_forward / `132a84f7f21b…` | sq_forward_w4v2 / `a08fb3a7b8bb…` | ELF OVERRIDE |
| FW05 | FW05-F6-W8-S01-R01 | …-R02 | …-R03 | …-R04 | …-R05 | 1025137124, 1653118510, 2442802213, 899944922, 2836530945 | fw05_forward / `0cf405092e33…` | fw05_forward / same | MATCH |
| SQ01 | SQ01-F0-W3-S01-R01 | …-R02 | …-R03 | …-R04 | …-R05 | 591611458, 576447973, 1257175390, 3116972755, 172636228 | sq_drain / `d423539c68ec…` | sq_reload_v3212 / `bcab9cc5e1e4…` | ELF OVERRIDE |
| SQ03 | SQ03-F0-W3-S02-R01 | …-R02 | …-R03 | …-R04 | …-R05 | 2214819981, 1486471869, 3102670938, 3974203372, 729970077 | sq_drain / `d423539c68ec…` | sq_reload_v3212 / `bcab9cc5e1e4…` | ELF OVERRIDE |
| SP05 | SP05-F6-W6-S01-R01 | …-R02 | …-R03 | …-R04 | …-R05 | 1489155957, 1290498198, 2768710389, 2741073922, 4098160626 | store_path / `906b3798adc6…` | sq_reload_v3212 / `bcab9cc5e1e4…` | ELF OVERRIDE |
| DA04 | DA04-F0-W8-S02-R01 | …-R02 | …-R03 | …-R04 | …-R05 | 4185444934, 2627302015, 3592849939, 3815557835, 2016743094 | alignment / `89ff937a73a0…` | alignment / same | MATCH |
| LP01 | LP01-F0-W5-S01-R01 | …-R02 | …-R03 | …-R04 | …-R05 | 1349924126, 2648660520, 2021175746, 3894776903, 1604604537 | load_response / `3779e8ced41a…` | load_response / same | MATCH |
| MD04 | MD04-F6-W7-S01-R01 | …-R02 | …-R03 | …-R04 | …-R05 | 2595563470, 811948497, 2545691512, 2149193331, 1008734674 | replay_dependency / `ca15390f1a79…` | md04_violations_v332 / `dd241c3097e6…` | ELF OVERRIDE |
| LQ04 | LQ04-F0-W2-S01-R01 | …-R02 | …-R03 | …-R04 | …-R05 | 1842987246, 2188214204, 3953171871, 4153250964, 3410523942 | lq_lifetime_ordinal / `fa25f785a482…` | lq_lifetime_ordinal / same | MATCH |
| RP01 | RP01-F6-W7-S01-R01 | …-R02 | …-R03 | …-R04 | …-R05 | 3135797961, 226489823, 1735144973, 2455796178, 3984724524 | replay_dependency / `ca15390f1a79…` | replay_partial_v332 / `3f880cba7b6d…` | ELF OVERRIDE |

(`…-R0X` above abbreviates the same model's `-S0X-R0X` prefix; full strings were verified
against the CSV for all 60 rows.)

### Gaps / corrections needed for the v3.3.3 Excel

1. **ID remap:** replace all `V332-<model>-R<ctx>` with the 60 authoritative `SampleRunID`s
   above. No authoritative ID is missing; no ID is reused for two contexts. The mapping is
   deterministic. Do **not** invent new IDs.
2. **Seed:** all 60 frozen seeds are valid and already present in
   `audit_v3_3_2/roi/LSU_60Context_ROI_Percentile_Mapping.csv` (0 blank). The blank-seed
   symptom is in `summary.json` (110/120) and the raw matrix table `…_Final_J.csv` (60/60),
   not in the authoritative workbook or the curated ROI table. A03 seeds are **not** blank in
   the v3.2.7 workbook sheet 5 (`A03-F5-W1-S01-R01 = 663646247`, etc.).
3. **Workload identity:** for the 30 override rows, keep the frozen SampleRunID/Seed but add
   `FrozenWorkloadPath`, `FrozenWorkloadSHA256`, `ExecutedWorkload`, `ExecutedWorkloadSHA256`
   and `IdentityStatus=WORKLOAD_OVERRIDE_PENDING_APPROVAL`. Do not present them as unchanged
   frozen samples.
4. **Event ordinal:** the frozen `EventOrdinal` is 1–5 (context index), while the executed
   injector ordinal is the percentile value in §1.1. Both must be separate columns
   (`ExcelEventOrdinal`, `InjectorEventOrdinal`). `pilot_meta.excel_identity` already stores
   both (`event_ordinal`, `event_ordinal_used`) for 105 runs.

---

## 6. Binary / config provenance

| Item | Recorded | Verified live / in evidence | Status |
|---|---|---|---|
| Git HEAD | `3097ad82e7066f18fc35cf64dcb612a05c1fc021` | `git rev-parse HEAD` = same | OK |
| Source-equivalent HEAD | `fc60822408cbb3f5af4788bd99fc82c114917367` | exists; `fc608224..HEAD` = 3 commits (results/evidence/package), but `e7d30c99` also edits `tools/lsu_v332_matrix.py` | OK with caveat (not purely results) |
| Final binary | `build/ARM/gem5.opt` | SHA `070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca` | OK |
| Binary size | `1,149,044,528` (PROVENANCE.md, supplement workbook) | `stat` = `1,149,140,984` | **STALE (E-07)** |
| Archived binary | `audit_v3_3_2/binary/gem5.opt.v332-070d68a6` | same SHA + size; hardlink (nlink=2) | OK |
| Baseline binary | `audit_v3_3_2/binary/gem5.opt.v331-d3807fbe` | SHA `d3807fbe…e2b2` | OK |
| Build logs | `/tmp/v332_build.log`, `/tmp/v332_build2.log` | 0 `error:` lines each; `scons: done building targets.` in both; binary mtime 18:36:18 matches build2 start 18:36 | OK |
| Config | `configs/se/lsu_proxy.py` | SHA `01f912de3388aaf420aa69d5dd55098ddfb97851faf0269a6b009fcc389bf6e5`; identical in all 105 manifests | OK |
| Per-run binary SHA | 120 `summary.json` | one distinct value: `070d68a6…f5ca` | OK |
| Per-run manifest binary/config SHA | 105 `manifest.json` | one distinct binary and one distinct config value | OK |
| Workload/ELF SHA | 105 manifests | equals the live `--cmd=` file SHA for 105/105 | OK |
| Frozen CSV `gem5Commit` | `6f98088a7144d7f6fb22d985be3023ac5658e71b` | not the run HEAD (`fc608224`) | **STALE** |
| Frozen CSV `BinaryPath` / `BinarySHA256` | points at the workload ELF (`90a190…`, `132a84…`, …) | gem5 binary is `build/ARM/gem5.opt` / `070d68a6…` | **MISLABELLED (E-17)** |
| Frozen CSV `WorkloadPath` prefix | `…/worktrees/lsu-platform-v3.2/…` | current worktree is `…/lsu-platform-v3.2.12/`; ELF SHAs identical for the 30 matching rows | stale path only |
| `ConfigFrozen` | `NO` (all 60 rows) | still `NO` | open blocker |
| PROVENANCE base commit/binary | `3504ec23…`, `d3807fbe…` | match the archived baseline binary | OK |
| `audit_v3_3_2/binary` git state | untracked (`?? audit_v3_3_2/binary/`) | `git status --short` confirms | OK (documented as not committed) |

---

## 7. Excel output requirements for v3.3.3

### 7.1 Sheets that must exist

Keep/update the existing workbook structure:
1. `1.实验总览`, `2.研究问题与Observation映射`, `3.最终12模型矩阵`, `4.源码Hook审计`,
   `5.60个样本执行矩阵`, `6.工作负载及无故障基线`, `7.Trace Hook规范`, `8.终态分类`,
   `9.实验执行计划`, `10.暂缓研究模型`, `11.风险与待确认事项`, `12.变更记录`,
   `13.v3.2实施状态` … `22.v3.2.12传播链闭包矩阵`.
2. New `23.v3.3.3 60-Context ROI Mapping` — one row per context with:
   `SampleRunID, RunID, SubTaskID, Seed, ContextID, Workload, WorkloadStatus,
   ROI_Start_Ordinal, ROI_End_Ordinal, ROI_N, Percentile, Rank_k, Absolute_Eligible_Ordinal,
   ExcelEventOrdinal, InjectorEventOrdinal, InjectionIdentity, EvidenceBinarySHA, EvidencePath,
   MappingStatus`.
3. New `24.v3.3.3 Fault/Control Pairing & Zero-Injection Proof` — one row per context with:
   `SampleRunID, Seed, ControlRunID, ControlSeed, SameBinarySHA, SameConfigSHA, SameELF,
   SameOrdinal, InjectorMountClass (INJECTOR_ABSENT|MOUNTED_BUT_DISABLED|
   MOUNTED_BUT_SUPPRESSED), MountEvidence, Gate, ControlInjectionCount, ControlTraceInjections,
   ControlOracle, ControlExitCode, ZeroProofPaths`.
4. New `25.v3.3.3 Provenance` — `RepoHEAD, SourceHEAD, Gem5BinarySHA256, Gem5BinarySize,
   ConfigScriptSHA256, BuildLog, BuildLogSHA256, BuildErrors, ManifestSHA256(per run),
   FrozenMatrixSHA256, FrozenWorkbookSHA256, ELFSHA256(per model), BaselineBinarySHA256`.
5. New `26.v3.3.3 Defect Ledger` — the E-01… issues with status, affected contexts, approval
   flag, validation command.

### 7.2 Columns that must be added to sheet 5 (and CSV)

`ExecutedWorkload`, `ExecutedWorkloadSHA256`, `FrozenWorkloadPath`, `FrozenWorkloadSHA256`,
`IdentityStatus`, `Gem5BinarySHA256`, `ConfigScriptSHA256`, `ExcelEventOrdinal`,
`InjectorEventOrdinal`, `InjectorMountClass`, `SampleRunID_Working` (the old
`V332-<model>-R<ctx>` for traceability).

### 7.3 Existing workbook defects to fix

1. **W6 `ExpectedGolden` stale:** sheet `6.工作负载及无故障基线` W6 has
   `Oracle=2543a2a60de01795`, `ExpectedGolden=7284dc0b3f6c64cf`; the actual
   `store_path.golden` is `checksum=0x2543a2a60de01795`. Fix the ExpectedGolden cell (or drop
   the duplicate column and reference `Oracle`).
2. **W8 `ExpectedGolden` stale:** W8 has `Oracle=3f89eab79392ce69`,
   `ExpectedGolden=8009aab3f75f7417`; `alignment.golden` is `checksum=0x3f89eab79392ce69`.
   Same fix.
3. **Missing workload rows:** sheet 6 has only W1–W8 (`agu_addrmodes, lq_lifetime, sq_drain,
   sq_forward, load_response, store_path, replay_dependency, alignment`). The 60 contexts
   actually execute `sq_reload_v3212` (SQ01/SQ03/SP05, no W row), `sq_forward_w4v2` (FW02,
   no W row), `fw05_forward` (FW05, no W row), `md04_violations_v332` (MD04, no W row),
   `replay_partial_v332` (RP01, no W row), `lq_lifetime_ordinal` (LQ04, no W row). Add rows
   with absolute path, ELF SHA, golden, baseline status, and a `Candidate=YES` flag.
4. **A03 seeds blank in a working table:** not in the authoritative ROI mapping CSV (60/60
   populated) and not in workbook sheet 5 (A03 seeds present). It **is** true in
   `audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final_J.csv` (60/60 seed column blank) and in
   `summary.json` (110/120 null). Fix E-02 and delete/regenerate the `_J` table.
5. **Working IDs:** replace `V332-<model>-R<ctx>` with the authoritative SampleRunIDs
   everywhere in the Excel (sheet 23/24 and any propagation/closure sheet).
6. **Supplement workbook provenance:** `LSU_Formal_Experiment_Config.xlsx` `Provenance` sheet
   has `Final HEAD=fc608224…` (repo HEAD is `3097ad82…`) and binary size `1149044528`
   (actual `1149140984`). Regenerate (E-07).
7. **Sheet 22 granularity:** `22.v3.2.12传播链闭包矩阵` aggregates by `ModelID@hash`, not by
   the 60 contexts. v3.3.3 needs a per-context closure/propagation sheet keyed by
   authoritative SampleRunID (sheet 23/24 cover the identity side; the propagation sheet is
   Agent C's deliverable but must join on the same key).

---

## 8. Consolidated issue list

| ID | Class | Severity | One-line summary | Affected | Fix type |
|---|---|---|---|---|---|
| E-01 | D | high | `ControlZeroProof` reads the run_pilot argv and mislabels all 60 controls `INJECTOR_ABSENT`; 35 are mounted | 60 controls | tool source |
| E-02 | D | high | Seed is null in 110/120 `summary.json`; only RP01 has a seeds list | 110 runs | matrix source |
| E-03 | D | high | Matrix and report write the same curated CSV path; `_J` shows the collision | tooling | path rename |
| E-04 | D | high | 30 contexts reuse frozen SampleRunID/Seed with a different workload ELF | FW02/SQ01/SQ03/SP05/MD04/RP01 | identity status + approval |
| E-05 | D | medium | `FaultCommand` always blank via `if False` dead code | 60 rows | report source |
| E-06 | D | medium | RP01 `summary.terminal=CRASH` vs true `HANG_WATCHDOG` (stdout-only parse) | 5 fault runs | matrix source |
| E-07 | D | medium | PROVENANCE/supplement binary size stale (1149044528 vs 1149140984); Final HEAD stale | package | generated values |
| E-08 | A | high (latent) | MD04 gates only on `--md04_probability` (default 1.0), not `--probability` | MD04 mount | config/injector |
| E-09 | A | high (latent) | DA04/LQ04/RP01 have no global-probability gate; mounting at p=0 injects | DA04/LQ04/RP01 | config mount predicate |
| E-10 | A | medium (latent) | SQ03/SP05 arm a watchdog in the p=0 control | 10 controls | injector ctor |
| E-11 | A | medium | SQ01 control disabled only by non-attachment; no in-injector gate | 5 controls | runner/injector |
| E-12 | D | high | Runner records no injector mount/attach/gate fields in pilot_meta | 105 metas | run_pilot |
| E-13 | D | medium | A03-fault + RP01 fault/control bypass run_pilot: no manifest/pilot_meta/trace | 15 runs | runner/driver |
| E-14 | D | medium | run_pilot lacks RP01; `_workload_for` stock names; EXCEL points to v3.2.4 | runner | run_pilot |
| E-15 | D | medium | Trace identity uses PILOT-*; controls carry a fault_id | 105 traces | run_pilot/convert |
| E-16 | D | low | No lock; concurrent matrix runs clobber outdirs/CSVs | tooling | driver |
| E-17 | D | low | A03 `injection_count=20000` is a log cap, not a fault count | A03 ×5 | matrix source |
| E-18 | D | low | `summary.injection_events` null for FW02-family | 15 runs | matrix source |
| E-19 | D | medium | Frozen CSV `BinarySHA256`/`BinaryPath` hold the workload, not gem5.opt; gem5Commit stale | frozen Excel | Excel |
| E-20 | D | medium | Frozen `EventOrdinal` 1–5 (context) vs executed injector ordinal | 60 rows | Excel columns |
| E-21 | D | medium | Sheet 6 W6/W8 `ExpectedGolden` stale; candidate workload rows missing | workbook sheet 6 | Excel |

Severity here is evidence/consumer impact for v3.3.3, not a claim about the physics of any
fault run.

---

## 9. Bottom line

- **Pairing identity is sound at the pair-internal level.** All 60 fault/control pairs use the
  same gem5 binary SHA (`070d68a6…`), the same config script SHA (`01f912de…`), the same
  executed ELF (`--cmd` path and SHA), the same seed (literal for 35, intended/recoverable for
  25), the same CPU/variant (`O3/B0`), and the same intended event ordinal. The fault's target
  dynamic instruction appears in the paired control trace in 50/50 pairs that have traces; A01
  goes further (control eligible count equals the fault ordinal 5/5).
- **All 60 controls prove zero injections.** Five independent checks (summary count, pilot_meta
  acceptance, activation status, trace scan of 1,384,799 records, per-model logs) are clean.
- **The curated control table's classification is wrong and must be fixed before the Excel is
  written.** The authoritative split is **35 MOUNTED_BUT_DISABLED / 25 INJECTOR_ABSENT / 0
  SUPPRESSED**, not 60 ABSENT. Root cause is E-01 (wrong argv source), not the runs.
- **The dangerous close-path hazards are latent, not live.** MD04 (`md04_probability` defaults
  1.0), DA04, LQ04 and RP01 have no global-probability gate; all current controls are safe only
  because the runner omits those injectors. SQ03/SP05 controls arm watchdogs. These need a
  single mount predicate + runner metadata (E-08…E-12).
- **Runner/tooling is tracked and clean**, contrary to the stale v3.3.2 claim, but it has real
  output-integrity defects: seed/terminal dropped from 110/97 summaries, a CSV path collision,
  a dead-code empty column, and a wrong RP01 terminal.
- **Authoritative identity is fully available and 1:1 mappable:** 60/60 SampleRunIDs and
  60/60 seeds exist and match the frozen workbook. The only identity gap is the 30
  candidate-workload overrides that reuse the frozen ID/seed while executing a different ELF
  (E-04); this requires explicit override status and researcher approval, not invented values.
- **Provenance is correct for SHA values** (HEAD, source HEAD, binary, config, 120/120 run
  binary SHAs, 105/105 manifest ELF SHAs) but stale for the binary size and workbook Final
  HEAD. Build logs show 0 errors.
- **Excel:** the v3.3.3 workbook must add authoritative-ID/seed, mount-class, provenance and
  defect-ledger sheets, add executed/frozen workload columns, and repair the W6/W8
  `ExpectedGolden` cells and the missing candidate-workload rows.

## 10. Could not verify

1. **Frozen ROI / warm-up:** no command encodes ROI or warm-up for 105 of 120 runs; manifests
   say `NEEDS_RESEARCHER_CONFIRMATION`. Pair equality is therefore not verifiable beyond
   "identical commands where the flags exist". `n/a`.
2. **RP01 control dynamic context at instruction level:** no `trace_v31.jsonl` exists for RP01
   fault or control; the proof rests on identical command/workload/seed and `summary.rp01`.
3. **A03 fault dynamic context at instruction level:** no `trace_v31.jsonl`, no
   `pilot_meta.json`, no `manifest.json`; only the raw `addrpath_injections.log` and stdout
   checksum (1fd794b8489219e1, which does not match the frozen A03 oracle
   `728e604ffcec539d` — expected, because the run is a fault run and is partial/timed out; I
   did not grade it).
4. **True injection count for A03:** only the 20,000 log cap is observable; the actual number
   of persistent applications after the cap is unknown from the retained artifacts.
5. **Whether the six candidate workloads are the approved formal workloads:** that is a
   researcher decision (B1/B6), not determinable from files.
6. **Trace-level `event_id`/`fault_id` semantics for the formal campaign:** the current traces
   are PILOT-identified; I verified their presence and values but did not re-run conversion.
7. **`param`/`config.ini` semantic equality beyond the CPU/variant fields:** I diffed whole
   `config.ini` files for five representative pairs; the only differences were the injector
   block and `probability`. A byte-level diff of all 60 pairs was not performed (the injector
   blocks legitimately differ for absent controls).
8. **v3.2.7 workbook sheets 7–21 semantic content:** inspected for provenance/seed/ID purposes
   only; not re-graded here (other agents own trace/oracle and propagation content).
