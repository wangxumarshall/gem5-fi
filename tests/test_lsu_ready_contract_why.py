#!/usr/bin/env python3
"""契约测试：ready_contract.json 的 BLOCKED 行**不得**在 why 字段自报通过。

动机（R5-U5，实测缺陷）：`_classify` 在 `flags is None` 分支返回 `str(cov_status)`，
而 S01/S02-F0-W1、S10-F2-W5/W9 的 coverage 恰为 "PASS" —— 于是 4 条**被拒绝**的
行在 why 里写着 "PASS"。BLOCKED 行声称通过是误导性陈述，会被下游读者（含人）
误读为"该 RunID 已通过"。修复后 why 为 resolve_cell 的真实拒绝理由。

用法：python3 tests/test_lsu_ready_contract_why.py [contract.json]
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT = REPO / "docs/gem5-fi/lsu/mdspec/ready_contract.json"
# BLOCKED 行的 why 不得是"通过类"字样（大小写不敏感、允许包裹空格）
PASS_TOKENS = {"pass", "ok", "ready", "succeeded", "success", "通过"}

fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {detail}"))
    if not cond:
        fails.append(name)


def main(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    blocked = [r for r in doc["entries"] if r["status"] == "BLOCKED"]
    check("has_blocked_rows", len(blocked) > 0, f"{len(blocked)}")

    bad = [r["run_id"] for r in blocked
           if (r.get("why") or "").strip().lower() in PASS_TOKENS]
    check("no_blocked_row_claims_pass", not bad, f"自报通过：{bad}")

    empty = [r["run_id"] for r in blocked if not (r.get("why") or "").strip()]
    check("every_blocked_row_has_reason", not empty, f"无理由：{empty}")

    # 未被拒绝的行才允许空 why
    nonblocked_bad = [r["run_id"] for r in doc["entries"]
                      if r["status"] != "BLOCKED" and (r.get("why") or "").strip()
                      and r["status"] == "READY"]
    check("ready_rows_have_empty_why", not nonblocked_bad, f"{nonblocked_bad[:5]}")

    print(f"\n{'ALL PASS' if not fails else 'FAILED (%d): %s' % (len(fails), fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT))
