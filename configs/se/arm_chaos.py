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
from m5.objects import CHAOSReg, CHAOSPhysReg, CHAOSMem, CHAOSLSQFwd, CHAOSRenameMap, CHAOSFreeList, CHAOSROB, CHAOSIQ, CHAOSExec, CHAOSFPU, CHAOSL1DForward, CHAOSBPU, CHAOSAddrPath, CHAOSDecode, CHAOSExMon, CHAOSRAS
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
p.add_argument("--args", default="",
               help="space-separated argv passed to the SE binary (e.g. "
                    "'pure_fma' for method1_controls). Empty = no args.")
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
# §1.3/§2.1B F3 data-dependent trigger (method2 undervoltage) + semanticRole.
p.add_argument("--phys_trigger_mask", type=lambda x: int(x,0), default=0,
               help="F3: inject only when (val & mask) == pattern; 0 = off")
p.add_argument("--phys_trigger_pattern", type=lambda x: int(x,0), default=0,
               help="F3: the pattern the masked value must equal")
p.add_argument("--phys_semantic_role", default="",
               help="§2.1B: ABI role annotation for campaign stratification")
# CHAOSMem (backing-store byte injector; G4 fixed weights/boundary)
p.add_argument("--chaos_mem", action="store_true",
               help="attach CHAOSMem to the board DRAM")
p.add_argument("--addr_start", type=lambda x: int(x,0), default=0)
p.add_argument("--addr_end", type=lambda x: int(x,0), default=0)
p.add_argument("--bit_flip_prob", type=float, default=0.9)
p.add_argument("--stuck_at_zero_prob", type=float, default=0.05)
p.add_argument("--stuck_at_one_prob", type=float, default=0.05)
p.add_argument("--protection_model", default="none",
               choices=["none","secded","sed","secded_poison"],
               help="§1.2 protection-aware modeling layer (CHAOSMem uses "
                    "'secded' = Huawei DDR ECC; others accepted but treated "
                    "as raw for DRAM). 'none' (default = raw escape, zero "
                    "regression); 'secded' (1-bit undo=Corrected, 2-bit "
                    "poison-log=Latent E3, >=3 silent). Applied before "
                    "write-back so undo restores the byte.")
p.add_argument("--ecc_logic_fault", action="store_true",
               help="§2.17: corrupt the in-CHAOSMem SECDED syndrome (not the "
                    "data) -> mis-correction / missed-detection. Models "
                    "'ECC logic itself unreliable'. Default false = backing-byte injection.")
# CHAOSLSQFwd (store->load forwarding-path injector; O3 only). It
# SELF-ATTACHES: its constructor does `cpu->lsqFwd = this` (no python
# setLSQFwd call needed — that method has no python binding anyway).
# Just instantiate it with cpu=cpu0; lsq_unit.cc reaches it via cpu->lsqFwd.
p.add_argument("--chaos_lsqfwd", action="store_true",
               help="attach CHAOSLSQFwd (O3 store->load forwarding-path FI)")
p.add_argument("--lsq_byte_offset", type=int, default=-1,
               help="CHAOSLSQFwd directed byte offset within forwarded data")
# §2.4 CHAOSLSQFwd structured fault mode extension (byte_lane_skew/all_zero).
p.add_argument("--lsq_struct_mode", default="byte_flip",
               choices=["byte_flip","byte_lane_skew","all_zero"],
               help="§2.4 structured fault mode (byte_flip=orig | byte_lane_skew "
                    "(rol_k) | all_zero)")
p.add_argument("--lsq_lane_skew_k", type=int, default=1,
               help="§2.4 byte_lane_skew: rotate by k bytes")
# §2.2 CHAOSRenameMap (O3 rename-map fault injector). SELF-ATTACHES at
# startup() to thread-0 frontRenameMap.chaosRenameMap. map_bitflip /
# f5_substitute / f4_field_stuck modes (design doc §2.2).
p.add_argument("--chaos_rename", action="store_true",
               help="attach CHAOSRenameMap (O3 rename-map injector, §2.2)")
p.add_argument("--rename_mode", default="map_bitflip",
               choices=["map_bitflip","f5_substitute","f4_field_stuck","spec_leak"])
p.add_argument("--rename_target_arch", type=int, default=-1,
               help="arch reg index whose map entry to corrupt (-1=random 0..30)")
p.add_argument("--rename_first_clock", type=lambda x: int(x,0), default=100000)
p.add_argument("--rename_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--rename_fault_mask", type=lambda x: int(x,0), default=0)
p.add_argument("--rename_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.2 CHAOSFreeList (O3 freelist fault injector). SELF-ATTACHES at startup()
# to physFreeList().chaosFreeList. mark_free / pop_wrong modes (design doc §2.2).
p.add_argument("--chaos_freelist", action="store_true",
               help="attach CHAOSFreeList (O3 freelist injector, §2.2)")
p.add_argument("--freelist_mode", default="mark_free",
               choices=["mark_free","pop_wrong"])
p.add_argument("--freelist_first_clock", type=lambda x: int(x,0), default=100000)
p.add_argument("--freelist_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--freelist_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.3 CHAOSROB (O3 ROB fault injector). SELF-ATTACHES at startup() to
# cpu.rob.chaosROB. entry_bitflip / exc_suppress modes (§2.3).
p.add_argument("--chaos_rob", action="store_true",
               help="attach CHAOSROB (O3 ROB injector, §2.3)")
p.add_argument("--rob_mode", default="entry_bitflip",
               choices=["entry_bitflip","exc_suppress"])
p.add_argument("--rob_field", default="exc_status",
               choices=["result","done","exc_status","dest_phys","spec"])
p.add_argument("--rob_distance", type=int, default=0)
p.add_argument("--rob_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--rob_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--rob_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.5 CHAOSIQ (O3 instruction-queue injector). SELF-ATTACHES at startup()
# to IEW.instQueue.chaosIQ. wake_omit (F6) mode (§2.5).
p.add_argument("--chaos_iq", action="store_true",
               help="attach CHAOSIQ (O3 IQ injector, §2.5)")
p.add_argument("--iq_mode", default="wake_omit",
               choices=["wake_omit", "src_ready_bitflip", "wake_phase"])
p.add_argument("--iq_phase_offset", type=int, default=1,
               help="F6 wake_phase: delay cycles (positive only)")
p.add_argument("--iq_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--iq_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--iq_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.12 CHAOSExec (O3 integer execution-unit injector). SELF-ATTACHES at
# startup() to cpu.chaosExec. Hooks DynInst::execute() post-staticInst->execute;
# filters opClass IntAlu/IntMult/IntDiv; XORs integer result.
p.add_argument("--chaos_exec", action="store_true",
               help="attach CHAOSExec (O3 integer-exec injector, §2.12)")
p.add_argument("--exec_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--exec_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--exec_fault_mask", type=lambda x: int(x,0), default=0)
p.add_argument("--exec_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.6 CHAOSFPU (O3 FP/vector execution-unit injector). SELF-ATTACHES at
# startup() to cpu.chaosFPU. Hooks DynInst::execute() post-execute; filters
# opClass Float*/SimdFloat*; XORs FP result blob (IEEE754 sign/exp/mantissa).
p.add_argument("--chaos_fpu", action="store_true",
               help="attach CHAOSFPU (O3 FP/vector-exec injector, §2.6)")
p.add_argument("--fpu_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--fpu_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--fpu_fault_mask", type=lambda x: int(x,0), default=0)
p.add_argument("--fpu_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.7 CHAOSL1DForward (post-check escape injector). SELF-ATTACHES at startup()
# to cpu.chaosL1DFwd. Hooks LSQUnit::completeDataAccess before writeback;
# XORs the load response data (post-L1D, post-ECC) — the escape path.
p.add_argument("--chaos_l1dfwd", action="store_true",
               help="attach CHAOSL1DForward (O3 post-check-escape, §2.7)")
p.add_argument("--l1dfwd_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--l1dfwd_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--l1dfwd_fault_mask", type=lambda x: int(x,0), default=0)
p.add_argument("--l1dfwd_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.13 CHAOSBPU (O3 branch-prediction injector). SELF-ATTACHES at startup()
# to cpu.o3BAC().chaosBPU. Hooks BAC::predict post-bpu->predict; F5 flips
# direction (dir_flip) or PC target bit (target_flip).
p.add_argument("--chaos_bpu", action="store_true",
               help="attach CHAOSBPU (O3 branch-pred injector, §2.13)")
p.add_argument("--bpu_mode", default="dir_flip", choices=["dir_flip","target_flip"])
p.add_argument("--bpu_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--bpu_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--bpu_fault_mask", type=lambda x: int(x,0), default=0)
p.add_argument("--bpu_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.4 CHAOSAddrPath (AGU address-path injector). SELF-ATTACHES at startup()
# to cpu.chaosAddrPath. Hooks LSQ::sendFragmentToTranslation pre-translateTiming;
# byte7_zero / low_bit_flip. HONEST: SE-inert (byte7 zero lands in SE range).
p.add_argument("--chaos_addrpath", action="store_true",
               help="attach CHAOSAddrPath (O3 AGU address-path, §2.4, SE-inert)")
p.add_argument("--addrpath_mode", default="byte7_zero",
               choices=["byte7_zero","low_bit_flip"])
p.add_argument("--addrpath_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--addrpath_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--addrpath_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.14 CHAOSDecode (O3 decode-unit injector). SELF-ATTACHES at startup()
# to cpu.chaosDecode. Hooks rename.cc:1137 post-flattenedDestIdx; dest_reg_sub
# F5 (per-inst, safe — _flatDestIdx is per-DynInst, not shared staticInst).
p.add_argument("--chaos_decode", action="store_true",
               help="attach CHAOSDecode (O3 decode injector, §2.14)")
p.add_argument("--decode_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--decode_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--decode_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.4 CHAOSExMon (ARM exclusive-monitor injector). SELF-ATTACHES to cpu->isa[0].
# Hooks ISA::handleLockedWrite (STXR verdict); stxr_force_success/fail.
p.add_argument("--chaos_exmon", action="store_true",
               help="attach CHAOSExMon (ARM exclusive-monitor, §2.4)")
p.add_argument("--exmon_mode", default="stxr_force_success",
               choices=["stxr_force_success","stxr_force_fail"])
p.add_argument("--exmon_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--exmon_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--exmon_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.18 CHAOSRAS (O3 RAS-escape injector). SELF-ATTACHES at startup() to
# cpu.commit.chaosRAS. Hooks Commit::commitHead fault-check; exc_suppress.
p.add_argument("--chaos_ras", action="store_true",
               help="attach CHAOSRAS (O3 RAS-escape, §2.18)")
p.add_argument("--ras_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--ras_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--ras_rng_seed", type=lambda x: int(x,0), default=20260825)
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

board.set_se_binary_workload(
    binary=FileResource(args.cmd, override=True),
    arguments=args.args.split() if args.args else [],
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
        triggerValueMask=args.phys_trigger_mask,
        triggerValuePattern=args.phys_trigger_pattern,
        semanticRole=args.phys_semantic_role,
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
    # Frequency-correct cycles->ticks ratio (same fix as kp920_proxy.py):
    # firstClock is in CPU cycles; the old hardcoded tickToClockRatio=1000
    # assumed 1GHz. C0 is 2GHz -> period 500 ticks, so the old value opened
    # the window at 2x the requested cycle count. Compute from the board
    # clock exactly as gem5 rounds it (Tick=1ps, Decimal ROUND_HALF_UP —
    # m5/ticks.py:80). (clk_domain.clock.getValue() can't be used here: the
    # global frequency isn't fixed until m5.instantiate().)
    import decimal
    _ratio = int(decimal.Decimal((1.0 / 2e9) * 1e12)
                 .to_integral_value(decimal.ROUND_HALF_UP))
    print(f"[arm_chaos] CHAOSMem tickToClockRatio={_ratio} "
          f"(board 2GHz, was hardcoded 1000)")
    board.chaos_mem = CHAOSMem(
        mem=dram,
        probability=args.probability,
        firstClock=args.first_clock,
        lastClock=0,
        faultType=args.fault_type,
        # CHAOSMem parses faultMask as BINARY (std::stoi(..., 2)), so "0" means
        # random mask. Pass --fault_mask through as an 8-char binary string so
        # a directed bit (e.g. --fault_mask 0x40 = bit6) is honored (was
        # hardcoded "0" -> always random; fixed here). Empty/0 -> random.
        faultMask=(format(args.fault_mask, "08b") if args.fault_mask else "0"),
        tickToClockRatio=_ratio,
        bitFlipProb=args.bit_flip_prob,
        stuckAtZeroProb=args.stuck_at_zero_prob,
        stuckAtOneProb=args.stuck_at_one_prob,
        addr_start=args.addr_start,
        addr_end=args.addr_end,
        rngSeed=args.rng_seed,
        maxFaults=args.max_faults,
        protectionModel=args.protection_model,
        addrMapSub=args.addr_map_sub,
        eccLogicFault=args.ecc_logic_fault if hasattr(args,'ecc_logic_fault') else False,
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
        structMode=args.lsq_struct_mode,
        laneSkewK=args.lsq_lane_skew_k,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
    )
    board.chaos_lsqfwd = lsq

if args.chaos_rename:
    # §2.2 CHAOSRenameMap: O3-only. SELF-ATTACHES at startup() to thread-0
    # frontRenameMap().chaosRenameMap (the injector dynamic_casts to O3CPU
    # and sets the pointer; UnifiedRenameMap::setEntry calls maybeCorrupt).
    # Instantiate as a board child with cpu=cpu0 — no explicit attach call.
    ren = CHAOSRenameMap(
        cpu=cpu0,
        mode=args.rename_mode,
        targetArchReg=args.rename_target_arch,
        probability=args.probability,
        firstClock=args.rename_first_clock,
        maxFaults=args.rename_max_faults,
        faultMask=args.rename_fault_mask,
        rngSeed=args.rename_rng_seed,
        writeLog=True,
    )
    board.chaos_rename = ren

if args.chaos_freelist:
    # §2.2 CHAOSFreeList: O3-only. SELF-ATTACHES at startup() to
    # physFreeList().chaosFreeList (UnifiedFreeList::getReg calls maybeCorrupt).
    fl = CHAOSFreeList(
        cpu=cpu0,
        mode=args.freelist_mode,
        probability=args.probability,
        firstClock=args.freelist_first_clock,
        maxFaults=args.freelist_max_faults,
        rngSeed=args.freelist_rng_seed,
        writeLog=True,
    )
    board.chaos_freelist = fl

if args.chaos_rob:
    # §2.3 CHAOSROB: O3-only. SELF-ATTACHES at startup() to cpu.rob.chaosROB
    # (ROB::retireHead calls maybeCorrupt on the head inst pre-clearInROB).
    rob = CHAOSROB(
        cpu=cpu0,
        mode=args.rob_mode,
        field=args.rob_field,
        distanceFromHead=args.rob_distance,
        probability=args.probability,
        firstClock=args.rob_first_clock,
        maxFaults=args.rob_max_faults,
        rngSeed=args.rob_rng_seed,
        writeLog=True,
    )
    board.chaos_rob = rob

if args.chaos_iq:
    # §2.5 CHAOSIQ: O3-only. SELF-ATTACHES at startup() to
    # IEW.instQueue.chaosIQ (wakeDependents calls shouldOmitWake).
    iq = CHAOSIQ(
        cpu=cpu0,
        mode=args.iq_mode,
        phaseOffset=args.iq_phase_offset,
        probability=args.probability,
        firstClock=args.iq_first_clock,
        maxFaults=args.iq_max_faults,
        rngSeed=args.iq_rng_seed,
        writeLog=True,
    )
    board.chaos_iq = iq

if args.chaos_exec:
    # §2.12 CHAOSExec: O3-only. SELF-ATTACHES at startup() to cpu.chaosExec
    # (DynInst::execute() calls maybeCorrupt post-execute).
    ex = CHAOSExec(
        cpu=cpu0,
        probability=args.probability,
        firstClock=args.exec_first_clock,
        maxFaults=args.exec_max_faults,
        faultMask=args.exec_fault_mask,
        rngSeed=args.exec_rng_seed,
        writeLog=True,
    )
    board.chaos_exec = ex

if args.chaos_fpu:
    # §2.6 CHAOSFPU: O3-only. SELF-ATTACHES at startup() to cpu.chaosFPU.
    fpu = CHAOSFPU(
        cpu=cpu0,
        probability=args.probability,
        firstClock=args.fpu_first_clock,
        maxFaults=args.fpu_max_faults,
        faultMask=args.fpu_fault_mask,
        rngSeed=args.fpu_rng_seed,
        writeLog=True,
    )
    board.chaos_fpu = fpu

if args.chaos_l1dfwd:
    # §2.7 CHAOSL1DForward: O3-only. SELF-ATTACHES at startup() to
    # cpu.chaosL1DFwd (completeDataAccess calls maybeCorrupt pre-writeback).
    l1df = CHAOSL1DForward(
        cpu=cpu0,
        probability=args.probability,
        firstClock=args.l1dfwd_first_clock,
        maxFaults=args.l1dfwd_max_faults,
        faultMask=args.l1dfwd_fault_mask,
        rngSeed=args.l1dfwd_rng_seed,
        writeLog=True,
    )
    board.chaos_l1dfwd = l1df

if args.chaos_bpu:
    # §2.13 CHAOSBPU: O3-only. SELF-ATTACHES at startup() to cpu.o3BAC().
    # chaosBPU (BAC::predict calls maybeCorrupt post-predict).
    bpu = CHAOSBPU(
        cpu=cpu0,
        mode=args.bpu_mode,
        probability=args.probability,
        firstClock=args.bpu_first_clock,
        maxFaults=args.bpu_max_faults,
        faultMask=args.bpu_fault_mask,
        rngSeed=args.bpu_rng_seed,
        writeLog=True,
    )
    board.chaos_bpu = bpu

if args.chaos_addrpath:
    # §2.4 CHAOSAddrPath: O3-only. SELF-ATTACHES at startup() to
    # cpu.chaosAddrPath (sendFragmentToTranslation calls maybeCorrupt).
    ap = CHAOSAddrPath(
        cpu=cpu0,
        mode=args.addrpath_mode,
        probability=args.probability,
        firstClock=args.addrpath_first_clock,
        maxFaults=args.addrpath_max_faults,
        rngSeed=args.addrpath_rng_seed,
        writeLog=True,
    )
    board.chaos_addrpath = ap

if args.chaos_decode:
    # §2.14 CHAOSDecode: O3-only. SELF-ATTACHES at startup() to
    # cpu.chaosDecode (rename.cc:1137 calls maybeCorrupt post-flatten).
    dc = CHAOSDecode(
        cpu=cpu0,
        mode="dest_reg_sub",
        probability=args.probability,
        firstClock=args.decode_first_clock,
        maxFaults=args.decode_max_faults,
        rngSeed=args.decode_rng_seed,
        writeLog=True,
    )
    board.chaos_decode = dc

if args.chaos_exmon:
    # §2.4 CHAOSExMon: ARM-only. SELF-ATTACHES to cpu0.isa[0].chaosExMon
    # (ISA::handleLockedWrite calls maybeCorrupt on the STXR verdict).
    ex = CHAOSExMon(
        isa=cpu0.isa[0],
        cpu=cpu0,
        mode=args.exmon_mode,
        probability=args.probability,
        firstClock=args.exmon_first_clock,
        maxFaults=args.exmon_max_faults,
        rngSeed=args.exmon_rng_seed,
        writeLog=True,
    )
    board.chaos_exmon = ex

if args.chaos_ras:
    # §2.18 CHAOSRAS: O3-only. SELF-ATTACHES at startup() to
    # cpu.commit.chaosRAS (commitHead calls maybeCorrupt at fault-check).
    ras = CHAOSRAS(
        cpu=cpu0,
        mode="exc_suppress",
        probability=args.probability,
        firstClock=args.ras_first_clock,
        maxFaults=args.ras_max_faults,
        rngSeed=args.ras_rng_seed,
        writeLog=True,
    )
    board.chaos_ras = ras

if args.maxinsts:
    cpu0.max_insts = args.maxinsts

simulator = Simulator(board=board, full_system=False)
simulator.run()
