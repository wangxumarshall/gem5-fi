#!/usr/bin/env python3
"""Independent audit of the generated R6-C propagation Markdown.

Every claim in a doc is checked against the seed's own raw evidence:
  * the doc's `binary_sha256` equals the manifest's;
  * the doc's run-level terminal/provable_to/admitted/certified equal the
    seed's `chain_report.json`;
  * every row of every per-fault canonical-path table names an event that
    really exists in `prop_evt.txt.gz`, with the same kind/tick, and the
    layer is exactly `r6_c_evidence.layer_of(kind, event)`;
  * every `path_event_ids` entry of the report appears in the doc.

A negative control (tampering one event id / one hash) must be reported.
Exit 0 iff every doc has 0 errors.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r6_c_evidence as ev  # noqa: E402

DOCS = "/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS"
DEFAULT_OUT = "/home/sdc/gem5-fi-ding-cleanup-20261029/R6C_DOC_AUDIT"

ROW = re.compile(
    r"^\|\s*(\d+)\s*\|\s*(L\d|—)\s*\|\s*(\d+)\s*\|\s*([^|]*)\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|")
SHA_ROW = re.compile(r"\|\s*binary_sha256\s*\|\s*`([0-9a-f]{64})`\s*\|")
EVT_ROW = re.compile(r"\|\s*prop_evt_path\s*\|\s*`([^`]+)`\s*\|")
TERM_ROW = re.compile(r"\|\s*terminal（链模型整体）\s*\|\s*`([^`]+)`\s*\|")
PROV_ROW = re.compile(r"\|\s*provable_to（链模型整体）\s*\|\s*`([^`]+)`\s*\|")
ADMIT_ROW = re.compile(r"\|\s*admitted\s*\|\s*`(True|False)`\s*\|")
CERT_ROW = re.compile(r"\|\s*certified\s*\|\s*`(True|False)`\s*\|")


def audit_doc(path):
    errs = []
    txt = open(path, errors="replace").read()
    m_evt = EVT_ROW.search(txt)
    if not m_evt:
        return ["prop_evt_path row missing"]
    prop_evt = m_evt.group(1)
    seed_dir = os.path.dirname(prop_evt)
    root = os.path.dirname(os.path.dirname(seed_dir))
    try:
        s = ev.load_sample(root)
    except Exception as exc:
        return [f"cannot load seed {root}: {exc!r}"]
    m_sha = SHA_ROW.search(txt)
    if not m_sha or m_sha.group(1) != s["manifest"].get("binary_sha256"):
        errs.append("binary_sha256 mismatch")
    chain = s["chain"]
    for rx, key in ((TERM_ROW, "terminal"), (PROV_ROW, "provable_to")):
        m = rx.search(txt)
        if not m or m.group(1) != str(chain.get(key)):
            errs.append(f"{key} mismatch")
    for rx, key in ((ADMIT_ROW, "admitted"), (CERT_ROW, "certified")):
        m = rx.search(txt)
        if not m or m.group(1) != str(chain.get(key)):
            errs.append(f"{key} mismatch")
    if chain.get("terminal") == "injected_not_activated":
        if "Injected-not-activated" not in txt:
            errs.append("injected_not_activated section missing")
        if chain.get("provable_to") != "L0":
            errs.append("injected_not_activated provable_to != L0")
        if "未被再次" not in txt:
            errs.append("injected_not_activated explanation missing")

    events, _trunc, _summ, _issues = __import__("lsu_prop_fields").read_stream(prop_evt)
    by_id = {str(e.get("event_id")): e for e in events}
    covered = set()
    for line in txt.splitlines():
        m = ROW.match(line)
        if not m:
            continue
        _pos, layer, eid, _parent, tick, _cycle, kind = m.groups()
        e = by_id.get(eid)
        if e is None:
            errs.append(f"event {eid} not in raw stream")
            continue
        covered.add(eid)
        if e.get("kind") != kind:
            errs.append(f"event {eid} kind {e.get('kind')!r} != doc {kind!r}")
        if str(e.get("tick")) != tick:
            errs.append(f"event {eid} tick {e.get('tick')} != doc {tick}")
        want = ev.layer_of(kind, e)
        if layer != want:
            errs.append(f"event {eid} layer {layer} != authoritative {want}")
    for fid, f in (chain.get("faults") or {}).items():
        for eid in (f.get("path_event_ids") or []):
            if str(eid) not in covered:
                errs.append(f"fault {fid} path event {eid} not transcribed")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default=DOCS)
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    only = set(args.only)
    results = []
    for run_id in sorted(os.listdir(args.docs)):
        if not re.match(r"^C\d{2}-", run_id):
            continue
        d = os.path.join(args.docs, run_id)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            m = re.match(rf"^{re.escape(run_id)}-seed(\d+)\.md$", name)
            if not m:
                continue
            key = f"{run_id}:{m.group(1)}"
            if only and key not in only:
                continue
            errs = audit_doc(os.path.join(d, name))
            results.append({"doc": os.path.join(d, name), "errors": errs,
                            "ok": not errs})
    out = os.path.join(args.out, "R6C_DOC_AUDIT.json")
    json.dump({"docs": len(results),
               "errors": sum(len(r["errors"]) for r in results),
               "ok": all(r["ok"] for r in results) and bool(results),
               "results": results}, open(out, "w"), ensure_ascii=False, indent=1)
    for r in results:
        if r["errors"]:
            print("FAIL", r["doc"])
            for e in r["errors"][:5]:
                print("  ", e)
    print(json.dumps({"docs": len(results),
                      "errors": sum(len(r["errors"]) for r in results),
                      "ok": all(r["ok"] for r in results) and bool(results)},
                     ensure_ascii=False))
    return 0 if results and all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
