#!/usr/bin/env python3
"""[MDSPEC][B2] pilot 证据汇总器：prop_evt.txt.gz → pilot_evidence.json。

用户第 3 点要求"不得因注册表布尔值为 true 就判定整族完成"。本工具把
**真实 pilot 运行**的 PROP-EVT 流折算成覆盖矩阵可消费的证据文件：

    {"pilots": {run_id: {"unit":…, "kinds":[…], "events":N, "faults":N}},
     "kinds_observed": [...],           # 所有 pilot 的 kind 并集
     "kinds_observed_by_unit": {...}}   # 按单元拆分（矩阵逐单元判据）

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


def unit_of(run_id):
    """RunID → 单元（复用 B1 的机读映射，避免第二处硬编码）。"""
    mp = REPO / "docs/gem5-fi/lsu/mdspec/runid_map.json"
    if not mp.exists():
        return None
    for e in json.loads(mp.read_text(encoding="utf-8"))["entries"]:
        if e["run_id"] == run_id:
            return e["unit"]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("runs", nargs="+", help="<RunID>=<prop_evt path>")
    a = ap.parse_args()

    pilots, union, by_unit = {}, set(), {}
    for spec in a.runs:
        rid, _, path = spec.partition("=")
        events, truncated = P.read_events(Path(path))
        kinds = sorted({e["kind"] for e in events if e.get("kind")})
        unit = unit_of(rid)
        pilots[rid] = {"unit": unit, "path": path, "kinds": kinds,
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
        print(f"  {rid:14s} unit={p['unit']} events={p['events']} "
              f"kinds={len(p['kinds'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
