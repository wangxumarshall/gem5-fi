"""Unit tests for the three power-stress pattern families and McPAT adapter."""

from pathlib import Path

from sdcfuzz import power


def test_type1_is_continuous_high_power():
    stream = power.type1_continuous("fpmul", iterations=10)
    features = power.power_features(stream)
    assert len(stream.body) == 1
    assert stream.body[0].kind == "fmul"
    assert features.variance == 0.0
    assert features.average == 1.5


def test_type2_oscillates_and_has_variance():
    stream = power.type2_oscillation("fpmul", period=8, duty=0.5,
                                     iterations=10)
    features = power.power_features(stream)
    kinds = {op.kind for op in stream.body}
    assert kinds == {"mov", "fmul"}
    assert len(stream.body) == 8
    assert features.variance > 0.0
    # The square wave has a high phase, so a short rolling window sees it.
    assert features.peak > features.average


def test_type2_rejects_bad_parameters():
    for period, duty in ((1, 0.5), (7, 0.5), (8, 0.0), (8, 1.0)):
        try:
            power.type2_oscillation("fpadd", period=period, duty=duty)
        except ValueError:
            pass
        else:
            raise AssertionError((period, duty))


def test_type3_is_a_single_structure_hotspot():
    stream = power.type3_hotspot("fpadd", copies=16, iterations=4)
    assert len(stream.body) == 16
    assert {op.kind for op in stream.body} == {"fadd"}


def test_default_streams_cover_three_types_and_nine_streams():
    streams = power.default_streams()
    assert len(streams) == 9
    patterns = {name.split("-")[0] for name in streams}
    assert patterns == {"type1", "type2", "type3"}
    assert any(name.endswith("l1d") for name in streams)


def test_as_template_round_trip():
    stream = power.type1_continuous("div", iterations=3)
    template = power.as_template(stream, "p", "div")
    assert template.id == "p"
    assert template.body == stream.body
    # The generator's interpreter must accept every op.
    from sdcfuzz import isa
    assert isa.expected_checksum(template, 1) >= 0


def test_mcpat_missing_path_returns_structured_error(tmp_path):
    result = power.mcpat_power(Path("/definitely/not/a/m5out"))
    assert result["status"] == "unavailable"
    assert "reason" in result
