#!/usr/bin/env python3
"""[MDSPEC][B2] Markdown→实现覆盖矩阵（计划 Task B2）。

PASS/PARTIAL/BLOCKED 判定（Review Focus #1：部分已有≠PASS——PASS=0 起步，
每个 PASS 都要有钩子+字段双重证据）：
  BLOCKED: runid_map 的任一 status_reasons（campaign 裁罚 / spec 需新增 /
           workload 缺载体）
  PASS:    模型实现可用 AND 其全部钩子族已装（HOOK_REGISTRY）AND
           H0 字段 schema 齐备（fields_complete）
  PARTIAL: 其余（部分已有——注入/传播链存在但钩子族或字段不全）
钩子族可用性来自显式注册表（H1-H7 逐族在装好后翻转，防"部分监控冒充完整"）。
用法：python3 tools/lsu_coverage_matrix.py --map <runid_map.json> --out <md>
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_prop_fields as P  # noqa: E402  （发射端 kind 注册表 = 实现证据）

# ---------------------------------------------------------------------------
# 2026-10-20 证据化重构（用户第 3 点：不得因注册表布尔值为 true 就判整族完成）。
#
# 旧实现：HOOK_REGISTRY = 8 个布尔值 → 全 True ⇒ PASS。该口径被实证证伪：
# H4/H5/H6 当时有整族节点未实现（MSHR fill/free、pf_queue/fill/demand、
# exmon_rmw/retry）却被判 PASS。现口径**逐节点、双证据**：
#
#   PASS    = 该单元规格所需的**全部节点**（UNIT_REQUIRED_NODES）
#             (a) 已在发射端实现（kind ∈ lsu_prop_fields.KIND_LAYER）
#             (b) 已在**真实 pilot 运行**中实际出现（pilot_evidence.json，
#                 由 tools/lsu_pilot_evidence.py 从 prop_evt.txt.gz 生成）
#   PARTIAL = 其余（缺哪些节点逐项列出：missing_nodes / unobserved_nodes）
#   BLOCKED = runid_map 的 status_reasons（裁决/载体/许可证——外部阻塞）
#
# 证据文件缺省缺失时**不降级为 PASS**：所有非 BLOCKED 一律 PARTIAL
# （unobserved=全部节点），因为"没证据" ≠ "已实现"。
#
# 2026-10-21 辅助运行边界（R4-3 评审 Important-1）：PASS 的节点级证据取
# **全部 pilot 的 kind 并集**（节点=钩子能力级证据，与注入单元解耦）。
# 证据可来自**辅助运行**（RunID ≠ 矩阵 RunID 的真实 pilot：directed 载体 /
# campaign smoke 复跑）——但必须显式标出（aux_run_boundary：逐单元列出
# 仅辅助运行观测到的必需节点 + 提供/未观测到它们的 RunID），否则 PASS 行
# 会被误读为"该矩阵单元自身的 campaign 运行观测到了全部节点"。逐单元归属
# 索引见 pilot_evidence.json 的 kinds_observed_by_unit（RunID→单元解析：
# 精确匹配 → 行标签，见 tools/lsu_pilot_evidence.py unit_of）。
UNIT_REQUIRED_NODES = {
    # AGU/LSQ 全链（表 9 A01：inj→L1 EA 入 LSQRequest→L2 dTLB→L3 LQ/SQ+访问
    # L1D→L4 PRF/消费者/提交→L5 终局）
    "AGU": ["inj", "addr_form", "lsq_push", "lsq_sendfrag", "tlb_translate",
            "mem_req", "resp", "taint_reg", "consumer", "errant_commit",
            "chain_end"],
    # 翻译单元（表 9 T01-T04：translate/walk/refill + fault）
    "L1d-TLB": ["inj", "lsq_sendfrag", "tlb_translate", "tlb_fault",
                "mem_req", "chain_end"],
    "Load Queue": ["inj", "lsq_push", "lq_read", "lq_complete", "resp",
                   "taint_reg", "chain_end"],
    "Store Queue": ["inj", "lsq_push", "lsq_sendfrag", "sq_execute",
                    "sq_writeback", "sq_complete", "chain_end"],
    # cache（表 9 C01：lookup→hit返回/miss→MSHR allocate/merge/fill/free→
    # victim/writeback→response）
    "L1d-Cache": ["inj", "cache_access", "cache_return", "mshr_alloc",
                  "mshr_merge", "mshr_fill", "mshr_free", "cache_fill",
                  "cache_evict", "cache_writeback", "chain_end"],
    # prefetch（表 9 P01：训练→队列→请求→fill→后续 demand）
    "数据预取器": ["inj", "pf_train", "pf_queue", "pf_issue", "pf_fill",
                   "pf_demand", "chain_end"],
    # atomic/exmon（表 9 O01：monitor→保留比较→STXR 消费/重试）
    "原子与同步": ["inj", "exmon_monitor", "exmon_rmw", "exmon_stxr",
                   "atomic_op", "chain_end"],
}


def load_evidence(path):
    """pilot_evidence.json → {kind: seen_bool} ∪ 原始结构。

    结构（tools/lsu_pilot_evidence.py 产出）：
      {"pilots": {run_id: {"unit":…, "kinds": [...], "events": n}},
       "kinds_observed": [...]}
    """
    if path is None or not Path(path).exists():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def assess(entry, evidence):
    if entry["status"] == "BLOCKED":
        return "BLOCKED", entry["status_reasons"]
    required = UNIT_REQUIRED_NODES.get(entry["unit"], [])
    if not required:
        return "PARTIAL", [f"unit_has_no_required_node_set:{entry['unit']}"]
    # (a) 发射端实现证据
    missing_impl = [k for k in required if k not in P.KIND_LAYER]
    # (b) 真实运行证据（无证据文件 = 全未观测，绝不当 PASS）
    observed = set(evidence.get("kinds_observed", [])) if evidence else set()
    unobserved = [k for k in required if k not in observed]
    if not missing_impl and not unobserved:
        return "PASS", []
    why = []
    if missing_impl:
        why.append(f"missing_nodes:{','.join(missing_impl)}")
    if unobserved:
        why.append(f"unobserved_nodes:{','.join(unobserved)}")
    return "PARTIAL", why


def aux_run_boundary(entries, evidence):
    """逐单元计算"仅在辅助运行中观测到的必需节点"（R4-3 评审边界要求）。

    辅助运行 = 证据文件里 RunID ≠ 矩阵 RunID 的真实 pilot（directed 载体、
    campaign smoke 复跑、机理变体——**不是**矩阵单元自身的运行）。PASS 的
    节点级证据允许来自辅助运行（节点=钩子能力证据，判据取全部 pilot 的
    kind 并集），但必须显式标出——否则矩阵 PASS 行会被误读为"该单元的
    campaign 运行自己观测到了全部节点"。

    返回 {unit: {"nodes": [...], "aux_rids": [...], "matrix_rids": [...]}}：
      nodes       必需节点中，辅助运行观测到、而该单元全部矩阵 RunID 运行
                  均未观测到的节点（aux-only 定义保证后者；按
                  UNIT_REQUIRED_NODES 顺序）；
      aux_rids    提供上述节点的辅助运行 RunID；
      matrix_rids 该单元在证据文件中的全部矩阵 RunID 运行（均未观测到
                  上述节点）。
    无证据文件 / 旧格式（无 pilots）→ {}。
    """
    if not evidence or "pilots" not in evidence:
        return {}
    matrix_rids = {e["run_id"] for e in entries}
    per_unit = {}
    for rid, p in evidence["pilots"].items():
        unit = p.get("unit")
        if not unit:
            continue
        d = per_unit.setdefault(unit, {"matrix_kinds": set(), "aux": {}})
        if rid in matrix_rids:
            d["matrix_kinds"].update(p.get("kinds", []))
        else:
            d["aux"][rid] = set(p.get("kinds", []))
    out = {}
    for unit, d in per_unit.items():
        req = UNIT_REQUIRED_NODES.get(unit, [])
        aux_kinds = (set().union(*d["aux"].values()) if d["aux"] else set())
        nodes = [k for k in req
                 if k in aux_kinds and k not in d["matrix_kinds"]]
        if not nodes:
            continue
        node_set = set(nodes)
        out[unit] = {
            "nodes": nodes,
            "aux_rids": sorted(r for r, ks in d["aux"].items() if ks & node_set),
            "matrix_rids": sorted(
                r for r, p in evidence["pilots"].items()
                if r in matrix_rids and p.get("unit") == unit),
        }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--map", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--evidence", default=None,
                    help="pilot_evidence.json（真实运行观测证据；缺省=无证据，"
                         "非 BLOCKED 一律 PARTIAL）")
    a = ap.parse_args()
    m = json.loads(Path(a.map).read_text(encoding="utf-8"))
    evidence = load_evidence(a.evidence)
    boundary = aux_run_boundary(m["entries"], evidence)
    rows = []
    for e in m["entries"]:
        st, why = assess(e, evidence)
        # 辅助运行边界标注（R4-3 评审）：PASS 所依据的节点证据里，哪些
        # 必需节点**仅**由非矩阵 RunID 的辅助运行（directed 载体等）提供。
        if st == "PASS" and e["unit"] in boundary:
            why = why + [f"aux_run_nodes:{','.join(boundary[e['unit']]['nodes'])}"]
        rows.append((e["run_id"], e["model_id"], e["unit"], e["freq"], st,
                     "; ".join(why)))
    cnt = Counter(r[4] for r in rows)
    obs = sorted(evidence.get("kinds_observed", [])) if evidence else []
    lines = ["# Markdown→实现覆盖矩阵（MDSPEC Phase B，**节点级证据化**）", "",
             f"- 总数：{len(rows)}（RunID 唯一，表7∩表9 集合相等——B1 已证）",
             f"- **PASS={cnt.get('PASS', 0)} / PARTIAL={cnt.get('PARTIAL', 0)} / "
             f"BLOCKED={cnt.get('BLOCKED', 0)}**",
             "- 判定口径（2026-10-20 证据化）：PASS = 该单元规格所需**全部节点**"
             "既已实现（kind ∈ 发射端注册表）**又**在真实 pilot 运行中出现；"
             "缺任一节点 = PARTIAL 并逐项列出。注册表布尔值**不再**作为判据。",
             "- 节点级证据取**全部 pilot 的 kind 并集**（节点=钩子能力级证据，"
             "与注入单元解耦）；逐单元归属索引见 pilot_evidence.json 的 "
             "kinds_observed_by_unit（RunID→单元解析：精确匹配 → 行标签，"
             "见 tools/lsu_pilot_evidence.py unit_of）。"]
    if boundary:
        lines.append(
            "- **辅助运行证据边界**：下表所列单元的部分必需节点仅在**非矩阵"
            " RunID 的辅助运行**（directed 载体 / campaign smoke 复跑，**非**"
            "该矩阵单元自身的运行）中观测到——矩阵单元自身的运行（含 campaign "
            "单元）未观测到这些节点；PASS 行已逐行标注 `aux_run_nodes:`，"
            "详见文末\"辅助运行证据边界\"表。")
    lines += [
        f"- 真实运行观测到的 kind（{len(obs)}）：{', '.join(obs) or '（无证据文件）'}",
        "",
        "| RunID | 模型 | 单元 | 频率 | 状态 | 原因 |", "|---|---|---|---|---|---|"]
    lines += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5][:160]} |"
              for r in rows]

    # 单元级节点能力（与 RunID 阻塞无关）：即使某单元的全部 RunID 因外部
    # 原因 BLOCKED，其钩子能力仍应可见——否则"H6 已验证"会被 126 BLOCKED
    # 淹没（用户第 3/5 点：能力与裁决要分开陈述）。
    lines += ["", "## 单元级节点能力（与 RunID 阻塞解耦）", "",
              "| 单元 | 需要节点 | 已实现 | 真实运行已观测 | 仍缺 | "
              "仅辅助运行观测 |",
              "|---|---|---|---|---|---|"]
    observed_set = set(obs)
    for unit in sorted(UNIT_REQUIRED_NODES):
        req = UNIT_REQUIRED_NODES[unit]
        impl = [k for k in req if k in P.KIND_LAYER]
        miss = [k for k in req if k not in P.KIND_LAYER]
        obs_u = [k for k in req if k in observed_set]
        unobs = [k for k in req if k not in observed_set]
        aux_nodes = boundary.get(unit, {}).get("nodes", [])
        lines.append(
            f"| {unit} | {len(req)} | {len(impl)} | "
            f"{len(obs_u)}/{len(req)} | "
            f"{('impl:' + ','.join(miss) + ' ') if miss else ''}"
            f"{('unobserved:' + ','.join(unobs)) if unobs else ''} | "
            f"{(', '.join(aux_nodes)) if aux_nodes else '—'} |")

    # 辅助运行证据边界表（R4-3 评审 Important-1）：把"决定 PASS 的节点证据
    # 来自哪些运行"逐单元摊开——辅助运行 RunID 与该单元的矩阵 RunID 运行
    # （后者均未观测到这些节点）并排列出，边界不可误读。
    if boundary:
        lines += ["", "## 辅助运行证据边界（矩阵单元自身运行 vs 辅助运行）", "",
                  "PASS 的节点级证据允许来自辅助运行（RunID ≠ 矩阵 RunID 的"
                  "真实 pilot：directed 载体 / campaign smoke 复跑 / 机理变体）。"
                  "下表逐单元列出**仅在辅助运行中观测到**的必需节点；最后一列"
                  "是该单元在证据文件中的全部矩阵 RunID 运行——它们**均未**"
                  "观测到这些节点（含 campaign 单元自身的运行）：", "",
                  "| 单元 | 仅辅助运行观测的必需节点 | 辅助运行 RunID | "
                  "矩阵 RunID 运行（均未观测到） |",
                  "|---|---|---|---|"]
        for unit in sorted(boundary):
            b = boundary[unit]
            lines.append(f"| {unit} | {', '.join(b['nodes'])} | "
                         f"{', '.join(b['aux_rids'])} | "
                         f"{', '.join(b['matrix_rids'])} |")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[coverage] PASS={cnt.get('PASS', 0)} PARTIAL={cnt.get('PARTIAL', 0)} "
          f"BLOCKED={cnt.get('BLOCKED', 0)} → {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
