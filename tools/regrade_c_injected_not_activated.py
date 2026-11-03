#!/usr/bin/env python3
"""Offline regrade: certify strictly-proven injected_not_activated samples.

Reads ONLY each seed's existing raw evidence (prop_evt gzip, stats, injection
log, manifest, chain_report). Never runs gem5, never edits the raw stream.

For each seed:
  * recompute SHA-256 of prop_evt before and after (must be identical);
  * prove gzip EOF, stats, injection counts, L0 address, no downstream event;
  * require the old report to be the open L0 terminal (not already admitted);
  * back up chain_report.json (.pre-injected-not-activated) and rewrite it with
    the new terminal, provable_to=L0, admitted/certified=True, subkind, and a
    provenance block (old report SHA, stream SHA before/after, tool head);
  * emit an old -> new field-level diff.

Usage:
  python3 tools/regrade_c_injected_not_activated.py \
      --root runs/lsu/r6_c_unit/runs \
      --out runs/lsu/r6_c_unit/regrade_injected_not_activated
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lsu_prop_fields as PF  # noqa: E402
import lsu_chain_check as CHAIN  # noqa: E402
import r6_c_evidence as ev  # noqa: E402

TARGETS = [
    ("C04-F0-W6", 1), ("C04-F1-W6", 1), ("C04-F2-W6", 1),
    ("C05-F0-W6", 1), ("C05-F2-W6", 1),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write(path, text):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-ina-", text=True)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def regrade(root, run_id, seed, outdir):
    seed_root = os.path.join(root, f"{run_id}_s{seed}")
    sample = ev.load_sample(seed_root)
    rep_path = sample["paths"]["seed_chain_report"]
    stream = sample["paths"]["prop_evt"]
    stats_path = sample["paths"]["stats"]
    log_path = sample["paths"]["inj_log"]
    man = sample["manifest"]
    old_rep_sha = sha256_file(rep_path)
    stream_before = sha256_file(stream)

    rec = {"run_id": run_id, "seed": seed, "ok": False, "reasons": []}

    # 1. gzip EOF (read_stream raises on an incomplete stream)
    try:
        events, truncated, _summ, _issues = PF.read_stream(stream)
    except Exception as exc:
        rec["reasons"].append(f"stream unreadable/truncated: {exc!r}")
        return rec
    if truncated:
        rec["reasons"].append("read_stream reports truncated=True")
        return rec

    stats = ev.parse_stats(stats_path)
    inj_rows = ev.parse_injection_log(log_path)
    old = json.load(open(rep_path))
    acct = old.get("consumer_summary_accounting") or {}

    verdict = CHAIN.injected_not_activated_verdict(
        events,
        oracle_outcome=old.get("oracle_outcome"),
        exit_code=old.get("exit_code"),
        truncated=old.get("truncated") is True
                  or old.get("evidence_truncated") is True,
        stats=stats, inj_rows=len(inj_rows),
        binary_sha256=man.get("binary_sha256"),
        binary_source_head=man.get("binary_source_head"),
        analysis_tool_head=man.get("analysis_tool_head"),
        consumer_summary_accounting=acct,
    )
    if not verdict["ok"]:
        rec["reasons"] = verdict["reasons"]
        return rec

    # Require the OLD report to be the open L0 terminal, not already admitted.
    if old.get("admitted") is True:
        rec["reasons"].append("old report already admitted; refusing to regrade")
        return rec
    old_prov = old.get("provable_to")
    if old_prov != "L0":
        rec["reasons"].append(f"old provable_to={old_prov!r} != L0")
        return rec

    fid = verdict["fault_id"]
    new = json.loads(json.dumps(old))
    new["terminal"] = CHAIN.INJECTED_NOT_ACTIVATED
    new["provable_to"] = "L0"
    new["beyond"] = ""
    new["chain_valid"] = True
    new["admitted"] = True
    new["certified"] = True
    new["admission"] = {
        "admitted": True, "path": CHAIN.INJECTED_NOT_ACTIVATED,
        "terminal": CHAIN.INJECTED_NOT_ACTIVATED,
        "violations": [], "reasons": [],
        "note": "严格证明：真实注入但被污染缓存行在程序结束前未被再次访问，"
                "无下游架构影响。",
    }
    new["injected_not_activated"] = {
        "subkind": CHAIN.INA_SUBKIND,
        "fault_id": fid,
        "l0": verdict["l0"],
        "line": verdict["line"],
        "oracle": verdict["oracle"],
        "stats_injected": verdict["stats_injected"],
        "log_rows": verdict["log_rows"],
        "simTicks": verdict["simTicks"],
        "conditions": {
            "gzip_eof": True,
            "stats_nonempty_simticks_gt_0": True,
            "counts_log_stream_stats_equal": True,
            "l0_address_and_field_verifiable": bool(verdict["l0"].get("field")),
            "no_downstream_access_of_line": True,
            "no_fabricated_l1_to_l5": True,
            "no_errant_commit_or_containment": True,
            "chain_end_is_lifecycle_only": True,
            "consumer_conservation_ok": True,
            "binary_and_tool_identity_recorded": True,
        },
    }
    faults = new.get("faults") or {}
    if fid in faults:
        faults[fid]["raw_terminal"] = faults[fid].get("terminal")
        faults[fid]["terminal"] = CHAIN.INJECTED_NOT_ACTIVATED
        faults[fid]["provable_to"] = "L0"
        faults[fid]["beyond"] = ""
    new["regrade"] = {
        "kind": "injected_not_activated",
        "timestamp": os.environ.get("R6C_REGRADE_TIME", ""),
        "original_report_sha256": old_rep_sha,
        "prop_evt_sha256_before": stream_before,
        "prop_evt_sha256_after": None,  # filled below
        "tool_head": os.popen(
            "git -C %s rev-parse HEAD" % os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))).read().strip(),
        "binary_sha256": man.get("binary_sha256"),
        "binary_source_head": man.get("binary_source_head"),
        "stats_injected": verdict["stats_injected"],
        "log_rows": verdict["log_rows"],
        "event_count": len(events),
    }

    # Backup + write.
    bak = rep_path + ".pre-injected-not-activated"
    if not os.path.exists(bak):
        shutil.copy2(rep_path, bak)
    # Prove the raw stream was not touched by the rewrite.
    stream_after = sha256_file(stream)
    if stream_after != stream_before:
        rec["reasons"].append("prop_evt changed during regrade; aborting")
        return rec
    new["regrade"]["prop_evt_sha256_after"] = stream_after
    atomic_write(rep_path, json.dumps(new, ensure_ascii=False, indent=1))

    diff = {
        "run_id": run_id, "seed": seed,
        "fields": {
            "terminal": {"old": old.get("terminal"), "new": new.get("terminal")},
            "provable_to": {"old": old.get("provable_to"),
                            "new": new.get("provable_to")},
            "beyond": {"old": old.get("beyond"), "new": new.get("beyond")},
            "admitted": {"old": old.get("admitted"), "new": new.get("admitted")},
            "certified": {"old": old.get("certified"),
                          "new": new.get("certified")},
            "admission.path": {"old": (old.get("admission") or {}).get("path"),
                               "new": CHAIN.INJECTED_NOT_ACTIVATED},
        },
        "raw_stream_sha256": stream_after,
        "raw_stream_unchanged": stream_before == stream_after,
        "original_report_sha256": old_rep_sha,
    }
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, f"{run_id}-seed{seed}.diff.json"), "w") as f:
        json.dump(diff, f, ensure_ascii=False, indent=1)
    rec.update({"ok": True, "diff": diff,
                "terminal": new["terminal"],
                "provable_to": new["provable_to"],
                "admitted": True, "certified": True})
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root",
                    default="/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/runs")
    ap.add_argument("--out", default="/home/sdc/gem5-fi-ding/runs/lsu/"
                                     "r6_c_unit/regrade_injected_not_activated")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    rows = []
    for run_id, seed in TARGETS:
        rec = regrade(args.root, run_id, seed, args.out)
        rows.append(rec)
        print(("PASS" if rec["ok"] else "FAIL"), run_id, "seed", seed,
              rec.get("terminal", ""), rec.get("reasons", []))
    with open(os.path.join(args.out, "SUMMARY.json"), "w") as f:
        json.dump({"targets": len(rows),
                   "pass": sum(1 for r in rows if r["ok"]),
                   "rows": rows}, f, ensure_ascii=False, indent=1)
    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
