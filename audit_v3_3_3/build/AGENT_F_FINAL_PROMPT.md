# Agent F — Final Independent Acceptance Brief (v3.3.3)

You are the **fresh, independent final auditor** for LSU v3.3.3. You did not
write any of the artifacts. Work read-only in
`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`.

**Do not edit any file except your report**
`audit_v3_3_3/reports/Agent_F_Final_Independent_Acceptance.md`.
**Do not run gem5, scons, or any pilot.** Python read-only analysis, `sha256sum`,
`git`, `unzip -t`, openpyxl read-only are allowed.

## Inputs to read first

- `audit_v3_3_3/README_GROUND_TRUTH.md`
- `audit_v3_3_3/LSU_v3.3.3_Master_Defect_Ledger.csv`
- `audit_v3_3_3/LSU_v3.3.3_Consolidated_Repair_Plan.md`
- `audit_v3_3_3/LSU_v3.3.3_Researcher_Decision_Packet.md` + `decisions/`
- `audit_v3_3_3/build/PROVENANCE.md` + `RUNBOOK.md` + build logs
- `audit_v3_3_3/LSU_v3.3.3_Final_Acceptance_Report.md` (the main agent's claim)
- The authoritative `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv` and v3.2.7 workbook

## What to verify independently (recompute; do not trust the claim)

1. **Binary/provenance:** final `build/ARM/gem5.opt` SHA256 equals
   `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`;
   `git diff --stat <final-source-HEAD> -- CHAOS/gem5/src` is empty;
   build logs have 0 `error:`; no new warning class.
2. **Run set:** 120 run dirs; 60 fault + 60 control; every `summary.json`
   carries the final SHA; every fault `injection_count>0`; every control
   `injection_count==0` and a real zero-proof artifact.
3. **ROI arithmetic:** all 60 rows: `ROI_N=end-start+1`, absolute ordinal =
   `start + ceil(p*N) − 1`, percentiles 0.1/0.3/0.5/0.7/0.9; A01 uses the
   approved 8-byte-only window `585–713 (N=129)`; A03 uses `1040–1222 (N=183)`.
4. **Context distinctness:** 60 identities distinct within each model; state the
   cross-model SQ01/SQ03 shared-workload fact explicitly.
5. **Causal chain:** every row has injection, activation/first divergence,
   downstream/consumer (or terminal-type witness), commit/squash/replay/hang,
   oracle/terminal; MASKED has a mechanism; SQUASHED proves no architectural
   entry; HANG has the internal watchdog/deadline; SDC has an independent
   oracle FAIL. `COMPLETE` must not be structural only.
6. **Terminal honesty:** A03 = SDC/POST_ORACLE_SIM_HANG with the final checksum;
   A01-R02 = SQUASHED/UNRELATED_SQUASH_NO_ARCH_ENTRY; SQ03 = MASKED/
   VISIBILITY_TIMING_SHIFT (4/5 + 1/5); SP05 has `store_data_fnv` non-null;
   RP01 = HANG_WATCHDOG; no `UNRESOLVED`/`TRACE_INCOMPLETE` masquerading.
7. **Fault-control pairing:** same seed, ELF SHA, binary SHA, config, ROI,
   ordinal; classify 35 `MOUNTED_BUT_DISABLED` / 25 `INJECTOR_ABSENT` /
   0 `SUPPRESSED`; optionally re-run the MD04/DA04 mounted-at-p=0 gate test
   evidence under `audit_v3_3_3/gate_tests/`.
8. **Identity/Excel:** 60/60 authoritative SampleRunID/Seed preserved; 30
   candidate contexts carry `OVERRIDE_APPROVED`; Design vs Executed
   EventOrdinal separated; workbook has all 8 sheets; no blank critical field
   marked PASS; numbers match the CSVs.
9. **Regression:** read the captured pytest output (232 + 121 expected);
   confirm the two updated tests (RP01 in MODELS, A01 discard =
   INJECTION_NOT_ACTIVATED) are justified.
10. **Package:** `unzip -t` clean; SHA sidecar matches; all 14 required items
    present; no mixed-binary traces; `audit_v3_3_2/` untouched.

## Output

A PASS/FAIL table per Ready-Gate item, the exact command/output for each,
a findings list with severity and evidence paths, and a final verdict:
`READY_FOR_FORMAL_EXPERIMENT` / `PARTIALLY_READY` / `NOT_READY`.
Do not rubber-stamp. If you find a contradiction, report it with the raw path
and line.
