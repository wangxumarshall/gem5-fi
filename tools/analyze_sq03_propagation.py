#!/usr/bin/env python3
"""Analyze SQ03 propagation: permission, writeback event, cache visibility.

Reads the five v3.2.8 SQ03 pilot traces (trace_v31.jsonl) and matched
control traces (same seed/workload, probability 0.0) and reports, per
target store, the distinct moments the user work order requires:

  . _canWB granted (injection old_value 0 -> new_value 1)
  . store_writeback trace node
  . store_mem_write (the actual cache/memory update)
  . commit
  . sq_lifecycle free / sq03_complete

`store_writeback` is NOT cache visibility; `store_mem_write` is the actual
update. Later loads to the target address and consumer edges are counted
from real events only.
"""
import argparse
import csv
import gzip
import json
from pathlib import Path


def load_pilot_seq(pilot_dir: Path):
    meta = json.loads((pilot_dir / "pilot_meta.json").read_text())
    ev = meta.get("injection", {}).get("events", [])
    if not ev:
        return None, None, meta
    return ev[0].get("store_seq"), ev[0].get("store_addr"), meta


def first_tick(events, kind, seq):
    ticks = [e["timestamp"] for e in events
             if e.get("event_type") == kind and e.get("dyn_inst_seq") == seq
             and e.get("timestamp") is not None]
    return min(ticks) if ticks else None


def all_ticks(events, kind, seq):
    return sorted(e["timestamp"] for e in events
                  if e.get("event_type") == kind and e.get("dyn_inst_seq") == seq
                  and e.get("timestamp") is not None)


def _read_events(path: Path):
    """Read trace_v31.jsonl or a prop_trace.csv.gz into dict records."""
    events = []
    if str(path).endswith(".jsonl"):
        with path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return events
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            row = next(csv.reader([line]))
            if len(row) < 5:
                continue
            try:
                tick = int(row[1])
                seqv = int(row[4]) if row[4] else None
            except ValueError:
                continue
            events.append({"event_type": row[3], "timestamp": tick,
                           "dyn_inst_seq": seqv,
                           "va": row[6] if len(row) > 6 else None,
                           "old_value": None, "new_value": None,
                           "detail": row[9] if len(row) > 9 else ""})
    return events


def analyze_trace(path: Path, seq, addr):
    if not path.is_file():
        alt = path.with_name("prop_trace.csv.gz")
        if alt.is_file():
            path = alt
    events = _read_events(path)

    injection = None
    for e in events:
        if e.get("event_type") == "injection" and e.get("dyn_inst_seq") == seq:
            injection = e
            break

    inj_tick = injection["timestamp"] if injection else None
    later_loads = []
    consumers = 0
    for e in events:
        if e.get("consumer_inst_seq") is not None:
            consumers += 1
        va = e.get("va")
        if (va is not None and addr is not None and inj_tick is not None
                and e.get("timestamp", 0) > inj_tick
                and e.get("event_type") in
                ("mem_response", "forwarding_decision", "lq_lifecycle")):
            try:
                if int(str(va), 0) == int(str(addr), 0):
                    later_loads.append(e["timestamp"])
            except (TypeError, ValueError):
                pass

    wb = all_ticks(events, "store_writeback", seq)
    return {
        "inj_tick": inj_tick,
        "canwb_before": injection.get("old_value") if injection else None,
        "canwb_after": injection.get("new_value") if injection else None,
        "wb_ticks": wb,
        "writeback_event_tick": (wb[0] if wb else None),
        "mem_write_tick": first_tick(events, "store_mem_write", seq),
        "commit_tick": first_tick(events, "commit", seq),
        "complete_tick": first_tick(events, "sq03_complete", seq),
        "later_load_events": len(later_loads),
        "later_load_first_tick": min(later_loads) if later_loads else None,
        "consumer_records": consumers,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilots", required=True)
    ap.add_argument("--controls", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = []
    for r in range(1, 6):
        pdir = Path(args.pilots) / f"SQ03-R0{r}"
        cdir = Path(args.controls) / f"SQ03-CONTROL-R0{r}"
        if not cdir.is_dir():
            cdir = Path(args.controls) / f"R0{r}"
        if not pdir.is_dir():
            continue
        seq, addr, _ = load_pilot_seq(pdir)
        f = analyze_trace(pdir / "trace_v31.jsonl", seq, addr)
        c = analyze_trace(cdir / "trace_v31.jsonl", seq, addr) if cdir.is_dir() else None
        row = {
            "pilot": f"R0{r}",
            "store_seq": seq,
            "store_addr": addr,
            **{f"fault_{k}": v for k, v in f.items() if k != "wb_ticks"},
            "fault_wb_ticks": ";".join(str(x) for x in f["wb_ticks"]),
        }
        if c:
            row.update({f"control_{k}": v for k, v in c.items() if k != "wb_ticks"})
            row["control_wb_ticks"] = ";".join(str(x) for x in c["wb_ticks"])
            for key in ("mem_write_tick", "commit_tick", "complete_tick"):
                if f[key] is not None and c[key] is not None:
                    row[f"delta_{key}"] = f[key] - c[key]
        rows.append(row)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
