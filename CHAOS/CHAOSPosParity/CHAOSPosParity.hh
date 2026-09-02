#ifndef __CPU_O3_CHAOS_POS_PARITY_HH__
#define __CPU_O3_CHAOS_POS_PARITY_HH__

#include <cstdint>
#include <memory>

#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSPosParity.hh"
#include "sim/sim_object.hh"

namespace gem5
{

namespace o3 { class CPU; }

// CHAOSPosParity — positional-parity (position-anchored check) validator for
// the O3 store->load forwarding path. Research prototype for paper_zh.md §6.2:
// byte-lane skew (a Hamming-distance-0 structural fault) is invisible to
// conventional ECC when check bits misroute in lockstep with data (the column
// permutation of H commutes with the syndrome — see
// POSITIONAL_PARITY_RESEARCH.md §2.1). This validator anchors a per-lane
// position tag to each byte channel, making any non-identity lane permutation
// a guaranteed mismatch.
//
// Tag design (spec locked in the research plan, §2.1(ii)):
//   L_i  = (i+1) & 0x7                — lane constants
//   T_i  = L_i ^ popcount1(data[i])   — per-lane tag (data parity mixed in)
//   W    = XOR_i (data[i] ^ (L_i << 5)) — aggregate check word
//
// L is a BIJECTION on 8 lanes: {(i+1)&7 : i=0..7} = {1,2,3,4,5,6,7,0} is
// exactly the set {0..7} — 8 pairwise-distinct constants filling the whole
// 3-bit space (the plan's early "lane 7 maps to 0, forbidden" hesitation is
// resolved by this bijection argument: 0 is a legal constant, distinctness is
// what matters, and (i+1)&7 delivers it). Lane 7's tag being 0^parity carries
// no positional information *of that lane alone*, but the permutation
// argument below needs only distinctness, not nonzeroness.
//
// Detection — division of labor (per the locked spec and §2.1(iii)):
//   * ROTATIONS: caught by the per-lane tags, probability EXACTLY 1. Under
//     the snapshot model wired in lsq_unit.cc (tag() BEFORE corrupt(),
//     verify() AFTER), lane i receives data[sigma(i)] for permutation sigma;
//     the recomputed tag is L_i ^ p(d_sigma(i)) while the sender stored
//     L_sigma(i) ^ p(d_sigma(i)). The parity terms cancel, so mismatch iff
//     L_i != L_sigma(i) iff i != sigma(i) (L injective). The ONLY escape is
//     the identity permutation — verified exhaustively over all 8! = 40,320
//     permutations. Data-independent.
//   * BIT-FLIPS: caught by the aggregate word W, probability 1 (W is
//     bit-sensitive to every data bit). NOTE: W is a pure-XOR folded form and
//     is therefore permutation-INVARIANT under rotation (W' ^ W = 0 — the
//     XOR-invariance theorem, §2.1(iii)); it does NOT detect rotations. Its
//     sole prototype role is the bit-flip backstop.
//   * ALL_ZERO: caught by the per-lane tags with probability 1 - 2^-24
//     (every byte parity would have to coincidentally equal L_i).
//
// NOT covered (honest boundary, mirrors paper §6.2 / §2.3(iii)): stale-line
// replay where the *value* is correct but the *source* is wrong — needs a
// source/origin tag (fill-buffer slot ID), future work.
class CHAOSPosParity : public SimObject
{
  public:
    CHAOSPosParity(const CHAOSPosParityParams &p);
    ~CHAOSPosParity();

    // Sender side: snapshot tags for freshly-forwarded data. Call BEFORE any
    // injector corrupts it (models tagging at the send end of the bus).
    // Idempotent and deterministic.
    void tag(const uint8_t *data, unsigned size, Addr vaddr);

    // Receiver side: recompute and compare (call AFTER corruption). Returns
    // true on mismatch. Honors `action`: "count" tallies and continues
    // (observable telemetry), "panic" fails fast (the §6.1 philosophy).
    bool verify(const uint8_t *data, unsigned size, Addr vaddr);

  private:
    static uint8_t laneConst(unsigned i, unsigned tag_width);
    uint8_t laneParity(uint8_t byte) const;      // popcount1
    // Storage for the last tagged snapshot (single outstanding forward —
    // sufficient because tag()/verify() are called back-to-back around the
    // same buffer in lsq_unit.cc, so the snapshot model holds: the sender
    // snapshot is taken pre-injection and compared post-injection, within the
    // same event. DOCUMENTED LIMITATION for interleaved forwards: a silicon
    // implementation would need a small tag RAM indexed by forwarding slot.
    uint8_t tag_snapshot[16];
    unsigned tag_snapshot_size = 0;
    uint16_t word_snapshot = 0;
    Addr tag_snapshot_vaddr = 0;

    o3::CPU *cpu;
    int tag_width;
    enum class Action { Count, Panic };
    Action action_enum;
    uint64_t rng_seed;

    struct CHAOSPosParityStats : public statistics::Group {
        statistics::Scalar numTagged;
        statistics::Scalar numVerified;
        statistics::Scalar numMismatches;
        statistics::Scalar numMismatchesPanic;
        CHAOSPosParityStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSPosParityStats> stats;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_POS_PARITY_HH__
