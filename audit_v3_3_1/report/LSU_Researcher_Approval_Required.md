# LSU v3.3.1 — Researcher Approval Required

Date: 2026-11-11. No item below has been applied to the frozen design.

| # | Decision | Recommendation | Evidence | Effect if approved |
|---|---|---|---|---|
| A1 | **SQ01/SQ03/SP05 workload** | Adopt `sq_reload_v3212` for all three | `sq_workload/*.md`, preflight K*=1006/1009/940 | Changes WorkloadPath, ELF SHA `bcab9cc5…`, golden `7df5034c23f3e703`, ordinals 1018/1044/1069/1095/1121 (SQ01), 1021/1047/1072/1098/1124 (SQ03), 952/978/1003/1029/1055 (SP05) |
| A2 | **ROI boundaries / percentile ordinals** | Freeze the measured values in `LSU_60Context_ROI_Percentile_Mapping.csv` | census JSONL + tool output | Replaces EventOrdinal 1–5 for A01/A03/FW05/DA04/LQ04 and the SQ rows |
| A3 | **Warm-up / ROI fields** | Set the workbook `WarmUp`/`ROI` to the measured ROI definitions | Q3 of the report | Removes 60/60 `NEEDS_RESEARCHER_CONFIRMATION` |
| A4 | **FW02 / W4 workload** | Choose `sq_forward_v33` (proposal) or a new W4 with real store→load pairs, then re-freeze the golden | Agent B; `sq_forward_v33` exists at commit `c1846ae4` | Changes W4 ELF/golden/SHA and the FW02 context mapping |
| A5 | **RP01 / W7 workload** | Redesign W7 to contain a genuine partial-overlap store→younger-load | Agent B: W7 has only full 8B alias | Enables 5 RP01 contexts; current N_ROI=0 |
| A6 | **MD04 / W7 workload** | Redesign or extend W7 so ≥5 in-loop violation reports are eligible | census: only ordinal 3 in `main` | Current N_ROI=1 cannot form 5 percentiles |
| A7 | **LP01 observation hook** | Approve an observation-only change that records VA/PC in the L1DForward injection record | census: only a physical address is exposed | Requires a rebuild and a new binary SHA; no fault semantics change |
| A8 | **A03 percentile semantics** | Accept the measured outcome (R01/R03/R04 `ALREADY_STUCK`, affected=0 at activation) or define a tie-break rule | `A03_STREAM` census rows | Determines whether 3/5 A03 contexts are usable as-is |
| A9 | **Control rerun** | Approve 58 control runs and 60 fault reruns on one binary/config | `LSU_60Context_Control_Readiness.csv` | Only 2/60 controls currently valid on `d3807fbe` |
| A10 | **Config freeze** | Approve the corrected `gem5Commit`, worktree paths, and binary SHA after A1–A9 | Agent E freeze checklist | `ConfigFrozen=YES` can be set |

## What is explicitly NOT requested

- No change to SampleRunIDs or authoritative seeds.
- No change to fault-model semantics.
- No formal campaign launch.
- No regrade or overwrite of historical pilots.

## Minimum approval needed to proceed

**A1 + A2 + A3 + A9** unblock the 25 formal-workload contexts (A01, A03,
FW05, DA04, LQ04) for a one-binary 5-context pilot plus matched controls.
**A4 + A5 + A6 + A7** are required before FW02, RP01, MD04 and LP01 can join.
**A8** is a semantics acceptance, not a hijack: the percentile rule is applied
exactly as approved; the result is that some A03 activations are no-ops.
