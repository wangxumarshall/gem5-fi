#!/usr/bin/env python3
"""Build the SampleRunID -> RETRY2 run-id / trace / build-hash evidence index.

After the 0202c re-run, this produces:
  analysis/retry2_map.json          -- flat {SampleRunID: retry2_run_id} for
                                       finalize.py's run_manifest_for().
  analysis/retry2_evidence_index.json -- rich {SampleRunID: {retry_run_id,
                                       trace, trace_sha256, gem5_sha256,
                                       terminal_sha256, returncode,
                                       activation_count, total_events}} for the
                                       per-event file/line evidence mapping.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RETRY2 = os.path.join(ROOT, "runs", "W5X3_RETRY2")
ANALYSIS = os.path.join(ROOT, "analysis")

# (SampleRunID, Model, WL, NewContext, ControlContext, TimingID)
PARTIAL_23 = [
    ("M03-F0-W11-W5X3-C02-T01", "M03", "W11", "C02", "R05", "T01"),
    ("M03-F0-W11-W5X3-C02-T02", "M03", "W11", "C02", "R05", "T02"),
    ("M03-F0-W11-W5X3-C02-T03", "M03", "W11", "C02", "R05", "T03"),
    ("M04-F0-W12-W5X3-C02-T01", "M04", "W12", "C02", "R05", "T01"),
    ("M04-F0-W12-W5X3-C02-T02", "M04", "W12", "C02", "R05", "T02"),
    ("M04-F0-W12-W5X3-C02-T03", "M04", "W12", "C02", "R05", "T03"),
    ("M05-F0-W13-W5X3-C02-T01", "M05", "W13", "C02", "R05", "T01"),
    ("M05-F0-W13-W5X3-C02-T02", "M05", "W13", "C02", "R05", "T02"),
    ("M05-F0-W13-W5X3-C02-T03", "M05", "W13", "C02", "R05", "T03"),
    ("M05-F0-W13-W5X3-C03-T01", "M05", "W13", "C03", "C03", "T01"),
    ("M05-F0-W13-W5X3-C03-T02", "M05", "W13", "C03", "C03", "T02"),
    ("M05-F0-W13-W5X3-C03-T03", "M05", "W13", "C03", "C03", "T03"),
    ("M05-F0-W13-W5X3-C04-T01", "M05", "W13", "C04", "R04", "T01"),
    ("M05-F0-W13-W5X3-C04-T02", "M05", "W13", "C04", "R04", "T02"),
    ("M05-F0-W13-W5X3-C04-T03", "M05", "W13", "C04", "R04", "T03"),
    ("M05-F0-W13-W5X3-C05-T01", "M05", "W13", "C05", "R03", "T01"),
    ("M05-F0-W13-W5X3-C05-T02", "M05", "W13", "C05", "R03", "T02"),
    ("M05-F0-W13-W5X3-C05-T03", "M05", "W13", "C05", "R03", "T03"),
    ("M07-F0-W14-W5X3-C02-T01", "M07", "W14", "C02", "R03", "T01"),
    ("M07-F0-W14-W5X3-C02-T02", "M07", "W14", "C02", "R03", "T02"),
    ("M07-F0-W14-W5X3-C05-T01", "M07", "W14", "C05", "R05", "T01"),
    ("M07-F0-W14-W5X3-C05-T02", "M07", "W14", "C05", "R05", "T02"),
    ("M07-F0-W14-W5X3-C05-T03", "M07", "W14", "C05", "R05", "T03"),
]


def rid_for(s):
    (_, model, wl, nctx, _, tidx) = s
    return "%s-F0-%s-W5X3-RETRY2-%s-%s" % (model, wl, nctx, tidx)


def main():
    os.makedirs(ANALYSIS, exist_ok=True)
    flat = {}
    rich = {}
    for s in PARTIAL_23:
        rid = rid_for(s)
        mp = os.path.join(RETRY2, rid, "manifest.json")
        if not os.path.isfile(mp):
            rich[s[0]] = {"retry_run_id": rid, "status": "MISSING"}
            continue
        with open(mp) as fh:
            d = json.load(fh)
        flat[s[0]] = rid
        rich[s[0]] = {
            "retry_run_id": rid,
            "trace": d.get("trace"),
            "trace_sha256": d.get("trace_sha256"),
            "gem5_sha256": d.get("gem5_sha256"),
            "terminal": d.get("terminal"),
            "terminal_sha256": d.get("terminal_sha256"),
            "returncode": d.get("returncode"),
            "activation_count": d.get("activation_count"),
            "total_events": d.get("total_events"),
            "elapsed_sec": d.get("elapsed_sec"),
            "ordinal": d.get("ordinal"),
        }
    with open(os.path.join(ANALYSIS, "retry2_map.json"), "w") as fh:
        json.dump(flat, fh, indent=2, sort_keys=True)
    with open(os.path.join(ANALYSIS, "retry2_evidence_index.json"), "w") as fh:
        json.dump(rich, fh, indent=2, sort_keys=True)
    print("wrote retry2_map.json (%d) + retry2_evidence_index.json (%d)" %
          (len(flat), len(rich)))
    missing = [k for k, v in rich.items() if v.get("status") == "MISSING"]
    if missing:
        print("MISSING:", missing)


if __name__ == "__main__":
    main()