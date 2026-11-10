"""Unit tests for the local operand heuristic (not upstream D13)."""

import pytest

from sdcfuzz import operand_heuristic as d13


def test_carry_chain_hand_examples():
    assert d13.carry_chain(0, 0) == 0
    assert d13.carry_chain(1, 1) == 1
    assert d13.carry_chain(0b11, 0b1) == 2
    assert d13.carry_chain(0b1000, 0b1000) == 1
    # All-ones plus one carries through every bit position.
    assert d13.carry_chain(d13.MASK64, 1) == 64


def test_toggle_bits_and_masking_risk():
    assert d13.toggle_bits(0, d13.MASK64) == 64
    assert d13.toggle_bits(0xF0, 0x0F) == 8
    assert d13.masking_risk(0, 123) is True
    assert d13.masking_risk(1, d13.MASK64) is True
    assert d13.masking_risk(0x1234, 0x1234) is True
    # Only a handful of differing bits: easily masked downstream.
    assert d13.masking_risk(0x1000, 0x1001) is True
    assert d13.masking_risk(0x00FF00FF00FF00FF, 0xFF00FF00FF00FF00) is False


def test_select_prefers_carry_chain_then_toggle():
    reference = 0x0000000000000001
    candidates = [0x0000000000000003, 0xFFFFFFFFFFFFFFFF, 0x00FF00FF00FF00FF]
    chosen = d13.select(candidates, reference=reference)
    allowed = [value for value in candidates
               if not d13.masking_risk(value, reference)]
    scores = {value: d13.score(value, reference) for value in allowed}
    assert chosen == max(allowed, key=lambda value: scores[value])
    assert chosen in candidates


def test_select_rejects_fully_masked_pools():
    with pytest.raises(ValueError):
        d13.select([0, 1], reference=0)
    with pytest.raises(ValueError):
        d13.select([], reference=0)


def test_select_validates_operands():
    with pytest.raises(TypeError):
        d13.select([1.5], reference=0)  # type: ignore[list-item]
    with pytest.raises(ValueError):
        d13.select([1 << 64], reference=0)


def test_candidates_are_deterministic_and_bounded():
    first = d13.candidates_for(0x1234, count=32, seed=7)
    second = d13.candidates_for(0x1234, count=32, seed=7)
    assert first == second
    assert len(first) == 32
    assert all(0 <= value <= d13.MASK64 for value in first)
    assert len(set(first)) > 16


def test_choose_operand_beats_random_pool_and_is_not_masked():
    reference = 0x00FF00FF00FF00FF
    pool = d13.candidates_for(reference, count=128, seed=99)
    chosen = d13.choose_operand(reference, count=128, seed=99)
    assert chosen in pool
    assert not d13.masking_risk(chosen, reference)
    allowed = [value for value in pool
               if not d13.masking_risk(value, reference)]
    scores = sorted(d13.score(value, reference) for value in allowed)
    chosen_score = d13.score(chosen, reference)
    assert allowed, "test pool must contain unmasked candidates"
    assert chosen_score >= scores[int(len(scores) * 0.95)]
    assert chosen_score == scores[-1]
