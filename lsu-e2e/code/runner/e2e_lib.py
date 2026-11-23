"""Shared parsers and evidence primitives for the LSU E2E reconstruction.

Observation layers (all read-only):
  commit_trace.csv.gz v2  per committed instruction: DynInst seqNum, PC,
                          opcode, destination values, source phys ids.
  sw markers              four consecutive `mov x28` rows -> one software
                          event (type, site, sequence, addr, value, aux).
  prop_trace.csv.gz       injector/LSQ/cache/commit nodes with detail KV.
  micro_snap.csv.gz       ROB/IQ/free-list/RAT snapshots.
  stdout / injector log   injector ledger, checksum, RP01 replay ledger.

Marker event types (when_common.h):
  0x11 LOAD    tag,a=address,b=loaded value,c=(iter<<32)|aux
  0x12 STORE   tag,a=address,b=intended value,c=(iter<<32)|aux
  0x13 HASH    tag,a=input,b=hash before,c=hash after
  0x14 BRANCH  tag,a=condition,b=taken,c=(iter<<32)|0
  0x15 OUTPUT  tag,a=checksum,b=aux,c=aux
  0x16 PHASE   tag,a=phase
  0x17 VALUE   tag,a=value,c=(iter<<32)|0
  0x18 CHECK   tag,a=observed,b=expected,c=(iter<<32)|path
"""
from __future__ import annotations

import bisect
import collections
import csv
import gzip
import io
import json
import os
import re
import subprocess
import zlib
from pathlib import Path

EXT = Path(os.environ.get("LSU_E2E_ROOT", str(Path(__file__).resolve().parents[1])))
ROOT = Path(os.environ.get("LSU_WORKSPACE_ROOT", str(EXT.parent)))
FROZEN = ROOT
FAMILY = {
    "A01": "agu", "A03": "agu", "LQ04": "lq",
    "SQ01": "sq", "SQ03": "sq", "SP05": "sq",
    "FW02": "fwd_full", "FW05": "fwd_partial",
    "MD04": "md", "RP01": "md", "DA04": "align", "LP01": "lp",
}

T_LOAD, T_STORE, T_HASH, T_BRANCH = 0x11, 0x12, 0x13, 0x14
T_OUTPUT, T_PHASE, T_VALUE, T_CHECK = 0x15, 0x16, 0x17, 0x18
TYPE_NAME = {
    T_LOAD: "LOAD", T_STORE: "STORE", T_HASH: "HASH", T_BRANCH: "BRANCH",
    T_OUTPUT: "OUTPUT", T_PHASE: "PHASE", T_VALUE: "VALUE",
    T_CHECK: "CHECK",
}
MEM_TYPES = {T_LOAD, T_STORE}
AUX_ITER_TYPES = {T_LOAD, T_STORE, T_BRANCH, T_VALUE, T_CHECK}

LOAD_OPS = ("ldr", "ldur", "ldrb", "ldrh", "ldrsb", "ldrsh", "ldrsw",
            "ldp", "ldpsw", "ldar", "ldaxr", "ldxr")
STORE_OPS = ("str", "stur", "strb", "strh", "stp", "stlr", "stlxr",
             "stxr", "cas", "swp", "st1")


def gz_lines(path: Path | str):
    """Yield text lines from a gzip file, including a truncated stream."""
    data = Path(path).read_bytes()
    d = zlib.decompressobj(31)
    try:
        out = d.decompress(data)
    except zlib.error:
        out = b""
    if not out:
        # fall back to gzip (some producers omit the zlib header path)
        try:
            out = gzip.decompress(data)
        except OSError:
            out = b""
    for raw in out.splitlines():
        yield raw.decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# commit trace
# ---------------------------------------------------------------------------
class Marker:
    __slots__ = ("seq", "tag", "type", "site", "order", "a", "b", "c",
                 "line", "idx")

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

    def as_dict(self):
        return {"dyn_inst_seq": self.seq, "type": TYPE_NAME.get(self.type,
                hex(self.type)), "site": self.site,
                "event_seq": self.order, "a": self.a, "b": self.b,
                "c": self.c, "ctrace_line": self.line}


class CommitTrace:
    def __init__(self, path: Path | str):
        self.path = str(path)
        self.seq = []
        self.tick = []
        self.pc = []
        self.op = []
        self.dst = []      # [(class, arch, phys, value)]
        self.src = []      # [(class, arch, phys)]
        self.srcv = []     # [(class, arch, phys, value_at_commit)]
        self.line = []
        self.squash = set()
        self.squash_tick = {}
        self.markers = []
        self._parse()

    def _parse(self):
        seq, tick, pc, op, dst, src, srcv, lines = (
            self.seq, self.tick, self.pc, self.op, self.dst, self.src,
            self.srcv, self.line)
        regval = {}
        mseq, mtag, mvals, mline = [], [], [], []
        ln = 0
        for text in gz_lines(self.path):
            ln += 1
            if text.startswith("# squash"):
                p = text.split()
                if len(p) >= 3:
                    s = int(p[2])
                    self.squash.add(s)
                    self.squash_tick[s] = int(p[3]) if len(p) > 3 else 0
                mseq.clear(); mtag.clear(); mvals.clear(); mline.clear()
                continue
            if text.startswith("#"):
                continue
            a = text.split(",")
            if len(a) < 7:
                continue
            try:
                e = int(a[1]); t = int(a[3]); paddr = int(a[4], 16)
                o = a[5]; nd = int(a[6])
            except (ValueError, IndexError):
                continue
            i = 7
            ds = []
            for _ in range(nd):
                try:
                    c = int(a[i]); ar = int(a[i+1]); ph = int(a[i+2])
                    v = int(a[i+3], 16)
                except (ValueError, IndexError):
                    ds = []
                    i = len(a)
                    break
                ds.append((c, ar, ph, v))
                i += 4
            ss = []
            try:
                ns = int(a[i]); i += 1
                for _ in range(ns):
                    c = int(a[i]); ar = int(a[i+1]); ph = int(a[i+2])
                    ss.append((c, ar, ph))
                    i += 3
            except (ValueError, IndexError):
                ss = []
            sv = [(c, ar, ph, regval.get((c, ph))) for (c, ar, ph) in ss]
            for (c, ar, ph, v) in ds:
                regval[(c, ph)] = v
            seq.append(e); tick.append(t); pc.append(paddr); op.append(o)
            dst.append(ds); src.append(ss); srcv.append(sv); lines.append(ln)
            # marker grouping: four consecutive single-dest x28 ALU rows
            if (nd == 1 and ds[0][1] == 28
                    and o.startswith(("mov", "orr", "add"))):
                mseq.append(e); mtag.append(ds[0][3]); mvals.append(ds[0][3])
                mline.append(ln)
                if len(mseq) == 4:
                    tag = mvals[0]
                    self.markers.append(Marker(
                        seq=mseq[3], tag=tag, type=tag >> 56,
                        site=(tag >> 32) & 0xffffff,
                        order=tag & 0xffffffff,
                        a=mvals[1], b=mvals[2], c=mvals[3], line=mline[3],
                        idx=len(seq) - 1))
                    mseq.clear(); mtag.clear(); mvals.clear(); mline.clear()
            else:
                mseq.clear(); mtag.clear(); mvals.clear(); mline.clear()

    def __len__(self):
        return len(self.seq)

    def index_of(self, dyn_seq: int) -> int | None:
        i = bisect.bisect_left(self.seq, dyn_seq)
        if i < len(self.seq) and self.seq[i] == dyn_seq:
            return i
        return None

    def commit_row(self, dyn_seq: int):
        i = self.index_of(dyn_seq)
        if i is None:
            return None
        return {"seq": self.seq[i], "tick": self.tick[i], "pc": self.pc[i],
                "op": self.op[i], "dst": self.dst[i], "src": self.src[i],
                "line": self.line[i]}

    def dest_values(self, dyn_seq: int):
        r = self.commit_row(dyn_seq)
        return [d[3] for d in r["dst"]] if r else []


def is_load(op: str) -> bool:
    return op.startswith(LOAD_OPS)


def is_store(op: str) -> bool:
    return op.startswith(STORE_OPS)


# ---------------------------------------------------------------------------
# marker <-> dynamic instruction mapping
# ---------------------------------------------------------------------------
_CATALOG = None


def site_catalog():
    global _CATALOG
    if _CATALOG is None:
        p = Path(__file__).resolve().parent / "e2e_site_catalog.json"
        _CATALOG = json.loads(p.read_text()) if p.exists() else {}
    return _CATALOG


def map_marker_ops_catalog(ct: CommitTrace, markers: list[Marker],
                           family: str) -> list[int | None]:
    """Map markers by validated site->PC identity from the control census.

    Fault runs may corrupt the value, so identity comes from the PC.  Any
    marker without a catalog entry falls back to the value/group mapper.
    """
    cat = site_catalog().get(family, {})
    ops = map_marker_ops(ct, markers)
    for mi, m in enumerate(markers):
        if m.type != T_LOAD:
            continue
        ent = cat.get(f"{m.type}:{m.site}")
        if not ent:
            continue
        pcs = {e["pc"] for e in ent}
        i = bisect.bisect_left(ct.seq, m.seq) - 1
        scanned = 0
        while i >= 0 and scanned < 600:
            if ct.pc[i] in pcs:
                if ((m.type == T_LOAD and is_load(ct.op[i])) or
                        (m.type == T_STORE and is_store(ct.op[i]))):
                    ops[mi] = ct.seq[i]
                    break
            i -= 1
            scanned += 1
    return ops


def map_marker_ops(ct: CommitTrace, markers: list[Marker]) -> list[int | None]:
    """Return the dynamic instruction identity of each marker's operation.

    LOAD markers immediately follow their load: take the nearest preceding
    load and verify the recorded value is one of its destinations.
    STORE markers are emitted as a consecutive group after the dependent
    load: pair the group in program order with the last K store commits.
    """
    ops: list[int | None] = [None] * len(markers)
    seqs = ct.seq

    # LOAD groups: the compiler may schedule a whole straight-line load run
    # before the marker block.  Pair the group in program order with the last
    # K load commits; a single 16-byte load can carry two marker events.
    i = 0
    while i < len(markers):
        if markers[i].type != T_LOAD:
            i += 1
            continue
        j = i
        while j < len(markers) and markers[j].type == T_LOAD:
            j += 1
        run = markers[i:j]
        anchor = run[0].seq
        k = bisect.bisect_left(seqs, anchor) - 1
        loads = []
        scanned = 0
        while k >= 0 and scanned < 400 and len(loads) < len(run) + 4:
            if is_load(ct.op[k]):
                loads.append(k)
            k -= 1
            scanned += 1
        loads = loads[::-1]  # program order
        assigned = False
        if (len(run) == 2 and loads
                and len(ct.dst[loads[-1]]) >= 2
                and ct.dst[loads[-1]][0][1] != 28):
            # one 16-byte load, two 64-bit marker events
            s = ct.seq[loads[-1]]
            ops[i] = s
            ops[i + 1] = s
            assigned = True
        elif len(loads) >= len(run):
            cand = loads[-len(run):]
            ok = True
            for qi, m in enumerate(run):
                vals = [d[3] for d in ct.dst[cand[qi]]]
                if not any(v == m.b or (v & 0xffffffff) == (m.b & 0xffffffff)
                           for v in vals):
                    ok = False
            if ok:
                for qi in range(len(run)):
                    ops[i + qi] = ct.seq[cand[qi]]
                assigned = True
        if not assigned:
            # fall back to nearest-value search per marker
            for qi, m in enumerate(run):
                kk = bisect.bisect_left(seqs, m.seq) - 1
                fallback = None
                scanned = 0
                while kk >= 0 and scanned < 400:
                    if is_load(ct.op[kk]):
                        vals = [d[3] for d in ct.dst[kk]]
                        if fallback is None:
                            fallback = ct.seq[kk]
                        if any(v == m.b or
                               (v & 0xffffffff) == (m.b & 0xffffffff)
                               for v in vals):
                            ops[i + qi] = ct.seq[kk]
                            break
                    kk -= 1
                    scanned += 1
                if ops[i + qi] is None:
                    ops[i + qi] = fallback
        i = j

    i = 0
    while i < len(markers):
        if markers[i].type != T_STORE:
            i += 1
            continue
        j = i
        while j < len(markers) and markers[j].type == T_STORE:
            j += 1
        run = markers[i:j]
        anchor = run[0].seq
        k = bisect.bisect_left(seqs, anchor) - 1
        cand = []
        scanned = 0
        while k >= 0 and scanned < 400 and len(cand) < len(run) * 2 + 8:
            if is_store(ct.op[k]):
                cand.append(k)
            k -= 1
            scanned += 1
        cand = cand[::-1]  # program order
        # value-guided assignment, then order fallback
        used = set()
        for qi, m in enumerate(run):
            pick = None
            for ci in range(len(cand) - 1, -1, -1):
                if ci in used:
                    continue
                vals = [v for (_, _, _, v) in ct.srcv[cand[ci]] if v is not None]
                if any(v == m.b or (v & 0xffffffff) == (m.b & 0xffffffff)
                       for v in vals):
                    pick = ci
                    break
            if pick is None:
                for ci in range(len(cand) - 1, -1, -1):
                    if ci not in used:
                        pick = ci
                        break
            if pick is not None:
                used.add(pick)
                ops[i + qi] = ct.seq[cand[pick]]
        i = j
    return ops


# ---------------------------------------------------------------------------
# software event log and control/fault alignment
# ---------------------------------------------------------------------------
class SWEvent:
    __slots__ = ("marker", "op_seq", "key", "occurrence", "order_index")

    def __init__(self, marker, op_seq, key, occurrence, order_index):
        self.marker = marker
        self.op_seq = op_seq
        self.key = key
        self.occurrence = occurrence
        self.order_index = order_index

    @property
    def ident(self):
        return (self.marker.type, self.marker.site, self.marker.order)


def event_key(m: Marker):
    if m.type in AUX_ITER_TYPES:
        return (m.type, m.site, m.c >> 32)
    return (m.type, m.site)


def build_sw_events(ct: CommitTrace, family: str | None = None):
    ops = (map_marker_ops_catalog(ct, ct.markers, family) if family
           else map_marker_ops(ct, ct.markers))
    cnt = collections.Counter()
    out = []
    for i, m in enumerate(ct.markers):
        k = event_key(m)
        n = cnt[k]
        cnt[k] += 1
        out.append(SWEvent(m, ops[i], k, n, i))
    return out


def sw_event_index(events):
    return {(e.key, e.occurrence): e for e in events}


def load_ctrl_events(model: str, context: str):
    p = (EXT / "results/controls" / f"E2E-{model}-{context}-CTRL" /
         "attempt_1/sw_events.json")
    d = json.loads(p.read_text())
    out = []
    for i, e in enumerate(d["events"]):
        m = Marker(seq=e["seq"], tag=0, type=e["type"], site=e["site"],
                   order=e["order"], a=e["a"], b=e["b"], c=e["c"],
                   line=e["line"], idx=i)
        out.append(SWEvent(m, e["op_seq"], tuple(e["key"]), e["occ"], i))
    return d, out


def marker_for_op(events, op_seq, types=None):
    for e in events:
        if e.op_seq == op_seq and (types is None or e.marker.type in types):
            return e
    return None


def next_event(events, marker_seq, types=None):
    for e in events:
        if e.marker.seq > marker_seq and (types is None or
                                          e.marker.type in types):
            return e
    return None


def is_marker_commit(ct: CommitTrace, idx: int) -> bool:
    return any(d[1] == 28 for d in ct.dst[idx])


def all_sw_diffs(fault_events, ctrl_events):
    cmap = sw_event_index(ctrl_events)
    out = []
    for e in fault_events:
        c = cmap.get((e.key, e.occurrence))
        if c is None:
            out.append({"kind": "event_missing_in_control", "fault": e,
                        "control": None, "fields": ["event"]})
            continue
        fields = []
        if e.marker.a != c.marker.a:
            fields.append("a")
        if e.marker.b != c.marker.b:
            fields.append("b")
        if e.marker.c != c.marker.c:
            fields.append("c")
        if fields:
            out.append({"kind": "value", "fault": e, "control": c,
                        "fields": fields})
    fmap = sw_event_index(fault_events)
    for c in ctrl_events:
        if (c.key, c.occurrence) not in fmap:
            out.append({"kind": "event_missing_in_fault", "fault": None,
                        "control": c, "fields": ["event"]})
    return out


def first_sw_diff(fault_events, ctrl_events):
    """First committed software-event value divergence.

    Returns dict(kind, fault, control, fields).  The event order is the
    commit order of the fault run.  Events absent from the control are a
    control-flow divergence.
    """
    cmap = sw_event_index(ctrl_events)
    for e in fault_events:
        c = cmap.get((e.key, e.occurrence))
        if c is None:
            return {"kind": "event_missing_in_control", "fault": e,
                    "control": None, "fields": ["event"]}
        fields = []
        if e.marker.a != c.marker.a:
            fields.append("a")
        if e.marker.b != c.marker.b:
            fields.append("b")
        if e.marker.c != c.marker.c:
            fields.append("c")
        if fields:
            return {"kind": "value", "fault": e, "control": c,
                    "fields": fields}
    # control events with no fault counterpart
    fmap = sw_event_index(fault_events)
    for c in ctrl_events:
        if (c.key, c.occurrence) not in fmap:
            return {"kind": "event_missing_in_fault", "fault": None,
                    "control": c, "fields": ["event"]}
    return None


# ---------------------------------------------------------------------------
# propagation trace
# ---------------------------------------------------------------------------
def parse_prop(path: Path | str):
    rows = []
    for text in gz_lines(path):
        if text.startswith("#"):
            continue
        r = next(csv.reader([text]))
        if len(r) < 10:
            continue
        d = dict(zip(("node_id", "tick", "ptag", "kind", "dyn_inst_seq",
                      "request_id", "addr", "phys_reg", "arch_reg",
                      "detail"), r))
        d["kv"] = dict(re.findall(r"([A-Za-z0-9_]+)=([^;]*)", d["detail"]))
        try:
            d["seq_int"] = int(d["dyn_inst_seq"]) if d["dyn_inst_seq"] else None
            d["tick_int"] = int(d["tick"]) if d["tick"] else None
        except ValueError:
            d["seq_int"] = d["tick_int"] = None
        rows.append(d)
    return rows


def prop_by_kind(rows, *kinds):
    return [r for r in rows if r["kind"] in kinds]


def prop_for_seq(rows, seq):
    return [r for r in rows if r["seq_int"] == seq]


# ---------------------------------------------------------------------------
# micro snapshots / stats
# ---------------------------------------------------------------------------
def micro_snapshots(path: Path | str):
    out = []
    if not Path(path).exists():
        return out
    for text in gz_lines(path):
        if text.startswith("#") or not text.strip():
            continue
        a = text.split(",")
        if len(a) < 9:
            continue
        try:
            out.append({"snap_seq": int(a[0]), "commit_seq": int(a[1]),
                        "tick": int(a[2]), "rob_occ": int(a[3]),
                        "iq_occ": int(a[4]), "fl_int": int(a[5]),
                        "fl_fp": int(a[6]), "fl_vec": int(a[7]),
                        "rob_head": int(a[8]), "rob_tail": int(a[9])})
        except ValueError:
            continue
    return out


def stats_values(path: Path | str):
    vals = {}
    if not Path(path).exists():
        return vals
    for line in open(path, errors="replace"):
        m = re.match(r"^(\S+)\s+([0-9.]+)\s", line)
        if m:
            vals[m.group(1)] = m.group(2)
    return vals


# ---------------------------------------------------------------------------
# misc
# ---------------------------------------------------------------------------
def hexv(v):
    if v is None:
        return None
    try:
        return "0x%x" % int(v)
    except (TypeError, ValueError):
        return str(v)


def kv_int(kv, *keys):
    for k in keys:
        if k in kv:
            try:
                return int(str(kv[k]), 0)
            except ValueError:
                continue
    return None


def load_state(run_id: str, kind: str = "fault"):
    d = "faults" if kind == "fault" else "controls"
    p = EXT / "results" / d / run_id / "attempt_1"
    sp = EXT / "results/state" / f"{run_id}.json"
    st = json.loads(sp.read_text()) if sp.exists() else {}
    return st, p


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
