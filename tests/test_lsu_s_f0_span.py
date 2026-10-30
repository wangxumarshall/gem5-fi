#!/usr/bin/env python3
"""F0 span 无偏标定契约：独立 census、上限、seed draw、拒绝复用、其他 tier 不受影响。

事实来源（2026-10-30 R6-S-REPAIR2）：
  * tools/lsu_campaign.py LSQFWD_F0_SPAN 的 6/6/1/6 与 S03=7；
  * docs/gem5-fi/lsu/evidence/R6-S-REPAIR2-CENSUS.md 的 campaign 同形绝对路径
    census（相对路径旧读数 7/7/2/7 不是同一个实验）；
  * CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh:265-273 的 F0 draw：
      next_fire = warmup(1) + chaosSampleLCG(seed) % span
    seed3/span=7 得到 next_fire=7 > eligible=6 ⇒ NO_FIRE（旧 span 的实证）。

用法：python3 tests/test_lsu_s_f0_span.py   退出码 0=全 PASS。
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def lcg(x):
    """chaos_event_sample.hh:49 的 chaosSampleLCG，逐位一致。"""
    return (x * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)


# (model, workload binary, campaign-form census eligible count)
PAIRS = [
    ("S01", "sq_forward", 6),
    ("S02", "sq_forward", 6),
    ("S08", "sq_forward", 1),
    ("S09", "sq_forward", 6),
    ("S03", "sq_forward", 7),
]


def main():
    print("[1] campaign-form census values, per (model, workload)")
    for model, wl, expected in PAIRS:
        got = LC.LSQFWD_F0_SPAN.get((model, wl))
        check(f"{model}/{wl} span == census {expected}", got == expected, got)
    check("S08 (1) is not silently copied from S01/S02 (6)",
          LC.LSQFWD_F0_SPAN[("S08", "sq_forward")] !=
          LC.LSQFWD_F0_SPAN[("S01", "sq_forward")])
    check("S09 and S03 have their own measured values",
          LC.LSQFWD_F0_SPAN[("S09", "sq_forward")] == 6 and
          LC.LSQFWD_F0_SPAN[("S03", "sq_forward")] == 7)

    print("[2] census document agrees with the table")
    doc = (ROOT / "docs/gem5-fi/lsu/evidence/R6-S-REPAIR2-CENSUS.md").read_text(
        encoding="utf-8")
    for model, _wl, expected in PAIRS[:4]:
        m = re.search(r"\|\s*%s\s*\|\s*directed/sq_forward\s*\|\s*(\d+)\s*\|"
                      % model, doc)
        check(f"census doc {model} = {expected}",
              m is not None and int(m.group(1)) == expected,
              m.group(1) if m else "row missing")

    print("[3] seed1/2/3 draws are inside [warmup, warmup+span)")
    for model, wl, span in PAIRS:
        draws = [1 + lcg(seed) % span for seed in (1, 2, 3)]
        check(f"{model} seed draws 1..{span}", all(1 <= d <= span for d in draws),
              draws)
        flags = LC._lsqfwd_tier_flags(model, "F0", wl)
        check(f"{model} F0 flags use the measured span",
              bool(flags) and flags[flags.index("--lsqfwd_span_events") + 1]
              == str(span), flags)
    # The old relative-path readings must not reappear: seed3 with span=7
    # would draw 7 > eligible 6 and silently NO_FIRE.
    check("seed3/span=7 reproduces the old NO_FIRE (draw 7 > 6)",
          1 + lcg(3) % 7 == 7)
    check("seed3/span=6 is reachable (draw <= 6)",
          1 + lcg(3) % 6 <= 6)

    print("[4] an unmeasured pair refuses loudly")
    check("unmeasured (model, workload) returns None",
          LC._lsqfwd_tier_flags("S01", "F0", "no_such_wl") is None)

    print("[5] F1/F2/F4/F5/F6 are unaffected by the F0 table")
    for tier in ("F1", "F2", "F4", "F5", "F6"):
        flags = LC._lsqfwd_tier_flags("S01", tier, "sq_forward")
        check(f"{tier} keeps the historical inert span",
              bool(flags) and flags[flags.index("--lsqfwd_span_events") + 1]
              == "1000", flags)
    r = LC._lsqfwd_tier_flags("S10", "F2", "sq_forward")
    check("F2 unreachable pair still refuses via its own table",
          isinstance(r, str) and "interval-tier-unreachable" in r, r)

    print(f"FAILED: {len(FAILED)}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
