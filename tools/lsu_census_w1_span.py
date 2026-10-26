#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-CENSUS] S01/S02 (LSQFwd SQ-data family) F0 span census on the
W1 carrier (`mibench/bin/w1_all`) — UNINJECTED control run.

Why this exists
---------------
`tools/lsu_campaign.resolve_cell` refuses S01-F0-W1 / S02-F0-W1 LOUDLY with
`BLOCKED(F0-span-unmeasured: model S01 on workload mibench/bin/w1_all — measure
its eligible stream with a real run and set
LSQFWD_F0_SPAN[('S01','mibench/bin/w1_all')] in tools/lsu_campaign.py)`.

`LSQFWD_F0_SPAN` (tools/lsu_campaign.py) has rows for the short directed W5
carrier (`sq_forward`: 7) but NO row for the W1 MiBench-TC23 carrier, so the two
W1 cells stay UNRESOLVED and cannot be routed.

This script runs the CENSUS: the resolved lsqfwd F0 command for the model on the
W1 carrier, but with the F0 draw pinned so it can never land (span=INT64_MAX)
AND `--max_faults 0`, so the run is a pure CONTROL. The injector's teardown line
`CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=<N> eligible=<N>
injected=0 ...` then reports the WHOLE eligible stream — exactly the value that
belongs in `LSQFWD_F0_SPAN[(model, 'mibench/bin/w1_all')]`.

Honesty contract
----------------
* This is an UNINJECTED control: `injected=` MUST be 0. A nonzero value means
  the pin failed and the census is contaminated (the R5 §4 injected trial at
  17,663,390 was exactly that) — the script exits nonzero rather than report it.
* It never writes into `LSQFWD_F0_SPAN`; registering the measurement in the
  contract is the contract owner's call (this lane must not edit
  tools/lsu_campaign.py, tools/lsu_chain_check.py, tools/lsu_ready_contract.py).
* `n/a` is reported, never a silent zero.

Usage:
  python3 tools/lsu_census_w1_span.py --model S01 \
      --gem5 <path>/gem5.opt --outdir /abs/out \
      [--carrier mibench/bin/w1_all] [--variant B0] [--rng-seed 1] [--timeout 36000]
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CARRIER_DEFAULT = "mibench/bin/w1_all"
# The TRUE F0-uniform pin: warmup=1 + span=N. Here N = INT64_MAX, so
# next_fire = 1 + lcg(seed) % INT64_MAX essentially never lands; combined with
# --max_faults 0 the run is guaranteed uninjected.
SPAN_NEVER = 9223372036854775807

# The model's resolved family flags, kept in lockstep with
# tools/lsu_campaign.MODEL_FLAGS (quoted there, not imported, so this census
# keeps working if the campaign table is refactored).
MODEL_FLAGS = {
    "S01": ["--lsq_struct_mode", "byte_flip"],
    "S02": ["--lsq_struct_mode", "byte_flip", "--bits_to_change", "2"],
}

TRIGGER_RE = re.compile(
    r"CHAOS_LSU_TRIGGER: injector=(?P<inj>\S+)(?P<rest>.*?)"
    r"attempted=(?P<attempted>\d+)\s+eligible=(?P<eligible>\d+)"
    r"\s+injected=(?P<injected>\d+)")


def build_cmd(args, outdir):
    cmd = [args.gem5, "--outdir", str(outdir),
           str(REPO / "configs/se/lsu_proxy.py"),
           "--cmd", str(REPO / "workloads" / args.carrier),
           "--cpu", "O3", "--variant", args.variant,
           "--chaos_lsqfwd", *MODEL_FLAGS[args.model],
           "--lsqfwd_lsu_tier", "F0",
           "--lsqfwd_warmup_events", "1",
           "--lsqfwd_span_events", str(SPAN_NEVER),
           "--max_faults", "0",
           "--rng_seed", str(args.rng_seed)]
    return cmd


def parse_trigger(text):
    hits = [m.groupdict() for m in TRIGGER_RE.finditer(text)]
    return hits[-1] if hits else None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, choices=sorted(MODEL_FLAGS))
    ap.add_argument("--gem5", required=True, help="frozen integration gem5.opt")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--carrier", default=CARRIER_DEFAULT)
    ap.add_argument("--variant", default="B0")
    ap.add_argument("--rng-seed", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=36000,
                    help="wall seconds; the W1 suite simulates ~1270 s in "
                         "~7.5 h wall — do not use the 600 s SE default")
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = build_cmd(args, outdir)
    print("CMD:", " ".join(cmd), flush=True)
    t0 = time.time()
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True,
                       timeout=args.timeout)
    log = outdir / "census.run.out"
    log.write_text(r.stdout + r.stderr)
    trig = parse_trigger(r.stdout + r.stderr)
    elapsed = time.time() - t0
    summary = {
        "model": args.model, "carrier": args.carrier, "variant": args.variant,
        "binary": args.gem5, "outdir": str(outdir), "rc": r.returncode,
        "elapsed_s": round(elapsed, 1), "trigger": trig,
        "n/a": "teardown CHAOS_LSU_TRIGGER line absent (run truncated or "
               "injector unmounted)",
    }
    (outdir / "census.summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1))
    print(json.dumps(summary, ensure_ascii=False, indent=1), flush=True)

    if trig is None:
        print("CENSUS INVALID: no teardown eligible= line (n/a, not 0).",
              file=sys.stderr)
        return 2
    if trig["injected"] != "0":
        print(f"CENSUS CONTAMINATED: injected={trig['injected']} (must be 0); "
              f"the span pin failed — do NOT register this value.",
              file=sys.stderr)
        return 3
    print(f"CENSUS OK: LSQFWD_F0_SPAN[('{args.model}','{args.carrier}')] "
          f"= {trig['eligible']}  (injected=0, uninjected control)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
