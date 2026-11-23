# §2.16 HCCS 验证：ruby test + CHAOSCHI cross_die_msg_delay (MessageBuffer hook)
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
parser.add_argument("--chaos_chi", action="store_true",
                    help="attach CHAOSCHI (cross_die_msg_delay) to MessageBuffers")
parser.add_argument("--chi_mode", default="cross_die_msg_delay")
parser.add_argument("--chi_probability", type=float, default=1.0)
parser.add_argument("--chi_first_clock", type=int, default=100)
parser.add_argument("--chi_max_faults", type=int, default=1)
parser.add_argument("--chi_rng_seed", type=int, default=20260825)
parser.add_argument("--maxloads", type=int, default=100)
parser.add_argument("--wakeup_freq", type=int, default=10)
args = parser.parse_args()

check_flush = True if buildEnv["PROTOCOL"] == "MOESI_hammer" else False
tester = RubyTester(
    check_flush=check_flush,
    checks_to_complete=args.maxloads,
    wakeup_frequency=args.wakeup_freq,
)
system = System(cpu=tester, mem_ranges=[AddrRange(args.mem_size)])
system.voltage_domain = VoltageDomain(voltage=args.sys_voltage)
system.clk_domain = SrcClockDomain(clock=args.sys_clock,
                                    voltage_domain=system.voltage_domain)
cpu_list = [system.cpu] * args.num_cpus
Ruby.create_system(args, False, system, cpus=cpu_list)
system.ruby.clk_domain = SrcClockDomain(
    clock=args.ruby_clock, voltage_domain=system.voltage_domain
)
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

if args.chaos_chi:
    chi = CHAOSCHI(mode=args.chi_mode,
                   probability=args.chi_probability,
                   firstClock=args.chi_first_clock,
                   maxFaults=args.chi_max_faults,
                   rngSeed=args.chi_rng_seed,
                   writeLog=True)
    # MessageBuffer is a python-visible SimObject — attach directly
    # §2.9: attach via each MessageBuffer's chaosCHI python param (C++ ctor
    # reads it at construction). MessageBuffers are created inside
    # Ruby.create_system — re-attach post-hoc via the param doesn't work, so
    # we set the param BEFORE by monkey-patching... actually simplest: set on
    # each python-visible MessageBuffer AFTER create_system (the C++ side
    # reads it lazily at dequeue via a name-resolved singleton instead).
    # attach via each MessageBuffer's python param — C++ ctor reads it at
    # instantiate (after this assignment). MessageBuffers are python-visible
    # SimObjects in the ruby system tree.
    count = 0
    for obj in system.descendants():
        try:
            if isinstance(obj, m5.objects.MessageBuffer):
                obj.chaosCHI = chi
                count += 1
        except Exception:
            pass
    print(f"[chi-test] CHAOSCHI attached to {count} MessageBuffers via param")

root = Root(full_system=False, system=system)
m5.instantiate()
print("[chi-test] starting simulation")
exit_event = m5.simulate(50000000)
print(f"[chi-test] Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
