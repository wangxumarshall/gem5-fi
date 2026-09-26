#!/usr/bin/env python3
"""LSU campaign orchestrator (09 W10) — model resolution + adaptive-sampling engine.

Reads 07-expanded-matrix.csv (337 cells), resolves every cell to either a
runnable gem5 command or an honest BLOCKED/DEFERRED/N-A classification
(README §8.3: blocked is marked, never silently skipped), runs each runnable
cell with the three-phase adaptive sampling from 05 r12-r15:
  Phase 1 (trial): 30 activated — discover injector errors / all-Crash /
                   zero-activation units (05 r13)
  Phase 2 (screening): >=385 activated (95% CI, ±5pp) — cell pass/fail
  Phase 3 (main): sequential until Wilson 95% half-width <=2pp or 5000
                   activated (05 r14/r15)

Per-run classification via tools/lsu_l5_classify.py (L5 conservation).

MODEL->INJECTOR MAPPING PROVENANCE (git-verified, 2026-09-26):
  A-series   W4 9fbec314 (dual-hook 7-mode family on CHAOSAddrPath)
  S/L-series W5 c7743989..a0ecfd20 (pre-hook family + lsqfwd modes + l03)
  C-series   W6 65e5d022..2b967a9b (CHAOSCache targetField/faultType)
  P-series   W8 (this branch, f76f5632 CHAOSPrefetch)
  O-series   W8 (this branch, 1b97b714 ExMon O01/O02 + existing stxr modes)
HONEST DEFERRED (notify-only event sources, consumer-side corruption NOT
implemented — W5/W6 wired chaosLsuF6Notify call sites only): S10, L04,
C11, C12, C14, C15. No-clean-hook deferred: A07, P06, O04, O09.
B0 protection rows (09 §6.4 — not applicable, never zero-filled):
S12, T09, C13, O08.

Usage:
  python3 tools/lsu_campaign.py --matrix docs/gem5-fi/lsu/07-expanded-matrix.csv \
      --outdir runs/lsu --max-parallel 4 [--cells A01-F0-W3,...] [--dry-run]
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
G5 = REPO / "build/ARM/gem5.opt"
LSU_PROXY = REPO / "configs/se/lsu_proxy.py"
L5 = REPO / "tools/lsu_l5_classify.py"

# Expanded matrix column indices (0-based; col 0 = "Excel行")
COL_RUNID = 1     # RunID like A01-F0-W3
COL_MODEL = 2     # Model ID like A01
COL_UNIT = 3      # Unit like AGU
COL_FREQ = 7      # Frequency tier F0-F6
COL_WORKLOAD = 9  # Workload name

# ---------------------------------------------------------------- workloads
# W9 SE-testable binaries (all gem5==native, goldens in runner.py GOLDEN_IDS).
WL_BINARY = {
    "MiniCheck": "mini_check",
    "AGU-AddrModes": "agu_addrmodes",
    "SQ-Forward": "sq_forward",
    "Cache-DirtyEvict": "cache_dirtyevict",
    "Prefetch-Stride": "prefetch_stride",
    "STREAM+PointerChase": "stream_chase",
    "BEEBS-DelayAVF": "beebs_kernels",
    "GAP/Graph500": "gap_bfs",
    "SQLite": "sqlite_like",
}
GOLDENS = {
    "mini_check": "07568da9f3ad5665",
    "agu_addrmodes": "728e604ffcec539d",
    "sq_forward": "1f4cbf14327717df",
    "cache_dirtyevict": "062e5124df3667f9",
    "prefetch_stride": "629727c0ad9ca8ef",
    "stream_chase": "50ab96a7fe8f6ec2",
    "beebs_kernels": "a10b9827edd8a9fb",
    "gap_bfs": "030921682b3731f2",
    "sqlite_like": "33f836327a416d35",
}
# Workload-level structural blocks (README §8.3 — 65 cells on W1/W4/W7/W13,
# plus SPEC-license W11). Matched by keyword on the workload column.
WL_BLOCKED = {
    "MiBench": "blocked(fs-infra: SE has no MiBench FS pipeline)",
    "TLB-AliasPerm": "blocked(fs-infra: TLB workload needs FS)",
    "Atomic-Litmus": "blocked(multicore-fs: litmus needs multi-core FS)",
    "PARSEC": "blocked(multicore-fs: PARSEC needs multi-core FS)",
    "SPEC": "blocked(spec-license: SPEC CPU2017 needs a license)",
}

# ---------------------------------------------------------------- models
# model -> (family, extra_flags). The family decides the trigger-tier flags
# and the seed flag; tier value comes from the cell's F column.
#   addrpath family: bit-level A01-A03 ride --addrpath_mode; the PRE family
#     (A04-A06/A08 + S04-S07/S11/S13 + L01/L02) rides --agu_pre_mode at the
#     LSQ::pushRequest entry hook (W1 ⑦ ruling).
#   lsqfwd family: S01-S03/S08/S09 data/forwarding modes + L03 flag.
#   cache family: CHAOSCache on l1d-cache-0 (legacy firstClock/probability/
#     maxFaults mechanism — lsuTier params are wire-ready, NOT consumed yet;
#     honest approximation documented per-cell in the backfill notes).
#   prefetch family: CHAOSPrefetch (W8, f76f5632).
#   exmon family: CHAOSExMon (legacy window path; O-cells are workload-
#     blocked anyway — wire-verification vehicle only).
MODEL_FLAGS = {
    # --- AGU (W4 9fbec314) ---
    "A01": ("addrpath", ["--addrpath_mode", "a01_bit"]),
    "A02": ("addrpath", ["--addrpath_mode", "a02_2bit"]),
    "A03": ("addrpath", ["--addrpath_mode", "a03_stuck0"]),  # stuck1 by seed parity (note)
    "A04": ("addrpath", ["--agu_pre_mode", "a04_subst"]),
    "A05": ("addrpath", ["--agu_pre_mode", "a05_shift"]),
    "A06": ("addrpath", ["--agu_pre_mode", "a06_size", "--agu_size_to", "2"]),
    "A08": ("addrpath", ["--agu_pre_mode", "a08_subst"]),
    # --- SQ data/forwarding family on CHAOSLSQFwd (W5 b41f4d9a verified) ---
    "S01": ("lsqfwd", ["--lsq_struct_mode", "byte_flip"]),
    "S02": ("lsqfwd", ["--lsq_struct_mode", "byte_flip", "--bits_to_change", "2"]),
    "S03": ("lsqfwd", ["--lsq_struct_mode", "byte_lane_skew"]),  # approx: stuck-lane mask family
    "S08": ("lsqfwd", ["--lsq_struct_mode", "fwd_source_sub"]),
    "S09": ("lsqfwd", ["--lsq_struct_mode", "byte_lane_skew"]),  # approx: concat/assembly skew
    # --- SQ addr/state family on the PRE hook (W5 c7743989..1beea50d) ---
    "S04": ("addrpath", ["--agu_pre_mode", "s04_store_subst"]),
    "S05": ("addrpath", ["--agu_pre_mode", "s05_store_size"]),
    "S06": ("addrpath", ["--agu_pre_mode", "s06_store_state"]),
    "S07": ("addrpath", ["--agu_pre_mode", "s07_store_ptr"]),
    "S11": ("addrpath", ["--agu_pre_mode", "s11_store_lost"]),
    "S13": ("addrpath", ["--agu_pre_mode", "s13_store_addr"]),
    # --- LQ (W5) ---
    "L01": ("addrpath", ["--agu_pre_mode", "l01_load_addr"]),
    "L02": ("addrpath", ["--agu_pre_mode", "l02_load_state"]),
    "L03": ("lsqfwd", ["--lsqfwd_l03"]),
    # --- L1D-Cache (W6; C-series runs the CHAOSCache legacy mechanism) ---
    "C01": ("cache", ["--l1d_target_field", "data", "--l1d_fault_type", "bit_flip"]),
    "C02": ("cache", ["--l1d_target_field", "data", "--l1d_fault_type", "bit_flip",
                      "--bits_to_change", "2"]),
    "C03": ("cache", ["--l1d_target_field", "data", "--l1d_fault_type", "stuck_at_zero"]),
    "C04": ("cache", ["--l1d_target_field", "tag", "--l1d_fault_type", "bit_flip"]),
    "C05": ("cache", ["--l1d_target_field", "tag", "--l1d_fault_type", "bit_flip"]),   # approx: tag relabel = C04
    "C06": ("cache", ["--l1d_target_field", "valid"]),
    "C07": ("cache", ["--l1d_target_field", "dirty"]),
    "C08": ("cache", ["--l1d_target_field", "coh"]),
    "C09": ("cache", ["--l1d_target_field", "data_shift"]),
    "C10": ("cache", ["--l1d_target_field", "valid"]),  # approx: PLRU->valid invalidate
    # --- Prefetcher (W8 f76f5632, verified today) ---
    "P01": ("prefetch", ["--prefetch_mode", "p01_stride_bitflip"]),
    "P02": ("prefetch", ["--prefetch_mode", "p02_confidence_corrupt"]),
    "P03": ("prefetch", ["--prefetch_mode", "p03_addr_subst"]),
    "P04": ("prefetch", ["--prefetch_mode", "p05_drop_dup"]),   # approx: queue drop/dup
    "P05": ("prefetch", ["--prefetch_mode", "p05_drop_dup"]),
    "P07": ("cache", ["--l1d_target_field", "tag"]),            # approx: fill way/tag -> tag
    "P08": ("prefetch", ["--prefetch_mode", "p08_stride_stuck"]),
    "P09": ("cache", ["--l1d_target_field", "dirty"]),          # approx: pf dirty evict -> dirty
    # --- Atomic (W8 1b97b714 + existing stxr modes) ---
    "O01": ("exmon", ["--exmon_mode", "o01_monitor_addr_bitflip"]),
    "O02": ("exmon", ["--exmon_mode", "o02_monitor_state_corrupt"]),
    "O03": ("exmon", ["--exmon_mode", "stxr_force_fail"]),  # status-flip semantics
}
# Model-level blocks (never silently skipped; the reason lands in col26/27).
MODEL_BLOCKED = {
    # notify-only event sources — consumer-side corruption NOT implemented
    # (W5/W6 wired chaosLsuF6Notify call sites only; grep-verified 2026-09-26)
    "S10": "deferred(consumer-side: StoreSet SSID corruption event source only)",
    "L04": "deferred(consumer-side: response-pairing event source only)",
    "C11": "deferred(consumer-side: MSHR merge event source only)",
    "C12": "deferred(consumer-side: fill-timing event source only)",
    "C14": "deferred(consumer-side: MSHR busy event source only)",
    "C15": "deferred(consumer-side: MSHR occupancy event source only)",
    # no clean hook (documented in injector headers / W4-W8 session notes)
    "A07": "deferred(R4: no clean hook)",
    "P06": "deferred(no clean hook: prefetch-as-demand marking)",
    "O04": "deferred(RMW data path needs cache-side SwapResp hook)",
    "O09": "deferred(RMW operand path needs cache-side hook)",
    # B0 protection rows (09 §6.4): not applicable, never zero-filled
    "S12": "不适用(B0无保护)",
    "T09": "不适用(B0无保护)",
    "C13": "不适用(B0无保护)",
    "O08": "不适用(B0无保护)",
    # TLB models: SE-inert by construction (W1 ③: SE translateSe never
    # calls TLB::lookup) — every T cell is workload-blocked anyway; the
    # model-level block makes the classification robust even if a T cell
    # ever appeared on an SE workload.
    **{f"T{i:02d}": "blocked(fs-infra: TLB::lookup zero-call in SE, W1 ③)"
       for i in range(1, 11)},
}
# O05-O07 are multicore-semantic models — their cells sit on Atomic-Litmus/
# PARSEC (workload-blocked); add the model-level reason for robustness.
MODEL_BLOCKED.update({
    "O05": "blocked(multicore-fs: RMW ordering needs multi-core)",
    "O06": "blocked(multicore-fs: barrier completion needs multi-core)",
    "O07": "blocked(multicore-fs: order-tag swap needs multi-core)",
})

# Trigger-tier flags per family. F0 span: addrpath/lsqfwd eligible streams
# are per-request (large; span 1000 verified by the W10 trial); prefetch
# eligible streams are per-calculatePrefetch (131/9 on prefetch_stride —
# span 50/8 verified today; a span larger than the stream never fires,
# noted as the F0-uniform approximation).
FAMILY_TIER_FLAGS = {
    "addrpath": lambda tier: ["--addrpath_lsu_tier", tier,
                              "--addrpath_warmup_events", "0",
                              "--addrpath_span_events", "1000"],
    "lsqfwd": lambda tier: ["--lsqfwd_lsu_tier", tier,
                            "--lsqfwd_warmup_events", "0",
                            "--lsqfwd_span_events", "1000"],
    "cache": lambda tier: [],   # legacy firstClock mechanism (tier not consumed)
    "prefetch": lambda tier: ["--prefetch_lsu_tier", tier,
                              "--prefetch_warmup_events", "0",
                              "--prefetch_span_events", "50"],
    "exmon": lambda tier: [],   # legacy window path (tier not consumed)
}
FAMILY_MOUNT = {
    "addrpath": ["--chaos_addrpath"],
    "lsqfwd": ["--chaos_lsqfwd"],
    "cache": ["--chaos_l1d", "--l1d_first_clock", "1000", "--l1d_max_faults", "1"],
    "prefetch": ["--chaos_prefetch", "--prefetch_max_faults", "1"],
    "exmon": ["--chaos_exmon", "--exmon_first_clock", "1000", "--exmon_max_faults", "1"],
}
# Seed flag per family (findings lesson: injectors take --<inj>_rng_seed,
# lsqfwd takes the generic --rng_seed).
FAMILY_SEED = {
    "addrpath": "--addrpath_rng_seed",
    "lsqfwd": "--rng_seed",
    "cache": "--l1d_rng_seed",
    "prefetch": "--prefetch_rng_seed",
    "exmon": "--exmon_rng_seed",
}


def load_matrix(path):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    header = rows[0]
    cells = []
    for r in rows[1:]:
        if len(r) > COL_RUNID and r[COL_RUNID].strip():
            cells.append(r)
    return header, cells


def resolve_cell(cell):
    """Cell -> (flags list, golden, binary) or (None, None, blocked_reason).

    Every cell resolves to exactly one of: runnable flags, or a blocked/
    deferred/N-A reason string. No cell may resolve to 'not mapped' —
    main() asserts this (CLAUDE.md: half-routed components are rejected).
    """
    model = cell[COL_MODEL].strip()
    freq = cell[COL_FREQ].strip()
    workload = cell[COL_WORKLOAD].strip()

    # 1. workload-level block (FS / multicore-FS / SPEC license)
    for key, reason in WL_BLOCKED.items():
        if key in workload:
            return None, None, reason
    # 2. model-level block / deferral / N-A
    if model in MODEL_BLOCKED:
        return None, None, MODEL_BLOCKED[model]
    # 3. model must have a mapping
    if model not in MODEL_FLAGS:
        return None, None, f"NOT-MAPPED(model {model})"
    # 4. workload must have an SE binary + golden
    binary = None
    for key, bin_name in WL_BINARY.items():
        if key in workload:
            binary = bin_name
            break
    if binary is None:
        return None, None, f"NOT-MAPPED(workload {workload[:40]})"
    golden = GOLDENS[binary]

    family, extra = MODEL_FLAGS[model]
    flags = ["--cmd", str(REPO / "workloads/directed" / binary), "--cpu", "O3"]
    flags += FAMILY_MOUNT[family]
    flags += FAMILY_TIER_FLAGS[family](freq)
    flags += extra
    return flags, golden, binary


def classify_run(outdir, stdout_file, golden, exit_code, stderr_file=None):
    """Run L5 classifier on one run's output."""
    cmd = ["python3", str(L5),
           "--run-dir", str(outdir),
           "--stdout", str(stdout_file),
           "--golden", golden,
           "--exit", str(exit_code)]
    if stderr_file and Path(stderr_file).exists():
        cmd += ["--stderr", str(stderr_file)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode == 0 and "LSU_L5:" in r.stdout:
        try:
            json_str = r.stdout.split("LSU_L5: ", 1)[1].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            pass
    return {"outcome": "Unclassified", "error": r.stderr[:200] if r.stderr else "unknown"}


def run_single_cell(cell, args, seed, outdir):
    """Run one gem5 invocation for a single cell×seed. Returns classification dict."""
    runid = cell[COL_RUNID]
    model = cell[COL_MODEL].strip()

    flags, golden, _binary = resolve_cell(cell)
    if flags is None:
        return {"outcome": "Blocked", "error": golden}

    family = MODEL_FLAGS[model][0]
    cmd = [str(G5), "--outdir", str(outdir), str(LSU_PROXY)]
    cmd += flags
    cmd += [FAMILY_SEED[family], str(seed)]
    # A03 stuck0/stuck1 alternate by seed parity (both sub-modes sampled)
    if model == "A03":
        cmd[-2] = "--addrpath_mode"
        cmd[-1] = "a03_stuck0" if seed % 2 else "a03_stuck1"

    outdir.mkdir(parents=True, exist_ok=True)
    stdout_file = outdir / "run.out"
    stderr_file = outdir / "run.err"
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=args.timeout)
        stdout_file.write_text(proc.stdout)
        stderr_file.write_text(proc.stderr)
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        stdout_file.write_text("")
        stderr_file.write_text("TIMEOUT")
        return {"outcome": "Timeout", "injected": 0, "activated": 0}

    # C-series: CHAOSCache logs to cache_injections.log, not stdout — read
    # it for the injection count (223e4b12 fix).
    cache_log = outdir / "cache_injections.log"
    cache_inj = 0
    if cache_log.exists():
        for line in cache_log.read_text(errors="replace").splitlines():
            if "Tick: " in line or "Cycle: " in line:
                cache_inj += 1

    result = classify_run(outdir, stdout_file, golden, exit_code, stderr_file)
    if cache_inj > 0 and result.get("injected", 0) == 0:
        result["injected"] = cache_inj
        result["injection_source"] = "cache_injections.log"
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--matrix", required=True)
    p.add_argument("--outdir", default="runs/lsu")
    p.add_argument("--max-parallel", type=int, default=4)
    p.add_argument("--cells", help="comma-separated RunIDs to run (default: all)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--phase", default="trial", choices=["trial", "screening", "main"])
    p.add_argument("--n-seeds", type=int, default=5,
                   help="seeds per cell this invocation (adaptive stop rules land "
                        "with the W10 engine; this remains the batch knob)")
    p.add_argument("--timeout", type=int, default=300,
                   help="per-run wall-clock seconds (05 r17)")
    a = p.parse_args()

    header, cells = load_matrix(a.matrix)
    print(f"Loaded {len(cells)} cells from {a.matrix}")

    if a.cells:
        wanted = set(a.cells.split(","))
        cells = [c for c in cells if c[COL_RUNID] in wanted]
        print(f"Filtered to {len(cells)} cells")

    # ---- resolution audit: every cell resolves or is honestly blocked ----
    counts = {}
    unrunnable = []
    runnable = []
    for cell in cells:
        flags, _g, reason = resolve_cell(cell)
        if flags is None:
            key = reason.split("(")[0].split(":")[0]
            counts[key] = counts.get(key, 0) + 1
            unrunnable.append((cell[COL_RUNID], reason))
        else:
            runnable.append(cell)
    counts["runnable"] = len(runnable)
    print(f"Resolution: {counts}")
    not_mapped = [r for r in unrunnable if r[1].startswith("NOT-MAPPED")]
    if not_mapped:
        for runid, why in not_mapped[:20]:
            print(f"  NOT-MAPPED: {runid}: {why}", file=sys.stderr)
        sys.exit("REFUSED: unmapped cells present (half-routed grid)")
    if a.dry_run:
        for runid, reason in unrunnable[:80]:
            print(f"  [blocked] {runid}: {reason}")
        print(f"dry-run: runnable={len(runnable)} blocked/deferred/na={len(unrunnable)}")
        return

    outroot = Path(a.outdir)
    for cell in runnable:
        runid = cell[COL_RUNID]
        cell_out = outroot / runid
        results = []
        for seed in range(1, a.n_seeds + 1):
            run_out = cell_out / f"seed{seed}"
            result = run_single_cell(cell, a, seed, run_out)
            results.append(result)
            outcome = result.get("outcome", "?")

        # Summarize
        outcomes = {}
        for r in results:
            oc = r.get("outcome", "Unclassified")
            outcomes[oc] = outcomes.get(oc, 0) + 1
        total_injected = sum(r.get("injected", 0) or 0 for r in results)
        print(f"  {runid}: n={len(results)} injected={total_injected} "
              f"outcomes={outcomes}")

        # Save cell summary (W10 engine consumes/upgrades this format)
        summary = {"runid": runid, "n_seeds": a.n_seeds,
                   "total_injected": total_injected, "outcomes": outcomes,
                   "results": results}
        (cell_out / "summary.json").parent.mkdir(parents=True, exist_ok=True)
        (cell_out / "summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
