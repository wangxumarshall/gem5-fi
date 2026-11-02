#!/usr/bin/env python3
"""Independent audit of generated R6-S W1 LSQFwd docs against raw evidence.

Re-reads each doc, then re-derives every value from the seed's raw files.
Exit code 0 iff every doc matches the raw evidence.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r6_w1_evidence as ev  # noqa: E402

DEFAULT_STAGE = "/home/sdc/gem5-fi-ding-cleanup-20261029/R6S_W1_DOCS_STAGE_20261102"


def unq(s):
    return s.strip().strip("`").strip()


def split_sections(text):
    out, cur, buf = {}, "preamble", []
    for line in text.splitlines():
        if line.startswith("## "):
            out[cur] = "\n".join(buf)
            cur, buf = line[3:].strip(), []
        else:
            buf.append(line)
    out[cur] = "\n".join(buf)
    return out


def table(block, header_key):
    rows, inside, seen_header = [], False, False
    for line in block.splitlines():
        if not line.startswith("|"):
            if inside:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not seen_header:
            if header_key in line:
                seen_header = inside = True
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(cells)
    return rows


def dict2col(block, header_key="| 项 | 值 |"):
    return {unq(r[0]): unq(r[1]) for r in table(block, header_key) if len(r) >= 2}


def num(x):
    try:
        return int(unq(x))
    except Exception:
        return None


def audit_doc(doc_path, root):
    errs = []

    def ck(cond, msg):
        if not cond:
            errs.append(msg)

    s = ev.load_sample(root)
    st = ev.load_streams(s)
    man, cell, chain = s["manifest"], s["cell"], s["chain"]
    run = (cell.get("runs") or [{}])[0]
    evs = st["events"]
    faults = chain.get("faults") or {}
    text = open(doc_path, errors="replace").read()
    sec = split_sections(text)

    ck(len(sec) >= 9, f"{doc_path}: missing sections ({list(sec)})")

    ident = dict2col(sec.get("1. 样本身份", ""))
    ck(ident.get("RunID") == s["run_id"], f"{doc_path}: RunID")
    ck(num(ident.get("seed")) == s["seed"], f"{doc_path}: seed")
    ck(ident.get("binary_sha256") == man.get("binary_sha256"), f"{doc_path}: binary sha")
    ck(ident.get("binary_source_head") == str(man.get("binary_source_head", "n/a")),
       f"{doc_path}: source head")
    ck(ident.get("analysis_tool_head") == man.get("analysis_tool_head"),
       f"{doc_path}: tool head")
    for key, p in (("prop_evt_path", "prop_evt"), ("stats_path", "stats"),
                   ("run_out_path", "run_out"), ("inj_log_path", "inj_log"),
                   ("manifest_path", "manifest")):
        ck(ident.get(key) == s["paths"][p], f"{doc_path}: {key}")

    verdict = dict2col(sec.get("2. 最终判定（run 级 + 逐 fault）", ""))
    ck(verdict.get("oracle outcome") == chain.get("oracle_outcome"), f"{doc_path}: oracle")
    ck(num(verdict.get("gem5 guest exit")) == chain.get("exit_code"), f"{doc_path}: exit")
    ck(verdict.get("terminal（链模型整体）") == chain.get("terminal"), f"{doc_path}: terminal")
    ck(verdict.get("provable_to（链模型整体）") == chain.get("provable_to"),
       f"{doc_path}: provable_to")
    ck(verdict.get("admitted") == str(chain.get("admitted")), f"{doc_path}: admitted")
    ck(verdict.get("certified") == str(chain.get("certified")), f"{doc_path}: certified")
    ck(verdict.get("truncated") == str(chain.get("truncated")), f"{doc_path}: truncated")
    ck(verdict.get("chain_valid") == str(chain.get("chain_valid")), f"{doc_path}: chain_valid")
    ck(num(verdict.get("事件总数")) == evs["count"], f"{doc_path}: event total")
    ck(num(verdict.get("fault 数")) == len(faults), f"{doc_path}: fault count")
    funnel = st["runout"]["funnel"] or {}
    ck(f"injected=`{funnel.get('injected')}`" in verdict.get("L0 funnel", ""),
       f"{doc_path}: funnel injected")
    ck(verdict.get("cell admission_status") == cell.get("admission_status"),
       f"{doc_path}: admission status")
    ck(num(verdict.get("cell activated / attempted", "0 / 0").split("/")[0]) ==
       run.get("activated"), f"{doc_path}: activated")

    # per-fault verdict
    fv = table(sec.get("2. 最终判定（run 级 + 逐 fault）", ""),
               "| fault | 注入 Cycle |")
    ck(len(fv) == len(faults), f"{doc_path}: fault verdict rows {len(fv)}")
    for r in fv:
        fid = unq(r[0])
        f = faults.get(fid)
        if not f:
            errs.append(f"{doc_path}: unknown fault {fid}")
            continue
        e = {k: v for k, v in (f.get("edges") or {}).items()
             if not k.endswith("_witness")}
        proven = {k for k, v in e.items() if v == "proven"}
        missing = {k for k, v in e.items() if v != "proven"}
        ck(set(x.strip() for x in r[3].split(",") if x.strip() and x.strip() != "—") == proven,
           f"{doc_path}: fault {fid} proven edges")
        ck(set(x.strip() for x in r[4].split(",") if x.strip() and x.strip() != "—") == missing,
           f"{doc_path}: fault {fid} missing edges")
        ck(unq(r[5]) == f.get("terminal"), f"{doc_path}: fault {fid} terminal")
        ck(unq(r[6]) == f.get("provable_to"), f"{doc_path}: fault {fid} provable_to")

    # injection table
    inj = table(sec.get("3. 真实注入清单", ""), "| fault | Cycle | Site |")
    ck(len(inj) == len(st["inj"]), f"{doc_path}: injection rows")
    fields = ("Cycle", "Site", "FaultType", "Vaddr", "FwdSize", "ByteOffset",
              "Mask", "StoreSeq", "SqIdx", "LoadSeq", "LqIdx")
    for r, raw in zip(inj, st["inj"]):
        for cellv, key in zip(r[1:], fields):
            ck(unq(cellv) == str(raw.get(key)), f"{doc_path}: inj {key} {cellv}")

    # per-fault path tables
    faults_blk = sec.get("4. 传播过程（逐 fault 的规范路径）", "")
    parts = re.split(r"^### fault (\d+)\s*$", faults_blk, flags=re.M)
    found = set()
    for i in range(1, len(parts), 2):
        fid, body = parts[i], parts[i + 1]
        found.add(fid)
        ids = st["path_ids"].get(fid, [])
        rows = table(body, "| 位置 | 层 |")
        ck(len(rows) == len(ids), f"{doc_path}: fault {fid} path rows {len(rows)}")
        for pos, r in enumerate(rows):
            d = evs["captured"].get(unq(r[2]), {})
            ck(unq(r[0]) == str(pos), f"{doc_path}: fault {fid} position {r[0]}")
            ck(unq(r[1]) == f"L{pos}", f"{doc_path}: fault {fid} layer {r[1]}")
            ck(unq(r[2]) == ids[pos], f"{doc_path}: fault {fid} event id")
            ck(unq(r[3]) == (d.get("parent_event_id") or "—"),
               f"{doc_path}: fault {fid} parent")
            ck(num(r[4]) == int(d.get("tick") or -1), f"{doc_path}: fault {fid} tick")
            ck(num(r[5]) == int(d.get("cycle") or -1), f"{doc_path}: fault {fid} cycle")
            ck(unq(r[6]) == d.get("kind"), f"{doc_path}: fault {fid} kind")
            ck(unq(r[9]) == (("0x" + d["va"]) if d.get("va") else "—"),
               f"{doc_path}: fault {fid} va")
            for key, idx in (("detection_layer", 12), ("contained", 12),
                             ("outcome", 12)):
                if d.get(key):
                    ck(str(d[key]) in r[idx],
                       f"{doc_path}: fault {fid} {key} missing in row")
        wrows = table(body, "| 层边 | witness from |")
        ew = {k: v for k, v in (faults[fid].get("edges") or {}).items()
              if k.endswith("_witness")}
        ck(len(wrows) == len(ew), f"{doc_path}: fault {fid} witness rows")
        for r in wrows:
            key = unq(r[0])
            w = ew.get(key)
            if not w:
                errs.append(f"{doc_path}: fault {fid} unknown witness {key}")
                continue
            ck(unq(r[1]) == w.get("from"), f"{doc_path}: fault {fid} witness from")
            ck(unq(r[2]) == w.get("to"), f"{doc_path}: fault {fid} witness to")
            ck([x.strip() for x in r[3].split(",")] == w.get("shared_keys"),
               f"{doc_path}: fault {fid} shared_keys")
        for k, w in ew.items():
            frm = w.get("from", "").split(":", 1)[-1].split("@t")[0]
            to = w.get("to", "").split(":", 1)[-1].split("@t")[0]
            # edge "Lx->Ly" -> positions x,y
            m = re.match(r"L(\d+)->L(\d+)", k)
            if m:
                x, y = int(m.group(1)), int(m.group(2))
                if x < len(ids) and y < len(ids):
                    ck(evs["captured"][ids[x]].get("kind") == frm,
                       f"{doc_path}: fault {fid} {k} from-kind")
                    ck(evs["captured"][ids[y]].get("kind") == to,
                       f"{doc_path}: fault {fid} {k} to-kind")
    ck(found == set(faults), f"{doc_path}: fault sections {sorted(found)}")

    # consumer summary
    cs = chain.get("consumer_summary") or []
    csrows = table(sec.get("4. 传播过程（逐 fault 的规范路径）", ""),
                   "| fault | source_id |")
    if isinstance(cs, list) and cs:
        ck(len(csrows) == len(cs), f"{doc_path}: consumer rows")
        # one CONSUMER-SUMMARY entry per (fault, source_id); keep list order
        for r, c in zip(csrows, cs):
            fid = unq(r[0])
            ck(fid == str(c.get("fault_id")), f"{doc_path}: consumer fault {fid}")
            ck(unq(r[1]) == c.get("source_id"), f"{doc_path}: consumer source {fid}")
            ck(num(r[2]) == int(c["emitted_consumer_count"]),
               f"{doc_path}: consumer emitted {fid}")
            ck(num(r[3]) == int(c["suppressed_consumer_count"]),
               f"{doc_path}: consumer suppressed {fid}")
            logical = int(c["emitted_consumer_count"]) + int(c["suppressed_consumer_count"])
            ck(num(r[4]) == logical, f"{doc_path}: consumer logical {fid}")
            ck(unq(r[5]) == c.get("by_outcome"), f"{doc_path}: consumer outcome {fid}")
            ck(unq(r[6]) == c.get("by_kind"), f"{doc_path}: consumer kind {fid}")

    # census
    crows = table(sec.get("5. 事件总览", ""), "| kind | count |")
    cmap = {unq(r[0]): num(r[1]) for r in crows}
    ck(cmap == evs["kind_counts"], f"{doc_path}: kind census mismatch")
    ck(sum(cmap.values()) == evs["count"], f"{doc_path}: census sum")

    # hashes
    shrows = table(sec.get("6. 原始证据与哈希", ""), "| 证据 | 路径 | SHA-256 |")
    claimed = {unq(r[0]): (unq(r[1]), unq(r[2])) for r in shrows}
    expected = {k for k, p in s["paths"].items() if os.path.isfile(p)}
    ck(set(claimed) == expected, f"{doc_path}: hash table keys")
    for key, (p, sha) in claimed.items():
        ck(p == s["paths"].get(key), f"{doc_path}: hash path {key}")
        if os.path.isfile(p):
            ck(sha == ev.sha256(p), f"{doc_path}: hash mismatch {key}")
        ck(p.startswith(s["root"]), f"{doc_path}: hash path outside root {p}")

    # stats + command
    strows = table(sec.get("7. 运行规模与可复现命令", ""), "| 统计 | 值 |")
    for r in strows:
        k, v = unq(r[0]), unq(r[1])
        raw_key = ("board.processor.cores.core.numCycles" if k == "numCycles" else k)
        ck(st["stats"].get(raw_key) == v, f"{doc_path}: stat {k}")
    ck(man.get("command", "n/a") in sec.get("7. 运行规模与可复现命令", ""),
       f"{doc_path}: command missing")

    ck("## 8. 诚实边界" in text, f"{doc_path}: honesty section")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", default=[])
    ap.add_argument("--stage", default=DEFAULT_STAGE)
    args = ap.parse_args()
    roots = args.root or ev.discover_roots()
    all_errs, checked = [], 0
    for root in roots:
        man = json.load(open(os.path.join(root, "manifest.json")))
        doc = os.path.join(args.stage, man["run_id"],
                           f"{man['run_id']}-seed{man['seed']}.md")
        if not os.path.isfile(doc):
            all_errs.append(f"missing doc {doc}")
            continue
        errs = audit_doc(doc, root)
        checked += 1
        print(("PASS " if not errs else "FAIL ") + doc)
        for e in errs[:10]:
            print("   ", e)
        all_errs.extend(errs)
    print(f"audited {checked} docs; {len(all_errs)} errors")
    return 0 if not all_errs else 1


if __name__ == "__main__":
    sys.exit(main())
