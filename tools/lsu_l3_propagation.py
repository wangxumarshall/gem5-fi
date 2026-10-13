#!/usr/bin/env python3
"""lsu_l3_propagation.py — [LSU][OBS-L3] 真实 L3 传播链解析器（纠偏轮 Subagent-A）。

中央纠偏指令 2026-10-13：LSU 非 PRF 故障的 L3 = 真实传播关联
（inj→addr_form→mem_req→resp→taint_reg→consumer→errant_commit），
绝不以 commit-divergence 计数或 PRF liveness proxy 冒充传播证据。

生产者：CHAOS/gem5/src/cpu/o3/CHAOSPropagation/（prop_trace.csv.gz v1，
逐节点 gzflush(Z_SYNC_FLUSH)——abort 前缀可打捞，W2.1 契约）。
本模块是唯一解析/判定入口；tools/lsu_obs_core.build_l3 在
prop_trace_path 非 None 时委托本模块（B 侧接线）。

契约（钉死，勿单侧漂移）：
  COVERED_FAMILIES = {"addrpath", "cache"}   # 其余家族一律 unsupported
  parse_prop_trace(path) -> {"truncated", "nodes", "funnel", "malformed"}
  build_l3(family, l2, prop_trace_path, inactive=False) -> dict
    - inactive → {"status": "N/A(inactive_no_activation)", "reason": ...}
    - 家族未覆盖 / trace 缺失或 0 节点 →
      {"status": "unsupported", "method": None, "reason": ...}
    - 正常 → {"status": "complete", "method": "propagation_trace",
        "correlation_keys": ["dynInstSeqNum", "request_id", "ptag"],
        "evidence": {injection, address_formation, mem_requests, responses,
                     tainted_regs, consumers, first_errant_commit,
                     path_complete},
        "caveats": [...], ...}
  诚实边界：auxiliary_commit_footprint（L2 副产品）可附注但绝不作
  evidence；commit_diff 的 divergence 计数绝不冒充传播链。
"""
import gzip
import json
from pathlib import Path

# 仅真实实现的家族；lsqfwd/prefetch/exmod 首版未接线 → unsupported（如实）
COVERED_FAMILIES = {"addrpath", "cache"}

# prop_trace.csv.gz v1 钉死格式（CHAOSPropagation.hh 头注释 = 规范）
HEADER_PREFIX = "# lsu-propagation v1:"
COLUMNS = ["node_id", "tick", "ptag", "kind", "dyn_inst_seq", "request_id",
           "addr", "phys_reg", "arch_reg", "detail"]
KINDS = {"inj", "addr_form", "mem_req", "resp", "taint_reg", "consumer",
         "errant_commit", "funnel"}
_INT_COLS = {"node_id", "tick", "ptag", "dyn_inst_seq", "request_id",
             "phys_reg", "arch_reg"}
_EVIDENCE_NODE_CAP = 20          # evidence 列表节点上限（全量在 trace 文件）


def _parse_detail(raw):
    """detail 列 'k=v;k=v' → dict（值保持字符串；无 '=' 的段忽略）。"""
    out = {}
    for seg in (raw or "").split(";"):
        if "=" in seg:
            k, v = seg.split("=", 1)
            out[k] = v
    return out


def _parse_node(raw):
    """一行 CSV → node dict；格式不符（列数≠10）→ None。"""
    parts = raw.rstrip("\n").split(",", 9)
    if len(parts) != len(COLUMNS):
        return None
    node = dict(zip(COLUMNS, parts))
    for col in _INT_COLS:
        node[col] = int(node[col]) if node[col] != "" else None
    node["addr"] = (int(node["addr"], 16) if node["addr"] != ""
                    else None)
    node["detail"] = _parse_detail(node["detail"])
    return node


def parse_prop_trace(path):
    """解析 prop_trace.csv.gz v1。

    abort 打捞契约（W2.1 同款）：生产者每节点 gzflush(Z_SYNC_FLUSH)，
    abort 后文件缺 gzip trailer → Python gzip 在耗尽前缀后抛 EOFError，
    已读行保留（truncated=true）；0 字段/0 字节文件如实返回 0 节点。
    首行 '# ' 注释（格式头）跳过；列数不符的行记入 malformed（不静默
    丢弃）。
    """
    out = {"truncated": False, "nodes": [], "funnel": None,
           "malformed": []}
    lines = []
    try:
        with gzip.open(str(path), "rt", encoding="utf-8",
                       errors="replace") as f:
            for line in f:
                lines.append(line)
    except EOFError:
        # trailer-less Z_SYNC_FLUSH 前缀（abort 样本）：保留已读行
        out["truncated"] = True
    except (OSError, gzip.BadGzipFile) as e:
        # 不是 gzip / 读失败：0 节点 + 如实说明（malformed 首条）
        out["malformed"].append(f"gz_read_error: {e}")
        return out
    for raw in lines:
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        node = _parse_node(raw)
        if node is None:
            out["malformed"].append(raw.rstrip("\n")[:160])
            continue
        out["nodes"].append(node)
    # funnel = 最后一个 funnel 节点（abort 存活口径：注入时快照）
    for node in out["nodes"]:
        if node["kind"] == "funnel":
            d = node["detail"]
            try:
                out["funnel"] = {
                    "site": d.get("site"),
                    "attempted": int(d.get("attempted")),
                    "eligible": int(d.get("eligible")),
                    "injected": int(d.get("injected")),
                    "node_id": node["node_id"], "tick": node["tick"],
                }
            except (TypeError, ValueError):
                out["malformed"].append(
                    f"funnel_detail_unparsed: {d}")
    return out


def _compact(node):
    """evidence 列表用的紧凑节点引用（全量字段在 trace 文件本体）。"""
    return {k: node[k] for k in ("node_id", "tick", "ptag", "kind",
                                 "dyn_inst_seq", "request_id", "addr",
                                 "phys_reg", "arch_reg", "detail")}


def _kind_nodes(nodes, kind):
    return [n for n in nodes if n["kind"] == kind]


def build_l3(family, l2, prop_trace_path, inactive=False):
    """L3：真实传播链证据（契约见模块 docstring）。

    绝不用 commit_diff 的 divergence 计数或 PRF liveness proxy 冒充
    L3——L2 副产品仅以 auxiliary_commit_footprint 附注（不作 evidence）。
    """
    if inactive:
        return {"status": "N/A(inactive_no_activation)",
                "reason": "activated=0（用户指令 2026-10-12 二.4）"}
    if family not in COVERED_FAMILIES:
        return {"status": "unsupported", "method": None,
                "reason": (f"家族（{family}）不在传播链 v1 覆盖集 "
                           f"{sorted(COVERED_FAMILIES)} 内：该家族注入器"
                           f"未接 CHAOSPropagation（OBS-L3 纠偏轮首版范"
                           f"围=addrpath+cache；lsqfwd/prefetch/exmod 如实"
                           f"unsupported）")}
    if prop_trace_path is None:
        return {"status": "unsupported", "method": None,
                "reason": "无 prop_trace（未收集：非 full 模式或驱动未加"
                          "--chaos_propagation 旗标）"}
    p = Path(prop_trace_path)
    if not p.exists():
        return {"status": "unsupported", "method": None,
                "reason": f"prop_trace 缺失：{p}"}
    parsed = parse_prop_trace(p)
    nodes = parsed["nodes"]
    if not nodes:
        return {"status": "unsupported", "method": None,
                "reason": (f"prop_trace 0 节点（truncated="
                           f"{parsed['truncated']}；abort 早于首个节点或"
                           f"注入未发生）"),
                "funnel": parsed["funnel"],
                "malformed": parsed["malformed"]}

    inj_nodes = _kind_nodes(nodes, "inj")
    addr_forms = _kind_nodes(nodes, "addr_form")
    mem_reqs = _kind_nodes(nodes, "mem_req")
    resps = _kind_nodes(nodes, "resp")
    taints = _kind_nodes(nodes, "taint_reg")
    consumers = _kind_nodes(nodes, "consumer")
    errants = _kind_nodes(nodes, "errant_commit")

    caveats = [
        "内存间接污染（污染值经 store 写入内存后被另一 load 读回）v1 不"
        "覆盖——污染集仅跟踪 load 目的寄存器",
        "errant_commit=首个污染路径提交（faulting_load_commit|"
        "first_consumer，传播视角）；字段级首个错误提交以 L2 "
        "commit_diff.first_errant_commit 为准（同一 dyn_inst_seq 空间，"
        "可对齐）",
        "squash-后-重分配 stale-taint 窗口（load 写回后被 squash 的罕见"
        "情形；clean-overwrite 规则界定，v1 无 squash hook）",
    ]
    if family == "addrpath":
        caveats.append("纯 flag 模式（S06/L02）链止于 addr_form——无被污"
                       "染地址可跟踪；translation fault（FS 非法地址）无"
                       " completeDataAccess 响应，链止于 mem_req")
    if family == "cache":
        caveats.append("CPU 侧 hook 无法区分 cache hit/miss——clean 块逐"
                       "出后 refetch 的响应可能被误计为 resp（假阳性上"
                       "界；dirty 块回写后 refetch 为真阳性）")
        caveats.append("SE vaddr==paddr 假设（cache 注册表按物理块地址匹"
                       "配）；metadata 字段故障（tag/valid/dirty/coh）与"
                       "victim 路径链止于 inj（无投递跟踪，如实）")
    if parsed["truncated"]:
        caveats.append(f"trace 截断（abort 前缀打捞 {len(nodes)} 节点；"
                       f"链可能在截断点后继续）")
    if parsed["funnel"] is None:
        caveats.append("无 FUNNEL 行（abort 早于首个注入点或注入器未写漏"
                       "斗）")
    if parsed["malformed"]:
        caveats.append(f"{len(parsed['malformed'])} 行格式不符（详见 "
                       f"malformed 列表，不静默丢弃）")

    # L2 副产品附注（单列，绝不作 evidence——obs_core.build_l3 同款口径）
    cd = (l2 or {}).get("commit_diff") or {}
    aux = None
    if cd:
        aux = {
            "n_divergence_points": cd.get("total_divergence_points"),
            "divergence_counts": cd.get("divergence_counts"),
            "first_errant_seq": (cd.get("first_errant_commit") or {}).get("seq"),
            "note": "L2 commit 足迹副产品；不是传播证据（不冒充）",
        }

    return {
        "status": "complete",
        "method": "propagation_trace",
        "correlation_keys": ["dynInstSeqNum", "request_id", "ptag"],
        "evidence": {
            "injection": (_compact(inj_nodes[0]) if inj_nodes else None),
            "address_formation": (_compact(addr_forms[0])
                                  if addr_forms else None),
            "mem_requests": {"count": len(mem_reqs),
                             "nodes": [_compact(n) for n in
                                       mem_reqs[:_EVIDENCE_NODE_CAP]]},
            "responses": {"count": len(resps),
                          "nodes": [_compact(n) for n in
                                    resps[:_EVIDENCE_NODE_CAP]]},
            "tainted_regs": {"count": len(taints),
                             "nodes": [_compact(n) for n in
                                       taints[:_EVIDENCE_NODE_CAP]]},
            "consumers": {"count": len(consumers),
                          "nodes": [_compact(n) for n in
                                    consumers[:_EVIDENCE_NODE_CAP]]},
            "first_errant_commit": (_compact(errants[0]) if errants
                                    else None),
            "path_complete": bool(errants),
        },
        "caveats": caveats,
        "funnel": parsed["funnel"],
        "malformed": parsed["malformed"],
        "truncated": parsed["truncated"],
        "auxiliary_commit_footprint": aux,
    }


def main():
    """CLI 便捷入口：python3 tools/lsu_l3_propagation.py <prop_trace.gz>

    打印 parse_prop_trace + build_l3 摘要（调试/巡检用，无副作用）。
    """
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("trace", help="prop_trace.csv.gz 路径")
    ap.add_argument("--family", default="addrpath",
                    choices=sorted(COVERED_FAMILIES | {"lsqfwd",
                                                       "prefetch"}))
    args = ap.parse_args()
    parsed = parse_prop_trace(args.trace)
    print(json.dumps({
        "parse": {"truncated": parsed["truncated"],
                  "n_nodes": len(parsed["nodes"]),
                  "funnel": parsed["funnel"],
                  "malformed": parsed["malformed"]},
        "build_l3": build_l3(args.family, {}, args.trace),
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
