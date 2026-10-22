#!/usr/bin/env python3
"""契约测试：BLOCKED 台账（blocked_triage.md / blockers_for_approval.md）
必须与权威契约 ready_contract.json 同源、同数、同集合。

动机（R5-U4）：两个台账曾是手写/自带旧正则的产物，与契约严重漂移——
同一份数据三处总数（126 / 100 / 106），18 个 RunID 在台账里 BLOCKED 而在契约里
READY，且完全没有 UNRESOLVED 桶。用户据以裁决的台账因此陈旧 42 项。
CLAUDE.md「One classifier, no drift」：分类只能有一个来源。
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MDS = REPO / "docs/gem5-fi/lsu/mdspec"

fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {detail}"))
    if not cond:
        fails.append(name)


def main():
    doc = json.loads((MDS / "ready_contract.json").read_text(encoding="utf-8"))
    blocked = {r["run_id"] for r in doc["entries"] if r["status"] == "BLOCKED"}
    n_blocked = len(blocked)

    triage = (MDS / "blocked_triage.md").read_text(encoding="utf-8")
    appr = (MDS / "blockers_for_approval.md").read_text(encoding="utf-8")

    m = re.search(r"BLOCKED 总数：(\d+)", triage)
    check("triage_declares_total", bool(m), triage[:200])
    check("triage_total_matches_contract", m and int(m.group(1)) == n_blocked,
          f"台账 {m and m.group(1)} vs 契约 {n_blocked}")

    rows = set(re.findall(r"^\| ([A-Z]\d{2}-F\d-W\d+) \|", triage, re.M))
    check("triage_rows_match_contract_set", rows == blocked,
          f"对称差 {sorted(rows ^ blocked)[:8]}")

    check("triage_cites_contract_source", "ready_contract.json" in triage,
          "台账未标注分类来源")

    check("approval_total_matches_contract", bool(m), appr[:200])
    am = re.search(r"（(\d+) BLOCKED 中的不可自解项）", appr)
    check("approval_header_total", am and int(am.group(1)) == n_blocked,
          f"清单头 {am and am.group(1)} vs 契约 {n_blocked}")

    arows = set(re.findall(r"^\| ([A-Z]\d{2}-F\d-W\d+) \|", appr, re.M))
    check("approval_rows_subset_of_blocked", arows <= blocked,
          f"清单出现非 BLOCKED：{sorted(arows - blocked)[:8]}")
    # 可自行实现类（MODE-UNIMPL / HOOK-UNIMPL）不得出现在"需用户裁决"清单
    self_fixable = {r["run_id"] for r in doc["entries"]
                    if r["status"] == "BLOCKED"
                    and r.get("category") in ("MODE-UNIMPL", "HOOK-UNIMPL")}
    check("self_fixable_not_in_approval_list", not (arows & self_fixable),
          f"误入清单：{sorted(arows & self_fixable)[:8]}")
    check("approval_plus_self_fixable_is_all",
          arows | self_fixable == blocked,
          f"遗漏 {sorted(blocked - arows - self_fixable)[:8]}")

    print(f"\n{'ALL PASS' if not fails else 'FAILED (%d): %s' % (len(fails), fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
