#!/usr/bin/env python3
"""R6-C cache-family evidence reader + doc generator tests.

Uses the real canary seed as the fixture (skipped when it is absent), so the
tests cannot pass on synthetic data that the real stream does not have.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import r6_c_evidence as ev  # noqa: E402
import gen_r6_c_docs as g  # noqa: E402

CANARY = "/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/canary/C01-F0-W6_s1"

pytestmark = pytest.mark.skipif(
    not os.path.isdir(CANARY), reason="canary seed absent")


def test_load_sample_has_chain_and_stream():
    s = ev.load_sample(CANARY)
    assert s["chain"]["stream_present"] is True
    assert s["chain"]["event_count"] > 0
    assert s["manifest"]["binary_sha256"].startswith("6db026e7")
    assert os.path.isfile(s["paths"]["inj_log"])


def test_cache_family_layer_map_has_no_drift():
    # The authoritative table lives in lsu_prop_fields and is shared with
    # lsu_chain_check.  If that module is importable, the alias must be the
    # same mapping (one classifier, no drift).
    try:
        import lsu_prop_fields as p
    except Exception:
        pytest.skip("lsu_prop_fields unavailable")
    assert ev.KIND_LAYER["cache_access"] == p.KIND_LAYER["cache_access"] == "L1"
    assert ev.KIND_LAYER["cache_return"] == p.KIND_LAYER["cache_return"] == "L2"
    assert ev.KIND_LAYER["cache_writeback"] == p.KIND_LAYER["cache_writeback"] == "L3"


def test_layer_of_promotes_explicit_detection_and_excludes_lifecycle():
    assert ev.layer_of("chain_end", {"kind": "chain_end"}) == "—"
    assert ev.layer_of("errant_commit",
                       {"detection_layer": "L5", "outcome": "errant_commit"}) == "L5"
    assert ev.layer_of("cache_access", {"kind": "cache_access"}) == "L1"


def test_injection_log_joins_to_l0_event():
    s = ev.load_sample(CANARY)
    st = ev.load_streams(s)
    rows = st["inj"]
    assert len(rows) == 1
    inj = st["events"]["captured"]["0"]
    assert inj["kind"] == "inj"
    assert int(rows[0]["Cache Block Addr"], 10) == int(inj["va"], 16)
    assert rows[0]["Tick"] == inj["tick"]


def test_doc_contains_identity_path_and_honest_verdict(tmp_path):
    s = ev.load_sample(CANARY)
    old = g.STAGE
    g.STAGE = str(tmp_path)
    try:
        out, size = g.generate(CANARY)
    finally:
        g.STAGE = old
    md = open(out).read()
    assert s["chain"]["run_id"] in md
    assert s["manifest"]["binary_sha256"] in md
    assert "## 4. 传播过程" in md
    assert "| L1 |" in md and "`cache_access`" in md
    # Honest: the canary chain was not admitted; the doc must say so.
    assert "admitted | `False`" in md
    assert size > 5000
