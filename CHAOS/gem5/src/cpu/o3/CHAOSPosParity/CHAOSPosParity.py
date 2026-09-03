# CHAOSPosParity — positional-parity (position-anchored check) validator for
# the O3 store->load forwarding path. Research prototype for paper_zh.md §6.2
# (see docs/cases/core179-microarch-rootcause-synthesis/
# POSITIONAL_PARITY_RESEARCH.md §2.1 for the locked spec).
#
# Sender/receiver model: lsq_unit.cc calls tag() on the freshly-forwarded
# data BEFORE the CHAOSLSQFwd injector's corrupt() (send-end tagging), and
# verify() AFTER it (receive-end comparison). The check is a DUAL
# NON-COMMUTATIVE weighted mod-256 aggregate pair (pure-XOR mixing cancels
# under lane permutation — the XOR-invariance theorem, §2.1(iii); the round-1
# per-lane-tag snapshot degenerated to plain parity for exactly this reason):
#   W1 = (SUM_i (2i+1)   * (data[i]+1)) mod 256
#   W2 = (SUM_i ((2i+1)^0x5A) * (data[i]+1)) mod 256
# Honest detection figures (exact, subgroup-enumeration verified): single
# bit-flips 0 escapes (deterministic — odd weights); lane permutations on
# uniform random data escape with 2^-12 (ror odd k) / 2^-10 (ror 2,6) /
# 2^-5 (ror 4); adversarial data CAN escape (17/40319 perms for the
# uniform-parity probe word) — probabilistic vs adversarial data, NOT
# deterministic. The deterministic probability-1 claim holds ONLY for the
# lockstep design where tags travel with the data (future silicon work;
# tagWidth configures that design). Not covered: stale-line replay (needs a
# source tag).
from m5.params import *
from m5.SimObject import SimObject


class CHAOSPosParity(SimObject):
    type = "CHAOSPosParity"
    cxx_class = "gem5::CHAOSPosParity"
    cxx_header = "cpu/o3/CHAOSPosParity/CHAOSPosParity.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    tagWidth = Param.Int(3,
        "Lockstep-variant per-lane constant width in bits (L_i=(i+1)&"
        "2^w-1); 3 hosts the 8 pairwise-distinct lane constants. Configures "
        "the lockstep silicon design, NOT this snapshot model's dual "
        "weighted aggregates (which use fixed weight vectors).")

    action = Param.String("count",
        "count | panic  (mismatch response: count only, or fail-fast panic)")

    rngSeed = Param.UInt64(0,
        "RNG seed (unused; the dual weighted aggregates are deterministic)")
