# ooo_proxy.py — C3-OOO SE config (docs/gem5-fi/ooo north-star platform).
#
# Mirrors configs/se/kp920_proxy.py (stdlib SimpleBoard + classic L1/L2 +
# SimpleProcessor + the 16 CHAOS injector mount blocks) BUT sets the OoO
# fault-injection north-star platform parameters
# (docs/gem5-fi/ooo/00-overview.md 平台假设 + README §7):
#   width=4 all stages, ROB=128, PRF int128/fp192/vec48, 2.6GHz.
#
# HONEST NOTES (north-star 边界⑤: params are A72-public + gem5-example
# estimates, NOT Kunpeng 920 silicon values):
#   1. IQ: gem5 v25 unified IQ (instQueues=vector<IQUnit>); the default
#      IQUnit is numEntries=64 — matches north-star IQ=64. Int/FP split-IQ
#      (Neoverse V2 style, configs/common/cores/arm/neoverse_v2.py:120-198)
#      deferred pending the FUPool spike follow-up.
#   2. LQ/SQ: north star is silent on LSQ sizes -> gem5 defaults, no knobs.
#   3. SVE predicate pool (numPhysVecPredRegs) reserved for the C3-SVE
#      variant (north-star D78-D82, deferred; 920 has no SVE).
#   4. Default ArmO3CPU FUPool (IntALU×6/IntMultDiv×2/FP_ALU×4/FP_MultDiv×2)
#      — custom port map is separate work.
#
# USAGE (identical injector arg surface to arm_chaos.py / kp920_proxy.py):
#   gem5.opt --outdir=<dir> configs/se/ooo_proxy.py --cmd=<bin> --cpu O3 \
#       [--chaos_phys --phys_mode arch_frontend ...] \
#       [--rob 128 --phys_int 128 --phys_float 192 --phys_vec 48]

import argparse
import m5
from m5.objects import CHAOSReg, CHAOSPhysReg, CHAOSMem, CHAOSLSQFwd, CHAOSRenameMap, CHAOSFreeList, CHAOSROB, CHAOSIQ, CHAOSExec, CHAOSFPU, CHAOSL1DForward, CHAOSBPU, CHAOSAddrPath, CHAOSDecode, CHAOSExMon, CHAOSRAS, CHAOSProbe, CHAOSCommitTrace, CHAOSMicroSnap
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

# ---- C3-OOO north-star defaults (docs/gem5-fi/ooo README §7, 00-overview) ----
# These are the sweepable window axes. CLI --rob etc. override.
OOO = {
    "fetch_width": 4, "decode_width": 4, "rename_width": 4,
    "issue_width": 4, "dispatch_width": 4, "commit_width": 4,
    "rob": 128,            # 北极星边界⑤（A72+gem5 示例估计，非 920 真值）
    "phys_int": 128,       # docs/gem5-fi/ooo README §7
    "phys_float": 192,
    "phys_vec": 48,        # numPhysVecRegs（gem5 默认 256；北极星向量 PRF）
    "clk": "2.6GHz",       # 北极星 00-overview（公开资料折算）
}

p = argparse.ArgumentParser()
p.add_argument("--cmd", required=True)
p.add_argument("--cpu", default="O3", choices=list(cpu_map))
p.add_argument("--maxinsts", type=int, default=0)
# --- OOO window sweep knobs (north star; default = OOO) ---
p.add_argument("--rob", type=int, default=OOO["rob"],
               help=f"numROBEntries (north star ROB={OOO['rob']})")
p.add_argument("--phys_int", type=int, default=OOO["phys_int"],
               help=f"numPhysIntRegs (north star int={OOO['phys_int']})")
p.add_argument("--phys_float", type=int, default=OOO["phys_float"],
               help=f"numPhysFloatRegs (north star fp={OOO['phys_float']})")
p.add_argument("--phys_vec", type=int, default=OOO["phys_vec"],
               help=f"numPhysVecRegs (north star vec48={OOO['phys_vec']})")
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
p.add_argument("--addr_map_sub", action="store_true",
               help="§2.17 F5: CHAOSMem displaced write (addr map substitution)")
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
                        "all_zero", "fwd_source_sub", "phase_offset"])
p.add_argument("--lsq_lane_skew_k", type=int, default=1)
# §2.2 CHAOSRenameMap (O3 rename-map fault injector). SELF-ATTACHES at
# startup() to thread-0 frontRenameMap.chaosRenameMap. map_bitflip /
# map_bitflip2 (W4.1 D12: 2 distinct random index bits) / swap_to_active
# (W4.2a D13: swap mapping to a random ROB in-flight dest physReg) /
# f5_substitute / f4_field_stuck / f5_rat_stuck (W4.3 D15: ONE entry bit
# stuck-at-0/1, write-path mask on BOTH rename + squash-restore writes) /
# stale_read (W4.4 D16: the next rename overwrite of the entry silently
# fails once — readers get the old still-legal mapping)
# modes (design doc §2.2 + ooo 04 D12/D13/D15/D16).
p.add_argument("--chaos_rename", action="store_true",
               help="attach CHAOSRenameMap (O3 rename-map injector, §2.2)")
p.add_argument("--rename_mode", default="map_bitflip",
               choices=["map_bitflip","map_bitflip2","swap_to_active","f5_substitute","f4_field_stuck","spec_leak","f5_rat_stuck","stale_read","swap_mispred_event","hb_bitflip","hb_bitflip2"])
p.add_argument("--rename_target_arch", type=int, default=-1,
               help="arch reg index whose map entry to corrupt (-1=random 0..30 int / 0..31 vec)")
# W7.2 (ooo 04 D62-D71 merged rows): register-class axis for the RAT
# injector — vec = VecRegClass V0-V31 (scalar FP renames via VecRegClass
# on AArch64, so the north-star scalar-FP rows D62-66 are merged into the
# vec class; attribution of scalar-FP vs SIMD producers is post-hoc via
# the commit trace — documented in CHAOSRenameMap.hh).
p.add_argument("--rename_target_class", default="int", choices=["int","vec"],
               help="W7.2: register class whose RAT entries to corrupt (vec = VecRegClass V0-V31)")
p.add_argument("--rename_first_clock", type=lambda x: int(x,0), default=100000)
p.add_argument("--rename_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--rename_fault_mask", type=lambda x: int(x,0), default=0)
p.add_argument("--rename_rng_seed", type=lambda x: int(x,0), default=20260825)
# §2.2 CHAOSFreeList (O3 freelist fault injector). SELF-ATTACHES at startup()
# to physFreeList().chaosFreeList. mark_free (D17 fixed-interval) /
# pop_wrong / mark_free_event (W4.5 D18: duplicate allocation triggered when
# the int freelist remaining <= threshold) modes (§2.2 + ooo 04 D17/D18).
p.add_argument("--chaos_freelist", action="store_true",
               help="attach CHAOSFreeList (O3 freelist injector, §2.2)")
p.add_argument("--freelist_mode", default="mark_free",
               choices=["mark_free","pop_wrong","mark_free_event","drop_release","head_bitflip","head_bitflip2","head_stuck"])
# W7.3 (ooo 04 D72-D77 merged rows): register-class axis for the freelist
# injector — vec = VecRegClass pool (scalar FP rows D72/73/76 merged into
# D74/75/77).
p.add_argument("--freelist_target_class", default="int", choices=["int","vec"],
               help="W7.3: which class freelist to corrupt (vec = VecRegClass pool)")
p.add_argument("--freelist_first_clock", type=lambda x: int(x,0), default=100000)
p.add_argument("--freelist_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--freelist_rng_seed", type=lambda x: int(x,0), default=20260825)
p.add_argument("--freelist_event_threshold", type=lambda x: int(x,0), default=8,
               help="D18 mark_free_event: trigger when int freelist remaining <= N")
p.add_argument("--freelist_event_threshold_vec", type=lambda x: int(x,0), default=0,
               help="W7.3 D75 mark_free_event vec threshold (default 0 = pool drained; "
                    "04's <=6 re-derived per the W1.5b initial-free-4 calibration)")
# §2.3 CHAOSROB (O3 ROB fault injector). SELF-ATTACHES at startup() to
# cpu.rob.chaosROB. entry_bitflip / exc_suppress modes (§2.3).
p.add_argument("--chaos_rob", action="store_true",
               help="attach CHAOSROB (O3 ROB injector, §2.3)")
p.add_argument("--rob_mode", default="entry_bitflip",
               choices=["entry_bitflip","exc_suppress",
                        "pc_bitflip","pc_bitflip2","pc_stuck",
                        "destid_bitflip","destid_bitflip2",
                        "destid_swap_active","destid_stuck",
                        # W5.4 (D32-D35): done/completed bit at the commit
                        # gate (Commit::markCompletedInsts site).
                        "done_early","done_early_event",
                        "done_delay","done_delay_event",
                        # W5.6 (D40): whole-record stale read at insert.
                        "rob_stale_read",
                        # W5.6 (D36-D39): old-phys family — mounted via this
                        # flag but INSTANTIATED as CHAOSRenameMap below (the
                        # gem5 old-phys = rename historyBuffer prevPhysReg,
                        # W4 N1); CHAOSROB itself stays inert for them.
                        "oldphys_bitflip","oldphys_bitflip2",
                        "oldphys_swap_active","oldphys_stuck",
                        # W5.8-W5.9 (D41-D46): ROB head/tail pointer family —
                        # honest approximations at the rob_insert site
                        # (gem5 ROB = std::list, no pointer registers; head
                        # = commit-side entry-selection misalignment, tail
                        # = allocation-side alias onto an in-use entry).
                        "head_ptr_bitflip","head_ptr_bitflip2",
                        "head_ptr_stuck",
                        "tail_ptr_bitflip","tail_ptr_bitflip2",
                        "tail_ptr_stuck"])
p.add_argument("--rob_field", default="exc_status",
               choices=["result","done","exc_status","dest_phys","spec"])
p.add_argument("--rob_distance", type=int, default=0)
p.add_argument("--rob_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--rob_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--rob_rng_seed", type=lambda x: int(x,0), default=20260825)
# W7.4 (FP/SIMD Dispatch/ROB): register-class scope of the ROB dest-id
# family at the rob_insert site — "int" = the W5 D28-D31 scope (default,
# byte-identical); "vec" = the FP/SIMD twins (VecRegClass dests, domain
# [0, numVecPhysRegs), swap_active pool collects vec dests). PC/done/ptr
# families stay class-agnostic (unified ROB — TC'23).
p.add_argument("--rob_target_class", default="int", choices=["int","vec"],
               help="W7.4: ROB destid family register class")
# §2.5 CHAOSIQ (O3 instruction-queue injector). SELF-ATTACHES at startup()
# to IEW.instQueue.chaosIQ. wake_omit (F6) mode (§2.5).
p.add_argument("--chaos_iq", action="store_true",
               help="attach CHAOSIQ (O3 IQ injector, §2.5)")
p.add_argument("--iq_mode", default="wake_omit",
               choices=["wake_omit", "src_ready_bitflip", "wake_phase",
                        # W5.10-W5.11 (D47-D54, ooo 04-design-matrix
                        # R48-R55): the Int-IQ entry's ready bit and
                        # source-tag field, hooked at InstructionQueue
                        # insert / wakeDependents / the issue loop.
                        "ready_early", "ready_never", "ready_never_event",
                        "tag_swap", "tag_bitflip", "tag_bitflip2",
                        "tag_stuck", "tag_stale_read",
                        # W5.12 (D55, R56): FU-class misroute at the issue
                        # site (IntAlu<->IntMult; timing/port only — spike C).
                        "dispatch_misroute"])
p.add_argument("--iq_phase_offset", type=int, default=1,
               help="F6 wake_phase: delay cycles (positive only)")
p.add_argument("--iq_fault_mask", type=lambda x: int(x,0), default=0,
               help="W5.11 D51-D53: directed bit mask for the int-tag index")
p.add_argument("--iq_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--iq_max_faults", type=lambda x: int(x,0), default=1)
p.add_argument("--iq_rng_seed", type=lambda x: int(x,0), default=20260825)
# W7.4 (ooo 04-design-matrix D86-D91, FP/SIMD Dispatch/ROB): register-class
# scope of the IQ ready-bit / tag-field family — "int" = the W5 Int-IQ
# modes (default, byte-identical); "vec" = the FP/SIMD twins (VecRegClass
# rename domain: scalar FP + FP SIMD + integer SIMD all rename onto
# VecRegClass; tag domain [0, numVecPhysRegs)). fpOnly: the three §2.5
# wake modes restrict eligibility to FP/SIMD (Float* ∪ SimdFloat*)
# completed instructions — the D86 "FP/SIMD 队列版" opClass scoping.
p.add_argument("--iq_target_class", default="int", choices=["int","vec"],
               help="W7.4 D86-D91: IQ ready/tag family register class")
p.add_argument("--iq_fp_only", action="store_true",
               help="W7.4 D86: §2.5 wake modes fire only on FP/SIMD ops")
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
# v1.3 Phase 19.1: FPU mode knobs (parity with arm_chaos.py — the v1.1/v1.2
# modes were only wired on C0; the C2 arm died with argparse errors -> all
# 384 reps Inactive).
p.add_argument("--fpu_events_to_skip", type=lambda x: int(x,0), default=-1)
p.add_argument("--fpu_count_only", action="store_true")
p.add_argument("--fpu_bitseg", default="",
               choices=["", "sign", "exp_hi", "exp_lo", "mant_hi", "mant_mid",
                        "mant_lo"])
p.add_argument("--fpu_fma_weighted", action="store_true")
p.add_argument("--fpu_recurring_stuck", action="store_true")
p.add_argument("--fpu_rounding_sub", action="store_true")
p.add_argument("--fpu_f3_dependent", action="store_true")
p.add_argument("--fpu_exp_range", default="-1,-1")
p.add_argument("--fpu_fpsr_suppress", action="store_true")
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
# W6 D01-D07 (ooo 04-design-matrix R2-R8): encoding-corruption modes at
# the FETCH decode output (fetch.cc post-decode hook, AArch64 non-macroop
# only). dest_reg_sub keeps the legacy §2.14 rename-site semantics.
# W6 batch 2 (D08-D10, R9-R11): sign_ext_bit flips EXACTLY the format-
# located sign/top bit of the immediate's encoding (per-format table,
# GNU-as verified); imm_subfield_shift transposes two equal-width named
# subfields of the immediate encoding (immr<->imms, immlo<->immhi[1:0],
# hw<->imm16[15:14], sh<->imm12[11:10]; single-field formats honestly
# skipped+logged); crack_ctrl flips the LDP/STP addressing-mode field
# enc[24:23] on macroop (cracked) decodes — the gem5-v25 crack decision is
# baked into the static ISA decode table (no runtime latch), so the
# µop-stream perturbation is modeled at the encoding level (+1 spurious
# writeback µop / -1 lost writeback µop / composition swap, counts logged).
p.add_argument("--decode_mode", default="dest_reg_sub",
               choices=["dest_reg_sub","opcode_bitflip","opcode_bitflip2",
                        "opcode_swap","reg_bitflip","reg_bitflip2",
                        "imm_bitflip","imm_bitflip2",
                        "sign_ext_bit","imm_subfield_shift","crack_ctrl",
                        # W7 batch 1 (D56-D61, R57-R62 FP/SIMD Decode): same
                        # encoding-corruption engine gated by fpOnly (opClass
                        # in Float* ∪ SimdFloat*, CHAOSFPU.cc:88-98 scope;
                        # integer SIMD out of scope, documented). fp_opcode_
                        # swap = GNU-as-verified FP pair table (FADD<->FSUB/
                        # FMUL<->FDIV/FMADD<->FMSUB/FCMP<->FCMPE + SIMD
                        # mirrors); fp_reg_bitflip/2 ride W6 kRegBits
                        # (Vd/Vn/Vm covered); fp_route_bit flips enc[28:24]
                        # class bits with an opClass-change predicate.
                        "fp_opcode_bitflip","fp_opcode_bitflip2",
                        "fp_opcode_swap","fp_reg_bitflip",
                        "fp_reg_bitflip2","fp_route_bit"])
p.add_argument("--decode_first_clock", type=lambda x: int(x,0), default=1000)
p.add_argument("--decode_last_clock", type=lambda x: int(x,0), default=0)
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
# W0.3a CHAOSProbe (OoO occupancy/threshold event probe). READ-ONLY: no
# injector, no architectural-state writes — the reg_chain golden checksum
# must be unchanged with it attached. Emits ONE `CHAOS_PROBE samples=...
# robOver80=... iqOver80=... flIntLe8=... ...` stdout line at end of sim
# (field names embed these thresholds; parsed by tools/event_density.py).
p.add_argument("--chaos_probe", action="store_true",
               help="attach CHAOSProbe (OoO occupancy/threshold event probe, W0.3a)")
p.add_argument("--probe_sample_every", type=int, default=1,
               help="probe sampling period in CPU cycles")
p.add_argument("--probe_rob_pct", type=int, default=80,
               help="ROB over-occupancy threshold percent")
p.add_argument("--probe_iq_pct", type=int, default=80,
               help="IQ over-occupancy threshold percent")
p.add_argument("--probe_fl_int_le", type=int, default=8,
               help="int PRF freelist low-watermark (remaining <= N counts)")
p.add_argument("--probe_fl_float_le", type=int, default=12,
               help="float PRF freelist low-watermark")
p.add_argument("--probe_fl_vec_le", type=int, default=6,
               help="vec PRF freelist low-watermark")
# W2.1 CHAOSCommitTrace (L2 commit-per-instruction trace). READ-ONLY: no
# injector, no state writes, no events — the workload FINAL checksum must be
# byte-identical with it attached (hard gate). Writes one pinned-format CSV
# line per committed instruction (seq,tid,tick,pc,op,ndest[,class,arch,phys,
# val]*; consumed by tools/commit_diff.py) into the run --outdir.
p.add_argument("--chaos_ctrace", action="store_true",
               help="attach CHAOSCommitTrace (L2 commit trace, W2.1)")
p.add_argument("--ctrace_file", default="commit_trace.csv.gz",
               help="commit trace output file (relative to --outdir; "
                    "a .gz suffix is gzip-compressed automatically)")
# W2.4 CHAOSMicroSnap (L1 µarch shadow snapshot). READ-ONLY: no injector, no
# state writes, no events, nothing on stdout — the workload FINAL checksum
# must be byte-identical with it attached (hard gate). Emits one pinned-format
# CSV row every msnap_every committed instructions (ROB/IQ/freelist occupancy
# + ROB head/tail + the FRONT rename map per class as FNV hash + full table)
# into the run --outdir; tools/micro_diff.py aligns a no-fault reference run
# against a faulted run by snap_seq (L1 shadow compare).
p.add_argument("--chaos_msnap", action="store_true",
               help="attach CHAOSMicroSnap (L1 µarch snapshot, W2.4)")
p.add_argument("--msnap_every", type=int, default=1000,
               help="snapshot period in committed instructions")
p.add_argument("--msnap_file", default="micro_snap.csv.gz",
               help="snapshot CSV output (relative to --outdir; .gz = auto gzip)")
args = p.parse_args()

# C3-OOO cache geometry = same as kp920_proxy.py/C0: 64KiB L1 (4-way, 64B),
# 512KiB L2 (8-way, 64B). (Mirrors kp920_proxy.py; the C3-OOO differentiator
# is the O3 uarch params + 2.6GHz, NOT the cache sizes.)
cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="64KiB", l1i_size="64KiB", l2_size="512KiB",
)
memory = SingleChannelDDR3_1600("1GiB")
processor = SimpleProcessor(cpu_type=cpu_map[args.cpu], num_cores=1, isa=ISA.ARM)
core0 = processor.get_cores()[0]
cpu0 = core0.core  # the underlying BaseCPU SimObject

# ---- apply C3-OOO north-star microarchitecture params (the C3 point) ----
# Verified param names exist in build/ARM/params/BaseO3CPU.hh. Setting on the
# ArmO3CPU SimObject before m5.instantiate() is the standard gem5 pattern
# (cf. fi_research/probes/o3_chaos_smoke.py:68 on a bare ArmO3CPU).
if args.cpu == "O3":
    cpu0.fetchWidth = OOO["fetch_width"]
    cpu0.decodeWidth = OOO["decode_width"]
    cpu0.renameWidth = OOO["rename_width"]
    cpu0.issueWidth = OOO["issue_width"]
    cpu0.dispatchWidth = OOO["dispatch_width"]
    cpu0.commitWidth = OOO["commit_width"]
    cpu0.numROBEntries = args.rob
    cpu0.numPhysIntRegs = args.phys_int
    cpu0.numPhysFloatRegs = args.phys_float
    cpu0.numPhysVecRegs = args.phys_vec
    print(f"[ooo_proxy] C3-OOO params applied: width=4-wide, ROB={args.rob}, "
          f"physInt={args.phys_int}, physFloat={args.phys_float}, "
          f"physVec={args.phys_vec} (IQ=64 unified default; LQ/SQ=gem5 "
          f"default, north star silent; 2.6GHz)")

board = SimpleBoard(
    clk_freq=OOO["clk"],    # 2.6GHz (north star 00-overview, 公开资料折算)
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

board.set_se_binary_workload(binary=FileResource(args.cmd, override=True))

# CHAOS injector mount blocks — identical to arm_chaos.py / kp920_proxy.py
# (same 16 injectors, same arg mapping) so runner.py-style command lines work
# unchanged on C3-OOO.
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
    # hardcoded tickToClockRatio=1000 assumed 1GHz. On 2.6GHz (C2-KP/C3-OOO)
    # the period is 385 ticks, so 50000 cycles * 1000 = 50M ticks > cholesky's
    # total 31.7M ticks -> the window NEVER opened -> mem_formal was 384/384
    # Inactive (n_valid=0, invalid campaign). Compute the ratio from the
    # OOO clock exactly as gem5 does (Tick=1ps, Decimal ROUND_HALF_UP —
    # m5/ticks.py:80): 2.6GHz -> 385 t/cyc. (Can't read
    # clk_domain.clock.getValue() here: the global frequency isn't fixed
    # until m5.instantiate().)
    import decimal
    _freq = float(OOO["clk"].replace("GHz", "")) * 1e9
    _ratio = int(decimal.Decimal((1.0 / _freq) * 1e12)
                 .to_integral_value(decimal.ROUND_HALF_UP))
    print(f"[ooo_proxy] CHAOSMem tickToClockRatio={_ratio} "
          f"(CPU clock {OOO['clk']}, was hardcoded 1000)")
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
        addrMapSub=args.addr_map_sub,
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
        targetClass=args.rename_target_class,
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
        targetClass=args.freelist_target_class,
        probability=args.probability,
        firstClock=args.freelist_first_clock,
        maxFaults=args.freelist_max_faults,
        rngSeed=args.freelist_rng_seed,
        eventThreshold=args.freelist_event_threshold,
        eventThresholdVec=args.freelist_event_threshold_vec,
        writeLog=True,
    )
    board.chaos_freelist = fl

# W5.6 D36-D39 old-phys family: the design's component is the ROB entry's
# old-physical-register field, but gem5 stores old-phys in the rename
# historyBuffer checkpoint (W4 N1 mechanism finding) — those modes live in
# CHAOSRenameMap and are mounted here through the --rob_mode route (the rob
# block's own increment; the --rename_* args block is left untouched for
# the parallel W6 batch). CHAOSROB itself is inert for them (C++ side maps
# oldphys_* to Mode::OldphysInert — never a silent entry_bitflip fallback).
_W5_OLDPHYS_ROB_MODES = ("oldphys_bitflip", "oldphys_bitflip2",
                         "oldphys_swap_active", "oldphys_stuck")
if args.chaos_rob and args.rob_mode not in _W5_OLDPHYS_ROB_MODES:
    # §2.3 CHAOSROB: O3-only. SELF-ATTACHES at startup() to cpu.rob.chaosROB
    # (ROB::retireHead calls maybeCorrupt on the head inst pre-clearInROB;
    # W5.4 done-bit modes also hook Commit::markCompletedInsts via
    # cpu.o3Commit().setChaosROB).
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
        # W7.4: destid-family register class (int = W5 default; vec = the
        # FP/SIMD twins at the same rob_insert site).
        targetClass=args.rob_target_class,
    )
    board.chaos_rob = rob
elif args.chaos_rob:
    # W5.6: oldphys_* — instantiate the rename-history injector instead
    # (same push_front site as hb_bitflip; the rob_* knob set drives it:
    # first_clock / max_faults / rng_seed / probability).
    rob_oldphys = CHAOSRenameMap(
        cpu=cpu0,
        mode=args.rob_mode,
        targetArchReg=-1,
        probability=args.probability,
        firstClock=args.rob_first_clock,
        maxFaults=args.rob_max_faults,
        faultMask=0,
        rngSeed=args.rob_rng_seed,
        writeLog=True,
    )
    board.chaos_rob_oldphys = rob_oldphys

if args.chaos_iq:
    # §2.5 CHAOSIQ: O3-only. SELF-ATTACHES at startup() to
    # IEW.instQueue.chaosIQ (wakeDependents calls shouldOmitWake; the
    # W5.10-12 insert/wake/issue-site hooks likewise).
    iq = CHAOSIQ(
        cpu=cpu0,
        mode=args.iq_mode,
        phaseOffset=args.iq_phase_offset,
        probability=args.probability,
        firstClock=args.iq_first_clock,
        maxFaults=args.iq_max_faults,
        rngSeed=args.iq_rng_seed,
        faultMask=args.iq_fault_mask,
        writeLog=True,
        # W7.4 D86-D91: ready/tag family register class (int = W5 default;
        # vec = the FP/SIMD twins) + the D86 fpOnly opClass filter for the
        # §2.5 wake modes.
        targetClass=args.iq_target_class,
        fpOnly=args.iq_fp_only,
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
        eventsToSkip=(0xFFFFFFFFFFFFFFFF if args.fpu_events_to_skip < 0
                      else args.fpu_events_to_skip),
        countOnly=args.fpu_count_only,
        bitseg=args.fpu_bitseg,
        fmaWeighted=args.fpu_fma_weighted,
        recurringStuck=args.fpu_recurring_stuck,
        roundingSub=args.fpu_rounding_sub,
        f3Dependent=args.fpu_f3_dependent,
        expLo=int(args.fpu_exp_range.split(",")[0]),
        expHi=int(args.fpu_exp_range.split(",")[1]),
        fpsrSuppress=args.fpu_fpsr_suppress,
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
    # cpu.chaosDecode (rename.cc:1137 calls maybeCorrupt post-flatten;
    # W6 D01-D07 encoding modes hook fetch.cc post-decode instead).
    dc = CHAOSDecode(
        cpu=cpu0,
        mode=args.decode_mode,
        probability=args.probability,
        firstClock=args.decode_first_clock,
        lastClock=args.decode_last_clock,
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

if args.chaos_probe:
    # W0.3a CHAOSProbe: O3-only, READ-ONLY occupancy/threshold probe.
    # SELF-ATTACHES at startup() (dynamic_cast O3CPU; no gem5 source hook —
    # unlike the injectors it patches nothing). Sampling is a periodic
    # EventFunctionWrapper on the CPU clock; the summary line comes from an
    # exit callback at end of sim.
    probe = CHAOSProbe(
        cpu=cpu0,
        sampleEvery=args.probe_sample_every,
        robThresholdPct=args.probe_rob_pct,
        iqThresholdPct=args.probe_iq_pct,
        flIntLe=args.probe_fl_int_le,
        flFloatLe=args.probe_fl_float_le,
        flVecLe=args.probe_fl_vec_le,
        writeLog=True,
    )
    board.chaos_probe = probe

if args.chaos_ctrace:
    # W2.1 CHAOSCommitTrace: O3-only, READ-ONLY L2 commit trace. SELF-ATTACHES
    # at startup() to cpu.commit.chaosCommitTrace (commitHead calls
    # traceCommit right after the commit-renameMap setEntry loop — the
    # POST-INJECTION RAT — and before rob->retireHead). Unlike the probe it
    # needs that one-line gem5 source hook; attaching changes nothing else.
    ctr = CHAOSCommitTrace(
        cpu=cpu0,
        traceFile=args.ctrace_file,
        writeLog=True,
    )
    board.chaos_ctrace = ctr

if args.chaos_msnap:
    # W2.4 CHAOSMicroSnap: O3-only, READ-ONLY L1 µarch shadow snapshot.
    # SELF-ATTACHES at startup() to cpu.commit.chaosMicroSnap (commitHead
    # calls maybeSample at the same anchor point as the W2.1 trace — one
    # added gem5 source hook next to the W2.1 one; attaching changes nothing
    # else). Sampled every msnap_every committed instructions.
    msnap = CHAOSMicroSnap(
        cpu=cpu0,
        snapEvery=args.msnap_every,
        traceFile=args.msnap_file,
        writeLog=True,
    )
    board.chaos_msnap = msnap

if args.maxinsts:
    # W1.5b followup fix: BaseCPU's real param is max_insts_any_thread
    # (base.cc:334 -> scheduleInstStopAnyThread); the inherited
    # `cpu0.max_insts` raised AttributeError on ArmO3CPU (no such param,
    # discovered sizing W1.5b). Works for every cpu type incl. O3.
    # NOTE: arm_chaos.py / kp920_proxy.py carry the same broken knob on the
    # KP920 track — deliberately NOT touched here (track isolation).
    cpu0.max_insts_any_thread = args.maxinsts

simulator = Simulator(board=board, full_system=False)
simulator.run()
