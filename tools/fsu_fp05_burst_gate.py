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
# The real emitter must also emit the explicit episode terminal; a burst
# with no end record cannot prove how it ended (completed/run_exit/etc.).
BURST_LIFECYCLE_FIELDS = ("burst_end",)
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
    for field in BURST_FIELDS + BURST_LIFECYCLE_FIELDS:
        present[field] = re.search(r'"%s"' % re.escape(field), emitter) \
            is not None
    missing = [f for f in BURST_FIELDS + BURST_LIFECYCLE_FIELDS
               if not present[f]]
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


def check_burst_stream(events, require_end=False, expected_episodes=None):
    """Validate FP05 burst semantics of one in-memory event list.

    ``require_end`` makes the gate STRICT (used for formal F0 pilots): every
    episode must have exactly one explicit ``burst_end`` record whose reason
    is ``completed``, each applied event must carry ``attempted=1`` /
    ``applied=1`` and a real value hash.  Without it the historical rule-only
    behaviour is preserved (missing terminals are not silently PASSed: a
    stream with no burst tags is still SKIP).

    ``expected_episodes`` is the pre-registered F0 episode count (normally 1);
    a different count is a hard FAIL — one run must never silently start a
    second episode.
    """
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

    # A pre-registered formal episode count turns "no evidence" into a
    # contract failure: the run promised an episode and produced none.
    def _expected_empty():
        return expected_episodes is not None and expected_episodes > 0

    if had_model and not events:
        result["reason"] = "no FP05 events in the stream"
        result["evidence_missing"] = ["FP05 fault_applied events"]
        if _expected_empty():
            result["status"] = "FAIL"
            result["reason"] += (" (expected %d episode(s), got 0)"
                                 % expected_episodes)
        return result
    if not applied:
        result["reason"] = "no fault_applied events in the stream"
        result["evidence_missing"] = ["fault_applied events"]
        if _expected_empty():
            result["status"] = "FAIL"
            result["reason"] += (" (expected %d episode(s), got 0)"
                                 % expected_episodes)
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
        if _expected_empty():
            result["status"] = "FAIL"
            result["reason"] += (" (expected %d episode(s), got 0)"
                                 % expected_episodes)
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

    # ---- explicit episode terminal (`burst_end`) -------------------------
    # The workbook requires an explicit record when a burst ends (completed,
    # early run exit, or an impossible pre-registered geometry). A stream
    # that simply stops is not allowed to look complete.
    terminates = {}
    for idx, ev in enumerate(events):
        if ev.get("kind", "") != "burst_end":
            continue
        bid = _int(ev.get("burst_id"))
        terminates.setdefault(bid, []).append((idx, ev))

    evt_pos = {id(ev): idx for idx, ev in enumerate(events)}
    for bid, rows in runs:
        ends = terminates.get(bid, [])
        if len(ends) > 1:
            checks.append(_check(
                "single_burst_end", False,
                "burst_id=%s has %d burst_end records" % (bid, len(ends))))
            all_ok = False
            continue
        if not ends:
            if require_end:
                # Missing evidence, not a contract violation: SKIP (never a
                # PASS). A formal pilot must supply the terminal.
                evidence_missing.append("burst_end")
                checks.append(_check(
                    "burst_end_present", True,
                    "burst_id=%s terminal missing -> evidence_missing"
                    % bid))
            else:
                checks.append(_check(
                    "burst_end_present", True,
                    "burst_id=%s terminal not required in rule-only mode"
                    % bid))
            continue
        end_idx, end_ev = ends[0]
        checks.append(_check("burst_end_present", True, ""))
        reason = str(end_ev.get("burst_end_reason", "")).strip()
        completed = reason == "completed"
        checks.append(_check(
            "burst_end_completed", completed,
            "burst_id=%s burst_end_reason=%r" % (bid, reason)))
        all_ok = all_ok and completed
        if completed:
            try:
                declared = int(str(end_ev.get("burst_length", "")), 0)
            except ValueError:
                declared = None
            ep = next((e for e in result["episodes"]
                       if e["burst_id"] == bid), None)
            want = ep["declared_length"] if ep else None
            checks.append(_check(
                "burst_end_length_matches", declared == want,
                "burst_id=%s end_length=%s declared=%s" %
                (bid, declared, want)))
            all_ok = all_ok and declared == want
            try:
                ep_events = int(str(end_ev.get("burst_episode_events", "")), 0)
            except ValueError:
                ep_events = None
            checks.append(_check(
                "burst_end_event_count", ep_events == len(rows),
                "burst_id=%s end_events=%s actual=%s" %
                (bid, ep_events, len(rows))))
            all_ok = all_ok and ep_events == len(rows)
        # The terminal must follow the last event of its own episode.
        last_idx = max((evt_pos[id(r)] for r in rows), default=-1)
        after = end_idx > last_idx
        checks.append(_check(
            "burst_end_after_events", after,
            "burst_id=%s end_pos=%s last_event_pos=%s" %
            (bid, end_idx, last_idx)))
        all_ok = all_ok and after
        # Accounting must reconcile (explicit, never inferred).
        acct = str(end_ev.get("burst_accounting_ok", "")).strip()
        if acct:
            checks.append(_check(
                "burst_accounting_ok", acct == "1",
                "burst_id=%s burst_accounting_ok=%s" % (bid, acct)))
            all_ok = all_ok and acct == "1"

    if expected_episodes is not None:
        match = result["burst_episode_count"] == expected_episodes
        checks.append(_check(
            "episode_count_matches_expected", match,
            "expected=%s actual=%s" %
            (expected_episodes, result["burst_episode_count"])))
        all_ok = all_ok and match

    if require_end:
        # Per-event identity/propagation evidence and the multi-source
        # merge contract are hard requirements for a formal pilot.
        for ev in tagged:
            bid = _int(ev.get("burst_id"))
            ordn = _int(ev.get("burst_ordinal"))
            tag = "burst_id=%s ordinal=%s" % (bid, ordn)
            attempted = str(ev.get("attempted", "")).strip() == "1"
            applied = str(ev.get("applied", "")).strip() == "1"
            checks.append(_check("event_attempted_applied",
                                 attempted and applied, tag))
            all_ok = all_ok and attempted and applied
            has_hash = bool(str(ev.get("value_hash", "")).strip() or
                            str(ev.get("after_hash", "")).strip())
            checks.append(_check("event_value_identity", has_hash, tag))
            all_ok = all_ok and has_hash
        # Multi-source merge evidence can live on L2/L4/L5 events (not only
        # on the L0 roots): every declared merge count must name exactly that
        # many real burst fault ids, and each named id must be one of the
        # episode's applied events.
        # Every applied burst result must have an explicit propagation
        # terminal: an activated consumer read, an explicit squash, or an
        # honest not_activated. A fault that simply disappears is rejected.
        terminals = set()
        for ev in events:
            fid = str(ev.get("fault_id", ""))
            kind = ev.get("kind", "")
            if kind == "operand_read" and str(
                    ev.get("activated", "")).strip() == "1":
                terminals.add(fid)
            elif kind in ("not_activated", "squash"):
                terminals.add(fid)
        for ev in tagged:
            fid = str(ev.get("fault_id", ""))
            ok_term = fid in terminals
            checks.append(_check(
                "event_terminal_evidence", ok_term,
                ("fault_id=%s terminal present" % fid) if ok_term else
                ("fault_id=%s has no activation/squash/not_activated "
                 "terminal" % fid)))
            all_ok = all_ok and ok_term

        burst_fault_ids = {str(e.get("fault_id")) for e in tagged}
        for ev in events:
            merged = str(ev.get("burst_merged_sources", "")).strip()
            if not merged:
                continue
            try:
                n = int(merged, 0)
            except ValueError:
                n = -1
            # n == 0 is the aggregate/lifecycle form (e.g. burst_end reports
            # "no merged sources"). It advertises no merge, so it is not a
            # lost-merge violation; positive merges still need real source ids.
            if n == 0:
                continue
            src = [s for s in str(
                ev.get("burst_source_fault_ids", "")).split(",") if s]
            ok_merge = (n >= 1 and len(src) == n
                        and all(s in burst_fault_ids for s in src))
            checks.append(_check(
                "merged_sources_not_lost", ok_merge,
                "kind=%s event_id=%s merged=%s sources=%s" %
                (ev.get("kind", ""), ev.get("event_id", ""), merged, src)))
            all_ok = all_ok and ok_merge

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
                        "0..len-1 and length in [%d,%d]" %
                        (result["burst_episode_count"],
                         result["burst_event_count"], BURST_MIN, BURST_MAX))
    return result


def build_report(stream_path=None, root=ROOT, require_end=False,
                 expected_episodes=None):
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
                                  "burst_length", "burst_end", "stream"]
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

    stream = check_burst_stream(events, require_end=require_end,
                                expected_episodes=expected_episodes)
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
    ap.add_argument("--require-end", action="store_true",
                    help="strict formal mode: every episode must have one "
                         "burst_end with reason=completed + per-event "
                         "identity/merge evidence")
    ap.add_argument("--expected-episodes", type=int, default=None,
                    help="pre-registered F0 episode count (normally 1)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args(argv)

    report = build_report(args.stream, args.source_root,
                          require_end=args.require_end,
                          expected_episodes=args.expected_episodes)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return {"PASS": 0, "FAIL": 1, "SKIP": 2}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
