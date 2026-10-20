#!/usr/bin/env python3
"""[MDSPEC][B2] pilot 证据汇总器：prop_evt.txt.gz → pilot_evidence.json。

用户第 3 点要求"不得因注册表布尔值为 true 就判定整族完成"。本工具把
**真实 pilot 运行**的 PROP-EVT 流折算成覆盖矩阵可消费的证据文件：

    {"pilots": {run_id: {"unit":…, "unit_source":…, "kinds":[…],
                         "events":N, "faults":N}},
     "kinds_observed": [...],           # 所有 pilot 的 kind 并集
     "kinds_observed_by_unit": {...}}   # 按单元拆分（矩阵逐单元判据）

RunID→单元归属（unit_of，原则化解析、**非逐名特判**）：
  1. RunID 精确等于某矩阵 RunID（runid_map.json）→ 该 entry 的 unit；
  2. 否则按**行标签**（首个 '-' 段）归属：C09-R4T3-MSHRREF-s1 → 行 C09 →
     L1d-Cache；A01-F0-W3-campaign → 行 A01 → AGU。行标签在矩阵中唯一属于
     一个单元才归属——directed 载体、campaign 复跑等任意 <row>-<suffix>
     辅助运行由此通用归单元，其观测计入 kinds_observed_by_unit。否则
     （未知标签 / 跨单元歧义）→ unit=null，不贡献逐单元判据（诚实不归属）。
  归属依据写入 unit_source（"exact" / "row_tag" / null），可审计。
  背景（R4-3 评审 Important-1）：此前辅助运行一律 unit=null，导致本文件的
  逐单元索引与 coverage_matrix 的全局 kind 并集判据互相矛盾（矩阵称
  L1d-Cache 11/11 而逐单元索引无 mshr_alloc）。

用法：
  python3 tools/lsu_pilot_evidence.py --out docs/.../pilot_evidence.json \
      A01-F0-W3=runs/.../prop_evt.txt.gz C01-F0-W6=runs/.../prop_evt.txt.gz ...
  （每个参数形如 <RunID>=<path>；路径可为 .gz）

诚实纪律：pilot 跑失败/无事件 → 该 RunID 记录 events=0，且**不**贡献
任何 kind（"没跑出来" ≠ "已实现"）。
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lsu_chain_check as CC      # noqa: E402  (_group_by_fault)
import lsu_prop_fields as P       # noqa: E402

REPO = HERE.parent
sys.path.insert(0, str(REPO / "tools"))


def _map_entries():
    mp = REPO / "docs/gem5-fi/lsu/mdspec/runid_map.json"
    if not mp.exists():
        return []
    return json.loads(mp.read_text(encoding="utf-8"))["entries"]


def unit_of(run_id, entries=None):
    """RunID → (unit, basis)；basis ∈ {"exact", "row_tag", None}。

    复用 B1 的机读映射（避免第二处硬编码），解析原则见模块 docstring：
    1. 精确匹配矩阵 RunID → (该 entry 的 unit, "exact")；
    2. 行标签（首个 '-' 段）在矩阵中唯一属于一个单元 → (该 unit, "row_tag")
       ——任意 <row>-<suffix> 辅助运行（directed 载体 / campaign 复跑）通用；
    3. 未知行标签或跨单元歧义 → (None, None)（诚实：不归属）。
    """
    if entries is None:
        entries = _map_entries()
    for e in entries:
        if e["run_id"] == run_id:
            return e["unit"], "exact"
    tag = run_id.split("-")[0]
    units = {e["unit"] for e in entries
             if e["run_id"].split("-")[0] == tag}
    if len(units) == 1:
        return units.pop(), "row_tag"
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("runs", nargs="+", help="<RunID>=<prop_evt path>")
    a = ap.parse_args()

    entries = _map_entries()
    pilots, union, by_unit = {}, set(), {}
    for spec in a.runs:
        rid, _, path = spec.partition("=")
        events, truncated = P.read_events(Path(path))
        kinds = sorted({e["kind"] for e in events if e.get("kind")})
        unit, basis = unit_of(rid, entries)
        pilots[rid] = {"unit": unit, "unit_source": basis, "path": path,
                       "kinds": kinds,
                       "events": len(events), "truncated": truncated,
                       "faults": len(CC._group_by_fault(events))}
        union.update(kinds)
        if unit:
            by_unit.setdefault(unit, set()).update(kinds)

    doc = {
        "pilots": pilots,
        "kinds_observed": sorted(union),
        "kinds_observed_by_unit": {k: sorted(v) for k, v in by_unit.items()},
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"[evidence] {len(pilots)} pilots, {len(union)} distinct kinds → {out}")
    for rid, p in pilots.items():
        print(f"  {rid:22s} unit={p['unit']}[{p['unit_source']}] "
              f"events={p['events']} kinds={len(p['kinds'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
