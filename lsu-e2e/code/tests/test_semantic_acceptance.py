#!/usr/bin/env python3
"""Paper-final acceptance checks for the semantic repair round.

Paths are resolved by ``final_paths`` against the package root, so the same
suite runs unchanged in the working tree and in an independently extracted
``LSU_E2E_PAPER_FINAL_FROZEN_R2`` package.
"""
from __future__ import annotations

import collections
import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import final_paths as P

CH = P.CHAINS
REP = P.REPORTS
SEM = P.semantic()
CTL = P.controls()


def _chains():
    return [json.loads(p.read_text()) for p in
            sorted(CH.glob("E2E-*-FAULT.causal_chain.json"))]


def test_all_165_non_rp01_walks_are_semantically_clean():
    runs = [r for r in _chains() if r.get("model") != "RP01"]
    assert len(runs) == 165
    for r in runs:
        sw = r.get("semantic_walk") or {}
        assert sw, r["run_id"]
        assert sw.get("semantic_mismatches", 0) == 0, r["run_id"]
        assert sw.get("unsupported_semantics", 0) == 0, r["run_id"]
        assert sw.get("unsupported_critical", 0) == 0, r["run_id"]
        assert sw.get("unverified_semantic_edges", 0) == 0, r["run_id"]
        nz = sw.get("nzcv") or {}
        assert nz.get("flag_semantic_mismatches", 0) == 0, r["run_id"]
        assert nz.get("conditional_unverified", 0) == 0, r["run_id"]
        mem = sw.get("memory") or {}
        assert mem.get("semantics_incomplete", 0) == 0, r["run_id"]
        multi = sw.get("multi_source") or {}
        assert multi.get("dropped_sources", 0) == 0, r["run_id"]


def test_every_pre_repair_mismatch_has_a_final_outcome():
    rows = list(csv.DictReader(open(
        SEM / "SEMANTIC_MISMATCH_RECONCILIATION.csv")))
    assert len(rows) == 6812
    assert collections.Counter(r["OldStatus"] for r in rows) == {
        "MISMATCH": 6808, "UNSUPPORTED": 4}
    final = collections.Counter(r["FinalOutcome"] for r in rows)
    allowed = {"RESOLVED_BY_CORRECT_SEMANTICS",
               "DIRECTLY_VERIFIED_FROM_COMMIT_TRACE",
               "OUTSIDE_CAUSAL_PATH_WITH_PROOF",
               "UNRESOLVED_CRITICAL_SEMANTICS"}
    assert set(final) <= allowed
    assert final.get("UNRESOLVED_CRITICAL_SEMANTICS", 0) == 0
    assert sum(final.values()) == 6812
    for r in rows:
        assert r["NewStatus"] in ("MATCH", "")
        if r["FinalOutcome"] == "RESOLVED_BY_CORRECT_SEMANTICS":
            assert r["NewStatus"] == "MATCH"


def test_semantic_statistics_match_json_and_csv():
    st = json.loads((SEM / "SEMANTIC_STATISTICS.json").read_text())
    rows = list(csv.DictReader(open(
        SEM / "SEMANTIC_REVALIDATION_SUMMARY_BY_RUN.csv")))
    assert st["before_mismatch"] == 6808
    assert st["before_unsupported"] == 4
    assert st["before_rows"] == 6812
    assert st["semantic_mismatches"] == 0
    assert st["unsupported_critical"] == 0
    assert st["unverified_semantic_edges"] == 0
    assert st["flag_semantic_mismatches"] == 0
    assert st["conditional_unverified"] == 0
    assert st["memory_semantics_incomplete"] == 0
    assert st["dropped_sources"] == 0
    assert len(rows) == 180
    assert sum(int(r["SemanticMismatches"] or 0) for r in rows) == 0
    assert sum(int(r["UnsupportedCritical"] or 0) for r in rows) == 0
    assert sum(int(r["UnverifiedSemanticEdges"] or 0) for r in rows) == 0
    assert sum(int(r["RevalidationRows"] or 0) for r in rows) == \
        st["reval_rows"]
    assert sum(1 for r in rows
               if r["SemanticWalkStatus"] == "EXECUTED") == 153
    assert sum(1 for r in rows
               if r["SemanticWalkStatus"] == "NO_TAINTED_INSTRUCTION") == 12
    assert sum(1 for r in rows
               if r["SemanticWalkStatus"] == "RP01_SEPARATE_TRACE") == 15


def test_all_180_ledger_covers_every_run():
    path = P.all180_ledger()
    with P.open_text(path) as f:
        reader = csv.DictReader(f)
        seen = set()
        total = 0
        for r in reader:
            total += 1
            seen.add(r["RunID"])
    chains = {r["run_id"] for r in _chains()}
    assert chains <= seen
    assert len(seen) == 180
    # The ledger contains one sentinel row for each run whose SemanticWalk
    # is not a register walk (12 NO_TAINTED_INSTRUCTION + 15
    # RP01_SEPARATE_TRACE).  Those sentinel rows are not revalidation
    # records; reconcile the total explicitly instead of hiding the gap.
    st = json.loads((SEM / "SEMANTIC_STATISTICS.json").read_text())
    rows = list(csv.DictReader(open(
        SEM / "SEMANTIC_REVALIDATION_SUMMARY_BY_RUN.csv")))
    sentinels = sum(1 for r in rows if int(r["RevalidationRows"] or 0) == 0)
    assert sentinels == 27
    assert total == st["reval_rows"] + sentinels == 1141593


def test_control_evidence_index_is_complete_and_hashable():
    rows = list(csv.DictReader(open(
        CTL / "STRICT_E2E_CONTROL_EVIDENCE_INDEX.csv")))
    assert len(rows) == 60
    assert {r["ModelID"] for r in rows} == {
        "A01", "A03", "DA04", "FW02", "FW05", "LP01", "LQ04",
        "MD04", "RP01", "SP05", "SQ01", "SQ03"}
    assert all(r["ContextID"] in {"C01", "C02", "C03", "C04", "C05"}
               for r in rows)
    for r in rows:
        assert r["PropExists"] == r["CommitExists"] == r["StdoutExists"] == \
            "True", r["RunID"]
        for k in ("PropSHA256", "CommitSHA256", "StdoutSHA256"):
            assert len(r[k]) == 64, (r["RunID"], k)
        assert r["ControlStatus"] == "COMPLETED", r["RunID"]
        assert r["OraclePass"] in ("True", "true"), r["RunID"]


def test_evidence_index_contains_all_controls():
    rows = list(csv.DictReader(open(
        CTL / "STRICT_E2E_EVIDENCE_INDEX.csv")))
    ctrl = {r["RunID"] for r in rows if r["RunID"].endswith("-CTRL")}
    assert len(ctrl) == 60
    assert all(r["Exists"] == "True" for r in rows
               if r["RunID"].endswith("-CTRL"))
