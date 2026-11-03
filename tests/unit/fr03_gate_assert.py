#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fr03_gate_assert.py — FR03 permanent physical-cell gate assertions.

Reads a real FSU_PROP-EVT stream (prop_evt.txt.gz) produced by a gem5 run
with CHAOSPhysReg attached in `phys` mode and checks the facts that a host
unit test cannot observe:

  * exactly one permanent-cell root (kind=fault_installed, field=permanent_stuck)
    with a fixed Vec target / mask / polarity;
  * every L2 operand_read / L5 commit / squash event belongs to that same
    physical cell (reg_class=vec, phys_reg=target) and uses the fixed
    mask/polarity (no drift);
  * an L5 witness is a REAL commit: kind=commit, detection_layer=L5,
    outcome=errant_commit, and its consumer_seq is a recorded operand_read
    of the target cell;
  * a squash is kind=squash with squashed=1, is NOT a commit, keeps the
    generation captured at the consumer read, and is followed by a later
    write to the same cell (the defect survives the squash);
  * every phys_write implements the fixed stuck operation on the target
    lane (after == force(before, mask, polarity), non-target bits intact),
    and every generation_change is followed by a write in the new
    generation (the defect survives free/realloc);
  * an old-generation consumer is never relabelled into a newer generation
    (L5 reg_generation must be one of that consumer's operand_read
    generations);
  * chain_end's terminal is honest (committed only with a real L5 commit;
    squashed only with squashes and no commit) and it carries BOTH exact
    counters: write_exposures_total (install + re-writes) and
    read_exposures_total (consumer reads), plus first_impact_sn /
    first_impact_latency / l5_witness_event / squash_events.

Usage:
    python3 tests/unit/fr03_gate_assert.py <prop_evt.txt.gz|dir> [--json-out F]

Exit 0 = PASS, 1 = FAIL (violations printed). This script never runs gem5.
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _load_prop_fields():
    path = REPO / "tools" / "fsu_prop_fields.py"
    spec = importlib.util.spec_from_file_location("fsu_prop_fields", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P = _load_prop_fields()

TERMINALS = ("committed", "squashed", "exposed_unconsumed", "not_activated")
L5_OUTCOMES = ("errant_commit", "sdc", "sdc_escape")


def _c(evt, key):
    return str(evt.get(key, "") or "").strip()


def _int(evt, key):
    text = _c(evt, key)
    if text == "":
        return None
    try:
        return int(text, 0)
    except ValueError:
        return None


def read_stream(path: Path):
    """Return (events, truncated). Accepts a .gz file or a directory."""
    if path.is_dir():
        candidates = sorted(path.rglob("prop_evt.txt.gz"))
        if not candidates:
            raise SystemExit(f"no prop_evt.txt.gz under {path}")
        path = candidates[0]
    truncated = False
    events = []
    try:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                evt = P.parse_line(line)
                if evt is not None:
                    events.append(evt)
    except (OSError, EOFError, zlib.error):
        # Honest truncation: a gzip tail that cannot be read is not a pass.
        truncated = True
    return events, truncated


def analyze(events, truncated=False):
    """Validate one FR03 permanent-cell stream. Returns a report dict."""
    report = {
        "ok": False,
        "truncated": bool(truncated),
        "fault_id": None,
        "target": {},
        "counts": {},
        "l5": {},
        "violations": [],
    }
    v = report["violations"]

    if truncated:
        v.append("stream_truncated")

    groups = {}
    for e in events:
        groups.setdefault(_c(e, "fault_id") or "<empty>", []).append(e)

    roots = []
    for fid, evts in groups.items():
        for e in evts:
            if (_c(e, "kind") == "fault_installed"
                    and _c(e, "field") == "permanent_stuck"):
                roots.append((fid, e, evts))
    if len(roots) != 1:
        v.append(f"permanent_root_count:{len(roots)}")
        return report

    fid, root, evts = roots[0]
    report["fault_id"] = fid
    root_id = _c(root, "event_id")
    target_phys = _c(root, "phys_reg")
    root_mask = _c(root, "fixed_mask")
    root_pol = _c(root, "stuck_polarity")
    report["target"] = {
        "reg_class": _c(root, "reg_class"),
        "phys_reg": target_phys,
        "fixed_mask": root_mask,
        "stuck_polarity": root_pol,
        "lane_width": _c(root, "lane_width"),
        "lane_offset": _c(root, "lane_offset"),
        "bit_in_lane": _c(root, "bit_in_lane"),
        "install_event": root_id,
    }
    if _c(root, "reg_class") != "vec":
        v.append("root_not_vec")
    if not target_phys or _int(root, "phys_reg") is None:
        v.append("root_missing_phys_reg")
    if not root_mask or not root_pol:
        v.append("root_missing_mask_or_polarity")

    def same_cell(e):
        return (_c(e, "reg_class") == _c(root, "reg_class")
                and _c(e, "phys_reg") == target_phys)

    # ------------------------------------------------------------------
    # L2 consumers: consumer_seq -> generations observed at the read.
    # ------------------------------------------------------------------
    operand_gens = {}
    operand_count = 0
    for e in evts:
        if _c(e, "kind") != "operand_read":
            continue
        operand_count += 1
        if not same_cell(e):
            v.append(f"operand_read_wrong_cell:{_c(e, 'event_id')}")
        seq = _c(e, "consumer_seq")
        if not seq:
            v.append(f"operand_read_without_consumer:{_c(e, 'event_id')}")
            continue
        operand_gens.setdefault(seq, set()).add(_c(e, "reg_generation"))
        if _c(e, "fixed_mask") != root_mask:
            v.append(f"operand_read_mask_drift:{_c(e, 'event_id')}")
        if _c(e, "stuck_polarity") != root_pol:
            v.append(f"operand_read_polarity_drift:{_c(e, 'event_id')}")

    # ------------------------------------------------------------------
    # L5 commits and squashes. Only real consumers may reach L5.
    # ------------------------------------------------------------------
    commits, squashes = [], []
    for e in evts:
        kind = _c(e, "kind")
        if kind == "commit":
            commits.append(e)
        elif kind == "squash":
            squashes.append(e)
        if kind == "commit" and _c(e, "detection_layer") != "L5":
            v.append(f"commit_without_L5:{_c(e, 'event_id')}")
        if kind == "squash" and _c(e, "detection_layer") == "L5":
            v.append(f"squash_claimed_L5:{_c(e, 'event_id')}")

    for e in commits:
        eid = _c(e, "event_id")
        if not same_cell(e):
            v.append(f"commit_wrong_cell:{eid}")
        seq = _c(e, "consumer_seq")
        if seq not in operand_gens:
            v.append(f"commit_without_operand_read:{eid}")
            continue
        if _c(e, "dyn_inst_seq") != seq:
            v.append(f"commit_dyn_seq_mismatch:{eid}")
        if _c(e, "install_event") != root_id:
            v.append(f"commit_wrong_install_event:{eid}")
        if _c(e, "outcome") not in L5_OUTCOMES:
            v.append(f"commit_bad_outcome:{eid}:{_c(e, 'outcome')}")
        if _c(e, "reg_generation") not in operand_gens[seq]:
            # Old/new generation must never be merged.
            v.append(f"commit_generation_join:{eid}")
        if _c(e, "fixed_mask") != root_mask:
            v.append(f"commit_mask_drift:{eid}")
        if _c(e, "stuck_polarity") != root_pol:
            v.append(f"commit_polarity_drift:{eid}")

    for e in squashes:
        eid = _c(e, "event_id")
        if _c(e, "squashed") != "1":
            v.append(f"squash_without_flag:{eid}")
        if not same_cell(e):
            v.append(f"squash_wrong_cell:{eid}")
        seq = _c(e, "consumer_seq")
        if seq not in operand_gens:
            v.append(f"squash_without_operand_read:{eid}")
            continue
        if _c(e, "kind") == "commit":
            v.append(f"squash_masquerades_as_commit:{eid}")
        if _c(e, "reg_generation") not in operand_gens[seq]:
            v.append(f"squash_generation_join:{eid}")

    # ------------------------------------------------------------------
    # Every write re-application must implement the SAME stuck operation:
    # after == force(before, fixed_mask, polarity), no non-target bit moved.
    # A squash / generation change must be followed by a later write to the
    # same cell (the defect survives both).
    # ------------------------------------------------------------------
    writes = [e for e in evts if _c(e, "kind") == "phys_write"]
    for e in writes:
        eid = _c(e, "event_id")
        if not same_cell(e):
            v.append(f"phys_write_wrong_cell:{eid}")
        if _c(e, "fixed_mask") != root_mask:
            v.append(f"phys_write_mask_drift:{eid}")
        if _c(e, "stuck_polarity") != root_pol:
            v.append(f"phys_write_polarity_drift:{eid}")
        before = _int(e, "before")
        after = _int(e, "after")
        mask = _int(e, "fixed_mask")
        pol = _int(e, "stuck_polarity")
        if None not in (before, after, mask, pol) and pol in (0, 1):
            expected = (before | mask) if pol else (before & ~mask)
            if after != expected:
                v.append(f"phys_write_apply_mismatch:{eid}")
            if ((before ^ after) & ~mask) != 0:
                v.append(f"phys_write_non_target_bit:{eid}")

    def _tick(e):
        return _int(e, "tick") or 0

    for e in squashes:
        eid = _c(e, "event_id")
        t = _tick(e)
        if not any(_tick(w) > t for w in writes):
            v.append(f"no_write_after_squash:{eid}")
    for e in evts:
        if _c(e, "kind") != "generation_change":
            continue
        new_gen = _c(e, "generation_new")
        if not any(_c(w, "reg_generation") == new_gen for w in writes):
            v.append(f"no_write_after_generation_change:{_c(e, 'event_id')}")

    # ------------------------------------------------------------------
    # chain_end: unique, honest terminal, exact split counters.
    # ------------------------------------------------------------------
    ends = [e for e in evts if _c(e, "kind") == "chain_end"]
    if len(ends) != 1:
        v.append(f"chain_end_count:{len(ends)}")
        return report
    end = ends[0]
    terminal = _c(end, "terminal")
    report["counts"] = {
        "exposures_total": _int(end, "exposures_total"),
        "write_exposures_total": _int(end, "write_exposures_total"),
        "read_exposures_total": _int(end, "read_exposures_total"),
        "commit_events": _int(end, "commit_events"),
        "squash_events": _int(end, "squash_events"),
        "consumers_recorded": _int(end, "consumers_recorded"),
        "observed_operand_reads": operand_count,
        "observed_phys_writes": len(writes),
        "observed_commits": len(commits),
        "observed_squashes": len(squashes),
    }
    report["l5"] = {
        "terminal": terminal,
        "first_impact_sn": _c(end, "first_impact_sn"),
        "first_impact_latency": _c(end, "first_impact_latency"),
        "l5_witness_event": _c(end, "l5_witness_event"),
    }
    if terminal not in TERMINALS:
        v.append(f"chain_end_bad_terminal:{terminal}")
    if terminal == "committed":
        if not commits:
            v.append("chain_end_claims_commit_without_L5")
        else:
            witness = _c(end, "l5_witness_event")
            if witness != _c(commits[0], "event_id"):
                v.append(f"l5_witness_mismatch:{witness}")
            if _c(end, "first_impact_sn") != _c(commits[0], "dyn_inst_seq"):
                v.append("first_impact_sn_mismatch")
            if _int(end, "first_impact_latency") is None:
                v.append("first_impact_latency_missing")
    elif terminal == "squashed":
        if commits:
            v.append("chain_end_squashed_but_L5_commit")
        if not squashes:
            v.append("chain_end_squashed_without_squash_events")
    elif terminal == "exposed_unconsumed":
        if commits or squashes:
            v.append("chain_end_exposed_unconsumed_with_consumer_terminal")
    elif terminal == "not_activated":
        if commits or squashes:
            v.append("chain_end_not_activated_with_consumer_terminal")

    write_total = _int(end, "write_exposures_total")
    read_total = _int(end, "read_exposures_total")
    exp_total = _int(end, "exposures_total")
    if write_total is None:
        v.append("write_exposures_total_missing")
    if read_total is None:
        v.append("read_exposures_total_missing")
    if write_total is not None and exp_total is not None \
            and write_total != exp_total:
        v.append(f"write_total_mismatch:{write_total}!={exp_total}")
    for name, total, observed in (
            ("write", write_total, len([e for e in evts
                                        if _c(e, "kind") == "phys_write"])),
            ("read", read_total, operand_count)):
        if total is not None and total < observed:
            v.append(f"{name}_total_underflow:{total}<{observed}")
    if write_total is not None and read_total is not None \
            and write_total + read_total == 0:
        v.append("no_read_or_write_exposures")

    if _int(end, "squash_events") is not None \
            and _int(end, "squash_events") != len(squashes):
        v.append(f"squash_events_mismatch:"
                 f"{_int(end, 'squash_events')}!={len(squashes)}")
    if _int(end, "commit_events") is not None \
            and _int(end, "commit_events") != len(commits):
        v.append(f"commit_events_mismatch:"
                 f"{_int(end, 'commit_events')}!={len(commits)}")

    report["ok"] = not v
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stream", type=Path,
                    help="prop_evt.txt.gz (or a run directory containing it)")
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument("--expect-terminal", default=None,
                    help="optional expected chain_end terminal")
    args = ap.parse_args(argv)

    events, truncated = read_stream(args.stream)
    report = analyze(events, truncated=truncated)
    if args.expect_terminal and report["l5"].get("terminal") \
            != args.expect_terminal:
        report["violations"].append(
            f"terminal_expected:{args.expect_terminal}"
            f"!=got:{report['l5'].get('terminal')}")
        report["ok"] = False
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.json_out:
        args.json_out.write_text(text + "\n", encoding="utf-8")
    print(text)
    if report["ok"]:
        print("FR03 GATE ASSERT: PASS")
        return 0
    print("FR03 GATE ASSERT: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
