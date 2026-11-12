# LSU v3.3.3 — Formal Campaign Launch Package

**Date:** 2026-11-12
**Verdict:** `READY_TO_LAUNCH_FORMAL_CAMPAIGN = YES` (independent audit PASS, Agent F final)
**Source HEAD:** `b5031bf7` · **Results HEAD:** `b8405580`
**Binary SHA256:** `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`
**Config SHA256:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`

## Required deliverables
1. LSU_Launch_Preflight_Report.md
2. LSU_Formal_Experiment_Config_Final.xlsx
3. LSU_120Run_Campaign_Manifest.csv
4. LSU_60Fault_60Control_Pair_Map.csv
5. LSU_60Context_Causal_Propagation_Final.csv
6. LSU_Control_Zero_Injection_Proof.csv
7. LSU_Binary_Provenance.md
8. LSU_Runner_Dryrun_Report.md
9. LSU_Resource_Preflight.md
10. LSU_Final_Blockers.md
11. LSU_Independent_Launch_Acceptance.md
12. Source diff / runner diff / build & test logs / preflight reports

## Launch (not executed)
```
python3 tools/lsu_v332_matrix.py --models all --roles fault,control \
  --contexts 1,2,3,4,5 --out-base runs/lsu/formal_v333 \
  --out-csv runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv
python3 tools/lsu_v333_launch.py --runs runs/lsu/formal_v333 \
  --out runs/lsu/formal_v333/manifests --manifest-only
```
120 runs (60 fault + 60 control); serial; 30–40 min realistic; 51 GiB free.
