#!/usr/bin/env python3
"""LSU campaign orchestrator (09 W10) — model resolution + adaptive-sampling engine.

Reads 07-expanded-matrix.csv (337 cells), resolves every cell to either a
runnable gem5 command or an honest BLOCKED/DEFERRED/N-A classification
(README §8.3: blocked is marked, never silently skipped), runs each runnable
cell with the three-phase adaptive sampling from 05 r12-r15:
  Phase 1 (trial): 30 activated — discover injector errors / all-Crash /
                   zero-activation units (05 r13)
  Phase 2 (screening): >=385 activated (95% CI, ±5pp) — cell pass/fail
  Phase 3 (main): fixed-sample — the 21 frozen KEY_RUNIDS (task_plan
                   D-2026-10-08-采样) accumulate to MAIN_TARGET_KEY=2401;
                   every other RunID stays at the screening target (385,
                   no expansion). No sequential stop — Wilson 95% is
                   reported, never a stop condition (2026-10-08 policy).

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
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# M12: 深度无关 repo 根——draft 位于 tools/draft/（比正式文件深一层），
# parent.parent 会错解析到 tools/。向上查找标记目录；复制回 tools/ 后
# 解析结果与原式一致（T10 REPO 相等断言守护）。
_REPO = Path(__file__).resolve()
while not (_REPO / "configs" / "se").is_dir() and _REPO.parent != _REPO:
    _REPO = _REPO.parent
REPO = _REPO
G5 = REPO / "build/ARM/gem5.opt"
LSU_PROXY = REPO / "configs/se/lsu_proxy.py"
L5 = REPO / "tools/lsu_l5_classify.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from wilson import wilson_ci  # repo's single Wilson impl (no drift)

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
# ---- 2026-10-08 sampling policy (task_plan 全局实验口径,
# D-2026-10-08-采样; tools/draft/MIGRATION_DESIGN.md M2) ----
KEY_RUNIDS = frozenset({
    "A01-F0-W3", "A04-F0-W3", "T10-F0-W4", "T04-F0-W4",
    "S13-F0-W5", "S04-F0-W5", "L01-F0-W5", "L03-F0-W5",
    "C04-F0-W6", "C05-F0-W6", "C10-F0-W6", "C12-F0-W6",
    "O01-F0-W7", "O05-F0-W7", "P03-F0-W8", "P07-F0-W8", "P09-F0-W6",
    "T10-F0-W11", "S13-F0-W12", "O09-F0-W13", "P09-F0-W13",
})
SCREENING_TARGET = 385   # 全部有效 RunID 累计 activated 目标
MAIN_TARGET_KEY = 2401   # 仅 KEY_RUNIDS 累计 activated 目标


def resolve_main_target(runid, args):
    """M3/M5: main 阶段目标按 RunID 解析——KEY_RUNIDS→2401，其余→
    screening 目标（不扩样）。--main-target 已废弃，不参与解析。"""
    return MAIN_TARGET_KEY if runid in KEY_RUNIDS else args.screening_target


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
    # --- TLB (W7 / M3 plan Task 5): FS-only family on lsu_b0_fs + B0 cpt.
    # faultType surface verified on arm_chaos_fs.py:81-100 (T3 smoke real run).
    # HONEST approximations: T10's low/mid/high pfn-bit banding submodel is
    # NOT parameterized in CHAOSArmTLB (random-bit only) — T10 rides T01's
    # bit_flip with the campaign seed driving bit choice (noted per-cell).
    "T01": ("armtlb", ["--tlb_fault_type", "bit_flip"]),
    "T02": ("armtlb", ["--tlb_fault_type", "bit_flip",
                       "--tlb_bits_to_change", "2"]),
    "T03": ("armtlb", ["--tlb_fault_type", "stuck_at_zero"]),  # stuck1 by seed parity
    "T04": ("armtlb", ["--tlb_fault_type", "pfn_to_mapped_page"]),
    "T10": ("armtlb", ["--tlb_fault_type", "bit_flip"]),  # approx: no banding submodel
}

# ---- FS carrier (M3 plan Task 5/6 decision tree) ----
# T-cell design workloads (MiBench/TLB-AliasPerm/GAP) have no binaries on the
# stock ubuntu image; SPEC stays license-blocked. Runnable T-cells execute on
# the tlb_probe.rcS carrier (kernel/user mixed TLB pressure + md5 oracle) —
# the substitution is recorded in the backfill note, never silent.
FS_CONFIG = REPO / "configs/fs/lsu_b0_fs.py"
FS_CARRIER_RC = REPO / "configs/fs/tlb_probe.rcS"
FS_KERNEL = REPO / "gem5-fs/vmlinux"
FS_DISK = REPO / "gem5-fs/ubuntu.img"
FS_BOOTLOADER = REPO / "gem5-fs/boot.arm64"
TLB_PROBE_GOLDEN = "b6d81b360a5672d80c27430f39153e2c"  # md5 of 1 MiB zeros (host-computed)
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
    # TLB models: T05-T08 modes NOT yet implemented in CHAOSArmTLB (W7
    # follow-up — M3 plan Task 7 Step 3); T01-T04/T10 are mapped (armtlb
    # family above), T09 is B0-N/A below. The old blanket T01-T10 block
    # fired before MODEL_FLAGS and masked the new FS routing (dry-run caught).
    "T05": "deferred(mode unimplemented: valid/global/ASID state)",
    "T06": "deferred(mode unimplemented: permission legal-substitution)",
    "T07": "deferred(mode unimplemented: hit fabrication/way select)",
    "T08": "deferred(mode unimplemented: walk pairing)",
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
    FS families (armtlb) resolve to an FS flag set with the tlb_probe
    carrier; their golden is the host-computed payload oracle.
    """
    model = cell[COL_MODEL].strip()
    freq = cell[COL_FREQ].strip()
    workload = cell[COL_WORKLOAD].strip()

    # 1. workload-level block (FS / multicore-FS / SPEC license). SPEC stays
    #    blocked even for FS-family models — the license gap is workload-real
    #    and a carrier substitution cannot honor it (T6 decision, honest).
    for key, reason in WL_BLOCKED.items():
        if key in workload:
            if model in MODEL_FLAGS and MODEL_FLAGS[model][0] == "armtlb" \
                    and key == "SPEC":
                return None, None, reason
            if model in MODEL_FLAGS and MODEL_FLAGS[model][0] == "armtlb":
                # MiBench / TLB-AliasPerm / GAP carriers: runnable via FS
                continue
            return None, None, reason
    # 2. model-level block / deferral / N-A
    if model in MODEL_BLOCKED:
        return None, None, MODEL_BLOCKED[model]
    # 3. model must have a mapping
    if model not in MODEL_FLAGS:
        return None, None, f"NOT-MAPPED(model {model})"
    family, extra = MODEL_FLAGS[model]

    # 3a. FS family: B0 platform + checkpoint restore + tlb_probe carrier
    if family == "armtlb":
        flags = ["--kernel", str(FS_KERNEL), "--disk", str(FS_DISK),
                 "--bootloader", str(FS_BOOTLOADER), "--cpu", "O3",
                 "--readfile", str(FS_CARRIER_RC), "--ckpt-first-clock",
                 "--chaos_armtlb", "--tlb_first_clock", "1000",
                 "--tlb_probability", "1.0",
                 "--tlb_max_faults", "1"] + extra
        return flags, TLB_PROBE_GOLDEN, "fs:tlb_probe"

    # 4. workload must have an SE binary + golden
    binary = None
    for key, bin_name in WL_BINARY.items():
        if key in workload:
            binary = bin_name
            break
    if binary is None:
        return None, None, f"NOT-MAPPED(workload {workload[:40]})"
    golden = GOLDENS[binary]

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


def classify_fs_run(outdir, run_stdout, exit_code):
    """L5 classification for one FS (armtlb) run.

    Channels (T3 smoke-verified physics):
      Crash: kernel Oops — guest terminal 'Internal error: Oops' or the gem5
             log 'Kernel oops in guest' (crash_kind=kernel_oops)
      SDC:   tlb_probe oracle line present but wrong — md5 != host-computed
             golden (b6d81...) or rounds ok<10 (some round mismatched)
      Masked: oracle line with golden md5 AND ok==10
      Timeout: driver-killed (handled by caller)
    Injected: armtlb_injections.log 'Site: ' lines (the injector logs
    'Tick: ..., Site: arm_tlb_lookup_hit, ...'); activated=injected
    (near-tautological proxy, same documented class as other injectors).
    """
    import re as _re
    terminal = ""
    tf = outdir / "board.terminal"
    if tf.exists():
        terminal = tf.read_text(errors="replace")
    injected = 0
    ilog = outdir / "armtlb_injections.log"
    if ilog.exists():
        injected = sum(1 for ln in ilog.read_text(errors="replace").splitlines()
                       if "Site: " in ln)
    out = {"injected": injected, "activated": injected,
           "attempted": None, "eligible": None, "checksum": None}
    if "Oops" in terminal or "Kernel oops in guest" in run_stdout:
        out.update(outcome="Crash", crash_kind="kernel_oops")
    else:
        m = _re.findall(r"\[tlb_probe\.rcS\] ([0-9a-f]{32}) rounds ok=(\d+)/10",
                        terminal)
        if m:
            md5, ok = m[-1]
            out["checksum"] = md5
            out["rounds_ok"] = int(ok)
            if md5 != TLB_PROBE_GOLDEN or int(ok) < 10:
                out["outcome"] = "SDC"
            else:
                out["outcome"] = "Masked"
        elif exit_code != 0:
            out.update(outcome="Crash", crash_kind="guest_or_unknown")
        else:
            # clean exit but no oracle line — the guest died between restore
            # and payload (unclassifiable without more evidence; honest)
            out["outcome"] = "Unclassified"
    oc = out["outcome"]
    classes = {k: 0 for k in ("Masked", "Detected/Contained", "SDC",
                              "Crash", "Timeout")}
    if oc in classes and injected:
        classes[oc] = injected
    out["classes"] = classes
    out["mode"] = "FS"
    return out


def run_single_cell(cell, args, seed, outdir):
    """Run one gem5 invocation for a single cell×seed. Returns classification dict."""
    runid = cell[COL_RUNID]
    model = cell[COL_MODEL].strip()

    flags, golden, _binary = resolve_cell(cell)
    if flags is None:
        return {"outcome": "Blocked", "error": golden}

    family = MODEL_FLAGS[model][0]
    outdir.mkdir(parents=True, exist_ok=True)

    # ---- FS family (armtlb): lsu_b0_fs + checkpoint restore + carrier ----
    if family == "armtlb":
        if not args.fs_checkpoint:
            return {"outcome": "Blocked",
                    "error": "FS cells need --fs-checkpoint (B0 cpt)"}
        cmd = [str(G5), "--outdir", str(outdir), str(FS_CONFIG)]
        cmd += ["--restore-checkpoint", args.fs_checkpoint]
        cmd += flags
        cmd += ["--tlb_rng_seed", str(seed)]
        # T03 stuck0/stuck1 alternate by seed parity (both sub-modes sampled)
        if model == "T03":
            i = cmd.index("--tlb_fault_type")
            cmd[i + 1] = "stuck_at_zero" if seed % 2 else "stuck_at_one"
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=args.fs_timeout)
            (outdir / "run.out").write_text(proc.stdout)
            (outdir / "run.err").write_text(proc.stderr)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            (outdir / "run.out").write_text("")
            (outdir / "run.err").write_text("TIMEOUT")
            # Evidence-preserving timeout (the 6e0dcd52 family): a killed
            # run may already carry injections — read the log and classify
            # Timeout WITH the activated count. The T01 anchor trial hid
            # 2/5 runs per cell this way (injected bit-63 corruptions that
            # survived as slow-progress runs; killed at the 30-min cap with
            # injected=0 — the Timeout channel was silently empty).
            inj = 0
            ilog = outdir / "armtlb_injections.log"
            if ilog.exists():
                inj = sum(1 for ln in
                          ilog.read_text(errors="replace").splitlines()
                          if "Site: " in ln)
            classes = {k: 0 for k in ("Masked", "Detected/Contained", "SDC",
                                      "Crash", "Timeout")}
            classes["Timeout"] = inj
            return {"outcome": "Timeout", "injected": inj, "activated": inj,
                    "classes": classes, "mode": "FS"}
        return classify_fs_run(outdir, proc.stdout, exit_code)

    # ---- SE families ----
    cmd = [str(G5), "--outdir", str(outdir), str(LSU_PROXY)]
    cmd += flags
    cmd += [FAMILY_SEED[family], str(seed)]
    # A03 stuck0/stuck1 alternate by seed parity (both sub-modes sampled);
    # swap the mode VALUE in place — the flag sits mid-list, before the
    # seed flag (the first version clobbered --addrpath_rng_seed by writing
    # cmd[-2], losing per-seed variation for A03; caught in code review).
    if model == "A03":
        i = cmd.index("--addrpath_mode")
        cmd[i + 1] = "a03_stuck0" if seed % 2 else "a03_stuck1"

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
        # CHAOSCache logs "Tick:"/"Cycle:" lines (no "Site: " lines and no
        # CHAOS_LSU_TRIGGER stdout funnel — the legacy firstClock mechanism),
        # so the classifier's fallback misses it. Recover the FULL L0/L5
        # record from the log count: injected = activated (near-tautological
        # activation, same documented approximation as the other injectors)
        # and the whole run's outcome lands in one class (04 L5 single-run
        # verdict) so the conservation identity holds.
        result["injected"] = cache_inj
        result["activated"] = cache_inj
        oc = result.get("outcome", "Masked")
        if isinstance(result.get("classes"), dict):
            result["classes"][oc] = cache_inj
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
    p.add_argument("--max-seeds-per-cell", type=int, default=10,
                   help="seed cap per cell (05 r13-r15: adaptive targets govern; "
                        "the cap bounds compute when activation is sparse)")
    p.add_argument("--n-seeds", type=int, default=None,
                   help="[deprecated alias] sets --max-seeds-per-cell")
    # Adaptive-sampling knobs (05 r13-r15). Defaults are the spec values;
    # toy-grid verification lowers them explicitly.
    p.add_argument("--trial-target", type=int, default=30,
                   help="trial-phase activated target (05 r13)")
    p.add_argument("--screening-target", type=int, default=385,
                   help="screening-phase activated target (05 r14)")
    p.add_argument("--main-target", type=int, default=None,
                   help="[deprecated 2026-10-08] ignored — main-phase target "
                        "resolves per RunID (KEY_RUNIDS→2401, others→"
                        "screening-target)")
    p.add_argument("--wilson-stop-hw", type=float, default=0.02,
                   help="[deprecated 2026-10-08] ignored — fixed-sample "
                        "policy; Wilson 95% is reported, never a stop")
    p.add_argument("--timeout", type=int, default=300,
                   help="per-run wall-clock seconds — absolute cap (05 r17; all "
                         "SE workloads run 10-40s, so 300s > 10x any golden)")
    # ---- FS (armtlb family / M3) ----
    p.add_argument("--fs-checkpoint", default=None,
                   help="B0 checkpoint dir (runs/fs_lsu/boot_b0/cpt.*) — "
                        "required for T-cell runs")
    p.add_argument("--fs-timeout", type=int, default=1800,
                   help="FS per-run wall-clock cap (05 r17 FS: restore+payload "
                        "~4 min measured, 30 min absolute cap)")
    a = p.parse_args()
    if a.n_seeds is not None:
        a.max_seeds_per_cell = a.n_seeds
    if a.main_target is not None:
        print("warning: --main-target is deprecated (2026-10-08 sampling "
              "policy) and ignored; main target = 2401 for KEY_RUNIDS, "
              "else screening-target", file=sys.stderr)

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

    def work(cell):
        return run_cell_adaptive(cell, a, outroot)

    # Parallel slots: CLAUDE.md hard cap 4 concurrent gem5 processes (29GB
    # host OOM discipline). Cells run in parallel; the adaptive loop within
    # a cell is sequential (each seed's stop-rule check needs prior results).
    slots = max(1, min(4, a.max_parallel))
    with ThreadPoolExecutor(max_workers=slots) as pool:
        for _runid, line in pool.map(work, runnable):
            print(line)


def run_cell_adaptive(cell, args, outroot):
    """Three-phase adaptive sampling for one cell (05 r13-r15, r16, r19/r20).

    trial:      stop at --trial-target activated (injector-error discovery)
    screening:  stop at --screening-target activated (cell pass/fail)
    main:       fixed-sample — KEY_RUNIDS→2401, others→screening target;
                no sequential stop (2026-10-08 policy)
    All phases additionally respect --max-seeds-per-cell (compute bound;
    stop_reason records which bound fired — never silent).
    F1-F4 cells: multi-activated runs are one cluster (05 r19/r20) — the
    Wilson interval is computed per-RUN (runs-with-SDC / runs); F0/F5/F6
    are per-activated (SDC/activated, 05 r12).
    Seeds are 1..N per cell — common random numbers across cells by
    construction (same seed = same injection-point RNG draws, 05 r16).
    """
    runid = cell[COL_RUNID]
    freq = cell[COL_FREQ].strip()
    clustered = freq in ("F1", "F2", "F3", "F4")
    if args.phase == "main":
        target = resolve_main_target(runid, args)   # M5: KEY→2401 其余→385
    else:
        target = {"trial": args.trial_target,
                  "screening": args.screening_target}[args.phase]
    classes = {k: 0 for k in ("Masked", "Detected/Contained", "SDC",
                              "Crash", "Timeout")}
    runs, attempted, activated = [], 0, 0
    seed, stop_reason = 0, None
    cell_out = outroot / runid

    while True:
        if activated >= target:
            stop_reason = "%s-target-met" % args.phase
            break
        if seed >= args.max_seeds_per_cell:
            stop_reason = "seed-cap(%d)" % args.max_seeds_per_cell
            break
        seed += 1
        r = run_single_cell(cell, args, seed, cell_out / f"seed{seed}")
        act = int(r.get("activated", 0) or 0)
        runs.append({"seed": seed, "cluster_id": "%s#%d" % (runid, seed),
                     "activated": act,
                     "outcome": r.get("outcome", "Unclassified")})
        attempted += int(r.get("attempted", 0) or 0)
        activated += act
        oc = r.get("outcome")
        if oc in classes:
            classes[oc] += act

    hw, lo, hi = _wilson_stats(classes, activated, runs, clustered)
    sdc_rate = (classes["SDC"] / activated) if activated else 0.0
    act_rate = (activated / attempted) if attempted else 0.0
    cons = (activated == sum(classes.values()))
    result = {
        "runid": runid, "phase": args.phase, "seed_batches": seed,
        "clustered": clustered, "n_runs": len(runs),
        "attempted": attempted, "activated": activated,
        "classes": classes, "sdc_rate": round(sdc_rate, 4),
        "activation_rate": round(act_rate, 4),
        "wilson": {"lo": round(lo, 4), "hi": round(hi, 4)},
        "stop_reason": stop_reason, "conservation": "OK" if cons else "VIOLATION",
        "runs": runs,
    }
    cell_out.mkdir(parents=True, exist_ok=True)
    (cell_out / "cell_results.json").write_text(json.dumps(result, indent=1))
    return runid, ("  %s: phase=%s n_runs=%d activated=%d sdc=%d "
                   "stop=%s cons=%s" %
                   (runid, args.phase, len(runs), activated, classes["SDC"],
                    stop_reason, result["conservation"]))


def _wilson_stats(classes, activated, runs, clustered):
    """Wilson 95% on the SDC rate; F1-F4 clusters per-run (05 r19/r20)."""
    if clustered:
        k = sum(1 for r in runs if r["outcome"] == "SDC")
        n = len(runs)
    else:
        k, n = classes["SDC"], activated
    lo, hi, _p = wilson_ci(k, n)
    return (hi - lo) / 2, lo, hi


if __name__ == "__main__":
    main()
