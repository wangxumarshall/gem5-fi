"""R6-L bounded-repeat routing: L01/L02 addrpath + L03 lsqfwd/F0."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import lsu_campaign as C  # noqa: E402

MATRIX = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv")


def _cell(runid):
    header, cells = C.load_matrix(str(MATRIX))
    for c in cells:
        if c[C.COL_RUNID] == runid:
            return c
    raise AssertionError("cell not found: %s" % runid)


def _rep(flags):
    return int(flags[flags.index("--chaos_repeat") + 1])


def test_l01_f1_uses_measured_factor(monkeypatch):
    monkeypatch.setitem(C.REPEAT_FACTOR, ("L01", "F1", "sq_forward", ""), 777)
    flags, golden, binary = C.resolve_cell(_cell("L01-F1-W5"), seed=1)
    assert flags is not None, golden
    assert binary == "sq_forward"
    assert _rep(flags) == 777


def test_l02_f2_uses_own_factor(monkeypatch):
    monkeypatch.setitem(C.REPEAT_FACTOR, ("L02", "F2", "sqlite_like", ""), 31)
    flags, golden, _ = C.resolve_cell(_cell("L02-F2-W12"), seed=2)
    assert flags is not None, golden
    assert _rep(flags) == 31


def test_l03_f4_uses_measured_factor(monkeypatch):
    monkeypatch.setitem(C.REPEAT_FACTOR, ("L03", "F4", "sq_forward", ""), 314)
    flags, golden, _ = C.resolve_cell(_cell("L03-F4-W5"), seed=1)
    assert flags is not None, golden
    assert _rep(flags) == 314


def test_unmeasured_l_interval_refuses_loudly(monkeypatch):
    monkeypatch.delitem(C.REPEAT_FACTOR, ("L01", "F2", "sq_forward", ""),
                        raising=False)
    flags, _, reason = C.resolve_cell(_cell("L01-F2-W5"), seed=1)
    assert flags is None
    assert "repeat-factor-unmeasured" in reason


def test_l03_f0_seed3_uses_seed_keyed_factor(monkeypatch):
    monkeypatch.setitem(C.L_F0_REPEAT, ("L03", "sq_forward", 3), 2)
    flags, golden, _ = C.resolve_cell(_cell("L03-F0-W5"), seed=3)
    assert flags is not None, golden
    assert _rep(flags) == 2
    # the F0 draw parameters themselves are untouched
    assert flags[flags.index("--lsqfwd_warmup_events") + 1] == "1"
    assert flags[flags.index("--lsqfwd_span_events") + 1] == "571"


def test_l03_f0_unmeasured_seed_stays_repeat1(monkeypatch):
    monkeypatch.delitem(C.L_F0_REPEAT, ("L03", "sq_forward", 1), raising=False)
    flags, golden, _ = C.resolve_cell(_cell("L03-F0-W5"), seed=1)
    assert flags is not None, golden
    assert "--chaos_repeat" not in flags


def test_a_unit_repeat_unchanged():
    flags, golden, _ = C.resolve_cell(_cell("A01-F1-W3"), seed=1)
    assert flags is not None, golden
    assert _rep(flags) == C.REPEAT_FACTOR[("A01", "F1", "agu_addrmodes", "")]
