#!/usr/bin/env python3
"""ed_score.py — ED 评分器（SDC-ED Task 5.1，Layer A 收口）。

输入（三源）：
  1. stats.txt（--cov 运行的 gem5 stats；读 harp.covUnits 7 维向量 +
     per-collector 标量 + SDC-ACE/gap + 值类熵 + 敏感度）
  2. CPU 描述 YAML（ed_profile.load_profile：w_u / ρ 初值 / ceiling）
  3. ρ 实测表（可选 --rho-measured，Task 6.1 calibration-report 回填；
     优先于初值；YAML rho_overrides 恒最高优先）

输出：
  ED(S) = Σ_u w_u · ρ_u · q_u · A_u(S)   （q 默认 1.0 = golden-diff）
  per-unit 分解表（决策必须附 7 维分解——单标量只用于排序）
  校准锚对齐表（给定覆盖率表 c_u 的相对序复现检查）
  gap 配额建议（w·ρ·(ceiling−A) 排序的「下一步补哪个单元」）

用法：
  python3 tools/ed_score.py --stats <dir>/stats.txt \
      --profile configs/cpu-profiles/taishan-v110.yaml [--json out.json]

诚实边界（method.md §4）：
  - A_IFU/A_MMU = 0 占位（Crash 轴 / SE 封顶），ED 对这两单元贡献 0
    ——这不是「序列无覆盖」而是「该轴不可达」，报告单列。
  - ρ 未实测的单元用保护矩阵推导初值（标注 uncertainty）。
  - A_OoO 此版消费 irfAvf（裸 ACE）——SDC-ACE（irfAvfSdc）落地后可
    用 --ooo-sdc 切换；两者差值即该序列 OoO 轴的松量。
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ed_profile import load_profile, UNITS as UNIT_KEYS  # noqa: E402

# 校准锚（用户给定覆盖率表，Spec 2026-09-19；method.md §3.2）
CALIB_ANCHOR = {
    "FSU": 0.80, "IEX": 0.70, "IFU": 0.66, "OoO": 0.56,
    "LSU": 0.54, "L2C": 0.40, "MMU": 0.20,
}


def read_stat(stats_text, key):
    """system.CHAOSCov.harp.<key>  <value>  # desc"""
    m = re.search(rf"system\.CHAOSCov\.harp\.{key}\s+([\d.eE+-]+)", stats_text)
    return float(m.group(1)) if m else None


def read_coverage(stats_text):
    """从 stats 提取 7 维 A_u + 诊断标量。covUnits 缺失时从旧标量归并
    （与 CHAOSCov.cc finishStats 的 Task 2.3 映射一致）。"""
    cov = {}
    for u in UNIT_KEYS:
        m = re.search(rf"system\.CHAOSCov\.harp\.covUnits::{u}\s+([\d.eE+-]+)",
                      stats_text)
        cov[u] = float(m.group(1)) if m else None
    if all(v is None for v in cov.values()):
        # fallback: legacy scalars (Task 2.3 mapping)
        irf = read_stat(stats_text, "irfAvf") or 0.0
        l1d = read_stat(stats_text, "l1dAvf") or 0.0
        l2c_a = read_stat(stats_text, "l2cAvf") or 0.0
        cov = {
            "IFU": 0.0, "MMU": 0.0,
            "OoO": irf,
            "IEX": max(read_stat(stats_text, "ibrIntAdd") or 0.0,
                       read_stat(stats_text, "ibrIntMul") or 0.0),
            "LSU": read_stat(stats_text, "sqAvf") or 0.0,
            "FSU": max(read_stat(stats_text, "ibrFpAdd") or 0.0,
                       read_stat(stats_text, "ibrFpMul") or 0.0),
            "L2C": max(l1d, l2c_a),
        }
    return {u: (v or 0.0) for u, v in cov.items()}


def load_rho_measured(path):
    """Task 6.1 calibration-report 的 rho_measured 块（YAML/JSON 均可）。"""
    with open(path) as f:
        data = json.load(f) if path.endswith(".json") else None
        if data is None:
            import yaml
            f.seek(0)
            data = yaml.safe_load(f)
    return {k: float(v) for k, v in (data or {}).items()}


def main():
    ap = argparse.ArgumentParser(description="ED scorer (SDC-ED Task 5.1)")
    ap.add_argument("--stats", required=True, help="stats.txt path")
    ap.add_argument("--profile", required=True, help="cpu-profile YAML")
    ap.add_argument("--rho-measured", default=None,
                    help="rho_measured table (overrides profile initials; "
                         "rho_overrides in the YAML still win)")
    ap.add_argument("--ooo-sdc", action="store_true",
                    help="use irfAvfSdc (SDC-ACE) for the OoO axis instead "
                         "of the raw irfAvf")
    ap.add_argument("--q", default=None,
                    help="checker observability JSON {unit: q_u} "
                         "(default 1.0 = golden-diff)")
    ap.add_argument("--json", default=None, help="write machine-readable out")
    args = ap.parse_args()

    stats_text = Path(args.stats).read_text()
    prof = load_profile(args.profile)
    w = prof.weights()
    rho = prof.rho_initial()
    if args.rho_measured:
        rho.update(load_rho_measured(args.rho_measured))
    # YAML explicit overrides win over everything (schema.md rule)
    ov = (getattr(prof, "raw", {}) or {}).get("rho_overrides") or {}
    for k, v in ov.items():
        rho[k] = float(v)
    q = {u: 1.0 for u in UNIT_KEYS}
    if args.q:
        q.update(json.loads(Path(args.q).read_text()))

    cov = read_coverage(stats_text)
    if args.ooo_sdc:
        sdc = read_stat(stats_text, "irfAvfSdc")
        if sdc is not None:
            cov["OoO"] = sdc

    # ED + per-unit decomposition + effective coverage (ceiling-capped)
    rows = []
    ed = 0.0
    for u in UNIT_KEYS:
        ceil_u = prof.ceiling(u)
        a_eff = min(cov[u], ceil_u)
        contrib = w[u] * rho.get(u, 0.0) * q[u] * a_eff
        ed += contrib
        rows.append({
            "unit": u, "A": cov[u], "ceiling": ceil_u, "A_eff": a_eff,
            "w": w[u], "rho": rho.get(u, 0.0), "q": q[u],
            "contribution": contrib,
            "gap_quota": w[u] * rho.get(u, 0.0) * max(0.0, ceil_u - a_eff),
        })

    # Calibration-anchor alignment: relative order of A_eff (SDC 轴上
    # IFU/MMU 恒 0，对齐检查只在可活动 5 单元上做)
    active = [r for r in rows if r["unit"] in ("OoO", "IEX", "LSU", "FSU", "L2C")]
    got_order = [r["unit"] for r in sorted(active, key=lambda r: -r["A_eff"])]
    exp_order = [u for u in sorted(("OoO", "IEX", "LSU", "FSU", "L2C"),
                                   key=lambda u: -CALIB_ANCHOR[u])]
    matches = sum(1 for a, b in zip(got_order, exp_order) if a == b)

    # Report
    print(f"ED = {ed:.6f}   (profile: {args.profile})")
    print(f"{'unit':<5} {'A_u':>10} {'ceil':>6} {'A_eff':>10} {'w_u':>8} "
          f"{'rho_u':>7} {'q_u':>4} {'contrib':>10} {'gap_quota':>10}")
    for r in sorted(rows, key=lambda r: -r["contribution"]):
        print(f"{r['unit']:<5} {r['A']:>10.6f} {r['ceiling']:>6.2f} "
              f"{r['A_eff']:>10.6f} {r['w']:>8.4f} {r['rho']:>7.4f} "
              f"{r['q']:>4.2f} {r['contribution']:>10.6f} "
              f"{r['gap_quota']:>10.6f}")
    print(f"\nanchor alignment (5 active units): {matches}/5 positions match "
          f"the c_u relative order")
    print("top gap quotas (next-unit advice):",
          ", ".join(f"{r['unit']}({r['gap_quota']:.4f})"
                    for r in sorted(rows, key=lambda r: -r["gap_quota"])[:3]))

    if args.json:
        Path(args.json).write_text(json.dumps({
            "ED": ed, "units": rows, "cov": cov, "rho": rho, "weights": w,
            "anchor_matches": matches,
        }, indent=2))
        print(f"[json] {args.json}")


if __name__ == "__main__":
    main()
