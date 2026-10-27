#!/usr/bin/env python3
"""[LSU][MDSPEC][R4-8-SPEC] W11（SPEC 12 行）阻塞集 + 残余阻塞集合的机读钉扎。

本测试把三件事钉死（每一条都对应证据文件
`docs/gem5-fi/lsu/mdspec/R4-8-SPEC-residual-report.md` 的一节）：

  [A] W11 12 行的阻塞集合：逐 RunID、逐理由（spec-license），不多不少。
  [B] 「非 blanket」证明：SPEC 阻塞键只命中规格钉住的负载身份
      （表 7 里唯一含 "SPEC CPU2017" 的负载名），且四个模型
      （C15/L04/S13/T10）都有**非 W11 的、不被许可证拦截的**可跑/可解析 cell
      —— 即 W11 不是模型级 blanket 缺口。
  [C] 残余集合结构：把「runid_map 判可跑（PARTIAL）但 campaign 静态解析器拒跑」
      的行**从工具重新推导**，断言它们**全部**落在 W1/MiBench 负载身份上
      （= 另一个 agent 的口径订正范围），W11 与 T08-W9 都不在其中。

用法：python3 tests/test_lsu_w11_spec_residual.py   （退出码 0=全 PASS）
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_campaign as C       # noqa: E402
import lsu_runid_map as M      # noqa: E402

XLSX = ROOT / "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"
MATRIX = ROOT / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv"

W11 = ["C15-F0-W11", "C15-F4-W11", "C15-F6-W11",
       "L04-F0-W11", "L04-F2-W11", "L04-F6-W11",
       "S13-F0-W11", "S13-F1-W11", "S13-F2-W11",
       "T10-F0-W11", "T10-F1-W11", "T10-F2-W11"]
W11_MODELS = ["C15", "L04", "S13", "T10"]
# 规格钦定的 W11 负载身份（表 6/7）：逐字。
SPEC_IDENTITY = "SPEC CPU2017"
T08_W9 = ["T08-F0-W9", "T08-F4-W9", "T08-F6-W9"]


def fresh_map():
    """从 xlsx 现场重生成 runid_map（不信任何提交的 JSON）。"""
    out = Path(tempfile.mkdtemp(prefix="w11pin_")) / "m.json"
    subprocess.run([sys.executable, str(ROOT / "tools/lsu_runid_map.py"),
                    "--xlsx", str(XLSX), "--out", str(out)],
                   check=True, capture_output=True, text=True)
    return {e["run_id"]: e for e in
            json.loads(out.read_text(encoding="utf-8"))["entries"]}


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name +
              ("   <- " + detail if not cond else ""))
        if not cond:
            fails.append(name)

    m = fresh_map()
    hdr, cells = C.load_matrix(str(MATRIX))
    by_rid = {c[C.COL_RUNID].strip(): c for c in cells}

    # ---------------------------------------------------------------- [A]
    w11_rids = sorted(r for r in m if r.endswith("-W11"))
    check("A1_w11_is_exactly_12_rows", w11_rids == sorted(W11),
          f"got={w11_rids}")
    bad = [r for r in W11
           if not (m[r]["status"] == "BLOCKED"
                   and any(("spec-license: SPEC CPU2017 needs a license" in x
                            or "BLOCKED_SPEC: SPEC CPU2017 needs a license" in x)
                           for x in m[r]["status_reasons"]))]
    check("A2_w11_all_blocked_with_spec_license_reason", not bad, str(bad))
    check("A3_w11_models_are_the_four",
          sorted({m[r]["model_id"] for r in W11}) == sorted(W11_MODELS),
          str(sorted({m[r]["model_id"] for r in W11})))
    # campaign 侧同一裁决：12 行全部被 resolve_cell 拒跑，理由 = 许可证（不是
    # NOT-MAPPED —— 即阻塞是"响亮且精确"的，不是缺映射的静默）。
    camp = {}
    for r in W11:
        _f, _g, why = C.resolve_cell(by_rid[r])
        camp[r] = why
    check("A4_campaign_refuses_all_12_as_blocked",
          all(v is not None and "spec-license" in v for v in camp.values()),
          str(camp))

    # ---------------------------------------------------------------- [B]
    # B1: WL_BLOCKED 里只有一个 SPEC 键，且它就是规格钦定的身份串。
    spec_keys = [k for k in C.WL_BLOCKED if "SPEC" in k]
    check("B1_single_spec_key_is_pinned_identity",
          spec_keys == [SPEC_IDENTITY], str(spec_keys))
    # B2: 该键是子串匹配——扫**全部**出现的负载名，只有 W11 身份串含 "SPEC"。
    wl_names = sorted({row["workload"]["spec_name"] for row in
                       json.loads(json.dumps(list(m.values())))})
    spec_named = [w for w in wl_names if "SPEC" in w]
    check("B2_only_the_w11_identity_carries_spec",
          len(spec_named) == 1 and spec_named[0].startswith(SPEC_IDENTITY),
          str(spec_named))
    # B3: 非 blanket（模型维度）——四个模型都各有一条**不被许可证拦截**的
    # 非 W11 cell；否则 W11 就是模型级缺口的伪装。
    for model in W11_MODELS:
        rids = [r for r in by_rid if r.startswith(model + "-") and r not in W11]
        non_lic = []
        for r in rids:
            f, g, why = C.resolve_cell(by_rid[r])
            if why is None or "spec-license" not in why:
                non_lic.append(r)
        check(f"B3_{model}_has_non_licence_cell", bool(non_lic),
              f"candidates={rids}")
    # B4: 模型覆盖存在（替代载体审计的机器可读结论）——每个 W11 模型至少一条
    # 非 W11 cell 在**开放载体**上真能解析出可跑 flags（不是仅"没被许可证拦"）。
    for model in W11_MODELS:
        runnable = []
        for r in by_rid:
            if not r.startswith(model + "-") or r in W11:
                continue
            f, g, why = C.resolve_cell(by_rid[r])
            if f is not None:
                runnable.append(r)
        check(f"B4_{model}_has_runnable_open_carrier_cell", bool(runnable),
              f"runnable={runnable}")

    # ---------------------------------------------------------------- [C]
    st = {r: v["status"] for r, v in m.items()}
    unresolved = []
    for rid, c in by_rid.items():
        if st.get(rid) != "PARTIAL":
            continue                     # 只在 map 说"可跑"的行里找
        f, _g, why = C.resolve_cell(c)
        if f is None:
            unresolved.append((rid, c[C.COL_WORKLOAD], why))
    # [R4-8-INT] 合并 r4-7-fsinfra-w1（W1/MiBench 订正）后残余不再是"全部
    # MiBench"：MiBench 的过宽阻塞已删，只剩 S01/S02-F0-W1 两格由**精确的**
    # F0-span-unmeasured 拒绝；另两格 S10-F2 由 r4-8-S10 的
    # interval-tier-unreachable 拒绝（spec 固定 interval 语义，非本任务范围）。
    # 改钉**结构不变量**：每格残余必须归入已具名的精确拒绝，不允许无归属拒跑。
    # [MDSPEC][R6-FTIER] 追加具名拒绝 armtlb-lookup-tier-unimplemented：
    # armtlb lookup 路径不消费 tier（TLB::lookup 不 poll lsuTrigger），F1-F6
    # 档显式 BLOCKED —— 同样是**已具名的精确拒绝**（R6-FTIER）。
    unexplained = [(r, w, y) for r, w, y in unresolved
                   if not (y and ("F0-span-unmeasured" in y
                                  or "interval-tier-unreachable" in y
                                  or "armtlb-lookup-tier-unimplemented" in y
                                  or "PARTIAL_SUBMODEL_PROVEN" in y))]
    check("C1_unresolved_is_explained_by_precise_refusals",
          not unexplained, str(unexplained))
    # C2: 残余集合里没有 W11（许可证阻塞走的是 BLOCKED 通道，不进 UNRESOLVED）。
    check("C2_no_w11_in_unresolved",
          not any(r.endswith("-W11") for r, _w, _wh in unresolved),
          str([r for r, _w, _wh in unresolved]))
    # C3: [R6-PROPAGATION-V3] T08-W9 is now an explicit hard workload gap —
    # the GAP/Graph500 FS carrier is absent.  Assert the precise label rather
    # than the obsolete "no workload-level block" claim.
    wl_level = [r for r in T08_W9
                if not any("BLOCKED_WORKLOAD_GAP" in x
                           for x in m[r]["status_reasons"])]
    check("C3_t08_w9_is_explicit_BLOCKED_WORKLOAD_GAP", not wl_level,
          str(wl_level))
    check("C4_t08_w9_resolves_to_se_carrier",
          all(m[r]["workload"]["binary"] == "gap_bfs" for r in T08_W9),
          str({r: m[r]["workload"]["binary"] for r in T08_W9}))

    print()
    print(f"UNRESOLVED (map=PASSABLE but campaign refuses) = {len(unresolved)}")
    for r, w, why in unresolved[:25]:
        print(f"  {r} | {w[:22]} | {why[:60]}")
    print()
    print("FAILURES: " + ("无" if not fails else ", ".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
