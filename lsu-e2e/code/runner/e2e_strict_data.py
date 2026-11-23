#!/usr/bin/env python3
"""Strict evidence data layer for the LSU E2E repair round.

Unlike ``e2e_lib.CommitTrace`` (which is optimised for marker extraction),
this parser keeps every committed instruction's real operand values at
commit time, the physical-register definition order, the exact marker
group instruction set, and a static instruction index from the workload
ELF.  Everything here is read-only over the recorded evidence.

No causal edge is created in this module: it only exposes facts.
"""
from __future__ import annotations

import bisect
import collections
import gzip
import re
import subprocess
import zlib
from dataclasses import dataclass, field
from pathlib import Path

EXT = Path(os.environ.get("LSU_E2E_ROOT", str(Path(__file__).resolve().parents[1])))
WORK = EXT / "workloads"

# Marker register reserved by the instrumented workloads (-ffixed-x28).
MARKER_ARCH = 28

T_LOAD, T_STORE, T_HASH, T_BRANCH = 0x11, 0x12, 0x13, 0x14
T_OUTPUT, T_PHASE, T_VALUE, T_CHECK = 0x15, 0x16, 0x17, 0x18
TYPE_NAME = {
    T_LOAD: "LOAD", T_STORE: "STORE", T_HASH: "HASH", T_BRANCH: "BRANCH",
    T_OUTPUT: "OUTPUT", T_PHASE: "PHASE", T_VALUE: "VALUE", T_CHECK: "CHECK",
}
AUX_ITER_TYPES = {T_LOAD, T_STORE, T_BRANCH, T_VALUE, T_CHECK}

MASK64 = (1 << 64) - 1


def gz_lines(path):
    """Yield text lines from a possibly truncated gzip stream."""
    data = Path(path).read_bytes()
    d = zlib.decompressobj(31)
    try:
        out = d.decompress(data)
    except zlib.error:
        out = b""
    if not out:
        try:
            out = gzip.decompress(data)
        except OSError:
            out = b""
    yield from out.decode("utf-8", "replace").splitlines()


@dataclass
class Insn:
    idx: int
    seq: int
    tick: int
    pc: int
    op: str
    dsts: list = field(default_factory=list)    # [(class,arch,phys,value)]
    srcs: list = field(default_factory=list)    # [(class,arch,phys)]
    srcvals: list = field(default_factory=list)  # value at commit or None
    line: int = 0
    tid: int = 0
    disasm: str = ""

    def dst_value(self, arch=None):
        for (c, a, p, v) in self.dsts:
            if arch is None or a == arch:
                return v
        return None

    def src_regs(self):
        return [(c, p) for (c, a, p) in self.srcs if p is not None and p >= 0]

    def value_of(self, cls, phys):
        """The committed value this instruction wrote to (cls, phys)."""
        for (c, _a, p, v) in self.dsts:
            if c == cls and p == phys:
                return v
        return None


def row_src_map(row):
    """architectural register index -> value at this instruction's commit."""
    out = {}
    for (_c, arch, p), val in zip(row.srcs, row.srcvals):
        if arch is not None and arch >= 0 and val is not None:
            out[arch] = val
    return out


def real_sources(row):
    """Renamed sources that are real architectural registers (not xzr)."""
    return [(c, a, p) for (c, a, p) in row.srcs
            if c is not None and c >= 0 and a is not None and a >= 0 and
            p is not None and p >= 0]


def copy_source(row, disasm):
    """Return (class, arch, phys) when row is a value-preserving copy.

    Only true aliases are accepted (``mov xD, xS``, ``orr xD, xS, xzr``,
    ``add xD, xS, #0``).  Anything that transforms the value is a real
    producing instruction and is returned as a terminal, never followed.
    """
    info = disasm.get(row.pc) if disasm else None
    if not info:
        return None
    mnem, operands = info
    mnem = mnem.lower()
    ops = split_ops(operands)
    srcs = real_sources(row)
    if mnem == "mov" and len(ops) == 2 and parse_reg(ops[1]) and \
            len(srcs) == 1:
        return srcs[0]
    if mnem == "orr" and len(ops) == 3 and len(srcs) == 1:
        third = ops[2].strip().lower()
        if third in ("xzr", "zr", "#0", "#0x0"):
            return srcs[0]
    if mnem in ("add", "adds") and len(ops) == 3 and len(srcs) == 1:
        if parse_imm(ops[2]) == 0:
            return srcs[0]
    return None


@dataclass
class MarkerGroup:
    start_idx: int
    seqs: list
    tag: int
    mtype: int
    site: int
    order: int
    vals: list              # (tag, a, b, c) destination values
    srcs: list              # per slot [(class, arch, phys)]
    srcvals: list           # per slot [value at commit]
    idxs: list
    lines: list

    def slot_source(self, slot):
        for (c, a, p), v in zip(self.srcs[slot], self.srcvals[slot]):
            if p is not None and p >= 0:
                return (c, p), v, a
        return None, None, None


class StrictTrace:
    """Committed-instruction stream with exact commit-time operand values."""

    def __init__(self, path):
        self.path = str(path)
        self.rows = []
        self.squash = set()
        self.squash_tick = {}
        self.markers = []
        self._parse()
        self._index()

    def _parse(self):
        regval = {}
        ln = 0
        for text in gz_lines(self.path):
            ln += 1
            if text.startswith("# squash"):
                p = text.split()
                if len(p) >= 3:
                    try:
                        s = int(p[2])
                        self.squash.add(s)
                        self.squash_tick[s] = int(p[3]) if len(p) > 3 else 0
                    except ValueError:
                        pass
                continue
            if text.startswith("#") or not text.strip():
                continue
            a = text.split(",")
            if len(a) < 7:
                continue
            try:
                seq = int(a[1]); tick = int(a[3]); pc = int(a[4], 16)
                tid = int(a[2]); op = a[5]; nd = int(a[6])
            except (ValueError, IndexError):
                continue
            i = 7
            dsts = []
            for _ in range(nd):
                try:
                    dsts.append((int(a[i]), int(a[i+1]), int(a[i+2]),
                                 int(a[i+3], 16)))
                except (ValueError, IndexError):
                    dsts = []
                    i = len(a)
                    break
                i += 4
            srcs = []
            try:
                ns = int(a[i]); i += 1
                for _ in range(ns):
                    srcs.append((int(a[i]), int(a[i+1]), int(a[i+2])))
                    i += 3
            except (ValueError, IndexError):
                srcs = []
            srcvals = [regval.get((c, p)) for (c, _a, p) in srcs]
            for (c, _a, p, v) in dsts:
                if p is not None and p >= 0:
                    regval[(c, p)] = v
            self.rows.append(Insn(len(self.rows), seq, tick, pc, op, dsts,
                                  srcs, srcvals, ln, tid, ""))

    def _index(self):
        # phys definition chain: (class,phys) -> [(idx, seq, value)]
        self.phys_defs = collections.defaultdict(list)
        # architectural definition chain: (class,arch) -> [(idx, seq, phys, val)]
        self.arch_defs = collections.defaultdict(list)
        for r in self.rows:
            for (c, a, p, v) in r.dsts:
                if p is None or p < 0:
                    continue
                self.phys_defs[(c, p)].append((r.idx, r.seq, v))
                if a is not None and a >= 0:
                    self.arch_defs[(c, a)].append((r.idx, r.seq, p, v))
        self._build_markers()

    def _build_markers(self):
        i = 0
        n = len(self.rows)
        while i < n:
            if not self._is_marker_row(self.rows[i]):
                i += 1
                continue
            j = i
            while j < n and self._is_marker_row(self.rows[j]):
                j += 1
            run = self.rows[i:j]
            if len(run) == 4:
                vals = tuple(r.dst_value(MARKER_ARCH) for r in run)
                tag = vals[0]
                self.markers.append(MarkerGroup(
                    start_idx=i, seqs=[r.seq for r in run], tag=tag,
                    mtype=(tag >> 56) & 0xff,
                    site=(tag >> 32) & 0xffffff,
                    order=tag & 0xffffffff,
                    vals=list(vals),
                    srcs=[[(c, a, p) for (c, a, p) in r.srcs]
                          for r in run],
                    srcvals=[list(r.srcvals) for r in run],
                    idxs=[r.idx for r in run],
                    lines=[r.line for r in run]))
            i = j

    @staticmethod
    def _is_marker_row(r):
        return any(d[1] == MARKER_ARCH for d in r.dsts)

    def __len__(self):
        return len(self.rows)

    def index_of_seq(self, seq):
        lo = bisect.bisect_left([r.seq for r in self.rows], seq)
        # rows are append-only and sorted by seqNum at commit
        if lo < len(self.rows) and self.rows[lo].seq == seq:
            return lo
        return None

    def row_of_seq(self, seq):
        i = self.index_of_seq(seq)
        return self.rows[i] if i is not None else None

    def conforms(self):
        seqs = [r.seq for r in self.rows]
        return all(a < b for a, b in zip(seqs, seqs[1:]))

    def defining_insn(self, cls, phys, before_idx):
        """The last committed writer of (cls, phys) before before_idx."""
        defs = self.phys_defs.get((cls, phys), [])
        lo, hi = 0, len(defs)
        while lo < hi:
            mid = (lo + hi) // 2
            if defs[mid][0] < before_idx:
                lo = mid + 1
            else:
                hi = mid
        if lo == 0:
            return None
        idx, seq, val = defs[lo - 1]
        return self.rows[idx]

    def arch_last_def_before(self, cls, arch, before_idx):
        defs = self.arch_defs.get((cls, arch), [])
        best = None
        for (idx, seq, phys, val) in defs:
            if idx >= before_idx:
                break
            best = (idx, seq, phys, val)
        return best

    def first_arch_def_after(self, cls, arch, after_idx):
        for (idx, seq, phys, val) in self.arch_defs.get((cls, arch), []):
            if idx > after_idx:
                return (idx, seq, phys, val)
        return None

    def first_seq_after(self, idx):
        return self.rows[idx + 1].seq if idx + 1 < len(self.rows) else None


# ---------------------------------------------------------------------------
# static disassembly
# ---------------------------------------------------------------------------
_RE_OBJDUMP = re.compile(
    r"^\s*([0-9a-f]+):\s+([0-9a-f]+)\s+(\S+)\s*(.*?)\s*$")


class Disasm:
    def __init__(self, elf):
        self.elf = str(elf)
        self.by_pc = {}
        out = subprocess.run(["objdump", "-d", self.elf],
                             capture_output=True, text=True)
        for line in out.stdout.splitlines():
            m = _RE_OBJDUMP.match(line)
            if not m:
                continue
            pc = int(m.group(1), 16)
            mnem = m.group(3)
            operands = m.group(4).split("//")[0].strip()
            self.by_pc[pc] = (mnem, operands)

    def get(self, pc):
        return self.by_pc.get(pc)


# ---------------------------------------------------------------------------
# ARM64 operand and semantics helpers
# ---------------------------------------------------------------------------
def split_ops(text):
    """Split an operand string on top-level commas."""
    out, cur, depth = [], [], 0
    for ch in text:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur).strip())
    return out


def parse_reg(tok):
    """Return ('x'|'w'|'sp'|'zr', index) or None."""
    tok = tok.strip()
    if tok in ("sp", "wsp"):
        return ("sp", 31)
    if tok in ("xzr", "wzr"):
        return ("zr", 31)
    m = re.fullmatch(r"([xw])(\d+)", tok)
    if m:
        return (m.group(1), int(m.group(2)))
    return None


def parse_imm(tok):
    tok = tok.strip()
    if not tok.startswith("#"):
        return None
    s = tok[1:].strip()
    try:
        neg = s.startswith("-")
        s = s.lstrip("-")
        v = int(s, 0) if s.lower().startswith("0x") else int(s, 10)
        return -v if neg else v
    except ValueError:
        return None


def parse_shift(tok):
    """Parse 'lsl #3', 'lsr #2', 'asr #1', extend forms."""
    m = re.fullmatch(r"(lsl|lsr|asr|ror)\s+#(\d+)", tok.strip())
    if m:
        return (m.group(1), int(m.group(2)))
    m = re.fullmatch(r"(sxtw|uxtw|sxtb|uxth|sxth|uxtb)\s*(?:#(\d+))?",
                     tok.strip())
    if m:
        return (m.group(1), int(m.group(2)) if m.group(2) else 0)
    return None


def _mask(width):
    return (1 << width) - 1


def reg_width(reg):
    """Data width of an architectural register operand."""
    if reg is None:
        return 64
    return 32 if reg[0] == "w" else 64


def _sp_value(values):
    """gem5/ARM uses arch index 42 for SP in the commit trace; synthetic
    traces may use 31.  Accept either without guessing a value."""
    for a in (42, 31):
        if a in values:
            return values[a]
    return None


def lookup_reg(reg, values):
    if reg is None:
        return None
    if reg[0] == "zr":
        return 0
    if reg[0] == "sp":
        return _sp_value(values)
    return values.get(reg[1])


def _norm(v, width):
    return None if v is None else (v & _mask(width))


def shift_value(v, kind, amount, width=64):
    """Apply an immediate shift at the instruction's operation width.

    W-register operations rotate/shift within 32 bits; X-register
    operations within 64.  Illegal immediate shift amounts are rejected
    rather than silently modulo-reduced.
    """
    if v is None:
        return None
    if kind not in ("lsl", "lsr", "asr", "ror"):
        raise SemanticsError("not a shift: %s" % kind)
    if amount < 0 or amount >= width:
        raise SemanticsError("shift amount %d out of range for %d-bit op"
                             % (amount, width))
    m = _mask(width)
    v &= m
    if kind == "lsl":
        return (v << amount) & m
    if kind == "lsr":
        return (v >> amount) & m
    if kind == "asr":
        sv = v if v < (1 << (width - 1)) else v - (1 << width)
        return (sv >> amount) & m
    if amount == 0:
        return v
    return ((v >> amount) | (v << (width - amount))) & m


def extend_value(v, kind, amount=0, width=64):
    """Apply UXTB/UXTH/UXTW/SXTB/SXTH/SXTW followed by an optional LSL."""
    if v is None:
        return None
    bits = {"uxtb": 8, "uxth": 16, "uxtw": 32,
            "sxtb": 8, "sxth": 16, "sxtw": 32}.get(kind)
    if bits is None:
        raise SemanticsError("unsupported extend %s" % kind)
    if bits > width:
        raise SemanticsError("extend %s wider than %d-bit op" % (kind, width))
    x = v & ((1 << bits) - 1)
    if kind.startswith("s") and (x >> (bits - 1)) & 1:
        x |= _mask(width) ^ ((1 << bits) - 1)
    if amount:
        if amount >= width:
            raise SemanticsError("extend shift %d out of range" % amount)
        x = (x << amount) & _mask(width)
    return x


def widen(value, reg):
    """Apply the 32-bit write semantics of a W register."""
    if value is None:
        return None
    return value & 0xffffffff if reg and reg[0] == "w" else value & MASK64


class SemanticsError(Exception):
    pass


def _operand_value(tok, values, width):
    imm = parse_imm(tok)
    if imm is not None:
        return imm & _mask(width)
    reg = parse_reg(tok)
    if reg is None:
        raise SemanticsError(f"operand: {tok}")
    v = lookup_reg(reg, values)
    if v is None:
        raise SemanticsError(f"missing source {tok}")
    return v & _mask(width)


def _apply_tail(tail, value, values, width):
    """Apply the optional shift/extend operand (ops[3] or ops[2])."""
    if not tail:
        return value
    if len(tail) > 1:
        raise SemanticsError("multiple operand modifiers: %s" % tail)
    tok = tail[0].strip()
    sh = parse_shift(tok)
    if sh is None:
        raise SemanticsError("unsupported operand modifier: %s" % tok)
    kind, amount = sh
    if kind in ("lsl", "lsr", "asr", "ror"):
        return shift_value(value, kind, amount, width)
    return extend_value(value, kind, amount, width)


def _addsub_flags(mn, a, b, width):
    m = _mask(width)
    a &= m
    b &= m
    is_sub = mn in ("subs", "sub", "cmp", "cmp_uop", "negs")
    if is_sub:
        r = (a - b) & m
        carry = 1 if a >= b else 0
        overflow = 1 if (((a ^ b) & (a ^ r)) & (1 << (width - 1))) else 0
    else:
        r = (a + b) & m
        carry = 1 if ((a + b) >> width) & 1 else 0
        overflow = 1 if (((~(a ^ b)) & (a ^ r)) & (1 << (width - 1))) else 0
    return r, {"N": (r >> (width - 1)) & 1,
               "Z": 1 if r == 0 else 0,
               "C": carry, "V": overflow}


def _logical_flags(r, width):
    return {"N": (r >> (width - 1)) & 1,
            "Z": 1 if (r & _mask(width)) == 0 else 0,
            "C": 0, "V": 0}


def _bitfield(a, immr, imms, width, signed):
    """ARM64 UBFM/SBFM with datasize == width.

    imms is the most-significant source bit of the field.  For
    imms >= immr the field is a straight extract; otherwise the field
    wraps from the top of the register (this is the encoding used by
    UBFIZ/SBFIZ).
    """
    m = _mask(width)
    a &= m
    if immr < 0 or immr >= width or imms < 0 or imms >= width:
        raise SemanticsError("bitfield position out of range")
    if imms >= immr:
        fw = imms - immr + 1
        field = (a >> immr) & ((1 << fw) - 1)
        if signed and (a >> imms) & 1:
            field |= m ^ ((1 << fw) - 1)
    else:
        fw = imms + 1
        field = (a & ((1 << fw) - 1)) << (width - immr)
        if signed:
            ext = (a & ((1 << fw) - 1))
            if (a >> imms) & 1:
                ext |= m ^ ((1 << fw) - 1)
            field = (ext << (width - immr)) & m
    return field & m


def evaluate(mnem, operands, srcvals, flags=None, memory=None):
    """Evaluate one committed ARM64 instruction from actual source values.

    Returns (list_of_dest_values, flags_after).  Only the mnemonic family
    that the instrumented workloads actually emit is implemented; anything
    else raises SemanticsError so an unverified edge is never silently
    upgraded.

    ``srcvals`` is keyed by architectural register index.  W operations
    are evaluated at 32 bits at every step (not by computing in 64 bits
    and truncating at the end).  ``memory`` is only required for LDP/
    LDPSW; it may be a dict address->byte or a callable(address)->byte.
    """
    ops = split_ops(operands)
    mn = mnem.lower()
    flags = dict(flags or {})
    values = dict(srcvals or {})

    if not ops and mn not in ("nop", "dmb", "dsb", "isb", "ret", "br"):
        raise SemanticsError("missing operands")

    # ---- moves / immediates -------------------------------------------
    if mn in ("mov", "movz", "movn", "movk"):
        if len(ops) < 2:
            raise SemanticsError("mov arity")
        dst = parse_reg(ops[0])
        if dst is None:
            raise SemanticsError("mov destination")
        width = reg_width(dst)
        if mn == "movk":
            imm = parse_imm(ops[1])
            if imm is None:
                raise SemanticsError("movk immediate")
            shift = 0
            if len(ops) > 2:
                sh = parse_shift(ops[2])
                if not sh or sh[0] != "lsl":
                    raise SemanticsError("movk shift")
                shift = sh[1]
            if shift not in ((0, 16) if width == 32 else (0, 16, 32, 48)):
                raise SemanticsError("movk shift out of range")
            base = values.get(dst[1], 0)
            nm = _mask(width)
            mask = 0xffff << shift
            v = (base & ~mask) | ((imm & 0xffff) << shift)
            return [widen(v & nm, dst)], flags
        if mn == "mov" and parse_reg(ops[1]) is not None:
            v = _operand_value(ops[1], values, width)
            if len(ops) > 2:
                v = _apply_tail(ops[2:], v, values, width)
            return [widen(v & _mask(width), dst)], flags
        v = _operand_value(ops[1], values, width)
        shift = 0
        if len(ops) > 2:
            sh = parse_shift(ops[2])
            if not sh or sh[0] != "lsl":
                raise SemanticsError("%s shift" % mn)
            shift = sh[1]
        if shift not in ((0, 16) if width == 32 else (0, 16, 32, 48)):
            raise SemanticsError("%s shift out of range" % mn)
        v = (v << shift) & _mask(width)
        if mn == "movn":
            v = (~v) & _mask(width)
        return [widen(v, dst)], flags

    # ---- logical register / immediate --------------------------------
    if mn in ("orr", "and", "eor", "bic", "orn", "eon",
              "ands", "bics", "tst"):
        if mn == "tst":
            dst = None
            a_tok, b_tok = ops[0], ops[1]
            tail = ops[2:]
            width = reg_width(parse_reg(a_tok))
        else:
            dst = parse_reg(ops[0])
            if dst is None:
                raise SemanticsError("logical destination")
            width = reg_width(dst)
            a_tok, b_tok = ops[1], ops[2]
            tail = ops[3:]
        a = _operand_value(a_tok, values, width)
        b = _operand_value(b_tok, values, width)
        # A fourth operand on a logical instruction is a shifted register.
        b = _apply_tail(tail, b, values, width)
        m = _mask(width)
        if mn in ("orr",):
            v = a | b
        elif mn in ("and", "ands", "tst"):
            v = a & b
        elif mn == "eor":
            v = a ^ b
        elif mn in ("bic", "bics"):
            v = a & (~b & m)
        elif mn == "orn":
            v = a | (~b & m)
        else:  # eon
            v = a ^ (~b & m)
        v &= m
        if mn in ("ands", "bics", "tst"):
            flags = _logical_flags(v, width)
        return ([widen(v, dst)] if dst else []), flags

    # ---- add / subtract / compare ------------------------------------
    if mn in ("add", "adds", "sub", "subs", "cmp", "cmn", "neg", "negs"):
        if mn in ("cmp", "cmn"):
            dst = None
            a_tok, b_tok = ops[0], ops[1]
            tail = ops[2:]
            a_reg = parse_reg(a_tok)
            width = reg_width(a_reg)
        elif mn in ("neg", "negs"):
            dst = parse_reg(ops[0])
            width = reg_width(dst)
            a_tok, b_tok, tail = "xzr", ops[1], ops[2:]
        else:
            dst = parse_reg(ops[0])
            if dst is None:
                raise SemanticsError("add/sub destination")
            width = reg_width(dst)
            a_tok, b_tok = ops[1], ops[2]
            tail = ops[3:]
        a = _operand_value(a_tok, values, width)
        b_imm = parse_imm(b_tok)
        if b_imm is not None:
            b = b_imm & _mask(width)
            if tail:
                sh = parse_shift(tail[0])
                if not sh or sh[0] != "lsl" or sh[1] not in (0, 12):
                    raise SemanticsError("add/sub immediate shift")
                b = shift_value(b, "lsl", sh[1], width)
        else:
            b = _operand_value(b_tok, values, width)
            b = _apply_tail(tail, b, values, width)
        if mn in ("sub", "subs", "cmp", "negs"):
            r = (a - b) & _mask(width)
            sets = mn in ("subs", "cmp", "negs")
        else:
            r = (a + b) & _mask(width)
            sets = mn in ("adds", "cmn")
        if sets:
            _, flags = _addsub_flags("subs" if mn in ("subs", "cmp", "negs")
                                     else "adds", a, b, width)
        return ([widen(r, dst)] if dst else []), flags

    # ---- multiply / multiply-add -------------------------------------
    if mn in ("mul", "madd", "msub"):
        dst = parse_reg(ops[0])
        if dst is None:
            raise SemanticsError("%s destination" % mn)
        width = reg_width(dst)
        a = _operand_value(ops[1], values, width)
        b = _operand_value(ops[2], values, width)
        if mn == "mul":
            v = (a * b) & _mask(width)
        else:
            c = _operand_value(ops[3], values, width)
            v = (a * b + (c if mn == "madd" else -c)) & _mask(width)
        return [widen(v, dst)], flags

    # ---- variable and immediate shifts -------------------------------
    if mn in ("lslv", "lsrv", "asrv", "rorv"):
        dst = parse_reg(ops[0])
        if dst is None:
            raise SemanticsError("shift destination")
        width = reg_width(dst)
        a = _operand_value(ops[1], values, width)
        b = _operand_value(ops[2], values, width)
        amount = b % width
        kind = {"lslv": "lsl", "lsrv": "lsr",
                "asrv": "asr", "rorv": "ror"}[mn]
        return [widen(shift_value(a, kind, amount, width), dst)], flags

    if mn in ("lsl", "lsr", "asr", "ror"):
        dst = parse_reg(ops[0])
        if dst is None:
            raise SemanticsError("shift destination")
        width = reg_width(dst)
        a = _operand_value(ops[1], values, width)
        if len(ops) < 3:
            raise SemanticsError("shift amount missing")
        amount = parse_imm(ops[2])
        if amount is None:
            reg = parse_reg(ops[2])
            if reg is None:
                raise SemanticsError("shift amount")
            av = lookup_reg(reg, values)
            if av is None:
                raise SemanticsError("shift amount missing")
            amount = av % width
        return [widen(shift_value(a, mn, amount, width), dst)], flags

    # ---- branches / no-ops -------------------------------------------
    if mn.startswith("b") and (mn == "b" or mn.startswith("b.")):
        return [], flags
    if mn in ("bl", "blr", "ret", "br", "cbz", "cbnz",
              "tbz", "tbnz", "nop", "dmb", "dsb", "isb"):
        return [], flags

    # ---- bitfield ------------------------------------------------------
    if mn in ("ubfm", "sbfm", "ubfx", "sbfx", "ubfiz", "sbfiz"):
        dst = parse_reg(ops[0])
        if dst is None:
            raise SemanticsError("bitfield destination")
        width = reg_width(dst)
        a = _operand_value(ops[1], values, width)
        p1 = parse_imm(ops[2])
        p2 = parse_imm(ops[3])
        if p1 is None or p2 is None:
            raise SemanticsError("bitfield immediate")
        signed = mn.startswith("s")
        if mn in ("ubfx", "sbfx"):
            immr, imms = p1, p1 + p2 - 1
        elif mn in ("ubfiz", "sbfiz"):
            immr = (-p1) % width
            imms = p2 - 1
        else:
            immr, imms = p1, p2
        if imms < 0:
            raise SemanticsError("bitfield width")
        return [widen(_bitfield(a, immr, imms, width, signed), dst)], flags

    # ---- conditional select / increment ------------------------------
    if mn in ("cset", "csetm"):
        dst = parse_reg(ops[0])
        if dst is None:
            raise SemanticsError("cset destination")
        width = reg_width(dst)
        cond = ops[1].strip().lower()
        take = eval_cond(cond, flags)
        m = _mask(width)
        v = (m if mn == "csetm" else 1) if take else 0
        return [widen(v, dst)], flags

    if mn in ("cinc", "cinv", "cneg"):
        dst = parse_reg(ops[0])
        if dst is None:
            raise SemanticsError("conditional destination")
        width = reg_width(dst)
        a = _operand_value(ops[1], values, width)
        cond = ops[2].strip().lower()
        take = eval_cond(cond, flags)
        if mn == "cinc":
            v = a + 1 if take else a
        elif mn == "cinv":
            v = (~a) & _mask(width) if take else a
        else:
            v = (-a) & _mask(width) if take else a
        return [widen(v & _mask(width), dst)], flags

    if mn in ("csel", "csinc", "csinv", "csneg"):
        dst = parse_reg(ops[0])
        if dst is None:
            raise SemanticsError("conditional destination")
        width = reg_width(dst)
        a = _operand_value(ops[1], values, width)
        b = _operand_value(ops[2], values, width)
        cond = ops[3].strip().lower()
        take_a = eval_cond(cond, flags)
        m = _mask(width)
        if mn == "csel":
            v = a if take_a else b
        elif mn == "csinc":
            v = a if take_a else (b + 1) & m
        elif mn == "csinv":
            v = a if take_a else (~b) & m
        else:
            v = a if take_a else (-b) & m
        return [widen(v & m, dst)], flags

    # ---- pair memory ---------------------------------------------------
    if mn in ("stp", "stnp", "ldp", "ldnp", "ldpsw"):
        layout = pair_memory_layout(mn, operands, values)
        if layout is None:
            raise SemanticsError("pair memory form")
        addr, elem_width, regs, wb = layout
        if mn in ("stp", "stnp"):
            # The commit trace splits the pair into per-element micro-ops;
            # the byte write itself is validated by SemanticWalk.
            for reg in regs:
                if lookup_reg(reg, values) is None:
                    raise SemanticsError("stp data register")
            return [], flags
        if memory is None:
            raise SemanticsError("ldp requires memory model")
        out = []
        for i, reg in enumerate(regs):
            v = 0
            for k in range(elem_width):
                b = (memory(addr + i * elem_width + k)
                     if callable(memory) else memory.get(addr + i * elem_width + k, 0))
                v |= (b & 0xff) << (8 * k)
            if mn == "ldpsw":
                v = v & 0xffffffff
                if v & 0x80000000:
                    v -= 1 << 32
            out.append(widen(v & _mask(reg_width(reg)), reg))
        return out, flags

    raise SemanticsError(f"unsupported mnemonic {mn}")


def eval_cond(cond, flags):
    n, z, c, v = flags.get("N", 0), flags.get("Z", 0), \
        flags.get("C", 0), flags.get("V", 0)
    table = {
        "eq": z == 1, "ne": z == 0,
        "cs": c == 1, "hs": c == 1, "cc": c == 0, "lo": c == 0,
        "mi": n == 1, "pl": n == 0, "vs": v == 1, "vc": v == 0,
        "hi": c == 1 and z == 0, "ls": c == 0 or z == 1,
        "ge": n == v, "lt": n != v, "gt": z == 0 and n == v,
        "le": z == 1 or n != v, "al": True,
    }
    if cond not in table:
        raise SemanticsError(f"unsupported condition {cond}")
    return table[cond]


def src_name_map(operands, srcs):
    """Map operand-order source register names to commit-trace src indices.

    gem5 records renamedSrcIdx in static-instruction source order, which is
    the encoding order.  objdump prints operands in a related but not
    always identical order (destination first, then sources in encoding
    order).  For the simple ALU forms used here the source order matches
    the operand order after dropping the destination.  We validate by
    count; a mismatch makes the edge unverified rather than guessed.
    """
    ops = split_ops(operands)
    names = []
    for tok in ops[1:]:
        # Memory operands contribute their base/index registers.
        if tok.startswith("["):
            inner = tok.strip("[]!")
            for part in split_ops(inner):
                p = parse_reg(part.split(",")[0].strip())
                if p and p[0] not in ("sp", "zr"):
                    names.append(p)
                sh = parse_shift(part)
                if sh and sh[0] in ("lsl", "lsr", "asr", "ror"):
                    # shift text follows the index register in its own comma
                    pass
            continue
        sh = parse_shift(tok)
        if sh:
            continue
        p = parse_reg(tok.split("!")[0])
        if p and p[0] not in ("sp", "zr"):
            names.append(p)
    if len(names) != len(srcs):
        return None
    return dict(zip(names, srcs))


def _mem_base_value(reg, values):
    return lookup_reg(reg, values)


def _parse_mem_operand(mnem, operands):
    """Return (regs, memtok, post_tok) for a scalar/pair memory instruction."""
    ops = split_ops(operands)
    pair = mnem in ("stp", "stnp", "ldp", "ldnp", "ldpsw")
    if pair:
        if len(ops) < 3:
            return None
        regs = [parse_reg(ops[0]), parse_reg(ops[1])]
        memtok, post = ops[2], (ops[3] if len(ops) > 3 else None)
    else:
        if len(ops) < 2:
            return None
        regs = [parse_reg(ops[0])]
        memtok, post = ops[1], (ops[2] if len(ops) > 2 else None)
    if any(r is None for r in regs):
        return None
    return regs, memtok, post


def _effective_address(memtok, values, width=64):
    """Compute [base], [base,#imm], [base,reg,lsl #n] and pre-index."""
    writeback = None
    if memtok.endswith("!"):
        memtok = memtok[:-1]
        pre = True
    else:
        pre = False
    if not memtok.startswith("[") or not memtok.endswith("]"):
        return None
    inner = memtok.strip("[]")
    parts = split_ops(inner)
    if not parts:
        return None
    base = parse_reg(parts[0])
    if base is None or base[0] == "zr":
        return None
    basev = _mem_base_value(base, values)
    if basev is None:
        return None
    addr = basev & MASK64
    if len(parts) > 1:
        off = parse_imm(parts[1])
        if off is not None:
            off = off & MASK64
        else:
            idx = parse_reg(parts[1])
            if idx is None:
                return None
            off = _mem_base_value(idx, values)
            if off is None:
                return None
            if len(parts) > 2:
                sh = parse_shift(parts[2])
                if sh is None:
                    return None
                if sh[0] in ("lsl", "lsr", "asr", "ror"):
                    off = shift_value(off, sh[0], sh[1], 64)
                else:
                    off = extend_value(off, sh[0], sh[1], 64)
            off &= MASK64
        addr = (addr + off) & MASK64
    return addr, base, pre


def pair_memory_layout(mnem, operands, values):
    """Address, per-element width, register list and writeback for STP/LDP.

    Returns (addr, elem_width, regs, writeback) or None.  writeback is
    (register, new_value) for pre/post-index forms.
    """
    mn = mnem.lower()
    parsed = _parse_mem_operand(mn, operands)
    if parsed is None:
        return None
    regs, memtok, post = parsed
    if mn == "ldpsw":
        elem_width = 4
    else:
        widths = {reg_width(r) // 8 for r in regs}
        if len(widths) != 1:
            return None
        elem_width = widths.pop()
    ea = _effective_address(memtok, values)
    if ea is None:
        return None
    addr, base, pre = ea
    wb = None
    if post is not None:
        imm = parse_imm(post)
        if imm is not None:
            bv = _mem_base_value(base, values)
            wb = (base, (bv + imm) & MASK64)
    elif pre:
        bv = _mem_base_value(base, values)
        wb = (base, addr)
    return addr, elem_width, regs, wb


def memory_address(mnem, operands, values):
    """Compute the data address of a scalar/pair load/store.

    Supports [base], [base,#imm], [base,reg], [base,reg,lsl #n],
    pre-index and post-index forms.  Returns (address, width_bytes,
    writeback) or None if the form is unsupported.  For pair operations
    ``width_bytes`` is the total byte span (2 * element width).
    """
    mn = mnem.lower()
    scalar_width = None
    if mn in ("ldr", "str", "ldur", "stur", "ldar", "stlr", "ldxr", "stxr"):
        first = parse_reg(split_ops(operands)[0]) if split_ops(operands) else None
        scalar_width = 4 if (first and first[0] == "w") else 8
    elif mn in ("ldrb", "strb", "ldurb", "sturb"):
        scalar_width = 1
    elif mn in ("ldrh", "strh", "ldurh", "sturh"):
        scalar_width = 2
    elif mn in ("ldrsw", "ldrsb", "ldrsh"):
        scalar_width = 4
    if scalar_width is not None:
        parsed = _parse_mem_operand(mn, operands)
        if parsed is None:
            return None
        regs, memtok, post = parsed
        ea = _effective_address(memtok, values)
        if ea is None:
            return None
        addr, base, pre = ea
        wb = None
        if post is not None:
            imm = parse_imm(post)
            if imm is not None:
                bv = _mem_base_value(base, values)
                wb = (base, (bv + imm) & MASK64)
        elif pre:
            bv = _mem_base_value(base, values)
            wb = (base, addr)
        return addr, scalar_width, wb
    if mn in ("stp", "stnp", "ldp", "ldnp", "ldpsw"):
        layout = pair_memory_layout(mn, operands, values)
        if layout is None:
            return None
        addr, elem, regs, wb = layout
        return addr, elem * 2, wb
    return None


def fnv1a64_bytes(data):
    h = 1469598103934665603
    for b in data:
        h ^= b
        h = (h * 1099511628211) & MASK64
    return h


def when_fnv(h, v):
    """Byte-exact when_fnv from when_common.h (little-endian 8 bytes)."""
    h &= MASK64
    for k in range(8):
        h ^= (v >> (8 * k)) & 0xff
        h = (h * 1099511628211) & MASK64
    return h


def load_elf_disasm(model, context):
    from e2e_strict_data import WORK
    fam = {
        "A01": "agu", "A03": "agu", "LQ04": "lq",
        "SQ01": "sq", "SQ03": "sq", "SP05": "sq",
        "FW02": "fwd_full", "FW05": "fwd_partial",
        "MD04": "md", "RP01": "md", "DA04": "align", "LP01": "lp",
    }[model]
    return Disasm(WORK / "bin" / f"{fam}_{context}")
