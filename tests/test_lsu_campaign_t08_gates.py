#!/usr/bin/env python3
"""[LSU][R6-PROPAGATION-V3] Capability gates for the 11 non-STOP T cells.

Pinned semantics (user ruling 2026-10-27):

  * T05/T06/T07 W4 are runnable: the modes are in the current binary, so the
    stale MODEL_BLOCKED "COMPILE-UNVERIFIED" entry must not refuse them.
  * T08-F0-W4 / T08-F4-W4: only the explicit T08-a representative canary may
    run; the whole T08 model stays PARTIAL (T08-b/c/d not dynamically proven).
  * T08-F0-W9 / T08-F4-W9: hard BLOCKED_WORKLOAD_GAP. No generic flag
    (--allow-blocked-models / evidence pilot) may turn them into a
    tlb_probe.rcS run.
  * screening/formal may not use the generic MODEL_BLOCKED bypass at all.
  * T09, F6 and W11 SPEC stay refused.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import lsu_campaign as lc  # noqa: E402

MATRIX = os.path.join(ROOT, "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv")


def _cells():
    _hdr, cells = lc.load_matrix(MATRIX)
    return {c[lc.COL_RUNID].strip(): c for c in cells}


CELLS = _cells()


def _resolve(rid, **kw):
    return lc.resolve_cell(CELLS[rid], **kw)


@pytest.mark.parametrize("rid", [
    "T05-F0-W4", "T05-F2-W4",
    "T06-F0-W4", "T06-F2-W4",
    "T07-F0-W4", "T07-F4-W4",
])
def test_t05_t06_t07_w4_runnable_without_bypass(rid):
    flags, golden, reason = _resolve(rid)
    assert flags is not None, f"{rid} should be runnable, got {reason}"
    assert golden and reason == "fs:tlb_probe"


def test_t05_t06_t07_are_out_of_model_blocked():
    for model in ("T05", "T06", "T07"):
        assert model not in lc.MODEL_BLOCKED


def test_t08_w4_default_is_partial_not_runnable():
    for rid in ("T08-F0-W4", "T08-F4-W4"):
        flags, _g, reason = _resolve(rid)
        assert flags is None
        assert "PARTIAL_SUBMODEL_PROVEN" in reason
        assert "T08-a" in reason


def test_t08_w4_explicit_t08a_canary_is_runnable():
    for rid in ("T08-F0-W4", "T08-F4-W4"):
        flags, _g, reason = _resolve(rid, t08a_canary=True)
        assert flags is not None, reason
        assert "--tlb_fault_type" in flags
        i = flags.index("--tlb_fault_type")
        assert flags[i + 1] == "walk_pairing"
        assert reason == "fs:tlb_probe"


def test_generic_allow_blocked_does_not_unlock_t08_w4():
    for rid in ("T08-F0-W4", "T08-F4-W4"):
        flags, _g, reason = _resolve(rid, allow_blocked=True)
        assert flags is None
        assert "PARTIAL_SUBMODEL_PROVEN" in reason


def test_t08_w9_hard_workload_gap_no_bypass():
    for rid in ("T08-F0-W9", "T08-F4-W9"):
        for kw in ({}, {"allow_blocked": True}, {"evidence_pilot": True},
                   {"t08a_canary": True}, {"allow_blocked": True,
                                            "evidence_pilot": True,
                                            "t08a_canary": True}):
            flags, _g, reason = _resolve(rid, **kw)
            assert flags is None, (rid, kw)
            assert reason.startswith("BLOCKED_WORKLOAD_GAP"), (rid, kw, reason)
            # No runnable flag set (and therefore no tlb_probe --readfile)
            # may be produced for W9 under any bypass combination.
            assert "--readfile" not in reason


def test_t08_f6_is_not_a_canary():
    flags, _g, reason = _resolve("T08-F6-W4", t08a_canary=True)
    assert flags is None
    assert "PARTIAL_SUBMODEL_PROVEN" in reason


def test_t09_cannot_be_unblocked_by_generic_flag():
    flags, _g, reason = _resolve("T09-F0-W4", allow_blocked=True)
    assert flags is None
    assert "不适用" in reason or "OUT_OF_SCOPE" in reason


def test_w11_spec_stays_blocked():
    flags, _g, reason = _resolve("T10-F0-W11", allow_blocked=True,
                                 t08a_canary=True)
    assert flags is None
    assert "spec-license" in reason


def test_screening_formal_reject_generic_bypass():
    for phase in ("screening", "main"):
        with pytest.raises(SystemExit):
            lc.check_phase_gate(phase, allow_blocked_models=True,
                                t08a_canary=False)
    # trial may use the narrow flags
    lc.check_phase_gate("trial", allow_blocked_models=True,
                        t08a_canary=True)


def test_screening_formal_reject_t08a_canary():
    for phase in ("screening", "main"):
        with pytest.raises(SystemExit):
            lc.check_phase_gate(phase, allow_blocked_models=False,
                                t08a_canary=True)
