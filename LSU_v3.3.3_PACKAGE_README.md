# LSU v3.3.3 — Formal Experiment Ready Package

**Date:** 2026-11-12
**Package:** `LSU_v3.3.3_Formal_Experiment_Ready_Package.zip`
**SHA256:** `168a13300c5ec85b8e125a9ca6f4ef126fb81088a948ca6a4d962c97a2a8cf23`
**Size:** 195 MB compressed / 1,812 files / 3.37 GB uncompressed
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`
**Final source HEAD:** `b5031bf7d857ca7901810a3bf3629f5649ddaaac`
**Final binary:** `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`
**Final config:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
**Verdict:** `READY_FOR_FORMAL_EXPERIMENT` (independent audit PASS — Agent F3, 2026-11-12)

## Required deliverables (14)

| # | Item | Path in package |
|---|---|---|
| 1 | Final Acceptance Report | `LSU_v3.3.3_Final_Acceptance_Report.md` |
| 2 | Master Defect Ledger | `LSU_v3.3.3_Master_Defect_Ledger.csv` |
| 3 | Consolidated Repair Plan | `LSU_v3.3.3_Consolidated_Repair_Plan.md` |
| 4 | Researcher Decision Packet | `LSU_v3.3.3_Researcher_Decision_Packet.md` + `decisions/` |
| 5 | Formal Experiment Design workbook | `gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx` |
| 6 | 60-Context Readiness | `LSU_60Context_Final_Readiness.csv` |
| 7 | Causal Propagation | `LSU_60Context_Causal_Propagation.csv` |
| 8 | Fault-Control Audit | `LSU_Fault_Control_Final_Audit.csv` |
| 9 | Workload/Oracle Audit | `LSU_12Model_Workload_Oracle_Audit.csv` |
| 10 | Binary Provenance | `LSU_Final_Binary_Provenance.md` |
| 11 | Source Diff | `LSU_Final_Source_Diff.patch` |
| 12 | Independent Acceptance | `LSU_Independent_Acceptance.md` |
| 13 | Raw runs, traces, logs, oracles, tests | `runs/` (120 dirs), `reports/`, `roi/`, `controls/`, `propagation/`, `census/`, `gate_tests_final/`, `build/` logs |
| 14 | Commands / runner config | `build/RUNBOOK.md`, per-run `command.txt`, `config.ini`, `config.json` |

Also included: `LSU_v3.3.3_Ledger_Reconciliation.md`, the six Phase-1 agent reports, the final
Agent F3 report, and the A01 8-byte census evidence.

## Not in the zip (retained locally, cited by SHA)

- The 1.1 GB final binary `audit_v3_3_3/binary/gem5.opt.v333-1126e0fd` (SHA in `binary/SHA256.txt` and the provenance).
- The pre-correction `685d88f7` runs (`audit_v3_3_3/runs_685d88f7/`), archived and never mixed with the final set.

## Verification

`unzip -t` reports `No errors detected`; 12 required items + raw evidence present; the final
workbook has 8 sheets and 60 authoritative SampleRunID/Seed rows; regression 232 + 121 passed;
runner dry-run 120 commands. See `LSU_v3.3.3_Final_Acceptance_Report.md` and
`LSU_Independent_Acceptance.md` for the evidence tables.
