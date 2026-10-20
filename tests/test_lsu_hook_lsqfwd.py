#!/usr/bin/env python3
"""test_lsu_hook_lsqfwd.py — [MDSPEC][R4-1] lsq_fwd 事件契约测试。

规格（任务 R4-1 brief 1.3/1.4 + 用户裁决 2026-10-20）：
"把生产 store 的 dyn_inst_seq/sq_idx/request_id 与消费 load 的
dyn_inst_seq/lq_idx/request_id 传入 CHAOSLSQFwd；lsq_fwd 事件必录字段加入
store_dyn_inst_seq/sq_idx/lq_idx/request_id；移除仅地址关联路径
（或标注为 fallback 并记录）"

契约：
- kind=lsq_fwd → L3（转发数据被污染，S 系转发故障）
- 必录字段（PRIMARY 关联键，裁决 1）：
  dyn_inst_seq（消费 load）、store_dyn_inst_seq（生产 store）、
  sq_idx、lq_idx、request_id + 原有 fault_id/va/field/before/after
- corr 标注（裁决 1 的 fallback 半边）：seq 可得 → corr=seq_primary；
  seq 不可得 → corr=addr_fallback，不得静默走地址关联
- 注册表双源一致（store_dyn_inst_seq / corr 在 C++ 与 Python 注册表中
  同名同序——发射端 unknown-key 丢弃语义要求它们必须是注册字段）
- join 面：lsq_fwd.sq_idx 与 sq_writeback/sq_complete 的 sq_idx 同源
  （DynInst::sqIdx）；lsq_fwd.lq_idx 与 lq_read 的 lq_idx 同源（read()
  的 load_idx 参数）——字段名层面可 1:1 关联

用法：python3 tests/test_lsu_hook_lsqfwd.py   （退出码 0=全 PASS）
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
    print("[1] lsq_fwd kind→层级 + 必录字段（PRIMARY 关联键）")
    check("lsq_fwd -> L3", P.KIND_LAYER.get("lsq_fwd") == "L3",
          str(P.KIND_LAYER.get("lsq_fwd")))
    req = P.REQUIRED_FIELDS.get("lsq_fwd")
    check("lsq_fwd required fields registered", req is not None)
    check("new R4-1 keys required",
          req is not None and all(f in req for f in (
              "store_dyn_inst_seq", "sq_idx", "lq_idx", "request_id")),
          str(req))
    check("load-side seq required (dyn_inst_seq)",
          req is not None and "dyn_inst_seq" in req, str(req))
    check("legacy keys still required",
          req is not None and all(f in req for f in (
              "fault_id", "va", "field", "before", "after")), str(req))

    print("[2] 注册表双源一致（新字段必须进注册表——发射端丢弃 unknown key）")
    hh = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/"
          "CHAOSPropagation.hh").read_text()
    begin = hh.index("PROP_EVT_FIELDS[] = {")
    end = hh.index("};", begin)
    import re
    cpp_fields = re.findall(r'"([a-z_0-9]+)"', hh[begin:end])
    check("store_dyn_inst_seq in both registries",
          "store_dyn_inst_seq" in P.PROP_EVT_FIELDS
          and "store_dyn_inst_seq" in cpp_fields)
    check("corr in both registries",
          "corr" in P.PROP_EVT_FIELDS and "corr" in cpp_fields)
    check("python registry == cpp registry (same name same order)",
          P.PROP_EVT_FIELDS == cpp_fields,
          f"py len={len(P.PROP_EVT_FIELDS)} cpp len={len(cpp_fields)}")

    print("[3] 契约行校验（validate_event）")
    good = P.parse_line(
        "PROP-EVT: kind=lsq_fwd fault_id=1 dyn_inst_seq=207 "
        "store_dyn_inst_seq=133 sq_idx=4 lq_idx=3 request_id=207 "
        "va=7fff12a0 field=bit_flip before=store_data "
        "after=fwd_corrupt:bit_flip corr=seq_primary")
    check("complete seq_primary lsq_fwd validates",
          good is not None and P.validate_event(good) == [],
          str(P.validate_event(good)) if good else "parse None")
    bad = P.parse_line(
        "PROP-EVT: kind=lsq_fwd fault_id=1 va=7fff12a0 field=bit_flip "
        "before=store_data after=fwd_corrupt:bit_flip")
    errs = P.validate_event(bad) if bad else ["parse None"]
    check("missing seq/idx keys flagged (no silent address-only)",
          len(errs) >= 5, str(errs))
    fb = P.parse_line(
        "PROP-EVT: kind=lsq_fwd fault_id=1 dyn_inst_seq=207 "
        "store_dyn_inst_seq=133 sq_idx=4 lq_idx=3 request_id=207 "
        "va=7fff12a0 field=bit_flip before=store_data "
        "after=fwd_corrupt:bit_flip corr=addr_fallback")
    check("addr_fallback marker round-trips",
          fb is not None and fb.get("corr") == "addr_fallback",
          str(fb.get("corr")) if fb else "parse None")

    print("[4] join 面：sq_idx/lq_idx 字段名与 sq_*/lq_read 事件同源")
    sq_wb = P.REQUIRED_FIELDS.get("sq_writeback")
    sq_cp = P.REQUIRED_FIELDS.get("sq_complete")
    lq_rd = P.REQUIRED_FIELDS.get("lq_read")
    check("sq_writeback/sq_complete carry dyn_inst_seq+sq_idx",
          all(r is not None and "dyn_inst_seq" in r and "sq_idx" in r
              for r in (sq_wb, sq_cp)))
    check("lq_read carries dyn_inst_seq+lq_idx",
          lq_rd is not None and "dyn_inst_seq" in lq_rd
          and "lq_idx" in lq_rd)
    # 生产 store 的 sq_writeback/sq_complete 以 store seq 为 dyn_inst_seq，
    # 与 lsq_fwd.store_dyn_inst_seq 同一指令 → 字段面可 join（真机逐边
    # 记录见 docs/gem5-fi/lsu/mdspec/round4_findings.md §1.5）
    chain = [
        P.parse_line("PROP-EVT: kind=inj fault_id=1 event_id=0"),
        good,
        P.parse_line("PROP-EVT: kind=sq_writeback fault_id=1 "
                     "dyn_inst_seq=133 sq_idx=4 event_id=2"),
        P.parse_line("PROP-EVT: kind=sq_complete fault_id=1 "
                     "dyn_inst_seq=133 sq_idx=4 event_id=3"),
    ]
    v = P.provable_to(chain)
    check("inj→lsq_fwd→sq_writeback→sq_complete reaches L3",
          v["provable_to"] == "L3", str(v))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
