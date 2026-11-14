"""Unit tests for the 1-bit avalanche / logical-masking test."""

from sdcfuzz import avalanche, isa


def _mov(reg, value):
    return isa.Op("mov", dst=reg, imm=value)


def test_and_mask_masks_the_data_operand():
    # x12 is zero: flipping x8 (the data) is masked, while flipping x12
    # (the mask operand itself) changes the output.
    stream = avalanche.Stream(
        setup=(_mov("x8", 0xFF), _mov("x12", 0)),
        body=(isa.Op("and", dst="x8", a="x8", b="x12"),),
        iterations=1, reps=1)
    result = avalanche.avalanche(stream, bits=[0, 1, 2, 3])
    assert result.trials == 8
    assert result.per_register["x8"]["changed"] == 0
    assert result.per_register["x12"]["changed"] == 4
    assert result.masking_penalty == 0.5


def test_eor_propagates_every_bit():
    stream = avalanche.Stream(
        setup=(_mov("x8", 0x1234), _mov("x12", 0xAAAA)),
        body=(isa.Op("eor", dst="x8", a="x8", b="x12"),),
        iterations=1, reps=1)
    result = avalanche.avalanche(stream, bits=[0, 1, 2, 3])
    assert result.changed_trials == result.trials
    assert result.masking_penalty == 0.0
    assert result.avalanche_bit_ratio > 0.0


def test_dead_write_masks_the_input():
    # The body overwrites x8 without reading it; flipping x8 is invisible.
    stream = avalanche.Stream(
        setup=(_mov("x8", 0x1234),),
        body=(_mov("x8", 7),),
        iterations=2)
    result = avalanche.avalanche(stream, bits=[0, 1, 2, 3])
    assert result.masking_penalty == 1.0


def test_repeated_body_is_deterministic():
    stream = avalanche.template_stream("alu-add-carry", iterations=3)
    first = avalanche.avalanche(stream, bits=[0, 7, 15])
    second = avalanche.avalanche(stream, bits=[0, 7, 15])
    assert first.as_dict() == second.as_dict()


def test_all_templates_have_bounded_metrics():
    results, summary = avalanche.evaluate_all(iterations=2, bits=[0, 31, 63])
    assert len(results) == 19
    assert set(summary) == {"alu", "mult", "div", "l1d", "l1i", "fpadd",
                            "fpmul"}
    for row in results.values():
        assert 0.0 <= row["word_flip_ratio"] <= 1.0
        assert 0.0 <= row["masking_penalty"] <= 1.0
        assert row["trials"] > 0


def test_store_output_includes_memory_word():
    stream = avalanche.Stream(
        setup=(_mov("x8", 0xDEADBEEF),),
        body=(isa.Op("str", dst="x8", off=8),),
        iterations=2)
    result = avalanche.avalanche(stream, bits=[0, 1])
    assert "mem:1" in result.output_words
    assert result.changed_trials > 0


def test_bad_stream_rejected():
    try:
        avalanche.avalanche(avalanche.Stream(iterations=0))
    except ValueError as error:
        assert "iterations" in str(error)
    else:
        raise AssertionError("zero iterations must be rejected")
