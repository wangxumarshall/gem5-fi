#!/usr/bin/env python3
"""Compare sdcfuzz-generated LSU streams with the core-179 NEON trigger.

The OpenDCDiag test ``neon_rot_ldr_at_top_rowmajor`` (179core-docs/test.c) is
the workload that exposed the core-179 SDC on the 0102 board.  This tool puts
it next to streams that sdcfuzz itself generates for the LSU:

  core179-neon      re-implementation of the OpenDCDiag inner loop
                    (workloads/directed/core179_neon_kernel.c), with and
                    without its per-sweep comparison pass
  sdcfuzz-l1d       ``autousens target --structure l1d`` top-k composition
  sdcfuzz-template  the ``l1d-load-stream`` / ``l1d-store-hot`` templates

Every stream runs in the same gem5 O3 model, with the TaiShan V110 proxy,
RF ACE / L1 ACE / FU IBR / SAD enabled, and the ROI delimited by
``m5_work_begin(7, 0)``.

Instruction normalisation
-------------------------
``sad.issuedOps`` cannot be used as the per-instruction denominator: it counts
every pass through the IQ issue path, including re-selection when no capable
FU is available.  The ``ldxr`` stream below reports 27.5k "issued" for 3.9k
retired instructions (7x).  The shipped gem5 build has no ROI-scoped committed
counter, and rebuilding it for this comparison is not worth the churn, so the
tool calibrates the ROI size instead: it runs the same guest with ``N`` and
``N-1`` loop counts and takes the difference of the committed instructions at
the ROI-end dump.  That difference is the per-sweep / per-iteration increment,
and ``(simInsts(N) - simInsts(N-1)) * N`` is the exact ROI instruction count
for the measured run (the pre-ROI initialisation cancels out).

The output is a JSON document plus two console tables; the interpretation
lives in docs/sdcfuzz/lsu-vs-core179-2026-11-14.md.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import autousens  # noqa: E402  (reuse stat parsing / candidate rendering)
from sdcfuzz import templates as template_module  # noqa: E402
from sdcfuzz.generator import render_guest  # noqa: E402

ARM_CHAOS = ROOT / "configs/se/arm_chaos.py"
KERNEL_SOURCE = ROOT / "workloads/directed/core179_neon_kernel.c"
DEFAULT_MAP = ROOT / "m5out/phase1-gate-final/autousens/map/structure_map.json"

EXACT = {
    "insts": "simInsts",
    "cycles": "board.processor.cores.core.numCycles",
    "ipc": "board.processor.cores.core.ipc",
    "roi_issued": "board.processor.cores.core.sad.issuedOps",
    "rf_int_ratio": "board.processor.cores.core.rfAce.intAceRatio",
    "rf_vec_ratio": "board.processor.cores.core.rfAce.vecAceRatio",
    "rf_int_reads": "board.processor.cores.core.rfAce.intTrackedReads",
    "rf_int_writes": "board.processor.cores.core.rfAce.intTrackedWrites",
    "rf_vec_reads": "board.processor.cores.core.rfAce.vecTrackedReads",
    "rf_vec_writes": "board.processor.cores.core.rfAce.vecTrackedWrites",
    "rf_int_squash": "board.processor.cores.core.rfAce.intSquashDiscards",
    "rf_vec_squash": "board.processor.cores.core.rfAce.vecSquashDiscards",
    "l1d_ratio": "board.cache_hierarchy.l1d-cache-0.l1Ace.aceRatio",
    "l1d_reads": "board.cache_hierarchy.l1d-cache-0.l1Ace.trackedDemandReads",
    "l1d_writes": "board.cache_hierarchy.l1d-cache-0.l1Ace.trackedDemandWrites",
    "l1d_fills": "board.cache_hierarchy.l1d-cache-0.l1Ace.trackedFills",
    "l1d_lifetimes": "board.cache_hierarchy.l1d-cache-0.l1Ace.lifetimeEnds",
    "l1d_hits": "board.cache_hierarchy.l1d-cache-0.demandHits::total",
    "l1d_misses": "board.cache_hierarchy.l1d-cache-0.demandMisses::total",
    "l1d_replacements": "board.cache_hierarchy.l1d-cache-0.replacements",
    "l1i_ratio": "board.cache_hierarchy.l1i-cache-0.l1Ace.aceRatio",
    "l1i_reads": "board.cache_hierarchy.l1i-cache-0.l1Ace.trackedDemandReads",
    "sad_samples": "board.processor.cores.core.sad.samples",
    "sad_issue_ratio": "board.processor.cores.core.sad.issueRatio",
}
IBR_CLASSES = ("intAlu", "intMult", "intDiv", "fpAdd", "fpMult")
SAD_RESOURCES = ("rob", "iq", "lq", "sq", "intPrf", "vecPrf", "fu")


def stat(stats, key):
    try:
        return float(stats[key])
    except KeyError:
        raise SystemExit(f"missing statistic {key!r} in gem5 dump")


def collect(stats):
    """Turn one stats dump into the flat metric dictionary we report."""
    data = {name: stat(stats, key) for name, key in EXACT.items()}
    for cls in IBR_CLASSES:
        data[f"ibr_bits_{cls}"] = stat(
            stats, f"board.processor.cores.core.fuIbr.inputBits::{cls}")
        data[f"ibr_issued_{cls}"] = stat(
            stats, f"board.processor.cores.core.fuIbr.issuedOps::{cls}")
        data[f"ibr_ratio_{cls}"] = stat(
            stats, f"board.processor.cores.core.fuIbr.ibrRatio::{cls}")
    for res in SAD_RESOURCES:
        data[f"sad_used_{res}"] = stat(
            stats, f"board.processor.cores.core.sad.usedSum::{res}")
        data[f"sad_cap_{res}"] = stat(
            stats, f"board.processor.cores.core.sad.capacity::{res}")
    return data


def derive(data, roi_insts):
    """Normalised metrics: per 1k ROI instructions, per cycle, ratios."""
    insts = float(roi_insts)
    if insts <= 0:
        raise SystemExit("ROI instruction count must be positive")
    per_1k = lambda value: value / insts * 1000.0
    sad_samples = data["sad_samples"] or 1.0
    derived = {
        "roi_insts": insts,
        "roi_issued": data["roi_issued"],
        "issued_per_commit": data["roi_issued"] / insts,
        "commit_per_cycle": insts / sad_samples,
        "ipc": data["ipc"],
        "cycles": data["cycles"],
        "lsu_ops_per_1k": per_1k(data["l1d_reads"] + data["l1d_writes"]),
        "l1d_reads_per_1k": per_1k(data["l1d_reads"]),
        "l1d_writes_per_1k": per_1k(data["l1d_writes"]),
        "l1d_fills_per_1k": per_1k(data["l1d_fills"]),
        "l1d_miss_rate": (data["l1d_misses"] /
                          max(data["l1d_hits"] + data["l1d_misses"], 1.0)),
        "l1d_mpki": per_1k(data["l1d_misses"]),
        "rf_ops_per_1k": per_1k(data["rf_int_reads"] + data["rf_int_writes"]
                                + data["rf_vec_reads"] + data["rf_vec_writes"]),
    }
    for res in SAD_RESOURCES:
        used = data[f"sad_used_{res}"]
        cap = data[f"sad_cap_{res}"] or 1.0
        derived[f"sad_{res}"] = used / (sad_samples * cap)
    for cls in IBR_CLASSES:
        issued = data[f"ibr_issued_{cls}"]
        derived[f"ibr_bits_per_op_{cls}"] = (
            data[f"ibr_bits_{cls}"] / issued if issued else 0.0)
    derived["ibr_covered_ops_per_1k"] = per_1k(sum(
        data[f"ibr_issued_{cls}"] for cls in IBR_CLASSES))
    return derived


def run_stream(gem5, outdir, guest, workload_args):
    """Run one guest; return (ROI-end committed instructions, last dump)."""
    outdir.mkdir(parents=True, exist_ok=True)
    command = [
        str(gem5), "--outdir=" + str(outdir), str(ARM_CHAOS), "--cpu=O3",
        "--cmd=" + str(guest), "--workload_args=" + workload_args,
        "--kp920_proxy",
        "--rf_ace", "--rf_ace_granularity=bit", "--l1_ace", "--fu_ibr", "--sad",
    ]
    with (outdir / "gem5.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                       env=autousens.gem5_environment(), check=True)
    text = (outdir / "gem5.log").read_text()
    if not any(token in text for token in ("status=DONE", "status=PASS")):
        raise SystemExit(f"{outdir}: guest did not report a success status; "
                         f"see {outdir / 'gem5.log'}")
    dumps = autousens.stat_dumps(outdir / "stats.txt")
    return stat(dumps[0], "simInsts"), dumps[-1]


def top_modes(map_document, structure, count):
    ranked = autousens.rank_for_structure(map_document, structure)
    return [mode for mode, _entry in ranked[:count]]


def kernel_stream(args):
    guest = autousens.compile_guest(
        KERNEL_SOURCE, args.outdir / "bin" / "core179_neon", args.cc)
    return [
        {"name": "core179-neon", "guest": lambda _n: guest,
         "args": lambda n: f"{args.elements} {n} 1"},
        {"name": "core179-neon-nocheck", "guest": lambda _n: guest,
         "args": lambda n: f"{args.elements} {n} 0"},
    ]


def candidate_stream(args, chosen):
    source = autousens.candidate_source("l1d", chosen, args.iterations)
    path = args.outdir / "generated" / "l1d_target.c"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)
    guest = autousens.compile_guest(
        path, args.outdir / "bin" / "l1d_target", args.cc)
    return {"name": f"sdcfuzz-l1d-top{len(chosen)}",
            "guest": lambda _n: guest, "args": lambda n: str(n)}


def template_stream(args, template_id):
    template = template_module.TEMPLATE_BY_ID[template_id]

    def build(n):
        source, _expected = render_guest(template, n)
        path = args.outdir / "generated" / f"{template_id}-{n}.c"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        return autousens.compile_guest(
            path, args.outdir / "bin" / f"{template_id}-{n}", args.cc)

    return {"name": f"template-{template_id.replace('l1d-', '')}",
            "guest": build, "args": lambda _n: ""}


def render_tables(results):
    lines = []
    header = (f"{'stream':26s} {'roi inst':>9s} {'cmt/cyc':>7s} "
              f"{'LSU/1k':>7s} {'rd/1k':>7s} {'wr/1k':>7s} "
              f"{'miss%':>6s} {'MPKI':>6s} {'L1D ACE':>7s} {'iss/cmt':>7s}")
    lines.append(header)
    lines.append("-" * len(header))
    for name, data, derived in results:
        lines.append(
            f"{name:26s} {derived['roi_insts']:9.0f} "
            f"{derived['commit_per_cycle']:7.2f} "
            f"{derived['lsu_ops_per_1k']:7.1f} "
            f"{derived['l1d_reads_per_1k']:7.1f} "
            f"{derived['l1d_writes_per_1k']:7.1f} "
            f"{derived['l1d_miss_rate'] * 100:6.2f} "
            f"{derived['l1d_mpki']:6.1f} {data['l1d_ratio']:7.4f} "
            f"{derived['issued_per_commit']:7.2f}")
    lines.append("")
    header = (f"{'stream':26s} {'RFint':>7s} {'RFvec':>7s} "
              f"{'IBRalu':>8s} {'IBRmul':>8s} {'SADrob':>7s} "
              f"{'SADlq':>7s} {'SADsq':>7s} {'issueU':>7s}")
    lines.append(header)
    lines.append("-" * len(header))
    for name, data, derived in results:
        lines.append(
            f"{name:26s} {data['rf_int_ratio']:7.4f} "
            f"{data['rf_vec_ratio']:7.4f} "
            f"{data['ibr_ratio_intAlu']:8.4f} "
            f"{data['ibr_ratio_intMult']:8.4f} "
            f"{derived['sad_rob']:7.3f} {derived['sad_lq']:7.3f} "
            f"{derived['sad_sq']:7.3f} {derived['commit_per_cycle']:7.2f}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gem5", type=Path, default=autousens.default_gem5())
    parser.add_argument("--cc", default=autousens.default_cc())
    parser.add_argument("--outdir", type=Path,
                        default=ROOT / "m5out/lsu-compare")
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--top", type=int, default=3,
                        help="instructions composed for the l1d-target stream")
    parser.add_argument("--iterations", type=int, default=200,
                        help="loop count of the generated streams (>= 2)")
    parser.add_argument("--elements", type=int, default=1024)
    parser.add_argument("--sweeps", type=int, default=8,
                        help="sweep count of the trigger kernel (>= 2)")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)
    args.outdir = args.outdir.resolve()
    if args.iterations < 2 or args.sweeps < 2:
        raise SystemExit("--iterations and --sweeps must be >= 2 for "
                         "the ROI calibration run")

    if not args.map.is_file():
        raise SystemExit(
            f"structure map not found: {args.map}\n"
            "build it with: python3 tools/autousens.py map --outdir <dir>")
    document = json.loads(args.map.read_text())
    chosen = top_modes(document, "l1d", args.top)

    streams = kernel_stream(args)
    streams.append(candidate_stream(args, chosen))
    for template_id in ("l1d-load-stream", "l1d-store-hot"):
        streams.append(template_stream(args, template_id))

    results = []
    evidence = {}
    for stream in streams:
        name = stream["name"]
        n = args.sweeps if name.startswith("core179") else args.iterations
        print(f"[run] {name} (n={n}, calibration n={n - 1})", file=sys.stderr)

        roi_end_n, last_dump = run_stream(
            args.gem5, args.outdir / name, stream["guest"](n),
            stream["args"](n))
        roi_end_prev, _ = run_stream(
            args.gem5, args.outdir / f"{name}-calib",
            stream["guest"](n - 1), stream["args"](n - 1))

        per_unit = roi_end_n - roi_end_prev
        if per_unit <= 0:
            raise SystemExit(
                f"{name}: ROI calibration produced {per_unit} instructions per "
                "unit; the loop is not linear or the guest ignored the count")
        roi_insts = per_unit * n

        data = collect(last_dump)
        derived = derive(data, roi_insts)
        derived["calibration"] = {
            "n": n,
            "per_unit_insts": per_unit,
            "roi_end_insts_n": roi_end_n,
            "roi_end_insts_n_minus_1": roi_end_prev,
        }
        results.append((name, data, derived))
        evidence[name] = {"raw": data, "derived": derived}

    output = {
        "schema": "sdcfuzz.lsu_compare.v1",
        "gem5": str(args.gem5),
        "config": {"cpu": "O3", "kp920_proxy": True, "l1d": "64KiB",
                   "l1i": "64KiB", "l2": "512KiB",
                   "denominator": "committed instructions in ROI, "
                                  "calibrated with N vs N-1 runs"},
        "generated": {
            "l1d_target_modes": chosen,
            "iterations": args.iterations,
            "kernel_elements": args.elements,
            "kernel_sweeps": args.sweeps,
        },
        "streams": evidence,
    }
    path = args.json or (args.outdir / "lsu_compare.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(render_tables(results))
    print(f"\nreport: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
