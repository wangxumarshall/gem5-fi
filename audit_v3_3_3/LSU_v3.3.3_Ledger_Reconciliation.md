# LSU v3.3.3 — Master Defect Ledger Reconciliation

**Date:** 2026-11-12
**Ledger:** `LSU_v3.3.3_Master_Defect_Ledger.csv` (47 issues: 12 A, 9 B, 10 C, 16 D)
**Final status:** 0 blocking OPEN; 11 VERIFIED, 32 CLOSED, 3 OPEN_NONBLOCKING, 1 SUPERSEDED.

## Status counts

| Status | Count | Meaning |
|---|---:|---|
| VERIFIED_V333 | 11 | Source/behavior fix verified on the final binary with raw evidence |
| CLOSED_V333 | 32 | Artifact/tooling/documentation fix completed and reflected in the final tables/workbook |
| OPEN_NONBLOCKING | 3 | Tooling nicety not required by any Ready-Gate item; documented below |
| SUPERSEDED_BY_L-A12 | 1 | L-A08's old A01-R02 SQUASHED label is replaced by the approved 8-byte scope; final R02 is a genuine SDC |

## The three non-blocking OPEN items

1. **L-A11 — `summary.json` exposes one `exit_code`**, not separate gem5/wrapper codes. The final summaries carry `exit_code` (A01-R03 final is 0; A03 fault is 1 via the watchdog `exitSimLoop`). No Ready-Gate item depends on the split; the raw gem5 exit is recorded where relevant.
2. **L-D11 — `manifest_validate.py` remains selftest-only.** The final manifests are validated by the matrix/report/workbook checks; no gate depends on the selftest validator.
3. **L-D15 — `summary.injection_events` remains null.** `injection_count` is populated and used in every table; the null extra field is not referenced by any gate.

## Closed/verified highlights

- **Source fixes:** L-A01 PRE retry, L-A02/A03/A04 A03 watchdog+terminal+count, L-A05 SP05 store data, L-A06 control gates, L-A12 A01 8-byte scope/census.
- **Workload/identity:** L-B01…L-B09; 30 candidate contexts `OVERRIDE_APPROVED`; SampleRunID/Seed unchanged.
- **Propagation/oracle:** L-C01…L-C10; 60 causal rows; A03 `COMPLETE_PROP_TRACE`; RP01 `PARTIAL_WATCHDOG` accepted for HANG.
- **Excel/runner:** L-D01…L-D17 (except the two non-blocking tool fields); 35/25 control classification; ConfigFrozen=YES with config SHA `8309da72…`; final binary `1126e0fd…`.
- **L-A08** is superseded: the final A01-R02 at ordinal 623 is SDC with register-writeback, commit and consumers; the old SQUASHED label described the pre-correction workload.

Every status line cites the artifact used in the main acceptance report; nothing was relabelled to make a gate pass.
