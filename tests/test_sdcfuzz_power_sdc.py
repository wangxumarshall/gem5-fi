"""Unit tests for Pearson/Spearman, Fisher and the H1–H3 analysis."""

from sdcfuzz import power_sdc


def test_pearson_and_spearman_extremes():
    x = [1, 2, 3, 4, 5]
    assert abs(power_sdc.pearson(x, x) - 1.0) < 1e-12
    assert abs(power_sdc.pearson(x, [-v for v in x]) + 1.0) < 1e-12
    assert abs(power_sdc.spearman(x, [v ** 3 for v in x]) - 1.0) < 1e-12
    assert power_sdc.pearson([1, 1, 1], x) == 0.0


def test_spearman_handles_ties():
    # Ranks: x -> 1.5,1.5,3 ; y -> 1,2,3
    value = power_sdc.spearman([10, 10, 20], [1, 2, 3])
    assert 0.0 < value < 1.0


def test_fisher_extreme_and_null():
    assert power_sdc.fisher_2x2(10, 0, 0, 10) < 1e-4
    assert power_sdc.fisher_2x2(5, 5, 5, 5) > 0.99


def _payloads():
    power = {"streams": {}}
    fi = {"streams": {}}
    for structure in ("fpadd", "fpmul"):
        for pattern, rate in (("type1", 4), ("type2", 8), ("type3", 7)):
            name = f"{pattern}-{structure}"
            power["streams"][name] = {
                "pattern": pattern, "structure": structure,
                "power": {"average": 2.0 if pattern == "type2" else 4.0,
                          "peak": 6.0 if pattern == "type2" else 4.0,
                          "variance": 4.0 if pattern == "type2" else 0.0,
                          "slope": 0.0, "stress": 0.5},
                "mcpat": {"status": "ok", "dynamic_power_w": 80.0},
            }
            fi["streams"][name] = {"sdc": rate, "n": 10}
    return power, fi


def test_analyze_produces_h1_h2_h3():
    power, fi = _payloads()
    payload = power_sdc.analyze(power, fi, trials=200)
    assert len(payload["records"]) == 6
    assert set(payload["h1_power_vs_sdc"]) >= {"average", "peak", "variance",
                                               "slope"}
    assert payload["h2_oscillation_vs_continuous"]["pairs_count"] == 2
    assert payload["h2_oscillation_vs_continuous"]["positive_pairs"] == 2
    assert payload["h3_hotspot_vs_global"]["pairs_count"] == 2
    assert 0.0 <= payload["h2_oscillation_vs_continuous"]["fisher_p"] <= 1.0


def test_render_markdown_has_sections():
    power, fi = _payloads()
    payload = power_sdc.analyze(power, fi, trials=100)
    markdown = power_sdc.render_markdown(payload)
    assert "H1" in markdown
    assert "H2" in markdown
    assert "H3" in markdown
    assert "fpadd" in markdown
