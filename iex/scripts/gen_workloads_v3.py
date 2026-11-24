#!/usr/bin/env python3
"""Generate the 35 frozen Model x Context AArch64 kernels for v3.

Each ELF is a freestanding static binary with embedded inputs, fixed mask,
the model target, the frozen context-specific consumer chain and a raw
two-word output region.  Symbols are extracted from the linked ELF and
cross-checked against objdump so the injection selector can bind an exact
target PC.
"""
import argparse
import csv
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iex_oracle as oracle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "workloads", "v3", "src")
BUILD = os.path.join(ROOT, "workloads", "v3", "build")
XCC = "aarch64-openEuler-linux-gcc"
MASK = oracle.MASK
N_EPISODES = 128


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise SystemExit("failed: %s\n%s\n%s" %
                         (" ".join(cmd), p.stdout, p.stderr))
    return p.stdout


def common_c():
    return r'''
#define N_EP %d
typedef unsigned long u64;
volatile u64 iex_output[2 * N_EP] __attribute__((aligned(16)));
extern const char iex_context[];

static long
sys_write(int fd, const void *buf, unsigned long n)
{
    register long x8 __asm__("x8") = 64;
    register long x0 __asm__("x0") = fd;
    register const void *x1 __asm__("x1") = buf;
    register unsigned long x2 __asm__("x2") = n;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x8)
                     : "memory");
    return x0;
}

static void __attribute__((noreturn))
sys_exit(int code)
{
    register long x8 __asm__("x8") = 93;
    register long x0 __asm__("x0") = code;
    __asm__ volatile("svc #0" : : "r"(x0), "r"(x8) : "memory");
    __builtin_unreachable();
}

static char *
hex64(char *p, u64 v)
{
    static const char d[] = "0123456789ABCDEF";
    int i;
    *p++ = '0';
    *p++ = 'x';
    for (i = 60; i >= 0; i -= 4)
        *p++ = d[(v >> i) & 0xf];
    return p;
}

void
iex_print_mem(void)
{
    char buf[256];
    char *p = buf;
    const char *c;
    int i;
    for (c = iex_context; *c; ++c)
        *p++ = *c;
    for (i = 0; i < N_EP; ++i) {
        *p++ = ',';
        p = hex64(p, iex_output[2 * i]);
        *p++ = ',';
        p = hex64(p, iex_output[2 * i + 1]);
        if (p - buf > 200) {
            sys_write(1, buf, (unsigned long)(p - buf));
            p = buf;
        }
    }
    *p++ = '\n';
    sys_write(1, buf, (unsigned long)(p - buf));
    sys_exit(0);
}
''' % (N_EPISODES,)


def asm_for(model, ctx, vec):
    a, b = vec["a"], vec["b"]
    tg, tf = vec["final_golden"], vec["final_fault"]
    L = []
    add = L.append
    add("\t.arch armv8-a")
    add("\t.text")
    add("\t.global _start")
    add("\t.type _start,%function")
    add("_start:")
    add("\tbl iex_run")
    add("\tbl iex_print_mem")
    add("\t.global iex_run")
    add("\t.type iex_run,%function")
    add("iex_run:")
    add("\tldr x9, =0x%016X" % a)
    add("\tldr x10, =0x%016X" % b)
    add("\tldr x11, =0x%016X" % MASK)
    add("\tldr x12, =iex_output")
    if model == "IEX-M006":
        op1, op2 = oracle.M006_CSEL[ctx]
        add("\tldr x5, =0x%016X" % op1)
        add("\tldr x6, =0x%016X" % op2)

    if ctx != "C05":
        # Every context is a full ROI of N episodes.  A single eligible
        # target is not enough for the frozen N>=20 gate.
        add("\tmov x20, #%d" % N_EPISODES)
        add(".Lloop:")
        add("\t.global iex_roi_start")
        add("iex_roi_start:")
        add("\tldr x9, =0x%016X" % a)
        add("\tldr x10, =0x%016X" % b)
        if model == "IEX-M006":
            op1, op2 = oracle.M006_CSEL[ctx]
            add("\tldr x5, =0x%016X" % op1)
            add("\tldr x6, =0x%016X" % op2)

    if ctx in ("C01", "C02"):
        if model == "IEX-M005":
            m = oracle.M005_MARKERS[ctx]
            cond = "eq" if ctx != "C02" else "ne"
            add("\tcmp x9, x10")
            add("\t.global iex_target_pc")
            add("iex_target_pc:")
            add("\tb.%s .Ltaken" % cond)
            add("\tldr x2, =0x%016X" % m["eq_fall" if ctx != "C02"
                                               else "ne_fall"])
            add("\tb .Lmerge")
            add(".Ltaken:")
            add("\tldr x2, =0x%016X" % m["eq_taken" if ctx != "C02"
                                               else "ne_taken"])
            add(".Lmerge:")
            raw = "x2"
        else:
            add("\t.global iex_target_pc")
            add("iex_target_pc:")
            if model == "IEX-M001":
                add("\tadd x0, x9, x10")
            elif model == "IEX-M002":
                add("\tlslv x0, x9, x10")
            elif model == "IEX-M003":
                add("\tumulh x0, x9, x10")
            elif model == "IEX-M004":
                add("\tudiv x0, x9, x10")
            elif model == "IEX-M006":
                add("\tsubs x2, x9, x10")
                add("\t.global iex_consumer_pc")
                add("iex_consumer_pc:")
                add("\tcsel x0, x5, x6, eq")
            elif model == "IEX-M007":
                add("\tclz x0, x9")
            raw = "x0"
        add("\teor x1, %s, x11" % raw)
        add("\tstr %s, [x12]" % raw)
        add("\tstr x1, [x12, #8]")
        add("\tadd x12, x12, #16")

    elif ctx == "C03":
        if model == "IEX-M005":
            m = oracle.M005_MARKERS[ctx]
            add("\tcmp x9, x10")
            add("\t.global iex_target_pc")
            add("iex_target_pc:")
            add("\tb.eq .Ltaken")
            add("\tldr x2, =0x%016X" % m["eq_fall"])
            add("\tb .Lmerge")
            add(".Ltaken:")
            add("\tldr x2, =0x%016X" % m["eq_taken"])
            add(".Lmerge:")
            raw = "x2"
        else:
            add("\t.global iex_target_pc")
            add("iex_target_pc:")
            if model == "IEX-M001":
                add("\tadd x0, x9, x10")
            elif model == "IEX-M002":
                add("\tlslv x0, x9, x10")
            elif model == "IEX-M003":
                add("\tumulh x0, x9, x10")
            elif model == "IEX-M004":
                add("\tudiv x0, x9, x10")
            elif model == "IEX-M006":
                add("\tsubs x2, x9, x10")
                add("\t.global iex_consumer_pc")
                add("iex_consumer_pc:")
                add("\tcsel x0, x5, x6, eq")
            elif model == "IEX-M007":
                add("\tclz x0, x9")
            raw = "x0"
        # Exactly one real consumer of raw, then both values are overwritten
        # before any store or print.  No polluted value reaches memory.
        add("\teor x24, %s, x11" % raw)
        add("\tmov x24, #0")
        add("\tmov %s, #0" % raw)
        add("\tldr x2, =0x%016X" % oracle.C03_FINAL)
        add("\tstr x2, [x12]")
        add("\tstr xzr, [x12, #8]")
        add("\tadd x12, x12, #16")

    elif ctx == "C04":
        if model == "IEX-M005":
            m = oracle.M005_MARKERS[ctx]
            add("\tcmp x9, x10")
            add("\t.global iex_target_pc")
            add("iex_target_pc:")
            add("\tb.eq .Ltaken")
            add("\tldr x2, =0x%016X" % m["eq_fall"])
            add("\tb .Lmerge")
            add(".Ltaken:")
            add("\tldr x2, =0x%016X" % m["eq_taken"])
            add(".Lmerge:")
            raw = "x2"
        else:
            add("\t.global iex_target_pc")
            add("iex_target_pc:")
            if model == "IEX-M001":
                add("\tadd x0, x9, x10")
            elif model == "IEX-M002":
                add("\tlslv x0, x9, x10")
            elif model == "IEX-M003":
                add("\tumulh x0, x9, x10")
            elif model == "IEX-M004":
                add("\tudiv x0, x9, x10")
            elif model == "IEX-M006":
                add("\tsubs x2, x9, x10")
                add("\t.global iex_consumer_pc")
                add("iex_consumer_pc:")
                add("\tcsel x0, x5, x6, eq")
            elif model == "IEX-M007":
                add("\tclz x0, x9")
            raw = "x0"
        add("\teor x1, %s, x11" % raw)
        add("\tadd x2, x1, #17")
        add("\tror x3, x2, #7")
        add("\tadd x4, x3, x3, lsl #1")
        add("\tstr x4, [x12]")
        add("\teor x1, x4, x11")
        add("\tstr x1, [x12, #8]")
        add("\tadd x12, x12, #16")

    elif ctx == "C05":
        add("\tldr x22, =v3_cold1")
        add("\tldr x23, =v3_cold2")
        add("\tmov x20, #%d" % N_EPISODES)
        if model == "IEX-M006":
            add("\tldr x15, =0x%016X" % vec["local_golden"])
        elif model != "IEX-M005":
            add("\tldr x15, =0x%016X" % vec["local_golden"])
        add("\t.global iex_roi_start")
        add("iex_roi_start:")
        add(".Lloop:")
        add("\tldr x13, [x22]")
        add("\tadd x22, x22, #4096")
        add("\tldr x14, [x13, x23]")
        add("\tadd x23, x23, #4096")
        add("\t.global iex_older_branch_pc")
        add("iex_older_branch_pc:")
        add("\tcbnz x14, .Lold_taken")
        if model == "IEX-M005":
            m = oracle.M005_MARKERS[ctx]
            add("\tcmp x9, x10")
            add("\t.global iex_target_pc")
            add("iex_target_pc:")
            add("\tb.eq .Lgold")
            add("\tldr x2, =0x%016X" % m["eq_fall"])
            add("\tb .Lmerge")
            add(".Lgold:")
            add("\tldr x2, =0x%016X" % m["eq_taken"])
            add(".Lmerge:")
        else:
            add("\t.global iex_target_pc")
            add("iex_target_pc:")
            if model == "IEX-M001":
                add("\tadd x0, x9, x10")
            elif model == "IEX-M002":
                add("\tlslv x0, x9, x10")
            elif model == "IEX-M003":
                add("\tumulh x0, x9, x10")
            elif model == "IEX-M004":
                add("\tudiv x0, x9, x10")
            elif model == "IEX-M006":
                add("\tsubs x2, x9, x10")
                add("\t.global iex_consumer_pc")
                add("iex_consumer_pc:")
                add("\tcsel x0, x5, x6, eq")
            elif model == "IEX-M007":
                add("\tclz x0, x9")
            add("\tcmp x0, x15")
            add("\tb.eq .Lgold")
            add("\tldr x2, =0x%016X" % oracle.C05_FAULT)
            add("\tb .Lmerge")
            add(".Lgold:")
            add("\tldr x2, =0x%016X" % oracle.C05_GOLD)
            add(".Lmerge:")
        add("\teor x1, x2, x11")
        add("\tstr x2, [x12]")
        add("\tstr x1, [x12, #8]")
        add("\tadd x12, x12, #16")
        add("\t.global iex_iter_pc")
        add("iex_iter_pc:")
        add("\tsub x20, x20, #1")
        add("\tcbnz x20, .Lloop")
        add("\t.global iex_roi_end")
        add("iex_roi_end:")
        add("\tb .Ldone")
        add(".Lold_taken:")
        add("\tldr x2, =0x00000000DEADBEEF")
        add("\tstr x2, [x12]")
        add(".Ldone:")
        add("\tret")

    else:
        raise SystemExit("bad context " + ctx)

    if ctx != "C05":
        add("\t.global iex_iter_pc")
        add("iex_iter_pc:")
        add("\tsub x20, x20, #1")
        add("\tcbnz x20, .Lloop")
        add("\t.global iex_roi_end")
        add("iex_roi_end:")
        add("\tret")
    add("\t.section .rodata")
    add("\t.global iex_context")
    add('iex_context: .asciz "%s-%s"' % (model, ctx))
    add("\t.ltorg")
    if ctx == "C05":
        add("\t.section .bss")
        add("\t.align 12")
        add("v3_cold1: .skip 0x80000")
        add("\t.align 12")
        add("v3_cold2: .skip 0x80000")
    return "\n".join(L) + "\n"


def symbols(elf):
    out = run(["nm", "-n", elf])
    d = {}
    for line in out.splitlines():
        p = line.split()
        if len(p) == 3:
            d[p[2]] = int(p[0], 16)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-build", action="store_true")
    args = ap.parse_args()
    os.makedirs(SRC, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)
    vectors = oracle.all_vectors()
    rows = []
    if not args.skip_build:
        common = os.path.join(SRC, "v3_common.c")
        with open(common, "w") as f:
            f.write(common_c())
        common_o = os.path.join(BUILD, "v3_common.o")
        run([XCC, "-c", "-O2", "-ffreestanding", "-fno-builtin",
             "-fno-stack-protector", "-march=armv8-a", "-o", common_o,
             common])
        for model in oracle.MODELS:
            for ctx in oracle.CONTEXTS:
                key = "%s-%s" % (model, ctx)
                vec = vectors[key]
                name = key.replace("IEX-", "")
                asm = os.path.join(SRC, name + ".S")
                obj = os.path.join(BUILD, name + ".o")
                elf = os.path.join(BUILD, name + ".elf")
                with open(asm, "w") as f:
                    f.write(asm_for(model, ctx, vec))
                run([XCC, "-c", "-march=armv8-a", "-o", obj, asm])
                run([XCC, "-nostdlib", "-static", "-no-pie", "-Wl,-e,_start",
                     "-Wl,--build-id=none", "-Wl,-T," +
                     os.path.join(SRC, "v3.ld"), "-Wl,-z,max-page-size=4096",
                     "-o", elf, common_o, obj])
                rows.append(make_row(model, ctx, vec, asm, elf))
    else:
        for model in oracle.MODELS:
            for ctx in oracle.CONTEXTS:
                key = "%s-%s" % (model, ctx)
                name = key.replace("IEX-", "")
                rows.append(make_row(model, ctx, vectors[key],
                                     os.path.join(SRC, name + ".S"),
                                     os.path.join(BUILD, name + ".elf")))
    manifest = os.path.join(ROOT, "workloads", "v3", "manifest.json")
    with open(manifest, "w") as f:
        json.dump({"spec": "IEX_WHEN_5x3_v3_2026-11-23",
                   "episodes": N_EPISODES, "contexts": rows}, f, indent=2)
    csvp = os.path.join(ROOT, "workloads", "v3", "manifest.csv")
    keys = list(rows[0].keys())
    with open(csvp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print("wrote %d workloads -> %s" % (len(rows), manifest))
    for r in rows:
        print(r["context_key"], r["target_pc"], r["roi_start"], r["roi_end"],
              r["target_opcode"])


def make_row(model, ctx, vec, asm, elf):
    sym = symbols(elf)
    for need in ("iex_run", "iex_roi_start", "iex_roi_end", "iex_target_pc"):
        if need not in sym:
            raise SystemExit("%s-%s missing %s" % (model, ctx, need))
    dis = run(["objdump", "-d", "--no-show-raw-insn", elf])
    tgt = sym["iex_target_pc"]
    line = next((l for l in dis.splitlines()
                 if l.strip().startswith("%x:" % tgt)), "")
    opcode = line.split(":", 1)[1].strip() if line else ""
    if not opcode:
        raise SystemExit("%s-%s no target instruction at 0x%x" %
                         (model, ctx, tgt))
    return {
        "context_key": "%s-%s" % (model, ctx),
        "model": model, "context": ctx,
        "workload_id": "IEX-W%02d-%s" %
                       (oracle.MODELS.index(model) + 1, ctx),
        "source": asm, "elf": elf,
        "elf_sha256": sha256(elf),
        "a_hex": "0x%016X" % vec["a"],
        "b_hex": "0x%016X" % vec["b"],
        "mask_hex": "0x%016X" % MASK,
        "local_golden_hex": "0x%016X" % vec["local_golden"],
        "local_fault_hex": "0x%016X" % vec["local_fault"],
        "final_golden_hex": "0x%016X" % vec["final_golden"],
        "final_fault_hex": "0x%016X" % vec["final_fault"],
        "aux_golden_hex": "0x%016X" % vec["aux_golden"],
        "aux_fault_hex": "0x%016X" % vec["aux_fault"],
        "target_pc": "0x%016X" % tgt,
        "target_opcode": opcode,
        "consumer_pc": ("0x%016X" % sym["iex_consumer_pc"]
                        if "iex_consumer_pc" in sym else ""),
        "older_branch_pc": ("0x%016X" % sym["iex_older_branch_pc"]
                            if "iex_older_branch_pc" in sym else ""),
        "iter_pc": ("0x%016X" % sym["iex_iter_pc"]
                    if "iex_iter_pc" in sym else ""),
        "iter_init": N_EPISODES,
        "roi_start": "0x%016X" % sym["iex_roi_start"],
        "roi_end": "0x%016X" % sym["iex_roi_end"],
        "selector_mode": "C05_ORDINAL" if ctx == "C05" else "ORDINAL",
    }


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    main()
