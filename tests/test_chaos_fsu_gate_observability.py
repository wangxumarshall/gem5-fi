"""FQ08-c / FP08 observability wiring (2026-11-05).

These are static contract checks: the real gem5 evidence lives under
runs/fsu-gates/FQ08-C-FIRE and runs/fsu-gates/FP08-ROUNDING-REASON and is
summarised in docs/gem5-fi/fsu/FQ08-FP08-GATE-EVIDENCE.md.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IQ_CC = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.cc"
IQ_HH = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.hh"
FPU_CC = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc"
FPU_HH = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.hh"


def test_fq08c_fire_records_woken_target_state():
    cc = IQ_CC.read_text(encoding="utf-8")
    hh = IQ_HH.read_text(encoding="utf-8")
    assert "const int woken =" in cc
    assert "wakeDependents(inst)" in cc
    assert "delayed_dependents_woken" in cc
    assert "delayed_dependents_woken" in hh
    assert '<< ", woken=" << woken' in cc


def test_fp08_rounding_rejection_reasons_are_conserved():
    cc = FPU_CC.read_text(encoding="utf-8")
    hh = FPU_HH.read_text(encoding="utf-8")
    for key in ("rounding_skip_no_o3cpu", "rounding_skip_no_vec_dest",
                "rounding_skip_no_writable_dest", "rounding_skip_nonfinite"):
        assert key in hh and key in cc
    # Both summary sites (census and injection pass) must print all buckets.
    assert cc.count('CHAOS_ROUNDING_SKIP_NO_O3CPU') == 2
    assert cc.count('CHAOS_ROUNDING_SKIP_NO_VEC_DEST') == 2
    assert cc.count('CHAOS_ROUNDING_SKIP_NO_WRITABLE_DEST') == 2
    assert cc.count('CHAOS_ROUNDING_SKIP_NONFINITE') == 2
    assert cc.count('CHAOS_ROUNDING_CONSERVED') == 2
    # Fail closed for ambiguous early-return mode combinations.
    assert "fpsrSuppress is incompatible" in cc
    assert "roundingSub is incompatible" in cc
