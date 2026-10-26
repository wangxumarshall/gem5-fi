#!/usr/bin/env python3
"""test_lsu_geom_distribution.py — [MDSPEC][A4] GEOM 移植验证（35ccda91）。

用户指令二.2：reject/resample 必须可观测，不得**静默**改变 A01/A02 目标分布。
GEOM 语义（35ccda91 diff 实证）：跨 64B 线的随机位翻转按设计重采样（≤16 次，
替代原先的 packet-geometry 断言崩溃）；固定位模式一次即拒；拒斥经
REJECT 日志行（reason=block_geometry，写 addrpath_injections.log）与退出摘要
CHAOS_L0_DECLINE 行的 post_geomreject= 字段（printf 至 stdout，仅正常退出时
运行——abort 运行以逐注入 REJECT 行为可观测面）可观测；translate 站点日志
使用真实 mode 标签（修复"所有模式硬编码 low_bit_flip"）。
用法：python3 tests/test_lsu_geom_distribution.py   （退出码 0=全 PASS）
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEM5 = ROOT / "CHAOS" / "gem5" / "build" / "ARM" / "gem5.opt"
PROXY = ROOT / "configs" / "se" / "lsu_proxy.py"
WL = ROOT / "workloads" / "directed" / "agu_addrmodes"


def run_mode(tag, mode):
    out = Path("/tmp") / f"mdspec_a4_{tag}"
    subprocess.run(["rm", "-rf", str(out)], check=False)
    r = subprocess.run(
        [str(GEM5), f"--outdir={out}", str(PROXY), "--cmd", str(WL),
         "--cpu", "O3", "--chaos_addrpath", f"--addrpath_mode={mode}",
         "--addrpath_lsu_tier=F0", "--addrpath_span_events=2000",
         "--addrpath_max_faults=2"],
        capture_output=True, text=True, timeout=900)
    inj = out / "addrpath_injections.log"
    inj_text = inj.read_text(encoding="utf-8", errors="replace") if inj.exists() else ""
    return r, inj_text


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name + ("   <- " + detail if not cond else ""))
        if not cond:
            fails.append(name)

    # ---- 1) a01_bit：真实 mode 标签 + 全部注入满足 64B 几何 ----
    r1, inj1 = run_mode("a01", "a01_bit")
    lines1 = [l for l in inj1.splitlines() if "faults_injected" in l]
    check("a01_injection_lines_present", len(lines1) >= 1,
          f"rc={r1.returncode} lines={len(lines1)}")
    check("a01_true_mode_label",
          any("mode=a01_bit" in l for l in lines1),
          f"first={lines1[0] if lines1 else None}")
    va = re.findall(r"new_vaddr=0x([0-9a-fA-F]+)", inj1)
    check("a01_all_injected_within_64B_line",
          bool(va) and all((int(v, 16) & 63) + 8 <= 64 for v in va),
          f"new_vaddrs={va[:4]}")

    # ---- 2) a02_2bit：标签随模式变化（非硬编码） ----
    r2, inj2 = run_mode("a02", "a02_2bit")
    lines2 = [l for l in inj2.splitlines() if "faults_injected" in l]
    check("a02_true_mode_label",
          any("mode=a02_2bit" in l for l in lines2),
          f"first={lines2[0] if lines2 else None}")

    # ---- 3) 拒斥可观测（两条面）：REJECT 行格式 + 退出摘要 post_geomreject ----
    for txt, tag in ((inj1, "a01"), (inj2, "a02")):
        for l in txt.splitlines():
            if "REJECT" in l:
                check(f"{tag}_reject_line_format",
                      ("reason=block_geometry" in l) and ("mode=" in l),
                      l[:160])
                break
    corpus = r1.stdout + r2.stdout
    m = re.search(r"CHAOS_L0_DECLINE:.*post_geomreject=(\d+)", corpus)
    check("geomreject_counter_observable",
          m is not None,
          "stdout 未见 CHAOS_L0_DECLINE...post_geomreject=（若两 run 均 abort 属预期，由第 4 项兜底）")
    # ---- 4) byte7_zero（SE-inert，必然正常退出）：退出摘要必含 post_geomreject 字段 ----
    r3, inj3 = run_mode("b7", "byte7_zero")
    m3 = re.search(r"CHAOS_L0_DECLINE:.*post_geomreject=(\d+)", r3.stdout)
    check("byte7_clean_exit_summary_has_geomreject",
          m3 is not None,
          f"rc={r3.returncode} stdout_tail={r3.stdout[-200:] if not m3 else ''}")
    check("byte7_geomreject_is_zero",
          m3 is not None and int(m3.group(1)) == 0,
          m3.group(0) if m3 else "（无摘要行）")  # byte7 清位不改变 offset，几何恒合法

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
