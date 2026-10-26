#!/usr/bin/env python3
"""test_lsu_runner_ftier_no_collapse.py — [0202-REBUILD] F 档路由不得坍缩契约。

背景（实测缺陷）：`tools/lsu_runner.py` 的 armtlb 家族只从 `MODEL_FLAGS[model]`
取 injector_flags（**按 model，不按 frequency**），因此
T02-F2-W4 / T04-F2-W4 / T04-F6-W4 的 injector_flags 与各自 F0 兄弟**逐字节
相同** —— 经 runner 运行在物理上就是 F0。把这种运行报告成 F2/F6 成功是禁止的
（R6-FTIER：`--tlb_lsu_tier` 曾经半接线，F1–F6 不可表达）。

本套件锁死：
  1. 六个目标 RunID 的 armtlb injector_flags **两两不坍缩**：F0 不带 tier，
     F2 带 `--tlb_lsu_tier F2`，F6 带 `--tlb_lsu_tier F6`；
  2. F2/F6 的命令行里出现 tier flag（manifest 与命令同源）；
  3. 每个 RunID 的 tier flag 与 `LC._armtlb_lookup_tier_flags(freq)` 逐字节一致
     （复用唯一映射，不另写一套）；
  4. F0 保持 byte-for-byte legacy（不带 tier flag）。

用法：python3 tests/test_lsu_runner_ftier_no_collapse.py   （退出码 0=全 PASS）
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402
import lsu_runner as RUN  # noqa: E402

FAILED = []


def check(name, ok, detail=""):
    print(("  PASS " if ok else "  FAIL ") + name + (("  :: " + str(detail)) if detail and not ok else ""))
    if not ok:
        FAILED.append(name)


# ITEM → (RunID, freq) for the six frozen 0202 targets
SIX = [("ITEM-041", "T01-F0-W4", "F0"), ("ITEM-047", "T02-F0-W4", "F0"),
       ("ITEM-049", "T02-F2-W4", "F2"), ("ITEM-052", "T04-F0-W4", "F0"),
       ("ITEM-053", "T04-F2-W4", "F2"), ("ITEM-054", "T04-F6-W4", "F6")]


def main():
    real_sha = RUN._sha
    RUN._sha = lambda p: "0" * 64
    try:
        os.environ.pop(RUN.FS_CHECKPOINT_ENV, None)
        ms = {}
        print("[1] 六个 RunID 的 armtlb injector_flags 不坍缩")
        for item, runid, freq in SIX:
            m = RUN.build_manifest(item, "engineering", 0)
            ms[runid] = m
            check(f"{item} → {runid} freq={freq}", m["run_id"] == runid and m["frequency"] == freq,
                  f"{m['run_id']}/{m['frequency']}")

        def tier_of(m):
            f = m["injector_flags"]
            return f[f.index("--tlb_lsu_tier") + 1] if "--tlb_lsu_tier" in f else None

        for item, runid, freq in SIX:
            m = ms[runid]
            check(f"{runid} tier flag 与权威映射一致（LC._armtlb_lookup_tier_flags）",
                  [t for t in (["--tlb_lsu_tier", tier_of(m)] if tier_of(m) else [])]
                  == LC._armtlb_lookup_tier_flags(freq),
                  f"got={tier_of(m)} expect={LC._armtlb_lookup_tier_flags(freq)}")

        print("[2] F0 legacy 不带 tier；F2/F6 必须带")
        for runid in ("T01-F0-W4", "T02-F0-W4", "T04-F0-W4"):
            check(f"{runid} F0 不带 --tlb_lsu_tier", tier_of(ms[runid]) is None, tier_of(ms[runid]))
        for runid, want in (("T02-F2-W4", "F2"), ("T04-F2-W4", "F2"), ("T04-F6-W4", "F6")):
            check(f"{runid} 带 --tlb_lsu_tier {want}", tier_of(ms[runid]) == want, tier_of(ms[runid]))

        print("[3] 命令与 manifest 同源（tier flag 真进入守卫命令）")
        for runid, want in (("T02-F2-W4", "F2"), ("T04-F2-W4", "F2"), ("T04-F6-W4", "F6")):
            _cfg, args = RUN.build_guard_cmd(ms[runid], Path("/tmp/does_not_matter"))
            ok = "--tlb_lsu_tier" in args and args[args.index("--tlb_lsu_tier") + 1] == want
            check(f"{runid} 守卫命令含 tier={want}", ok, args)

        print("[4] 非 F0 的 armtlb 命令行两两互异（反坍缩）")
        norm = {}
        for runid in ("T01-F0-W4", "T02-F0-W4", "T02-F2-W4", "T04-F0-W4", "T04-F2-W4", "T04-F6-W4"):
            _cfg, args = RUN.build_guard_cmd(ms[runid], Path("/tmp/does_not_matter"))
            norm[runid] = tuple(args)
        pairs = [("T01-F0-W4", "T02-F0-W4"), ("T02-F0-W4", "T02-F2-W4"),
                 ("T04-F0-W4", "T04-F2-W4"), ("T04-F2-W4", "T04-F6-W4"),
                 ("T02-F2-W4", "T04-F2-W4")]
        for a, b in pairs:
            check(f"命令 {a} != {b}", norm[a] != norm[b])
    finally:
        RUN._sha = real_sha

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
