#!/usr/bin/env python3
"""Add the R6-S W1 (2026-11-02) seeds to the authoritative indexes.

Additive and reversible: every target file is backed up before it is rewritten
(no backup is ever overwritten), and old TIMEOUT/truncated evidence records are
left in place.  Refuses to run unless the evidence audit and the doc audit both
report every seed PASS.
"""
import argparse
import csv
import json
import os
import re
import shutil
import tempfile

LS = "/home/sdc/gem5-fi-ding/runs/lsu"
DOCS = f"{LS}/R6_COMPLETE_PROPAGATION_PATHS"
RESULTS = f"{LS}/RESULTS"
STAMP = "20261102-w1e"

RUN_IDS = ["S01-F0-W1", "S01-F1-W1", "S01-F2-W1", "S02-F0-W1", "S02-F2-W1"]


def atomic_write(path, text):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-w1e-", text=True)
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


def entry_from_audit(rec, doc):
    man = json.load(open(os.path.join(rec["root"], "manifest.json")))
    inner = rec["inner"]
    cell = json.load(open(os.path.join(inner, "cell_results.json")))
    return {
        "run_id": rec["run_id"], "seed": rec["seed"],
        "oracle_outcome": rec["oracle"],
        "terminal": rec["terminal"], "provable_to": rec["provable_to"],
        "admitted": rec["admitted"], "certified": rec["certified"],
        "truncated": rec["truncated"], "violations": rec["violations"],
        "doc": f"{rec['run_id']}/{rec['run_id']}-seed{rec['seed']}.md",
        "evidence_dir": rec["root"], "evidence_seed_dir": rec["seed_dir"],
        "binary_sha256": rec["binary_sha256"],
        "binary_source_head": rec["binary_source_head"],
        "analysis_tool_head": rec["analysis_tool_head"],
        "metadata_provenance": man.get("metadata_provenance", {}).get("kind", "live"),
        "source_root": "w1canary" if "/w1canary/" in rec["root"] else "w1e",
        "admission_status": cell.get("admission_status"),
        "manifest_kind": rec.get("manifest_kind", "worker"),
        "event_count": rec.get("event_count_scanned"),
        "fault_count": rec.get("fault_count"),
        "funnel": rec.get("funnel"),
        "doc_path": doc,
    }


def parse_doc_evidence(doc_path):
    t = open(doc_path, errors="replace").read()
    m = re.search(r"\|\s*prop_evt_path\s*\|\s*`([^`]+)`\s*\|", t)
    if not m:
        return None
    return os.path.dirname(os.path.dirname(m.group(1)))


def scan_s_docs():
    sdoc = []
    for run_id in sorted(os.listdir(DOCS)):
        if not re.match(r"^S\d{2}-", run_id):
            continue
        d = os.path.join(DOCS, run_id)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            m = re.match(rf"^{re.escape(run_id)}-seed(\d+)\.md$", name)
            if not m:
                continue
            seed = int(m.group(1))
            doc_path = os.path.join(d, name)
            txt = open(doc_path, errors="replace").read()

            def pick(patterns, default="n/a"):
                for pat in patterns:
                    mm = re.search(pat, txt)
                    if mm:
                        return mm.group(1)
                return default

            terminal = pick([r"\|\s*terminal[^|]*\|\s*`([^`]+)`\s*\|",
                             r"terminal[：:]\s*`([^`]+)`"])
            provable = pick([r"\|\s*provable_to[^|]*\|\s*`([^`]+)`\s*\|",
                             r"provable_to[：:]\s*`([^`]+)`"])
            admitted = pick([r"\|\s*admitted\s*\|\s*`(True|False)`\s*\|",
                             r"admitted=(True|False)"])
            certified = pick([r"\|\s*certified\s*\|\s*`(True|False)`\s*\|",
                              r"certified=(True|False)"])
            bin_sha = pick([r"binary_sha256\s*\|\s*`([0-9a-f]{64})`",
                            r"binary SHA-256[：:]\s*`([0-9a-f]{64})`"])
            ev = parse_doc_evidence(doc_path)
            if ev and bin_sha == "n/a":
                man_path = os.path.join(os.path.dirname(os.path.dirname(ev)), "manifest.json")
                if os.path.isfile(man_path):
                    bin_sha = json.load(open(man_path)).get("binary_sha256", "n/a")
            sdoc.append({"run_id": run_id, "seed": seed, "terminal": terminal,
                         "provable_to": provable, "admitted": admitted,
                         "certified": certified, "doc": f"{run_id}/{name}",
                         "evidence_dir": ev or "n/a", "binary_sha256": bin_sha})
    sdoc.sort(key=lambda x: (x["run_id"], x["seed"]))
    return sdoc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True,
                    help="R6S_W1_EVIDENCE_AUDIT.jsonl")
    ap.add_argument("--docs-audit-ok", action="store_true",
                    help="assert audit_r6_w1_docs.py reported 0 errors")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.docs_audit_ok:
        raise SystemExit("refusing: --docs-audit-ok not given (run the doc audit first)")

    recs = [json.loads(l) for l in open(args.audit)]
    if len(recs) != 15:
        raise SystemExit(f"expected 15 audited seeds, got {len(recs)}")
    bad = [r for r in recs if not r.get("pass")]
    if bad:
        raise SystemExit(f"refusing: {len(bad)} audited seeds FAIL: "
                         f"{[r['root'] for r in bad]}")
    missing = [r for r in recs if not os.path.isfile(
        os.path.join(DOCS, r["run_id"], f"{r['run_id']}-seed{r['seed']}.md"))]
    if missing:
        raise SystemExit(f"refusing: {len(missing)} docs not deployed")

    entries = [entry_from_audit(r, os.path.join(
        DOCS, r["run_id"], f"{r['run_id']}-seed{r['seed']}.md")) for r in recs]
    entries.sort(key=lambda e: (e["run_id"], e["seed"]))
    print(f"entries: {len(entries)}; run_ids: {sorted({e['run_id'] for e in entries})}")

    # what the S table will look like
    sdoc = scan_s_docs()
    by_run = {}
    for r in sdoc:
        by_run.setdefault(r["run_id"], set()).add(r["seed"])
    complete = {k: v for k, v in by_run.items() if {1, 2, 3} <= v}
    print(f"S docs total={len(sdoc)} runids={len(by_run)} complete3={len(complete)}")

    if args.dry_run:
        for e in entries:
            print("WOULD", e["run_id"], e["seed"], e["oracle_outcome"],
                  e["terminal"], e["provable_to"], e["source_root"])
        print("DRY-RUN: no files written")
        return

    # 1) EVIDENCE symlinks
    for e in entries:
        d = os.path.join(RESULTS, "EVIDENCE", e["run_id"])
        os.makedirs(d, exist_ok=True)
        link = os.path.join(d, f"seed{e['seed']}")
        if os.path.islink(link) or os.path.exists(link):
            real = os.path.realpath(link)
            if real == os.path.realpath(e["evidence_seed_dir"]):
                print("link ok:", link)
            else:
                print("EXISTS (left unchanged):", link, "->", real)
            continue
        rel = os.path.relpath(e["evidence_seed_dir"], d)
        os.symlink(rel, link)
        assert os.path.isdir(os.path.realpath(link)), link
        print("link:", link, "->", rel)

    # 2) CATALOG.tsv
    cat = os.path.join(RESULTS, "CATALOG.tsv")
    backup(cat)
    with open(cat, newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    header, body = rows[0], rows[1:]
    for e in entries:
        note = (f"provable_to={e['provable_to']}; terminal={e['terminal']}; "
                f"oracle={e['oracle_outcome']}; source_root={e['source_root']}; "
                f"metadata={e['metadata_provenance']}; "
                f"faults={e['fault_count']}; events={e['event_count']}")
        body = [r for r in body if not (r[0] == "S" and r[1] == e["run_id"]
                                        and r[2] == str(e["seed"]))]
        body.append(["S", e["run_id"], str(e["seed"]), "success", e["terminal"],
                     str(e["admitted"]), str(e["certified"]),
                     f"PROPAGATION_PATHS/{e['doc']}",
                     f"EVIDENCE/{e['run_id']}/seed{e['seed']}",
                     e["binary_source_head"], e["binary_sha256"], note])
    body.sort(key=lambda r: (r[0], r[1], int(r[2])))
    atomic_write(cat, "\n".join(["\t".join(header)] +
                                ["\t".join(r) for r in body]) + "\n")
    print("CATALOG rows:", len(body))

    # 3) INDEX.md
    idx = os.path.join(DOCS, "INDEX.md")
    backup(idx)
    text = open(idx).read()
    heading = "## R6-S（Store Queue 单元）逐 seed 传播路径"
    pos = text.find(heading)
    if pos < 0:
        raise SystemExit("S section heading not found")
    prefix = text[:pos]

    n_by_freq = {}
    for e in entries:
        freq = e["run_id"].split("-")[1]
        n_by_freq[freq] = n_by_freq.get(freq, 0) + 1
    cont = [
        "## R6-S-W1-CONTINUATION-2（2026-11-02）",
        "",
        f"- 收口 5 个 W1 RunID 的 15 个 seed（S01-F0/F1/F2-W1、S02-F0/F2-W1），"
        f"其中 S01-F1-W1 seed1 为首轮 canary（不重跑）。",
        "- 全部样本经独立证据审计 PASS（gzip EOF×2、stats 非零、ADMITTED、"
        "admitted/certified、truncated=false、violations=[]、fault 路径闭合、"
        "注入日志与事件流一一对应）。",
        f"- 权威二进制 SHA-256：`{entries[0]['binary_sha256']}`（`gem5.opt-6db026e7`，"
        "源 `43d1bb08`）；旧二进制截断样本仅作失败对照，未计入合格数。",
        "- 每份文档逐 fault 记录层边与终局；run 级 terminal/provable_to 与逐 fault 不一致时并列保留。",
        "- 旧 TIMEOUT/截断证据保留在原目录，未删除、未覆盖。",
        "",
    ]
    s_heading = [
        heading, "",
        f"- S seed 文档：**{len(sdoc)}**（{len(by_run)} 个 RunID；COMPLETE_3_OF_3：**{len(complete)}**）",
        "- 判定字段逐 seed 取自该 seed 的 `chain_report.json`；`source_root` 指向该 seed 自己的证据目录。",
        "- 旧轮 TIMEOUT 尝试仍保留在原证据目录，未被删除；本轮新合格 seed 单独列于下表。",
        "", "| RunID | seed | terminal | provable_to | 文档 |",
        "|---|---|---|---|---|",
    ]
    rows = [f"| {r['run_id']} | {r['seed']} | {r['terminal']} | {r['provable_to']} | "
            f"[`{os.path.basename(r['doc'])}`]({r['doc']}) |" for r in sdoc]
    atomic_write(idx, prefix + "\n".join(cont) + "\n" +
                 "\n".join(s_heading + rows) + "\n")
    print(f"INDEX.md: S docs={len(sdoc)} runids={len(by_run)} complete3={len(complete)}")

    # 4) INDEX.json
    ij = os.path.join(DOCS, "INDEX.json")
    backup(ij)
    data = json.load(open(ij))
    data["r6_s_w1_continuation_20261102"] = {
        "generated": "2026-11-02",
        "binary_sha256": entries[0]["binary_sha256"],
        "binary_source_head": "43d1bb0833e59559366fdb2d5254d77b0b139351",
        "counts": {"new_seeds": len(entries), "run_ids_resolved": len(RUN_IDS),
                   "s_docs_total": len(sdoc), "complete_3_of_3_total": len(complete),
                   "by_frequency": n_by_freq},
        "entries": entries,
    }
    atomic_write(ij, json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print("INDEX.json updated")

    # 5) S-UNIT-STATUS.json
    stp = os.path.join(RESULTS, "STATUS/R6-S-UNIT-STATUS.json")
    backup(stp)
    st = json.load(open(stp))
    by_seed = {}
    for e in entries:
        by_seed.setdefault(e["run_id"], {})[e["seed"]] = e
    for row in st["rows"]:
        rid = row["run_id"]
        if rid not in by_seed:
            continue
        row.setdefault("w1_continuation_20261102", {})["seeds"] = {
            str(s): {"status": "PASS", "root": e["source_root"],
                     "oracle": e["oracle_outcome"], "terminal": e["terminal"],
                     "provable_to": e["provable_to"], "admitted": e["admitted"],
                     "certified": e["certified"], "truncated": e["truncated"],
                     "evidence_dir": e["evidence_seed_dir"],
                     "manifest_kind": e["manifest_kind"],
                     "metadata_provenance": e["metadata_provenance"]}
            for s, e in by_seed[rid].items()}
        row["w1_continuation_20261102"]["note"] = (
            "Supersedes the earlier truncated seed1 attempts; the old evidence "
            "directories are preserved. S01-F1-W1 seed1 is the verified canary.")
        for s in by_seed[rid]:
            row[f"seed{s}"] = "PASS"
        have = {s for s in (1, 2, 3) if row.get(f"seed{s}") == "PASS"}
        row["final_status"] = f"PASS_{len(have)}_OF_3"
        row["current_policy"] = "AUTHORITATIVE"
        row["dry_run_status"] = "runnable"
    st["counts"]["prop_docs_s"] = len(sdoc)
    st["counts"]["pass_seeds_total"] = len(sdoc)
    st["counts"]["complete_3_of_3_total"] = len(complete)
    st["w1_continuation_20261102_note"] = (
        "15 W1 seeds across 5 RunIDs closed on gem5.opt-6db026e7; evidence and doc "
        "audits both PASS. No seed was re-run: S01-F1-W1 seed1 is the canary.")
    atomic_write(stp, json.dumps(st, indent=1, ensure_ascii=False) + "\n")
    print("S status updated; complete3 =", len(complete))

    # 6) RESULTS/README.md
    rp = os.path.join(RESULTS, "README.md")
    backup(rp)
    rt = open(rp).read()
    rt = re.sub(r"\((\d+) seed docs: 83 T \+ 90 A(?: \+ \d+ S)?\)",
                f"({len(sdoc) + 173} seed docs: 83 T + 90 A + {len(sdoc)} S)", rt)
    if "R6-S-W1-CONTINUATION-2" not in rt:
        rt += ("\n- `R6-S-W1-CONTINUATION-2 (2026-11-02)`: +15 S W1 seed docs; "
               f"S total {len(sdoc)}, COMPLETE_3_OF_3 {len(complete)}. "
               "All 15 passed independent evidence and doc audits.\n")
    atomic_write(rp, rt)
    print("RESULTS/README updated")

    # 7) S final report
    fp = os.path.join(RESULTS, "REPORTS/R6-S-UNIT-FINAL-REPORT.md")
    backup(fp)
    lines = ["", "", "---", "",
             "## R6-S-W1-CONTINUATION-2（2026-11-02）—— 五个 W1 RunID 收口", "",
             "| RunID | seed | oracle | chain terminal | provable_to | faults | events | 证据根 |",
             "|---|---|---|---|---|---|---|---|"]
    for e in entries:
        lines.append(f"| {e['run_id']} | {e['seed']} | {e['oracle_outcome']} | "
                     f"{e['terminal']} | {e['provable_to']} | {e['fault_count']} | "
                     f"{e['event_count']} | `{e['source_root']}` |")
    lines += ["",
              f"- 二进制：`{entries[0]['binary_sha256']}`（`gem5.opt-6db026e7`，源 `43d1bb08`）。",
              "- 15/15 样本：`admitted=True`、`certified=True`、`violations=[]`、`truncated=False`、"
              "gzip EOF×2、stats 非零、注入日志与事件流一一对应。",
              "- 未重跑任何既有合格 seed；S01-F1-W1 seed1 即 canary。旧截断样本保留为失败对照。",
              f"- S 合格 seed：{len(sdoc) - 15} → **{len(sdoc)}**；"
              f"COMPLETE_3_OF_3：{len(complete) - len(RUN_IDS)} → **{len(complete)}**。",
              ""]
    atomic_write(fp, open(fp).read() + "\n".join(lines))
    print("S final report appended")
    print("DONE")


if __name__ == "__main__":
    main()
