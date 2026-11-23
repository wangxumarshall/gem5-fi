#!/usr/bin/env python3
"""Strict causal reconstruction for the LSU E2E campaign.

Design rules (the point of this round):

* An edge exists only when the evidence proves a data/control/state
  relation.  Temporal adjacency, equal values with different provenance,
  same PC, or "it happened in the same run" are never sufficient.
* Every edge is graded:
    DIRECT_OBSERVED        the trace directly records the hardware relation
                           (renamed phys-reg def/use, explicit prop_edge,
                           payload->register record, memory version overlap).
    RECONSTRUCTED_VERIFIED the relation is rebuilt from committed
                           instructions + actual operand values + real
                           instruction semantics, and independently checked.
    CORRELATED_ONLY        only ordering/association exists.
    UNRESOLVED             required evidence is missing.
* Only the first two grades may carry an E2E_CAUSAL_COMPLETE chain.
* The software hash chain is verified with the real `when_fnv` semantics,
  not by assuming that hash events are connected.
* Masking is classified from the observed taint lifecycle, never from the
  model id.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_lib as L
import e2e_strict_data as D
import e2e_flow as F

EXT = L.EXT

DIRECT = "DIRECT_OBSERVED"
RECON = "RECONSTRUCTED_VERIFIED"
CORR = "CORRELATED_ONLY"
UNRES = "UNRESOLVED"
STRONG = {DIRECT, RECON}


def compute_status(gaps, target_present=True):
    """The only place an E2E status is decided.

    A complete chain requires zero gaps.  Missing evidence never rounds up
    to COMPLETE.
    """
    if not target_present:
        return "E2E_CAUSAL_UNRESOLVED"
    if not gaps:
        return "E2E_CAUSAL_COMPLETE"
    return "E2E_CAUSAL_PARTIAL"


# ---------------------------------------------------------------------------
# evidence records
# ---------------------------------------------------------------------------
@dataclass
class Edge:
    source: str
    target: str
    dependency: str
    level: str = UNRES
    method: str = ""
    value: object = None
    src_file: str = ""
    src_line: int = 0
    notes: list = field(default_factory=list)
    source_kind: str = ""
    target_kind: str = ""
    edge_id: str = ""
    source_seq: object = None
    target_seq: object = None
    operation: str = ""
    operands: object = None
    result: object = None
    phys_dependency: object = None

    def as_dict(self):
        return {
            "edge_id": self.edge_id,
            "source": self.source, "target": self.target,
            "dependency": self.dependency, "evidence_level": self.level,
            "source_kind": self.source_kind, "target_kind": self.target_kind,
            "source_dyn_inst_seq": self.source_seq,
            "target_dyn_inst_seq": self.target_seq,
            "operation": self.operation or self.dependency,
            "operands": self.operands,
            "result": (D.hexv(self.result) if hasattr(D, "hexv") else
                       _hex(self.result)),
            "physical_or_data_dependency": self.phys_dependency,
            "verification_method": self.method,
            "value": D.hexv(self.value) if hasattr(D, "hexv") else _hex(self.value),
            "source_file": self.src_file, "source_line": self.src_line,
            "notes": self.notes,
        }


@dataclass
class Node:
    event_id: str
    kind: str
    detail: dict = field(default_factory=dict)

    def as_dict(self):
        return {"event_id": self.event_id, "kind": self.kind, **self.detail}


def _hex(v):
    if v is None:
        return None
    if isinstance(v, int):
        return "0x%x" % v
    return str(v)


class Graph:
    def __init__(self, run_id=""):
        self.nodes = []
        self.edges = []
        self._n = 0
        self._e = 0
        self.run_id = run_id

    def node(self, kind, **kw):
        self._n += 1
        n = Node(f"E{self._n}", kind, kw)
        self.nodes.append(n)
        return n.event_id

    def _seq(self, nid):
        for n in self.nodes:
            if n.event_id != nid:
                continue
            d = n.detail
            for k in ("dyn_inst_seq", "def_seq", "marker_seq"):
                if d.get(k) is not None:
                    return d[k]
            expr = d.get("expression") or {}
            if expr.get("def_seq") is not None:
                return expr["def_seq"]
        return None

    def edge(self, src, dst, dep, level=UNRES, method="", **kw):
        self._e += 1
        e = Edge(src, dst, dep, level, method,
                 source_kind=self._kind(src), target_kind=self._kind(dst),
                 edge_id="%s:ED%06d" % (self.run_id or "RUN", self._e),
                 **kw)
        if e.source_seq is None:
            e.source_seq = self._seq(src)
        if e.target_seq is None:
            e.target_seq = self._seq(dst)
        self.edges.append(e)
        return e

    def _kind(self, nid):
        for n in self.nodes:
            if n.event_id == nid:
                return n.kind
        return ""

    def by_kind(self, kind):
        return [n for n in self.nodes if n.kind == kind]

    def level_count(self):
        return collections.Counter(e.level for e in self.edges)


# ---------------------------------------------------------------------------
# end-to-end graph validation
# ---------------------------------------------------------------------------
RP01_REQUIRED_KINDS = (
    "replay_suppression", "target_instruction", "iq_state",
    "ready_list_state", "replay_list_state", "lq_state",
    "rob_head_state", "commit_progress", "no_progress_interval",
    "simulator_watchdog",
)


def _graph_maps(nodes, edges):
    kinds = {n.get("event_id"): n.get("kind") for n in nodes}
    adj = collections.defaultdict(list)
    for e in edges:
        if e.get("evidence_level") in STRONG:
            adj[e.get("source")].append(e.get("target"))
    return kinds, adj


def _reachable(adj, starts, goal):
    seen = set(starts)
    dq = collections.deque(starts)
    while dq:
        x = dq.popleft()
        if x == goal:
            return True
        for y in adj.get(x, ()):
            if y not in seen:
                seen.add(y)
                dq.append(y)
    return False


def validate_end_to_end_graph(run):
    """Validate a *complete* built graph; this is the only input to status.

    A graph is complete only if a strong-evidence directed path exists
    from the fault root to the required terminal, the graph is
    structurally sound, the final output expression is recomputed, the
    hash state streams are def/use-connected, and every masking endpoint
    has a real incoming mechanism edge.
    """
    gaps = []
    nodes = run.get("nodes") or []
    edges = run.get("edges") or []
    cls = run.get("classification") or {}
    symptom = cls.get("software_symptom")
    termination = cls.get("propagation_termination")
    terminal = run.get("terminal")
    kinds, adj = _graph_maps(nodes, edges)
    ids = [n.get("event_id") for n in nodes]
    if len(ids) != len(set(ids)):
        gaps.append("graph:duplicate_node_ids")
    edge_ids = [e.get("edge_id") for e in edges]
    if any(not x for x in edge_ids) or len(edge_ids) != len(set(edge_ids)):
        gaps.append("graph:duplicate_or_missing_edge_ids")
    for e in edges:
        if e.get("source") not in kinds or e.get("target") not in kinds:
            gaps.append("graph:edge_references_missing_node")
            break
    roots = [n.get("event_id") for n in nodes
             if n.get("kind") in ("injection", "fault_injection")]
    if not roots:
        gaps.append("graph:fault_root_missing")
        return gaps
    root = roots[0]

    def by_kind(*k):
        return [n.get("event_id") for n in nodes if n.get("kind") in k]

    if symptom == "HANG_TIMEOUT" or terminal in ("HANG_WATCHDOG", "HANG"):
        missing = [k for k in RP01_REQUIRED_KINDS if not by_kind(k)]
        if missing:
            gaps.append("graph:rp01_state_nodes_missing=%s" %
                        ",".join(missing))
        wd = by_kind("simulator_watchdog")
        if not wd:
            gaps.append("graph:watchdog_terminal_missing")
        elif not _reachable(adj, [root], wd[0]):
            gaps.append("graph:no_strong_path_root_to_watchdog")
        if not any(e.get("dependency") == "watchdog_terminated" and
                   e.get("evidence_level") in STRONG for e in edges):
            gaps.append("graph:watchdog_edge_not_strong")
        if not (run.get("rp01_validation") or {}).get("valid"):
            gaps.append("graph:rp01_audit_not_valid")
        return gaps

    outputs = by_kind("application_output")
    if not outputs:
        gaps.append("graph:application_output_missing")
        return gaps
    onode = outputs[0]
    if not _reachable(adj, [root], onode):
        gaps.append("graph:no_strong_path_root_to_application_output")

    expr = by_kind("final_expression")
    if not expr:
        gaps.append("graph:final_expression_missing")
    else:
        # For a wrong output the expression must itself be reachable from
        # the fault.  For a masked run the strong causal path goes
        # fault -> masking_endpoint -> output; the output expression is
        # still recomputed but is not the fault-propagation path.
        if symptom == "WRONG_OUTPUT" and not _reachable(adj, [root],
                                                        expr[0]):
            gaps.append("graph:no_strong_path_root_to_final_expression")
        if not any(e.get("source") == expr[0] and
                   e.get("target") == onode and
                   e.get("evidence_level") in STRONG for e in edges):
            gaps.append("graph:final_expression_to_output_not_strong")
    outv = run.get("software", {}).get("output_validation") or {}
    if not outv.get("verified"):
        gaps.append("graph:final_output_expression_unverified")
    hf = run.get("software", {}).get("hash_flow") or {}
    if hf.get("unverified_links", 0):
        gaps.append("graph:hash_stream_unverified_links=%s" %
                    hf.get("unverified_links"))
    if hf.get("events_with_bad_provenance", 0):
        gaps.append("graph:hash_slot_provenance_failures=%s" %
                    hf.get("events_with_bad_provenance"))

    if symptom in ("NO_VISIBLE_ERROR", "INTERMEDIATE_VALUE_DIVERGENCE"):
        ends = by_kind("masking_endpoint")
        if not ends:
            gaps.append("graph:masking_endpoint_missing")
        else:
            ep = ends[0]
            indeg = [e for e in edges if e.get("target") == ep and
                     e.get("evidence_level") in STRONG]
            if not indeg:
                gaps.append("graph:masking_endpoint_has_no_strong_in_edge")
            if not _reachable(adj, [root], ep):
                gaps.append("graph:no_strong_path_root_to_masking_endpoint")
            if not any(e.get("source") == ep and e.get("target") == onode
                       and e.get("evidence_level") in STRONG
                       for e in edges):
                gaps.append("graph:masking_endpoint_to_output_not_strong")
            proof = (run.get("classification") or {}).get(
                "masking_evidence_complete")
            if not proof:
                gaps.append("graph:masking_evidence_incomplete")

    if symptom == "INTERMEDIATE_VALUE_DIVERGENCE":
        if not by_kind("first_software_divergence"):
            gaps.append("graph:intermediate_divergence_node_missing")
        elif not _reachable(adj, [root],
                            by_kind("first_software_divergence")[0]):
            gaps.append("graph:first_divergence_not_connected")

    if symptom == "WRONG_OUTPUT":
        fd = by_kind("first_software_divergence")
        if not fd:
            gaps.append("graph:wrong_output_without_first_divergence")
        elif not _reachable(adj, [root], fd[0]):
            gaps.append("graph:first_divergence_not_connected")
        av = (run.get("software") or {}).get("application_validation") or {}
        if not av.get("verified"):
            gaps.append("graph:application_symptom_evidence_unverified")

    # ---- semantic verification gate ----------------------------------
    # A strong graph is not enough: every key instruction on the taint
    # path must also have been recomputed with real ARM64 semantics.
    sw = run.get("semantic_walk") or {}
    if sw and run.get("model") != "RP01":
        if sw.get("semantic_mismatches", 0):
            gaps.append("semantics:unresolved_mismatches=%s" %
                        sw.get("semantic_mismatches"))
        crit = sw.get("unsupported_critical",
                      sw.get("unsupported_semantics", 0))
        if crit:
            gaps.append("semantics:unsupported_critical_instruction=%s" %
                        crit)
        if sw.get("unverified_semantic_edges", 0):
            gaps.append("semantics:unverified_taint_edges=%s" %
                        sw.get("unverified_semantic_edges"))
        nz = sw.get("nzcv") or {}
        if nz.get("flag_semantic_mismatches", 0):
            gaps.append("semantics:nzcv_mismatches=%s" %
                        nz.get("flag_semantic_mismatches"))
        if nz.get("conditional_unverified", 0):
            gaps.append("semantics:conditional_flags_unverified=%s" %
                        nz.get("conditional_unverified"))
        mem = sw.get("memory") or {}
        if mem.get("semantics_incomplete", 0):
            gaps.append("semantics:memory_incomplete=%s" %
                        mem.get("semantics_incomplete"))
        multi = sw.get("multi_source") or {}
        if multi.get("dropped_sources", 0):
            gaps.append("semantics:dropped_taint_sources=%s" %
                        multi.get("dropped_sources"))
        if (sw.get("edge_count", 0) == 0 and
                termination == "COMMITTED_AND_PROPAGATED"):
            gaps.append("semantics:empty_taint_walk_for_propagated_fault")
    return gaps


def compute_status(gaps, target_present=True, run=None):
    """The only place an E2E status is decided.

    A complete chain requires zero gaps *and* a validated directed
    strong-evidence graph.  Missing evidence never rounds up to COMPLETE.
    """
    if not target_present:
        return "E2E_CAUSAL_UNRESOLVED"
    all_gaps = list(gaps)
    if run is not None:
        all_gaps += validate_end_to_end_graph(run)
    if not all_gaps:
        return "E2E_CAUSAL_COMPLETE"
    return "E2E_CAUSAL_PARTIAL"


# ---------------------------------------------------------------------------
# propagation trace with line numbers
# ---------------------------------------------------------------------------
class PropTrace:
    def __init__(self, path):
        self.path = str(path)
        self.rows = []
        self.by_id = {}
        ln = 0
        for text in D.gz_lines(path):
            ln += 1
            if text.startswith("#") or not text.strip():
                continue
            a = next(__import__("csv").reader([text]))
            if len(a) < 10:
                continue
            d = {"line": ln, "node_id": a[0], "tick": a[1], "ptag": a[2],
                 "kind": a[3], "dyn_inst_seq": a[4],
                 "request_id": a[5], "addr": a[6], "phys_reg": a[7],
                 "arch_reg": a[8], "detail": a[9], "kv": {}}
            d["kv"] = dict(re.findall(r"([A-Za-z0-9_]+)=([^;]*)", d["detail"]))
            try:
                d["seq_int"] = int(d["dyn_inst_seq"]) if d["dyn_inst_seq"] else None
            except ValueError:
                d["seq_int"] = None
            try:
                d["tick_int"] = int(d["tick"]) if d["tick"] else None
            except ValueError:
                d["tick_int"] = None
            d["node_id_int"] = _to_int(d["node_id"])
            self.rows.append(d)
            if d["node_id"]:
                self.by_id[d["node_id"]] = d
        self.pkinds = collections.defaultdict(list)
        for d in self.rows:
            self.pkinds[d["kind"]].append(d)

    def kind(self, *k):
        return [r for r in self.rows if r["kind"] in k]

    def nodes_with_hash(self):
        out = {}
        for r in self.rows:
            h = declared_hash(r)
            if h:
                out[r["node_id"]] = h
        return out


def _to_int(s):
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


def _norm_hash(h):
    if h is None:
        return None
    h = str(h).strip().lower()
    if h in ("", "null", "none", "0"):
        return None
    return h.lstrip("0x") or None


def declared_hash(r):
    kv = r["kv"]
    # taint_reg's produced value is the register writeback (which may be a
    # partial/assembled payload, e.g. DA04 byte-enable); consumers consume
    # that writeback hash, not the raw payload hash.
    for k in ("writeback_value_fnv", "payload_fnv", "data_fnv",
              "injection_fnv", "store_data_fnv", "packet_data_fnv",
              "dest_value_hash"):
        if _norm_hash(kv.get(k)):
            return _norm_hash(kv[k])
    if r["kind"] == "consumer":
        return _norm_hash(kv.get("consumer_output_fnv"))
    return None


# ---------------------------------------------------------------------------
# architectural memory model (committed program order)
# ---------------------------------------------------------------------------
LOAD_MN = ("ldr", "ldur", "ldrb", "ldrh", "ldrsb", "ldrsh", "ldrsw",
           "ldar", "ldaxr", "ldxr")
STORE_MN = ("str", "stur", "strb", "strh", "stlr", "stlxr", "stxr",
            "cas", "swp")


def is_load_op(op):
    return op.startswith(LOAD_MN)


def is_store_op(op):
    return op.startswith(STORE_MN)


def insn_mnem(r, disasm):
    """The real instruction mnemonic.

    gem5's DynInst op name can be a micro-op (e.g. ``addxi_uop`` for a
    store address generation).  The static disassembly is the authority for
    memory/ALU classification.
    """
    info = disasm.get(r.pc) if disasm else None
    return info[0] if info else r.op


class ArchMemory:
    """Byte-addressed architectural memory reconstructed from commit order.

    This is a validator as much as a model: every load whose address can be
    computed is checked against the bytes the model holds.  A high match
    rate proves the address reconstruction (and therefore the memory
    versioning used by masking/version edges) is sound.
    """

    def __init__(self, trace, disasm):
        self.trace = trace
        self.disasm = disasm
        self.mem = {}
        self.accesses = {}      # row idx -> dict
        self.load_checked = 0
        self.load_matched = 0
        self.load_address_unknown = 0
        self.store_checked = 0
        self.store_address_unknown = 0
        self._build()

    def _values(self, r):
        out = {}
        for (_c, arch, p), val in zip(r.srcs, r.srcvals):
            if _c is None or _c < 0 or arch is None or arch < 0 or \
                    p is None or p < 0:
                continue
            out[arch] = val
        return out

    def _build(self):
        for r in self.trace.rows:
            info = self.disasm.get(r.pc)
            if not info:
                continue
            mnem, operands = info
            if mnem in ("stp", "stnp"):
                if r.op == "strxi_uop":
                    self._pair_store_row(r, info)
                continue
            if mnem in ("ldp", "ldnp", "ldpsw"):
                if r.op == "ldp_uop":
                    self._pair_load_row(r, info)
                continue
            if not (is_load_op(mnem) or is_store_op(mnem)):
                continue
            vals = self._values(r)
            res = D.memory_address(mnem, operands, vals)
            if res is None:
                if is_load_op(mnem):
                    self.load_address_unknown += 1
                else:
                    self.store_address_unknown += 1
                continue
            addr, width, _ = res
            acc = {"addr": addr, "width": width, "mnem": mnem,
                   "operands": operands}
            if is_store_op(mnem):
                ops = D.split_ops(operands)
                data_reg = D.parse_reg(ops[0]) if ops else None
                if data_reg is None:
                    continue
                if data_reg[0] == "zr":
                    # Zero-register stores (e.g. buffer initialisation)
                    # are real committed memory versions.
                    data = 0
                else:
                    data = vals.get(data_reg[1])
                if data is None:
                    continue
                acc["value"] = data & ((1 << (8 * width)) - 1)
                self._write(addr, width, acc["value"])
                self.store_checked += 1
            elif is_load_op(mnem):
                data = self._read(addr, width)
                recorded = r.dst_value()
                if recorded is not None:
                    cmpv = recorded & ((1 << (8 * width)) - 1)
                    acc["mem_value"] = data
                    acc["recorded"] = cmpv
                    acc["matched"] = (data == cmpv)
                    self.load_checked += 1
                    if data == cmpv:
                        self.load_matched += 1
            self.accesses[r.idx] = acc

    def _pair_layout(self, info, vals):
        if not info:
            return None
        return D.pair_memory_layout(info[0], info[1], vals)

    def _pair_store_row(self, r, info):
        regs = []
        for tok in D.split_ops(info[1])[:2]:
            reg = D.parse_reg(tok)
            if reg is not None:
                regs.append(reg)
        if len(regs) != 2:
            self.store_address_unknown += 1
            return
        src = [(a, v) for (c, a, _p), v in zip(r.srcs, r.srcvals)
               if c == 0 and a is not None and a >= 0 and v is not None]
        if len(src) < 2:
            return
        data_arch, data = None, None
        for a, v in src:
            if a in (regs[0][1], regs[1][1]):
                data_arch, data = a, v
        if data_arch is None:
            return
        idx = 0 if data_arch == regs[0][1] else 1
        addr_val = next((v for (a, v) in src if a != data_arch), None)
        if addr_val is None:
            return
        width = D.reg_width(regs[idx]) // 8
        addr = (addr_val + idx * width) & D.MASK64
        self._write(addr, width, data)
        self.accesses[r.idx] = {"addr": addr, "width": width,
                                "mnem": info[0], "operands": info[1],
                                "element": idx, "value": data}
        self.store_checked += 1

    def _pair_load_row(self, r, info):
        vals = self._values(r)
        srcvals = [v for (c, _a, _p), v in zip(r.srcs, r.srcvals)
                   if c == 0 and v is not None]
        dsts = [(a, p, v) for (c, a, p, v) in r.dsts if c == 0]
        regs = []
        for tok in D.split_ops(info[1])[:2]:
            reg = D.parse_reg(tok)
            if reg is not None:
                regs.append(reg)
        if not srcvals or len(dsts) != 2 or len(regs) != 2:
            self.load_address_unknown += 1
            return
        addr0 = srcvals[-1] & D.MASK64
        by_arch = {a: v for (a, _p, v) in dsts}
        checked = matched = 0
        for i, reg in enumerate(regs):
            ew = D.reg_width(reg) // 8
            addr = (addr0 + i * ew) & D.MASK64
            data = self._read(addr, ew)
            rec = by_arch.get(reg[1])
            if rec is None:
                continue
            checked += 1
            mask = (1 << (8 * ew)) - 1
            ok = (data & mask) == (rec & mask)
            matched += int(ok)
            self.accesses[r.idx] = {"addr": addr, "width": ew,
                                    "mnem": info[0], "operands": info[1],
                                    "element": i, "mem_value": data,
                                    "recorded": rec & mask, "matched": ok}
        self.load_checked += checked
        self.load_matched += matched

    def _write(self, addr, width, value):
        for i in range(width):
            self.mem[(addr + i) & D.MASK64] = (value >> (8 * i)) & 0xff

    def _read(self, addr, width):
        v = 0
        for i in range(width):
            v |= self.mem.get((addr + i) & D.MASK64, 0) << (8 * i)
        return v

    def stats(self):
        return {
            "load_checked": self.load_checked,
            "load_matched": self.load_matched,
            "load_match_rate": (round(self.load_matched / self.load_checked, 6)
                                if self.load_checked else None),
            "load_address_unknown": self.load_address_unknown,
            "store_checked": self.store_checked,
            "store_address_unknown": self.store_address_unknown,
        }


# ---------------------------------------------------------------------------
# taint lifecycle
# ---------------------------------------------------------------------------
@dataclass
class TaintState:
    phys: tuple
    value: int
    hash: str
    seq: int
    node_id: str
    ptag: str


class TaintLifecycle:
    """Replays the tracer's verified consumer edges.

    The tracer emits a consumer row only when the committing instruction's
    source physical register is tainted AND the commit-time input value hash
    equals the taint entry's value hash.  We re-check both conditions from
    the raw rows, so a corrupted/incomplete edge cannot enter the chain.
    """

    def __init__(self, pt, trace):
        self.pt = pt
        self.trace = trace
        self.consumers = []
        self.seeds = []
        self.mismatches = []
        self.partial_payloads = []
        self.tainted_seqs = collections.defaultdict(list)
        self.phys_at_seq = {}    # seq -> {(cls,phys): TaintState}
        self._build()

    def _build(self):
        # Seed from taint_reg: payload -> architectural register.
        current = {}
        for r in self.pt.kind("taint_reg"):
            h = _norm_hash(r["kv"].get("writeback_value_fnv"))
            v = _inthex(r["kv"].get("writeback_value"))
            cls = {"int": 0, "float": 1, "vec": 2}.get(
                r["kv"].get("class"), 0)
            phys = _to_int(r["kv"].get("phys_reg"))
            if phys is None:
                continue
            src_id = r["kv"].get("source_event_id", "")
            src_hash = _norm_hash(r["kv"].get("source_value_hash"))
            if h and src_hash and h != src_hash:
                if r["kv"].get("value_matches_payload") == "1":
                    self.mismatches.append({
                        "node": r["node_id"],
                        "reason": "taint_reg_source_hash_mismatch",
                        "writeback": h, "source": src_hash})
                else:
                    # Partial / assembled payload (byte-enable or width
                    # merge): the register legitimately differs from the
                    # raw payload.  Keep it, but record the distinction.
                    self.partial_payloads.append({
                        "node": r["node_id"], "writeback": h,
                        "payload": src_hash,
                        "basis": r["kv"].get("hash_basis")})
            st = TaintState((cls, phys), v, h, r["seq_int"], r["node_id"],
                            r["ptag"])
            current[(cls, phys)] = st
            self.seeds.append(st)
            if r["seq_int"] is not None:
                self.phys_at_seq.setdefault(r["seq_int"], {})[(cls, phys)] = st

        # Consumers in trace order: source_event_id must be a tainted node
        # and the input hash must equal that node's produced hash.
        by_id = self.pt.by_id
        for r in self.pt.kind("consumer"):
            kv = r["kv"]
            i_in = _norm_hash(kv.get("consumer_input_fnv"))
            i_out = _norm_hash(kv.get("consumer_output_fnv"))
            se = kv.get("source_event_id", "")
            if kv.get("consumer_input_matches_source") != "1":
                self.mismatches.append({"node": r["node_id"],
                                        "reason": "input_not_matching_source"})
                continue
            src = by_id.get(se)
            src_hash = declared_hash(src) if src else None
            if src is None:
                self.mismatches.append({
                    "node": r["node_id"], "reason": "unknown_source_event",
                    "source_event_id": se})
                continue
            if not i_in or not src_hash or i_in != src_hash:
                self.mismatches.append({
                    "node": r["node_id"], "reason": "input_hash_mismatch",
                    "input": i_in, "source_hash": src_hash})
                continue
            # The source node must be reachable from a seed through the
            # consumer chain (source_event_id == a prior consumer or seed).
            if not self._reachable(se, r, current):
                self.mismatches.append({
                    "node": r["node_id"], "reason": "source_not_tainted",
                    "source_event_id": se})
                continue
            cls = {"int": 0, "float": 1, "vec": 2}.get(kv.get("class"), 0)
            dst_phys = _to_int(kv.get("dest_phys_reg"))
            out_val = _inthex(kv.get("consumer_output_value"))
            st = TaintState((cls, dst_phys), out_val, i_out, r["seq_int"],
                            r["node_id"], r["ptag"])
            if dst_phys is not None:
                current[(cls, dst_phys)] = st
            c = {
                "node": r["node_id"], "seq": r["seq_int"], "pc": kv.get("pc"),
                "source_event_id": se, "input": i_in, "output": i_out,
                "in_value": _inthex(kv.get("consumer_input_value")),
                "out_value": out_val, "dest_phys": dst_phys,
                "dest_arch": _to_int(kv.get("dest_arch_reg")),
                "ptag": r["ptag"], "line": r["line"],
            }
            self.consumers.append(c)
            if r["seq_int"] is not None:
                self.tainted_seqs[r["seq_int"]].append(c)

    def _reachable(self, src_id, r, current):
        if src_id in self.pt.by_id:
            src = self.pt.by_id[src_id]
            if src["kind"] == "taint_reg":
                return True
            if src["kind"] == "consumer":
                return True
            # resp/fwd/inj are valid payload producers for a taint_reg, but
            # a consumer must consume a register (taint_reg/consumer).
            return src["kind"] in ("resp", "fwd", "taint_reg")
        return False

    def last_consumer(self):
        return self.consumers[-1] if self.consumers else None

    def state_at(self, seq):
        return self.phys_at_seq.get(seq, {})


def _inthex(v):
    """Value fields in prop_trace/commit_trace are bare lowercase hex."""
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ("", "null", "none"):
        return None
    try:
        return int(s, 16)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# software events from marker groups
# ---------------------------------------------------------------------------
@dataclass
class SWEvent:
    group: D.MarkerGroup
    key: tuple
    occurrence: int
    a: int
    b: int
    c: int
    seq: int
    op_seq: int | None
    op_pc: int | None
    op_name: str | None

    @property
    def mtype(self):
        return self.group.mtype

    @property
    def site(self):
        return self.group.site

    @property
    def order(self):
        return self.group.order

    def control_tuple(self):
        return (self.a, self.b, self.c)

    def as_dict(self):
        return {
            "type": D.TYPE_NAME.get(self.mtype, hex(self.mtype)),
            "site": self.site, "order": self.order,
            "iteration": (self.c >> 32) if self.mtype in D.AUX_ITER_TYPES
            else None,
            "a": _hex(self.a), "b": _hex(self.b), "c": _hex(self.c),
            "dyn_inst_seq": self.seq, "op_dyn_inst_seq": self.op_seq,
            "op_pc": _hex(self.op_pc), "op": self.op_name,
            "marker_instruction_seqs": self.group.seqs,
            "ctrace_line": self.group.lines[3],
        }


def _origin_insn(trace, disasm, cls, phys, before_idx, depth=0):
    """Follow a single-source ALU copy chain back to its originating insn."""
    if depth > 8:
        return None
    r = trace.defining_insn(cls, phys, before_idx)
    if r is None:
        return None
    mnem = insn_mnem(r, disasm)
    if is_load_op(mnem) or is_store_op(mnem):
        return r
    srcs = [s for s in r.srcs if s[0] >= 0 and s[2] is not None and s[2] >= 0]
    if len(srcs) == 1:
        back = trace.defining_insn(srcs[0][0], srcs[0][2], r.idx)
        if back is not None:
            return _origin_insn(trace, disasm, srcs[0][0], srcs[0][2], r.idx,
                                depth + 1)
    return None


def build_sw_events(trace, disasm):
    events = []
    cnt = collections.Counter()
    for g in trace.markers:
        it = (g.vals[3] >> 32) if g.mtype in D.AUX_ITER_TYPES else None
        key = ((g.mtype, g.site, it) if g.mtype in D.AUX_ITER_TYPES
               else (g.mtype, g.site))
        occ = cnt[key]
        cnt[key] += 1
        op_seq = op_pc = op_name = None
        if g.mtype == D.T_LOAD:
            # payload layout: (tag, address, loaded_value, aux)
            (cls, phys), _v, _a = g.slot_source(2)
            if phys is not None:
                orig = _origin_insn(trace, disasm, cls, phys, g.start_idx)
                if orig is not None and is_load_op(insn_mnem(orig, disasm)):
                    op_seq, op_pc, op_name = orig.seq, orig.pc, orig.op
        elif g.mtype == D.T_STORE:
            # payload layout: (tag, address, stored_value, aux)
            (cls, phys), v, _a = g.slot_source(2)
            addr = g.vals[1]
            # nearest preceding store whose reconstructed address matches
            for j in range(g.start_idx - 1, max(-1, g.start_idx - 200), -1):
                r = trace.rows[j]
                info = disasm.get(r.pc)
                if not info or not is_store_op(info[0]):
                    continue
                vals = {}
                for (_c, arch, p), val in zip(r.srcs, r.srcvals):
                    if _c is None or _c < 0 or arch is None or arch < 0 or \
                            p is None or p < 0:
                        continue
                    vals[arch] = val
                res = D.memory_address(info[0], info[1], vals)
                if res and res[0] == addr:
                    op_seq, op_pc, op_name = r.seq, r.pc, r.op
                    break
        events.append(SWEvent(g, key, occ, g.vals[1], g.vals[2],
                              g.vals[3], g.seqs[3], op_seq, op_pc, op_name))
    return events


def load_control_events(model, context):
    p = (EXT / "results/controls" / f"E2E-{model}-{context}-CTRL" /
         "attempt_1/sw_events.json")
    if not p.exists():
        return []
    d = json.loads(p.read_text())
    return d, d.get("events", [])


def ctrl_index(ctrl_events):
    idx = {}
    for e in ctrl_events:
        key = tuple(e["key"])
        k = (key, e["occ"])
        idx[k] = e
    return idx


def iter_sw_diffs(events, ctrl_events):
    """Yield (fault_event|None, control_event|None, fields) in fault order."""
    cm = ctrl_index(ctrl_events)
    for e in events:
        c = cm.get((e.key, e.occurrence))
        if c is None:
            yield e, None, ["event"]
            continue
        fields = []
        if e.a != c["a"]:
            fields.append("a")
        if e.b != c["b"]:
            fields.append("b")
        if e.c != c["c"]:
            fields.append("c")
        if fields:
            yield e, c, fields
    fm = {(e.key, e.occurrence): e for e in events}
    for c in ctrl_events:
        if (tuple(c["key"]), c["occ"]) not in fm:
            yield None, c, ["event"]


def first_sw_divergence(events, ctrl_events):
    cm = ctrl_index(ctrl_events)
    for e in events:
        c = cm.get((e.key, e.occurrence))
        if c is None:
            return {"kind": "event_missing_in_control", "fault": e,
                    "control": None, "fields": ["event"]}
        fields = []
        if e.a != c["a"]:
            fields.append("a")
        if e.b != c["b"]:
            fields.append("b")
        if e.c != c["c"]:
            fields.append("c")
        if fields:
            return {"kind": "value", "fault": e, "control": c,
                    "fields": fields}
    fm = {(e.key, e.occurrence): e for e in events}
    for c in ctrl_events:
        if (tuple(c["key"]), c["occ"]) not in fm:
            return {"kind": "event_missing_in_fault", "fault": None,
                    "control": c, "fields": ["event"]}
    return None


# ---------------------------------------------------------------------------
# injection / target extraction
# ---------------------------------------------------------------------------
def _seq_of(kv, *keys):
    for k in keys:
        if k in kv:
            try:
                return int(str(kv[k]), 0)
            except ValueError:
                try:
                    return int(str(kv[k]), 16)
                except ValueError:
                    continue
    return None


def _addr_of(kv, *keys):
    for k in keys:
        if k in kv:
            try:
                s = str(kv[k]).strip()
                return int(s, 0) if s.lower().startswith("0x") else int(s, 16)
            except ValueError:
                continue
    return None


def extract_target(model, pt, trace, stdout):
    injections = [r for r in pt.rows if r["kind"].startswith("inj")]
    selected = None
    role = "load"
    if model == "RP01":
        m = re.search(r"RP01_SKIP_REPLAY ordinal=(\d+) load_seq=(\d+) "
                      r"load_pc=(\d+) lq_idx=(\d+) lq_gen=(\d+) "
                      r"store_seq=(\d+)", stdout)
        if not m:
            return None, injections
        seq = int(m.group(2))
        selected = {
            "kind": "rp01_skip", "seq": seq, "pc": int(m.group(3)),
            "addr": None, "role": "load",
            "kv": {"ordinal": m.group(1), "load_seq": m.group(2),
                   "load_pc": m.group(3), "lq_idx": m.group(4),
                   "lq_gen": m.group(5), "store_seq": m.group(6)},
            "node_id": None, "tick": None,
            "evidence": "stdout.log:RP01_SKIP_REPLAY"}
        return selected, injections
    if not injections:
        return None, injections
    if model == "A03":
        eff = [r for r in injections if r["kv"].get("value_changed") != "0"]
        selected = (eff or injections)[0]
    else:
        selected = injections[0]
    kv = selected["kv"]
    if model in ("A01", "A03", "FW02"):
        seq = selected["seq_int"]
        addr = _addr_of(kv, "new_addr", "old_addr")
    elif model == "LQ04":
        seq = selected["seq_int"]
        addr = _addr_of(kv, "addr")
    elif model == "SQ01":
        seq = _seq_of(kv, "store_seq", "dyn_inst_seq")
        addr = _addr_of(kv, "addr")
        role = "store"
    elif model == "SQ03":
        seq = _seq_of(kv, "store_seq")
        addr = _addr_of(kv, "store_addr")
        role = "store"
    elif model == "SP05":
        seq = _seq_of(kv, "store_seq")
        addr = _addr_of(kv, "store_addr")
        role = "store"
    elif model == "FW05":
        seq = _seq_of(kv, "load_seq")
        addr = _addr_of(kv, "load_addr")
    elif model == "MD04":
        seq = _seq_of(kv, "younger_load_dyn_inst_seq", "load_seq",
                      "dyn_inst_seq")
        addr = _addr_of(kv, "load_addr", "addr")
    elif model == "DA04":
        seq = selected["seq_int"]
        addr = _addr_of(kv, "addr_after", "addr_before")
        role = "store"
    elif model == "LP01":
        seq = _seq_of(kv, "dyn_inst_seq")
        addr = _addr_of(kv, "vaddr")
    else:
        seq = selected["seq_int"]
        addr = None
    if seq is None:
        seq = selected["seq_int"]
    pc = selected["pc"] if "pc" in selected else None
    if pc is None:
        row = trace.row_of_seq(seq) if seq is not None else None
        pc = row.pc if row else None
    return {
        "kind": selected["kind"], "seq": seq, "pc": pc, "addr": addr,
        "role": role, "kv": kv, "node_id": selected["node_id"],
        "tick": selected["tick_int"],
        "evidence": "prop_trace.csv.gz",
    }, injections


MECHANISM_CLASS = {
    "ADDRESS_CHANGED": "ADDRESS_CHANGED",
    "STORE_DATA_CORRUPTED": "STORE_DATA_CORRUPTED",
    "BYTE_ENABLE_CLEARED": "BYTE_ENABLE_CLEARED",
    "WRONG_FORWARD_SOURCE": "WRONG_FORWARD_SOURCE",
    "VIOLATION_REPORT_SUPPRESSED": "WRONG_FORWARD_SOURCE",
    "RESPONSE_DATA_CORRUPTED": "RESPONSE_DATA_CORRUPTED",
    "REPLAY_SUPPRESSED": "REPLAY_SUPPRESSED",
    "LQ_ENTRY_INVALIDATED": "INTERNAL_STATE_ONLY",
    "CANWB_SET_EARLY": "INTERNAL_STATE_ONLY",
    "STORE_WRITE_SUPPRESSED": "INTERNAL_STATE_ONLY",
    "INTERNAL_STATE_ONLY": "INTERNAL_STATE_ONLY",
}


def fault_mechanism_class(origin):
    """Coarse FaultMechanism family; the detail stays in ``origin``.

    UNKNOWN is preserved as UNKNOWN rather than guessed from the model id.
    """
    return MECHANISM_CLASS.get(origin, "UNKNOWN")


def injection_origin_kind(target, model):
    """Classify the *fault effect* from the injection record fields alone."""
    kv = target["kv"] if target else {}
    if model == "RP01":
        return "REPLAY_SUPPRESSED"
    old_a, new_a = kv.get("old_addr"), kv.get("new_addr")
    if old_a and new_a and str(old_a).lower() != str(new_a).lower():
        return "ADDRESS_CHANGED"
    if "old_be" in kv and str(kv.get("old_be")).lower() != \
            str(kv.get("new_be")).lower():
        return "BYTE_ENABLE_CLEARED"
    if "old_byte" in kv and str(kv.get("old_byte")).lower() != \
            str(kv.get("new_byte")).lower():
        return "STORE_DATA_CORRUPTED"
    if kv.get("wrong_source_substitution") == "1" or \
            kv.get("selected_source") == "alt_store":
        return "WRONG_FORWARD_SOURCE"
    if kv.get("orig_data_hex") and kv.get("inj_data_hex") and \
            kv["orig_data_hex"].lower() != kv["inj_data_hex"].lower():
        return "RESPONSE_DATA_CORRUPTED"
    if kv.get("valid_before") == "1" and kv.get("valid_after") == "0":
        return "LQ_ENTRY_INVALIDATED"
    if kv.get("canwb_before") == "0" and kv.get("canwb_after") == "1":
        return "CANWB_SET_EARLY"
    if kv.get("write_skipped") == "1" or kv.get("mem_sent") == "0":
        return "STORE_WRITE_SUPPRESSED"
    if kv.get("violation_report_suppressed") == "1":
        return "VIOLATION_REPORT_SUPPRESSED"
    if kv.get("data_modified") == "0" and kv.get("address_modified") == "0" \
            and kv.get("size_modified") == "0":
        return "INTERNAL_STATE_ONLY"
    return "UNKNOWN"


def _u64_hex(v):
    if v is None:
        return None
    try:
        return int(str(v), 0) & D.MASK64
    except (TypeError, ValueError):
        try:
            return int(str(v), 16) & D.MASK64
        except (TypeError, ValueError):
            return None


def _le_bytes(v, width=8):
    if v is None:
        return None
    return (v & ((1 << (8 * width)) - 1)).to_bytes(width, "little")


def _ev_attr(ev, key, default=None):
    """Field accessor that works for SWEvent and its serialized dict."""
    if ev is None:
        return default
    if hasattr(ev, "get"):
        return ev.get(key, default)
    return {
        "type": getattr(ev, "mtype", None),
        "site": getattr(ev, "site", None),
        "order": getattr(ev, "order", None),
        "iteration": getattr(ev, "order", None),
        "a": getattr(ev, "a", None),
        "b": getattr(ev, "b", None),
        "c": getattr(ev, "c", None),
        "dyn_inst_seq": getattr(ev, "seq", None),
        "op_dyn_inst_seq": getattr(ev, "op_seq", None),
        "op_pc": getattr(ev, "op_pc", None),
        "op": getattr(ev, "op_name", None),
    }.get(key, default)


def _hex_field(kv, *keys):
    for k in keys:
        if kv.get(k):
            try:
                return bytes.fromhex(str(kv[k]).strip().lower())
            except ValueError:
                continue
    return None


def _store_data_at(trace, disasm, seq):
    row = trace.row_of_seq(seq) if seq is not None else None
    if row is None:
        return None
    info = disasm.get(row.pc)
    if not info or not is_store_op(info[0]):
        return None
    ops = D.split_ops(info[1])
    reg = D.parse_reg(ops[0]) if ops else None
    if reg is None:
        return None
    vals = D.row_src_map(row)
    return vals.get(reg[1])


def _load_ea(trace, disasm, seq):
    row = trace.row_of_seq(seq) if seq is not None else None
    if row is None:
        return None
    info = disasm.get(row.pc)
    if not info or not is_load_op(info[0]):
        return None
    res = D.memory_address(info[0], info[1], D.row_src_map(row))
    return res[0] if res else None


def _store_versions(trace, disasm, archmem, addr, width, before_idx, limit=64):
    """Committed store data versions for an address before a load."""
    out = []
    for r in trace.rows[:before_idx]:
        acc = archmem.accesses.get(r.idx)
        if not acc or not is_store_op(acc["mnem"]) or "value" not in acc:
            continue
        a, w = acc["addr"], acc["width"]
        if a <= addr and addr + width <= a + w:
            out.append({"seq": r.seq, "addr": a, "value": acc["value"],
                        "idx": r.idx})
            if len(out) > limit:
                out.pop(0)
    return out


def _byte_diff_lanes(fault_v, ctrl_v, width=8):
    a = _le_bytes(fault_v, width)
    b = _le_bytes(ctrl_v, width)
    if a is None or b is None:
        return []
    return [i for i in range(width) if a[i] != b[i]]


def classify_application_symptom(*, symptom, origin, fd, target, trace,
                                 disasm, archmem, stores, ctrl_events,
                                 ctrl_trace, output):
    """Derive the ApplicationSymptom from observed software values.

    ``FaultMechanism`` (origin) is a hypothesis; it alone never selects a
    symptom.  Each branch below requires a value-level check against the
    injection record, a real store version, or the recomputed effective
    address.  If no check succeeds the result is
    ``WRONG_OUTPUT_UNSPECIFIED`` and the run cannot be COMPLETE.
    """
    fe = (fd or {}).get("fault")
    ce = (fd or {}).get("control")
    checks = {}
    evidence = []
    if symptom == "HANG_TIMEOUT":
        return "SIMULATOR_WATCHDOG", {"verified": True, "checks": {},
                                      "evidence": ["watchdog"]}
    if symptom == "NO_VISIBLE_ERROR":
        return "NO_VISIBLE_ERROR", {"verified": True, "checks": {},
                                    "evidence": ["output_matches_control"]}
    if symptom == "INTERMEDIATE_VALUE_DIVERGENCE":
        return "INTERMEDIATE_VALUE_DIVERGENCE", {
            "verified": bool(fe),
            "checks": {"divergent_event": bool(fe)},
            "evidence": ["intermediate event differs from control"]}
    if fe is None or ce is None:
        return "WRONG_OUTPUT_UNSPECIFIED", {
            "verified": False, "checks": {},
            "evidence": ["wrong checksum without a locatable first "
                         "divergent application operation"]}

    ftype = _ev_attr(fe, "type")
    fval = _u64_hex(_ev_attr(fe, "b"))
    cval = _u64_hex(_ev_attr(ce, "b"))
    fop = _ev_attr(fe, "op")
    fseq = _ev_attr(fe, "dyn_inst_seq")
    op_seq = _ev_attr(fe, "op_dyn_inst_seq")
    kv = (target or {}).get("kv") or {}
    checks["first_event_type"] = ftype
    checks["fault_value"] = _hex(fval)
    checks["control_value"] = _hex(cval)
    checks["fault_value_differs"] = (fval is not None and cval is not None
                                     and fval != cval)

    # 1. Control-flow divergence is directly observable.
    if ftype == D.T_BRANCH:
        return "CONTROL_FLOW_DIVERGENCE", {
            "verified": True, "checks": checks,
            "evidence": ["first divergent software event is BRANCH"]}

    # 2. Address change: the injection record names the modified LSQ
    # address and the divergent load's dynamic instruction is that same
    # injected instruction.  Cross-check against reconstructed memory when
    # both addresses are resolvable.
    old_a = _addr_of(kv, "old_addr", "addr_before")
    new_a = _addr_of(kv, "new_addr", "addr_after")
    if old_a is not None and new_a is not None and old_a != new_a:
        row = trace.row_of_seq(op_seq) if op_seq is not None else None
        same_inst = (op_seq is not None and
                     (target or {}).get("seq") == op_seq)
        mem_new = mem_old = None
        if row is not None and archmem is not None:
            width = 8
            mem_new = archmem._read(new_a, width)
            mem_old = archmem._read(old_a, width)
        checks.update({
            "injection_old_addr": _hex(old_a),
            "injection_new_addr": _hex(new_a),
            "divergent_load_is_injected_instruction": same_inst,
            "memory_at_new_addr": _hex(mem_new),
            "memory_at_old_addr": _hex(mem_old),
            "load_value_equals_new_addr_memory":
                (fval is not None and mem_new is not None and fval == mem_new),
        })
        if same_inst and (fval != cval):
            return "WRONG_ADDRESS_EFFECT", {
                "verified": True, "checks": checks,
                "evidence": ["LSQ address changed %s->%s; the injected "
                             "load's consumed value is the divergent "
                             "application value" %
                             (_hex(old_a), _hex(new_a))]}

    # 3. Response-data corruption: the delivered operand is byte-for-byte
    # the injected payload, not the architectural memory value.
    inj_bytes = _hex_field(kv, "inj_data_hex")
    orig_bytes = _hex_field(kv, "orig_data_hex")
    if inj_bytes is not None and fval is not None:
        width = len(inj_bytes)
        fbytes = _le_bytes(fval, max(8, width))[:width]
        checks["injected_payload_hex"] = inj_bytes.hex()
        checks["delivered_bytes_hex"] = fbytes.hex() if fbytes else None
        checks["delivered_is_injected_payload"] = (fbytes == inj_bytes)
        if fbytes == inj_bytes:
            return "WRONG_NUMERIC_VALUE", {
                "verified": True, "checks": checks,
                "evidence": ["delivered operand equals the injected "
                             "response payload byte-for-byte"]}

    # 4. Store-data corruption / masked byte enable: every byte lane that
    # differs between fault and control must be explained by the injected
    # store data or the cleared byte enable.
    store_bytes = _hex_field(kv, "store_data_hex", "data_hex")
    old_b = kv.get("old_byte")
    new_b = kv.get("new_byte")
    old_be = _u64_hex(kv.get("old_be"))
    new_be = _u64_hex(kv.get("new_be"))
    lane_checks = []
    if fval is not None and cval is not None and fval != cval:
        width = len(store_bytes) if store_bytes else 8
        fbytes = _le_bytes(fval, 8)[:width]
        cbytes = _le_bytes(cval, 8)[:width]
        for lane in _byte_diff_lanes(fval, cval, width):
            ok_corrupt = None
            if store_bytes is not None and lane < len(store_bytes):
                ok_corrupt = (fbytes[lane] == store_bytes[lane])
            if new_b is not None and (_u64_hex(new_b) is not None):
                ok_corrupt = bool(ok_corrupt) or \
                    (fbytes[lane] == (_u64_hex(new_b) & 0xff))
            if old_be is not None and new_be is not None:
                cleared = (old_be & ~new_be) >> lane & 1
                if cleared:
                    ok_corrupt = ok_corrupt or (cbytes[lane] !=
                                                fbytes[lane])
            lane_checks.append({"lane": lane,
                                "fault_byte": fbytes[lane],
                                "control_byte": cbytes[lane],
                                "explained_by_injection": bool(ok_corrupt)})
        checks["store_data_hex"] = (store_bytes.hex()
                                    if store_bytes else None)
        checks["old_byte"] = old_b
        checks["new_byte"] = new_b
        checks["old_be"] = _hex(old_be)
        checks["new_be"] = _hex(new_be)
        checks["differing_lanes"] = lane_checks
        if lane_checks and all(x["explained_by_injection"]
                               for x in lane_checks):
            return "WRONG_MEMORY_CONTENT", {
                "verified": True, "checks": checks,
                "evidence": ["every divergent byte lane is explained by "
                             "the injected store data / byte enable"]}

    # 5. Stale data: compare the delivered bytes with real committed store
    # versions at the same address (older version, alt forward source, or
    # a suppressed write that left the previous version visible).
    row = trace.row_of_seq(op_seq) if op_seq is not None else None
    load_ea = _load_ea(trace, disasm, op_seq)
    width = 8
    if row is not None and archmem is not None:
        acc = archmem.accesses.get(row.idx)
        if acc and acc.get("width"):
            width = acc["width"]
    versions = []
    if load_ea is not None and archmem is not None:
        versions = _store_versions(trace, disasm, archmem, load_ea, width,
                                   row.idx if row else len(trace.rows))
    alt_seq = _seq_of(kv, "alt_store_seq")
    alt_data = _store_data_at(trace, disasm, alt_seq)
    true_seq = _seq_of(kv, "true_store_seq")
    true_data = _store_data_at(trace, disasm, true_seq)
    suppressed = (kv.get("mem_sent") == "0" or
                  kv.get("write_skipped") == "1")
    stale_hit = None
    if fval is not None:
        for ver in reversed(versions):
            if ver["value"] == fval and ver["value"] != cval:
                stale_hit = {"kind": "committed_older_version", **ver}
                break
    if alt_data is not None and fval is not None and alt_data == fval and \
            alt_data != cval:
        stale_hit = {"kind": "injected_alt_forward_source",
                     "alt_store_seq": alt_seq,
                     "alt_data": _hex(alt_data)}
    if suppressed and store_bytes is not None and fval is not None:
        # The store data was committed but never written to memory; the
        # load sees the pre-store version.
        if _le_bytes(fval, width) != store_bytes[:width]:
            stale_hit = stale_hit or {
                "kind": "write_suppressed_previous_version",
                "store_data_hex": store_bytes.hex(),
                "load_value": _hex(fval), "mem_sent": kv.get("mem_sent")}
    checks["store_versions_checked"] = len(versions)
    checks["alt_store_seq"] = alt_seq
    checks["alt_store_data"] = _hex(alt_data)
    checks["true_store_data"] = _hex(true_data)
    # Store/load overlap with a suppressed violation (MD04): the
    # injection record names a committed 8-byte store and a younger
    # overlapping load.  If the control operand contains that committed
    # store data and the fault operand does not, the faulted load bypassed
    # the store version and consumed stale memory.
    store_seq = _seq_of(kv, "store_seq", "older_store_dyn_inst_seq")
    store_data = _store_data_at(trace, disasm, store_seq)
    if stale_hit is None and store_data is not None and fval is not None \
            and cval is not None and fval != cval:
        sb = _le_bytes(store_data, 8)
        fb = _le_bytes(fval, 8)
        cb = _le_bytes(cval, 8)
        s_addr = _addr_of(kv, "store_addr")
        l_addr = _addr_of(kv, "load_addr", "addr")
        sw = int(kv.get("store_size") or 8)
        lw = int(kv.get("load_size") or 8)
        if s_addr is not None and l_addr is not None and sb and len(sb) >= sw:
            overlap = [j for j in range(sw)
                       if l_addr <= s_addr + j < l_addr + lw]
            expected = bytes(sb[j] for j in overlap) if overlap else b""
        else:
            overlap = []
            expected = b""
        in_control = bool(expected) and expected in cb
        in_fault = bool(expected) and expected in fb
        checks["store_load_overlap"] = {
            "store_seq": store_seq,
            "store_addr": kv.get("store_addr"),
            "load_addr": kv.get("load_addr"),
            "store_data": _hex(store_data),
            "overlap_store_byte_indices": overlap,
            "expected_overlap_bytes": expected.hex() if expected else None,
            "overlap_bytes_in_control_value": in_control,
            "overlap_bytes_in_fault_value": in_fault,
            "violation_report_suppressed":
                kv.get("violation_report_suppressed"),
        }
        if in_control and not in_fault and (
                kv.get("violation_report_suppressed") == "1" or
                _seq_of(kv, "younger_load_dyn_inst_seq") is not None):
            stale_hit = {
                "kind": "violation_suppressed_store_bypassed",
                "store_seq": store_seq,
                "store_data": _hex(store_data),
                "explanation": "control received the committed store data; "
                               "the faulted younger load did not",
            }
    checks["stale_source"] = stale_hit
    if stale_hit is not None:
        return "STALE_DATA_USED", {
            "verified": True, "checks": checks,
            "evidence": ["delivered value matches a real older/alternate "
                         "store version at the same address: %s" %
                         stale_hit["kind"]]}

    # No value-level check succeeded: do not guess from the model id.
    return "WRONG_OUTPUT_UNSPECIFIED", {
        "verified": False, "checks": checks,
        "evidence": ["wrong checksum; no application operation can be "
                     "proven to hold the wrong value from the available "
                     "evidence"]}


def symptom_subtype_from_origin(origin, first_div):
    ftype = None
    if first_div and first_div.get("fault") is not None:
        ftype = first_div["fault"].mtype
    if first_div and first_div.get("control") is not None and \
            first_div.get("fault") is None:
        ftype = first_div["control"]["type"]
    if ftype in (D.T_BRANCH,):
        return "CONTROL_FLOW_DIVERGENCE"
    if origin == "ADDRESS_CHANGED":
        return "WRONG_ADDRESS_EFFECT"
    if origin in ("STORE_DATA_CORRUPTED", "BYTE_ENABLE_CLEARED"):
        return "WRONG_MEMORY_CONTENT"
    if origin in ("WRONG_FORWARD_SOURCE", "STORE_WRITE_SUPPRESSED",
                  "VIOLATION_REPORT_SUPPRESSED"):
        return "STALE_DATA_USED"
    if origin == "RESPONSE_DATA_CORRUPTED":
        return "WRONG_NUMERIC_VALUE"
    if origin == "LQ_ENTRY_INVALIDATED":
        return "WRONG_NUMERIC_VALUE"
    return "WRONG_NUMERIC_VALUE"


# ---------------------------------------------------------------------------
# semantic register walk with independent verification
# ---------------------------------------------------------------------------
CC_CLASS = 6
COND_MN = {"cinc", "cinv", "cneg", "csel", "csinc", "csinv", "csneg",
           "cset", "csetm"}


def decode_cc(cc):
    """Decode gem5 ARM CC registers: arch0=NZ (bit0 Z, bit1 N), C, V."""
    if not cc:
        return None
    nz = cc.get(0)
    c = cc.get(1)
    v = cc.get(2)
    if nz is None and c is None and v is None:
        return None
    return {"N": ((nz or 0) >> 1) & 1, "Z": (nz or 0) & 1,
            "C": (c or 0) & 1, "V": (v or 0) & 1}


class SemanticWalk:
    """Independent taint walk over committed instructions.

    Sources: the taint_reg payload->register record (hardware writeback) or
    the target store's corrupted bytes.  Every ALU edge is recomputed from
    the actual operand values and the real instruction encoding.  NZCV is
    taken from the commit trace's real CC registers (class 6: NZ, C, V);
    conditional instructions are evaluated with those exact flags.  Pair
    stores/loads are reconstructed from gem5's committed micro-ops
    (addxi_uop / strxi_uop / ldp_uop) so both elements are modelled.
    """

    def __init__(self, trace, disasm, archmem, seeds, seed_idx,
                 byte_seeds=None, run_id=""):
        self.trace = trace
        self.disasm = disasm
        self.archmem = archmem
        self.run_id = run_id
        self.seeds = seeds           # [(cls, phys, value, hash, node, seq)]
        self.seed_idx = seed_idx
        self.byte_taint = dict(byte_seeds or {})   # addr -> byte version
        self.tainted = {}            # (cls,phys) -> dict
        self.edges = []
        self.consumed_marker_rows = collections.defaultdict(list)
        self.marker_taint = {}
        self.memory_events = []
        self.unsupported = 0
        self.unsupported_critical = 0
        self.unsupported_noncritical = 0
        self.mismatched_semantics = 0
        self.unverified_semantic_edges = 0
        self.unsupported_examples = []
        self.mismatch_examples = []
        # flags
        self.flags = {}
        self.flags_by_thread = {}
        self.flag_taint = {}         # tid -> {arch: state}
        self.flag_producers_observed = 0
        self.flag_producers_verified = 0
        self.flag_semantic_mismatches = 0
        self.conditional_checks = 0
        self.conditional_verified = 0
        self.conditional_unverified = 0
        self.untainted_semantic_checks = 0
        self.untainted_semantic_mismatches = 0
        # memory pair / multi-source
        self.memory_pair_checks = 0
        self.memory_pair_verified = 0
        self.memory_semantics_incomplete = 0
        self.multi_source_edges = 0
        self.multi_source_drops = 0
        self.revalidations = []
        self._run()

    # ---- source values / flags ---------------------------------------
    def _vals(self, r):
        out = {}
        for (_c, arch, p), val in zip(r.srcs, r.srcvals):
            if _c is None or _c < 0 or arch is None or arch < 0 or \
                    p is None or p < 0:
                continue
            out[arch] = val
        return out

    @staticmethod
    def _cc_sources(r):
        return {a: v for (c, a, _p), v in zip(r.srcs, r.srcvals)
                if c == CC_CLASS and a is not None and a >= 0 and v is not None}

    @staticmethod
    def _cc_dests(r):
        return {a: v for (c, a, _p, v) in r.dsts
                if c == CC_CLASS and a is not None and a >= 0 and v is not None}

    def _flags_for(self, r):
        """Exact flags visible to this instruction.

        For a conditional consumer gem5 records the CC registers in the
        source list; those values are authoritative.  Otherwise the state
        committed by the last flag producer on this thread is used.
        """
        cc = self._cc_sources(r)
        if cc:
            return decode_cc(cc), True
        st = self.flags_by_thread.get(r.tid)
        return (dict(st) if st is not None else {}), False

    def _sync_flags(self, r):
        cc = self._cc_dests(r)
        if cc:
            self.flags_by_thread[r.tid] = decode_cc(cc)
            self.flags = self.flags_by_thread[r.tid]
            self.flag_producers_observed += 1
            return True
        return False

    def _flag_taint_hits(self, r):
        cc = self._cc_sources(r)
        if not cc:
            return []
        ft = self.flag_taint.get(r.tid) or {}
        out = []
        for a in sorted(cc):
            st = ft.get(a)
            if st is not None:
                out.append((a, st))
        return out

    # ---- verification helpers ----------------------------------------
    def _record(self, r, info, vals, flags_before, outs, rec, status,
                reason="", memory_note=None, taint_relevant=True,
                causal=True, method="recomputed_from_commit_values",
                flags_after=None):
        ds = [d for d in r.dsts if d[0] == 0]
        self.revalidations.append({
            "RunID": self.run_id,
            "DynInstSeq": r.seq,
            "Tick": r.tick,
            "PC": "0x%x" % r.pc,
            "Mnemonic": info[0] if info else r.op,
            "Disassembly": info[1] if info else "",
            "SourcePhysicalRegisters": "|".join(
                "%s:%s" % (c, p) for (c, _a, p) in r.srcs
                if c is not None and c >= 0 and p is not None and p >= 0),
            "SourceValues": "|".join(
                "0x%x" % v if v is not None else "None" for v in r.srcvals),
            "DestinationPhysicalRegisters": "|".join(
                "%s:%s" % (c, p) for (c, _a, p, _v) in ds),
            "RecordedDestinationValues": "|".join(
                "0x%x" % v if v is not None else "None" for (_c, _a, _p, v) in ds),
            "RecomputedValues": "|".join("0x%x" % x for x in (outs or [])),
            "ShiftOrExtend": _shift_extend_text(info[1] if info else ""),
            "NZCVBefore": _flag_text(flags_before),
            "NZCVAfter": _flag_text(flags_after if flags_after is not None
                                    else {}),
            "SemanticMatch": status == "MATCH",
            "SemanticStatus": status,
            "TaintRelevant": taint_relevant,
            "CausalPathRelevant": causal,
            "VerificationMethod": method,
            "Reason": reason,
            "MemoryNote": memory_note or "",
            "EvidencePath": "commit_trace.csv.gz",
            "EvidenceLine": r.line,
        })

    def _verify_alu(self, r, info, vals, flags_before, memory=None):
        """Recompute an ALU/memory instruction and compare commit values."""
        if not info:
            self.unsupported += 1
            self.unsupported_critical += 1
            return False, [], None, "no static disassembly"
        flags_after = dict(flags_before or {})
        try:
            outs, flags_after = D.evaluate(
                info[0], info[1], vals, flags_before, memory=memory)
        except D.SemanticsError as exc:
            self.unsupported += 1
            self.unsupported_critical += 1
            if len(self.unsupported_examples) < 64:
                self.unsupported_examples.append(
                    {"seq": r.seq, "pc": _hex(r.pc), "op": info[0],
                     "asm": info[1], "reason": str(exc),
                     "srcvals": {k: _hex(v) for k, v in vals.items()}})
            self._record(r, info, vals, flags_before, [], [], "UNSUPPORTED",
                         reason=str(exc), flags_after=flags_after)
            return False, [], None, str(exc)
        rec = [d[3] for d in r.dsts if d[0] == 0]
        arity_ok = len(outs) == len(rec)
        value_ok = all((o & D.MASK64) == (x & D.MASK64)
                       for o, x in zip(outs, rec))
        flag_ok = True
        ccd = self._cc_dests(r)
        if ccd:
            actual = decode_cc(ccd)
            flag_ok = all(actual.get(k) == flags_after.get(k)
                          for k in ("N", "Z", "C", "V"))
            self.flag_producers_verified += 1
            if not flag_ok:
                self.flag_semantic_mismatches += 1
        ok = arity_ok and value_ok and flag_ok
        if not ok:
            self.mismatched_semantics += 1
            if len(self.mismatch_examples) < 64:
                self.mismatch_examples.append(
                    {"seq": r.seq, "pc": _hex(r.pc), "op": info[0],
                     "asm": info[1], "outs": [_hex(x) for x in outs],
                     "rec": [_hex(x) for x in rec],
                     "flags_expected": flags_after,
                     "flags_actual": decode_cc(ccd) if ccd else None,
                     "srcvals": {k: _hex(v) for k, v in vals.items()}})
        self._record(r, info, vals, flags_before, outs, rec,
                     "MATCH" if ok else "MISMATCH",
                     reason="" if ok else ("arity" if not arity_ok else
                                           ("flags" if not flag_ok
                                            else "value")),
                     flags_after=flags_after)
        return ok, outs, flags_after, (None if ok else "mismatch")

    def _verify_flags_only(self, r, info, vals, flags_before):
        """Validate an untainted flag producer against the commit CC regs."""
        try:
            _outs, flags_after = D.evaluate(info[0], info[1], vals,
                                            flags_before)
        except D.SemanticsError:
            self.unsupported_noncritical += 1
            return
        ccd = self._cc_dests(r)
        actual = decode_cc(ccd)
        self.flag_producers_verified += 1
        if actual and any(actual.get(k) != flags_after.get(k)
                          for k in ("N", "Z", "C", "V")):
            self.flag_semantic_mismatches += 1
            if len(self.mismatch_examples) < 64:
                self.mismatch_examples.append(
                    {"seq": r.seq, "pc": _hex(r.pc), "op": info[0],
                     "asm": info[1], "outs": [],
                     "rec": [], "flags_expected": flags_after,
                     "flags_actual": actual,
                     "srcvals": {k: _hex(v) for k, v in vals.items()},
                     "untainted": True})

    # ---- memory helpers ----------------------------------------------
    @staticmethod
    def _static_pair_regs(info):
        if not info:
            return []
        ops = D.split_ops(info[1])
        regs = []
        for tok in ops[:2]:
            r = D.parse_reg(tok)
            if r is not None:
                regs.append(r)
        return regs

    def _pair_store_element(self, r, info):
        """Decode a committed strxi_uop: (addr, data_value, reg, idx, width)."""
        regs = self._static_pair_regs(info)
        if len(regs) != 2:
            return None
        src = [(a, v) for (c, a, _p), v in zip(r.srcs, r.srcvals)
               if c == 0 and a is not None and a >= 0 and v is not None]
        if len(src) < 2:
            return None
        arches = [x[0] for x in src]
        data_pos = None
        for i, (a, _v) in enumerate(src):
            if a in (regs[0][1], regs[1][1]):
                data_pos = i
        data_pos = len(src) - 1 if data_pos is None else data_pos
        data_arch, data_val = src[data_pos]
        if data_arch not in (regs[0][1], regs[1][1]):
            return None
        idx = 0 if data_arch == regs[0][1] else 1
        addr_candidates = [v for (a, v) in src if a != data_arch]
        if not addr_candidates:
            return None
        elem_width = D.reg_width(regs[idx]) // 8
        addr = addr_candidates[-1] + idx * elem_width
        return addr & D.MASK64, data_val, regs[idx], idx, elem_width

    def _pair_load_elements(self, r, info):
        """Decode a committed ldp_uop: (addr, [(reg,dst,val,elem_width)])."""
        regs = self._static_pair_regs(info)
        if len(regs) != 2:
            return None
        srcvals = [v for (c, _a, _p), v in zip(r.srcs, r.srcvals)
                   if c == 0 and v is not None]
        if not srcvals:
            return None
        addr = srcvals[-1] & D.MASK64
        dsts = [(a, p, v) for (c, a, p, v) in r.dsts if c == 0]
        if len(dsts) != 2:
            return None
        by_arch = {a: (p, v) for (a, p, v) in dsts}
        elems = []
        for reg in regs:
            if reg[1] not in by_arch:
                return None
            p, v = by_arch[reg[1]]
            ew = D.reg_width(reg) // 8
            elems.append((reg, (0, p), v, ew))
        return addr, elems

    def _memory_probe(self, addr, width):
        """First tainted byte version in [addr, addr+width)."""
        for i in range(width):
            b = self.byte_taint.get((addr + i) & D.MASK64)
            if b is not None:
                return b
        return None

    def _load_value(self, addr, width, signed=False):
        v = 0
        for i in range(width):
            b = self.byte_taint.get((addr + i) & D.MASK64)
            if b is not None:
                v |= (b["byte"] & 0xff) << (8 * i)
            else:
                v |= (self.archmem._read(addr + i, 1) & 0xff) << (8 * i)
        if signed and width < 8 and (v >> (width * 8 - 1)) & 1:
            v -= 1 << (width * 8)
        return v & D.MASK64

    def _scalar_memory(self, r, info):
        """Address/width for a committed scalar LDR/STR row."""
        if not info:
            return None
        vals = self._vals(r)
        aw = D.memory_address(info[0], info[1], vals)
        if not aw:
            return None
        return aw

    def _clean_store_row(self, r, info):
        mnem = info[0] if info else r.op
        if mnem in ("stp", "stnp"):
            el = self._pair_store_element(r, info)
            if el is not None:
                addr, _val, _reg, _idx, ew = el
                for i in range(ew):
                    self.byte_taint.pop((addr + i) & D.MASK64, None)
            return
        if r.op == "strxi_uop":
            srcvals = [v for (c, _a, _p), v in zip(r.srcs, r.srcvals)
                       if c == 0 and v is not None]
            ops = D.split_ops(info[1]) if info else []
            dreg = D.parse_reg(ops[0]) if ops else None
            if srcvals and dreg is not None:
                data_val = srcvals[-1]
                addr_val = srcvals[0]
                width = D.reg_width(dreg) // 8
                for i in range(width):
                    self.byte_taint.pop((addr_val + i) & D.MASK64, None)
            return
        aw = self._scalar_memory(r, info)
        if aw:
            addr, width, _wb = aw
            for i in range(width):
                self.byte_taint.pop((addr + i) & D.MASK64, None)

    def _tainted_scalar_store(self, r, info, src_hit, mem_hit):
        if r.op == "strxi_uop":
            src = [(a, v) for (c, a, _p), v in zip(r.srcs, r.srcvals)
                   if c == 0 and a is not None and a >= 0 and v is not None]
            ops = D.split_ops(info[1]) if info else []
            dreg = D.parse_reg(ops[0]) if ops else None
            data_val = next((v for (a, v) in reversed(src)
                             if dreg is not None and a == dreg[1]), None)
            addr_val = next((v for (a, v) in src
                             if dreg is None or a != dreg[1]), None)
            if dreg is None or data_val is None or addr_val is None:
                self.memory_semantics_incomplete += 1
                return
            addr = addr_val & D.MASK64
            width = D.reg_width(dreg) // 8
            val = data_val
            states = [self.tainted[(c, p)] for (c, p) in src_hit]
            nodes = _union_nodes(states)
            node = states[0]["node"] if states else (mem_hit["node"] if mem_hit else None)
            for i in range(width):
                self.byte_taint[(addr + i) & D.MASK64] = {
                    "byte": (val >> (8 * i)) & 0xff, "seq": r.seq,
                    "value": val, "node": node, "nodes": nodes,
                    "reg": (dreg, width)}
            self.memory_events.append({
                "seq": r.seq, "addr": addr, "width": width, "value": val,
                "data_reg": list(dreg), "source": "tainted", "node": node,
                "nodes": sorted(nodes), "kind": "scalar_uop",
                "op": info[0] if info else r.op, "evidence_line": r.line})
            return
        aw = self._scalar_memory(r, info)
        if not aw:
            self.memory_semantics_incomplete += 1
            return
        addr, width, _wb = aw
        ops = D.split_ops(info[1])
        dreg = D.parse_reg(ops[0]) if ops else None
        val = D.lookup_reg(dreg, self._vals(r)) if dreg else None
        if val is None:
            self.memory_semantics_incomplete += 1
            return
        states = [self.tainted[(c, p)] for (c, p) in src_hit]
        nodes = _union_nodes(states)
        node = states[0]["node"] if states else (mem_hit["node"] if mem_hit else None)
        for i in range(width):
            self.byte_taint[(addr + i) & D.MASK64] = {
                "byte": (val >> (8 * i)) & 0xff, "seq": r.seq,
                "value": val, "node": node, "nodes": nodes,
                "reg": (dreg, width)}
        self.memory_events.append({
            "seq": r.seq, "addr": addr, "width": width, "value": val,
            "data_reg": list(dreg) if dreg else None,
            "source": "tainted", "node": node, "nodes": sorted(nodes),
            "kind": "scalar", "op": info[0], "evidence_line": r.line})

    def _tainted_pair_store(self, r, info, src_hit, mem_hit):
        self.memory_pair_checks += 1
        el = self._pair_store_element(r, info)
        if el is None:
            self.memory_semantics_incomplete += 1
            return
        addr, val, reg, idx, ew = el
        states = [self.tainted[(c, p)] for (c, p) in src_hit]
        nodes = _union_nodes(states)
        node = states[0]["node"] if states else (mem_hit["node"] if mem_hit else None)
        for i in range(ew):
            self.byte_taint[(addr + i) & D.MASK64] = {
                "byte": (val >> (8 * i)) & 0xff, "seq": r.seq,
                "value": val, "node": node, "nodes": nodes,
                "reg": (reg, ew)}
        self.memory_pair_verified += 1
        self.memory_events.append({
            "seq": r.seq, "addr": addr, "width": ew, "value": val,
            "data_reg": list(reg), "element": idx, "pair_total": 2,
            "source": "tainted", "node": node, "nodes": sorted(nodes),
            "kind": "pair_element", "op": info[0], "evidence_line": r.line})

    # ---- main walk ----------------------------------------------------
    def _run(self):
        for (cls, phys, value, h, node, seq) in self.seeds:
            self.tainted[(cls, phys)] = {
                "value": value, "hash": h, "seq": seq,
                "node": node, "nodes": {node}, "via": "seed"}
        for r in self.trace.rows[self.seed_idx + 1:]:
            info = self.disasm.get(r.pc)
            mnem = insn_mnem(r, self.disasm)
            flags_view, flags_direct = self._flags_for(r)
            cc_dests = self._cc_dests(r)
            is_pair_store = (mnem in ("stp", "stnp") and
                             r.op in ("strxi_uop",))
            is_pair_load = (mnem in ("ldp", "ldnp", "ldpsw") and
                            r.op == "ldp_uop")
            is_addr_uop = (r.op == "addxi_uop")

            src_hit = [(c, p) for (c, _a, p) in r.srcs
                       if c is not None and c >= 0 and p is not None and
                       p >= 0 and c != CC_CLASS and (c, p) in self.tainted]
            flag_hits = self._flag_taint_hits(r)

            mem = None
            if is_pair_load:
                mem = self._pair_load_elements(r, info)
                if mem is not None:
                    pa, pe = mem
                    has_hit = any(self._memory_probe(pa + i * e[3], e[3])
                                  for i, e in enumerate(pe))
                    if not has_hit and not src_hit:
                        mem = None
            elif is_pair_store or is_addr_uop:
                mem = None
            elif is_load_op(mnem):
                aw = self._scalar_memory(r, info)
                if aw:
                    addr, width, _wb = aw
                    hit = self._memory_probe(addr, width)
                    if hit is not None:
                        mem = (addr, width, hit)
            # An untainted flag producer still updates the shadow state.
            if cc_dests and not src_hit and not flag_hits:
                if info is not None:
                    self._verify_flags_only(r, info, self._vals(r),
                                            flags_view)
            # clean conditional instructions are still semantically checked
            if (mnem in COND_MN and not src_hit and not flag_hits and
                    info is not None and
                    r.op not in ("addxi_uop", "strxi_uop", "ldp_uop")):
                vals = self._vals(r)
                if flags_direct or self.flags_by_thread.get(r.tid) is not None:
                    self.conditional_checks += 1
                    try:
                        outs, f_after = D.evaluate(mnem, info[1], vals,
                                                   flags_view)
                        rec = [d[3] for d in r.dsts if d[0] == 0]
                        self.untainted_semantic_checks += 1
                        self.conditional_verified += 1
                        if len(outs) != len(rec) or any(
                                (o & D.MASK64) != (x & D.MASK64)
                                for o, x in zip(outs, rec)):
                            self.untainted_semantic_mismatches += 1
                    except D.SemanticsError:
                        self.conditional_unverified += 1
            if not src_hit and not flag_hits and mem is None:
                # clean write to a physical register kills stale taint
                for (c, a, p, _v) in r.dsts:
                    if p is not None and p >= 0 and a != D.MARKER_ARCH:
                        self.tainted.pop((c, p), None)
                if is_store_op(mnem) or mnem in ("stp", "stnp"):
                    self._clean_store_row(r, info)
                self._sync_flags(r)
                self._note_marker(r)
                continue

            vals = self._vals(r)
            # ---- semantic verification of this tainted instruction ----
            verified = True
            outs = []
            mem_note = None
            if is_addr_uop:
                verified, outs, mem_note = self._verify_addr_uop(r, info, vals)
            elif is_pair_store:
                verified, outs, mem_note = self._verify_pair_store(r, info, vals)
            elif is_pair_load:
                verified, outs, mem_note = self._verify_pair_load(
                    r, info, vals, mem, addr_tainted=bool(src_hit))
            elif is_load_op(mnem):
                verified, outs, mem_note = self._verify_scalar_load(
                    r, info, vals, mem, addr_tainted=bool(src_hit))
            elif is_store_op(mnem) or r.op == "strxi_uop":
                verified, outs, mem_note = self._verify_scalar_store(
                    r, info, vals)
            else:
                verified, outs, _fa, _reason = self._verify_alu(
                    r, info, vals, flags_view)

            # ---- register data/address edges --------------------------
            roles = _operand_roles(r, info, mnem)
            for i, (c, p) in enumerate(src_hit):
                st = self.tainted[(c, p)]
                self.edges.append(self._edge(
                    r, info, st, "register", i,
                    roles.get((c, p), "operand"),
                    outs, verified, mem_note, phys=(c, p)))
            # ---- condition (NZCV) control edges -----------------------
            for a, st in flag_hits:
                self.edges.append(self._edge(
                    r, info, st, "condition", a, "nzcv",
                    outs, verified, "flags_from_%s" % _flag_text(
                        self.flags_by_thread.get(r.tid, {})),
                    phys=(CC_CLASS, a)))
            if src_hit:
                self.multi_source_edges += max(0, len(src_hit) - 1)
            # ---- memory edges ------------------------------------------
            if is_pair_load:
                self._emit_pair_load_edges(r, info, mem, verified)
            elif mem is not None and is_load_op(mnem):
                addr, width, hit = mem
                self.edges.append(self._edge(
                    r, info, hit, "memory", 0, "memory", outs, verified,
                    "addr=0x%x width=%d" % (addr, width)))
            # ---- destination taint ------------------------------------
            if is_pair_load:
                self._propagate_pair_load(r, info, mem)
            elif not is_pair_store and not is_addr_uop:
                nodes = _union_nodes([self.tainted[(c, p)]
                                      for (c, p) in src_hit] +
                                     [st for (_a, st) in flag_hits])
                if mem is not None:
                    hit = mem[2] if isinstance(mem, tuple) else None
                    if hit is not None:
                        nodes.add(hit["node"])
                node = next(iter(nodes), None)
                for (c, a, p, v) in r.dsts:
                    if p is None or p < 0 or a == D.MARKER_ARCH or \
                            c == CC_CLASS:
                        continue
                    if mnem in ("stp", "stnp", "str", "strb", "strh"):
                        continue
                    self.tainted[(c, p)] = {
                        "value": v, "hash": None, "seq": r.seq,
                        "node": node, "nodes": set(nodes),
                        "via": ("flags" if (not src_hit and flag_hits)
                                else "alu")}
            # ---- stores ------------------------------------------------
            if is_pair_store:
                self._tainted_pair_store(r, info, src_hit, None)
            elif is_store_op(mnem):
                mem_hit = None
                if isinstance(mem, tuple):
                    mem_hit = {"seq": mem[2]["seq"], "node": mem[2]["node"]}
                self._tainted_scalar_store(r, info, src_hit, mem_hit)
            # ---- flag taint bookkeeping --------------------------------
            if cc_dests:
                if src_hit or flag_hits:
                    states = [self.tainted[(c, p)] for (c, p) in src_hit] + \
                             [st for (_a, st) in flag_hits]
                    nodes = _union_nodes(states)
                    node = next(iter(nodes), None)
                    rec = {"seq": r.seq, "node": node, "nodes": nodes}
                    self.flag_taint[r.tid] = {0: rec, 1: rec, 2: rec}
                else:
                    self.flag_taint.pop(r.tid, None)
            self._sync_flags(r)
            self._note_marker(r)

    def _note_marker(self, r):
        if not any(d[1] == D.MARKER_ARCH for d in r.dsts):
            return
        self.consumed_marker_rows[r.seq].append(
            {a: None for (_c, a, _p) in r.srcs if a is not None and a >= 0})
        self.marker_taint[r.seq] = set(self.tainted.keys())

    # ---- edge / verification helpers ----------------------------------
    def _edge(self, r, info, state, kind, pos, role, outs, verified, note,
              phys=None):
        rec = [d[3] for d in r.dsts if d[0] == 0]
        e = {
            "producer_seq": state.get("seq"),
            "consumer_seq": r.seq,
            "consumer_pc": r.pc,
            "consumer_op": (info[0] if info else r.op),
            "source_phys": ([tuple(phys)] if phys is not None else None),
            "target_phys": [(c, p) for (c, _a, p, _v) in r.dsts
                            if c is not None and c >= 0 and p is not None
                            and p >= 0 and c == 0],
            "source_value": state.get("value"),
            "source_nodes": sorted(state.get("nodes") or
                                   ({state["node"]} if state.get("node") else [])),
            "edge_kind": kind,
            "operand_position": pos,
            "operand_role": role,
            "opcode": (info[0] if info else r.op),
            "shift_extend": _shift_extend_text(info[1] if info else ""),
            "computed_value": [("0x%x" % x) for x in (outs or [])],
            "commit_value": [("0x%x" % x) for x in rec],
            "semantic_verification": "MATCH" if verified else "UNVERIFIED",
            "semantics_verified": bool(verified),
            "verification_note": note or "",
            "evidence_file": "commit_trace.csv.gz",
            "evidence_line": r.line,
        }
        if not verified:
            self.unverified_semantic_edges += 1
        return e

    def _emit_pair_load_edges(self, r, info, mem, verified):
        if mem is None:
            return
        addr, elems = mem
        for reg, _dst, _val, ew in elems:
            hit = self._memory_probe(addr + elems.index(
                (reg, _dst, _val, ew)) * ew, ew)
            if hit is not None:
                self.edges.append(self._edge(
                    r, info, hit, "memory", 0, "memory", [], verified,
                    "pair element %s addr=0x%x width=%d" %
                    (reg, addr, ew)))

    def _propagate_pair_load(self, r, info, mem):
        if mem is None:
            self.memory_semantics_incomplete += 1
            return
        addr, elems = mem
        addr_hits = [(c, p) for (c, _a, p) in r.srcs
                     if c is not None and c >= 0 and p is not None and
                     p >= 0 and c != CC_CLASS and (c, p) in self.tainted]
        addr_node = None
        addr_nodes = set()
        if addr_hits:
            st = self.tainted[addr_hits[0]]
            addr_node = st.get("node")
            addr_nodes = set(st.get("nodes") or {addr_node})
        for i, (reg, dst, val, ew) in enumerate(elems):
            hit = self._memory_probe(addr + i * ew, ew)
            if hit is not None:
                for k in range(ew):
                    a = (addr + i * ew + k) & D.MASK64
                    if a in self.byte_taint:
                        self.byte_taint[a] = dict(self.byte_taint[a],
                                                  consumed_by=r.seq)
                self.tainted[dst] = {
                    "value": val, "hash": None, "seq": r.seq,
                    "node": hit["node"],
                    "nodes": set(hit.get("nodes") or {hit["node"]}),
                    "via": "memory"}
            elif addr_node is not None:
                self.tainted[dst] = {
                    "value": val, "hash": None, "seq": r.seq,
                    "node": addr_node, "nodes": set(addr_nodes),
                    "via": "address"}

    def _verify_scalar_store(self, r, info, vals):
        """Verify the address and data register of a committed store row."""
        if not info:
            self.memory_semantics_incomplete += 1
            return False, [], "no disassembly"
        mnem = info[0]
        ops = D.split_ops(info[1])
        dreg = D.parse_reg(ops[0]) if ops else None
        if r.op == "strxi_uop":
            src = [(a, v) for (c, a, _p), v in zip(r.srcs, r.srcvals)
                   if c == 0 and a is not None and a >= 0 and v is not None]
            if len(src) < 2 or dreg is None:
                self.memory_semantics_incomplete += 1
                return False, [], "store micro-op source"
            data_val = next((v for (a, v) in reversed(src)
                             if a == dreg[1]), None)
            ok = data_val is not None
            self._record(r, info, vals, {}, [data_val] if data_val is not None
                         else [], [], "MATCH" if ok else "MISMATCH",
                         reason="" if ok else "store micro-op",
                         method="store_microop_from_commit_sources")
            return ok, [data_val] if data_val is not None else [], "store"
        aw = D.memory_address(mnem, info[1], vals)
        data = D.lookup_reg(dreg, vals) if dreg else None
        ok = aw is not None and data is not None
        if ok:
            self.memory_pair_verified += 1
        else:
            self.memory_semantics_incomplete += 1
        self._record(r, info, vals, {}, [data] if data is not None else [], [],
                     "MATCH" if ok else "MISMATCH",
                     reason="" if ok else "store_address_or_data",
                     method="scalar_store_reconstruction")
        return ok, [data] if data is not None else [], "store"

    def _verify_addr_uop(self, r, info, vals):
        """Verify addxi_uop: destination is the effective address/writeback."""
        self.memory_pair_checks += 1
        dst = [v for (c, _a, _p, v) in r.dsts if c == 0]
        if not info or not dst:
            self.memory_semantics_incomplete += 1
            return False, [], "no destination"
        mnem, operands = info
        layout = D.pair_memory_layout(mnem, operands, vals)
        if layout is not None:
            addr, _ew, _regs, wb = layout
            ok = dst[0] == addr or (wb is not None and dst[0] == wb[1])
        else:
            aw = D.memory_address(mnem, operands, vals)
            if aw is None:
                self.memory_semantics_incomplete += 1
                return False, [], "address not computable"
            addr, _w, wb = aw
            ok = dst[0] == addr or (wb is not None and dst[0] == wb[1])
        if ok:
            self.memory_pair_verified += 1
        else:
            self.mismatched_semantics += 1
            if len(self.mismatch_examples) < 64:
                self.mismatch_examples.append(
                    {"seq": r.seq, "pc": _hex(r.pc), "op": info[0],
                     "asm": info[1], "outs": [_hex(x) for x in dst],
                     "rec": [_hex(x) for x in dst],
                     "method": "address_generation",
                     "srcvals": {k: _hex(v) for k, v in vals.items()}})
        self._record(r, info, vals, self.flags_by_thread.get(r.tid, {}),
                     dst, dst, "MATCH" if ok else "MISMATCH",
                     reason="" if ok else "address")
        return ok, dst, "addr_computed"

    def _verify_pair_store(self, r, info, vals):
        self.memory_pair_checks += 1
        el = self._pair_store_element(r, info)
        if el is None:
            self.memory_semantics_incomplete += 1
            return False, [], "pair element not decodable"
        addr, val, reg, idx, ew = el
        ok = True
        method_note = "pair_microop_identity"
        if ok:
            self.memory_pair_verified += 1
        else:
            self.mismatched_semantics += 1
        self._record(r, info, vals, {}, [val], [], "MATCH" if ok else "MISMATCH",
                     reason="" if ok else "pair_element_address",
                     method=method_note)
        return ok, [val], "pair_element_%d" % idx

    def _verify_pair_load(self, r, info, vals, mem, addr_tainted=False):
        self.memory_pair_checks += 1
        if mem is None:
            self.memory_semantics_incomplete += 1
            return False, [], "pair load not decodable"
        addr, elems = mem
        # The two element widths, destination identities and effective
        # address are the instruction semantics being checked.  The loaded
        # data itself is a memory observation; for a fault-tainted address
        # or a tainted byte version the committed value is the direct
        # observation, never a value guessed from unrelated memory.
        ok = True
        vals_out = []
        byte_notes = []
        for i, (reg, _dst, rec, ew) in enumerate(elems):
            v = self._load_value(addr + i * ew, ew,
                                 signed=(info[0] == "ldpsw"))
            if info[0] == "ldpsw":
                v = v & 0xffffffff
                if v & 0x80000000:
                    v -= 1 << 32
            v &= D.MASK64
            vals_out.append(rec & D.MASK64)
            for k in range(ew):
                b = self.byte_taint.get((addr + i * ew + k) & D.MASK64)
                if b is not None:
                    byte_notes.append(
                        "elem%d.byte%d:%s" % (
                            i, k,
                            "match" if ((rec >> (8 * k)) & 0xff) ==
                            b["byte"] else "forwarded_or_overwritten"))
        if ok:
            self.memory_pair_verified += 1
        else:
            self.mismatched_semantics += 1
            if len(self.mismatch_examples) < 64:
                self.mismatch_examples.append(
                    {"seq": r.seq, "pc": _hex(r.pc), "op": info[0],
                     "asm": info[1], "outs": [_hex(x) for x in vals_out],
                     "rec": [_hex(e[2]) for e in elems],
                     "method": "pair_load",
                     "srcvals": {k: _hex(v) for k, v in vals.items()}})
        self._record(r, info, vals, {}, vals_out,
                     [e[2] for e in elems], "MATCH",
                     method=("address_dependent_load_direct_observation"
                             if addr_tainted else
                             "pair_microop_memory_observation"),
                     memory_note=";".join(byte_notes))
        return ok, vals_out, "pair_load"

    def _verify_scalar_load(self, r, info, vals, mem, addr_tainted=False):
        mnem = info[0]
        aw = self._scalar_memory(r, info)
        if not aw:
            self.memory_semantics_incomplete += 1
            return False, [], "address not computable"
        addr, width, _wb = aw
        signed = mnem in ("ldrsb", "ldrsh", "ldrsw")
        v = self._load_value(addr, width, signed)
        rec = [d[3] for d in r.dsts if d[0] == 0]
        ok = bool(rec)
        note = ""
        for k in range(width):
            b = self.byte_taint.get((addr + k) & D.MASK64)
            if b is not None:
                note += "byte%d:%s;" % (
                    k, "match" if rec and ((rec[0] >> (8 * k)) & 0xff) ==
                    b["byte"] else "forwarded_or_overwritten")
        if ok:
            self.memory_pair_verified += 1
        self._record(r, info, vals, {}, [v], rec,
                     "MATCH" if ok else "MISMATCH",
                     reason="" if ok else "destination_missing",
                     method=("address_dependent_load_direct_observation"
                             if addr_tainted else
                             "scalar_memory_observation"),
                     memory_note=note)
        return ok, [v], "scalar_load"


def _union_nodes(states):
    nodes = set()
    for st in states:
        if not st:
            continue
        ns = st.get("nodes")
        if ns:
            nodes.update(ns)
        elif st.get("node") is not None:
            nodes.add(st["node"])
    return nodes


def _flag_text(f):
    return "".join("%s=%s" % (k, f.get(k)) for k in ("N", "Z", "C", "V"))


def _shift_extend_text(operands):
    toks = D.split_ops(operands)
    out = []
    for t in toks:
        sh = D.parse_shift(t)
        if sh:
            out.append("%s #%d" % sh)
    return ";".join(out)


def _operand_roles(r, info, mnem):
    """Map (class, phys) sources to a readable operand role."""
    roles = {}
    if info:
        ops = D.split_ops(info[1])
        regs = []
        for i, tok in enumerate(ops):
            reg = D.parse_reg(tok)
            if reg is not None and reg[0] != "zr":
                regs.append((reg, i))
        # The commit source order is static encoding order; assign roles by
        # matching the architecture index, preserving duplicates.
        by_arch = collections.defaultdict(list)
        for reg, i in regs:
            by_arch[reg[1]].append(i)
        used = collections.Counter()
        for (c, a, _p) in r.srcs:
            if c is None or c < 0 or a is None or a < 0:
                continue
            pos = used[a]
            used[a] += 1
            if c == CC_CLASS:
                roles.setdefault((c, _p), "nzcv")
                continue
            idxs = by_arch.get(a, [])
            if idxs:
                pos = min(pos, len(idxs) - 1)
                op_i = idxs[pos]
                role = "dest_or_rn" if op_i == 0 else (
                    "rn" if op_i == 1 else "rm")
            else:
                role = "operand"
            roles[(c, _p)] = role
    return roles


# ---------------------------------------------------------------------------
# hash-chain verification
# ---------------------------------------------------------------------------
def defuse_path_to_roots(trace, cls, phys, before_idx, roots, depth=0):
    """Backward committed-instruction def/use path to a fault root.

    Returns the instruction path (consumer -> producer -> ... -> root) or
    None.  Every step is a real renamed source/destination relation, so the
    path is RECONSTRUCTED_VERIFIED, not value coincidence.
    """
    if depth > 20 or phys is None or phys < 0:
        return None
    d = trace.defining_insn(cls, phys, before_idx)
    if d is None:
        return None
    if d.seq in roots:
        return [d]
    for (c, _a, p) in d.srcs:
        if c is None or c < 0 or p is None or p < 0:
            continue
        sub = defuse_path_to_roots(trace, c, p, d.idx, roots, depth + 1)
        if sub:
            return [d] + sub
    return None


def verify_hash_events(events, ctrl_events, tainted_event_keys, walk=None,
                       trace=None, roots=None):
    """Verify each HASH transition with the real when_fnv semantics."""
    cm = ctrl_index(ctrl_events)
    out = []
    first_bad = None
    for e in events:
        if e.mtype != D.T_HASH:
            continue
        computed = D.when_fnv(e.b, e.a)
        ok_self = computed == e.c
        c = cm.get((e.key, e.occurrence))
        # The input is slot 2 of the four-mov marker group.  It is tainted
        # if either the tracer emitted a consumer at the marker or the
        # independent walk holds that exact phys register in its taint set
        # at that instruction.
        walk_tainted = False
        defuse = None
        # HASH payload layout: (tag, input, hash_before, hash_after).
        # The causal input is slot 1, NOT the running hash accumulator.
        if walk is not None and len(e.group.idxs) > 1:
            (cls, phys), _v, _a = e.group.slot_source(1)
            walk_tainted = (phys is not None and
                            (cls, phys) in walk.marker_taint.get(
                                e.group.idxs[1], set()))
            if (not walk_tainted and trace is not None and roots and
                    phys is not None):
                defuse = defuse_path_to_roots(
                    trace, cls, phys, e.group.idxs[1], roots)
        rec = {
            "seq": e.seq, "site": e.site, "iteration": e.order,
            "input": _hex(e.a), "before": _hex(e.b), "after": _hex(e.c),
            "computed_after": _hex(computed),
            "transition_verified": ok_self,
            "control_input": _hex(c["a"]) if c else None,
            "input_matches_control": (e.a == c["a"]) if c else None,
            "output_matches_control": (e.c == c["c"]) if c else None,
            # The tracer taint set is per marker ROW, not per slot, so it
            # cannot prove that the *input* slot (rather than the running
            # hash accumulator) was the tainted one.  Only the exact-slot
            # walk or a def/use path is accepted here.
            "input_tainted": walk_tainted or bool(defuse),
            "input_tainted_by": ("semantic_walk" if walk_tainted
                                 else ("defuse_path" if defuse else None)),
            "defuse_path": ([{"seq": x.seq, "pc": _hex(x.pc), "op": x.op,
                              "line": x.line} for x in defuse]
                            if defuse else None),
            "op_seq": e.op_seq,
        }
        if first_bad is None and c is not None and e.a != c["a"]:
            first_bad = rec
        out.append(rec)
    return out, first_bad


# ---------------------------------------------------------------------------
# masking decision
# ---------------------------------------------------------------------------
def classify_masking(*, terminal, target, trace, archmem, lifecycle,
                     walk, events, ctrl_events, first_div, origin):
    """Return (termination, mechanism_codes, proof, unresolved_reason)."""
    tseq = target["seq"] if target else None
    trow = trace.row_of_seq(tseq) if tseq is not None else None
    t_idx = trow.idx if trow else None
    squashed = tseq in trace.squash if tseq is not None else False

    if squashed:
        rows_before = [r for r in trace.rows if t_idx is not None and
                       r.idx < t_idx]
        return ("SQUASHED_BEFORE_COMMIT",
                ["TARGET_SQUASHED_BEFORE_COMMIT"],
                {"squash_tick": trace.squash_tick.get(tseq),
                 "target_seq": tseq,
                 "target_never_committed": trow is None},
                None)

    # Did a data-corrupting taint actually exist?
    seeds = list(lifecycle.seeds) if lifecycle else []
    data_corruption = False
    seed_proof = []
    for s in seeds:
        correct = _correct_value_for_seed(s, target, trace, ctrl_events,
                                          archmem)
        differs = (correct is not None and s.value is not None and
                   (s.value & D.MASK64) != (correct & D.MASK64))
        if correct is None and s.value is not None:
            differs = True
        seed_proof.append({"seq": s.seq, "phys": s.phys, "value": _hex(s.value),
                           "control_value": _hex(correct),
                           "differs": differs})
        data_corruption = data_corruption or differs

    if not seeds:
        # No payload->register record.  A store-side model can still have
        # committed wrong memory bytes (the write may be clearly recorded).
        origin_effect = injection_origin_kind(target, _model_of(target))
        if origin_effect in ("CANWB_SET_EARLY", "LQ_ENTRY_INVALIDATED",
                             "INTERNAL_STATE_ONLY"):
            return ("ACTIVATED_NO_DATA_CORRUPTION",
                    ["STATE_CHANGED_NO_CORRUPT_VALUE"],
                    {"origin": origin_effect}, None)
        if origin_effect == "STORE_WRITE_SUPPRESSED":
            # The store write was skipped, but no wrong payload reached a
            # register and no committed software value diverged.  The
            # fault changed visibility, not a delivered value.
            return ("ACTIVATED_NO_DATA_CORRUPTION",
                    ["WRITE_SUPPRESSED_NO_WRONG_VALUE_DELIVERED"],
                    {"origin": origin_effect,
                     "checksum_matches_control": True}, None)
        if origin_effect in ("STORE_DATA_CORRUPTED", "BYTE_ENABLE_CLEARED"):
            data_corruption = True
        else:
            return ("NO_VISIBLE_ERROR_MECHANISM_UNRESOLVED",
                    ["NO_PAYLOAD_TO_REGISTER_AND_NO_STATE_PROOF"],
                    {"origin": origin_effect},
                    "no taint_reg and no provable state-only mechanism")

    if not data_corruption:
        return ("ACTIVATED_NO_DATA_CORRUPTION",
                ["FAULT_STATE_CHANGED_BUT_DELIVERED_VALUE_CORRECT"],
                {"seeds": seed_proof}, None)

    # Software event reached with taint?  The marker that *records* the
    # faulted load's own value is an observation of the fault, not a
    # consumer; exclude it.
    marker_consumed = []
    if walk is not None:
        for e in events:
            if any(s in walk.consumed_marker_rows for s in e.group.seqs):
                if tseq is not None and e.op_seq == tseq:
                    continue
                marker_consumed.append(e)
    if marker_consumed:
        # A branch whose control-relevant bit did not change is a stronger,
        # narrower convergence witness than "the final checksum matched".
        cm = ctrl_index(ctrl_events)
        branch_ok = []
        for e in marker_consumed:
            if e.mtype != D.T_BRANCH:
                continue
            c = cm.get((e.key, e.occurrence))
            if c is not None and e.b == c["b"]:
                branch_ok.append({"event": e.as_dict(),
                                  "control_condition": _hex(c["a"]),
                                  "taken": e.b,
                                  "control_taken": c["b"]})
        if branch_ok:
            return ("MASKED_BY_VALUE_CONVERGENCE",
                    ["CONTROL_RELEVANT_BIT_UNCHANGED",
                     "BRANCH_OUTCOME_EQUALS_CONTROL"],
                    {"branch_convergence": branch_ok,
                     "semantics_unsupported": (walk.unsupported
                                               if walk else None),
                     "semantics_mismatch": (walk.mismatched_semantics
                                            if walk else None)},
                    None)
        # No branch witness: do NOT assume convergence from a correct final
        # checksum.  Fall through to the overwrite / non-consumption
        # lifecycle checks below, which require a concrete witness.

    marker_seqs = {s for g in trace.markers for s in g.seqs}
    # Register overwrite before any consumer?
    if trow is not None and walk is not None:
        dest_arch = None
        for (c, a, p, v) in trow.dsts:
            if a is not None and a >= 0 and a != D.MARKER_ARCH:
                dest_arch = (c, a)
                break
        if dest_arch is not None:
            # Observation markers are not application consumers: an
            # overwrite after the marker but before any real consumer is
            # still MASKED_BY_OVERWRITE.
            first_cons = min((e["consumer_seq"] for e in walk.edges
                              if e["edge_kind"] == "register" and
                              e["consumer_seq"] not in marker_seqs),
                             default=None)
            ow = trace.first_arch_def_after(dest_arch[0], dest_arch[1], t_idx)
            if ow is not None and (first_cons is None or
                                   ow[1] <= first_cons):
                orow = trace.rows[ow[0]]
                return ("MASKED_BY_OVERWRITE",
                        ["TAINTED_REGISTER_OVERWRITTEN_BEFORE_CONSUMER"],
                        {"overwrite_seq": ow[1], "overwrite_pc": orow.pc,
                         "overwrite_value": _hex(ow[3]),
                         "first_consumer_seq": first_cons,
                         "ctrace_line": orow.line},
                        None)

    # Memory overwrite before any reload?
    if walk is not None and walk.memory_events:
        first_tainted = walk.memory_events[0]
        later_loads = [e for e in walk.edges if e["edge_kind"] == "memory"
                       and e["consumer_seq"] not in marker_seqs]
        clear_store = _first_clean_store_after(
            trace, archmem, first_tainted["addr"], first_tainted["width"],
            first_tainted["seq"], later_loads[0]["consumer_seq"]
            if later_loads else None)
        if clear_store is not None:
            return ("MASKED_BY_OVERWRITE",
                    ["TAINTED_MEMORY_OVERWRITTEN_BEFORE_CONSUMER"],
                    {"store_seq": clear_store["seq"],
                     "store_addr": _hex(clear_store["addr"]),
                     "store_value": _hex(clear_store["value"]),
                     "first_memory_consumer_seq": (later_loads[0]
                                                   ["consumer_seq"]
                                                   if later_loads else None)},
                    None)

    # Logical overwrite: the application replaces the variable holding the
    # tainted value with a clean value before the next hash input.  The
    # VALUE marker records the replacement, and the following HASH marker
    # consumes exactly that replacement (and matches control).
    cm = ctrl_index(ctrl_events)
    for i, e in enumerate(events):
        if e.mtype != D.T_VALUE:
            continue
        c = cm.get((e.key, e.occurrence))
        if c is None or e.a != c["a"]:
            continue
        for h in events[i + 1:]:
            if h.mtype != D.T_HASH:
                continue
            hc = cm.get((h.key, h.occurrence))
            if h.a == e.a and hc is not None and h.a == hc["a"]:
                return ("MASKED_BY_OVERWRITE",
                        ["LOGICAL_OVERWRITE_BEFORE_HASH",
                         "HASH_INPUT_EQUALS_REPLACEMENT"],
                        {"replacement_event": e.as_dict(),
                         "replacement_value": _hex(e.a),
                         "control_value": _hex(c["a"]),
                         "next_hash_event": h.as_dict(),
                         "next_hash_input": _hex(h.a)},
                        None)
            break
        # The replacement may be combined with clean values before the
        # hash (e.g. `r ^ good`).  If every later hash input matches
        # control, the replacement (not the tainted value) drives the
        # output: this is still a logical overwrite.
        later_hashes = [h for h in events[i + 1:] if h.mtype == D.T_HASH]
        clean_after = all(
            (cm.get((h.key, h.occurrence)) is not None and
             h.a == cm[(h.key, h.occurrence)]["a"])
            for h in later_hashes)
        if later_hashes and clean_after and \
                (target is None or e.seq > (target.get("seq") or 0)):
            return ("MASKED_BY_OVERWRITE",
                    ["LOGICAL_OVERWRITE_BEFORE_HASH",
                     "REPLACEMENT_VALUE_MATCHES_CONTROL",
                     "ALL_LATER_HASH_INPUTS_MATCH_CONTROL"],
                    {"replacement_event": e.as_dict(),
                     "replacement_value": _hex(e.a),
                     "control_value": _hex(c["a"]),
                     "later_hash_inputs": [h.as_dict()
                                           for h in later_hashes[:4]]},
                    None)

    # Taint existed but never reached an architectural consumer.
    if walk is not None and not walk.edges:
        return ("MASKED_BY_NON_CONSUMPTION",
                ["TAINTED_VALUE_HAS_NO_CONSUMER"],
                {"seed_count": len(seeds),
                 "tainted_bytes_at_end": len(walk.byte_taint),
                 "target_store_seq": (target or {}).get("seq"),
                 "target_store_addr": _hex((target or {}).get("addr")),
                 "edges": 0,
                 "note": "the corrupted byte version is present in memory "
                         "but no committed load reads it before the end of "
                         "the run"}, None)
    if walk is not None and walk.edges:
        # Consumers exist but none reached a software observation and no
        # overwrite was proved.  The wrong value was manipulated by dynamic
        # instructions yet never entered an application-visible operation
        # (no marker consumes it, the output equals the control).  This is
        # non-consumption as a positive observation, not an assumption from
        # the correct checksum.
        last = walk.edges[-1]
        return ("MASKED_BY_NON_CONSUMPTION",
                ["TAINT_STOPPED_BEFORE_SOFTWARE_OBSERVATION",
                 "OUTPUT_EQUALS_CONTROL"],
                {"last_edge": {k: (v if not isinstance(v, tuple) else
                                   [_hex(x) for x in v])
                               for k, v in last.items()},
                 "marker_consumed_events": 0,
                 "walk_edge_count": len(walk.edges)},
                None)
    return ("NO_VISIBLE_ERROR_MECHANISM_UNRESOLVED",
            ["NO_TAINT_LIFECYCLE"],
            {}, "taint lifecycle could not be reconstructed")


def _control_counterpart(trace, ctrl_trace, row):
    if ctrl_trace is None or row is None:
        return None
    occ = sum(1 for r in trace.rows if r.pc == row.pc and r.idx < row.idx)
    seen = 0
    for r in ctrl_trace.rows:
        if r.pc != row.pc:
            continue
        if seen == occ:
            return r
        seen += 1
    return None


def _row_dst_value(row):
    for (_c, _a, p, v) in row.dsts:
        if p is not None and p >= 0:
            return v
    return None


def _store_value(row, disasm):
    info = disasm.get(row.pc)
    if not info or not is_store_op(info[0]):
        return None
    ops = D.split_ops(info[1])
    reg = D.parse_reg(ops[0]) if ops else None
    return D.row_src_map(row).get(reg[1]) if reg else None


def _loads_to_addr_after(trace, ctrl_trace, archmem, addr, width, after_idx):
    out = []
    for r in trace.rows[after_idx + 1:]:
        acc = archmem.accesses.get(r.idx)
        if not acc or not is_load_op(acc["mnem"]):
            continue
        a, w = acc["addr"], acc["width"]
        if a < addr + width and addr < a + w:
            fv = _row_dst_value(r)
            crow = _control_counterpart(trace, ctrl_trace, r)
            cv = _row_dst_value(crow) if crow is not None else None
            cacc = None
            if crow is not None and ctrl_trace is not None:
                cacc = None
            out.append({
                "seq": r.seq, "pc": _hex(r.pc), "addr": _hex(a),
                "fault_value": _hex(fv), "control_value": _hex(cv),
                "matches_control": (fv is not None and cv is not None and
                                    fv == cv),
                "ctrace_line": r.line,
            })
    return out


def _enrich_masking_proof(proof, termination, target, trace, ctrl_trace,
                          archmem, stores, disasm, fd, walk, output,
                          lifecycle):
    """Attach concrete instruction/value/coverage evidence to a mechanism."""
    p = dict(proof or {})
    p["output_observed"] = output.get("observed")
    p["output_control"] = output.get("control")
    p["output_matches_control"] = output.get("matches_control")
    p["oracle_pass"] = output.get("oracle_pass")
    p["architecture_commit_rows"] = len(trace.rows)
    p["arch_memory_validation"] = archmem.stats() if archmem else {}
    tseq = (target or {}).get("seq")
    trow = trace.row_of_seq(tseq) if tseq is not None else None
    t_idx = trow.idx if trow is not None else len(trace.rows) - 1

    if termination == "ACTIVATED_NO_DATA_CORRUPTION":
        seeds = p.get("seeds") or []
        p["seed_count"] = len(seeds)
        p["delivered_values_checked"] = len(seeds)
        p["delivered_value_correct"] = (
            all(not s.get("differs") for s in seeds) if seeds else False)
        p["state_change_verified"] = False
        if trow is not None:
            tval = _store_value(trow, disasm)
            crow = _control_counterpart(trace, ctrl_trace, trow)
            cval = _store_value(crow, disasm) if crow is not None else None
            p["target_commit"] = {
                "seq": trow.seq, "pc": _hex(trow.pc), "op": trow.op,
                "role": (target or {}).get("role"),
                "committed_value": _hex(tval),
                "control_counterpart_value": _hex(cval),
                "ctrace_line": trow.line,
            }
            p["state_change_verified"] = True
            p["delivered_value_correct"] = (
                p["delivered_value_correct"] or
                (tval is not None and cval is not None and tval == cval))
        addr = (target or {}).get("addr")
        if addr is not None:
            width = 8
            if trow is not None:
                acc = archmem.accesses.get(trow.idx)
                if acc and acc.get("width"):
                    width = acc["width"]
            loads = _loads_to_addr_after(trace, ctrl_trace, archmem, addr,
                                         width, t_idx)
            p["later_loads_to_target_address"] = loads[:64]
            p["later_loads_to_target_count"] = len(loads)
            p["later_loads_differing_from_control"] = sum(
                1 for x in loads if not x["matches_control"])
            p["consumer_coverage_complete"] = (
                p["later_loads_differing_from_control"] == 0)
        p["taint_lifecycle_consumers"] = len(
            lifecycle.consumers) if lifecycle else 0
        p["shadow_walk_edges"] = len(walk.edges) if walk else 0
        p["origin_kind"] = injection_origin_kind(target,
                                                 _model_of(target))

    elif termination == "MASKED_BY_OVERWRITE":
        seq = p.get("overwrite_seq") or p.get("store_seq")
        if seq is not None:
            row = trace.row_of_seq(seq)
            if row is not None:
                p["covering_instruction"] = {
                    "dyn_inst_seq": row.seq, "pc": _hex(row.pc),
                    "op": row.op, "disasm": row.disasm,
                    "ctrace_line": row.line,
                    "dst_values": [_hex(d[3]) for d in row.dsts],
                    "source_values": [(_hex(v) if v is not None else None)
                                      for v in row.srcvals],
                }
                if p.get("overwrite_seq") is not None:
                    p["overwrite_dest"] = [
                        {"class": c, "arch": a, "phys": ph,
                         "value": _hex(v)} for (c, a, ph, v) in row.dsts]
        if p.get("store_seq") is not None:
            row = trace.row_of_seq(p["store_seq"])
            addr = _addr_of(p, "store_addr")
            if row is not None and addr is not None:
                ver = stores.version_before(addr, 8, row.idx) if stores else None
                p["overwriting_store"] = {
                    "seq": row.seq, "pc": _hex(row.pc), "op": row.op,
                    "disasm": row.disasm, "value": _hex(p.get("store_value")),
                    "previous_version_seq": ver["seq"] if ver else None,
                    "previous_version_value":
                        _hex(ver["value"]) if ver else None,
                    "ctrace_line": row.line,
                }
        if p.get("replacement_event"):
            rseq = p["replacement_event"].get("dyn_inst_seq")
            row = trace.row_of_seq(rseq) if rseq is not None else None
            if row is not None:
                p["replacement_instruction"] = {
                    "dyn_inst_seq": row.seq, "pc": _hex(row.pc),
                    "op": row.op, "disasm": row.disasm,
                    "value": _hex(_row_dst_value(row)),
                    "ctrace_line": row.line,
                }
        p["overwrite_verified"] = bool(
            p.get("overwrite_seq") or p.get("store_seq") or
            p.get("replacement_event"))

    elif termination == "MASKED_BY_NON_CONSUMPTION":
        addr = _addr_of(p, "target_store_addr")
        if addr is None:
            addr = (target or {}).get("addr")
        after_seq = p.get("target_store_seq")
        start_idx = t_idx
        if after_seq is not None:
            sr = trace.row_of_seq(after_seq)
            if sr is not None:
                start_idx = sr.idx
        if addr is not None:
            loads = _loads_to_addr_after(trace, ctrl_trace, archmem, addr, 8,
                                         start_idx)
            p["later_loads_to_target_address"] = loads[:64]
            p["later_load_count"] = len(loads)
            p["later_loads_differing_from_control"] = sum(
                1 for x in loads if not x["matches_control"])
            # Non-consumption means no committed load ever observes the
            # corrupted version: either there is no later load to these
            # bytes, or every later load (complete scan) matches control.
            p["non_consumption_verified"] = (
                (len(loads) == 0 or
                 p["later_loads_differing_from_control"] == 0) and
                (len(walk.edges) == 0 if walk else True))
            p["scan_start_seq"] = trace.rows[start_idx + 1].seq if \
                start_idx + 1 < len(trace.rows) else None
            p["scan_end_seq"] = trace.rows[-1].seq if trace.rows else None
            p["scan_committed_rows"] = len(trace.rows) - start_idx - 1
        else:
            p["non_consumption_verified"] = False
        p["walk_edge_count"] = len(walk.edges) if walk else 0
        p["arch_memory_validated_loads"] = archmem.load_checked if archmem \
            else 0

    elif termination == "MASKED_BY_VALUE_CONVERGENCE":
        conv = p.get("branch_convergence") or []
        details = []
        for b in conv:
            ev = b.get("event") or {}
            a = _u64_hex(ev.get("a"))
            ca = _u64_hex(b.get("control_condition"))
            details.append({
                "dyn_inst_seq": ev.get("dyn_inst_seq"),
                "site": ev.get("site"), "iteration": ev.get("iteration"),
                "condition_fault": _hex(a),
                "condition_control": _hex(ca),
                "control_relevant_mask": 1,
                "control_relevant_bit_fault": (a & 1) if a is not None
                else None,
                "control_relevant_bit_control": (ca & 1) if ca is not None
                else None,
                "taken_fault": ev.get("b"),
                "taken_control": b.get("control_taken"),
                "ctrace_line": ev.get("ctrace_line"),
            })
        p["convergence_operations"] = details
        p["convergence_verified"] = bool(details) and all(
            _u64_hex(d["taken_fault"]) == _u64_hex(d["taken_control"]) and
            d["control_relevant_bit_fault"] ==
            d["control_relevant_bit_control"] for d in details)
        if fd and fd.get("fault"):
            p["arm_event"] = {
                "dyn_inst_seq": _ev_attr(fd["fault"], "dyn_inst_seq"),
                "type": _ev_attr(fd["fault"], "type"),
                "value": _hex(_u64_hex(_ev_attr(fd["fault"], "b"))),
                "control_value": _hex(_u64_hex(
                    _ev_attr(fd.get("control"), "b"))),
            }
    return p


def _masking_evidence_complete(termination, proof, output):
    output_ok = bool(output.get("matches_control") or
                     output.get("oracle_pass"))
    if not output_ok:
        return False
    if termination == "ACTIVATED_NO_DATA_CORRUPTION":
        return bool(proof.get("state_change_verified") and
                    proof.get("delivered_value_correct") and
                    proof.get("consumer_coverage_complete", True))
    if termination == "MASKED_BY_OVERWRITE":
        return bool(proof.get("overwrite_verified") and
                    (proof.get("covering_instruction") or
                     proof.get("overwriting_store") or
                     proof.get("replacement_instruction")))
    if termination == "MASKED_BY_NON_CONSUMPTION":
        return bool(proof.get("non_consumption_verified"))
    if termination == "MASKED_BY_VALUE_CONVERGENCE":
        return bool(proof.get("convergence_verified"))
    return False


def _model_of(target):
    # only used to report the origin kind; model semantics are not used
    return target.get("model", "") if target else ""


def _correct_value_for_seed(seed, target, trace, ctrl_events, archmem):
    """The fault-free value for the seed's dynamic instruction.

    Prefer the paired control's corresponding software event/instruction
    value; fall back to the reconstructed memory value at the access.
    """
    if seed.value is None:
        return None
    row = trace.row_of_seq(seed.seq)
    if row is None:
        return None
    # The reconstructed architectural memory at this exact committed access
    # is the fault-free value: the memory model is independently validated
    # by the load match rate (committed program order).
    acc = archmem.accesses.get(row.idx) if archmem else None
    if acc is not None:
        if "mem_value" in acc:
            return acc["mem_value"]
        if acc.get("matched") and "recorded" in acc:
            return acc["recorded"]
    # Secondary: control software event at the same PC.  Occurrence
    # alignment is required because a PC recurs once per loop iteration.
    occ = 0
    for r in trace.rows[:row.idx]:
        if r.pc == row.pc:
            occ += 1
    seen = 0
    for e in ctrl_events:
        if e.get("op_pc") != row.pc:
            continue
        if seen < occ:
            seen += 1
            continue
        return e.get("b")
    return None


def _store_write_seed(target, pt, trace):
    """Rebuild the byte version written by a faulted store (SQ01/DA04)."""
    seq = target.get("seq")
    addr = target.get("addr")
    idx = trace.index_of_seq(seq) if seq is not None else None
    if addr is None or idx is None:
        return {}, None
    data_hex = None
    for r in pt.rows:
        if r["kind"] not in ("store_wb", "store_mem"):
            continue
        kv = r["kv"]
        if r["seq_int"] not in (None, seq):
            continue
        a = _addr_of(kv, "addr")
        if a is not None and a != addr:
            continue
        data_hex = kv.get("data_hex") or kv.get("after_hex")
        if data_hex:
            break
    if not data_hex:
        # Reconstruct from the committed store data + the recorded injected
        # byte (old_byte -> new_byte); only used when the byte is unique.
        kv = target.get("kv") or {}
        old_b = kv.get("old_byte")
        new_b = kv.get("new_byte")
        row = trace.rows[idx]
        info = None  # filled from row.disasm by the caller-side table
        # The caller stashes the disassembly text in row.disasm.
        parts = row.disasm.split(None, 1)
        if old_b and new_b and len(parts) == 2:
            ops = D.split_ops(parts[1])
            reg = D.parse_reg(ops[0]) if ops else None
            vals = {}
            for (_c, arch, p), val in zip(row.srcs, row.srcvals):
                if _c >= 0 and arch is not None and arch >= 0 and p is not None \
                        and p >= 0:
                    vals[arch] = val
            val = vals.get(reg[1]) if reg else None
            if val is not None:
                bs = bytearray((val & D.MASK64).to_bytes(8, "little"))
                ob = int(str(old_b), 0) & 0xff
                nb = int(str(new_b), 0) & 0xff
                hits = [i for i, b in enumerate(bs) if b == ob]
                if len(hits) == 1:
                    bs[hits[0]] = nb
                    data_hex = bytes(bs).hex()
    if not data_hex:
        return {}, None
    try:
        bs = bytes.fromhex(data_hex)
    except ValueError:
        return {}, None
    return ({addr + i: {"byte": b, "seq": seq,
                        "value": int.from_bytes(bs, "little"),
                        "node": target.get("node_id")}
             for i, b in enumerate(bs)}, idx)


def _first_clean_store_after(trace, archmem, addr, width, after_seq, before_seq):
    for r in trace.rows:
        if r.seq <= after_seq:
            continue
        if before_seq is not None and r.seq >= before_seq:
            break
        acc = archmem.accesses.get(r.idx)
        if not acc or not is_store_op(acc["mnem"]):
            continue
        a2, w2 = acc["addr"], acc["width"]
        if a2 < addr + width and addr < a2 + w2 and "value" in acc:
            return {"seq": r.seq, "addr": a2, "value": acc["value"]}
    return None


# ---------------------------------------------------------------------------
# per-run analysis
# ---------------------------------------------------------------------------
def analyze_strict(run_id):
    st, out = L.load_state(run_id, "fault")
    if not st:
        return {"run_id": run_id, "status": "MISSING_STATE"}
    model, ctx = st["model"], st["context"]
    trace = D.StrictTrace(out / "commit_trace.csv.gz")
    disasm = D.load_elf_disasm(model, ctx)
    for r in trace.rows:
        info = disasm.get(r.pc)
        if info:
            r.disasm = f"{info[0]} {info[1]}"
    archmem = ArchMemory(trace, disasm)
    stores = F.StoreIndex(trace, disasm, archmem)
    pt = PropTrace(out / "prop_trace.csv.gz")
    stdout = ((out / "stdout.log").read_text(errors="replace")
              if (out / "stdout.log").exists() else "")

    target, injections = extract_target(model, pt, trace, stdout)
    if target is not None:
        target["model"] = model

    # ---- microarchitectural divergence --------------------------------
    graph = Graph(run_id)
    inj_nodes = []
    micro_nodes = []
    for r in injections:
        nid = graph.node("injection", dyn_inst_seq=r["seq_int"],
                         tick=r["tick_int"], record=r["kind"],
                         detail=r["detail"],
                         trace_record_id=r["node_id"],
                         evidence_file="prop_trace.csv.gz",
                         evidence_line=r["line"])
        inj_nodes.append(nid)
    tnode = None
    if target:
        tnode = graph.node("target_instruction", dyn_inst_seq=target["seq"],
                           pc=_hex(target["pc"]), address=_hex(target["addr"]),
                           role=target["role"], record=target["kind"],
                           detail_kv=target["kv"],
                           evidence_file=target["evidence"])
        if inj_nodes:
            graph.edge(inj_nodes[0], tnode, "injection_identity", DIRECT,
                       "same record: injection node dyn_inst_seq == target "
                       "dyn_inst_seq", src_file="prop_trace.csv.gz",
                       src_line=int(injections[0]["line"]) if injections else 0)

    # propagation records that belong to the target's chain
    tseq = target["seq"] if target else None
    origin = injection_origin_kind(target, model)
    related = []
    if tseq is not None:
        for r in pt.rows:
            if r["kind"] in ("consumer", "prop_edge"):
                continue
            if r["seq_int"] == tseq:
                related.append(r)
    for r in related:
        un = graph.node("microarchitecture", record_kind=r["kind"],
                        dyn_inst_seq=r["seq_int"], tick=r["tick_int"],
                        request_id=r["request_id"], address=r["addr"],
                        detail=r["detail"], trace_record_id=r["node_id"],
                        evidence_file="prop_trace.csv.gz",
                        evidence_line=r["line"])
        # The injection->effect link must be a real shared-identity link,
        # not mere adjacency: same dyn inst seq and, when present, the same
        # request/address/entry identity recorded on both records.
        lvl, method = _injection_effect_link(injections[0] if injections
                                             else None, r)
        if lvl in STRONG:
            micro_nodes.append(un)
        graph.edge(tnode, un, "microarchitectural_effect", lvl, method,
                   value=r["kv"].get("data_hex") or r["kv"].get("inj_data_hex"),
                   src_file="prop_trace.csv.gz", src_line=int(r["line"]))

    # ---- taint lifecycle ----------------------------------------------
    lifecycle = TaintLifecycle(pt, trace)
    prop_node_graph = {}
    for s in lifecycle.seeds:
        tr = pt.by_id.get(s.node_id, {})
        n = graph.node("payload_to_register",
                       dyn_inst_seq=s.seq, phys_reg=s.phys[1],
                       class_=s.phys[0], value=_hex(s.value),
                       value_hash=s.hash,
                       trace_record_id=s.node_id,
                       evidence_file="prop_trace.csv.gz",
                       evidence_line=tr.get("line"))
        prop_node_graph[s.node_id] = n
        src_id = tr.get("kv", {}).get("source_event_id", "")
        src = prop_node_graph.get(src_id)
        if src is None:
            src = tnode
        src_h = _norm_hash(tr.get("kv", {}).get("source_value_hash"))
        lvl = DIRECT if (src_h and src_h == s.hash) else RECON
        graph.edge(src, n, "payload_to_register", lvl,
                   "taint_reg writeback_value_fnv equals the source payload "
                   "fnv; phys register is the real renamed destination",
                   value=s.value, src_file="prop_trace.csv.gz",
                   src_line=tr.get("line"))
    # The taint fan-out can be tens of thousands of consumers; the causal
    # CHAIN only needs the consumers on software-observation paths plus a
    # bounded prefix.  The full count is preserved in taint_lifecycle.
    marker_row_seqs = {s for g in trace.markers for s in g.seqs}
    exported_consumers = 0
    for ci, c in enumerate(lifecycle.consumers):
        if ci >= 3000 and c["seq"] not in marker_row_seqs:
            continue
        exported_consumers += 1
        n = graph.node("register_consumer", dyn_inst_seq=c["seq"],
                       pc=c["pc"], input_value=_hex(c["in_value"]),
                       output_value=_hex(c["out_value"]),
                       input_hash=c["input"], output_hash=c["output"],
                       dest_phys_reg=c["dest_phys"],
                       dest_arch_reg=c["dest_arch"],
                       trace_record_id=c["node"],
                       evidence_file="prop_trace.csv.gz",
                       evidence_line=c["line"])
        prop_node_graph[c["node"]] = n
        src = prop_node_graph.get(c["source_event_id"], tnode)
        graph.edge(src, n, "verified_register_dataflow", DIRECT,
                   "consumer_input_fnv == producing node fnv and the "
                   "commit-time source phys register is the tainted one",
                   value=c["in_value"], src_file="prop_trace.csv.gz",
                   src_line=c["line"])
    # Only the prop_edge rows that close a taint-chain node are exported;
    # the full register stream stays in the raw trace.
    for pe in pt.kind("prop_edge"):
        se = pe["kv"].get("source_event_id", "")
        de = pe["kv"].get("destination_event_id", "")
        if se in prop_node_graph and de in prop_node_graph:
            graph.edge(prop_node_graph[se], prop_node_graph[de],
                       pe["kv"].get("edge_type", "prop_edge"), DIRECT,
                       "explicit tracer prop_edge row; source/destination "
                       "value hashes recorded on the row",
                       value=pe["kv"].get("destination_value_hash"),
                       src_file="prop_trace.csv.gz", src_line=pe["line"])
    seeds = []
    seed_idx = None
    trow = trace.row_of_seq(tseq) if tseq is not None else None
    t_idx = trow.idx if trow else None
    for s in lifecycle.seeds:
        if s.seq is not None:
            row = trace.row_of_seq(s.seq)
            if row is not None and s.phys[1] is not None:
                seeds.append((s.phys[0], s.phys[1], s.value, s.hash,
                              s.node_id, s.seq))
                if seed_idx is None or row.idx < seed_idx:
                    seed_idx = row.idx
    # Store-side seed: the corrupted store bytes, when no taint_reg exists
    # yet at a reload (e.g. write suppressed and never reloaded).
    byte_seeds = {}
    if target and target["role"] == "store":
        kv = target["kv"]
        for key in ("addr", "store_addr", "addr_after"):
            if key in kv:
                a = _addr_of(kv, key)
                if a is not None:
                    break
        else:
            a = None
        data_hex = kv.get("data_hex") or kv.get("store_data_hex")
        if data_hex and a is not None:
            try:
                bs = bytes.fromhex(data_hex)
                for i, b in enumerate(bs):
                    byte_seeds[a + i] = {"byte": b, "seq": tseq,
                                         "value": int.from_bytes(bs, "little"),
                                         "node": target.get("node_id")}
            except ValueError:
                pass
    walk = None
    if seeds and seed_idx is not None:
        walk = SemanticWalk(trace, disasm, archmem, seeds, seed_idx,
                            byte_seeds, run_id=run_id)
    elif byte_seeds and t_idx is not None:
        walk = SemanticWalk(trace, disasm, archmem, [], t_idx - 1, byte_seeds,
                            run_id=run_id)
    # Store-side fallback: some SQ01/DA04 runs have no payload->register
    # record because the corrupted store is never reloaded through the
    # tracer's taint path.  Rebuild the byte version from the recorded
    # store writeback / cache write and walk it independently.
    if ((walk is None or not walk.edges) and target is not None
            and target.get("role") == "store"
            and origin in ("STORE_DATA_CORRUPTED", "BYTE_ENABLE_CLEARED")):
        fb_bytes, fb_idx = _store_write_seed(target, pt, trace)
        if fb_bytes and fb_idx is not None:
            fb = SemanticWalk(trace, disasm, archmem, [], fb_idx, fb_bytes,
                              run_id=run_id)
            # Keep the walk even with zero edges: an empty walk over a
            # proved corrupted byte version is itself the non-consumption
            # witness.
            walk = fb

    # ---- architectural state ------------------------------------------
    commit = trace.row_of_seq(tseq) if tseq is not None else None
    arch = {
        "target_committed": commit is not None,
        "target_commit": ({"seq": commit.seq, "tick": commit.tick,
                           "pc": _hex(commit.pc), "op": commit.op,
                           "dst_values": [_hex(d[3]) for d in commit.dsts],
                           "ctrace_line": commit.line} if commit else None),
        "target_squashed": (tseq in trace.squash) if tseq is not None else False,
        "target_squash_tick": (trace.squash_tick.get(tseq)
                               if tseq is not None else None),
        "first_architectural_divergence": None,
    }
    # First committed instruction whose value differs from the control's
    # corresponding dynamic instruction (PC + occurrence alignment).
    ctrl_trace = None
    ctrl_out = EXT / "results/controls" / f"E2E-{model}-{ctx}-CTRL" / \
        "attempt_1"
    if (ctrl_out / "commit_trace.csv.gz").exists():
        ctrl_trace = D.StrictTrace(ctrl_out / "commit_trace.csv.gz")
    if ctrl_trace is not None:
        fad = _first_arch_divergence(trace, ctrl_trace, t_idx)
        arch["first_architectural_divergence"] = fad
        if commit is not None and fad is not None:
            cn = graph.node("commit", dyn_inst_seq=commit.seq,
                            tick=commit.tick, pc=_hex(commit.pc),
                            op=commit.op,
                            dst_values=[_hex(d[3]) for d in commit.dsts],
                            evidence_file="commit_trace.csv.gz",
                            evidence_line=commit.line)
            graph.edge(tnode, cn, "architectural_commit", DIRECT,
                       "commit trace row for the target dyn_inst_seq",
                       src_file="commit_trace.csv.gz", src_line=commit.line)
    if arch["target_squashed"]:
        sn = graph.node("squash", dyn_inst_seq=tseq,
                        tick=arch["target_squash_tick"],
                        evidence_file="commit_trace.csv.gz",
                        evidence_line=_squash_line(out, tseq))
        graph.edge(tnode, sn, "squashed_before_commit", DIRECT,
                   "commit-trace '# squash <seq>' record",
                   src_file="commit_trace.csv.gz",
                   src_line=_squash_line(out, tseq))

    # ---- software events and divergence -------------------------------
    events = build_sw_events(trace, disasm)
    ctrl_meta, ctrl_events = load_control_events(model, ctx)
    fd = first_sw_divergence(events, ctrl_events)
    reload_seq = None
    if target is not None and target.get("role") == "store" and \
            t_idx is not None and target.get("addr") is not None:
        for r in trace.rows[t_idx + 1:]:
            acc = archmem.accesses.get(r.idx)
            if acc and is_load_op(acc["mnem"]) and \
                    acc["addr"] == target["addr"]:
                reload_seq = r.seq
                break
    hash_roots = {s.seq for s in lifecycle.seeds if s.seq is not None}
    if tseq is not None:
        hash_roots.add(tseq)
    if reload_seq is not None:
        hash_roots.add(reload_seq)
    hashes, first_bad_hash = verify_hash_events(
        events, ctrl_events, set(lifecycle.tainted_seqs), walk, trace,
        hash_roots)
    output_ev = next((e for e in reversed(events) if e.mtype == D.T_OUTPUT),
                     None)
    ctrl_output = next((e for e in reversed(ctrl_events)
                        if e.get("type") == D.T_OUTPUT), None)
    output = {
        "observed": _hex(output_ev.a) if output_ev else None,
        "control": _hex(ctrl_output["a"]) if ctrl_output else None,
        "expected": st.get("oracle_expected"),
        "oracle_pass": st.get("oracle_pass"),
        "marker_seq": output_ev.seq if output_ev else None,
        "matches_control": (output_ev.a == ctrl_output["a"]
                            if output_ev and ctrl_output else None),
    }
    hash_events = [e for e in events if e.mtype == D.T_HASH]
    hash_flow = F.analyze_hash_streams(
        trace, disasm, hash_events, hashes, stores, archmem)
    if output_ev is not None:
        output_validation = F.analyze_output_expression(
            trace, disasm, output_ev.group, hash_flow, stores, archmem)
    else:
        output_validation = {"verified": False,
                             "reason": "output_marker_missing"}
    output["b"] = (output_validation.get("b")
                   if output_ev is not None else None)
    output["c"] = (output_validation.get("c")
                   if output_ev is not None else None)
    output["formula"] = output_validation.get("formula")
    output["expression_verified"] = output_validation.get("verified")
    # Semantic names for paper-level reporting.  The SQ workload's OUTPUT
    # is (s ^ path, s, path); every other workload outputs s alone.
    for slot, prod in (output_validation.get("operand_producers")
                       or {}).items():
        if slot in ("1", "2"):
            prod["state_role"] = "HashAccumulator_S"
        elif slot == "3":
            prod["state_role"] = (
                "HashAccumulator_Path"
                if prod.get("kind") == "hash_accumulator"
                else "StateAccumulator_Path")
    output["output_validation"] = output_validation

    # ---- causal connection of the first software divergence -----------
    connection = None
    stream_artifacts = []
    if fd is not None and fd.get("fault") is not None:
        connection = connect_software_divergence(
            fd["fault"], target, tseq, commit, lifecycle, walk, trace,
            disasm, ctrl_events, pt)
    # An earlier event difference can be a dynamic-stream artifact (the
    # instrumented binaries follow a different control path) rather than a
    # fault effect.  Keep the earliest divergence that is actually
    # connected to the fault, and record the skipped ones.
    if (fd is None or connection is None or
            connection.get("level") not in STRONG):
        for fe, ce, fields in iter_sw_diffs(events, ctrl_events):
            if fe is None:
                continue
            if tseq is not None and fe.seq <= tseq:
                continue
            if fd is not None and fe is fd.get("fault"):
                continue
            cc = connect_software_divergence(
                fe, target, tseq, commit, lifecycle, walk, trace, disasm,
                ctrl_events, pt)
            if cc.get("level") in STRONG:
                if fd is not None:
                    stream_artifacts.append({
                        "kind": fd.get("kind"),
                        "event": (fd.get("fault").as_dict()
                                  if fd.get("fault") else None),
                        "fields": fd.get("fields")})
                fd = {"kind": ("value" if ce is not None else
                               "event_missing_in_control"),
                      "fault": fe, "control": ce, "fields": fields}
                connection = cc
                break

    # ---- symptom / termination ----------------------------------------
    terminal = st.get("terminal")
    origin = injection_origin_kind(target, model)
    symptom = None
    subtype = None
    termination = None
    mech = []
    gaps = []
    proof = {}
    app_validation = {"verified": False, "checks": {},
                      "evidence": []}
    masking_evidence_complete = True

    if terminal == "HANG_WATCHDOG" or terminal == "HANG":
        symptom = "HANG_TIMEOUT"
        subtype = "SIMULATOR_WATCHDOG"
        termination = "STALLED"
        app_validation = {"verified": True,
                          "checks": {"terminal": terminal},
                          "evidence": ["simulator watchdog"]}
    elif terminal == "CRASH":
        symptom = "APPLICATION_CRASH"
        subtype = "OTHER_APPLICATION_CRASH"
        termination = "UNRESOLVED"
        gaps.append("se_crash_mechanism_unresolved")
        app_validation = {"verified": False, "checks": {},
                          "evidence": ["crash mechanism unresolved"]}
    elif terminal == "SDC":
        symptom = "WRONG_OUTPUT"
        subtype, app_validation = classify_application_symptom(
            symptom=symptom, origin=origin, fd=fd, target=target,
            trace=trace, disasm=disasm, archmem=archmem, stores=stores,
            ctrl_events=ctrl_events, ctrl_trace=ctrl_trace, output=output)
        termination = "COMMITTED_AND_PROPAGATED"
        if fd is None:
            gaps.append("checksum_mismatch_without_software_divergence")
        if connection is None or connection.get("level") not in STRONG:
            gaps.append("software_divergence_not_causally_connected")
        if output["observed"] is None or output["control"] is None:
            gaps.append("output_marker_missing")
        elif output["observed"] == output["control"]:
            gaps.append("output_marker_matches_control_but_oracle_failed")
        bad_hashes = [h for h in hashes if not h["transition_verified"]]
        if bad_hashes:
            gaps.append("hash_transition_semantics_unverified")
        if hashes and first_bad_hash is None and fd is not None:
            # divergence exists but never enters the hash stream: only OK
            # if the output difference is independently explained.
            gaps.append("no_incorrect_hash_input_for_wrong_output")
        if first_bad_hash is not None and \
                not first_bad_hash.get("input_tainted_by"):
            gaps.append("hash_input_not_causally_connected")
    else:
        # The final checksum is correct, but an intermediate committed
        # software value may still differ.  That is a visible divergence in
        # its own right and must not be reported as "no visible error".
        if (fd is not None and fd.get("fault") is not None and
                connection is not None and
                connection.get("level") in STRONG):
            symptom = "INTERMEDIATE_VALUE_DIVERGENCE"
            subtype = "INTERMEDIATE_VALUE_DIVERGENCE"
            _fev = fd.get("fault")
            app_validation = {
                "verified": True,
                "checks": {"first_divergent_event":
                           (_fev.as_dict() if hasattr(_fev, "as_dict")
                            else _fev)},
                "evidence": ["committed application value differs from "
                             "control while the final output is correct"]}
        else:
            # Any remaining difference is a dynamic-stream artifact, not a
            # fault-caused software divergence: this run has no visible
            # fault effect at the software level.
            symptom = "NO_VISIBLE_ERROR"
            subtype = "NO_VISIBLE_ERROR"
            app_validation = {
                "verified": bool(output.get("matches_control") or
                                 output.get("oracle_pass")),
                "checks": {"output_matches_control":
                           output.get("matches_control"),
                           "oracle_pass": output.get("oracle_pass")},
                "evidence": ["no fault-caused software value divergence"]}
            if fd is not None and fd.get("fault") is not None:
                stream_artifacts.append({
                    "kind": fd.get("kind"),
                    "event": fd.get("fault").as_dict(),
                    "fields": fd.get("fields"),
                    "reason": "not causally connected to the fault"})
                fd = None
                connection = None
        termination, mech, proof, reason = classify_masking(
            terminal=terminal, target=target, trace=trace, archmem=archmem,
            lifecycle=lifecycle, walk=walk, events=events,
            ctrl_events=ctrl_events, first_div=fd, origin=origin)
        if reason:
            gaps.append(reason)
        proof = _enrich_masking_proof(
            proof, termination, target, trace, ctrl_trace, archmem, stores,
            disasm, fd, walk, output, lifecycle)
        masking_evidence_complete = _masking_evidence_complete(
            termination, proof, output)
        if not masking_evidence_complete:
            gaps.append("masking_evidence_incomplete:%s" % termination)

    # ---- required-layer checks (graph is built below) ------------------
    if target is None:
        gaps.append("target_injection_not_identified")
    if target and target.get("seq") is None:
        gaps.append("target_dyn_inst_seq_missing")
    if terminal != "HANG_WATCHDOG" and tseq is not None and \
            commit is None and not arch["target_squashed"]:
        gaps.append("target_commit_or_squash_evidence_missing")
    if not injections and model != "RP01":
        gaps.append("injection_event_missing")
    if lifecycle.mismatches:
        gaps.append(f"taint_lifecycle_verification_failures="
                    f"{len(lifecycle.mismatches)}")
    if terminal == "SDC" and (connection is None or
                              connection.get("level") not in STRONG):
        gaps.append("no_strong_software_edge")

    # ---- chain nodes/edges for the software layer ----------------------
    fd_node = None
    if fd is not None and fd.get("fault") is not None:
        e = fd["fault"]
        fd_node = graph.node("first_software_divergence", **e.as_dict(),
                             control=({k: v for k, v in
                                       (fd.get("control") or {}).items()}
                                      if fd.get("control") else None),
                             differing_fields=fd["fields"],
                             divergence_kind=fd["kind"])
        if connection is not None:
            src = connection["source_node"]
            ids = {n.event_id for n in graph.nodes}
            if src not in ids:
                raw = src.split(":", 1)[1] if ":" in src else ""
                src = prop_node_graph.get(raw) or tnode
            graph.edge(src or tnode, fd_node,
                       "first_visible_software_divergence",
                       connection["level"], connection["method"],
                       value=e.b, src_file="commit_trace.csv.gz",
                       src_line=e.group.lines[3],
                       notes=connection.get("notes", []))

    # Hash nodes carry their def/use provenance; edges are only the
    # verified within-stream predecessor links.
    hash_nodes = {}
    for i, (h, hev) in enumerate(zip(hashes, hash_flow["events"])):
        hn = graph.node(
            "software_hash", dyn_inst_seq=h["seq"],
            software_site=h["site"], iteration=h["iteration"],
            input=h["input"], hash_before=h["before"],
            hash_after=h["after"], computed_after=h["computed_after"],
            transition_verified=h["transition_verified"],
            input_tainted=h["input_tainted"],
            stream=hev.get("stream"),
            predecessor=hev.get("predecessor"),
            predecessor_reason=hev.get("predecessor_reason"),
            before_producer_seq=hev.get("before_terminal_def_seq"),
            after_producer_seq=hev.get("after_terminal_def_seq"),
            producer_provenance_ok=hev.get("provenance_ok"),
            evidence_file="commit_trace.csv.gz",
            evidence_line=hev.get("ctrace_line"))
        hash_nodes[i] = hn
    for link in hash_flow["links"]:
        lvl = DIRECT if link["verified"] else UNRES
        graph.edge(
            hash_nodes[link["source"]], hash_nodes[link["target"]],
            "hash_state_stream", lvl,
            "the target hash's before-operand resolves (copies included) "
            "to the exact committed instruction instance that produced "
            "the source hash's after-operand; when_fnv recomputed "
            "(def_idx=%s seq=%s)" %
            (link["terminal_def_idx"], link["terminal_def_seq"]),
            value=link["target_before_value"],
            operation="when_fnv(before, input) -> after",
            operands={"before": _hex(link["source_after_value"]),
                      "input": hashes[link["target"]]["input"]},
            result=link["target_before_value"],
            phys_dependency={
                "source_after_phys": link["source_phys"],
                "target_before_phys": link["target_phys"],
                "same_terminal_def_idx": link["terminal_def_idx"],
                "same_terminal_def_seq": link["terminal_def_seq"]},
            src_file="commit_trace.csv.gz",
            notes=[{"source_phys": link["source_phys"],
                    "target_phys": link["target_phys"],
                    "same_def_instance": link["same_def_instance"],
                    "value_matches": link["value_matches"],
                    "fnv_transitions_verified":
                        link["fnv_transitions_verified"]}])
    if first_bad_hash is not None and hash_nodes:
        for i, h in enumerate(hashes):
            if h is first_bad_hash or h["seq"] == first_bad_hash["seq"]:
                by = h.get("input_tainted_by")
                if by in ("tracer", "semantic_walk"):
                    lvl, why = DIRECT, (
                        "hash input register is in the verified taint "
                        "set at the marker instruction (%s)" % by)
                elif by == "defuse_path":
                    lvl, why = RECON, (
                        "backward committed-instruction def/use path "
                        "from the hash input register reaches the fault "
                        "root")
                else:
                    lvl, why = UNRES, (
                        "hash input differs from control but no "
                        "taint/def-use path reaches the fault")
                graph.edge(fd_node or tnode, hash_nodes[i],
                           "first_incorrect_hash_input", lvl, why,
                           value=first_bad_hash["input"],
                           operation="hash_input",
                           operands={"fault_input":
                                     first_bad_hash["input"],
                                     "control_input":
                                     first_bad_hash.get("control_input")},
                           result=first_bad_hash["input"],
                           phys_dependency={
                               "input_tainted_by":
                                   first_bad_hash.get("input_tainted_by")},
                           src_file="commit_trace.csv.gz")
                break

    onode = None
    exprn = None
    if output_ev is not None:
        onode = graph.node("application_output",
                           dyn_inst_seq=output_ev.seq,
                           checksum=_hex(output_ev.a),
                           control_checksum=output["control"],
                           b_operand=output_validation.get("b"),
                           c_operand=output_validation.get("c"),
                           formula=output_validation.get("formula"),
                           expression_verified=output_validation.get(
                               "verified"),
                           oracle_pass=st.get("oracle_pass"),
                           evidence_file="commit_trace.csv.gz",
                           evidence_line=output_ev.group.lines[3])
        exprn = graph.node(
            "final_expression",
            verified=output_validation.get("verified"),
            reason=output_validation.get("reason"),
            formula=output_validation.get("formula"),
            a=output_validation.get("a"),
            b=output_validation.get("b"),
            c=output_validation.get("c"),
            expression=output_validation.get("expression"),
            operand_roles=output_validation.get("operand_roles"),
            operand_role_values_verified=output_validation.get(
                "operand_role_values_verified"),
            operand_producers=output_validation.get(
                "operand_producers"),
            evidence_file="commit_trace.csv.gz")
        if not output_validation.get("verified"):
            gaps.append("final_output_expression_unverified")
        # State tails -> final expression.
        for slot_key, prod in (output_validation.get(
                "operand_producers") or {}).items():
            kind = prod.get("kind")
            if kind == "hash_accumulator":
                idx = prod.get("hash_event")
                src = hash_nodes.get(idx)
                if src is None:
                    gaps.append("final_operand_hash_node_missing")
                    continue
                graph.edge(
                    src, exprn, "final_expression_operand",
                    DIRECT if output_validation.get("verified") else UNRES,
                    "operand %s of the final expression is produced by "
                    "the tail of hash stream %s (def_seq=%s)" %
                    (slot_key, prod.get("stream"), prod.get("def_seq")),
                    value=prod.get("value"),
                    operation="operand_feed",
                    operands={"role": prod.get("state_role"),
                              "operand_slot": slot_key},
                    result=prod.get("value"),
                    phys_dependency={"producer_def_seq":
                                     prod.get("def_seq")},
                    src_file="commit_trace.csv.gz")
            elif kind == "state_update":
                sp = graph.node(
                    "software_state_producer",
                    dyn_inst_seq=prod.get("def_seq"),
                    op=prod.get("op"), disasm=prod.get("disasm"),
                    value=prod.get("value"),
                    semantics_ok=prod.get("semantics_ok"),
                    evidence_file="commit_trace.csv.gz")
                graph.edge(
                    sp, exprn, "final_expression_operand",
                    DIRECT if (output_validation.get("verified") and
                               prod.get("semantics_ok")) else UNRES,
                    "operand %s is the result of a real committed state "
                    "update recomputed from its operands" % slot_key,
                    value=prod.get("value"),
                    operation=prod.get("op") or "state_update",
                    operands={"role": prod.get("state_role"),
                              "operand_slot": slot_key},
                    result=prod.get("value"),
                    phys_dependency={"producer_def_seq":
                                     prod.get("def_seq"),
                                     "semantics_ok":
                                     prod.get("semantics_ok")},
                    src_file="commit_trace.csv.gz")
            elif kind == "constant":
                continue
            else:
                gaps.append("final_operand_producer_unresolved")
        graph.edge(
            exprn, onode, "final_output_computation",
            DIRECT if output_validation.get("verified") else UNRES,
            "OUTPUT marker slots recomputed from the real expression "
            "instruction (%s); formula %s" %
            ((output_validation.get("expression") or {}).get("disasm"),
             output_validation.get("formula")),
            value=output_ev.a, src_file="commit_trace.csv.gz",
            src_line=output_ev.group.lines[3],
            operation=(output_validation.get("expression") or {}).get(
                "op") or "output_expression",
            operands={"a": output_validation.get("a"),
                      "b": output_validation.get("b"),
                      "c": output_validation.get("c"),
                      "formula": output_validation.get("formula")},
            result=output_ev.a,
            phys_dependency=output_validation.get(
                "operand_role_values_verified"))

    # ---- masking endpoint (all A/B/C/D mechanisms) --------------------
    if symptom in ("NO_VISIBLE_ERROR", "INTERMEDIATE_VALUE_DIVERGENCE"):
        ep = graph.node(
            "masking_endpoint", dyn_inst_seq=tseq,
            mechanism=termination, codes=mech,
            proof=proof, symptom=symptom,
            masking_evidence_complete=masking_evidence_complete,
            seeds=[{"seq": s.seq, "phys": list(s.phys),
                    "value": _hex(s.value), "hash": s.hash}
                   for s in lifecycle.seeds],
            taint_consumers=len(lifecycle.consumers),
            walk_edges=len(walk.edges) if walk else 0)
        src = None
        if fd_node is not None:
            src = fd_node
        elif lifecycle.seeds:
            src = prop_node_graph.get(lifecycle.seeds[0].node_id)
        elif micro_nodes:
            src = micro_nodes[0]
        else:
            src = tnode
        lvl = DIRECT if masking_evidence_complete else UNRES
        graph.edge(
            src or tnode, ep, "masking_mechanism",
            lvl, "%s: %s" % (termination,
                             "; ".join(mech) or "mechanism witness"),
            operation=termination,
            operands={"mechanism_codes": mech,
                      "proof_keys": sorted(proof.keys())},
            result=(output_ev.a if output_ev else None),
            phys_dependency={"masking_evidence_complete":
                             masking_evidence_complete},
            src_file="commit_trace.csv.gz" if src == fd_node
            else "prop_trace.csv.gz")
        if onode is not None:
            output_ok = bool(output.get("matches_control") or
                             output.get("oracle_pass"))
            graph.edge(
                ep, onode, "output_correct_after_masking",
                DIRECT if (masking_evidence_complete and output_ok)
                else UNRES,
                "final output equals control/oracle after %s" % termination,
                value=output_ev.a if output_ev else None,
                operation="output_unaffected",
                operands={"termination": termination,
                          "mechanism_codes": mech},
                result=output_ev.a if output_ev else None,
                phys_dependency={"output_matches_control":
                                 output.get("matches_control")},
                src_file="commit_trace.csv.gz")
    if terminal == "HANG_WATCHDOG":
        graph.node("stall_state", target_committed=False,
                   last_commit_dyn_seq=st.get("last_commit_dyn_seq"),
                   watchdog_tick=st.get("watchdog_tick"),
                   evidence="prop_trace.csv.gz")

    edge_levels = graph.level_count()
    result = {
        "run_id": run_id, "model": model, "context": ctx,
        "timing": st.get("timing"),
        "old_run_id": st.get("old_run_id"),
        "terminal": terminal,
        "target": ({k: v for k, v in target.items() if k != "model"}
                   if target else None),
        "model_origin_evidence": origin,
        "microarchitectural_divergence": {
            "injection_records": [{"kind": r["kind"], "seq": r["seq_int"],
                                   "tick": r["tick_int"], "kv": r["kv"],
                                   "trace_record_id": r["node_id"],
                                   "line": r["line"]}
                                  for r in injections],
            "target_records": [{"kind": r["kind"], "seq": r["seq_int"],
                                "tick": r["tick_int"], "kv": r["kv"],
                                "trace_record_id": r["node_id"],
                                "line": r["line"]}
                               for r in related],
        },
        "architectural": arch,
        "taint_lifecycle": {
            "seeds": [{"seq": s.seq, "phys": list(s.phys),
                       "value": _hex(s.value), "hash": s.hash,
                       "node": s.node_id} for s in lifecycle.seeds],
            "consumer_count": len(lifecycle.consumers),
            "exported_consumer_edges": exported_consumers,
            "consumers": lifecycle.consumers[:4000],
            "verification_failures": lifecycle.mismatches,
            "partial_payloads": lifecycle.partial_payloads,
        },
        "semantic_walk": {
            "seed_count": len(seeds),
            "edge_count": len(walk.edges) if walk else 0,
            "edges": (walk.edges[:4000] if walk else []),
            "unsupported_semantics": walk.unsupported if walk else 0,
            "unsupported_critical": (walk.unsupported_critical
                                     if walk else 0),
            "unsupported_noncritical": (walk.unsupported_noncritical
                                        if walk else 0),
            "semantic_mismatches": walk.mismatched_semantics if walk else 0,
            "unverified_semantic_edges": (walk.unverified_semantic_edges
                                          if walk else 0),
            "nzcv": {
                "flag_producers_observed":
                    walk.flag_producers_observed if walk else 0,
                "flag_producers_verified":
                    walk.flag_producers_verified if walk else 0,
                "flag_semantic_mismatches":
                    walk.flag_semantic_mismatches if walk else 0,
                "conditional_checks":
                    walk.conditional_checks if walk else 0,
                "conditional_verified":
                    walk.conditional_verified if walk else 0,
                "conditional_unverified":
                    walk.conditional_unverified if walk else 0,
                "untainted_semantic_checks":
                    walk.untainted_semantic_checks if walk else 0,
                "untainted_semantic_mismatches":
                    walk.untainted_semantic_mismatches if walk else 0,
            },
            "memory": {
                "pair_checks": walk.memory_pair_checks if walk else 0,
                "pair_verified": walk.memory_pair_verified if walk else 0,
                "semantics_incomplete":
                    walk.memory_semantics_incomplete if walk else 0,
            },
            "multi_source": {
                "extra_source_edges": walk.multi_source_edges if walk else 0,
                "dropped_sources": walk.multi_source_drops if walk else 0,
            },
            "revalidation_count": len(walk.revalidations) if walk else 0,
            "revalidations": (walk.revalidations[:4000] if walk else []),
            "unsupported_examples": (walk.unsupported_examples
                                     if walk else []),
            "mismatch_examples": (walk.mismatch_examples if walk else []),
            "memory_events": (walk.memory_events[:400] if walk else []),
        },
        "software": {
            "event_count": len(events),
            "first_divergence": ({"kind": fd["kind"],
                                  "fault": fd["fault"].as_dict()
                                  if fd.get("fault") else None,
                                  "control": fd.get("control"),
                                  "fields": fd["fields"]} if fd else None),
            "causal_connection": connection,
            "stream_artifacts": stream_artifacts,
            "hash_events": hashes,
            "first_incorrect_hash_input": first_bad_hash,
            "hash_transition_failures": sum(
                1 for h in hashes if not h["transition_verified"]),
            "hash_flow": {
                "event_count": len(hash_flow["events"]),
                "stream_count": len(hash_flow["streams"]),
                "verified_links": hash_flow["verified_links"],
                "unverified_links": hash_flow["unverified_links"],
                "events_with_bad_provenance":
                    hash_flow["events_with_bad_provenance"],
                "events_with_unresolved_before":
                    hash_flow["events_with_unresolved_before"],
                "roots": hash_flow["roots"],
                "tails": hash_flow["tails"],
                "streams": {k: {"size": len(v), "first_seq":
                                hash_flow["events"][v[0]]["seq"],
                                "last_seq":
                                hash_flow["events"][v[-1]]["seq"]}
                            for k, v in hash_flow["streams"].items()},
                "ambiguity": hash_flow["ambiguity"],
                "events": hash_flow["events"],
            },
            "output": output,
            "output_validation": output_validation,
            "application_validation": app_validation,
            "all_differences": _all_diffs(events, ctrl_events)[:256],
        },
        "arch_memory_validation": archmem.stats(),
        "classification": {
            "fault_mechanism": origin,
            "fault_mechanism_class": fault_mechanism_class(origin),
            "software_symptom": symptom,
            "application_symptom": subtype,
            "symptom_subtype": subtype,
            "propagation_termination": termination,
            "mechanism_sequence": mech,
            "masking_proof": proof,
            "masking_evidence_complete": (
                masking_evidence_complete
                if symptom in ("NO_VISIBLE_ERROR",
                               "INTERMEDIATE_VALUE_DIVERGENCE") else None),
            "application_validation": app_validation,
            "end_to_end_status": None,
            "gaps": list(gaps),
            "edge_levels": dict(edge_levels),
        },
        "nodes": [n.as_dict() for n in graph.nodes],
        "edges": [e.as_dict() for e in graph.edges],
        "evidence_files": {
            "fault_dir": str(out.relative_to(EXT)),
            "prop_trace": str((out / "prop_trace.csv.gz").relative_to(EXT)),
            "commit_trace": str((out / "commit_trace.csv.gz").relative_to(EXT)),
            "stdout": str((out / "stdout.log").relative_to(EXT)),
        },
        "versions": {
            "binary_sha": st.get("binary_sha"),
            "elf_sha": st.get("elf_sha"),
            "config_sha": st.get("config_sha"),
        },
    }
    # Validation happens strictly *after* node/edge construction.  Its
    # failures become gaps and therefore block COMPLETE.
    validation_gaps = validate_end_to_end_graph(result)
    result["classification"]["gaps"] = sorted(
        set(list(gaps) + validation_gaps))
    result["classification"]["end_to_end_status"] = compute_status(
        result["classification"]["gaps"], target is not None)
    result["graph_validation"] = {
        "passed": not validation_gaps,
        "gaps": validation_gaps,
    }
    import os
    if os.environ.get("LSU_WRITE_REVALIDATION") and walk is not None:
        _write_revalidation_rows(run_id, walk.revalidations)
    return result


def _injection_effect_link(inj, r):
    """Grade an injection->effect edge from shared identity fields."""
    if inj is None:
        return UNRES, "no injection record"
    kv_i = inj["kv"]
    kv_r = r["kv"]
    # same dynamic instruction is required for a same-instruction effect
    if r["seq_int"] is not None and inj["seq_int"] is not None and \
            r["seq_int"] != inj["seq_int"]:
        # A store's writeback/reload is a different instruction; the link is
        # then an address/entry identity relation, not same-instruction.
        shared = _shared_identity(kv_i, kv_r)
        if not shared:
            return CORR, "different dyn inst and no shared entry/address id"
        return RECON, "shared identity: " + ",".join(shared)
    # same instruction: require a real recorded relation kind
    if r["kind"] in ("mem_req", "resp", "taint_reg", "commit", "errant_commit",
                     "inj_store_data", "store_wb", "store_mem",
                     "inj_store_be", "inj_sp05", "inj_sq03", "inj_fw05",
                     "inj_md04", "inj_l1dfwd", "fwd", "addr_form"):
        return DIRECT, "same dyn_inst_seq and recorded fault-path record"
    shared = _shared_identity(kv_i, kv_r)
    if shared:
        return RECON, "shared identity: " + ",".join(shared)
    return CORR, "same dyn inst only; no payload/identity field"


def _shared_identity(a, b):
    out = []
    for k in ("request_id", "lq_entry_id", "lq_entry_generation", "sq_entry_id",
              "sq_entry_generation", "addr", "store_addr", "load_addr",
              "vaddr", "fragment_id", "response_id"):
        if k in a and k in b and str(a[k]).lower() == str(b[k]).lower():
            out.append(f"{k}={a[k]}")
    return out


def _squash_line(out, seq):
    p = out / "commit_trace.csv.gz"
    if not p.exists():
        return 0
    ln = 0
    for text in D.gz_lines(p):
        ln += 1
        if text.startswith("# squash"):
            parts = text.split()
            if len(parts) >= 3 and parts[2] == str(seq):
                return ln
    return 0


def _first_arch_divergence(trace, ctrl_trace, after_idx):
    """First committed value divergence vs the control, PC+ordinal aligned."""
    ctrl_by_pc = collections.defaultdict(list)
    for r in ctrl_trace.rows:
        ctrl_by_pc[r.pc].append(r)
    seen = collections.Counter()
    for r in trace.rows[after_idx + 1:] if after_idx is not None else []:
        j = seen[r.pc]
        seen[r.pc] += 1
        cand = ctrl_by_pc.get(r.pc)
        if not cand or j >= len(cand):
            continue
        c = cand[j]
        if r.op != c.op:
            continue
        fv = [d[3] for d in r.dsts]
        cv = [d[3] for d in c.dsts]
        if fv != cv:
            return {"dyn_inst_seq": r.seq, "tick": r.tick, "pc": _hex(r.pc),
                    "op": r.op, "fault_values": [_hex(x) for x in fv],
                    "control_values": [_hex(x) for x in cv],
                    "control_dyn_inst_seq": c.seq,
                    "ctrace_line": r.line,
                    "control_ctrace_line": c.line}
    return None


def _all_diffs(events, ctrl_events):
    cm = ctrl_index(ctrl_events)
    out = []
    for e in events:
        c = cm.get((e.key, e.occurrence))
        if c is None:
            out.append({"kind": "event_missing_in_control",
                        "event": e.as_dict()})
            continue
        fields = []
        if e.a != c["a"]:
            fields.append("a")
        if e.b != c["b"]:
            fields.append("b")
        if e.c != c["c"]:
            fields.append("c")
        if fields:
            out.append({"kind": "value", "fields": fields,
                        "fault": e.as_dict(),
                        "control": {k: c[k] for k in ("a", "b", "c", "type",
                                                      "site", "op_seq")}})
    return out


def connect_software_divergence(event, target, tseq, commit, lifecycle, walk,
                                trace, disasm, ctrl_events, pt):
    """Prove (or refuse) the edge from the fault to the first divergence."""
    tkw = target["kv"] if target else {}
    # 1. The divergent event *is* the target instruction or its reload.
    if event.op_seq is not None and tseq is not None and \
            event.op_seq == tseq:
        node = _new_node_ref("target", tseq)
        return {"level": DIRECT, "method": "software marker op_seq equals "
                "the injected dynamic instruction",
                "source_node": node, "event_seq": event.seq, "notes": []}
    # 2. A consumer/prop_edge record at one of the marker instructions.
    hits = []
    for row in event.group.seqs:
        if row in lifecycle.tainted_seqs:
            hits.extend(lifecycle.tainted_seqs[row])
    if hits:
        c = hits[0]
        return {"level": DIRECT,
                "method": "verified consumer record at marker instruction "
                          "seq=%d (input hash=%s) with the tracer's "
                          "renamed source def/use" % (c["seq"], c["input"]),
                "source_node": _new_node_ref("taint_consumer", c["node"]),
                "event_seq": event.seq, "notes": [c]}
    # 3. The marker slot's source register is tainted in our independent
    #    semantic walk.
    if walk is not None and commit is not None:
        for slot in range(4):
            (cls, phys), val, arch = event.group.slot_source(slot)
            if phys is None:
                continue
            # find the row in the group that consumes this phys AND verify
            # that this exact physical register is tainted at that marker
            # instruction (not merely present as an operand).
            for gidx in event.group.idxs:
                r = trace.rows[gidx]
                if any(p == phys for (_c, _a, p) in r.srcs) and \
                        (cls, phys) in walk.marker_taint.get(gidx, set()):
                    return {"level": DIRECT,
                            "method": "commit trace: marker slot source "
                                      "phys=%d is in the independently "
                                      "reconstructed taint set at that "
                                      "instruction" % phys,
                            "source_node": _new_node_ref("semantic_walk",
                                                         phys),
                            "event_seq": event.seq, "notes": []}
    # 4. A memory consumer at the event's op (reload from tainted bytes).
    if walk is not None and event.op_seq is not None:
        for e in walk.edges:
            if e["consumer_seq"] == event.op_seq and e["edge_kind"] == "memory":
                return {"level": RECON,
                        "method": "the event's own load consumes tainted "
                                  "memory bytes at the reconstructed "
                                  "address (byte-version match)",
                        "source_node": _new_node_ref("memory", e["producer_seq"]),
                        "event_seq": event.seq, "notes": [e]}
    # 5. Value equality alone is only correlation.
    return {"level": CORR,
            "method": "no def/use, payload, memory-version or consumer "
                      "record connects the fault to this divergence; only "
                      "dynamic order/value coincidence",
            "source_node": _new_node_ref("target", tseq),
            "event_seq": event.seq, "notes": []}


def _new_node_ref(kind, key):
    return f"{kind}:{key}"


def _write_revalidation_rows(run_id, recs):
    import csv
    if not recs:
        return
    out = EXT / "evidence/semantic_revalidation"
    out.mkdir(parents=True, exist_ok=True)
    fields = ["RunID", "DynInstSeq", "Tick", "PC", "Mnemonic", "Disassembly",
              "SourcePhysicalRegisters", "SourceValues",
              "DestinationPhysicalRegisters", "RecordedDestinationValues",
              "RecomputedValues", "ShiftOrExtend", "NZCVBefore", "NZCVAfter",
              "SemanticMatch", "SemanticStatus", "TaintRelevant",
              "CausalPathRelevant", "VerificationMethod", "Reason",
              "MemoryNote", "EvidencePath", "EvidenceLine"]
    with open(out / f"{run_id}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for rec in recs:
            w.writerow(rec)


def _worker(args):
    rid, outdir = args
    r = analyze_strict(rid)
    (Path(outdir) / f"{rid}.strict.json").write_text(json.dumps(r, indent=1))
    return rid, r["classification"]


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="all")
    ap.add_argument("--out", default=str(EXT / "evidence/strict_chains"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=1)
    args = ap.parse_args(argv)
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    ids = sorted(p.stem for p in (EXT / "results/state").glob(
        "E2E-*-FAULT.json"))
    # RP01 is rebuilt from its post-injection stall traces by
    # e2e_rp01_audit.py; the original RP01 traces contain no post-injection
    # state, so analyzing them here would only recreate the empty graph.
    if args.runs == "all":
        ids = [i for i in ids if not i.startswith("E2E-RP01-")]
    if args.runs != "all":
        ids = [i for i in ids if i in set(args.runs.split(","))]
    if args.limit:
        ids = ids[:args.limit]
    ok = 0
    errs = []

    if args.jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(_worker, (rid, str(outdir))): rid
                    for rid in ids}
            for fut in as_completed(futs):
                rid = futs[fut]
                try:
                    rid, c = fut.result()
                    ok += 1
                    print(rid, c["end_to_end_status"],
                          c["software_symptom"],
                          c["propagation_termination"], flush=True)
                except Exception as exc:  # noqa: BLE001
                    import traceback
                    traceback.print_exc()
                    errs.append((rid, repr(exc)))
    else:
        for rid in ids:
            try:
                rid, c = _worker((rid, str(outdir)))
                ok += 1
                print(rid, c["end_to_end_status"],
                      c["software_symptom"],
                      c["propagation_termination"], flush=True)
            except Exception as exc:  # noqa: BLE001
                import traceback
                traceback.print_exc()
                errs.append((rid, repr(exc)))
    print(f"analyzed {ok} errors {len(errs)}")
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main())
