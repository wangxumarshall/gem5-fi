#!/usr/bin/env python3
"""Add the R6-C (L1d Cache, 2026-11-02) seeds to the authoritative indexes.

Additive and reversible: every target file is backed up before it is
rewritten (a backup is never overwritten).  Refuses to run unless:
  * the evidence audit reports every discovered seed PASS, and
  * every audited seed has a deployed propagation document, and
  * --docs-audit-ok is given (doc audit reported 0 errors).

Usage:
  python3 tools/update_r6_c_indexes.py \
      --audit <R6C_EVIDENCE_AUDIT.jsonl> --docs-audit-ok [--dry-run]
"""
import argparse
import csv
import json
import os
import re
import shutil
import tempfile

DOCS = "/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS"
RESULTS = "/home/sdc/gem5-fi-ding/runs/lsu/RESULTS"
STAMP = "20261102-cunit"
UNIT = "C"
HEADING = "## R6-C（L1d Cache 单元）逐 seed 传播路径"
SECTION_MARK = "## R6-C-UNIT（2026-11-02）"


def atomic_write(path, text):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-cunit-", text=True)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def backup(path):
    b = f"{path}.bak-{STAMP}"
    if not os.path.exists(b):
        shutil.copy2(path, b)
    return b


def entry_from_audit(rec):
    return {
        "run_id": rec["run_id"], "seed": rec["seed"],
        "oracle_outcome": rec.get("oracle"),
        "terminal": rec.get("terminal"), "provable_to": rec.get("provable_to"),
        "admitted": rec.get("admitted"), "certified": rec.get("certified"),
        "truncated": rec.get("truncated"),
        "violations": rec.get("violations") or [],
        "doc": f"{rec['run_id']}/{rec['run_id']}-seed{rec['seed']}.md",
        "evidence_dir": rec["root"],
        "evidence_seed_dir": rec["seed_dir"],
        "binary_sha256": rec.get("binary_sha256"),
        "binary_source_head": rec.get("binary_source_head"),
        "analysis_tool_head": rec.get("analysis_tool_head"),
        "event_count": rec.get("event_count"),
        "fault_count": rec.get("fault_count"),
        "address_provenance": rec.get("address_provenance") or {},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True)
    ap.add_argument("--docs-audit-ok", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.docs_audit_ok:
        raise SystemExit("refusing: --docs-audit-ok not given (run the doc audit first)")

    recs = [json.loads(l) for l in open(args.audit)]
    bad = [r for r in recs if not r.get("pass")]
    if bad:
        raise SystemExit(f"refusing: {len(bad)} audited seeds FAIL: "
                         f"{[(r.get('run_id'), r.get('seed')) for r in bad[:5]]}")
    missing = [r for r in recs if not os.path.isfile(
        os.path.join(DOCS, r["run_id"], f"{r['run_id']}-seed{r['seed']}.md"))]
    if missing:
        raise SystemExit(f"refusing: {len(missing)} docs not deployed")

    entries = [entry_from_audit(r) for r in recs]
    entries.sort(key=lambda e: (e["run_id"], e["seed"]))
    by_run = {}
    for e in entries:
        by_run.setdefault(e["run_id"], set()).add(e["seed"])
    complete = sorted(k for k, v in by_run.items() if {1, 2, 3} <= v)
    print(f"entries={len(entries)} runids={len(by_run)} complete3={len(complete)}")
    if len(by_run) != 31:
        raise SystemExit(f"refusing: expected 31 C RunIDs, got {len(by_run)}")

    if args.dry_run:
        for e in entries:
            print("WOULD", e["run_id"], e["seed"], e["oracle_outcome"],
                  e["terminal"], e["provable_to"])
        print("DRY-RUN: no files written")
        return

    # 1) EVIDENCE symlinks
    for e in entries:
        d = os.path.join(RESULTS, "EVIDENCE", e["run_id"])
        os.makedirs(d, exist_ok=True)
        link = os.path.join(d, f"seed{e['seed']}")
        if os.path.islink(link) or os.path.exists(link):
            real = os.path.realpath(link)
            if real != os.path.realpath(e["evidence_seed_dir"]):
                print("EXISTS (left unchanged):", link, "->", real)
            continue
        os.symlink(os.path.relpath(e["evidence_seed_dir"], d), link)
        assert os.path.isdir(os.path.realpath(link)), link

    # 2) CATALOG.tsv
    cat = os.path.join(RESULTS, "CATALOG.tsv")
    backup(cat)
    with open(cat, newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    header, body = rows[0], rows[1:]
    for e in entries:
        body = [r for r in body if not (r[0] == UNIT and r[1] == e["run_id"]
                                        and r[2] == str(e["seed"]))]
        note = (f"provable_to={e['provable_to']}; terminal={e['terminal']}; "
                f"oracle={e['oracle_outcome']}; faults={e['fault_count']}; "
                f"events={e['event_count']}")
        body.append([UNIT, e["run_id"], str(e["seed"]), "success", e["terminal"],
                     str(e["admitted"]), str(e["certified"]),
                     f"PROPAGATION_PATHS/{e['doc']}",
                     f"EVIDENCE/{e['run_id']}/seed{e['seed']}",
                     e["binary_source_head"], e["binary_sha256"], note])
    body.sort(key=lambda r: (r[0], r[1], int(r[2])))
    atomic_write(cat, "\n".join(["\t".join(header)] +
                                ["\t".join(r) for r in body]) + "\n")

    # 3) INDEX.md (additive; existing sections untouched)
    idx = os.path.join(DOCS, "INDEX.md")
    backup(idx)
    text = open(idx).read()
    if SECTION_MARK in text:
        text = text[:text.index(SECTION_MARK)].rstrip() + "\n\n"
    rows = [f"| {e['run_id']} | {e['seed']} | {e['terminal']} | "
            f"{e['provable_to']} | [`{os.path.basename(e['doc'])}`]({e['doc']}) |"
            for e in entries]
    section = [
        SECTION_MARK, "",
        f"- C 单元（L1d Cache）seed 文档：**{len(entries)}**"
        f"（{len(by_run)} 个 RunID；COMPLETE_3_OF_3：**{len(complete)}**）。",
        "- RunID 范围：`r6_matrix_325.csv` 中记录状态=`试跑` 且频率≠F6 的 31 个 C RunID。",
        f"- 权威二进制 SHA-256：`{entries[0]['binary_sha256']}`"
        f"（源 `{entries[0]['binary_source_head']}`，含 `errant_commit` 父事件修复）。",
        "- 全部 seed 经独立证据审计（原始流离线重判）PASS；逐 fault 层边/终局取自各自 "
        "`chain_report.json`，文档与原始流逐项复核。",
        "- 旧 canary/截断证据保留在原目录，未删除、未覆盖。",
        "",
        HEADING, "",
        "| RunID | seed | terminal | provable_to | 文档 |", "|---|---|---|---|---|",
    ] + rows
    atomic_write(idx, text.rstrip() + "\n\n" + "\n".join(section) + "\n")

    # 4) INDEX.json (additive key)
    ij = os.path.join(DOCS, "INDEX.json")
    backup(ij)
    data = json.load(open(ij))
    data["r6_c_unit_20261102"] = {
        "generated": "2026-11-02",
        "binary_sha256": entries[0]["binary_sha256"],
        "binary_source_head": entries[0]["binary_source_head"],
        "counts": {"new_seeds": len(entries), "run_ids": len(by_run),
                   "complete_3_of_3": len(complete)},
        "run_ids": sorted(by_run),
        "complete_3_of_3": complete,
        "entries": entries,
    }
    json.dump(data, open(ij, "w"), ensure_ascii=False, indent=2)

    # 5) STATUS sidecar
    st = os.path.join(RESULTS, "STATUS", "R6-C-UNIT-STATUS.json")
    os.makedirs(os.path.dirname(st), exist_ok=True)
    json.dump({"unit": "C", "unit_name": "L1d Cache",
               "generated": "2026-11-02",
               "binary_sha256": entries[0]["binary_sha256"],
               "binary_source_head": entries[0]["binary_source_head"],
               "run_ids": len(by_run), "seeds": len(entries),
               "complete_3_of_3": complete,
               "incomplete": sorted(set(by_run) - set(complete)),
               "entries": entries}, open(st, "w"), ensure_ascii=False, indent=1)

    print(f"done: docs={len(entries)} runids={len(by_run)} complete3={len(complete)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
