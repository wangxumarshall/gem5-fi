"""Unit tests for the Phase-0 template corpus and generator (no gem5)."""

import pytest

from sdcfuzz import isa
from sdcfuzz.generator import display_operand, render_guest, with_operand
from sdcfuzz.templates import TEMPLATES, TEMPLATE_BY_ID


def test_corpus_has_19_unique_templates():
    assert len(TEMPLATES) == 19
    ids = [template.id for template in TEMPLATES]
    assert len(set(ids)) == 19
    for template in TEMPLATES:
        assert template.target in ("alu", "mult", "div", "l1d", "l1i", "none")
        assert template.injector.startswith("CHAOS")
        assert template.body


def test_render_embeds_reference_checksum_and_markers():
    template = TEMPLATE_BY_ID["mul64"]
    source, expected = render_guest(template, iterations=7)
    assert f"EXPECTED_CHECKSUM 0x{expected:016x}ULL" in source
    assert "m5_work_begin(7, 0)" in source
    assert "m5_work_end(7, 0)" in source
    assert ".rept 16" in source
    assert "mul x8, x8, x12" in source


def test_expected_checksum_is_deterministic_and_iteration_dependent():
    template = TEMPLATE_BY_ID["alu-add-carry"]
    first = isa.expected_checksum(template, 5)
    second = isa.expected_checksum(template, 5)
    other = isa.expected_checksum(template, 6)
    assert first == second
    assert first != other


def test_with_operand_changes_the_reference_value():
    template = TEMPLATE_BY_ID["alu-add-carry"]
    default = isa.expected_checksum(template, 3)
    changed = isa.expected_checksum(
        with_operand(template, "x12", 0xFF00FF00FF00FF00), 3)
    assert default != changed


def test_32_bit_semantics_wrap_and_zero_extend():
    state = isa.State()
    state.regs["x8"] = 0xFFFFFFFFFFFFFFFF
    state.regs["x12"] = 3
    isa.apply(isa.Op("mul", dst="x8", a="x8", b="x12", width=32), state)
    assert state.regs["x8"] == (0xFFFFFFFF * 3) & 0xFFFFFFFF
    state.regs["x8"] = 0xFFFFFFFF
    isa.apply(isa.Op("udiv", dst="x8", a="x8", b="x12", width=32), state)
    assert state.regs["x8"] == 0xFFFFFFFF // 3


def test_division_by_zero_is_zero():
    state = isa.State()
    state.regs["x8"] = 123
    state.regs["x12"] = 0
    isa.apply(isa.Op("udiv", dst="x8", a="x8", b="x12", width=64), state)
    assert state.regs["x8"] == 0


def test_display_operand_is_stable():
    template = TEMPLATE_BY_ID["mul64"]
    assert display_operand(template) == 0x9E3779B97F4A7C15


def test_unknown_op_is_rejected():
    with pytest.raises(ValueError):
        isa.render(isa.Op("rmw"))
    with pytest.raises(ValueError):
        isa.apply(isa.Op("rmw"), isa.State())
