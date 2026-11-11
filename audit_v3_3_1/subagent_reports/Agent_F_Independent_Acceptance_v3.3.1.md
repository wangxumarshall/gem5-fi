# LSU v3.3.1 — Agent F Independent Cross-Acceptance Audit

**Date:** 2026-11-11
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111` (HEAD `8f7a1354`)
**Auditor posture:** adversarial — try to refute the package, not to agree.
**Read-only:** no tracked file, Excel, pilot, record, CSV, or verdict was modified.
**Authorized probes run (2):**
1. `python3 tools/lsu_v331_census.py --model A01 --seed 1113826800 --ordinals 1059 --tag FCHECK_A01 --timeout 30` → `K=1059 rc=0 inj=1 pc=0x400598 seq=12978 addr=4796416 (0x493000)`
2. `python3 tools/lsu_v331_census.py --model FW05 --seed 2836530945 --ordinals 1800 --tag FCHECK_FW05 --timeout 30` → `K=1800 rc=0 inj=1 pc=0x400564 seq=46484 addr=4790728 (0x4919c8)`; `sq_entry_generation=10296`
(Probe artifacts were removed after recording; the only new persistent file is this report.)

---

## 0. Verdict summary

**The package's headline status is honest and defensible: `PARTIALLY_READY` / `12_MODEL_FORMAL_READY = NO`.** The four 60-row CSVs are structurally sound (60 unique rows each), the status tally is exact, the percentile arithmetic is self-consistent, and the largest claims (A01/FW05/DA04 ROI and ordinals, SQ/SP05 store catalogue, MD04=1 / FW02=0 / RP01=0 / LP01 gap) are reproducible from the retained census and from two fresh probes.

**However, the package contains real provenance and internal-consistency defects that block any stronger READY claim:**
- **C1 (major):** LQ04's five mapping rows attribute `EvidenceBinarySHA = d3807fbe` (final binary) to evidence that is actually the **v3.2.10 historical pilot** on `f3c2a442` — a misattribution.
- **C2:** LQ04 distinctness `Generation = 1` for all five rows contradicts the cited `lq04_injections.log` (gen 1..5).
- **C3:** The report's FW05 claim of "different addresses" is false for R01 vs R05 (both `0x4919c8`).
- **C4:** The 12-model CSV says MD04 is statically sufficient (256 alias pairs, `EligibleEventSufficiency=YES`) while the measured census says `N_ROI=1`; not reconciled.
- **C5:** The 12-model CSV names `68c6ce73` as the "FINAL binary"; the only binary on disk is `d3807fbe`.
- **C6:** The claimed A01 coarse scan (K=100..1295, 1030–1049, 1230–1239) is **not retained**; the ROI lower bound rests on a single positive point (K=1040).
- **C7/C8:** Minor count/phrasing errors in Q6 and Q9.
- **C9:** `lsu_v331_build_mapping.py` hardcodes ROI/N/ordinals; the census only fills seq/PC/addr, so the docstring's "no value is invented"/"built from census" is overstated.

No model can be defended as **formal-ready**. `PARTIALLY_READY` is the correct ceiling.

---

## 1. The 15-item check table

| # | Claim | Verdict | Command / observation |
|---|---|---|---|
| 1 | Four 60-row CSVs: 60 unique (ModelID,ContextID), no blank required cells | **CONFIRMED (with caveat)** | `csv.DictReader` on all four: rows=60, unique=60, dups=[]; per-model exactly 5, per-context R01–R05 exactly 12. Mapping has blanks only in `Notes` (optional) and in ROI fields of explicitly NOT_AVAILABLE rows (FW02/RP01 `ROI_N=0`; **LP01 `ROI_N` is blank rather than `n/a`/`0`**). |
| 2 | Status tally MAPPED 20 / CAVEAT 5 / RECOMMENDED 15 / INSUFFICIENT 15 / GAP 5 | **CONFIRMED** | `Counter(MappingStatus)` = `{MAPPED:20, MAPPED_WITH_SEMANTIC_CAVEAT:5, INSUFFICIENT_EVENTS:15, MAPPED_ON_RECOMMENDED_WORKLOAD:15, OBSERVABILITY_GAP:5}`. |
| 3 | A01 ROI 1040–1234 (N=195); pct 1059/1098/1137/1176/1215; R04/R05 share PC 0x4006d0 but differ seq/addr | **CONFIRMED** | Mapping A01 rows: ROI 1040–1234, N=195 (195 span), ranks 20/59/98/137/176 → abs 1059/1098/1137/1176/1215; R04 seq 14719 addr 0x493230, R05 seq 15086 addr 0x493368, both PC 0x4006d0. Boundary K=1234 in-main / K=1235 libc 0x409928 retained. |
| 4 | A03 shares A01 stream; ordinal 1059 activation seq 12978; exactly 3/5 ALREADY_STUCK (R01/R03/R04) | **CONFIRMED** | `A03_w1_pct_r01.jsonl`: K1059 reason=ALREADY_STUCK affected=0 dyn_inst_seq=12978; K1137 ALREADY_STUCK (14049); K1176 ALREADY_STUCK (14719); K1098 & K1215 STUCK_APPLIED. All `pc=0` in A03_STREAM. |
| 5 | FW05 ROI 1–2000 (N=2000); pct 200/600/1000/1400/1800; all load PC 0x400564 | **CONFIRMED (sub-claim refuted)** | Mapping + census: ROI 1–2000, ranks 200/600/1000/1400/1800, all PC 0x400564; K2001 has 0 injections (end boundary). **Refuted sub-claim:** report Q2 says "different addresses"; R01 and R05 are both `0x4919c8` (confirmed by fresh K=1800 probe). Entry generations do differ (2296→10296). |
| 6 | DA04 ROI 33–1056 (N=1024); pct 135/340/544/749/954 | **CONFIRMED** | `DA04_w8b_r01.jsonl`: K32 stack `0x7ffffefce0` (out), K33 `0x491991` (in), K1056 `0x49298d` (in), K1057 `0x491650` (out); rank arithmetic exact. Five addresses distinct (0x491b29…0x4927f5). |
| 7 | LQ04 N=5; anchors seq 3..7 / PC 0x400338..0x400348 / lq_idx 1..5 | **CONFIRMED (evidence historical)** | `docs/.../pilots_v3_2_10/LQ04-R0{1..5}/lq04_injections.log`: seq=3/4/5/6/7, pc=0x400338/33c/340/344/348, lq_idx=1..5. These are v3.2.10 logs, not a v3.3.1 census. |
| 8 | SQ pct SQ01 1018/1044/1069/1095/1121; SQ03 1021/1047/1072/1098/1124; SP05 952/978/1003/1029/1055; store seq 13328/15122/16847/18641/20435 | **CONFIRMED** | Mapping + census: SQ01 sqreload K{1018,1044,1069,1095,1121}; SQ03 K{1021,1047,1072,1098,1124}; SP05 K{952,978,1003,1029,1055} (reruns after disk failure carry the data). Store seq and addrs 0x4919f0/0x491ac0/0x491b88/0x491c58/0x491d28 all match. Rank 13/39/64/90/116 = ceil(p·128). |
| 9 | MD04 N_ROI=1 (only ordinal 3 in main); FW02 N_ROI=0 (no data load); RP01 N_ROI=0 (no partial overlap); LP01 observability gap (no PC/VA) | **CONFIRMED** | MD04 census: ROI 3–3 N=1, K3 seq 17488 pc 0x400530 addr 0x491990; K1/K2/K4/K5/K6 are libc/helper. FW02/RP01: no event (Agent B §W4/W7; 12-model CSV ROIFeasible=NO). LP01 JSONL: `pc=null`, detail carries only `addr=0x80bf0` (physical), no VA. |
| 10 | PARTIALLY_READY and FORMAL_READY=NO consistent with CSVs | **CONFIRMED** | 40/60 mapped (25 on formal workloads, 15 on unapproved SQ workload); 20/60 unmapped; 2/60 controls READY; 0 formal campaigns. The report's Section 3 states exactly this. |
| 11 | No frozen file modified; git shows only untracked audit_v3_3_1/ + plan + tools | **CONFIRMED** | `git status --porcelain` = `?? .tmp_lsu_conc/`, `?? audit_v3_3_1/`, `?? docs/superpowers/plans/2026-11-11-...md`, `?? tools/lsu_v331_build_mapping.py`, `?? tools/lsu_v331_census.py`; `git diff --stat` empty; `git diff --cached --stat` empty. (`.tmp_lsu_conc/` was pre-existing and untracked.) |
| 12 | Census JSONL matches per-K injection logs for ≥3 spot-checks | **CONFIRMED (3/3)** | A01 K1059 log `dyn_inst_seq=12978 pc=400598 golden_ea=493000`; FW05 K200 log `LoadSeq: 16084 … sq_entry_generation=2296`; DA04 K135 log `seq: 14320 … sq_idx: 1563 … old_addr: 0x491b29`. All equal the JSONL rows. |
| 13 | Rank_k = ceil(Percentile·ROI_N); Absolute_Eligible_Ordinal in [ROI_Start, ROI_End] | **CONFIRMED (all 35 mapped rows)** | Programmatic check: for every mapped row `Rank_k == ROI_Relative_Ordinal == ceil(p·N)`, `abs == start+k-1`, `start ≤ abs ≤ end`, and `end-start+1 == N`. |
| 14 | Report answers all 11 required questions | **CONFIRMED (with one count error)** | Q1–Q11 all present with evidence. **Q6 error:** `NO_CONSUMER_EDGE: 10` but the parenthetical lists only 9 (omits A01-R03). All other Q6 MissingEdges counts match exactly. |
| 15 | No historical/prior-quoted chain or recommendation turned into approved fact | **CONTRADICTED (provenance), otherwise clean** | SQ switch is correctly "approval pending"; FW05 is marked PRIOR_QUOTE; controls are not claimed approved. **But** LQ04 historical-pilot evidence is presented as `MAPPED (observed)` with `EvidenceBinarySHA=d3807fbe` although the evidence is on `f3c2a442` (see C1). This is the one place historical evidence is attributed to the final binary. |

---

## 2. Independent counts

**Per model (each of the four 60-row CSVs):** A01 5, A03 5, FW02 5, FW05 5, SQ01 5, SQ03 5, SP05 5, DA04 5, LP01 5, MD04 5, LQ04 5, RP01 5. Per context R01–R05 = 12 each. Total 60, all unique.

**Mapping status (mapping CSV):** MAPPED 20 {A01, FW05, DA04, LQ04}; MAPPED_WITH_SEMANTIC_CAVEAT 5 {A03}; MAPPED_ON_RECOMMENDED_WORKLOAD 15 {SQ01, SQ03, SP05}; INSUFFICIENT_EVENTS 15 {FW02, MD04, RP01}; OBSERVABILITY_GAP 5 {LP01}.

**Control status:** READY 2 (A01-R02, FW02-R01 — both `ControlBinarySHA=d3807fbe`); NEEDS_REDO 16 (ControlValid=TRUE but superseded binary/config); MISSING 42.

**Causal chain:** EvidenceType NATIVE_PARSE 55, PRIOR_QUOTE 5 (all FW05). ChainClass: MASKED 23, SDC 16, SQUASHED 7, CRASH 5, UNRESOLVED 4, HANG 3, ARCH_STATE 2.

**Census:** 18 JSONL files, 180 raw records = 175 distinct (tag,ordinal) probes (+ 5 duplicate SP05 rerun records); 15 timed-out; 177 retained per-K `command.txt`. The "18 files, 175 probes, 15 timeouts" claim reconciles exactly when counted by distinct probe.

**SampleRunID / Seed vs workbook sheet 5:** **all 60 match exactly** (60/60 workbook rows parsed to (Model,Context); zero mismatches, zero missing). Workbook EventOrdinal is still the old `1..5` for every model, confirming the report's claim that the measured percentile ordinals are not yet frozen. Workbook SHA `3b219ee060b51cb9f07567e7c60e57b431b366cd432aaf4c1e0ec8f35d03db1c` matches PROVENANCE.

---

## 3. Contradictions and defects

**C1 (major) — LQ04 evidence-binary misattribution.** In `LSU_60Context_ROI_Percentile_Mapping.csv`, all five LQ04 rows carry `EvidenceBinarySHA = d3807fbe…` (the final binary), but their `EvidencePath` is `pilots_v3_2_10/LQ04-R0x/lq04_injections.log`, and the report's Q9 states LQ04's evidence is on `f3c2a442`. The CSV therefore attributes historical pilot evidence to a binary on which LQ04 was never re-run. This is a provenance error that would mislead a researcher applying A2/A9.

**C2 — LQ04 distinctness generation.** `LSU_60Context_Distinctness_Audit.csv` lists `Generation = 1` for all five LQ04 rows; the cited `lq04_injections.log` shows `gen=1,2,3,4,5`. The build tool hardcodes `Generation=1` (`lsu_v331_build_mapping.py:184`). The CSV contradicts its own cited evidence.

**C3 — FW05 "different addresses" overclaim.** Report Q2: "Five seq … at the same load PC …, with different addresses and forwarding entry generations." Verified with a fresh probe: R01 addr = R05 addr = `0x4919c8`. Generations genuinely differ (sq gen 2296/4296/6296/8296/10296), and the dynamic instances differ by seq, so the contexts are distinct — but the "different addresses" wording is false for R01/R05.

**C4 — MD04 static-vs-measured inconsistency.** `LSU_12Model_Workload_Readiness.csv` records `ROIFeasible=YES … 256 alias pairs` and `EligibleEventSufficiency=YES` for MD04, while the measured census/report give `N_ROI=1` and `INSUFFICIENT_EVENTS`. The two deliverables were not reconciled; a reader of the 12-model CSV would believe MD04 has 256 eligible contexts.

**C5 — "FINAL binary" mislabel.** `LSU_12Model_Workload_Readiness.csv` GoldenStatus says `PASS on FINAL binary 68c6ce73`; the only binary on disk is `d3807fbe` (verified `sha256sum`), and `68c6ce73` is not on disk. Calling `68c6ce73` the "FINAL binary" contradicts PROVENANCE, the report Q9, and Agent E.

**C6 — A01 ROI lower-bound not retained.** ROUND_LOG claims an A01 coarse/boundary scan `K=100..1295, then 1030–1049 and 1230–1239`, but `census/A01_w1_r01/` retains only 9 K-dirs (K1059,1098,1137,1176,1177,1215,1216,1234,1235); no probe below K=1040 is retained. The report's "Probe commands are persisted in every …/K*/command.txt" is true only for retained probes. The upper bound is well-evidenced (K1234 in, K1235 libc); the lower bound rests on the single positive point K=1040 (`test_A01`).

**C7 — Q6 enumeration error.** `NO_CONSUMER_EDGE: 10` is the correct MissingEdges count, but the parenthetical list ("FW02 R01/R05, DA04 R01–R03, MD04 R01/R04, RP01 R02/R03") has only 9 entries; A01-R03 is omitted.

**C8 — Q9 "four complete verdicts".** Five FW05 rows are `PRIOR_QUOTE` (R01–R05). R02–R05 are four complete FAIL/SDC verdicts; R01 is UNRESOLVED. The phrase is reconcilable but ambiguous against Q6's "5 prior-quoted".

**C9 — build-tool overstatement.** `lsu_v331_build_mapping.py` docstring: "Every row is OBSERVED or explicitly NOT_MAPPED; no value is invented." In fact ROI boundaries, `ROI_N`, and the percentile ordinals are **hardcoded constants** in the `ROI` dict; the census JSONL is used only to fill `DynInstSeq`/`PC`/`Address`. The values are corroborated by retained probes, but they are transcribed, not computed. This weakens the "measured by census" framing for A2.

**Cross-deliverable numbering drift (minor).** The SQ comparison docs still describe the Agent-D preflight scheme "1..5 → 1009..1013 (SQ03) / 940..944 (SP05) / K*=1006 (SQ01)", whereas the mapping/approval table use the percentile ordinals 1018…1121 / 1021…1124 / 952…1055. The report's own numbers are self-consistent, but the SQ docs were not updated to the percentile scheme.

---

## 4. Residual blockers (unchanged by this audit, all correctly disclosed)

- Only **2/60** controls valid on `d3807fbe`; 58 control runs + 60 fault reruns needed.
- Measured ROI/percentile ordinals are **not frozen** in the workbook (sheet 5 still holds 1..5).
- SQ workload switch (`sq_reload_v3212`) is **unapproved**; all 15 SQ-status contexts depend on it.
- FW02/W4 has no data load; RP01/W7 has no partial-overlap; MD04/W7 has N_ROI=1; LP01 lacks PC/VA — each needs a workload or observation-hook change.
- Historical binaries (`68c6ce73`, `720eb780`, `8373e…`, `f3c2a442`, `0de25644`, `3e9148fc`, `8377c011`) are **not on disk**; historical pairs are non-reproducible, and FW05's five chains are prior quotes.
- **New from this audit:** LQ04 provenance must be corrected to `f3c2a442` before the mapping can be used for A2/A9; MD04's 12-model `Suff=YES` must be reconciled with `N_ROI=1`; the 12-model "FINAL binary 68c6ce73" label must be fixed.

---

## 5. Can any READY claim be defended?

- **`PARTIALLY_READY` / `12_MODEL_FORMAL_READY = NO`: YES, defensible** — and conservative. The measured evidence supports "partially mapped but not formal-ready."
- **Any per-model "READY" as *formal* readiness: NO.** The 12-model CSV's `READY` for FW05/DA04 is workload-level only; formal readiness is defeated by 2/60 controls, unfrozen ordinals, and (for FW05) prior-quoted chains.
- **The SQ "MAPPED_ON_RECOMMENDED_WORKLOAD" rows as approved: NO** — correctly labeled pending; not defensible as adopted.
- **LQ04's five "MAPPED (observed)" rows as current-binary observations: NO** until C1/C2 are corrected; they are historical `f3c2a442` evidence.

**Bottom line:** the package's *status* is honest, but several *evidence-attribution* claims (LQ04 binary provenance, LQ04 generation, MD04 static sufficiency, "FINAL binary" label, FW05 "different addresses") are contradicted by the package's own files. Fix C1–C5 before promoting any row beyond `PARTIALLY_READY`.
