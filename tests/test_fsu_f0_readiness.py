"""tests/test_fsu_f0_readiness.py — F0 readiness ordering consistency test.

This test is STRICTLY read-only and does NOT run gem5. It verifies:

  [1] `docs/gem5-fi/fsu/F0-READINESS-ORDER.md` covers exactly the active F0
      RunIDs that are still incomplete according to the source registry
      (`runids.json`, 72 F0 RunIDs) and the implementation matrix
      (`IMPLEMENTATION_MATRIX.json`, seed_completion_count == 0);
  [2] the machine-readable block embedded in the document agrees with the
      registry/matrix identity fields and the ranking is well formed;
  [3] the recommended top-3 pilot candidates exist, are distinct model
      families, and are inside the high-readiness set;
  [4] the four known-defect verdicts recorded in the document agree with the
      real code evidence (literal source patterns), so a stale or fabricated
      verdict fails this test;
  [5] the document names the recommended next pilot and a real (non-formal)
      minimal verification command.

The document parser uses the explicit markers
`<!-- F0_READINESS_JSON_BEGIN -->` / `<!-- F0_READINESS_JSON_END -->`.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/gem5-fi/fsu/F0-READINESS-ORDER.md"
REGISTRY = ROOT / "docs/gem5-fi/fsu/runids.json"
MATRIX = ROOT / "docs/gem5-fi/fsu/IMPLEMENTATION_MATRIX.json"

DONE_F0 = {
    "FSU-FP04-F0-W1",
    "FSU-FP04-F0-W3",
    "FSU-FP04-F0-W4",
    "FSU-FP04-F0-W5",
    "FSU-FP04-F0-W6",
    "FSU-FR07-F0-W1",   # real PRF-WB hook v2 certification
}

TIER_MIN = {"T1": 7.0, "T2": 5.0, "T3": 3.0, "T4": 1.0, "T5": -999.0}


def _doc_payload():
    assert DOC.is_file(), f"missing readiness document: {DOC}"
    text = DOC.read_text(encoding="utf-8")
    m = re.search(
        r"<!-- F0_READINESS_JSON_BEGIN -->\s*(\{.*?\})\s*"
        r"<!-- F0_READINESS_JSON_END -->",
        text, re.S)
    assert m is not None, "readiness JSON block markers not found"
    return json.loads(m.group(1)), text


def _registry_f0():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {r["RunID"]: r for r in reg["runids"] if r["频率"] == "F0"}


def _matrix():
    mat = json.loads(MATRIX.read_text(encoding="utf-8"))
    return {r["runid"]: r for r in mat["runids"]}


def _code(path):
    p = ROOT / path
    assert p.is_file(), path
    return p.read_text(encoding="utf-8", errors="replace")


def test_doc_covers_exactly_remaining_f0():
    payload, _ = _doc_payload()
    f0 = _registry_f0()
    matrix = _matrix()

    assert payload["schema"] == "fsu-f0-readiness-v1"
    assert payload["active_frequency"] == "F0"
    assert payload["source_registry_count"] == 173
    assert payload["f0_total"] == len(f0) == 72

    completed = {rid for rid, r in f0.items()
                 if int(matrix[rid].get("seed_completion_count", 0)) > 0}
    assert completed == DONE_F0, sorted(completed ^ DONE_F0)
    assert set(payload["completed_f0"]) == DONE_F0

    remaining = set(f0) - completed
    assert len(remaining) == 66
    row_ids = [r["runid"] for r in payload["rows"]]
    assert len(row_ids) == len(set(row_ids)) == 66
    assert set(row_ids) == remaining
    assert payload["remaining_f0_count"] == 66


def test_rows_agree_with_registry_and_matrix_identity():
    payload, _ = _doc_payload()
    f0 = _registry_f0()
    matrix = _matrix()
    for row in payload["rows"]:
        rid = row["runid"]
        assert rid in f0 and rid in matrix
        assert row["model_id"] == f0[rid]["模型ID"] == matrix[rid]["model_id"]
        assert row["load_id"] == f0[rid]["负载ID"] == matrix[rid]["load_id"]
        assert matrix[rid].get("freq") == "F0"
        assert int(matrix[rid].get("seed_completion_count", 0)) == 0


def test_ranking_is_well_formed_and_monotone():
    payload, _ = _doc_payload()
    rows = payload["rows"]
    assert [r["rank"] for r in rows] == list(range(1, len(rows) + 1))
    scores = [float(r["score"]) for r in rows]
    assert scores == sorted(scores, reverse=True), "scores must be non-increasing"
    for r in rows:
        assert r["tier"] in TIER_MIN
        assert float(r["score"]) >= TIER_MIN[r["tier"]]
        assert r["injector"] in {"exact", "partial", "proxy", "wrong", "none"}
        assert r["chain"] in {"full", "partial", "none"}
        assert r["workload"] in {"real", "partial", "none"}
        assert r["cost"] in {"S", "M", "L"}
        assert r["risk"] in {"low", "medium", "high"}
        assert r["gap"].strip()


def test_top3_candidates_exist_and_are_distinct_families():
    payload, _ = _doc_payload()
    by_id = {r["runid"]: r for r in payload["rows"]}
    top3 = payload["recommended_top3_distinct"]
    assert len(top3) == 3
    assert len(set(top3)) == 3
    assert len({by_id[r]["model_id"] for r in top3}) == 3, \
        "top-3 recommendation must be three distinct model families"
    for rid in top3:
        assert rid in by_id, rid
        assert float(by_id[rid]["score"]) >= 7.0
        assert by_id[rid]["injector"] in {"exact", "partial", "proxy"}
    # The first recommended candidate is the highest-scoring single RunID.
    assert top3[0] == payload["rows"][0]["runid"]


def test_known_defect_verdicts_match_code_evidence():
    payload, text = _doc_payload()
    defects = payload["defects"]
    expected = {
        "FQ08-b": "fixed_pending_gem5_gate",
        "PRF-identity-generation": "partial",
        "FP08-suppressed_count": "fixed_pending_gem5_gate",
        "FQ08-c": "fixed_pending_gem5_gate",
    }
    assert set(defects) == set(expected)
    for key, verdict in expected.items():
        assert defects[key]["verdict"] == verdict, (key, defects[key]["verdict"])
        # Every code citation in the document must really exist, so a claim
        # cannot be supported by a file/pattern that was never there.
        ev = defects[key]["evidence"]
        assert ev, key
        for item in ev:
            src = _code(item["file"])
            needle = item["pattern"]
            assert needle in src, (
                f"{key}: evidence pattern not found in {item['file']}: "
                f"{needle!r}")
    # The prose must name all four defects.
    for key in expected:
        assert key in text


def test_fq08b_counts_only_after_real_victim():
    """FQ08-b fix: the gate only records an attempt; the injection counter and
    maxFaults budget move to the real victim application (noteTagWake)."""
    iq = _code("CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.cc")
    m = re.search(r"CHAOSIQ::shouldWrongSourceWake\((.*?)\n    \}\n", iq, re.S)
    assert m, "shouldWrongSourceWake body not found"
    body = m.group(1)
    # The old defect shape must be gone.
    assert "faults_injected_count++" not in body
    assert "return true" not in body
    assert "attempted" in body
    # Real application lives in noteTagWake / its lifecycle helper and is
    # gated on a victim; the attempt-only gate never counts an injection.
    assert iq.find("CHAOSIQ::noteTagWake") != -1
    assert "iq_counts.applied++" in iq
    assert "no_victim" in iq
    # The lifecycle model keeps attempted/eligible/applied/activated separate.
    life = _code("CHAOS/gem5/src/cpu/o3/CHAOSIQ/chaos_iq_lifecycle.hh")
    for field in ("attempted", "eligible", "applied", "activated", "no_victim"):
        assert field in life


def test_prf_generation_evidence_is_pinned():
    """FR03: permanent key = class+index; generation only provenance.
    Non-FR03: vec bit_flip never arms/emits the FR03 chain; FR02's random
    2-bit mask can collapse because generateRandomMask may draw a bit twice.
    """
    rf = _code("CHAOS/gem5/src/cpu/o3/regfile.hh")
    assert "vec_stuck.matches((int)p->classValue(), (int)p->index())" in rf
    assert "++flat_generation[flat];" in rf
    assert "++vec_stuck_reads;" in rf

    phys = _code("CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc")
    # Only the StuckAtZero / StuckAtOne vec branches arm the permanent cell.
    assert phys.count("armVecStuck(") == 2
    assert "if (vec_stuck_armed)" in phys
    assert "case FaultType::BitFlip:" in phys
    # Random mask may repeat a bit => fewer set bits than requested.
    assert "while (bits_to_change-- > 0) mask |= (1ULL << bitDist(gen));" in phys
    # arch_* modes resolve a phys id by rename/commit lookup at attack time.
    assert "commitRenameMapAccess()[tid].lookup(flat)" in phys
    assert "frontRenameMap()[tid].lookup(flat)" in phys


def test_fp08_suppressed_count_is_emitted_with_conservation():
    hh = _code("CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.hh")
    cc = _code("CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc")
    for field in ("fpsr_attempted", "fpsr_applied", "suppressed_count",
                  "rounding_attempted", "rounding_applied"):
        assert field in hh
    assert "CHAOS_FPSR_ATTEMPTED=" in cc
    assert "CHAOS_FPSR_APPLIED=" in cc
    assert "CHAOS_FPSR_SUPPRESSED=" in cc
    assert "CHAOS_ROUNDING_APPLIED=" in cc
    assert "fpsr_suppress_proxy" in cc
    assert "rounding_sub_one_ulp_proxy" in cc
    # The rounding early-return path must reach the real L0 emitter.
    rnd = cc[cc.find("if (rounding_sub) {"):cc.find("chaos_fsu::MaskInfo mi;")]
    assert "noteFaultApplied(dyn_inst, fi);" in rnd
    runner = _code("tools/fsu_seed_runner.py")
    assert "fpu_fpsr_suppress" in runner


def test_fq08c_delayed_wake_is_squash_and_generation_aware():
    """FQ08-c fix: CHAOSIQ's own DelayedWake validates squash/generation/
    identity before re-waking; the unsafe inst_queue event is unreachable."""
    life = _code("CHAOS/gem5/src/cpu/o3/CHAOSIQ/chaos_iq_lifecycle.hh")
    for decision in ("IgnoreSquashed", "IgnoreGeneration", "IgnoreIdentity",
                     "IgnoreNoInst"):
        assert decision in life
    iq = _code("CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.cc")
    assert "CHAOSIQ::DelayedWake::process()" in iq
    assert "IGNORED reason=" in iq
    assert "wakeDecisionName" in iq
    assert "delayed_ignored_squashed" in iq
    assert "delayed_scheduled" in iq
    # wake_phase no longer schedules the legacy o3 DelayedWakeEvent.
    assert "cpu->schedule(new DelayedWakeEvent" not in iq
    assert "shouldDelayWake" in iq


def test_document_names_next_pilot_and_real_command():
    payload, text = _doc_payload()
    assert payload["next_pilot"] == "FSU-FR07-F0-W3"
    assert payload["next_pilot"] in text
    cmd = payload["minimal_verification_command"]
    assert "tools/fsu_seed_runner.py" in cmd
    assert "--out-root" in cmd
    assert "/tmp" in cmd
    assert "runs/fsu" not in cmd.split("--out-root")[1].split()[0]
