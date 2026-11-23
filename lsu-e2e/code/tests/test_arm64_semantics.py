#!/usr/bin/env python3
"""Independent ARM64 semantics and SemanticWalk regression tests.

Expected values below are hand-computed from the ARM64 encoding rules (or
from a deliberately different expression), never by calling the function
under test with the same implementation.
"""
from __future__ import annotations

import gzip
import sys
from pathlib import Path

import pytest

EXT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXT / "runner"))
import e2e_strict_data as D
import e2e_strict_engine as E


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
class FakeDisasm:
    def __init__(self, table=None):
        self.table = table or {}

    def get(self, pc):
        return self.table.get(pc)


class FakeMem:
    def __init__(self, mem=None):
        self.mem = dict(mem or {})

    def _read(self, addr, width):
        v = 0
        for i in range(width):
            v |= self.mem.get((addr + i) & D.MASK64, 0) << (8 * i)
        return v


def _row(seq, pc, op, dsts=(), srcs=(), tid=0, tick=None):
    parts = [str(seq), str(seq), str(tid),
             str(tick if tick is not None else seq), "%x" % pc, op,
             str(len(dsts))]
    for c, a, p, v in dsts:
        parts += [str(c), str(a), str(p), "%016x" % (v & D.MASK64)]
    parts.append(str(len(srcs)))
    for s in srcs:
        parts += [str(s[0]), str(s[1]), str(s[2])]
    return ",".join(parts)


class Builder:
    def __init__(self):
        self.rows = []
        self.dis = {}
        self.seq = 1
        self.pc = 0x1000
        self.phys = 1000

    def np(self):
        self.phys += 1
        return self.phys

    def add(self, op, disasm, dsts=(), srcs=(), tid=0):
        pc = self.pc
        self.pc += 4
        self.rows.append(_row(self.seq, pc, op, dsts, srcs, tid))
        self.dis[pc] = disasm
        self.seq += 1
        return pc

    def trace(self, tmp_path, name="ct.gz"):
        p = tmp_path / name
        with gzip.open(p, "wt") as f:
            f.write("# ctrace v2 seq,seqencNum,tid,tick,pc,op,ndest"
                    "[,class,arch,phys,val]*,nsrc[,class,arch,phys]*\n")
            for r in self.rows:
                f.write(r + "\n")
        return D.StrictTrace(p)


def walk_from(b, tmp_path, seeds, seed_idx=0, byte_seeds=None,
              name="ct.gz"):
    t = b.trace(tmp_path, name)
    return E.SemanticWalk(t, FakeDisasm(b.dis), FakeMem(), seeds, seed_idx,
                          byte_seeds=byte_seeds, run_id="SYN")


def cc_dsts(nz, c, v, base=500):
    return [(6, 0, base, nz), (6, 1, base + 1, c), (6, 2, base + 2, v)]


def cc_srcs(base=500):
    return [(6, 0, base), (6, 1, base + 1), (6, 2, base + 2)]


# ---------------------------------------------------------------------------
# 1. shifted register / immediate operands
# ---------------------------------------------------------------------------
def test_required_shifted_examples():
    outs, _ = D.evaluate("eor", "w4, w4, w4, lsr #13", {4: 0xbe1e0817})
    assert outs[0] == 0xbe1bf8e7
    outs, _ = D.evaluate("add", "x1, x11, x2, lsl #3",
                         {11: 0x420000, 2: 0x14})
    assert outs[0] == 0x4200a0
    outs, _ = D.evaluate("eor", "x1, x10, x10, lsr #30",
                         {10: 0x886f9ec00e614dc})
    assert outs[0] == 0x886f9ec22fdf36c
    outs, _ = D.evaluate("eor", "x1, x1, x1, lsr #27",
                         {1: 0xe70160bb1074850c})
    expected = 0xe70160bb1074850c ^ (0xe70160bb1074850c >> 27)
    assert outs[0] == expected


def test_logical_shifted_forms():
    # Independent expression: operate on the 32-bit low halves only.
    a, b = 0xf0f0f0f0, 0x0f0f0f0f
    masked = (b << 4) & 0xffffffff
    assert D.evaluate("and", "w0, w1, w2, lsl #4",
                      {1: a, 2: b})[0][0] == a & masked
    assert D.evaluate("orr", "w0, w1, w2, lsr #4",
                      {1: a, 2: b})[0][0] == a | (b >> 4)
    assert D.evaluate("eor", "x0, x1, x2, ror #8",
                      {1: 0x1122334455667788, 2: 0x99aabbccddeeff00})[0][0] \
        == 0x1122334455667788 ^ 0x0099aabbccddeeff
    assert D.evaluate("bic", "x0, x1, x2, lsl #1",
                      {1: 0xffff, 2: 1})[0][0] == 0xffff & ~2
    assert D.evaluate("orn", "w0, w1, w2, lsl #1",
                      {1: 0, 2: 1})[0][0] == 0xfffffffd
    assert D.evaluate("eon", "x0, x1, x2, lsr #1",
                      {1: 0, 2: 1})[0][0] == 0xffffffffffffffff


def test_sub_shifted_register_and_shifted_immediate():
    assert D.evaluate("sub", "x0, x1, x2, lsl #3",
                      {1: 0x100, 2: 3})[0][0] == 0x100 - 24
    assert D.evaluate("subs", "w0, w1, w2, lsl #2",
                      {1: 0x100, 2: 3})[0][0] == 0x100 - 12
    # ADD/SUB immediate permits only LSL #0 or #12.
    assert D.evaluate("sub", "w14, w13, #0x1b2, lsl #12",
                      {13: 0x500000})[0][0] == 0x500000 - 0x1b2000
    assert D.evaluate("cmp", "x1, #0x2, lsl #12", {1: 0x2000})[1]["Z"] == 1


def test_w32_shift_semantics_and_zero_extension():
    assert D.evaluate("lsl", "w0, w1, #31", {1: 1})[0][0] == 0x80000000
    assert D.evaluate("lsr", "w0, w1, #31", {1: 0x80000000})[0][0] == 1
    assert D.evaluate("asr", "w0, w1, #1", {1: 0x80000000})[0][0] == 0xc0000000
    assert D.evaluate("ror", "w0, w1, #1", {1: 1})[0][0] == 0x80000000
    # upper 32 bits of the source must not leak into a W operation
    assert D.evaluate("add", "w0, w1, w2, lsl #1",
                      {1: 0xffffffff00000001, 2: 1})[0][0] == 3


def test_x64_shift_semantics():
    assert D.evaluate("lsl", "x0, x1, #63", {1: 1})[0][0] == 1 << 63
    assert D.evaluate("lsr", "x0, x1, #63", {1: 1 << 63})[0][0] == 1
    assert D.evaluate("asr", "x0, x1, #63",
                      {1: 0x8000000000000000})[0][0] == 0xffffffffffffffff
    assert D.evaluate("ror", "x0, x1, #1", {1: 1})[0][0] == 1 << 63


def test_illegal_immediate_shift_rejected():
    for mn, ops in (("lsl", "w0, w1, #32"), ("lsl", "x0, x1, #64"),
                    ("lsr", "w0, w1, #32"), ("add", "x0, x1, x2, lsl #64"),
                    ("ror", "x0, x1, #64")):
        with pytest.raises(D.SemanticsError):
            D.evaluate(mn, ops, {1: 1, 2: 1})


def test_extend_register_operands():
    assert D.evaluate("add", "x0, x1, w2, uxtw #2",
                      {1: 0x100, 2: 0xffffffff})[0][0] == 0x100 + (0xffffffff << 2)
    assert D.evaluate("add", "x0, x1, w2, sxtw",
                      {1: 0, 2: 0xffffffff})[0][0] == 0xffffffffffffffff
    assert D.evaluate("and", "x0, x1, w2, uxtb",
                      {1: 0xff, 2: 0x1ff})[0][0] == 0xff
    assert D.evaluate("add", "x0, x1, w2, sxth",
                      {1: 0, 2: 0x8000})[0][0] == 0xffffffffffff8000
    with pytest.raises(D.SemanticsError):
        D.evaluate("add", "x0, x1, x2, lsl #1, lsl #2", {1: 1, 2: 1})


# ---------------------------------------------------------------------------
# 2. NZCV
# ---------------------------------------------------------------------------
def test_nzcv_32_and_64_add_sub():
    outs, f = D.evaluate("adds", "w0, w1, w2", {1: 0x7fffffff, 2: 1})
    assert outs[0] == 0x80000000
    assert f == {"N": 1, "Z": 0, "C": 0, "V": 1}
    outs, f = D.evaluate("adds", "x0, x1, x2",
                         {1: 0xffffffffffffffff, 2: 1})
    assert outs[0] == 0
    assert f == {"N": 0, "Z": 1, "C": 1, "V": 0}
    outs, f = D.evaluate("subs", "w0, w1, w2", {1: 0, 2: 1})
    assert outs[0] == 0xffffffff
    assert f == {"N": 1, "Z": 0, "C": 0, "V": 0}
    outs, f = D.evaluate("subs", "x0, x1, x2",
                         {1: 0x8000000000000000, 2: 1})
    assert f == {"N": 0, "Z": 0, "C": 1, "V": 1}


def test_nzcv_cmp_cmn_borrow_carry_zero_negative():
    _, f = D.evaluate("cmp", "x1, x2", {1: 5, 2: 5})
    assert f == {"N": 0, "Z": 1, "C": 1, "V": 0}
    _, f = D.evaluate("cmp", "x1, x2", {1: 4, 2: 5})
    assert f == {"N": 1, "Z": 0, "C": 0, "V": 0}
    _, f = D.evaluate("cmn", "x1, x2", {1: 1, 2: 2})
    assert f == {"N": 0, "Z": 0, "C": 0, "V": 0}
    _, f = D.evaluate("cmn", "x1, x2", {1: 0x7fffffffffffffff, 2: 1})
    assert f == {"N": 1, "Z": 0, "C": 0, "V": 1}


def test_logical_flag_producers():
    _, f = D.evaluate("ands", "w0, w1, w2", {1: 0, 2: 0xffffffff})
    assert f == {"N": 0, "Z": 1, "C": 0, "V": 0}
    _, f = D.evaluate("bics", "x0, x1, x2",
                      {1: 1 << 63, 2: 0})
    assert f["N"] == 1 and f["Z"] == 0 and f["C"] == 0 and f["V"] == 0


def test_conditional_operand_selection_with_real_flags():
    eq = {"N": 0, "Z": 1, "C": 1, "V": 0}
    ne = {"N": 0, "Z": 0, "C": 1, "V": 0}
    assert D.evaluate("cinc", "x10, x10, eq", {10: 5}, eq)[0][0] == 6
    assert D.evaluate("cinc", "x10, x10, eq", {10: 5}, ne)[0][0] == 5
    assert D.evaluate("cinc", "w10, w10, ne", {10: 5}, ne)[0][0] == 6
    assert D.evaluate("csel", "x0, x1, x2, eq",
                      {1: 0xa, 2: 0xb}, eq)[0][0] == 0xa
    assert D.evaluate("csinc", "x0, x1, x2, ne",
                      {1: 0xa, 2: 0xb}, ne)[0][0] == 0xa
    assert D.evaluate("csinv", "x0, x1, x2, ne",
                      {1: 0xa, 2: 0xb}, eq)[0][0] == 0xfffffffffffffff4
    assert D.evaluate("csneg", "w0, w1, w2, eq",
                      {1: 0xa, 2: 0xb}, ne)[0][0] == 0xfffffff5
    # cset/csetm aliases observed in the C02 workloads
    assert D.evaluate("cset", "w3, eq", {}, eq)[0][0] == 1
    assert D.evaluate("cset", "w3, eq", {}, ne)[0][0] == 0
    assert D.evaluate("csetm", "x3, ne", {}, ne)[0][0] == D.MASK64
    assert D.evaluate("csetm", "x3, ne", {}, eq)[0][0] == 0


# ---------------------------------------------------------------------------
# 3. STP/LDP encoding and memory
# ---------------------------------------------------------------------------
def test_pair_memory_addressing_forms():
    sp = 42
    r = D.pair_memory_layout("stp", "x0, x1, [sp, #96]", {sp: 0x1000})
    assert (r[0], r[1]) == (0x1060, 8)
    r = D.pair_memory_layout("stp", "x0, x1, [sp, #-48]!", {sp: 0x1000})
    assert r[0] == 0xfd0 and r[1] == 8 and r[3][1] == 0xfd0
    r = D.pair_memory_layout("ldp", "x0, x1, [sp], #48", {sp: 0x1000})
    assert r[0] == 0x1000 and r[3][1] == 0x1030
    r = D.pair_memory_layout("stp", "w0, w1, [sp, #8]", {sp: 0x1000})
    assert (r[0], r[1]) == (0x1008, 4)
    aw = D.memory_address("stp", "x0, x1, [sp, #96]", {sp: 0x1000})
    assert (aw[0], aw[1]) == (0x1060, 16)


def test_stp_supported_and_ldp_from_memory_model():
    assert D.evaluate("stp", "x0, x1, [sp, #96]",
                      {42: 0x1000, 0: 1, 1: 2})[0] == []
    mem = {0x1000 + i: (i + 1) for i in range(16)}
    outs, _ = D.evaluate("ldp", "x0, x1, [sp]",
                         {42: 0x1000, 0: 0x123456789abcdef0,
                          1: 0xfedcba9876543210}, memory=mem)
    assert outs[0] == int.from_bytes(
        bytes(mem[0x1000 + i] for i in range(8)), "little")
    assert outs[1] == int.from_bytes(
        bytes(mem[0x1008 + i] for i in range(8)), "little")


def test_stp_untainted_second_element_does_not_inherit_first(tmp_path):
    b = Builder()
    b.add("mov", ("mov", "x0, #0x5"), dsts=[(0, 0, 100, 5)])
    b.add("add", ("add", "x35, sp, #0x96"),
          dsts=[(0, 35, 200, 0x1000)])
    b.add("strxi_uop", ("stp", "x0, x1, [sp, #96]"),
          srcs=[(0, 35, 200), (0, 0, 100)])
    b.add("strxi_uop", ("stp", "x0, x1, [sp, #96]"),
          srcs=[(0, 35, 200), (0, 1, 101)])
    b.add("add", ("add", "x36, sp, #0x96"),
          dsts=[(0, 36, 201, 0x1000)])
    b.add("ldp_uop", ("ldp", "x2, x3, [sp]"),
          dsts=[(0, 2, 300, 5), (0, 3, 301, 0x77)],
          srcs=[(0, 36, 201)])
    w = walk_from(b, tmp_path,
                  [(0, 100, 5, "h", "N", 1)])
    assert (0, 300) in w.tainted
    assert w.tainted[(0, 300)]["value"] == 5
    assert (0, 301) not in w.tainted
    assert any(e["consumer_seq"] == 6 and e["edge_kind"] == "memory"
               for e in w.edges)
    assert w.mismatched_semantics == 0
    assert w.unsupported == 0
    assert w.memory_semantics_incomplete == 0


def test_stp_both_elements_loaded_and_overwritten(tmp_path):
    b = Builder()
    b.add("mov", ("mov", "x0, #0x5"), dsts=[(0, 0, 100, 5)])
    b.add("mov", ("mov", "x1, #0x6"), dsts=[(0, 1, 101, 6)])
    b.add("add", ("add", "x35, sp, #0x60"),
          dsts=[(0, 35, 200, 0x1000)])
    b.add("strxi_uop", ("stp", "x0, x1, [sp, #96]"),
          srcs=[(0, 35, 200), (0, 0, 100)])
    b.add("strxi_uop", ("stp", "x0, x1, [sp, #96]"),
          srcs=[(0, 35, 200), (0, 1, 101)])
    b.add("add", ("add", "x36, sp, #0x60"),
          dsts=[(0, 36, 201, 0x1000)])
    b.add("ldp_uop", ("ldp", "x2, x3, [sp]"),
          dsts=[(0, 2, 300, 5), (0, 3, 301, 6)],
          srcs=[(0, 36, 201)])
    w = walk_from(b, tmp_path,
                  [(0, 100, 5, "h", "N", 1), (0, 101, 6, "h2", "N", 2)],
                  seed_idx=1)
    assert (0, 300) in w.tainted and (0, 301) in w.tainted
    assert w.tainted[(0, 300)]["value"] == 5
    assert w.tainted[(0, 301)]["value"] == 6
    assert w.mismatched_semantics == 0


def test_stack_spill_reload_pair_semantics(tmp_path):
    b = Builder()
    b.add("mov", ("mov", "x0, #0x1234"), dsts=[(0, 0, 100, 0x1234)])
    b.add("add", ("add", "x35, sp, #0xa0"),
          dsts=[(0, 35, 200, 0x2000)])
    b.add("strxi_uop", ("stp", "x0, x1, [sp, #160]"),
          srcs=[(0, 35, 200), (0, 0, 100)])
    b.add("strxi_uop", ("stp", "x0, x1, [sp, #160]"),
          srcs=[(0, 35, 200), (0, 1, 101)])
    b.add("add", ("add", "x36, sp, #0xa0"),
          dsts=[(0, 36, 201, 0x2000)])
    b.add("ldp_uop", ("ldp", "x4, x5, [sp]"),
          dsts=[(0, 4, 400, 0x1234), (0, 5, 401, 0)],
          srcs=[(0, 36, 201)])
    w = walk_from(b, tmp_path,
                  [(0, 100, 0x1234, "h", "N", 1)])
    assert w.tainted[(0, 400)]["value"] == 0x1234
    assert w.memory_semantics_incomplete == 0


# ---------------------------------------------------------------------------
# 4. SemanticWalk integration
# ---------------------------------------------------------------------------
def test_untainted_cmp_updates_flags_for_tainted_cinc(tmp_path):
    b = Builder()
    b.add("mov", ("mov", "x10, #0x5"), dsts=[(0, 10, 100, 5)])
    b.add("mov", ("mov", "x1, #0x5"), dsts=[(0, 1, 101, 5)])
    b.add("mov", ("mov", "x2, #0x5"), dsts=[(0, 2, 102, 5)])
    b.add("cmp", ("cmp", "x1, x2"),
          dsts=cc_dsts(1, 1, 0),
          srcs=[(0, 2, 102), (0, 1, 101)])
    b.add("cinc", ("cinc", "x10, x10, eq"),
          dsts=[(0, 10, 103, 6)],
          srcs=cc_srcs() + [(0, 10, 100), (0, 10, 100)])
    w = walk_from(b, tmp_path, [(0, 100, 5, "h", "N", 1)])
    assert w.mismatched_semantics == 0
    assert w.flag_semantic_mismatches == 0
    assert w.flags_by_thread[0] == {"N": 0, "Z": 1, "C": 1, "V": 0}
    assert w.tainted[(0, 103)]["value"] == 6
    assert any(e["consumer_seq"] == 5 for e in w.edges)


def test_cmp_ne_does_not_increment_cinc(tmp_path):
    b = Builder()
    b.add("mov", ("mov", "x10, #0x5"), dsts=[(0, 10, 100, 5)])
    b.add("mov", ("mov", "x1, #0x4"), dsts=[(0, 1, 101, 4)])
    b.add("mov", ("mov", "x2, #0x5"), dsts=[(0, 2, 102, 5)])
    b.add("cmp", ("cmp", "x1, x2"),
          dsts=cc_dsts(2, 0, 0),
          srcs=[(0, 2, 102), (0, 1, 101)])
    b.add("cinc", ("cinc", "x10, x10, eq"),
          dsts=[(0, 10, 103, 5)],
          srcs=cc_srcs() + [(0, 10, 100), (0, 10, 100)])
    w = walk_from(b, tmp_path, [(0, 100, 5, "h", "N", 1)])
    assert w.mismatched_semantics == 0
    assert w.tainted[(0, 103)]["value"] == 5


def test_tainted_cmp_creates_condition_control_dependency(tmp_path):
    b = Builder()
    b.add("mov", ("mov", "x1, #0x5"), dsts=[(0, 1, 100, 5)])
    b.add("mov", ("mov", "x2, #0x5"), dsts=[(0, 2, 101, 5)])
    b.add("mov", ("mov", "x4, #0xaa"), dsts=[(0, 4, 102, 0xaa)])
    b.add("mov", ("mov", "x5, #0xbb"), dsts=[(0, 5, 103, 0xbb)])
    b.add("cmp", ("cmp", "x1, x2"),
          dsts=cc_dsts(1, 1, 0),
          srcs=[(0, 2, 101), (0, 1, 100)])
    b.add("csel", ("csel", "x3, x4, x5, eq"),
          dsts=[(0, 3, 300, 0xaa)],
          srcs=cc_srcs() + [(0, 4, 102), (0, 5, 103)])
    w = walk_from(b, tmp_path,
                  [(0, 100, 5, "h", "N", 1), (0, 101, 5, "h2", "N", 2)],
                  seed_idx=1)
    assert w.mismatched_semantics == 0
    assert any(e["edge_kind"] == "condition" and e["consumer_seq"] == 6
               for e in w.edges)
    assert (0, 300) in w.tainted


def test_multiple_tainted_sources_keep_all_edges(tmp_path):
    b = Builder()
    b.add("mov", ("mov", "x1, #0x5"), dsts=[(0, 1, 100, 5)])
    b.add("mov", ("mov", "x2, #0x6"), dsts=[(0, 2, 101, 6)])
    b.add("add", ("add", "x3, x1, x2, lsl #1"),
          dsts=[(0, 3, 300, 17)],
          srcs=[(0, 1, 100), (0, 2, 101)])
    w = walk_from(b, tmp_path,
                  [(0, 100, 5, "h1", "N1", 1), (0, 101, 6, "h2", "N2", 2)],
                  seed_idx=1)
    cons = [e for e in w.edges if e["consumer_seq"] == 3]
    assert len(cons) == 2
    assert {tuple(e["source_phys"][0]) for e in cons} == {(0, 100), (0, 101)}
    assert w.tainted[(0, 300)]["nodes"] == {"N1", "N2"}
    assert w.multi_source_drops == 0


def test_phys_register_reuse_kills_stale_taint(tmp_path):
    b = Builder()
    b.add("mov", ("mov", "x1, #0x5"), dsts=[(0, 1, 100, 5)])
    # clean overwrite of the same physical register
    b.add("mov", ("mov", "x1, #0x9"), dsts=[(0, 1, 100, 9)])
    b.add("add", ("add", "x2, x1, #1"), dsts=[(0, 2, 300, 10)],
          srcs=[(0, 1, 100)])
    w = walk_from(b, tmp_path, [(0, 100, 5, "h", "N", 1)])
    assert (0, 300) not in w.tainted
    assert not any(e["consumer_seq"] == 3 for e in w.edges)


def test_thread_nzcv_isolation(tmp_path):
    b = Builder()
    b.add("mov", ("mov", "x10, #0x5"), dsts=[(0, 10, 100, 5)])
    b.add("mov", ("mov", "x1, #0x5"), dsts=[(0, 1, 101, 5)])
    b.add("mov", ("mov", "x2, #0x5"), dsts=[(0, 2, 102, 5)])
    # thread 0: equal -> Z=1
    b.add("cmp", ("cmp", "x1, x2"), dsts=cc_dsts(1, 1, 0),
          srcs=[(0, 2, 102), (0, 1, 101)], tid=0)
    # thread 1: not equal -> Z=0
    b.add("cmp", ("cmp", "x1, x2"), dsts=cc_dsts(2, 0, 0, base=510),
          srcs=[(0, 2, 102), (0, 1, 101)], tid=1)
    # thread 0 consumer has no CC sources: it must use thread 0's state
    b.add("cinc", ("cinc", "x10, x10, eq"),
          dsts=[(0, 10, 103, 6)], srcs=[(0, 10, 100)], tid=0)
    w = walk_from(b, tmp_path, [(0, 100, 5, "h", "N", 1)])
    assert w.mismatched_semantics == 0
    assert w.tainted[(0, 103)]["value"] == 6


def test_tainted_add_and_eor_shifted_are_verified(tmp_path):
    b = Builder()
    b.add("mov", ("mov", "x1, #0x420000"), dsts=[(0, 1, 100, 0x420000)])
    b.add("mov", ("mov", "x2, #0x14"), dsts=[(0, 2, 101, 0x14)])
    b.add("add", ("add", "x3, x1, x2, lsl #3"),
          dsts=[(0, 3, 300, 0x4200a0)],
          srcs=[(0, 1, 100), (0, 2, 101)])
    b.add("eor", ("eor", "x4, x3, x3, lsr #17"),
          dsts=[(0, 4, 301, 0x4200a0 ^ (0x4200a0 >> 17))],
          srcs=[(0, 3, 300), (0, 3, 300)])
    w = walk_from(b, tmp_path,
                  [(0, 100, 0x420000, "h1", "N1", 1),
                   (0, 101, 0x14, "h2", "N2", 2)], seed_idx=1)
    assert w.mismatched_semantics == 0
    assert w.tainted[(0, 300)]["value"] == 0x4200a0
    assert w.tainted[(0, 301)]["value"] == 0x4200a0 ^ (0x4200a0 >> 17)


# ---------------------------------------------------------------------------
# 5. COMPLETE must fail on unverified semantics
# ---------------------------------------------------------------------------
def _n(kind, eid):
    return {"event_id": eid, "kind": kind}


def _e(s, t, dep="d", level=E.DIRECT):
    return {"edge_id": "%s-%s" % (s, t), "source": s, "target": t,
            "dependency": dep, "evidence_level": level}


def _base_run():
    nodes = [_n("injection", "E1"), _n("application_output", "E2"),
             _n("final_expression", "E3"),
             _n("first_software_divergence", "E4")]
    edges = [_e("E1", "E2"), _e("E3", "E2"), _e("E1", "E4"),
             _e("E1", "E3")]
    return {
        "run_id": "SYN", "model": "A01", "terminal": "NON_SDC",
        "nodes": nodes, "edges": edges,
        "classification": {
            "software_symptom": "WRONG_OUTPUT",
            "propagation_termination": "COMMITTED_AND_PROPAGATED",
            "masking_evidence_complete": True,
        },
        "software": {
            "output_validation": {"verified": True},
            "hash_flow": {"unverified_links": 0,
                          "events_with_bad_provenance": 0},
            "application_validation": {"verified": True},
            "output": {"matches_control": True, "oracle_pass": True},
        },
        "semantic_walk": {
            "edge_count": 10, "semantic_mismatches": 0,
            "unsupported_critical": 0, "unsupported_noncritical": 0,
            "unverified_semantic_edges": 0,
            "nzcv": {"flag_semantic_mismatches": 0,
                     "conditional_unverified": 0},
            "memory": {"semantics_incomplete": 0},
            "multi_source": {"dropped_sources": 0},
        },
    }


def test_semantic_gate_accepts_fully_verified_run():
    run = _base_run()
    run["semantic_walk"]["revalidation_count"] = 10
    assert E.validate_end_to_end_graph(run) == []
    assert E.compute_status([], True, run=run) == "E2E_CAUSAL_COMPLETE"


@pytest.mark.parametrize("setter,needle", [
    (lambda s: s.__setitem__("semantic_mismatches", 1),
     "semantics:unresolved_mismatches"),
    (lambda s: s.__setitem__("unsupported_critical", 1),
     "semantics:unsupported_critical_instruction"),
    (lambda s: s.__setitem__("unverified_semantic_edges", 1),
     "semantics:unverified_taint_edges"),
    (lambda s: s["nzcv"].__setitem__("flag_semantic_mismatches", 1),
     "semantics:nzcv_mismatches"),
    (lambda s: s["nzcv"].__setitem__("conditional_unverified", 1),
     "semantics:conditional_flags_unverified"),
    (lambda s: s["memory"].__setitem__("semantics_incomplete", 1),
     "semantics:memory_incomplete"),
    (lambda s: s["multi_source"].__setitem__("dropped_sources", 1),
     "semantics:dropped_taint_sources"),
    (lambda s: s.__setitem__("edge_count", 0),
     "semantics:empty_taint_walk_for_propagated_fault"),
])
def test_complete_is_blocked_by_semantic_failure(setter, needle):
    run = _base_run()
    setter(run["semantic_walk"])
    gaps = E.validate_end_to_end_graph(run)
    assert any(g.startswith(needle) for g in gaps), gaps
    assert E.compute_status([], True, run=run) != "E2E_CAUSAL_COMPLETE"


def test_reachable_nodes_alone_do_not_override_semantics():
    run = _base_run()
    # Every strong edge is present; only the instruction semantics failed.
    run["semantic_walk"]["semantic_mismatches"] = 7
    assert E.validate_end_to_end_graph(run)
    assert E.compute_status([], True, run=run) == "E2E_CAUSAL_PARTIAL"


def test_tainted_cmp_changes_conditional_result(tmp_path):
    """A fault in CMP operands must change the real NZCV and the select."""
    def build(x1_val, x2_val, expect):
        b = Builder()
        b.add("mov", ("mov", "x1, #%d" % x1_val),
              dsts=[(0, 1, 100, x1_val)])
        b.add("mov", ("mov", "x2, #%d" % x2_val),
              dsts=[(0, 2, 101, x2_val)])
        b.add("mov", ("mov", "x4, #0xaa"), dsts=[(0, 4, 102, 0xaa)])
        b.add("mov", ("mov", "x5, #0xbb"), dsts=[(0, 5, 103, 0xbb)])
        # equal -> Z=1,C=1; unequal (x1>x2) -> Z=0,C=1
        nz = 1 if x1_val == x2_val else 0
        cc = 1
        b.add("cmp", ("cmp", "x1, x2"),
              dsts=cc_dsts(nz, cc, 0),
              srcs=[(0, 2, 101), (0, 1, 100)])
        b.add("csel", ("csel", "x3, x4, x5, eq"),
              dsts=[(0, 3, 300, expect)],
              srcs=cc_srcs() + [(0, 4, 102), (0, 5, 103)])
        return b

    wa = walk_from(build(5, 5, 0xaa), tmp_path,
                   [(0, 100, 5, "h1", "N1", 1)])
    wb = walk_from(build(6, 5, 0xbb), tmp_path,
                   [(0, 100, 6, "h1", "N1", 1)], name="ctb.gz")
    assert wa.tainted[(0, 300)]["value"] == 0xaa
    assert wb.tainted[(0, 300)]["value"] == 0xbb
    assert wa.mismatched_semantics == wb.mismatched_semantics == 0
    assert wa.flags_by_thread[0]["Z"] == 1
    assert wb.flags_by_thread[0]["Z"] == 0
