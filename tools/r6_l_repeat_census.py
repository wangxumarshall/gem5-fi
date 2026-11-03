#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-L-UNIT] Bounded-repeat census for the L unit.

Measures, with REAL gem5 runs on the frozen campaign binary, the eligible
stream of each L cell at repeat = 1 / 5 / 10 (interval tiers) or 1 / 2 / 5
(L03's per-seed F0 draw), then computes the repeat factor that covers the
SPEC-FIXED first-fire position:

    interval: R = 1 + ceil((1.2 * max_first_fire - E1) / delta)
    F0:       R = 1 + ceil((1.2 * draw_next_fire - E1) / delta)

delta = (E5 - E1)/4 (or the more conservative min of the 5/10 deltas when
the linear model is unstable). A run that injects during measurement is
re-measured with warmup=10,000,000 so E1/delta come from the UNINJECTED
stream; the tier/interval/seed/LCG sequence is unchanged.

Each run has its own fresh directory, manifest, PID/PGID, binary SHA,
source/tool head, start/end and exit code. Concurrency is capped at 2.
Never edits existing evidence.
"""
import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import lsu_campaign as LC  # noqa: E402

RUNS_ROOT = Path("/home/sdc/gem5-fi-ding/runs/lsu")
NO_FIRE_WARMUP = 10_000_000
LCG_MUL = 6364136223846793005
LCG_ADD = 1442695040888963407
U64 = (1 << 64) - 1
INTERVAL = {"F1": 1000000, "F2": 100000, "F4": 100000}
TRIGGER_RE = re.compile(
    r"^CHAOS_LSU_TRIGGER: injector=(\S+) tier=(\S+) attempted=(\d+) "
    r"eligible=(\d+) injected=(\d+)", re.M)
DRAW_RE = re.compile(r"draw_next_fire=(\d+)")

KEYS = [
    # key, runid, model, workload label, binary, seed, tier, draw(F0 only)
    ("L01-F1-W5", "L01-F1-W5", "L01", "SQ-Forward", "sq_forward", 1, "F1", None),
    ("L01-F1-W12", "L01-F1-W12", "L01", "SQLite", "sqlite_like", 1, "F1", None),
    ("L01-F2-W5", "L01-F2-W5", "L01", "SQ-Forward", "sq_forward", 1, "F2", None),
    ("L01-F2-W12", "L01-F2-W12", "L01", "SQLite", "sqlite_like", 1, "F2", None),
    ("L02-F2-W5", "L02-F2-W5", "L02", "SQ-Forward", "sq_forward", 1, "F2", None),
    ("L02-F2-W12", "L02-F2-W12", "L02", "SQLite", "sqlite_like", 1, "F2", None),
    ("L03-F4-W5", "L03-F4-W5", "L03", "SQ-Forward", "sq_forward", 1, "F4", None),
    ("L03-F4-W12", "L03-F4-W12", "L03", "SQLite", "sqlite_like", 1, "F4", None),
    # F0: the draw is this seed's own eligible ordinal (561 observed in the
    # 2026-11-03 evidence run; warmup=1, span=571).
    ("L03-F0-W5-s3", "L03-F0-W5", "L03", "SQ-Forward", "sq_forward", 3, "F0", 561),
]
BY_KEY = {k[0]: k for k in KEYS}


def lcg(x):
    return (int(x) * LCG_MUL + LCG_ADD) & U64


def first_fire(tier, seed, warmup=0):
    iv = INTERVAL.get(tier)
    if iv is None:
        return None
    return int(warmup) + iv // 2 + lcg(int(seed)) % iv


def max_first_fire(tier, seeds=(1, 2, 3)):
    vals = [first_fire(tier, s) for s in seeds]
    return max(v for v in vals if v is not None)


def cell_for(rec):
    _key, runid, model, workload, _binary, _seed, tier, _draw = rec
    cell = [""] * 12
    cell[LC.COL_RUNID] = runid
    cell[LC.COL_MODEL] = model
    cell[LC.COL_UNIT] = "Load Queue"
    cell[LC.COL_FREQ] = tier
    cell[LC.COL_WORKLOAD] = workload
    return cell


def no_fire(flags, family):
    flag = {"addrpath": "--addrpath_warmup_events",
            "lsqfwd": "--lsqfwd_warmup_events"}[family]
    i = flags.index(flag)
    flags[i + 1] = str(NO_FIRE_WARMUP)
    return flags


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_trigger(text):
    ms = TRIGGER_RE.findall(text or "")
    if not ms:
        return None
    inj, tier, att, elig, injected = ms[-1]
    return {"injector": inj, "tier": tier, "attempted": int(att),
            "eligible": int(elig), "injected": int(injected)}


def run_once(rec, repeat, outroot, gem5, timeout=3600, force_no_fire=False):
    key, runid, model, _workload, binary, seed, tier, _draw = rec
    family = LC.MODEL_FLAGS[model][0]
    outdir = Path(outroot) / ("%s_r%d%s" % (key, repeat,
                                            "_nofire" if force_no_fire else ""))
    outdir.mkdir(parents=True, exist_ok=True)
    flags, golden, resolved = LC.resolve_cell(
        cell_for(rec), seed=seed, repeat_override=int(repeat))
    if flags is None:
        raise SystemExit("BLOCKED %s r%d: %s" % (key, repeat, golden))
    flags = LC.apply_seed_variant_flags(model, tier, seed, resolved, flags)
    if force_no_fire:
        flags = no_fire(flags, family)
    cmd = [str(gem5), "--outdir", str(outdir), str(LC.LSU_PROXY)] + flags
    cmd += [LC.FAMILY_SEED[family], str(seed)]
    cmd += LC.propagation_flags(runid, seed)
    t0 = time.time()
    start = datetime.now().astimezone().isoformat(timespec="seconds")
    r = LC.run_gem5(cmd, timeout, outdir / "run.out", outdir / "run.err",
                    sigint_grace=LC.FS_SIGINT_GRACE)
    seconds = round(time.time() - t0, 3)
    end = datetime.now().astimezone().isoformat(timespec="seconds")
    text = (outdir / "run.out").read_text(errors="replace")
    trig = parse_trigger(text)
    iters = len(re.findall(r"^ITER:\d+:[0-9a-f]{16}\s*$", text, re.M))
    man = {
        "key": key, "runid": runid, "model": model, "seed": seed,
        "tier": tier, "repeat": int(repeat), "no_fire": force_no_fire,
        "cmd": cmd, "binary_path": str(gem5),
        "binary_sha256": sha256_of(gem5),
        "source_head": LC.head_rev() if hasattr(LC, "head_rev") else "",
        "pid": r["pid"], "process_group_id": r["pid"],
        "start_time": start, "end_time": end, "seconds": seconds,
        "exit_code": r["exit_code"], "signal": r["signal"],
        "timed_out": r["timed_out"], "trigger": trig, "iter_lines": iters,
        "golden": golden,
    }
    (outdir / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=1) + "\n")
    return {"outdir": str(outdir), "trigger": trig, "seconds": seconds,
            "exit_code": r["exit_code"], "iters": iters,
            "binary_sha256": man["binary_sha256"]}


def measure(key, outroot, gem5, timeout):
    rec = BY_KEY[key]
    tier = rec[6]
    repeats = (1, 2, 5) if tier == "F0" else (1, 5, 10)
    runs = {}
    for rep in repeats:
        runs["r%d" % rep] = run_once(rec, rep, outroot, gem5, timeout)
    # Pollution: if any measurement injected, re-measure the whole set on the
    # uninjected stream (warmup high; tier/seed/LCG unchanged).
    if any((r["trigger"] or {}).get("injected", 0) > 0 for r in runs.values()):
        for rep in repeats:
            runs["r%d" % rep] = run_once(rec, rep, outroot, gem5, timeout,
                                         force_no_fire=True)
        stream_mode = "uninjected (warmup=%d)" % NO_FIRE_WARMUP
    else:
        stream_mode = "injected-path clean (no fire during measurement)"
    el = {k: (r["trigger"] or {}).get("eligible") for k, r in runs.items()}
    E1 = el.get("r1")
    if E1 is None:
        raise SystemExit("no trigger line for %s" % key)
    if tier == "F0":
        Enext = el.get("r2")
        delta = (Enext - E1) / 1.0 if Enext is not None else None
        target = rec[7]
        source = "repeat=2"
        if el.get("r5") is not None:
            d5 = (el["r5"] - E1) / 4.0
            if delta is not None and abs(d5 - delta) > max(2.0, 0.02 * abs(delta)):
                delta = min(delta, d5)
                source = "min(repeat=2,repeat=5)"
    else:
        E5 = el.get("r5")
        delta = (E5 - E1) / 4.0 if E5 is not None else None
        target = max_first_fire(tier)
        source = "repeat=5"
        if el.get("r10") is not None and delta is not None:
            d10 = (el["r10"] - E1) / 9.0
            if abs(d10 - delta) > max(2.0, 0.02 * abs(delta)):
                delta = min(delta, d10)
                source = "min(repeat=5,repeat=10)"
    if delta is None or delta <= 0:
        raise SystemExit("%s: non-positive delta %r" % (key, delta))
    need = 1.2 * target - E1
    R = 1 + int(math.ceil(need / delta)) if need > 0 else 1
    return {
        "key": key, "runid": rec[1], "model": rec[2], "binary": rec[4],
        "seed": rec[5], "tier": tier, "target": target,
        "stream_mode": stream_mode, "eligible": el,
        "E1": E1, "delta": round(delta, 6), "delta_source": source,
        "R": R, "R_within_cap": R <= LC.REPEAT_MAX,
        "seconds": {k: v["seconds"] for k, v in runs.items()},
        "iter_lines": {k: v["iters"] for k, v in runs.items()},
        "exit_codes": {k: v["exit_code"] for k, v in runs.items()},
        "outdirs": {k: v["outdir"] for k, v in runs.items()},
        "binary_sha256": runs["r1"]["binary_sha256"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", help="comma-separated key list (default: all)")
    ap.add_argument("--outroot", default=str(RUNS_ROOT / "r6_l_census_20261103"))
    ap.add_argument("--gem5", default=os.environ.get(
        "LSU_GEM5_BIN",
        "/home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102/"
        "CHAOS/gem5/build/ARM/gem5.opt"))
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--jobs", type=int, default=2)
    args = ap.parse_args()
    keys = args.keys.split(",") if args.keys else [k[0] for k in KEYS]
    jobs = max(1, min(2, args.jobs))
    outroot = Path(args.outroot)
    outroot.mkdir(parents=True, exist_ok=True)
    gem5 = Path(args.gem5)
    summary = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futs = {pool.submit(measure, k, outroot, gem5, args.timeout): k
                for k in keys}
        for f in concurrent.futures.as_completed(futs):
            k = futs[f]
            try:
                summary[k] = f.result()
                print("[census] %-14s E1=%-7s delta=%-9s R=%s"
                      % (k, summary[k]["E1"], summary[k]["delta"],
                         summary[k]["R"]), flush=True)
            except Exception as exc:  # noqa: BLE001 — recorded, not hidden
                summary[k] = {"key": k, "error": repr(exc)}
                print("[census] %-14s ERROR %r" % (k, exc), flush=True)
    (outroot / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1) + "\n")
    lines = ["# R6-L 有界重复 census（真实 gem5 运行）", ""]
    lines += ["| key | tier | E1 | delta | source | target | R | within cap |",
              "|---|---|---|---|---|---|---|---|"]
    for k in keys:
        s = summary[k]
        if "error" in s:
            lines.append("| %s | — | — | — | — | — | ERROR: %s | — |"
                         % (k, s["error"][:80]))
            continue
        lines.append("| %(key)s | %(tier)s | %(E1)s | %(delta)s | "
                     "%(delta_source)s | %(target)s | %(R)s | "
                     "%(R_within_cap)s |" % s)
    (outroot / "summary.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({k: (v.get("R"), v.get("error")) for k, v in
                      summary.items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
