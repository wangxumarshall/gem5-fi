# kp920_proxy.py — C2-KP (Kunpeng 920 / TaiShan V110) SE proxy config.
#
# Mirrors configs/se/arm_chaos.py (stdlib SimpleBoard + PrivateL1PrivateL2CacheHierarchy
# + SimpleProcessor + the 5 CHAOS injector mount points) BUT sets the TaiShan V110
# microarchitecture parameters on the O3 CPU, per design doc
# `docs/KUNPENG920-故障注入方案详细工程设计.md` §1.1 (config family "C2-KP", E3).
#
# V110 params sourced from docs/kunpeng.md §3 (TaiShan V110 core), as cited by the
# design doc §1.1. 4-wide OoO; ROB "moderate"; PRF-based rename; deep LSQ (weak
# memory order); double FSU. This config is the SE-mode proxy used by formal
# campaigns (config: C2) to quantify per-unit SDC on a Kunpeng-informed window —
# NOT a cycle-accurate V110 (see E3 limitations below).
#
# USAGE (identical arg surface to arm_chaos.py + sweep knobs):
#   gem5.opt --outdir=<dir> configs/se/kp920_proxy.py --cmd=<bin> --cpu O3 \
#       [--chaos_phys --phys_mode arch_frontend --phys_target_arch 3 ...] \
#       [--rob 128 --phys_int 160 --phys_float 192 --lq 48 --sq 42]
#
# HONEST E3 LIMITATIONS (design doc §1.1, §4.3) — do NOT treat as cycle-accurate:
#   1. gem5 v25 O3 uses a UNIFIED instruction queue (instQueues: vector<IQUnit>);
#      V110 has DISTRIBUTED four schedulers (~33 entries each). There is NO scalar
#      numIQEntries param to set (the IQ is constructed from IQUnit sub-objects),
#      so the unified-IQ approximation stands. numIQEntries≈66 from the doc is a
#      modeling target, not a settable knob here — flagged E3.
#   2. No bufferless NoC / HCCS / partitioned L3 Tag-Data split (those are §14/§16/§17,
#      Ruby/CHI/Garnet, separate S4 system-level work).
#   3. classic cache hierarchy has no real ECC logic (protection-aware modeling is
#      §1.2, a separate S0 unit; this config passes protection_model as a no-op axis).
#   4. The default gem5 ArmO3CPU FUPool (not a custom IntALU×3 + IntMultDiv×1 +
#      AGU×2 + FSU×2 port map) is used as the execution-port proxy — custom FUPool
#      is a separate larger patch.
# Absolute SDC rates from this config are E3 (proxy); trends across sweep axes are E2.

import argparse
import m5
from m5.objects import CHAOSReg, CHAOSPhysReg, CHAOSMem, CHAOSLSQFwd
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import FileResource
from gem5.simulate.simulator import Simulator

cpu_map = {"O3": CPUTypes.O3, "Timing": CPUTypes.TIMING,
           "Atomic": CPUTypes.ATOMIC, "Minor": CPUTypes.MINOR}

# ---- TaiShan V110 defaults (docs/kunpeng.md §3, design doc §1.1) ----
# These are the sweepable window axes (design doc §2.1 H2). CLI --rob etc. override.
V110 = {
    "fetch_width": 4, "decode_width": 4, "rename_width": 4,
    "issue_width": 4, "dispatch_width": 4, "commit_width": 4,
    "rob": 128,            # "moderate"; sweep {96,128,160}
    "phys_int": 160,       # third-party estimate ~128-160; sweep {128,160,192}
    "phys_float": 192,     # vector/FP, double FSU
    "lq": 48,              # deep LSQ (weak memory order); sweep {32,48,64}
    "sq": 42,
    "clk": "2.6GHz",
}

p = argparse.ArgumentParser()
p.add_argument("--cmd", required=True)
p.add_argument("--cpu", default="O3", choices=list(cpu_map))
p.add_argument("--maxinsts", type=int, default=0)
# --- V110 window sweep knobs (design doc §2.1 H2; default = V110) ---
p.add_argument("--rob", type=int, default=V110["rob"],
               help=f"numROBEntries (V110={V110['rob']}; sweep {{96,128,160}})")
p.add_argument("--phys_int", type=int, default=V110["phys_int"],
               help=f"numPhysIntRegs (V110={V110['phys_int']}; sweep {{128,160,192}})")
p.add_argument("--phys_float", type=int, default=V110["phys_float"],
               help=f"numPhysFloatRegs (V110={V110['phys_float']})")
p.add_argument("--lq", type=int, default=V110["lq"],
               help=f"LQEntries (V110={V110['lq']}; sweep {{32,48,64}})")
p.add_argument("--sq", type=int, default=V110["sq"],
               help=f"SQEntries (V110={V110['sq']})")
# --- CHAOS injector args (identical surface to arm_chaos.py) ---
p.add_argument("--chaos_reg", action="store_true")
p.add_argument("--probability", type=float, default=1.0)
p.add_argument("--rng_seed", type=lambda x: int(x, 0), default=20260825)
p.add_argument("--first_clock", type=lambda x: int(x, 0), default=1000)
p.add_argument("--last_clock", type=lambda x: int(x, 0), default=0)
p.add_argument("--max_faults", type=lambda x: int(x, 0), default=1)
p.add_argument("--max_reg_idx", type=lambda x: int(x, 0), default=31)
p.add_argument("--target_reg_idx", type=int, default=-1)
p.add_argument("--fault_type", default="bit_flip",
               choices=["bit_flip", "stuck_at_zero", "stuck_at_one", "random"])
p.add_argument("--fault_mask", type=lambda x: int(x, 0), default=0)
p.add_argument("--bits_to_change", type=int, default=1)
p.add_argument("--reg_class", default="integer",
               choices=["integer", "floating_point", "both"])
p.add_argument("--chaos_phys", action="store_true")
p.add_argument("--phys_mode", default="phys",
               choices=["phys", "arch_frontend", "arch_commit"])
p.add_argument("--phys_target_idx", type=int, default=-1)
p.add_argument("--phys_target_arch", type=int, default=0)
p.add_argument("--phys_reg_class", default="integer",
               choices=["integer", "floating_point", "vector", "both"])
p.add_argument("--vec_lane_width", type=int, default=32, choices=[8, 16, 32, 64])
p.add_argument("--vec_lane_offset", type=int, default=-1)
p.add_argument("--chaos_mem", action="store_true")
p.add_argument("--addr_start", type=lambda x: int(x, 0), default=0)
p.add_argument("--addr_end", type=lambda x: int(x, 0), default=0)
p.add_argument("--bit_flip_prob", type=float, default=0.9)
p.add_argument("--stuck_at_zero_prob", type=float, default=0.05)
p.add_argument("--stuck_at_one_prob", type=float, default=0.05)
p.add_argument("--chaos_lsqfwd", action="store_true")
p.add_argument("--lsq_byte_offset", type=int, default=-1)
args = p.parse_args()

# C2-KP cache geometry = V110: 64KiB L1 (4-way, 64B), 512KiB L2 (8-way, 64B).
# (Same as the C0 baseline — V110 actually matches the default geometry; the
# C2-KP differentiator is the O3 uarch params + 2.6GHz, NOT the cache sizes.)
cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="64KiB", l1i_size="64KiB", l2_size="512KiB",
)
memory = SingleChannelDDR3_1600("1GiB")
processor = SimpleProcessor(cpu_type=cpu_map[args.cpu], num_cores=1, isa=ISA.ARM)
core0 = processor.get_cores()[0]
cpu0 = core0.core  # the underlying BaseCPU SimObject

# ---- apply TaiShan V110 O3 microarchitecture params (the C2-KP point) ----
# Verified param names exist in build/ARM/params/BaseO3CPU.hh. Setting on the
# ArmO3CPU SimObject before m5.instantiate() is the standard gem5 pattern
# (cf. fi_research/probes/o3_chaos_smoke.py:68 on a bare ArmO3CPU).
if args.cpu == "O3":
    cpu0.fetchWidth = args.fetch_width if hasattr(args, "fetch_width") else V110["fetch_width"]
    cpu0.decodeWidth = V110["decode_width"]
    cpu0.renameWidth = V110["rename_width"]
    cpu0.issueWidth = V110["issue_width"]
    cpu0.dispatchWidth = V110["dispatch_width"]
    cpu0.commitWidth = V110["commit_width"]
    cpu0.numROBEntries = args.rob
    cpu0.numPhysIntRegs = args.phys_int
    cpu0.numPhysFloatRegs = args.phys_float
    cpu0.LQEntries = args.lq
    cpu0.SQEntries = args.sq
    print(f"[kp920_proxy] C2-KP V110 O3 params applied: "
          f"width=4-wide, ROB={args.rob}, physInt={args.phys_int}, "
          f"physFloat={args.phys_float}, LQ={args.lq}, SQ={args.sq} "
          f"(IQ unified-vector — E3, not V110 distributed four-scheduler)")

board = SimpleBoard(
    clk_freq=V110["clk"],   # 2.6GHz (V110 typical; doc §1.1)
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

board.set_se_binary_workload(binary=FileResource(args.cmd, override=True))

# CHAOS injector mount blocks — identical to arm_chaos.py (same 5 injectors,
# same arg mapping) so runner.py-style command lines work unchanged on C2-KP.
if args.chaos_reg:
    chaos = CHAOSReg(
        cpu=cpu0,
        probability=args.probability,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        maxRegIdx=args.max_reg_idx,
        targetRegIdx=args.target_reg_idx,
        faultType=args.fault_type,
        faultMask=args.fault_mask,
        bitsToChange=args.bits_to_change,
        regTargetClass=args.reg_class,
        writeLog=True,
    )
    board.chaos_reg = chaos

if args.chaos_phys:
    chaos_p = CHAOSPhysReg(
        cpu=cpu0,
        injectionMode=args.phys_mode,
        targetPhysRegIdx=args.phys_target_idx,
        targetArchRegIdx=args.phys_target_arch,
        regTargetClass=args.phys_reg_class,
        vecLaneWidth=args.vec_lane_width,
        vecLaneOffset=args.vec_lane_offset,
        probability=args.probability,
        bitsToChange=args.bits_to_change,
        faultMask=args.fault_mask,
        faultType=args.fault_type,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
    )
    board.chaos_phys = chaos_p

if args.chaos_mem:
    dram = memory.mem_ctrl[0].dram
    board.chaos_mem = CHAOSMem(
        mem=dram,
        probability=args.probability,
        firstClock=args.first_clock,
        lastClock=0,
        faultType=args.fault_type,
        faultMask="0",
        tickToClockRatio=1000,
        bitFlipProb=args.bit_flip_prob,
        stuckAtZeroProb=args.stuck_at_zero_prob,
        stuckAtOneProb=args.stuck_at_one_prob,
        addr_start=args.addr_start,
        addr_end=args.addr_end,
        rngSeed=args.rng_seed,
        maxFaults=args.max_faults,
        writeLog=True,
    )

if args.chaos_lsqfwd:
    lsq = CHAOSLSQFwd(
        cpu=cpu0,
        probability=args.probability,
        faultType=args.fault_type,
        faultMask=str(args.fault_mask),
        bitsToChange=args.bits_to_change,
        byteOffset=args.lsq_byte_offset,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
    )
    board.chaos_lsqfwd = lsq

if args.maxinsts:
    cpu0.max_insts = args.maxinsts

simulator = Simulator(board=board, full_system=False)
simulator.run()
