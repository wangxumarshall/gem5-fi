#!/usr/bin/env python3
"""test_lsu_hook_lq.py — [MDSPEC][H7] LQ 逐事件钩子契约测试。

规格（表 9 H7）：src/cpu/o3/lsq_unit.cc insertLoad/read/checkViolations/
completeDataAccess 与 replay 的 lq_idx 生命周期。

契约（本提交覆盖 read/completeDataAccess 两个主生命周期点；insert 在
dispatch 期早于注入注册（PRE 族在 pushRequest 注入）——除 replay 外结构
性缺席，如实；checkViolations/replay 属 violation 路径，下一提交补）：
- kind=lq_read    → L3（load 的访存读发射；lsq_unit.cc read() 入口）
- kind=lq_complete→ L3（响应返回 LQ 表项；noteMemResponse 内，带 va/pa）
- 必录字段：
  lq_read:     fault_id, dyn_inst_seq, lq_idx, va
  lq_complete: fault_id, dyn_inst_seq, lq_idx, va, pa

用法：python3 tests/test_lsu_hook_lq.py   （退出码 0=全 PASS）
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
    print("[1] H7 kind→层级与必录字段注册")
    check("lq_read -> L3", P.KIND_LAYER.get("lq_read") == "L3",
          str(P.KIND_LAYER.get("lq_read")))
    check("lq_complete -> L3", P.KIND_LAYER.get("lq_complete") == "L3",
          str(P.KIND_LAYER.get("lq_complete")))
    rr = P.REQUIRED_FIELDS.get("lq_read")
    rc = P.REQUIRED_FIELDS.get("lq_complete")
    check("lq_read required",
          rr is not None and all(f in rr for f in
                                 ("fault_id", "dyn_inst_seq", "lq_idx", "va")))
    check("lq_complete required",
          rc is not None and all(f in rc for f in
                                 ("fault_id", "dyn_inst_seq", "lq_idx",
                                  "va", "pa")))

    print("[2] 契约行校验")
    good_r = P.parse_line("PROP-EVT: kind=lq_read fault_id=1 dyn_inst_seq=42 "
                          "lq_idx=3 va=1ffff70 corr=seq_primary")
    check("complete lq_read validates",
          good_r is not None and P.validate_event(good_r) == [])
    good_c = P.parse_line("PROP-EVT: kind=lq_complete fault_id=1 "
                          "dyn_inst_seq=42 lq_idx=3 va=1ffff70 pa=1ffff70 "
                          "corr=addr_fallback")
    check("complete lq_complete validates",
          good_c is not None and P.validate_event(good_c) == [])
    bad = P.parse_line("PROP-EVT: kind=lq_read fault_id=1 dyn_inst_seq=42")
    check("missing lq_idx/va/corr flagged", len(P.validate_event(bad)) == 3)

    print("[3] 链推进")
    chain = [P.parse_line("PROP-EVT: kind=%s fault_id=1 event_id=%d" % (k, i))
             for i, k in enumerate(["inj", "addr_form", "lsq_push",
                                    "lsq_sendfrag"])] + [good_r, good_c]
    v = P.provable_to(chain)
    check("full chain reaches L3", v["provable_to"] == "L3", str(v))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
