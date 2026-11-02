#!/usr/bin/env python3
"""Independent audit of R6-C (L1d Cache) seed evidence.

Reads only the raw evidence of each seed and re-derives every claimed verdict
with the authoritative checker (`lsu_chain_check.check_chain`).  It does not
trust `chain_report.json`'s terminal/provable_to: those are compared against
the fresh re-derivation and any mismatch is a failure.

Usage:
  python3 tools/audit_r6_c_evidence.py --root <seed-root-or-parent> \
      --out <audit-dir>

Exit 0 iff every discovered seed passes every check.
"""
import argparse
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r6_c_evidence as ev  # noqa: E402
import lsu_chain_check as CHAIN  # noqa: E402
import lsu_prop_fields as PF  # noqa: E402

DEFAULT_OUT = "/home/sdc/gem5-fi-ding-cleanup-20261029/R6C_EVIDENCE_AUDIT"


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
    except Exception as exc:
        ck("load_sample", False, repr(exc))
        return rec
    man, chain = s["manifest"], s["chain"]
    rec.update({
        "run_id": s["run_id"], "seed": s["seed"],
        "oracle": chain.get("oracle_outcome"),
        "terminal": chain.get("terminal"),
        "provable_to": chain.get("provable_to"),
        "admitted": chain.get("admitted"),
        "certified": chain.get("certified"),
        "truncated": chain.get("truncated"),
        "evidence_truncated": chain.get("evidence_truncated"),
        "violations": (chain.get("admission") or {}).get("violations") or [],
        "binary_sha256": man.get("binary_sha256"),
        "binary_source_head": man.get("binary_source_head"),
        "analysis_tool_head": man.get("analysis_tool_head"),
        "event_count": chain.get("event_count"),
        "fault_count": len(chain.get("faults") or {}),
        "seed_dir": s["seed_dir"],
    })

    # 1. identity + termination metadata
    ck("manifest_status_finished", man.get("status") == "FINISHED",
       man.get("status"))
    ck("exit_code_zero", str(man.get("exit_code")) == "0", man.get("exit_code"))
    ck("binary_sha_present", bool(man.get("binary_sha256")))
    ck("run_id_matches", man.get("run_id") == s["run_id"])
    ck("seed_matches", int(man.get("seed", -1)) == s["seed"])

    # 2. stream completeness
    evt = s["paths"]["prop_evt"]
    trc = s["paths"]["prop_trace"]
    try:
        n_evt = gzip_eof_lines(evt)
        ck("prop_evt_gzip_eof", n_evt > 0, n_evt)
    except Exception as exc:
        ck("prop_evt_gzip_eof", False, repr(exc))
    try:
        n_trc = gzip_eof_lines(trc)
        ck("prop_trace_gzip_eof", n_trc > 0, n_trc)
    except Exception as exc:
        ck("prop_trace_gzip_eof", False, repr(exc))
    stats = ev.parse_stats(s["paths"]["stats"])
    ck("stats_nonempty", os.path.getsize(s["paths"]["stats"]) > 0 if
       os.path.isfile(s["paths"]["stats"]) else False)
    ck("stats_simticks", "simTicks" in stats)
    ck("report_stream_present", chain.get("stream_present") is True)
    ck("report_not_truncated",
       chain.get("truncated") is False and chain.get("evidence_truncated") is False,
       (chain.get("truncated"), chain.get("evidence_truncated")))
    ck("chain_valid", chain.get("chain_valid") is True)

    # 3. independent re-derivation from the raw stream
    try:
        events, truncated, _summaries, _issues = PF.read_stream(evt)
        rec["rederived_event_count"] = len(events)
        verdict = CHAIN.check_chain(events, oracle_outcome=chain.get("oracle_outcome"))
    except Exception as exc:
        ck("rederive_check_chain", False, repr(exc))
        return rec
    rfaults = verdict.get("faults") or {}
    cfaults = chain.get("faults") or {}
    ck("fault_set_matches", set(rfaults) == set(cfaults),
       (sorted(rfaults), sorted(cfaults)))
    mism = []
    for fid in sorted(set(rfaults) & set(cfaults), key=lambda x: int(x)):
        a, b = rfaults[fid], cfaults[fid]
        for key in ("terminal", "provable_to"):
            if a.get(key) != b.get(key):
                mism.append(f"fault {fid} {key}: rederived={a.get(key)!r} "
                            f"report={b.get(key)!r}")
        if a.get("edges") != b.get("edges"):
            mism.append(f"fault {fid} edges differ")
        if [str(x) for x in (a.get("path_event_ids") or [])] != \
                [str(x) for x in (b.get("path_event_ids") or [])]:
            mism.append(f"fault {fid} path_event_ids differ")
    ck("rederived_matches_report", not mism, "; ".join(mism[:4]))
    ck("event_count_matches", len(events) == chain.get("event_count"),
       (len(events), chain.get("event_count")))

    # 4. admission / qualification
    ck("report_admitted", chain.get("admitted") is True)
    ck("report_certified", chain.get("certified") is True)
    viol = (chain.get("admission") or {}).get("violations") or []
    ck("report_no_violations", viol == [], viol[:3])
    ck("conservation_ok",
       (chain.get("consumer_summary_accounting") or {}).get("conservation")
       in ("ok", "n/a"))

    # 5. injection-bookkeeping consistency (L0 truth)
    inj_events = [e for e in events
                  if e.get("kind") == "inj" and str(e.get("fault_id", "")) not in ("", "0")]
    inj_rows = ev.parse_injection_log(s["paths"]["inj_log"])
    funnel = ev.parse_funnel(s["paths"]["inj_log"]) or {}
    ck("injection_rows_nonzero", len(inj_rows) > 0, len(inj_rows))
    ck("l0_events_match_log", len(inj_events) == len(inj_rows),
       (len(inj_events), len(inj_rows)))
    ck("funnel_books_injection",
       funnel.get("attempted", 0) >= funnel.get("injected", 0) >= 0,
       funnel)

    # 6. address provenance (never fabricate)
    prov = {}
    for fid in sorted(cfaults, key=lambda x: int(x)):
        f = cfaults[fid]
        ids = [str(x) for x in (f.get("path_event_ids") or [])]
        vas, pas = [], []
        for eid in ids:
            e = next((x for x in events if str(x.get("event_id")) == eid), None)
            if not e:
                continue
            if e.get("va") and e["va"] not in vas:
                vas.append(e["va"])
            if e.get("pa") and e["pa"] not in pas:
                pas.append(e["pa"])
        prov[fid] = {"va": vas, "pa": pas,
                     "pfn": [format(int(p, 16) >> 12, "x") for p in pas]}
    rec["address_provenance"] = prov

    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", default=[])
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    roots = args.root or [ev.DEFAULT_ROOT]
    os.makedirs(args.out, exist_ok=True)
    jsonl = os.path.join(args.out, "R6C_EVIDENCE_AUDIT.jsonl")
    seeds = []
    for r in roots:
        seeds.extend(ev.discover_seeds(r))
    rows = []
    with open(jsonl, "w") as fh:
        for root, run_id, seed in seeds:
            rec = audit(root)
            rec["run_id"] = rec.get("run_id", run_id)
            rec["seed"] = rec.get("seed", seed)
            rec["pass"] = all(rec["checks"].values()) and bool(rec["checks"])
            rows.append(rec)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    npass = sum(1 for r in rows if r["pass"])
    summary = {"seeds": len(rows), "pass": npass,
               "fail": len(rows) - npass,
               "failing": [f"{r['run_id']}:s{r['seed']}" for r in rows
                           if not r["pass"]]}
    with open(os.path.join(args.out, "R6C_EVIDENCE_AUDIT_SUMMARY.json"), "w") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if rows and npass == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
