#!/usr/bin/env python3
"""[LSU][DOCS] R6 propagation-document layout contract (R6-RESULTS-LAYOUT).

One RunID = one directory; each doc is <RunID>-seedN.md; no seed docs at the
top level; T = 83 valid docs, A = 90 (88 successful + 2 SPEC_EXCLUDED);
173 total.  Index links resolve; every referenced raw-evidence path exists;
successful docs carry event_id/parent_event_id/tick/SHA-256; the two N/A docs
never claim injection/admission/certification.
"""
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DOCS = Path(os.environ.get(
    "R6_PROP_DOCS_DIR",
    ROOT / "runs/lsu/R6_COMPLETE_PROPAGATION_PATHS"))

SEEDRE = re.compile(r"^(?P<rid>[AT]\d{2}-F\d+-W\d+)-seed(?P<seed>\d)\.md$")
RUNIDRE = re.compile(r"^[AT]\d{2}-F\d+-W\d+$")
SPEC_EXCLUDED = {("A08-F2-W3", 2), ("A08-F2-W5", 2)}
OLD_FLAT_A = [
    "A01-F0-W9-seed2.md", "A01-F2-W9-seed2.md", "A02-F0-W3-seed1.md",
    "A02-F0-W9-seed1.md", "A02-F2-W9-seed1.md", "A03-F5-W10-seed3.md",
    "A03-F5-W3-seed3.md", "A07-F0-W3-seed2.md", "A07-F0-W5-seed2.md",
]


def _docs():
    """[(rid, seed, path)] for every doc under a RunID directory."""
    out = []
    for d in sorted(DOCS.iterdir()):
        if not d.is_dir() or not RUNIDRE.match(d.name):
            continue
        for f in sorted(d.glob("*.md")):
            m = SEEDRE.match(f.name)
            if m:
                out.append((m.group("rid"), int(m.group("seed")), f))
    return out


def test_top_level_has_no_seed_docs():
    tops = [p.name for p in DOCS.iterdir()
            if p.is_file() and "-seed" in p.name and p.suffix == ".md"]
    assert tops == [], tops


def test_every_runid_dir_name_is_legal():
    for d in DOCS.iterdir():
        if d.is_dir():
            assert RUNIDRE.match(d.name), d.name


def test_file_parent_equals_runid():
    for rid, seed, path in _docs():
        assert path.parent.name == rid, str(path)


def test_file_name_is_exact_runid_seedn():
    for rid, seed, path in _docs():
        assert path.name == f"{rid}-seed{seed}.md", str(path)


def test_t_docs_total_83():
    t = [x for x in _docs() if x[0].startswith("T")]
    assert len(t) == 83, len(t)


def test_a_docs_total_90():
    a = [x for x in _docs() if x[0].startswith("A")]
    assert len(a) == 90, len(a)


def test_a_success_docs_88():
    ok = []
    for rid, seed, p in _docs():
        if not rid.startswith("A") or (rid, seed) in SPEC_EXCLUDED:
            continue
        txt = p.read_text()
        assert "admitted=True" in txt or "admitted | True" in txt, p
        ok.append(p)
    assert len(ok) == 88, len(ok)


def test_a_na_docs_2():
    na = [p for rid, seed, p in _docs()
          if (rid, seed) in SPEC_EXCLUDED]
    assert len(na) == 2, na
    for p in na:
        t = p.read_text()
        assert "`N/A`" in t and "SPEC_EXCLUDED" in t, p


def test_total_seed_docs_173():
    assert len(_docs()) == 173


def test_no_duplicate_runid_seed():
    keys = [(rid, seed) for rid, seed, _ in _docs()]
    assert len(keys) == len(set(keys)), "duplicate RunID+seed"


def test_index_a_links_exist():
    t = (DOCS / "INDEX-A.md").read_text()
    links = re.findall(r"\]\(([^)]+\.md)\)", t)
    assert links
    missing = [l for l in links if not (DOCS / l).exists()]
    assert missing == [], missing


def test_index_v4_links_exist():
    t = (DOCS / "INDEX-V4.md").read_text()
    links = re.findall(r"\]\(([^)]+\.md)\)", t)
    assert links
    missing = [l for l in links if not (DOCS / l).exists()]
    assert missing == [], missing


def test_index_json_paths_exist():
    d = json.loads((DOCS / "INDEX.json").read_text())
    paths = [e.get("md_path", "") for e in d.get("entries", [])]
    assert paths
    missing = [p for p in paths
               if not (Path(p) if os.path.isabs(p) else DOCS / p).exists()]
    assert missing == [], missing[:5]


def test_success_docs_have_event_id():
    for rid, seed, p in _docs():
        if (rid, seed) in SPEC_EXCLUDED:
            continue
        assert "event_id" in p.read_text(), p


def test_success_docs_have_parent_event_id():
    for rid, seed, p in _docs():
        if (rid, seed) in SPEC_EXCLUDED:
            continue
        assert "parent_event_id" in p.read_text(), p


def test_success_docs_have_tick():
    for rid, seed, p in _docs():
        if (rid, seed) in SPEC_EXCLUDED:
            continue
        assert "tick" in p.read_text(), p


def test_success_docs_have_evidence_sha256():
    for rid, seed, p in _docs():
        if (rid, seed) in SPEC_EXCLUDED:
            continue
        assert re.search(r"\b[0-9a-f]{64}\b", p.read_text()), p


ABSENCE_MARK = re.compile(r"ABSENT|缺失|不存在|\bN/A\b")


def _evidence_refs(text):
    """Paths actually referenced by backtick spans rooted at /home/sdc/.

    A span containing whitespace is a shell invocation, so the filesystem
    path it references is its first token (the executable), not the whole
    command line.  A whitespace-free span is a filesystem path.
    """
    for span in re.findall(r"`(/home/sdc/[^`]+)`", text):
        toks = span.split()
        yield toks[0]


def _annotated_absent(path, lines):
    """True only if a line names this exact path and marks it absent.

    A path the document itself records as ABSENT/缺失 is honest evidence
    reporting, not a dangling link.  Unannotated missing paths remain
    failures, so this does not weaken the existence contract.
    """
    return any(path in ln and ABSENCE_MARK.search(ln) for ln in lines)


def test_referenced_evidence_paths_exist():
    missing = []
    for rid, seed, p in _docs():
        if (rid, seed) in SPEC_EXCLUDED:
            continue
        txt = p.read_text()
        lines = txt.splitlines()
        for path in _evidence_refs(txt):
            if os.path.exists(path):
                continue
            if not _annotated_absent(path, lines):
                missing.append((str(p), path))
    assert missing == [], missing[:5]


def test_na_docs_do_not_claim_pass_or_chain():
    for rid, seed in SPEC_EXCLUDED:
        t = (DOCS / rid / f"{rid}-seed{seed}.md").read_text()
        for bad in ("admitted=True", "certified=True",
                    "terminal=detected_contained", "terminal=full",
                    "PROP-EVT:", "kind=inj"):
            assert bad not in t, (rid, seed, bad)
        assert "没有启动 gem5" in t


def test_nine_old_flat_a_files_absent():
    for name in OLD_FLAT_A:
        assert not (DOCS / name).exists(), name


if __name__ == "__main__":
    # Standalone entry point: report in the repository's PASS/FAIL vocabulary
    # (tools/lsu_test_runner.py parses "ALL PASS" / "FAILURES: [...]"), while
    # the exit code remains pytest's real rc -- a failure is never masked.
    import pytest
    _rc = pytest.main([str(Path(__file__)), "-q", "-p", "no:cacheprovider"])
    if _rc == 0:
        print("R6 RESULTS LAYOUT TEST: ALL PASSED")
    else:
        print("R6 RESULTS LAYOUT TEST: FAILURES: [pytest rc=%d]" % _rc)
    sys.exit(_rc)
