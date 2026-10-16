# tools/o3_atlas/tests/test_matrix.py
from pathlib import Path

import pytest

FORMATS = Path("/home/sdc/gem5-fi-ding/docs/cpu/o3-atlas/data/instructions/Arithmetic.yaml")

pytestmark = pytest.mark.skipif(
    not FORMATS.is_file(),
    reason="o3-atlas 数据未生成（诚实跳过）")


def test_matrix_shape_and_min_default_hits():
    from tools.o3_atlas.generate import render_matrix
    from tools.o3_atlas.schema import INJECTORS
    from tools.o3_atlas.validate import load_data
    families, instructions = load_data()
    md = render_matrix(instructions)
    lines = [l for l in md.splitlines() if l.startswith("|")]
    assert len(lines) == 2 + len(instructions)  # 表头 + 分隔行 + 372 数据行
    for inj in INJECTORS:
        assert inj in md, inj
    add_row = next(l for l in lines if "Arithmetic-ADD_immediate" in l)
    assert add_row.count("✓") >= 8  # 默认底座 ≥8 命中
    # unimplemented 行全 ·（无命中）
    cpyp_row = next(l for l in lines if "Other-CPYP__CPYM_CPYE" in l)
    assert cpyp_row.count("✓") == 0
