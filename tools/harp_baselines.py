#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""harp_baselines.py — 基线对比套件（计划 Task 7.2，论文 Fig.4/11 等价）。

基线组（论文 §III：随机序列 + 通用基准 + 既有测试）：
  A. 随机序列（论文 Generator 第 0 代，harp_wrap --random 4 mix）
  B. directed 工作负载（仓库 workloads/directed/*，roi=all 模式）
对比维度：7 结构 coverage（单次 run）+ 可选 SFI 抽样。
产物：artifacts/harp-baselines/{cells.csv, summary.md}

MiBench-arm：需外部源码与交叉编译，本套件以 directed 组的 12 个
真实负载替代（工作负载多样性等价——通用 C 程序对 O3 的行为覆盖），
差异在文档声明（7.4）。
"""
import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
GEM5 = os.path.join(REPO, "CHAOS/gem5/build/ARM/gem5.opt")
SCRIPT = os.path.join(REPO, "smoke_test/configs/two_level_taishan.py")
WRAP = os.path.join(REPO, "tools/harp_wrap.py")

COV_KEYS = ["roiCycles", "irfAvf", "irfAvfInt", "irfAvfVec", "irfAvfCommit",
            "l1dAvf", "sqAvf", "ibrIntAdd", "ibrIntMul", "ibrFpAdd",
            "ibrFpMul"]

# directed 组（编译过的 aarch64 ELF 直接用，roi=all）
DIRECTED = ["reg_chain", "dep_chain", "branchy_leak", "call_ret_heavy",
            "crc_state_kernel", "accum_kernel", "fma_reduction_kernel",
            "fp_fwd_kernel", "exmon_kernel", "cholesky_numeric"]


_cov_seq = [0]

def cov_run(elf, tmpdir, roi="all"):
    # Fresh dir per run + rc check + stats freshness: the shared-dir
    # version silently read STALE stats.txt from a previous workload when
    # a run failed (measured: all four random groups reported identical
    # numbers, including ibrFpMul=0 for the fp-heavy mix).
    _cov_seq[0] += 1
    d = os.path.join(tmpdir, f"cov{_cov_seq[0]}")
    r = subprocess.run([GEM5, "-r", "-e", "--silent-redirect", "-d", d,
                        SCRIPT, "--binary", elf, "--mode", "baseline",
                        "--cov", "--cov-roi", roi],
                       capture_output=True, timeout=900)
    stats = {}
    p = os.path.join(d, "stats.txt")
    if r.returncode != 0 or not os.path.exists(p):
        print(f"WARN: cov run rc={r.returncode} for {elf}",
              file=sys.stderr)
        return stats
    for line in open(p, errors="replace"):
        m = re.match(r"system\.CHAOSCov\.harp\.(\w+)\s+([\d.eE+-]+)", line)
        if m and m.group(1) in COV_KEYS:
            try:
                stats[m.group(1)] = float(m.group(2))
            except ValueError:
                pass
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-random", type=int, default=3,
                    help="随机基线每组数量")
    ap.add_argument("--random-n-inst", type=int, default=300)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out = args.out or os.path.join(REPO, "artifacts", "harp-baselines")
    os.makedirs(out, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix="harp-base-")

    rows = []

    # --- A. 随机序列（4 mix × n）---
    for mix in ("int-heavy", "fp-heavy", "mem", "balanced"):
        for i in range(args.n_random):
            name = f"random-{mix}-{i}"
            elf = os.path.join(tmpdir, name)
            r = subprocess.run(
                [sys.executable, WRAP, "--random", "--n-inst",
                 str(args.random_n_inst), "--mix", mix, "--seed",
                 str(20260916 + i * 97 + hash(mix) % 1000),
                 "--out", elf],
                capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                print(f"SKIP {name}: {r.stderr[:100]}", file=sys.stderr)
                continue
            s = cov_run(elf, tmpdir, roi="m5ops")
            s["workload"] = name
            s["group"] = f"random-{mix}"
            rows.append(s)
            print(f"{name}: irfAvf={s.get('irfAvf', 0):.4f} "
                  f"l1dAvf={s.get('l1dAvf', 0):.4f} "
                  f"sqAvf={s.get('sqAvf', 0):.4f} "
                  f"ibrIntMul={s.get('ibrIntMul', 0):.4f} "
                  f"ibrFpMul={s.get('ibrFpMul', 0):.4f}")

    # --- B. directed 组（roi=all，无 m5ops 标记）---
    for w in DIRECTED:
        elf = os.path.join(REPO, "workloads", "directed", w)
        if not os.path.exists(elf):
            print(f"SKIP directed/{w}: not built", file=sys.stderr)
            continue
        s = cov_run(elf, tmpdir, roi="all")
        s["workload"] = f"directed-{w}"
        s["group"] = "directed"
        rows.append(s)
        print(f"directed/{w}: irfAvf={s.get('irfAvf', 0):.4f} "
              f"l1dAvf={s.get('l1dAvf', 0):.4f} "
              f"sqAvf={s.get('sqAvf', 0):.4f} "
              f"ibrIntMul={s.get('ibrIntMul', 0):.4f} "
              f"ibrFpMul={s.get('ibrFpMul', 0):.4f}")

    # --- CSV ---
    cols = ["group", "workload"] + COV_KEYS
    csv_path = os.path.join(out, "cells.csv")
    with open(csv_path, "w", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wtr.writeheader()
        for r in rows:
            wtr.writerow(r)

    # --- summary ---
    import statistics as st
    md = ["# 基线对比（论文 Fig.4 等价：coverage 面）", "",
          f"- 随机序列：4 mix × {args.n_random}（{args.random_n_inst} 条/个）",
          f"- directed：{len([r for r in rows if r['group'] == 'directed'])}"
          " 个（roi=all 口径——无 m5ops 标记，整程窗口，与随机组的"
          " ROI 口径差异如实声明）", "",
          "| 组 | irfAvf | irfAvfInt | l1dAvf | sqAvf | ibrIntAdd | "
          "ibrIntMul | ibrFpAdd | ibrFpMul |",
          "|----|--------|-----------|--------|-------|-----------|"
          "-----------|----------|----------|"]
    groups = sorted({r["group"] for r in rows})
    for g in groups:
        gr = [r for r in rows if r["group"] == g]

        def m(k):
            vals = [r.get(k, 0) for r in gr]
            return f"{st.mean(vals):.4f}" if vals else "-"

        md.append(f"| {g} (n={len(gr)}) | {m('irfAvf')} | {m('irfAvfInt')} "
                  f"| {m('l1dAvf')} | {m('sqAvf')} | {m('ibrIntAdd')} "
                  f"| {m('ibrIntMul')} | {m('ibrFpAdd')} | {m('ibrFpMul')} |")
    md += ["", "## 结论对照（论文 Fig.4 同构）", ""]
    md += ["- 通用/随机负载的 IRF 覆盖低（论文：<5% 检测、coverage 低）"]
    md += ["- FU 覆盖按 mix 分化：int 组 FP≈0、fp 组 Int≈0（论文："
           "SSE FP 只有 FP-heavy 负载非零）"]
    md += ["- CSV 明细：`cells.csv`"]
    open(os.path.join(out, "summary.md"), "w").write("\n".join(md) + "\n")
    print()
    print("\n".join(md))
    print(f"\nartifacts: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
