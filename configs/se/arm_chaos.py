# arm_chaos.py — minimal SE config for AArch64 CHAOS fault injection.
#
# Uses the gem5 v25 stdlib (SimpleBoard + PrivateL1PrivateL2CacheHierarchy) for a
# SUPPORTED ARM SE path (ARM release/ISA/TLB wired correctly), then attaches
# CHAOS SimObjects explicitly. This is the baseline harness for the ARM64 SDC
# study (plan docs/arm64-fi-plan-based-on-CHAOS.md). NOT a formal campaign
# runner — that comes with the manifest runner (Patch 9).
#
# Usage:
#   gem5.opt --outdir=<dir> arm_chaos.py --cmd=<bin> [--cpu=O3|Timing|Atomic]
#            [--maxinsts=N] [--chaos_reg ...]
#
# HONESTY NOTE: CHAOSReg injects ARCHITECTURAL state (ThreadContext). On O3
# out-of-order this does NOT reach in-flight instructions reliably (commit vs
# frontend rename-map split). Valid O3 SDC requires CHAOSPhysReg (Patch 0b).
# This baseline CHAOSReg path is reported as architectural-state only.

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

p = argparse.ArgumentParser()
p.add_argument("--cmd", required=True)
p.add_argument("--cpu", default="O3", choices=list(cpu_map))
p.add_argument("--maxinsts", type=int, default=0)
# CHAOSReg params (architectural-state; honest about limits)
p.add_argument("--chaos_reg", action="store_true")
p.add_argument("--probability", type=float, default=1.0)
p.add_argument("--rng_seed", type=lambda x: int(x,0), default=20260825)
p.add_argument("--first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--last_clock", type=lambda x: int(x,0), default=0)
p.add_argument("--max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--max_reg_idx", type=lambda x: int(x,0), default=31)
p.add_argument("--fault_type", default="bit_flip",
               choices=["bit_flip","stuck_at_zero","stuck_at_one","random"])
p.add_argument("--fault_mask", type=lambda x: int(x,0), default=0)
p.add_argument("--bits_to_change", type=int, default=1)
p.add_argument("--reg_class", default="integer",
               choices=["integer","floating_point","both"])
# CHAOSPhysReg (physical-register-file; valid O3 SDC, ITC'23/GeFIN-style)
p.add_argument("--chaos_phys", action="store_true",
               help="attach CHAOSPhysReg (O3 physical-register-file injector)")
p.add_argument("--phys_mode", default="phys",
               choices=["phys","arch_frontend","arch_commit"])
p.add_argument("--phys_target_idx", type=int, default=-1,
               help="phys reg index (phys mode); -1=random")
p.add_argument("--phys_target_arch", type=int, default=0,
               help="arch reg idx (arch_frontend/arch_commit modes)")
p.add_argument("--phys_reg_class", default="integer",
               choices=["integer","floating_point","vector","both"],
               help="CHAOSPhysReg target class. 'vector' targets VecRegClass "
                    "(now safe: buffer sized to actual vec width via "
                    "vecRegBytes(), fixes the 192B stack overflow).")
# CHAOSMem (backing-store byte injector; G4 fixed weights/boundary)
p.add_argument("--chaos_mem", action="store_true",
               help="attach CHAOSMem to the board DRAM")
p.add_argument("--addr_start", type=lambda x: int(x,0), default=0)
p.add_argument("--addr_end", type=lambda x: int(x,0), default=0)
p.add_argument("--bit_flip_prob", type=float, default=0.9)
p.add_argument("--stuck_at_zero_prob", type=float, default=0.05)
p.add_argument("--stuck_at_one_prob", type=float, default=0.05)
# CHAOSLSQFwd (store->load forwarding-path injector; O3 only). It
# SELF-ATTACHES: its constructor does `cpu->lsqFwd = this` (no python
# setLSQFwd call needed — that method has no python binding anyway).
# Just instantiate it with cpu=cpu0; lsq_unit.cc reaches it via cpu->lsqFwd.
p.add_argument("--chaos_lsqfwd", action="store_true",
               help="attach CHAOSLSQFwd (O3 store->load forwarding-path FI)")
p.add_argument("--lsq_byte_offset", type=int, default=-1,
               help="CHAOSLSQFwd directed byte offset within forwarded data")
args = p.parse_args()

cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="64KiB", l1i_size="64KiB", l2_size="512KiB",
)
memory = SingleChannelDDR3_1600("1GiB")
processor = SimpleProcessor(cpu_type=cpu_map[args.cpu], num_cores=1, isa=ISA.ARM)
core0 = processor.get_cores()[0]
cpu0 = core0.core  # the underlying BaseCPU SimObject

board = SimpleBoard(
    clk_freq="2GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

board.set_se_binary_workload(binary=FileResource(args.cmd, override=True))

# CHAOSReg attachment (architectural-state; honest per plan §2.2 — NOT PRF).
if args.chaos_reg:
    chaos = CHAOSReg(
        cpu=cpu0,
        probability=args.probability,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        maxRegIdx=args.max_reg_idx,
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
    # G4: attach CHAOSMem to the DRAM AbstractMemory. The stdlib
    # SingleChannelDDR3_1600 exposes its dram interface via mem_ctrl[0].dram
    # (DRAMInterface is an AbstractMemory subclass, so access()/getAddrRange()
    # are available). This is backing-store byte injection only — NOT a
    # timing DRAM/controller/ECC path (per plan §2.2).
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
    # Phase 2 §六.4 item 2 (LSQ store->load forwarding): CHAOSLSQFwd is
    # O3-only and SELF-ATTACHES — its constructor sets `cpu->lsqFwd = this`
    # (CHAOSLSQFwd.cc:50), so lsq_unit.cc's forward-path call site
    # (lsq_unit.cc:1498, `if (cpu->lsqFwd) cpu->lsqFwd->corrupt(...)`)
    # reaches it. No python setLSQFwd call (that method has no python
    # binding; the self-attach is the intended mechanism). Instantiating
    # the SimObject as a board child is enough.
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
