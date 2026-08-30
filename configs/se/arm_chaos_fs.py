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
                        VExpress_GEM5_V1, CHAOSArmTLB, CHAOSArmSysReg)
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
p.add_argument("--tlb_protection_model", default="none",
               choices=["none","parity_interleaved"],
               help="§1.2 protection-aware layer for the TLB injector. 'none' "
                    "(default = L1 TLB raw escape, zero regression); "
                    "'parity_interleaved' (L2 TLB/walk-cache proxy: 1-bit "
                    "detect -> entry pfn restored before MMU use = Corrected "
                    "(real HW invalidates+re-walks, this restores, E3); >=2-bit "
                    "silent = SilentEscape).")
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

board = ArmBoard(
    clk_freq="3GHz",
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
if args.chaos_armtlb or args.chaos_sysreg:
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
            protectionModel=args.tlb_protection_model,
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
    cache_hierarchy._pre_instantiate = _attach_tlb

# Exit when the kernel reports it has booted (default exit handlers include
# the KernelBooted handler). This makes the FS run CI-able: boot-to-
# userspace-success = exit 0.
simulator = Simulator(board=board, full_system=True)
simulator.run()
