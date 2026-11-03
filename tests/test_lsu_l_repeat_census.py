"""R6-L repeat census: first-fire math, key table, R formula."""
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import r6_l_repeat_census as C  # noqa: E402


def test_first_fire_matches_trigger_lcg():
    assert C.first_fire("F1", 1) == 1256412
    assert C.first_fire("F1", 2) == 1049417
    assert C.first_fire("F1", 3) == 1290806
    assert C.first_fire("F2", 1) == 106412
    assert C.first_fire("F4", 3) == 140806
    assert C.max_first_fire("F1") == 1290806
    assert C.max_first_fire("F2") == 140806


def test_key_table_covers_all_l_interval_cells_and_f0():
    keys = {k[0]: k for k in C.KEYS}
    for key in ("L01-F1-W5", "L01-F1-W12", "L01-F2-W5", "L01-F2-W12",
                "L02-F2-W5", "L02-F2-W12", "L03-F4-W5", "L03-F4-W12"):
        assert keys[key][6] in ("F1", "F2", "F4")
    assert keys["L03-F0-W5-s3"][6] == "F0"
    assert keys["L03-F0-W5-s3"][5] == 3
    assert keys["L03-F0-W5-s3"][7] == 561


def test_r_formula_covers_target():
    E1, delta, target = 1262, 16.333333, 1290806
    R = 1 + int(math.ceil((1.2 * target - E1) / delta))
    assert R == 94759
    assert E1 + (R - 1) * delta >= 1.2 * target - delta
