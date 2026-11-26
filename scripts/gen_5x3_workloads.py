#!/usr/bin/env python3
"""Generate the 60 FPU/SIMD 5x3 context workloads (12 models x 5 contexts).

Each emitted ELF is a freestanding AArch64 SE guest that executes the frozen
per-model target instruction exactly N times inside a ROI loop, writing one
128-byte raw record per dynamic execution to stdout.

Context semantics (authoritative: Excel sheet 24_Context_5x12):
  C01  Baseline Activation     shortest activate -> execute -> consume path
  C02  Activation Variation    scalar: different producer chain, bit-identical
                               SIMD : non-target lanes changed, target lane kept
  C03  Limited Dependency      faulted result captured then overwritten + sentinel
  C04  Extended Dependency     >=2 levels RAW / multiple consumers
  C05  Control & Speculation   train-then-mispredict; last execution squashed

Record layout (128 bytes LE): magic|model|context|mode|iter|raw0|raw1|
  fpsr|fpcr|nzcv|lane|status|raw2|qc|resv|resv
  (mode == 5 marks the 5x3 batch; status==0x55 marks a squashed slot)
"""
import os, subprocess, sys

OUT_SRC = os.path.join(os.path.dirname(__file__), '..', 'work', 'FPU_SIMD_5x3_FORMAL',
                       'workloads', 'src')
OUT_BIN = os.path.join(os.path.dirname(__file__), '..', 'work', 'FPU_SIMD_5x3_FORMAL',
                       'workloads', 'build')
MAGIC = 0x3149554650465046
CC = 'aarch64-linux-gnu-gcc'
N_STD = 100     # C01..C04 loop count
N_C05 = int(os.environ.get('N_C05', '9'))   # measurement target executions (8 commit + 1 squash)
TRAIN = int(os.environ.get('TRAIN', '40'))  # branch-training iterations (target gated off)

# ---------------------------------------------------------------------------
# Per-model frozen facts (from 02_Models / 24_Context_5x12 AnchorInput_R03)
# fields: kind, inst, sources, lane, consume(C01/C03), C04 chain + final + mid
# ---------------------------------------------------------------------------
MODELS = {
    1: dict(kind='scalar', inst='fadd s0, s1, s2',
            src1=0x40800005, src2=0x34800000, src3=None, xa=0, xb=0, lane=-1,
            gpr_consume=False, pre_chain='',
            chain=('fadd s4, s0, s0', 'fmul s5, s4, s4', 'fadd s6, s5, s0'),
            final=('fmov w10, s6', 'str w10, [x9]'),
            mid=('fmov w11, s4', 'str x11, [x8, #96]')),
    2: dict(kind='scalar', inst='fmul s0, s1, s2',
            src1=0xBE800000, src2=0x41000000, src3=None, xa=0, xb=0, lane=-1,
            gpr_consume=False, pre_chain='',
            chain=('fmul s4, s0, s0', 'fadd s5, s4, s4', 'fmul s6, s5, s0'),
            final=('fmov w10, s6', 'str w10, [x9]'),
            mid=('fmov w11, s4', 'str x11, [x8, #96]')),
    3: dict(kind='scalar', inst='fmadd s0, s1, s2, s3',
            src1=0xC0000000, src2=0x40800000, src3=0x40400000, xa=0, xb=0, lane=-1,
            gpr_consume=False, pre_chain='',
            chain=('fadd s4, s0, s0', 'fmul s5, s4, s4', 'fsub s6, s5, s0'),
            final=('fmov w10, s6', 'str w10, [x9]'),
            mid=('fmov w11, s4', 'str x11, [x8, #96]')),
    4: dict(kind='scalar', inst='fdiv s0, s1, s2',
            src1=0x3F800000, src2=0x41000000, src3=None, xa=0, xb=0, lane=-1,
            gpr_consume=False, pre_chain='',
            chain=('fadd s4, s0, s0', 'fmul s5, s4, s4', 'fdiv s6, s5, s0'),
            final=('fmov w10, s6', 'str w10, [x9]'),
            mid=('fmov w11, s4', 'str x11, [x8, #96]')),
    5: dict(kind='scalar', inst='fsqrt s0, s1',
            src1=0xBE800000, src2=None, src3=None, xa=0, xb=0, lane=-1,
            gpr_consume=False, pre_chain='',
            chain=('fadd s4, s0, s0', 'fmul s5, s4, s4', 'fadd s6, s5, s0'),
            final=('fmov w10, s6', 'str w10, [x9]'),
            mid=('fmov w11, s4', 'str x11, [x8, #96]')),
    6: dict(kind='gpr', inst='fcvtzs x0, s1',
            src1=0x40100000, src2=None, src3=None, xa=0, xb=0, lane=-1,
            gpr_consume=True, pre_chain='',
            chain=('add x4, x0, x0', 'mul x5, x4, x4', 'sub x6, x5, x0'),
            final=('mov x10, x6', 'str x10, [x9]'),
            mid=('mov x11, x4', 'str x11, [x8, #96]')),
    7: dict(kind='fcmp', inst='fcmp s1, s2',
            src1=0xC0400000, src2=0xC0A00000, src3=None, xa=0x11, xb=0x22, lane=-1,
            gpr_consume=False, pre_chain='csel x10, x5, x6, lo',
            chain=('add x4, x10, x10', 'mul x5, x4, x4', 'sub x6, x5, x10'),
            final=('mov x10, x6', 'str x10, [x9]'),
            mid=('mov x11, x4', 'str x11, [x8, #96]')),
    8: dict(kind='vec', inst='uqadd v0.16b, v1.16b, v2.16b', lane=7,
            v1=[0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x80,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F],
            v2=[0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x80,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01],
            v1b=[0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x80,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            v2b=[0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x80,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02],
            chain=('add v3.16b, v0.16b, v0.16b', 'add v4.16b, v3.16b, v0.16b'),
            final=('str q4, [x9]',), mid=('str q3, [x8, #96]',)),
    9: dict(kind='vec', inst='umull v0.8h, v1.8b, v2.8b', lane=3,
            v1=[0x01,0x02,0x03,0x11,0x05,0x06,0x07,0x08],
            v2=[0x02,0x02,0x02,0x21,0x02,0x02,0x02,0x02],
            v1b=[0x01,0x01,0x01,0x11,0x01,0x01,0x01,0x01],
            v2b=[0x03,0x03,0x03,0x21,0x03,0x03,0x03,0x03],
            chain=('add v3.8h, v0.8h, v0.8h', 'add v4.8h, v3.8h, v0.8h'),
            final=('str q4, [x9]',), mid=('str q3, [x8, #96]',)),
    10: dict(kind='vec', inst='ushl v0.16b, v1.16b, v2.16b', lane=7,
             v1=[0x00,0x01,0x02,0x03,0x04,0x05,0x06,0xF3,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F],
             v2=[0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFD,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
             v1b=[0x11,0x11,0x11,0x11,0x11,0x11,0x11,0xF3,0x11,0x11,0x11,0x11,0x11,0x11,0x11,0x11],
             v2b=[0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFD,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
             chain=('add v3.16b, v0.16b, v0.16b', 'add v4.16b, v3.16b, v0.16b'),
             final=('str q4, [x9]',), mid=('str q3, [x8, #96]',)),
    11: dict(kind='vec', inst='tbl v0.16b, {v1.16b}, v2.16b', lane=7,
             v1=list(range(0xA0, 0xB0)),
             v2=[0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x20,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F],
             v1b=list(range(0xA0, 0xB0)),
             v2b=[0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x20,0x18,0x19,0x1A,0x1B,0x1C,0x1D,0x1E,0x1F],
             chain=('add v3.16b, v0.16b, v0.16b', 'add v4.16b, v3.16b, v0.16b'),
             final=('str q4, [x9]',), mid=('str q3, [x8, #96]',)),
    12: dict(kind='xtn2', inst='xtn2 v0.16b, v1.8h', lane=-1,
             v1=[0x1220,0x1221,0x1222,0x1223,0x1224,0x1225,0x1226,0x1227],
             v0old=[0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF],
             v0old_b=[0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0xAA,0xAA,0xAA,0xAA,0xAA,0xAA,0xAA,0xAA],
             chain=('add v2.16b, v0.16b, v0.16b', 'add v3.16b, v2.16b, v0.16b'),
             final=('str q3, [x9]',), mid=('str q2, [x8, #96]',)),
}


def lo(v): return v & 0xffff
def hi(v): return (v >> 16) & 0xffff


def consume(m, gpr):
    """The single consumer that reads the target result and stores raw0."""
    k = m['kind']
    if k in ('scalar',):
        return ('fmov w10, s0\n        str w10, [x9]')
    if k == 'gpr':
        return ('str x0, [x9]')
    if k == 'fcmp':
        return ('csel x10, x5, x6, lo\n        str x10, [x9]')
    if k in ('vec', 'xtn2'):
        return ('str q0, [x9]')
    raise AssertionError(k)


def data_section(m):
    lines = ['.section .data', '.align 4']
    if m['kind'] in ('vec',):
        lines.append('v1_data: .byte ' + ', '.join(str(b) for b in m['v1']))
        lines.append('v2_data: .byte ' + ', '.join(str(b) for b in m['v2']))
        lines.append('v1b_data: .byte ' + ', '.join(str(b) for b in m['v1b']))
        lines.append('v2b_data: .byte ' + ', '.join(str(b) for b in m['v2b']))
    elif m['kind'] == 'xtn2':
        hw = m['v1']
        lines.append('v1_data: .byte ' + ', '.join(
            '0x%02x, 0x%02x' % (h & 0xff, (h >> 8) & 0xff) for h in hw))
        lines.append('v0old_data: .byte ' + ', '.join(str(b) for b in m['v0old']))
        lines.append('v0oldb_data: .byte ' + ', '.join(str(b) for b in m['v0old_b']))
    else:
        words = [m['src1']]
        if m['src2'] is not None: words.append(m['src2'])
        if m['src3'] is not None: words.append(m['src3'])
        lines.append('src_data: .word ' + ', '.join('0x%08x' % w for w in words))
    lines += ['.section .bss', '.align 8', 'outbuf: .skip 16384']
    return '\n'.join(lines)


def _scalar_src_load(m, variant):
    """movz/movk (r03) or mov+lsl+add (c02) producer chain."""
    lines = []
    srcs = [m['src1'], m['src2'], m['src3']]
    regs = ['s1', 's2', 's3']
    for i, src in enumerate(srcs):
        if src is None: continue
        if variant == 'r03':
            lines.append('    movz w7, #0x%x' % lo(src))
            lines.append('    movk w7, #0x%x, lsl #16' % hi(src))
        else:
            lines.append('    mov w7, #0x%x' % hi(src))
            lines.append('    mov w6, #0x%x' % lo(src))
            lines.append('    lsl w7, w7, #16')
            lines.append('    add w7, w7, w6')
        lines.append('    fmov %s, w7' % regs[i])
    return '\n'.join(lines)


def load_inputs(m, variant='r03'):
    k = m['kind']
    if k in ('scalar', 'gpr', 'fcmp'):
        s = _scalar_src_load(m, variant)
        if k == 'fcmp':
            s += '\n    mov x5, #0x%x\n    mov x6, #0x%x' % (m['xa'], m['xb'])
        return s
    if k in ('vec',):
        tab = 'v1b_data' if variant == 'c02' else 'v1_data'
        tab2 = 'v2b_data' if variant == 'c02' else 'v2_data'
        return ('    adr x7, %s\n    ldr q1, [x7]\n'
                '    adr x7, %s\n    ldr q2, [x7]' % (tab, tab2))
    if k == 'xtn2':
        tab = 'v0oldb_data' if variant == 'c02' else 'v0old_data'
        return ('    adr x7, %s\n    ldr q0, [x7]\n'
                '    adr x7, v1_data\n    ldr q1, [x7]' % tab)
    raise AssertionError(k)


def rec_header(model, ctx):
    return ('    ldr x10, =0x%x\n    str x10, [x8, #0]\n'
            '    mov x10, #%d\n    str x10, [x8, #8]\n'
            '    mov x10, #%d\n    str x10, [x8, #16]\n'
            '    mov x10, #5\n    str x10, [x8, #24]\n'
            '    str x21, [x8, #32]' % (MAGIC, model, ctx))


def rec_flags(lane):
    return ('    mrs x10, fpsr\n    str x10, [x8, #56]\n'
            '    ubfx x11, x10, #27, #1\n    str x11, [x8, #104]\n'
            '    mrs x10, fpcr\n    str x10, [x8, #64]\n'
            '    mrs x10, nzcv\n    str x10, [x8, #72]\n'
            '    mov x10, #%d\n    str x10, [x8, #80]' % lane)


def ctx_num(ctx): return int(ctx[1:])


def body_C01(mid, m):
    return ('    add x8, x20, x21, lsl #7\n    add x9, x8, #40\n'
            + rec_header(mid, 1) + '\n' + load_inputs(m, 'r03') + '\n'
            + 'fpu_target_r:\n    %s\n        %s\n' % (m['inst'], consume(m, False))
            + rec_flags(m['lane']) + '\n    mov x10, #0\n    str x10, [x8, #88]\n'
            + '    str xzr, [x8, #96]\n')


def body_C02(mid, m):
    return ('    add x8, x20, x21, lsl #7\n    add x9, x8, #40\n'
            + rec_header(mid, 2) + '\n' + load_inputs(m, 'c02') + '\n'
            + 'fpu_target_r:\n    %s\n        %s\n' % (m['inst'], consume(m, False))
            + rec_flags(m['lane']) + '\n    mov x10, #0\n    str x10, [x8, #88]\n'
            + '    str xzr, [x8, #96]\n')


def body_C03(mid, m):
    k = m['kind']
    # Limited Dependency: the faulted destination is OVERWRITTEN with a fixed
    # correct value BEFORE any consumer reads it, so the error is produced but
    # never reaches a software-visible consumer (raw0 == control).
    s = ('    add x8, x20, x21, lsl #7\n    add x9, x8, #40\n'
         + rec_header(mid, 3) + '\n' + load_inputs(m, 'r03') + '\n'
         + 'fpu_target_r:\n    %s\n' % m['inst'])
    # overwrite destination immediately (before any consumer reads it)
    if k in ('scalar',):
        s += '\n    movz w7, #0x3f80\n    movk w7, #0, lsl #16\n    fmov s0, w7'
    elif k == 'gpr':
        s += '\n    mov x0, #0'
    elif k == 'fcmp':
        # overwrite the faulted NZCV with a deterministic value before CSEL
        s += '\n    cmp xzr, xzr'
    elif k in ('vec', 'xtn2'):
        s += '\n    movi v0.16b, #0'
    # now consume the OVERWRITTEN (correct) value -> raw0
    s += '\n        %s' % consume(m, False)
    s += '\n' + rec_flags(m['lane'])
    # sentinel (correct-path) -> raw2
    s += ('\n    movz x10, #0x5678\n    movk x10, #0x1234, lsl #16\n'
          '    str x10, [x8, #96]\n'
          '    mov x10, #0\n    str x10, [x8, #88]\n')
    return s


def body_C04(mid, m):
    s = ('    add x8, x20, x21, lsl #7\n    add x9, x8, #40\n'
         + rec_header(mid, 4) + '\n' + load_inputs(m, 'r03') + '\n'
         + 'fpu_target_r:\n    %s\n' % m['inst'])
    if m.get('pre_chain'):
        s += '        %s\n' % m['pre_chain']
    for c in m['chain']:
        s += '        %s\n' % c
    for c in m['final']:
        s += '        %s\n' % c
    for c in m['mid']:
        s += '        %s\n' % c
    s += rec_flags(m['lane']) + '\n    mov x10, #0\n    str x10, [x8, #88]\n'
    return s


def gen(mid, ctx):
    m = MODELS[mid]
    n = N_C05 if ctx == 'C05' else N_STD
    if ctx == 'C05':
        loop_top = 'c05_loop:\n'
        # Control & Speculation: a branch is trained "taken" over TRAIN
        # iterations (target gated off), then during the measurement phase the
        # target executes N times. On the final measurement the branch is
        # mispredicted (predicted taken, actually not-taken) so the last target
        # execution runs speculatively and is squashed on recovery. T03 =
        # ceil(0.9*N) therefore lands on the squashed execution.
        inner = (
            '    mov w4, #0x3f800000\n'
            '    mov w26, #0x40000000\n'
            '    cmp x19, #0\n'
            '    ccmp x24, #1, #0, eq\n'
            '    csel w4, w26, w4, eq\n'
            '    fmov s20, w4\n'
            '    fdiv s20, s20, s21\n'
            '    fdiv s20, s20, s21\n'
            '    fdiv s20, s20, s21\n'
            '    fdiv s20, s20, s21\n'
            '    fdiv s20, s20, s21\n'
            '    fdiv s20, s20, s21\n'
            '    fdiv s20, s20, s21\n'
            '    fdiv s20, s20, s21\n'
            '    fcmp s20, s21\n'
            'c05_branch:\n'
            '    b.eq c05_taken\n'
            '    b c05_done\n'
            'c05_taken:\n'
            '    cbz x19, c05_emit\n'
            '    sub x19, x19, #1\n'
            '    b c05_loop\n'
            'c05_emit:\n'
            '    add x8, x20, x21, lsl #7\n'
            '    add x9, x8, #40\n'
            + rec_header(mid, 5) + '\n' + load_inputs(m, 'r03') + '\n'
            + 'fpu_target_r:\n    %s\n        %s\n' % (m['inst'], consume(m, False))
            + rec_flags(m['lane'])
            + '\n    mov x10, #0\n    str x10, [x8, #88]\n    str xzr, [x8, #96]\n'
            + '    add x21, x21, #1\n    sub x24, x24, #1\n    b c05_loop\n')
        done = '''c05_done:
    add x8, x20, x21, lsl #7
    ldr x10, =0x%x
    str x10, [x8, #0]
    mov x10, #%d
    str x10, [x8, #8]
    mov x10, #%d
    str x10, [x8, #16]
    mov x10, #5
    str x10, [x8, #24]
    str x21, [x8, #32]
    str xzr, [x8, #40]
    str xzr, [x8, #48]
    mrs x10, fpsr
    str x10, [x8, #56]
    mrs x10, fpcr
    str x10, [x8, #64]
    mrs x10, nzcv
    str x10, [x8, #72]
    mov x10, #%d
    str x10, [x8, #80]
    mov x10, #0x55
    str x10, [x8, #88]
    str xzr, [x8, #96]
    str xzr, [x8, #104]
    mov x2, #%d
    lsl x2, x2, #7
    adr x1, outbuf
    b write_exit
''' % (MAGIC, mid, ctx_num(ctx), m['lane'], n)
        return ('''// 5x3 context workload FPU-M%03d %s (model %d, C05)
.text
.global _start
_start:
    msr fpsr, xzr
    msr fpcr, xzr
    adr x20, outbuf
    mov x21, #0
    mov x19, #%d
    mov x24, #%d
    mov w4, #0x3f800000
    fmov s21, w4
%s
%s
%s

write_exit:
    mov x0, #1
    mov x8, #64
    svc #0
    mov x0, #0
    mov x8, #93
    svc #0

%s
''' % (mid, ctx, mid, TRAIN, n, loop_top, inner, done, data_section(m)))

    body = {'C01': body_C01, 'C02': body_C02, 'C03': body_C03,
            'C04': body_C04}[ctx](mid, m)
    return ('''// 5x3 context workload FPU-M%03d %s (model %d, %s)
.text
.global _start
_start:
    msr fpsr, xzr
    msr fpcr, xzr
    adr x20, outbuf
    mov x21, #0
    mov x22, #%d
loop_top:
%s
    add x21, x21, #1
    cmp x21, x22
    b.ne loop_top
    mov x2, x22
    lsl x2, x2, #7
    adr x1, outbuf
write_exit:
    mov x0, #1
    mov x8, #64
    svc #0
    mov x0, #0
    mov x8, #93
    svc #0

%s
''' % (mid, ctx, mid, ctx, n, body, data_section(m)))


def build():
    os.makedirs(OUT_SRC, exist_ok=True)
    os.makedirs(OUT_BIN, exist_ok=True)
    ok, fail = 0, []
    for mid in range(1, 13):
        for ctx in ('C01', 'C02', 'C03', 'C04', 'C05'):
            asm = gen(mid, ctx)
            src = os.path.join(OUT_SRC, 'fpu_%02d_%s.S' % (mid, ctx))
            with open(src, 'w') as f:
                f.write(asm)
            elf = os.path.join(OUT_BIN, 'fpu_%02d_%s' % (mid, ctx))
            p = subprocess.run([CC, '-nostdlib', '-static', '-o', elf, src],
                               capture_output=True, text=True)
            if p.returncode != 0:
                fail.append((mid, ctx, p.stderr.strip()))
            else:
                ok += 1
    print('built %d/%d workloads' % (ok, 60))
    for mid, ctx, err in fail:
        print('FAIL fpu_%02d_%s: %s' % (mid, ctx, err.splitlines()[-1] if err else ''))
    return len(fail) == 0


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'dump':
        print(gen(int(sys.argv[2]), sys.argv[3]) if len(sys.argv) > 3
              else '\n'.join(gen(m, c) for m in range(1, 13) for c in
                             ('C01', 'C02', 'C03', 'C04', 'C05')))
    else:
        sys.exit(0 if build() else 1)