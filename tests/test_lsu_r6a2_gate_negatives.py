#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A2] 终局门禁组合负向测试。

新增真实终局事件（arch_translation_fault / squash_discarded /
store_not_retired）不得成为绕过既有门禁的后门。本测试用**真实解析器**
（lsu_prop_fields.parse_line）+ **真实门禁函数**（lsu_chain_check）钉死：

  N1 truncated 流不能产出 containment；
  N2 open chain（有 inj 但无终局）不能产出 containment；
  N3 仅有 chain_end（哪怕 contained=1）不能当 L5；
  N4 未知终局不能通过；
  N5 新事件也必须 corr 可关联、前缀可证；corr=none 或跨祖先一律拒绝；
  N6 新事件本身在没有 L0→L1 前缀时不能收口。

用法：python3 tests/test_lsu_r6a2_gate_negatives.py （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_chain_check as C  # noqa: E402
import lsu_prop_fields as P  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def evt(**kw):
    base = dict(run_id="X", sample_run_id="s1", fault_id="1",
                parent_event_id="", tick="1", detection_layer="",
                contained="", outcome="", corr="", field="")
    base.update(kw)
    line = "PROP-EVT: " + " ".join(f"{k}={v}" for k, v in base.items())
    return P.parse_line(line)


def prefix():
    return [
        evt(kind="inj", event_id="0", corr="origin", tick="1"),
        evt(kind="addr_form", event_id="1", parent_event_id="0",
            corr="origin", tick="2"),
    ]


def main():
    print("[N1] truncated 流不能产出 containment")
    arch = evt(kind="arch_translation_fault", event_id="2",
               parent_event_id="1", detection_layer="L2", contained="1",
               outcome="arch_exception", corr="seq_primary", tick="3")
    check("truncated=True -> None",
          C.containment_from_events(prefix() + [arch], run_id="X",
                                    truncated=True) is None)

    print("[N2] open chain 不能产出 containment")
    check("只有 L0/L1 -> None",
          C.containment_from_events(prefix(), run_id="X") is None)
    r = C.check_chain(prefix())
    check("open chain terminal 不是 detected_contained",
          r["faults"]["1"]["terminal"] != "detected_contained",
          str(r["faults"]["1"]["terminal"]))

    print("[N3] 仅 chain_end（contained=1）不能当 L5")
    ce = evt(kind="chain_end", event_id="2", parent_event_id="1",
             detection_layer="L4", contained="1",
             outcome="detected_contained", corr="none", tick="3")
    check("_explicit_l5(chain_end) is False", C._explicit_l5(ce) is False)
    check("chain_end-only -> None",
          C.containment_from_events(prefix() + [ce], run_id="X") is None)
    r = C.check_chain(prefix() + [ce])
    check("chain_end-only terminal 非 detected_contained",
          r["faults"]["1"]["terminal"] != "detected_contained",
          str(r["faults"]["1"]["terminal"]))

    print("[N4] 未知终局不能通过")
    unk = evt(kind="resp", event_id="2", parent_event_id="1",
              detection_layer="L3", contained="", outcome="", corr="seq_primary",
              tick="3")
    check("未知终局 -> None",
          C.containment_from_events(prefix() + [unk], run_id="X") is None)

    print("[N5] 新事件必须 corr 可关联且前缀可证")
    arch_nocorr = dict(arch)
    arch_nocorr["corr"] = "none"
    check("arch corr=none -> None",
          C.containment_from_events(prefix() + [arch_nocorr], run_id="X")
          is None)
    arch_orphan = evt(kind="arch_translation_fault", event_id="9",
                      parent_event_id="", detection_layer="L2", contained="1",
                      outcome="arch_exception", corr="seq_primary", tick="3")
    check("arch 无 L0→L1 前缀 -> None",
          C.containment_from_events([arch_orphan], run_id="X") is None)

    squash_nocorr = evt(kind="squash_discarded", event_id="2",
                        parent_event_id="1", detection_layer="L4",
                        contained="1", outcome="contained", corr="none",
                        tick="3")
    check("squash corr=none -> None",
          C.containment_from_events(prefix() + [squash_nocorr], run_id="X")
          is None)
    snr_empty_layer = evt(kind="store_not_retired", event_id="2",
                          parent_event_id="1", detection_layer="",
                          contained="1", outcome="contained",
                          corr="taint_prop", tick="3")
    check("store_not_retired 无 detection_layer -> None",
          C.containment_from_events(prefix() + [snr_empty_layer], run_id="X")
          is None)

    print("[N6] 合法新事件仍能收口（正对照，防测试只会拒绝）")
    deep = prefix() + [
        evt(kind="mem_req", event_id="2", parent_event_id="1",
            corr="seq_primary", tick="3"),
        evt(kind="sq_execute", event_id="3", parent_event_id="2",
            corr="seq_primary", tick="4"),
    ]
    sq = evt(kind="squash_discarded", event_id="4", parent_event_id="3",
             detection_layer="L4", contained="1", outcome="contained",
             corr="seq_primary", tick="5")
    closed = evt(kind="chain_end", event_id="5", parent_event_id="4",
                 detection_layer="", contained="0", outcome="run_end",
                 corr="none", tick="6")
    c = C.containment_from_events(deep + [sq, closed], run_id="X")
    check("squash 合法 + 收口 -> L4 containment",
          c is not None and c["layer"] == "L4", str(c))

    if FAILED:
        print(f"R6-A2 GATE NEGATIVES: {len(FAILED)} FAILURE(S)")
        return 1
    print("R6-A2 GATE NEGATIVES: ALL PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
