#!/usr/bin/env python3
"""R6-S-REPAIR2 文档审计：33 份 seed 文档与各自原始流逐字段一致。

检查：
  1. 每份文档恰好八个一级章节；
  2. 事件总览表行数/event_id/kind/parent/tick 与 prop_evt 逐条一致；
  3. 文档第 7 章列出的每个证据路径 SHA-256 与实际文件一致；
  4. S11-F0-W6 没有文档（不可归因，不得伪造）；
  5. 不存在顶层 seed 文档；S 文档总数为 65。

用法：python3 tests/test_lsu_s_repair2_docs.py   退出码 0=全 PASS。
"""
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import r6_s_repair2_prop_docs as G  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    for rid in G.RIDS:
        for seed in G.SEEDS:
            rec = G.load(rid, seed)
            docp = G.OUT / rid / f"{rid}-seed{seed}.md"
            check(f"{rid} s{seed} qualified", rec.get("qualified"),
                  rec.get("error") or "not qualified")
            check(f"{rid} s{seed} doc exists", docp.exists(), docp)
            if not docp.exists():
                continue
            text = docp.read_text()
            heads = re.findall(r"^## \d+\.", text, re.M)
            check(f"{rid} s{seed} eight chapters", len(heads) == 8, len(heads))

            # Event table rows: start with '| ' and have numeric first cell.
            rows = []
            for line in text.splitlines():
                if not line.startswith("| "):
                    continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                if cells and cells[0].isdigit():
                    rows.append(cells)
            evs = rec["cev"]
            check(f"{rid} s{seed} table rows == events",
                  len(rows) == len(evs), (len(rows), len(evs)))
            for cells, e in zip(rows, evs):
                ok = (cells[0] == str(e.get("event_id", ""))
                      and cells[1] == e.get("kind", "")
                      and cells[3] == (e.get("parent_event_id") or "—")
                      and cells[4] == e.get("tick", ""))
                if not ok:
                    check(f"{rid} s{seed} row {cells[0]} matches event", False,
                          (cells[:5], e.get("event_id"), e.get("kind"),
                           e.get("parent_event_id"), e.get("tick")))
                    break
            else:
                check(f"{rid} s{seed} all table rows match events", True)

            # Evidence SHA lines.
            sha_lines = re.findall(r"^- `([^`]+)`：`([0-9a-f]{64})`$",
                                   text, re.M)
            check(f"{rid} s{seed} has evidence SHAs", bool(sha_lines),
                  len(sha_lines))
            for p, digest in sha_lines:
                path = Path(p)
                check(f"{rid} s{seed} evidence exists {path.name}",
                      path.exists(), path)
                if path.exists():
                    check(f"{rid} s{seed} SHA {path.name}",
                          sha(path) == digest, (sha(path), digest))

    # S11-F0-W6 must not have a fabricated doc.
    check("S11-F0-W6 has no propagation doc",
          not list(G.OUT.glob("S11-F0-W6/*.md")))
    check("no top-level seed docs",
          not list(G.OUT.glob("*seed*.md")))
    sdocs = [p for p in G.OUT.glob("S*-*/*-seed*.md")]
    check("65 S seed docs", len(sdocs) == 65, len(sdocs))

    print(f"FAILED: {len(FAILED)}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
