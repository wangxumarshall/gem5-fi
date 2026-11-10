"""Unit tests for the local operand heuristic (not upstream D13)."""

import pytest

from sdcfuzz import operand_heuristic as heuristic


def test_carry_chain_hand_examples():
    assert heuristic.carry_chain(0, 0) == 0
    assert heuristic.carry_chain(1, 1) == 1
    assert heuristic.carry_chain(0b11, 0b1) == 2
    assert heuristic.carry_chain(0b1000, 0b1000) == 1
    # All-ones plus one carries through every bit position.
    assert heuristic.carry_chain(heuristic.MASK64, 1) == 64


def test_toggle_bits_and_masking_risk():
    assert heuristic.toggle_bits(0, heuristic.MASK64) == 64
    assert heuristic.toggle_bits(0xF0, 0x0F) == 8
    assert heuristic.masking_risk(0, 123) is True
    assert heuristic.masking_risk(1, heuristic.MASK64) is True
    assert heuristic.masking_risk(0x1234, 0x1234) is True
    # Only a handful of differing bits: easily masked downstream.
    assert heuristic.masking_risk(0x1000, 0x1001) is True
    assert heuristic.masking_risk(0x00FF00FF00FF00FF, 0xFF00FF00FF00FF00) is False


def test_select_prefers_carry_chain_then_toggle():
    reference = 0x0000000000000001
    candidates = [0x0000000000000003, 0xFFFFFFFFFFFFFFFF, 0x00FF00FF00FF00FF]
    chosen = heuristic.select(candidates, reference=reference)
    allowed = [value for value in candidates
               if not heuristic.masking_risk(value, reference)]
    scores = {value: heuristic.score(value, reference) for value in allowed}
    assert chosen == max(allowed, key=lambda value: scores[value])
    assert chosen in candidates


def test_select_rejects_fully_masked_pools():
    with pytest.raises(ValueError):
        heuristic.select([0, 1], reference=0)
    with pytest.raises(ValueError):
        heuristic.select([], reference=0)


def test_select_validates_operands():
    with pytest.raises(TypeError):
        heuristic.select([1.5], reference=0)  # type: ignore[list-item]
    with pytest.raises(ValueError):
        heuristic.select([1 << 64], reference=0)


def test_candidates_are_deterministic_and_bounded():
    first = heuristic.candidates_for(0x1234, count=32, seed=7)
    second = heuristic.candidates_for(0x1234, count=32, seed=7)
    assert first == second
    assert len(first) == 32
    assert all(0 <= value <= heuristic.MASK64 for value in first)
    assert len(set(first)) > 16


def test_choose_operand_beats_random_pool_and_is_not_masked():
    reference = 0x00FF00FF00FF00FF
    pool = heuristic.candidates_for(reference, count=128, seed=99)
    chosen = heuristic.choose_operand(reference, count=128, seed=99)
    assert chosen in pool
    assert not heuristic.masking_risk(chosen, reference)
    allowed = [value for value in pool
               if not heuristic.masking_risk(value, reference)]
    scores = sorted(heuristic.score(value, reference) for value in allowed)
    chosen_score = heuristic.score(chosen, reference)
    assert allowed, "test pool must contain unmasked candidates"
    assert chosen_score >= scores[int(len(scores) * 0.95)]
    assert chosen_score == scores[-1]
