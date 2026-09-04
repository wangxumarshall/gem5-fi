import os, sys, csv, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

def _mk_l1d(path, tag, prot, bits, cls):
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["tag","protection","bits","classification","faults"])
        w.writerow([tag, prot, bits, cls, 1])

def test_mechanism_A_for_unprotected_SDC():
    from escape_decomp import classify_escape_mechanism as c
    assert c("prf", "none", 1, "SDC") == "A"
    assert c("rat", "none", 1, "SDC") == "A"
    assert c("prf-readtrace-formal", "none", 1, "Latent") == "A"

def test_mechanism_C_for_3bit_beyond_secded():
    from escape_decomp import classify_escape_mechanism as c
    assert c("l1d", "secded", 3, "SDC") == "C"
    assert c("l1d", "secded", 3, "Latent") == "C"

def test_non_SDC_is_not_escape():
    from escape_decomp import classify_escape_mechanism as c
    assert c("l1d", "secded", 1, "Corrected") == "None"
    assert c("prf", "none", 1, "Crash") == "None"
    assert c("l1d", "secded", 2, "DetectedContained") == "None"
    assert c("l1d", "none", 1, "Masked") == "None"

def test_decompose_counts_by_mechanism():
    from escape_decomp import decompose
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "raw-b3.csv")
        _mk_l1d(p, "raw-b3", "secded", 3, "SDC")    # C
        _mk_l1d(p, "raw-b3", "secded", 3, "SDC")    # C
        p2 = os.path.join(d, "raw-b1.csv")
        _mk_l1d(p2, "raw-b1", "none", 1, "Masked")  # 非逃逸
        dec = decompose(l1d_dir=d, campaigns=[])
        assert dec["C"]["count"] == 2
        assert dec["A"]["count"] == 0

def test_decompose_from_campaign_cells():
    from escape_decomp import decompose
    with tempfile.TemporaryDirectory() as d:
        camp = os.path.join(d, "prf-formal")
        os.makedirs(camp)
        with open(os.path.join(camp, "cells.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["SDC","Crash","Hang","Inactive","Masked","SimulatorError","Latent"])
            w.writerow([10, 2, 1, 0, 5, 0, 0])
        dec = decompose(l1d_dir=None, campaigns=[camp])
        assert dec["A"]["count"] == 10   # prf none SDC → A

def test_render_markdown_contains_rows():
    from escape_decomp import render_markdown
    md = render_markdown({"A": {"count": 10, "share": 0.5, "sources": "prf-formal"},
                          "B": {"count": 0, "share": 0.0, "sources": ""},
                          "C": {"count": 10, "share": 0.5, "sources": "l1d-ecc"},
                          "D": {"count": 0, "share": 0.0, "sources": ""},
                          "E": {"count": 0, "share": 0.0, "sources": ""},
                          "F": {"count": 0, "share": 0.0, "sources": ""}})
    assert "| A |" in md and "| C |" in md
    assert "no data" in md   # B/D/E/F 无数据行如实标注
