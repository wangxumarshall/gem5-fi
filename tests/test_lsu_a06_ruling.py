#!/usr/bin/env python3
"""test_lsu_a06_ruling.py — [MDSPEC][A6] A06 安全化改造验证（计划 §2 裁决）。

用户指令二.3：不得把 A06 静默替换成 A06S；Markdown 定义 A06（无 A06S）；
若只能 store-only，A06 相关 RunID 必须标 BLOCKED，不得伪装完成、不得私改模型ID。
裁决落地形态：模式名回归规格（a06_size 承载 store-only 安全路径 + load 候选
REJECT 日志）；a06s_store_size 成为被拒别名；campaign 删 A06S 条目、A06 标
BLOCKED（load 侧 + byte-enable 待 §2.c spike 后解除）。
用法：python3 tests/test_lsu_a06_ruling.py   （退出码 0=全 PASS）
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_campaign as lc   # noqa: E402

GEM5 = ROOT / "CHAOS" / "gem5" / "build" / "ARM" / "gem5.opt"
PROXY = ROOT / "configs" / "se" / "lsu_proxy.py"
WL = ROOT / "workloads" / "directed" / "sq_forward"


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name + ("   <- " + detail if not cond else ""))
        if not cond:
            fails.append(name)

    # ---- 1) 规格模型名承载安全路径 + BLOCKED 标记（二.3.d） ----
    family, extra = lc.MODEL_FLAGS["A06"]
    check("a06_mode_name_is_spec_legal",
          family == "addrpath" and "--agu_pre_mode" in extra
          and "a06_size" in extra,
          f"family={family} extra={extra}")
    check("a06_runids_blocked", "A06" in lc.MODEL_BLOCKED,
          f"MODEL_BLOCKED keys={sorted(lc.MODEL_BLOCKED)[:12]}")
    check("a06_blocked_reason_mentions_loadside",
          "load" in str(lc.MODEL_BLOCKED.get("A06", "")).lower(),
          str(lc.MODEL_BLOCKED.get("A06"))[:120])

    # ---- 2) 无 A06S 模型 ID 泄入（二.3：不得私改模型ID） ----
    check("a06s_model_id_absent",
          not any(m.startswith("A06S") for m in lc.MODEL_FLAGS)
          and not any(m.startswith("A06S") for m in lc.MODEL_BLOCKED),
          f"A06S in flags={any(m.startswith('A06S') for m in lc.MODEL_FLAGS)}")

    # ---- 3) 旧别名 config-time 被拒（83ff9265 拒绝逻辑反转到 a06s_store_size） ----
    r = subprocess.run(
        [str(GEM5), "--outdir=/tmp/mdspec_a6_rej", str(PROXY),
         "--cmd", str(WL), "--cpu", "O3", "--chaos_addrpath",
         "--agu_pre_mode", "a06s_store_size", "--agu_size_to", "2"],
        capture_output=True, text=True, timeout=300)
    check("a06s_alias_rejected_at_config",
          r.returncode != 0 and "a06s_store_size" in (r.stdout + r.stderr)
          and "invalid choice" in (r.stdout + r.stderr),
          f"rc={r.returncode}")

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
