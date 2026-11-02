#!/usr/bin/env python3
"""Doc-audit controls: a clean doc passes, a tampered event id fails."""
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import r6_c_evidence as ev  # noqa: E402
import gen_r6_c_docs as g  # noqa: E402
import audit_r6_c_docs as a  # noqa: E402

CANARY = "/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/canary/C01-F0-W6_s1"
pytestmark = pytest.mark.skipif(
    not os.path.isdir(CANARY), reason="canary seed absent")


@pytest.fixture()
def doc_tree(tmp_path):
    old = g.STAGE
    g.STAGE = str(tmp_path / "stage")
    try:
        out, _size = g.generate(CANARY)
    finally:
        g.STAGE = old
    return os.path.dirname(out)


def test_clean_doc_has_zero_errors(doc_tree):
    assert a.audit_doc(os.path.join(doc_tree, "C01-F0-W6-seed1.md")) == []


def test_tampered_event_id_is_detected(doc_tree):
    src = os.path.join(doc_tree, "C01-F0-W6-seed1.md")
    dst = os.path.join(str(doc_tree), "tampered.md")
    txt = open(src).read().replace("| 0 | L0 | 0 |", "| 0 | L0 | 999999 |")
    open(dst, "w").write(txt)
    errs = a.audit_doc(dst)
    assert any("999999" in e for e in errs)
