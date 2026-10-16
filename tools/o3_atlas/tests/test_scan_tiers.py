# tools/o3_atlas/tests/test_scan_tiers.py
from pathlib import Path

import pytest

GEN = Path("/home/sdc/gem5-fi-ding/build/ARM/arch/arm/generated/decoder-ns.hh.inc")

pytestmark = pytest.mark.skipif(
    not GEN.is_file(),
    reason="build/ARM/arch/arm/generated 缺失（需先构建 gem5；诚实跳过，不静默通过）")


def test_class_names_contains_known_a64_classes():
    from tools.o3_atlas.scan_tiers import class_names
    names = class_names()
    for expected in ("AddXImm", "BCond64", "STXRX64", "Pacia", "Movz"):
        assert expected in names, expected
    assert len(names) > 3000  # 实测 3790（含 A32/T32）


def test_constructor_mnemonics_basic_and_dynamic():
    from tools.o3_atlas.scan_tiers import constructor_mnemonics
    m = constructor_mnemonics()
    assert m.get("AddXImm") == ["add"]
    assert m.get("BCond64") == ["b"]
    # 动态助记符特例：LdpStp 的助记符来自解码点（formats/aarch64.isa:1690-1737）
    assert set(m.get("LdpStp", [])) >= {"ldp", "stp"}


def test_candidates_for_add_immediate_top_hit():
    from tools.o3_atlas.scan_tiers import candidates_for
    c = candidates_for("ADD (immediate)")
    assert c and c[0]["class"] == "AddXImm" and c[0]["mnemonic"] == "add"


def test_candidates_for_alias_resolves_to_primary():
    # 别名：MOV (to/from SP) 实为 ADD (immediate) 的别名
    from tools.o3_atlas.scan_tiers import candidates_for
    c = candidates_for("MOV (to/from SP)")
    assert any(x["class"] == "AddXImm" for x in c)


def test_candidates_integer_variant_outranks_fp_variant():
    # 修复①：整型变体必须排在 FP/SIMD 变体前（LDR 主类是 LDRX64_IMM 不是 LDRBFP64_IMM）
    from tools.o3_atlas.scan_tiers import candidates_for
    c = candidates_for("LDR (immediate)")
    assert c[0]["class"] == "LDRX64_IMM", f"top={c[0]['class']}"
