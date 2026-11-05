"""Compile and run the host-side C++ unit test for chaos_fsu_burst.hh.

This does not need a gem5 build: the header is pure standard C++.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tests/unit/chaos_fsu_burst_test.cc"
INCLUDE = ROOT / "CHAOS/gem5/src"


def test_chaos_fsu_burst_unit(tmp_path):
    exe = tmp_path / "chaos_fsu_burst_test"
    compile_cmd = [
        "g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
        "-I", str(INCLUDE), str(SRC), "-o", str(exe),
    ]
    r = subprocess.run(compile_cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"compile failed:\n{r.stdout}\n{r.stderr}"
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 0, f"unit test failed:\n{run.stdout}\n{run.stderr}"
    assert "all checks passed" in run.stdout
