"""A small AArch64 subset used by the local sdcfuzz Phase-0 baseline corpus.

Each template is a list of :class:`Op` values.  The same list is rendered to
GNU-assembler text for the guest and interpreted in Python to compute the
expected checksum, so the expected value is independent of the guest build.

Only the instructions the templates need are modelled; unsupported operations
raise instead of silently degrading.
"""

import struct
from dataclasses import dataclass, field

MASK64 = (1 << 64) - 1
MASK32 = (1 << 32) - 1

GPRS = ("x8", "x9", "x10", "x11", "x12", "x13")
FPREGS = ("d0", "d1", "d2", "d3")
MEM_WORDS = 128


def double_bits(value):
    return struct.unpack("<Q", struct.pack("<d", value))[0]


def bits_double(bits):
    return struct.unpack("<d", struct.pack("<Q", bits & MASK64))[0]


def initial_memory():
    """Deterministic data buffer shared by the guest and the reference."""
    memory = []
    for index in range(MEM_WORDS):
        value = (0x0123456789ABCDEF + index * 0x9E3779B97F4A7C15) & MASK64
        memory.append(value)
    # FP templates load their operands from the first two words.
    memory[0] = double_bits(1.5)
    memory[1] = double_bits(2.25)
    return memory


def load_imm(reg, value):
    """Render a 64-bit constant load with movz/movk."""
    value &= MASK64
    lines = [f"movz {reg}, #{value & 0xFFFF:#x}"]
    for shift in (16, 32, 48):
        part = (value >> shift) & 0xFFFF
        if part:
            lines.append(f"movk {reg}, #{part:#x}, lsl #{shift}")
    return lines


@dataclass(frozen=True)
class Op:
    kind: str
    dst: str | None = None
    a: str | None = None
    b: str | None = None
    imm: int | None = None
    c: str | None = None
    width: int = 64
    off: int | None = None


def _w(reg, width):
    """Register spelling for the selected width (Wn for 32-bit ops)."""
    if width == 32:
        if not reg.startswith("x"):
            raise ValueError(f"32-bit operand must be a GPR, got {reg}")
        return "w" + reg[1:]
    return reg


def render(op):
    """Assembler lines for one operation."""
    kind = op.kind
    if kind == "mov":
        return load_imm(op.dst, op.imm)
    if kind in ("add", "sub", "and", "orr", "eor"):
        return [f"{kind} {op.dst}, {op.a}, {op.b}"]
    if kind == "add_imm":
        return [f"add {op.dst}, {op.dst}, #{op.imm}"]
    if kind == "add_lsl":
        return [f"add {op.dst}, {op.a}, {op.b}, lsl #{op.imm}"]
    if kind in ("mul", "udiv"):
        d, a, b = (_w(r, op.width) for r in (op.dst, op.a, op.b))
        return [f"{kind} {d}, {a}, {b}"]
    if kind == "madd":
        d, a, b = (_w(r, op.width) for r in (op.dst, op.a, op.b))
        if not op.c:
            raise ValueError("madd requires an addend register")
        return [f"madd {d}, {a}, {b}, {_w(op.c, op.width)}"]
    if kind == "ldr":
        return [f"ldr {op.dst}, [%[buf], #{op.off}]"]
    if kind == "str":
        return [f"str {op.dst}, [%[buf], #{op.off}]"]
    if kind == "ldrf":
        return [f"ldr {op.dst}, [%[buf], #{op.off}]"]
    if kind in ("fadd", "fsub", "fmul", "fdiv"):
        return [f"{kind} {op.dst}, {op.a}, {op.b}"]
    if kind == "busy_loop":
        return [f"mov {op.a}, #{op.imm}",
                "1:",
                f"add {op.dst}, {op.dst}, #1",
                f"subs {op.a}, {op.a}, #1",
                "b.ne 1b"]
    raise ValueError(f"unknown op kind {kind!r}")


@dataclass
class State:
    regs: dict = field(default_factory=dict)
    fregs: dict = field(default_factory=dict)
    mem: list = field(default_factory=initial_memory)

    def gpr(self, name):
        if name not in GPRS:
            raise ValueError(f"unknown GPR {name!r}")
        return self.regs.get(name, 0)

    def set_gpr(self, name, value, width=64):
        if name not in GPRS:
            raise ValueError(f"unknown GPR {name!r}")
        self.regs[name] = value & (MASK32 if width == 32 else MASK64)

    def fpr(self, name):
        if name not in FPREGS:
            raise ValueError(f"unknown FP register {name!r}")
        return self.fregs.get(name, 0.0)


def apply(op, state):
    """Execute one operation with AArch64 semantics on the Python state."""
    kind = op.kind
    if kind == "mov":
        state.set_gpr(op.dst, op.imm)
    elif kind in ("add", "sub", "and", "orr", "eor"):
        a, b = state.gpr(op.a), state.gpr(op.b)
        value = {"add": a + b, "sub": a - b, "and": a & b,
                 "orr": a | b, "eor": a ^ b}[kind]
        state.set_gpr(op.dst, value)
    elif kind == "add_imm":
        state.set_gpr(op.dst, state.gpr(op.dst) + op.imm)
    elif kind == "add_lsl":
        state.set_gpr(op.dst, state.gpr(op.a) + (state.gpr(op.b) << op.imm))
    elif kind == "mul":
        a, b = state.gpr(op.a), state.gpr(op.b)
        state.set_gpr(op.dst, (a % (1 << op.width)) * (b % (1 << op.width)),
                      op.width)
    elif kind == "madd":
        a, b = state.gpr(op.a), state.gpr(op.b)
        c = state.gpr(op.c)
        state.set_gpr(op.dst, (a % (1 << op.width)) * (b % (1 << op.width)) + c,
                      op.width)
    elif kind == "udiv":
        a = state.gpr(op.a) % (1 << op.width)
        b = state.gpr(op.b) % (1 << op.width)
        state.set_gpr(op.dst, 0 if b == 0 else a // b, op.width)
    elif kind in ("ldr", "ldrf"):
        word = state.mem[(op.off or 0) // 8]
        if kind == "ldr":
            state.set_gpr(op.dst, word)
        else:
            state.fregs[op.dst] = bits_double(word)
    elif kind == "str":
        state.mem[(op.off or 0) // 8] = state.gpr(op.dst)
    elif kind in ("fadd", "fsub", "fmul", "fdiv"):
        a, b = state.fpr(op.a), state.fpr(op.b)
        try:
            value = {"fadd": a + b, "fsub": a - b, "fmul": a * b,
                     "fdiv": a / b}[kind]
        except ZeroDivisionError:
            # IEEE-754: division by zero yields a signed infinity unless the
            # numerator is also zero, which yields NaN.
            value = float("nan") if a == 0.0 else float("inf")
            if value != value:
                pass
            elif (a < 0) != (b < 0):
                value = -value
        state.fregs[op.dst] = value
    elif kind == "busy_loop":
        state.set_gpr(op.a, op.imm)
        for _ in range(op.imm):
            state.set_gpr(op.dst, state.gpr(op.dst) + 1)
            state.set_gpr(op.a, state.gpr(op.a) - 1)
    else:
        raise ValueError(f"unknown op kind {kind!r}")


def mix(h, value):
    return ((h ^ (value & MASK64)) * 1099511628211) & MASK64


def checksum(state):
    """Checksum contract shared with the generated guest (8 GPRs, 4 FP, mem)."""
    h = 1469598103934665603
    for name in GPRS:
        h = mix(h, state.gpr(name))
    for name in FPREGS:
        h = mix(h, double_bits(state.fpr(name)))
    for word in state.mem:
        h = mix(h, word)
    return h


def run_body(body, state, repetitions):
    for _ in range(repetitions):
        for op in body:
            apply(op, state)


def expected_checksum(template, iterations, reps=16):
    state = State()
    for op in template.setup:
        apply(op, state)
    run_body(template.body, state, iterations * reps)
    return checksum(state)
