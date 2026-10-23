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

    # --- 6. 辅助运行证据边界（R4-3 评审 Important-1；R4-5.1 更新）----------
    # R4-3 时期：L1d-Cache 的 mshr_* 必需节点仅由 directed 载体
    # （C09-R4T3-MSHRREF-*，非矩阵 RunID）提供。R4-5.1 C11 落地后，
    # **矩阵 RunID 自身的 campaign 运行**（C11-F0-W6，3-seed 真跑）直接
    # 观测到全部 mshr_* 节点 → L1d-Cache 不再有辅助独供节点，边界对该
    # 单元关闭（矩阵运行自证，优于辅助运行兜底）。
    if ev.exists():
        evidence = json.loads(ev.read_text(encoding="utf-8"))
        b = CM.aux_run_boundary(entries, evidence)
        check("boundary_l1d_closed_by_c11_matrix_run",
              "L1d-Cache" not in b, str(sorted(b)))
        # 关闭依据可审计：C11-F0-W6（矩阵 RunID 的 campaign 运行）的
        # pilot 观测含全部 mshr_* 必需节点；R4-3 的 6 载体与 R4-5.1 的
        # 3 载体仍在证据文件中留证。
        # [R6-MERGEFIX 2026-10-23] L17（b3321b6f）扫盘重生成 pilot_evidence.json
        # 后，pilot 键由裸 `<RunID>` 变为**逐 seed** `<RunID>-seed<N>`（dropped_
        # existing 明记 `C11-F0-W6` 被 `-seed1..3` 取代）。按裸键 `.get()` 取值一律
        # 落空——但证据并未缺失（C11-F0-W6-seed1 kinds 含全部 mshr_*）。改按工具
        # 单一真相源 `CM.runid_kinds`（裸键 ∪ 逐 seed 流，与 aux_run_boundary 同判据）
        # 聚合；要求仍是**该矩阵 RunID 自身**观测到生命周期节点（辅助载体不计入）。
        c11_kinds = CM.runid_kinds(evidence, "C11-F0-W6")
        mshr_nodes = {"mshr_alloc", "mshr_merge", "mshr_fill", "mshr_free"}
        check("c11_matrix_run_observes_mshr_lifecycle",
              mshr_nodes.issubset(c11_kinds), str(sorted(c11_kinds)))
        carriers = set(evidence["pilots"])
        check("boundary_carriers_retained_in_evidence",
              all(f"C09-R4T3-MSHRREF-s{i}" in carriers for i in range(1, 7))
              and all(f"C11-R4T5-MSHRREF-s{i}" in carriers
                      for i in range(1, 4)),
              str(sorted(c for c in carriers if "MSHRREF" in c)))
        # [R4-5.4 集成] 边界表**整体为空**：R4-5.4 落地 P06 后，数据预取器的
        # pf_queue/pf_issue 由矩阵 RunID P06-F0-W6/F6-W6/F6-W8 自身的 campaign
        # 运行直接观测到——最后一个"仅辅助运行可见"的单元也关闭了。这意味着
        # **每个 PASS 单元的必需节点都由该单元自己的矩阵运行自证**，无需辅助
        # 运行兜底，也就不再有需要标注的边界行。这是比"机制生效"更强的状态。
        check("boundary_empty_all_units_self_corroborated", b == {},
              str({u: v["nodes"] for u, v in b.items()}))
        # 关闭依据可审计：矩阵 RunID P01-F0-W8（**精确匹配**，非辅助）的 pilot
        # 观测到 pf_queue/pf_issue —— 数据预取器单元因此不再依赖辅助运行。
        # [R6-MERGEFIX 2026-10-23] 同 c11/c12：L17 后 P01-F0-W8 的 pilot 亦为逐
        # seed 键（P01-F0-W8-seed1..4），裸键落空。改用 runid_kinds 聚合自证。
        pref_kinds = CM.runid_kinds(evidence, "P01-F0-W8")
        check("prefetch_nodes_observed_by_matrix_run",
              {"pf_queue", "pf_issue"}.issubset(pref_kinds),
              str(sorted(pref_kinds & {"pf_queue", "pf_issue"})))
        # 机制本身仍须被钉死（活数据已干净 → 用**合成夹具**验证，否则回归网
        # 会在"数据恰好干净"时静默失效）：一个单元的必需节点只出现在
        # 非矩阵运行的 pilot 里时，必须被标出。
        synth_entries = [{"run_id": "ZZ1-F0-W1", "unit": "L1d-Cache"}]
        synth_ev = {"pilots": {
            "ZZ1-F0-W1": {"unit": "L1d-Cache", "kinds": ["cache_access"]},
            "ZZ1-SYNTHCARRIER-s1": {"unit": "L1d-Cache",
                                    "kinds": ["mshr_alloc"]},
            # 矩阵 RunID 的逐 seed 流 = 该矩阵运行本身，**不得**算辅助
            "ZZ1-F0-W1-seed2": {"unit": "L1d-Cache", "kinds": ["mshr_fill"]},
        }}
        sb = CM.aux_run_boundary(synth_entries, synth_ev)
        check("boundary_mechanism_flags_aux_only_node",
              sb.get("L1d-Cache", {}).get("nodes") == ["mshr_alloc"],
              str(sb.get("L1d-Cache", {}).get("nodes")))
        check("boundary_seed_stream_counts_as_matrix_run",
              sb.get("L1d-Cache", {}).get("aux_rids")
              == ["ZZ1-SYNTHCARRIER-s1"],
              str(sb.get("L1d-Cache", {}).get("aux_rids")))
        md = Path("/tmp/mdspec_coverage_test_ev.md").read_text(
            encoding="utf-8")
        # L1d 行不再标注 mshr（矩阵运行已自证）；C11 8 行全 PASS
        check("md_l1d_rows_not_annotated_mshr",
              "aux_run_nodes:mshr" not in md)
        c11_pass = [l for l in md.splitlines()
                    if l.startswith("| C11-") and "| PASS |" in l]
        check("md_c11_rows_all_pass", len(c11_pass) == 8, str(len(c11_pass)))
        # [MDSPEC][R4-5.2] C12 落地后的同构钉：矩阵运行（C12-F0-W6
        # campaign 3-seed 之 seed1）+ 3 载体（C12-R4T52-MSHRREF-*）均在
        # 证据文件中；6 行 C12 全 PASS；L1d 边界保持关闭（C11 已闭，C12
        # 载体的 16 kinds 不引入辅助独供节点）。
        c12_kinds = CM.runid_kinds(evidence, "C12-F0-W6")
        mshr_fill_nodes = {"mshr_fill", "mshr_free", "cache_fill"}
        check("c12_matrix_run_observes_delayed_fill_lifecycle",
              mshr_fill_nodes.issubset(c12_kinds), str(sorted(c12_kinds)))
        c12_carriers = set(evidence["pilots"])
        check("c12_carriers_retained_in_evidence",
              all(f"C12-R4T52-MSHRREF-s{i}" in c12_carriers
                  for i in range(1, 4)),
              str(sorted(c for c in c12_carriers if "R4T52" in c)))
        c12_pass = [l for l in md.splitlines()
                    if l.startswith("| C12-") and "| PASS |" in l]
        check("md_c12_rows_all_pass", len(c12_pass) == 6, str(len(c12_pass)))
        check("boundary_l1d_still_closed_after_c12",
              "L1d-Cache" not in b, str(sorted(b)))
        has_section = "## 辅助运行证据边界" in md
        check("md_boundary_section_present", has_section)
        tail = md.split("## 辅助运行证据边界", 1)[1] if has_section else ""
        # 边界为空 → 章节必须以**空集结论**显式出声（否则读者会把"没写"
        # 误读成"没查"），并指向判据来源（aux_run_boundary）。
        check("md_boundary_states_empty_conclusion",
              "**本表为空**" in tail and "aux_run_boundary" in tail,
              tail.strip()[:120])
        check("md_capability_table_has_aux_column",
              "仅辅助运行观测" in md)

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
