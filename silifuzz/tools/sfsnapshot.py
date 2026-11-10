"""Reference Python implementation of the SiliFuzz snapshot format (ARM64).

The C++ implementation in src/snapshot.cc is authoritative; this module must
produce byte-identical encodings.  It is used by the corpus/fleet/quarantine
tooling and cross-checked by tests/test_crosslang.py.

Format (little endian):
  magic "SILIFZ01", u32 version, u32 arch, u32 flags, u64 id, u32 meta_len,
  meta bytes,
  regs: x[31] u64, sp, pc, pstate, fpcr, fpsr, v[32][16],
  u32 nmap; each { u64 start, u64 size, u32 perms, u32 kind, u32 data_len,
                  data bytes },
  u32 nend; each { u32 signal, u64 sig_addr, regs, u32 ncs,
                  each { u64 start, u64 size, u64 hash } }
"""

from __future__ import annotations

import dataclasses
import hashlib
import struct
from typing import List, Optional

MAGIC = b"SILIFZ01"
VERSION = 1
ARCH_AARCH64 = 1
PAGE = 4096
CODE_BASE = 0x10000000
DATA_BASE = 0x20000000
STACK_BASE = 0x30000000
STACK_TOP = STACK_BASE + 0x800

PERM_READ = 1
PERM_WRITE = 2
PERM_EXEC = 4


def fnv1a64(data: bytes) -> int:
    h = 14695981039346656037
    for b in data:
        h ^= b
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


@dataclasses.dataclass
class RegState:
    x: List[int] = dataclasses.field(default_factory=lambda: [0] * 31)
    sp: int = 0
    pc: int = 0
    pstate: int = 0
    fpcr: int = 0
    fpsr: int = 0
    v: bytes = dataclasses.field(default_factory=lambda: bytes(32 * 16))


@dataclasses.dataclass
class MemoryMapping:
    start: int
    size: int
    perms: int
    data: bytes = b""

    def checksum(self) -> int:
        buf = bytearray(self.size)
        buf[: len(self.data)] = self.data
        return fnv1a64(bytes(buf))


@dataclasses.dataclass
class MemChecksum:
    start: int
    size: int
    hash: int


@dataclasses.dataclass
class EndState:
    signal: int = 0
    sig_addr: int = 0
    regs: RegState = dataclasses.field(default_factory=RegState)
    checksums: List[MemChecksum] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Snapshot:
    arch: int = ARCH_AARCH64
    flags: int = 0
    id: int = 0
    meta: str = ""
    regs: RegState = dataclasses.field(default_factory=RegState)
    mappings: List[MemoryMapping] = dataclasses.field(default_factory=list)
    end_states: List[EndState] = dataclasses.field(default_factory=list)


def _pack_regs(r: RegState) -> bytes:
    out = bytearray()
    out += struct.pack("<31Q", *r.x)
    out += struct.pack("<5Q", r.sp, r.pc, r.pstate, r.fpcr, r.fpsr)
    if len(r.v) != 512:
        raise ValueError("v register file must be 512 bytes")
    out += r.v
    return bytes(out)


def _unpack_regs(buf: bytes, off: int) -> (RegState, int):
    if off + 800 > len(buf):
        raise ValueError("truncated registers")
    x = list(struct.unpack_from("<31Q", buf, off))
    sp, pc, pstate, fpcr, fpsr = struct.unpack_from("<5Q", buf, off + 31 * 8)
    v = buf[off + 288 : off + 800]
    return RegState(x=x, sp=sp, pc=pc, pstate=pstate, fpcr=fpcr, fpsr=fpsr, v=v), off + 800


def encode(s: Snapshot) -> bytes:
    meta = s.meta.encode()
    if len(meta) > 64 * 1024:
        raise ValueError("metadata too large")
    out = bytearray()
    out += MAGIC
    out += struct.pack("<IIIQI", VERSION, s.arch, s.flags, s.id, len(meta))
    out += meta
    out += _pack_regs(s.regs)
    if len(s.mappings) > 64:
        raise ValueError("too many mappings")
    out += struct.pack("<I", len(s.mappings))
    for m in s.mappings:
        if m.start % PAGE or m.size == 0 or m.size % PAGE or len(m.data) > m.size:
            raise ValueError(f"invalid mapping {m.start:x}+{m.size:x}")
        out += struct.pack("<QQIII", m.start, m.size, m.perms,
                           1 if m.data else 0, len(m.data))
        out += m.data
    if len(s.end_states) > 16:
        raise ValueError("too many end states")
    out += struct.pack("<I", len(s.end_states))
    for e in s.end_states:
        out += struct.pack("<IQ", e.signal, e.sig_addr)
        out += _pack_regs(e.regs)
        out += struct.pack("<I", len(e.checksums))
        for c in e.checksums:
            out += struct.pack("<QQQ", c.start, c.size, c.hash)
    return bytes(out)


def decode(buf: bytes) -> Snapshot:
    if len(buf) < 32 or buf[:8] != MAGIC:
        raise ValueError("bad magic")
    version, arch, flags, sid, meta_len = struct.unpack_from("<IIIQI", buf, 8)
    if version != VERSION:
        raise ValueError(f"unsupported version {version}")
    off = 32
    if off + meta_len > len(buf):
        raise ValueError("truncated metadata")
    meta = buf[off : off + meta_len].decode()
    off += meta_len
    regs, off = _unpack_regs(buf, off)
    (nmap,) = struct.unpack_from("<I", buf, off)
    off += 4
    if nmap > 64:
        raise ValueError("too many mappings")
    maps: List[MemoryMapping] = []
    for _ in range(nmap):
        start, size, perms, kind, dlen = struct.unpack_from("<QQIII", buf, off)
        off += 28
        if kind > 1 or dlen > size:
            raise ValueError("bad mapping")
        data = buf[off : off + dlen] if kind == 1 else b""
        off += dlen
        maps.append(MemoryMapping(start, size, perms, data))
    (nend,) = struct.unpack_from("<I", buf, off)
    off += 4
    if nend > 16:
        raise ValueError("too many end states")
    ends: List[EndState] = []
    for _ in range(nend):
        sig, addr = struct.unpack_from("<IQ", buf, off)
        off += 12
        eregs, off = _unpack_regs(buf, off)
        (ncs,) = struct.unpack_from("<I", buf, off)
        off += 4
        if ncs > 64:
            raise ValueError("too many checksums")
        cs: List[MemChecksum] = []
        for _ in range(ncs):
            st, sz, h = struct.unpack_from("<QQQ", buf, off)
            off += 24
            cs.append(MemChecksum(st, sz, h))
        ends.append(EndState(sig, addr, eregs, cs))
    if off != len(buf):
        raise ValueError("trailing bytes")
    return Snapshot(arch=arch, flags=flags, id=sid, meta=meta, regs=regs,
                    mappings=maps, end_states=ends)


def encode_without_id(s: Snapshot) -> bytes:
    s2 = dataclasses.replace(s, id=0)
    return encode(s2)


def content_hash(s: Snapshot) -> str:
    return hashlib.sha256(encode_without_id(s)).hexdigest()


def content_id(s: Snapshot) -> int:
    return int(content_hash(s)[:16], 16)


def load(path: str) -> Snapshot:
    with open(path, "rb") as f:
        return decode(f.read())


def save(path: str, s: Snapshot) -> None:
    data = encode(s)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    import os
    os.replace(tmp, path)


def same_regs(a: RegState, b: RegState) -> bool:
    return (a.x == b.x and a.sp == b.sp and a.pc == b.pc
            and a.pstate == b.pstate and a.fpcr == b.fpcr
            and a.fpsr == b.fpsr and a.v == b.v)


def same_end_state(a: EndState, b: EndState) -> bool:
    return (a.signal == b.signal and a.sig_addr == b.sig_addr
            and same_regs(a.regs, b.regs)
            and [(c.start, c.size, c.hash) for c in a.checksums]
            == [(c.start, c.size, c.hash) for c in b.checksums])


def summary(s: Snapshot) -> dict:
    return {
        "id": f"0x{s.id:016x}",
        "pc": f"0x{s.regs.pc:016x}",
        "mappings": len(s.mappings),
        "end_states": len(s.end_states),
        "signal": s.end_states[0].signal if s.end_states else None,
        "meta": s.meta,
    }
