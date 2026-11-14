#!/usr/bin/env python3
"""Controlled random-fault-injection comparison: sdcfuzz vs SiliFuzz streams.

Both arms execute a 3600-instruction register-only stream inside the same
AArch64 guest harness (same sandbox, same m5 work-item ROI, same FNV oracle
over x0-x30, q0-q31 and 1 KiB of data).  The only difference is the stream:

  sdcfuzz   fp-add / fp-mul templates rendered by sdcfuzz.generator, three
            operand pairs each (6 streams)
  silifuzz  snapshots from the fixed SiliFuzz corpus, reduced to their executed
            register-only prefix and concatenated (6 blocks, 3600 words each)

Fault model: CHAOSFPU, one transient bit flip at a randomly chosen FP source
read (probability=0.001 per read, max_faults=1), which is the only CHAOS
injector with a source-read hook that reaches in-flight O3 values.  Integer
register injectors (CHAOSReg / CHAOSPhysReg arch_frontend) are bypassed by
O3 renaming on these streams and are reported separately as not measurable.

Usage:
  python3 fi_campaign.py --n 40 --jobs 8 [--rebuild] [--only sdcfuzz|silifuzz]
"""
import argparse
import json
import math
import os
import random
import re
import shutil
import struct
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path("/home/sdc/sdc-mhw")
GEM5 = ROOT / "CHAOS/gem5/build/ARM/gem5.opt"
CONFIG = ROOT / "configs/se/arm_chaos.py"
M5OP = ROOT / "CHAOS/gem5/util/m5/src/abi/arm64/m5op.S"
CC = "aarch64-openEuler-linux-gcc"
CORPUS = ROOT / "silifuzz/work/corpus/ifuzz"
OUT = ROOT / "m5out/silifuzz-vs-sdcfuzz-fi"
WORK = ROOT / "fi_research/sdcfuzz_vs_silifuzz/work"
PREFIX_CACHE = WORK / "snapshot_prefixes.json"
TARGET_INSNS = 3600

HARNESS = r"""
#include <stdint.h>
#include <stdio.h>
#include <sys/mman.h>
#include <gem5/m5ops.h>

#ifndef DATA0
#define DATA0 0x3ff8000000000000ULL
#endif
#ifndef DATA1
#define DATA1 0x4002000000000000ULL
#endif

#define SANDBOX_BASE 0x20000UL
#define SANDBOX_SIZE 0x240000UL
#define STACK_TOP    (SANDBOX_BASE + 0x210000UL)
#define DATA_WORDS   128

uint64_t g_in[32];
volatile uint64_t g_out[128];
uint64_t g_host[16];
extern void run_block(void);

static uint64_t mix(uint64_t h, uint64_t v) {
    return (h ^ v) * 1099511628211ULL;
}

int main(void) {
    void *p = mmap((void *)SANDBOX_BASE, SANDBOX_SIZE,
                   PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED, -1, 0);
    if (p != (void *)SANDBOX_BASE) { perror("mmap"); return 2; }
    uint64_t *data = (uint64_t *)SANDBOX_BASE;
    data[0] = (uint64_t)DATA0;
    data[1] = (uint64_t)DATA1;
    for (int i = 2; i < DATA_WORDS; i++)
        data[i] = 0x0123456789ABCDEFULL +
                  (uint64_t)i * 0x9E3779B97F4A7C15ULL;
    for (int i = 0; i < 31; i++)
        g_in[i] = SANDBOX_BASE + (uint64_t)i * 0x80;
    g_in[27] = SANDBOX_BASE;   /* template buffer base */
    g_in[31] = STACK_TOP;

    m5_work_begin(7, 0);
    run_block();
    m5_work_end(7, 0);

    uint64_t h = 1469598103934665603ULL;
    for (int i = 0; i < 28; i++) h = mix(h, g_out[i]);
    h = mix(h, g_out[28]);
    h = mix(h, g_out[29]);
    for (int i = 0; i < 64; i++) h = mix(h, g_out[32 + i]);
    for (int i = 0; i < DATA_WORDS; i++) h = mix(h, data[i]);
    printf("%016llx\n", (unsigned long long)h);
    return 0;
}
"""


def asm_header():
    lines = [
        "    .arch armv8-a",
        "    .text",
        "    .align 4",
        "    .global run_block",
        "    .type run_block, %function",
        "run_block:",
        "    adrp x9, g_host",
        "    add  x9, x9, :lo12:g_host",
        "    mov  x10, sp",
        "    stp  x10, x30, [x9]",
        "    stp  x18, x19, [x9, #16]",
        "    stp  x20, x21, [x9, #32]",
        "    stp  x22, x23, [x9, #48]",
        "    stp  x24, x25, [x9, #64]",
        "    stp  x26, x27, [x9, #80]",
        "    stp  x28, x29, [x9, #96]",
        "    adrp x28, g_in",
        "    add  x28, x28, :lo12:g_in",
    ]
    for i in range(0, 28, 2):
        lines.append(f"    ldp x{i}, x{i+1}, [x28, #{i*8}]")
    lines += [
        "    ldr x29, [x28, #232]",
        "    ldr x30, [x28, #240]",
        "    ldr x9, [x28, #248]",
        "    mov sp, x9",
        "    adrp x28, g_out",
        "    add  x28, x28, :lo12:g_out",
    ]
    return "\n".join(lines) + "\n"


def asm_footer():
    lines = []
    for i in range(0, 28, 2):
        lines.append(f"    stp x{i}, x{i+1}, [x28, #{i*8}]")
    lines.append("    stp x29, x30, [x28, #224]")
    for i in range(0, 32, 2):
        lines.append(f"    stp q{i}, q{i+1}, [x28, #{256 + i*16}]")
    lines += [
        "    adrp x9, g_host",
        "    add  x9, x9, :lo12:g_host",
        "    ldp  x10, x30, [x9]",
        "    ldp  x18, x19, [x9, #16]",
        "    ldp  x20, x21, [x9, #32]",
        "    ldp  x22, x23, [x9, #48]",
        "    ldp  x24, x25, [x9, #64]",
        "    ldp  x26, x27, [x9, #80]",
        "    ldp  x28, x29, [x9, #96]",
        "    mov  sp, x10",
        "    ret",
        "    .size run_block, .-run_block",
    ]
    return "\n".join(lines) + "\n"


def render_stream(template_id, target_insns=TARGET_INSNS):
    sys.path.insert(0, str(ROOT))
    from sdcfuzz.templates import TEMPLATE_BY_ID
    from sdcfuzz import isa

    t = TEMPLATE_BY_ID[template_id]

    def body_insns(op):
        return [ln for ln in isa.render(op) if not ln.rstrip().endswith(":")]

    per_iter = 16 * sum(len(body_insns(op)) for op in t.body) + 2
    iterations = max(1, round(target_insns / per_iter))
    lines = []
    for op in t.setup:
        lines.extend(isa.render(op))
    lines.append(f"    mov x14, #{iterations}")
    lines.append("9:")
    for _ in range(16):
        for op in t.body:
            lines.extend(isa.render(op))
    lines.append("    subs x14, x14, #1")
    lines.append("    b.ne 9b")
    text = "\n".join("    " + ln if not ln.startswith(("9:", "1:")) else ln
                     for ln in lines)
    text = text.replace("[%[buf]", "[x27")
    return text, iterations


UNSAFE_MN = {
    "b", "bl", "br", "blr", "ret", "cbz", "cbnz", "tbz", "tbnz",
    "mrs", "msr", "svc", "hvc", "smc", "hlt", "brk", "udf", "dc", "ic",
    "tlbi", "at", "sys", "isb", "dsb", "dmb", "adr", "adrp", "eret",
    "wfe", "wfi", "axflag", "xaflag", "rmif", "setf8", "setf16", "cfp",
    "rcpp", "stg", "ldg", "stz", "ldz", "bti", "esb", "csdb", "nop",
}


def load_snapshot_prefixes(max_files=30000):
    """Return [{words, fp, src}] of executed register-only prefixes."""
    sys.path.insert(0, str(ROOT / "silifuzz/tools"))
    import sfsnapshot as S
    from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    paths = sorted(CORPUS.glob("*/*.sfs"))[:max_files]
    out = []
    for path in paths:
        try:
            snap = S.load(str(path))
        except Exception:
            continue
        code_map = None
        for m in snap.mappings:
            if (m.perms & 4) and m.start <= snap.regs.pc < m.start + m.size:
                code_map = m
                break
        if code_map is None or not code_map.data:
            continue
        off = snap.regs.pc - code_map.start
        end = len(code_map.data)
        sig = snap.end_states[0].sig_addr if snap.end_states else 0
        if code_map.start <= sig < code_map.start + code_map.size:
            end = min(end, sig - code_map.start)
        n = max(0, (end - off) // 4)
        if n <= 0:
            continue
        code = code_map.data[off:off + n * 4]
        words, fps = [], 0
        for i in range(0, len(code), 4):
            ins = list(md.disasm(code[i:i+4], 0))
            if not ins:
                break
            mn = ins[0].mnemonic
            txt = f"{mn} {ins[0].op_str}"
            if (mn in UNSAFE_MN or mn.startswith(("b.", "dcps", "pac", "aut"))
                    or "[" in ins[0].op_str
                    or re.search(r"\bx28\b|\bw28\b|\bsp\b", txt)):
                break
            words.append(int.from_bytes(code[i:i+4], "little"))
            if re.search(r"\b[qdsv]\d+\b", txt):
                fps += 1
        if words:
            out.append({"src": path.name, "words": words, "fp": fps})
    return out


def build_block(prefixes, target_insns, seed):
    rng = random.Random(seed)
    order = list(range(len(prefixes)))
    rng.shuffle(order)
    words, fp, used_q = [], 0, set()
    from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    for idx in order:
        p = prefixes[idx]
        for w in p["words"]:
            words.append(w)
            ins = list(md.disasm(w.to_bytes(4, "little"), 0))
            if ins:
                txt = f"{ins[0].mnemonic} {ins[0].op_str}"
                if re.search(r"\b[qdsv]\d+\b", txt):
                    fp += 1
                for m in re.finditer(r"\bq(\d+)\b", txt):
                    used_q.add(int(m.group(1)))
            if len(words) >= target_insns:
                break
        if len(words) >= target_insns:
            break
    while len(words) < target_insns:
        words.append(0xD503201F)
    words = words[:target_insns]
    return "\n".join(f"    .word 0x{w:08x}" for w in words), fp, sorted(used_q)


def compile_guest(work, block_asm, tag, data0, data1, force=False):
    work.mkdir(parents=True, exist_ok=True)
    exe = work / f"guest_{tag}"
    if exe.exists() and not force:
        return exe
    (work / "harness.c").write_text(HARNESS)
    (work / "block.S").write_text(asm_header() + block_asm + "\n" + asm_footer())
    subprocess.run(
        [CC, "-O2", "-static", "-fno-pie", "-no-pie", "-Wall", "-Werror",
         f"-DDATA0={data0}ULL", f"-DDATA1={data1}ULL",
         "-I" + str(ROOT / "CHAOS/gem5/include"),
         str(work / "harness.c"), str(work / "block.S"), str(M5OP),
         "-o", str(exe)], check=True)
    return exe


def run_gem5(exe, outdir, extra, timeout=30):
    outdir = Path(outdir)
    shutil.rmtree(outdir, ignore_errors=True)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [str(GEM5), "--quiet", "-d", str(outdir), str(CONFIG),
           "--cmd", str(exe), "--cpu", "O3", "--kp920_proxy"] + extra
    t0 = time.time()
    try:
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout)
        rc, out, err = res.returncode, res.stdout or "", res.stderr or ""
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        rc, timed_out = 124, True
        out = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        err = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
    text = out + "\n" + err
    (outdir / "gem5.log").write_text(text)
    checks = re.findall(r"^[0-9a-f]{16}$", text, re.MULTILINE)
    return {
        "checksum": checks[-1] if checks else None,
        "returncode": rc,
        "timed_out": timed_out,
        "seconds": round(time.time() - t0, 2),
        "text": text,
    }


def golden(exe):
    a = run_gem5(exe, exe.parent / "golden_a", [])
    b = run_gem5(exe, exe.parent / "golden_b", [])
    if not a["checksum"] or a["checksum"] != b["checksum"]:
        raise SystemExit(f"golden not deterministic for {exe}: "
                         f"{a['checksum']} vs {b['checksum']}")
    return a["checksum"]


def classify(exe, gold, seed, outdir, prob=0.001):
    extra = ["--chaos_fpu", "--probability=" + str(prob),
             "--max_faults=1", "--first_clock=1000",
             "--rng_seed=" + str(seed), "--fpu_bit_segment=all"]
    res = run_gem5(exe, outdir, extra)
    text = res["text"]
    log = Path(outdir) / "fpu_injections.log"
    inj = 0
    if log.exists():
        inj = sum(1 for line in log.read_text(errors="replace").splitlines()
                  if "Site:" in line)
    for junk in ("stats.txt", "config.ini", "config.json", "citations.bib"):
        p = Path(outdir) / junk
        if p.exists():
            p.unlink()
    if inj == 0:
        cat = "Inactive"
    elif res["timed_out"] and not res["checksum"]:
        cat = "Hang"
    elif re.search(r"panic:|fatal: |SimulatorError", text):
        cat = "SimulatorError"
    elif not res["checksum"]:
        cat = "Crash"
    elif res["checksum"] == gold:
        cat = "Masked"
    else:
        cat = "SDC"
    return cat, inj, res["seconds"]


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), p, min(1.0, c + h)


def fisher(a, b, c, d):
    """Two-sided Fisher exact for [[a,b],[c,d]]; log-space, no scipy."""
    n = a + b + c + d
    r1, c1 = a + b, a + c

    def lg(x):
        return math.lgamma(x + 1)

    def pl(k):
        return lg(c1) + lg(n - c1) - lg(k) - lg(c1 - k) - lg(r1 - k) - \
            lg(n - c1 - r1 + k) - lg(n) + lg(r1) + lg(n - r1)

    p_obs = pl(a)
    lo, hi = max(0, r1 - (n - c1)), min(r1, c1)
    ps = [pl(k) for k in range(lo, hi + 1) if pl(k) <= p_obs + 1e-9]
    m = max(ps)
    return min(1.0, math.exp(m + math.log(sum(math.exp(x - m) for x in ps))))


def streams(n_per_stream, jobs, only, rebuild):
    WORK.mkdir(parents=True, exist_ok=True)
    specs = []
    sdc_variants = [
        ("fp-add", "0x3ff8000000000000", "0x4002000000000000", "1.5", "2.25"),
        ("fp-add", "0x4008000000000000", "0x3ff4000000000000", "3.0", "1.25"),
        ("fp-add", "0x3fb999999999999a", "0x3fc999999999999a", "0.1", "0.2"),
        ("fp-mul", "0x3ff8000000000000", "0x3ff0000000000001", "1.5", "1+2^-52"),
        ("fp-mul", "0x3ff4000000000000", "0x3fefffffffffffff", "1.25", "1-2^-53"),
        ("fp-mul", "0x4008000000000000", "0x3ff0000000000002", "3.0", "1+2^-51"),
    ]
    arm = "sdcfuzz"
    for i, (tid, d0, d1, l0, l1) in enumerate(sdc_variants, 1):
        tag = f"{tid}-v{(i-1)%3 + 1}"
        block, iterations = render_stream(tid)
        exe = compile_guest(WORK / tag, block, tag, d0, d1, force=rebuild)
        specs.append({"arm": arm, "stream": tag, "exe": str(exe),
                      "length": TARGET_INSNS, "iterations": iterations,
                      "data": [l0, l1], "fp": 16 * iterations})
    arm = "silifuzz"
    if PREFIX_CACHE.exists() and not rebuild:
        prefixes = json.loads(PREFIX_CACHE.read_text())
    else:
        prefixes = load_snapshot_prefixes()
        PREFIX_CACHE.write_text(json.dumps(prefixes))
    for i in range(1, 7):
        block, fp, qregs = build_block(prefixes, TARGET_INSNS, seed=i)
        tag = f"snap-{i}"
        exe = compile_guest(WORK / tag, block, tag,
                            "0x3ff8000000000000", "0x4002000000000000",
                            force=rebuild)
        specs.append({"arm": arm, "stream": tag, "exe": str(exe),
                      "length": TARGET_INSNS, "iterations": 1,
                      "data": ["1.5", "2.25"], "fp": fp,
                      "qregs": len(qregs)})
    if only:
        specs = [s for s in specs if s["arm"] == only]
    return specs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--only", choices=["sdcfuzz", "silifuzz"])
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--prob", type=float, default=0.001)
    args = ap.parse_args()

    specs = streams(args.n, args.jobs, args.only, args.rebuild)
    print(f"streams: {len(specs)}; runs/stream: {args.n}", flush=True)
    for s in specs:
        s["golden"] = golden(Path(s["exe"]))
        print(f"  golden {s['stream']:14s} {s['golden']} "
              f"fp={s['fp']}/{s['length']}", flush=True)

    tasks = []
    for s in specs:
        for r in range(args.n):
            tasks.append((s["stream"], s["arm"], s["exe"], s["golden"],
                          10000 + r, str(OUT / "runs" / s["stream"] / f"r{r:03d}"),
                          args.prob))
    results = {}
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futs = {pool.submit(classify, Path(t[2]), t[3], t[4], Path(t[5]),
                            args.prob): (t[0], t[1]) for t in tasks}
        done = 0
        import concurrent.futures as cf
        for fut in cf.as_completed(futs):
            stream, arm = futs[fut]
            cat, inj, secs = fut.result()
            results.setdefault(stream, {"arm": arm, "cats": {},
                                        "seconds": 0.0, "inj": 0})
            results[stream]["cats"][cat] = results[stream]["cats"].get(cat, 0) + 1
            results[stream]["seconds"] += secs
            results[stream]["inj"] += inj
            done += 1
            if done % 40 == 0:
                print(f"  {done}/{len(tasks)} runs", flush=True)

    # aggregate
    for arm in ("sdcfuzz", "silifuzz"):
        cats = {}
        for s in specs:
            if s["arm"] != arm:
                continue
            for k, v in results[s["stream"]]["cats"].items():
                cats[k] = cats.get(k, 0) + v
        valid = sum(v for k, v in cats.items()
                    if k not in ("Inactive", "SimulatorError"))
        sdc = cats.get("SDC", 0)
        lo, p, hi = wilson(sdc, valid)
        results[arm] = {"cats": cats, "valid": valid, "sdc": sdc,
                        "rate": p, "wilson": [lo, hi]}

    a = results["sdcfuzz"]
    b = results["silifuzz"]
    p = fisher(a["sdc"], a["valid"] - a["sdc"],
               b["sdc"], b["valid"] - b["sdc"])
    ratio = (a["rate"] / b["rate"]) if b["rate"] else float("inf")
    out = {"schema": "sdcfuzz.vs.silifuzz.fi.v1",
           "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "host": "sdc-0103", "gem5": str(GEM5),
           "protocol": {"injector": "CHAOSFPU", "probability": args.prob,
                        "max_faults": 1, "first_clock": 1000,
                        "stream_insns": TARGET_INSNS,
                        "n_per_stream": args.n},
           "streams": {s["stream"]: {**{k: s[k] for k in
                                        ("arm", "length", "fp")},
                                     **results[s["stream"]]}
                       for s in specs},
           "aggregate": {"sdcfuzz": a, "silifuzz": b,
                         "ratio": ratio, "fisher_p": p}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(out, indent=2))

    lines = ["# sdcfuzz vs SiliFuzz 随机故障注入实验结果", "",
             f"- 日期：{out['generated']}；主机：sdc-0103；gem5：`{GEM5}`",
             f"- 协议：CHAOSFPU，单次瞬态 bit flip，`probability={args.prob}`，"
             f"`max_faults=1`；每条流 {TARGET_INSNS} 条指令；每流 n={args.n}",
             "", "## 汇总", "",
             "| 组 | 有效注入 | SDC | SDC 率 | Wilson 95% CI |",
             "|---|---:|---:|---:|---|"]
    for arm in ("sdcfuzz", "silifuzz"):
        r = results[arm]
        lines.append(f"| {arm} | {r['valid']} | {r['sdc']} | "
                     f"{r['rate']:.4f} | [{r['wilson'][0]:.4f}, "
                     f"{r['wilson'][1]:.4f}] |")
    lines += ["", f"Fisher 精确检验 p = {p:.3g}；SDC 率比 = {ratio:.3f}。", "",
              "## 逐流", "",
              "| 流 | 组 | FP 指令 | 有效 | SDC | Masked | Hang | Crash | 其他 |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for s in specs:
        r = results[s["stream"]]
        c = r["cats"]
        lines.append(
            f"| {s['stream']} | {s['arm']} | {s['fp']} | {sum(c.values())} | "
            f"{c.get('SDC', 0)} | {c.get('Masked', 0)} | {c.get('Hang', 0)} | "
            f"{c.get('Crash', 0)} | "
            f"{c.get('Inactive', 0) + c.get('SimulatorError', 0)} |")
    (OUT / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[-12:]))
    print(f"\nsummary: {OUT/'summary.json'}")


if __name__ == "__main__":
    main()
