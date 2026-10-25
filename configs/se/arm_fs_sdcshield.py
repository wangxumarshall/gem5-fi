#!/usr/bin/env python3
# arm_fs_sdcshield.py — multi-core FS config: sdcshield in the guest with a
# second virtio disk (/dev/vdb), for MULTI-THREAD verification of tests
# (e.g. eigen_svd with -n <cores>) under a real Linux kernel + real pthreads.
#
# Based on arm_chaos_fs.py (Phase 3 FS bootstrap CI config). Differences:
#   1. --num-cpus N (default 2): SimpleProcessor multi-core (FS multi-thread
#      needs N guest CPUs; the stdlib VExpress platform generates the DTB
#      from the board, so no manual .dtb pick is needed).
#   2. --extra-disk IMG: attached as a second PciVirtIO block device ->
#      /dev/vdb in the guest (mke2fs -d ext2 image with bin/ + libs/;
#      see tools/fs_mk_sdcshield_disk.sh).
#   3. --readfile SCRIPT: run by the gem5 image hook after boot; the script
#      mounts /dev/vdb and runs the workload, ending with `/sbin/m5 exit`.
#   4. --timeout S: wall-clock SIGALRM backstop so a hung boot/guest cannot
#      wedge CI (simulation is NOT interrupted mid-instruction; alarm raises
#      and the process exits non-zero).
#   5. Default CPU is Atomic (fastest boot; functionally-correct multi-core
#      semantics — memory consistency is modeled; timing is not). Use
#      --cpu=TIMING/O3 only if timing fidelity is required (much slower).
#
# Usage:
#   gem5.opt --outdir=runs/fs_sdcshield configs/se/arm_fs_sdcshield.py \
#       --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img \
#       --bootloader=gem5-fs/boot.arm64 --root-partition=/dev/vda1 \
#       --extra-disk=gem5-fs-work/sdcshield.img \
#       --readfile=gem5-fs-work/guest_svd.sh --num-cpus=2

import argparse
import signal
from pathlib import Path

import m5
from m5.objects import (ArmDefaultRelease, VExpress_GEM5_V1,
                        PciVirtIO, VirtIOBlock, RawDiskImage, CowDiskImage)
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
from gem5.simulate.exit_event import ExitEvent

p = argparse.ArgumentParser()
p.add_argument("--kernel", required=True)
p.add_argument("--disk", required=True)
p.add_argument("--bootloader", required=True)
p.add_argument("--root-partition", default="/dev/vda1")
p.add_argument("--num-cpus", type=int, default=2)
p.add_argument("--extra-disk", default=None,
               help="second virtio-blk disk (ext2, appears as /dev/vdb)")
p.add_argument("--readfile", default=None,
               help="script the guest runs after boot (end it with m5 exit)")
p.add_argument("--cpu", default="Atomic", choices=["TIMING", "O3", "Atomic"])
p.add_argument("--mem-size", default="4GiB")
p.add_argument("--timeout", type=int, default=3600,
               help="wall-clock seconds backstop (SIGALRM)")
p.add_argument("--save-checkpoint", default=None,
               help="DIR: exit at KernelBooted and save a checkpoint there "
                    "(boot phase). The save point is BEFORE the userspace "
                    "readfile hook, so a later --checkpoint restore can run "
                    "a different --readfile workload.")
p.add_argument("--checkpoint", default=None,
               help="DIR: restore from a KernelBooted checkpoint "
                    "(run phase); requires --readfile for the workload")
args = p.parse_args()

signal.alarm(args.timeout)

cpu_map = {"TIMING": CPUTypes.TIMING, "O3": CPUTypes.O3,
           "Atomic": CPUTypes.ATOMIC}

cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="16KiB", l1i_size="16KiB", l2_size="256KiB",
)
memory = DualChannelDDR4_2400(size=args.mem_size)
processor = SimpleProcessor(cpu_type=cpu_map[args.cpu],
                            num_cores=args.num_cpus, isa=ISA.ARM)
release = ArmDefaultRelease()
platform = VExpress_GEM5_V1()

board = ArmBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
    release=release,
    platform=platform,
)

kernel = KernelResource(local_path=args.kernel)
disk = DiskImageResource(local_path=args.disk,
                         root_partition=args.root_partition)
bootloader = BootloaderResource(local_path=args.bootloader)

wl_kwargs = dict(
    kernel=kernel,
    disk_image=disk,
    bootloader=bootloader,
    readfile=args.readfile,
    kernel_args=["root=" + args.root_partition, "rw",
                 "console=ttyAMA0", "earlycon=pl011,0x1c090000"],
)
if args.checkpoint:
    # stdlib restore path: must be a Path (kernel_disk_workload.py
    # type-checks Path or CheckpointResource — a str raises).
    wl_kwargs["checkpoint"] = Path(args.checkpoint)
board.set_kernel_disk_workload(**wl_kwargs)

# Second disk -> /dev/vdb, attached in _pre_instantiate (the ArmBoard builds
# PCI devices lazily — same pattern as the CHAOS injector attach in
# arm_chaos_fs.py). Read-only RawDiskImage: the guest mounts it ext2.
if args.extra_disk:
    _attached = [False]
    _orig_pi = getattr(cache_hierarchy, "_pre_instantiate", None)
    def _attach_extra_disk(root):
        if _orig_pi:
            _orig_pi(root)
        if _attached[0]:
            return
        # CowDiskImage wrap (same pattern as the boot disk in
        # ArmBoard._add_disk_to_board): the guest may WRITE the ext2
        # superblock on mount, so a raw read_only image panics gem5
        # ("Cannot write to a read only disk image"). COW keeps writes in
        # the copy, the host file stays pristine.
        board._add_pci_device(PciVirtIO(vio=VirtIOBlock(
            image=CowDiskImage(
                child=RawDiskImage(read_only=True,
                                   image_file=args.extra_disk),
                read_only=False))))
        _attached[0] = True
    cache_hierarchy._pre_instantiate = _attach_extra_disk

if args.save_checkpoint:
    # Boot phase: exit at KernelBooted (before the userspace readfile hook
    # runs) and save. Generator yields True -> exit the simulation loop.
    def _kernel_booted_exit():
        yield True
    simulator = Simulator(
        board=board, full_system=True,
        on_exit_event={ExitEvent.KERNEL_BOOTED: _kernel_booted_exit()},
    )
    simulator.run()
    simulator.save_checkpoint(Path(args.save_checkpoint))
    print("[arm_fs_sdcshield] boot phase done; checkpoint saved to",
          args.save_checkpoint)
else:
    simulator = Simulator(board=board, full_system=True)
    simulator.run()
    print("[arm_fs_sdcshield] simulation ended normally")
