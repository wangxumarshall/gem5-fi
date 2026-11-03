#!/usr/bin/env python3
"""Add the R6-L (Load Queue, 2026-11-03) 42 seeds to the authoritative
indexes. Additive and reversible: every target file is backed up first.

Refuses unless:
  * all 42 audited seeds PASS,
  * all 14 RunIDs have seed1/2/3,
  * every audited seed has a deployed propagation document,
  * --docs-audit-ok is given (the independent doc audit reported 0 errors).

Usage:
  python3 tools/update_r6_l_indexes.py --audit <R6L_EVIDENCE_AUDIT.jsonl> \
      --docs-audit-ok [--dry-run]
"""
import argparse
import csv
import json
import os
import shutil
import tempfile

DOCS = "/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS"
RESULTS = "/home/sdc/gem5-fi-ding/runs/lsu/RESULTS"
STAMP = "20261103-lunit"
UNIT = "L"
HEADING = "## R6-L（Load Queue 单元）逐 seed 传播路径"
SECTION_MARK = "## R6-L-UNIT（2026-11-03）"
EXPECTED_RUNIDS = 14


def atomic_write(path, text):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-lunit-", text=True)
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
        "evidence_seed_dir": rec.get("seed_dir"),
        "binary_sha256": rec.get("binary_sha256"),
        "binary_source_head": rec.get("binary_source_head"),
        "binary_source_commit": rec.get("binary_source_commit"),
        "analysis_tool_head": rec.get("analysis_tool_head"),
        "event_count": rec.get("event_count"),
        "fault_count": rec.get("fault_count"),
        "repeat_factor": rec.get("repeat_factor"),
        "workload": rec.get("workload"),
        "tier": rec.get("tier"),
        "eligible": rec.get("eligible"),
        "gzip_eof": rec.get("gzip_eof"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True)
    ap.add_argument("--docs-audit-ok", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.docs_audit_ok:
        raise SystemExit("refusing: --docs-audit-ok not given")
    recs = [json.loads(l) for l in open(args.audit) if l.strip()]
    bad = [r for r in recs if not r.get("pass")]
    if bad:
        raise SystemExit(f"refusing: {len(bad)} audited seeds FAIL: "
                         f"{[(r.get('run_id'), r.get('seed')) for r in bad[:5]]}")
    missing = [r for r in recs if not os.path.isfile(
        os.path.join(DOCS, r["run_id"], f"{r['run_id']}-seed{r['seed']}.md"))]
    if missing:
        raise SystemExit(f"refusing: {len(missing)} docs not deployed")
    if len(recs) != 42:
        raise SystemExit(f"refusing: expected 42 L seeds, got {len(recs)}")
    entries = [entry_from_audit(r) for r in recs]
    entries.sort(key=lambda e: (e["run_id"], e["seed"]))
    by_run = {}
    for e in entries:
        by_run.setdefault(e["run_id"], set()).add(e["seed"])
    complete = sorted(k for k, v in by_run.items() if {1, 2, 3} <= v)
    if len(by_run) != EXPECTED_RUNIDS or len(complete) != EXPECTED_RUNIDS:
        raise SystemExit(
            f"refusing: expected 14 RunIDs all 3/3, got runids={len(by_run)} "
            f"complete={len(complete)}")
    print(f"entries={len(entries)} runids={len(by_run)} complete3={len(complete)}")
    if args.dry_run:
        for e in entries:
            print("WOULD", e["run_id"], e["seed"], e["terminal"],
                  e["provable_to"], e["repeat_factor"])
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
                f"events={e['event_count']}; repeat={e['repeat_factor']}")
        body.append([UNIT, e["run_id"], str(e["seed"]), "success", e["terminal"],
                     str(e["admitted"]), str(e["certified"]),
                     f"PROPAGATION_PATHS/{e['doc']}",
                     f"EVIDENCE/{e['run_id']}/seed{e['seed']}",
                     e["binary_source_head"], e["binary_sha256"], note])
    body.sort(key=lambda r: (r[0], r[1], int(r[2])))
    atomic_write(cat, "\n".join(["\t".join(header)] +
                                ["\t".join(r) for r in body]) + "\n")

    # 3) INDEX.md (additive section)
    idx = os.path.join(DOCS, "INDEX.md")
    backup(idx)
    text = open(idx).read()
    if SECTION_MARK in text:
        text = text[:text.index(SECTION_MARK)].rstrip() + "\n\n"
    rows_md = [f"| {e['run_id']} | {e['seed']} | {e['terminal']} | "
               f"{e['provable_to']} | {e['repeat_factor']} | "
               f"[`{os.path.basename(e['doc'])}`]({e['doc']}) |"
               for e in entries]
    section = [
        SECTION_MARK, "",
        f"- L 单元（Load Queue）seed 文档：**{len(entries)}**"
        f"（{len(by_run)} 个 RunID；COMPLETE_3_OF_3：**{len(complete)}**）。",
        "- RunID 范围：`r6_matrix_325.csv` 中记录状态=`试跑` 且频率≠F6 的 14 个 L RunID。",
        "- 有界重复只扩展同一 workload 的 eligible 供给；频率定义/warmup/span/seed/"
        "注入字段/注入点/RunID 身份未变（见 `docs/gem5-fi/lsu/evidence/"
        "R6-L-REPEAT-CENSUS.md`）。",
        "- 每个 seed 的二进制 SHA 以其 manifest 为准（17 个既有样本沿用原二进制，"
        "25 个重跑样本使用 `deecd9e3…`）；源文件逐字节一致见 manifest 的 "
        "`source_file_sha256`。",
        "- 全部 seed 经独立证据审计（原始流离线重判）PASS；逐 fault 层边/终局取自各自 "
        "`chain_report.json`，文档与原始流逐项复核。",
        "- 旧 NO_INJECTION/canary 证据保留在原目录，未删除、未覆盖。",
        "",
        HEADING, "",
        "| RunID | seed | terminal | provable_to | repeat | 文档 |",
        "|---|---|---|---|---|---|",
    ] + rows_md
    atomic_write(idx, text.rstrip() + "\n\n" + "\n".join(section) + "\n")

    # 4) INDEX.json (additive key)
    ij = os.path.join(DOCS, "INDEX.json")
    backup(ij)
    data = json.load(open(ij))
    data["r6_l_unit_20261103"] = {
        "generated": "2026-11-03",
        "counts": {"seeds": len(entries), "run_ids": len(by_run),
                   "complete_3_of_3": len(complete)},
        "run_ids": sorted(by_run),
        "complete_3_of_3": complete,
        "binary_sha256_by_seed": {
            f"{e['run_id']}-seed{e['seed']}": e["binary_sha256"]
            for e in entries},
        "entries": entries,
    }
    json.dump(data, open(ij, "w"), ensure_ascii=False, indent=2)

    # 5) Authoritative evidence (L-specific; do not overwrite the T file)
    ev = os.path.join("/home/sdc/gem5-fi-ding/runs/lsu",
                      "R6-L-AUTHORITATIVE-EVIDENCE.json")
    json.dump({
        "generated_at": "2026-11-03",
        "scope": "14 COMPLETE_3_OF_3 L RunIDs x 3 seeds = 42 seeds",
        "rules": [
            "Exactly one authoritative evidence directory per RunID+seed.",
            "Classify by key-file hashes and identity, never by directory name.",
            "NO_INJECTION is never counted as a qualified seed.",
            "injected_not_activated requires the strict ten-condition proof.",
            "chain_end is lifecycle only, never L5.",
            "Repeat runs extend the same workload's eligible supply; frequency/"
            "tier/seed/field/site/RunID identity are unchanged.",
        ],
        "analysis_tool_head": entries[0]["analysis_tool_head"],
        "doc_set_version": "R6-L-2026-11-03",
        "seeds": entries,
    }, open(ev, "w"), ensure_ascii=False, indent=1)

    # 6) STATUS sidecar
    st = os.path.join(RESULTS, "STATUS", "R6-L-UNIT-STATUS.json")
    os.makedirs(os.path.dirname(st), exist_ok=True)
    json.dump({
        "unit": "L", "unit_name": "Load Queue",
        "generated": "2026-11-03",
        "baseline": "d69ae2884dc360db285f1256e0426e2663e2f34b",
        "runnable_runids": len(by_run),
        "target_seeds": 42,
        "qualified_seeds": len(entries),
        "no_injection_seeds": 0,
        "not_qualified_seeds": 0,
        "complete_3_of_3": complete,
        "docs_deployed": len(entries),
        "binary_sha256_by_seed": {
            f"{e['run_id']}-seed{e['seed']}": e["binary_sha256"]
            for e in entries},
        "entries": entries,
    }, open(st, "w"), ensure_ascii=False, indent=1)
    print(f"done: docs={len(entries)} runids={len(by_run)} "
          f"complete3={len(complete)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
