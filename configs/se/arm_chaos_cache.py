# arm_chaos_cache.py — explicit ARM SE config for CHAOSCache L1D injection.
# Uses ArmSystem + explicit classic L1I/L1D/L2 (real Cache SimObjects, so
# CHAOSCache attaches via the supported Cache::getTags() accessor). Solves the
# release_se error by setting ArmSystem.release = ArmDefaultRelease() (the
# stdlib SimpleBoard does this internally; here we do it explicitly so the
# L1D Cache is directly constructible/attachable).
import os, argparse
import m5
from m5.objects import (ArmSystem, SrcClockDomain, VoltageDomain, AddrRange,
    ArmTimingSimpleCPU, SystemXBar, L2XBar, Cache, BaseSetAssoc, LRURP,
    MemCtrl, DDR3_1600_8x8, Process, SEWorkload, CHAOSCache, Root,
    ArmDefaultRelease)
from m5.util import warn

p = argparse.ArgumentParser()
p.add_argument("--cmd", required=True)
p.add_argument("--target", default="l1d", choices=["l1d","l1i","l2"])
p.add_argument("--first_clock", type=lambda x:int(x,0), default=10000)
p.add_argument("--max_faults", type=lambda x:int(x,0), default=1)
p.add_argument("--rng_seed", type=lambda x:int(x,0), default=20260825)
p.add_argument("--fault_type", default="bit_flip")
p.add_argument("--bits_to_change", type=int, default=1)
p.add_argument("--probability", type=float, default=1.0)
args = p.parse_args()

system = ArmSystem()
system.release = ArmDefaultRelease()   # wires release_se via isa -> mmu
system.clk_domain = SrcClockDomain(clock="2GHz", voltage_domain=VoltageDomain())
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("1GiB")]
system.multi_proc = False

system.cpu = ArmTimingSimpleCPU()
system.cpu.createInterruptController()
system.membus = SystemXBar()

def mk(size, assoc, tl):
    return Cache(size=size, assoc=assoc, tag_latency=tl, data_latency=tl,
                 response_latency=2, mshrs=4, tgts_per_mshr=16,
                 replacement_policy=LRURP(), tags=BaseSetAssoc())
system.l1i = mk("64KiB", 2, 2)
system.l1d = mk("64KiB", 2, 2)
system.l2  = mk("512KiB", 8, 10)
system.l2xbar = L2XBar()
system.cpu.icache_port = system.l1i.cpu_side
system.cpu.dcache_port = system.l1d.cpu_side
system.l1i.mem_side = system.l2xbar.cpu_side_ports
system.l1d.mem_side = system.l2xbar.cpu_side_ports
system.l2xbar.mem_side_ports = system.l2.cpu_side
system.l2.mem_side = system.membus.cpu_side_ports
system.system_port = system.membus.cpu_side_ports

system.mem_ctrl = MemCtrl(dram=DDR3_1600_8x8())
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

system.workload = SEWorkload.init_compatible(args.cmd)
process = Process(pid=100); process.cmd = [args.cmd]
system.cpu.workload = process

target = {"l1d": system.l1d, "l1i": system.l1i, "l2": system.l2}[args.target]
system.chaos_cache = CHAOSCache(
    target_cache=target, probability=args.probability,
    firstClock=args.first_clock, lastClock=0,
    faultType=args.fault_type, bitsToChange=args.bits_to_change,
    rngSeed=args.rng_seed, maxFaults=args.max_faults, writeLog=True)

root = Root(full_system=False, system=system)
m5.instantiate()
ev = m5.simulate()
print(f"[arm_chaos_cache] exited cause={ev.getCause()} code={ev.getCode()}")
