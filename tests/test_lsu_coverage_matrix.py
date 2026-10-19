#!/usr/bin/env python3
"""test_lsu_coverage_matrix.py — [MDSPEC][B2] 覆盖矩阵（Review Focus #1 核心）。"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_coverage_matrix as CM   # noqa: E402


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name + ("   <- " + detail if not cond else ""))
        if not cond:
            fails.append(name)

    m = json.loads((ROOT / "docs/gem5-fi/lsu/mdspec/runid_map.json")
                   .read_text(encoding="utf-8"))
    rows = [(e["run_id"],) + CM.assess(e) for e in m["entries"]]
    st = [r[1] for r in rows]
    # Review Focus #1：钩子未装时 PASS 必须为 0（部分已有≠完整实现）
    check("baseline_pass_is_zero", st.count("PASS") == 0, f"PASS={st.count('PASS')}")
    check("blocked_count_matches_map",
          st.count("BLOCKED") == m["summary"]["status"]["BLOCKED"],
          f"matrix={st.count('BLOCKED')} map={m['summary']['status']['BLOCKED']}")
    check("partial_is_rest",
          st.count("PARTIAL") == 325 - st.count("BLOCKED") - st.count("PASS"),
          f"PARTIAL={st.count('PARTIAL')}")
    # 装一个族的 AGU 路径不全（H1/H2/H0 三族才 PASS）——逐族翻转语义
    CM.HOOK_REGISTRY["H1_lsq_unified"] = True
    agu = [e for e in m["entries"] if e["unit"] == "AGU" and e["status"] != "BLOCKED"]
    check("agu_still_partial_with_one_hook",
          all(CM.assess(e)[0] == "PARTIAL" for e in agu),
          f"n_agu={len(agu)}")
    CM.HOOK_REGISTRY["H2_tlb_trace"] = True
    CM.HOOK_REGISTRY["H0_prop_fields"] = True
    check("agu_passes_with_all_three_hooks",
          all(CM.assess(e)[0] == "PASS" for e in agu),
          f"n_agu={len(agu)} reasons={CM.assess(agu[0]) if agu else None}")
    CM.HOOK_REGISTRY["H1_lsq_unified"] = False
    CM.HOOK_REGISTRY["H2_tlb_trace"] = False
    CM.HOOK_REGISTRY["H0_prop_fields"] = False
    # CLI 全链
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools/lsu_coverage_matrix.py"),
         "--map", str(ROOT / "docs/gem5-fi/lsu/mdspec/runid_map.json"),
         "--out", "/tmp/mdspec_coverage_test.md"],
        capture_output=True, text=True, timeout=120)
    check("cli_generates_matrix",
          r.returncode == 0 and "PASS=0" in r.stdout,
          f"rc={r.returncode} out={r.stdout.strip()[:120]}")

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
