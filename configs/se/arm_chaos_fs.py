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
                        VExpress_GEM5_V1, CHAOSArmTLB, CHAOSArmSysReg,
                        CHAOSPTW)
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
# §3.2 FS checkpoint pipeline (Phase 5.2): restore from a checkpoint taken
# by boot_ckpt.rcS (Atomic boot -> m5 checkpoint -> m5 exit). The restore
# run may use a DIFFERENT cpu type (e.g. O3) — gem5's checkpoint restore
# switches the CPU and drains. Injectors mount fresh on the restore run;
# their firstClock is interpreted RELATIVE to the checkpoint tick when
# --ckpt_first_clock is given (see the rebase below).
p.add_argument("--restore-checkpoint", default=None,
               help="path to a checkpoint directory (e.g. m5out/cpt.12345); "
                    "restores from it instead of a fresh boot")
p.add_argument("--ckpt-first-clock", action="store_true", default=False,
               help="rebase --tlb_first_clock/--sysreg_first_clock to be "
                    "RELATIVE to the checkpoint tick (read from the ckpt's "
                    "m5out/tick file)")
# Phase 3 §六.4 item 3: CHAOSArmTLB TLB-entry injector (FS only).
p.add_argument("--chaos_armtlb", action="store_true",
               help="attach CHAOSArmTLB (ARM TLB-entry pfn corruptor)")
p.add_argument("--tlb_first_clock", type=lambda x:int(x,0), default=100000,
               help="CHAOSArmTLB first clock cycle eligible for injection")
p.add_argument("--tlb_probability", type=float, default=0.0,
               help="CHAOSArmTLB per-lookup injection probability")
p.add_argument("--tlb_fault_type", default="bit_flip",
               choices=["bit_flip", "stuck_at_zero", "stuck_at_one",
                        "random", "pfn_to_mapped_page"],
               help="CHAOSArmTLB fault type; pfn_to_mapped_page = §2.10 F5 "
                    "(substitute with another mapped entry's pfn)")
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
p.add_argument("--sysreg_fault_type", default="bit_flip",
               choices=["bit_flip", "stuck_at_zero", "stuck_at_one",
                        "random", "value_to_legal"],
               help="CHAOSArmSysReg fault type; value_to_legal = §2.10 F5 "
                    "(substitute with another whitelisted sysreg's value)")
p.add_argument("--sysreg_probability", type=float, default=0.0)
p.add_argument("--sysreg_max_faults", type=lambda x:int(x,0), default=1)
p.add_argument("--sysreg_fault_mask", type=lambda x:int(x,0), default=0)
p.add_argument("--sysreg_rng_seed", type=lambda x:int(x,0), default=20260825)
# §2.10 CHAOSPTW (page-table-walker PTE injector, FS-only, H7 knob).
p.add_argument("--chaos_ptw", action="store_true",
               help="attach CHAOSPTW to the D-side walk unit (FS-only)")
p.add_argument("--ptw_mode", default="single_bit_xor",
               choices=["single_bit_xor", "clear_valid"],
               help="PTE fault mode (clear_valid = H7 conditionalValidBit)")
p.add_argument("--ptw_first_clock", type=lambda x:int(x,0), default=100000)
p.add_argument("--ptw_max_faults", type=lambda x:int(x,0), default=1)
p.add_argument("--ptw_fault_mask", type=lambda x:int(x,0), default=0,
               help="PTE XOR bitmask; 0 = random single bit")
p.add_argument("--ptw_rng_seed", type=lambda x:int(x,0), default=20260825)
p.add_argument("--ptw_ecc", type=lambda x: (str(x).lower() in ("1","true","on")),
               default=True,
               help="H7: ECC on (spurious~0) / off (spurious>0)")
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
if args.chaos_armtlb or args.chaos_sysreg or args.chaos_ptw:
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
            faultType=args.tlb_fault_type,
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

        # §2.10 CHAOSPTW (Phase 5.3): hooks WalkUnit::doLongDescriptor —
        # bit-flips the fetched PTE pre-eval. FS-only (SE walks translateMmuOff).
        # The D-side walk unit is mmu.walker.walk_units[1] (inst/data/unified/
        # unified/... order in ArmMMU.py). ptwEcc models H7.
        if args.chaos_ptw:
            dwalker = cpu0.mmu.walker.walk_units[1]
            ptw = CHAOSPTW(
                walker=dwalker,
                mode=args.ptw_mode,
                probability=1.0,
                firstClock=args.ptw_first_clock,
                faultMask=args.ptw_fault_mask,
                ptwEcc=args.ptw_ecc,
                maxFaults=args.ptw_max_faults,
                rngSeed=args.ptw_rng_seed,
                writeLog=True,
            )
            board.chaos_ptw = ptw
            # CHAOSPTW SELF-ATTACHES (ctor sets walker->chaosPTW = this).

        # Phase 3 §六.4 item 3 (SYS): CHAOSArmSysReg attaches to the CPU's
        # ISA (isa vector, per-thread). The injector SELF-ATTACHES in its
        # constructor (isa->chaosSysReg = this), hooking readMiscRegNoEffect.
        if args.chaos_sysreg:
            isa0 = cpu0.isa[0]  # ArmISA instance for thread 0
            sys_reg = CHAOSArmSysReg(
                isa=isa0,
                probability=args.sysreg_probability,
                firstClock=args.sysreg_first_clock,
                faultType=args.sysreg_fault_type,
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

# §3.2 FS checkpoint pipeline (Phase 5.2): restore mode. Setting
# board._checkpoint makes the Simulator restore from that directory instead
# of a fresh boot (m5._create_cpp_objects(ckpt_dir=...)); the CPU type of
# THIS run replaces the checkpointed one (Atomic boot -> O3 ROI is the
# canonical pipeline). --ckpt-first-clock rebases the injector windows to be
# relative to the checkpoint tick: firstClock is in CPU cycles, and the
# checkpoint's tick is read from <ckpt>/../*.tick via m5's Utility.
if args.restore_checkpoint:
    import pathlib
    ckpt = pathlib.Path(args.restore_checkpoint)
    if not ckpt.exists():
        raise FileNotFoundError(f"--restore-checkpoint: {ckpt} not found")
    board._checkpoint = ckpt
    print(f"[arm_chaos_fs] restoring from checkpoint: {ckpt}")
    if args.ckpt_first_clock:
        # the tick file lives next to the checkpoint dir (m5out/cpt.<tick>
        # has no tick file inside; the sibling '<tick>.tick' under m5out
        # holds it — gem5 writes 'm5out/cpt.<tick>' plus a '<tick>.tick')
        # The tick is embedded in the checkpoint dir name (cpt.<tick>);
        # the .tick file variant is only written by some gem5 versions.
        ckpt_tick = None
        if ckpt.name.startswith("cpt."):
            try:
                ckpt_tick = int(ckpt.name[4:])
            except ValueError:
                pass
        if ckpt_tick is None:
            tick_file = ckpt.parent / (ckpt.name.replace("cpt.", "") + ".tick")
            if not tick_file.exists():
                cands = sorted(ckpt.parent.glob("*.tick"))
                tick_file = cands[-1] if cands else None
            ckpt_tick = int(open(tick_file).read().strip()) if (
                tick_file and tick_file.exists()) else None
        if ckpt_tick is not None:
            print(f"[arm_chaos_fs] checkpoint tick: {ckpt_tick} "
                  f"(injector windows rebased relative to it)")
            # Rebase: firstClock stays a cycle count but the injectors'
            # inWindow compares curTick() against first_clock*period —
            # so we add the checkpoint's cycle equivalent. The board clock
            # is 3GHz (333 ps period -> ~333 ticks/cycle at 1ps ticks).
            period_ticks = 333  # 3GHz board clock, ps-resolution ticks
            rebased = args.tlb_first_clock + (ckpt_tick // period_ticks)
            print(f"[arm_chaos_fs] tlb_first_clock: {args.tlb_first_clock} "
                  f"-> {rebased}")
            args.tlb_first_clock = rebased
        else:
            print("[arm_chaos_fs] WARN: no .tick file found; "
                  "first_clock NOT rebased (absolute cycles)")

# Exit when the kernel reports it has booted (default exit handlers include
# the KernelBooted handler). This makes the FS run CI-able: boot-to-
# userspace-success = exit 0.
simulator = Simulator(board=board, full_system=True)
simulator.run()
