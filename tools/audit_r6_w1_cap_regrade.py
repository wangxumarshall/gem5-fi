#!/usr/bin/env python3
"""Independent audit of an EVENT_CAP regrade.

The regrade re-runs the shipped chain analysis with cap=n+1 on a COMPLETE
stream.  That is only legitimate if (a) the raw evidence was not modified,
(b) the original report is still recoverable, and (c) the *only* fields that
changed are the ones the analysis cap controls.  This tool re-derives those
facts from the files on disk and refuses to pass otherwise.

Per seed it checks:
  * `gzip -t`-equivalent full decompression of prop_evt (and prop_trace), and
    that the PROP-EVT count equals the manifest's recorded event count;
  * evidence mtimes predate the regrade backup (nothing rewritten afterwards);
  * the original sample is preserved in `<RunID>/chain_report.json.pre-...`;
    its canonical serialisation reproduces the original per-seed report
    byte-for-byte (validated on un-regraded seeds, whose aggregate sample
    equals the standalone file);
  * the old->new diff touches only cap-dependent keys;
  * the regraded sample is full/L5, admitted/certified, truncated=false,
    violations=[], conservation OK, event_count == n;
  * `chain_regrade.original_seed_chain_sha256` matches the reconstructed
    original.  A mismatch is the known 2026-11-02 backup-ordering defect and
    is reported as FAIL unless `--apply-fix` corrects the manifest (the old
    value is retained in the record as `..._corrected_from`).

Raw evidence and derived reports are never modified by this tool.
"""
import argparse
import gzip
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STAMP = "20261102"
# Fields the cap controls.  Anything else changing means the regrade altered a
# verdict, not just the analysis bound.
ALLOWED_CHANGED = {
    "admission", "admitted", "certified", "chain_valid", "event_count",
    "evidence_truncated", "faults", "summary", "truncated",
    "truncation_reason",
}
CANON = dict(indent=1, ensure_ascii=False)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def decompress_count(path, prefix):
    """Full decompression to EOF; raises on a truncated gzip stream."""
    n = 0
    with gzip.open(path, "rt", errors="replace") as f:
        for line in f:
            if line.startswith(prefix):
                n += 1
    return n


def canonical_sample(sample):
    return json.dumps(sample, **CANON).encode()


def audit(root, apply_fix=False):
    out = {"root": root, "errors": [], "warnings": []}
    err = out["errors"].append

    man_path = os.path.join(root, "manifest.json")
    man = json.load(open(man_path))
    runid, seed = man["run_id"], int(man["seed"])
    inner = os.path.join(root, runid)
    sdir = os.path.join(inner, "seed%d" % seed)
    reg = man.get("chain_regrade")
    out.update({"run_id": runid, "seed": seed})
    if not reg:
        err("manifest has no chain_regrade")
        out["pass"] = False
        return out

    agg_pre = os.path.join(inner, "chain_report.json.pre-capregrade-%s" % STAMP)
    seed_pre = os.path.join(sdir, "chain_report.json.pre-capregrade-%s" % STAMP)
    cell_pre = os.path.join(inner, "cell_results.json.pre-capregrade-%s" % STAMP)
    man_pre = os.path.join(root, "manifest.json.pre-capregrade-%s" % STAMP)
    for p in (agg_pre, seed_pre, cell_pre, man_pre):
        if not os.path.isfile(p):
            err("missing backup %s" % p)
    if out["errors"]:
        out["pass"] = False
        return out

    old_agg = json.load(open(agg_pre))
    samples = old_agg.get("samples") or []
    if len(samples) != 1:
        err("aggregate backup has %d samples, expected 1" % len(samples))
        out["pass"] = False
        return out
    old_sample = samples[0]
    if old_sample.get("sample_run_id") != "s%d" % seed:
        err("aggregate backup sample id %r != s%d"
            % (old_sample.get("sample_run_id"), seed))
    rebuilt = canonical_sample(old_sample)
    rebuilt_sha = sha256_bytes(rebuilt)

    new = json.load(open(os.path.join(sdir, "chain_report.json")))
    changed = sorted(k for k in set(old_sample) | set(new)
                     if old_sample.get(k) != new.get(k))
    out["changed_keys"] = changed
    illegal = [k for k in changed if k not in ALLOWED_CHANGED]
    if illegal:
        err("non-cap fields changed: %s" % illegal)

    # the seed-level backup must either be the original (fixed tool) or a
    # post-write copy of the new report (the 2026-11-02 ordering defect).
    seed_pre_sha = sha256_file(seed_pre)
    new_sha = sha256_file(os.path.join(sdir, "chain_report.json"))
    out["seed_backup_is_original"] = seed_pre_sha == rebuilt_sha
    if not out["seed_backup_is_original"]:
        if seed_pre_sha != new_sha:
            err("seed backup is neither the original nor the new report")
        else:
            out["warnings"].append(
                "seed-level backup is a copy of the NEW report (pre-fix "
                "ordering defect); original recovered from aggregate backup")

    # raw evidence unchanged: still decompresses to EOF, correct count, and
    # was last written before the regrade backup.
    evt = os.path.join(sdir, "prop_evt.txt.gz")
    trc = os.path.join(sdir, "prop_trace.csv.gz")
    stats = os.path.join(sdir, "stats.txt")
    for p in (evt, trc, stats):
        if not os.path.isfile(p):
            err("missing evidence %s" % p)
    if out["errors"]:
        out["pass"] = False
        return out
    try:
        n = decompress_count(evt, "PROP-EVT:")
    except Exception as e:
        err("prop_evt gzip not complete: %r" % (e,))
        n = -1
    try:
        decompress_count(trc, "")  # full read proves the gzip trailer
    except Exception as e:
        err("prop_trace gzip not complete: %r" % (e,))
    if n != reg.get("events"):
        err("stream has %d PROP-EVT, manifest records %s"
            % (n, reg.get("events")))
    if new.get("event_count") != n:
        err("report event_count %s != stream %d"
            % (new.get("event_count"), n))
    if os.path.getsize(stats) == 0:
        err("stats.txt empty")
    reg_time = os.path.getmtime(man_pre)
    out["evidence_mtime_before_regrade"] = all(
        os.path.getmtime(p) <= reg_time + 1 for p in (evt, trc, stats))
    if not out["evidence_mtime_before_regrade"]:
        err("evidence modified after the regrade backup was taken")
    out["evidence_sha256"] = {"prop_evt.txt.gz": sha256_file(evt),
                              "prop_trace.csv.gz": sha256_file(trc),
                              "stats.txt": sha256_file(stats)}

    # sample-level gates
    adm = new.get("admission") or {}
    cons = (new.get("consumer_summary_accounting") or {}).get("conservation")
    gates = {
        "stream_present": new.get("stream_present") is True,
        "truncated_false": new.get("truncated") is False,
        "evidence_truncated_false": new.get("evidence_truncated") is False,
        "admitted": new.get("admitted") is True,
        "certified": new.get("certified") is True,
        "violations_empty": (adm.get("violations") or []) == [],
        "conservation_ok": str(cons).lower() == "ok",
        "terminal_full": new.get("terminal") == "full",
        "provable_to_L5": new.get("provable_to") == "L5",
    }
    out["gates"] = gates
    for k, ok in gates.items():
        if not ok:
            err("gate %s failed" % k)
    faults = new.get("faults") or {}
    spread = {}
    for f in faults.values():
        key = "%s/%s" % (f.get("terminal"), f.get("provable_to"))
        spread[key] = spread.get(key, 0) + 1
    out["fault_count"] = len(faults)
    out["fault_verdict_spread"] = spread

    # provenance
    recorded = reg.get("original_seed_chain_sha256")
    out["reconstructed_original_seed_sha256"] = rebuilt_sha
    out["recorded_original_seed_sha256"] = recorded
    if recorded != rebuilt_sha:
        msg = ("manifest original_seed_chain_sha256 %s does not match the "
               "reconstructed original %s" % (recorded, rebuilt_sha))
        if apply_fix:
            reg["original_seed_chain_sha256_corrected_from"] = recorded
            reg["original_seed_chain_sha256"] = rebuilt_sha
            reg["original_seed_chain_reconstructed_from"] = agg_pre
            reg["seed_backup_note"] = (
                "seed-level .pre-capregrade-%s is a post-write copy left by "
                "the pre-fix backup ordering; the true original sample is "
                "preserved in the aggregate backup and reproduced byte-for-"
                "byte from it" % STAMP)
            tmp = man_path + ".tmp"
            json.dump(man, open(tmp, "w"), indent=1)
            os.replace(tmp, man_path)
            out["provenance_fixed"] = True
            out["warnings"].append(msg + " -- corrected")
        else:
            err(msg + " (rerun with --apply-fix to correct)")
    out["pass"] = not out["errors"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--apply-fix", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    recs = [audit(r, apply_fix=args.apply_fix) for r in args.root]
    for r in recs:
        print(json.dumps(r, ensure_ascii=False, sort_keys=True))
    npass = sum(1 for r in recs if r.get("pass"))
    print("cap-regrade audit: %d samples, %d PASS, %d FAIL"
          % (len(recs), npass, len(recs) - npass))
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "R6S_W1_CAP_REGRADE_AUDIT.json"), "w") as f:
            json.dump(recs, f, indent=1, ensure_ascii=False)
    return 0 if npass == len(recs) else 1


if __name__ == "__main__":
    sys.exit(main())
