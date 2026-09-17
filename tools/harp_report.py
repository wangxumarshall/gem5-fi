#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""harp_report.py — 单命令端到端报告（计划 Task 7.1，用户目标的最终形态）。

对给定指令流序列输出一份 markdown 报告：
  1. 7 结构微架构覆盖量化值（单次 --cov run：IRF/L1D/LSQ 的 ACE
     [含 commit-confirmed 双口径] + 4 FU 的 IBR，公式口径注明）
  2. （--sfi N 时）SFI 检测能力：detection + Wilson 95% CI +
     四类细分（调用 harp_eval）
  3. 变异改进建议 Top-K（调用 harp_advice 规则引擎）

用法：
  python3 tools/harp_report.py --seq workloads/harp/sample_seq.S
  python3 tools/harp_report.py --seq old_aarch64.elf --sfi 30
  python3 tools/harp_report.py --seq seq.S --out report.md --sfi 30
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
GEM5 = os.path.join(REPO, "CHAOS/gem5/build/ARM/gem5.opt")
SCRIPT = os.path.join(REPO, "smoke_test/configs/two_level_taishan.py")
WRAP = os.path.join(REPO, "tools/harp_wrap.py")
EVAL = os.path.join(REPO, "tools/harp_eval.py")
ADVICE = os.path.join(REPO, "tools/harp_advice.py")

STAT_ROWS = [
    ("roiCycles", "ROI 周期数（m5ops workbegin..workend）", "-"),
    ("irfAvf", "IRF AVF（int+float+vec 加权，ACE 上界）", "ACE = Σ区间/(bits×T)"),
    ("irfAvfInt", "IRF AVF（int 空间 125 regs）", "同上，int 空间口径"),
    ("irfAvfVec", "IRF AVF（vec 空间 96 regs，AArch64 FP/SIMD 实际驻留）", "同上，vec 空间"),
    ("irfAvfCommit", "IRF AVF（commit-confirmed，wrong-path 剔除）", "提交视角口径"),
    ("l1dAvf", "L1D AVF（1024 blocks，块粒度）", "ACE = Σ[block 出生,最后读]/(blocks×T)"),
    ("sqAvf", "LSQ SQ-data AVF（47 entries）", "ACE = Σ[store 写入,消费]/(entries×T)"),
    ("ibrIntAdd", "IBR IntAdd（128b×3 FU）", "输入位/(满宽×FU×T)"),
    ("ibrIntMul", "IBR IntMul（128b×1 FU）", "同上"),
    ("ibrFpAdd", "IBR FPAdd（256b×2，NEON=SSE-FP 对应）", "同上"),
    ("ibrFpMul", "IBR FPMul（256b×2）", "同上"),
]


def wrap_if_needed(seq, tmpdir, iters=200):
    """序列文件 → 静态 ELF（已是 ELF 则直接用）。"""
    with open(seq, "rb") as f:
        if f.read(4) == b"\x7fELF":
            return seq
    out = os.path.join(tmpdir, "wrapped")
    r = subprocess.run([sys.executable, WRAP, "--seq", seq, "--out", out,
                        "--iters", str(iters)],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        sys.exit(f"ERROR: wrap failed:\n{r.stderr}")
    return out


def cov_run(elf, tmpdir):
    d = os.path.join(tmpdir, "cov")
    subprocess.run([GEM5, "-r", "-e", "--silent-redirect", "-d", d, SCRIPT,
                    "--binary", elf, "--mode", "baseline", "--cov"],
                   capture_output=True, timeout=600)
    stats = {}
    for line in open(os.path.join(d, "stats.txt"), errors="replace"):
        m = re.match(r"system\.CHAOSCov\.harp\.(\w+)\s+([\d.eE+-]+)", line)
        if m:
            try:
                stats[m.group(1)] = float(m.group(2))
            except ValueError:
                pass
    return d, stats


def main():
    ap = argparse.ArgumentParser(description="Harpocrates end-to-end report")
    ap.add_argument("--seq", required=True,
                    help="指令序列（.S/.txt 或现成 aarch64 ELF）")
    ap.add_argument("--iters", type=int, default=200,
                    help="序列循环次数（wrapper）")
    ap.add_argument("--sfi", type=int, default=0, metavar="N",
                    help="附加 SFI 检测能力评估（N 次注入，IRF transient）")
    ap.add_argument("--sfi-structure", default="irf",
                    choices=["irf", "l1d", "lsq", "intadd", "intmul",
                             "fpadd", "fpmul"])
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--top-k", type=int, default=8)
    ap.add_argument("--out", default=None, help="输出 markdown 路径")
    args = ap.parse_args()

    tmpdir = tempfile.mkdtemp(prefix="harp-report-")
    elf = wrap_if_needed(args.seq, tmpdir, args.iters)
    covdir, stats = cov_run(elf, tmpdir)

    lines = []
    lines.append(f"# Harpocrates 微架构覆盖报告 — "
                 f"{os.path.basename(args.seq)}")
    lines.append("")
    lines.append(f"- 被测序列：`{args.seq}`"
                 + ("" if elf == args.seq else f"（wrapped ×{args.iters}）"))
    lines.append(f"- 覆盖 run：`{covdir}`（单次仿真，ROI 由 m5ops 标记）")
    lines.append("")

    # --- 覆盖表 ---
    lines.append("## 一、7 结构微架构覆盖量化值")
    lines.append("")
    lines.append("| 结构 | 指标 | 值 | 公式口径 |")
    lines.append("|------|------|----|----------|")
    present = [(k, d, f) for k, d, f in STAT_ROWS if k in stats]
    for k, desc, formula in present:
        lines.append(f"| {desc} | `{k}` | **{stats[k]:.4f}** | {formula} |")
    lines.append("")
    lines.append("指标定义与论文（Harpocrates ISCA'24/Micro'26）逐项对齐："
                 "ACE lifetime（bit-array 上界）+ IBR（FU 相关性）；"
                 "细节与诚实边界见 docs/harpocrates/method.md。")
    lines.append("")

    # --- SFI ---
    if args.sfi > 0:
        lines.append(f"## 二、SFI 检测能力（{args.sfi_structure}，"
                     f"N={args.sfi}）")
        lines.append("")
        r = subprocess.run([sys.executable, EVAL, "--seq", elf,
                            "--structure", args.sfi_structure,
                            "--n", str(args.sfi), "--jobs", str(args.jobs),
                            "--out", os.path.join(tmpdir, "sfi")],
                           capture_output=True, text=True, timeout=3600)
        lines.append("```")
        lines.append((r.stdout or r.stderr).strip())
        lines.append("```")
        lines.append("")

    # --- 建议 ---
    lines.append("## 三、指令流变异改进建议（证据驱动）")
    lines.append("")
    r = subprocess.run([sys.executable, ADVICE, "--cov-dir", covdir,
                        "--top-k", str(args.top_k)],
                       capture_output=True, text=True, timeout=60)
    lines.append("```markdown")
    lines.append((r.stdout or r.stderr).strip())
    lines.append("```")

    text = "\n".join(lines)
    if args.out:
        open(args.out, "w").write(text)
        print(f"report: {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
