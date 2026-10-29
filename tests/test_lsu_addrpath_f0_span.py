#!/usr/bin/env python3
"""test_lsu_addrpath_f0_span.py — [R6-A-SPAN] 所有 addrpath F0 模型必须用
(warmup=1, span=实测 golden eligible 流长) 参数化，而不是历史 span=1000。

缺陷（2026-10-28 A04-F0-W3 seed1 实测）：
  `_addrpath_tier_flags` 只对 A07 查 `ADDRPATH_F0_SPAN`，其余 addrpath 模型
  一律 warmup=0/span=1000；而 agu_addrmodes 的 eligible 流约 2800 —— F0 抽签
  被限制在前 1000 个事件，campaign 打印 EARLY_BIAS（silent early bias）。
  R4-1-review-I2 规定的正确参数化是 warmup=1 + span=measured golden size
  （A07 注释：“TRUE F0-uniform parameterization”）。

本测试钉住：
  1) A 单元全部 F0 (model, workload) 对都在 ADDRPATH_F0_SPAN 表中；
  2) `_addrpath_tier_flags(model, "F0", wl)` 返回 warmup=1 且 span=表值；
  3) F5（A03）不套用 F0 参数化（tier flags 保持既有语义）。

用法：python3 tests/test_lsu_addrpath_f0_span.py   退出码 0 = ALL PASSED
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as C  # noqa: E402

FAILED = []


def fail(msg):
    FAILED.append(msg)
    print(f"FAIL: {msg}")


# A 单元 F0 格：(model, workload binary)
F0_PAIRS = [
    ("A01", "agu_addrmodes"), ("A01", "gap_bfs"),
    ("A02", "agu_addrmodes"), ("A02", "gap_bfs"),
    ("A04", "agu_addrmodes"), ("A04", "mini_check"),
    ("A05", "agu_addrmodes"),
    ("A07", "agu_addrmodes"), ("A07", "sq_forward"),
    ("A08", "agu_addrmodes"), ("A08", "sq_forward"),
]


def main():
    for pair in F0_PAIRS:
        if pair not in C.ADDRPATH_F0_SPAN:
            fail(f"ADDRPATH_F0_SPAN missing {pair} (F0 uniform draw has no "
                 f"measured golden stream)")
            continue
        span = C.ADDRPATH_F0_SPAN[pair]
        if not isinstance(span, int) or span <= 1:
            fail(f"ADDRPATH_F0_SPAN[{pair}] = {span!r} is not a positive "
                 f"measured eligible count")
            continue
        flags = C._addrpath_tier_flags(pair[0], "F0", pair[1])
        if flags is None:
            fail(f"_addrpath_tier_flags({pair}, F0) returned None (loud "
                 f"refusal) — table/refusal mismatch")
            continue
        try:
            warm = flags[flags.index("--addrpath_warmup_events") + 1]
            span_arg = flags[flags.index("--addrpath_span_events") + 1]
        except (ValueError, IndexError):
            fail(f"_addrpath_tier_flags({pair}, F0) lacks warmup/span flags: "
                 f"{flags}")
            continue
        if warm != "1":
            fail(f"{pair}: F0 warmup={warm} (must be 1 — the A07-proven "
                 f"draw_end = 1 + span keeps the window on the golden "
                 f"stream)")
        if span_arg != str(span):
            fail(f"{pair}: F0 span={span_arg} != measured {span}")

    # F5 keeps its own semantics (no F0 span rewrite)
    a03 = C._addrpath_tier_flags("A03", "F5", "agu_addrmodes")
    if a03 and "--addrpath_warmup_events" in a03:
        w = a03[a03.index("--addrpath_warmup_events") + 1]
        if w != "0":
            fail(f"A03 F5 warmup changed to {w}: F5 tier flags must stay "
                 f"byte-identical")

    if FAILED:
        print(f"ADDRPATH F0 SPAN TEST: {len(FAILED)} FAILURE(S)")
        return 1
    print("ADDRPATH F0 SPAN TEST: ALL PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
