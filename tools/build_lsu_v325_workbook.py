#!/usr/bin/env python3
"""Build the authoritative v3.2.5 LSU workbook from v3.2.4.

Changes are limited to LQ04 (the v3.2.10 pilot round):
  - sheet ``5.60个样本执行矩阵`` rows 12-16: workload identity
    (lq_lifetime_ordinal, new SHA/oracle per decision D3), the real pilot
    FullCommand (copied verbatim from each pilot's pilot_meta.json), pilot
    statuses, researcher acceptance and a v3.2.10 provenance appendix;
  - sheet ``3.最终12模型矩阵`` row 4: WorkloadName and status cells;
  - sheet ``4.源码Hook审计`` row 4: hook-audit status cells (the frozen fault
    definition fields are untouched);
  - LQ04 status alignment with the approved round (researcher decision
    2026-11-08 / pilots_v3_2_10): DecisionStatus is
    ACCEPTED_BY_RESEARCHER_2026-11-08 in sheets 3 and 4, and PreflightStatus
    is PILOT_ONLY_NOT_FORMAL in the five sheet-5 rows;
  - new sheet ``18.v3.2.10变更记录`` recording the changes and the audit
    verdicts;
  - ``MODEL_STATUS_MATRIX.csv`` LQ04 stage row (CRLF preserved).
Identities (60 SampleRunID/RunID/SubTaskID/Seed), the other 11 models,
ConfigFrozen=NO and WarmUp/ROI are unchanged (decision D6).
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2"
EXCEL = IMPL / "excel"
SRC = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx"
DST = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.5.xlsx"
SAMPLE_CSV = EXCEL / "60_SAMPLE_MATRIX.csv"
MATRIX_CSV = IMPL / "MODEL_STATUS_MATRIX.csv"
PILOTS = IMPL / "pilots_v3_2_10"
WORKLOAD = IMPL / "workloads/lq_lifetime_ordinal"
GOLDEN = IMPL / "workloads/lq_lifetime_ordinal.golden"

SAMPLE_SHEET = "5.60个样本执行矩阵"
MODEL_SHEET = "3.最终12模型矩阵"
HOOK_SHEET = "4.源码Hook审计"
REVISION_SHEET = "18.v3.2.10变更记录"

WORKLOAD_PATH = str(WORKLOAD)
WORKLOAD_SHA = "fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba"
ORACLE = "b097eb83f71545cb"

REQUIRED_FLAGS = ("--chaos_lq04", "--lq04_max_faults 1",
                  "--lq04_watchdog_cycles 500000000")

OLD_MATRIX_LINE = ("LQ04,LQ,lifetime,1,0,0,0,0,0,0,"
                   "v3.2.3 audit; HIGH-RISK")
NEW_MATRIX_LINE = ("LQ04,LQ,lifetime,1,1,1,1,1,1,0,"
                   "v3.2.10: literal fields cleared; boundary restore; "
                   "5/5 pilots MASKED; consumers correct data "
                   "(no corrupting propagation); no SDC")


def _header(ws):
    return {str(c.value).strip(): c.column for c in ws[1] if c.value}


def _rows_for(ws, cols, model, key="FaultModelID"):
    return [r for r in range(2, ws.max_row + 1)
            if str(ws.cell(r, cols[key]).value) == model]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _pilot(i: int) -> dict:
    with (PILOTS / f"LQ04-R0{i}" / "pilot_meta.json").open() as fh:
        return json.load(fh)


def _verify_inputs():
    if _sha256(WORKLOAD) != WORKLOAD_SHA:
        raise SystemExit(f"workload SHA mismatch: {WORKLOAD}")
    golden = GOLDEN.read_text()
    if ORACLE not in golden:
        raise SystemExit(f"oracle {ORACLE} not in {GOLDEN}")
    for i in range(1, 6):
        meta = _pilot(i)
        ident = meta["excel_identity"]
        if ident["sample_run_id"] != f"LQ04-F0-W2-S01-R0{i}":
            raise SystemExit(f"pilot {i}: unexpected sample_run_id")
        if ident["event_ordinal"] != i or ident["event_ordinal_used"] != i:
            raise SystemExit(f"pilot {i}: ordinal mismatch")
        if meta["workload"] != WORKLOAD_PATH:
            raise SystemExit(f"pilot {i}: workload path mismatch")
        cmd = meta["command"]
        if f"--lq04_event_ordinal" not in cmd or str(i) not in cmd:
            raise SystemExit(f"pilot {i}: ordinal flag missing")
        joined = " ".join(cmd)
        for flag in REQUIRED_FLAGS:
            if flag not in joined:
                raise SystemExit(f"pilot {i}: flag {flag} missing")
        cls = meta["classification"]
        if cls["terminal_state"] != "MASKED":
            raise SystemExit(f"pilot {i}: terminal {cls['terminal_state']}")
        if cls["fault_activation_status"] != "TRIGGERED":
            raise SystemExit(f"pilot {i}: not triggered")
        if cls["trace_completeness"] != "COMPLETE":
            raise SystemExit(f"pilot {i}: trace incomplete")
        if not meta["oracle_pass"]:
            raise SystemExit(f"pilot {i}: oracle failed")


def main():
    _verify_inputs()

    wb = openpyxl.load_workbook(SRC)

    # --- sheet 5: LQ04 sample rows -------------------------------------
    ws = wb[SAMPLE_SHEET]
    cols = _header(ws)
    rows = _rows_for(ws, cols, "LQ04")
    if len(rows) != 5:
        raise SystemExit(f"expected 5 LQ04 rows, got {len(rows)}")
    for i, r in enumerate(rows, start=1):
        if int(ws.cell(r, cols["EventOrdinal"]).value) != i:
            raise SystemExit(f"row {r}: unexpected EventOrdinal")
        meta = _pilot(i)
        ws.cell(r, cols["WorkloadPath"]).value = WORKLOAD_PATH
        # BinaryPath follows the new workload so the row stays consistent
        # with BinarySHA256 (the old lq_lifetime binary has a different SHA).
        ws.cell(r, cols["BinaryPath"]).value = WORKLOAD_PATH
        ws.cell(r, cols["BinarySHA256"]).value = WORKLOAD_SHA
        ws.cell(r, cols["Oracle"]).value = ORACLE
        ws.cell(r, cols["FullCommand"]).value = " ".join(meta["command"])
        ws.cell(r, cols["ExecutionStatus"]).value = "PILOT_RUN"
        ws.cell(r, cols["RunStatus"]).value = "PILOT_MASKED"
        ws.cell(r, cols["FaultActivationStatus"]).value = "TRIGGERED"
        ws.cell(r, cols["TerminalState_v31"]).value = "MASKED"
        ws.cell(r, cols["TraceCompleteness_v31"]).value = "COMPLETE"
        ws.cell(r, cols["DecisionStatus"]).value = \
            "ACCEPTED_BY_RESEARCHER_2026-11-08"
        ws.cell(r, cols["PreflightStatus"]).value = "PILOT_ONLY_NOT_FORMAL"
        prov = str(ws.cell(r, cols["v3.2_ConfigProvenance"]).value or "")
        ws.cell(r, cols["v3.2_ConfigProvenance"]).value = (
            prov.rstrip()
            + "; v3.2.10 LQ04 pilot round (accepted by researcher 2026-11-08):"
            + " literal definition executed per LQ04_Definition_Freeze_v3.2.10.md"
            + " D1-D6 - literal _valid/_request cleared at executeLoad_post"
            + " (no pop, no reuse) with boundary restore at commit/squash;"
            + " ordinal anchors 1-5 via workload lq_lifetime_ordinal and"
            + " --lq04_event_ordinal (D3/D4, supersedes the seeded-tier note"
            + " above for LQ04); propagation grading per"
            + " LQ04_Propagation_Audit_v3.2.10.md: MASKED 5/5,"
            + " TraceCompleteness COMPLETE, PropagationCoverage LIFECYCLE_ONLY,"
            + " PROPAGATION_VERIFIED=0, no SDC; response binds via"
            + " pkt->senderState (no response loss); see pilots_v3_2_10;")

    # ConfigFrozen must remain NO everywhere.
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, cols["SampleRunID"]).value:
            ws.cell(r, cols["ConfigFrozen"]).value = "NO"

    # --- sheet 3: model matrix row --------------------------------------
    ws3 = wb[MODEL_SHEET]
    c3 = _header(ws3)
    rows3 = _rows_for(ws3, c3, "LQ04", key="ModelID")
    if len(rows3) != 1:
        raise SystemExit(f"expected 1 LQ04 model row, got {len(rows3)}")
    r3 = rows3[0]
    ws3.cell(r3, c3["WorkloadName"]).value = "lq_lifetime_ordinal"
    ws3.cell(r3, c3["WorkloadStatus"]).value = "READY"
    ws3.cell(r3, c3["ImplementationStatus"]).value = (
        "PILOT_IMPLEMENTED_VERIFIED_F0 (literal _valid/_request clear; "
        "boundary restore; MASKED 5/5)")
    ws3.cell(r3, c3["OverallStatus"]).value = "PILOT_RUN_MASKED_5/5"
    ws3.cell(r3, c3["DecisionStatus"]).value = \
        "ACCEPTED_BY_RESEARCHER_2026-11-08"
    ws3.cell(r3, c3["Notes"]).value = (
        "literal semantics accepted by the researcher 2026-11-08; "
        "response binds via pkt->senderState, no response loss; "
        "expected MASKED confirmed 5/5; ordinal anchors 1-5 "
        "(lq_lifetime_ordinal); PROPAGATION_VERIFIED=0 (LIFECYCLE_ONLY, "
        "no SDC)")

    # --- sheet 4: hook-audit row (fault definition untouched) -----------
    ws4 = wb[HOOK_SHEET]
    c4 = _header(ws4)
    rows4 = _rows_for(ws4, c4, "LQ04", key="ModelID")
    if len(rows4) != 1:
        raise SystemExit(f"expected 1 LQ04 hook row, got {len(rows4)}")
    r4 = rows4[0]
    ws4.cell(r4, c4["ExistingHook"]).value = "CHAOSLQ04"
    ws4.cell(r4, c4["RequiredSourceChange"]).value = (
        "implemented: CHAOSLQ04 SimObject + LQEntry side channel + "
        "executeLoad hook")
    ws4.cell(r4, c4["ImplementationStatus"]).value = "IMPLEMENTED_VERIFIED"
    ws4.cell(r4, c4["DecisionStatus"]).value = \
        "ACCEPTED_BY_RESEARCHER_2026-11-08"
    ev = str(ws4.cell(r4, c4["Evidence"]).value or "")
    ws4.cell(r4, c4["Evidence"]).value = (
        ev.rstrip()
        + "; CHAOS/gem5/src/cpu/o3/CHAOSLQ04/; lsq_unit.hh side channel; "
        + "pilots_v3_2_10")

    # --- revision sheet --------------------------------------------------
    rev = wb.create_sheet(REVISION_SHEET)
    rev["A1"] = ("v3.2.10 revision record (2026-11-09; LQ04 literal "
                 "semantics accepted by the researcher 2026-11-08)")
    rev["A1"].font = Font(bold=True, size=12)
    rev.append([])
    rev.append(["Item", "Change", "Reason"])
    for row in [
        ("LQ04 workload identity",
         "workloads/lq_lifetime -> workloads/lq_lifetime_ordinal "
         "(v3.2.10 worktree); BinarySHA256 "
         f"{WORKLOAD_SHA}; Oracle {ORACLE}",
         "Decision D3: explicit-anchor workload whose first five eligible "
         "Loads are five distinct anchors (PC/address/data/destination/"
         "consumer); the original lq_lifetime remains archived (sheet 6 W2 "
         "row unchanged)."),
        ("LQ04 BinaryPath",
         "aligned with the new workload path lq_lifetime_ordinal",
         "BinarySHA256 now describes lq_lifetime_ordinal; a stale path "
         "pointing at lq_lifetime would contradict the recorded SHA."),
        ("LQ04 FullCommand",
         "'BLOCKED: no executable hook yet' -> the real v3.2.10 pilot "
         "command (--chaos_lq04 --lq04_event_ordinal N --lq04_max_faults 1 "
         "--lq04_watchdog_cycles 500000000)",
         "Command copied verbatim from each pilot's pilot_meta.json "
         "(LQ04-R01..R05); outdir is the pilot directory."),
        ("LQ04 sample status (sheet 5 rows 12-16)",
         "ExecutionStatus PILOT_RUN; RunStatus PILOT_MASKED; "
         "FaultActivationStatus TRIGGERED; TerminalState_v31 MASKED; "
         "TraceCompleteness_v31 COMPLETE; DecisionStatus "
         "ACCEPTED_BY_RESEARCHER_2026-11-08",
         "Five fault pilots LQ04-R01..R05 plus five matched no-fault "
         "controls LQ04-CONTROL-R01..R05; oracle PASS and gem5 exit 0 in "
         "all ten runs."),
        ("Sheet 3 LQ04 row",
         "WorkloadName lq_lifetime_ordinal; ImplementationStatus "
         "PILOT_IMPLEMENTED_VERIFIED_F0 (literal _valid/_request clear; "
         "boundary restore; MASKED 5/5); OverallStatus PILOT_RUN_MASKED_5/5; "
         "Notes record the researcher acceptance",
         "v3.2.10 implementation and pilots; literal semantics accepted by "
         "the researcher 2026-11-08."),
        ("Sheet 4 LQ04 row",
         "ExistingHook CHAOSLQ04; RequiredSourceChange implemented; "
         "ImplementationStatus IMPLEMENTED_VERIFIED; Evidence extended with "
         "CHAOS/gem5/src/cpu/o3/CHAOSLQ04/, the lsq_unit.hh side channel "
         "and pilots_v3_2_10",
         "Frozen fault definition fields (TargetField, NormalValue, "
         "FaultValue, InjectionTiming, Duration) unchanged."),
        ("LQ04 status alignment (sheets 3/4/5)",
         "DecisionStatus: NEEDS_USER_DECISION -> "
         "ACCEPTED_BY_RESEARCHER_2026-11-08 in sheet 3 row 4 and sheet 4 "
         "row 4 (LQ04 only); PreflightStatus: BLOCKED_NO_HOOK -> "
         "PILOT_ONLY_NOT_FORMAL in sheet 5 rows 12-16 (LQ04 only)",
         "Researcher decision 2026-11-08 / pilots_v3_2_10: the five LQ04 "
         "pilots were approved and the round is pilot-only, not the formal "
         "60-sample campaign; fault definition, identities and the other 11 "
         "models are unchanged."),
        ("MODEL_STATUS_MATRIX.csv",
         "LQ04 stages DESIGNED/SOURCE_AUDITED/IMPLEMENTED/COMPILED/"
         "UNIT_TESTED/PILOT_RUN=1, PROPAGATION_VERIFIED=0",
         "Evidence: v3.2.10: literal fields cleared; boundary restore; "
         "5/5 pilots MASKED; consumers correct data (no corrupting "
         "propagation); no SDC."),
        ("Audit verdicts (LQ04-R01..R05)",
         "RecordIntegrity VALID; TraceCompleteness COMPLETE; "
         "PropagationCoverage LIFECYCLE_ONLY; PROPAGATION_VERIFIED=0; "
         "SDC no; terminal MASKED (all five)",
         "Controller ruling per LQ04_Propagation_Audit_v3.2.10.md section 0: "
         "the consumer edges exist but carry the correct payload "
         "(data_corruption=0, consumer_input_matches_source=1), so the "
         "fault effect stays inside the entry lifecycle; no SDC claim."),
        ("Matched controls",
         "LQ04-CONTROL-R01..R05: 0 injections, NOT_TRIGGERED, oracle PASS, "
         "checksum identical to the fault runs",
         "Matched no-fault baseline; the fault runs' identical checksum is "
         "not attributable to run-to-run variance."),
        ("Identity freeze (D6)",
         "60 SampleRunID/RunID/SubTaskID/Seed unchanged; ConfigFrozen NO "
         "for all 60; WarmUp/ROI NEEDS_RESEARCHER_CONFIRMATION",
         "Decision D6; global Warm-up/ROI still need researcher "
         "confirmation."),
        ("Unchanged scope",
         "Other 11 models byte-equivalent in content (sheets 3/4/5); sheet 6 "
         "W2 keeps the archived lq_lifetime record; OutputDir and gem5Commit "
         "cells untouched (LQ04 PreflightStatus is covered by the status "
         "alignment row above)",
         "Formal preflight / Gate 4 has not run; the pilots are not the "
         "formal 60-sample campaign."),
    ]:
        rev.append(list(row))
    for row in rev.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for col, width in (("A", 34), ("B", 64), ("C", 88)):
        rev.column_dimensions[col].width = width

    wb.save(DST)

    # --- derived sample CSV (round-trip of sheet 5) ----------------------
    with SAMPLE_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row,
                                values_only=True):
            writer.writerow(["" if v is None else v for v in row])

    # --- model status matrix (preserve CRLF) -----------------------------
    raw = MATRIX_CSV.read_bytes().decode("utf-8")
    lines = raw.splitlines(keepends=True)
    hits = [k for k, line in enumerate(lines) if line.rstrip("\r\n") ==
            OLD_MATRIX_LINE]
    if len(hits) == 0:
        # Idempotent rerun: the v3.2.10 update may already be applied.
        done = [k for k, line in enumerate(lines) if line.rstrip("\r\n") ==
                NEW_MATRIX_LINE]
        if len(done) != 1:
            raise SystemExit(f"expected exactly 1 old or new LQ04 matrix "
                             f"line, got old={len(hits)} new={len(done)}")
    elif len(hits) != 1:
        raise SystemExit(f"expected exactly 1 old LQ04 matrix line, "
                         f"got {len(hits)}")
    else:
        ending = "\r\n" if lines[hits[0]].endswith("\r\n") else "\n"
        lines[hits[0]] = NEW_MATRIX_LINE + ending
        MATRIX_CSV.write_bytes("".join(lines).encode("utf-8"))

    print(f"wrote {DST}")
    print(f"wrote {SAMPLE_CSV}")
    print(f"updated {MATRIX_CSV}")


if __name__ == "__main__":
    main()
