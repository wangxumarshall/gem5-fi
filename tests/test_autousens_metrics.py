"""Unit tests for the ACE/IBR/SAD metric layer (plan unit 2).

The module is loaded by path because ``tools/autousens.py`` (the CLI) and the
``experiments/autousens`` package share the module name ``autousens``.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_metrics():
    path = ROOT / "experiments" / "autousens" / "metrics.py"
    spec = importlib.util.spec_from_file_location("autousens_metrics_ut", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


metrics = _load_metrics()

CORE = "board.processor.cores.core."
L1D = "board.cache_hierarchy.l1d-cache-0.l1Ace."
L1I = "board.cache_hierarchy.l1i-cache-0.l1Ace."


def synthetic_stats(window=100.0):
    """Build a dump that contains every counter the layer requires."""

    stats = {}
    for name in metrics.ACE_RF_SCALARS:
        value = window if name == "measuredCycles" else 1.0
        stats[CORE + "rfAce." + name] = value
    for cache, prefix in (("l1d", L1D), ("l1i", L1I)):
        for name in metrics.ACE_CACHE_SCALARS:
            value = window if name == "measuredCycles" else 1.0
            stats[prefix + name] = value
    for fu in metrics.IBR_CLASSES:
        for name in metrics.IBR_PER_CLASS:
            value = window if name == "issuedOps" else 1.0
            stats[CORE + f"fuIbr.{name}::{fu}"] = value
    for name in metrics.IBR_GLOBALS:
        value = window if name == "measuredCycles" else 1.0
        stats[CORE + "fuIbr." + name] = value
    for name in metrics.SAD_GLOBALS:
        if name == "samples":
            stats[CORE + "sad." + name] = window
        elif name == "issueRatio":
            stats[CORE + "sad." + name] = 0.5
        else:
            stats[CORE + "sad." + name] = 1.0
    for resource in metrics.SAD_RESOURCES:
        for name in metrics.SAD_PER_RESOURCE:
            stats[CORE + f"sad.{name}::{resource}"] = 1.0
    return stats


def test_extract_covers_all_three_families():
    document = metrics.extract(synthetic_stats())
    assert set(document) >= {"windows", "window_consistent", "ace", "ibr", "sad"}
    assert document["ace"]["rf"]["intTrackedReads"] == 1.0
    assert document["ace"]["caches"]["l1d"]["aceRatio"] == 1.0
    assert document["ibr"]["classes"]["intAlu"]["ibrRatio"] == 1.0
    assert document["sad"]["resources"]["rob"]["ratio"] == 1.0
    assert document["sad"]["globals"]["issueRatio"] == 0.5


def test_window_consistency_is_checked_across_families():
    stats = synthetic_stats(window=100.0)
    assert metrics.extract(stats)["window_consistent"] is True
    stats[CORE + "sad.samples"] = 90.0
    document = metrics.extract(stats)
    assert document["window_consistent"] is False
    assert document["windows"]["sad_samples"] == 90.0


def test_window_consistency_uses_roi_cycles_when_present():
    stats = synthetic_stats(window=100.0)
    stats[CORE + "sad.enabled"] = 1.0
    stats[CORE + "sad.roiCycles"] = 100.0
    stats[CORE + "sad.idleCycles"] = 10.0
    stats[CORE + "sad.activeCycles"] = 90.0
    stats[CORE + "sad.samples"] = 90.0
    document = metrics.extract(stats)
    assert document["window_consistent"] is True
    assert document["windows"]["sad_roi"] == 100.0
    assert document["sad"]["derived"]["active_share"] == pytest.approx(0.9)
    flat = metrics.flatten(document)
    assert flat["window.sad_roi"] == 100.0
    assert flat["sad.globals.roiCycles"] == 100.0
    stats = synthetic_stats()
    stats.pop(CORE + "sad.ratio::rob")
    with pytest.raises(metrics.MetricError, match="sad.ratio::rob"):
        metrics.extract(stats)


def test_ambiguous_suffix_raises():
    stats = synthetic_stats()
    stats["duplicate.rfAce.intAceRatio"] = 0.0
    with pytest.raises(metrics.MetricError, match="ambiguous"):
        metrics.extract(stats)


def test_flatten_and_activation_pattern():
    document = metrics.extract(synthetic_stats())
    flat = metrics.flatten(document)
    assert flat["window.consistent"] is True
    assert flat["ace.rf.intAceRatio"] == 1.0
    assert flat["ibr.intAlu.ibrRatio"] == 1.0
    assert flat["sad.rob.ratio"] == 1.0
    pattern = metrics.activation_pattern(document)
    assert "ace.rf.intAceRatio" in pattern
    assert "ibr.intAlu.ibrRatio" in pattern
    assert "sad.rob.ratio" in pattern
    assert set(pattern) == set(metrics.activation_pattern(document))


def test_check_coverage_separates_zero_from_unmeasurable():
    document = metrics.extract(synthetic_stats())
    inactive = metrics.check_coverage(document, minimum=10.0)
    assert all(entry["state"] == "zero" for entry in inactive)
    document["ace"]["rf"]["intAceRatio"] = None
    inactive = metrics.check_coverage(document, minimum=10.0)
    assert any(entry["state"] == "unmeasurable" for entry in inactive)


def test_csv_header_and_row_align():
    document = metrics.extract(synthetic_stats())
    flat = metrics.flatten(document)
    header = metrics.csv_header(flat)
    row = metrics.csv_row("stream-1", flat)
    assert len(header) == len(row)
    assert row[0] == "stream-1"
