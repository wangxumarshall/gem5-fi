#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""harp_advice.py — Harpocrates 变异建议引擎（计划 Task 6.1）。

输入：一次 --cov run 的产物（stats.txt + harp_cov_detail.log），输出
排序的指令流变异建议——每条含：目标结构、证据数字（来自 detail dump）、
具体变异操作（指令级）、预期收益区间（由 mix 缺口数据边界推出）、
置信度（推导链长度）。这是论文 MuSeqGen 盲变异的建议驱动（advice-
driven）超越点：论文只有标量 fitness + 均匀随机指令替换。

规则集（计划 §四，由指标公式逆推）：
  症状 → 建议的映射全部基于实测数字，无臆测。

用法：
  python3 tools/harp_advice.py --cov-dir m5out_dir [--top-k 10]
  python3 tools/harp_advice.py --seq workloads/harp/seq   # 自动跑 cov
"""
import argparse
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
GEM5 = os.path.join(REPO, "CHAOS/gem5/build/ARM/gem5.opt")
SCRIPT = os.path.join(REPO, "smoke_test/configs/two_level_taishan.py")

STAT_KEYS = [
    "roiCycles", "irfAvf", "irfAvfInt", "irfAvfFloat", "irfAvfVec",
    "irfAvfCommit", "irfAvfCommitInt", "l1dAvf", "sqAvf",
    "ibrIntAdd", "ibrIntMul", "ibrFpAdd", "ibrFpMul",
    "l1dReads", "l1dWrites", "l1dEvicts",
    "sqWrites", "sqConsumes", "sqFrees",
    # SDC-ED Task 5.3 新信号（规则引擎扩展）
    "irfAvfSdc", "irfAvfSdcInt", "sdcGap", "sdcOnPathReads",
    "sdcTotalReads", "fpValueEntropy", "gateSensRatio", "gateSensSamples",
    "mulSensRatio", "mulSensSamples", "l2cReads", "l2cWrites",
    "l2cTagReads", "l2cTagFaceRatio", "l2cAvf",
    "ibrIssues::IntAdd", "ibrIssues::IntMul",
    "ibrIssues::FPAdd", "ibrIssues::FPMul",
]


def parse_stats(path):
    d = {}
    if not os.path.exists(path):
        return d
    for line in open(path, errors="replace"):
        # ::subname form for Vector stats (ibrIssues::FPAdd etc.) —
        # \w+ alone truncates at the colons (measured).
        m = re.match(r"system\.CHAOSCov\.harp\.(\w+(?:::\w+)*)\s+([\d.eE+-]+)",
                     line)
        if m and m.group(1) in STAT_KEYS:
            try:
                d[m.group(1)] = float(m.group(2))
            except ValueError:
                pass
    return d


def parse_detail(path):
    d = {"irf_input_bits": [0, 0, 0, 0], "irf_issues": [0, 0, 0, 0]}
    if not os.path.exists(path):
        return d
    for line in open(path, errors="replace"):
        m = re.match(r"ibr (\d+)/(\d+) (\d+)/(\d+) (\d+)/(\d+) (\d+)/(\d+)", line)
        if m:
            for i in range(4):
                d["irf_input_bits"][i] = int(m.group(1 + 2 * i))
                d["irf_issues"][i] = int(m.group(2 + 2 * i))
    return d


def build_advice(stats, detail, top_k=10):
    """规则引擎：症状（实测数字）→ 建议。返回排序后的建议列表。"""
    adv = []
    roi = stats.get("roiCycles", 0)

    def add(struct, symptom, action, gain, conf):
        adv.append({"structure": struct, "symptom": symptom,
                    "action": action, "gain": gain, "confidence": conf})

    # --- IRF 规则 ---
    avf_int = stats.get("irfAvfInt", 0)
    avf_commit = stats.get("irfAvfCommitInt", 0)
    if avf_int < 0.10:
        add("IRF",
            f"irfAvfInt={avf_int:.4f} 偏低（写后读区间短/覆写频繁）",
            "提高寄存器依赖距离：把串行链 (add x9,x9,x9) 改为多目的"
            "寄存器并行链 (add x9,x10,x11; add x12,x13,x14; ...)，"
            "让每个值在被覆写前保持更长的可读窗口",
            "+ΔAVF 上界 = 新写读间距/旧间距 比值 × 现值（实证由重测确认）",
            "high（直接作用区间语义）")
    if avf_int > 0 and avf_commit > avf_int * 1.10:
        add("IRF",
            f"commit 口径 {avf_commit:.4f} >> 乐观口径 {avf_int:.4f}"
            f"（差 {avf_commit - avf_int:.4f}）",
            "wrong-path 读占比高：降低序列分支密度，或让分支两侧都"
            "消费同一寄存器组（消除 squash 回退差）",
            "口径差收敛 → 乐观 AVF 向 commit AVF 靠拢",
            "medium（间接作用于分支行为）")

    # --- L1D 规则 ---
    l1d_avf = stats.get("l1dAvf", 0)
    reads = stats.get("l1dReads", 0)
    writes = stats.get("l1dWrites", 0)
    evicts = stats.get("l1dEvicts", 0)
    if l1d_avf < 0.05 and writes > reads:
        add("L1D",
            f"l1dAvf={l1d_avf:.4f}，writes={writes} > reads={reads}"
            f"（fill/store 后未充分读）",
            "增加对已 fill 块的重复读：把一次性写改为 store→load 同址对"
            "（str x9,[x8]; ldr x10,[x8]），或顺序 stride-8 扫 32KB",
            "read 占比提升直接加长 block 的 read→next-event 区间",
            "high（fill→read→read 即 ACE 模式）")
    if evicts > 0 and evicts > reads:
        add("L1D",
            f"evicts={evicts} > reads={reads}（块在消费前被逐出）",
            "缩小工作集或提高时间局部性：让同一 64B 块的多次访问聚在"
            "一起（访问序列按块分组），减少 fill→evict 未读窗口",
            "fill→evict 转 fill→read",
            "medium")

    # --- LSQ 规则 ---
    sq_avf = stats.get("sqAvf", 0)
    sq_w = stats.get("sqWrites", 0)
    sq_c = stats.get("sqConsumes", 0)
    if sq_avf < 0.05 and sq_w > 0 and sq_c / sq_w < 0.5:
        add("LSQ",
            f"sqAvf={sq_avf:.4f}，consumes/writes={sq_c}/{sq_w}"
            f"={sq_c/max(sq_w,1):.2f}（store 数据驻留短）",
            "拉长 store 在飞时间：store 后插长依赖链再触发写回"
            "（str x9,[x8]; ...8 条无关 ALU...; 再下一条 store），"
            "并增加 store→load 前转对让 SQ data 被读",
            "execute→writeback 间距拉长直接加 ACE 区间",
            "high")
    elif sq_w == 0:
        add("LSQ",
            "sqWrites=0（序列无 store）",
            "插入 store→load 前转对：str xN,[x8,#k]; ldr xM,[x8,#k]"
            "（前转命中即 SQ data 消费）",
            "SQ AVF 从 0 起步",
            "high")

    # --- FU IBR 规则（mix 缺口量化）---
    ibr = {"IntAdd": stats.get("ibrIntAdd", 0),
           "IntMul": stats.get("ibrIntMul", 0),
           "FPAdd": stats.get("ibrFpAdd", 0),
           "FPMul": stats.get("ibrFpMul", 0)}
    issues = detail.get("irf_issues", [0, 0, 0, 0])
    total_issues = sum(issues) if any(issues) else None
    op_of = {0: "IntAdd", 1: "IntMul", 2: "FPAdd", 3: "FPMul"}
    for i, name in op_of.items():
        if ibr[name] < 0.03:
            ins = issues[i] if total_issues else 0
            share = ins / total_issues if total_issues else 0
            sample = {
                "IntAdd": "add x9, x10, x11",
                "IntMul": "mul x19, x20, x21",
                "FPAdd": "fadd d8, d9, d10",
                "FPMul": "fmul d11, d12, d13",
            }[name]
            add(f"FU-{name}",
                f"ibr{name}={ibr[name]:.4f} 偏低；issue 占比 "
                f"{share:.1%}（{ins} 条）",
                f"指令 mix 缺口：把序列中出现的低贡献指令替换为"
                f" {sample}（全宽操作数，W 寄存器只有 32b 有效）",
                f"上界：全替换后 issue 占比→100% 时 IBR 饱和值"
                f"（实测重测确认）",
                "high（mix 直接决定分子）")

    # --- ACE-detection gap（若有 SFI 数据则用；advice 阶段无则跳过）---

    # --- SDC-ED 新信号规则（Task 5.3：covUnits/SDC-ACE/值类/敏感度）---
    # sdcGap：读而不达（dead-chain）证据——动态切片已把「被读但从不
    # 到达校验输出」的驻留从 SDC-ACE 剔除，gap 就是序列设计缺陷的
    # 直接度量。
    sdc_gap = stats.get("sdcGap", None)
    if sdc_gap is not None and sdc_gap > 0.10:
        add("IRF-SDC",
            f"sdcGap={sdc_gap:.4f}（commit 读流中 {sdc_gap:.0%} 的消费"
            f"不在到达校验输出的数据流切片上）",
            "死链改造：把「读后丢弃」的消费者改为把结果串到序列末尾"
            "仍存回的寄存器（或删除中间死写），让每次读都落在"
            "store-back 可达的链上",
            "SDC-ACE 是 ED 的 OoO 轴分量——gap 每降 1 个点，"
            "irfAvfSdc 同比例上升（区间算术不变、分母不变）",
            "high（负对照 dead_read gap=0.196 vs 直达 0 实测）")
    # FSU 值类熵：值域覆盖不足（软件掩蔽是值依赖的）。
    fp_ent = stats.get("fpValueEntropy", None)
    fp_issues = (stats.get("ibrIssues::FPAdd", 0)
                 + stats.get("ibrIssues::FPMul", 0))
    if fp_ent is not None and fp_issues > 0 and fp_ent < 0.30:
        add("FSU-value",
            f"fpValueEntropy={fp_ent:.4f}（FP 源操作数值类集中在少数"
            f" IEEE754 类；{fp_issues} 条 FP issue）",
            "值域扩展：序列中加入产生 subnormal/NaN/Inf 的操作数源"
            "（ldr 随机位模式 d 寄存器天然覆盖五类；或对大数 fadd "
            "制造溢出 Inf、对 Inf×0 制造 NaN）",
            "CHAOSFPU 全 Masked 证明 FP 软件掩蔽值依赖——值类熵是"
            "IBR 之外的 FSU 覆盖轴",
            "high（randbits_seq 熵 0.392 vs rand_fp 0.351 实测分化）")
    # IEX 乘法敏感度：操作数掩蔽（0×anything 全掩蔽）。
    mul_ratio = stats.get("mulSensRatio", None)
    mul_samples = stats.get("mulSensSamples", 0)
    if mul_ratio is not None and mul_samples > 0 and mul_ratio < 0.9:
        add("IEX-mul",
            f"mulSensRatio={mul_ratio:.4f}（乘法输入位 "
            f"{1-mul_ratio:.0%} 被逻辑掩蔽；{mul_samples} 采样）",
            "非零密集操作数：把乘法源改成全 64 位都非零/非一的值"
            "（ldr 随机位模式源），避开 0×x / 1×x / 高位零重叠",
            "乘法器真实掩蔽在 Task 4.3 实测（0×0→0.000，随机对"
            "→1.000）；敏感度即检测位面",
            "medium（加法器零掩蔽为 1.000 结构值，无需 advice）")
    # L2C tag-face：ECC 盲平面的触达。
    tag_ratio = stats.get("l2cTagFaceRatio", None)
    l2c_reads = stats.get("l2cReads", 0)
    if tag_ratio is not None and l2c_reads == 0 and tag_ratio == 0:
        add("L2C-tag",
            "l2cReads=0（L2 数据面零触达——工作集全部 L1 命中或"
            " targetCache 未含 L2）",
            "扩大工作集越过 L1D 容量（64KiB）迫使 L2 读写："
            "stride 访问 >128KiB 区域；再构造同 tag 不同 set 的冲突"
            "对触发 tag 比较路径",
            "ρ_L2C(tag)=0.45 是 ECC 盲高危面（39-47% 实测线），"
            "tag-face 触达是 L2C 单元的主要覆盖缺口",
            "high（w_L2C=0.525 最大翻转份额）")

    # 排序：confidence high > medium，然后按影响结构数量
    conf_rank = {"high": 0, "medium": 1, "low": 2}
    adv.sort(key=lambda a: (conf_rank.get(a["confidence"], 3),
                            len(a["symptom"]) * -1))
    return adv[:top_k]


def main():
    ap = argparse.ArgumentParser(description="Harpocrates advice engine")
    ap.add_argument("--cov-dir", help="已有 --cov run 的 m5out 目录")
    ap.add_argument("--seq", help="被测 ELF（自动跑一次 cov run）")
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--out", default=None, help="输出 markdown（默认 stdout）")
    args = ap.parse_args()

    if not args.cov_dir and not args.seq:
        ap.error("需要 --cov-dir 或 --seq")

    if args.seq:
        import tempfile
        args.cov_dir = tempfile.mkdtemp(prefix="harp-advice-")
        cmd = [GEM5, "-r", "-e", "--silent-redirect", "-d", args.cov_dir,
               SCRIPT, "--binary", args.seq, "--mode", "baseline", "--cov"]
        subprocess.run(cmd, capture_output=True, timeout=300)

    stats = parse_stats(os.path.join(args.cov_dir, "stats.txt"))
    detail = parse_detail(os.path.join(args.cov_dir, "harp_cov_detail.log"))
    advice = build_advice(stats, detail, args.top_k)

    lines = ["# Harpocrates 变异建议（证据驱动）", "",
             f"来源：`{args.cov_dir}`（roiCycles={stats.get('roiCycles', 0):.0f}）",
             ""]
    lines.append("| # | 结构 | 症状（实测证据） | 建议变异操作 | 预期收益 | 置信度 |")
    lines.append("|---|------|------------------|--------------|----------|--------|")
    for i, a in enumerate(advice, 1):
        lines.append(f"| {i} | {a['structure']} | {a['symptom']} | "
                     f"{a['action']} | {a['gain']} | {a['confidence']} |")
    lines.append("")
    lines.append("## 当前覆盖快照")
    lines.append("")
    for k in STAT_KEYS:
        if k in stats:
            lines.append(f"- {k}: {stats[k]:.6f}")
    text = "\n".join(lines)
    if args.out:
        open(args.out, "w").write(text)
        print(f"advice written: {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
