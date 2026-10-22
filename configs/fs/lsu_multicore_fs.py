#!/usr/bin/env python3
# lsu_multicore_fs.py — ARM64 SMP full-system (FS) platform for CHAOS LSU FI.
#
# WHY THIS FILE EXISTS (R4-8-FSMC, 2026-10-22)
# -------------------------------------------
# 35 MDSPEC RunIDs are ledgered BLOCKED with the reason
# "workload-level:blocked(multicore-fs: litmus needs multi-core FS)" (W7
# Atomic-Litmus / W13 PARSEC). The standing ruling for this round is: first
# try to satisfy them with legal carriers that already exist in this repo,
# with open-source substitute workloads and with reproducible small litmus
# tests — a blanket "defer" is a failure mode.
#
# What the repo had (measured, not assumed):
#   * configs/se/arm_chaos_fs.py:254 hardcodes `SimpleProcessor(num_cores=1)`;
#     every CHAOS FS hook binds `processor.get_cores()[0]` (line 303/515/565).
#   * the only FS boot checkpoint (runs/lsu/fs_cpt_boot/cpt.237949797015,
#     taken 2026-09-29) is 1-core: its sibling config.ini has exactly one
#     `[board.processor.cores.core]` (type=BaseAtomicSimpleCPU, numThreads=1).
#   * the FS hierarchy is `PrivateL1PrivateL2CacheHierarchy` (CLASSIC).
#     gem5's classic memory system has NO cross-core coherence: v25 ships
#     `src/mem/cache/noncoherent_cache.{cc,hh}` and the old
#     `src/mem/cache/coherence/` directory is GONE. A multi-core classic
#     system therefore cannot run a litmus test at all — even the
#     FAULT-FREE control run would fail/hang, because a store by core 1
#     never invalidates core 0's private L1 line.
#   * coherence in this binary must come from Ruby. CHECKED: the prebuilt
#     binary (sha256 prefix 7d52bc1392a10055) contains
#     `gem5::ruby::RubySystem` and `gem5::ruby::CHI::CHIRequestMsg`, so the
#     stdlib CHI hierarchy (gem5.components.cachehierarchies.chi) is usable
#     WITHOUT a rebuild.
#   * gem5-fs/ ships `armv8_gem5_v1_{1,2,4,8,16}cpu.dtb`; the guest kernel is
#     Linux 5.15.36 (SMP-capable).
#
# So the missing piece was never "a kernel that can do SMP" — it was the
# BOARD: a multi-core FS config with a COHERENT (Ruby/CHI) + optionally a
# classic hierarchy, plus a checkpoint with >1 CPU (a 1-core checkpoint
# CANNOT be restored into a 2-core system: the restore would have to
# recreate a core that the checkpoint has no state for). This config is
# that board. `--coherence classic` is kept deliberately: it is the
# control arm that shows the classic path is non-coherent, and it is what
# the legacy single-core pipeline uses.
#
# PIPELINE (mirrors the 1-core §3.2 flow, checkpoint tick = the baseline):
#   1. boot (fast CPU):  --cpu Atomic   --coherence chi --num-cores 2 \
#                        --readfile configs/fs/boot_ckpt.rcS
#      -> boot_ckpt.rcS takes m5 checkpoint at userspace and m5 exit
#   2. run   (ROI CPU):  --restore-checkpoint <outdir>/cpt.<tick> --cpu O3 \
#                        --num-cores 2 --readfile configs/fs/litmus.rcS
#      -> the payload deploys and runs the repo-local litmus binaries
#
# HONEST LIMITS (recorded here, not discovered later):
#   * CHAOS injectors whose SimObject takes `Param.Cache` (CHAOSCache: C08
#     L1D coherence-state, P09 prefetch victim/dirty) CANNOT mount on a Ruby
#     hierarchy — Ruby L1s are cache *controllers*, not classic `Cache`
#     objects. The coherent multi-core platform and the classic-cache
#     injector are mutually exclusive by construction; see the R4-8-FSMC
#     report (docs/gem5-fi/lsu/mdspec/R4-8-FSMC-report.md) for the per-row
#     consequence. This config therefore mounts only CPU-side injectors
#     (CHAOSExMon self-attaches to cpu->isa[0]).
#   * the injector mounts on ONE core (--chaos_core, default 0). A fault on
#     core 1's exclusive monitor is not reachable from here without a
#     second SimObject instance; the flag exists so the choice is explicit
#     and auditable instead of silent.
#
# Usage:
#   build/ARM/gem5.opt --outdir=/tmp/out configs/fs/lsu_multicore_fs.py \
#       --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img \
#       --bootloader=gem5-fs/boot.arm64 --num-cores=2 --coherence=chi \
#       --cpu=Atomic --readfile=configs/fs/boot_ckpt.rcS

import argparse
import m5
from m5.objects import (ArmDefaultRelease, VExpress_GEM5_Foundation,
                        VExpress_GEM5_V1, CHAOSExMon, CHAOSArmTLB)
from gem5.components.boards.arm_board import ArmBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy as ClassicL1L2,
)
from gem5.components.cachehierarchies.chi.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy as ChiL1L2,
)
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import (
    KernelResource, DiskImageResource, BootloaderResource,
)
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator

# [MDSPEC][R4-8-FSMC-B] CHAOSPropagation may be absent from an older binary —
# import defensively and refuse loudly rather than silently emitting nothing.
try:
    from m5.objects import CHAOSPropagation
except ImportError:  # pragma: no cover - depends on the binary
    CHAOSPropagation = None

p = argparse.ArgumentParser()
p.add_argument("--kernel", required=True, help="path to vmlinux")
p.add_argument("--disk", required=True, help="path to the disk image")
p.add_argument("--bootloader", required=True, help="path to boot.arm64")
p.add_argument("--root-partition", default="/dev/vda1")
p.add_argument("--cpu", default="Atomic", choices=["TIMING", "O3", "Atomic"])
p.add_argument("--mem-size", default="2GiB")
p.add_argument("--platform", default="V1", choices=["V1", "Foundation"])
p.add_argument("--readfile", default=None)
p.add_argument("--restore-checkpoint", default=None)
# ---- the R4-8-FSMC knobs -------------------------------------------------
p.add_argument("--num-cores", type=int, default=2,
               help="SMP core count. The DTB + kernel arg 'nr_cpus' follow "
                    "this. A checkpoint taken with N cores can only be "
                    "restored with the same N.")
p.add_argument("--coherence", default="chi", choices=["chi", "classic"],
               help="chi = Ruby/CHI (COHERENT; required for any litmus/"
                    "shared-memory ordering workload). classic = the legacy "
                    "non-coherent classic hierarchy (control arm; keeps the "
                    "old 1-core pipeline byte-identical at --num-cores=1).")
p.add_argument("--l1d-size", default="16KiB")
p.add_argument("--l1i-size", default="16KiB")
p.add_argument("--l2-size", default="256KiB")
p.add_argument("--l1d-assoc", type=int, default=4)
p.add_argument("--l1i-assoc", type=int, default=4)
p.add_argument("--l2-assoc", type=int, default=8)
p.add_argument("--chaos_core", type=int, default=0,
               help="which core the CPU-side injectors attach to "
                    "(processor.get_cores()[N])")
# §2.4 CHAOSExMon (O01/O02/O03) — CPU-side, self-attaches to isa.
p.add_argument("--chaos_exmon", action="store_true")
p.add_argument("--exmon_mode", default="stxr_force_success",
               choices=["stxr_force_success", "stxr_force_fail",
                        "o01_monitor_addr_bitflip", "o02_monitor_state_corrupt"])
p.add_argument("--exmon_first_clock", type=lambda x: int(x, 0), default=1000)
p.add_argument("--exmon_max_faults", type=lambda x: int(x, 0), default=1)
p.add_argument("--exmon_rng_seed", type=lambda x: int(x, 0), default=20260825)
p.add_argument("--exmon_lsu_tier", default="off",
               choices=["off", "F0", "F1", "F2", "F3", "F4", "F5", "F6"])
p.add_argument("--exmon_lsu_warmup_events", type=lambda x: int(x, 0), default=0)
p.add_argument("--exmon_lsu_span_events", type=lambda x: int(x, 0), default=1000)
# [MDSPEC][R4-8-FSMC-B] CHAOSPropagation unified propagation stream (FS side).
# WHY: CHAOSExMon already emits the O-series monitor-side chain events
# (exmon_monitor L1 -> exmon_rmw L2 -> exmon_stxr L3, CHAOSExMon.cc:255/97/113)
# but those calls route through CHAOSPropagation::instance(), which is nullptr
# unless a CHAOSPropagation SimObject is instantiated — so on the multi-core FS
# platform those events were silently dropped and the A-group cells had an
# oracle but NO propagation chain. This mounts it, mirroring the 1-core FS
# precedent (configs/se/arm_chaos_fs.py:551-575).
p.add_argument("--chaos_propagation", action="store_true",
               help="attach CHAOSPropagation (L0-L5 propagation trace); "
                    "O3-only, hard error otherwise")
p.add_argument("--prop_trace_file", default="prop_trace.csv.gz")
p.add_argument("--prop_run_id", default="")
p.add_argument("--prop_sample_run_id", default="")
args = p.parse_args()

if args.num_cores < 1:
    raise SystemExit("[lsu_multicore_fs] --num-cores must be >= 1")
if args.coherence == "chi" and args.num_cores == 1:
    # Not fatal — a 1-core coherent system is a legitimate (degenerate)
    # control — but it is almost always a configuration mistake, so say so.
    print("[lsu_multicore_fs] NOTE: --coherence chi with --num-cores 1 is a "
          "degenerate (single-core) coherent system; the multi-core litmus "
          "grid needs >= 2.")

cpu_map = {"O3": CPUTypes.O3, "TIMING": CPUTypes.TIMING,
           "Atomic": CPUTypes.ATOMIC}

if args.coherence == "chi":
    cache_hierarchy = ChiL1L2(
        l1i_size=args.l1i_size, l1i_assoc=args.l1i_assoc,
        l1d_size=args.l1d_size, l1d_assoc=args.l1d_assoc,
        l2_size=args.l2_size, l2_assoc=args.l2_assoc,
    )
else:
    cache_hierarchy = ClassicL1L2(
        l1d_size=args.l1d_size, l1i_size=args.l1i_size,
        l2_size=args.l2_size,
    )

memory = DualChannelDDR4_2400(size=args.mem_size)
processor = SimpleProcessor(cpu_type=cpu_map[args.cpu],
                            num_cores=args.num_cores, isa=ISA.ARM)
release = ArmDefaultRelease()
platform = (VExpress_GEM5_V1() if args.platform == "V1"
            else VExpress_GEM5_Foundation())

board = ArmBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
    release=release,
    platform=platform,
)

kernel = KernelResource(local_path=args.kernel)
disk = DiskImageResource(local_path=args.disk, root_partition=args.root_partition)
bootloader = BootloaderResource(local_path=args.bootloader)

board.set_kernel_disk_workload(
    kernel=kernel,
    disk_image=disk,
    bootloader=bootloader,
    readfile=args.readfile,
    kernel_args=["root=" + args.root_partition, "rw",
                 "console=ttyAMA0", "earlycon=pl011,0x1c090000"],
)

print(f"[lsu_multicore_fs] num_cores={args.num_cores} "
      f"coherence={args.coherence} cpu={args.cpu} "
      f"l1d={args.l1d_size}/{args.l1d_assoc} l2={args.l2_size}/{args.l2_assoc}")

# CPU-side injector attachment. The stdlib ArmBoard builds the CPU + MMU
# lazily, so the hooks run in the hierarchy's _pre_instantiate (after
# construction, before m5.instantiate) — same discipline as
# configs/se/arm_chaos_fs.py. AbstractCacheHierarchy._pre_instantiate exists
# for BOTH the classic and the Ruby/CHI hierarchy, so one patch point works.
if args.chaos_exmon:
    if args.cpu != "O3":
        print(f"[lsu_multicore_fs] NOTE: --chaos_exmon on {args.cpu}; the "
              "exclusive-monitor hooks are ISA-side and work on any CPU, but "
              "the O-cell grid is an O3 north-star grid (--cpu O3).")
    _mounted = [False]
    _orig_pi = cache_hierarchy._pre_instantiate

    def _attach_injectors(root):
        _orig_pi(root)
        if _mounted[0]:
            return
        _mounted[0] = True
        core = processor.get_cores()[args.chaos_core]
        cpu = core.core
        ex = CHAOSExMon(
            isa=cpu.isa[0], cpu=cpu, mode=args.exmon_mode,
            probability=1.0, firstClock=args.exmon_first_clock,
            maxFaults=args.exmon_max_faults, rngSeed=args.exmon_rng_seed,
            lsuTier=args.exmon_lsu_tier,
            lsuWarmupEvents=args.exmon_lsu_warmup_events,
            lsuSpanEvents=args.exmon_lsu_span_events,
            writeLog=True,
        )
        board.chaos_exmon = ex
        print(f"[lsu_multicore_fs] CHAOSExMon attached to core "
              f"{args.chaos_core} (mode={args.exmon_mode}, "
              f"tier={args.exmon_lsu_tier})")
    cache_hierarchy._pre_instantiate = _attach_injectors

# [MDSPEC][R4-8-FSMC-B] CHAOSPropagation (FS multi-core path). O3-only: it
# self-attaches at startup() to cpu.chaosPropagation (LSQ-side hooks) and
# cpu.commit.chaosPropagation — Atomic/TIMING cores have neither, so asking
# for a trace on a non-O3 run is a hard error, not a silent empty file.
# Mirrors the 1-core FS precedent (configs/se/arm_chaos_fs.py:551-575).
if args.chaos_propagation:
    # NOTE (verified): `raise SystemExit(<str>)` inside a gem5 config does NOT
    # print the message on this build — it surfaces as an opaque
    # "pybind11::cast_error: Unable to cast Python instance of type <class
    # 'str'> to C++ type 'int'" abort at tick 0 (reproduced with the
    # pre-existing --num-cores guard too, so it is a platform quirk, not this
    # block's). Therefore print the reason explicitly BEFORE exiting so the
    # refusal is actually legible.
    if CHAOSPropagation is None:
        print("[lsu_multicore_fs] FATAL: --chaos_propagation needs a gem5 "
              "binary built with CHAOSPropagation (the worktree binary has it).")
        raise SystemExit(1)
    if cpu_map[args.cpu] is not CPUTypes.O3:
        print("[lsu_multicore_fs] FATAL: --chaos_propagation is O3-only (got "
              "--cpu %s). The FS roadmap is Atomic boot -> O3 restore; set "
              "--cpu O3." % args.cpu)
        raise SystemExit(1)
    _prop_cpu = processor.get_cores()[args.chaos_core].core
    board.chaos_propagation = CHAOSPropagation(
        cpu=_prop_cpu,
        traceFile=args.prop_trace_file,
        writeLog=True,
        runId=args.prop_run_id,
        sampleRunId=args.prop_sample_run_id,
    )
    print("[lsu_multicore_fs] CHAOSPropagation attached on core %d "
          "(trace=%s, run_id=%r, sample_run_id=%r)"
          % (args.chaos_core, args.prop_trace_file, args.prop_run_id,
             args.prop_sample_run_id))

if args.restore_checkpoint:
    import pathlib
    ckpt = pathlib.Path(args.restore_checkpoint)
    if not ckpt.exists():
        raise FileNotFoundError(f"--restore-checkpoint: {ckpt} not found")
    board._checkpoint = ckpt
    print(f"[lsu_multicore_fs] restoring from checkpoint: {ckpt}")


def _kernel_oops_exit():
    print("[lsu_multicore_fs] KERNEL OOPS under fault — exiting (classify: "
          "Crash/DUE per fs_mode)")
    return True


simulator = Simulator(
    board=board, full_system=True,
    on_exit_event={ExitEvent.KERNEL_OOPS: _kernel_oops_exit},
)
simulator.run()
