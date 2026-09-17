#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""harp_micro26.py — Micro'26 两个附加实验复现（计划 Task 7.3）。

(a) 种子敏感性（论文 Fig.5 等价）：最优指令序列 × K 个随机种子
    （重采 wrapper 的寄存器初值/立即数），每 variant 跑 SFI，
    报告 detection 分布（min/max/方差）。
    论文：多数组件 <1% 方差；int multiplier 最大 ~17%。
(b) 子序列截断（论文 Fig.6 等价）：序列取前缀 {0.1, 0.25, 0.5, 1.0}
    ×2 档重包装，FU permanent（L1）SFI，报告检测率 vs 前缀长度。
    论文：0.1× 前缀即可保持检测率（数百条指令）。

规模（计划 §五预算案）：每 cell N=10（Wilson CI ±~30%），
实验目标是与论文比较量级/趋势而非逐点，CI 内结论成立。
"""
import argparse
import os
import random
import re
import statistics as st
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
GEM5 = os.path.join(REPO, "CHAOS/gem5/build/ARM/gem5.opt")
SCRIPT = os.path.join(REPO, "smoke_test/configs/two_level_taishan.py")
WRAP = os.path.join(REPO, "tools/harp_wrap.py")
EVAL = os.path.join(REPO, "tools/harp_eval.py")

SUM_RE = re.compile(r"SUM=(\d+) CRC=([0-9a-f]+)")


def run_gem5(out_dir, cmd, timeout=300):
    os.makedirs(out_dir, exist_ok=True)
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        pass
    so = os.path.join(out_dir, "simout.txt")
    return open(so, errors="replace").read() if os.path.exists(so) else ""


def sfu_detection(elf, seed0, n, tmpdir, opclass, first_clock, tag):
    """N 次 FU permanent 注入的 detection。"""
    rng = random.Random(seed0)
    detected = 0
    for i in range(n):
        bit = rng.randint(0, 63)
        d = os.path.join(tmpdir, f"{tag}-{i}")
        txt = run_gem5(d, [GEM5, "-r", "-e", "--silent-redirect", "-d", d,
                           SCRIPT, "--binary", elf, "--mode", "baseline",
                           "--fu-perm", "--fu-perm-opclass", opclass,
                           "--fu-perm-mask", hex(1 << bit),
                           "--fu-perm-first-clock", str(first_clock)])
        m = SUM_RE.search(txt)
        # golden 对比在调用侧（每 elf 的 golden 不同）
        outcomes_file = os.path.join(d, "outcome")
        open(outcomes_file, "w").write(
            "CRASH" if (not m and "Exiting @ tick" not in txt)
            else (m.group(0) if m else "NOOUT"))
    # 汇总由调用侧做
    return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seq", required=True, help="最优序列（.S）")
    ap.add_argument("--k-seeds", type=int, default=10,
                    help="(a) 种子变体数（论文 50；预算案缩减）")
    ap.add_argument("--n-sfi", type=int, default=10,
                    help="每 variant SFI 次数（预算案）")
    ap.add_argument("--iters", type=int, default=200)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out = args.out or os.path.join(REPO, "artifacts", "harp-micro26")
    os.makedirs(out, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix="harp-m26-")

    lines = [l.strip() for l in open(args.seq)
             if l.strip() and not l.startswith("#")]

    # ============ (a) 种子敏感性 ============
    print(f"=== (a) 种子敏感性：{args.k_seeds} variants × "
          f"{args.n_sfi} SFI（intmul permanent）===")
    det_list = []
    for k in range(args.k_seeds):
        seed1 = 0x9510D3BF1AA8D548 + k * 0x9E37
        seed2 = 0xA5C11881A68E546E + k * 0x6C2B
        elf = os.path.join(tmpdir, f"var{k}")
        subprocess.run([sys.executable, WRAP, "--seq", args.seq,
                        "--out", elf, "--iters", str(args.iters),
                        "--reg-seed1", hex(seed1 & 0xFFFFFFFFFFFFFFFF),
                        "--reg-seed2", hex(seed2 & 0xFFFFFFFFFFFFFFFF)],
                       capture_output=True, timeout=120)
        # golden
        d = os.path.join(tmpdir, f"g{k}")
        txt = run_gem5(d, [GEM5, "-r", "-e", "--silent-redirect", "-d", d,
                           SCRIPT, "--binary", elf, "--mode", "baseline",
                           "--cov"])
        gm = SUM_RE.search(txt)
        golden = gm.group(0) if gm else None
        # ROI first_clock
        s = open(os.path.join(d, "stats.txt"), errors="replace").read()
        b = re.search(r"roiBeginTick\s+(\d+)", s)
        fc = int(b.group(1)) // 1000 if b else 20000
        # N 次 SFI（并行）
        rng = random.Random(9000 + k)
        bits = [rng.randint(0, 63) for _ in range(args.n_sfi)]
        def one(vi):
            di = os.path.join(tmpdir, f"v{k}-{vi}")
            txt = run_gem5(di, [GEM5, "-r", "-e", "--silent-redirect",
                                "-d", di, SCRIPT, "--binary", elf,
                                "--mode", "baseline", "--fu-perm",
                                "--fu-perm-opclass", "IntMult",
                                "--fu-perm-mask", hex(1 << bits[vi]),
                                "--fu-perm-first-clock", str(fc)])
            m = SUM_RE.search(txt)
            return 1 if ((m is None) or
                         (golden and m.group(0) != golden)) else 0
        with ThreadPoolExecutor(max_workers=12) as ex:
            det = sum(ex.map(one, range(args.n_sfi)))
        d_rate = det / args.n_sfi
        det_list.append(d_rate)
        print(f"  variant {k}: detection={d_rate:.2f} ({det}/{args.n_sfi})")

    mean = st.mean(det_list)
    var = (st.pstdev(det_list) if len(det_list) > 1 else 0.0)
    spread = (max(det_list) - min(det_list)) if det_list else 0

    # ============ (b) 前缀截断 ============
    print(f"=== (b) 前缀截断：4 档 × {args.n_sfi} SFI（intmul permanent）===")
    trunc_rows = []
    for frac in (0.1, 0.25, 0.5, 1.0):
        n_keep = max(1, int(len(lines) * frac))
        prefix = lines[:n_keep]
        elf = os.path.join(tmpdir, f"pre{frac}")
        subprocess.run([sys.executable, WRAP, "--seq", args.seq,
                        "--out", elf, "--iters",
                        str(max(1, int(args.iters / frac))),
                        ], capture_output=True, timeout=120)
        # 用前缀内容重写 .S（wrap 不支持子集，手写临时 S）
        # 简化：直接截 .S 文件内容再 wrap
        pre_s = os.path.join(tmpdir, f"pre{frac}.S")
        open(pre_s, "w").write("\n".join(prefix) + "\n")
        elf = os.path.join(tmpdir, f"pre{frac}elf")
        subprocess.run([sys.executable, WRAP, "--seq", pre_s, "--out", elf,
                        "--iters", str(args.iters)],
                       capture_output=True, timeout=120)
        d = os.path.join(tmpdir, f"pg{frac}")
        txt = run_gem5(d, [GEM5, "-r", "-e", "--silent-redirect", "-d", d,
                           SCRIPT, "--binary", elf, "--mode", "baseline",
                           "--cov"])
        gm = SUM_RE.search(txt)
        golden = gm.group(0) if gm else None
        s = open(os.path.join(d, "stats.txt"), errors="replace").read()
        b = re.search(r"roiBeginTick\s+(\d+)", s)
        fc = int(b.group(1)) // 1000 if b else 20000
        rng = random.Random(7000 + int(frac * 100))
        bits = [rng.randint(0, 63) for _ in range(args.n_sfi)]
        def one(vi):
            di = os.path.join(tmpdir, f"p{frac}-{vi}")
            txt = run_gem5(di, [GEM5, "-r", "-e", "--silent-redirect",
                                "-d", di, SCRIPT, "--binary", elf,
                                "--mode", "baseline", "--fu-perm",
                                "--fu-perm-opclass", "IntMult",
                                "--fu-perm-mask", hex(1 << bits[vi]),
                                "--fu-perm-first-clock", str(fc)])
            m = SUM_RE.search(txt)
            return 1 if ((m is None) or
                         (golden and m.group(0) != golden)) else 0
        with ThreadPoolExecutor(max_workers=12) as ex:
            det = sum(ex.map(one, range(args.n_sfi)))
        rate = det / args.n_sfi
        trunc_rows.append((frac, n_keep, rate))
        print(f"  prefix {frac:.2f}x ({n_keep} inst): detection={rate:.2f}")

    # ============ 报告 ============
    md = [f"# Micro'26 附加实验复现（{os.path.basename(args.seq)}）", "",
          f"预算口径：K={args.k_seeds} variants × N={args.n_sfi}"
          "（论文 50×更大 N；量级对比而非逐点，计划 §五）", "",
          "## (a) 种子敏感性（论文 Fig.5 等价）", "",
          f"- detection 均值: {mean:.4f}",
          f"- 标准差: {var:.4f}（论文：多数组件 <1%，int-mul 最大 ~17%）",
          f"- 极差 (max-min): {spread:.4f}",
          f"- 各 variant: {[f'{x:.2f}' for x in det_list]}",
          "",
          "## (b) 前缀截断（论文 Fig.6 等价）", "",
          "| 前缀比例 | 指令数 | detection |",
          "|----------|--------|-----------|"]
    for frac, n_keep, rate in trunc_rows:
        md.append(f"| {frac:.2f}x | {n_keep} | {rate:.2f} |")
    md += ["",
           "论文：permanent gate-level 故障在 0.1× 前缀（数百条指令）"
           "即可保持检测率。"]
    open(os.path.join(out, "summary.md"), "w").write("\n".join(md) + "\n")
    print()
    print("\n".join(md))
    print(f"\nartifacts: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
