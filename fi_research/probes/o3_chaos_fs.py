# FS-mode CHAOS injection config for H6/H7 verification.
#
# WHY THIS EXISTS (honest): o3_chaos_smoke.py is SE-mode (Root(full_system=False),
# SEWorkload). In SE mode SCTLR.M=0, so mmu.cc:1213 dispatches to translateMmuOff
# -> setPaddr(vaddr), bypassing the page-table walker entirely. Hence:
#   - D2 hook (lsq.cc:1146 corruptAddr) fires but byte7-zeroed vaddr still maps
#     into [0, 512MiB) physical -> no fault -> 0 observable failures (H6 null).
#   - D3 hook (table_walker.cc:1959 corruptDescriptor) is in doLongDescriptor,
#     which SE never calls -> numFaultsInjected=0 (H7 null).
# FS mode (SCTLR.M=1 after Linux enables the MMU) walks real page tables through
# doLongDescriptor, so D2/D3 hooks actually trigger. This config wires the three
# injectors onto an fs_bigLITTLE-style system so H6/H7 can be exercised under
# MMU-on translation.
#
# This is a THIN WRAPPER over fs_bigLITTLE.run(): it builds the real FS system
# (VExpress_GEM5_V1 + real vmlinux + ubuntu.img + bootloader + dtb), then
# attaches CHAOSAddrPath/CHAOSPTW/CHAOSLSQFwd to the big cluster's CPU[0] and MMU.
#
# HONEST LIMITATION: FS boot to bash takes 15min-2h wall (130k inst/s measured).
# A full H6 (2x2) / H7 (3-arm) run is therefore many sim-hours. The FALSIFIABLE
# milestone that does NOT need bash: run a few minutes into early kernel init,
# SIGINT, and check that numAddrFaults / PTW injection counts > 0 in stats.txt
# -- this directly refutes the SE null result (hooks fire under FS translation).
#
# Usage (healthy cpus, isolate cpu179):
#   cd CHAOS/gem5
#   taskset -c 0-7 build/ARM/gem5.opt -d /tmp/h6fs --listener-mode on \
#       fi_research/probes/o3_chaos_fs.py \
#       --kernel /home/sdc/vmcore/gem5-fi/gem5-fs/vmlinux \
#       --disk   /home/sdc/vmcore/gem5-fi/gem5-fs/ubuntu.img \
#       --bootloader /home/sdc/vmcore/gem5-fi/gem5-fs/boot_emm.arm64 \
#       --dtb /home/sdc/vmcore/gem5-fi/gem5-fs/armv8_gem5_v1_1cpu.dtb \
#       --machine-type VExpress_GEM5_V1 --caches --mem-size 2GB \
#       --big-cpus 1 \
#       --addr-prob 0.01 --addr-byte 7 \
#       --ptw-prob 0.01 --ptw-ecc \
#       --lsq-fwd-prob 0.0
import os
import sys

# Make the gem5 configs/example/arm dir importable so we can reuse fs_bigLITTLE.
THIS = os.path.dirname(os.path.realpath(__file__))
GEM5 = os.path.abspath(os.path.join(THIS, "..", "..", "CHAOS", "gem5"))
sys.path.insert(0, os.path.join(GEM5, "configs", "example", "arm"))
os.chdir(GEM5)  # fs_bigLITTLE expects to be run from the gem5 root

import argparse
import m5
import fs_bigLITTLE as fsbl
from m5.objects import CHAOSAddrPath, CHAOSPTW, CHAOSLSQFwd

# Our extra injection args; the rest go to fs_bigLITTLE's option parser.
ap = argparse.ArgumentParser(add_help=False)
ap.add_argument("--addr-prob", default="0.0")
ap.add_argument("--addr-byte", default="7")
ap.add_argument("--ptw-prob", default="0.0")
ap.add_argument("--ptw-bits", default="1")
ap.add_argument("--ptw-ecc", action="store_true")
ap.add_argument("--lsq-fwd-prob", default="0.0")
ap.add_argument("--lsq-structural", default="none")
ap.add_argument("--lsq-skew", default="0")
ap.add_argument("--first-clock", default="0")
ap.add_argument("--max-faults", default="0")
ap.add_argument("--seed", default="0")
ap.add_argument("--max-tick", default="0", help="0=no cap; else cap sim")
fi_args, remaining = ap.parse_known_args()
sys.argv = [sys.argv[0]] + remaining

# Parse the FS options with fs_bigLITTLE's own parser, then build the system
# (build() returns root WITHOUT instantiating — so we can attach injectors).
parser = argparse.ArgumentParser(description="FS + CHAOS injection")
fsbl.addOptions(parser)
options = parser.parse_args()
root = fsbl.build(options)
system = root.system

# The big cluster holds the O3 CPUs (O3_ARM_v7a_3 <: ArmO3CPU).
target_cpu = system.bigCluster.cpus[0]

if float(fi_args.addr_prob) > 0.0:
    system.addrfi = CHAOSAddrPath(
        cpu=target_cpu,
        probability=float(fi_args.addr_prob),
        byteOffset=int(fi_args.addr_byte),
        firstClock=int(fi_args.first_clock),
        maxFaults=int(fi_args.max_faults),
        rngSeed=int(fi_args.seed),
        writeLog=True,
    )
    m5.util.inform("CHAOSAddrPath (D2) attached: prob=%s byte=%s",
                   fi_args.addr_prob, fi_args.addr_byte)

if float(fi_args.ptw_prob) > 0.0:
    system.ptwfi = CHAOSPTW(
        mmu=target_cpu.mmu,
        probability=float(fi_args.ptw_prob),
        bitsToChange=int(fi_args.ptw_bits),
        ptwEcc=bool(fi_args.ptw_ecc),
        firstClock=int(fi_args.first_clock),
        maxFaults=int(fi_args.max_faults),
        rngSeed=int(fi_args.seed),
        writeLog=True,
    )
    m5.util.inform("CHAOSPTW (D3) attached: prob=%s ecc=%s",
                   fi_args.ptw_prob, fi_args.ptw_ecc)

if float(fi_args.lsq_fwd_prob) > 0.0:
    system.lsqfi = CHAOSLSQFwd(
        cpu=target_cpu,
        probability=float(fi_args.lsq_fwd_prob),
        structuralFault=fi_args.lsq_structural,
        skewBytes=int(fi_args.lsq_skew),
        firstClock=int(fi_args.first_clock),
        maxFaults=int(fi_args.max_faults),
        rngSeed=int(fi_args.seed),
        writeLog=True,
    )
    m5.util.inform("CHAOSLSQFwd (D1) attached: prob=%s structural=%s",
                   fi_args.lsq_fwd_prob, fi_args.lsq_structural)

# Instantiate (after injectors are attached) then simulate. Cap sim via
# m5.simulate(max_tick) if requested (Root has no max_tick param in v25.1).
m5.instantiate()
m5.util.inform("FS+CHAOS instantiated. Simulating (MMU-on translation will "
               "exercise D2/D3 hooks; SIGINT to dump stats & exit).")
max_tick = int(fi_args.max_tick)
exit_event = m5.simulate(max_tick) if max_tick > 0 else m5.simulate()
m5.util.inform("Exiting @ tick %d cause=%s",
               m5.curTick(), exit_event.getCause())
