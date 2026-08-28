# arm_chaos_cache.py — CHAOSCache L1D/L1I/L2 injection via stdlib SimpleBoard.
#
# Solves the stdlib SimpleBoard L1D-exposure blocker (G3 functional test):
# the cache SimObjects are created lazily during Simulator._instantiate via
# the hierarchy's _pre_instantiate (which does setattr(hierarchy, name, cache)
# — CacheNode.__init__, abstract_cache_hierarchy.py:72). We monkey-patch the
# hierarchy's _pre_instantiate to capture the L1D Cache AFTER the setattr
# but BEFORE the final m5.instantiate, and attach CHAOSCache to it via the
# supported Cache::getTags() accessor (G3).
import sys, argparse, m5
from m5.objects import CHAOSCache
import gem5.components.cachehierarchies.classic.abstract_classic_cache_hierarchy as _ab
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy as _Base,
)
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import FileResource
from gem5.simulate.simulator import Simulator

p = argparse.ArgumentParser()
p.add_argument("--cmd", required=True)
p.add_argument("--cpu", default="O3", choices=["O3","Timing","Atomic","Minor"])
p.add_argument("--target", default="l1d", choices=["l1d","l1i","l2"])
p.add_argument("--first_clock", type=lambda x:int(x,0), default=10000)
p.add_argument("--max_faults", type=lambda x:int(x,0), default=1)
p.add_argument("--rng_seed", type=lambda x:int(x,0), default=20260825)
p.add_argument("--fault_type", default="bit_flip")
p.add_argument("--bits_to_change", type=int, default=1)
p.add_argument("--probability", type=float, default=1.0)
# Directed injection (report §六.3 'fixed-to' runs): pin the fault to a
# specific cache block (by address) and/or byte offset — lands on live
# data (L1D) or executed instruction bytes (L1I) instead of random.
p.add_argument("--target_block_addr", type=lambda x:int(x,0), default=0,
               help="Directed: cache block address to inject (block-aligned "
                    "lookup among VALID blocks). 0 = random (default).")
p.add_argument("--target_byte_offset", type=int, default=-1,
               help="Directed: byte offset within the target block "
                    "(0..blockSize-1). -1 = random (default).")
p.add_argument("--paired", action="store_true",
               help="§7.7 128B paired-sector fault-domain proxy: fault both "
                    "the target 64B block AND its 128B-aligned partner, same "
                    "byte offset. Use --target=l2 (as 'L3').")
args = p.parse_args()

cm = {"O3":CPUTypes.O3,"Timing":CPUTypes.TIMING,"Atomic":CPUTypes.ATOMIC,"Minor":CPUTypes.MINOR}
ch = _Base(l1d_size="64KiB", l1i_size="64KiB", l2_size="512KiB")
mem = SingleChannelDDR3_1600("1GiB")
proc = SimpleProcessor(cpu_type=cm[args.cpu], num_cores=1, isa=ISA.ARM)
board = SimpleBoard(clk_freq="2GHz", processor=proc, memory=mem, cache_hierarchy=ch)
board.set_se_binary_workload(binary=FileResource(args.cmd, override=True))
sim = Simulator(board=board, full_system=False)

# Capture the target cache via the _pre_instantiate hook (runs inside
# Simulator._instantiate, AFTER the hierarchy setattr the caches, BEFORE
# the final m5.instantiate). Attach CHAOSCache there.
attached = [False]
orig_pi = ch._pre_instantiate
def cap(root):
    orig_pi(root)
    if attached[0]:
        return
    target = getattr(ch, f"{args.target}-cache-0", None)
    if target is None:
        print(f"[arm_chaos_cache] WARNING: {args.target}-cache-0 not found; "
              f"available: l1d-cache-0/l1i-cache-0/l2-cache-0", file=sys.stderr)
        return
    board.chaos_cache = CHAOSCache(
        target_cache=target, probability=args.probability,
        firstClock=args.first_clock, lastClock=0,
        faultType=args.fault_type, bitsToChange=args.bits_to_change,
        rngSeed=args.rng_seed, maxFaults=args.max_faults,
        targetBlockAddr=args.target_block_addr,
        targetByteOffset=args.target_byte_offset,
        pairedSector=args.paired,
        writeLog=True)
    attached[0] = True
    print(f"[arm_chaos_cache] CHAOSCache attached to {args.target}-cache-0 "
          f"(supported Cache::getTags() path)")
ch._pre_instantiate = cap

sim.run()
