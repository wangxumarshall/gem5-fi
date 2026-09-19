#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""harp_evolve.py — advice-driven vs 盲变异对比实验（计划 Task 6.2）。

论文 Fig.10 的等价物 + 超越证据：同预算下两条优化路径的覆盖曲线——
  (a) advice-driven：每步从 harp_advice 的规则直接改写序列
      （FU mix 缺口 → 替换指令；IRF 低 → 并行链化）
  (b) blind：论文 MuSeqGen 的策略——均匀随机选一条指令替换为
      池中随机指令（V-B1：所有 A 的出现替换为随机 B 的简化版：
      单条替换，保持序列长度）
每步重测 coverage（单次 --cov run，秒级），产出曲线 CSV；
收敛后各抽 1 点跑 SFI 验证 coverage↑⇒detection↑。

用法：
  python3 tools/harp_evolve.py --seq workloads/harp/sample_seq.S \\
      --target fu-intmul --steps 12 [--blind-seed 1] \\
      [--out artifacts/harp-advice-vs-random]
"""
import argparse
import os
import random
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
GEM5 = os.path.join(REPO, "CHAOS/gem5/build/ARM/gem5.opt")
SCRIPT = os.path.join(REPO, "smoke_test/configs/two_level_taishan.py")
WRAP = os.path.join(REPO, "tools/harp_wrap.py")

# 与 harp_wrap.py INST_POOL 一致的指令池（盲变异的替换空间）
INT_POOL = [
    "add x9, x10, x11", "sub x12, x13, x14", "eor x15, x16, x17",
    "and x18, x19, x20", "orr x21, x22, x23", "bic x24, x25, x26",
    "eor x27, x28, x9", "add x10, x11, x12", "sub x13, x14, x15",
    "and x16, x17, x18", "mul x19, x20, x21", "mul x22, x23, x24",
    "add x25, x26, x27", "eor x28, x9, x10", "sub x11, x12, x13",
    "orr x14, x15, x16", "mul x17, x18, x19", "add x20, x21, x22",
]
FP_POOL = [
    "ldr d8, [x8, #0]", "ldr d9, [x8, #8]", "fadd d8, d9, d10",
    "fmul d11, d8, d9", "fsub d12, d10, d11", "fadd d13, d12, d11",
    "fmul d14, d13, d8", "str d14, [x8, #32]", "fmul d15, d14, d13",
]
MEM_POOL = [
    "ldr x9, [x8, #0]", "str x10, [x8, #8]", "ldr x11, [x8, #16]",
    "str x12, [x8, #24]", "ldr x13, [x8, #32]", "str x14, [x8, #40]",
]

# 目标结构 → （覆盖 stat key, advice 替换指令, 是否 mem）
TARGETS = {
    "fu-intadd": ("ibrIntAdd", "add x9, x10, x11", False),
    "fu-intmul": ("ibrIntMul", "mul x19, x20, x21", False),
    "fu-fpadd": ("ibrFpAdd", "fadd d8, d9, d10", True),
    "fu-fpmul": ("ibrFpMul", "fmul d11, d12, d13", True),
    "irf": ("irfAvfInt", None, False),
}


def measure(lines, tmpdir, iters=200):
    """包装 + 编译 + cov run，返回 {stat: value}。"""
    seq_path = os.path.join(tmpdir, "cur.S")
    with open(seq_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    out = os.path.join(tmpdir, "cur")
    r = subprocess.run([sys.executable, WRAP, "--seq", seq_path,
                        "--out", out, "--iters", str(iters)],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        sys.exit(f"wrap failed: {r.stderr}")
    d = os.path.join(tmpdir, "m5out")
    subprocess.run([GEM5, "-r", "-e", "--silent-redirect", "-d", d, SCRIPT,
                    "--binary", out, "--mode", "baseline", "--cov"],
                   capture_output=True, timeout=300)
    stats = {}
    for line in open(os.path.join(d, "stats.txt"), errors="replace"):
        # Vector stats carry ::subname (covUnits::IFU etc.) — \w+ alone
        # would truncate at the colons and lose the subname (measured).
        m = re.match(r"system\.CHAOSCov\.harp\.(\w+(?:::\w+)*)\s+([\d.eE+-]+)",
                     line)
        if m:
            try:
                stats[m.group(1)] = float(m.group(2))
            except ValueError:
                pass
    return stats


def ed_of_stats(stats, profile_path):
    """SDC-ED Task 5.3：从 measure() 的 stats 字典直接算 ED（复用
    ed_score 的推导：covUnits 7 维 + profile 的 w/ρ/ceiling）。"""
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    from ed_profile import load_profile, UNITS
    prof = load_profile(profile_path)
    w = prof.weights()
    rho = prof.rho_initial()
    cov = {u: stats.get(f"covUnits::{u}", 0.0) for u in UNITS}
    ed = 0.0
    for u in UNITS:
        a_eff = min(cov[u], prof.ceiling(u))
        ed += w[u] * rho.get(u, 0.0) * a_eff
    return ed


def advice_step(lines, target, rng):
    """建议驱动的一步：按规则直接改写。"""
    key, repl, is_mem = TARGETS[target]
    if target == "irf":
        # 策略 A（并行链化）：串行自依赖 (a xN,xN,xN) → 独立三操作数。
        # 策略 B（冷目的寄存器）：dest 在近期已被写过（即将覆写一个
        # 在飞值）→ 改写到冷寄存器（最近最少作 dest 的 x9-x28），
        # 拉长旧值的可读窗口（advice 引擎 IRF 规则的通用化——
        # overwrite_seq 首版只匹配自依赖模式未命中，实测持平后补）。
        out = list(lines)
        changed = False
        dest_hist = []
        for l in out:
            m = re.match(r"\w+ x(\d+), x(\d+), x(\d+)", l)
            if m:
                dest_hist.append(int(m.group(1)))
        cold = [r for r in range(9, 29) if r not in dest_hist] or \
            [min(set(dest_hist), key=dest_hist.count)]
        for i, l in enumerate(out):
            m = re.match(r"(\w+) x(\d+), x(\d+), x(\d+)", l)
            if not m or m.group(1) not in ("add", "sub", "eor", "and",
                                           "orr", "mul", "bic"):
                continue
            # A: 自依赖
            if m.group(2) == m.group(3) == m.group(4):
                d = int(m.group(2))
                out[i] = f"add x{d}, x{(d + 1) % 20 + 9}, x{(d + 2) % 20 + 9}"
                changed = True
                break
            # B: dest 是重复目的（覆写在飞值）→ 冷寄存器
            d = int(m.group(2))
            if dest_hist.count(d) > 1 and cold and cold[0] != d:
                out[i] = f"{m.group(1)} x{cold[0]}, x{m.group(3)}, x{m.group(4)}"
                changed = True
                break
        return out if changed else out
    # FU mix：把一条非目标类指令替换为目标类
    idxs = [i for i, l in enumerate(lines)
            if not l.startswith(repl.split()[0])]
    if not idxs:
        return lines
    i = rng.choice(idxs)
    out = list(lines)
    out[i] = repl
    return out


def blind_step(lines, rng):
    """论文盲变异：均匀随机选一条替换为池中随机指令。"""
    pool = INT_POOL + FP_POOL + MEM_POOL
    out = list(lines)
    out[rng.randrange(len(out))] = pool[rng.randrange(len(pool))]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seq", required=True, help="起始 .S 序列")
    ap.add_argument("--target", required=True, choices=list(TARGETS))
    ap.add_argument("--steps", type=int, default=12)
    ap.add_argument("--iters", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20260916)
    ap.add_argument("--out", default=None)
    # SDC-ED Task 5.3: ED fitness mode (legacy = the original single-stat
    # scalar; ed = Σ w·ρ·A_eff from the cpu profile — kept side by side
    # for the comparison protocol).
    ap.add_argument("--fitness", choices=["legacy", "ed"], default="legacy")
    ap.add_argument("--profile",
                    default=os.path.join(REPO, "configs/cpu-profiles",
                                         "taishan-v110.yaml"),
                    help="cpu profile for --fitness ed")
    args = ap.parse_args()

    out = args.out or os.path.join(REPO, "artifacts", "harp-advice-vs-random")
    os.makedirs(out, exist_ok=True)
    key = TARGETS[args.target][0]

    def fitness(stats):
        if args.fitness == "ed":
            return ed_of_stats(stats, args.profile)
        return stats.get(key, 0)

    lines = [l.strip() for l in open(args.seq)
             if l.strip() and not l.startswith("#")]

    rng_a = random.Random(args.seed)
    rng_b = random.Random(args.seed + 1)

    # 两条路径共享同一起点
    seq_a, seq_b = list(lines), list(lines)
    tmp_a = tempfile.mkdtemp(prefix="harp-evo-a-")
    tmp_b = tempfile.mkdtemp(prefix="harp-evo-b-")

    rows = []
    # step 0
    s0 = measure(seq_a, tmp_a, args.iters)
    rows.append((0, fitness(s0), fitness(s0)))
    print(f"step 0: advice={rows[0][1]:.6f} blind={rows[0][2]:.6f}")

    for step in range(1, args.steps + 1):
        seq_a = advice_step(seq_a, args.target, rng_a)
        seq_b = blind_step(seq_b, rng_b)
        sa = measure(seq_a, tmp_a, args.iters)
        sb = measure(seq_b, tmp_b, args.iters)
        rows.append((step, fitness(sa), fitness(sb)))
        print(f"step {step}: advice={rows[-1][1]:.6f} "
              f"blind={rows[-1][2]:.6f}")

    csv = os.path.join(out, f"curve-{args.target}.csv")
    with open(csv, "w") as f:
        f.write("step,advice,blind\n")
        for s, a, b in rows:
            f.write(f"{s},{a:.6f},{b:.6f}\n")

    # 保存终态序列
    for name, seq in (("advice", seq_a), ("blind", seq_b)):
        p = os.path.join(out, f"final-{name}-{args.target}.S")
        open(p, "w").write("\n".join(seq) + "\n")

    final_a = rows[-1][1]
    final_b = rows[-1][2]
    summary = os.path.join(out, "summary.md")
    with open(summary, "w") as f:
        f.write(f"# advice-driven vs 盲变异（{args.target}，"
                f"{args.steps} 步）\n\n")
        f.write(f"- 起始 {key}: {rows[0][1]:.6f}\n")
        f.write(f"- advice 终态: {final_a:.6f}\n")
        f.write(f"- blind 终态: {final_b:.6f}\n")
        f.write(f"- advice - blind = {final_a - final_b:+.6f}\n")
        f.write(f"- 曲线: {csv}\n")
    print(open(summary).read())
    print(f"artifacts: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
