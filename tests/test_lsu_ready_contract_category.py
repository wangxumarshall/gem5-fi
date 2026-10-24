#!/usr/bin/env python3
"""[LSU][MDSPEC][R4-8-SPEC] READY 契约的互斥类别分类：显式判据 + 兜底报警钉扎。

背景（本轮实测）：`lsu_ready_contract._classify` 原来用 `else: cat = "RULING"`
兜底。R4-5.9 把 `MODEL_BLOCKED["T08"]` 的文案从
"deferred(mode unimplemented: walk pairing)" 改成
"landed compile-unverified, pilot pending" 之后，T08-F{0,4,6}-W9 的类别就
**静默**从 MODE-UNIMPL 变成 RULING（RULING 6→9）—— 没有任何工具出声。
本测试把"类别判据显式 + 未知理由必须响亮"钉死：

  [1] 分类普查与证据文件登记值逐字一致（RULING=6 只含 A06；MODE-UNIMPL=3 只含 T08-W9）；
  [2] 没有一行落进兜底类别 UNCLASSIFIED（= 没有静默未知）；
  [3] AS-IS 的具体归属：A06→RULING、T08-*-W9→MODE-UNIMPL、W11 12 行→LICENSE。

用法：python3 tests/test_lsu_ready_contract_category.py   （退出码 0=全 PASS）
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_ready_contract as RC   # noqa: E402

XLSX = ROOT / "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"

# [R4-8-INT] 合并后重钉：PLATFORM-DEFECT 0（S10 平台缺陷修复 + F0 真机解锁）、
# UNRESOLVED 19→4（W1/MiBench 过宽阻塞订正 + S10-F2 转精确拒绝）、
# MODE-UNIMPL 保持 3（T08-W9，理由已改实测但仍属子模型模式未实现）。
# [R6-GATE] 追加链准入门禁：本测试以 `pilots={}`（无链证据）构建，故原 241 行
# READY 全部降为 BLOCKED/CHAIN-EVIDENCE-MISSING —— READY 不再仅凭 coverage
# PASS 得出，须真链准入。原 84 阻塞行分类不变。
# [MDSPEC][R6-FTIER] 追加具名类别 TIER-UNIMPL：armtlb lookup 路径无法表达
# F1-F6（TLB::lookup 不 poll lsuTrigger），resolve_cell 响亮拒绝这些格。
# [MDSPEC][R6-FIXTOOLS] 该 C++ 缺口已由 6ec7c5aa 补齐（lookupTierMounted /
# lookupTierAllowsInjection），工具侧 F1-F6 现产出真实 `--tlb_lsu_tier`：原
# 6 行（T01-F1/F2-W1、T02-F2-W1、T03-F5-W9、T10-F1/F2-W1）不再落 TIER-UNIMPL
# （类别消失）而回到链门禁（无样本）——CHAIN-EVIDENCE-MISSING 235 → 241。
# TIER-UNIMPL 现只在**未知**档位（F7/off）时出现，325 行内无此格。
EXPECTED = {"RULING": 6, "FS-INFRA": 24, "MODE-UNIMPL": 3, "UNRESOLVED": 4,
            "FS-MULTICORE": 35, "LICENSE": 12,
            "CHAIN-EVIDENCE-MISSING": 241}


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name +
              ("   <- " + detail if not cond else ""))
        if not cond:
            fails.append(name)

    tmp = Path(tempfile.mkdtemp(prefix="r4_8_contract_"))
    fresh = tmp / "map.json"
    subprocess.run([sys.executable, str(ROOT / "tools/lsu_runid_map.py"),
                    "--xlsx", str(XLSX), "--out", str(fresh)],
                   check=True, capture_output=True, text=True)
    rows = RC.build_contract(str(fresh), str(RC.DEFAULT_MATRIX),
                             str(RC.MDS / "coverage_matrix.md"), pilots={})
    from collections import Counter
    cats = Counter(r["category"] for r in rows if r["status"] == "BLOCKED")
    st = Counter(r["status"] for r in rows)

    check("total_325", len(rows) == 325, f"n={len(rows)}")
    check("category_census_matches_evidence", dict(cats) == EXPECTED,
          str(dict(cats)))
    check("no_unclassified_fallthrough", cats.get("UNCLASSIFIED", 0) == 0,
          "有理由语句落进兜底 UNCLASSIFIED —— 分类器需补显式判据")
    # [R6-GATE] 无链证据时不得有任何行 READY（硬门生效）
    check("no_ready_without_chain_evidence",
          st["READY"] == 0 and st["BLOCKED"] == 325 and st["PARTIAL"] == 0,
          str(dict(st)))

    def cat_of(rid):
        return next(r["category"] for r in rows if r["run_id"] == rid)

    a06 = [r for r in rows if r["model"] == "A06"]
    check("a06_is_ruling_6", len(a06) == 6
          and all(r["category"] == "RULING" for r in a06),
          str([(r["run_id"], r["category"]) for r in a06]))
    t08w9 = ["T08-F0-W9", "T08-F4-W9", "T08-F6-W9"]
    check("t08_w9_is_mode_unimpl_3",
          all(cat_of(r) == "MODE-UNIMPL" for r in t08w9),
          str([(r, cat_of(r)) for r in t08w9]))
    w11 = [r["run_id"] for r in rows if r["run_id"].endswith("-W11")]
    check("w11_is_license_12",
          len(w11) == 12 and all(cat_of(r) == "LICENSE" for r in w11),
          str([(r, cat_of(r)) for r in w11]))
    # 类别互斥定义里 RULING 只应来自 A06（§2 裁决），不得被兜底的 T08 之类污染。
    ruling_ids = sorted(r["run_id"] for r in rows if r["category"] == "RULING")
    check("ruling_only_a06", ruling_ids == sorted(r["run_id"] for r in a06),
          str(ruling_ids))

    print()
    print("FAILURES: " + ("无" if not fails else ", ".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
