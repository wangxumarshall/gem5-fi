#!/usr/bin/env python3
"""test_lsu_runid_map.py — [MDSPEC][B1] RunID 机读映射生成器（用户三.1）。

规格→CLI→注入点→监控钩子→结果字段 的可机读映射：325 条、唯一、表7∩表9
集合相等、A06-* 6 条 BLOCKED（§2 裁决）、无 A06S-*、负载映射不猜
（WL_BINARY 前缀匹配 + 实存校验；未映射→binary:null+注记+BLOCKED）。
用法：python3 tests/test_lsu_runid_map.py   （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_runid_map as M   # noqa: E402

XLSX = ROOT / "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"
REQUIRED_KEYS = {"run_id", "model_id", "unit", "freq", "fault_type", "submodels",
                 "trigger", "workload", "path_nodes", "monitors",
                 "correlation_keys", "termination", "missing_hooks",
                 "existing_coverage", "status", "status_reasons",
                 "target_activated_samples"}


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name + ("   <- " + detail if not cond else ""))
        if not cond:
            fails.append(name)

    m = M.generate_map(XLSX)
    entries = m["entries"]
    ids = [e["run_id"] for e in entries]

    check("map_has_325_entries", len(entries) == 325, f"n={len(entries)}")
    check("runids_unique", len(set(ids)) == 325, f"unique={len(set(ids))}")
    check("all_keys_present",
          all(REQUIRED_KEYS <= set(e.keys()) for e in entries),
          str(sorted(REQUIRED_KEYS - set(entries[0].keys()))))
    a06 = [e for e in entries if e["model_id"] == "A06"]
    check("a06_six_entries_all_blocked",
          len(a06) == 6 and all(e["status"] == "BLOCKED" for e in a06),
          f"n={len(a06)} statuses={[e['status'] for e in a06]}")
    check("a06_blocked_reason_from_ruling",
          all(any("load" in r.lower() for r in e["status_reasons"]) for e in a06),
          str(a06[0]["status_reasons"]) if a06 else "")
    check("no_a06s_runid", not any(i.startswith("A06S") for i in ids))
    # 规格实证：49 条路径 L5 后继续回 L1（squash→replay 反馈边，如
    # L0>L1>L2>L3>L4>L5>L1）——断言"起点 L0 且途经 L5"，不要求以 L5 结尾。
    check("path_nodes_start_l0_pass_l5",
          all(e["path_nodes"] and e["path_nodes"][0] == "L0"
              and "L5" in e["path_nodes"] for e in entries),
          f"first={entries[0]['run_id']} nodes={entries[0]['path_nodes']}")
    known_wl = [e for e in entries if e["workload"]["binary"]]
    check("known_workloads_resolve_to_existing_binary",
          len(known_wl) >= 150 and all(
              (ROOT / "workloads" / "directed" / e["workload"]["binary"]).exists()
              or (ROOT / "workloads" / e["workload"]["binary"]).exists()
              for e in known_wl),
          f"n_known={len(known_wl)}")   # 非空性下限：防 vacuous-pass（B1 缺陷教训）
    check("agu_addrmodes_resolved",
          any(e["workload"]["binary"] == "agu_addrmodes" for e in entries))
    unknown_wl = [e for e in entries if not e["workload"]["binary"]]
    check("unknown_workloads_marked_not_guessed",
          all(e["workload"]["note"] and e["status"] == "BLOCKED"
              for e in unknown_wl),
          f"n_unknown={len(unknown_wl)} "
          f"names={sorted({e['workload']['spec_name'][:20] for e in unknown_wl})}")
    check("mibench_prefixed_match_resolved",
          any(e["workload"]["spec_name"].startswith("MiBench")
              and e["workload"]["binary"] for e in entries))

    # [MDSPEC][R4-8-W1] 口径一致性（R4-6.0 §0.5 记录的 19 行冲突的机械封口）：
    # runid_map 视为"有载体可跑"的行，campaign 的 resolve_cell **不得**再以
    # 负载级（WL_BLOCKED）理由拒跑。逐行核验——任何一行重新落回负载级拒跑
    # 都会 fail（无声回退 = bug）。
    import lsu_campaign as lc   # noqa: E402  (唯一阻塞真相来源)

    def _cell(e):
        c = [""] * 10
        c[lc.COL_RUNID] = e["run_id"]
        c[lc.COL_MODEL] = e["model_id"]
        c[lc.COL_FREQ] = e["freq"]
        c[lc.COL_WORKLOAD] = e["workload"]["spec_name"]
        return c

    # 冲突口径 = 非 FS-family（非 armtlb）的 W1 行：27 - 8 个 T 模型 = 19。
    # T 模型的 W1 行走 FS 载体（其 golden 是 TLB probe 的，不是 MiBench 的），
    # 不属于"口径冲突"集合，单独断言它们仍走 FS。
    _w1_all = [e for e in entries if e["run_id"].endswith("-W1")
               and e["workload"]["binary"]]
    check("w1_rows_total_is_27", len(_w1_all) == 27, f"n={len(_w1_all)}")
    t_rows = [e for e in _w1_all if e["model_id"] in lc.ARMTLB_MODELS]
    # [MDSPEC][R6-FTIER] F0 rows still resolve to the armtlb FS flag set
    # (TLB-probe golden); F!=F0 lookup rows are now honestly BLOCKED by the
    # tier gate. The invariant here is "neither may route to the MiBench SE
    # carrier". See tests/test_lsu_ftier_armtlb_lookup.py.
    _tr = {e["run_id"]: lc.resolve_cell(_cell(e)) for e in t_rows}
    check("T-model W1 rows (8) never route to the MiBench SE carrier",
          len(t_rows) == 8 and all(
              f is None or "--cmd" not in f for f, _g, _k in _tr.values()),
          str([e["run_id"] for e in t_rows]))
    # [MDSPEC][R6-FTOOLS 2026-10-24] 策略已由 FTIER 的
    # ARMTLB_LOOKUP_TIERS={F0} 变更为 {F0..F6}（用户裁决）：F!=F0 的 lookup
    # 行不再 BLOCKED，而是携带真实 --tlb_lsu_tier。本处期望同步指向**当前**
    # 口径 —— 断言只增强（新增 tier 值一致性），未删除、未弱化。
    def _tiers(_flags):
        """flags 是 list；拼回字符串后抽取 tier 值（不是列表成员判断）。"""
        import re as _re
        return _re.findall(r"--tlb_lsu_tier\s+(\S+)", " ".join(_flags or []))

    _f0 = {r: v for r, v in _tr.items() if r.endswith("F0-W1")}
    _fnf = {r: v for r, v in _tr.items() if not r.endswith("F0-W1")}
    check("T-model W1 F0 rows (3): resolved, TLB-probe golden, "
          "no --tlb_lsu_tier, never MiBench SE",
          len(_f0) == 3
          and all(f is not None and g == lc.TLB_PROBE_GOLDEN
                  and _tiers(f) == [] and "--cmd" not in f
                  for f, g, _k in _f0.values()),
          str({r: f for r, (f, _g, _k) in _f0.items()}))
    check("T-model W1 F!=F0 rows (5): resolved, TLB-probe golden, exactly one "
          "--tlb_lsu_tier equal to the row's F tier, never MiBench SE",
          len(_fnf) == 5
          and all(f is not None and g == lc.TLB_PROBE_GOLDEN
                  and "--cmd" not in f
                  and _tiers(f) == [r.split("-")[1]]
                  for r, (f, g, _k) in _fnf.items()),
          str({r: (_tiers(f), r.split("-")[1])
               for r, (f, _g, _k) in _fnf.items()}))
    w1 = [e for e in _w1_all if e["model_id"] not in lc.ARMTLB_MODELS]
    check("w1_audit_scope_is_19_rows", len(w1) == 19, f"n={len(w1)}")
    wl_blocked_rows, runnable, span_rows, other = [], [], [], []
    for e in w1:
        flags, _g, kind = lc.resolve_cell(_cell(e))
        if flags is not None:
            runnable.append(e["run_id"])
        elif "TLB workload needs FS" in kind or "has no" in kind \
                or "multicore-fs" in kind or "license" in kind:
            wl_blocked_rows.append((e["run_id"], kind))
        elif "F0-span-unmeasured" in kind:
            span_rows.append(e["run_id"])
        else:
            other.append((e["run_id"], kind))
    check("no W1 row is workload-blocked in campaign while runid_map says "
          "runnable (the R4-8 fix)",
          not wl_blocked_rows, str(wl_blocked_rows))
    check("17 W1 rows resolve runnable; the 2 F0 rows are blocked by the "
          "PRECISE per-(model,workload) F0-span census gate",
          len(runnable) == 17 and sorted(span_rows) == ["S01-F0-W1",
                                                        "S02-F0-W1"]
          and not other,
          f"runnable={len(runnable)} span={sorted(span_rows)} other={other}")
    check("the over-broad 'MiBench' workload block is gone; the four precise "
          "blockers remain",
          # [R4-8-INT] SPEC 键已收窄为 SPEC_WL_IDENTITY（见 r4-8-spec-residual）。
          set(lc.WL_BLOCKED) == {"TLB-AliasPerm", "Atomic-Litmus", "PARSEC",
                                 lc.SPEC_WL_IDENTITY},
          str(sorted(lc.WL_BLOCKED)))
    # [LSU][MDSPEC][R6-FSINFRA] FS-family workload key correction (R5 §8).
    # The fabricated, model-agnostic key
    #   workload:workload-level:blocked(fs-infra: TLB workload needs FS)
    # is REFUTED by real FS runs on disk (R5-FS-PILOT-EVIDENCE.md: T01/T04-F0-W4
    # activated on the FS carrier; the T08 containment chain). It is a stale
    # *workload-level* claim emitted by _resolve_workload, which is blind to
    # resolve_cell's armtlb FS special-case. Per row the key must be rewritten
    # to name (i) the refutation, (ii) the refuting artifact, and (iii) the TRUE
    # residual blocker -- and NOTHING may be mass-cleared: all 24 rows stay
    # BLOCKED because no cell yet meets the documented unlock condition
    # (30 activated/cell, blockers_for_approval.md §FS-INFRA).
    fs_rows = [e for e in entries
               if e["model_id"] in lc.ARMTLB_MODELS
               and "TLB-AliasPerm" in e["workload"]["spec_name"]
               and "fs-infra" in " ".join(e["status_reasons"])]
    fs_ids = sorted(e["run_id"] for e in fs_rows)
    check("fs-infra family is exactly the 24 TLB-AliasPerm rows",
          len(fs_rows) == 24, f"n={len(fs_rows)} {fs_ids}")
    STALE = "blocked(fs-infra: TLB workload needs FS)"
    bad = [e["run_id"] for e in fs_rows
           if STALE in " ".join(e["status_reasons"])]
    check("the stale fabricated claim is gone from every fs-infra row",
          not bad, str(bad))
    check("no fs-infra row was mass-cleared (24/24 stay BLOCKED)",
          all(e["status"] == "BLOCKED" for e in fs_rows),
          str([(e["run_id"], e["status"]) for e in fs_rows
               if e["status"] != "BLOCKED"]))
    check("every corrected key names the refutation + the FS carrier",
          all(any(r.startswith("workload:fs-infra: refuted(")
                  and lc.TLB_PROBE_GOLDEN in r for r in e["status_reasons"])
              for e in fs_rows),
          str([e["run_id"] for e in fs_rows
               if not any(r.startswith("workload:fs-infra: refuted(")
                          for r in e["status_reasons"])]))
    check("every corrected key names the TRUE residual blocker (pilot, "
          "not the stale FS claim)",
          all(any("residual blocker:" in r for r in e["status_reasons"])
              for e in fs_rows),
          str([e["run_id"] for e in fs_rows
               if not any("residual blocker:" in r
                          for r in e["status_reasons"])]))
    # Per-row evidence: exactly the rows with a real FS pilot artifact carry a
    # path into the committed evidence manifest; the rest say so loudly.
    MANIFEST = "docs/gem5-fi/lsu/mdspec/R6-FSINFRA-EVIDENCE.md"
    ev_rows = [e for e in fs_rows if e.get("fs_workload", {}).get("evidence")]
    no_ev = [e["run_id"] for e in fs_rows
             if not e.get("fs_workload", {}).get("evidence")]
    check("evidence manifest exists (durable, committed)",
          (ROOT / MANIFEST).exists(), MANIFEST)
    check("evidence-covered FS rows record a manifest anchor",
          len(ev_rows) == 16 and all(
              e["fs_workload"]["evidence"].startswith(MANIFEST + "#")
              and e["fs_workload"]["run_artifact"]
              for e in ev_rows),
          f"n_ev={len(ev_rows)}")
    check("rows with no per-cell FS pilot say so (no silent claim)",
          sorted(no_ev) == ["T05-F2-W4", "T05-F6-W4", "T06-F2-W4",
                            "T06-F6-W4", "T07-F4-W4", "T07-F6-W4",
                            "T08-F4-W4", "T08-F6-W4"],
          str(sorted(no_ev)))
    check("every evidenced row is named in the manifest section it cites",
          all(e["run_id"] in (ROOT / MANIFEST).read_text()
              for e in ev_rows),
          str([e["run_id"] for e in ev_rows
               if e["run_id"] not in (ROOT / MANIFEST).read_text()]))

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
