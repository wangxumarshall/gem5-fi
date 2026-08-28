# x86_chaos.py — minimal x86-64 SE config for CHAOS mechanism verification.
# Phase 6 §10.4 cross-ISA prerequisite: prove CHAOS injectors work on x86.
# Uses stdlib SimpleBoard + ISA.X86 + O3. CHAOSReg attaches to the cpu.
# HONEST: this is a MECHANISM check (x86 hello, stdout oracle), NOT a formal
# §10.4 semantic-role pair (that needs an x86 checksum kernel, unavailable —
# no x86 cross-compiler on this aarch64 host; only gem5's bundled x86 hello).
import argparse, m5
from m5.objects import CHAOSReg
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import PrivateL1PrivateL2CacheHierarchy
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import FileResource
from gem5.simulate.simulator import Simulator

p = argparse.ArgumentParser()
p.add_argument("--cmd", required=True)
p.add_argument("--chaos_reg", action="store_true")
p.add_argument("--probability", type=float, default=1.0)
p.add_argument("--first_clock", type=lambda x:int(x,0), default=1000)
p.add_argument("--max_faults", type=lambda x:int(x,0), default=1)
p.add_argument("--rng_seed", type=lambda x:int(x,0), default=20260825)
p.add_argument("--fault_type", default="bit_flip")
p.add_argument("--bits_to_change", type=int, default=1)
p.add_argument("--reg_class", default="integer", choices=["integer","floating_point","both"])
args = p.parse_args()

ch = PrivateL1PrivateL2CacheHierarchy(l1d_size="64KiB", l1i_size="64KiB", l2_size="512KiB")
mem = SingleChannelDDR3_1600("1GiB")
proc = SimpleProcessor(cpu_type=CPUTypes.O3, num_cores=1, isa=ISA.X86)
board = SimpleBoard(clk_freq="2GHz", processor=proc, memory=mem, cache_hierarchy=ch)
board.set_se_binary_workload(binary=FileResource(args.cmd, override=True))

if args.chaos_reg:
    cpu0 = proc.get_cores()[0].core
    board.chaos_reg = CHAOSReg(
        cpu=cpu0, probability=args.probability, firstClock=args.first_clock,
        lastClock=0, maxFaults=args.max_faults, rngSeed=args.rng_seed,
        maxRegIdx=15, faultType=args.fault_type, faultMask=0,
        bitsToChange=args.bits_to_change, regTargetClass=args.reg_class,
        writeLog=True)

simulator = Simulator(board=board, full_system=False)
simulator.run()
