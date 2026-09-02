# Minimal ArmO3CPU + CHAOSPhysReg smoke config for the SDC research framework.
# Runs a user-supplied AArch64 static binary; injects ONE bit-flip into a
# (by default random) physical integer register at firstClock, traces reads.
#
# Usage:
#   build/ARM/gem5.opt o3_chaos_smoke.py --binary ./movbe_kernel --iters 200 \
#       --phys-idx -1 --bits 1
import sys, os
import m5
from m5.objects import *

thispath = os.path.dirname(os.path.realpath(__file__))

class L1ICache(Cache):
    assoc = 4; size = "32KiB"; tag_latency = 2; data_latency = 2
    response_latency = 2; mshrs = 4; tgts_per_mshr = 20
    def connectCPU(self, cpu): self.cpu_side = cpu.icache_port
    def connectBus(self, bus): self.mem_side = bus.cpu_side_ports

class L1DCache(Cache):
    assoc = 4; size = "32KiB"; tag_latency = 2; data_latency = 2
    response_latency = 2; mshrs = 4; tgts_per_mshr = 20
    def connectCPU(self, cpu): self.cpu_side = cpu.dcache_port
    def connectBus(self, bus): self.mem_side = bus.cpu_side_ports

class L2Cache(Cache):
    assoc = 8; size = "256KiB"; tag_latency = 20; data_latency = 20
    response_latency = 20; mshrs = 20; tgts_per_mshr = 12
    def connectCPUSideBus(self, bus): self.cpu_side = bus.mem_side_ports
    def connectMemSideBus(self, bus): self.mem_side = bus.cpu_side_ports

bin_default = os.path.join(thispath, "movbe_kernel")
opts = m5.options
from m5.util import addToPath
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--binary", default=bin_default)
ap.add_argument("--iters", default="200")
ap.add_argument("--phys-idx", default="-1", help="-1 = random phys reg")
ap.add_argument("--arch-idx", default="0", help="arch reg idx (arch modes)")
ap.add_argument("--mode", default="phys", help="phys|arch_frontend|arch_commit")
ap.add_argument("--reg-class", default="integer", help="integer|floating_point|vector|both")
ap.add_argument("--bits", default="1", help="bits to flip")
ap.add_argument("--mask", default="0", help="bitmask; 0=random(bits)")
ap.add_argument("--fault", default="bit_flip", help="bit_flip|stuck_at_zero|stuck_at_one|random")
ap.add_argument("--first-clock", default="100000", help="cycle of single injection")
ap.add_argument("--max-faults", default="1")
ap.add_argument("--probability", default="1.0", help="per-interval injection probability (use <1 with maxFaults>1 to spread injections in time)")
ap.add_argument("--seed", default="0")
ap.add_argument("--no-fi", action="store_true", help="disable injection (golden run)")
ap.add_argument("--max-tick", default="0", help="0 = no cap; else cap sim (Root.max_tick)")
ap.add_argument("--lsq-fwd-prob", default="0.0", help="CHAOSLSQFwd per-forward corruption probability (0=off)")
ap.add_argument("--lsq-fwd-bits", default="1", help="bits to flip on forwarded data")
ap.add_argument("--lsq-fwd-byte", default="-1", help="byte offset in forwarded buffer (-1=random)")
# P-D1: structural (whole-word) fault axis for CHAOSLSQFwd. Orthogonal to the
# per-byte bit-fault above. Models core-179 D1 (byte-lane skew / all-zero) which
# is NOT expressible as a bit flip (MICROARCH_SUPplement §2.2).
ap.add_argument("--lsq-structural", default="none", help="none|byte_lane_skew|all_zero (P-D1)")
ap.add_argument("--lsq-skew", default="0", help="byte_lane_skew rotation 1..7 (0=random)")
# P-D2: address-path (D2) injector — zeroes a byte of the load effAddr
# presented to the MMU. Models core 179's D2 (0814/0824: arch MSB != MMU MSB).
ap.add_argument("--addr-prob", default="0.0", help="CHAOSAddrPath per-load addr-corruption prob (0=off)")
ap.add_argument("--addr-byte", default="7", help="which byte of effAddr to zero (7=MSB,-1=random)")
# P-D3: PTW readout (D3) injector — bit-flips fetched PTEs. H7 knob: ptwEcc.
ap.add_argument("--ptw-prob", default="0.0", help="CHAOSPTW per-descriptor-fetch flip prob (0=off)")
ap.add_argument("--ptw-bits", default="1", help="bits to flip per PTE")
ap.add_argument("--ptw-ecc", action="store_true", help="model PTW array ECC (H7: corrects single-bit)")
# CHAOSPosParity: positional-parity validator (paper §6.2 detection prototype).
# Sender/receiver snapshot model: tag() before CHAOSLSQFwd corrupt(), verify()
# after — per-lane tags catch lane permutations (detection prob 1, identity
# the only escape); XOR aggregate word backstops bit-flips (W is permutation-
# invariant, does NOT detect rotations). Stats: numTagged/numVerified/
# numMismatches/numMismatchesPanic.
ap.add_argument("--posparity", action="store_true", help="attach CHAOSPosParity validator (paper §6.2)")
ap.add_argument("--posparity-action", default="count", help="count | panic (mismatch response)")

ap.add_argument("--l1d", default="32KiB")
a = ap.parse_args()

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "2GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]

system.cpu = ArmO3CPU()
# Larger OoO window — mirrors the ARM64 "big ROB/PRF" thesis in cpu.md.
system.cpu.numROBEntries = 192
system.cpu.LQEntries = 32
system.cpu.SQEntries = 32
system.cpu.numPhysIntRegs = 256
system.cpu.numPhysFloatRegs = 256

system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()
system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)
system.l2bus = L2XBar()
system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)
system.l2cache = L2Cache()
system.l2cache.connectCPUSideBus(system.l2bus)
system.membus = SystemXBar()
system.l2cache.connectMemSideBus(system.membus)
system.cpu.createInterruptController()
system.system_port = system.membus.cpu_side_ports
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

system.workload = SEWorkload.init_compatible(a.binary)
process = Process()
process.cmd = [a.binary, a.iters]
system.cpu.workload = process
system.cpu.createThreads()

if not a.no_fi:
    system.fi = CHAOSPhysReg(
        cpu=system.cpu,
        injectionMode=a.mode,
        targetPhysRegIdx=int(a.phys_idx),
        targetArchRegIdx=int(a.arch_idx),
        regTargetClass=a.reg_class,
        probability=float(a.probability),
        bitsToChange=int(a.bits),
        faultMask=int(a.mask, 0),
        faultType=a.fault,
        firstClock=int(a.first_clock),
        lastClock=0,
        maxFaults=int(a.max_faults),
        rngSeed=int(a.seed),
        writeLog=True,
    )

# CHAOSLSQFwd: store->load forwarding-path corruption (method2 mechanism).
# Independent of CHAOSPhysReg (register-cell) — this corrupts the datapath.
# The injector registers itself with the CPU in its constructor (cpu->lsqFwd
# = this), so lsq_unit.cc reaches it via the cpu pointer it already holds.
if float(a.lsq_fwd_prob) > 0.0:
    system.lsqfi = CHAOSLSQFwd(
        cpu=system.cpu,
        probability=float(a.lsq_fwd_prob),
        bitsToChange=int(a.lsq_fwd_bits),
        byteOffset=int(a.lsq_fwd_byte),
        structuralFault=a.lsq_structural,
        skewBytes=int(a.lsq_skew),
        firstClock=int(a.first_clock),
        lastClock=0,
        maxFaults=int(a.max_faults),
        rngSeed=int(a.seed),
        writeLog=True,
    )

# CHAOSAddrPath (D2): address-path corruption — zero a byte of the load's
# effAddr at the address->MMU boundary (lsq.cc sendFragmentToTranslation).
# Independent of CHAOSLSQFwd (D1, data path) — this corrupts the address.
if float(a.addr_prob) > 0.0:
    system.addrfi = CHAOSAddrPath(
        cpu=system.cpu,
        probability=float(a.addr_prob),
        byteOffset=int(a.addr_byte),
        firstClock=int(a.first_clock),
        lastClock=0,
        maxFaults=int(a.max_faults),
        rngSeed=int(a.seed),
        writeLog=True,
    )

# CHAOSPTW (D3): page-table-walker readout corruption — bit-flips fetched
# PTEs in the ARM table walker (table_walker.cc doLongDescriptor). H7 knob
# ptwEcc models whether the PTW array has ECC. Attaches via system.cpu.mmu.
if float(a.ptw_prob) > 0.0:
    system.ptwfi = CHAOSPTW(
        mmu=system.cpu.mmu,
        probability=float(a.ptw_prob),
        bitsToChange=int(a.ptw_bits),
        ptwEcc=bool(a.ptw_ecc),
        firstClock=int(a.first_clock),
        lastClock=0,
        maxFaults=int(a.max_faults),
        rngSeed=int(a.seed),
        writeLog=True,
    )

# CHAOSPosParity: positional-parity validator — the DETECTION counterpart of
# CHAOSLSQFwd above. Registers itself with the CPU in its constructor
# (cpu->posParity = this); lsq_unit.cc calls tag() before corrupt() and
# verify() after on the same forwarded buffer.
if a.posparity:
    system.posparity = CHAOSPosParity(
        cpu=system.cpu,
        tagWidth=3,
        action=a.posparity_action,
        rngSeed=int(a.seed),
    )


root = Root(full_system=False, system=system)
if int(a.max_tick) > 0:
    root.max_tick = int(a.max_tick)
m5.instantiate()
print(f"[smoke] binary={a.binary} iters={a.iters} mode={a.mode} phys_idx={a.phys_idx} "
      f"bits={a.bits} fault={a.fault} fi={'OFF' if a.no_fi else 'ON'}")
exit_event = m5.simulate()
print(f"[smoke] Exiting @ tick {m5.curTick()} cause={exit_event.getCause()}")
