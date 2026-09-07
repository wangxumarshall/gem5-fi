#!/usr/bin/env python3
"""spectrum_triage.py — fingerprint-library ↔ diagnosis-engine integration
CLI (plan §7.7 / Task 4.5).

Field-side flow: a field engineer observes SDC bit spectra (XOR masks,
golden^actual) — this CLI walks the spectrum through the fingerprint
library to Top-K candidate microarchitectural units, then maps each
candidate unit onto its associated §7.3/§7.4 diagnostic rules (the
experiment-feedback direction of §7.7: injection spectra -> diagnosis
priors).

Pipeline:
  1. spectrum in (hex XOR values, or a masks file, one hex/line)
  2. fingerprint lookup (sdc_fingerprint.lookup) -> Top-K candidate units
  3. per-unit P_SDC prior from the formal campaigns (when available in the
     priors table) -> §7.3-style relevance stars
  4. unit -> diagnostic-rule mapping (§7.7 item 3: each unit family has
     characteristic log signatures; printed as actionable checks)
  5. optionally feed a vmcore-dumps dir to sdc_diagnose for the log-side
     verdict, and print the COMBINED triage (spectrum + logs agree?)

Usage:
  # spectrum-only triage
  python3 spectrum_triage.py --lib docs/paper/tables/fingerprint-library.json \
      --masks 0x00000100 0x0000000000000080
  # spectrum + log-side diagnosis (end-to-end)
  python3 spectrum_triage.py --lib ... --masks-file masks.txt \
      --logparse-dir /home/sdc/wangxu/vmcore0102 --extra extra.json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

from sdc_fingerprint import build_library, lookup, _field_counts  # noqa: E402
from sdc_diagnose import evaluate, evidence_from_logparse  # noqa: E402

# §7.7 item 2/3: unit -> diagnostic prior + characteristic log signature.
# The P_SDC priors come from this repo's formal campaigns (artifacts/);
# stars follow §7.3 weighting. The signature column is the log-side check
# the field engineer runs next (rules/flight-rules.md material).
UNIT_DIAGNOSTICS = {
    "lsq_fwd": {
        "p_sdc_prior": 0.50,   # lsq-matrix formal (artifacts/lsq-matrix)
        "stars": "★★★★",
        "signature": "store->load forwarding: DABT on recently-stored "
                     "addresses; check for spurious translation faults on "
                     "reload of just-written lines (movbe_kernel probe)",
    },
    "prf": {
        "p_sdc_prior": 0.10,   # prf-formal X3 bit-grid
        "stars": "★★★",
        "signature": "register-cell flip: single-variable value corruption, "
                     "no address anomalies; read-trace reads>0 events",
    },
    "fpu": {
        "p_sdc_prior": 0.16,   # t3-1 fsu formal (gemm_double, all-segments)
        "stars": "★★★★",
        "signature": "FP result corruption: mantissa-dominant spectra on "
                     "numeric apps (§6.2: 85-93% mantissa, sign-immune)",
    },
    "l1d": {
        "p_sdc_prior": None,
        "stars": "★★★",
        "signature": "cache data corruption: reload != stored on the same "
                     "core; ECC outcome per protectionModel",
    },
    # units without formal P_SDC yet are listed with prior=None (honest);
    # the fingerprint lookup still ranks them by spectral similarity.
}


def triage(masks, lib, topk=3):
    """One triage per observed XOR mask + an aggregate over all masks."""
    per_mask = []
    unit_votes = {}
    for m in masks:
        cands = lookup(lib, m)[:topk]
        s, e, x = _field_counts(m)
        per_mask.append({
            "xor": f"0x{m:x}",
            "fields": {"sign": s, "exp": e, "mantissa": x,
                       "popcount": bin(m).count("1")},
            "candidates": [{"unit": u, "similarity": sim,
                            "p_sdc_prior": UNIT_DIAGNOSTICS.get(
                                u, {}).get("p_sdc_prior"),
                            "stars": UNIT_DIAGNOSTICS.get(u, {}).get(
                                "stars", "?"),
                            "signature": UNIT_DIAGNOSTICS.get(u, {}).get(
                                "signature", "")}
                           for u, sim in cands],
        })
        for u, sim in cands:
            unit_votes[u] = unit_votes.get(u, 0.0) + sim
    aggregate = sorted(unit_votes.items(), key=lambda kv: -kv[1])
    return per_mask, aggregate


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lib", required=True, help="fingerprint library JSON")
    ap.add_argument("--masks", nargs="*", default=[],
                    help="observed XOR values (hex)")
    ap.add_argument("--masks-file", help="one hex XOR per line")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--logparse-dir",
                    help="vmcore dumps dir — run the log-side diagnosis too")
    ap.add_argument("--extra", help="extra evidence JSON for sdc_diagnose")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    with open(args.lib) as f:
        lib = json.load(f)

    masks = [int(x, 0) for x in args.masks]
    if args.masks_file:
        with open(args.masks_file) as f:
            masks += [int(l.strip(), 0) for l in f if l.strip()]
    if not masks:
        ap.error("need --masks or --masks-file")

    per_mask, aggregate = triage(masks, lib, args.top)

    log_verdict = None
    if args.logparse_dir:
        extra = {}
        if args.extra:
            with open(args.extra) as f:
                extra = json.load(f)
        ev = evidence_from_logparse(args.logparse_dir, extra)
        log_verdict = evaluate(ev)

    if args.json:
        print(json.dumps({"per_mask": per_mask,
                          "aggregate_ranking": aggregate,
                          "log_verdict": log_verdict},
                         indent=2, ensure_ascii=False, default=str))
        return

    for pm in per_mask:
        f = pm["fields"]
        print(f"XOR {pm['xor']}  (sign={f['sign']} exp={f['exp']} "
              f"mantissa={f['mantissa']} popcount={f['popcount']})")
        for c in pm["candidates"]:
            prior = (f"{c['p_sdc_prior']:.2f}" if c["p_sdc_prior"] is not None
                     else "n/a")
            print(f"  -> {c['unit']:<10} sim={c['similarity']:.3f} "
                  f"P_SDC先验={prior} {c['stars']}")
            print(f"     签名: {c['signature']}")
    print("\n综合排序（谱相似度累计）:")
    for u, v in aggregate:
        print(f"  {u:<10} {v:.3f}")
    if log_verdict:
        print(f"\n日志侧诊断（sdc_diagnose）: {log_verdict['confidence']}")
        print(f"  处置: {log_verdict['action']}")
        rules = ", ".join(r["rule"] for r in log_verdict["rules_hit"])
        print(f"  规则命中: {rules or '-'}")


if __name__ == "__main__":
    main()
