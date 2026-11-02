#!/usr/bin/env python3
"""Re-run the campaign chain analysis when a COMPLETE stream exceeds EVENT_CAP.

Why: `lsu_prop_fields.read_stream` bounds retained events at 200000 and flags
an over-cap stream with the same `truncated=True` as a genuinely half-written
gzip.  A 71-injection F2 seed produces ~1.5M events with a valid gzip trailer
(`gzip -t` = 0), so the campaign marks it EVIDENCE-TRUNCATED and refuses to
certify — even though the evidence is complete.

This tool does NOT touch the experiment or the raw evidence.  It:
  1. proves the gzip stream reaches EOF and stats.txt is non-empty;
  2. counts the real PROP-EVT events;
  3. re-runs the shipped `write_chain_report` with the read cap set to n+1
     (same parser, same chain checker, same admission gate);
  4. refuses unless the new report says truncated=False, evidence_truncated=
     False, event_count==n, admitted=True, certified=True;
  5. backs up the old chain reports / cell_results / manifest, writes the
     regraded files, and records `chain_regrade` provenance.

Default is a dry run against a temporary copy; `--apply` writes in place.
"""
import argparse
import gzip
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lsu_prop_fields as PF  # noqa: E402
import lsu_campaign as LC  # noqa: E402

SUMMARY = "/home/sdc/gem5-fi-ding-cleanup-20261029/r6s-w1-par-summary.jsonl"
REGRADE_LOG = "/home/sdc/gem5-fi-ding-cleanup-20261029/R6S_W1_CAP_REGRADE.jsonl"


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_prop_events(path):
    """Full decompression to EOF. Raises on an incomplete gzip stream."""
    n = 0
    with gzip.open(path, "rt", errors="replace") as f:
        for line in f:
            if line.startswith("PROP-EVT:"):
                n += 1
    return n


def analyze(seed_dir, runid, seed, oracle, exit_code, cap):
    """Run write_chain_report with the module defaults temporarily raised."""
    old_rs = PF.read_stream.__defaults__
    old_re = PF.read_events.__defaults__
    PF.read_stream.__defaults__ = (cap,)
    PF.read_events.__defaults__ = (cap,)
    try:
        result = {"outcome": oracle, "lookup_tier_capability": None,
                  "blocked": False, "blocked_reason": ""}
        rep = LC.write_chain_report(seed_dir, runid, seed, result,
                                    exit_code=exit_code)
    finally:
        PF.read_stream.__defaults__ = old_rs
        PF.read_events.__defaults__ = old_re
    return rep


def backup(path, stamp):
    b = f"{path}.pre-capregrade-{stamp}"
    if not os.path.exists(b):
        shutil.copy2(path, b)
    return b


def regrade(root, apply=False, stamp="20261102"):
    man_path = os.path.join(root, "manifest.json")
    man = json.load(open(man_path))
    runid, seed = man["run_id"], int(man["seed"])
    inner = os.path.join(root, runid)
    seed_dir = os.path.join(inner, f"seed{seed}")
    old_seed_path = os.path.join(seed_dir, "chain_report.json")
    agg_path = os.path.join(inner, "chain_report.json")
    cell_path = os.path.join(inner, "cell_results.json")
    old_seed = json.load(open(old_seed_path))
    cell = json.load(open(cell_path))
    run = cell["runs"][0]
    if apply and "chain_regrade" in man:
        return {"root": root, "status": "REFUSED",
                "reason": "already regraded (chain_regrade present); refusing to "
                          "overwrite the only original backup"}

    evt = os.path.join(seed_dir, "prop_evt.txt.gz")
    stats = os.path.join(seed_dir, "stats.txt")
    if not os.path.isfile(evt):
        return {"root": root, "status": "REFUSED", "reason": "no prop_evt"}
    if not os.path.isfile(stats) or os.path.getsize(stats) == 0:
        return {"root": root, "status": "REFUSED", "reason": "stats missing/empty"}
    try:
        n = count_prop_events(evt)          # proves gzip EOF
    except Exception as e:
        return {"root": root, "status": "REFUSED",
                "reason": f"gzip incomplete: {e!r}"}
    if n <= PF.EVENT_CAP:
        return {"root": root, "status": "REFUSED",
                "reason": f"stream has {n} events <= cap {PF.EVENT_CAP}"}

    cap = n + 1
    tmp = None
    orig_seed_sha = None
    if apply:
        outdir = seed_dir
        # Backup BEFORE analyze(): write_chain_report() writes the new report
        # into <outdir>/chain_report.json in place, so a backup taken after it
        # would be a copy of the new file (provenance defect fixed 2026-11-02).
        orig_seed_sha = sha256(old_seed_path)
        for p in (old_seed_path, agg_path, cell_path, man_path):
            backup(p, stamp)
        pre_seed = old_seed_path + f".pre-capregrade-{stamp}"
        if sha256(pre_seed) != orig_seed_sha:
            return {"root": root, "status": "REFUSED",
                    "reason": "existing seed backup differs from the current "
                              "original; refusing to regrade"}
    else:
        # same filesystem as the evidence so hard links work (no copy, no
        # mutation); removed after the dry run
        tmp = tempfile.mkdtemp(prefix=".w1regrade-", dir=os.path.dirname(root))
        for name in ("prop_evt.txt.gz", "prop_trace.csv.gz", "stats.txt",
                     "run.out", "run.err", "lsq_fwd_injections.log"):
            src = os.path.join(seed_dir, name)
            if os.path.isfile(src):
                os.link(src, os.path.join(tmp, name))
        outdir = tmp

    try:
        rep = analyze(outdir, runid, seed, old_seed.get("oracle_outcome"),
                      old_seed.get("exit_code"), cap)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    ok = (rep.get("truncated") is False and
          rep.get("evidence_truncated") is False and
          rep.get("event_count") == n and
          rep.get("stream_present") is True and
          rep.get("admitted") is True and rep.get("certified") is True)
    rec = {"root": root, "run_id": runid, "seed": seed, "events": n,
           "cap": cap, "dry_run": not apply,
           "old": {"truncated": old_seed.get("truncated"),
                   "evidence_truncated": old_seed.get("evidence_truncated"),
                   "event_count": old_seed.get("event_count"),
                   "admitted": old_seed.get("admitted"),
                   "certified": old_seed.get("certified")},
           "new": {"truncated": rep.get("truncated"),
                   "evidence_truncated": rep.get("evidence_truncated"),
                   "event_count": rep.get("event_count"),
                   "admitted": rep.get("admitted"),
                   "certified": rep.get("certified"),
                   "terminal": rep.get("terminal"),
                   "provable_to": rep.get("provable_to"),
                   "faults": len(rep.get("faults") or {})},
           "status": "OK" if ok else "REGraded-but-not-admitted"}
    if not apply:
        rec["status"] = "DRY-" + rec["status"]
        return rec
    if not ok:
        return rec

    # --- apply: backups were already taken before analyze() ----------------
    run["chain"] = rep
    run["admitted"] = rep["admitted"]
    run["evidence_truncated"] = rep["evidence_truncated"]
    run["truncation_reason"] = rep["truncation_reason"]
    act = int(run.get("activated") or 0)
    if act <= 0:
        gate = "NO-ACTIVATION"
    elif run["evidence_truncated"]:
        gate = "EVIDENCE-TRUNCATED"
    elif run["admitted"] is True:
        gate = "ADMITTED"
    else:
        gate = "GATE-REFUSED"
    cell["admission_gate_status"] = gate
    if cell.get("admission_status") != "BLOCKED":
        cell["admission_status"] = gate
    cell["evidence_truncated_samples"] = (
        [f"seed{seed}: {run['truncation_reason']}"]
        if run["evidence_truncated"] else [])
    cell_tmp = cell_path + ".tmp"
    json.dump(cell, open(cell_tmp, "w"), indent=1)
    os.replace(cell_tmp, cell_path)

    cell_rep = {"runid": runid, "samples": [rep]}
    cell_rep_tmp = os.path.join(inner, "chain_report.json.tmp")
    json.dump(cell_rep, open(cell_rep_tmp, "w"), indent=1, ensure_ascii=False)
    os.replace(cell_rep_tmp, os.path.join(inner, "chain_report.json"))

    summary_lines = ["# chain summary — %s" % runid, "",
                     "| seed | oracle | admitted | stream | truncated | "
                     "evid_truncated | events | terminal | provable_to | beyond |",
                     "|---|---|---|---|---|---|---|---|---|---|",
                     "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                         rep.get("sample_run_id"), rep.get("oracle_outcome"),
                         rep.get("admitted"), rep.get("stream_present"),
                         rep.get("truncated"), rep.get("evidence_truncated"),
                         rep.get("event_count"), rep.get("terminal"),
                         rep.get("provable_to"), rep.get("beyond"))]
    open(os.path.join(inner, "chain_summary.md"), "w").write(
        "\n".join(summary_lines) + "\n")

    man["chain_regrade"] = {
        "timestamp": "2026-11-02",
        "reason": ("complete gzip stream has %d PROP-EVT events > EVENT_CAP "
                   "%d; analysis re-run with cap=%d (same parser/checker/gate)"
                   % (n, PF.EVENT_CAP, cap)),
        "event_cap": cap, "events": n,
        "original_seed_chain_sha256": orig_seed_sha,
        "original_aggregate_chain_sha256": sha256(
            agg_path + f".pre-capregrade-{stamp}"),
        "original_cell_results_sha256": sha256(
            cell_path + f".pre-capregrade-{stamp}"),
        "evidence_unchanged": True,
    }
    man_tmp = man_path + ".tmp"
    json.dump(man, open(man_tmp, "w"), indent=1)
    os.replace(man_tmp, man_path)

    rec.update({"status": "APPLIED", "dir": root,
                "oracle": rep.get("oracle_outcome"),
                "terminal": rep.get("terminal"),
                "provable_to": rep.get("provable_to")})
    with open(REGRADE_LOG, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    # append a truthful grade record (the queue's earlier FAILED record stays)
    with open(SUMMARY, "a") as f:
        f.write(json.dumps({
            "run_id": runid, "seed": seed, "dir": root, "source": "regrade",
            "status": man.get("status"), "exit_code": man.get("exit_code"),
            "binary_sha256": man.get("binary_sha256"),
            "analysis_tool_head": man.get("analysis_tool_head"),
            "admission_status": cell.get("admission_status"),
            "conservation": cell.get("conservation"),
            "oracle": rep.get("oracle_outcome"), "terminal": rep.get("terminal"),
            "provable_to": rep.get("provable_to"), "admitted": rep.get("admitted"),
            "certified": rep.get("certified"), "truncated": rep.get("truncated"),
        }, ensure_ascii=False, sort_keys=True) + "\n")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--stamp", default="20261102")
    args = ap.parse_args()
    bad = 0
    for root in args.root:
        rec = regrade(root, apply=args.apply, stamp=args.stamp)
        print(json.dumps(rec, ensure_ascii=False, sort_keys=True))
        if not rec["status"].endswith("OK") and rec["status"] not in (
                "APPLIED", "DRY-OK"):
            bad += 1
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
