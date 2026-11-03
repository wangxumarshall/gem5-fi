"""tests/test_chaos_physreg_generation_cpp.py — FR03 generation semantics.

Compiles tests/unit/chaos_physreg_generation_test.cc with the host g++ (no
gem5 build) and requires every permanent-cell generation check to pass.

The test pins the workbook ruling (table 3 FR03 + table 7/9 FR03):
the permanent key is reg_class + phys_index + lane/bit/mask + polarity;
generation is allocation/exposure identity only. Free/realloc/squash do NOT
clear the defect; a new generation restarts its exposure chain; only an
explicit end-of-run reset clears it.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "tests/unit/chaos_physreg_generation_test.cc"
INC = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg"


def test_chaos_physreg_generation_unit():
    cxx = shutil.which("g++")
    if not cxx:
        pytest.skip("g++ not available")
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "chaos_physreg_generation_test"
        build = subprocess.run(
            [cxx, "-O0", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-I", str(INC), str(SRC), "-o", str(exe)],
            capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], capture_output=True, text=True)
        assert run.returncode == 0, run.stdout + run.stderr
        assert "ALL GENERATION CHECKS PASSED" in run.stdout
        # Pin the load-bearing semantics explicitly.
        assert "PERMANENT STUCK ACROSS GENERATIONS" in run.stdout
        assert "GENERATION CHAIN RESTART: exposure_id back to 1" in run.stdout
        assert "SQUASH DOES NOT CLEAR" in run.stdout
        assert "reset clears the cell" in run.stdout
        assert "int register class does not cross-talk" in run.stdout
        assert "float register class does not cross-talk" in run.stdout
