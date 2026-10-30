#!/usr/bin/env python3
"""test_lsu_s_unit_blocked.py — B2/B3 正式阻塞收口。

B2（触发不可达）：完整 workload 的 simTicks / eligible 计数小于首火下界，
    加 timeout 不可能触发。正式分类 BLOCKED_TRIGGER_REACHABILITY，记录
    RunID、workload 总 simTicks、tier、首火下界、eligible 总数、不可达
    原因、解除阻塞条件。
B3（F4）：权威规格 `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md`
    （F4 行）已定义：每 100,000 eligible 触发一次，连续污染 2-4 个；
    `chaos_lsu_trigger.hh` 已实现且 `tests/chaos_lsu_trigger_test.cc` 有
    确定性测试。故 F4 不是规格阻塞，而是按 eligible 计数的可达性阻塞。

用法：python3 tests/test_lsu_s_unit_blocked.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import r6_s_trigger_census as CENSUS   # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


REQUIRED = ("run_id", "tier", "simTicks", "earliest_fire_tick",
            "eligible_total", "reason", "unblock_condition")


def test_census_classification():
    print("[1] census classification and required fields")
    rows = CENSUS.census()
    by = {r["run_id"]: r for r in rows}
    check("20 NO_FIRE cells classified", len(rows) == 20, len(rows))
    reach = [r for r in rows
             if r["classification"] == "BLOCKED_TRIGGER_REACHABILITY"]
    report = [r for r in rows
              if r["classification"] == "BLOCKED_TRIGGER_REPORTING"]
    check("18 reachability-blocked", len(reach) == 18,
          [r["run_id"] for r in reach])
    check("2 reporting-blocked (S10-F5-W5/W9)",
          {r["run_id"] for r in report} == {"S10-F5-W5", "S10-F5-W9"},
          [r["run_id"] for r in report])
    check("no cell is silently passed",
          all(r["classification"].startswith("BLOCKED") for r in rows))

    for r in reach:
        missing = [k for k in REQUIRED if not str(r.get(k, "")).strip()]
        check(f"{r['run_id']}: required evidence fields", not missing, missing)
    for rid in ("S07-F4-W5", "S11-F4-W5", "S11-F4-W6"):
        r = by.get(rid)
        check(f"{rid}: F4 is reachability-blocked, not spec-blocked",
              r is not None and
              r["classification"] == "BLOCKED_TRIGGER_REACHABILITY", r)
        if r:
            check(f"{rid}: eligible floor is the F4 100000-event interval",
                  r.get("earliest_fire_events") == 100000,
                  r.get("earliest_fire_events"))
            check(f"{rid}: whole-run eligible below the floor",
                  r.get("eligible_total") is not None and
                  r["eligible_total"] < 100000, r.get("eligible_total"))
    for rid in ("S13-F1-W12", "S13-F2-W12"):
        r = by.get(rid)
        check(f"{rid}: cycle floor exceeds whole-run simTicks",
              r is not None and r["simTicks"] is not None and
              r["earliest_fire_tick"] is not None and
              r["simTicks"] < r["earliest_fire_tick"], r)
    # anti-cheat: the unblock condition must not propose forbidden shortcuts
    forbidden = ("reduce interval", "lower interval", "change seed",
                 "force injection", "longer timeout")
    for r in reach:
        u = str(r.get("unblock_condition", "")).lower()
        check(f"{r['run_id']}: unblock condition is honest",
              u and not any(f in u for f in forbidden), u)


def test_f4_authoritative():
    print("[2] F4 authoritative semantics")
    spec = (ROOT / "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md")
    text = spec.read_text(errors="replace")
    line = next((ln for ln in text.splitlines()
                 if ln.startswith("| F4 |")), "")
    check("authoritative F4 row exists", bool(line))
    check("F4 defined as 100000-eligible interval",
          "100,000" in line or "100000" in line, line)
    check("F4 defined as 2-4 consecutive eligible events",
          "2-4" in line, line)
    trig = (ROOT / "CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh").read_text()
    check("implementation uses the 100000 interval",
          "F4: return  100000" in trig or "case ChaOSLsuTier::F4: return  100000"
          in trig or "100000" in trig)
    check("implementation bursts 2-4", "2 + rng % 3" in trig)
    check("deterministic F4 unit test exists",
          (ROOT / "tests/chaos_lsu_trigger_test.cc").exists() and
          "F4" in (ROOT / "tests/chaos_lsu_trigger_test.cc").read_text())


def test_f4_determinism():
    print("[3] F4 same-seed bit-identical reproducibility")
    src = ROOT / "tests/chaos_lsu_trigger_test.cc"
    gxx = shutil.which("g++") or shutil.which("c++")
    check("compiler present", gxx is not None)
    if not gxx:
        return
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "trig"
        r = subprocess.run([gxx, "-std=c++17", "-I",
                            str(ROOT / "CHAOS/gem5/src"), str(src),
                            "-o", str(exe)], capture_output=True, text=True)
        check("trigger unit test compiles", r.returncode == 0,
              r.stderr[-1200:])
        if r.returncode != 0:
            return
        a = subprocess.run([str(exe)], capture_output=True, text=True)
        b = subprocess.run([str(exe)], capture_output=True, text=True)
        check("trigger unit test passes", a.returncode == 0,
              a.stdout[-800:])
        check("same seed -> byte-identical output", a.stdout == b.stdout)


def main():
    for fn in (test_census_classification, test_f4_authoritative,
               test_f4_determinism):
        fn()
    if FAILED:
        print(f"\nFAILED {len(FAILED)}: {FAILED}")
        return 1
    print("\nALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
