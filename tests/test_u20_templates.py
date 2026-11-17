"""Pure-Python contracts for the 20-template vs AutoµSens experiment."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))

from autousens import u20_templates as u20  # noqa: E402
from sdcfuzz import seed_templates  # noqa: E402
from sdcfuzz.target_oracle import expected_checksum  # noqa: E402

# The repository has two modules named ``autousens``: the CLI script
# ``tools/autousens.py`` and the experiment package ``experiments/autousens``.
# Importing the package here must not shadow the CLI for tests that deliberately
# do ``import autousens`` after putting ``tools/`` on sys.path.  The u20 module
# keeps direct references to the package submodules it needs, so removing the
# package entries from sys.modules is safe.
for _name in [name for name in sys.modules
              if name == "autousens" or name.startswith("autousens.")]:
    del sys.modules[_name]


def fake_map():
    def entry(value, l1d=0.0):
        activation = {structure: 0.0 for structure in u20.TOOL.STRUCTURES}
        per_instruction = {structure: 0.0 for structure in u20.TOOL.STRUCTURES}
        activation["alu"] = value
        activation["l1d"] = l1d
        per_instruction["alu"] = value / 100.0
        per_instruction["l1d"] = l1d / 100.0
        return {
            "activation": activation,
            "activation_per_instruction": per_instruction,
        }

    return {
        "dynamic_ops": 100.0,
        "instructions": {
            "add": entry(3300.0),
            "sub": entry(3200.0),
            "ldr": entry(0.0, 100.0),
        },
    }


def test_mapping_covers_all_20_seeds():
    assert len(u20.MAPPINGS) == 20
    assert len(set(mapping.seed for mapping in u20.MAPPINGS)) == 20
    assert {mapping.seed for mapping in u20.MAPPINGS} == {
        seed.id for seed in seed_templates.SEEDS}
    for mapping in u20.MAPPINGS:
        assert mapping.auto in u20.TOOL.STRUCTURES
        assert mapping.measured in u20.PRIMARY
        assert mapping.measured in u20.FOCUS
        assert mapping.kind in {"direct", "proxy", "unmeasurable"}


def test_x12_is_never_read_before_write_in_any_seed():
    for seed in seed_templates.SEEDS:
        access = u20.x12_first_access(seed.source())
        assert access in {"write", "absent"}, (seed.id, access)


def test_groups_for_matches_the_straight_line_budget():
    assert u20.groups_for(15) == 2
    assert u20.groups_for(38) == 8
    assert u20.groups_for(73) == 16
    assert u20.groups_for_loaded(15) == 1
    assert u20.groups_for_loaded(38) == 4
    assert u20.groups_for_loaded(73) == 9
    with pytest.raises(ValueError):
        u20.groups_for(0)


def test_top1_selection_uses_the_tool_ranking():
    mode, skipped = u20.select_auto_mode(fake_map(), "alu")
    assert mode == "add"
    assert skipped == []


def test_straight_line_guest_has_the_right_body_and_oracle():
    sequence = ["add"] * u20.OPS_PER_GROUP
    groups = 3
    expected = expected_checksum(sequence, groups, groups=1)
    source = u20.render_straightline("alu", sequence, groups)
    assert source.count('"add x8, x8, x12\\n\\t"') == groups * len(sequence)
    assert f"0x{expected:016x}" in source
    assert f"requested != {groups}" in source
    assert "operands[" not in source


def test_straight_line_d13_guest_adds_one_operand_per_group():
    sequence = ["add"] * u20.OPS_PER_GROUP
    operands = [1, 2, 3]
    expected = expected_checksum(sequence, 3, groups=1, operands=operands)
    source = u20.render_straightline("alu", sequence, 3, operands=operands)
    assert source.count('"ldr x12, [%[ops]], #8\\n\\t"') == 3
    assert "UINT64_C(0x0000000000000001)" in source
    assert f"0x{expected:016x}" in source
    with pytest.raises(ValueError):
        u20.render_straightline("alu", sequence, 3, operands=[1, 2])


def test_d13_changes_the_add_checksum():
    sequence = ["add"] * u20.OPS_PER_GROUP
    default = expected_checksum(sequence, 2, groups=1)
    directed = expected_checksum(sequence, 2, groups=1, operands=[5, 7])
    assert default != directed


def test_straight_line_expected_constant_is_a_volatile_load():
    source = u20.render_straightline("alu", ["add"] * u20.OPS_PER_GROUP, 2)
    assert "static volatile const uint64_t expected_storage" in source
    assert "const uint64_t expected = expected_storage;" in source
    assert "const uint64_t expected = UINT64_C" not in source


def test_stabilise_expected_handles_the_target_oracle_renderer():
    from sdcfuzz.target_oracle import render_candidate

    source = render_candidate("alu", ["add"] * u20.OPS_PER_GROUP, 2,
                              u20.MODE_ASM, groups=16)
    assert "expected = UINT64_C" in source
    stable = u20.stabilise_expected(source)
    assert "static volatile const uint64_t expected_storage" in stable
    assert stable.count("expected = expected_storage;") == 2
    assert "expected = UINT64_C" not in stable
