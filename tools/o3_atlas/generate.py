# tools/o3_atlas/generate.py
"""Deterministic renderer: docs/cpu/o3-atlas/data/*.yaml → pages/ + index/.

No timestamps, no dict-order dependence, sorted iteration everywhere:
running twice must be byte-identical (validate.py enforces it).
"""
import argparse
import shutil
import subprocess
from pathlib import Path

from .corpus import REPO, category_of, instruction_pages
from .schema import INJECTORS
from .validate import load_data

ATLAS = REPO / "docs/cpu/o3-atlas"
PAGES = ATLAS / "pages"
INDEX = ATLAS / "index"
DIAGRAMS = ATLAS / "diagrams"

# 总图 = 全部 implemented 指令链路的并集（数据推导）+ 单元富化 + 注入器叠加
# 注入器 → 挂载站点（依据计划「关键事实 §7」挂载语义表，锚点在 families.yaml）
INJECTOR_MOUNTS = {
    "CHAOSDecode": "DECODE", "CHAOSRenameMap": "RENAME", "CHAOSFreeList": "RENAME",
    "CHAOSPhysReg": "EXECUTE", "CHAOSIQ": "ISSUE", "CHAOSROB": "COMMIT",
    "CHAOSReg": "COMMIT", "CHAOSExec": "EXECUTE", "CHAOSFPU": "EXECUTE",
    "CHAOSLSQFwd": "MEMORY", "CHAOSL1DForward": "MEMORY", "CHAOSAddrPath": "MEMORY",
    "CHAOSBPU": "BPU", "CHAOSRAS": "COMMIT", "CHAOSExMon": "MEMORY",
    "CHAOSProbe": "COMMIT", "CHAOSCommitTrace": "COMMIT",
    "CHAOSMem": "MEMORY", "CHAOSCache": "MEMORY",
}
_MEM_FUS = ("MemReadOp", "MemWriteOp")  # 访存侧 opClass（挂 LSQ→MEMORY），其余为执行单元


def build_union_graph(families, instructions):
    """对全部 implemented 指令的家族 pipeline 求并集。

    返回 (nodes, edges, fus, queues, node_anchor)：
    - nodes/edges：家族链路的节点与相邻边并集（如 ALU 的 EXECUTE→WRITEBACK 与
      load 的 EXECUTE→MEMORY 在并集中并存，形成真实的分岔拓扑）
    - fus/queues：记录级 FU（overrides 优先）与家族 queue 的并集
    - node_anchor：站点 → families.yaml 的代码锚点
    """
    pref = ["BPU", "FTQ", "FETCH", "DECODE", "RENAME", "DISPATCH",
            "ISSUE", "EXECUTE", "MEMORY", "WRITEBACK", "COMMIT", "REDIRECT"]
    edges, nodes_seen, fus, queues, node_anchor = set(), set(), set(), set(), {}
    for r in instructions:
        if r.get("tier") == "unimplemented":
            continue
        fam = families.get(r.get("family"))
        if not fam:
            continue
        pipe = fam["pipeline"]
        for i, n in enumerate(pipe):
            nodes_seen.add(n)
            if i:
                edges.add((pipe[i - 1], n))
        for n, a in (fam.get("anchors") or {}).items():
            node_anchor.setdefault(n, a)
        fu = (r.get("overrides") or {}).get("fu") or fam.get("fu")
        if fu:
            fus.add(fu)
        if fam.get("queue"):
            queues.add(fam["queue"])
    nodes = [n for n in pref if n in nodes_seen] + sorted(nodes_seen - set(pref))
    return nodes, edges, fus, queues, node_anchor


def _node_label(n, anchors):
    a = anchors.get(n)
    return f"{n} · {a.rsplit('/', 1)[-1]}" if a else n


def render_master_mermaid(families=None, instructions=None):
    """O3 全流水线总图（mermaid）：所有指令链路的并集 + IQ/LSQ/ROB + FU 并集
    扇出 + 19 个 CHAOS 注入器挂载。无参调用时从数据层加载。"""
    if families is None or instructions is None:
        families, instructions = load_data()
    nodes, edges, fus, queues, anchors = build_union_graph(families, instructions)
    int_fus = sorted(f for f in fus if f not in _MEM_FUS)
    mem_fus = sorted(f for f in fus if f in _MEM_FUS)
    L = ["flowchart LR"]
    for n in nodes:
        L.append(f'    {n}["{_node_label(n, anchors)}"]')
    if "IQ" in queues:
        L.append('    IQ["IQ · inst_queue.cc:868"]')
    if "LSQ" in queues:
        L.append('    LSQ["LSQ（LQ/SQ→L1D/TLB）· lsq_unit.cc:338"]')
    L.append('    ROB["ROB · rob.cc:194"]')
    for a, b in sorted(edges):
        if (a, b) == ("COMMIT", "REDIRECT"):
            L.append(f"    {a} -.误预测恢复.-> {b}")
        else:
            L.append(f"    {a} --> {b}")
    if "REDIRECT" in nodes:
        L.append("    REDIRECT -.-> FETCH")
    # 队列与 ROB 通道（来自 queue 并集与锚点表：gem5 v25 中 ROB 在 rename→commit 传递上入队）
    if "IQ" in queues:
        L.append("    DISPATCH --> IQ")
        L.append("    IQ --> ISSUE")
    if "LSQ" in queues:
        L.append("    DISPATCH --> LSQ")
        L.append("    LSQ --> ISSUE")
    L.append("    RENAME --> ROB")
    L.append("    ROB --> COMMIT")
    # FU 并集扇出：执行单元（EXECUTE→FU→WRITEBACK）与访存 opClass（LSQ→FU→MEMORY）
    for fu in int_fus:
        L.append(f'    FU_{fu}["{fu}"]')
        L.append(f"    EXECUTE --> FU_{fu}")
        L.append(f"    FU_{fu} --> WRITEBACK")
    for fu in mem_fus:
        L.append(f'    FU_{fu}["{fu}"]')
        L.append(f"    LSQ --> FU_{fu}")
        L.append(f"    FU_{fu} --> MEMORY")
    for inj, stage in sorted(INJECTOR_MOUNTS.items()):
        L.append(f"    {inj}[{sanitize_mermaid(inj)}]:::chaos -.命中.-> {stage}")
    L.append("    classDef chaos fill:#fdd,stroke:#900,stroke-width:2px")
    return "\n".join(L)


def render_master_dot(families=None, instructions=None):
    """同构 graphviz dot 版并集总图（dot -Tsvg 可渲染）。"""
    if families is None or instructions is None:
        families, instructions = load_data()
    nodes, edges, fus, queues, anchors = build_union_graph(families, instructions)
    int_fus = sorted(f for f in fus if f not in _MEM_FUS)
    mem_fus = sorted(f for f in fus if f in _MEM_FUS)
    L = ["digraph o3_atlas {", "    rankdir=LR; node [shape=box];"]
    for n in nodes:
        L.append(f'    {n} [label="{_node_label(n, anchors)}"];')
    if "IQ" in queues:
        L.append('    IQ [label="IQ · inst_queue.cc:868"];')
    if "LSQ" in queues:
        L.append('    LSQ [label="LSQ（LQ/SQ→L1D/TLB）· lsq_unit.cc:338"];')
    L.append('    ROB [label="ROB · rob.cc:194"];')
    for a, b in sorted(edges):
        style = ' [style=dashed, label="误预测恢复"]' if (a, b) == ("COMMIT", "REDIRECT") else ""
        L.append(f"    {a} -> {b}{style};")
    if "REDIRECT" in nodes:
        L.append("    REDIRECT -> FETCH [style=dashed];")
    if "IQ" in queues:
        L.append("    DISPATCH -> IQ; IQ -> ISSUE;")
    if "LSQ" in queues:
        L.append("    DISPATCH -> LSQ; LSQ -> ISSUE;")
    L.append("    RENAME -> ROB; ROB -> COMMIT;")
    for fu in int_fus:
        L.append(f'    FU_{fu} [label="{fu}", shape=ellipse];')
        L.append(f"    EXECUTE -> FU_{fu}; FU_{fu} -> WRITEBACK;")
    for fu in mem_fus:
        L.append(f'    FU_{fu} [label="{fu}", shape=ellipse];')
        L.append(f"    LSQ -> FU_{fu}; FU_{fu} -> MEMORY;")
    for inj, stage in sorted(INJECTOR_MOUNTS.items()):
        L.append(f'    {inj} [label="{inj}", shape=hexagon, '
                 f'style=filled, fillcolor="#fdd", color="#900"];')
        L.append(f"    {inj} -> {stage} [style=dashed, label=命中];")
    L.append("}")
    return "\n".join(L)


def render_matrix(instructions):
    """指令 × CHAOS 注入器命中矩阵（372 行 × 19 列；✓ 命中 / · 未命中）。"""
    injs = list(INJECTORS)
    out = ["# 指令 × CHAOS 注入器命中矩阵", "",
           f"| 指令 | {' | '.join(injs)} |",
           "|---|" + "---|" * len(injs)]
    for r in sorted(instructions, key=lambda x: x["doc"]):
        hits = set(r.get("injectors", []))
        cells = ["✓" if i in hits else "·" for i in injs]
        out.append(f"| [{r['doc']}](../pages/{r['doc']}) | {' | '.join(cells)} |")
    out.append("")
    return "\n".join(out)


def write_diagrams(families, instructions):
    DIAGRAMS.mkdir(parents=True, exist_ok=True)
    mmd = DIAGRAMS / "o3-pipeline.mmd"
    dot_f = DIAGRAMS / "o3-pipeline.dot"
    svg = DIAGRAMS / "o3-pipeline.svg"
    mmd.write_text(render_master_mermaid(families, instructions) + "\n", encoding="utf-8")
    dot_f.write_text(render_master_dot(families, instructions) + "\n", encoding="utf-8")
    if shutil.which("dot"):
        r = subprocess.run(["dot", "-Tsvg", str(dot_f), "-o", str(svg)],
                           capture_output=True, timeout=300)
        if r.returncode != 0:
            raise RuntimeError("dot -Tsvg 失败: " + r.stderr.decode()[:400])
        print(f"diagrams: {mmd.name} + {dot_f.name} + {svg.name}")
    else:
        print(f"diagrams: {mmd.name} + {dot_f.name}（dot 缺失，SVG 未再生，如实记录）")
    (DIAGRAMS / "injector-matrix.md").write_text(
        render_matrix(instructions), encoding="utf-8")
    print("diagrams: injector-matrix.md")

# mermaid 标签里的敌对字符一律换下划线（括号/引号/花括号等会破坏节点语法）
_MERMAID_BAD = str.maketrans({c: "_" for c in '()"\'`;:[]{}|<>#,'})

BEHAVIOR_CHAIN = {
    "absent": "FETCH → DECODE（无匹配编码）→ Unknown64 → IllegalInstFault → 提交异常",
    "warn-nop": "FETCH → DECODE → WarnUnimplemented（警告 + NOP 语义）→ ISSUE → EXECUTE(nop) → WRITEBACK → COMMIT",
    "illegal-fault": "FETCH → DECODE（解码但实现拒绝）→ fault → COMMIT",
}


def sanitize_mermaid(s):
    return str(s).translate(_MERMAID_BAD)


def render_mini_mermaid(fam, hit_injectors=()):
    """家族流水线主链 + 命中注入器按总图 INJECTOR_MOUNTS 挂到对应站点。"""
    nodes = fam["pipeline"]
    lines = ["flowchart LR"]
    for i, n in enumerate(nodes):
        lines.append(f"    N{i}[{sanitize_mermaid(n)}]")
    for i in range(len(nodes) - 1):
        lines.append(f"    N{i} --> N{i + 1}")
    idx = {n: i for i, n in enumerate(nodes)}
    for j, inj in enumerate(sorted(hit_injectors)):
        target = INJECTOR_MOUNTS.get(inj, "EXECUTE")
        ti = idx.get(target, len(nodes) - 1)
        lines.append(f"    I{j}[{sanitize_mermaid(inj)}] -.-> N{ti}")
    return "\n".join(lines)


def render_page(rec, fam):
    doc = rec["doc"]
    out = [f"# {rec['mnemonic']} — O3 微架构链路\n"]
    out.append(f"> 原文：[{doc}](../../armv8-isa/{doc})")
    if rec["tier"] == "unimplemented":
        out.append(f"> tier: {rec['tier']} · behavior: {rec.get('behavior', 'n/a')}\n")
        out.append("## 短链路\n")
        out.append(BEHAVIOR_CHAIN.get(rec.get("behavior"), "n/a") + "\n")
    else:
        overrides = rec.get("overrides") or {}
        queue = fam.get("queue", "n/a")
        fu = overrides.get("fu", fam.get("fu", "n/a"))
        out.append(f"> tier: {rec['tier']} · family: {rec.get('family')}\n")
        out.append("## 一图链路\n")
        out.append("```mermaid")
        out.append(render_mini_mermaid(fam, rec.get("injectors", [])))
        out.append("```\n")
        out.append("## 分站链路\n")
        out.append("| 站点 | 代码锚点 |")
        out.append("|---|---|")
        for node in fam["pipeline"]:
            out.append(f"| {node} | {fam.get('anchors', {}).get(node, 'n/a')} |")
        out.append("")
        gem5 = rec.get("gem5") or {}
        out.append("## 解码身份\n")
        out.append(f"- decoder 格式：{gem5.get('decode_mnemonic', 'n/a')}")
        out.append(f"- StaticInst 类：{gem5.get('static_inst', 'n/a')}")
        out.append(f"- 解码锚点：{(gem5.get('anchors') or {}).get('decoder', 'n/a')}\n")
        out.append("## 队列与执行单元\n")
        out.append(f"- 队列：{queue} · FU：{fu}\n")
        out.append("## CHAOS 注入器命中\n")
        out.append("| 注入器 |")
        out.append("|---|")
        for inj in sorted(rec.get("injectors", [])):
            out.append(f"| {inj} |")
        out.append("")
    out.append("## 证据\n")
    out.append("| 断言 | 锚点 |")
    out.append("|---|---|")
    for ev in rec.get("evidence", []):
        out.append(f"| {ev.get('claim', '')} | {ev.get('anchor', '')} |")
    out.append("")
    return "\n".join(out)


def render_index(cat, recs):
    total = len(instruction_pages())
    tiers = {}
    for r in recs:
        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    out = [f"# {cat} 链路索引\n", "## 统计\n", "| 分类 | 收录 | 覆盖 |", "|---|---|---|",
           f"| {cat} | {len(recs)} | {total} 项中的 {len(recs)} 项 |\n"]
    out.append("tier 分布：" + "、".join(f"{k} {v}" for k, v in sorted(tiers.items())) + "\n")
    out += ["## 记录\n", "| 原文 | 助记符 | tier | family |", "|---|---|---|---|"]
    for r in sorted(recs, key=lambda x: x["doc"]):
        out.append(f"| [{r['doc']}](../pages/{r['doc']}) | {r.get('mnemonic', '')} "
                   f"| {r['tier']} | {r.get('family', 'n/a')} |")
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default=None,
                    help="只生成该分类（默认全部有记录的分类）")
    ap.add_argument("--diagrams", action="store_true",
                    help="只生成总图与注入器矩阵（diagrams/）")
    args = ap.parse_args()
    families, instructions = load_data()
    if args.diagrams:
        write_diagrams(families, instructions)
        return
    by_cat = {}
    for rec in instructions:
        by_cat.setdefault(category_of(Path(rec["doc"])), []).append(rec)
    cats = [args.category] if args.category else sorted(by_cat)
    if args.category and args.category not in by_cat:
        raise SystemExit(f"no records for category {args.category}")
    PAGES.mkdir(parents=True, exist_ok=True)
    INDEX.mkdir(parents=True, exist_ok=True)
    for cat in cats:
        for rec in by_cat[cat]:
            fam = families.get(rec.get("family")) if rec["tier"] != "unimplemented" else None
            (PAGES / rec["doc"]).write_text(render_page(rec, fam), encoding="utf-8")
        (INDEX / f"{cat}.md").write_text(render_index(cat, by_cat[cat]), encoding="utf-8")
        print(f"{cat}: {len(by_cat[cat])} pages + index")


if __name__ == "__main__":
    main()
