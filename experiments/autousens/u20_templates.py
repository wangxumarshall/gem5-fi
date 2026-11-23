"""Execution-level coverage comparison: 20 upstream templates vs AutoµSens.

Protocol (2026-11-17, plan ``2026-11-17-u20-templates-vs-autousens.md``)
-------------------------------------------------------------------------
* **Template arm**: one faithful execution of each vendored upstream ``seeds/*.S``
  probe, with the upstream initial state (x6/x7/sp) reproduced by an assembly
  wrapper.  Setup is outside the m5 work item, so ACE/IBR/SAD measure the probe.
* **AutoµSens arm**: the tool's top-1 instruction for the template's mapped
  structure, repeated four times (``OPS_PER_GROUP``) in a *straight-line* body
  of G groups.  G is chosen so the generated guest's dynamic instruction count
  matches the template's ROI count.  No 16-group loop is used because it would
  add more control instructions than the short upstream probes execute.
* **D13 arm**: identical body/G, but each group loads x12 from the bit-exact
  Python port of the upstream D13 operand stream.  The independent
  ``sdcfuzz.target_oracle`` checksum still guards the guest (``status=PASS``).
* **Metrics**: every ACE/IBR/SAD field in ``experiments/autousens/metrics.py``,
  plus a per-structure focus set.  The full CSV is the primary artifact; the
  tables are views of it.

Why no template/D13 cell: no seed reads x12 before writing it (4 never mention
x12 at all; the other 16 write it first), so D13's x12 injection cannot reach
the fixed template body.  A template/D13 run would only add an operand-load
instruction and would not be a D13 variant.  This is reported instead of
fabricated.

Run from the repository root::

    python3 experiments/autousens/u20_templates.py --run-id 2026-11-17-u20
    python3 experiments/autousens/u20_templates.py --verify 2026-11-17-u20
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))

from autousens import arms, d13, metrics  # noqa: E402
from sdcfuzz import seed_templates  # noqa: E402
from sdcfuzz.target_oracle import (  # noqa: E402
    INITIAL_FP,
    INITIAL_MEMORY,
    MEMORY_WORDS,
    MASK64,
    expected_checksum,
)

TOOL = arms.TOOL
MODE_ASM = TOOL.MODE_ASM
CONFIG = ROOT / "configs/se/arm_chaos.py"
GEM5 = ROOT / "CHAOS/gem5/build/ARM/gem5.opt"
M5OP = ROOT / "CHAOS/gem5/util/m5/src/abi/arm64/m5op.S"
GEM5_INCLUDE = ROOT / "CHAOS/gem5/include"
SEEDS_DIR = ROOT / "sdcfuzz/upstream/seeds"
DEFAULT_MAP = ROOT / "m5out/autousens-eval/2026-11-17-r2/map/structure_map.json"
DEFAULT_RUN_ID = "2026-11-17-u20"
OPS_PER_GROUP = TOOL.OPS_PER_GROUP  # 4
WORK_ID = 7

METRIC_ARGS = (
    "--kp920_proxy",
    "--rf_ace", "--rf_ace_granularity=bit",
    "--l1_ace",
    "--fu_ibr",
    "--sad",
)


# --------------------------------------------------------------------------
# Mapping: nominal template structure -> measured structure -> Auto target
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Mapping:
    seed: str
    nominal: str          # what the template header says it stresses
    measured: str         # which existing counter family we compare on
    auto: str             # which structure AutoµSens targets
    kind: str             # direct | proxy | unmeasurable
    rationale: str


MAPPINGS = (
    Mapping("c1_l2_eviction", "L2 cache", "l1d", "l1d", "proxy",
            "L2 has no ACE/IBR/SAD counter; L1D is the closest measured cache"),
    Mapping("c3_l3_128b", "L3 cache", "l1d", "l1d", "proxy",
            "L3 has no ACE/IBR/SAD counter; L1D is the closest measured cache"),
    Mapping("e1_carry_chain", "ALU carry chain", "alu", "alu", "direct",
            "integer adds target intAlu IBR"),
    Mapping("e2_mul_extreme", "multiplier", "mult", "mult", "direct",
            "64-bit multiply targets intMult IBR"),
    Mapping("e3_toggle_rate", "ALU toggle rate", "alu", "alu", "direct",
            "integer xor/eon chain targets intAlu IBR"),
    Mapping("f1_subnormal_nan", "FSU special operands", "fpadd", "fpadd", "direct",
            "the body's first FP operation is fadd; fpAdd IBR is the match"),
    Mapping("i1_icache_boundary", "L1I boundary", "l1i", "alu", "proxy",
            "L1I is measured but not per-instruction targetable; Auto targets alu"),
    Mapping("i2_branch_dense", "BPU / L1I", "l1i", "alu", "proxy",
            "no BPU counter and L1I is not targetable; Auto targets alu"),
    Mapping("l1_disambig", "LSU disambiguation", "l1d", "l1d", "direct",
            "loads and stores target L1D ACE"),
    Mapping("l2_dualagu_split", "dual AGU / L1D", "l1d", "l1d", "direct",
            "split loads target L1D ACE"),
    Mapping("m1_tlb_thrash", "TLB / PTW", "l1d", "l1d", "proxy",
            "no TLB counter in this build; L1D ACE and LQ occupancy are measured"),
    Mapping("m3_cross_page", "MMU + LSU cross-page", "l1d", "l1d", "proxy",
            "no TLB counter; the page-crossing store/load is measured as L1D"),
    Mapping("o1_rob_full_wakeup", "ROB / scheduler", "rob", "l1d", "proxy",
            "no ROB target in Auto; a long-latency load is the closest generator"),
    Mapping("o2_mispredict_rollback", "BPU / PRF rollback", "rob", "alu", "proxy",
            "no branch counter; SAD ROB/IQ and an alu stream are the proxy"),
    Mapping("v1_fsu_vdroop", "FSU FMLA burst", "vec", "vec", "proxy",
            "128-bit vector FMLA is outside the scalar fpMult IBR; vector RF ACE "
            "is the measurable target and Auto's vec body is scalar fadd"),
    Mapping("v2_alu_complex_saturation", "ALU + complex port", "mult", "mult", "direct",
            "the body fills the complex port with MUL/MADD"),
    Mapping("v3_prf_mispredict", "PRF pressure / rollback", "rf", "rf", "direct",
            "register-pressure body targets integer RF ACE"),
    Mapping("v4_lsu_cross_boundary", "LSU split access", "l1d", "l1d", "direct",
            "cross-boundary loads/stores target L1D ACE"),
    Mapping("v5_lse_cross_die", "LSE atomics / LSU", "l1d", "l1d", "direct",
            "LSE atomics are memory operations measured by L1D ACE"),
    Mapping("v6_crypto_toggle", "crypto / vector unit", "vec", "vec", "proxy",
            "no crypto counter; vector RF ACE and SAD vecPRF are measured"),
)

MAPPING_BY_SEED = {mapping.seed: mapping for mapping in MAPPINGS}

#: The metric that is the headline for each measured structure.
PRIMARY = {
    "alu": "ibr.intAlu.ibrRatio",
    "mult": "ibr.intMult.ibrRatio",
    "div": "ibr.intDiv.ibrRatio",
    "fpadd": "ibr.fpAdd.ibrRatio",
    "fpmul": "ibr.fpMult.ibrRatio",
    "rf": "ace.rf.intAceRatio",
    "vec": "ace.rf.vecAceRatio",
    "l1d": "ace.l1d.aceRatio",
    "l1i": "ace.l1i.aceRatio",
    "rob": "sad.rob.ratio",
}

FOCUS = {
    "alu": (
        "ibr.intAlu.ibrRatio", "ibr.intAlu.inputBits", "ibr.intAlu.issuedOps",
        "ibr.intAlu.unitCount", "ibr.intAlu.maxInputBits",
        "ace.rf.intAceRatio", "ace.rf.intTrackedReads", "ace.rf.intTrackedWrites",
        "ace.rf.intAceBitCycles",
        "sad.rob.ratio", "sad.iq.ratio", "sad.fu.ratio",
    ),
    "mult": (
        "ibr.intMult.ibrRatio", "ibr.intMult.inputBits", "ibr.intMult.issuedOps",
        "ibr.intMult.unitCount", "ibr.intMult.maxInputBits",
        "ace.rf.intAceRatio", "ace.rf.intAceBitCycles",
        "sad.rob.ratio", "sad.fu.ratio",
    ),
    "div": (
        "ibr.intDiv.ibrRatio", "ibr.intDiv.inputBits", "ibr.intDiv.issuedOps",
        "ibr.intDiv.unitCount", "ibr.intDiv.maxInputBits",
        "ace.rf.intAceRatio", "sad.rob.ratio", "sad.fu.ratio",
    ),
    "fpadd": (
        "ibr.fpAdd.ibrRatio", "ibr.fpAdd.inputBits", "ibr.fpAdd.issuedOps",
        "ibr.fpAdd.unitCount", "ibr.fpAdd.maxInputBits",
        "ace.rf.vecAceRatio", "ace.rf.vecAceBitCycles",
        "sad.vecPrf.ratio", "sad.fu.ratio",
    ),
    "fpmul": (
        "ibr.fpMult.ibrRatio", "ibr.fpMult.inputBits", "ibr.fpMult.issuedOps",
        "ibr.fpMult.unitCount", "ibr.fpMult.maxInputBits",
        "ace.rf.vecAceRatio", "ace.rf.vecAceBitCycles",
        "sad.vecPrf.ratio", "sad.fu.ratio",
    ),
    "rf": (
        "ace.rf.intAceRatio", "ace.rf.intTrackedReads", "ace.rf.intTrackedWrites",
        "ace.rf.intAceBitCycles", "ace.rf.intAceRegCycles",
        "ace.rf.intOverwriteDrops", "ace.rf.intSquashDiscards",
        "sad.intPrf.ratio", "sad.rob.ratio", "sad.fu.ratio",
    ),
    "vec": (
        "ace.rf.vecAceRatio", "ace.rf.vecTrackedReads", "ace.rf.vecTrackedWrites",
        "ace.rf.vecAceBitCycles", "ace.rf.vecAceRegCycles",
        "ace.rf.vecOverwriteDrops", "ace.rf.vecSquashDiscards",
        "sad.vecPrf.ratio", "sad.fu.ratio",
    ),
    "l1d": (
        "ace.l1d.aceRatio", "ace.l1d.trackedDemandReads",
        "ace.l1d.trackedDemandWrites", "ace.l1d.trackedFills",
        "ace.l1d.aceLineCycles", "ace.l1d.aceBitCycles",
        "ace.derived.l1d_events_per_cycle",
        "sad.lq.ratio", "sad.sq.ratio", "sad.rob.ratio",
        "ibr.intAlu.ibrRatio",
    ),
    "l1i": (
        "ace.l1i.aceRatio", "ace.l1i.trackedDemandReads",
        "ace.l1i.trackedFills", "ace.l1i.aceLineCycles",
        "ace.l1i.aceBitCycles",
        "sad.iq.ratio", "sad.rob.ratio", "sad.fu.ratio",
    ),
    "rob": (
        "sad.rob.ratio", "sad.rob.usedSum", "sad.rob.capacity",
        "sad.iq.ratio", "sad.iq.usedSum", "sad.fu.ratio",
        "ace.rf.intAceRatio", "ibr.intAlu.ibrRatio",
    ),
}


# --------------------------------------------------------------------------
# Assembly wrapper (upstream snap_tool initial state, ROI around the probe)
# --------------------------------------------------------------------------
WRAPPER_ASM = r"""
    .section .text
    .globl _start
_start:
    // mmap data1: addr=0x700000000, len=4 MiB, prot=RW, flags=PRIVATE|ANON|FIXED
    movz    x0, #7, lsl #32
    mov     x1, #0x400000
    mov     x2, #3
    mov     x3, #0x32
    mov     x4, #-1
    mov     x5, #0
    mov     x8, #222
    svc     #0
    mov     x19, x0

    // mmap data2: addr=0x100700000000
    movz    x0, #0x1007, lsl #32
    mov     x1, #0x400000
    mov     x2, #3
    mov     x3, #0x32
    mov     x4, #-1
    mov     x5, #0
    mov     x8, #222
    svc     #0
    mov     x20, x0

    // mmap stack: addr=0x2000000, len=64 KiB
    movz    x0, #0x200, lsl #16
    mov     x1, #0x10000
    mov     x2, #3
    mov     x3, #0x32
    mov     x4, #-1
    mov     x5, #0
    mov     x8, #222
    svc     #0
    add     x21, x0, #0x1000

    // "其余寄存器 = 0" per asm_common.S.inc
    mov     x0, #0
    mov     x1, #0
    mov     x2, #0
    mov     x3, #0
    mov     x4, #0
    mov     x5, #0
    mov     x8, #0
    mov     x9, #0
    mov     x10, #0
    mov     x11, #0
    mov     x12, #0
    mov     x13, #0
    mov     x14, #0
    mov     x15, #0
    mov     x16, #0
    mov     x17, #0
    mov     x18, #0
    mov     x22, #0
    mov     x23, #0
    mov     x24, #0
    mov     x25, #0
    mov     x26, #0
    mov     x27, #0
    mov     x28, #0
    mov     x29, #0
    mov     x30, #0

    mov     x6, x19
    mov     x7, x20
    mov     sp, x21
    mov     x19, #0
    mov     x20, #0
    mov     x21, #0

    mov     x0, #7
    mov     x1, #0
    bl      m5_work_begin

    mov     x0, #0
    mov     x1, #0
    bl      probe_entry

    mov     x0, #7
    mov     x1, #0
    bl      m5_work_end

    mov     x0, #0
    mov     x8, #93
    svc     #0
1:  b       1b
"""

TRAMPOLINE_ASM = r"""
    .section .text
    .globl __probe_fell_through
__probe_fell_through:
    // Exit 86 if a template ever runs past its appended ret.
    mov     x0, #86
    mov     x8, #93
    svc     #0
1:  b       1b
"""


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dump_last(stats_path):
    dumps = TOOL.stat_dumps(Path(stats_path))
    if not dumps:
        raise RuntimeError(f"no statistics dump in {stats_path}")
    return dumps[-1]


def numeric(stats, key):
    try:
        return float(stats[key])
    except KeyError:
        return None


def groups_for(sim_insts):
    """Choose straight-line Auto groups so 4G instructions match the probe."""
    if sim_insts is None or sim_insts <= 0:
        raise ValueError("template ROI has no simulated instructions")
    return max(1, int(round((sim_insts - 8.0) / OPS_PER_GROUP)))


def groups_for_loaded(sim_insts):
    """Groups for a variant with one post-index operand load per group.

    A post-index ``ldr`` is issued as more than one operation in this model
    (measured: +3.1 issued ops per group), so the per-group cost is 7, not 5.
    """
    if sim_insts is None or sim_insts <= 0:
        raise ValueError("template ROI has no simulated instructions")
    return max(1, int(round((sim_insts - 8.0) / 7.0)))


def select_auto_mode(document, structure):
    chosen, skipped = arms.select_target(document, [structure], None, 1)
    if not chosen:
        raise RuntimeError(f"AutoµSens selected no mode for {structure}")
    if len(chosen) != 1:
        raise RuntimeError(f"top-1 selection returned {chosen}")
    return chosen[0], skipped


def body_for(mode):
    return [mode] * OPS_PER_GROUP


_EXPECTED_RE = re.compile(r"    const uint64_t expected = UINT64_C\(0x([0-9a-fA-F]+)\);")
_EXPECTED_ASSIGN_RE = re.compile(r"expected = UINT64_C\(0x([0-9a-fA-F]+)\);")


def stabilise_expected(source):
    """Move the checksum constant to a volatile data load.

    The immediate value in the expected-checksum expression changes the pre-ROI
    instruction count when the checksum changes (GCC emits a different
    movz/movk sequence).  For a controlled D13-vs-load comparison the code must
    be identical and only the data value may differ, so the constant is stored
    in a volatile static and loaded at run time.
    """

    match = _EXPECTED_RE.search(source)
    if match is not None:
        value = match.group(1)
        source = source.replace(
            match.group(0), "    const uint64_t expected = expected_storage;")
    else:
        assignments = _EXPECTED_ASSIGN_RE.findall(source)
        if not assignments:
            raise ValueError("could not locate the expected-checksum expression")
        value = assignments[0]
        source = _EXPECTED_ASSIGN_RE.sub("expected = expected_storage;", source)
    source = source.replace(
        "int main(int argc",
        f"static volatile const uint64_t expected_storage = UINT64_C(0x{value});\n\n"
        "int main(int argc", 1)
    return source


#: Mnemonics whose first operand is a destination register.
_DEST_FIRST = {
    "mov", "movz", "movk", "movn", "add", "adds", "sub", "subs", "and",
    "ands", "orr", "eor", "eon", "mul", "madd", "msub", "udiv", "sdiv",
    "lsl", "lsr", "asr", "fmov", "movi", "dup", "crc32cx", "crc32cw",
    "crc32ch", "crc32cb", "crc32x", "crc32w", "crc32h", "crc32b",
}
_LOADS = {"ldr", "ldur", "ldp", "ldxr", "ldaxr", "ldar"}
_STORES = {"str", "stur", "stp", "stxr", "stlxr", "stlr"}
_COMPARE = {"cmp", "cmn", "tst", "fcmp", "fcmpe"}


def x12_first_access(text):
    """Return ``"write"`` or ``"read"`` for the first x12 mention in a seed.

    This is the static check behind the report's claim that D13's x12 operand
    injection cannot reach the fixed template body.  Macro invocations such as
    ``LOAD_ALT_10 x12`` are writes because the upstream macros build their
    register argument.
    """

    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line.startswith(".") or line.endswith(":"):
            continue
        if "x12" not in line:
            continue
        mnemonic = line.split(None, 1)[0].lower()
        rest = line.split(None, 1)[1] if " " in line else ""
        if mnemonic.startswith("load_"):
            return "write"
        if mnemonic in _LOADS:
            before_bracket = line.split("[", 1)[0]
            return "write" if "x12" in before_bracket else "read"
        if mnemonic in _STORES or mnemonic in _COMPARE:
            return "read"
        first = rest.split(",", 1)[0].strip()
        return "write" if first == "x12" else "read"
    return "absent"


# --------------------------------------------------------------------------
# C renderer for a straight-line generated body (optionally with D13 operands)
# --------------------------------------------------------------------------
def render_straightline(target, sequence, groups, operands=None):
    """Render a checked guest whose body is ``sequence`` repeated ``groups`` times.

    With ``operands`` (one value per group) each group starts with
    ``ldr x12, [ops], #8``; the independent Python oracle accounts for the same
    values.  Without operands x12 stays at the tool's default constant 3.
    """

    if not sequence or set(sequence) - set(MODE_ASM):
        raise ValueError("candidate requires a nonempty supported sequence")
    if groups < 1 or groups > 100000:
        raise ValueError("invalid group count")
    if operands is not None:
        if len(operands) != groups:
            raise ValueError("operands must have one value per group")
        operands = [int(value) & MASK64 for value in operands]

    expected = expected_checksum(sequence, groups, groups=1, operands=operands)
    lines = []
    if operands is not None:
        values = "".join(f"    UINT64_C(0x{value:016x}),\n" for value in operands)
        table = (f"\nstatic const uint64_t operands[{groups}] "
                 f"__attribute__((aligned(64))) = {{\n{values}}};\n")
        declaration = "    const uint64_t *operand_pointer = operands;\n"
        operand_output = ', [ops] "+r"(operand_pointer)'
    else:
        table = ""
        declaration = ""
        operand_output = ""

    for _ in range(groups):
        if operands is not None:
            lines.append('"ldr x12, [%[ops]], #8\\n\\t"')
        for mode in sequence:
            lines.append(f'"{MODE_ASM[mode]}\\n\\t"')
    body = "\n        ".join(lines)

    return f'''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <gem5/m5ops.h>

static uint64_t data[{MEMORY_WORDS}] __attribute__((aligned(64))) = {{
    [0] = UINT64_C(0x{INITIAL_MEMORY:016x}),
}};
{table}
static uint64_t mix(uint64_t hash, uint64_t value)
{{
    return (hash ^ value) * UINT64_C(1099511628211);
}}

static volatile const uint64_t expected_storage = UINT64_C(0x{expected:016x});

int main(int argc, char **argv)
{{
    if (argc != 2) return 2;
    char *end = NULL;
    errno = 0;
    const uint64_t requested = strtoull(argv[1], &end, 0);
    if (errno || !end || *end || end == argv[1] || requested != {groups}) return 2;
    const uint64_t expected = expected_storage;
    uint64_t count = 0;
    uint64_t value, addend, constant, fp_value, fp_operand;
    uint64_t initial_fp = UINT64_C(0x{INITIAL_FP:016x});
    uint64_t *buffer = data;
{declaration}    m5_work_begin(7, 0);
    __asm__ volatile(
        "mov x8, #3\\n\\t"
        "mov x10, #5\\n\\t"
        "mov x12, #3\\n\\t"
        "fmov d0, #1.5\\n\\t"
        "fmov d1, %[initial_fp]\\n\\t"
        {body}
        "mov %[value], x8\\n\\t"
        "mov %[addend], x10\\n\\t"
        "mov %[constant], x12\\n\\t"
        "fmov %[fp_value], d0\\n\\t"
        "fmov %[fp_operand], d1\\n\\t"
        : [value] "=r"(value), [addend] "=r"(addend),
          [constant] "=r"(constant), [fp_value] "=r"(fp_value),
          [fp_operand] "=r"(fp_operand){operand_output}
        : [buf] "r"(buffer), [initial_fp] "r"(initial_fp)
        : "x8", "x10", "x12", "d0", "d1", "cc", "memory");
    m5_work_end(7, 0);
    uint64_t checksum = UINT64_C(1469598103934665603);
    checksum = mix(checksum, value);
    checksum = mix(checksum, addend);
    checksum = mix(checksum, constant);
    checksum = mix(checksum, fp_value);
    checksum = mix(checksum, fp_operand);
    checksum = mix(checksum, count);
    for (unsigned index = 0; index < {MEMORY_WORDS}; ++index)
        checksum = mix(checksum, data[index]);
    printf("candidate={target} groups={groups} status=%s\\n",
           checksum == expected ? "PASS" : "FAIL");
    printf("%016llx\\n", (unsigned long long)checksum);
    return checksum == expected ? 0 : 1;
}}
'''


# --------------------------------------------------------------------------
# Build / run
# --------------------------------------------------------------------------
def prepare_dir(path):
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to reuse existing directory: {path}")
    path.mkdir(parents=True)
    return path


def compile_objects(bindir, cc):
    bindir = Path(bindir)
    bindir.mkdir(parents=True, exist_ok=True)
    (bindir / "wrapper.S").write_text(WRAPPER_ASM)
    (bindir / "trampoline.S").write_text(TRAMPOLINE_ASM)
    commands = {
        "wrapper.o": [cc, "-c", str(bindir / "wrapper.S"), "-o", str(bindir / "wrapper.o")],
        "trampoline.o": [cc, "-c", str(bindir / "trampoline.S"), "-o",
                         str(bindir / "trampoline.o")],
        "m5op.o": [cc, "-c", "-I" + str(GEM5_INCLUDE), str(M5OP), "-o",
                   str(bindir / "m5op.o")],
    }
    for name, command in commands.items():
        if not (bindir / name).is_file():
            subprocess.run(command, check=True, capture_output=True, text=True)
    return {name: bindir / name for name in commands}


def build_template_guest(seed, outdir, cc, objects):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    probe = outdir / "probe.S"
    probe.write_text(f'#include "{seed.path.name}"\n    ret\n')
    probe_o = outdir / "probe.o"
    subprocess.run([cc, "-c", "-I" + str(SEEDS_DIR),
                    "-D_start=probe_entry", str(probe), "-o", str(probe_o)],
                   check=True, capture_output=True, text=True)
    guest = outdir / "guest"
    subprocess.run([cc, "-static", "-nostdlib", "-no-pie",
                    str(objects["wrapper.o"]), str(probe_o),
                    str(objects["trampoline.o"]), str(objects["m5op.o"]),
                    "-o", str(guest)], check=True, capture_output=True, text=True)
    return probe, guest


def build_auto_guest(outdir, source_text, cc):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    source = outdir / "source.c"
    source.write_text(source_text)
    guest = outdir / "guest"
    TOOL.compile_guest(source, guest, cc)
    return source, guest


def run_gem5(gem5, run_dir, guest, workload_args, timeout=900):
    run_dir = Path(run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    # Fixed argv[0] and fixed working directory are part of the experimental
    # control: the SE initial stack contains argv/env, so a longer --cmd path
    # shifts the stack and changes cache warm-up.  Measured 1930 vs 1895 cycles
    # for the *same* l1d body when the o1/l1 path lengths differed.  Copy the
    # guest to the run directory and invoke it as the relative name ``guest``.
    local_guest = run_dir / "guest"
    if Path(guest).resolve() != local_guest:
        shutil.copy2(guest, local_guest)
    command = [
        str(gem5), "--outdir=" + str(run_dir),
        str(CONFIG), "--cpu=O3",
        "--cmd=guest", "--workload_args=" + str(workload_args),
        *METRIC_ARGS,
    ]
    env = TOOL.gem5_environment()
    env.pop("PWD", None)
    env.pop("OLDPWD", None)
    started = time.time()
    with (run_dir / "gem5.log").open("w") as log:
        try:
            completed = subprocess.run(
                command, stdout=log, stderr=subprocess.STDOUT, cwd=run_dir,
                env=env, timeout=timeout, check=False)
            returncode = completed.returncode
            timed_out = False
        except subprocess.TimeoutExpired:
            returncode = None
            timed_out = True
    elapsed = time.time() - started
    text = (run_dir / "gem5.log").read_text(errors="replace")
    status = None
    for line in text.splitlines():
        if "status=" in line:
            status = line.rsplit("status=", 1)[1].split()[0]
    error = None
    if timed_out:
        error = "timeout"
    elif returncode != 0:
        error = "crash"
    elif "fatal:" in text or "panic:" in text:
        error = "crash"
    return {
        "command": command,
        "returncode": returncode,
        "status": status,
        "error": error,
        "elapsed_s": round(elapsed, 3),
        "log_tail": "\n".join(text.splitlines()[-6:]),
    }


def metric_row(stats_path):
    doc = metrics.from_stats_path(stats_path)
    flat = metrics.flatten(doc)
    dumps = TOOL.stat_dumps(Path(stats_path))
    last = dumps[-1]
    first = dumps[0]
    # ``simInsts`` at the first dump is ROI-scoped: m5_work_begin resets the
    # gem5 statistics and m5_work_end dumps them before the Auto guest runs its
    # post-ROI checksum/print.  Do NOT use sad.issuedOps here: it counts issue
    # events (gem5 iq.instsIssued semantics; ldxr reports 7.849x the retired
    # count), not retired instructions.  Fall back to it only when a run has no
    # work_end dump at all.
    roi_insts = numeric(first, "simInsts") if len(dumps) > 1 else None
    if not roi_insts or roi_insts <= 0:
        roi_insts = flat.get("sad.globals.issuedOps")
    roi_cycles = flat.get("ace.rf.measuredCycles") or doc["windows"]["rf_ace"]
    meta = {
        "sim_insts": roi_insts,
        "cycles": roi_cycles,
        "ipc": ratio(roi_insts, roi_cycles),
        "issued_insts": roi_insts,
        "global_sim_insts": numeric(last, "simInsts"),
        "global_cycles": numeric(last, "board.processor.cores.core.numCycles"),
        "global_ipc": numeric(last, "board.processor.cores.core.ipc"),
        "dumps": len(dumps),
        "window_consistent": doc["window_consistent"],
        "windows": doc["windows"],
    }
    return doc, flat, meta


# --------------------------------------------------------------------------
# One seed = template + Auto default + Auto D13
# --------------------------------------------------------------------------
def cell_dirs(root, seed_id):
    base = Path(root) / "cells" / seed_id
    return {
        "auto-default": base / "auto-default",
        "auto-load": base / "auto-load",
        "auto-d13": base / "auto-d13",
    }


def run_seed(seed, mapping, document, root, cc, objects, gem5, timeout):
    base = Path(root) / "templates" / seed.id
    row_path = base / "row.json"
    if row_path.is_file():
        template_row = json.loads(row_path.read_text())
        meta = template_row["meta"]
    else:
        template_probe, template_guest = build_template_guest(seed, base, cc, objects)
        outcome = run_gem5(gem5, base / "run", template_guest, 0, timeout)
        stats_path = base / "run" / "stats.txt"
        if outcome["error"] or outcome["returncode"] != 0 or not stats_path.is_file():
            raise RuntimeError(f"{seed.id}: template run failed: {outcome}")
        _doc, flat, meta = metric_row(stats_path)
        if not meta["sim_insts"] or meta["sim_insts"] <= 0:
            raise RuntimeError(f"{seed.id}: template ROI has no instructions")
        template_row = {
            "kind": "template",
            "seed": seed.id,
            "sha256": seed.sha256,
            "source": str(template_probe),
            "guest": str(template_guest),
            "mapping": mapping.__dict__,
            "sequence": None,
            "groups": None,
            "outcome": outcome,
            "meta": meta,
            "flat": flat,
        }
        base.mkdir(parents=True, exist_ok=True)
        row_path.write_text(json.dumps(template_row, indent=2, sort_keys=True))

    roi_insts = meta["sim_insts"]
    g_plain = groups_for(roi_insts)
    g_load = groups_for_loaded(roi_insts)
    mode, skipped = select_auto_mode(document, mapping.auto)
    sequence = body_for(mode)
    variants = (
        ("auto-default", g_plain, None),
        ("auto-load", g_load, [3] * g_load),
        ("auto-d13", g_load, d13.operand_stream(g_load)[:g_load]),
    )
    for variant, groups, operands in variants:
        outdir = cell_dirs(root, seed.id)[variant]
        variant_row_path = outdir / "row.json"
        if variant_row_path.is_file():
            continue
        source_text = render_straightline(mapping.auto, sequence, groups,
                                          operands=operands)
        source, guest = build_auto_guest(outdir, source_text, cc)
        outcome = run_gem5(gem5, outdir / "run", guest, groups, timeout)
        stats_path = outdir / "run" / "stats.txt"
        if outcome["error"] or outcome["status"] != "PASS" or not stats_path.is_file():
            raise RuntimeError(f"{seed.id}/{variant}: run failed: {outcome}")
        _doc, flat, meta = metric_row(stats_path)
        row = {
            "kind": "auto",
            "seed": seed.id,
            "sha256": seed.sha256,
            "variant": variant,
            "structure": mapping.auto,
            "sequence": sequence,
            "mode": mode,
            "skipped": skipped,
            "groups": groups,
            "operands": operands,
            "source": str(source),
            "guest": str(guest),
            "mapping": mapping.__dict__,
            "outcome": outcome,
            "meta": meta,
            "flat": flat,
        }
        variant_row_path.write_text(json.dumps(row, indent=2, sort_keys=True))
    return template_row


def load_cell(root, seed_id, variant):
    path = Path(root) / "cells" / seed_id / variant / "row.json"
    return json.loads(path.read_text())


# --------------------------------------------------------------------------
# Analysis / artifacts
# --------------------------------------------------------------------------
def ratio(numerator, denominator):
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def compact(row):
    return {
        "kind": row["kind"],
        "seed": row["seed"],
        "variant": row.get("variant"),
        "structure": row.get("structure"),
        "sequence": row.get("sequence"),
        "mode": row.get("mode"),
        "groups": row.get("groups"),
        "meta": row["meta"],
        "outcome": {
            "status": row["outcome"].get("status"),
            "returncode": row["outcome"].get("returncode"),
            "error": row["outcome"].get("error"),
            "elapsed_s": row["outcome"].get("elapsed_s"),
        },
        "flat": row["flat"],
    }


def comparison(template, auto_default, auto_load, auto_d13, primary):
    def value(row):
        return row["flat"].get(primary) if row else None

    t = value(template)
    a = value(auto_default)
    load = value(auto_load)
    d = value(auto_d13)
    return {
        "primary": primary,
        "template": t,
        "auto_default": a,
        "auto_load": load,
        "auto_d13": d,
        "template_over_auto": ratio(t, a),
        "template_over_auto_load": ratio(t, load),
        "template_over_auto_d13": ratio(t, d),
        "d13_delta": (d - load) if (load is not None and d is not None) else None,
        "d13_ratio": ratio(d, load),
    }


def build_summary(root, document, run_id, protocol):
    cells = {}
    for seed in seed_templates.SEEDS:
        mapping = MAPPING_BY_SEED[seed.id]
        template_path = Path(root) / "templates" / seed.id / "row.json"
        template = json.loads(template_path.read_text())
        auto_default = load_cell(root, seed.id, "auto-default")
        auto_load = load_cell(root, seed.id, "auto-load")
        auto_d13 = load_cell(root, seed.id, "auto-d13")
        primary = PRIMARY[mapping.measured]
        cells[seed.id] = {
            "seed": seed.id,
            "sha256": seed.sha256,
            "mapping": mapping.__dict__,
            "template": compact(template),
            "auto_default": compact(auto_default),
            "auto_load": compact(auto_load),
            "auto_d13": compact(auto_d13),
            "comparison": comparison(template, auto_default, auto_load,
                                     auto_d13, primary),
        }

    aggregates = {}
    for mapping in MAPPINGS:
        key = mapping.measured
        rows = [cells[m.seed]["comparison"] for m in MAPPINGS if m.measured == key]
        ratios = [row["template_over_auto"] for row in rows
                  if row["template_over_auto"] is not None]
        load_ratios = [row["template_over_auto_load"] for row in rows
                       if row["template_over_auto_load"] is not None]
        d13 = [row["d13_ratio"] for row in rows if row["d13_ratio"] is not None]
        aggregates[key] = {
            "structures": len(rows),
            "primary": PRIMARY[key],
            "template_wins": sum(1 for value in ratios if value > 1.0),
            "auto_wins": sum(1 for value in ratios if value < 1.0),
            "ties": sum(1 for value in ratios if value == 1.0),
            "median_template_over_auto": median(ratios),
            "min_template_over_auto": min(ratios) if ratios else None,
            "max_template_over_auto": max(ratios) if ratios else None,
            "median_template_over_auto_load": median(load_ratios),
            "median_d13_ratio": median(d13),
        }

    summary = {
        "schema": "autousens.u20.summary.v1",
        "run_id": run_id,
        "protocol": protocol,
        "mappings": [mapping.__dict__ for mapping in MAPPINGS],
        "primary": PRIMARY,
        "focus": FOCUS,
        "aggregates": aggregates,
        "cells": cells,
    }
    path = Path(root) / "summary.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def median(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return None
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2.0


def write_metrics_csv(root, summary):
    rows = []
    for seed_id, cell in summary["cells"].items():
        for key in ("template", "auto_default", "auto_load", "auto_d13"):
            row = cell[key]
            meta = row["meta"]
            rows.append({
                "seed": seed_id,
                "nominal": cell["mapping"]["nominal"],
                "measured": cell["mapping"]["measured"],
                "auto_structure": cell["mapping"]["auto"],
                "arm": row["kind"],
                "variant": row.get("variant") or "",
                "sequence": "+".join(row.get("sequence") or []),
                "groups": row.get("groups") or "",
                "sim_insts": meta.get("sim_insts"),
                "cycles": meta.get("cycles"),
                "ipc": meta.get("ipc"),
                "window_consistent": meta.get("window_consistent"),
                **row["flat"],
            })
    keys = sorted({key for row in rows for key in row})
    ordered = ["seed", "nominal", "measured", "auto_structure", "arm", "variant",
               "sequence", "groups", "sim_insts", "cycles", "ipc",
               "window_consistent"] + [key for key in keys if key not in {
                   "seed", "nominal", "measured", "auto_structure", "arm",
                   "variant", "sequence", "groups", "sim_insts", "cycles",
                   "ipc", "window_consistent"}]
    path = Path(root) / "metrics.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ordered)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_target_csv(root, summary):
    fields = sorted({field for values in FOCUS.values() for field in values})
    rows = []
    for seed_id, cell in summary["cells"].items():
        mapping = cell["mapping"]
        focus = FOCUS[mapping["measured"]]
        for key in ("template", "auto_default", "auto_load", "auto_d13"):
            row = cell[key]
            meta = row["meta"]
            record = {
                "seed": seed_id,
                "nominal": mapping["nominal"],
                "measured": mapping["measured"],
                "auto_structure": mapping["auto"],
                "mapping": mapping["kind"],
                "arm": row["kind"],
                "variant": row.get("variant") or "",
                "groups": row.get("groups") or "",
                "sim_insts": meta.get("sim_insts"),
                "cycles": meta.get("cycles"),
                "window_consistent": meta.get("window_consistent"),
            }
            for field in fields:
                record[field] = row["flat"].get(field) if field in focus else ""
            rows.append(record)
    path = Path(root) / "target_metrics.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def fmt(value, digits=6):
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if digits == 0 and value.is_integer():
            return str(int(value))
        return f"{value:.{digits}g}"
    return str(value)


def markdown_tables(summary, root):
    lines = ["# AutoµSens u20 tables", ""]
    lines.append("## Mapping")
    lines.append("")
    lines.append("| seed | nominal | measured | Auto | kind | rationale |")
    lines.append("|---|---|---|---|---|---|")
    for mapping in MAPPINGS:
        lines.append(f"| {mapping.seed} | {mapping.nominal} | {mapping.measured} | "
                     f"{mapping.auto} | {mapping.kind} | {mapping.rationale} |")
    lines.append("")
    lines.append("## Headline metric")
    lines.append("")
    lines.append("| seed | target metric | template | auto | auto-load | auto+D13 | T/A | T/AL | D13/AL |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for seed in seed_templates.SEEDS:
        cell = summary["cells"][seed.id]
        comp = cell["comparison"]
        lines.append(
            f"| {seed.id} | {comp['primary']} | {fmt(comp['template'])} | "
            f"{fmt(comp['auto_default'])} | {fmt(comp['auto_load'])} | "
            f"{fmt(comp['auto_d13'])} | "
            f"{fmt(comp['template_over_auto'], 4)} | "
            f"{fmt(comp['template_over_auto_load'], 4)} | "
            f"{fmt(comp['d13_ratio'], 6)} |")
    lines.append("")
    lines.append("## Per measured structure")
    lines.append("")
    lines.append("| structure | n | primary | template wins | auto wins | median T/A | min T/A | max T/A | median D13/A |")
    lines.append("|---|---:|---|---:|---:|---:|---:|---:|---:|")
    for key, agg in summary["aggregates"].items():
        lines.append(
            f"| {key} | {agg['structures']} | {agg['primary']} | "
            f"{agg['template_wins']} | {agg['auto_wins']} | "
            f"{fmt(agg['median_template_over_auto'], 4)} | "
            f"{fmt(agg['min_template_over_auto'], 4)} | "
            f"{fmt(agg['max_template_over_auto'], 4)} | "
            f"{fmt(agg['median_d13_ratio'], 6)} |")
    lines.append("")
    lines.append("## Window / length audit")
    lines.append("")
    lines.append("| seed | template insts | template cycles | auto insts | auto cycles | auto-load insts | auto-load cycles | auto+D13 insts | auto+D13 cycles | windows consistent |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for seed in seed_templates.SEEDS:
        cell = summary["cells"][seed.id]
        t = cell["template"]["meta"]
        a = cell["auto_default"]["meta"]
        load = cell["auto_load"]["meta"]
        d = cell["auto_d13"]["meta"]
        lines.append(
            f"| {seed.id} | {fmt(t['sim_insts'], 0)} | {fmt(t['cycles'], 0)} | "
            f"{fmt(a['sim_insts'], 0)} | {fmt(a['cycles'], 0)} | "
            f"{fmt(load['sim_insts'], 0)} | {fmt(load['cycles'], 0)} | "
            f"{fmt(d['sim_insts'], 0)} | {fmt(d['cycles'], 0)} | "
            f"{fmt(t['window_consistent'])}/{fmt(a['window_consistent'])}/"
            f"{fmt(load['window_consistent'])}/{fmt(d['window_consistent'])} |")
    lines.append("")
    path = Path(root) / "tables.md"
    path.write_text("\n".join(lines) + "\n")
    return path


# --------------------------------------------------------------------------
# Protocol / verification
# --------------------------------------------------------------------------
def git_info():
    def run(*args):
        completed = subprocess.run(["git", *args], cwd=ROOT, text=True,
                                   capture_output=True, check=False)
        return completed.stdout.strip()

    status = run("status", "--porcelain")
    return {
        "commit": run("rev-parse", "HEAD") or None,
        "dirty_files": len([line for line in status.splitlines() if line]),
    }


def protocol_document(run_id, map_path):
    return {
        "schema": "autousens.u20.protocol.v1",
        "run_id": run_id,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "git": git_info(),
        "gem5": str(GEM5),
        "gem5_sha256": sha256_file(GEM5) if GEM5.is_file() else None,
        "config": str(CONFIG),
        "config_sha256": sha256_file(CONFIG),
        "map": str(map_path),
        "map_sha256": sha256_file(map_path),
        "seed_manifest_sha256": sha256_file(seed_templates.MANIFEST),
        "seeds": [{"id": seed.id, "sha256": seed.sha256}
                  for seed in seed_templates.SEEDS],
        "model": {
            "config": "configs/se/arm_chaos.py",
            "cpu": "O3",
            "args": list(METRIC_ARGS),
            "proxy": "TaiShan V110 proxy (--kp920_proxy), not cycle-accurate",
        },
        "protocol": {
            "template_arm": "one faithful execution; upstream x6/x7/sp initial state",
            "auto_arm": "top-1 mode x4, straight-line G groups; G matches template ROI",
            "d13_arm": "same body/G; one D13 x12 per group",
            "template_d13": "not applicable: no seed reads x12 before writing it",
        },
    }


def verify_run(root):
    root = Path(root)
    summary = json.loads((root / "summary.json").read_text())
    problems = []
    if len(summary["cells"]) != 20:
        problems.append(f"expected 20 cells, found {len(summary['cells'])}")
    for seed_id, cell in summary["cells"].items():
        for key in ("template", "auto_default", "auto_load", "auto_d13"):
            row = cell[key]
            if row["outcome"]["error"]:
                problems.append(f"{seed_id}/{key}: {row['outcome']['error']}")
            if key != "template" and row["outcome"]["status"] != "PASS":
                problems.append(f"{seed_id}/{key}: status {row['outcome']['status']}")
            if not row["meta"]["sim_insts"]:
                problems.append(f"{seed_id}/{key}: no simInsts")
        if not cell["comparison"]["primary"]:
            problems.append(f"{seed_id}: missing primary metric")
    if problems:
        for problem in problems:
            print("FAIL:", problem)
        return 1
    print(f"verified {len(summary['cells'])} cells x 4 arms; "
          f"all Auto runs PASS, all rows have metrics")
    return 0


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--outroot", default=str(ROOT / "m5out/autousens-eval"))
    parser.add_argument("--map", default=str(DEFAULT_MAP))
    parser.add_argument("--gem5", default=str(GEM5))
    parser.add_argument("--cc", default="aarch64-openEuler-linux-gcc")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--only", default="",
                        help="comma-separated seed ids for a partial run")
    parser.add_argument("--verify", metavar="RUN_ID_OR_DIR")
    args = parser.parse_args(argv)

    if args.verify:
        target = Path(args.verify)
        if not target.is_dir():
            target = Path(args.outroot) / args.verify
        return verify_run(target)

    map_path = Path(args.map)
    if not map_path.is_file():
        raise SystemExit(f"structure map not found: {map_path}")
    document = json.loads(map_path.read_text())
    unknown = [mapping.auto for mapping in MAPPINGS if mapping.auto not in TOOL.STRUCTURES]
    if unknown:
        raise SystemExit(f"mapping names unsupported structures: {unknown}")
    if len(MAPPINGS) != len(seed_templates.SEEDS):
        raise SystemExit("mapping count does not match the 20 seeds")

    root = Path(args.outroot) / args.run_id
    if root.exists():
        raise SystemExit(f"run directory already exists: {root}")
    root.mkdir(parents=True)
    protocol = protocol_document(args.run_id, map_path)
    (root / "protocol.json").write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")

    objects = compile_objects(root / "bin", args.cc)
    gem5 = Path(args.gem5).resolve()
    if not gem5.is_file():
        raise SystemExit(f"gem5 binary not found: {gem5}")

    only = {item.strip() for item in args.only.split(",") if item.strip()}
    if only:
        unknown_seeds = only - {seed.id for seed in seed_templates.SEEDS}
        if unknown_seeds:
            raise SystemExit(f"unknown seed ids: {sorted(unknown_seeds)}")
    seeds = [seed for seed in seed_templates.SEEDS
             if not only or seed.id in only]

    def task(seed):
        mapping = MAPPING_BY_SEED[seed.id]
        return run_seed(seed, mapping, document, root, args.cc, objects, gem5,
                        args.timeout)

    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(task, seed) for seed in seeds]
        for seed, future in zip(seeds, futures):
            try:
                future.result()
                print(f"OK {seed.id}")
            except Exception as error:  # noqa: BLE001 - recorded, not hidden
                failures.append((seed.id, str(error)))
                print(f"FAIL {seed.id}: {error}")
    if failures:
        (root / "failures.json").write_text(json.dumps(failures, indent=2))
        print(f"{len(failures)} seed(s) failed; see {root}/failures.json")
        return 1
    if only:
        print(f"partial run complete for {len(seeds)} seed(s); summary skipped")
        return 0

    summary = build_summary(root, document, args.run_id, protocol)
    write_metrics_csv(root, summary)
    write_target_csv(root, summary)
    markdown_tables(summary, root)
    print(f"summary: {root / 'summary.json'}")
    print(f"metrics: {root / 'metrics.csv'}")
    print(f"target : {root / 'target_metrics.csv'}")
    print(f"tables : {root / 'tables.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
