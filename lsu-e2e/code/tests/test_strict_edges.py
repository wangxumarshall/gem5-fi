#!/usr/bin/env python3
"""Negative and positive tests for the strict causal-edge verifier.

These tests are deliberately adversarial: they encode the failure modes
that made the previous round's "180/180 COMPLETE" unacceptable.
"""
from __future__ import annotations

import gzip
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runner"))
import e2e_strict_data as D
import e2e_strict_engine as E


# ---------------------------------------------------------------------------
# synthetic commit trace helpers
# ---------------------------------------------------------------------------
class FakeDisasm:
    def __init__(self, table):
        self.table = table

    def get(self, pc):
        return self.table.get(pc)


def _row(seq, pc, op, dsts=(), srcs=(), tick=None):
    """One ctrace v2 row.  dsts/srcs are (class,arch,phys[,value])."""
    nd = len(dsts)
    parts = [str(seq), str(seq), "0", str(tick if tick is not None else seq),
             "%x" % pc, op, str(nd)]
    for d in dsts:
        c, a, p = d[:3]
        v = d[3] if len(d) > 3 else 0
        parts += [str(c), str(a), str(p), "%016x" % v]
    parts.append(str(len(srcs)))
    for s in srcs:
        parts += [str(s[0]), str(s[1]), str(s[2])]
    return ",".join(parts)


def make_trace(tmp_path, rows, name="ct.gz"):
    p = tmp_path / name
    with gzip.open(p, "wt") as f:
        f.write("# ctrace v2 seq,seqencNum,tid,tick,pc,op,ndest"
                "[,class,arch,phys,val]*,nsrc[,class,arch,phys]*\n")
        for r in rows:
            f.write(r + "\n")
    return D.StrictTrace(p)


def marker_group(seq0, mtype=0x11, site=2, order=1, a=0x1000, b=0x2000,
                 c=0):
    tag = (mtype << 56) | (site << 32) | order
    rows = []
    for i, v in enumerate((tag, a, b, c)):
        rows.append(_row(seq0 + i, 0x100 + i, "orr",
                         dsts=[(0, 28, 60 + i, v)],
                         srcs=[(0, 1 + i, 200 + i), (-1, 0, 65535)],
                         tick=100))
    return rows


# ---------------------------------------------------------------------------
# 1. temporal adjacency is not causality
# ---------------------------------------------------------------------------
def test_temporal_adjacency_without_identity_is_correlated():
    inj = {"seq_int": 10, "kv": {"addr": "0x1000"}, "tick_int": 1}
    eff = {"seq_int": 11, "kind": "consumer", "kv": {}, "tick_int": 2}
    level, why = E._injection_effect_link(inj, eff)
    assert level == E.CORR
    assert "different dyn inst" in why


def test_same_dyn_inst_fault_record_is_direct():
    inj = {"seq_int": 10, "kv": {"request_id": "7"}, "tick_int": 1}
    eff = {"seq_int": 10, "kind": "resp", "kv": {"request_id": "7"},
           "tick_int": 2}
    level, _ = E._injection_effect_link(inj, eff)
    assert level == E.DIRECT


def test_shared_identity_requires_matching_field():
    assert E._shared_identity({"request_id": "1"}, {"request_id": "2"}) == []
    assert E._shared_identity({"request_id": "1"},
                              {"request_id": "1"}) == ["request_id=1"]


# ---------------------------------------------------------------------------
# 2. equal values with different provenance are not an edge
# ---------------------------------------------------------------------------
def test_equal_value_different_provenance_rejected(tmp_path):
    # Two events with identical value tuples but different keys/occurrence:
    # first_sw_divergence must align by identity, never by value.
    rows = marker_group(100, mtype=0x11, site=2, order=1, b=0xdead)
    t = make_trace(tmp_path, rows)
    events = E.build_sw_events(t, FakeDisasm({}))
    # control has one event with the same *values* but site 9.
    ctrl = [{"type": 0x11, "site": 9, "order": 1, "a": 0,
             "b": 0xdead, "c": 0, "seq": 1, "op_seq": None,
             "key": [0x11, 9, None], "occ": 0, "line": 1,
             "op_pc": None, "op_name": None}]
    fd = E.first_sw_divergence(events, ctrl)
    # The fault event has no control counterpart at its identity: this is a
    # real stream divergence, but it must not be reported as a *value*
    # match merely because b is equal.
    assert fd is not None
    assert fd["kind"] == "event_missing_in_control"


def test_value_equality_alone_is_not_a_strong_software_edge():
    # Build a marker event not tied to any taint lifecycle.
    g = D.MarkerGroup(start_idx=0, seqs=[1, 2, 3, 4], tag=0,
                      mtype=0x13, site=3, order=1,
                      vals=[0, 0x1234, 0x99, 0xaa],
                      srcs=[[(0, 1, 5)] * 4 for _ in range(4)],
                      srcvals=[[0] for _ in range(4)],
                      idxs=[0, 1, 2, 3], lines=[1, 2, 3, 4])
    ev = E.SWEvent(g, (0x13, 3), 0, 0x1234, 0x99, 0xaa, 4, None, None,
                   None)
    life = type("L", (), {"tainted_seqs": {}, "consumers": []})()
    walk = type("W", (), {"edges": []})()
    conn = E.connect_software_divergence(ev, {"kv": {}}, 42, None, life,
                                         walk, None, FakeDisasm({}), [], None)
    assert conn["level"] == E.CORR


def test_marker_operand_present_but_untainted_is_correlated():
    # A marker row reads phys 7, but phys 7 is not tainted at that marker:
    # the connection must NOT be upgraded to DIRECT.
    row = type("R", (), {"srcs": [(0, 2, 7)], "dsts": [(0, 28, 9, 1)]})()
    trace = type("T", (), {"rows": [row]})()
    g = D.MarkerGroup(start_idx=0, seqs=[1, 2, 3, 4], tag=0,
                      mtype=0x11, site=2, order=1,
                      vals=[0, 0x1000, 0x2000, 0],
                      srcs=[[(0, 2, 7), (-1, 0, 65535)] for _ in range(4)],
                      srcvals=[[0x2000, 0] for _ in range(4)],
                      idxs=[0, 0, 0, 0], lines=[1, 1, 1, 1])
    ev = E.SWEvent(g, (0x11, 2), 0, 0x1000, 0x2000, 0, 4, None, None, None)
    life = type("L", (), {"tainted_seqs": {}, "consumers": []})()
    walk = type("W", (), {"edges": [], "marker_taint": {0: set()}})()
    conn = E.connect_software_divergence(ev, {"kv": {}}, 42, object(),
                                         life, walk, trace, FakeDisasm({}),
                                         [], None)
    assert conn["level"] == E.CORR


def test_marker_operand_in_taint_set_is_direct():
    row = type("R", (), {"srcs": [(0, 2, 7)], "dsts": [(0, 28, 9, 1)]})()
    trace = type("T", (), {"rows": [row]})()
    g = D.MarkerGroup(start_idx=0, seqs=[1, 2, 3, 4], tag=0,
                      mtype=0x11, site=2, order=1,
                      vals=[0, 0x1000, 0x2000, 0],
                      srcs=[[(0, 2, 7), (-1, 0, 65535)] for _ in range(4)],
                      srcvals=[[0x2000, 0] for _ in range(4)],
                      idxs=[0, 0, 0, 0], lines=[1, 1, 1, 1])
    ev = E.SWEvent(g, (0x11, 2), 0, 0x1000, 0x2000, 0, 4, None, None, None)
    life = type("L", (), {"tainted_seqs": {}, "consumers": []})()
    walk = type("W", (), {"edges": [],
                          "marker_taint": {0: {(0, 7)}}})()
    conn = E.connect_software_divergence(ev, {"kv": {}}, 42, object(),
                                         life, walk, trace, FakeDisasm({}),
                                         [], None)
    assert conn["level"] == E.DIRECT


# ---------------------------------------------------------------------------
# 3. transformed dependency: real semantics accepted
# ---------------------------------------------------------------------------
def test_transformed_dependency_semantics_verified():
    # eor x4, x5, x6 with actual values
    vals = {5: 0x00ff00ff00ff00ff, 6: 0x0ff00ff00ff00ff0}
    outs, _ = D.evaluate("eor", "x4, x5, x6", vals)
    assert outs[0] == (vals[5] ^ vals[6]) & D.MASK64
    # madd x4, x5, x6, x7
    outs, _ = D.evaluate("madd", "x4, x5, x6, x7",
                         {5: 2, 6: 3, 7: 10})
    assert outs[0] == 16
    # lsr variable amount
    outs, _ = D.evaluate("lsr", "x3, x2, x1", {1: 8, 2: 0x1234})
    assert outs[0] == 0x12


def test_unsupported_semantics_never_upgraded():
    with pytest.raises(D.SemanticsError):
        D.evaluate("fancy_op", "x1, x2, x3", {1: 1, 2: 2, 3: 3})


# ---------------------------------------------------------------------------
# 4. wire dependency without value equality is still a dependency
# ---------------------------------------------------------------------------
def test_register_dependency_detected_even_when_value_changes():
    # producer writes phys 10; consumer reads it and changes the value.
    rows = [
        _row(1, 0x100, "add", dsts=[(0, 1, 10, 0x10)], srcs=[]),
        _row(2, 0x104, "eor", dsts=[(0, 2, 11, 0x10 ^ 0xff)],
             srcs=[(0, 1, 10), (0, 3, 12)], tick=2),
    ]
    t = make_trace(Path("/tmp"), rows, "wire.gz")
    # def/use is directly recorded regardless of value change.
    d = t.defining_insn(0, 10, 1)
    assert d is not None and d.seq == 1
    assert any(p == 10 for (_c, _a, p) in t.rows[1].srcs)


# ---------------------------------------------------------------------------
# 5. overwrite stops propagation
# ---------------------------------------------------------------------------
def test_clean_store_stops_memory_taint(tmp_path):
    dis = FakeDisasm({
        0x200: ("str", "x1, [x0]"),
        0x204: ("str", "x2, [x0]"),   # clean overwrite
        0x208: ("ldr", "x3, [x0]"),
    })
    rows = [
        _row(1, 0x200, "addxi_uop", srcs=[(0, 1, 10), (0, 0, 11)],
             tick=1),
        _row(2, 0x204, "addxi_uop", srcs=[(0, 2, 20), (0, 0, 11)],
             tick=2),
        _row(3, 0x208, "ldr", dsts=[(0, 3, 30, 0xbeef)],
             srcs=[(0, 0, 11)], tick=3),
    ]
    t = make_trace(tmp_path, rows)
    # source values: x0=0x4000 (address), x1=tainted, x2=clean
    t.rows[0].srcvals = [0xdead, 0x4000]
    t.rows[1].srcvals = [0x1234, 0x4000]
    t.rows[2].srcvals = [0x4000]
    seeds = [(0, 10, 0xdead, "h", "n", 0)]
    byte_seeds = {0x4000: {"byte": 0xde, "seq": 1, "value": 0xdead,
                           "node": "n"}}
    w = E.SemanticWalk(t, dis, E.ArchMemory(t, dis), seeds, 0, byte_seeds)
    # The clean store at seq 2 must remove the taint before the load at 3.
    assert not any(e["consumer_seq"] == 3 and e["edge_kind"] == "memory"
                   for e in w.edges)


def test_multiple_stores_same_address_versioned(tmp_path):
    # tainted store, clean store, load -> the clean store is the version.
    dis = FakeDisasm({0x200: ("str", "x1, [x0]"),
                      0x204: ("str", "x2, [x0]"),
                      0x208: ("ldr", "x3, [x0]")})
    rows = [
        _row(1, 0x200, "str", srcs=[(0, 1, 10), (0, 0, 11)], tick=1),
        _row(2, 0x204, "str", srcs=[(0, 2, 20), (0, 0, 11)], tick=2),
        _row(3, 0x208, "ldr", dsts=[(0, 3, 30, 0x1234)],
             srcs=[(0, 0, 11)], tick=3),
    ]
    t = make_trace(tmp_path, rows)
    t.rows[0].srcvals = [0xdead, 0x4000]
    t.rows[1].srcvals = [0x1234, 0x4000]
    t.rows[2].srcvals = [0x4000]
    w = E.SemanticWalk(t, dis, E.ArchMemory(t, dis),
                       [(0, 10, 0xdead, "h", "n", 0)], 0,
                       {0x4000: {"byte": 0xde, "seq": 1, "value": 0xdead,
                                 "node": "n"}})
    assert not any(e["consumer_seq"] == 3 for e in w.edges)


def test_tainted_store_then_load_is_an_edge(tmp_path):
    dis = FakeDisasm({0x200: ("str", "x1, [x0]"),
                      0x208: ("ldr", "x3, [x0]")})
    rows = [
        _row(1, 0x200, "str", srcs=[(0, 1, 10), (0, 0, 11)], tick=1),
        _row(2, 0x208, "ldr", dsts=[(0, 3, 30, 0xdead)],
             srcs=[(0, 0, 11)], tick=2),
    ]
    t = make_trace(tmp_path, rows)
    t.rows[0].srcvals = [0xdead, 0x4000]
    t.rows[1].srcvals = [0x4000]
    w = E.SemanticWalk(t, dis, E.ArchMemory(t, dis),
                       [(0, 10, 0xdead, "h", "n", 0)], 0,
                       {0x4000: {"byte": 0xde, "seq": 1, "value": 0xdead,
                                 "node": "n"}})
    assert any(e["consumer_seq"] == 2 and e["edge_kind"] == "memory"
               for e in w.edges)


# ---------------------------------------------------------------------------
# 6. unrelated squash is not attributed to the fault
# ---------------------------------------------------------------------------
def test_unrelated_squash_is_not_a_fault_target(tmp_path):
    rows = [
        _row(1, 0x100, "add", dsts=[(0, 1, 10, 1)], srcs=[]),
        "# squash 99 500",
    ]
    p = tmp_path / "sq.gz"
    with gzip.open(p, "wt") as f:
        f.write("# ctrace v2 seq,seqencNum,tid,tick,pc,op,ndest"
                "[,class,arch,phys,val]*,nsrc[,class,arch,phys]*\n")
        for r in rows:
            f.write(r + "\n")
    t = D.StrictTrace(p)
    assert 99 in t.squash
    inj = {"seq_int": 1, "kv": {}, "tick_int": 1}
    eff = {"seq_int": 99, "kind": "squash", "kv": {}, "tick_int": 2}
    level, _ = E._injection_effect_link(inj, eff)
    assert level == E.CORR


# ---------------------------------------------------------------------------
# 7. missing critical edge fails completeness
# ---------------------------------------------------------------------------
def test_missing_edge_blocks_complete():
    assert E.compute_status(["no_strong_software_edge"], True) != \
        "E2E_CAUSAL_COMPLETE"
    assert E.compute_status([], True) == "E2E_CAUSAL_COMPLETE"
    assert E.compute_status([], False) == "E2E_CAUSAL_UNRESOLVED"


def test_hash_chain_requires_tainted_input():
    g = D.MarkerGroup(start_idx=0, seqs=[1, 2, 3, 4], tag=0,
                      mtype=0x13, site=3, order=1,
                      vals=[0, 0x1234, 0x99, 0xaa],
                      srcs=[[(0, 1, 5)] * 4 for _ in range(4)],
                      srcvals=[[0] for _ in range(4)],
                      idxs=[0, 1, 2, 3], lines=[1, 2, 3, 4])
    ev = E.SWEvent(g, (0x13, 3), 0, 0x1234, 0x99, 0xaa, 4, None, None,
                   None)
    _, first_bad = E.verify_hash_events([ev], [], set())
    # The input differs from control (control missing) but is not tainted.
    assert first_bad is None  # no control event to compare against
    rec = E.verify_hash_events([ev], [{"type": 0x13, "site": 3,
                                       "order": 1, "a": 0x1, "b": 0x99,
                                       "c": 0xaa, "seq": 4, "op_seq": None,
                                       "key": [0x13, 3], "occ": 0,
                                       "line": 1, "op_pc": None,
                                       "op_name": None}], set())[1]
    assert rec is not None and rec["input_tainted"] is False
