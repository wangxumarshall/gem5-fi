"""Shared test fixtures.

`test_claim_concurrency.py` was written against a `check(name, condition,
message)` callable. No installed pytest plugin provides that signature
(pytest-check's fixture is `check(condition, message)` and was missing here
before v3.2.9), so the fixture is supplied explicitly. It only turns a false
condition into a test failure; it does not weaken any assertion.
"""
import os
from pathlib import Path

import pytest

# Portability for the historical v3.3.3 acceptance suite: the frozen binary,
# config and raw run logs are preserved in a separate tree on this host (the
# 3.4 GiB of *.log / prop_trace.csv.gz artifacts are git-ignored, so the repo
# carries only the small manifest files).  Point the tools at that preserved
# tree via the documented environment variables; every assertion stays exact.
# Override LSU_V333_FROZEN_ROOT to relocate it.
_ROOT = Path(__file__).resolve().parents[1]
_FROZEN = Path(os.environ.get(
    "LSU_V333_FROZEN_ROOT",
    "/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12"))
if _FROZEN.is_dir():
    os.environ.setdefault("LSU_GEM5_BIN", str(_FROZEN / "build/ARM/gem5.opt"))
    os.environ.setdefault("LSU_CONFIG", str(_FROZEN / "configs/se/lsu_proxy.py"))
    if not (_ROOT / "audit_v3_3_2/runs/A03-R01-fault/stdout.log").exists():
        os.environ.setdefault("LSU_V333_RUNS_ROOT",
                              str(_FROZEN / "audit_v3_3_2/runs"))


@pytest.fixture
def check():
    def _check(name, condition, message=""):
        assert condition, f"{name}: {message}"
    return _check
