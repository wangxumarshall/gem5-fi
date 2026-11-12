# LSU v3.3.3 — Stale Status Reconciliation

**Date:** 2026-11-12
**Scope:** metadata/report consistency only. No historical raw trace, `summary.json`,
oracle log, or run manifest was modified. No `QUALIFIED` state was upgraded.

## 1. Authoritative causal propagation file

`LSU_60Context_Causal_Propagation_Final.csv` is fixed to the 16-column, 60-row
file generated for v3.3.3:

| Item | Value |
|---|---|
| Authoritative source | `audit_v3_3_3/LSU_60Context_Causal_Propagation.csv` |
| SHA256 | `4e53b424fb9f62ed86e160f958499903005a3baabe4b58124a96ee3a27371e1b` |
| Columns / rows | 16 / 60 |
| Launch copy | `audit_launch_fix_v333/artifacts/LSU_60Context_Causal_Propagation_Final.csv` (same SHA) |

Archived versions are listed in
`audit_launch_fix_v333/artifacts/LSU_ARCHIVED_Propagation_Versions.csv` with
their SHA256 and `Status=ARCHIVED`:

- `audit_v3_3_3/propagation/LSU_60Context_Causal_Propagation_Final.csv`
  (older copy, SHA256 `c824f36f…`)
- `audit_v3_3_2/propagation/…` and `audit_v3_3_2/pkg/propagation/…`
  (identical v3.3.2 copies, SHA256 `b98eeed3…`)
- `audit_launch_v333/artifacts/…` (pre-round launch copy, same bytes as the
  authoritative source)

## 2. A01 — no longer open/UNRESOLVED

The v3.3.2 ground-truth README records “B2: A01-R03 has no register-writeback
divergence evidence → UNRESOLVED”. That statement is superseded. The
authoritative causal CSV now carries for all five A01 contexts:

```
A01 R01..R05: Terminal=SDC, TraceCompleteness=COMPLETE,
TerminalReason=ORACLE_FAIL;committed_data_value_diverged
```

Source: the A01 8-byte-load correction `b5031bf7` (ROI 585–713, N=129;
ordinals 597/623/649/675/701). `README_GROUND_TRUTH.md` is a historical v3.3.2
record and is left byte-identical; this report supersedes B2 for launch
purposes.

## 3. RP01 — `NO_CHECKSUM` is correct, not an oracle FAIL

All five RP01 contexts carry:

```
Terminal=HANG_WATCHDOG, TraceCompleteness=PARTIAL_WATCHDOG,
TerminalReason=RP01_WATCHDOG_EXPIRED;target_ordinal=…;injected=1;checksum=None
```

`NO_CHECKSUM` is the honest label for a model-internal watchdog hang; it is
not an application oracle FAIL and must not be rewritten as `PASS` or as a
complete propagation chain. The old launch collector mapped this to a
PRE_FORMAL oracle result; the new collector reports it in
`TerminalState`/`OracleResult` and `QualifiedStatus=TRACE_INCOMPLETE`.

## 4. Other stale auxiliary status files

| File | Stale content | Current authoritative content |
|---|---|---|
| `audit_v3_3_3/LSU_60Context_Final_Readiness_Matrix.csv` | 30 × `CANDIDATE_PENDING_APPROVAL` | `audit_launch_v333/artifacts/LSU_60Context_Final_Readiness.csv`: 30 × `FORMAL` + 30 × `OVERRIDE_APPROVED`, `Approval=2026-11-12`, `ReadyGate=READY` (60/60) |
| `audit_v3_3_3/controls/LSU_Fault_Control_Pair_FINAL.csv` | `WorkloadStatus`: 30 × `CANDIDATE_PENDING_APPROVAL` | same 60/60 `OVERRIDE_APPROVED` decision recorded in `LSU_v3.3.3_Ledger_Reconciliation.md` §Workload/identity |

The historical files are not overwritten (they document the pre-approval
state); they are marked as superseded here. The researcher decision packet
already records the approval, and the frozen SampleRunID/Seed are unchanged.

## 5. v3.3.2 blockers B1–B6 — current truth

| Blocker (v3.3.2) | Current status | Evidence |
|---|---|---|
| B1: 30 candidate contexts pending approval | **Resolved** | 30 `OVERRIDE_APPROVED` in `audit_launch_v333/artifacts/LSU_60Context_Final_Readiness.csv`; IDs/seeds unchanged |
| B2: A01-R03 `UNRESOLVED` | **Refuted** | A01 R01–R05 all `SDC`/`COMPLETE` in the authoritative CSV |
| B3: A03 uses an external 30 s timeout, no in-simulator watchdog | **Refuted** | `audit_v3_3_3/runs/A03-R01-fault/summary.json`: `terminal=SDC`, `watchdog_expired=true` (source fix `7a33dc5f`) |
| B4: SP05 `store_data_fnv=null`, no early anomaly | **Partially resolved** | `store_data_fnv` present in SP05 `summary.json` and `trace_v31.jsonl`; qualified evidence still lacks `commit_event`/`writeback_event` → `QUALIFIED` (not upgraded) |
| B5: SQ03 must be MASKED / visibility shift | **Confirmed (carried)** | SQ03 rows remain MASKED/visibility in the authoritative CSV |
| B6: `ConfigFrozen=NO`, ROI/warm-up/binary approval pending | **Resolved** | binary `1126e0fd…`, config `8309da72…`, frozen matrix `60_SAMPLE_MATRIX.csv`; identity read-only |

## 6. Non-modification statement

No file under `audit_v3_3_3/runs/`, `audit_v3_3_3/propagation/`, or any raw
`trace_v31.jsonl` / `summary.json` / `oracle.log` was rewritten by this round.
