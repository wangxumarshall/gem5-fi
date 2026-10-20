#!/usr/bin/env python3
"""test_lsu_hook_cpf.py — [MDSPEC][H4/H5/H6] cache/prefetch/atomic 契约测试。

规格（表 9 缺失钩子列）：
- H4（73 RunID）: cache.cc access/evictBlock — cache_access(L1)/cache_evict(L2)，
  与 469429f4 C04-C09 fault_applied→delivery 衔接
- H5（53 RunID）: CHAOSPrefetch 注入漏斗 — pf_train(L1)，pf_request_id
  training→queue→request→fill→demand 链的起点
- H6（28 RunID）: lsq.cc pushRequest atomic — atomic_op(L2)，amo 请求入队

用法：python3 tests/test_lsu_hook_cpf.py   （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def main():
    print("[1] H4/H5/H6 kind→层级与必录字段注册")
    expect = {
        "cache_access": ("L1", ["fault_id", "va", "pa"]),
        # [H4] MSHR 生命周期（allocate/merge/fill/free）+ writeback 持久化
        "mshr_alloc": ("L2", ["fault_id", "cache_line", "mshr_id"]),
        "mshr_merge": ("L2", ["fault_id", "cache_line", "mshr_id"]),
        "mshr_fill": ("L2", ["fault_id", "cache_line", "mshr_id",
                             "fill_id"]),
        "mshr_free": ("L2", ["fault_id", "cache_line", "mshr_id"]),
        "cache_writeback": ("L3", ["fault_id", "cache_line"]),
        "atomic_op": ("L2", ["fault_id", "dyn_inst_seq", "va"]),
    }
    for kind, (layer, fields) in expect.items():
        check(f"{kind} -> {layer}", P.KIND_LAYER.get(kind) == layer,
              str(P.KIND_LAYER.get(kind)))
        req = P.REQUIRED_FIELDS.get(kind)
        check(f"{kind} required fields",
              req is not None and all(f in req for f in fields),
              str(req))

    print("[2] 契约行校验")
    lines = [
        "PROP-EVT: kind=cache_access fault_id=1 va=1ffff70 pa=1ffff70",
        "PROP-EVT: kind=atomic_op fault_id=3 dyn_inst_seq=99 va=7fbff "
        "field=amo",
    ]
    for line in lines:
        evt = P.parse_line(line)
        check(f"validate {evt['kind']}",
              evt is not None and P.validate_event(evt) == [],
              str(P.validate_event(evt) if evt else None))
    bad = P.parse_line("PROP-EVT: kind=cache_evict fault_id=1")
    check("missing cache_line flagged",

    print("[3] cache 故障链推进（C01 真实链 + H4 L1 节点）")
    chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=10",
        "PROP-EVT: kind=cache_access fault_id=1 event_id=1 tick=20 "
        "va=1ffff70 pa=1ffff70",
        "PROP-EVT: kind=cache_evict fault_id=1 event_id=2 tick=22 "
        "cache_line=1ffc00",
        "PROP-EVT: kind=resp fault_id=1 event_id=3 tick=25",
        "PROP-EVT: kind=taint_reg fault_id=1 event_id=4 tick=26",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=5 tick=40",
    ]]
    import lsu_chain_check as CC  # noqa: E402（tools/ 已在 sys.path）
    v = CC.check_chain(chain)
    f1 = v["faults"]["1"]
    check("cache 链 L0→L4 全边 proven → full（cache_access 补 L1 缺口）",
          f1["terminal"] == "full", f1["terminal"])

    print("[4] prefetch 链起点（pf_train L1 → 后续 cache 交付）")
    chain2 = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=2 event_id=0 tick=10",
        "PROP-EVT: kind=pf_train fault_id=2 event_id=1 tick=11 "
        "pf_request_id=1",
        "PROP-EVT: kind=cache_access fault_id=2 event_id=2 tick=20 "
        "va=1ffff70 pa=1ffff70",
        "PROP-EVT: kind=cache_evict fault_id=2 event_id=3 tick=22 "
        "cache_line=1ffc00",
        "PROP-EVT: kind=resp fault_id=2 event_id=4 tick=25",
        "PROP-EVT: kind=taint_reg fault_id=2 event_id=5 tick=26",
        "PROP-EVT: kind=errant_commit fault_id=2 event_id=6 tick=40",
    ]]
    v2 = CC.check_chain(chain2)
    f2 = v2["faults"]["2"]
    check("pf 链 full（pf_train 补 L1）", f2["terminal"] == "full", f2["terminal"])

    print("[5] atomic 链（atomic_op L2）")
    chain3 = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=3 event_id=0 tick=10",
        "PROP-EVT: kind=addr_form fault_id=3 event_id=1 tick=10",
        "PROP-EVT: kind=lsq_push fault_id=3 event_id=2 tick=11",
        "PROP-EVT: kind=atomic_op fault_id=3 event_id=3 tick=12 "
        "dyn_inst_seq=99 va=7fbff field=amo",
        "PROP-EVT: kind=resp fault_id=3 event_id=4 tick=20",
        "PROP-EVT: kind=taint_reg fault_id=3 event_id=5 tick=21",
        "PROP-EVT: kind=errant_commit fault_id=3 event_id=6 tick=40",
    ]]
    v3 = CC.check_chain(chain3)
    f3 = v3["faults"]["3"]
    check("atomic 链 full", f3["terminal"] == "full", f3["terminal"])

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
