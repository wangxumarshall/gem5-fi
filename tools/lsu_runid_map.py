#!/usr/bin/env python3
"""[MDSPEC][B1] RunID 机读映射生成器（用户指令三.1，计划 2026-10-19 Task B1）。

把规格工作簿联结为每 RunID 的机读映射（规格→CLI→注入点→监控钩子→结果字段
的数据基础）：
  表 7（执行矩阵：model/unit/freq/fault_type/workload）× 表 9（传播规格：
  触发/路径/必监控/关联键/终止判定/缺失钩子/实现状态/首轮目标）×
  lsu_campaign（MODEL_BLOCKED=W6+MDSPEC 裁决；WL_BINARY/GOLDENS=实测负载
  映射，前缀匹配 + 实存校验，未映射→binary:null+注记+BLOCKED，不猜）。

用法：python3 tools/lsu_runid_map.py --xlsx <p> --out <json>
"""
import argparse
import json
import re
import sys
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_campaign as lc   # noqa: E402  (MODEL_BLOCKED / WL_BINARY / GOLDENS)

RUNID_RE = re.compile(r"^[A-Z]\d{2}-F\d+-W\d+$")


def _rows(ws):
    hdr = [c.value for c in ws[1]]
    ix = {h: i for i, h in enumerate(hdr)}
    out = []
    for r in ws.iter_rows(min_row=2):
        v = [c.value for c in r]
        if v[0] is None or not str(v[0]).strip():
            continue
        out.append(v)
    return ix, out


def _txt(v):
    return "" if v is None else str(v).strip()


def _resolve_workload(spec_name):
    """WL_BINARY 前缀匹配（长键优先）+ 实存校验；未映射 → 不猜（null+注记）。

    路径解析：裸名（agu_addrmodes 等）位于 workloads/directed/；
    带子目录的值（mibench/bin/w1_all）相对 workloads/ 直取。
    """
    for key, binary in sorted(lc.WL_BINARY.items(), key=lambda kv: -len(kv[0])):
        if spec_name.startswith(key):
            for cand in (ROOT / "workloads" / "directed" / binary,
                         ROOT / "workloads" / binary):
                if cand.exists():
                    return binary, None
            return None, f"WL_BINARY 映射 {key}→{binary} 但二进制不存在"
    return None, "规格负载名无 SE 载体映射（WL_BINARY 前缀未命中；不猜）"


def generate_map(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    i7, r7 = _rows(wb["7.展开执行矩阵"])
    i9, r9 = _rows(wb["9.逐RunID传播监控"])

    rid9 = {}
    for r in r9:
        rid = _txt(r[i9["RunID"]])
        if RUNID_RE.match(rid):
            if rid in rid9:
                sys.exit(f"[ABORT] 表9 RunID 重复：{rid}")
            rid9[rid] = r
    ids7 = [_txt(r[i7["RunID"]]) for r in r7 if RUNID_RE.match(_txt(r[i7["RunID"]]))]
    if set(ids7) != set(rid9):
        sys.exit(f"[ABORT] 表7∩表9 RunID 集合不一致："
                 f"only7={sorted(set(ids7) - set(rid9))[:5]} "
                 f"only9={sorted(set(rid9) - set(ids7))[:5]}")

    entries = []
    for r in r7:
        rid = _txt(r[i7["RunID"]])
        if not RUNID_RE.match(rid):
            continue
        model = _txt(r[i7["模型ID"]])
        spec_name = _txt(r[i7["负载（真实名称）"]])
        binary, wl_note = _resolve_workload(spec_name)
        s9 = rid9[rid]
        impl_status = _txt(s9[i9["实现状态"]])
        reasons = []
        if model in lc.MODEL_BLOCKED:
            reasons.append(f"campaign:{lc.MODEL_BLOCKED[model]}")
        if impl_status.startswith("需新增"):
            reasons.append(f"spec:{impl_status}")
        if wl_note:
            reasons.append(f"workload:{wl_note}")
        entries.append(dict(
            run_id=rid, model_id=model,
            unit=_txt(r[i7["单元"]]), freq=_txt(r[i7["频率"]]),
            fault_type=_txt(r[i7["故障类型"]]),
            submodels=_txt(s9[i9["故障子模型"]]),
            trigger=_txt(s9[i9["触发条件"]]),
            workload=dict(spec_name=spec_name, binary=binary,
                          golden=lc.GOLDENS.get(binary) if binary else None,
                          note=wl_note or ""),
            path_raw=_txt(s9[i9["完整传播路径（按顺序）"]]),
            path_nodes=re.findall(r"L\d", _txt(s9[i9["完整传播路径（按顺序）"]])),
            monitors=_txt(s9[i9["必监控单元/事件/指标"]]),
            existing_coverage=_txt(s9[i9["现有代码监控与源码"]]),
            missing_hooks=_txt(s9[i9["缺失监控及新增钩子"]]),
            correlation_keys=_txt(s9[i9["跨单元关联键"]]),
            termination=_txt(s9[i9["完整性/传播终止判定"]]),
            impl_status=impl_status,
            status="BLOCKED" if reasons else "PARTIAL",
            status_reasons=reasons,
            target_activated_samples=_txt(s9[i9["首轮目标Activated样本数"]]),
        ))

    from collections import Counter
    summary = dict(total=len(entries),
                   status=dict(Counter(e["status"] for e in entries)),
                   blocked_by_unit=dict(Counter(
                       e["unit"] for e in entries if e["status"] == "BLOCKED")))
    return dict(source=Path(xlsx_path).name, entries=entries, summary=summary)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    m = generate_map(a.xlsx)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(m, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    print(f"[runid_map] {m['summary']['total']} RunID → {a.out}")
    print(f"[runid_map] status={m['summary']['status']} "
          f"blocked_by_unit={m['summary']['blocked_by_unit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
