#!/usr/bin/env python3
"""ed_select.py — 次模序列集选择器（SDC-ED Task 5.2）。

给定候选池（每条序列一份 stats.txt 派生的 7 维 A_u + CPU profile 的
w/ρ），贪心最大化加权覆盖：
    maximize Σ_u w_u·ρ_u·q_u · [1 − Π_{S∈T}(1 − A_u(S))]
选择 K 条 + per-unit 配额约束（quota_u ∝ w·ρ·gap，前 K 轮中每单元
至多 ceil(K·share) 条——防止全选同型序列堆叠）。

输出选择集 + 每条的选择理由（补了哪个单元的边际增益）。

用法：
  python3 tools/ed_select.py --pool dir1:dir2:... --profile yaml -k 10
  # dir 含 stats.txt（--cov 运行输出）；或 --manifest json
  # （{"seq": {"units": {...}}} 形态，便于合成数据单元测试）

理论依据：f(T) = Σ w·[1−Π(1−A_u)] 是关于 T 的单调次模函数
（每元素增加的边际增益随已选集增大而递减），贪心达 (1−1/e) 近似
最优——小规模可穷举对照（单测验证）。
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ed_profile import load_profile, UNITS  # noqa: E402
from ed_score import read_coverage  # noqa: E402


def coverage_gain(cov_selected, cov_candidate, w_rho):
    """边际增益：Δf = Σ_u wρ_u·([1−Π_S∈sel∪{c}(1−A_u)] − [1−Π_S∈sel(1−A_u)])
    = Σ_u wρ_u·Π_S∈sel(1−A_u(S))·A_u(c) —— 闭式，无需重算乘积。"""
    gain = 0.0
    for u in UNITS:
        gain += w_rho[u] * cov_selected.get(u, 1.0) * cov_candidate[u]
    return gain


def greedy_select(pool, k, w_rho, quotas=None):
    """pool: {name: {unit: A_u}}；返回 [(name, reason, gain), ...]。
    quotas: {unit: max_picks}——超配额的单元本条增益记 0（不硬禁，
    后续轮仍可选——软配额，理由：硬禁会在池枯竭时选空）。"""
    selected = []
    cov_selected = {u: 1.0 for u in UNITS}   # Π(1−A_u) 初值 1
    picked_per_unit = {u: 0 for u in UNITS}
    remaining = dict(pool)
    while len(selected) < k and remaining:
        best_name, best_gain, best_unit = None, -1.0, None
        for name, cov in remaining.items():
            # 该序列的最强贡献单元（理由展示）+ 软配额检查
            gains = {u: w_rho[u] * cov_selected[u] * cov[u] for u in UNITS}
            top_u = max(gains, key=gains.get)
            g = sum(gains.values())
            if quotas and top_u in quotas:
                if picked_per_unit[top_u] >= quotas[top_u]:
                    g = 0.0   # soft quota: this pick adds no novelty
            if g > best_gain:
                best_name, best_gain, best_unit = name, g, top_u
        if best_name is None or best_gain <= 0:
            break
        for u in UNITS:
            cov_selected[u] *= (1.0 - pool[best_name][u])
        picked_per_unit[best_unit] += 1
        selected.append((best_name, best_unit, best_gain))
        del remaining[best_name]
    return selected, cov_selected


def main():
    ap = argparse.ArgumentParser(description="Submodular sequence-set "
                                             "selector (SDC-ED Task 5.2)")
    ap.add_argument("--pool", default=None,
                    help="colon-separated stats dirs (each has stats.txt)")
    ap.add_argument("--manifest", default=None,
                    help="JSON {name: {unit: A_u}} (synthetic pools)")
    ap.add_argument("--profile", required=True)
    ap.add_argument("-k", type=int, default=10)
    ap.add_argument("--quota-share", type=float, default=0.4,
                    help="per-unit soft quota = ceil(k*share) picks whose "
                         "top unit is the same (anti-stacking)")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    prof = load_profile(args.profile)
    w = prof.weights()
    rho = prof.rho_initial()
    w_rho = {u: w[u] * rho.get(u, 0.0) for u in UNITS}

    pool = {}
    if args.manifest:
        pool = json.loads(Path(args.manifest).read_text())
    elif args.pool:
        for d in args.pool.split(":"):
            st = Path(d) / "stats.txt"
            name = Path(d).name
            if not st.exists():
                print(f"warn: {st} missing, skipped", file=sys.stderr)
                continue
            pool[name] = read_coverage(st.read_text())
    if not pool:
        ap.error("empty pool (need --pool or --manifest)")

    quotas = {u: math.ceil(args.k * args.quota_share) for u in UNITS}
    selected, cov_left = greedy_select(pool, args.k, w_rho, quotas)

    total_cov = {u: 1.0 - cov_left[u] for u in UNITS}
    obj = sum(w_rho[u] * total_cov[u] for u in UNITS)
    print(f"selected {len(selected)}/{len(pool)} candidates, "
          f"objective Σ wρ·coverage = {obj:.6f}")
    for i, (name, unit, gain) in enumerate(selected, 1):
        print(f"  {i:>2}. {name:<28} top-unit {unit:<4} marginal {gain:.6f}")
    print("per-unit achieved coverage:")
    for u in UNITS:
        if w_rho[u] > 0:
            print(f"  {u:<4} {total_cov[u]:.4f}  (wρ={w_rho[u]:.4f})")

    if args.json:
        Path(args.json).write_text(json.dumps({
            "selected": [{"name": n, "top_unit": u, "gain": g}
                         for n, u, g in selected],
            "coverage": total_cov, "objective": obj,
        }, indent=2))


if __name__ == "__main__":
    main()
