#!/usr/bin/env python3
"""loo_validate.py — fingerprint-library leave-one-out validation (plan §8.3).

For each observed XOR event: build the library from all OTHER events, look
up the held-out event's field mix, and check whether its true unit lands in
the Top-K candidates. Acceptance (§8.3): Top-3 hit rate >= 60% ⇒ the
library is diagnostically valid. Reuses sdc_fingerprint's build_library /
lookup (field classification is NOT rewritten here).

Usage:
  python3 tools/loo_validate.py --lib docs/paper/tables/fingerprint-library.json \
      [--masks unit:masks.txt ...] [--top 3] [--out docs/paper/tables/t7-loo-validation.md]
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdc_fingerprint import build_library, lookup   # reuse, do not rewrite

def loo_cross_validate(unit_masks, topk=3):
    """Leave-one-out over all XOR events across units.

    unit_masks: {unit_name: [xor values]}. For each event, the training
    library is built from every OTHER event; lookup ranks the candidate
    units by field-mix similarity. Returns per-unit and aggregate Top-1 /
    Top-K hit rates. A single-unit library is a trivial 100% (the only
    candidate always matches) — callers flag this honestly."""
    events = [(u, m) for u, masks in unit_masks.items() for m in masks]
    n = len(events)
    top1_hits = 0
    topk_hits = 0
    per_unit = {}
    for i, (true_unit, xor) in enumerate(events):
        # training set: all events except this one
        train = {}
        for j, (u2, m2) in enumerate(events):
            if j == i:
                continue
            train.setdefault(u2, []).append(m2)
        if not train:
            continue   # single event total: cannot validate
        lib = build_library(train)
        ranked = lookup(lib, xor)
        names = [u for u, _ in ranked[:topk]]
        pu = per_unit.setdefault(true_unit, {"n": 0, "top1": 0, "topk": 0})
        pu["n"] += 1
        if ranked and ranked[0][0] == true_unit:
            top1_hits += 1
            pu["top1"] += 1
        if true_unit in names:
            topk_hits += 1
            pu["topk"] += 1
    return {"top1_hit_rate": top1_hits / n if n else 0.0,
            "topk_hit_rate": topk_hits / n if n else 0.0,
            "topk": topk, "n_events": n, "per_unit": per_unit}

def render_markdown(res):
    lines = ["# 指纹库留一法验证（§8.3——Top-3 命中率 ≥60% 即有效）", "",
             f"- 事件数: {res['n_events']}",
             f"- Top-1 命中率: {res['top1_hit_rate']:.1%}",
             f"- Top-{res['topk']} 命中率: {res['topk_hit_rate']:.1%}",
             "",
             "| 单元 | 事件数 | Top-1 | Top-K |",
             "|---|---|---|---|"]
    for u, pu in sorted(res["per_unit"].items()):
        lines.append(f"| {u} | {pu['n']} | {pu['top1']} | {pu['topk']} |")
    verdict = "VALID (≥60%)" if res["topk_hit_rate"] >= 0.6 else "NOT VALID (<60%)"
    lines += ["", f"**验收判定: {verdict}**",
              "> 诚实边界：单单元库的 LOO 为平凡命中（唯一候选必中）；",
              "> 多单元判别力需扩充库（per-run xor 收集机制，后续）。"]
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", default=None, help="existing library JSON (info only)")
    ap.add_argument("--masks", nargs="*", default=[],
                    help="unit:masks_file pairs (one hex xor per line)")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    unit_masks = {}
    for spec in a.masks:
        unit, path = spec.split(":", 1)
        with open(path) as f:
            unit_masks[unit] = [int(line.strip(), 0) for line in f if line.strip()]
    if not unit_masks and a.lib and os.path.exists(a.lib):
        # single-unit library without raw masks: trivial LOO (recorded honestly)
        with open(a.lib) as f:
            unit_masks = {u: [0] * fp["n"] for u, fp in json.load(f).items()}
        print(f"[loo] WARNING: library {a.lib} has no raw masks; "
              f"single-unit trivial validation only", file=sys.stderr)
    if not unit_masks:
        sys.exit("[loo] no masks given (use --masks unit:file ...)")
    res = loo_cross_validate(unit_masks, topk=a.top)
    md = render_markdown(res)
    print(md)
    if a.out:
        with open(a.out, "w") as f:
            f.write(md + "\n")

if __name__ == "__main__":
    main()
