#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A4] A 单元收口一致性测试（用户裁决 2026-10-29）。

权威口径（必须同时出现在 STATUS.json / STATUS.md / INDEX-A.md /
FINAL-REPORT.md）：

    applicable_samples=88
    qualified_applicable_samples=88
    spec_excluded_samples=2
    failed_applicable_samples=0
    unit_status=COMPLETE_WITH_SPEC_EXCLUSIONS

两个 SPEC_EXCLUDED 样本（A08-F2-W3 seed2 / A08-F2-W5 seed2）必须是
`status=N/A`、`classification=SPEC_EXCLUDED`、
`reason=A08-b structurally unreachable under F2`；不是 PASS、不是 FAIL，
admitted/certified 为空，无传播链，不计入 88 的分母。

本测试只读状态/索引/报告/证据，不改任何原始事件流。
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPORTS = ROOT / "runs/lsu/r6_reports"
DOCS = ROOT / "runs/lsu/R6_COMPLETE_PROPAGATION_PATHS"
EVIDENCE_ROOT = Path("/home/sdc/gem5-fi-ding/runs/lsu")

RUNIDS = """A01-F0-W3 A01-F0-W9 A01-F1-W3 A01-F1-W9 A01-F2-W3 A01-F2-W9
A02-F0-W3 A02-F0-W9 A02-F2-W3 A02-F2-W9
A03-F5-W3 A03-F5-W10
A04-F0-W3 A04-F0-W0 A04-F2-W3 A04-F2-W0
A05-F0-W3 A05-F2-W3
A06-F0-W3 A06-F0-W5 A06-F2-W3 A06-F2-W5
A07-F0-W3 A07-F0-W5 A07-F4-W3 A07-F4-W5
A08-F0-W3 A08-F0-W5 A08-F2-W3 A08-F2-W5""".split()

SPEC_EXCLUDED = {("A08-F2-W3", 2), ("A08-F2-W5", 2)}
CANON = ("88/88 applicable samples qualified; 2/2 structurally inapplicable "
         "samples explicitly excluded; 0 applicable failures; A unit closed "
         "as COMPLETE_WITH_SPEC_EXCLUSIONS.")


def _status():
    return json.loads((REPORTS / "R6-A4-STATUS.json").read_text())


def _text(name):
    return (REPORTS / name).read_text()


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_counts_consistent_across_documents():
    s = _status()
    assert s["applicable_samples"] == 88
    assert s["qualified_applicable_samples"] == 88
    assert s["spec_excluded_samples"] == 2
    assert s["failed_applicable_samples"] == 0
    assert s["not_run_applicable_samples"] == 0
    assert s["unit_status"] == "COMPLETE_WITH_SPEC_EXCLUSIONS"
    assert s["target_samples"] == 90
    assert s["canonical_conclusion"] == CANON

    md = _text("R6-A4-STATUS.md")
    idx = (DOCS / "INDEX-A.md").read_text()
    fin = _text("R6-A4-FINAL-REPORT.md")
    for field in ("applicable_samples=88", "qualified_applicable_samples=88",
                  "spec_excluded_samples=2", "failed_applicable_samples=0",
                  "unit_status=COMPLETE_WITH_SPEC_EXCLUSIONS"):
        assert field in md, field
    assert "88/88 applicable samples qualified" in md
    assert "88/88 applicable samples qualified" in idx
    assert "88/88 applicable samples qualified" in fin
    assert "unit_status=COMPLETE_WITH_SPEC_EXCLUSIONS" in idx
    assert "unit_status=COMPLETE_WITH_SPEC_EXCLUSIONS" in fin
    # The old "88/90" framing must be gone; the only allowed mention of
    # 90/90 is the explicit negation ("不把结果写成 90/90 PASS").
    assert "88/90" not in fin
    assert "90/90 合格" not in fin
    assert "A 单元 90/90" not in fin


def test_applicable_plus_spec_is_90_and_qualified_identity():
    s = _status()
    rows = s["samples"]
    assert len(rows) == 90
    spec = [r for r in rows if r["classification"] == "SPEC_EXCLUDED"]
    applicable = [r for r in rows if r["classification"] != "SPEC_EXCLUDED"]
    assert len(applicable) == s["applicable_samples"] == 88
    assert len(spec) == s["spec_excluded_samples"] == 2
    assert len(applicable) + len(spec) == 90
    assert sum(1 for r in applicable if r["qualified"]) == 88
    assert sum(1 for r in applicable if r["status"] == "FAIL") == 0
    assert {r["runid"] for r in spec} == {"A08-F2-W3", "A08-F2-W5"}
    assert {r["seed"] for r in spec} == {2}


def test_na_rows_are_not_pass_admitted_certified_or_chained():
    s = _status()
    for r in s["samples"]:
        if r["classification"] != "SPEC_EXCLUDED":
            continue
        assert r["status"] == "N/A"
        assert r["reason"] == "A08-b structurally unreachable under F2"
        assert r["qualified"] is False
        assert not r["admitted"]
        assert not r["certified"]
        assert r["terminal"] in (None, "")
        assert r["events"] in (None, "")
        # No sample/stream means no propagation chain was generated: the
        # campaign may have written an EMPTY chain_report (samples == []), but
        # there is no sample record and no event stream.
        cr = Path(r["outdir"]) / r["runid"] / "chain_report.json"
        if cr.exists():
            assert json.loads(cr.read_text()).get("samples") == [], cr
        stream = (Path(r["outdir"]) / r["runid"] / ("seed%d" % r["seed"])
                  / "prop_evt.txt.gz")
        assert not stream.exists()


def test_na_evidence_recorded_in_json():
    s = _status()
    ex = {(e["run_id"], e["seed"]): e for e in s["spec_exclusions"]}
    assert set(ex) == SPEC_EXCLUDED
    for key, e in ex.items():
        assert e["status"] == "N/A"
        assert e["classification"] == "SPEC_EXCLUDED"
        assert e["reason"] == "A08-b structurally unreachable under F2"
        assert e["admitted"] is None and e["certified"] is None
        assert e["terminal"] is None
        assert e["generated_propagation_chain"] is False
        ev = e["evidence"]
        assert ev["eligible_repeat_1_5_10"] == 21
        assert ev["repeat_delta"] == 0
        assert ev["first_fire_seed2_eligible_ordinal"] == 99417


def test_na_docs_do_not_claim_injection_or_chain():
    for rid, seed in SPEC_EXCLUDED:
        doc = (DOCS / rid / ("%s-seed%d.md" % (rid, seed))).read_text()
        assert "status | `N/A`" in doc
        assert "classification | `SPEC_EXCLUDED`" in doc
        assert "A08-b structurally unreachable under F2" in doc
        assert "E1=E5=E10=**21**" in doc
        assert "delta=**0**" in doc
        assert "99,417" in doc
        assert "不是 PASS" in doc and "不是 FAIL" in doc
        assert "没有启动 gem5" in doc
        # Forbidden: claiming a real injection / terminal / admission.
        for bad in ("admitted=True", "certified=True",
                    "terminal=detected_contained", "terminal=full",
                    "PROP-EVT:", "kind=inj"):
            assert bad not in doc, (rid, seed, bad)


def test_all_30_runids_have_final_state():
    s = _status()
    assert list(s["runids"]) == RUNIDS
    for rid in RUNIDS:
        rec = s["runids"][rid]
        assert set(rec["seeds"]) == {"1", "2", "3"}, rid
        for st in rec["seeds"].values():
            assert st in ("qualified", "N/A", "unqualified", "not_run"), (rid, st)
        assert rec["qualified"] + rec["spec_excluded"] == rec["applicable"] or \
            rec["qualified"] == rec["applicable"], rid
        assert rec["applicable"] + rec["spec_excluded"] == 3, rid
    # The two A08 rows: applicable=2, qualified=2.
    for rid in ("A08-F2-W3", "A08-F2-W5"):
        assert s["runids"][rid]["applicable"] == 2
        assert s["runids"][rid]["qualified"] == 2
        assert s["runids"][rid]["seeds"]["2"] == "N/A"


def test_f6_policy_exclusion_is_separate():
    s = _status()
    assert "f6_policy_excluded" in s
    assert "SEPARATE" in s["f6_policy_excluded"]["note"]
    # No F6 RunID sneaks into the 30-runid A table.
    assert not [r for r in RUNIDS if "-F6-" in r]
    assert all("F6" not in rid for rid in s["runids"])


def test_qualified_docs_evidence_paths_and_sha_unchanged():
    s = _status()
    n_docs = 0
    n_rows = 0
    for r in s["samples"]:
        if r["classification"] == "SPEC_EXCLUDED":
            continue
        assert r["qualified"] is True, (r["runid"], r["seed"])
        doc = DOCS / r["runid"] / ("%s-seed%d.md" % (r["runid"], r["seed"]))
        assert doc.exists(), doc
        n_docs += 1
        rows = re.findall(
            r"^\| ([A-Za-z0-9_.-]+) \| `([^`]+)` \| `([0-9a-f]{64})` \|$",
            doc.read_text(), re.M)
        assert rows, ("no evidence table", doc)
        for _name, path, sha in rows:
            n_rows += 1
            p = Path(path)
            assert p.exists(), (doc, path)
            assert _sha(p) == sha, (doc, path)
    assert n_docs == 88
    assert n_rows >= 88 * 5


def test_na_original_blocked_evidence_preserved():
    for rid, seed in SPEC_EXCLUDED:
        d = EVIDENCE_ROOT / ("r6_a_r6a4_%s_s%d" % (rid, seed))
        assert (d / "manifest.json").exists()
        assert (d / ".done").exists()
        assert (d / rid / "cell_results.json").exists()
        cr = json.loads((d / rid / "cell_results.json").read_text())
        assert cr["runs"][0]["outcome"] == "Blocked"
        assert cr["runs"][0]["activated"] == 0


def test_no_na_counted_in_index_or_final():
    idx = (DOCS / "INDEX-A.md").read_text()
    fin = _text("R6-A4-FINAL-REPORT.md")
    for rid in ("A08-F2-W3", "A08-F2-W5"):
        line = next(l for l in idx.splitlines() if l.startswith("| " + rid))
        assert "N/A (SPEC_EXCLUDED)" in line
        assert line.count("✅") == 2, line
    # The final report table marks seed2 as N/A and never as PASS.
    for line in fin.splitlines():
        if line.startswith("| A08-F2-W3 |") or line.startswith("| A08-F2-W5 |"):
            if "PASS" in line or "N/A" in line:
                assert "N/A (SPEC_EXCLUDED)" in line
                assert "| N/A (SPEC_EXCLUDED) |" in line


if __name__ == "__main__":
    sys.exit(pytest.main([str(Path(__file__)), "-q",
                          "-p", "no:cacheprovider"]))
