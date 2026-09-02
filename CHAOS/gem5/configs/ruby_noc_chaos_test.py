# §2.15 CHAOSNoC 验证：ruby_random_test + CHAOSNoC flit_delay 注入
# 用法（从 CHAOS/gem5 目录）:
#   build/ARM/gem5.opt configs/ruby_noc_chaos_test.py [--chaos_noc]
import sys, os, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import m5
from m5.objects import *
from m5.util import addToPath
addToPath(ROOT)
addToPath(HERE)
addToPath(os.path.join(HERE, "common"))

from common import Options
from ruby import Ruby

parser = argparse.ArgumentParser()
Options.addNoISAOptions(parser)
Ruby.define_options(parser)
parser.add_argument("--chaos_noc", action="store_true",
                    help="attach CHAOSNoC to all NetworkLinks")
parser.add_argument("--noc_mode", default="flit_delay")
parser.add_argument("--noc_probability", type=float, default=1.0)
parser.add_argument("--noc_first_clock", type=int, default=1000)
parser.add_argument("--noc_max_faults", type=int, default=1)
parser.add_argument("--noc_rng_seed", type=int, default=20260825)
parser.add_argument("--maxloads", type=int, default=100)
parser.add_argument("--wakeup_freq", type=int, default=10)
args = parser.parse_args()

# RubyTester (like ruby_random_test)
check_flush = True if buildEnv["PROTOCOL"] == "MOESI_hammer" else False
tester = RubyTester(
    check_flush=check_flush,
    checks_to_complete=args.maxloads,
    wakeup_frequency=args.wakeup_freq,
)

system = System(cpu=tester, mem_ranges=[AddrRange(args.mem_size)])
system.voltage_domain = VoltageDomain(voltage=args.sys_voltage)
system.clk_domain = SrcClockDomain(
    clock=args.sys_clock, voltage_domain=system.voltage_domain
)
cpu_list = [system.cpu] * args.num_cpus
Ruby.create_system(args, False, system, cpus=cpu_list)
# ruby_random_test's post-setup (full port wiring)
tester.num_cpus = len(system.ruby._cpu_ports)
system.ruby.randomization = True
for ruby_port in system.ruby._cpu_ports:
    if ruby_port.support_data_reqs and ruby_port.support_inst_reqs:
        tester.cpuInstDataPort = ruby_port.in_ports
    elif ruby_port.support_data_reqs:
        tester.cpuDataPort = ruby_port.in_ports
    elif ruby_port.support_inst_reqs:
        tester.cpuInstPort = ruby_port.in_ports
    ruby_port.no_retry_on_stall = True
    ruby_port.using_ruby_tester = True
system.ruby.clk_domain = SrcClockDomain(
    clock=args.ruby_clock, voltage_domain=system.voltage_domain
)

# CHAOSNoC mount
if args.chaos_noc:
    noc = CHAOSNoC(mode=args.noc_mode,
                   probability=args.noc_probability,
                   firstClock=args.noc_first_clock,
                   maxFaults=args.noc_max_faults,
                   rngSeed=args.noc_rng_seed,
                   writeLog=True)
    # §2.15: attach via GarnetNetwork's chaosNoC param — the C++ side
    # propagates to ALL NetworkLinks at init() (links are C++-internal).
    system.ruby.network.chaosNoC = noc
    system.noc_injector = noc
    print("[noc-test] CHAOSNoC attached via GarnetNetwork.chaosNoC")

root = Root(full_system=False, system=system)
print('[noc-test] root created, instantiating...')
m5.instantiate()
print('[noc-test] instantiated OK')
print("[noc-test] starting simulation")
try:
    exit_event = m5.simulate(50000000)
    print(f"[noc-test] Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"[noc-test] SIMULATION ERROR: {e}")
print(f"[noc-test] Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
