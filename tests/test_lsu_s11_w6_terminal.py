#!/usr/bin/env python3
"""S11-F0-W6：下游野指针 Crash 必须有真实归因桥，否则不得准入。

实证（r6_s_unit_r3/S11-F0-W6_s1 + 2026-10-30 LSQUnit 探针）：
  * 注入 store 在 tick 6,194,650 执行，Size=0（请求未形成）；
  * 之后没有任何 load 访问注入地址 0x4903e8（完整 LSQ 轨迹 0 命中）；
  * tick 7,638,015 的崩溃是独立的 downstream-unmapped 0x18 page-table
    fault，run.err 明确打印 downstream-unmapped，prop_evt 无
    arch_translation_fault。
因此 oracle=Crash 是真实 guest 结局，但链不可归因到该 store；不得用
crash_translation_fault 或任意 Crash 放行。

本测试钉死：W6 形状的链不产生 crash_translation_fault、不准入；只有真实
delivered 的 arch_translation_fault（exact 注入地址）才可走严格终局。

用法：python3 tests/test_lsu_s11_w6_terminal.py   退出码 0=全 PASS。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P   # noqa: E402
import lsu_chain_check as CC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def ev(kind, eid, parent, tick, **kw):
    d = {
        "kind": kind, "fault_id": "1", "event_id": str(eid),
        "parent_event_id": "" if parent is None else str(parent),
        "tick": str(tick), "cycle": "0", "dyn_inst_seq": "4055",
        "va": "4903e8", "corr": "origin", "field": "",
        "detection_layer": "", "contained": "", "outcome": "",
        "before": "", "after": "", "state_before": "", "state_after": "",
        "sq_idx": "339", "request_id": "", "store_dyn_inst_seq": "",
        "phys_reg": "", "arch_reg": "",
    }
    d.update({k: str(v) for k, v in kw.items()})
    return d


def w6_events():
    return [
        ev("inj", 0, None, 6194650, field="size", before=8, after=0),
        ev("addr_form", 1, 0, 6194650, field="size"),
        ev("sq_execute", 2, 1, 6194650, sq_idx=339,
           state_before="issued", corr="seq_primary"),
        ev("sq_complete", 3, 2, 6203505, sq_idx=339,
           state_after="completed", corr="seq_primary"),
        ev("chain_end", 4, 3, 7638015, detection_layer="L5",
           contained="0", outcome="run_end", corr="none"),
    ]


def admit(events, oracle="Crash", rc=139):
    return CC.check_admission({
        "run_id": "S11-F0-W6", "activated": 1, "events": events, "rc": rc,
        "oracle_outcome": oracle,
        "containment": CC.containment_from_events(events, "S11-F0-W6"),
        "truncated": False,
    })


def main():
    print("[1] W6 shape: real Crash, but no attribution bridge")
    evs = w6_events()
    f = CC.check_chain(evs, oracle_outcome="Crash")["faults"]["1"]
    check("not crash_translation_fault",
          f["terminal"] != "crash_translation_fault", f["terminal"])
    check("provable_to L1 (the store chain never formed a request)",
          f["provable_to"] == "L1", f["provable_to"])
    r = admit(evs)
    check("W6 is not admitted", r["admitted"] is False,
          (r["admitted"], r["violations"]))
    check("no containment fabricated for W6",
          CC.containment_from_events(evs, "S11-F0-W6") is None)
    check("no arch_translation_fault present", all(
        e["kind"] != "arch_translation_fault" for e in evs))

    print("[2] an orphan translation event cannot forge attribution")
    orphan = evs[:-1] + [
        ev("arch_translation_fault", 4, 99, 7638015, va="18",
           detection_layer="L2", contained="0", outcome="arch_exception",
           corr="origin"),
        ev("chain_end", 5, 4, 7638015, detection_layer="L5",
           contained="0", outcome="run_end", corr="none")]
    r = admit(orphan)
    check("orphan arch_translation_fault is refused", r["admitted"] is False,
          (r["admitted"], r["violations"]))
    check("orphan/forged crash terminal is refused",
          any(("crash_terminal_not_in_ancestry" in v or
               "crash_terminal_missing" in v or
               "crash_terminal_no_injection" in v) for v in r["violations"]),
          r["violations"])

    print("[3] only a real delivered translation fault is the strict terminal")
    # The injected VA is 0x4903e8; a delivered fault on that exact VA with a
    # continuous L0..L3 ancestry is the admissible translation terminal.
    good = [
        ev("inj", 0, None, 100, field="size", before=8, after=0),
        ev("addr_form", 1, 0, 100, field="addr", va="4903e8"),
        ev("mem_req", 2, 1, 100, request_id="4055", corr="seq_primary"),
        ev("sq_execute", 3, 2, 100, sq_idx=339, state_before="issued",
           corr="seq_primary"),
        ev("arch_translation_fault", 4, 3, 110, va="4903e8",
           detection_layer="L2", contained="0", outcome="arch_exception",
           corr="seq_primary"),
        ev("chain_end", 5, 4, 120, detection_layer="L5", contained="0",
           outcome="run_end", corr="none")]
    f = CC.check_chain(good, oracle_outcome="Crash")["faults"]["1"]
    check("delivered exact-VA fault is crash_translation_fault",
          f["terminal"] == "crash_translation_fault", f["terminal"])
    check("provable_to L3", f["provable_to"] == "L3", f["provable_to"])

    print("[4] source contract: no VA registration on the S11 PRE path")
    addr = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc"
            ).read_text()
    block = addr[addr.index('pre_mode == "s11_store_lost"'):
                 addr.index('pre_mode == "s11_store_lost"') + 700]
    check("S11 lost-size path does not register the VA",
          "noteInjectedGuestVa" not in block)
    faults = (ROOT / "CHAOS/gem5/src/sim/faults.cc").read_text()
    check("faults.cc gates the terminal on the exact injected range",
          "consumeInjectedGuestVa(vaddr)" in faults
          and "noteArchTranslationFault(vaddr, exact)" in faults)
    check("downstream wild pointers stay unattributed",
          "downstream-unmapped" in faults)

    print(f"FAILED: {len(FAILED)}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
