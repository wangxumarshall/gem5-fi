#!/usr/bin/env python3
"""test_lsu_hook_sq.py — [MDSPEC][H3] SQ 生命周期钩子契约测试。

规格（表 9 缺失钩子列，63 RunID）：
"src/cpu/o3/lsq_unit.cc insertStore/executeStore/checkViolations/
writebackStores/commit-drain — SQ 逐事件 + state_before/after"

契约：
- kind=sq_execute（L3）: executeStore 入口——fault_id/dyn_inst_seq/sq_idx/
  va/state_before（=issued）
- kind=sq_complete（L3）: completeStore（store 排放完成，SQ entry 释放）
  ——fault_id/dyn_inst_seq/sq_idx/va/state_after（=completed）
- 关联：correlateRequestBySeq（dyn-seq）；va 取注册表 base
- insertStore 在 dispatch 期早于注入注册（结构性缺席，同 H7 lq_insert
  裁决）；checkViolations 路径由 CHAOSLSQFwd 既有 violationCorrupt 承载。

用法：python3 tests/test_lsu_hook_sq.py   （退出码 0=全 PASS）
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
    print("[1] H3 kind→层级与必录字段注册")
    check("sq_execute -> L3", P.KIND_LAYER.get("sq_execute") == "L3",
          str(P.KIND_LAYER.get("sq_execute")))
    check("sq_complete -> L3", P.KIND_LAYER.get("sq_complete") == "L3",
          str(P.KIND_LAYER.get("sq_complete")))
    req_e = P.REQUIRED_FIELDS.get("sq_execute")
    req_c = P.REQUIRED_FIELDS.get("sq_complete")
    check("sq_execute required fields",
          req_e is not None
          and all(f in req_e for f in ("fault_id", "dyn_inst_seq", "sq_idx",
                                       "va", "state_before")))
    check("sq_complete required fields",
          req_c is not None
          and all(f in req_c for f in ("fault_id", "dyn_inst_seq", "sq_idx",
                                       "va", "state_after")))

    print("[2] 契约行校验")
    good_e = P.parse_line(
        "PROP-EVT: kind=sq_execute fault_id=1 dyn_inst_seq=133 sq_idx=22 "
        "va=7fbff state_before=issued")
    check("complete sq_execute validates",
          good_e is not None and P.validate_event(good_e) == [])
    good_c = P.parse_line(
        "PROP-EVT: kind=sq_complete fault_id=1 dyn_inst_seq=133 sq_idx=22 "
        "va=7fbff state_after=completed")
    check("complete sq_complete validates",
          good_c is not None and P.validate_event(good_c) == [])
    bad = P.parse_line("PROP-EVT: kind=sq_execute fault_id=1 dyn_inst_seq=1")
    errs = P.validate_event(bad)
    check("missing sq_idx/va/state_before flagged", len(errs) == 3, str(errs))

    print("[3] store 链推进（a04 全链含 sq 对）")
    chain = [P.parse_line(l) for l in [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=10",
        "PROP-EVT: kind=addr_form fault_id=1 event_id=1 tick=10",
        "PROP-EVT: kind=lsq_push fault_id=1 event_id=2 tick=11 "
        "dyn_inst_seq=133",
        "PROP-EVT: kind=lsq_sendfrag fault_id=1 event_id=3 tick=12 "
        "dyn_inst_seq=133",
        "PROP-EVT: kind=sq_execute fault_id=1 event_id=4 tick=15 "
        "dyn_inst_seq=133 sq_idx=22 va=7fbff state_before=issued",
        "PROP-EVT: kind=sq_complete fault_id=1 event_id=5 tick=30 "
        "dyn_inst_seq=133 sq_idx=22 va=7fbff state_after=completed",
        "PROP-EVT: kind=errant_commit fault_id=1 event_id=6 tick=40",
    ]]
    import lsu_chain_check as CC  # noqa: E402（tools/ 已在 sys.path）
    v = CC.check_chain(chain)
    f1 = v["faults"]["1"]
    check("store 链 L0→L4 全边 proven → full（含 sq_execute/complete）",
          f1["terminal"] == "full",
          f"{f1['terminal']} edges={ {k: v2 for k, v2 in f1['edges'].items() if not k.endswith('_witness')} }")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
