#!/usr/bin/env python3
"""test_lsu_f6_gate.py — [MDSPEC][A5] F6 单语义门禁（规格 F6 = 首次事件注入一次）。

用户指令二.4：正式运行只能使用并记录 early_stress 语义；steady_state 仅作
显式 opt-in 的独立扩展实验，不得与正式 F6 样本混合。
用法：python3 tests/test_lsu_f6_gate.py   （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name + ("   <- " + detail if not cond else ""))
        if not cond:
            fails.append(name)

    import lsu_campaign as lc

    # 规格 F6 语义 = early_stress（dd755d7e 实测：默认注入于事件首次出现）
    check("f6_default_mode_is_early_stress",
          getattr(lc, "F6_DEFAULT_MODE", None) == "early_stress",
          f"F6_DEFAULT_MODE={getattr(lc, 'F6_DEFAULT_MODE', '<缺失>')}")
    check("formal_gate_accepts_early_stress",
          lc.assert_formal_f6_mode("early_stress") is None,
          "early_stress 必须被正式 track 接受")
    try:
        lc.assert_formal_f6_mode("steady_state")
        check("formal_gate_rejects_steady_state", False,
              "steady_state 未被拒绝——将与正式 F6 样本混合，违反规格")
    except SystemExit:
        check("formal_gate_rejects_steady_state", True)

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
