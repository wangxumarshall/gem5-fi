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
import shlex
import m5
from m5.objects import CHAOSReg, CHAOSPhysReg, CHAOSMem, CHAOSExMon, CHAOSLSQFwd, CHAOSAddrPath, CHAOSRenameMap, CHAOSFreeList, CHAOSROB, CHAOSIQ, CHAOSExec, CHAOSFPU, CHAOSL1DForward, CHAOSBPU
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
# Workload argv (space-separated; parsed with shlex). Passed through
# set_se_binary_workload(arguments=...) — needed for kernels with variants
# (e.g. cholesky_numeric "<iters> both", accum_kernel "<iters> both").
p.add_argument("--workload_args", default="",
               help="space-separated argv for the SE workload binary")
# C2-KP: TaiShan V110 4-wide OoO proxy params (plan §4.1, E3 — NOT cycle-exact).
# When set, overrides the DerivO3CPU defaults with V110-informed values.
p.add_argument("--kp920_proxy", action="store_true",
               help="Apply TaiShan V110 O3 proxy params (E3): 4-wide, ROB=128, "
                    "PhysIntRegs=160, PhysFloatRegs=192, LQ=48, SQ=42, IQ=66, "
                    "2.6GHz. NOT cycle-exact (no distributed scheduler / no "
                    "partition L3 / no bufferless NoC).")
p.add_argument("--clk_freq", default="2GHz",
               help="Board clock (kp920_proxy default 2.6GHz).")
p.add_argument("--rob_entries", type=int, default=0,
               help="H2 window sweep: O3 ROB entries (0 = leave gem5 default)")
p.add_argument("--phys_int_regs", type=int, default=0,
               help="H2 window sweep: physical int regs (0 = leave gem5 default)")
p.add_argument("--phys_float_regs", type=int, default=192)
p.add_argument("--lq_entries", type=int, default=0,
               help="H2 window sweep: LQ entries (0 = leave gem5 default)")
p.add_argument("--sq_entries", type=int, default=0,
               help="H2 window sweep: SQ entries (0 = leave gem5 default)")
p.add_argument("--iq_entries", type=int, default=66)
# CHAOSReg params (architectural-state; honest about limits)
p.add_argument("--chaos_reg", action="store_true")
p.add_argument("--probability", type=float, default=1.0)
p.add_argument("--rng_seed", type=lambda x: int(x,0), default=20260825)
p.add_argument("--first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--last_clock", type=lambda x: int(x,0), default=0)
p.add_argument("--max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--max_reg_idx", type=lambda x: int(x,0), default=31)
p.add_argument("--target_reg_idx", type=int, default=-1,
               help="directed architectural reg index (manifest target.index); "
                    "-1 = random sample within [0, max_reg_idx)")
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
p.add_argument("--vec_lane_width", type=int, default=32,
               choices=[8,16,32,64],
               help="Phase2 NEON: vec lane width in BITS (8/16/32/64). Default "
                    "32 = the 4x32-bit ASIMD lane granularity. Used with "
                    "--phys_reg_class=vector to stratify per-lane SDC.")
p.add_argument("--vec_lane_offset", type=int, default=-1,
               help="Phase2 NEON: which lane (0-indexed) to corrupt in the "
                    "VecRegClass phys reg. -1 = random lane (default).")
# S1-1: F3 data-dependent trigger (method2 under-voltage) + semanticRole.
p.add_argument("--phys_trigger_mask", type=lambda x: int(x,0), default=0,
               help="CHAOSPhysReg F3 trigger mask (0=F3 disabled/unconditional). "
                    "When nonzero, inject only if (target_val & mask) == "
                    "--phys_trigger_pattern. Models method2 under-voltage "
                    "setup-time violation on a specific bit pattern.")
p.add_argument("--phys_trigger_pattern", type=lambda x: int(x,0), default=0,
               help="CHAOSPhysReg F3 trigger pattern: inject only when "
                    "(target_val & --phys_trigger_mask) == this. hex ok.")
p.add_argument("--phys_semantic_role", default="",
               help="ABI role label for campaign heatmap stratification "
                    "(arg_return/temp/callee_saved/fp_lr/pointer). Metadata only.")
# CHAOSMem (backing-store byte injector; G4 fixed weights/boundary)
p.add_argument("--chaos_exmon", action="store_true",
               help="S3-7: exclusive-monitor (LL/SC reservation) injector "
                    "on the DRAM AbstractMemory's lockedAddrList")
p.add_argument("--exmon_mode", default="stale_reservation",
               choices=["clear_reservation", "stale_reservation"])
p.add_argument("--chaos_mem", action="store_true",
               help="attach CHAOSMem to the board DRAM")
p.add_argument("--addr_start", type=lambda x: int(x,0), default=0)
p.add_argument("--addr_end", type=lambda x: int(x,0), default=0)
p.add_argument("--mem_addr_mode", default="fixed", choices=["fixed","addr_map_sub"])
p.add_argument("--mem_addr_xor", type=lambda x: int(x,0), default=0)
p.add_argument("--mem_protection_model", default="none", choices=["none","secded"])
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
p.add_argument("--lsq_mask_width", type=int, default=1,
               help="CHAOSLSQFwd 64-bit mask covers this many consecutive "
                    "bytes (little-endian), [1,8]. 1=legacy single-byte; "
                    "2/4/8=multi-byte for method2 cross-byte spectra (D2 fix).")
# S1-5 CHAOSLSQFwd structuralFault (P-D1, core 179 D1 signature).
p.add_argument("--lsq_structural_fault", default="none",
               choices=["none","byte_lane_skew","all_zero"],
               help="CHAOSLSQFwd whole-word structural fault (P-D1). "
                    "byte_lane_skew: right-rotate delivered bytes by "
                    "--lsq_skew_bytes (core179 D1 rol1/rol6, bit-exact). "
                    "all_zero: deliver all-zero word (empty-slot signature). "
                    "Takes precedence over faultType when != none.")
p.add_argument("--lsq_skew_bytes", type=int, default=0,
               help="byte_lane_skew right-rotation amount (1..7). 0=random.")
# S6-1/S6-2: source-substitution faults (forward-source F5 + stale line).
p.add_argument("--lsq_source_fault", default="none",
               choices=["none","fwd_source_sub","stale_line_replay","phase_offset"],
               help="CHAOSLSQFwd source substitution (BEFORE memcpy). "
                    "fwd_source_sub: stale buffer as source (wrong-store F5). "
                    "stale_line_replay: stale fill-buffer line. "
                    "phase_offset: F6, history N steps back (timing-phase race).")
p.add_argument("--lsq_phase_offset", type=int, default=1,
               help="F6 phase offset N (history depth 1..8). Used with "
                    "source_fault=phase_offset: return history N steps back, "
                    "modeling method3 timing-phase race (100%->10-20%).")
# CHAOSAddrPath (P-D2): address-path FI. FS-only for observable effect.
p.add_argument("--chaos_addrpath", action="store_true",
               help="attach CHAOSAddrPath (P-D2 address-path FI; FS required "
                    "for observable effect, SE short-circuits).")
p.add_argument("--addrpath_probability", type=float, default=0.0,
               help="CHAOSAddrPath per-load probability of zeroing an addr byte.")
p.add_argument("--addrpath_byte_offset", type=int, default=7,
               help="Which addr byte to zero (7=MSB bits56..63, reproduces "
                    "core179 D2; -1=random 0..7). FS required for fault.")
# S1-2 CHAOSRenameMap (RAT): method1 history residue F5 substitute.
p.add_argument("--chaos_rat", action="store_true",
               help="attach CHAOSRenameMap (RAT F5-substitute / map_bitflip / "
                    "f4_field_stuck; reproduces method1 history residue).")
p.add_argument("--rat_mode", default="f5_substitute",
               choices=["map_bitflip","f5_substitute","f4_field_stuck"],
               help="CHAOSRenameMap fault mode.")
p.add_argument("--rat_target_arch", type=int, default=-1,
               help="Target arch reg index (-1=random; method1=callee_saved).")
p.add_argument("--rat_fault_mask", type=lambda x: int(x,0), default=0,
               help="CHAOSRenameMap map_bitflip mask (0=random one bit).")
p.add_argument("--rat_semantic_role", default="",
               help="ABI role label (callee_saved/accum/fp_accum). Metadata.")
p.add_argument("--rat_reg_class", default="integer",
               choices=["integer","floating_point","vector"],
               help="CHAOSRenameMap register class. AArch64 FP/SIMD (d0 etc.) "
                    "lives in VecRegClass -> use 'vector' (ARM has no "
                    "separate FloatRegClass; regs/vec.hh).")
# S1-3 CHAOSFreeList (freelist): method1 live-reg-marked-free residue.
p.add_argument("--chaos_freelist", action="store_true",
               help="attach CHAOSFreeList (mark_free/pop_wrong; method1 "
                    "live-physReg-marked-free residue).")
p.add_argument("--freelist_mode", default="mark_free",
               choices=["mark_free","pop_wrong"],
               help="CHAOSFreeList fault mode.")
p.add_argument("--freelist_target_phys", type=int, default=-1,
               help="Target physReg index (-1=scan RAT for a live one).")
p.add_argument("--freelist_semantic_role", default="",
               help="ABI role label. Metadata only.")
# S1-4 CHAOSROB: exc_suppress (DUE->SDC) / entry_bitflip (seqNum) / spec_leak.
p.add_argument("--chaos_rob", action="store_true",
               help="attach CHAOSROB (exc_suppress/entry_bitflip/spec_leak; "
                    "method1 spec-leak + exception-bit silencing).")
p.add_argument("--rob_mode", default="entry_bitflip",
               choices=["entry_bitflip","exc_suppress","spec_leak"],
               help="CHAOSROB fault mode.")
p.add_argument("--rob_fault_mask", type=lambda x: int(x,0), default=0,
               help="CHAOSROB entry_bitflip seqNum mask (0=random bit).")
p.add_argument("--rob_semantic_role", default="",
               help="ABI role label. Metadata only.")
# S8-1 CHAOSIQ: src_ready_bitflip / tag_sub (F5) / wake_phase (F6 deferred).
p.add_argument("--chaos_iq", action="store_true",
               help="attach CHAOSIQ (src_ready_bitflip/tag_sub; method3 IQ race).")
p.add_argument("--iq_mode", default="src_ready_bitflip",
               choices=["src_ready_bitflip","tag_sub","wake_phase","wake_omit"])
p.add_argument("--iq_target_src", type=int, default=-1)
p.add_argument("--iq_semantic_role", default="")
# S8-3 CHAOSExec: int ALU writeback result corruption (negative control).
p.add_argument("--chaos_exec", action="store_true",
               help="attach CHAOSExec (int writeback result flip; negative control P_SDC(Int)<<P_SDC(FSU)).")
p.add_argument("--exec_fault_mask", type=lambda x: int(x,0), default=0)
p.add_argument("--exec_bit_segment", default="all", choices=["all","low","mid","high"])
p.add_argument("--exec_semantic_role", default="")
# S8-2 CHAOSFPU: FP writeback result corruption (IEEE754 bit spectrum).
p.add_argument("--chaos_fpu", action="store_true",
               help="attach CHAOSFPU (FP writeback result flip; method3 mantissa/sign spectrum).")
p.add_argument("--fpu_fault_mask", type=lambda x: int(x,0), default=0)
p.add_argument("--fpu_bit_segment", default="all", choices=["all","sign","exp","mantissa"])
p.add_argument("--fpu_semantic_role", default="")
# S8-4 CHAOSL1DForward: post-check escape (PCE) load result corruption.
p.add_argument("--chaos_l1dfwd", action="store_true",
               help="attach CHAOSL1DForward (PCE; load result post-ECC flip).")
p.add_argument("--l1dfwd_fault_mask", type=lambda x: int(x,0), default=0)
p.add_argument("--l1dfwd_semantic_role", default="")
# S8-4 CHAOSBPU: branch-predictor target_sub (F5) / direction_flip (F1).
p.add_argument("--chaos_bpu", action="store_true",
               help="attach CHAOSBPU (BAC::predict target sub; negative-control "
                    "surface — wrong spec stream should squash).")
p.add_argument("--bpu_mode", default="target_sub",
               choices=["target_sub","direction_flip"])
p.add_argument("--bpu_semantic_role", default="")
args = p.parse_args()

cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="64KiB", l1i_size="64KiB", l2_size="512KiB",
)
memory = SingleChannelDDR3_1600("1GiB")
processor = SimpleProcessor(cpu_type=cpu_map[args.cpu], num_cores=1, isa=ISA.ARM)
core0 = processor.get_cores()[0]
cpu0 = core0.core  # the underlying BaseCPU SimObject

# C2-KP: TaiShan V110 4-wide OoO proxy (plan §4.1, E3 — NOT cycle-exact).
# Override DerivO3CPU defaults with V110-informed values. Honest: gem5 unified
# IQ ≠ V110 distributed quad-scheduler; classic cache ≠ partition L3 Tag/Data
# split; no bufferless NoC. Only applied when --kp920_proxy (else defaults).
if args.kp920_proxy and args.cpu == "O3":
    cpu0.numROBEntries = args.rob_entries or 128
    cpu0.numPhysIntRegs = args.phys_int_regs or 160
    cpu0.numPhysFloatRegs = args.phys_float_regs
    cpu0.numPhysVecRegs = args.phys_float_regs  # ASIMD 128b, no SVE
    cpu0.LQEntries = args.lq_entries or 48
    cpu0.SQEntries = args.sq_entries or 42
    # NOTE: numIQEntries is NOT a Python-settable O3 param (gem5's unified IQ
    # size is ROB-derived, unlike V110's distributed quad-scheduler). The
    # plan §4.1 numIQEntries=66 is a modeling target, not a knob here.
    # 4-wide front-end (V110 is 4-issue)
    cpu0.fetchWidth = 4
    cpu0.decodeWidth = 4
    cpu0.renameWidth = 4
    cpu0.issueWidth = 4
    cpu0.dispatchWidth = 4
    cpu0.commitWidth = 4

# H2 window sweep (plan §5.1C): explicit --rob_entries/--phys_int_regs/etc.
# override the O3 defaults EVEN WITHOUT --kp920_proxy (the sweep isolates one
# window axis; kp920_proxy bundles all V110 params together). Applied after
# (and independent of) the kp920 block above.
if args.cpu == "O3":
    if args.rob_entries:
        cpu0.numROBEntries = args.rob_entries
    if args.phys_int_regs:
        cpu0.numPhysIntRegs = args.phys_int_regs
    if args.lq_entries:
        cpu0.LQEntries = args.lq_entries
    if args.sq_entries:
        cpu0.SQEntries = args.sq_entries

clk = "2.6GHz" if args.kp920_proxy else args.clk_freq

board = SimpleBoard(
    clk_freq=clk,
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

board.set_se_binary_workload(
    binary=FileResource(args.cmd, override=True),
    arguments=shlex.split(args.workload_args) if args.workload_args else [],
)

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
        triggerValueMask=args.phys_trigger_mask,
        triggerValuePattern=args.phys_trigger_pattern,
        semanticRole=args.phys_semantic_role,
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
        bitsToChange=args.bits_to_change,
        tickToClockRatio=1000,
        bitFlipProb=args.bit_flip_prob,
        stuckAtZeroProb=args.stuck_at_zero_prob,
        stuckAtOneProb=args.stuck_at_one_prob,
        addr_start=args.addr_start,
        addr_end=args.addr_end,
        rngSeed=args.rng_seed,
        addrMode=args.mem_addr_mode,
        addrXorMask=args.mem_addr_xor,
        protectionModel=args.mem_protection_model,
        maxFaults=args.max_faults,
        writeLog=True,
    )

if args.chaos_exmon:
    # S3-7 (plan §5.4B): exclusive-monitor injector. Attaches via the
    # namespace-level chaos_exmon_g pointer; CacheBlk's inline LLSC methods
    # (trackLoadLocked/checkWrite) call it. LDXR/STXR kernel: fwd_7case_ldxr.
    board.chaos_exmon = CHAOSExMon(
        probability=args.probability,
        mode=args.exmon_mode,
        firstClock=args.first_clock,
        lastClock=0,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
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
        maskWidth=args.lsq_mask_width,
        structuralFault=args.lsq_structural_fault,
        skewBytes=args.lsq_skew_bytes,
        sourceFault=args.lsq_source_fault,
        phaseOffset=args.lsq_phase_offset,
        bitsToChange=args.bits_to_change,
        byteOffset=args.lsq_byte_offset,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
    )
    board.chaos_lsqfwd = lsq

# CHAOSAddrPath (P-D2): address-path FI. SELF-ATTACHES (ctor sets
# cpu->addrPath = this). FS MODE REQUIRED for observable effect — SE uses
# translateMmuOff (identity map, byte7-zeroed vaddr still lands in phys mem,
# no fault). Here for SE it instantiates (validates the SimObject + hook
# wiring) but produces no observable corruption; use arm_chaos_fs.py for FS.
if args.chaos_addrpath:
    ap = CHAOSAddrPath(
        cpu=cpu0,
        probability=args.addrpath_probability,
        byteOffset=args.addrpath_byte_offset,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
    )
    board.chaos_addrpath = ap

# CHAOSRenameMap (S1-2, RAT): method1 history residue. Holds a cpu pointer
# (no self-attach — RAT isn't a SimObject; drives faults from attackEvent,
# same pattern as CHAOSPhysReg). O3-only.
if args.chaos_rat:
    rat = CHAOSRenameMap(
        cpu=cpu0,
        probability=args.probability,
        mode=args.rat_mode,
        targetArchReg=args.rat_target_arch,
        regTargetClass=args.rat_reg_class,
        faultMask=args.rat_fault_mask,
        bitsToChange=args.bits_to_change,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
        semanticRole=args.rat_semantic_role,
    )
    board.chaos_rat = rat

# CHAOSFreeList (S1-3, freelist): method1 live-reg-marked-free residue.
# Self-driven attackEvent (freelist not a SimObject). O3-only.
if args.chaos_freelist:
    fl = CHAOSFreeList(
        cpu=cpu0,
        probability=args.probability,
        mode=args.freelist_mode,
        targetPhysReg=args.freelist_target_phys,
        regTargetClass=args.reg_class,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
        semanticRole=args.freelist_semantic_role,
    )
    board.chaos_freelist = fl

# CHAOSROB (S1-4): exc_suppress (DUE->SDC) / entry_bitflip (seqNum) /
# spec_leak (deferred). Self-driven attackEvent (ROB not a SimObject).
if args.chaos_rob:
    rob = CHAOSROB(
        cpu=cpu0,
        probability=args.probability,
        mode=args.rob_mode,
        faultMask=args.rob_fault_mask,
        bitsToChange=args.bits_to_change,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
        semanticRole=args.rob_semantic_role,
    )
    board.chaos_rob = rob

# CHAOSIQ (S8-1): src_ready_bitflip / tag_sub. Self-driven attackEvent.
if args.chaos_iq:
    iq = CHAOSIQ(
        cpu=cpu0,
        probability=args.probability,
        mode=args.iq_mode,
        targetSrcIdx=args.iq_target_src,
        bitsToChange=args.bits_to_change,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
        semanticRole=args.iq_semantic_role,
    )
    board.chaos_iq = iq

# CHAOSExec (S8-3): int writeback result corruption.
if args.chaos_exec:
    ex = CHAOSExec(
        cpu=cpu0,
        probability=args.probability,
        faultMask=args.exec_fault_mask,
        bitsToChange=args.bits_to_change,
        bitSegment=args.exec_bit_segment,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
        semanticRole=args.exec_semantic_role,
    )
    board.chaos_exec = ex

# CHAOSFPU (S8-2): FP writeback result corruption.
if args.chaos_fpu:
    fp = CHAOSFPU(
        cpu=cpu0,
        probability=args.probability,
        faultMask=args.fpu_fault_mask,
        bitsToChange=args.bits_to_change,
        bitSegment=args.fpu_bit_segment,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
        semanticRole=args.fpu_semantic_role,
    )
    board.chaos_fpu = fp

# CHAOSL1DForward (S8-4 PCE): load result post-ECC corruption.
if args.chaos_l1dfwd:
    l1d = CHAOSL1DForward(
        cpu=cpu0,
        probability=args.probability,
        faultMask=args.l1dfwd_fault_mask,
        bitsToChange=args.bits_to_change,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
        semanticRole=args.l1dfwd_semantic_role,
    )
    board.chaos_l1dfwd = l1d

# CHAOSBPU (S8-4): BAC::predict target substitution. HONEST LIMITATION:
# BAC::predict is only called in the DECOUPLED front-end mode
# (decoupledFrontEnd defaults False; the coupled path queries the BPU
# directly from Fetch). Enabling decoupledFrontEnd on this stdlib board
# was tested and does NOT boot (empty stats — the v25 experimental
# decoupled FE is incompatible with SimpleBoard). The hook stays wired
# for decoupled-compatible configs; wiring it to the Fetch coupled path
# is future work.
if args.chaos_bpu:
    bpu = CHAOSBPU(
        cpu=cpu0,
        probability=args.probability,
        mode=args.bpu_mode,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
        semanticRole=args.bpu_semantic_role,
    )
    board.chaos_bpu = bpu

if args.maxinsts:
    cpu0.max_insts = args.maxinsts

simulator = Simulator(board=board, full_system=False)
simulator.run()
