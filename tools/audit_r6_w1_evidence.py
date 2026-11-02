#!/usr/bin/env python3
"""Independent audit of R6-S W1 (LSQFwd) seed evidence.

Reads only the raw evidence of each seed and re-derives every claimed verdict.
It never imports runner/classifier code, so a bug there cannot mask a bad seed.
Exit code 0 iff every discovered seed passes every check.
"""
import argparse
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r6_w1_evidence as ev  # noqa: E402

DEFAULT_OUT = "/home/sdc/gem5-fi-ding-cleanup-20261029/W1_EVIDENCE_AUDIT_20261102"


def gzip_eof_lines(path):
    n = 0
    with gzip.open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            n += b.count(b"\n")
    return n


def audit(root):
    rec = {"root": root, "checks": {}, "reasons": []}

    def ck(name, cond, detail=None):
        rec["checks"][name] = bool(cond)
        if not cond:
            rec["reasons"].append(f"{name}: {detail}" if detail else name)

    try:
        s = ev.load_sample(root)
    except Exception as e:
        ck("load_sample", False, repr(e))
        rec["pass"] = False
        return rec

    man, cell, chain = s["manifest"], s["cell"], s["chain"]
    rec.update({
        "run_id": s["run_id"], "seed": s["seed"], "inner": s["inner"],
        "seed_dir": s["seed_dir"], "manifest_kind": man.get("kind", "worker"),
        "status": man.get("status"), "exit_code": man.get("exit_code"),
        "binary_path": man.get("binary_path"),
        "binary_sha256": man.get("binary_sha256"),
        "binary_source_head": man.get("binary_source_head", "n/a"),
        "analysis_tool_head": man.get("analysis_tool_head"),
        "start_time": man.get("start_time"), "end_time": man.get("end_time"),
        "oracle": chain.get("oracle_outcome"),
        "terminal": chain.get("terminal"),
        "provable_to": chain.get("provable_to"),
        "beyond": chain.get("beyond"), "truncated": chain.get("truncated"),
        "evidence_truncated": chain.get("evidence_truncated"),
        "chain_valid": chain.get("chain_valid"),
        "admitted": chain.get("admitted"), "certified": chain.get("certified"),
        "violations": (chain.get("admission") or {}).get("violations"),
        "admission_path": (chain.get("admission") or {}).get("path"),
        "admission_status": cell.get("admission_status"),
        "conservation": cell.get("conservation"),
        "count_contradiction": cell.get("count_contradiction"),
        "event_count_chain": chain.get("event_count"),
        "worker_outcome": (cell.get("runs") or [{}])[0].get("outcome"),
        "worker_activated": (cell.get("runs") or [{}])[0].get("activated"),
        "worker_attempted": (cell.get("runs") or [{}])[0].get("attempted"),
    })

    # --- manifest / identity -------------------------------------------------
    ck("manifest_finished", man.get("status") == "FINISHED", man.get("status"))
    ck("manifest_exit_zero", man.get("exit_code") == 0, man.get("exit_code"))
    ck("binary_sha", man.get("binary_sha256") == ev.BIN_SHA256,
       man.get("binary_sha256"))
    base = os.path.basename(root)
    ck("dir_name", base == f"{s['run_id']}_s{s['seed']}", base)
    ck("cell_runs_one", len(cell.get("runs") or []) == 1)

    # --- required artifacts --------------------------------------------------
    for key, p in s["paths"].items():
        if key in ("manifest",):
            continue
        ck(f"exists_{key}", os.path.isfile(p), p)
    missing = [k for k in ("prop_evt", "prop_trace", "stats", "run_out")
               if not os.path.isfile(s["paths"][k])]
    if missing:
        rec["pass"] = False
        return rec

    ck("stats_nonzero", os.path.getsize(s["paths"]["stats"]) > 0)

    # --- stream integrity ----------------------------------------------------
    try:
        streams = ev.load_streams(s)
        rec["stream_ok"] = True
    except Exception as e:
        ck("prop_evt_gzip_eof", False, repr(e))
        rec["pass"] = False
        return rec
    ck("prop_evt_gzip_eof", True)
    try:
        n_trace = gzip_eof_lines(s["paths"]["prop_trace"])
        ck("prop_trace_gzip_eof", n_trace > 0, n_trace)
        rec["prop_trace_lines"] = n_trace
    except Exception as e:
        ck("prop_trace_gzip_eof", False, repr(e))

    events, inj, runout = streams["events"], streams["inj"], streams["runout"]
    faults = chain.get("faults") or {}
    rec["event_count_scanned"] = events["count"]
    rec["fault_count"] = len(faults)
    ck("event_count_matches",
       events["count"] == chain.get("event_count"),
       f"{events['count']} vs {chain.get('event_count')}")
    ck("events_present", events["count"] > 0)

    # --- chain verdict contract ---------------------------------------------
    ck("stream_present", chain.get("stream_present") is True)
    ck("not_truncated", chain.get("truncated") is False, chain.get("truncated"))
    ck("not_evidence_truncated", chain.get("evidence_truncated") is False)
    ck("chain_valid", chain.get("chain_valid") is True)
    ck("admitted", chain.get("admitted") is True)
    ck("certified", chain.get("certified") is True)
    ck("violations_empty", (chain.get("admission") or {}).get("violations") == [],
       (chain.get("admission") or {}).get("violations"))
    ck("admission_status", cell.get("admission_status") == "ADMITTED",
       cell.get("admission_status"))
    ck("conservation", cell.get("conservation") == "OK", cell.get("conservation"))
    ck("no_count_contradiction", cell.get("count_contradiction") is False)
    ck("oracle_present", chain.get("oracle_outcome") not in (None, ""))
    ck("terminal_present", chain.get("terminal") not in (None, ""))

    # --- injector accounting -------------------------------------------------
    funnel, trigger = runout["funnel"], runout["trigger"]
    ck("funnel_present", funnel is not None)
    ck("trigger_present", trigger is not None)
    if funnel:
        rec["funnel"] = funnel
        ck("faults_eq_activated", len(faults) == funnel["activated"],
           f"{len(faults)} vs {funnel['activated']}")
        ck("injected_ge_activated", funnel["injected"] >= funnel["activated"])
        ck("inj_rows_eq_injected", len(inj) == funnel["injected"],
           f"{len(inj)} vs {funnel['injected']}")
        ck("worker_activated_eq_funnel",
           (cell.get("runs") or [{}])[0].get("activated") == funnel["activated"])
    if trigger and funnel:
        ck("trigger_eq_funnel",
           (trigger["attempted"], trigger["eligible"], trigger["injected"]) ==
           (funnel["attempted"], funnel["eligible"], funnel["injected"]))

    # every activated fault has an inj event and a matching log row
    inj_events = {}
    for d in events["captured"].values():
        if d.get("kind") == "inj":
            inj_events[d.get("fault_id")] = d
    ck("inj_events_eq_faults", len(inj_events) == len(faults),
       f"{len(inj_events)} vs {len(faults)}")

    rows = {(r.get("Cycle"), r.get("Vaddr"), r.get("StoreSeq"), r.get("LoadSeq")): r
            for r in inj}
    matched = 0
    for fid in sorted(faults, key=lambda x: int(x)):
        d = inj_events.get(fid)
        if not d:
            continue
        key = (d.get("cycle"), "0x" + d.get("va", ""),
               d.get("store_dyn_inst_seq"), d.get("dyn_inst_seq"))
        if key in rows:
            matched += 1
        else:
            rec["reasons"].append(f"fault {fid}: inj event {key} absent from log")
    ck("inj_events_match_log", matched == len(inj_events),
       f"{matched}/{len(inj_events)}")

    # --- per-fault path integrity -------------------------------------------
    bad = []
    for fid, ids in streams["path_ids"].items():
        caps = [events["captured"].get(i) for i in ids]
        if not ids or any(c is None for c in caps):
            bad.append(f"fault {fid}: missing path events")
            continue
        if caps[0].get("kind") != "inj":
            bad.append(f"fault {fid}: first path event is {caps[0].get('kind')}")
        ticks = [int(c.get("tick") or -1) for c in caps]
        if ticks != sorted(ticks):
            bad.append(f"fault {fid}: path ticks not monotonic")
        f = faults[fid]
        for edge, status in (f.get("edges") or {}).items():
            if edge.endswith("_witness"):
                continue
            if status not in ("proven", "missing"):
                bad.append(f"fault {fid}: edge {edge}={status!r}")
    ck("fault_paths_valid", not bad, "; ".join(bad[:5]))

    # --- artifact hashes -----------------------------------------------------
    rec["hashes"] = {}
    for key, p in s["paths"].items():
        if os.path.isfile(p):
            rec["hashes"][key] = ev.sha256(p)
    rec["stats_size"] = os.path.getsize(s["paths"]["stats"])
    rec["prop_evt_size"] = os.path.getsize(s["paths"]["prop_evt"])

    rec["pass"] = all(rec["checks"].values())
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", default=[],
                    help="explicit seed root(s); default discovers w1e + canary")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    roots = args.root or ev.discover_roots()
    os.makedirs(args.out, exist_ok=True)
    results = [audit(r) for r in roots]
    jl = os.path.join(args.out, "R6S_W1_EVIDENCE_AUDIT.jsonl")
    with open(jl, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    md = ["# R6-S W1 证据审计（独立重算）", "",
          f"- 样本数：**{len(results)}**；PASS：**{sum(1 for r in results if r['pass'])}**；"
          f"FAIL：**{sum(1 for r in results if not r['pass'])}**",
          f"- 权威二进制 SHA-256：`{ev.BIN_SHA256}`",
          "- 每个样本均由 `tools/audit_r6_w1_evidence.py` 只读重算；未引用 runner 判定。", "",
          "| RunID | seed | 来源 | oracle | terminal | provable_to | admitted | certified | 事件数 | 注入/激活 | PASS |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        fn = r.get("funnel") or {}
        md.append(f"| {r.get('run_id','?')} | {r.get('seed','?')} | `{r['root']}` | "
                  f"{r.get('oracle','?')} | {r.get('terminal','?')} | "
                  f"{r.get('provable_to','?')} | {r.get('admitted')} | "
                  f"{r.get('certified')} | {r.get('event_count_scanned','?')} | "
                  f"{fn.get('injected','?')}/{fn.get('activated','?')} | "
                  f"{'PASS' if r['pass'] else '**FAIL**'} |")
    bad = [r for r in results if not r["pass"]]
    if bad:
        md += ["", "## FAIL 明细", ""]
        for r in bad:
            md.append(f"- `{r['root']}`：")
            for reason in r["reasons"]:
                md.append(f"  - {reason}")
    open(os.path.join(args.out, "R6S_W1_EVIDENCE_AUDIT.md"), "w").write(
        "\n".join(md) + "\n")
    print(f"audit: {len(results)} samples, "
          f"{sum(1 for r in results if r['pass'])} PASS, {len(bad)} FAIL")
    print("wrote", jl)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
