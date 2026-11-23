#!/usr/bin/env python3
"""Build-matched Fault <-> Control resolution for WHEN-5X3.

A Control is only a valid golden for a Fault when its gem5 build hash matches
the Fault's.  This module scans every CTRL*/CTRL2* run directory, indexes them
by (ModelID, NewContext), and exposes :func:`resolve_control` so every analysis
step (finalize / acceptance / validate / delivery) uses the SAME resolution and
never silently substitutes a cross-build Control.

The 0202c round produced two observation-only builds that differ solely in
``MMU_CONSUMER_REUSE_CAP`` (a warm-hit trace-volume bound that is inert for
Controls, which never produce fault-tagged entries):

  * ``eb327197…`` — fetch/IFU + masked_reason instrumentation.
  * ``fb1b6f01…`` — same, with the bounded M05 warm-hit consumer fan-out.

A Control is reported with ``build_matches`` so A20 can genuinely fail on a
cross-build substitution instead of hard-coding PASS.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS = os.path.join(ROOT, "analysis")

# (round_label, base_dir, dir_prefix) in search order (later rounds win).
# original/retry use CTRL-*, retry2 uses CTRL2-* / CTRL2B-* (the B suffix is a
# second 0202c build: fb1b vs eb327, differing only in MMU_CONSUMER_REUSE_CAP).
RUN_BASES = (
    ("original", os.path.join(ROOT, "runs", "W5X3"), "CTRL-"),
    ("retry", os.path.join(ROOT, "runs", "W5X3_RETRY"), "CTRL-"),
    ("retry2", os.path.join(ROOT, "runs", "W5X3_RETRY2"), "CTRL2-"),
    ("retry2b", os.path.join(ROOT, "runs", "W5X3_RETRY2"), "CTRL2B-"),
)

_MODEL_CTX = re.compile(r"(M\d\d)-([A-Z]+\d+)")


def load(p, d=None):
    try:
        with open(p) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return d


def control_meta(base, run_id):
    m = load(os.path.join(base, run_id, "manifest.json"), {})
    # An in-flight run (dir created but manifest not yet final) must never be
    # offered as a Control: its fields would be empty and a build-hash/terminal
    # match against it is meaningless.  `final` is only set at the very end of
    # write_manifest, so a missing/empty manifest is skipped by the caller.
    if not m.get("final") or not m.get("gem5_sha256"):
        return None
    # Skip stub/alias control dirs whose manifest `trace` points at a DIFFERENT
    # run dir's trace file (observed for CTRL-M02-C0X vs CTRL-M02-C0X-PFN and
    # CTRL-M04-C0X vs CTRL-M04-C0X-DECOY).  Such a dir is not an authoritative
    # control: its own on-disk trace differs from the trace its manifest claims,
    # so offering it would report a wrong ControlRunID for the right trace hash.
    trace = m.get("trace", "")
    if trace:
        trace_run_dir = os.path.basename(os.path.dirname(os.path.dirname(trace)))
        if trace_run_dir and trace_run_dir != run_id:
            return None
    return {
        "run_id": run_id,
        "base": base,
        "build_hash": m.get("gem5_sha256", ""),
        "trace": m.get("trace", ""),
        "trace_sha256": m.get("trace_sha256", ""),
        "rcs_sha256": m.get("rcs_sha256", ""),
        "terminal_sha256": m.get("terminal_sha256", ""),
        "eligible_total": int((m.get("eligible_summary") or {}).get(
            "eligible_total", 0) or 0),
        "activation_count": m.get("activation_count"),
        "terminal_lines": m.get("terminal_lines") or [],
        "manifest": m,
    }


def registry():
    """{(ModelID, NewContext): [control_meta, ...]} across all three rounds."""
    reg = {}
    for kind, base, prefix in RUN_BASES:
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base)):
            if not d.startswith(prefix):
                continue
            m = _MODEL_CTX.search(d)
            if not m:
                continue
            key = (m.group(1), m.group(2))
            meta = control_meta(base, d)
            if meta is not None:
                reg.setdefault(key, []).append(meta)
    return reg


def resolve_control(model, context, fault_build_hash, reg=None):
    """Pick the build-matched Control for a Fault.

    Returns ``(record_or_None, build_matches)``.  ``build_matches`` is True only
    when the chosen Control's gem5 build hash equals the Fault's.  When no exact
    build match exists the most recent round's Control is returned with
    ``build_matches=False`` so the caller can fail A20 honestly.
    """
    if reg is None:
        reg = registry()
    cands = reg.get((model, context), [])
    if not cands:
        return None, False
    for c in cands:
        if c["build_hash"] == fault_build_hash:
            return c, True
    # no exact build match: fall back to the most recent round's Control
    best = cands[0]
    for c in cands:
        if c["base"].endswith("RETRY2"):
            best = c
    return best, False


def write_control_map(cond_rows, fault_manifest_for, out_path=None):
    """Materialise the Fault<->Control map to ``analysis/control_map.json``.

    Each row records the fault's build hash and the resolved Control's build
    hash, plus the golden eligible N, trace path and SHA256, so the map is
    independently auditable (A20 / delivery manifest)."""
    reg = registry()
    out_path = out_path or os.path.join(ANALYSIS, "control_map.json")
    rows = []
    for c in cond_rows:
        sid = c["NewSampleRunID"]
        model, ctx = c["ModelID"], c["NewContext"]
        fm = fault_manifest_for(sid)
        fbuild = (fm or {}).get("gem5_sha256", "")
        rec, matches = resolve_control(model, ctx, fbuild, reg)
        rows.append({
            "SampleRunID": sid,
            "ModelID": model,
            "ContextID": ctx,
            "ControlID": c["ControlID"],
            "FaultBuildHash": fbuild,
            "FaultTraceSHA256": (fm or {}).get("trace_sha256", ""),
            "ControlRunID": (rec or {}).get("run_id", ""),
            "ControlBuildHash": (rec or {}).get("build_hash", ""),
            "ControlTracePath": (rec or {}).get("trace", ""),
            "ControlTraceSHA256": (rec or {}).get("trace_sha256", ""),
            "ControlRcsSHA256": (rec or {}).get("rcs_sha256", ""),
            "ControlEligibleN": (rec or {}).get("eligible_total", ""),
            "BuildMatches": bool(matches),
        })
    try:
        with open(out_path, "w") as fh:
            json.dump(rows, fh, indent=1, sort_keys=True)
    except OSError:
        pass
    return rows


if __name__ == "__main__":
    reg = registry()
    print("control registry: %d (model,context) cells" % len(reg))
    for key in sorted(reg):
        cands = reg[key]
        print("  %s-%s:" % key)
        for c in cands:
            print("    %-24s build=%.16s N=%s" %
                  (c["run_id"], c["build_hash"], c["eligible_total"]))
