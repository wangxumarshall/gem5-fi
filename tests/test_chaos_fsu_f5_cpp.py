"""Host-side verification of the [FSU][F5] CHAOSFPU implementation.

Two layers, both without a gem5 build (the host is under heavy load):

1. Compile and run tests/unit/chaos_fsu_f5_test.cc with g++ -O0. The header
   is pure standard C++, so the stuck-at semantics are tested for real.
2. Static wiring checks over CHAOSFPU.hh/.cc/.py: the five new parameters
   exist, the F5 path uses applyStuck/stuckActivated (never XOR), and the
   install is the only place that mints a new fault_id.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tests/unit/chaos_fsu_f5_test.cc"
INCLUDE = ROOT / "CHAOS/gem5/src"
FPU = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSFPU"


def test_chaos_fsu_f5_unit(tmp_path):
    exe = tmp_path / "chaos_fsu_f5_test"
    compile_cmd = [
        "g++", "-O0", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        "-I", str(INCLUDE), str(SRC), "-o", str(exe),
    ]
    r = subprocess.run(compile_cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"compile failed:\n{r.stdout}\n{r.stderr}"
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 0, f"unit test failed:\n{run.stdout}\n{run.stderr}"
    assert "all checks passed" in run.stdout


def test_f5_python_params_exist():
    text = (FPU / "CHAOSFPU.py").read_text(encoding="utf-8")
    for name in ("permanentStuck", "stuckPolarity", "f5Warmup",
                 "f5SampleLimit", "f5KeepFirstLastN"):
        assert re.search(rf"^\s*{name}\s*=\s*Param\.", text, re.M), name


def test_f5_header_declares_one_install_and_bounded_samples():
    text = (FPU / "CHAOSFPU.hh").read_text(encoding="utf-8")
    for name in ("notePermanentExposure", "registerF5Taint",
                 "flushF5Samples", "emitF5ChainEnd",
                 "f5_last_samples", "f5_exposures_total",
                 "f5_exposures_sampled", "f5_exposures_dropped"):
        assert name in text, name


def test_f5_cc_uses_forced_polarity_not_xor():
    text = (FPU / "CHAOSFPU.cc").read_text(encoding="utf-8")
    assert "chaos_fsu::applyStuck(" in text
    assert "chaos_fsu::stuckActivated(" in text
    # The F5 lane write must be guarded by permanent_stuck and call
    # applyStuck; the legacy XOR must remain the non-F5 branch only.
    assert re.search(
        r"lane_after\s*=\s*permanent_stuck\s*\?\s*"
        r"chaos_fsu::applyStuck\(", text)
    assert re.search(
        r"lane_after\s*=\s*permanent_stuck\s*[\s\S]{0,160}"
        r":\s*lane_before\s*\^\s*mi\.lane_mask", text)


def test_f5_install_is_the_only_new_fault_site():
    text = (FPU / "CHAOSFPU.cc").read_text(encoding="utf-8")
    # one allocation in noteFaultApplied (non-F5 path), one at F5 install.
    assert text.count("next_fault_id++") == 2
    assert 'emitFsu("fault_installed"' in text
    assert 'emitFsu("exposure"' in text
    # The F5 branch must call notePermanentExposure, never noteFaultApplied
    # per exposure (that would mint a fault_id per event).
    assert re.search(
        r"if\s*\(permanent_stuck\)\s*\{[\s\S]{0,600}"
        r"notePermanentExposure\(dyn_inst, info\);", text)
    # noteFaultApplied is the NON-F5 branch only; the F5 path reaches it
    # zero times, so it must occur exactly once in the source call site.
    assert text.count("noteFaultApplied(dyn_inst, info);") == 1


def test_f5_chain_end_reports_capacity():
    text = (FPU / "CHAOSFPU.cc").read_text(encoding="utf-8")
    assert '"exposures_total"' in text
    assert '"exposures_sampled"' in text
    assert '"exposures_dropped"' in text
    assert '"sample_policy"' in text
    assert 'emitFsu("chain_end"' in text
