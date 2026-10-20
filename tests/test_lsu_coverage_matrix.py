#!/usr/bin/env python3
"""[MDSPEC][B2] 覆盖矩阵（Review Focus #1 核心）——2026-10-20 证据化重写。

旧版用 8 个注册表布尔值判 PASS，被实证证伪（H4/H5/H6 有整族节点未实现仍判
PASS）。新版判据：**逐节点、双证据**（实现 + 真实运行观测），见
tools/lsu_coverage_matrix.py 头注释。本测试钉死：
  1. 无证据文件时**任何**非 BLOCKED 都不能 PASS（"没证据"≠"已实现"）；
  2. 缺**任一**节点即 PARTIAL 并逐项列出（不得因族内多数节点在就判完成）；
  3. BLOCKED 数与 runid_map 守恒；
  4. 证据充分时对应单元转 PASS（反向验证判据不是恒假）。
"""
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
        print(("PASS " if cond else "FAIL ") + name +
              ("   <- " + detail if not cond else ""))
        if not cond:
            fails.append(name)

    m = json.loads((ROOT / "docs/gem5-fi/lsu/mdspec/runid_map.json")
                   .read_text(encoding="utf-8"))
    entries = m["entries"]
    live = [e for e in entries if e["status"] != "BLOCKED"]

    # --- 1. 无证据 ⇒ 非 BLOCKED 一律 PARTIAL（PASS 必须由证据支撑） -------
    st = [CM.assess(e, None)[0] for e in entries]
    check("no_evidence_means_no_pass", st.count("PASS") == 0,
          f"PASS={st.count('PASS')}")
    check("blocked_count_conserved",
          st.count("BLOCKED") == m["summary"]["status"]["BLOCKED"],
          f"matrix={st.count('BLOCKED')} map={m['summary']['status']['BLOCKED']}")
    check("partial_is_rest",
          st.count("PARTIAL") == len(entries) - st.count("BLOCKED"),
          f"PARTIAL={st.count('PARTIAL')}")

    # --- 2. 族内缺一个节点 ⇒ PARTIAL，且该节点被逐项列出 ------------------
    # AGU 需要 11 个节点；只给 10 个（缺 chain_end）必须 PARTIAL 并指名
    agu = [e for e in live if e["unit"] == "AGU"]
    req = CM.UNIT_REQUIRED_NODES["AGU"]
    partial_evidence = {"kinds_observed": [k for k in req if k != "chain_end"]}
    res = [CM.assess(e, partial_evidence) for e in agu]
    check("one_missing_node_blocks_family",
          all(r[0] == "PARTIAL" for r in res),
          f"n_agu={len(agu)}")
    check("missing_node_named_in_reason",
          all(any("chain_end" in w for w in r[1]) for r in res),
          str(res[0][1] if res else None))

    # --- 3. 证据充分 + 节点齐 ⇒ PASS（判据可满足，非恒假） -----------------
    full_evidence = {"kinds_observed": list(req)}
    res2 = [CM.assess(e, full_evidence) for e in agu]
    check("all_nodes_evidence_and_impl_passes",
          all(r[0] == "PASS" for r in res2),
          str(res2[0] if res2 else None))

    # --- 4. 未实现的节点即使"证据齐"也不能 PASS（实现证据不可绕过） --------
    fake_evidence = {"kinds_observed": req + ["totally_made_up_kind"]}
    # 把 AGU 需求里塞一个不存在的 kind：模拟"规格要求但发射端没实现"
    CM.UNIT_REQUIRED_NODES["AGU"] = req + ["not_implemented_kind"]
    res3 = [CM.assess(e, fake_evidence) for e in agu]
    check("unimplemented_node_blocks_pass",
          all(r[0] == "PARTIAL" and
              any("not_implemented_kind" in w for w in r[1]) for r in res3),
          str(res3[0][1] if res3 else None))
    CM.UNIT_REQUIRED_NODES["AGU"] = req

    # --- 5. CLI 端到端 -----------------------------------------------------
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools/lsu_coverage_matrix.py"),
         "--map", str(ROOT / "docs/gem5-fi/lsu/mdspec/runid_map.json"),
         "--out", "/tmp/mdspec_coverage_test.md"],
        capture_output=True, text=True, timeout=120)
    check("cli_generates_matrix",
          r.returncode == 0 and "PASS=0" in r.stdout,
          f"rc={r.returncode} out={r.stdout.strip()[:140]}")
    ev = ROOT / "docs/gem5-fi/lsu/mdspec/pilot_evidence.json"
    if ev.exists():
        r2 = subprocess.run(
            [sys.executable, str(ROOT / "tools/lsu_coverage_matrix.py"),
             "--map", str(ROOT / "docs/gem5-fi/lsu/mdspec/runid_map.json"),
             "--evidence", str(ev),
             "--out", "/tmp/mdspec_coverage_test_ev.md"],
            capture_output=True, text=True, timeout=120)
        check("cli_with_evidence_runs",
              r2.returncode == 0, f"rc={r2.returncode} {r2.stderr[-160:]}")

    # --- 6. 辅助运行证据边界（R4-3 评审 Important-1）-----------------------
    # 载体归属修复后：L1d-Cache 的 mshr_* 必需节点由 directed 载体
    # （C09-R4T3-MSHRREF-*，非矩阵 RunID）提供，矩阵单元自身的运行（含
    # campaign 单元 C09-F0-W6）未观测到——边界必须显式、可审计。
    if ev.exists():
        evidence = json.loads(ev.read_text(encoding="utf-8"))
        b = CM.aux_run_boundary(entries, evidence)
        l1d = b.get("L1d-Cache")
        check("boundary_l1d_names_mshr_alloc",
              l1d is not None and "mshr_alloc" in l1d["nodes"],
              str(l1d["nodes"] if l1d else None))
        check("boundary_l1d_carriers_all_six",
              l1d is not None and
              all(f"C09-R4T3-MSHRREF-s{i}" in l1d["aux_rids"]
                  for i in range(1, 7)),
              str(l1d["aux_rids"] if l1d else None))
        check("boundary_l1d_lists_campaign_cell",
              l1d is not None and "C09-F0-W6" in l1d["matrix_rids"],
              str(l1d["matrix_rids"] if l1d else None))
        # 通用性（非为 MSHRREF 特判）：数据预取器的 pf_queue/pf_issue 同样
        # 仅由辅助运行（campaign smoke 复跑 / 机理变体）提供，必须同样标出
        pf = b.get("数据预取器")
        check("boundary_prefetch_general_too",
              pf is not None and pf["nodes"] == ["pf_queue", "pf_issue"],
              str(pf["nodes"] if pf else None))
        # 无辅助独供节点的单元不得误标（Store Queue 7/7 全由矩阵运行观测）
        check("boundary_no_false_positive_sq",
              "Store Queue" not in b, str(sorted(b)))
        md = Path("/tmp/mdspec_coverage_test_ev.md").read_text(
            encoding="utf-8")
        check("md_pass_rows_annotated",
              "aux_run_nodes:mshr_alloc" in md)
        has_section = "## 辅助运行证据边界" in md
        check("md_boundary_section_present", has_section)
        tail = md.split("## 辅助运行证据边界", 1)[1] if has_section else ""
        check("md_boundary_names_carrier_and_campaign_cell",
              "C09-R4T3-MSHRREF-s1" in tail and "C09-F0-W6" in tail)
        check("md_capability_table_has_aux_column",
              "仅辅助运行观测" in md)

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
