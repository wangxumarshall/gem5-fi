#!/usr/bin/env python3
"""Tests for tools/lsu_v333_propagation.py (LSU v3.3.3, Agent J).

Everything runs against the real v3.3.2 run fixtures.  If a fixture is absent
the affected assertion is skipped with an explicit reason instead of being
weakened.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "audit_v3_3_2/runs"
sys.path.insert(0, str(ROOT / "tools"))

import lsu_v333_propagation as prop  # noqa: E402

pytestmark = pytest.mark.skipif(
    not RUNS.is_dir(), reason=f"v3.3.2 run fixtures absent: {RUNS}")

REQUIRED_COLUMNS = (
    "ModelID", "ContextID", "ROI/Percentile/Ordinal", "Injection",
    "Activation", "FirstDivergence", "Downstream", "Consumer",
    "CommitSquashReplay", "Terminal", "TerminalReason", "ApplicationOracle",
    "EvidenceClass", "TraceCompleteness", "MaskingMechanism", "EvidencePaths",
)

RP01_TARGET = {"R01": 26, "R02": 77, "R03": 128, "R04": 179, "R05": 230}
A01_R01_FIRST_CONSUMER = 12980


@pytest.fixture(scope="module")
def rows(tmp_path_factory):
    out = tmp_path_factory.mktemp("propagation") / "causal.csv"
    assert prop.main(["--runs", str(RUNS), "--out", str(out)]) == 0
    with out.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def by_key(rows):
    return {(r["ModelID"], r["ContextID"]): r for r in rows}


def need(model):
    missing = [c for c in range(1, 6)
               if not (RUNS / f"{model}-R{c:02d}-fault").is_dir()]
    if missing:
        pytest.skip(f"{model} fixture runs missing: R{missing}")


def test_columns_and_60_rows(rows):
    assert len(rows) == 60
    assert tuple(rows[0].keys()) == REQUIRED_COLUMNS
    keys = {(r["ModelID"], r["ContextID"]) for r in rows}
    assert len(keys) == 60


def test_every_model_context_present(rows):
    for model in prop.MODELS:
        for ctx in range(1, 6):
            assert (model, f"R{ctx:02d}") in by_key(rows)


def test_a03_rows_are_sdc_not_hang(rows):
    need("A03")
    a03 = [r for r in rows if r["ModelID"] == "A03"]
    assert len(a03) == 5
    assert all(r["Terminal"] == "SDC" for r in a03), [r["Terminal"] for r in a03]
    assert all(r["ApplicationOracle"] == "FAIL" for r in a03)
    for r in a03:
        assert "ORACLE_FAIL" in r["TerminalReason"]
        assert "checksum=" in r["TerminalReason"]
        assert "golden=728e604ffcec539d" in r["TerminalReason"]


def test_a01_r03_is_injection_not_activated(rows):
    need("A01")
    r = by_key(rows)[("A01", "R03")]
    assert r["Terminal"] == "INJECTION_NOT_ACTIVATED"
    assert "NO_EFFECTIVE_INJECTION" in r["TerminalReason"]
    assert "applied_to_request=0" in r["TerminalReason"]


def test_a01_r02_squash_is_unrelated_but_valid(rows):
    need("A01")
    r = by_key(rows)[("A01", "R02")]
    assert r["Terminal"] == "SQUASHED"
    assert "UNRELATED_SQUASH_NO_ARCH_ENTRY" in r["TerminalReason"]
    assert "fault_caused=0" in r["TerminalReason"]


def test_rp01_activation_is_target_ordinal(rows):
    need("RP01")
    rp = [r for r in rows if r["ModelID"] == "RP01"]
    assert len(rp) == 5
    for r in rp:
        target = RP01_TARGET[r["ContextID"]]
        assert r["Terminal"] == "HANG_WATCHDOG"
        assert f"ordinal={target}" in r["Activation"]
        assert f"target_ordinal={target}" in r["TerminalReason"]
        assert "CHAOS_RP01_WATCHDOG_EXPIRED" in r["CommitSquashReplay"]


def test_sq03_is_masked_visibility_shift(rows):
    need("SQ03")
    sq = [r for r in rows if r["ModelID"] == "SQ03"]
    assert len(sq) == 5
    assert all(r["Terminal"] == "MASKED" for r in sq)
    for r in sq:
        assert "VISIBILITY_TIMING_SHIFT" in r["TerminalReason"]
        assert "VISIBILITY_TIMING_SHIFT" in r["MaskingMechanism"]
    moved = [r for r in sq
             if "effect_outcome=CHAIN_VISIBILITY_MOVED" in r["TerminalReason"]]
    lifecycle = [r for r in sq
                 if "effect_outcome=LIFECYCLE_ONLY" in r["TerminalReason"]]
    assert len(moved) == 4, [r["ContextID"] for r in moved]
    assert len(lifecycle) == 1
    assert lifecycle[0]["ContextID"] == "R02"


def test_sp05_reload_unverifiable_on_old_runs(rows):
    need("SP05")
    sp = [r for r in rows if r["ModelID"] == "SP05"]
    assert len(sp) == 5
    assert all(r["Terminal"] == "RELOAD_UNVERIFIABLE" for r in sp)
    for r in sp:
        assert "store_data_fnv=null" in r["TerminalReason"]


def test_activation_is_never_the_tautology(rows):
    for r in rows:
        assert not r["Activation"].startswith("injection seq="), r
        assert "record=" in r["Activation"] or r["Activation"] in ("n/a",)


def test_activation_carries_the_design_ordinal(rows):
    for r in rows:
        if r["Activation"] == "n/a":
            continue
        assert "ordinal=" in r["Activation"], r


def test_consumer_is_a_different_seq_record(rows):
    need("A01")
    r = by_key(rows)[("A01", "R01")]
    assert "consumer_commit" in r["Consumer"]
    assert f"seq={A01_R01_FIRST_CONSUMER}" in r["Consumer"]
    assert "pc=" in r["Consumer"]


def test_masked_mechanisms_are_specific(rows):
    key = by_key(rows)
    need("FW02")
    assert key[("FW02", "R03")]["Terminal"] == "MASKED"
    assert "SUPPRESSED_FORWARD_NORMAL_VALUE" in \
        key[("FW02", "R03")]["MaskingMechanism"]
    need("MD04")
    assert key[("MD04", "R01")]["Terminal"] == "MASKED"
    assert "INERT_AFTER_COMPLETION" in \
        key[("MD04", "R01")]["MaskingMechanism"]
    need("LQ04")
    for ctx in range(1, 6):
        assert "ENTRY_INVALIDATED_RESTORED" in \
            key[("LQ04", f"R{ctx:02d}")]["MaskingMechanism"]


def test_completeness_never_passes_on_structure_alone(rows):
    for r in rows:
        if r["TraceCompleteness"] != "COMPLETE":
            continue
        witness = (r["Consumer"] != "n/a"
                   or r["Terminal"] in ("SQUASHED", "INJECTION_NOT_ACTIVATED",
                                        "HANG_WATCHDOG", "HANG_TIMEOUT",
                                        "SDC", "MASKED"))
        assert witness, r
        assert r["TerminalReason"] not in ("n/a", "NO_INJECTION_EVENT",
                                           "NO_RUN_DIRECTORY"), r
