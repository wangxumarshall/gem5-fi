#!/usr/bin/env python3
# arm_chaos_fs.py — ARM64 full-system (FS) config for CHAOS fault injection.
#
# Phase 3 (§六.4 step 3: TLB/system-register FI) needs FS mode to reach the
# ARM MMU (TLB entries, page-table walker, system registers). This config
# boots the gem5-fs/ ARM Ubuntu disk via the gem5 v25 stdlib ArmBoard +
# VExpress_GEM5_Foundation platform, using LOCAL gem5-fs/ deps (kernel,
# disk, dtb, boot ROM) — no network resource fetch.
#
# The FS-mode bootstrap is itself the deliverable here: a TLB/SYS-reg
# injector SimObject does not exist yet (Phase 3 follow-up), but a
# bootable FS config is the prerequisite — without it, no TLB/SYS FI is
# possible. This config verifies FS mode boots to userspace on the
# gem5-fs deps, then exits (so it's CI-able).
#
# Usage:
#   gem5.opt --outdir=runs/fs configs/se/arm_chaos_fs.py \
#       --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img \
#       --bootloader=gem5-fs/boot.arm64 --root-partition=/dev/sda2 \
#       [--cpu=TIMING|O3|Atomic] [--mem-size=2GiB]

import argparse
import m5
from m5.objects import (ArmDefaultRelease, VExpress_GEM5_Foundation,
                        VExpress_GEM5_V1, CHAOSArmTLB, CHAOSArmSysReg, CHAOSAddrPath, CHAOSPTW)
from gem5.components.boards.arm_board import ArmBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import (
    KernelResource, DiskImageResource, BootloaderResource,
)
from gem5.simulate.simulator import Simulator

p = argparse.ArgumentParser()
p.add_argument("--kernel", required=True, help="path to vmlinux")
p.add_argument("--disk", required=True, help="path to the disk image")
p.add_argument("--bootloader", required=True, help="path to boot.arm64")
p.add_argument("--root-partition", default="/dev/vda1",
               help="root partition in the disk image. The ArmBoard attaches "
                    "the disk as a virtio-blk device, so it appears as "
                    "vda (NOT sda). gem5-fs/ubuntu.img is GPT; partition 1 "
                    "= ext4 root -> /dev/vda1.")
p.add_argument("--cpu", default="TIMING",
               choices=["TIMING", "O3", "Atomic"])
p.add_argument("--mem-size", default="2GiB")
# C2-KP FS: TaiShan V110 O3 proxy params (plan §4.1, E3). Applied to the O3
# CPU (when --cpu=O3, e.g. after checkpoint restore). FS boot uses Atomic by
# default (kp920 params are no-ops on Atomic, applied harmlessly).
p.add_argument("--kp920_proxy", action="store_true",
               help="Apply TaiShan V110 O3 proxy params (E3): ROB=128, "
                    "PhysIntRegs=160, PhysFloatRegs=192, LQ=48, SQ=42, 4-wide. "
                    "NOT cycle-exact. Applied to O3 (no-op on Atomic/Timing boot).")
p.add_argument("--rob_entries", type=int, default=128)
p.add_argument("--phys_int_regs", type=int, default=160)
p.add_argument("--phys_float_regs", type=int, default=192)
p.add_argument("--lq_entries", type=int, default=48)
p.add_argument("--sq_entries", type=int, default=42)
p.add_argument("--platform", default="V1",
               choices=["V1", "Foundation"],
               help="VExpress platform. V1 matches the gem5-fs "
                    "armv8_gem5_v1*.dtb + boot.arm64 combo; Foundation is "
                    "the stdlib default (different memory map).")
p.add_argument("--readfile", default=None,
               help="optional script run via m5 readfile after boot")
# Phase 3 §六.4 item 3: CHAOSArmTLB TLB-entry injector (FS only).
p.add_argument("--chaos_armtlb", action="store_true",
               help="attach CHAOSArmTLB (ARM TLB-entry pfn corruptor)")
p.add_argument("--tlb_first_clock", type=lambda x:int(x,0), default=100000,
               help="CHAOSArmTLB first clock cycle eligible for injection")
p.add_argument("--tlb_probability", type=float, default=0.0,
               help="CHAOSArmTLB per-lookup injection probability")
p.add_argument("--tlb_max_faults", type=lambda x:int(x,0), default=1,
               help="CHAOSArmTLB max faults; 1 for single-fault")
p.add_argument("--tlb_fault_mask", type=lambda x:int(x,0), default=0,
               help="CHAOSArmTLB 64-bit pfn mask; 0=random")
p.add_argument("--tlb_rng_seed", type=lambda x:int(x,0), default=20260825)
p.add_argument("--tlb_target_field", default="pfn",
               choices=["pfn","ap","xn","attridx","ng","asid"],
               help="CHAOSArmTLB field-level target (§5.7B).")
p.add_argument("--tlb_pfn_offset", type=lambda x:int(x,0), default=0,
               help="F5 directed pfn offset (pfn+=offset, another page frame).")
# Phase 3 §六.4 item 3 (SYS): CHAOSArmSysReg system-register injector.
# Hooks ISA::readMiscRegNoEffect (MRS read path). Whitelist of ARM MiscReg
# enum NAMES (TTBR/TCR/MAIR/SCTLR/VBAR etc.) — empty = no injection.
p.add_argument("--chaos_sysreg", action="store_true",
               help="attach CHAOSArmSysReg (ARM system-register read-path "
                    "corruptor, FS only)")
p.add_argument("--sysreg_first_clock", type=lambda x:int(x,0), default=100000)
p.add_argument("--sysreg_probability", type=float, default=0.0)
p.add_argument("--sysreg_max_faults", type=lambda x:int(x,0), default=1)
p.add_argument("--sysreg_fault_mask", type=lambda x:int(x,0), default=0)
p.add_argument("--sysreg_rng_seed", type=lambda x:int(x,0), default=20260825)
p.add_argument("--sysreg_target_regs", default="",
               help="comma-separated ARM miscRegName strings (lowercase, "
                    "from misc.hh miscRegName[]), e.g. "
                    "sctlr_el1,ttbr0_el1,tcr_el1,mair_el1,vbar_el1")
# S1-5b CHAOSAddrPath (P-D2): address-path FI. FS-only (byte7-zeroed vaddr
# faults only with MMU-on). Reproduces core 179 D2 signature.
p.add_argument("--chaos_addrpath", action="store_true",
               help="attach CHAOSAddrPath (P-D2 address-path FI; FS-only "
                    "observable, reproduces core179 D2 byte7-zero).")
p.add_argument("--addrpath_probability", type=float, default=0.0)
p.add_argument("--addrpath_byte_offset", type=int, default=7,
               help="Which addr byte to zero (7=MSB; reproduces core179 D2).")
p.add_argument("--addrpath_first_clock", type=lambda x:int(x,0), default=100000)
p.add_argument("--addrpath_max_faults", type=lambda x:int(x,0), default=1)
p.add_argument("--addrpath_rng_seed", type=lambda x:int(x,0), default=20260825)
# S2-5c CHAOSPTW (P-D3): PTW readout FI. FS-only (SE never walks the table).
p.add_argument("--chaos_ptw", action="store_true",
               help="attach CHAOSPTW (P-D3 PTW-readout FI; FS-only, "
                    "reproduces core179 D3 spurious translation faults).")
p.add_argument("--ptw_probability", type=float, default=0.0)
p.add_argument("--ptw_fault_mask", type=lambda x:int(x,0), default=0)
p.add_argument("--ptw_byte_offset", type=int, default=-1)
p.add_argument("--ptw_clear_valid_bit", action="store_true",
               help="force-clear PTE valid bits (reliably manufactures spurious).")
p.add_argument("--ptw_ecc", action="store_true",
               help="model PTW array ECC (H7: ECC-on corrects single-bit).")
p.add_argument("--ptw_first_clock", type=lambda x:int(x,0), default=100000)
p.add_argument("--ptw_max_faults", type=lambda x:int(x,0), default=1)
p.add_argument("--ptw_rng_seed", type=lambda x:int(x,0), default=20260825)
args = p.parse_args()

cpu_map = {"O3": CPUTypes.O3, "TIMING": CPUTypes.TIMING,
           "Atomic": CPUTypes.ATOMIC}

cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="16KiB", l1i_size="16KiB", l2_size="256KiB",
)
memory = DualChannelDDR4_2400(size=args.mem_size)
processor = SimpleProcessor(cpu_type=cpu_map[args.cpu], num_cores=1, isa=ISA.ARM)
release = ArmDefaultRelease()
platform = VExpress_GEM5_V1() if args.platform == "V1" else VExpress_GEM5_Foundation()

# C2-KP FS: V110 O3 proxy params (plan §4.1, E3). Applied to the O3 CPU;
# no-op on Atomic/Timing (the params are O3-specific, silently ignored).
# Honest: gem5 unified IQ ≠ V110 distributed quad-scheduler; no partition L3;
# no bufferless NoC. Used for formal FS campaign after checkpoint→O3 switch.
if args.kp920_proxy:
    _cpu0 = processor.get_cores()[0].core
    try:
        _cpu0.numROBEntries = args.rob_entries
        _cpu0.numPhysIntRegs = args.phys_int_regs
        _cpu0.numPhysFloatRegs = args.phys_float_regs
        _cpu0.numPhysVecRegs = args.phys_float_regs
        _cpu0.LQEntries = args.lq_entries
        _cpu0.SQEntries = args.sq_entries
        _cpu0.fetchWidth = 4
        _cpu0.decodeWidth = 4
        _cpu0.renameWidth = 4
        _cpu0.issueWidth = 4
        _cpu0.dispatchWidth = 4
        _cpu0.commitWidth = 4
    except AttributeError as e:
        m5.warn("kp920_proxy: some V110 params not settable on %s: %s" %
                (args.cpu, str(e)))

clk = "2.6GHz" if args.kp920_proxy else "3GHz"

board = ArmBoard(
    clk_freq=clk,
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
    release=release,
    platform=platform,
)

# Local gem5-fs/ resources (no network fetch).
kernel = KernelResource(local_path=args.kernel)
disk = DiskImageResource(local_path=args.disk,
                         root_partition=args.root_partition)
bootloader = BootloaderResource(local_path=args.bootloader)

# Minimal kernel args: the ArmBoard's get_default_kernel_args adds the
# console + mem args; we just append root= + init (and an m5 exit on boot
# via readfile if given, else rely on KernelBootedExitHandler).
board.set_kernel_disk_workload(
    kernel=kernel,
    disk_image=disk,
    bootloader=bootloader,
    readfile=args.readfile,
    kernel_args=["root=" + args.root_partition, "rw",
                 "console=ttyAMA0", "earlycon=pl011,0x1c090000"],
)

# Phase 3 §六.4 item 3: attach CHAOSArmTLB to the CPU's D-TLB (the TLB whose
# lookups carry data translations — the most SDC-relevant). CHAOSArmTLB is a
# SimObject that holds a TLB* and self-registers via TLB::setChaosTLB. The
# stdlib ArmBoard builds the CPU+MMU lazily, so attach in a _pre_instantiate
# hook (after construction, before m5.instantiate). The D-TLB path under
# the ArmBoard's cpu0 is cpu0.mmu.dtb (data TLB); i-TLB is cpu0.mmu.itb.
# Attach CHAOS injectors that need the stdlib-built CPU in a _pre_instantiate
# hook (the ArmBoard builds the CPU+MMU lazily). Either TLB or SYS (or both)
# trigger the hook. cpu0 = processor.get_cores()[0].core; D-TLB = cpu0.mmu.dtb;
# ISA = cpu0.isa[0] (BaseCPU.isa is a per-thread VectorParam.BaseISA).
if args.chaos_armtlb or args.chaos_sysreg or args.chaos_addrpath or args.chaos_ptw:
    _tlb_attached = [False]
    _orig_pi = getattr(cache_hierarchy, "_pre_instantiate", None)
    def _attach_tlb(root):
        if _orig_pi:
            _orig_pi(root)
        if _tlb_attached[0]:
            return
        core0 = processor.get_cores()[0]
        cpu0 = core0.core
        dtb = cpu0.mmu.dtb  # the data TLB (ArmISA::TLB)
        arm_tlb = CHAOSArmTLB(
            tlb=dtb,
            probability=args.tlb_probability,
            firstClock=args.tlb_first_clock,
            faultType="bit_flip",
            faultMask=args.tlb_fault_mask,
            bitsToChange=1,
            maxFaults=args.tlb_max_faults,
            rngSeed=args.tlb_rng_seed,
            targetField=args.tlb_target_field,
            pfnOffset=args.tlb_pfn_offset,
            writeLog=True,
        )
        board.chaos_armtlb = arm_tlb
        # CHAOSArmTLB SELF-ATTACHES (constructor sets tlb->chaosTLB = this),
        # same pattern as CHAOSLSQFwd — no setChaosTLB call (no python binding).
        _tlb_attached[0] = True

        # Phase 3 §六.4 item 3 (SYS): CHAOSArmSysReg attaches to the CPU's
        # ISA (isa vector, per-thread). The injector SELF-ATTACHES in its
        # constructor (isa->chaosSysReg = this), hooking readMiscRegNoEffect.
        if args.chaos_sysreg:
            isa0 = cpu0.isa[0]  # ArmISA instance for thread 0
            sys_reg = CHAOSArmSysReg(
                isa=isa0,
                probability=args.sysreg_probability,
                firstClock=args.sysreg_first_clock,
                faultType="bit_flip",
                faultMask=args.sysreg_fault_mask,
                bitsToChange=1,
                targetRegs=args.sysreg_target_regs,
                maxFaults=args.sysreg_max_faults,
                rngSeed=args.sysreg_rng_seed,
                writeLog=True,
            )
            board.chaos_sysreg = sys_reg
            # SELF-ATTACH: constructor set isa0->chaosSysReg = this.

        # S1-5b CHAOSAddrPath (P-D2): attaches to the O3CPU. SELF-ATTACHES
        # (ctor sets cpu->addrPath = this). FS MODE REQUIRED: byte7-zeroed
        # vaddr faults only with MMU-on (SCTLR.M=1 after Linux boots). Needs
        # O3 (CHAOSAddrPath hooks the O3 LSQ sendFragmentToTranslation).
        if args.chaos_addrpath:
            # The FS boot uses Atomic by default; CHAOSAddrPath's hook is in
            # the O3 LSQ, so it only fires when the CPU is switched to O3
            # (e.g. after checkpoint restore). On Atomic it instantiates but
            # does not fire (harmless).
            try:
                ap = CHAOSAddrPath(
                    cpu=cpu0,
                    probability=args.addrpath_probability,
                    byteOffset=args.addrpath_byte_offset,
                    firstClock=args.addrpath_first_clock,
                    maxFaults=args.addrpath_max_faults,
                    rngSeed=args.addrpath_rng_seed,
                    writeLog=True,
                )
                board.chaos_addrpath = ap
            except Exception as e:
                m5.warn("CHAOSAddrPath attach skipped (cpu0 may be Atomic, not O3): %s" % str(e))

        # S2-5c CHAOSPTW (P-D3): attaches to the MMU (whose table-walker to
        # hook). SELF-ATTACHES (ctor sets mmu->setPtwInj(this)). FS REQUIRED:
        # SE never walks the table. Uses cpu0.mmu (BaseMMU).
        if args.chaos_ptw:
            try:
                ptw = CHAOSPTW(
                    mmu=cpu0.mmu,
                    probability=args.ptw_probability,
                    faultMask=args.ptw_fault_mask,
                    byteOffset=args.ptw_byte_offset,
                    clearValidBit=args.ptw_clear_valid_bit,
                    ptwEcc=args.ptw_ecc,
                    firstClock=args.ptw_first_clock,
                    maxFaults=args.ptw_max_faults,
                    rngSeed=args.ptw_rng_seed,
                    writeLog=True,
                )
                board.chaos_ptw = ptw
            except Exception as e:
                m5.warn("CHAOSPTW attach skipped: %s" % str(e))
    cache_hierarchy._pre_instantiate = _attach_tlb

# Exit when the kernel reports it has booted (default exit handlers include
# the KernelBooted handler). This makes the FS run CI-able: boot-to-
# userspace-success = exit 0.
simulator = Simulator(board=board, full_system=True)
simulator.run()
