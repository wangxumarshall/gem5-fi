"""tests/test_chaos_vec_stuck_cpp.py — FR03 Vec permanent-stuck pure model.

Compiles tests/unit/chaos_vec_stuck_test.cc with the host g++ (no gem5 build)
and requires every semantic check to pass.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "tests/unit/chaos_vec_stuck_test.cc"
INC = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg"


def test_chaos_vec_stuck_unit():
    cxx = shutil.which("g++")
    if not cxx:
        pytest.skip("g++ not available")
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "chaos_vec_stuck_test"
        build = subprocess.run(
            [cxx, "-O0", "-std=c++17", "-I", str(INC), str(SRC),
             "-o", str(exe)],
            capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], capture_output=True, text=True)
        assert run.returncode == 0, run.stdout + run.stderr
        assert "ALL CHECKS PASSED" in run.stdout
        # Explicitly pin the non-XOR stuck-at semantics.
        assert "SA0 does not use XOR" in run.stdout
        assert "SA1 does not use XOR" in run.stdout
        assert "consecutive writes stay SA0" in run.stdout
        # Workbook table 3 FR03: the permanent defect survives physical-slot
        # reuse. Generation is identity, never a clearing condition.
        assert "still applies after reallocation" in run.stdout
        assert "matches ignores generation" in run.stdout
        assert "does not apply after reallocation" not in run.stdout
