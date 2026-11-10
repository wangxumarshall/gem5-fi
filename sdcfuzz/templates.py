"""Local Phase-0 seed corpus: 19 microarchitectural templates.

This corpus is a *local* re-implementation of the route document's Phase-0
"19 手工微架构模板" idea (sdcfuzz-v1.2.md §4.2/§7).  It is not a copy of the
external sdcfuzz corpus: the ids, instruction bodies and target mapping below
are derived from the structures and CHAOS injectors that exist in this
repository, and every template is measured with the ACE/IBR metrics added in
the previous milestone.

Each template names:
* ``target`` — the gem5-observable structure it is meant to activate
  (``alu``/``mult``/``div``/``l1d``/``l1i``/``fpadd``/``fpmul`` or ``none``
  when no metric exists);
* ``injector`` — the CHAOS injector class a fault-injection campaign would use;
* ``body`` — the instruction group repeated 16 times inside the m5 ROI.
"""

from dataclasses import dataclass, field

from .isa import Op


@dataclass(frozen=True)
class Template:
    id: str
    title: str
    target: str
    injector: str
    setup: tuple = field(default_factory=tuple)
    body: tuple = field(default_factory=tuple)
    note: str = ""


def _mov(reg, value):
    return Op("mov", dst=reg, imm=value)


def _alu(kind, dst, a, b):
    return Op(kind, dst=dst, a=a, b=b)


# A long, instruction-diverse group: a big L1I footprint with ALU work.
_BIG_BODY = tuple(Op("add_imm", dst="x8", imm=value) for value in range(1, 33))

TEMPLATES = (
    Template(
        "alu-add-carry", "整数加法进位链", "alu", "CHAOSExec",
        setup=(_mov("x8", 0x0123456789ABCDEF), _mov("x12", 0x00FF00FF00FF00FF)),
        body=(_alu("add", "x8", "x8", "x12"),),
        note="连续加法，进位在 8 位块间传播；本地启发式可用 x12 变体替换操作数",
    ),
    Template(
        "alu-sub-borrow", "整数减法借位链", "alu", "CHAOSExec",
        setup=(_mov("x8", 0xFEDCBA9876543210), _mov("x12", 0x0000FFFF0000FFFF)),
        body=(_alu("sub", "x8", "x8", "x12"),),
    ),
    Template(
        "alu-eor-toggle", "逻辑异或翻转", "alu", "CHAOSExec",
        setup=(_mov("x8", 0x5555555555555555), _mov("x12", 0xAAAAAAAAAAAAAAAA)),
        body=(_alu("eor", "x8", "x8", "x12"),),
    ),
    Template(
        "alu-and-mask", "逻辑与掩码", "alu", "CHAOSExec",
        setup=(_mov("x8", 0xFFFFFFFFFFFFFFFF), _mov("x12", 0x0F0F0F0F0F0F0F0F)),
        body=(_alu("and", "x8", "x8", "x12"),),
    ),
    Template(
        "alu-add-shifted", "移位加法", "alu", "CHAOSExec",
        setup=(_mov("x8", 3), _mov("x12", 0x0123456789ABCDEF)),
        body=(Op("add_lsl", dst="x8", a="x8", b="x12", imm=3),),
    ),
    Template(
        "mul64", "64 位乘法", "mult", "CHAOSExec",
        setup=(_mov("x8", 3), _mov("x12", 0x9E3779B97F4A7C15)),
        body=(Op("mul", dst="x8", a="x8", b="x12", width=64),),
    ),
    Template(
        "mul32", "32 位乘法", "mult", "CHAOSExec",
        setup=(_mov("x8", 3), _mov("x12", 0xDEADBEEF)),
        body=(Op("mul", dst="x8", a="x8", b="x12", width=32),),
    ),
    Template(
        "madd64", "乘法累加", "mult", "CHAOSExec",
        setup=(_mov("x8", 3), _mov("x12", 0x9E3779B97F4A7C15), _mov("x10", 5)),
        body=(Op("madd", dst="x8", a="x8", b="x12", c="x10", width=64),),
    ),
    Template(
        "div64", "64 位无符号除法", "div", "CHAOSExec",
        setup=(_mov("x8", 0xFFFFFFFFFFFF), _mov("x12", 3)),
        body=(Op("udiv", dst="x8", a="x8", b="x12", width=64),),
    ),
    Template(
        "div32", "32 位无符号除法", "div", "CHAOSExec",
        setup=(_mov("x8", 0xFFFFFFFF), _mov("x12", 7)),
        body=(Op("udiv", dst="x8", a="x8", b="x12", width=32),),
    ),
    Template(
        "l1d-load-hot", "L1D 热行重复读", "l1d", "CHAOSCache",
        setup=(_mov("x8", 0),),
        body=(Op("ldr", dst="x8", off=0),),
    ),
    Template(
        "l1d-load-stream", "L1D 多行顺序读", "l1d", "CHAOSCache",
        setup=(_mov("x8", 0),),
        body=tuple(Op("ldr", dst=reg, off=off) for reg, off in (
            ("x8", 0), ("x9", 128), ("x10", 256),
            ("x11", 384), ("x12", 512), ("x13", 640))),
    ),
    Template(
        "l1d-store-hot", "L1D 热行重复写", "l1d", "CHAOSCache",
        setup=(_mov("x8", 0xDEADBEEFCAFEF00D),),
        body=(Op("str", dst="x8", off=0),),
    ),
    Template(
        "l1d-load-store", "L1D 同址写后读", "l1d", "CHAOSCache",
        setup=(_mov("x8", 0x0123456789ABCDEF),),
        body=(Op("str", dst="x8", off=8), Op("ldr", dst="x9", off=8)),
    ),
    Template(
        "l1i-big-body", "L1I 大指令足迹", "l1i", "CHAOSCache",
        setup=(_mov("x8", 0),),
        body=_BIG_BODY,
        note="32 条不同立即数加法 ×16 次/迭代，指令足迹约 2 KiB/迭代",
    ),
    Template(
        "dep-chain", "长依赖链", "alu", "CHAOSPhysReg",
        setup=(_mov("x8", 1), _mov("x9", 3)),
        body=(_alu("add", "x8", "x8", "x9"), _alu("add", "x9", "x9", "x8")),
        note="两条互相依赖的加法，限制乱序并行度",
    ),
    Template(
        "branch-busy", "分支密集小循环", "alu", "CHAOSBPU",
        setup=(_mov("x8", 0),),
        body=(Op("busy_loop", dst="x8", a="x11", imm=8),),
    ),
    Template(
        "fp-add", "双精度浮点加法", "fpadd", "CHAOSFPU",
        setup=(Op("ldrf", dst="d0", off=0), Op("ldrf", dst="d1", off=8)),
        body=(Op("fadd", dst="d0", a="d0", b="d1"),),
        note="FP add 由 fpAdd IBR 与向量寄存器低 64 位 ACE 测量",
    ),
    Template(
        "fp-mul", "双精度浮点乘法", "fpmul", "CHAOSFPU",
        setup=(Op("ldrf", dst="d0", off=0), Op("ldrf", dst="d1", off=8)),
        body=(Op("fmul", dst="d0", a="d0", b="d1"),),
        note="FP multiply 由 fpMult IBR 与向量寄存器低 64 位 ACE 测量",
    ),
)

TEMPLATE_BY_ID = {template.id: template for template in TEMPLATES}

if len(TEMPLATES) != 19:
    raise AssertionError(f"phase-0 corpus must contain 19 templates, "
                         f"found {len(TEMPLATES)}")
