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
# §1.2 protection-aware modeling (CHAOSMem's protectionModel; DRAM = secded
# per Huawei DDR ECC proxy). Same surface as arm_chaos.py — runner.py passes
# it on the memory route.
p.add_argument("--protection_model", default="none",
               help="§1.2 protection-aware layer for CHAOSMem (none|secded)")
p.add_argument("--addr_start", type=lambda x: int(x, 0), default=0)
p.add_argument("--addr_end", type=lambda x: int(x, 0), default=0)
p.add_argument("--bit_flip_prob", type=float, default=0.9)
p.add_argument("--stuck_at_zero_prob", type=float, default=0.05)
p.add_argument("--stuck_at_one_prob", type=float, default=0.05)
p.add_argument("--chaos_lsqfwd", action="store_true")
p.add_argument("--lsq_byte_offset", type=int, default=-1)
# §2.4 structured fault modes (synced from arm_chaos.py — these were MISSING
# here while the mount below read them, so any runner.py invocation passing
# --lsq_struct_mode crashed with argparse exit 2: the entire lsqfwd formal
# (384/384 reps) recorded exit=2 / faults_injected=0 and was mis-classified
# as Crash => the committed "§2.4 LSQFwd 100% DUE" result is INVALID).
p.add_argument("--lsq_struct_mode", default="byte_flip",
               choices=["byte_flip", "byte_lane_skew", "stale_line_replay",
                        "all_zero"])
p.add_argument("--lsq_lane_skew_k", type=int, default=1)
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
p.add_argument("--iq_mode", default="wake_omit", choices=["wake_omit"])
p.add_argument("--iq_phase_offset", type=int, default=0)
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
    # Frequency-correct cycles->ticks ratio (same fix as the 10-injector
    # inWindow batch fix): firstClock is in CPU cycles, but the old
    # hardcoded tickToClockRatio=1000 assumed 1GHz. On C2-KP 2.6GHz the
    # period is 385 ticks, so 50000 cycles * 1000 = 50M ticks > cholesky's
    # total 31.7M ticks -> the window NEVER opened -> mem_formal was 384/384
    # Inactive (n_valid=0, invalid campaign). Compute the ratio from the
    # V110 clock exactly as gem5 does (Tick=1ps, Decimal ROUND_HALF_UP —
    # m5/ticks.py:80): 2.6GHz -> 385 t/cyc. (Can't read
    # clk_domain.clock.getValue() here: the global frequency isn't fixed
    # until m5.instantiate().)
    import decimal
    _freq = float(V110["clk"].replace("GHz", "")) * 1e9
    _ratio = int(decimal.Decimal((1.0 / _freq) * 1e12)
                 .to_integral_value(decimal.ROUND_HALF_UP))
    print(f"[kp920_proxy] CHAOSMem tickToClockRatio={_ratio} "
          f"(CPU clock {V110['clk']}, was hardcoded 1000)")
    board.chaos_mem = CHAOSMem(
        mem=dram,
        probability=args.probability,
        firstClock=args.first_clock,
        lastClock=0,
        faultType=args.fault_type,
        faultMask="0",
        tickToClockRatio=_ratio,
        bitFlipProb=args.bit_flip_prob,
        stuckAtZeroProb=args.stuck_at_zero_prob,
        stuckAtOneProb=args.stuck_at_one_prob,
        addr_start=args.addr_start,
        addr_end=args.addr_end,
        rngSeed=args.rng_seed,
        maxFaults=args.max_faults,
        protectionModel=args.protection_model,
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
