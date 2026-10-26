#!/usr/bin/env python3
"""test_lsu_hook_lsq.py — [MDSPEC][H1] lsq.cc 统一事件钩子契约测试。

规格（表 9 缺失钩子列，39 RunID 共文）：
"在 src/cpu/o3/lsq.cc::pushRequest 与 LSQRequest::sendFragmentToTranslation
增加统一事件；把 lq_idx/sq_idx、PC/opcode、VA/PA、event_id/parent_event_id
写入 CHAOSPropagation"

契约：
- kind=lsq_push   → L1（EA/size/flags 进入 LSQRequest；pushRequest 入口）
- kind=lsq_sendfrag → L2（请求离开 LSQ 去翻译/访存；sendFragmentToTranslation）
- 必录字段（H1 家族，规格表 9 L1/L2 列）：
  lsq_push:    dyn_inst_seq, pc, opcode, lq_idx, sq_idx, va（fault_id 关联链）
  lsq_sendfrag: dyn_inst_seq, pc, opcode, request_id, va
- 发射端只对 fault-correlated 请求发射（ptag 链关联，量级可控）；
  fault_id 必须非 0（观测流 = 故障传播流，规格 11 语义）。

用法：python3 tests/test_lsu_hook_lsq.py   （退出码 0=全 PASS）
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
    print("[1] H1 kind→层级与必录字段注册（lsu_prop_fields）")
    check("lsq_push -> L1", P.KIND_LAYER.get("lsq_push") == "L1",
          str(P.KIND_LAYER.get("lsq_push")))
    check("lsq_sendfrag -> L2", P.KIND_LAYER.get("lsq_sendfrag") == "L2",
          str(P.KIND_LAYER.get("lsq_sendfrag")))
    req_push = P.REQUIRED_FIELDS.get("lsq_push")
    req_frag = P.REQUIRED_FIELDS.get("lsq_sendfrag")
    check("lsq_push required fields",
          req_push is not None
          and all(f in req_push for f in ("dyn_inst_seq", "pc", "opcode",
                                          "lq_idx", "sq_idx", "va", "fault_id")))
    check("lsq_sendfrag required fields",
          req_frag is not None
          and all(f in req_frag for f in ("dyn_inst_seq", "pc", "opcode",
                                          "request_id", "va", "fault_id")))

    print("[2] 契约行校验（validate_event）")
    good_push = P.parse_line(
        "PROP-EVT: kind=lsq_push fault_id=1 dyn_inst_seq=42 pc=4096 "
        "opcode=ldr lq_idx=3 sq_idx=-1 va=1ffff70 corr=seq_primary "
        "sample_run_id=0")
    check("complete lsq_push validates",
          good_push is not None and P.validate_event(good_push) == [])
    bad_push = P.parse_line(
        "PROP-EVT: kind=lsq_push fault_id=1 dyn_inst_seq=42")
    errs = P.validate_event(bad_push)
    check("missing pc/opcode/lq_idx/sq_idx/va/corr flagged",
          len(errs) >= 6, str(errs))
    good_frag = P.parse_line(
        "PROP-EVT: kind=lsq_sendfrag fault_id=1 dyn_inst_seq=42 pc=4096 "
        "opcode=ldr request_id=42 va=1ffff70 corr=seq_primary")
    check("complete lsq_sendfrag validates",
          good_frag is not None and P.validate_event(good_frag) == [])

    print("[3] fault_id 非 0（传播流语义）+ 层级推进")
    check("correlated event has fault_id != 0",
          good_push["fault_id"] == "1")
    chain = [P.parse_line("PROP-EVT: kind=inj fault_id=1 event_id=0"),
             good_push, good_frag,
             P.parse_line("PROP-EVT: kind=resp fault_id=1")]
    v = P.provable_to(chain)
    check("inj→lsq_push→lsq_sendfrag→resp chain reaches L3",
          v["provable_to"] == "L3", str(v))

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
