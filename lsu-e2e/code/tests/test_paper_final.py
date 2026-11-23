#!/usr/bin/env python3
"""Regression tests for the paper-final causal reconstruction.

The suites below encode each failure mode that the previous round's
"180/180 COMPLETE" hid:

* hash events connected by time rather than by a real produced value;
* an unconditional final_checksum edge;
* masking endpoints without incoming mechanism edges;
* intermediate divergences without a terminal node;
* empty RP01 graphs and truncated gzip evidence;
* symptom labels derived from the fault model instead of software data;
* edge totals that differ between JSON, CSV and the report.

Synthetic traces are used where the defect is structural; the real E2E
evidence is used for end-to-end acceptance.
"""
from __future__ import annotations

import collections
import csv
import gzip
import json
import sys
import types
from pathlib import Path

import pytest

EXT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXT / "runner"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_strict_data as D
import e2e_strict_engine as E
import e2e_flow as F
import final_paths as P


# ---------------------------------------------------------------------------
# synthetic commit-trace builder
# ---------------------------------------------------------------------------
class FakeDisasm:
    def __init__(self):
        self.table = {}

    def get(self, pc):
        return self.table.get(pc)


def _row(seq, pc, op, dsts=(), srcs=(), tick=None):
    parts = [str(seq), str(seq), "0", str(tick if tick is not None else seq),
             "%x" % pc, op, str(len(dsts))]
    for c, a, p, v in dsts:
        parts += [str(c), str(a), str(p), "%016x" % (v & D.MASK64)]
    parts.append(str(len(srcs)))
    for s in srcs:
        parts += [str(s[0]), str(s[1]), str(s[2])]
    return ",".join(parts)


class Builder:
    """Build a small valid ctrace v2 with marker groups and real copies."""

    def __init__(self):
        self.rows = []
        self.dis = FakeDisasm()
        self.pc = 0x1000
        self.seq = 1
        self.v = {}
        self.n = collections.Counter()
        self.phys = 1000

    def newphys(self):
        self.phys += 1
        return self.phys

    def addr(self):
        p = self.pc
        self.pc += 4
        return p

    def emit(self, op, dsts=(), srcs=()):
        pc = self.addr()
        self.rows.append(_row(self.seq, pc, op, dsts, srcs))
        self.seq += 1
        for c, a, p, v in dsts:
            self.v[(c, p)] = v
        return pc

    def imm(self, arch, value, op="mov", disasm=None):
        phys = self.newphys()
        pc = self.addr()
        self.rows.append(_row(self.seq, pc, op,
                               dsts=[(0, arch, phys, value)]))
        self.seq += 1
        self.v[(0, phys)] = value
        self.dis.table[pc] = ("mov", "x%d, #0x%x" % (arch, value))
        return phys

    def copy(self, darch, sarch, sphys):
        dphys = self.newphys()
        val = self.v[(0, sphys)]
        pc = self.addr()
        self.rows.append(_row(self.seq, pc, "orr",
                               dsts=[(0, darch, dphys, val)],
                               srcs=[(0, sarch, sphys), (-1, 0, 65535)]))
        self.seq += 1
        self.v[(0, dphys)] = val
        self.dis.table[pc] = ("mov", "x%d, x%d" % (darch, sarch))
        return dphys

    def marker(self, mtype, site, order, a_val, b_val, c_val,
               a_src, b_src, c_src):
        tag = (mtype << 56) | (site << 32) | order
        tag_phys = self.imm(9, tag)
        p0 = self.copy(0, 9, tag_phys)
        p1 = self.copy(1, a_src[0], a_src[1])
        p2 = self.copy(2, b_src[0], b_src[1])
        p3 = self.copy(3, c_src[0], c_src[1])
        for i, (p, dis) in enumerate(((p0, "x0"), (p1, "x1"),
                                      (p2, "x2"), (p3, "x3"))):
            pc = self.addr()
            self.rows.append(_row(
                self.seq, pc, "orr",
                dsts=[(0, 28, self.newphys(),
                       [tag, a_val, b_val, c_val][i])],
                srcs=[(0, i, p), (-1, 0, 65535)]))
            self.seq += 1
            self.dis.table[pc] = ("mov", "x28, %s" % dis)

    def trace(self, tmp_path, name="ct.gz"):
        p = tmp_path / name
        with gzip.open(p, "wt") as f:
            f.write("# ctrace v2 seq,seqencNum,tid,tick,pc,op,ndest"
                    "[,class,arch,phys,val]*,nsrc[,class,arch,phys]*\n")
            for r in self.rows:
                f.write(r + "\n")
        t = D.StrictTrace(p)
        for r in t.rows:
            info = self.dis.get(r.pc)
            if info:
                r.disasm = "%s %s" % info
        return t


def add_hash_event(b, state_arch, state_phys, before, input_v, after,
                   site=1, order=0):
    """One HASH marker whose before/after are the same accumulator."""
    in_phys = b.imm(5, input_v)
    # after temp is the produced value; then the state register is updated
    a_phys = b.imm(6, after)
    b.marker(D.T_HASH, site, order, input_v, before, after,
             (5, in_phys), (state_arch, state_phys), (6, a_phys))
    # state <- produced value (real copy after the observation)
    s_phys = b.copy(state_arch, 6, a_phys)
    return s_phys


def hash_events(t):
    return [e for e in E.build_sw_events(t, FakeDisasm()) if
            e.mtype == D.T_HASH]


# ---------------------------------------------------------------------------
# 1. hash state streams and final OUTPUT
# ---------------------------------------------------------------------------
def test_single_hash_stream_requires_defuse(tmp_path):
    b = Builder()
    p = b.imm(4, 0x100)
    p = add_hash_event(b, 4, p, 0x100, 0x11, D.when_fnv(0x100, 0x11))
    p = add_hash_event(b, 4, p, D.when_fnv(0x100, 0x11), 0x22,
                       D.when_fnv(D.when_fnv(0x100, 0x11), 0x22))
    t = b.trace(tmp_path)
    evs = hash_events(t)
    recs, _ = E.verify_hash_events(evs, [], set())
    flow = F.analyze_hash_streams(t, b.dis, evs, recs, None, None)
    assert flow["verified_links"] == 1
    assert len(flow["streams"]) == 1
    assert flow["unverified_links"] == 0
    link = flow["links"][0]
    assert link["same_def_instance"] is True
    assert link["source_after_value"] == link["target_before_value"]


def test_value_equality_alone_is_not_a_stream_edge(tmp_path):
    # Event B's before value equals A's after value but is produced by a
    # different instruction instance (a fresh mov immediate).  No edge.
    b = Builder()
    p = b.imm(4, 0x10)
    p = add_hash_event(b, 4, p, 0x10, 0x11, D.when_fnv(0x10, 0x11))
    shared = D.when_fnv(0x10, 0x11)
    q = b.imm(4, shared)          # same value, new producing instruction
    q = add_hash_event(b, 4, q, shared, 0x22,
                       D.when_fnv(shared, 0x22))
    t = b.trace(tmp_path)
    evs = hash_events(t)
    recs, _ = E.verify_hash_events(evs, [], set())
    flow = F.analyze_hash_streams(t, b.dis, evs, recs, None, None)
    assert flow["verified_links"] == 0
    assert len(flow["roots"]) == 2


def test_interleaved_dual_stream_and_xor_output(tmp_path):
    b = Builder()
    s = b.imm(4, 0xabc)
    path = b.imm(7, 0)
    # interleaved updates of s (site 2) and path (site 3)
    s = add_hash_event(b, 4, s, 0xabc, 0x1, D.when_fnv(0xabc, 0x1), site=2)
    path = add_hash_event(b, 7, path, 0, 0x2, D.when_fnv(0, 0x2), site=3)
    s = add_hash_event(b, 4, s, D.when_fnv(0xabc, 0x1), 0x3,
                       D.when_fnv(D.when_fnv(0xabc, 0x1), 0x3), site=2)
    path = add_hash_event(b, 7, path, D.when_fnv(0, 0x2), 0x4,
                          D.when_fnv(D.when_fnv(0, 0x2), 0x4), site=3)
    s_val = D.when_fnv(D.when_fnv(0xabc, 0x1), 0x3)
    p_val = D.when_fnv(D.when_fnv(0, 0x2), 0x4)
    # OUTPUT: eor x1, x4(s), x7(path); slots b=s, c=path
    s10 = b.copy(10, 4, s)
    p11 = b.copy(11, 7, path)
    expr_pc = b.addr()
    b.rows.append(_row(b.seq, expr_pc, "eor",
                       dsts=[(0, 1, 401, s_val ^ p_val)],
                       srcs=[(0, 10, s10), (0, 11, p11)]))
    b.seq += 1
    b.v[(0, 401)] = s_val ^ p_val
    b.dis.table[expr_pc] = ("eor", "x1, x10, x11")
    b.marker(D.T_OUTPUT, 99, 0, s_val ^ p_val, s_val, p_val,
             (1, 401), (10, s10), (11, p11))

    t = b.trace(tmp_path)
    evs = hash_events(t)
    recs, _ = E.verify_hash_events(evs, [], set())
    flow = F.analyze_hash_streams(t, b.dis, evs, recs, None, None)
    assert len(flow["streams"]) == 2
    # No edge crosses the two streams.
    for link in flow["links"]:
        assert recs[link["source"]]["site"] == recs[link["target"]]["site"]
    outg = [g for g in t.markers if g.mtype == D.T_OUTPUT][-1]
    ov = F.analyze_output_expression(t, b.dis, outg, flow, None, None)
    assert ov["verified"] is True
    assert ov["formula"] == "b XOR c"
    assert ov["a_equals_b_xor_c"] is True
    assert ov["operand_producers"]["2"]["kind"] == "hash_accumulator"
    assert ov["operand_producers"]["3"]["kind"] == "hash_accumulator"
    # The last HASH event updates only one stream, so its after value is
    # not the XOR output; the expression is what connects them.
    assert int(recs[-1]["after"], 16) != int(ov["a"], 16)


def test_output_expression_mismatch_is_rejected(tmp_path):
    b = Builder()
    s = b.imm(4, 0x10)
    s10 = b.copy(10, 4, s)
    p11 = b.copy(11, 4, s)
    # The expression computes 0x10 ^ 0x10 = 0, but the marker claims 0x99.
    expr_pc = b.addr()
    b.rows.append(_row(b.seq, expr_pc, "eor",
                       dsts=[(0, 1, 401, 0)],
                       srcs=[(0, 10, s10), (0, 11, p11)]))
    b.seq += 1
    b.v[(0, 401)] = 0
    b.dis.table[expr_pc] = ("eor", "x1, x10, x11")
    b.marker(D.T_OUTPUT, 99, 0, 0x99, 0x10, 0x10,
             (1, 401), (10, s10), (11, p11))
    t = b.trace(tmp_path)
    outg = [g for g in t.markers if g.mtype == D.T_OUTPUT][-1]
    flow = {"records": [], "events": [], "streams": {}, "tails": {},
            "roots": [], "verified_links": 0, "unverified_links": 0}
    ov = F.analyze_output_expression(t, b.dis, outg, flow, None, None)
    assert ov["verified"] is False


# ---------------------------------------------------------------------------
# 2. masking / termination graph
# ---------------------------------------------------------------------------
def _run(symptom, termination, edges, nodes, complete=True, output_ok=True):
    return {
        "run_id": "SYN", "terminal": "NON_SDC", "nodes": nodes,
        "edges": edges,
        "classification": {
            "software_symptom": symptom,
            "propagation_termination": termination,
            "masking_evidence_complete": complete,
        },
        "software": {
            "output_validation": {"verified": True},
            "hash_flow": {"unverified_links": 0,
                          "events_with_bad_provenance": 0},
            "application_validation": {"verified": output_ok},
            "output": {"matches_control": output_ok, "oracle_pass": output_ok},
        },
    }


def _n(kind, eid):
    return {"event_id": eid, "kind": kind}


def _e(s, t, dep="d", level=E.DIRECT):
    return {"edge_id": "%s-%s" % (s, t), "source": s, "target": t,
            "dependency": dep, "evidence_level": level}


def test_masking_endpoint_without_in_edge_fails():
    nodes = [_n("injection", "E1"), _n("application_output", "E2"),
             _n("final_expression", "E3"), _n("masking_endpoint", "E4")]
    edges = [_e("E1", "E2"), _e("E3", "E2"), _e("E4", "E2")]
    run = _run("NO_VISIBLE_ERROR", "ACTIVATED_NO_DATA_CORRUPTION",
               edges, nodes)
    gaps = E.validate_end_to_end_graph(run)
    assert "graph:masking_endpoint_has_no_strong_in_edge" in gaps


def test_intermediate_divergence_needs_connected_terminal():
    nodes = [_n("injection", "E1"), _n("first_software_divergence", "E2"),
             _n("masking_endpoint", "E3"), _n("final_expression", "E4"),
             _n("application_output", "E5")]
    edges = [_e("E1", "E2"), _e("E2", "E3"), _e("E3", "E5"),
             _e("E4", "E5")]
    run = _run("INTERMEDIATE_VALUE_DIVERGENCE", "MASKED_BY_OVERWRITE",
               edges, nodes)
    assert E.validate_end_to_end_graph(run) == []
    # Remove the terminal in-edge: the path is broken.
    run["edges"] = [_e("E1", "E2"), _e("E4", "E5")]
    assert "graph:no_strong_path_root_to_masking_endpoint" in \
        E.validate_end_to_end_graph(run)


def test_overwrite_requires_real_covering_instruction():
    proof = {"overwrite_seq": 500}
    assert E._masking_evidence_complete(
        "MASKED_BY_OVERWRITE", {"overwrite_verified": True},
        {"matches_control": True}) is False
    complete = {"overwrite_verified": True,
                "covering_instruction": {"dyn_inst_seq": 500}}
    assert E._masking_evidence_complete(
        "MASKED_BY_OVERWRITE", complete,
        {"matches_control": True}) is True


def test_non_consumption_requires_complete_scan():
    out = {"matches_control": True}
    assert E._masking_evidence_complete(
        "MASKED_BY_NON_CONSUMPTION", {"non_consumption_verified": False},
        out) is False
    assert E._masking_evidence_complete(
        "MASKED_BY_NON_CONSUMPTION", {"non_consumption_verified": True},
        out) is True


def test_no_data_corruption_requires_delivery_and_coverage():
    out = {"matches_control": True}
    assert E._masking_evidence_complete(
        "ACTIVATED_NO_DATA_CORRUPTION",
        {"state_change_verified": True, "delivered_value_correct": False},
        out) is False
    assert E._masking_evidence_complete(
        "ACTIVATED_NO_DATA_CORRUPTION",
        {"state_change_verified": True, "delivered_value_correct": True,
         "consumer_coverage_complete": True}, out) is True


def test_value_convergence_recomputes_control_relevant_bit():
    trace = types.SimpleNamespace(rows=[], row_of_seq=lambda s: None)
    proof = {"branch_convergence": [{
        "event": {"a": "0x10", "b": "0x0", "dyn_inst_seq": 5,
                  "site": 3, "ctrace_line": 9},
        "control_condition": "0x12", "taken": "0x0",
        "control_taken": 0}]}
    p = E._enrich_masking_proof(
        proof, "MASKED_BY_VALUE_CONVERGENCE", {"seq": 1}, trace, None,
        None, None, None, None, None, {"matches_control": True}, None)
    assert p["convergence_verified"] is True
    proof["branch_convergence"][0]["event"]["b"] = "0x1"
    p2 = E._enrich_masking_proof(
        proof, "MASKED_BY_VALUE_CONVERGENCE", {"seq": 1}, trace, None,
        None, None, None, None, None, {"matches_control": True}, None)
    assert p2["convergence_verified"] is False


# ---------------------------------------------------------------------------
# 3. symptom classification must use software evidence
# ---------------------------------------------------------------------------
class FakeEv:
    def __init__(self, mtype, a, b, seq, op_seq=None):
        self.mtype = mtype
        self.a = a
        self.b = b
        self.c = 0
        self.seq = seq
        self.op_seq = op_seq
        self.op_pc = 0x1000
        self.op_name = "ldr"
        self.site = 1
        self.order = 0

    def as_dict(self):
        return {"type": self.mtype, "a": E._hex(self.a), "b": E._hex(self.b),
                "dyn_inst_seq": self.seq, "op_dyn_inst_seq": self.op_seq}


def _sym(origin, target, fe, fval_ctrl=None):
    fev = FakeEv(D.T_LOAD, 0x1000, fe, 10, 9)
    cev = {"type": D.T_LOAD, "a": 0x1000,
           "b": fval_ctrl if fval_ctrl is not None else 0x999}
    fd = {"fault": fev, "control": cev, "fields": ["b"]}
    trace = types.SimpleNamespace(rows=[], row_of_seq=lambda s: None)
    return E.classify_application_symptom(
        symptom="WRONG_OUTPUT", origin=origin, fd=fd, target=target,
        trace=trace, disasm=None, archmem=None, stores=None,
        ctrl_events=[], ctrl_trace=None,
        output={"observed": "0x0", "control": "0x1"})


def test_address_record_unchanged_does_not_imply_wrong_address():
    target = {"seq": 9, "kv": {"old_addr": "0x4000",
                               "new_addr": "0x4000"}, "addr": 0x4000}
    sym, val = _sym("ADDRESS_CHANGED", target, 0x10)
    assert sym != "WRONG_ADDRESS_EFFECT"
    assert val["verified"] is False


def test_address_change_requires_injected_instruction_and_diff():
    target = {"seq": 9, "kv": {"old_addr": "0x4000",
                               "new_addr": "0x4008"}, "addr": 0x4000}
    sym, val = _sym("ADDRESS_CHANGED", target, 0x10)
    assert sym == "WRONG_ADDRESS_EFFECT"
    assert val["verified"] is True


def test_origin_alone_never_selects_symptom():
    target = {"seq": 9, "kv": {}, "addr": 0x4000}
    sym, val = _sym("STORE_DATA_CORRUPTED", target, 0x10)
    assert sym == "WRONG_OUTPUT_UNSPECIFIED"
    assert val["verified"] is False


def test_response_payload_match_is_numeric_value(monkeypatch):
    target = {"seq": 9, "kv": {"inj_data_hex": "efbeadde"},
              "addr": 0x4000}
    sym, val = _sym("RESPONSE_DATA_CORRUPTED", target, 0xdeadbeef)
    assert sym == "WRONG_NUMERIC_VALUE"
    assert val["checks"]["delivered_is_injected_payload"] is True


def test_alternate_store_source_match_is_stale(monkeypatch):
    target = {"seq": 9, "kv": {"alt_store_seq": "7"}, "addr": 0x4000}
    monkeypatch.setattr(E, "_store_data_at",
                        lambda trace, dis, seq: 0x1234 if seq == 7 else None)
    sym, val = _sym("WRONG_FORWARD_SOURCE", target, 0x1234,
                    fval_ctrl=0x5678)
    assert sym == "STALE_DATA_USED"
    assert val["checks"]["stale_source"]["kind"] == \
        "injected_alt_forward_source"


# ---------------------------------------------------------------------------
# 4. completion requires a directed strong-evidence path
# ---------------------------------------------------------------------------
def test_complete_requires_strong_path():
    nodes = [_n("injection", "E1"), _n("application_output", "E2"),
             _n("final_expression", "E3")]
    weak = [_e("E1", "E2", level=E.CORR), _e("E3", "E2")]
    run = _run("WRONG_OUTPUT", "COMMITTED_AND_PROPAGATED", weak, nodes,
               output_ok=True)
    gaps = E.validate_end_to_end_graph(run)
    assert "graph:no_strong_path_root_to_application_output" in gaps
    assert E.compute_status([], True, run=run) != "E2E_CAUSAL_COMPLETE"
    strong = [_e("E1", "E2"), _e("E3", "E2")]
    run["edges"] = strong
    # WRONG_OUTPUT also requires a first-divergence node; add it.
    run["nodes"].append(_n("first_software_divergence", "E4"))
    run["edges"].append(_e("E1", "E4"))
    run["edges"].append(_e("E1", "E3"))
    assert E.validate_end_to_end_graph(run) == []
    assert E.compute_status([], True, run=run) == "E2E_CAUSAL_COMPLETE"


# ---------------------------------------------------------------------------
# 5. real evidence acceptance (fast JSON-only checks)
# ---------------------------------------------------------------------------
# Final package layout: 180 chains live in evidence/causal_chains and the
# 15 RP01 observation chains in evidence/rp01 (working tree: strict_chains).
CH = P.CHAINS
RP01 = P.rp01_chains()
RP = P.stall_traces()


def _load_chains():
    fs = sorted(CH.glob("E2E-*-FAULT.causal_chain.json"))
    return [json.loads(f.read_text()) for f in fs]


@pytest.mark.skipif(not CH.exists(), reason="evidence not generated")
def test_all_165_outputs_and_hash_streams_verified():
    runs = [r for r in _load_chains() if r.get("model") != "RP01"]
    assert len(runs) == 165
    for r in runs:
        ov = r["software"]["output_validation"]
        assert ov["verified"] is True, r["run_id"]
        hf = r["software"]["hash_flow"]
        assert hf["unverified_links"] == 0, r["run_id"]
        assert hf["events_with_bad_provenance"] == 0, r["run_id"]
        assert r["classification"]["end_to_end_status"] == \
            "E2E_CAUSAL_COMPLETE"
        for e in r["edges"]:
            assert e["dependency"] != "final_checksum"


@pytest.mark.skipif(not CH.exists(), reason="evidence not generated")
def test_sq_family_outputs_use_real_expression():
    runs = [r for r in _load_chains()
            if r.get("model") in ("SQ01", "SQ03", "SP05")]
    assert len(runs) == 45
    for r in runs:
        ov = r["software"]["output_validation"]
        ctx = r["context"]
        if ctx == "C05":
            assert ov["formula"] == "b XOR c", r["run_id"]
            assert r["software"]["hash_flow"]["stream_count"] == 2
            # The last temporal HASH is not the final output; the stream
            # count and expression are.
            last = r["software"]["hash_events"][-1]["after"]
            assert last != ov["a"]
            # At least one stream is updated by more than one HASH site
            # (SQ C05 updates s at sites 44 and 45); the reconstruction
            # must keep that one stream connected across sites.
            per_stream = collections.defaultdict(set)
            for ev in r["software"]["hash_flow"]["events"]:
                per_stream[ev["stream"]].add(ev["site"])
            assert any(len(v) >= 2 for v in per_stream.values()), r["run_id"]
        elif ctx == "C04":
            assert ov["formula"] == "identity"
        else:
            assert ov["formula"] == "b XOR c"


@pytest.mark.skipif(not CH.exists(), reason="evidence not generated")
def test_masking_endpoints_have_incoming_edges_and_ivd_terminal():
    runs = _load_chains()
    endpoints = 0
    ivd = 0
    for r in runs:
        c = r["classification"]
        if c["software_symptom"] not in ("NO_VISIBLE_ERROR",
                                         "INTERMEDIATE_VALUE_DIVERGENCE"):
            continue
        kinds = {n["kind"] for n in r["nodes"]}
        assert "masking_endpoint" in kinds, r["run_id"]
        ep = [n["event_id"] for n in r["nodes"]
              if n["kind"] == "masking_endpoint"][0]
        assert any(e["target"] == ep and e["evidence_level"] in E.STRONG
                   for e in r["edges"]), r["run_id"]
        assert any(e["source"] == ep and e["evidence_level"] in E.STRONG
                   for e in r["edges"]), r["run_id"]
        endpoints += 1
        if c["software_symptom"] == "INTERMEDIATE_VALUE_DIVERGENCE":
            ivd += 1
            assert any(n["kind"] == "first_software_divergence"
                       for n in r["nodes"])
            adj = collections.defaultdict(list)
            for e in r["edges"]:
                if e["evidence_level"] in E.STRONG:
                    adj[e["source"]].append(e["target"])
            root = [n["event_id"] for n in r["nodes"]
                    if n["kind"] == "injection"][0]
            assert E._reachable(adj, [root], ep), r["run_id"]
            out = [n["event_id"] for n in r["nodes"]
                   if n["kind"] == "application_output"][0]
            assert E._reachable(adj, [ep], out), r["run_id"]
    assert endpoints == 57
    assert ivd == 20


@pytest.mark.skipif(not CH.exists(), reason="evidence not generated")
def test_rp01_graphs_are_nonempty_and_watchdog_reachable():
    fs = sorted(RP01.glob("RP01OBS-*-FAULT.strict.json"))
    assert len(fs) == 15
    for f in fs:
        r = json.loads(f.read_text())
        assert len(r["nodes"]) >= 12
        assert len(r["edges"]) >= 10
        assert r["rp01_validation"]["valid"] is True
        kinds = {n["kind"] for n in r["nodes"]}
        for k in ("replay_suppression", "target_instruction", "iq_state",
                  "ready_list_state", "replay_list_state", "lq_state",
                  "rob_head_state", "commit_progress",
                  "no_progress_interval", "simulator_watchdog"):
            assert k in kinds, (r["run_id"], k)
        wd = [n["event_id"] for n in r["nodes"]
              if n["kind"] == "simulator_watchdog"][0]
        adj = collections.defaultdict(list)
        for e in r["edges"]:
            if e["evidence_level"] in E.STRONG:
                adj[e["source"]].append(e["target"])
        root = [n["event_id"] for n in r["nodes"]
                if n["kind"] == "fault_injection"][0]
        assert E._reachable(adj, [root], wd), r["run_id"]
        assert r["classification"]["end_to_end_status"] == \
            "E2E_CAUSAL_COMPLETE"


def test_rp01_empty_or_missing_terminals_fail():
    empty = {"run_id": "EMPTY", "terminal": "HANG_WATCHDOG",
             "nodes": [], "edges": [],
             "classification": {"software_symptom": "HANG_TIMEOUT",
                                "end_to_end_status": "E2E_CAUSAL_COMPLETE",
                                "gaps": []}}
    gaps = E.validate_end_to_end_graph(empty)
    assert "graph:fault_root_missing" in gaps
    run = json.loads(sorted(RP01.glob(
        "RP01OBS-*-FAULT.strict.json"))[0].read_text())
    run["nodes"] = [n for n in run["nodes"]
                    if n["kind"] != "simulator_watchdog"]
    gaps = E.validate_end_to_end_graph(run)
    assert any("rp01_state_nodes_missing" in g for g in gaps)
    assert "graph:watchdog_terminal_missing" in gaps


def test_rp01_missing_rob_iq_lsq_state_blocks_complete():
    run = json.loads(sorted(RP01.glob(
        "RP01OBS-*-FAULT.strict.json"))[0].read_text())
    for kind in ("iq_state", "lq_state", "rob_head_state"):
        run["nodes"] = [n for n in run["nodes"] if n["kind"] != kind]
    gaps = E.validate_end_to_end_graph(run)
    assert any("rp01_state_nodes_missing" in g and "iq_state" in g
               and "lq_state" in g and "rob_head_state" in g
               for g in gaps)


def test_rp01_incomplete_or_watchdogless_trace_is_not_canonical(tmp_path):
    import e2e_rp01_audit as R
    rows = ["# " + ",".join(R.COLUMNS)]
    vals = {c: "0" for c in R.COLUMNS}
    vals.update({"probe": "0", "phase": "INJECTION", "target_seq": "10",
                 "target_pc": "4096", "tick": "100", "cycle": "1"})
    rows.append(",".join(vals[c] for c in R.COLUMNS))
    for i in range(1, 4):
        v = dict(vals)
        v.update({"probe": str(i), "phase": "PROBE"})
        rows.append(",".join(v[c] for c in R.COLUMNS))
    p = tmp_path / "bad.csv.gz"
    with gzip.open(p, "wt") as f:
        f.write("\n".join(rows) + "\n")
    _, checks = R.canonicalize("BAD", p, tmp_path / "canon")
    assert checks["recovered_complete"] is False
    assert checks["canonical_path"] is None
    assert checks["watchdog_rows"] == 0


def test_rp01_control_not_committed_blocks_complete():
    run = json.loads(sorted(RP01.glob(
        "RP01OBS-*-FAULT.strict.json"))[0].read_text())
    run["rp01_validation"]["valid"] = False
    gaps = E.validate_end_to_end_graph(run)
    assert "graph:rp01_audit_not_valid" in gaps


@pytest.mark.skipif(not RP.exists(), reason="canonical traces missing")
def test_rp01_canonical_gzip_is_independently_readable():
    fs = sorted(RP.glob("*.csv.gz"))
    assert len(fs) == 15
    for f in fs:
        with gzip.open(f, "rb") as g:
            data = g.read()
        lines = [x for x in data.decode().splitlines()
                 if x and not x.startswith("#")]
        assert lines[-1].split(",")[1] == "WATCHDOG", f.name
        assert sum(1 for x in lines if ",PROBE," in x) >= 287
        assert sum(1 for x in lines if ",INJECTION," in x) == 1


# ---------------------------------------------------------------------------
# 6. global edge-count consistency
# ---------------------------------------------------------------------------
REP = P.REPORTS


@pytest.mark.skipif(not (REP / "STRICT_E2E_CAUSAL_EDGES.csv").exists(),
                    reason="delivery not generated")
def test_json_csv_and_per_run_edge_counts_agree():
    edges = list(csv.DictReader(
        open(REP / "STRICT_E2E_CAUSAL_EDGES.csv")))
    per = list(csv.DictReader(
        open(REP / "STRICT_E2E_EDGE_COUNTS_PER_RUN.csv")))
    assert len(per) == 180
    assert sum(int(r["Edges"]) for r in per) == len(edges)
    assert len({r["EdgeID"] for r in edges}) == len(edges)
    for r in per:
        assert r["Status"] == "E2E_CAUSAL_COMPLETE"
    # JSON totals: count edges in delivery chains.
    chains = list(CH.glob("*.causal_chain.json"))
    assert len(chains) == 180
    total = 0
    for f in chains:
        total += len(json.loads(f.read_text())["edges"])
    assert total == len(edges)
