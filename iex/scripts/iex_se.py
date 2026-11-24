#!/usr/bin/env python3
"""Minimal gem5 Arm O3 SE configuration for IEX directed samples.

One core, one thread, timing memory, classic L1/L2.  The workload is a
freestanding static AArch64 ELF with embedded context inputs.
"""
import argparse

import m5
from m5.objects import *
from m5.params import NULL
from gem5.components.cachehierarchies.classic.caches.l1icache import L1ICache
from gem5.components.cachehierarchies.classic.caches.l1dcache import L1DCache
from gem5.components.cachehierarchies.classic.caches.l2cache import L2Cache


def build(binary):
    system = System()
    system.clk_domain = SrcClockDomain(
        clock="2GHz", voltage_domain=VoltageDomain()
    )
    system.mem_mode = "timing"
    system.mem_ranges = [AddrRange("512MB")]

    system.cpu = ArmO3CPU()
    system.cpu.createInterruptController()

    system.membus = SystemXBar()
    system.l2bus = L2XBar()

    system.cpu.icache = L1ICache(size="32KiB")
    system.cpu.dcache = L1DCache(size="32KiB")
    # T04/T05 need real cold-load latency; disable prefetchers.
    system.cpu.icache.prefetcher = NULL
    system.cpu.dcache.prefetcher = NULL
    system.cpu.icache.cpu_side = system.cpu.icache_port
    system.cpu.dcache.cpu_side = system.cpu.dcache_port
    system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
    system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports

    system.l2 = L2Cache(size="256KiB")
    system.l2.prefetcher = NULL
    system.l2.cpu_side = system.l2bus.mem_side_ports
    system.l2.mem_side = system.membus.cpu_side_ports

    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR3_1600_8x8()
    system.mem_ctrl.dram.range = system.mem_ranges[0]
    system.mem_ctrl.port = system.membus.mem_side_ports
    system.system_port = system.membus.cpu_side_ports
    system.cache_line_size = 64

    system.workload = SEWorkload.init_compatible(binary)
    process = Process(pid=100)
    process.executable = binary
    process.cmd = [binary]
    system.cpu.workload = process
    system.cpu.createThreads()
    return system


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary")
    args = parser.parse_args()
    system = build(args.binary)
    root = Root(full_system=False, system=system)
    m5.instantiate()
    print("IEX_GEM5_BEGIN binary=%s" % args.binary, flush=True)
    event = m5.simulate()
    print("IEX_GEM5_END cause=%s tick=%d" % (event.getCause(), m5.curTick()),
          flush=True)


if __name__ == "__m5_main__":
    main()
