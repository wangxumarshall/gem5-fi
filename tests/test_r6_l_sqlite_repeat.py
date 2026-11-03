"""R6-L sqlite_like same-source bounded repeat (native oracle)."""
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIN = REPO / "workloads/directed/sqlite_like"
GOLDEN = "33f836327a416d35"


def _run(*args):
    return subprocess.run([str(BIN), *args], capture_output=True, text=True,
                          timeout=60)


def test_repeat_one_is_byte_identical_golden():
    run = _run()
    assert run.returncode == 0
    assert run.stdout == GOLDEN + "\n"


def test_repeat_five_emits_identical_iterations():
    run = _run("5")
    assert run.returncode == 0
    lines = run.stdout.strip().splitlines()
    iters = [l for l in lines if l.startswith("ITER:")]
    assert len(iters) == 5
    assert [l.split(":")[1] for l in iters] == ["0", "1", "2", "3", "4"]
    assert all(l.split(":")[2] == GOLDEN for l in iters)
    assert lines[-1] == GOLDEN


def test_illegal_repeat_falls_back_to_one():
    run = _run("0")
    assert run.stdout == GOLDEN + "\n"
