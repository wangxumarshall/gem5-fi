"""Power-stress vs SDC correlation and H1–H3 tests (sdcfuzz-v1.2 §5.3).

Inputs are two JSON files produced by the Phase-2 evidence pipeline:

``power_measurements.json``
    ``{"streams": {name: {"pattern": "type1|type2|type3",
                          "structure": "fpadd|fpmul|...",
                          "power": {average, peak, variance, slope, stress},
                          "mcpat": {"status": "ok", "dynamic_power_w": ...}}}}``
``fi_results.json``
    ``{"streams": {name: {"sdc": k, "n": n, ...}}}``

The module computes Pearson and Spearman correlations (NumPy only; no SciPy),
permutation p-values, and the three hypotheses:

H1  higher power -> higher SDC vulnerability (correlation across streams)
H2  Type-II power oscillation triggers more SDC than Type-I continuous
H3  Type-III single-structure hotspot triggers more SDC than Type-I global

All tests are two-sided and seeded, so the report is reproducible.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import numpy as np


def pearson(x, y) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 2 or x.std() == 0 or y.std() == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def _rank(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    sorted_values = values[order]
    index = 0
    while index < len(values):
        end = index + 1
        while end < len(values) and sorted_values[end] == sorted_values[index]:
            end += 1
        rank = (index + end - 1) / 2.0 + 1.0
        ranks[order[index:end]] = rank
        index = end
    return ranks


def spearman(x, y) -> float:
    return pearson(_rank(x), _rank(y))


def permutation_corr_p(x, y, observed: float, trials: int = 10000,
                       seed: int = 20260825) -> float:
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    count = 0
    for _ in range(trials):
        shuffled = rng.permutation(y)
        if abs(pearson(x, shuffled)) >= abs(observed) - 1e-12:
            count += 1
    return (count + 1.0) / (trials + 1.0)


def permutation_diff_p(left, right, trials: int = 10000,
                       seed: int = 20260825) -> float:
    left = list(left)
    right = list(right)
    if not left or not right:
        return 1.0
    observed = abs(sum(left) / len(left) - sum(right) / len(right))
    pooled = left + right
    rng = random.Random(seed)
    count = 0
    for _ in range(trials):
        rng.shuffle(pooled)
        a = pooled[:len(left)]
        b = pooled[len(left):]
        if abs(sum(a) / len(a) - sum(b) / len(b)) >= observed - 1e-12:
            count += 1
    return (count + 1.0) / (trials + 1.0)


def fisher_2x2(a, b, c, d):
    """Two-sided Fisher exact test for [[a,b],[c,d]] (log-space)."""
    n = a + b + c + d
    r1, c1 = a + b, a + c
    if n == 0:
        return 1.0

    def lg(x):
        return math.lgamma(x + 1)

    def pl(k):
        return (lg(c1) + lg(n - c1) - lg(k) - lg(c1 - k)
                - lg(r1 - k) - lg(n - c1 - r1 + k) - lg(n) + lg(r1)
                + lg(n - r1))

    observed = pl(a)
    lo, hi = max(0, r1 - (n - c1)), min(r1, c1)
    values = [pl(k) for k in range(lo, hi + 1)
              if pl(k) <= observed + 1e-9]
    peak = max(values)
    return min(1.0, math.exp(peak + math.log(
        sum(math.exp(value - peak) for value in values))))


def _rate(record):
    n = record.get("n", 0)
    return record.get("sdc", 0) / n if n else None


def analyze(power_payload: dict, fi_payload: dict,
            trials: int = 10000, seed: int = 20260825) -> dict:
    power_streams = power_payload.get("streams", {})
    fi_streams = fi_payload.get("streams", {})
    records = []
    for name, power_row in power_streams.items():
        fi_row = fi_streams.get(name)
        if not fi_row:
            continue
        rate = _rate(fi_row)
        if rate is None:
            continue
        records.append({
            "stream": name,
            "pattern": power_row.get("pattern", "unknown"),
            "structure": power_row.get("structure", "unknown"),
            "power": power_row.get("power", {}),
            "mcpat": power_row.get("mcpat", {}),
            "sdc": fi_row.get("sdc", 0),
            "n": fi_row.get("n", 0),
            "rate": rate,
        })
    if not records:
        raise SystemExit("no overlapping streams with SDC data")

    # H1: power features vs SDC rate across streams.
    h1 = {}
    for feature in ("average", "peak", "variance", "slope", "stress"):
        values = [row["power"].get(feature, 0.0) for row in records]
        rates = [row["rate"] for row in records]
        p = pearson(values, rates)
        s = spearman(values, rates)
        h1[feature] = {
            "pearson": round(p, 6),
            "spearman": round(s, 6),
            "permutation_p": round(permutation_corr_p(values, rates, p,
                                                      trials, seed), 6),
        }
    mcpat_records = [row for row in records
                     if row["mcpat"].get("status") == "ok"]
    if len(mcpat_records) >= 3:
        values = [row["mcpat"]["dynamic_power_w"] for row in mcpat_records]
        rates = [row["rate"] for row in mcpat_records]
        p = pearson(values, rates)
        h1["mcpat_dynamic_power_w"] = {
            "pearson": round(p, 6),
            "spearman": round(spearman(values, rates), 6),
            "permutation_p": round(permutation_corr_p(values, rates, p,
                                                      trials, seed), 6),
            "n": len(mcpat_records),
        }

    def paired(pattern_a, pattern_b):
        pairs = []
        for structure in sorted({row["structure"] for row in records}):
            left = [row["rate"] for row in records
                    if row["structure"] == structure
                    and row["pattern"] == pattern_a]
            right = [row["rate"] for row in records
                     if row["structure"] == structure
                     and row["pattern"] == pattern_b]
            if left and right:
                pairs.append({"structure": structure,
                              f"{pattern_a}_mean": sum(left) / len(left),
                              f"{pattern_b}_mean": sum(right) / len(right),
                              "delta": sum(right) / len(right)
                              - sum(left) / len(left)})
        if not pairs:
            return {"pairs": [], "summary": "no paired streams"}
        deltas = [pair["delta"] for pair in pairs]
        # Aggregate run-level 2x2 counts for a Fisher exact test.
        a_sdc = sum(row["sdc"] for row in records
                    if row["pattern"] == pattern_a)
        a_n = sum(row["n"] for row in records
                  if row["pattern"] == pattern_a)
        b_sdc = sum(row["sdc"] for row in records
                    if row["pattern"] == pattern_b)
        b_n = sum(row["n"] for row in records
                  if row["pattern"] == pattern_b)
        return {
            "pairs": pairs,
            "mean_delta": round(sum(deltas) / len(deltas), 6),
            "positive_pairs": sum(1 for value in deltas if value > 0),
            "pairs_count": len(deltas),
            "permutation_p": round(permutation_diff_p(
                [pair[f"{pattern_b}_mean"] for pair in pairs],
                [pair[f"{pattern_a}_mean"] for pair in pairs],
                trials, seed), 6),
            "counts": {pattern_a: [a_sdc, a_n - a_sdc],
                       pattern_b: [b_sdc, b_n - b_sdc]},
            "fisher_p": round(fisher_2x2(a_sdc, a_n - a_sdc,
                                         b_sdc, b_n - b_sdc), 6),
        }

    h2 = paired("type1", "type2")
    h3 = paired("type3", "type1")
    return {
        "schema": "sdcfuzz.power_sdc.v1",
        "records": records,
        "h1_power_vs_sdc": h1,
        "h2_oscillation_vs_continuous": h2,
        "h3_hotspot_vs_global": h3,
        "trials": trials,
        "seed": seed,
    }


def render_markdown(payload: dict) -> str:
    lines = ["# 功耗应力—SDC 相关性（Phase 2）", "",
             "| 流 | 模式 | 结构 | 平均功耗 | 峰值 | 方差 | SDC | n | SDC 率 |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in payload["records"]:
        p = row["power"]
        lines.append(
            f"| {row['stream']} | {row['pattern']} | {row['structure']} | "
            f"{p.get('average', 0):.2f} | {p.get('peak', 0):.2f} | "
            f"{p.get('variance', 0):.2f} | {row['sdc']} | {row['n']} | "
            f"{row['rate']:.3f} |")
    lines += ["", "## H1：功耗越高 → SDC 越强", "",
              "| 特征 | Pearson | Spearman | 置换 p |",
              "|---|---:|---:|---:|"]
    for feature, row in payload["h1_power_vs_sdc"].items():
        lines.append(f"| {feature} | {row['pearson']:+.4f} | "
                     f"{row['spearman']:+.4f} | {row['permutation_p']:.4g} |")
    for key, title in (("h2_oscillation_vs_continuous",
                        "H2：Type-II 功耗跳变 > Type-I 持续高功耗"),
                       ("h3_hotspot_vs_global",
                        "H3：Type-III 单结构热点 > Type-I 全局")):
        section = payload[key]
        lines += ["", f"## {title}", ""]
        if not section["pairs"]:
            lines.append("无配对数据。")
            continue
        lines.append("| 结构 | Type-I | Type-II/III | Δ |")
        lines.append("|---|---:|---:|---:|")
        for pair in section["pairs"]:
            left_key = next(key for key in pair if key.endswith("_mean")
                            and not key.startswith("type2")
                            and not key.startswith("type3"))
            right_key = next(key for key in pair if key.endswith("_mean")
                             and key != left_key)
            lines.append(f"| {pair['structure']} | {pair[left_key]:.3f} | "
                         f"{pair[right_key]:.3f} | {pair['delta']:+.3f} |")
        lines.append(f"\n平均 Δ = {section['mean_delta']:+.4f}，"
                     f"正向配对 {section['positive_pairs']}/"
                     f"{section['pairs_count']}，置换 p = "
                     f"{section['permutation_p']:.4g}。")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--power", type=Path,
                        default=Path("m5out/phase2-power/power_measurements.json"))
    parser.add_argument("--fi", type=Path,
                        default=Path("m5out/phase2-power/fi_results.json"))
    parser.add_argument("--out", type=Path,
                        default=Path("m5out/phase2-power/correlation.json"))
    parser.add_argument("--trials", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260825)
    args = parser.parse_args(argv)
    payload = analyze(json.loads(args.power.read_text()),
                      json.loads(args.fi.read_text()),
                      args.trials, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    markdown = render_markdown(payload)
    (args.out.parent / "correlation.md").write_text(markdown)
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
