"""Unit tests for the LSU comparison normalisation.

The comparison divides by the ROI instruction count calibrated from ``N`` and
``N-1`` runs, not by ``sad.issuedOps``: that counter includes issue-path
re-selections, so an ``ldxr`` stream reports 27.5k "issued" for 3.9k retired
instructions.  These tests pin the denominator arithmetic, the retry flag and
the SAD ratios.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lsu_compare  # noqa: E402


def raw_dump(issued=1000.0, **overrides):
    data = {name: 0.0 for name in lsu_compare.EXACT}
    data.update({
        "roi_issued": issued,
        "cycles": 2000.0,
        "ipc": 0.5,
        "sad_samples": 2000.0,
        "l1d_reads": 500.0,
        "l1d_writes": 250.0,
        "l1d_hits": 700.0,
        "l1d_misses": 50.0,
        "l1d_fills": 40.0,
        "rf_int_reads": 900.0,
        "rf_int_writes": 100.0,
    })
    for cls in lsu_compare.IBR_CLASSES:
        data[f"ibr_bits_{cls}"] = 0.0
        data[f"ibr_issued_{cls}"] = 0.0
        data[f"ibr_ratio_{cls}"] = 0.0
    for res in lsu_compare.SAD_RESOURCES:
        data[f"sad_used_{res}"] = 0.0
        data[f"sad_cap_{res}"] = 1.0
    data["sad_used_lq"] = 48.0 * 1000.0
    data["sad_cap_lq"] = 48.0
    data.update(overrides)
    return data


def test_denominator_is_calibrated_roi_count():
    derived = lsu_compare.derive(raw_dump(), 1000.0)
    assert derived["lsu_ops_per_1k"] == 750.0
    assert derived["l1d_reads_per_1k"] == 500.0
    assert derived["l1d_writes_per_1k"] == 250.0


def test_issue_retry_inflation_is_visible_but_not_used():
    inflated = lsu_compare.derive(raw_dump(issued=7000.0), 1000.0)
    assert inflated["issued_per_commit"] == 7.0
    assert inflated["lsu_ops_per_1k"] == 750.0

    clean = lsu_compare.derive(raw_dump(issued=1010.0), 1000.0)
    assert clean["issued_per_commit"] == 1.01


def test_cache_sad_and_commit_ratios():
    derived = lsu_compare.derive(raw_dump(), 1000.0)
    assert derived["l1d_miss_rate"] == 50.0 / 750.0
    assert derived["l1d_mpki"] == 50.0
    assert derived["sad_lq"] == 48.0 * 1000.0 / (2000.0 * 48.0)
    assert derived["commit_per_cycle"] == 0.5


def test_zero_roi_count_is_rejected():
    try:
        lsu_compare.derive(raw_dump(), 0.0)
    except SystemExit as error:
        assert "positive" in str(error)
    else:
        raise AssertionError("derive() accepted a zero ROI count")
