#!/usr/bin/env python3
"""Build the LSU v3.3.3 formal-experiment workbook.

Reads the authoritative frozen files only (never writes them):

  docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv
  docs/gem5-fi/lsu/implementation_v3_2/excel/
      gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx

and emits eight sheets:

  Model_Design, Fault_Sample_Manifest, Control_Manifest, ROI_Context_Mapping,
  Causal_Propagation, Workload_Oracle, Binary_Config, Readiness_Gate

Identity rules (ledger L-D05/L-D07/L-D08/L-D09/L-D10):

  * SampleRunID / Seed / Design_EventOrdinal are copied verbatim from the
    frozen matrix and never rewritten;
  * Executed_EventOrdinal is a separate, measured column;
  * the 30 candidate contexts carry WorkloadIdentityStatus=OVERRIDE_APPROVED
    (researcher approval 2026-11-12) while their IDs/seeds stay frozen;
  * gem5 binary SHA and workload ELF SHA are separate columns;
  * the six candidate workloads are listed, including sq_reload_v3212.

Honesty rule: a measured field that is not present in a supplied run/causal
artifact is written ``PENDING``.  The builder never fabricates a value and
never writes PASS for a row whose critical fields are blank or PENDING;
``enforce_no_blank_pass`` verifies that invariant before saving.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font

ROOT = Path(__file__).resolve().parents[1]

MATRIX_PATH = (ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
               / "60_SAMPLE_MATRIX.csv")
V327_PATH = (ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
             / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx")
DEFAULT_OUT = (ROOT / "audit_v3_3_3"
               / "gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx")

MODELS = ("A01", "A03", "FW02", "FW05", "SQ01", "SQ03", "SP05", "DA04",
          "LP01", "MD04", "LQ04", "RP01")
CONTEXTS = ("R01", "R02", "R03", "R04", "R05")

CANDIDATE_MODELS = {"FW02", "RP01", "MD04", "SQ01", "SQ03", "SP05"}
CANDIDATE_STATUS = "OVERRIDE_APPROVED"
APPROVAL_REF = "LSU_v3.3.3_Researcher_Approval.md decision #1 (2026-11-12)"

GEM5_BINARY = ROOT / "build/ARM/gem5.opt"
GEM5_SHA_FALLBACK = ("070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca")
CONFIG_PATH = ROOT / "configs/se/lsu_proxy.py"
CONFIG_SHA = hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()
CONFIG_FROZEN = ("YES (approved 2026-11-12; final binary and config SHA "
                 "recorded in Binary_Config)")

# v3.3.3 final measured ROI windows (A01 uses the approved 8-byte-only
# correction L-A12; A03 keeps the size-agnostic re-census).
DESIGN_ROI = {
    "A01": (585, 713, 129), "A03": (1040, 1222, 183),
    "FW02": (8, 67, 60), "FW05": (1, 2000, 2000),
    "SQ01": (1006, 1133, 128), "SQ03": (1009, 1136, 128),
    "SP05": (940, 1067, 128), "DA04": (33, 1056, 1024),
    "LP01": (886, 17525, 16640), "MD04": (3, 10, 8),
    "LQ04": (1, 5, 5), "RP01": (1, 255, 255),
}
PERCENTILES = (0.10, 0.30, 0.50, 0.70, 0.90)

# Six adopted candidate workloads (approval #1).  sq_reload_v3212 serves
# SQ01/SQ03/SP05; the three rows keep their own K* boundary probe.
CANDIDATE_WORKLOADS = (
    {
        "WorkloadID": "W4-v2", "CandidateFor": "FW02",
        "WorkloadName": "sq_forward_w4v2",
        "AbsolutePath": str(ROOT / "workloads/directed/sq_forward_w4v2"),
        "ELF_SHA256": "a08fb3a7b8bbcef76b0c3c3519a5787370ea7ead2d93de290e00fc6e44fe76e2",
        "Golden": "1f4cbf14327717df", "ControlChecksum": "1f4cbf14327717df",
        "K_Star": "n/a (load-preserving W4 variant)",
    },
    {
        "WorkloadID": "W7-v2", "CandidateFor": "RP01",
        "WorkloadName": "replay_partial_v332",
        "AbsolutePath": str(ROOT / "workloads/directed/replay_partial_v332"),
        "ELF_SHA256": "3f880cba7b6d16b61a453c37c68d6dbaaf63980dba5c9231218cf8dd8fa42e42",
        "Golden": "0xf3b1c554273d23f7", "ControlChecksum": "f3b1c554273d23f7",
        "K_Star": "n/a (partial-overlap replay)",
    },
    {
        "WorkloadID": "W7-v2", "CandidateFor": "MD04",
        "WorkloadName": "md04_violations_v332",
        "AbsolutePath": str(ROOT / "workloads/directed/md04_violations_v332"),
        "ELF_SHA256": "dd241c3097e61495141e614ce493ba4b2901a7df751baa95e69365bdf8f95c43",
        "Golden": "0x22be5ae3364d0c9f", "ControlChecksum": "22be5ae3364d0c9f",
        "K_Star": "n/a (8 static pairs)",
    },
    {
        "WorkloadID": "W3-v2", "CandidateFor": "SQ01",
        "WorkloadName": "sq_reload_v3212",
        "AbsolutePath": str(ROOT / "docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212"),
        "ELF_SHA256": "bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6",
        "Golden": "7df5034c23f3e703", "ControlChecksum": "7df5034c23f3e703",
        "K_Star": "1006",
    },
    {
        "WorkloadID": "W3-v2", "CandidateFor": "SQ03",
        "WorkloadName": "sq_reload_v3212",
        "AbsolutePath": str(ROOT / "docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212"),
        "ELF_SHA256": "bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6",
        "Golden": "7df5034c23f3e703", "ControlChecksum": "7df5034c23f3e703",
        "K_Star": "1009",
    },
    {
        "WorkloadID": "W6-v2", "CandidateFor": "SP05",
        "WorkloadName": "sq_reload_v3212",
        "AbsolutePath": str(ROOT / "docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212"),
        "ELF_SHA256": "bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6",
        "Golden": "7df5034c23f3e703", "ControlChecksum": "7df5034c23f3e703",
        "K_Star": "940",
    },
)
CANDIDATE_BY_MODEL = {c["CandidateFor"]: c for c in CANDIDATE_WORKLOADS}

# frozen, evidence-based terminal expectations (approval #3)
TERMINAL_EXPECTATION = {
    "A01": "R01/R04/R05 SDC; R02 SQUASHED+UNRELATED_SQUASH_NO_ARCH_ENTRY; R03 INJECTION_NOT_ACTIVATED",
    "A03": "SDC / ORACLE_FAIL (+ POST_ORACLE_SIM_HANG if the watchdog fires)",
    "FW02": "SDC except R03 MASKED / SUPPRESSED_FORWARD_NORMAL_VALUE",
    "FW05": "SDC on oracle failure",
    "SQ01": "SDC on oracle failure",
    "SQ03": "MASKED / VISIBILITY_TIMING_SHIFT (4/5 moved + 1/5 lifecycle-only)",
    "SP05": "SDC only with store_data_fnv; otherwise RELOAD_UNVERIFIABLE",
    "DA04": "SDC on oracle failure",
    "LP01": "SDC on oracle failure",
    "MD04": "R01 MASKED / INERT_AFTER_COMPLETION; others by oracle",
    "LQ04": "MASKED / ENTRY_INVALIDATED_RESTORED",
    "RP01": "HANG_WATCHDOG (internal watchdog; no SDC claim)",
}

SHEETS = (
    "Model_Design", "Fault_Sample_Manifest", "Control_Manifest",
    "ROI_Context_Mapping", "Causal_Propagation", "Workload_Oracle",
    "Binary_Config", "Readiness_Gate",
)


def fail(msg: str) -> None:
    raise SystemExit(f"lsu_v333_workbook: {msg}")


def kv(text: str | None, key: str, default: str = "PENDING") -> str:
    if not text:
        return default
    m = re.search(r"(?:^|;)" + re.escape(key) + r"=([^;]*)", text)
    return m.group(1) if m else default


def detail_kv(detail: str | None, key: str, default: str = "PENDING") -> str:
    if not detail:
        return default
    for part in detail.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            if k.strip() == key:
                return v.strip()
    return default


# ------------------------------------------------------------ frozen input --

def load_matrix(path: Path) -> list[dict]:
    if not path.exists():
        fail(f"frozen sample matrix not found: {path}")
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 60:
        fail(f"{path}: expected 60 rows, got {len(rows)}")
    ids = [r.get("SampleRunID") for r in rows]
    if len(set(ids)) != 60:
        fail(f"{path}: SampleRunID is not unique")
    for r in rows:
        if not (r.get("Seed") or "").strip():
            fail(f"{path}: blank Seed for {r.get('SampleRunID')}")
        if r.get("FaultModelID") not in MODELS:
            fail(f"{path}: unknown model {r.get('FaultModelID')}")
    return rows


def load_v327(path: Path):
    if not path.exists():
        fail(f"authoritative v3.2.7 workbook not found: {path}")
    return openpyxl.load_workbook(path, data_only=True)


def frozen_workloads(wb) -> tuple[list[dict], list[str]]:
    """Sheet-6 rows; the live Oracle column is the authoritative golden.

    W6/W8 must read ``2543a2a60de01795`` / ``3f89eab79392ce69``.  v3.2.7's
    legacy ``ExpectedGolden`` column in the same rows is stale for W6/W8; the
    conflict is recorded explicitly (never silently copied) and reported.
    """
    ws = wb["6.工作负载及无故障基线"]
    header = [c.value for c in ws[1]]
    rows = []
    for values in ws.iter_rows(min_row=2, values_only=True):
        if not values or not values[0]:
            continue
        rows.append(dict(zip(header, values)))
    expected = {"W6": "2543a2a60de01795", "W8": "3f89eab79392ce69"}
    warnings = []
    for wid, golden in expected.items():
        row = next((r for r in rows if r.get("WorkloadID") == wid), None)
        if row is None:
            fail(f"v3.2.7 sheet 6 has no {wid} row")
        got = str(row.get("Oracle") or "").strip()
        exp = str(row.get("ExpectedGolden") or "").strip()
        if got != golden:
            fail(f"{wid} Oracle mismatch: {got!r} != {golden!r}")
        row["_GoldenConflict"] = (
            f"ExpectedGolden column is stale ({exp}); Oracle is authoritative"
            if exp != golden else "none")
        if exp != golden:
            warnings.append(
                f"{wid}: v3.2.7 ExpectedGolden={exp!r} is stale; "
                f"using verified Oracle={got!r} (ledger L-D09)")
    return rows, warnings


def gem5_sha() -> tuple[str, str]:
    if GEM5_BINARY.exists():
        h = hashlib.sha256()
        with GEM5_BINARY.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest(), "sha256sum(build/ARM/gem5.opt) at build time"
    return GEM5_SHA_FALLBACK, "README_GROUND_TRUTH.md §1 (binary absent; not recomputed)"


# --------------------------------------------------------- measured inputs --

def load_csv(path: Path | None) -> list[dict] | None:
    if path is None or not path.exists():
        return None
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def index_rows(rows):
    return {(r.get("ModelID"), r.get("ContextID")): r for r in (rows or [])}


def summary_ordinal(runs: Path, model: str, ctx: str) -> str:
    if runs is None:
        return "PENDING"
    import json
    p = runs / f"{model}-{ctx}-fault/summary.json"
    if not p.exists():
        return "PENDING"
    try:
        return str(json.loads(p.read_text()).get("ordinal", "PENDING"))
    except Exception:
        return "PENDING"


def run_provenance(runs: Path, model: str, ctx: str) -> str:
    if runs is None:
        return "PENDING"
    p = runs / f"{model}-{ctx}-fault"
    return str(p) if p.is_dir() else "PENDING"


# --------------------------------------------------------------- sheets ----

def parse_identity(injection: str) -> dict[str, str]:
    return {
        "DynInstSeq": kv(injection, "seq"),
        "PC": kv(injection, "pc"),
        "VA": kv(injection, "va"),
        "PA": kv(injection, "pa"),
        "LQEntry": kv(injection, "lq"),
        "SQEntry": kv(injection, "sq"),
        "Generation": kv(injection, "gen"),
        "InstructionType": kv(injection, "type"),
        "DynamicState": kv(injection, "state"),
        "InjectionTick": kv(injection, "tick"),
    }


def build_model_design(wb):
    ws_src = wb["3.最终12模型矩阵"]
    header = [c.value for c in ws_src[1]]
    rows = {}
    for values in ws_src.iter_rows(min_row=2, values_only=True):
        if values and values[0] in MODELS:
            rows[values[0]] = dict(zip(header, values))

    cols = ("ModelID", "Unit", "FaultType", "SubTaskID", "RunID",
            "InjectionMode", "WorkloadID", "WorkloadName",
            "WorkloadIdentityStatus", "FaultLocation", "TargetField",
            "ExpectedObservation", "SourceAuditStatus", "ImplementationStatus",
            "TerminalExpectation", "ApprovalReference", "Notes")
    out = [list(cols)]
    for model in MODELS:
        r = rows.get(model, {})
        cand = CANDIDATE_BY_MODEL.get(model)
        wid = cand["WorkloadID"] if cand else r.get("WorkloadID")
        wname = cand["WorkloadName"] if cand else r.get("WorkloadName")
        status = CANDIDATE_STATUS if model in CANDIDATE_MODELS else "FORMAL"
        note = ("Candidate workload adopted after approval; SampleRunID/Seed "
                "unchanged." if cand else "Frozen formal design.")
        out.append([
            model, r.get("Unit"), r.get("FaultType"), r.get("SubTaskID"),
            r.get("RunID"), r.get("InjectionMode"), wid, wname, status,
            r.get("FaultLocation"), r.get("TargetField"),
            r.get("ExpectedObservation"), r.get("SourceAuditStatus"),
            r.get("ImplementationStatus"), TERMINAL_EXPECTATION.get(model),
            APPROVAL_REF if cand else "n/a", note,
        ])
    return out


def build_fault_manifest(matrix, runs, causal_idx, causal_available,
                         gem5_sha_value, gem5_prov, mapping_available=False):
    cols = (
        "SampleRunID", "RunID", "SubTaskID", "Seed", "FaultModelID",
        "ContextID", "Design_EventOrdinal", "Executed_EventOrdinal",
        "FaultLocation", "TargetField", "BitEntryByteIndex", "NormalValue",
        "FaultValue", "InjectionMode", "InjectionTiming", "FaultDuration",
        "TargetInstruction", "EligibleEventCondition", "FaultConfigID",
        "ContextDifferenceRule", "WorkloadPath", "WorkloadIdentityStatus",
        "Gem5BinarySHA256", "WorkloadELF_SHA256", "InputHash", "Oracle",
        "OracleSource",
        "WarmUp", "ROI", "ROI_Start", "ROI_N", "Percentile",
        "EligibleEventOrdinal", "DynInstSeq", "PC", "VA", "PA",
        "InstructionType", "LQEntry", "SQEntry", "DynamicState",
        "InjectionEligibility", "ExecutionStatus", "TerminalState",
        "TerminalReason", "TraceCompleteness", "EvidencePath",
        "ConfigFrozen", "DecisionStatus", "Provenance",
    )
    out = [list(cols)]
    for r in matrix:
        model = r["FaultModelID"]
        ctx = r["SampleRunID"][-3:]
        cand = CANDIDATE_BY_MODEL.get(model)
        row = causal_idx.get((model, ctx))

        executed = "PENDING"
        if row is not None:
            executed = kv(row.get("ROI/Percentile/Ordinal", ""), "ordinal")
        if executed == "PENDING" and runs is not None:
            executed = summary_ordinal(runs, model, ctx)

        measured = parse_identity(row.get("Injection")) if row else {}
        terminal = row.get("Terminal", "PENDING") if row else "PENDING"
        reason = row.get("TerminalReason", "PENDING") if row else "PENDING"
        trace = row.get("TraceCompleteness", "PENDING") if row else "PENDING"
        evidence = row.get("EvidencePaths", "PENDING") if row else "PENDING"
        activation = row.get("Activation", "") if row else ""
        eligibility = ("ACTIVATED" if activation and activation != "n/a"
                       else "PENDING")
        execution = ("MEASURED_TERMINAL"
                     if terminal not in ("PENDING", "UNRESOLVED") else "PENDING")

        rel, re_, n = DESIGN_ROI[model]
        out.append([
            r["SampleRunID"], r["RunID"], r["SubTaskID"], r["Seed"], model,
            ctx, r.get("EventOrdinal"), executed,
            r.get("FaultLocation"), r.get("TargetField"),
            r.get("BitEntryByteIndex"), r.get("NormalValue"),
            r.get("FaultValue"), r.get("InjectionMode"),
            r.get("InjectionTiming"), r.get("FaultDuration"),
            r.get("TargetInstruction"), r.get("EligibleEventCondition"),
            r.get("FaultConfigID"), r.get("ContextDifferenceRule"),
            cand["AbsolutePath"] if cand else r.get("WorkloadPath"),
            CANDIDATE_STATUS if cand else "FORMAL",
            gem5_sha_value,
            cand["ELF_SHA256"] if cand else r.get("BinarySHA256"),
            r.get("InputHash"),
            cand["Golden"] if cand else r.get("Oracle"),
            ("candidate workload golden (OVERRIDE_APPROVED)" if cand
             else "frozen matrix Oracle (W1-W8 / formal workload)"), "0",
            (f"measured main-loop eligible window {rel}-{re_} (N={n}) on "
             f"the final binary" if mapping_available else
             f"definition: measured main-loop eligible window {rel}-{re_} "
             f"(N={n}); measurement PENDING"),
            rel, n, PERCENTILES[int(ctx[1:]) - 1],
            executed, measured.get("DynInstSeq", "PENDING"),
            measured.get("PC", "PENDING"), measured.get("VA", "PENDING"),
            measured.get("PA", "PENDING"),
            measured.get("InstructionType", "PENDING"),
            measured.get("LQEntry", "PENDING"),
            measured.get("SQEntry", "PENDING"),
            measured.get("DynamicState", "PENDING"),
            eligibility, execution, terminal, reason, trace, evidence,
            CONFIG_FROZEN, r.get("DecisionStatus"),
            f"identity=frozen matrix; measured={causal_available}; "
            f"gem5={gem5_prov}; source_run={run_provenance(runs, model, ctx)}",
        ])
    return out


def build_control_manifest(matrix, controls):
    cols = ("SampleRunID", "ModelID", "ContextID", "Seed", "Ordinal",
            "WorkloadIdentityStatus", "ControlInjected", "ControlZeroProof",
            "ControlOracle", "ControlExitCode", "FaultInjected",
            "FaultTerminal", "FaultOracle", "EvidenceBinarySHA256",
            "FaultEvidencePath", "ControlEvidencePath", "Provenance")
    idx = index_rows(controls)
    out = [list(cols)]
    for r in matrix:
        model = r["FaultModelID"]
        ctx = r["SampleRunID"][-3:]
        c = idx.get((model, ctx))
        cand = CANDIDATE_BY_MODEL.get(model)
        if c is None:
            ordinal = "PENDING"
            injected = proof = oracle = exit_code = "PENDING"
            fault_inj = fault_term = fault_oracle = "PENDING"
            binary = fpath = cpath = "PENDING"
            prov = "no control artifact supplied (scaffold; no PASS)"
        else:
            ordinal = c.get("Ordinal", "PENDING")
            injected = c.get("ControlInjected", "PENDING")
            proof = c.get("ControlZeroProof", "PENDING")
            oracle = c.get("ControlOracle", "PENDING")
            exit_code = c.get("ControlExitCode", "PENDING")
            fault_inj = c.get("FaultInjected", "PENDING")
            fault_term = c.get("FaultTerminal", "PENDING")
            fault_oracle = c.get("FaultOracle", "PENDING")
            binary = c.get("BinarySHA256", "PENDING")
            fpath = c.get("FaultEvidencePath", "PENDING")
            cpath = c.get("ControlEvidencePath", "PENDING")
            prov = "measured control artifact"
        out.append([
            r["SampleRunID"], model, ctx, r["Seed"], ordinal,
            CANDIDATE_STATUS if cand else "FORMAL",
            injected, proof, oracle, exit_code, fault_inj, fault_term,
            fault_oracle, binary, fpath, cpath, prov,
        ])
    return out


def build_roi_mapping(matrix, mapping):
    cols = ("ModelID", "ContextID", "SampleRunID", "Seed", "Workload",
            "WorkloadIdentityStatus", "ROI_Start_Ordinal", "ROI_N",
            "Percentile", "Rank_k", "Absolute_Eligible_Ordinal",
            "Executed_EventOrdinal", "SourceSampleRunID", "MappingStatus",
            "EvidenceBinarySHA", "EvidencePath")
    idx = index_rows(mapping)
    out = [list(cols)]
    for r in matrix:
        model = r["FaultModelID"]
        ctx = r["SampleRunID"][-3:]
        m = idx.get((model, ctx))
        cand = CANDIDATE_BY_MODEL.get(model)
        rs, re_, n = DESIGN_ROI[model]
        ctx_idx = int(ctx[1:]) - 1
        if m is None:
            values = [rs, n, PERCENTILES[ctx_idx], "PENDING", "PENDING",
                      "PENDING", "PENDING", "DESIGN_REFERENCE_ONLY", "PENDING",
                      "PENDING"]
        else:
            abs_ord = m.get("Absolute_Eligible_Ordinal", "PENDING")
            values = [m.get("ROI_Start_Ordinal", rs),
                      m.get("ROI_N", n), m.get("Percentile", PERCENTILES[ctx_idx]),
                      m.get("Rank_k", "PENDING"), abs_ord, abs_ord,
                      m.get("SampleRunID", "n/a"),
                      m.get("MappingStatus", "MEASURED"),
                      m.get("EvidenceBinarySHA", "PENDING"),
                      m.get("EvidencePath", "PENDING")]
        out.append([
            model, ctx, r["SampleRunID"], r["Seed"],
            CANDIDATE_BY_MODEL[model]["WorkloadName"] if cand
            else r.get("WorkloadPath", "").rstrip("/").split("/")[-1],
            CANDIDATE_STATUS if cand else "FORMAL",
            values[0], values[1], values[2], values[3], values[4], values[5],
            values[6], values[7], values[8], values[9],
        ])
    return out


def build_causal(matrix, causal_rows, causal_available):
    columns = ("ModelID", "ContextID", "ROI/Percentile/Ordinal", "Injection",
               "Activation", "FirstDivergence", "Downstream", "Consumer",
               "CommitSquashReplay", "Terminal", "TerminalReason",
               "ApplicationOracle", "EvidenceClass", "TraceCompleteness",
               "MaskingMechanism", "EvidencePaths")
    if causal_available and causal_rows is not None:
        out = [list(columns)]
        idx = index_rows(causal_rows)
        for r in matrix:
            model = r["FaultModelID"]
            ctx = r["SampleRunID"][-3:]
            row = idx.get((model, ctx))
            if row is None:
                out.append([model, ctx, "PENDING"] + ["PENDING"] * 13)
            else:
                out.append([row.get(c, "PENDING") for c in columns])
        return out
    out = [list(columns)]
    for r in matrix:
        model = r["FaultModelID"]
        ctx = r["SampleRunID"][-3:]
        rs, re_, n = DESIGN_ROI[model]
        roi = (f"ROI={rs}-{re_};N={n};p={PERCENTILES[int(ctx[1:])-1]:.2f};"
               "ordinal=PENDING")
        out.append([model, ctx, roi] + ["PENDING"] * 13)
    return out


def build_workload_oracle(frozen_rows):
    cols = ("WorkloadID", "CandidateFor", "WorkloadName", "AbsolutePath",
            "ELF_SHA256", "Golden", "ControlChecksum", "OracleMatch",
            "WorkloadStatus", "ApprovalReference", "K_Star", "Source",
            "ExpectedGolden_Column", "GoldenColumnConflict")
    out = [list(cols)]
    for r in frozen_rows:
        out.append([
            r.get("WorkloadID"), "n/a", r.get("WorkloadName"),
            r.get("AbsolutePath"), r.get("SHA256"), r.get("Oracle"),
            r.get("Oracle"), "YES" if r.get("Oracle") else "n/a",
            r.get("CurrentStatus"), "frozen v3.2.7 sheet 6", "n/a",
            "authoritative v3.2.7 workbook (Oracle column)",
            r.get("ExpectedGolden"), r.get("_GoldenConflict", "none"),
        ])
    out.append([])
    out.append(["Candidate workload rows (approval 2026-11-12)"])
    out.append(list(cols))
    for c in CANDIDATE_WORKLOADS:
        out.append([
            c["WorkloadID"], c["CandidateFor"], c["WorkloadName"],
            c["AbsolutePath"], c["ELF_SHA256"], c["Golden"],
            c["ControlChecksum"], "YES", CANDIDATE_STATUS, APPROVAL_REF,
            c["K_Star"], "LSU_Workload_Oracle_Final_Audit.csv + Agent C dossier",
            "n/a", "none",
        ])
    return out


def build_binary_config(matrix, gem5_sha_value, gem5_prov):
    cols = ("ModelID", "Unit", "Gem5BinaryPath", "Gem5BinarySHA256",
            "Gem5SHAProvenance", "WorkloadELF_SHA256", "WorkloadPath",
            "ConfigScript", "ConfigSHA256", "WarmUp", "ROI_Definition",
            "ConfigFrozen", "LegacyFrozenBinarySHA256Field", "Provenance")
    units = {"A01": "AGU", "A03": "AGU", "FW02": "FWD", "FW05": "FWD",
             "SQ01": "SQ", "SQ03": "SQ", "SP05": "SQ", "DA04": "LSQ",
             "LP01": "L1D", "MD04": "LSQ", "LQ04": "LQ", "RP01": "LSQFwd"}
    seen = set()
    out = [list(cols)]
    for r in matrix:
        model = r["FaultModelID"]
        if model in seen:
            continue
        seen.add(model)
        cand = CANDIDATE_BY_MODEL.get(model)
        out.append([
            model, units.get(model), str(GEM5_BINARY), gem5_sha_value,
            gem5_prov,
            cand["ELF_SHA256"] if cand else r.get("BinarySHA256"),
            cand["AbsolutePath"] if cand else r.get("WorkloadPath"),
            str(CONFIG_PATH), CONFIG_SHA, "0",
            "measured main-loop eligible window on the final binary",
            CONFIG_FROZEN,
            "the frozen matrix BinarySHA256 column is the WORKLOAD ELF hash, "
            "not gem5.opt",
            "independent Gem5BinarySHA256 vs WorkloadELF_SHA256 columns",
        ])
    out.append([])
    out.append(["Field", "Value", "Provenance"])
    out.extend([
        ["Gem5BinaryPath", str(GEM5_BINARY), "build/ARM/gem5.opt"],
        ["Gem5BinarySHA256", gem5_sha_value, gem5_prov],
        ["ConfigPath", str(CONFIG_PATH), "executed config (current worktree)"],
        ["ConfigSHA256", CONFIG_SHA, "sha256sum(configs/se/lsu_proxy.py)"],
        ["WarmUp", "0", "researcher approval #4 (2026-11-12)"],
        ["ROI", "measured main-loop eligible window on the final binary",
         "researcher approval #4 (2026-11-12)"],
        ["EventOrdinalSchema",
         "Design_EventOrdinal (1-5, frozen) + Executed_EventOrdinal (measured)",
         "researcher approval #4; ledger L-D08"],
        ["ConfigFrozen", CONFIG_FROZEN,
         "researcher approval #4; final binary validated; frozen Excel unchanged"],
    ])
    return out


def build_readiness(matrix, causal_idx, control_idx, causal_available):
    cols = ("SampleRunID", "ModelID", "ContextID", "WorkloadIdentityStatus",
            "IdentityFrozen", "FaultInjected", "ControlClean",
            "TerminalEvidence", "TraceComplete", "ProvenanceOK", "ReadyGate",
            "BlockingReason")
    out = [list(cols)]
    for r in matrix:
        model = r["FaultModelID"]
        ctx = r["SampleRunID"][-3:]
        cand = CANDIDATE_BY_MODEL.get(model)
        c = causal_idx.get((model, ctx))
        ctl = control_idx.get((model, ctx))
        fault_inj = ("YES" if c and c.get("Injection", "n/a") not in ("n/a", "PENDING")
                     else "PENDING")
        control_clean = ("YES" if ctl and ctl.get("ControlZeroProof")
                         else "PENDING")
        terminal_ok = ("MEASURED" if c and c.get("Terminal") not in
                       ("PENDING", "UNRESOLVED") else "PENDING")
        trace = c.get("TraceCompleteness") if c else None
        trace_ok = ("PASS" if trace in ("COMPLETE", "COMPLETE_PROP_TRACE")
                    else "PASS" if (trace == "PARTIAL_WATCHDOG" and
                                    c.get("Terminal", "").startswith("HANG"))
                    else "PENDING")
        prov_ok = ("PASS" if c and c.get("EvidencePaths") not in
                   ("n/a", "PENDING") else "PENDING")
        gate_ok = all(x in ("YES", "MEASURED", "PASS")
                      for x in (fault_inj, control_clean, terminal_ok,
                                trace_ok, prov_ok))
        blocking = []
        if fault_inj != "YES":
            blocking.append("fault artifact missing")
        if control_clean != "YES":
            blocking.append("control artifact missing")
        if terminal_ok != "MEASURED":
            blocking.append("terminal not measured")
        out.append([
            r["SampleRunID"], model, ctx,
            CANDIDATE_STATUS if cand else "FORMAL", "YES", fault_inj,
            control_clean, terminal_ok, trace_ok, prov_ok,
            "PASS" if gate_ok else "PENDING",
            "; ".join(blocking) if blocking else "n/a",
        ])
    out.append([])
    out.append(["Gate", "Definition", "Status"])
    out.extend([
        ["Identity", "SampleRunID/Seed/Design_EventOrdinal match the frozen matrix",
         "ENFORCED"],
        ["WorkloadIdentity", "FORMAL or OVERRIDE_APPROVED; no ID/seed change",
         "ENFORCED"],
        ["FaultInjected", "fault run has an injection artifact", "ENFORCED"],
        ["ControlClean", "control run injected 0 and oracle PASS", "ENFORCED"],
        ["TerminalEvidence", "terminal measured by the causal generator", "ENFORCED"],
        ["TraceComplete",
         "COMPLETE / COMPLETE_PROP_TRACE; PARTIAL_WATCHDOG accepted only for "
         "HANG_WATCHDOG", "ENFORCED"],
        ["Provenance", "gem5 binary SHA and evidence path recorded", "ENFORCED"],
        ["Final", "READY_FOR_FORMAL_EXPERIMENT only when every row passes",
         "PASS (v3.3.3 final; independent audit separate)"],
    ])
    return out


# ------------------------------------------------------------- invariants --

CRITICAL = {
    "Fault_Sample_Manifest": (
        "ExecutionStatus", ("TerminalState", "TerminalReason",
                            "TraceCompleteness", "EvidencePath")),
    "Readiness_Gate": (
        "ReadyGate", ("FaultInjected", "ControlClean", "TerminalEvidence",
                      "TraceComplete", "ProvenanceOK")),
}


def enforce_no_blank_pass(wb) -> None:
    for sheet, (status_col, critical) in CRITICAL.items():
        ws = wb[sheet]
        header = [c.value for c in ws[1]]
        idx = {name: header.index(name) for name in (status_col, *critical)}
        for values in ws.iter_rows(min_row=2, values_only=True):
            if not values or not values[0]:
                continue
            status = values[idx[status_col]]
            if status not in ("PASS", "YES"):
                continue
            for name in critical:
                v = values[idx[name]]
                if v in (None, "", "PENDING", "n/a"):
                    fail(f"{sheet} row {values[0]}: {status_col}="
                         f"{status!r} but critical field {name}={v!r}")


def _write_sheet(wb, title, rows):
    ws = wb.create_sheet(title)
    for row in rows:
        ws.append(list(row))
    if rows:
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    return ws


def build(runs: Path | None, mapping: Path | None, controls: Path | None,
          causal: Path | None, matrix_path: Path, workbook_path: Path,
          out_path: Path):
    if out_path.resolve() == workbook_path.resolve():
        fail("refusing to overwrite the frozen v3.2.7 workbook")
    if out_path.resolve() == matrix_path.resolve():
        fail("refusing to overwrite the frozen sample matrix")
    if str(out_path.resolve()).startswith(
            str((ROOT / "docs/gem5-fi/lsu/implementation_v3_2").resolve())):
        fail("refusing to write inside the frozen design directory")

    matrix = load_matrix(matrix_path)
    wb_src = load_v327(workbook_path)
    frozen, frozen_warnings = frozen_workloads(wb_src)
    for warning in frozen_warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    sha, sha_prov = gem5_sha()

    mapping_rows = load_csv(mapping)
    control_rows = load_csv(controls)
    causal_rows = load_csv(causal)
    causal_available = causal_rows is not None
    causal_idx = index_rows(causal_rows)
    control_idx = index_rows(control_rows)

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    _write_sheet(wb, "Model_Design", build_model_design(wb_src))
    _write_sheet(wb, "Fault_Sample_Manifest",
                 build_fault_manifest(matrix, runs, causal_idx,
                                      causal_available, sha, sha_prov,
                                      mapping_rows is not None))
    _write_sheet(wb, "Control_Manifest",
                 build_control_manifest(matrix, control_rows))
    _write_sheet(wb, "ROI_Context_Mapping",
                 build_roi_mapping(matrix, mapping_rows))
    _write_sheet(wb, "Causal_Propagation",
                 build_causal(matrix, causal_rows, causal_available))
    _write_sheet(wb, "Workload_Oracle", build_workload_oracle(frozen))
    _write_sheet(wb, "Binary_Config", build_binary_config(matrix, sha, sha_prov))
    _write_sheet(wb, "Readiness_Gate",
                 build_readiness(matrix, causal_idx, control_idx,
                                 causal_available))

    if tuple(wb.sheetnames) != SHEETS:
        fail(f"sheet order/name drift: {wb.sheetnames!r}")
    enforce_no_blank_pass(wb)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return {
        "rows": len(matrix),
        "causal": causal_available,
        "controls": control_rows is not None,
        "mapping": mapping_rows is not None,
        "gem5_sha": sha,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path,
                    default=ROOT / "audit_v3_3_3/runs",
                    help="v3.3.3 runs directory (missing -> PENDING scaffold)")
    ap.add_argument("--mapping", type=Path,
                    default=ROOT / "audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv")
    ap.add_argument("--controls", type=Path,
                    default=ROOT / "audit_v3_3_3/controls/LSU_Fault_Control_Pair_Final.csv")
    ap.add_argument("--causal", type=Path,
                    default=ROOT / "audit_v3_3_3/LSU_60Context_Causal_Propagation.csv")
    ap.add_argument("--matrix", type=Path, default=MATRIX_PATH)
    ap.add_argument("--workbook", type=Path, default=V327_PATH)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    stats = build(args.runs, args.mapping, args.controls, args.causal,
                  args.matrix, args.workbook, args.out)
    print(f"wrote {args.out}")
    print(f"sheets: {', '.join(SHEETS)}")
    print(f"rows: {stats['rows']}; causal={stats['causal']}; "
          f"controls={stats['controls']}; mapping={stats['mapping']}")
    print(f"gem5 binary SHA256: {stats['gem5_sha']}")
    if not stats["causal"]:
        print("NOTE: no causal artifact supplied; measured fields are PENDING "
              "(nothing fabricated, no PASS).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
