#!/usr/bin/env python3
"""test_lsu_reclass_v2_adapt.py — [MDSPEC][A5.4] reclass_v2 证据门适配。

用户指令二.5：审核 guest_arch_fault/Timeout/SimFailure 分类规则——可复用逻辑，
但输出必须适配新版结果字段与 L0-L5 终止判定；不得用离线分类替代传播证据；
链路缺失必须标 Unknown（不得推断 Masked）。
evidence_gate 依据（真实 l5_verdict.json schema，runs/lsu/engineering 实测）：
injected/activated/outcome/checksum/crash_kind/gem5_exit——旧批次无 L0-L5
链事件（早于传播插桩），终局证据面只有 crash_kind/gem5_exit/checksum。
用法：python3 tests/test_lsu_reclass_v2_adapt.py   （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import lsu_reclass_v2 as C   # noqa: E402


def mk_verdict(injected=1, outcome="Masked", checksum=None,
               crash_kind=None, gem5_exit=0):
    return dict(injected=injected, activated=injected,
                injected_not_activated=0, checksum=checksum,
                outcome=outcome, crash_kind=crash_kind, gem5_exit=gem5_exit,
                classes="{}", detected_na=True, error=None)


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name + ("   <- " + detail if not cond else ""))
        if not cond:
            fails.append(name)

    # ---- 1) 用户二.5 核心：注入≥1 且 Masked 无 checksum 证据 → Unknown ----
    out, est = C.evidence_gate(mk_verdict(injected=1, outcome="Masked",
                                          checksum=None))
    check("missing_evidence_yields_unknown_not_masked",
          out == "Unknown" and est == "missing", f"out={out} est={est}")

    # 无 verdict 文件（防御路径）同样 Unknown/missing
    out2, est2 = C.evidence_gate(None)
    check("none_verdict_is_unknown_missing",
          out2 == "Unknown" and est2 == "missing", f"out={out2} est={est2}")

    # ---- 2) 终局直接证据 → observed，原判保持 ----
    out3, est3 = C.evidence_gate(mk_verdict(outcome="Crash",
                                            crash_kind="guest_page_fault",
                                            gem5_exit=-6))
    check("crash_evidence_observed", out3 == "Crash" and est3 == "observed",
          f"out={out3} est={est3}")
    out4, est4 = C.evidence_gate(mk_verdict(outcome="Timeout", gem5_exit=-15))
    check("timeout_evidence_observed", out4 == "Timeout" and est4 == "observed",
          f"out={out4} est={est4}")
    out5, est5 = C.evidence_gate(mk_verdict(outcome="Masked",
                                            checksum="deadbeef"))
    check("checksum_evidence_observed_masked_stands",
          out5 == "Masked" and est5 == "observed", f"out={out5} est={est5}")

    # ---- 3) 未注入 → 原样（Injected-not-activated 记账，非 Unknown） ----
    out6, est6 = C.evidence_gate(mk_verdict(injected=0, outcome="Masked"))
    check("not_injected_passthrough",
          est6 == "not_injected", f"out={out6} est={est6}")

    # ---- 4) 版本化 + 只读：reclassify 的 move 记录字段齐全 ----
    check("gate_version_present", C.EVIDENCE_GATE_VERSION == "mdspec-1",
          f"got {C.EVIDENCE_GATE_VERSION!r}")
    v = mk_verdict(outcome="Crash", crash_kind="simulator_assert", gem5_exit=-6)
    sample = dict(sample="sX_test", verdict=v, sig="pt", exit_code=-6,
                  fatal="Page table fault when accessing virtual address",
                  bucket=C.v1_bucket(v), guard="runs/x/_sX_guard.out")
    moves, agg, sig_cols, exit_cols, diag = C.reclassify([sample])
    check("reclass_move_carries_version_and_evidence",
          len(moves) == 1 and moves[0]["rule_id"] == "R2.1"
          and moves[0]["rule_version"] == C.RULE_VERSION
          and moves[0]["evidence"] == sample["guard"]
          and moves[0]["orig"] == "simfail" and moves[0]["new"] == "five:Crash",
          str(moves[:1]))

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
