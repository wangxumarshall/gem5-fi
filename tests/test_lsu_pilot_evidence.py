#!/usr/bin/env python3
"""[MDSPEC][R4-3] pilot 证据汇总器——RunID→单元归属（评审 Important-1 回归）。

R4-3 评审发现：directed 载体（C09-R4T3-MSHRREF-sN）此前一律 unit=null，
pilot_evidence.json 的逐单元索引（kinds_observed_by_unit）与 coverage_matrix
的全局 kind 并集判据互相矛盾——矩阵称 L1d-Cache 11/11 而逐单元索引没有
mshr_alloc。本测试钉死：
  1. unit_of 精确匹配矩阵 RunID → 该单元（basis="exact"）；
  2. unit_of 行标签回退：任意 <row>-<suffix> 辅助运行按行标签唯一归属
     （C09-R4T3-MSHRREF-s1 → L1d-Cache；A01-F0-W3-campaign → AGU；
     任意未来命名 C09-<anything> 同样归属——非逐名特判）；
  3. 未知行标签（C4-*）与跨单元歧义行标签 → (None, None)（诚实不归属）；
  4. 已交付证据文件自洽：kinds_observed_by_unit / kinds_observed 严格等于
     按 pilots[].unit/kinds 重算的结果（防止再出现"两套口径"）；
  5. 已交付证据文件里 L1d-Cache 逐单元含全部 11 个必需节点（含
     mshr_alloc），且 mshr_alloc 的提供者全部归属 L1d-Cache——矩阵 11/11
     的主张在逐单元索引可验证（评审要求的审计入口）。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_pilot_evidence as PE       # noqa: E402
import lsu_coverage_matrix as CM      # noqa: E402  （UNIT_REQUIRED_NODES 单源）


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name +
              ("   <- " + detail if not cond else ""))
        if not cond:
            fails.append(name)

    entries = PE._map_entries()
    check("runid_map_loaded", len(entries) > 0, f"n={len(entries)}")

    # --- 1. 精确匹配 ------------------------------------------------------
    check("exact_match", PE.unit_of("A01-F0-W3", entries) == ("AGU", "exact"),
          str(PE.unit_of("A01-F0-W3", entries)))
    check("exact_match_cache",
          PE.unit_of("C09-F0-W6", entries) == ("L1d-Cache", "exact"),
          str(PE.unit_of("C09-F0-W6", entries)))

    # --- 2. 行标签回退（通用，非逐名特判）---------------------------------
    check("row_tag_carrier",
          PE.unit_of("C09-R4T3-MSHRREF-s1", entries) == ("L1d-Cache", "row_tag"),
          str(PE.unit_of("C09-R4T3-MSHRREF-s1", entries)))
    check("row_tag_campaign_rerun",
          PE.unit_of("A01-F0-W3-campaign", entries) == ("AGU", "row_tag"),
          str(PE.unit_of("A01-F0-W3-campaign", entries)))
    check("row_tag_mech_variant",
          PE.unit_of("P01-F0-W8-P03mech", entries) == ("数据预取器", "row_tag"),
          str(PE.unit_of("P01-F0-W8-P03mech", entries)))
    check("row_tag_any_future_suffix",
          PE.unit_of("C09-ANYFUTURE-s9", entries) == ("L1d-Cache", "row_tag"),
          str(PE.unit_of("C09-ANYFUTURE-s9", entries)))

    # --- 3. 未知 / 歧义 → 不归属 ------------------------------------------
    check("unknown_tag_none",
          PE.unit_of("C4-cache_dirtyevict", entries) == (None, None),
          str(PE.unit_of("C4-cache_dirtyevict", entries)))
    check("unknown_rid_none",
          PE.unit_of("ZZ9-F0-W1", entries) == (None, None),
          str(PE.unit_of("ZZ9-F0-W1", entries)))
    amb = [{"run_id": "X1-F0-W1", "unit": "U-a"},
           {"run_id": "X1-F0-W2", "unit": "U-b"}]
    check("ambiguous_tag_none",
          PE.unit_of("X1-carrier-s1", amb) == (None, None),
          str(PE.unit_of("X1-carrier-s1", amb)))

    # --- 4. 已交付证据文件自洽 --------------------------------------------
    ev_path = ROOT / "docs/gem5-fi/lsu/mdspec/pilot_evidence.json"
    ev = json.loads(ev_path.read_text(encoding="utf-8"))
    recompute, union = {}, set()
    for rid, p in ev["pilots"].items():
        check(f"unit_source_present:{rid}",
              p.get("unit_source") in ("exact", "row_tag", None),
              str(p.get("unit_source")))
        union.update(p["kinds"])
        if p["unit"]:
            recompute.setdefault(p["unit"], set()).update(p["kinds"])
    check("by_unit_self_consistent",
          {k: sorted(v) for k, v in recompute.items()}
          == ev["kinds_observed_by_unit"],
          "kinds_observed_by_unit != 按 pilots[].unit 重算")
    check("union_self_consistent",
          sorted(union) == ev["kinds_observed"],
          "kinds_observed != 按 pilots[].kinds 重算")

    # --- 5. L1d-Cache 11/11 在逐单元索引可验证 ----------------------------
    req = CM.UNIT_REQUIRED_NODES["L1d-Cache"]
    got = ev["kinds_observed_by_unit"].get("L1d-Cache", [])
    missing = [k for k in req if k not in got]
    check("l1d_all_required_in_per_unit_index", not missing,
          f"missing={missing}")
    check("mshr_alloc_in_l1d_per_unit", "mshr_alloc" in got,
          "mshr_alloc 不在 kinds_observed_by_unit['L1d-Cache']")
    providers = [rid for rid, p in ev["pilots"].items()
                 if "mshr_alloc" in p["kinds"]]
    check("mshr_alloc_providers_attributed_to_l1d",
          bool(providers) and all(ev["pilots"][r]["unit"] == "L1d-Cache"
                                  for r in providers),
          str([(r, ev["pilots"][r]["unit"]) for r in providers]))

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
