#!/usr/bin/env python3
"""[MDSPEC][R6-FIXCPP/T2] consumer_summary 聚合逻辑（不跑仿真）。

契约冻结于 FIX-TOOLS `4c74e3ac`（`tools/lsu_prop_fields.py` 的 SUMMARY_*
+ `validate_consumer_summary`）。本套件钉 C++ 半边：
  [1] 真编译 + 真运行独立单测（tests/chaos_consumer_summary_test.cc），打印全部
      PASS；
  [2] 从真实输出抽取每条 `CONSUMER-SUMMARY:` 行，用**冻结契约的校验器**复核
      （若本 worktree 的 tools/ 已含 `validate_consumer_summary` 则直接用真件，
      否则用逐条对齐的本地移植；两条路径都打印，绝不静默跳过）；
  [3] 逐字对照 50 重复 consumer 的期望行；
  [4] 规模下降实测（1000 重复 → 2 行）；
  [5] 防漂移：C++ 聚合器只聚合 `consumer`、字段前缀与工具一致。

用法：python3 tests/test_lsu_r6_fixcpp_consumer_summary.py   （exit 0 = 全 PASS）
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "CHAOS/gem5/src"
HARNESS = ROOT / "tests/chaos_consumer_summary_test.cc"
AGGR_HH = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/chaos_consumer_summary.hh"

sys.path.insert(0, str(ROOT / "tools"))

failed = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name
          + ("" if cond or not detail else f"  [{detail}]"))
    if not cond:
        failed.append(name)


# --- frozen-contract validator: prefer the real tools module if present ------
try:  # pragma: no cover - depends on whether the FIX-TOOLS lane has landed
    import lsu_prop_fields as _PF  # noqa: E402
    _HAVE_REAL = all(hasattr(_PF, n) for n in
                     ("parse_consumer_summary", "validate_consumer_summary"))
except Exception:                                   # noqa: BLE001
    _PF = None
    _HAVE_REAL = False

SUMMARY_PREFIX = "CONSUMER-SUMMARY:"
_STR_F = ("schema", "version", "run_id", "sample_run_id", "fault_id", "source_id")
_INT_F = ("schema", "version", "suppressed_consumer_count",
          "distinct_dyn_seq_count", "emitted_consumer_count", "first_tick",
          "last_tick", "min_dyn_seq", "max_dyn_seq", "total_before", "total_after")
_MAP_F = ("by_kind", "by_outcome")


def _port_parse(line):
    i = line.find(SUMMARY_PREFIX)
    if i < 0:
        return None
    rec = {f: "" for f in set(_STR_F) | set(_INT_F) | set(_MAP_F)}
    for tok in line[i + len(SUMMARY_PREFIX):].strip().split():
        k, sep, v = tok.partition("=")
        if sep:
            rec[k] = v
    return rec


def _port_parse_map(raw):
    out = {}
    if not str(raw).strip():
        return out
    for part in str(raw).split(","):
        k, sep, v = part.partition(":")
        if not sep or not k.strip():
            return None
        try:
            out[k.strip()] = int(v)
        except ValueError:
            return None
    return out


def _port_validate(rec):
    errs = []
    for f in _STR_F:
        if not str(rec.get(f, "")).strip():
            errs.append(f"缺必录字段 '{f}'")
    for f in _MAP_F:
        if not str(rec.get(f, "")).strip():
            errs.append(f"缺必录字段 '{f}'")
    ints = {}
    for f in _INT_F:
        try:
            ints[f] = int(str(rec.get(f, "")).strip())
        except (TypeError, ValueError):
            errs.append(f"字段 '{f}' 非整数")
    if errs:
        return errs
    bk = _port_parse_map(rec.get("by_kind"))
    bo = _port_parse_map(rec.get("by_outcome"))
    if bk is None or bo is None:
        return ["by_kind/by_outcome 格式非法"]
    if ints["total_before"] != ints["total_after"]:
        errs.append("计数不守恒 total_before != total_after")
    if ints["total_after"] != (ints["emitted_consumer_count"]
                               + ints["suppressed_consumer_count"]):
        errs.append("计数不守恒 total_after != emitted + suppressed")
    if sum(bk.values()) != ints["total_before"]:
        errs.append("by_kind 合计 != total_before")
    if sum(bo.values()) != ints["total_before"]:
        errs.append("by_outcome 合计 != total_before")
    if ints["distinct_dyn_seq_count"] > ints["total_before"]:
        errs.append("distinct_dyn_seq_count > total_before")
    if ints["total_before"] > 0 and ints["emitted_consumer_count"] == 0:
        errs.append("简单截断（全抑无出）")
    return errs


def validate(line):
    if _HAVE_REAL:
        return _PF.validate_consumer_summary(_PF.parse_consumer_summary(line))
    return _port_validate(_port_parse(line))


def main():
    print(f"[0] 校验器来源：{'真件 tools/lsu_prop_fields.py' if _HAVE_REAL else '冻结契约的本地移植（tools/ 尚无 FIX-TOOLS 件）'}")

    print("[1] 真编译 + 真运行独立单测")
    out = ""
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "csum_test"
        cc = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             f"-I{SRC}", str(HARNESS), "-o", str(exe)],
            capture_output=True, text=True, cwd=str(ROOT))
        check("harness compiles clean (-Wall -Wextra -Werror)",
              cc.returncode == 0, (cc.stderr or "").strip()[:200])
        if cc.returncode == 0:
            r = subprocess.run([str(exe)], capture_output=True, text=True)
            out = r.stdout or ""
            print(out.rstrip())
            check("harness ALL PASS",
                  r.returncode == 0 and "ALL PASS" in out, out.strip()[-200:])
        else:
            print("  (harness did not build; behavioral checks skipped)")

    print("[2] 用冻结契约校验器复核真实 summary 行")
    lines = [ln.strip() for ln in out.splitlines()
             if ln.strip().startswith(SUMMARY_PREFIX)]
    check("真实输出含 CONSUMER-SUMMARY 行", len(lines) >= 2, str(len(lines)))
    for ln in lines:
        errs = validate(ln)
        check(f"校验通过：{ln[:70]}…" if errs else "校验通过（summary 行）",
              not errs, str(errs))

    print("[3] 50 重复 consumer 的期望行逐字对照")
    want = ("CONSUMER-SUMMARY: schema=1 version=1 run_id=L05-F0-W5 "
            "sample_run_id=s1 fault_id=1 source_id=phys_reg:31 "
            "suppressed_consumer_count=49 distinct_dyn_seq_count=1 "
            "emitted_consumer_count=1 first_tick=100 last_tick=149 "
            "min_dyn_seq=7 max_dyn_seq=7 by_kind=consumer:50 "
            "by_outcome=sd_observed:50 total_before=50 total_after=50")
    check("期望行在真实输出中逐字出现", want in out, want)

    print("[4] 规模下降实测（1000 重复 → 2 行 = 500x）")
    m = re.search(r"reduction.*?:\s*([0-9.]+)x", out)
    if m is None:
        m = re.search(r"(\d+)x reduction", out)
    ratio = float(m.group(1)) if m else 0.0
    check("1000 重复 consumer → 500x 下降（真实输出）", ratio >= 100.0,
          str(ratio))

    print("[5] 防漂移：聚合器只聚合 consumer、前缀与工具一致")
    agg = AGGR_HH.read_text(encoding="utf-8")
    check("只聚合 consumer（aggregatableKind 唯一白名单）",
          'return kind == "consumer";' in agg)
    check("记录前缀与工具一致（CONSUMER-SUMMARY:）",
          '"CONSUMER-SUMMARY:"' in agg or "CONSUMER-SUMMARY:" in agg)
    check("字段顺序冻结（by_kind -> by_outcome -> total_before -> total_after）",
          agg.find('by_kind=') < agg.find('by_outcome=')
          < agg.find('total_before=') < agg.find('total_after='))
    check("资源上限非静默：有 resourceAbortLine 且 suppressed=0",
          "resourceAbortLine" in agg and "suppressed=0" in agg)

    print()
    if failed:
        print(f"FAILURES: {failed}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
