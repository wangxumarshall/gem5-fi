#!/usr/bin/env python3
"""fs_checkpoint.py — FS checkpoint pipeline (plan §10.2).

Two-phase FS campaign flow that unlocks FS+O3 end-to-end injection for
CHAOSArmTLB / CHAOSArmSysReg / CHAOSAddrPath / CHAOSPTW:

  phase=boot : Atomic-boot Linux to the KernelBooted exit event, save a
               checkpoint (Simulator.save_checkpoint -> m5.checkpoint:
               drain + memWriteback + serializeAll), exit. (minutes; ONCE)
  phase=inject: restore from the checkpoint via
               set_kernel_disk_workload(checkpoint=<dir>) (the stdlib
               restore path — kernel_disk_workload.py sets board._checkpoint
               and Simulator.run() restores via _create_cpp_objects),
               attach CHAOS injectors, run the ROI with a single fault.
               (seconds-to-minutes per restore; per-seed)

HONEST v1 SCOPE: restore runs with the SAME (Atomic) CPU. TLB/SysReg/PTW
hooks fire on Atomic (their hook sites are CPU-model-independent);
CHAOSAddrPath's lsq.cc hook is O3-only and stays deferred until a
CPU-switch path lands (stdlib SimpleProcessor doesn't expose a clean
switchCpus — future work).

Usage:
  gem5.opt fs_checkpoint.py --phase=boot --ckpt-dir=cpts/base \
      --kernel=... --disk=... --bootloader=...
  gem5.opt fs_checkpoint.py --phase=inject --ckpt-dir=cpts/base \
      --injector=ptw --probability=1.0 --first-clock=1000 --seed=20260825 \
      --kernel=... --disk=... --bootloader=...
"""
import argparse
from pathlib import Path
import m5
from m5.objects import (ArmDefaultRelease, VExpress_GEM5_V1,
                        CHAOSArmTLB, CHAOSArmSysReg, CHAOSPTW)
from gem5.components.boards.arm_board import ArmBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy)
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import (KernelResource, DiskImageResource,
                                     BootloaderResource)
from gem5.simulate.simulator import Simulator

p = argparse.ArgumentParser()
p.add_argument("--phase", required=True, choices=["boot", "inject"])
p.add_argument("--ckpt-dir", required=True)
p.add_argument("--kernel", required=True)
p.add_argument("--disk", required=True)
p.add_argument("--bootloader", required=True)
p.add_argument("--root-partition", default="/dev/vda1")
p.add_argument("--mem-size", default="2GiB")
p.add_argument("--platform", default="V1", choices=["V1", "Foundation"])
p.add_argument("--cpu-timeout", type=int, default=3000,
               help="wall-clock seconds for the phase (default 3000)")
# inject-phase params
p.add_argument("--injector", default="none",
               choices=["none", "armtlb", "sysreg", "ptw"])
p.add_argument("--probability", type=float, default=1.0)
p.add_argument("--first-clock", type=lambda x: int(x, 0), default=1000)
p.add_argument("--max-faults", type=lambda x: int(x, 0), default=1)
p.add_argument("--seed", type=lambda x: int(x, 0), default=20260825)
p.add_argument("--fault-type", default="bit_flip")
p.add_argument("--tlb-target-field", default="pfn")
p.add_argument("--tlb-pfn-offset", type=lambda x: int(x, 0), default=0)
p.add_argument("--sysreg-target-regs", default="ttbr0_el1,ttbr1_el1")
p.add_argument("--ptw-clear-valid-bit", action="store_true")
args = p.parse_args()

cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="16KiB", l1i_size="16KiB", l2_size="256KiB")
memory = DualChannelDDR4_2400(size=args.mem_size)
processor = SimpleProcessor(cpu_type=CPUTypes.ATOMIC, num_cores=1, isa=ISA.ARM)
release = ArmDefaultRelease()
platform = VExpress_GEM5_V1() if args.platform == "V1" else None

board = ArmBoard(
    clk_freq="3GHz", processor=processor, memory=memory,
    cache_hierarchy=cache_hierarchy, release=release, platform=platform)

# Workload: boot phase = fresh boot; inject phase = restore from checkpoint
# (the checkpoint kwarg is the stdlib restore path).
wl_kwargs = dict(
    kernel=KernelResource(local_path=args.kernel),
    disk_image=DiskImageResource(local_path=args.disk,
                                 root_partition=args.root_partition),
    bootloader=BootloaderResource(local_path=args.bootloader),
    kernel_args=["root=" + args.root_partition, "rw",
                 "console=ttyAMA0", "earlycon=pl011,0x1c090000"])
if args.phase == "inject":
    # must be a Path (kernel_disk_workload.py:230 type-checks Path or
    # CheckpointResource — a str raises).
    wl_kwargs["checkpoint"] = Path(args.ckpt_dir)
board.set_kernel_disk_workload(**wl_kwargs)

# Attach the requested injector in a _pre_instantiate hook (same pattern as
# arm_chaos_fs.py — the ArmBoard builds the CPU/MMU lazily).
if args.phase == "inject" and args.injector != "none":
    _attached = [False]
    _orig_pi = getattr(cache_hierarchy, "_pre_instantiate", None)
    def _attach(root):
        if _orig_pi:
            _orig_pi(root)
        if _attached[0]:
            return
        cpu0 = processor.get_cores()[0].core
        if args.injector == "armtlb":
            dtb = cpu0.mmu.dtb
            board.chaos_armtlb = CHAOSArmTLB(
                tlb=dtb, probability=args.probability,
                firstClock=args.first_clock,
                faultType=args.fault_type,
                maxFaults=args.max_faults, rngSeed=args.seed,
                targetField=args.tlb_target_field,
                pfnOffset=args.tlb_pfn_offset,
                writeLog=True)
        elif args.injector == "sysreg":
            isa0 = cpu0.isa[0]
            board.chaos_sysreg = CHAOSArmSysReg(
                isa=isa0, probability=args.probability,
                firstClock=args.first_clock,
                faultType=args.fault_type,
                maxFaults=args.max_faults, rngSeed=args.seed,
                targetRegs=args.sysreg_target_regs,
                writeLog=True)
        elif args.injector == "ptw":
            # CHAOSPTW has no faultType param (its param face is
            # bitsToChange/faultMask/byteOffset/clearValidBit/ptwEcc).
            board.chaos_ptw = CHAOSPTW(
                mmu=cpu0.mmu, probability=args.probability,
                firstClock=args.first_clock,
                clearValidBit=args.ptw_clear_valid_bit,
                maxFaults=args.max_faults, rngSeed=args.seed,
                writeLog=True)
        _attached[0] = True
    cache_hierarchy._pre_instantiate = _attach

sim = Simulator(board=board, full_system=True)
sim.run()

if args.phase == "boot":
    # Reached here => the KernelBooted exit event fired. Save the checkpoint
    # (Simulator.save_checkpoint wraps m5.checkpoint: drain + memWriteback +
    # serializeAll — simulate/simulator.py:658).
    sim.save_checkpoint(Path(args.ckpt_dir))
    print(f"[fs_checkpoint] boot phase done; checkpoint at {args.ckpt_dir}")
else:
    print(f"[fs_checkpoint] inject phase done (injector={args.injector})")
