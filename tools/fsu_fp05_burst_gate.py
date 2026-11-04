#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_fp05_burst_gate.py — FP05 burst contract gate (read-only).

FP05 (workbook row ``FSU-FP05-*``) is a *burst* model, not a per-event
Bernoulli model:

    "在 2–4 个连续 eligible 结果上污染同 lane 或相邻 lane；
     不将 burst 事件当独立 Bernoulli 样本"

The workbook requires every burst event to carry ``burst_id``,
``burst_ordinal`` and ``burst_length`` (empty ``burst_id`` on every event is
NOT a burst).  One F0 injection unit is one burst *episode*, not one event.
``recurring_result_stuck`` / ``permanent_stuck`` repeat the same mask on every
eligible event and are explicitly NOT a burst; a stream may never count them
as one.

This tool validates a FSU PROP event stream against that contract.  It is
strictly read-only: it never writes into ``runs/`` and never launches gem5.

Status
------
``PASS``  every hard check passed: >=1 contiguous episode, each with a fixed
          ``burst_id``, ``burst_length`` in {2,3,4}, ordinals exactly
          ``0..len-1``, no interleaving/reuse of a burst id.
``FAIL``  the stream contradicts the contract (length out of range, duplicate
          or missing ordinal, an id reappearing after another burst, a
          recurring event tagged as a burst, mixed tagged/untagged events, or
          burst-tagged evidence while the source tree has no burst emitter).
``SKIP``  the evidence is missing, not wrong: no events, no FP05 events, no
          burst-tagged events, or the current CHAOSFPU source has no burst
          implementation.  ``blocked`` is true when the source itself lacks
          the emitter.  A SKIP is never a PASS.

Exit codes: 0 = PASS, 1 = FAIL, 2 = SKIP.

Usage
-----
    python3 tools/fsu_fp05_burst_gate.py                 # source check only
    python3 tools/fsu_fp05_burst_gate.py --stream prop_evt.txt.gz --json
    python3 tools/fsu_fp05_burst_gate.py --stream events.txt --source-root .

Event line format (one of the two prefixes used by the repo)::

    FSU_PROP-EVT: kind=fault_applied model_id=FP05 burst_id=3 ...
    PROP-EVT: kind=fault_applied model_id=FP05 burst_id=3 ...
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FPU_CC = "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc"
FPU_HH = "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.hh"
FPU_PY = "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.py"

PREFIXES = ("FSU_PROP-EVT:", "PROP-EVT:")
BURST_MIN = 2
BURST_MAX = 4
BURST_FIELDS = ("burst_id", "burst_ordinal", "burst_length")
MODEL = "FP05"

# A recurring/permanent stream uses these markers.  They are exposures of one
# repeated per-event pattern, never a burst episode.
RECURRING_FIELDS = {"recurring_result_stuck", "permanent_stuck"}
RECURRING_KINDS = {"fault_installed", "exposure"}


def _int(value):
    """Parse an int from decimal/0x text; '' / None / garbage -> None."""
    text = str(value if value is not None else "").strip()
    if not text:
        return None
    try:
        return int(text, 0)
    except ValueError:
        try:
            return int(text, 10)
        except ValueError:
            return None


def parse_stream_text(text):
    """Parse PROP/FSU_PROP event lines into dicts (order preserved)."""
    events = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        body = None
        for prefix in PREFIXES:
            if line.startswith(prefix):
                body = line[len(prefix):].strip()
                break
        if body is None:
            continue
        ev = {}
        for tok in body.split():
            if "=" not in tok:
                continue
            key, value = tok.split("=", 1)
            ev[key] = value
        if ev:
            events.append(ev)
    return events


def read_stream(path):
    """Read a plain or gzip PROP event file. Raises OSError if unreadable."""
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            return parse_stream_text(f.read())
    return parse_stream_text(path.read_text(encoding="utf-8",
                                             errors="replace"))


def is_recurring(ev):
    """True for recurring/permanent per-event repetition, never a burst."""
    if ev.get("kind", "") in RECURRING_KINDS:
        return True
    if ev.get("field", "") in RECURRING_FIELDS:
        return True
    if ev.get("f0_mode", "") in RECURRING_FIELDS:
        return True
    if ev.get("mode", "") in RECURRING_FIELDS:
        return True
    # permanent stuck-at provenance
    if str(ev.get("stuck_polarity", "")).strip():
        return True
    if str(ev.get("fixed_mask", "")).strip():
        return True
    return False


def _applied(ev):
    return ev.get("kind", "") == "fault_applied"


def _filter_fp05(events):
    """Prefer model_id=FP05 rows; fall back to all rows if untagged."""
    have_model = [e for e in events if str(e.get("model_id", "")).strip()]
    if not have_model:
        return list(events), False
    return [e for e in events if e.get("model_id", "") == MODEL], True


def check_source_support(root=ROOT):
    """Read-only check: does this source tree emit the burst fields at all?

    The signal is the QUOTED emitter literal (``{"burst_id", ...}``) in
    CHAOSFPU.cc.  A comment mentioning "burst" does not count.
    """
    root = Path(root)
    cc = root / FPU_CC
    hh = root / FPU_HH
    py = root / FPU_PY
    texts = {}
    for path in (cc, hh, py):
        try:
            texts[path.name] = path.read_text(encoding="utf-8",
                                              errors="replace")
        except OSError:
            texts[path.name] = ""
    emitter = texts.get("CHAOSFPU.cc", "")
    present = {}
    for field in BURST_FIELDS:
        present[field] = re.search(r'"%s"' % re.escape(field), emitter) \
            is not None
    missing = [f for f in BURST_FIELDS if not present[f]]
    return {
        "implemented": not missing,
        "present": present,
        "missing": missing,
        "source_files": {
            "cc": str(cc),
            "cc_readable": cc.is_file(),
            "hh": str(hh),
            "hh_readable": hh.is_file(),
            "py": str(py),
            "py_readable": py.is_file(),
        },
        "note": ("CHAOSFPU has no burst_id/burst_ordinal/burst_length emitter; "
                 "recurring_result_stuck is a per-event repetition, not a "
                 "burst" if missing else "burst emitter literals found"),
    }


def _check(name, ok, detail=""):
    return {"check": name, "ok": bool(ok), "detail": detail}


def _episode_report(burst_id, rows):
    """Validate one contiguous burst_id run. Returns (report, missing, ok)."""
    missing = []
    ordinals = []
    declared = []
    eligible = []
    for ev in rows:
        o = _int(ev.get("burst_ordinal"))
        if o is None:
            missing.append("burst_ordinal")
        ordinals.append(o)
        n = _int(ev.get("burst_length"))
        if n is None:
            missing.append("burst_length")
        declared.append(n)
        eligible.append(_int(ev.get("eligible_ordinal")))

    length = len(rows)
    report = {
        "burst_id": burst_id,
        "events": length,
        "ordinals": ordinals,
        "declared_length": declared[0] if declared else None,
        "eligible_ordinals": eligible,
    }
    ok = True
    checks = []

    if None not in ordinals:
        seq_ok = ordinals == list(range(length))
        checks.append(_check(
            "ordinal_0_to_len_minus_1",
            seq_ok,
            "burst_id=%s ordinals=%s expected=%s" %
            (burst_id, ordinals, list(range(length)))))
        ok = ok and seq_ok
        dup = len(set(ordinals)) != len(ordinals)
        checks.append(_check(
            "ordinal_unique", not dup,
            "burst_id=%s ordinals=%s" % (burst_id, ordinals)))
        ok = ok and not dup
    else:
        # Missing values are missing EVIDENCE, not a contract violation.
        missing.append("burst_ordinal")

    if None not in declared:
        fixed = len(set(declared)) == 1
        declared_len = declared[0]
        checks.append(_check(
            "length_declared_constant", fixed,
            "burst_id=%s declared=%s" % (burst_id, declared)))
        ok = ok and fixed
        in_range = BURST_MIN <= declared_len <= BURST_MAX
        checks.append(_check(
            "length_in_2_4", in_range,
            "burst_id=%s declared_length=%s" % (burst_id, declared_len)))
        ok = ok and in_range
        matches = declared_len == length
        checks.append(_check(
            "length_matches_events", matches,
            "burst_id=%s declared=%s actual=%s" %
            (burst_id, declared_len, length)))
        ok = ok and matches
    else:
        missing.append("burst_length")

    # eligible_ordinal is OPTIONAL here: the burst contract proper is
    # burst_id/burst_ordinal/burst_length.  When the stream carries it, the
    # burst must really be consecutive eligible results; when it does not, the
    # gate records "unknown" instead of inventing a pass or a skip.
    if None not in eligible:
        consecutive = all(eligible[i] + 1 == eligible[i + 1]
                          for i in range(len(eligible) - 1))
        checks.append(_check(
            "eligible_ordinal_consecutive", consecutive,
            "burst_id=%s eligible=%s" % (burst_id, eligible)))
        ok = ok and consecutive
        report["eligible_consecutive"] = consecutive
    else:
        report["eligible_consecutive"] = "unknown"

    report["checks"] = checks
    # De-duplicate while preserving order.
    report["missing"] = sorted(set(missing))
    return report, ok


def check_burst_stream(events):
    """Validate FP05 burst semantics of one in-memory event list."""
    events, had_model = _filter_fp05(events)
    applied = [e for e in events if _applied(e)]

    checks = []
    evidence_missing = []
    result = {
        "status": "SKIP",
        "blocked": False,
        "reason": "",
        "checks": checks,
        "evidence_missing": evidence_missing,
        "burst_episode_count": 0,
        "burst_event_count": 0,
        "recurring_event_count": 0,
        "episodes": [],
        "model_filter": "FP05" if had_model else "all-events",
    }

    # Count recurring/permanent evidence across the whole (filtered) stream:
    # it is excluded from bursts whether or not it is a `fault_applied` row
    # (an F5 exposure is recurring evidence too).
    result["recurring_event_count"] = sum(1 for e in events if is_recurring(e))

    if had_model and not events:
        result["reason"] = "no FP05 events in the stream"
        result["evidence_missing"] = ["FP05 fault_applied events"]
        return result
    if not applied:
        result["reason"] = "no fault_applied events in the stream"
        result["evidence_missing"] = ["fault_applied events"]
        if result["recurring_event_count"]:
            result["evidence_missing"].extend(BURST_FIELDS)
            result["evidence_missing"].append(
                "burst evidence (only recurring/permanent events present)")
        return result

    recurring = [e for e in applied if is_recurring(e)]
    normal = [e for e in applied if not is_recurring(e)]

    # Recurring/permanent events must never carry burst tags: that would be
    # the exact "recurring 被误计为 burst" failure.
    mislabeled = [e for e in recurring
                  if any(str(e.get(f, "")).strip() for f in BURST_FIELDS)]
    ok = not mislabeled
    checks.append(_check(
        "recurring_not_burst_tagged", ok,
        "%d recurring/permanent event(s) carry burst fields" %
        len(mislabeled)))
    if not ok:
        result["status"] = "FAIL"
        result["reason"] = ("recurring/permanent events tagged as a burst "
                            "(recurring is not a burst)")
        result["evidence_missing"] = []
        return result

    def _tagged(ev):
        return any(str(ev.get(f, "")).strip() for f in BURST_FIELDS)

    tagged = [e for e in normal if _tagged(e)]
    untagged = [e for e in normal if not _tagged(e)]

    if tagged and untagged:
        result["status"] = "FAIL"
        result["reason"] = ("mixed burst tagging: %d event(s) carry burst "
                            "fields, %d do not" %
                            (len(tagged), len(untagged)))
        checks.append(_check("all_events_tagged", False,
                             "%d untagged normal events" % len(untagged)))
        return result
    checks.append(_check("all_events_tagged", True, ""))

    if not tagged:
        result["reason"] = (
            "no burst-tagged events: burst_id/burst_ordinal/burst_length "
            "are absent (a per-event recurring/permanent stream is not a "
            "burst)")
        result["evidence_missing"] = ["burst_id", "burst_ordinal",
                                      "burst_length"]
        if recurring:
            result["evidence_missing"].append(
                "burst evidence (only recurring/permanent events present)")
        return result

    # Every tagged event must have all three fields: a partial tag cannot be
    # validated and is incomplete evidence, not a pass. Missing fields are
    # recorded in evidence_missing (SKIP), not as a contract FAIL.
    for field in BURST_FIELDS:
        missing_count = sum(1 for e in tagged
                            if not str(e.get(field, "")).strip())
        if missing_count:
            evidence_missing.append(field)
        else:
            checks.append(_check("field_%s_present" % field, True, ""))

    # Parse burst_id; a tagged event with no id cannot form an episode.
    ids = [_int(e.get("burst_id")) for e in tagged]
    if any(i is None or i < 0 for i in ids):
        result["status"] = "FAIL"
        result["reason"] = ("burst_id is not a non-negative integer on every "
                            "tagged event")
        checks.append(_check("burst_id_integer", False, str(ids)))
        return result
    checks.append(_check("burst_id_integer", True, ""))

    # Contiguous runs in stream order. A burst_id that reappears after another
    # burst means episodes were split or cross-mixed.
    runs = []
    for ev, bid in zip(tagged, ids):
        if not runs or runs[-1][0] != bid:
            runs.append((bid, [ev]))
        else:
            runs[-1][1].append(ev)
    seen = set()
    reappeared = []
    for bid, _rows in runs:
        if bid in seen:
            reappeared.append(bid)
        seen.add(bid)
    ok = not reappeared
    checks.append(_check(
        "burst_id_not_mixed", ok,
        "reappearing burst_id(s)=%s" % reappeared))
    if not ok:
        result["status"] = "FAIL"
        result["reason"] = ("a burst_id reappears after another burst "
                            "(cross-burst mixing / split episode)")
        result["evidence_missing"] = sorted(set(evidence_missing))
        return result

    all_ok = True
    for bid, rows in runs:
        ep, ok = _episode_report(bid, rows)
        result["episodes"].append(ep)
        checks.extend(ep["checks"])
        evidence_missing.extend(ep["missing"])
        result["burst_event_count"] += len(rows)
        all_ok = all_ok and ok

    result["burst_episode_count"] = len(runs)
    result["evidence_missing"] = sorted(set(evidence_missing))
    if not all_ok or any(not c["ok"] for c in checks):
        result["status"] = "FAIL"
        result["reason"] = "burst contract violated (see failed checks)"
        return result
    if result["evidence_missing"]:
        result["status"] = "SKIP"
        result["reason"] = ("burst fields present but required evidence is "
                            "missing: %s" %
                            ", ".join(result["evidence_missing"]))
        return result
    result["status"] = "PASS"
    result["reason"] = ("%d burst episode(s), %d event(s), all ordinals "
                        "0..len-1 and length in {%d,%d}" %
                        (result["burst_episode_count"],
                         result["burst_event_count"], BURST_MIN, BURST_MAX))
    return result


def build_report(stream_path=None, root=ROOT):
    """Full gate report: source support + optional stream validation."""
    source = check_source_support(root)
    report = {
        "gate": "fsu_fp05_burst_gate",
        "model": MODEL,
        "stream": str(stream_path) if stream_path else None,
        "source_support": source,
        "evidence_missing": [],
    }
    if stream_path is None:
        report.update({
            "status": "SKIP",
            "blocked": not source["implemented"],
            "reason": ("CHAOSFPU source has no burst emitter; no burst "
                       "evidence can exist yet"
                       if not source["implemented"] else
                       "burst emitter exists but no stream was supplied"),
            "evidence_missing": (["burst_id", "burst_ordinal",
                                  "burst_length", "stream"]
                                 if not source["implemented"]
                                 else ["stream"]),
        })
        return report

    try:
        events = read_stream(stream_path)
    except OSError as exc:
        report.update({
            "status": "FAIL",
            "blocked": False,
            "reason": "cannot read stream: %s" % exc,
            "evidence_missing": [],
        })
        return report

    stream = check_burst_stream(events)
    report.update(stream)
    report["source_support"] = source
    # Fail closed: a stream that claims bursts cannot come from a source tree
    # that has no burst emitter.
    if stream["status"] == "PASS" and not source["implemented"]:
        report["status"] = "FAIL"
        report["reason"] = ("stream claims a valid burst but the source tree "
                            "has no burst emitter (forged/stale evidence)")
    if report["status"] != "PASS" and not source["implemented"]:
        report["blocked"] = True
        for field in source["missing"]:
            if field not in report["evidence_missing"]:
                report["evidence_missing"].append(field)
    report["evidence_missing"] = sorted(set(report["evidence_missing"]))
    return report


def _print_text(report):
    print("FP05 BURST GATE: %s" % report["status"])
    print("reason: %s" % report.get("reason", ""))
    if report.get("blocked"):
        print("blocked: true (source has no burst emitter)")
    support = report.get("source_support") or {}
    if support:
        print("source: implemented=%s missing=%s" %
              (support.get("implemented"), support.get("missing")))
    print("burst_episodes=%s burst_events=%s recurring_events=%s" %
          (report.get("burst_episode_count", 0),
           report.get("burst_event_count", 0),
           report.get("recurring_event_count", 0)))
    for c in report.get("checks", []):
        print("  [%s] %s %s" %
              ("PASS" if c["ok"] else "FAIL", c["check"], c.get("detail", "")))
    if report.get("evidence_missing"):
        print("evidence_missing: %s" %
              ", ".join(report["evidence_missing"]))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="FP05 burst contract gate (read-only, no gem5)")
    ap.add_argument("--stream", help="PROP/FSU_PROP event file (.gz ok)")
    ap.add_argument("--source-root", default=str(ROOT),
                    help="repo root holding CHAOS/gem5/src/...")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args(argv)

    report = build_report(args.stream, args.source_root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return {"PASS": 0, "FAIL": 1, "SKIP": 2}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
