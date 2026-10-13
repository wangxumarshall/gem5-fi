#!/usr/bin/env python3
"""ooo_l3.py -- FIX-B offline L3 source->consumer propagation-chain builder.

Central mandate (2026-10-13 FIX-B): replace L3=unsupported for the decode
fault family with a REAL propagation chain, built by joining the L0
injection event (decode_injections.log, now carrying the injected DynInst's
seqNum as sn=) to the v2 commit trace (CHAOSCommitTrace --ctrace_v2: every
committed row carries seqencNum = DynInst::seqNum plus per-source
(class,arch,phys) triples), then BFS-ing the source->consumer dataflow by
phys-register matching over subsequent committed rows.

HONESTY RULES (hard):
  * The ONLY propagation evidence is a committed row's SOURCE triple
    matching a chain node's DEST triple (a real read of the register the
    corrupted instruction defined). No ref-vs-empty-run differencing, no
    PRF-write-liveness proxies, no fabricated hops.
  * Kill rule (correctness of the phys match): commit order is program
    order, so once a LATER committed row re-defines the same (class,phys)
    register, the older value is dead and later src matches on that phys
    are NOT consumers of our chain (the phys index may have been freed and
    reused). The scan processes rows in file order and kills on redef.
  * Evidence not available => reported, never invented:
      - v1 ctrace (no seqencNum column)        -> status unsupported
      - L0 events without sn (pre-FIX-B logs)  -> status unsupported
      - scan/hop budgets exhausted             -> honest truncation note
      - squash events observed but not matching any live key are NOT
        reported as consumers.
  * v2 ctrace (this builder's input) always records squash events when
    they occur (FIX-B unit 2); a squashed CONSUMER is visible through its
    `# squash <sn> <tick> [class arch phys]...` line when the squashed
    instruction's own src triples match a live chain key. Squashed
    instructions never appear as committed rows (they retire from the ROB
    via commit.cc's isSquashed path without reaching commitHead).

API (library):
    build_l3(component, l0_events, run_ctrace_path, coverage=None,
             first_divergent_commit=None) -> dict
      component   "decode" (fetch-site encoding-corruption family, the
                  FIX-B target) or "rename" (RAT family: same source_read
                  matching when the L0 event carries sn/phys tags).
                  Anything else -> status "unsupported" (no silent scope
                  creep into other components' semantics).
      l0_events   list of injection-event dicts (directly the `events`
                  list of tools/ooo_observation.parse_injection_log on a
                  FIX-B decode_injections.log, or hand-built dicts with
                  the same field names: tick/mode/pc/orig_enc/new_enc/
                  bits/sn/...). The FIRST event carrying an integer sn is
                  the chain source (single-fault regime of the formal
                  campaign); the rest are reported in the counts.
      run_ctrace_path  v2 commit trace of the SAME run (gzip or plain).
      coverage    opaque run-coverage context from the observation chain
                  (recorded verbatim in the result; NOT used as evidence).
      first_divergent_commit  commit-seq of the first L2 divergence if
                  known: the BFS window ENDS at that row (inclusive) --
                  beyond it the committed stream is already divergent and
                  the chain is not extended.

Result schema (pinned by the FIX-B mandate):
    {status: "ok"|"unsupported"|"error",
     method: "source_read",
     component, injected: {seqencNum, pc, tick, field, bit, orig, new},
     source_row: {...}|null, hops: [{seqencNum, seq, pc, op,
       via_src: {class,arch,phys}, dest: {class,arch,phys}, committed}],
     squashed_consumers: [...] | "n/a",
     first_divergent_commit, coverage, caveat, ...honest counters}

CLI:
  python3 tools/ooo_l3.py --component decode --l0-log decode_injections.log \
      --ctrace commit_trace.csv.gz [--fdc N] [--json OUT.json] [--max-rows N]
"""

import argparse
import json
import os
import re
import sys

# One parser, no drift: row/annotation parsing is commit_diff.py's (FIX-B
# unit 4 made it v2-aware); this module reuses it and only adds the squash
# event interpretation on top.
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from commit_diff import (  # noqa: E402
    TraceError, open_text, parse_line,
)

# "rat" is the manifest target.component name of the CHAOSRenameMap
# injector; "rename" is the same family's library name (kept for the
# FIX-B docstring/CLI vocabulary).
SUPPORTED_COMPONENTS = ("decode", "rename", "rat")

# Circuit breakers (honest truncation, never silent):
MAX_HOPS = 1000            # chain fanout bound
MAX_ROWS_AFTER_SOURCE = 200000  # linear-scan window bound after the source
MAX_SQUASH_CONSUMERS = 1000

_SQUASH_RE = re.compile(
    r"^# squash (\d+) (\d+)((?: -?\d+ -?\d+ -?\d+)*)\s*$")


class L3Error(Exception):
    """Loud, user-facing input error (status "error")."""


# ------------------------------------------------------------- ctrace events

def iter_ctrace_events(path):
    """Yield ("row", Rec) / ("squash", dict) / ("marker", text) in file
    order from a v1-or-v2 commit trace. Malformed input raises TraceError
    (from commit_diff.parse_line) or L3Error (unknown annotation)."""
    fh = open_text(path)
    lineno = 0
    try:
        for raw in fh:
            lineno += 1
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue
            if line.startswith("#"):
                m = _SQUASH_RE.match(line)
                if m:
                    sn = int(m.group(1))
                    tick = int(m.group(2))
                    srcs = []
                    nums = m.group(3).split()
                    if len(nums) % 3 != 0:
                        raise L3Error(
                            "%s: line %d: squash src triples not a "
                            "multiple of 3: %r" % (path, lineno, line))
                    for i in range(0, len(nums), 3):
                        srcs.append((int(nums[i]), int(nums[i + 1]),
                                     int(nums[i + 2])))
                    yield ("squash", dict(sn=sn, tick=tick, srcs=srcs,
                                          raw=line, lineno=lineno))
                    continue
                if line.startswith("# ctrace v2"):
                    yield ("marker", line)
                    continue
                raise L3Error("%s: line %d: unknown '#'-annotation %r"
                              % (path, lineno, line))
            rec = parse_line(path, lineno, line)
            yield ("row", rec)
    finally:
        fh.close()


def _dest_triples(rec):
    return [(c, a, p) for (c, a, p, _v) in rec.dests]


def _src_triples(rec):
    return list(rec.srcs or [])


# ------------------------------------------------------------ L0 event input

def load_l0_events(path_or_events):
    """Accept a list of event dicts as-is, or a decode_injections.log path
    parsed with tools/ooo_observation.parse_injection_log (the L0 contract
    -- marker-wins event/skip split)."""
    if isinstance(path_or_events, list):
        return path_or_events
    import ooo_observation
    parsed = ooo_observation.parse_injection_log(path_or_events, "decode")
    return parsed["events"]


def _pick_source_event(events):
    """First event with an integer sn (the FIX-B join key). Returns
    (event, n_events, n_with_sn)."""
    n = len(events or [])
    with_sn = [e for e in (events or []) if isinstance(e, dict)
               and isinstance(e.get("sn"), int)]
    if not with_sn:
        return None, n, 0
    return with_sn[0], n, len(with_sn)


# RegClassType int values as written into ctrace v2 (class,arch,phys)
# triples (src/cpu/reg_class.hh: IntRegClass=0, FloatRegClass=1,
# VecRegClass=2). CHAOSRenameMap targets only the vec ("V<n>",
# ", class=vec") and int ("X<n>", no tag) pools.
_REG_CLASS_TAG = {"vec": 2, "int": 0}
_RE_ARCH_NAME = re.compile(r"^[VX](\d+)$")


def _map_seed_from(event):
    """RAT map-corruption seed for a rename_setEntry map_bitflip-family
    event: the arch reg's mapping was corrupted old_phys -> new_phys, so
    the first reader RENAMED AFTER the fault carries the src triple
    (class, arch, new_phys) -- the wrong phys. Returns
    (class, arch, phys, tick, old_phys) or None when the tags are
    absent or not ints (no fabrication: no tags -> no join)."""
    if not isinstance(event, dict):
        return None
    cls = event.get("class")
    if isinstance(cls, str):
        cls = _REG_CLASS_TAG.get(cls.strip().lower())
    elif isinstance(cls, bool):
        cls = None
    arch = event.get("arch")
    if isinstance(arch, str):
        m = _RE_ARCH_NAME.match(arch.strip())
        arch = int(m.group(1)) if m else None
    phys = event.get("new_phys")
    tick = event.get("tick")
    old = event.get("old_phys")
    if not all(isinstance(x, int) and not isinstance(x, bool)
               for x in (cls, arch, phys, tick)):
        return None
    return cls, arch, phys, tick, \
        (old if isinstance(old, int) and not isinstance(old, bool)
         else None)


# ------------------------------------------------------------- chain builder

def build_l3(component, l0_events, run_ctrace_path, coverage=None,
             first_divergent_commit=None,
             max_hops=MAX_HOPS, max_rows=MAX_ROWS_AFTER_SOURCE):
    """Build the L3 source->consumer chain (see module docstring)."""
    if component not in SUPPORTED_COMPONENTS:
        return _unsupported(
            component, coverage, first_divergent_commit,
            "component %r outside the source_read builder's scope (%s); "
            "no L0->ctrace join semantics defined for it"
            % (component, ", ".join(SUPPORTED_COMPONENTS)))

    # FIX-RB integration contract: the pipeline (sample_runner do_l3 /
    # commit_diff) passes first_divergent_commit as the l2
    # first-divergent RECORD (a dict carrying "seq"); the CLI and the
    # unit tests pass a bare commit-seq int. Normalize once -- the
    # window bound uses the int, the result echoes the original.
    fdc_in = first_divergent_commit
    if isinstance(fdc_in, bool):
        fdc_seq = None
    elif isinstance(fdc_in, int):
        fdc_seq = fdc_in
    elif isinstance(fdc_in, dict):
        s = fdc_in.get("seq")
        fdc_seq = s if isinstance(s, int) and not isinstance(s, bool) \
            else None
    else:
        fdc_seq = None

    l0_events = load_l0_events(l0_events)
    src_event, n_events, n_with_sn = _pick_source_event(l0_events)
    if n_events == 0:
        return _unsupported(
            component, coverage, first_divergent_commit,
            "no L0 injection events in the log (nothing activated)")
    # RAT map-corruption family (rename/rat, map_bitflip* sub-modes): the
    # L0 event carries no sn (only the dest_reg_sub path logs one) but
    # carries the corrupted mapping tags (class/arch/old_phys/new_phys).
    # Join = the first committed reader of the WRONG phys triple.
    map_seed = None
    if n_with_sn == 0:
        if component in ("rename", "rat"):
            for e in l0_events:
                seed = _map_seed_from(e)
                if seed is not None:
                    src_event = e
                    map_seed = seed
                    break
        if map_seed is None:
            return _unsupported(
                component, coverage, first_divergent_commit,
                "L0 events carry no sn= join key and no rename map tags "
                "(class/arch/new_phys): the injected DynInst / corrupted "
                "mapping is not identifiable in the commit trace "
                "(pre-FIX-B decode log, or an untagged rename event)")

    if map_seed is not None:
        cls0, arch0, phys0, tick0, old0 = map_seed
        sn = None
        # a map-entry source has no seqencNum/pc -- those are DynInst
        # fields; the honest fields are the corrupted mapping itself
        injected = {
            "tick": src_event.get("tick"),
            "field": src_event.get("mode") or src_event.get("site"),
            "class": cls0, "arch": arch0,
            "old_phys": old0, "new_phys": phys0,
        }
    else:
        sn = src_event["sn"]
        injected = {
            "seqencNum": sn,
            "pc": src_event.get("pc"),
            "tick": src_event.get("tick"),
            "field": src_event.get("mode") or src_event.get("site"),
            "bit": src_event.get("bits"),
            "orig": src_event.get("orig_enc"),
            "new": src_event.get("new_enc"),
        }

    # ---- single pass: locate the source (sn row or map-entry reader),
    # then BFS in file order ----
    hops = []
    squashed_consumers = []
    squash_events_seen = 0
    saw_marker = False
    saw_v1_row = False
    source_row = None
    source_squashed = False
    # RAT map-entry mode: the seed (cls0, arch0, phys0) is live from
    # tick0 until the first committed reader (seed_consumed) or until a
    # later same-(class,arch) dest re-points the map entry (seed_killed).
    seed_triple = (cls0, arch0, phys0) if map_seed is not None else None
    seed_consumed = False
    seed_killed = False
    # live keys: (class, phys) -> dest triple of the chain node that most
    # recently defined it (kill-on-redef, see module docstring).
    live = {}
    rows_scanned_after_source = 0
    rows_seen = 0
    # [FIX-RB round 2] scan evidence (central directive): the range the
    # scan actually covered past the source, and why it ended -- "did
    # not scan" must never masquerade as "scanned, no consumers".
    scan_first_seq = None
    scan_last_seq = None
    scan_first_tick = None
    scan_last_tick = None
    terminal_reason = None
    _fdc_degenerate = False
    truncated = []
    fdc = fdc_seq

    try:
        for kind, payload in iter_ctrace_events(run_ctrace_path):
            if kind == "marker":
                saw_marker = True
                continue
            if kind == "squash":
                squash_events_seen += 1
                if seed_triple is not None and not seed_consumed:
                    # pre-consumer map window: a squashed instruction
                    # whose OWN src triple equals the corrupted mapping
                    # read the wrong phys but never commits -- an
                    # uncommitted terminal consumer (squash does NOT
                    # re-point the map entry; the seed stays live).
                    if len(squashed_consumers) < MAX_SQUASH_CONSUMERS:
                        for t in payload["srcs"]:
                            if (t[0], t[1], t[2]) == seed_triple:
                                squashed_consumers.append({
                                    "seqencNum": payload["sn"],
                                    "tick": payload["tick"],
                                    "via_src": {"class": t[0],
                                                "arch": t[1],
                                                "phys": t[2]},
                                    "committed": False,
                                })
                                break
                    elif len(squashed_consumers) >= \
                            MAX_SQUASH_CONSUMERS:
                        truncated.append("squash-consumer budget (%d) "
                                         "exhausted" % MAX_SQUASH_CONSUMERS)
                    continue
                if source_row is None:
                    if sn is not None and payload["sn"] == sn:
                        source_squashed = True
                    continue
                if len(squashed_consumers) >= MAX_SQUASH_CONSUMERS:
                    truncated.append("squash-consumer budget (%d) exhausted"
                                     % MAX_SQUASH_CONSUMERS)
                    continue
                for t in payload["srcs"]:
                    key = (t[0], t[2])
                    if key in live and live[key] == tuple(t):
                        # A squashed instruction whose OWN src triple equals
                        # a live chain dest read the corrupted register.
                        # It never commits (squash path), so it is a
                        # terminal, uncommitted consumer.
                        squashed_consumers.append({
                            "seqencNum": payload["sn"],
                            "tick": payload["tick"],
                            "via_src": {"class": t[0], "arch": t[1],
                                        "phys": t[2]},
                            "committed": False,
                        })
                        break
                continue

            rec = payload  # a committed row
            rows_seen += 1
            if seed_triple is not None and source_row is None:
                # ---- RAT map-entry join: the corruption mutated the
                # by-reference phys_reg of the DEFINING instruction's
                # setEntry (CHAOSRenameMap.cc "Apply" block), so the
                # corrupted definer's own commit row carries the dest
                # triple (class, arch, new_phys) -- locate THAT row (the
                # first at/after the injection tick; rows renamed before
                # the corruption cannot carry it, and the freelist cannot
                # hand the same phys to two in-flight allocations), then
                # the standard dest->src BFS below takes over. The
                # standard kill rule already encodes the map semantics:
                # a later dest re-definition of the same (class, phys)
                # ends the window -- phys-reuse readers after a re-point
                # are never counted (verified on the retained FR02 SDC
                # sample: source seq 5268 dest (2,1,13), first reader
                # 5269, phys-reuse re-definition 5326/reader 5327).
                if rec.tick < tick0:
                    continue
                rows_scanned_after_source += 1
                if scan_first_seq is None:
                    scan_first_seq, scan_first_tick = rec.seq, rec.tick
                scan_last_seq, scan_last_tick = rec.seq, rec.tick
                if any(tuple(t) == seed_triple
                       for t in _dest_triples(rec)):
                    source_row = rec
                    seed_consumed = True   # downstream BFS is now live
                    for t in _dest_triples(rec):
                        live[(t[0], t[2])] = tuple(t)
                    terminal_reason = "source located (corrupted definer)"
                continue
            if source_row is None and not seed_consumed:
                # sn mode only: locate the source row (map mode reaches
                # the downstream BFS directly once its first consumer
                # seeded the live set)
                if rec.seqenc is None:
                    saw_v1_row = True
                    continue
                if sn is not None and rec.seqenc == sn:
                    source_row = rec
                    for t in _dest_triples(rec):
                        live[(t[0], t[2])] = tuple(t)
                continue

            # past the source row: window bounds first. [FIX-RB round 2]
            # The fdc bound applies only when it lies PAST the source
            # row; fdc <= source seq means the SOURCE ITSELF is the first
            # divergence -- the scan continues (run-side dataflow past
            # the divergent source is real propagation evidence) with a
            # caveat, instead of stopping at zero rows scanned.
            if fdc is not None and fdc > source_row.seq \
                    and rec.seq > fdc:
                terminal_reason = ("fdc window: committed stream already "
                                   "divergent past seq %d" % fdc)
                break  # window end: committed stream already divergent
            if fdc is not None and fdc <= source_row.seq:
                _fdc_degenerate = True
            rows_scanned_after_source += 1
            if scan_first_seq is None:
                scan_first_seq, scan_first_tick = rec.seq, rec.tick
            scan_last_seq, scan_last_tick = rec.seq, rec.tick
            if rows_scanned_after_source > max_rows:
                truncated.append(
                    "row-scan budget (%d rows after the source) exhausted; "
                    "chain truncated at seq %d" % (max_rows, rec.seq))
                terminal_reason = "row-scan budget exhausted"
                break

            # consumer test BEFORE kill: a row may read the old value and
            # (re)define the same phys in one instruction (read-then-write)
            consumer_via = None
            if live:
                for t in _src_triples(rec):
                    key = (t[0], t[2])
                    if key in live and live[key] == tuple(t):
                        consumer_via = tuple(t)
                        break

            if consumer_via is not None:
                if len(hops) >= max_hops:
                    truncated.append("hop budget (%d) exhausted at seq %d"
                                     % (max_hops, rec.seq))
                    break
                dests = _dest_triples(rec)
                dest_out = dict(zip(("class", "arch", "phys"),
                                    dests[0])) if dests else None
                hops.append({
                    "seqencNum": rec.seqenc,
                    "seq": rec.seq,
                    "pc": rec.pc,
                    "op": rec.op,
                    "via_src": {"class": consumer_via[0],
                                "arch": consumer_via[1],
                                "phys": consumer_via[2]},
                    "dest": dest_out,
                    "committed": True,
                })
                # the consumer's own dests now carry (possibly) corrupted
                # data -> they join the live set
                for t in dests:
                    live[(t[0], t[2])] = tuple(t)
            else:
                # not a consumer: its dests still KILL the phys keys they
                # redefine (program-order redefinition; the phys may be a
                # fresh allocation after a squash freed it)
                for t in _dest_triples(rec):
                    live.pop((t[0], t[2]), None)
    except TraceError as e:
        return _error(component, coverage, first_divergent_commit,
                      injected, str(e))
    except L3Error as e:
        return _error(component, coverage, first_divergent_commit,
                      injected, str(e))

    if map_seed is not None and not seed_consumed:
        # The corrupted mapping was re-pointed (or the window ended)
        # before any committed reader: an honest completed observation
        # with an empty propagation set -- never a fabricated hop.
        if saw_v1_row:
            return _unsupported(
                component, coverage, first_divergent_commit,
                "commit trace has no seqencNum column (v1 format): rerun "
                "the faulted run with --ctrace_v2 to make the map-entry "
                "join possible", injected=injected, n_events=n_events,
                n_with_sn=n_with_sn)
        caveat = ("the corrupted defining DynInst (dest class=%d, arch=%d, "
                  "phys=%d) never committed in the retained trace (squashed "
                  "in flight, or outside the window): no propagation row "
                  "exists to anchor the chain"
                  % (cls0, arch0, phys0))
        if truncated:
            caveat += "; " + "; ".join(truncated)
        return {
            "status": "ok",
            "method": "source_read",
            "component": component,
            "injected": injected,
            "source_row": None,
            "source_map_entry": {"class": cls0, "arch": arch0,
                                 "old_phys": old0, "new_phys": phys0,
                                 "tick": tick0},
            "source_committed": False,
            "source_squashed": False,
            "hops": [],
            "squashed_consumers": (squashed_consumers
                                   if squash_events_seen or
                                   squashed_consumers
                                   else "n/a (no squash events in this "
                                        "trace)"),
            "squash_events_observed": squash_events_seen,
            "n_l0_events": n_events,
            "n_l0_events_with_sn": n_with_sn,
            "rows_scanned_after_source": rows_scanned_after_source,
            "scan_range": (None if scan_first_seq is None else
                           {"first_seq": scan_first_seq,
                            "last_seq": scan_last_seq,
                            "first_tick": scan_first_tick,
                            "last_tick": scan_last_tick}),
            "terminal_reason": (terminal_reason or
                                "map-entry scan ended before the corrupted "
                                "definer committed (re-pointed, window "
                                "end, or trace end)"),
            "first_divergent_commit": fdc_in,
            "coverage": coverage,
            "caveat": caveat,
        }

    if source_row is None and map_seed is None:
        if saw_v1_row or (rows_seen == 0 and not saw_marker):
            return _unsupported(
                component, coverage, first_divergent_commit,
                "commit trace has no seqencNum column (v1 format): rerun "
                "the faulted run with --ctrace_v2 to make the L0 sn= join "
                "possible", injected=injected, n_events=n_events,
                n_with_sn=n_with_sn)
        if source_squashed:
            caveat = ("injected DynInst sn=%d was SQUASHED before commit "
                      "(squash event observed): the corruption never "
                      "reached the architectural state via this "
                      "instruction; no committed propagation exists"
                      % sn)
        elif rows_seen == 0:
            caveat = ("retained trace carries no committed rows at all: "
                      "nothing to join (honest n/a)")
        else:
            caveat = ("injected DynInst sn=%d never committed and no "
                      "squash event carries it either: it was still in "
                      "flight when the simulation ended (or squashed "
                      "before entering the ROB, or it committed outside "
                      "the retained window). No committed propagation "
                      "exists to trace." % sn)
        return {
            "status": "ok",
            "method": "source_read",
            "component": component,
            "injected": injected,
            "source_row": None,
            "source_committed": False,
            "source_squashed": source_squashed,
            "hops": [],
            "squashed_consumers": "n/a",
            "squash_events_observed": squash_events_seen,
            "n_l0_events": n_events,
            "n_l0_events_with_sn": n_with_sn,
            "first_divergent_commit": fdc_in,
            "coverage": coverage,
            "caveat": caveat,
        }

    if terminal_reason is None:
        terminal_reason = ("trace ended: no further committed rows past "
                           "the source" if rows_scanned_after_source > 0
                           else "no committed rows exist past the source")
    if not hops and rows_scanned_after_source > 0 \
            and terminal_reason.startswith("source located"):
        terminal_reason = ("scanned %d rows past the source: every live "
                           "key was killed by redefinition before any "
                           "consumer read it"
                           % rows_scanned_after_source)
    caveats = []
    if _fdc_degenerate:
        caveats.append("first_divergence seq %d <= source seq %d: the "
                       "source row itself is the first divergence; the "
                       "chain records the run-side dataflow past it"
                       % (fdc, source_row.seq))
    if squash_events_seen == 0:
        caveats.append("no squash events in this trace: consumers that "
                       "were squashed before commit are invisible here "
                       "(this trace records squash events whenever they "
                       "occur, so zero events = no squashes in the window)")
    if truncated:
        caveats.append("; ".join(truncated))
    if fdc is None:
        if fdc_in is None:
            caveats.append("no first_divergent_commit given: the chain was "
                           "followed to the end of the trace window")
        else:
            caveats.append("first_divergent_commit given in a form without "
                           "a usable integer seq (%r): no window bound "
                           "applied" % (fdc_in,))

    return {
        "status": "ok",
        "method": "source_read",
        "component": component,
        "injected": injected,
        "source_row": ({
            "seq": source_row.seq, "seqencNum": source_row.seqenc,
            "tick": source_row.tick, "pc": source_row.pc,
            "op": source_row.op,
            "dests": [dict(zip(("class", "arch", "phys", "val"), d))
                      for d in source_row.dests],
        } if source_row is not None else None),
        **({"source_map_entry": {"class": cls0, "arch": arch0,
                                 "old_phys": old0, "new_phys": phys0,
                                 "tick": tick0}}
           if map_seed is not None else {}),
        "source_committed": source_row is not None,
        "source_squashed": False,
        "hops": hops,
        "squashed_consumers": (squashed_consumers
                               if squash_events_seen or squashed_consumers
                               else "n/a (no squash events in this trace)"),
        "squash_events_observed": squash_events_seen,
        "n_l0_events": n_events,
        "n_l0_events_with_sn": n_with_sn,
        "rows_scanned_after_source": rows_scanned_after_source,
        "scan_range": (None if scan_first_seq is None else
                       {"first_seq": scan_first_seq,
                        "last_seq": scan_last_seq,
                        "first_tick": scan_first_tick,
                        "last_tick": scan_last_tick}),
        "terminal_reason": terminal_reason,
        "first_divergent_commit": fdc_in,
        "coverage": coverage,
        "caveat": "; ".join(caveats) if caveats else "none",
    }


# ------------------------------------------------------------ status helpers

def _base(component, coverage, fdc):
    return {
        "method": "source_read",
        "component": component,
        "coverage": coverage,
        "first_divergent_commit": fdc,
    }


def _unsupported(component, coverage, fdc, reason, injected=None,
                 n_events=None, n_with_sn=None):
    d = _base(component, coverage, fdc)
    d.update({
        "status": "unsupported",
        "reason": reason,
        "injected": injected,
        "hops": "n/a",
        "squashed_consumers": "n/a",
    })
    if n_events is not None:
        d["n_l0_events"] = n_events
        d["n_l0_events_with_sn"] = n_with_sn
    return d


def _error(component, coverage, fdc, injected, message):
    d = _base(component, coverage, fdc)
    d.update({
        "status": "error",
        "error": message,
        "injected": injected,
        "hops": "n/a",
        "squashed_consumers": "n/a",
    })
    return d


# ------------------------------------------------------------------- report

def format_report(res):
    lines = ["== ooo_l3 (FIX-B): L3 source->consumer propagation chain =="]
    lines.append("component: %s    method: %s    status: %s"
                 % (res.get("component"), res.get("method"),
                    res.get("status")))
    if res.get("status") == "unsupported":
        lines.append("[不支持] %s" % res.get("reason"))
        return "\n".join(lines)
    if res.get("status") == "error":
        lines.append("[错误] %s" % res.get("error"))
        return "\n".join(lines)
    inj = res.get("injected") or {}
    lines.append("注入: sn=%s pc=%s tick=%s field=%s bit=%s orig=%s new=%s"
                 % (inj.get("seqencNum"), inj.get("pc"), inj.get("tick"),
                    inj.get("field"), inj.get("bit"), inj.get("orig"),
                    inj.get("new")))
    if not res.get("source_committed"):
        lines.append("[源指令] sn=%s 未提交（传播在提交前终止）"
                     % inj.get("seqencNum"))
    else:
        sr = res.get("source_row") or {}
        lines.append("[源指令] seq=%s sn=%s pc=%s op=%s dests=%d"
                     % (sr.get("seq"), sr.get("seqencNum"), sr.get("pc"),
                        sr.get("op"), len(sr.get("dests") or [])))
    lines.append("[传播链] %d 跳 (committed 消费者)" % len(res.get("hops")
                                                          or []))
    for h in (res.get("hops") or [])[:20]:
        lines.append("  seq=%s sn=%s pc=%s op=%s via src(c=%s,a=%s,p=%s)"
                     " -> dest(c=%s,a=%s,p=%s)"
                     % (h["seq"], h["seqencNum"], h["pc"], h["op"],
                        h["via_src"]["class"], h["via_src"]["arch"],
                        h["via_src"]["phys"],
                        (h["dest"] or {}).get("class"),
                        (h["dest"] or {}).get("arch"),
                        (h["dest"] or {}).get("phys")))
    if len(res.get("hops") or []) > 20:
        lines.append("  ... (%d more hops)" % (len(res["hops"]) - 20))
    sq = res.get("squashed_consumers")
    if isinstance(sq, list):
        lines.append("[squash 路径消费者] %d" % len(sq))
        for s in sq[:10]:
            lines.append("  sn=%s tick=%s via src(c=%s,a=%s,p=%s)"
                         % (s["seqencNum"], s["tick"], s["via_src"]["class"],
                            s["via_src"]["arch"], s["via_src"]["phys"]))
    else:
        lines.append("[squash 路径消费者] %s" % sq)
    lines.append("first_divergent_commit: %s"
                 % res.get("first_divergent_commit"))
    lines.append("caveat: %s" % res.get("caveat"))
    return "\n".join(lines)


# ---------------------------------------------------------------------- cli

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="ooo_l3.py",
        description="FIX-B L3 source->consumer propagation-chain builder "
                    "(decode family). Inputs: the run's "
                    "decode_injections.log (FIX-B, with sn=) and the SAME "
                    "run's --ctrace_v2 commit trace.")
    ap.add_argument("--component", default="decode",
                    choices=list(SUPPORTED_COMPONENTS),
                    help="injector family (default decode)")
    ap.add_argument("--l0-log", required=True,
                    help="decode_injections.log of the faulted run")
    ap.add_argument("--ctrace", required=True,
                    help="commit trace (v2, gzip or plain) of the SAME run")
    ap.add_argument("--fdc", type=int, default=None, metavar="SEQ",
                    help="first divergent commit seq (L2): BFS window ends "
                         "at this row, inclusive")
    ap.add_argument("--max-rows", type=int, default=MAX_ROWS_AFTER_SOURCE,
                    help="row-scan budget after the source row (default %d)"
                         % MAX_ROWS_AFTER_SOURCE)
    ap.add_argument("--json", default=None, metavar="OUT",
                    help="write the result dict as JSON to this file")
    args = ap.parse_args(argv)

    try:
        res = build_l3(args.component, args.l0_log, args.ctrace,
                       coverage=None,
                       first_divergent_commit=args.fdc,
                       max_rows=args.max_rows)
    except (TraceError, L3Error) as e:
        sys.stderr.write("ooo_l3: ERROR: %s\n" % e)
        return 1

    print(format_report(res))
    if args.json is not None:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
            f.write("\n")
        sys.stderr.write("ooo_l3: json written to %s\n" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
