#!/usr/bin/env python3
"""R2 final-package acceptance: graphs, root causes, masks, RP01, squash.

Package-self-contained tests resolve every path through ``final_paths``.
The one server-evidence test is explicitly gated: run it on the server with
``LSU_E2E_SERVER_EVIDENCE=1``; in an extracted package it is reported as a
documented skip, never as a pass.
"""
from __future__ import annotations

import collections
import csv
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "runner"))
import final_paths as P
import e2e_strict_engine as E

ROOT = P.ROOT
REP = P.REPORTS
CH = P.CHAINS
SQUASH = P.squash()

MODELS = ("A01", "A03", "DA04", "FW02", "FW05", "LP01", "LQ04",
          "MD04", "RP01", "SP05", "SQ01", "SQ03")
CONTEXTS = ("C01", "C02", "C03", "C04", "C05")
TIMINGS = ("T01", "T02", "T03")
MASKING = {"ACTIVATED_NO_DATA_CORRUPTION", "MASKED_BY_OVERWRITE",
           "MASKED_BY_NON_CONSUMPTION", "MASKED_BY_VALUE_CONVERGENCE"}
SQUASH_IDS = {
    ("FW02", "C05", "T01"), ("FW05", "C05", "T01"),
    ("FW05", "C05", "T02"), ("FW05", "C05", "T03"),
    ("LP01", "C05", "T02"), ("LQ04", "C05", "T03"),
}


@pytest.fixture(scope="module")
def chains():
    return [json.loads(p.read_text())
            for p in sorted(CH.glob("E2E-*-FAULT.causal_chain.json"))]


@pytest.fixture(scope="module")
def rp01():
    return [json.loads(p.read_text())
            for p in sorted(P.rp01_chains().glob(
                "RP01OBS-*-FAULT.strict.json"))]


def _csv(path):
    return list(csv.DictReader(open(path)))


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 180 causal graphs
# ---------------------------------------------------------------------------
def test_180_chains_cover_the_full_matrix(chains):
    ids = {c["run_id"] for c in chains}
    expected = {"E2E-%s-%s-%s-FAULT" % (m, c, t)
                for m in MODELS for c in CONTEXTS for t in TIMINGS}
    assert ids == expected
    assert len(chains) == 180
    for c in chains:
        gv = c.get("graph_validation") or {}
        assert gv.get("passed") is True, c["run_id"]
        assert gv.get("gaps") in ([], None), c["run_id"]
        cls = c["classification"]
        assert cls["end_to_end_status"] == "E2E_CAUSAL_COMPLETE", c["run_id"]
        assert not cls.get("gaps"), c["run_id"]
        assert c["nodes"], c["run_id"]
        assert c["edges"], c["run_id"]
        nid = {n["event_id"] for n in c["nodes"]}
        assert {e["source"] for e in c["edges"]} <= nid, c["run_id"]
        assert {e["target"] for e in c["edges"]} <= nid, c["run_id"]
        kinds = {n["kind"] for n in c["nodes"]}
        if c["model"] == "RP01":
            assert {"fault_injection", "target_instruction",
                    "simulator_watchdog", "commit_progress", "lq_state",
                    "rob_head_state"} <= kinds, (c["run_id"], kinds)
        else:
            assert {"injection", "target_instruction",
                    "application_output"} <= kinds, (c["run_id"], kinds)
            if c["classification"]["application_symptom"] in (
                    "WRONG_OUTPUT", "INTERMEDIATE_VALUE_DIVERGENCE"):
                assert "first_software_divergence" in kinds, c["run_id"]
        assert len({e["edge_id"] for e in c["edges"]}) == len(c["edges"])


# ---------------------------------------------------------------------------
# root-cause matrix
# ---------------------------------------------------------------------------
MATRIX_REQUIRED = {
    "RunID", "ModelID", "ContextID", "TimingID", "FaultMechanism",
    "InjectionHook", "InjectionParameters", "TargetDynInstSeq",
    "TargetDynInstPC", "OriginalMicroarchitecturalValue",
    "FaultyMicroarchitecturalValue", "FirstMicroarchitecturalDivergence",
    "FirstArchitecturalDivergence", "FirstSoftwareDivergence",
    "FaultApplicationValue", "ControlApplicationValue", "FaultAddress",
    "ControlAddress", "StoreVersion", "ForwardingSource",
    "FirstIncorrectHashInput", "FinalObservedOutput", "FinalControlOutput",
    "ApplicationSymptom", "PropagationTermination", "EvidencePaths",
    "EvidenceConfidence", "RootCauseNarrative",
}


def test_root_cause_matrix_is_complete_and_specific():
    rows = _csv(REP / "FINAL_ROOT_CAUSE_MATRIX_180.csv")
    assert len(rows) == 180
    assert MATRIX_REQUIRED <= set(rows[0])
    assert len({r["RunID"] for r in rows}) == 180
    for r in rows:
        assert r["TargetDynInstSeq"] not in ("", "UNKNOWN", "N/A"), r["RunID"]
        assert r["TargetDynInstPC"] not in ("", "UNKNOWN"), r["RunID"]
        assert r["RootCauseNarrative"].strip(), r["RunID"]
        assert r["EvidencePaths"].strip(), r["RunID"]
        assert r["ApplicationSymptom"] != "UNKNOWN", r["RunID"]
        assert r["PropagationTermination"] != "UNKNOWN", r["RunID"]
        assert r["FaultMechanismFamily"] != "UNMAPPED", r["RunID"]
        if r["RunID"].startswith("E2E-RP01-"):
            assert r["ApplicationSymptom"] == "SIMULATOR_WATCHDOG", r["RunID"]
            assert r["PropagationTermination"] == \
                "SIMULATOR_STALL_WATCHDOG", r["RunID"]
            assert "watchdog" in r["RootCauseNarrative"], r["RunID"]
        elif r["PropagationTermination"] == "COMMITTED_AND_PROPAGATED":
            assert r["FirstSoftwareDivergence"] != "NOT_OBSERVED", r["RunID"]
            assert r["FirstIncorrectHashInput"] not in ("N/A", "UNKNOWN"), \
                r["RunID"]
        if r["FaultMechanism"] == "UNKNOWN":
            # Only FW02 carries the frozen UNKNOWN label; its injected fwd
            # record supplies the concrete derived mechanism.
            assert r["ModelID"] == "FW02", r["RunID"]
            assert r["FaultMechanismFamily"] == \
                "STORE_TO_LOAD_FORWARDING_SUPPRESSED", r["RunID"]


def test_final_reports_agree_with_chains(chains):
    sym = _csv(REP / "FINAL_SOFTWARE_SYMPTOMS.csv")
    term = _csv(REP / "FINAL_PROPAGATION_TERMINATION.csv")
    assert len(sym) == len(term) == 180
    assert collections.Counter(r["SoftwareSymptom"] for r in sym) == {
        "WRONG_OUTPUT": 108, "NO_VISIBLE_ERROR": 37,
        "INTERMEDIATE_VALUE_DIVERGENCE": 20, "HANG_TIMEOUT": 15}
    assert collections.Counter(
        r["PropagationTermination"] for r in term) == {
            "COMMITTED_AND_PROPAGATED": 108,
            "ACTIVATED_NO_DATA_CORRUPTION": 34,
            "MASKED_BY_OVERWRITE": 18,
            "MASKED_BY_NON_CONSUMPTION": 3,
            "MASKED_BY_VALUE_CONVERGENCE": 2,
            "SIMULATOR_STALL_WATCHDOG": 15}
    assert collections.Counter(r["ApplicationSymptom"] for r in sym) == {
        "STALE_DATA_USED": 47, "WRONG_MEMORY_CONTENT": 27,
        "WRONG_ADDRESS_EFFECT": 24, "WRONG_NUMERIC_VALUE": 10,
        "NO_VISIBLE_ERROR": 37, "INTERMEDIATE_VALUE_DIVERGENCE": 20,
        "SIMULATOR_WATCHDOG": 15}
    for name in ("FINAL_MODEL_STATISTICS.csv",
                 "FINAL_CONTEXT_STATISTICS.csv",
                 "FINAL_TIMING_STATISTICS.csv"):
        rows = _csv(REP / name)
        assert sum(int(r["Runs"]) for r in rows) == 180, name
    edges = _csv(REP / "FINAL_EDGE_STATISTICS.csv")
    total = [r for r in edges if r["RunID"] == "TOTAL"][0]
    assert int(total["EdgeCount"]) == sum(len(c["edges"]) for c in chains)
    assert int(total["EdgeCount"]) == 712998
    gv = _csv(REP / "FINAL_GRAPH_VALIDATION.csv")
    assert len(gv) == 180
    assert all(r["EndToEndStatus"] == "E2E_CAUSAL_COMPLETE" for r in gv)
    assert all(r["GraphValidated"] == "True" for r in gv)


def test_masking_and_intermediate_divergence_are_connected(chains):
    masked = ivd = 0
    for c in chains:
        cls = c["classification"]
        if cls["propagation_termination"] not in MASKING:
            continue
        masked += 1
        kinds = {n["kind"] for n in c["nodes"]}
        assert "masking_endpoint" in kinds, c["run_id"]
        ep = next(n["event_id"] for n in c["nodes"]
                  if n["kind"] == "masking_endpoint")
        assert any(e["target"] == ep and e["evidence_level"] in E.STRONG
                   for e in c["edges"]), c["run_id"]
        assert any(e["source"] == ep and e["evidence_level"] in E.STRONG
                   for e in c["edges"]), c["run_id"]
        if cls["application_symptom"] == "INTERMEDIATE_VALUE_DIVERGENCE":
            ivd += 1
            assert "first_software_divergence" in kinds, c["run_id"]
            out = next(n["event_id"] for n in c["nodes"]
                       if n["kind"] == "application_output")
            root = next(n["event_id"] for n in c["nodes"]
                        if n["kind"] == "injection")
            adj = collections.defaultdict(list)
            for e in c["edges"]:
                if e["evidence_level"] in E.STRONG:
                    adj[e["source"]].append(e["target"])
            assert E._reachable(adj, [root], ep), c["run_id"]
            assert E._reachable(adj, [ep], out), c["run_id"]
    assert masked == 57
    assert ivd == 20


# ---------------------------------------------------------------------------
# RP01 / squash
# ---------------------------------------------------------------------------
def test_rp01_watchdog_evidence(rp01):
    assert len(rp01) == 15
    for r in rp01:
        assert r["rp01_validation"]["valid"] is True, r["run_id"]
        checks = r["rp01_validation"]["checks"]
        assert checks["target_committed_fault"] is False, r["run_id"]
        assert checks["target_committed_control"] is True, r["run_id"]
        assert checks["chain_proved"] is True, r["run_id"]
        assert checks["no_progress_monotonic"] is True, r["run_id"]
        assert checks["target_at_rob_head_count"] >= 1, r["run_id"]
        assert r["classification"]["application_symptom"] == \
            "SIMULATOR_WATCHDOG", r["run_id"]
        assert r["classification"]["propagation_termination"] == \
            "SIMULATOR_STALL_WATCHDOG", r["run_id"]
    traces = sorted(P.stall_traces().glob("*.csv.gz"))
    assert len(traces) == 15
    for f in traces:
        with gzip.open(f, "rt") as fh:
            lines = [x for x in fh.read().splitlines()
                     if x and not x.startswith("#")]
        assert lines[-1].split(",")[1] == "WATCHDOG", f.name
        assert sum(1 for x in lines if ",PROBE," in x) >= 287, f.name
        assert sum(1 for x in lines if ",INJECTION," in x) == 1, f.name


def test_six_historical_squash_cells_are_separate():
    rows = _csv(SQUASH / "STRICT_E2E_SQUASH_AUDIT.csv")
    assert len(rows) == 6
    got = {(r["ModelID"], r["ContextID"], r["TimingID"]) for r in rows}
    assert got == SQUASH_IDS
    for r in rows:
        assert r["FaultCausedSquash"] == "0", r["OldRunID"]
        assert r["SquashCause"] == "unrelated", r["OldRunID"]
        assert r["Verdict"] == "VERIFIED", r["OldRunID"]
    # Never part of the 180 denominator: the new stream differs.
    new_ids = {r["NewRunID"] for r in rows}
    assert len(new_ids) == 6


# ---------------------------------------------------------------------------
# semantic evidence
# ---------------------------------------------------------------------------
def test_semantic_reconciliation_and_four_stp_events():
    sem = P.semantic()
    rows = _csv(sem / "SEMANTIC_MISMATCH_RECONCILIATION.csv")
    assert len(rows) == 6812
    old = collections.Counter(r["OldStatus"] for r in rows)
    assert old == {"MISMATCH": 6808, "UNSUPPORTED": 4}
    stp = [r for r in rows if r["OldStatus"] == "UNSUPPORTED"]
    assert len(stp) == 4
    assert all(r["Mnemonic"] == "stp" for r in stp)
    assert all(r["NewMethod"] == "pair_microop_identity" for r in stp)
    assert all(r["NewStatus"] == "MATCH" for r in stp)
    assert all(r["FinalOutcome"] == "RESOLVED_BY_CORRECT_SEMANTICS"
               for r in rows)
    # Each historical unsupported event is one half of a paired micro-op:
    # same RunID + PC, adjacent dynamic instruction sequences.
    groups = collections.defaultdict(list)
    for r in stp:
        groups[(r["RunID"], r["PC"])].append(int(r["DynInstSeq"]))
    assert len(groups) == 2
    for seqs in groups.values():
        assert len(seqs) == 2
        assert abs(seqs[0] - seqs[1]) == 1

    stats = json.loads((sem / "SEMANTIC_STATISTICS.json").read_text())
    assert stats["reval_rows"] == 1141566
    assert stats["flag_producers_verified"] == 490710
    assert stats["pair_checks"] >= 4
    for k in ("semantic_mismatches", "unsupported_critical",
              "unverified_semantic_edges", "flag_semantic_mismatches",
              "conditional_unverified", "memory_semantics_incomplete",
              "dropped_sources"):
        assert stats[k] == 0, k
    summary = _csv(sem / "SEMANTIC_REVALIDATION_SUMMARY_BY_RUN.csv")
    assert len(summary) == 180
    assert sum(int(r["RevalidationRows"]) for r in summary) == \
        stats["reval_rows"]
    assert sum(int(r["FlagProducersVerified"]) for r in summary) == \
        stats["flag_producers_verified"]
    assert {r["SemanticWalkStatus"] for r in summary} == {
        "EXECUTED", "NO_TAINTED_INSTRUCTION", "RP01_SEPARATE_TRACE"}


# ---------------------------------------------------------------------------
# evidence manifest
# ---------------------------------------------------------------------------
def test_package_evidence_manifest_hashes():
    man = _csv(REP / "FINAL_EVIDENCE_MANIFEST.csv")
    assert man
    pkg = [r for r in man if r["Scope"] == "PACKAGE"]
    assert pkg
    assert not [r for r in man
                if r["VerificationStatus"] == "MISSING_REQUIRED"]
    by_type = collections.Counter(r["FileType"] for r in pkg)
    assert by_type["causal_chain_json"] == 180
    assert by_type["rp01_chain"] == 15
    assert by_type["rp01_stall_trace"] == 15
    for r in pkg:
        p = ROOT / r["RelativePath"]
        assert p.exists(), (r["RunID"], r["RelativePath"])
        assert int(r["Size"]) == p.stat().st_size, r["RelativePath"]
        assert len(r["SHA256"]) == 64, r["RelativePath"]
        assert _sha(p) == r["SHA256"], r["RelativePath"]


@pytest.mark.skipif(
    os.environ.get("LSU_E2E_SERVER_EVIDENCE") != "1",
    reason="SERVER_EVIDENCE_REQUIRED: run on the original server workspace "
           "with LSU_E2E_SERVER_EVIDENCE=1")
def test_server_evidence_manifest_hashes():
    man = _csv(REP / "FINAL_EVIDENCE_MANIFEST.csv")
    srv = [r for r in man if r["Scope"] == "SERVER_WORKSPACE"]
    assert srv, "manifest has no server-scope rows"
    for r in srv:
        p = Path(r["AbsolutePath"])
        assert p.exists(), r["AbsolutePath"]
        assert int(r["Size"]) == p.stat().st_size, r["AbsolutePath"]
        assert _sha(p) == r["SHA256"], r["AbsolutePath"]


# ---------------------------------------------------------------------------
# report hygiene
# ---------------------------------------------------------------------------
def test_superseded_reports_are_marked_and_final_set_exists():
    required = [
        "FINAL_EXECUTIVE_REPORT.md", "FINAL_ROOT_CAUSE_MATRIX_180.csv",
        "FINAL_SOFTWARE_SYMPTOMS.csv", "FINAL_PROPAGATION_TERMINATION.csv",
        "FINAL_MODEL_STATISTICS.csv", "FINAL_CONTEXT_STATISTICS.csv",
        "FINAL_TIMING_STATISTICS.csv", "FINAL_EDGE_STATISTICS.csv",
        "FINAL_EVIDENCE_MANIFEST.csv", "FINAL_REGRESSION_REPORT.md",
        "FINAL_REPRODUCTION_GUIDE.md",
    ]
    for name in required:
        assert (REP / name).exists(), name
    sup = REP / "history" / "superseded"
    assert sup.is_dir()
    assert "SUPERSEDED" in (sup / "README.md").read_text()
    # The obsolete E2E report set is preserved there, not deleted.
    assert (sup / "E2E_Symptom_Statistics.csv").exists()
    assert (sup / "E2E_FS_Symptom_Report.md").exists()
