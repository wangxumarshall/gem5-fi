# tools/o3_atlas/generate.py
"""Deterministic renderer: docs/cpu/o3-atlas/data/*.yaml → pages/ + index/.

No timestamps, no dict-order dependence, sorted iteration everywhere:
running twice must be byte-identical (validate.py enforces it).
"""
import argparse
import re
import shutil
import subprocess
from functools import lru_cache
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


# ── 微架构块级总图：节点 = µarch 单元，指令流边 = 全部指令链路的块级并集 ──
# 注入器 → ooo_proxy.py 能力参数（choices 即故障模式面；与实验工具面同源）
INJECTOR_FLAG_MAP = {
    "CHAOSDecode": ["decode_mode"],
    "CHAOSRenameMap": ["rename_mode"],
    "CHAOSFreeList": ["freelist_mode"],
    "CHAOSROB": ["rob_mode"],
    "CHAOSIQ": ["iq_mode"],
    "CHAOSPhysReg": ["phys_mode"],
    "CHAOSReg": ["fault_type"],
    "CHAOSFPU": ["fpu_bitseg"],
    "CHAOSLSQFwd": ["lsq_struct_mode"],
    "CHAOSAddrPath": ["addrpath_mode"],
    "CHAOSBPU": ["bpu_mode"],
    "CHAOSExMon": ["exmon_mode"],
    "CHAOSMem": ["protection_model"],
    "CHAOSExec": [], "CHAOSL1DForward": [], "CHAOSRAS": [], "CHAOSCache": [],
    "CHAOSProbe": [], "CHAOSCommitTrace": [],
}
# 无枚举模式的注入器的能力描述
_INJ_PLAIN_DESC = {
    "CHAOSExec": "整数结果 XOR 位翻转（exec_fault_mask 参数化）",
    "CHAOSL1DForward": "L1D 返回包数据位翻转（fault_mask 参数化）",
    "CHAOSRAS": "提交期 head fault 清除（异常抑制）",
    "CHAOSCache": "cache 行数据注入（arm_chaos_cache 配置族）",
}
# 注入器 → 破坏的目标状态
INJECTOR_TARGET = {
    "CHAOSDecode": "StaticInst 编码/寄存器号/立即数（解码输出 + rename 目的寄存器替换）",
    "CHAOSRenameMap": "RAT 表项（逻辑→物理映射、历史位、源标签）",
    "CHAOSFreeList": "空闲物理寄存器表（弹出/标记空闲/释放丢弃/栈头位）",
    "CHAOSPhysReg": "PRF 槽位值（bitflip/stuck，phys/arch_frontend/arch_commit 定位）",
    "CHAOSIQ": "IQ 表项源标签 CAM/就绪位/唤醒/派发路由",
    "CHAOSROB": "ROB 表项字段（pc/dest/done/exc/oldphys/头尾指针）+ done 位时序",
    "CHAOSReg": "提交态架构寄存器（GPR/FPR，bitflip/stuck-at/random + 永久化）",
    "CHAOSExec": "整数执行结果（IntAlu/IntMult/IntDiv 结果 XOR）",
    "CHAOSFPU": "浮点结果分段（sign/exp/mantissa + FMA 加权/舍入/FPSR）",
    "CHAOSLSQFwd": "store→load 前送数据通路（字节/车道/陈旧行/源替换/相位）",
    "CHAOSL1DForward": "L1D 返回包数据（ECC 检查后注入）",
    "CHAOSAddrPath": "翻译前虚地址（byte7 清零/低位翻转）",
    "CHAOSBPU": "分支预测方向/目标翻转 + RAS 返回地址",
    "CHAOSRAS": "提交期异常抑制（清除 head 挂起 fault）",
    "CHAOSExMon": "独占监视器（STXR 强制成败/监视器状态）",
    "CHAOSMem": "DRAM 侧（保护模型 + 概率位翻转/stuck）",
    "CHAOSCache": "cache 行数据（L1D/L1I/L2）",
    "CHAOSProbe": "观测器：ROB/IQ/FreeList 占基采样（只读）",
    "CHAOSCommitTrace": "观测器：commit 轨迹与 squash 记录（只读）",
}
# µarch 块表：(块 id, 显示名+结构, 挂载注入器, 挂载锚点)
MICROARCH_BLOCKS = [
    ("BPU", "BPU 分支预测器（BTB·RAS·方向/目标）", ["CHAOSBPU"],
     "CHAOS/gem5/src/cpu/o3/bac.cc:565"),
    ("FTQ", "FTQ 取指目标队列", [], "CHAOS/gem5/src/cpu/o3/ftq.cc:186"),
    ("ICACHE", "ICache 取指", [], "CHAOS/gem5/src/cpu/o3/fetch.cc:1059"),
    ("DECODER", "Decoder（编码→StaticInst）", ["CHAOSDecode"],
     "CHAOS/gem5/src/cpu/o3/fetch.cc:1257"),
    ("RAT", "RAT 重命名映射表", ["CHAOSRenameMap"],
     "CHAOS/gem5/src/cpu/o3/rename_map.hh:266"),
    ("FREELIST", "FreeList 空闲物理寄存器表", ["CHAOSFreeList"],
     "CHAOS/gem5/src/cpu/o3/free_list.hh:115"),
    ("IQ", "IQ 发射队列（源标签 CAM·就绪位·唤醒）", ["CHAOSIQ"],
     "CHAOS/gem5/src/cpu/o3/inst_queue.cc:694"),
    ("LSQ", "LSQ（LQ/SQ·store→load 前送·独占监视）",
     ["CHAOSLSQFwd", "CHAOSExMon"], "CHAOS/gem5/src/cpu/o3/lsq_unit.cc:338"),
    ("FU", "FU 池", ["CHAOSExec", "CHAOSFPU"],
     "CHAOS/gem5/src/cpu/o3/dyn_inst.cc:367"),
    ("TLBPATH", "地址通路（翻译前 vaddr·TLB）", ["CHAOSAddrPath"],
     "CHAOS/gem5/src/cpu/o3/lsq.cc:1176"),
    ("L1D", "L1D 返回通路（ECC 后包数据）", ["CHAOSL1DForward", "CHAOSCache"],
     "CHAOS/gem5/src/cpu/o3/lsq_unit.cc:200"),
    ("DRAM", "内存子系统（DRAM 保护模型）", ["CHAOSMem"],
     "CHAOS/gem5/src/mem/CHAOSMem/CHAOSMem.cc"),
    ("PRF", "PRF 物理寄存器堆", ["CHAOSPhysReg"],
     "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc:201"),
    ("ROB", "ROB 重排序缓冲（pc·dest·done·exc·指针）", ["CHAOSROB", "CHAOSRAS"],
     "CHAOS/gem5/src/cpu/o3/rob.cc:236"),
    ("ARCHRF", "架构寄存器堆（提交态）", ["CHAOSReg"],
     "CHAOS/gem5/src/CHAOSReg/CHAOSReg.cc:287"),
    ("OBS", "观测器（占基采样·commit 轨迹，只读）",
     ["CHAOSProbe", "CHAOSCommitTrace"], "CHAOS/gem5/src/cpu/o3/commit.cc:1299"),
]


@lru_cache(maxsize=1)
def parse_injector_caps():
    """解析 ooo_proxy.py argparse 的 choices——各注入器的故障模式全集。

    与实验工具面同源：ooo_proxy.py 新增/删除模式，本表与总图徽标自动跟随。
    """
    src = (REPO / "configs/se/ooo_proxy.py").read_text(encoding="utf-8",
                                                       errors="replace")
    # 先剥离 # 行注释：注释里的方括号（如 enc[28:24]）会提前终止 choices 匹配
    src = re.sub(r"#[^\n]*", "", src)
    caps = {}
    for part in src.split('add_argument("')[1:]:
        flag = part.split('"', 1)[0].lstrip("-")
        end = part.find("add_argument")
        body = part[:end] if end != -1 else part
        cm = re.search(r"choices\s*=\s*\[(.*?)\]", body, re.S)
        if cm:
            caps[flag] = re.findall(r'"([^"]+)"', cm.group(1))
    return caps


def _inj_modes(inj, caps):
    return [m for flag in INJECTOR_FLAG_MAP.get(inj, [])
            for m in caps.get(flag, [])]


def _inj_badge(inj, caps):
    if inj in ("CHAOSProbe", "CHAOSCommitTrace"):
        return f"👁{inj}(观测)"
    modes = _inj_modes(inj, caps)
    if modes:
        return f"⚡{inj}({len(modes)}模式)"
    return f"⚡{inj}({_INJ_PLAIN_DESC.get(inj, '参数化注入')})"


# 流水线站点标签（内嵌 µarch 结构；EXECUTE 的 FU 并集动态填充）
_STAGE_LABELS = {
    "BPU": "BPU<br/>BTB·RAS·方向/目标预测",
    "FTQ": "FTQ<br/>取指目标队列",
    "FETCH": "FETCH<br/>ICache 取指",
    "DECODE": "DECODE<br/>Decoder→StaticInst",
    "RENAME": "RENAME<br/>RAT·FreeList→物理标签",
    "DISPATCH": "DISPATCH<br/>IQ/LSQ 入队",
    "ISSUE": "ISSUE<br/>IQ 唤醒·选择",
    "EXECUTE": "EXECUTE<br/>FU 池",
    "MEMORY": "MEMORY<br/>LSQ·L1D·TLB",
    "WRITEBACK": "WRITEBACK<br/>PRF 写回",
    "COMMIT": "COMMIT<br/>ROB→架构RF",
    "REDIRECT": "REDIRECT<br/>误预测重定向",
}
_STAGE_ORDER = ["BPU", "FTQ", "FETCH", "DECODE", "RENAME", "DISPATCH",
                "ISSUE", "EXECUTE", "MEMORY", "WRITEBACK", "COMMIT", "REDIRECT"]


def _ordered_injectors():
    """按挂载站点在流水线中的顺序排列注入器（能力层与流水线从左到右对齐）。"""
    return sorted(INJECTOR_MOUNTS,
                  key=lambda i: (_STAGE_ORDER.index(INJECTOR_MOUNTS[i]), i))


def _caps_node_label(inj, caps):
    if inj in ("CHAOSProbe", "CHAOSCommitTrace"):
        return f"👁{inj}(观测)"
    modes = _inj_modes(inj, caps)
    if modes:
        rep = ", ".join(modes[:3]) + ("…" if len(modes) > 3 else "")
        return f"⚡{inj}({len(modes)}模式)<br/>{rep}"
    return f"⚡{inj}<br/>{_INJ_PLAIN_DESC.get(inj, '参数化注入')}"


def render_master_mermaid(families=None, instructions=None):
    """O3 总图（mermaid，上下两层）：上层 = CPU 微架构流水线（指令流 = 全部
    implemented 指令链路的并集，站点标签内嵌 µarch 结构）；下层 = 故障注入
    能力层（19 个注入器按挂载站点对齐，⚡模式计数实时解析自 ooo_proxy.py，
    虚线自流水线站点垂下）。无参时从数据层加载。"""
    if families is None or instructions is None:
        families, instructions = load_data()
    nodes, edges, fus, _q, _a = build_union_graph(families, instructions)
    caps = parse_injector_caps()
    int_fus = sorted(f for f in fus if f not in _MEM_FUS)
    L = ["flowchart TB"]
    L.append('    subgraph PIPE["⟦CPU 微架构流水线⟧ 指令流 = 全部 implemented 指令链路的并集"]')
    L.append("        direction LR")
    for s in nodes:
        label = _STAGE_LABELS.get(s, s)
        if s == "EXECUTE" and int_fus:
            label = f"EXECUTE<br/>FU 池（{'·'.join(int_fus)}）"
        L.append(f'        {s}["{label}"]')
    for a, b in sorted(edges):
        if (a, b) == ("COMMIT", "REDIRECT"):
            L.append(f"        {a} -.误预测.-> {b}")
        else:
            L.append(f"        {a} --> {b}")
    if "REDIRECT" in nodes:
        L.append("        REDIRECT -.-> FETCH")
    L.append("    end")
    L.append('    subgraph CAPS["⟦故障注入能力层⟧ ⚡注入器(模式数)·👁观测器（模式全集实时解析自 ooo_proxy.py）"]')
    L.append("        direction LR")
    for inj in _ordered_injectors():
        L.append(f'        {inj}["{_caps_node_label(inj, caps)}"]:::capnode')
    L.append("    end")
    # 挂载边：流水线站点 -.-> 正下方注入器
    for inj, stage in sorted(INJECTOR_MOUNTS.items()):
        L.append(f"    {stage} -.-> {inj}")
    L.append("    classDef capnode fill:#fdd,stroke:#900,stroke-width:2px")
    return "\n".join(L)


def render_master_dot(families=None, instructions=None):
    """同构 graphviz dot 版两层总图（dot -Tsvg 可渲染）。"""
    if families is None or instructions is None:
        families, instructions = load_data()
    nodes, edges, fus, _q, _a = build_union_graph(families, instructions)
    caps = parse_injector_caps()
    int_fus = sorted(f for f in fus if f not in _MEM_FUS)
    L = ["digraph o3_atlas {", "    rankdir=TB;",
         '    subgraph cluster_pipeline {',
         '        label="⟦CPU 微架构流水线⟧ 指令流=implemented 指令链路并集";',
         "        node [shape=box];"]
    for s in nodes:
        label = _STAGE_LABELS.get(s, s).replace("<br/>", "\\n")
        if s == "EXECUTE" and int_fus:
            label = f"EXECUTE\\nFU 池（{'·'.join(int_fus)}）"
        L.append(f'        {s} [label="{label}"];')
    for a, b in sorted(edges):
        style = ' [style=dashed, label="误预测"]' if (a, b) == ("COMMIT", "REDIRECT") else ""
        L.append(f"        {a} -> {b}{style};")
    if "REDIRECT" in nodes:
        L.append("        REDIRECT -> FETCH [style=dashed];")
    L.append("    }")
    L.append('    subgraph cluster_caps {')
    L.append('        label="⟦故障注入能力层⟧ ⚡注入器(模式数)·👁观测器（实时解析自 ooo_proxy.py）";')
    L.append('        node [shape=hexagon, style=filled, fillcolor="#fdd", color="#900"];')
    for inj in _ordered_injectors():
        label = _caps_node_label(inj, caps).replace("<br/>", "\\n")
        L.append(f'        {inj} [label="{label}"];')
    L.append("    }")
    for inj, stage in sorted(INJECTOR_MOUNTS.items()):
        L.append(f"    {stage} -> {inj} [style=dashed];")
    L.append("}")
    return "\n".join(L)


def render_injection_caps():
    """微架构单元 × 故障注入能力表（模式全集实时解析自 ooo_proxy.py）。"""
    caps = parse_injector_caps()
    out = ["# 微架构单元 × 故障注入能力", "",
           "> 故障模式全集实时解析自 `configs/se/ooo_proxy.py`（与实验工具面同源："
           "工具增删模式，此表与总图徽标自动跟随）。",
           "", "| 微架构单元 | 注入器 | 模式数 | 故障模式全集 / 能力 | 破坏目标 | 挂载锚点 |",
           "|---|---|---|---|---|---|"]
    for bid, label, injs, anchor in MICROARCH_BLOCKS:
        unit = f"{bid}（{label}）"
        if not injs:
            out.append(f"| {unit} | — | 0 | 无注入挂载 | — | {anchor} |")
            continue
        for inj in injs:
            modes = _inj_modes(inj, caps)
            cap_text = (", ".join(modes) if modes
                        else _INJ_PLAIN_DESC.get(inj, "参数化注入"))
            n = str(len(modes)) if modes else "—"
            out.append(f"| {unit} | **{inj}** | {n} | {cap_text} | "
                       f"{INJECTOR_TARGET[inj]} | {anchor} |")
    out.append("")
    return "\n".join(out)


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
    (DIAGRAMS / "injection-capabilities.md").write_text(
        render_injection_caps(), encoding="utf-8")
    print("diagrams: injection-capabilities.md")

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
