#!/usr/bin/env python3
"""L31 — independent 325-RunID evidence audit (lean).

For each RunID in the gate contract roster, find every on-disk PROP-EVT stream
from the full-host `find` list, then evaluate the strict `check_admission`
verdict (imported verbatim from origin/r6-gate tools/lsu_chain_check.py) on the
smallest COMPLETE stream (gz reads to EOF + non-empty sibling stats.txt);
if none is complete, evaluate the largest truncated one to characterise it.
Writes JSONL incrementally so partial results survive contention.
"""
import collections, gzip, json, os, re, sys
from pathlib import Path

GATE = Path("/home/sdc/gem5-fi-ding/.claude/worktrees/r6-gate")
sys.path.insert(0, str(GATE / "tools"))
import lsu_prop_fields as P   # noqa: E402
import lsu_chain_check as C   # noqa: E402

CONTRACT = GATE / "docs/gem5-fi/lsu/mdspec/ready_contract.json"
HOST_LIST = Path("/tmp/prop_evt_host.txt")
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/l31_audit.jsonl")
EVENT_CAP = 4000  # matches ready_contract.json chain_gate.event_cap
PAT = re.compile(r"\b([A-Z]\d\d-(?:F\d|ENG)[-A-Za-z0-9_]*W\d+)\b")


def gz_eof(p):
    try:
        with gzip.open(p, "rb") as f:
            while f.read(1 << 20):
                pass
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:70]}"


def stats_bytes(p):
    for c in ("stats.txt", "../stats.txt", "../../stats.txt"):
        q = os.path.normpath(os.path.join(os.path.dirname(p), c))
        if os.path.exists(q):
            return os.path.getsize(q)
    return None


def eval_stream(rid, p):
    ok, err = gz_eof(p)
    sb = stats_bytes(p)
    complete = bool(ok and sb and sb > 0)
    events = []
    if ok:
        try:
            events, _ = P.read_events(p)
        except Exception:
            events = []
    n_full = len(events)
    ev = events[:EVENT_CAP]
    act = 1 if any(e.get("kind") == "inj" for e in ev) else 0
    verdict = None
    if ev:
        try:
            r = C.check_admission({"run_id": rid, "activated": act, "events": ev})
            verdict = {"admitted": r["admitted"], "terminal": r["terminal"],
                       "applicable": r["applicable"], "violations": r["violations"],
                       "path_layers": r["path_layers"]}
        except Exception as e:
            verdict = {"error": f"{type(e).__name__}: {e}"}
    return {"path": p, "gz_eof": ok, "gz_error": err, "stats_bytes": sb,
            "complete": complete, "n_events": n_full, "n_used": len(ev),
            "activated": act, "verdict": verdict}


def main():
    d = json.loads(CONTRACT.read_text())
    cats = {e["run_id"]: e["category"] for e in d["entries"]}
    byid = collections.defaultdict(list)
    for line in HOST_LIST.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        for rid in set(PAT.findall(line)):
            byid[rid].append(line)
    fh = OUT.open("w")
    for rid in sorted(cats):
        paths = sorted(set(byid.get(rid, [])))
        samples = [eval_stream(rid, p) for p in paths]
        comp = [s for s in samples if s["complete"]]
        chosen = None
        if comp:
            s = min(comp, key=lambda x: (x["n_events"] or 1 << 60))
            chosen = {"how": "smallest_complete", "path": s["path"],
                      "verdict": s["verdict"], "n_events": s["n_events"]}
        elif samples:
            s = max(samples, key=lambda x: x["n_events"])
            chosen = {"how": "largest_truncated", "path": s["path"],
                      "verdict": s["verdict"], "n_events": s["n_events"]}
        rec = {"run_id": rid, "category": cats[rid], "n_streams": len(samples),
               "n_complete": len(comp), "n_truncated": len(samples) - len(comp),
               "chosen": chosen,
               "paths": [s["path"] for s in samples],
               "completeness": [{"path": s["path"], "complete": s["complete"],
                                 "gz_error": s["gz_error"]} for s in samples]}
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
    fh.close()
    print("done", file=sys.stderr)


if __name__ == "__main__":
    main()
