#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-32.0
# SPDX-License-Identifier: Apache-2.0
"""harp_eval.py — Harpocrates SFI 检测能力评估（计划 Task 5.1 + 6.1 扩展）。

论文 §II-E 的 SFI 协议（bit-array 结构：IRF/L1D/LSQ，transient 单 bit
flip，bit 与 cycle 均匀随机），产出 detection = n/N + Wilson 95% CI，
并与单次 coverage run 的 ACE 并列输出（论文 Fig.4/10 的数据形态：
coverage vs detection 双轴对照）。

Task 6.1（ρ_u 标定战役）扩展：
  1. 新增 --structure l2c_data / l2c_tag（CHAOSCache --target l2 的
     data-face/tag-face 双面臂，L2C 单元的 SFI 标定路径）；
  2. 修复 l1d 臂输出捕获缺陷：原实现 gem5 不带 -r 跑 arm_chaos_cache.py，
     simout.txt 从不生成 → 注入 run 全部误分类 NoOutput（本任务 N=2
     探针实测 2/2 NoOutput 复现）。统一改 -r -e --silent-redirect；
  3. 分类从 4 类升级为 classify.py §9.1 的六类口径：
     SimulatorError / Hang / Crash / Inactive / Masked / SDC。
     Inactive 由注入日志计数判定（各注入器 log 文件名见 INJ_LOG）。
     诚实边界：gem5 SE 对 workload 访问损坏地址的 Page table fault 走
     panic 通道（"Page table fault when accessing virtual address ..."）；
     这是 workload 级 DUE（注入的直接后果），归 Crash 而非
     SimulatorError——在该特定 panic 文本上对 classify.py 的
     SimulatorError 优先序开例外，理由入注释。

注入器复用（gem5-fi 既有资产）：
  IRF : two_level_taishan.py --injector phys（CHAOSPhysReg，phys 模式，
        targetPhysRegIdx 定向 + firstClock 窗口）
  L1D : configs/se/arm_chaos_cache.py（CHAOSCache，data 字段 transient）
  L2C : arm_chaos_cache.py --target l2 --target_field data|tag
        （tag 臂 = F5 合法别名替换；data 臂 = 数据位翻转）
  LSQ : two_level_taishan.py --injector lsq_fwd（CHAOSLSQFwd）

结果分类（classify.py §9.1 六类口径；论文的 detection 是
"faulty 偏离 fault-free" = SDC + Crash）：
  detection = (SDC + Crash) / N
  Inactive（注入未命中）另报 P_SDC|active 口径（剔 Inactive 分母），
  与全分母口径并列（诚实双口径）。

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
# 非 harp wrapper 的标定 kernel（如 stencil_5pt_kernel）打印 FINAL=<16hex>
FINAL_RE = re.compile(r"FINAL=([0-9a-f]{16})")

# 各 structure 对应的注入器日志文件名（Inactive 判定的数据源；文件名
# 由注入器源码 simout.create() 决定，见 CHAOS*/*.cc）。
INJ_LOG = {
    "irf": "fault_injections.log",
    "l1d": "cache_injections.log",
    "l2c_data": "cache_injections.log",
    "l2c_tag": "cache_injections.log",
    "lsq": "lsq_fwd_injections.log",
    "intadd": "fu_perm_injections.log",
    "intmul": "fu_perm_injections.log",
    "fpadd": "fpu_injections.log",
    "fpmul": "fpu_injections.log",
}

# 走 arm_chaos_cache.py（SimpleBoard 2GHz）的 structure：golden 也必须在
# 同一板/同一 config 路径跑（平台一致性）；ROI 窗口从该板 golden stats
# 的 simTicks 换算（500 ticks/cycle），而非 two_level_taishan 的 ROI tick。
CACHE_STRUCTURES = ("l1d", "l2c_data", "l2c_tag")

# gem5 SE 对 workload 损坏地址访问的 panic 文本（归 Crash 的例外规则，
# 见模块 docstring 诚实边界）
WORKLOAD_PAGE_FAULT_RE = re.compile(
    r"Page table fault when accessing virtual address")


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
    """跑一个 gem5 命令；返回 (simout 文本, simerr 文本, rc, timed_out)。"""
    os.makedirs(out_dir, exist_ok=True)
    timed_out = False
    rc = 0
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout)
        rc = r.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
    so = os.path.join(out_dir, "simout.txt")
    se = os.path.join(out_dir, "simerr.txt")
    txt = open(so, errors="replace").read() if os.path.exists(so) else ""
    err = open(se, errors="replace").read() if os.path.exists(se) else ""
    return txt, err, rc, timed_out


def count_injections(out_dir, structure):
    """数该 run 的注入次数（Inactive 判定）。日志不存在 → -1（不可判）。

    诚实边界：CHAOSCache 的 tag/tag_to_legal 模式在同 set 无其他
    valid block 时写 "SKIPPED" 行且不注入——SKIPPED 行不计入注入数
    （否则 Inactive 被虚报为 active）。
    """
    log = os.path.join(out_dir, INJ_LOG.get(structure, ""))
    if not log or not os.path.exists(log):
        return -1
    # 各注入器日志每行一条注入记录（"Cycle: N, ..."）；数非空行，
    # 剔除 SKIPPED（未真正注入的记录）
    n = 0
    for line in open(log, errors="replace"):
        if line.strip() and "SKIPPED" not in line:
            n += 1
    return n


def extract_output_line(txt):
    """提取程序的校验输出行（harp wrapper 的 SUM= 或 kernel 的 FINAL=）。
    返回完整匹配文本（与 golden 对照用）；无 → None。"""
    m = SUM_RE.search(txt)
    if m:
        return m.group(0)
    m = FINAL_RE.search(txt)
    if m:
        return m.group(0)
    return None


def sfi_run(i, binary, structure, seed, roi_lo_c, roi_hi_c, tmpdir,
            protection="none"):
    """第 i 次 SFI 注入 run。返回 (i, outcome_class, detail)。

    outcome ∈ 六类 {SDC, Crash, Hang, Masked, Inactive, SimulatorError}
    （classify.py §9.1 口径；SUM/FINAL 行对照 golden 在主线程做，
    但提取在此完成，减少二次读文件）。
    protection：CHAOSCache protectionModel（none/sed/secded/...），
    仅 cache structure（l1d/l2c_*）有效——Task 6.1 的 2x2
    （field x protection）验证臂用。
    """
    rng = random.Random(seed)
    out = os.path.join(tmpdir, f"inj{i:04d}")
    if os.path.exists(out):
        shutil.rmtree(out)
    # firstClock（CPU 周期域）：ROI tick / 1000（2.6GHz CPU 时钟下
    # 1 cycle = 385 ticks；用 1000 作保守近似并 clamp）。
    # cache structure（arm_chaos_cache 板 2GHz）：窗口由 main() 从该板
    # golden stats 换算传入（已是周期域），此处直接采样。
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
        # 6.1 修复：必须带 -r -e（原 --quiet 无重定向 → simout.txt
        # 从不生成 → 全部误分类 NoOutput，N=2 探针 2/2 复现）。
        byte_off = rng.randint(0, 63)
        cmd = [GEM5, "-r", "-e", "--silent-redirect", "-d", out, CACHE_CFG,
               "--cmd", binary, "--cpu", "O3",
               "--target", "l1d", "--target_field", "data",
               "--first_clock", str(first_clock),
               "--max_faults", "1", "--probability", "1.0",
               "--fault_type", "bit_flip",
               "--rng_seed", str(seed),
               "--target_byte_offset", str(byte_off)]
    elif structure in ("l2c_data", "l2c_tag"):
        # Task 6.1 L2C 双面臂：CHAOSCache 挂 shared L2（classic 层级
        # l2-cache-0）。tag 臂 = F5 合法别名替换（tag_to_legal 同族，
        # --target_field tag）；data 臂 = 数据位翻转。
        # protection（none/secded）实现 2x2 验证设计：data-face 在
        # secded 下应归零，tag 合法别名在 secded 下应保留（ECC 盲）。
        field = "data" if structure == "l2c_data" else "tag"
        byte_off = rng.randint(0, 63)
        cmd = [GEM5, "-r", "-e", "--silent-redirect", "-d", out, CACHE_CFG,
               "--cmd", binary, "--cpu", "O3",
               "--target", "l2", "--target_field", field,
               "--first_clock", str(first_clock),
               "--max_faults", "1", "--probability", "1.0",
               "--fault_type", "bit_flip",
               "--rng_seed", str(seed),
               "--target_byte_offset", str(byte_off),
               "--protection_model", protection]
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

    txt, err, rc, timed_out = run_gem5(out, cmd)
    n_inj = count_injections(out, structure)

    # --- 六类分类（classify.py §9.1 语义，SUM/FINAL 输出适配） ---
    # 1. Hang：超时且无校验输出（控制流损坏永不完成）
    out_line = extract_output_line(txt)
    if timed_out and out_line is None:
        return (i, "Hang", "timeout, no checksum line")
    # 2. workload 级 Page table fault panic：注入导致的损坏地址访问
    #    （gem5 SE 无处递送 → panic）。这是 workload DUE，归 Crash
    #    （例外规则见模块 docstring）。
    if WORKLOAD_PAGE_FAULT_RE.search(err):
        return (i, "Crash",
                "workload page-fault on corrupted address (DUE)")
    # 3. SimulatorError：gem5 自身坏（其他 panic/abort，非 workload 因果）
    if rc != 0 and out_line is None and not timed_out:
        if "panic" in err or "Assertion" in err or "fatal" in err:
            return (i, "SimulatorError",
                    f"gem5 panic (rc={rc}), no workload-fault text")
        return (i, "Crash", f"workload exited rc={rc}, no checksum")
    # 4. Inactive：注入未命中（0 条注入记录；日志缺失 → 不可判，按
    #    有注入处理并注明——诚实边界：不计入 Inactive）
    if n_inj == 0:
        return (i, "Inactive", "0 injections logged (fault did not land)")
    # 5/6. 有校验输出 → 待主线程对照 golden（SDC/Masked）
    if out_line is None:
        if timed_out:
            return (i, "Hang", "timeout after checksum? (odd)")
        return (i, "SimulatorError",
                f"no checksum line, rc={rc}, inj={n_inj}")
    return (i, "SUM_PENDING", out_line)   # 主线程对照 golden


def main():
    ap = argparse.ArgumentParser(description="Harpocrates SFI evaluation")
    ap.add_argument("--seq", required=True, help="被测 aarch64 静态 ELF")
    ap.add_argument("--structure", required=True,
                    choices=["irf", "l1d", "l2c_data", "l2c_tag", "lsq",
                             "intadd", "intmul", "fpadd", "fpmul"])
    ap.add_argument("--n", type=int, default=50, help="注入次数 N")
    ap.add_argument("--jobs", type=int, default=8, help="并行 gem5 进程数")
    ap.add_argument("--master-seed", type=int, default=20260916)
    ap.add_argument("--protection", default="none",
                    choices=["none", "sed", "secded", "secded_poison",
                             "parity_interleaved"],
                    help="CHAOSCache protectionModel（仅 l1d/l2c_* 臂；"
                         "Task 6.1 的 2x2 验证设计）")
    ap.add_argument("--out", default=None)
    ap.add_argument("--keep-runs", action="store_true")
    args = ap.parse_args()

    out = args.out or os.path.join(
        REPO, "artifacts",
        f"harp-eval-{args.structure}-{os.path.basename(args.seq)}")
    os.makedirs(out, exist_ok=True)
    tmpdir = os.path.join(out, "runs")
    os.makedirs(tmpdir, exist_ok=True)

    # 1. golden。cache structure 走 arm_chaos_cache 板（注入同板，
    # 平台一致）；其余走 two_level_taishan（与 coverage 同平台）。
    gdir = os.path.join(out, "golden")
    if args.structure in CACHE_STRUCTURES:
        gcmd = [GEM5, "-r", "-e", "--silent-redirect", "-d", gdir,
                CACHE_CFG, "--cmd", args.seq, "--cpu", "O3",
                "--target", "l1d" if args.structure == "l1d" else "l2",
                "--target_field", "data",
                "--first_clock", "1", "--max_faults", "0",
                "--probability", "0.0", "--rng_seed", str(args.master_seed)]
        gtxt, _, _, _ = run_gem5(gdir, gcmd)
        gm = extract_output_line(gtxt)
        if gm is None:
            sys.exit("ERROR: golden run produced no SUM=/FINAL= output")
        golden = gm
        print(f"golden (arm_chaos_cache board): {golden}")
        # ROI 窗口：该板无 CHAOSCov ROI stats → 从 golden stats 的
        # simTicks 换算周期（500 ticks/cycle @2GHz），窗口取
        # [5% 起始裕量, 95%]（覆盖主循环；诚实边界：非 m5ops ROI 精确窗）
        gs = os.path.join(gdir, "stats.txt")
        total_cycles = 40000
        if os.path.exists(gs):
            s = open(gs).read()
            m = re.search(r"^simTicks\s+(\d+)", s, re.M)
            if m:
                total_cycles = int(m.group(1)) // 500
        roi_lo_c = max(1, total_cycles // 20)
        roi_hi_c = max(roi_lo_c + 1, total_cycles * 19 // 20)
        print(f"ROI cycles (from golden simTicks/500, 5%-95%): "
              f"[{roi_lo_c}, {roi_hi_c}]")
    else:
        gtxt, _, _, _ = run_gem5(
            gdir, [GEM5, "-r", "-e", "--silent-redirect", "-d", gdir,
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
        roi_lo_c, roi_hi_c = roi_lo // 1000, roi_hi // 1000

    # 2. N 次 SFI（并行）
    tasks = [(i, args.seq, args.structure, args.master_seed + i,
              roi_lo_c, roi_hi_c, tmpdir, args.protection)
             for i in range(args.n)]
    outcomes = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(sfi_run, *t) for t in tasks]
        for idx, f in enumerate(as_completed(futs), 1):
            i, cls, detail = f.result()
            outcomes[i] = (cls, detail)
            if idx % 10 == 0 or idx == args.n:
                print(f"  {idx}/{args.n} runs done")

    # 3. 分类汇总（六类；SUM_PENDING 对照 golden 判 SDC/Masked）
    counts = {"SDC": 0, "Crash": 0, "Hang": 0,
              "Masked": 0, "Inactive": 0, "SimulatorError": 0}
    for i in range(args.n):
        cls, detail = outcomes[i]
        if cls == "SUM_PENDING":
            cls = "SDC" if detail != golden else "Masked"
        counts[cls] += 1
    detected = counts["SDC"] + counts["Crash"]
    lo, p, hi = wilson(detected, args.n)
    # 条件口径：剔 Inactive 与 SimulatorError 后的 detection
    n_active = args.n - counts["Inactive"] - counts["SimulatorError"]
    if n_active > 0:
        lo_a, p_a, hi_a = wilson(detected, n_active)
    else:
        lo_a, p_a, hi_a = (0.0, 0.0, 0.0)

    # 4. coverage 并列（golden --cov run 的 stats；cache 板无 CHAOSCov，
    #    改取 L2/L1D 命中统计作为注入面活跃度佐证）
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
        # cache 板（arm_chaos_cache）的注入面活跃度
        for name, key in [
                ("l2.demandHits", r"board\.cache_hierarchy\.l2-cache-0\.demandHits::total\s+(\d+)"),
                ("l2.demandMisses", r"board\.cache_hierarchy\.l2-cache-0\.demandMisses::total\s+(\d+)"),
                ("l1d.demandHits", r"board\.cache_hierarchy\.l1d-cache-0\.demandHits::total\s+(\d+)"),
                ("l1d.demandMisses", r"board\.cache_hierarchy\.l1d-cache-0\.demandMisses::total\s+(\d+)")]:
            m = re.search(key, s)
            if m:
                cov_stats[name] = int(m.group(1))

    # 5. 报告
    report = os.path.join(out, "summary.md")
    with open(report, "w") as f:
        f.write(f"# SFI detection — {os.path.basename(args.seq)} / "
                f"{args.structure}\n\n")
        f.write(f"- N = {args.n}（master seed {args.master_seed}）\n")
        f.write(f"- golden: `{golden}`\n")
        if args.structure in CACHE_STRUCTURES:
            f.write(f"- protection_model: {args.protection}\n")
        f.write(f"- detection = (SDC + Crash)/N = "
                f"({counts['SDC']} + {counts['Crash']})/{args.n} "
                f"= **{p:.4f}**\n")
        f.write(f"- Wilson 95% CI: [{lo:.4f}, {hi:.4f}]\n")
        f.write(f"- detection | active（剔 Inactive+SimulatorError，"
                f"n={n_active}）= **{p_a:.4f}** "
                f"[{lo_a:.4f}, {hi_a:.4f}]\n")
        f.write(f"- 六类分布: {counts}\n\n")
        # 注入空间的 AVF/IBR 口径必须对齐：IRF 的 SFI 打的是 int 物理
        # 寄存器空间，上界对照 irfAvfInt；FU 结构对照同类的 IBR
        # （IBR 是相关性指标而非上界，报告口径注明）。
        ace_key = {"irf": "irfAvfInt", "l1d": "l1dAvf", "lsq": "sqAvf",
                   "intadd": "ibrIntAdd", "intmul": "ibrIntMul",
                   "fpadd": "ibrFpAdd", "fpmul": "ibrFpMul"}.get(
            args.structure)
        f.write("## coverage vs detection（论文 Fig.4 形态）\n\n")
        if ace_key is not None:
            f.write(f"- {args.structure} ACE ({ace_key}): "
                    f"{cov_stats.get(ace_key, float('nan')):.4f}\n")
            f.write(f"- detection: {p:.4f}\n")
            ace = cov_stats.get(ace_key)
            if ace is not None:
                if args.structure in ("irf", "l1d", "lsq"):
                    f.write(f"- ACE >= detection（上界性质）: "
                            f"{'YES' if ace >= p else 'NO'}\n")
                else:
                    f.write(f"- IBR（相关性指标，非上界）：detection {p:.4f} "
                            f"vs IBR {ace:.4f}\n")
        else:
            # cache 板臂：无 CHAOSCov（该板不挂 coverage）——注入面活跃度
            # 用缓存命中计数佐证（诚实边界：非 ACE 口径）
            f.write(f"- {args.structure}：arm_chaos_cache 板无 CHAOSCov，"
                    f"ACE 不适用；注入面活跃度（golden run）：\n")
            for k in ("l2.demandHits", "l2.demandMisses",
                      "l1d.demandHits", "l1d.demandMisses"):
                if k in cov_stats:
                    f.write(f"  - {k}: {cov_stats[k]}\n")
        f.write("\n## 全部结构 coverage\n\n")
        for k, v in cov_stats.items():
            f.write(f"- {k}: {v}\n")
    print()
    print(open(report).read())
    print(f"report: {report}")
    if not args.keep_runs:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
