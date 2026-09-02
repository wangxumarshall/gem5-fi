# CHAOSPosParity — positional-parity (position-anchored check) validator for
# the O3 store->load forwarding path. Research prototype for paper_zh.md §6.2
# (see docs/cases/core179-microarch-rootcause-synthesis/
# POSITIONAL_PARITY_RESEARCH.md §2.1 for the locked spec).
#
# Sender/receiver model: lsq_unit.cc calls tag() on the freshly-forwarded
# data BEFORE the CHAOSLSQFwd injector's corrupt() (send-end tagging), and
# verify() AFTER it (receive-end comparison). Per-lane tags T_i =
# L_i ^ popcount1(data[i]) with L_i = (i+1)&7 (bijection onto {0..7}) detect
# any non-identity lane permutation with probability exactly 1 (identity is
# the only escape, verified over all 8! = 40,320 permutations); the pure-XOR
# aggregate word W backstops single bit-flips (W is permutation-INVARIANT
# under rotation by the XOR-invariance theorem — it does NOT detect
# rotations). Not covered: stale-line replay (needs a source tag).
from m5.params import *
from m5.SimObject import SimObject


class CHAOSPosParity(SimObject):
    type = "CHAOSPosParity"
    cxx_class = "gem5::CHAOSPosParity"
    cxx_header = "cpu/o3/CHAOSPosParity/CHAOSPosParity.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    tagWidth = Param.Int(3,
        "Per-byte-lane position tag width in bits. 3 hosts the 8 pairwise-"
        "distinct lane constants L_i=(i+1)&7 (a bijection onto {0..7}).")

    action = Param.String("count",
        "count | panic  (mismatch response: count only, or fail-fast panic)")

    rngSeed = Param.UInt64(0,
        "RNG seed (unused in v1; tags are deterministic)")
