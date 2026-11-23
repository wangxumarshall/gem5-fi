#!/usr/bin/env python3
"""Build per-control software-event caches (read-only, derived evidence)."""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_lib as L


def build(run_id: str) -> dict:
    st, out = L.load_state(run_id, "control")
    if st.get("status") != "COMPLETED":
        return {"run_id": run_id, "status": "SKIP", "reason": st.get("status")}
    ct = L.CommitTrace(out / "commit_trace.csv.gz")
    evs = L.build_sw_events(ct)

    def op_ok(e):
        if e.op_seq is None:
            return False
        r = ct.commit_row(e.op_seq)
        if not r:
            return False
        if e.marker.type == L.T_LOAD:
            return any(d[3] == e.marker.b or
                       (d[3] & 0xffffffff) == (e.marker.b & 0xffffffff)
                       for d in r["dst"])
        if e.marker.type == L.T_STORE:
            idx = ct.index_of(e.op_seq)
            return any(v is not None and
                       (v == e.marker.b or
                        (v & 0xffffffff) == (e.marker.b & 0xffffffff))
                       for (_, _, _, v) in ct.srcv[idx])
        return True

    cache = {
        "run_id": run_id,
        "model": st["model"], "context": st["context"],
        "checksum": st.get("oracle_got"),
        "eligible_n": st.get("eligible_n"),
        "eligible_ordinals": st.get("eligible_ordinals"),
        "commits": len(ct),
        "squash": len(ct.squash),
        "events": [{
            "type": e.marker.type, "site": e.marker.site,
            "order": e.marker.order, "a": e.marker.a, "b": e.marker.b,
            "c": e.marker.c, "seq": e.marker.seq, "op_seq": e.op_seq,
            "key": list(e.key), "occ": e.occurrence,
            "line": e.marker.line,
            "op_pc": ((ct.commit_row(e.op_seq) or {}).get("pc")
                      if e.op_seq is not None else None),
            "op_name": ((ct.commit_row(e.op_seq) or {}).get("op")
                        if e.op_seq is not None else None),
            "op_ok": op_ok(e),
        } for e in evs],
    }
    p = out / "sw_events.json"
    p.write_text(json.dumps(cache))
    return {"run_id": run_id, "status": "OK", "events": len(evs),
            "commits": len(ct), "path": str(p)}


def main():
    ids = sorted(p.stem for p in (L.EXT / "results/state").glob("E2E-*-CTRL.json"))
    print(f"controls: {len(ids)}", flush=True)
    with ProcessPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(build, i): i for i in ids}
        for f in as_completed(futs):
            r = f.result()
            print(r, flush=True)


if __name__ == "__main__":
    main()
