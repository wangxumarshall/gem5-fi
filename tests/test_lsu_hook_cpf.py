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
        "cache_evict": ("L2", ["fault_id", "cache_line", "set", "way"]),
        "cache_return": ("L2", ["fault_id", "pa", "field"]),
        "cache_fill": ("L2", ["fault_id", "pa", "cache_line", "fill_id"]),
        # [H4] MSHR 生命周期（allocate/merge/fill/free）+ writeback 持久化
        "mshr_alloc": ("L2", ["fault_id", "cache_line", "mshr_id"]),
        "mshr_merge": ("L2", ["fault_id", "cache_line", "mshr_id"]),
        "mshr_fill": ("L2", ["fault_id", "cache_line", "mshr_id",
                             "fill_id"]),
        "mshr_free": ("L2", ["fault_id", "cache_line", "mshr_id"]),
        "cache_writeback": ("L3", ["fault_id", "cache_line"]),
        # [H5] prefetch 全链：训练 L1 → 队列/发射 L2 → fill L3 → demand L4
        "pf_train": ("L1", ["fault_id", "pf_request_id", "pc",
                            "before", "after"]),
        "pf_queue": ("L2", ["fault_id", "pf_request_id", "va",
                            "entry_index"]),
        "pf_issue": ("L2", ["fault_id", "pf_request_id", "va"]),
        "pf_fill": ("L3", ["fault_id", "pf_request_id", "pa",
                           "cache_line"]),
        "pf_demand": ("L4", ["fault_id", "pf_request_id", "dyn_inst_seq",
                             "request_id", "pa"]),
        "atomic_op": ("L2", ["fault_id", "dyn_inst_seq", "va"]),
        # [H6] exmon 链：LDXR 置 monitor(L1) → 保留比较(L2) → STXR 消费(L3)
        "exmon_monitor": ("L1", ["fault_id", "dyn_inst_seq", "request_id",
                                 "pa", "before", "after"]),
        "exmon_rmw": ("L2", ["fault_id", "dyn_inst_seq", "pa",
                             "state_before", "state_after"]),
        "exmon_stxr": ("L3", ["fault_id", "dyn_inst_seq", "request_id",
                              "pa", "state_before", "state_after",
                              "entry_index"]),
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
        "PROP-EVT: kind=cache_evict fault_id=1 cache_line=1ffc00 set=3 "
        "way=1 before=1ffff field=dirty_evict_writeback",
        "PROP-EVT: kind=pf_train fault_id=2 pf_request_id=1 pc=4091a0 "
        "before=64 after=0 field=stride",
        "PROP-EVT: kind=pf_queue fault_id=2 pf_request_id=1 va=1ffff70 "
        "entry_index=3 state_after=queued",
        "PROP-EVT: kind=pf_issue fault_id=2 pf_request_id=1 va=1ffff70 "
        "state_after=issued",
        "PROP-EVT: kind=pf_fill fault_id=2 pf_request_id=1 pa=1ffff70 "
        "cache_line=1ffff70 state_after=filled",
        "PROP-EVT: kind=pf_demand fault_id=2 pf_request_id=1 "
        "dyn_inst_seq=4001 request_id=4001 pa=1ffff70 "
        "cache_line=1ffff70 field=demand_hit",
        "PROP-EVT: kind=atomic_op fault_id=3 dyn_inst_seq=99 va=7fbff "
        "field=amo",
        "PROP-EVT: kind=exmon_monitor fault_id=4 dyn_inst_seq=50 "
        "request_id=50 pa=7fbff00 before=7fbff00 after=7fbff40 "
        "field=o01_monitor_addr_bitflip state_before=1 state_after=0",
        "PROP-EVT: kind=exmon_rmw fault_id=4 dyn_inst_seq=51 pa=7fbff00 "
        "field=reservation_compare state_before=reserved "
        "state_after=mismatch_fail",
        "PROP-EVT: kind=exmon_stxr fault_id=4 dyn_inst_seq=51 "
        "request_id=51 pa=7fbff00 entry_index=2 field=stxr_consume "
        "state_before=reserved state_after=fail_retry",
        "PROP-EVT: kind=cache_return fault_id=5 pa=1ffff70 field=hit",
        "PROP-EVT: kind=cache_fill fault_id=5 pa=1ffff70 cache_line=1ffc00 "
        "fill_id=7",
        "PROP-EVT: kind=mshr_alloc fault_id=5 cache_line=1ffff70 "
        "mshr_id=3",
        "PROP-EVT: kind=mshr_merge fault_id=5 cache_line=1ffff70 "
        "mshr_id=3",
        "PROP-EVT: kind=mshr_fill fault_id=5 cache_line=1ffff70 mshr_id=3 "
        "fill_id=7 state_after=filled",
        "PROP-EVT: kind=mshr_free fault_id=5 cache_line=1ffff70 mshr_id=3 "
        "state_after=mshr_freed",
        "PROP-EVT: kind=cache_writeback fault_id=5 cache_line=1ffff70",
        "PROP-EVT: kind=cache_evict fault_id=5 cache_line=1ffff70 set=3 "
        "way=1 before=1ffff field=dirty_evict_writeback",
    ]
    for line in lines:
        evt = P.parse_line(line)
        check(f"validate {evt['kind']}",
              evt is not None and P.validate_event(evt) == [],
              str(P.validate_event(evt) if evt else None))
    bad = P.parse_line("PROP-EVT: kind=cache_evict fault_id=1")
    bad_errors = P.validate_event(bad)
    check("missing cache_line flagged",
          any("cache_line" in e for e in bad_errors), str(bad_errors))
    check("missing victim set/way flagged",
          any("'set'" in e for e in bad_errors)
          and any("'way'" in e for e in bad_errors), str(bad_errors))

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

    print("[6] [H5] pf_request_id 为请求级稳定标识（≠ fault_id）且全链一致")
    req_chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=7 event_id=0 tick=10",
        "PROP-EVT: kind=pf_train fault_id=7 event_id=1 tick=11 "
        "pf_request_id=31 pc=4091a0 before=64 after=0 field=stride",
        "PROP-EVT: kind=pf_queue fault_id=7 event_id=2 tick=12 "
        "pf_request_id=31 va=1ffff70 entry_index=1 state_after=queued",
        "PROP-EVT: kind=pf_issue fault_id=7 event_id=3 tick=13 "
        "pf_request_id=31 va=1ffff70 state_after=issued",
        "PROP-EVT: kind=pf_fill fault_id=7 event_id=4 tick=30 "
        "pf_request_id=31 pa=1ffff70 cache_line=1ffff70 "
        "state_after=filled",
        "PROP-EVT: kind=pf_demand fault_id=7 event_id=5 tick=40 "
        "pf_request_id=31 dyn_inst_seq=4001 request_id=4001 pa=1ffff70 "
        "cache_line=1ffff70 field=demand_hit",
        "PROP-EVT: kind=resp fault_id=7 event_id=6 tick=41",
        "PROP-EVT: kind=taint_reg fault_id=7 event_id=7 tick=42",
        "PROP-EVT: kind=errant_commit fault_id=7 event_id=8 tick=60",
    ]]
    pfids = {e["pf_request_id"] for e in req_chain if e["kind"].startswith("pf_")}
    check("同一预取请求的 pf_* 节点共享唯一 pf_request_id", pfids == {"31"},
          str(pfids))
    ids = {e["pf_request_id"] for e in req_chain if e["kind"].startswith("pf_")}
    fids = {e["fault_id"] for e in req_chain if e["kind"].startswith("pf_")}
    check("pf_request_id ≠ fault_id（请求级标识独立于链标识）",
          ids.isdisjoint(fids), f"pf={ids} fault={fids}")
    v4 = CC.check_chain(req_chain)
    f4 = v4["faults"]["7"]
    check("prefetch 链 L0→L4 全边 proven → full",
          f4["terminal"] == "full", f4["terminal"])
    check("prefetch 链 provable_to=L4", f4["provable_to"] == "L4",
          str(f4["provable_to"]))
    # 源码级不变式：pf_request_id 必须分配在**与 ptag 不相交**的编号空间
    # （真实运行中二者都是 1 会掩盖"等同 fault_id"的错误实现）
    src = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation"
           / "CHAOSPropagation.cc").read_text(encoding="utf-8")
    check("pf_request_id 使用不相交编号空间（PF_ID_BASE）",
          "PF_ID_BASE" in src and "PF_ID_BASE + (++next_pf_request_id)" in src,
          "未找到 PF_ID_BASE 分配")

    print("[7] [H6] exmon 全链（monitor L1 → 保留比较 L2 → STXR 消费 L3）")
    ex_chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=9 event_id=0 tick=10",
        "PROP-EVT: kind=exmon_monitor fault_id=9 event_id=1 tick=30 "
        "dyn_inst_seq=50 request_id=50 pa=7fbff00 before=7fbff00 "
        "after=7fbff40 field=o01_monitor_addr_bitflip state_before=1 "
        "state_after=1",
        "PROP-EVT: kind=cache_access fault_id=9 event_id=2 tick=31 "
        "va=7fbff00 pa=7fbff00",
        "PROP-EVT: kind=cache_return fault_id=9 event_id=3 tick=32 "
        "pa=7fbff00 field=hit",
        "PROP-EVT: kind=exmon_rmw fault_id=9 event_id=4 tick=40 "
        "dyn_inst_seq=51 pa=7fbff00 field=reservation_compare "
        "state_before=reserved state_after=mismatch_fail",
        "PROP-EVT: kind=exmon_stxr fault_id=9 event_id=5 tick=41 "
        "dyn_inst_seq=51 request_id=51 pa=7fbff00 entry_index=1 "
        "field=stxr_consume state_before=reserved state_after=fail_retry",
        "PROP-EVT: kind=resp fault_id=9 event_id=6 tick=45",
        "PROP-EVT: kind=taint_reg fault_id=9 event_id=7 tick=46",
        "PROP-EVT: kind=errant_commit fault_id=9 event_id=8 tick=60",
    ]]
    stxr = [e for e in ex_chain if e["kind"] == "exmon_stxr"][0]
    check("exmon_stxr 的 state_before ≠ state_after（真区分重试结局）",
          stxr["state_before"] != stxr["state_after"],
          f"{stxr['state_before']} vs {stxr['state_after']}")
    v5 = CC.check_chain(ex_chain)
    f5 = v5["faults"]["9"]
    check("exmon 链 L0→L4 全边 proven → full",
          f5["terminal"] == "full", f5["terminal"])
    check("exmon 链 provable_to=L4", f5["provable_to"] == "L4",
          str(f5["provable_to"]))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
