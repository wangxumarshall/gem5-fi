# gem5 SE-mode probe for the REAL sdcshield framework binary.
#
# Question (task_plan.md Phase 8.1/8.5): can the full sdcshield binary
# (meson build, dynamically linked, framework + per-CPU worker pthreads)
# execute under gem5 syscall emulation?
#
# Mechanism (multi-CPU pattern, following CHAOS/gem5's own
# configs/deprecated/example/se.py "one process per CPU"):
#   - cpu[0] runs the sdcshield Process.
#   - cpu[1..K] each run /bin/true; when those processes exit, their thread
#     contexts go Halted (syscall_emul.cc exitImpl -> tc->halt()) and become
#     the free pool that doClone() (src/sim/syscall_emul.hh) hands to guest
#     pthread_create() via System::Threads::findFree().
#   - futex is implemented (arm64 SE syscall table, base+98); exit (thread)
#     vs exit_group are distinguished (syscall_emul.cc exitImpl).
#   - AT_HWCAP/HWCAP2 are populated from the emulated ISA
#     (src/arch/arm/process.cc) so sdcshield's HWCAP feature gates work.
#
# Failed patterns (kept for the record, 2026-09-22):
#   v1: single CPU numThreads=8 -> BaseCPU::registerThreadContexts asserts
#       (needs system.multi_thread = True; Python param multi_thread).
#   v2: multi_thread=True + same Process on all 8 workload slots ->
#       Process::initState runs per slot, ArmProcess::argsInit re-maps the
#       arg region -> MemState::mapRegion isUnmapped assertion. Hence the
#       one-process-per-CPU pattern below.
#
# Usage:
#   gem5.opt se_sdcshield_probe.py <sdcshield-binary> [sdcshield args...]
# Probe invocation used 2026-09-22:
#   gem5.opt se_sdcshield_probe.py sdcshield/builddir/sdcshield \
#       -e fma -t 100 -n 1 -f no
#   (-n 1: single worker thread; -f no: no-fork ForkMode, gem5 SE has no fork)
#
# Precedent: sdcshield/scripts/eigen-sve-double/gem5/se_sve.py (single-thread
# standalone binaries, 2026-09-19). This probe extends it to the real
# framework binary via the clone()/findFree() thread-context pool.
import sys

import m5
from m5.objects import (
    ArmInterrupts,
    ArmISA,
    AtomicSimpleCPU,
    Process,
    Root,
    SEWorkload,
    SimpleMemory,
    SrcClockDomain,
    System,
    SystemXBar,
    VoltageDomain,
)

assert len(sys.argv) >= 2, "usage: gem5.opt se_sdcshield_probe.py <binary> [args...]"
cmd = sys.argv[1:]

import os
NUM_HELPER_CPUS = int(os.environ.get("PROBE_HELPERS", "6"))  # free TC pool for
# guest pthread_create() after helper exit; PROBE_HELPERS=0 = plain single-CPU run

system = System()
system.clk_domain = SrcClockDomain(
    clock="1GHz", voltage_domain=VoltageDomain(voltage="1V")
)
system.mem_mode = "atomic"
system.mem_ranges = [m5.objects.AddrRange("2GiB")]

system.cpu = [
    AtomicSimpleCPU(cpu_id=i) for i in range(1 + NUM_HELPER_CPUS)
]
for cpu in system.cpu:
    cpu.isa = ArmISA()

system.membus = SystemXBar()
system.system_port = system.membus.cpu_side_ports
for cpu in system.cpu:
    cpu.icache_port = system.membus.cpu_side_ports
    cpu.dcache_port = system.membus.cpu_side_ports
    cpu.interrupts = [ArmInterrupts()]
system.physmem = SimpleMemory(range=system.mem_ranges[0])
system.physmem.port = system.membus.mem_side_ports

# main process: the real sdcshield binary
main = Process(pid=100)  # unique pids required (Process default collides;
#   src/sim/process.cc:142 "fatal: _pid 100 is already used" otherwise)
main.executable = cmd[0]
main.cmd = cmd
system.cpu[0].workload = main

# helper processes: exit immediately -> Halted TCs = clone() free pool
for i in range(1, 1 + NUM_HELPER_CPUS):
    helper = Process(pid=100 + i)
    helper.executable = "/bin/true"
    helper.cmd = ["/bin/true"]
    system.cpu[i].workload = helper

system.workload = SEWorkload.init_compatible(cmd[0])

for cpu in system.cpu:
    cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

exit_event = m5.simulate()
print(
    f"Simulated exit code: {exit_event.getCode()} @ tick {m5.curTick()} "
    f"(cause: {exit_event.getCause()})"
)
sys.exit(exit_event.getCode())
