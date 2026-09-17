#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-32.0
# SPDX-License-Identifier: Apache-2.0
"""harp_eval.py — Harpocrates SFI 检测能力评估（计划 Task 5.1）。

论文 §II-E 的 SFI 协议（bit-array 结构：IRF/L1D/LSQ，transient 单 bit
flip，bit 与 cycle 均匀随机），产出 detection = n/N + Wilson 95% CI，
并与单次 coverage run 的 ACE 并列输出（论文 Fig.4/10 的数据形态：
coverage vs detection 双轴对照）。

注入器复用（gem5-fi 既有资产）：
  IRF : two_level_taishan.py --injector phys（CHAOSPhysReg，phys 模式，
        targetPhysRegIdx 定向 + firstClock 窗口）
  L1D : configs/se/arm_chaos_cache.py（CHAOSCache，data 字段 transient）
  LSQ : two_level_taishan.py --injector lsq_fwd（CHAOSLSQFwd）

结果分类（read_trace_stats.py 的六类口径；论文的 detection 是
"faulty 偏离 fault-free" = SDC + Crash）：
  detection = (SDC + Crash) / N

用法：
  python3 tools/harp_eval.py --seq workloads/harp/sample_seq \\
      --structure irf --n 50 [--jobs 8] [--out artifacts/harp-eval-xxx]
"""
import argparse
import math
import os
import random
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
GEM5 = os.path.join(REPO, "CHAOS/gem5/build/ARM/gem5.opt")
TS_CFG = os.path.join(REPO, "smoke_test/configs/two_level_taishan.py")
CACHE_CFG = os.path.join(REPO, "configs/se/arm_chaos_cache.py")

SUM_RE = re.compile(r"SUM=(\d+) CRC=([0-9a-f]+)")


def wilson(k, n, z=1.96):
    """Wilson score 95% CI（与 tools/campaign.py 同实现）。"""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), p, min(1.0, center + half))


def run_gem5(out_dir, cmd, timeout=300):
    """跑一个 gem5 命令；返回 simout 文本。"""
    os.makedirs(out_dir, exist_ok=True)
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ""
    so = os.path.join(out_dir, "simout.txt")
    return open(so, errors="replace").read() if os.path.exists(so) else ""


def sfi_run(i, binary, structure, seed, roi_lo_c, roi_hi_c, tmpdir):
    """第 i 次 SFI 注入 run。返回 (i, outcome_class, detail)。

    outcome ∈ {SDC, Crash, Masked, NoOutput}（对照 golden 在主线程做，
    但 SUM 提取在此完成，减少二次读文件）。
    """
    rng = random.Random(seed)
    out = os.path.join(tmpdir, f"inj{i:04d}")
    if os.path.exists(out):
        shutil.rmtree(out)
    # firstClock（CPU 周期域）：ROI tick / 1000（2.6GHz CPU 时钟下
    # 1 cycle = 385 ticks；用 1000 作保守近似并 clamp）
    lo_c = max(0, int(roi_lo_c))
    hi_c = max(lo_c + 1, int(roi_hi_c))
    first_clock = rng.randint(lo_c, hi_c)

    if structure == "irf":
        phys_idx = rng.randint(0, 124)          # numPhysIntRegs=125
        cmd = [GEM5, "-r", "-e", "--silent-redirect", "-d", out, TS_CFG,
               "--binary", binary, "--mode", "inject",
               "--injector", "phys", "--injection-mode", "phys",
               "--target-phys-idx", str(phys_idx),
               "--first-clock", str(first_clock),
               "--max-faults", "1", "--probability", "1.0",
               "--fault-type", "bit_flip", "--bits", "1",
               "--rng-seed", str(seed)]
    elif structure == "l1d":
        # CHAOSCache via arm_chaos_cache.py：随机块+随机字节（不定向，
        # 与论文"均匀随机 bit"一致——targetBlockAddr=0 默认随机块）。
        # 注意该脚本的参数是下划线形式（实测 --byte-offset 会
        # argparse error）。
        byte_off = rng.randint(0, 63)
        cmd = [GEM5, "--quiet", "-d", out, CACHE_CFG,
               "--cmd", binary, "--cpu", "O3",
               "--first_clock", str(first_clock),
               "--max_faults", "1", "--probability", "1.0",
               "--fault_type", "bit_flip",
               "--rng_seed", str(seed),
               "--target_byte_offset", str(byte_off)]
    elif structure == "lsq":
        cmd = [GEM5, "-r", "-e", "--silent-redirect", "-d", out, TS_CFG,
               "--binary", binary, "--mode", "inject",
               "--injector", "lsq_fwd",
               "--first-clock", str(first_clock),
               "--max-faults", "1", "--probability", "1.0",
               "--fault-type", "bit_flip", "--bits", "1",
               "--rng-seed", str(seed)]
    elif structure in ("intadd", "intmul"):
        # Int FU permanent (L1 execution-level): random result-bit mask
        # per run (the paper samples random gates; the L1 equivalent
        # samples a random output bit).
        opclass = {"intadd": "IntAlu", "intmul": "IntMult"}[structure]
        bit = rng.randint(0, 63)
        mask = 1 << bit
        cmd = [GEM5, "-r", "-e", "--silent-redirect", "-d", out, TS_CFG,
               "--binary", binary, "--mode", "baseline",
               "--fu-perm", "--fu-perm-opclass", opclass,
               "--fu-perm-mask", hex(mask),
               "--fu-perm-first-clock", str(first_clock)]
    elif structure in ("fpadd", "fpmul"):
        # FP FU: CHAOSFPU (the repo's proven FSU writeback injector —
        # AArch64 FP results bypass setRegOperand via the writable/blob
        # paths; CHAOSFPU's maybeCorruptWriteback(Blob) hooks exactly
        # those). Single fault (maxFaults=1) at a random bit, permanent
        # within the run from first_clock.
        bit = rng.randint(0, 63)
        mask = 1 << bit
        cmd = [GEM5, "-r", "-e", "--silent-redirect", "-d", out, TS_CFG,
               "--binary", binary, "--mode", "baseline",
               "--fpu-inject", "--fpu-fault-mask", hex(mask),
               "--fpu-first-clock", str(first_clock)]
    else:
        raise ValueError(structure)

    txt = run_gem5(out, cmd)
    if not txt:
        return (i, "NoOutput", "no simout")
    crashed = ("panic" in txt or "aborted" in txt or "fatal" in txt
               or "Exiting @ tick" not in txt)
    if crashed:
        return (i, "Crash", "sim crashed")
    m = SUM_RE.search(txt)
    if m is None:
        return (i, "NoOutput", "no SUM line")
    return (i, "SUM_PENDING", m.group(0))   # 主线程对照 golden


def main():
    ap = argparse.ArgumentParser(description="Harpocrates SFI evaluation")
    ap.add_argument("--seq", required=True, help="被测 aarch64 静态 ELF")
    ap.add_argument("--structure", required=True,
                    choices=["irf", "l1d", "lsq",
                             "intadd", "intmul", "fpadd", "fpmul"])
    ap.add_argument("--n", type=int, default=50, help="注入次数 N")
    ap.add_argument("--jobs", type=int, default=8, help="并行 gem5 进程数")
    ap.add_argument("--master-seed", type=int, default=20260916)
    ap.add_argument("--out", default=None)
    ap.add_argument("--keep-runs", action="store_true")
    args = ap.parse_args()

    out = args.out or os.path.join(
        REPO, "artifacts",
        f"harp-eval-{args.structure}-{os.path.basename(args.seq)}")
    os.makedirs(out, exist_ok=True)
    tmpdir = os.path.join(out, "runs")
    os.makedirs(tmpdir, exist_ok=True)

    # 1. golden（two_level_taishan baseline——与 coverage 同平台）
    gdir = os.path.join(out, "golden")
    gtxt = run_gem5(gdir, [GEM5, "-r", "-e", "--silent-redirect", "-d", gdir,
                           TS_CFG, "--binary", args.seq, "--mode", "baseline",
                           "--cov"])
    gm = SUM_RE.search(gtxt)
    if gm is None:
        sys.exit("ERROR: golden run produced no SUM= output")
    golden = gm.group(0)
    print(f"golden: {golden}")

    # ROI 窗口（周期近似域）：从 cov run 的 ticks 推
    roi_lo = int(re.search(r"roiBeginTick\s+(\d+)", gtxt) is not None
                 and re.search(r"roiBeginTick\s+(\d+)", gtxt).group(1) or 0)
    roi_hi_m = re.search(r"roiEndTick\s+(\d+)", gtxt)
    roi_hi = int(roi_hi_m.group(1)) if roi_hi_m else 40000
    # stats 文件里有 roiBegin/EndTick（simout 没有）——从 stats 读
    gs = os.path.join(gdir, "stats.txt")
    if os.path.exists(gs):
        s = open(gs).read()
        b = re.search(r"roiBeginTick\s+(\d+)", s)
        e = re.search(r"roiEndTick\s+(\d+)", s)
        if b and e:
            roi_lo, roi_hi = int(b.group(1)), int(e.group(1))
    print(f"ROI ticks: [{roi_lo}, {roi_hi}]")

    # 2. N 次 SFI（并行）
    tasks = [(i, args.seq, args.structure, args.master_seed + i,
              roi_lo // 1000, roi_hi // 1000, tmpdir)
             for i in range(args.n)]
    outcomes = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(sfi_run, *t) for t in tasks]
        for idx, f in enumerate(as_completed(futs), 1):
            i, cls, detail = f.result()
            outcomes[i] = (cls, detail)
            if idx % 10 == 0 or idx == args.n:
                print(f"  {idx}/{args.n} runs done")

    # 3. 分类汇总（SUM_PENDING 对照 golden 判 SDC/Masked）
    counts = {"SDC": 0, "Crash": 0, "Masked": 0, "NoOutput": 0}
    for i in range(args.n):
        cls, detail = outcomes[i]
        if cls == "SUM_PENDING":
            cls = "SDC" if detail != golden else "Masked"
        counts[cls] += 1
    detected = counts["SDC"] + counts["Crash"]
    lo, p, hi = wilson(detected, args.n)

    # 4. coverage 并列（golden --cov run 的 stats）
    cov_stats = {}
    gs = os.path.join(gdir, "stats.txt")
    if os.path.exists(gs):
        s = open(gs).read()
        for key in ["irfAvf", "irfAvfInt", "irfAvfCommit", "irfAvfVec",
                    "l1dAvf", "sqAvf",
                    "ibrIntAdd", "ibrIntMul", "ibrFpAdd", "ibrFpMul"]:
            m = re.search(rf"system\.CHAOSCov\.harp\.{key}\s+([\d.e+-]+)", s)
            if m:
                cov_stats[key] = float(m.group(1))

    # 5. 报告
    report = os.path.join(out, "summary.md")
    with open(report, "w") as f:
        f.write(f"# SFI detection — {os.path.basename(args.seq)} / "
                f"{args.structure}\n\n")
        f.write(f"- N = {args.n}（master seed {args.master_seed}）\n")
        f.write(f"- golden: `{golden}`\n")
        f.write(f"- detection = (SDC + Crash)/N = "
                f"({counts['SDC']} + {counts['Crash']})/{args.n} "
                f"= **{p:.4f}**\n")
        f.write(f"- Wilson 95% CI: [{lo:.4f}, {hi:.4f}]\n")
        f.write(f"- 分类: {counts}\n\n")
        # 注入空间的 AVF/IBR 口径必须对齐：IRF 的 SFI 打的是 int 物理
        # 寄存器空间，上界对照 irfAvfInt；FU 结构对照同类的 IBR
        # （IBR 是相关性指标而非上界，报告口径注明）。
        ace_key = {"irf": "irfAvfInt", "l1d": "l1dAvf", "lsq": "sqAvf",
                   "intadd": "ibrIntAdd", "intmul": "ibrIntMul",
                   "fpadd": "ibrFpAdd", "fpmul": "ibrFpMul"}[
            args.structure]
        f.write("## coverage vs detection（论文 Fig.4 形态）\n\n")
        f.write(f"- {args.structure} ACE ({ace_key}): "
                f"{cov_stats.get(ace_key, float('nan')):.4f}\n")
        f.write(f"- detection: {p:.4f}\n")
        ace = cov_stats.get(ace_key)
        if ace is not None:
            if args.structure in ("irf", "l1d", "lsq"):
                f.write(f"- ACE >= detection（上界性质）: "
                        f"{'YES' if ace >= p else 'NO'}\n")
            else:
                f.write(f"- IBR（相关性指标，非上界）：detection {p:.4f} vs "
                        f"IBR {ace:.4f}\n")
        f.write("\n## 全部结构 coverage\n\n")
        for k, v in cov_stats.items():
            f.write(f"- {k}: {v:.6f}\n")
    print()
    print(open(report).read())
    print(f"report: {report}")
    if not args.keep_runs:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
