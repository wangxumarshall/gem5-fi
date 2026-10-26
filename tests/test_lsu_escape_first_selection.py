#!/usr/bin/env python3
"""test_lsu_escape_first_selection.py — [MDSPEC][R6-F5-NOEFFECT]

Pins the user ruling 2026-10-26c: for a **multi-injection** sample the
cell-level verdict is ESCAPE-FIRST — if ANY fault reaches `full` (a genuine
errant-commit escape) the sample headline is `full` and it admits via
`full_chain`; a `detected_contained` containment is the terminus ONLY when no
fault escapes.  All three fault-selection sites use ONE shared rule
(`lsu_chain_check.select_representative_fault`):
    terminal rank first (full > detected_contained > provable_to_*),
    tie-break by proven path length, then by fault id.

Two kinds of coverage below:
  * unit-level pins of the shared rule itself (ranking / tie-breaks /
    determinism), driven by explicit synthetic fault records;
  * integration-level pins over REAL-SHAPED gzip ``PROP-EVT:`` streams
    (field names/order mirror an actual sample, e.g. the n7 T03-F5-W4 seed1
    stream): a multi-fault stream with one escape + one containment selects
    the escape and admits via `full_chain`; an analogous no-escape stream
    selects the containment; and `containment_from_events` prefers a fault
    that actually yields a containment candidate over the raw-event-count max.

Usage: ``python3 tests/test_lsu_escape_first_selection.py`` (exit 0 = all PASS)
"""
import gzip
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as P          # noqa: E402
import lsu_chain_check as CC         # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


# ---------------------------------------------------------------------------
# real-shaped PROP-EVT stream writer
# ---------------------------------------------------------------------------
# Field order mirrors the live header (prop-evt v1) recorded in the n7
# stream.  Only the keys the checker reads are placed; the rest stay blank so
# the shape matches production bytes.
_HEADER = ("# prop-evt v1: kind run_id sample_run_id fault_id event_id "
           "parent_event_id tick cycle core_id thread_id dyn_inst_seq "
           "store_dyn_inst_seq commit_seq pc opcode lq_idx sq_idx request_id "
           "walk_id mshr_id fill_id pf_request_id va pa cache_line set way "
           "entry_index field before after state_before state_after arch_reg "
           "phys_reg detection_layer contained outcome oracle_diff "
           "evidence_status corr containment_layer containment_reason "
           "old_request_id new_request_id source_event_id dest_event_id "
           "bridge_layer bridge_reason shared_addr shared_size")


def _line(kind, run_id, fid, eid, parent, tick, **kw):
    """One real-shaped PROP-EVT record."""
    fields = {
        "kind": kind, "run_id": run_id, "sample_run_id": "s1",
        "fault_id": fid, "event_id": eid, "parent_event_id": parent,
        "tick": tick,
    }
    fields.update({k: v for k, v in kw.items() if v is not None})
    return "PROP-EVT: " + " ".join(f"{k}={v}" for k, v in fields.items())


def _write_stream(lines, name="prop_evt.txt.gz"):
    d = Path(tempfile.mkdtemp(prefix="r6_f5_noeffect_"))
    p = d / name
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        fh.write(_HEADER + "\n")
        fh.write("\n".join(lines) + "\n")
    return p


# --- TLB-family chain fragments (real T-series shapes) ---------------------
def _tlb_l0_l4(rid, fid, tag, t0=1):
    """L0→L4 provable prefix: inj/tlb_lookup/tlb_pfn/lq_read/taint_reg."""
    return [
        _line("inj", rid, fid, f"{tag}0", "", t0, corr="origin"),
        _line("tlb_lookup", rid, fid, f"{tag}1", f"{tag}0", t0 + 1,
              dyn_inst_seq=7, request_id=7, entry_index=1,
              field="post_lookup", state_before="x", state_after="y",
              corr="origin"),
        _line("tlb_pfn", rid, fid, f"{tag}2", f"{tag}1", t0 + 2,
              dyn_inst_seq=7, request_id=7, va="1000", pa="2000",
              field="pfn", old_pfn="1", new_pfn="2", corr="seq_primary"),
        _line("lq_read", rid, fid, f"{tag}3", f"{tag}2", t0 + 3,
              dyn_inst_seq=7, request_id=7, va="1000", pa="2000",
              corr="seq_primary"),
        _line("taint_reg", rid, fid, f"{tag}4", f"{tag}3", t0 + 4,
              dyn_inst_seq=7, request_id=7, corr="seq_primary"),
    ]


def _escape_tail(rid, fid, tag, t0):
    """L5 errant_commit (explicit detection) + lifecycle chain_end."""
    return [
        _line("errant_commit", rid, fid, f"{tag}5", f"{tag}4", t0 + 5,
              dyn_inst_seq=7, request_id=7, detection_layer="L5",
              outcome="errant_commit", contained="0", corr="taint_prop"),
        _line("chain_end", rid, fid, f"{tag}6", f"{tag}5", t0 + 6,
              outcome="run_end", detection_layer="None", contained="0",
              corr="none"),
    ]


def _squash_tail(rid, fid, tag, t0):
    """L5 contain-by-squash (explicit detection) + lifecycle chain_end."""
    return [
        _line("squash_masked", rid, fid, f"{tag}5", f"{tag}4", t0 + 5,
              dyn_inst_seq=7, request_id=7, va="1000", pa="2000",
              field="squashed_load", outcome="masked", detection_layer="L4",
              contained="1", containment_layer="L4",
              containment_reason="squash_replay", corr="addr_fallback"),
        _line("chain_end", rid, fid, f"{tag}6", f"{tag}5", t0 + 6,
              outcome="run_end", detection_layer="None", contained="0",
              corr="none"),
    ]


def _adm(rid, events, containment="derive", truncated=False, oracle=None):
    if containment == "derive":
        containment = CC.containment_from_events(events, rid,
                                                truncated=truncated)
    return CC.check_admission({
        "run_id": rid, "activated": 1, "events": events, "rc": 0,
        "truncated": truncated, "oracle_outcome": oracle,
        "containment": containment})


# =====================================================================
# 1. the shared rule itself
# =====================================================================
def test_select_helper_escape_first():
    """full outranks detected_contained outranks provable_to_*, even when the
    lower-ranked fault has a LONGER proven path."""
    faults = {
        "1": {"terminal": "detected_contained",
              "path_event_ids": ["a", "b", "c", "d", "e", "f", "g"]},
        "2": {"terminal": "full", "path_event_ids": ["a", "b", "c"]},
        "3": {"terminal": "provable_to_L4_then_unknown",
              "path_event_ids": ["a", "b", "c", "d", "e", "f"]},
    }
    fid, f = CC.select_representative_fault(faults)
    assert fid == "2" and f["terminal"] == "full", (fid, f)
    # containment beats provable even when the provable path is longer
    assert CC._terminal_rank("full") > CC._terminal_rank("detected_contained")
    assert CC._terminal_rank("detected_contained") > \
        CC._terminal_rank("provable_to_L5_then_unknown")


def test_select_helper_tiebreaks_and_determinism():
    """rank ties break by proven path length, then by fault id; and the
    selection is deterministic (same input -> same output)."""
    long_prov = {"terminal": "provable_to_L4_then_unknown",
                 "path_event_ids": list(range(7))}
    short_prov = {"terminal": "provable_to_L4_then_unknown",
                  "path_event_ids": list(range(5))}
    faults = {"7": long_prov, "3": long_prov, "9": short_prov}
    fid, _ = CC.select_representative_fault(faults)      # tie -> smallest id
    assert fid == "3", fid
    # path-length tie-break
    fid2, _ = CC.select_representative_fault({"1": short_prov, "2": long_prov})
    assert fid2 == "2", fid2
    # determinism
    outs = {CC.select_representative_fault(faults)[0] for _ in range(5)}
    assert outs == {"3"}, outs
    # empty input
    assert CC.select_representative_fault({}) == (None, None)


# =====================================================================
# 2. multi-injection stream with one escape + one containment
# =====================================================================
def test_multi_fault_escape_beats_containment():
    """(1) of the brief: a synthetic multi-fault sample with one `full` fault
    and one contained fault selects the `full` one and admits via
    `full_chain`.  The containment fault is listed FIRST (so a naive
    first/longest pick would have chosen it, as on the real n7 sample)."""
    rid = "T03-F5-W4"
    lines = (_tlb_l0_l4(rid, "1", "a", t0=1) + _squash_tail(rid, "1", "a", 1)
             + _tlb_l0_l4(rid, "2", "b", t0=20) + _escape_tail(rid, "2", "b", 20))
    p = _write_stream(lines)
    events, _tr = P.read_events(p)
    v = CC.check_chain(events)
    terms = {k: v["faults"][k]["terminal"] for k in v["faults"]}
    assert terms.get("1") == "detected_contained", terms
    assert terms.get("2") == "full", terms
    # shared rule picks the escape, NOT the first/longest containment
    fid, f = CC.select_representative_fault(v["faults"])
    assert fid == "2" and f["terminal"] == "full", (fid, f)
    # end-to-end admission: full chain, no violations
    r = _adm(rid, events)
    assert r["admitted"] is True, r["violations"]
    assert r["path"] == "full_chain", r["path"]
    assert r["terminal"] == "full", r["terminal"]


# =====================================================================
# 3. no-escape sample -> containment is the terminus
# =====================================================================
def test_no_escape_sample_selects_containment():
    """(2) of the brief: a synthetic no-escape sample with a containment
    selects the containment and admits via `contained`."""
    rid = "T04-F5-W4"
    lines = (_tlb_l0_l4(rid, "1", "a", t0=1) + _squash_tail(rid, "1", "a", 1)
             + _tlb_l0_l4(rid, "2", "b", t0=20)[:4])       # L0..L3 only
    p = _write_stream(lines)
    events, _tr = P.read_events(p)
    v = CC.check_chain(events)
    fid, f = CC.select_representative_fault(v["faults"])
    assert f["terminal"] == "detected_contained", (fid, v["faults"])
    r = _adm(rid, events)
    assert r["admitted"] is True, r["violations"]
    assert r["path"] == "contained", r["path"]
    assert r["terminal"] == "detected_contained", r["terminal"]


# =====================================================================
# 4. containment_from_events prefers a real container over the event-count max
# =====================================================================
def test_containment_prefers_container_over_event_count_max():
    """(additional fix of the brief): on a no-escape multi-fault sample whose
    raw-event-count-max fault is NOT a container, `containment_from_events`
    must still return the (smaller) fault's real containment bundle — a real
    containment must not be missed."""
    rid = "T01-F5-W4"
    big = _tlb_l0_l4(rid, "1", "a", t0=1)                # 5 events, no closure
    big += [_line("lq_read", rid, "1", f"a{i}", f"a4", 100 + i,
                  dyn_inst_seq=7, request_id=7, va="1000", pa="2000",
                  corr="seq_primary") for i in range(5, 12)]   # filler -> 12
    small = _tlb_l0_l4(rid, "2", "b", t0=40) + _squash_tail(rid, "2", "b", 40)
    events_lines = big + small
    p = _write_stream(events_lines)
    events, _tr = P.read_events(p)
    grouped = CC._group_by_fault(events)
    assert len(grouped["1"]) > len(grouped["2"]), \
        (len(grouped["1"]), len(grouped["2"]))
    b = CC.containment_from_events(events, rid)
    assert b is not None, "real containment missed (would be a false negative)"
    assert b["layer"] == "L4" and b["na_layers"] == ["L5"], b
    r = _adm(rid, events, containment=b)
    assert r["admitted"] is True and r["path"] == "contained", r


# =====================================================================
# 5. determinism over the whole pipeline
# =====================================================================
def test_determinism_same_input_same_selection():
    """(3) of the brief: identical input yields an identical selection and
    verdict across repeated runs."""
    rid = "T03-F5-W4"
    lines = (_tlb_l0_l4(rid, "1", "a", t0=1) + _squash_tail(rid, "1", "a", 1)
             + _tlb_l0_l4(rid, "2", "b", t0=20) + _escape_tail(rid, "2", "b", 20))
    p = _write_stream(lines)
    events, _tr = P.read_events(p)
    picks = []
    verdicts = []
    for _ in range(5):
        v = CC.check_chain(events)
        picks.append(CC.select_representative_fault(v["faults"])[0])
        r = _adm(rid, events)
        verdicts.append((r["admitted"], r["path"], r["terminal"]))
    assert set(picks) == {"2"}, picks
    assert len(set(verdicts)) == 1, verdicts
    assert verdicts[0] == (True, "full_chain", "full"), verdicts[0]


def main():
    cases = [
        ("[1a] escape-first ranking in the shared rule",
         test_select_helper_escape_first),
        ("[1b] rank tie -> longest path -> smallest fault id; deterministic",
         test_select_helper_tiebreaks_and_determinism),
        ("[2] multi-injection stream: escape wins, admits via full_chain",
         test_multi_fault_escape_beats_containment),
        ("[3] no-escape sample: containment is the terminus",
         test_no_escape_sample_selects_containment),
        ("[4] containment_from_events prefers a real container",
         test_containment_prefers_container_over_event_count_max),
        ("[5] determinism: same input -> same selection/verdict",
         test_determinism_same_input_same_selection),
    ]
    for name, fn in cases:
        try:
            fn()
            check(name, True)
        except AssertionError as exc:
            check(name, False, f"AssertionError: {exc}")

    print()
    if FAILED:
        print(f"FAILED ({len(FAILED)}): {FAILED}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
