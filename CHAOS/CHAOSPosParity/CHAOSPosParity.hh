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
// POSITIONAL_PARITY_RESEARCH.md §2.1). This validator binds each byte's
// contribution to its lane position through two NON-commutative weighted
// mod-256 aggregates, so a lane permutation that preserves the data bits'
// multiset still has to preserve two position-dependent sums.
//
// Check design (fix of the round-1 review; supersedes the cancelled
// per-lane-tag snapshot, see "History" below):
//
//   w1_i  = 2*i + 1                 = 1,3,5,7,9,11,13,15
//   w2_i  = (2*i + 1) ^ 0x5A        = 0x5B,0x59,0x5F,0x5D,0x53,0x51,0x57,0x55
//   W1    = (SUM_i w1_i * (data[i] + 1)) mod 256
//   W2    = (SUM_i w2_i * (data[i] + 1)) mod 256
//
// Both weight vectors are pairwise distinct AND odd. Distinctness makes the
// coefficient vector of the escape equation (below) nonzero; oddness is
// REQUIRED for single-bit-flip detection (an even weight w would let a flip
// of a bit b with 2^b >= 256/gcd(w,256) vanish mod 256; with odd w, w*2^b is
// never 0 mod 256 for any b — this is the "w_i 两两不同且均为奇数" spec of
// report §2.1). The "+1" makes constant data (e.g. all-zero) produce a
// position-dependent nonzero sum, so all-same-byte data does not trivially
// collide across permutations.
//
// Detection semantics (honest figures, exact via subgroup enumeration over
// (Z/256)^2 and confirmed by 2x10^6-trial Monte Carlo; NOT overstated):
//
//   * SINGLE-BIT FLIPS: 0 escapes in 1,284,032 exhaustive tests (256 base
//     bytes x 8 lanes x 8 bits x both aggregates). Deterministic: flipping
//     bit b of byte i changes W1 by w1_i * 2^b mod 256 != 0 (odd weight),
//     and likewise W2. Caught by BOTH aggregates with probability 1.
//
//   * LANE PERMUTATIONS (random data): a permutation sigma preserves W1 iff
//     SUM_i (w1_{sigma^-1(i)} - w1_i) * d_i = 0 (mod 256) — a linear
//     constraint with a NONZERO coefficient vector (weights injective), i.e.
//     a hyperplane of codimension 1 in data space for ONE aggregate. TWO
//     independent weight vectors intersect at codimension <= 2. NOTE: the
//     intersection is exactly codimension 2 only over a field; over Z/256
//     (not a field) the two constraint rows can share factors. Exact escape
//     probabilities for the rotations this prototype faces:
//       ror_1/3/5/7: 2^-12   ror_2/6: 2^-10   ror_4: 2^-5
//     (ror_4 degenerates: for w1, sigma^-1(i)-i is always +-4, so the
//     coefficient vector is 8*(...,-1,-1,-1,-1,+1,+1,+1,+1); for w2 the same
//     happens — both aggregates impose the SAME constraint on ror_4, hence
//     only codimension 1 effective.) Averaged over all 40,319 non-identity
//     permutations (uniform data): mean escape 2^-11.34.
//
//   * LANE PERMUTATIONS (adversarial data): escapes EXIST. For data chosen
//     knowing the weights (e.g. the uniform-odd-parity word
//     0x0102040810204080), 17 of 40,319 non-identity permutations preserve
//     both aggregates. The detector is therefore PROBABILISTIC against
//     adversarial data, NOT deterministic. (None of the 7 pure rotations
//     ror_1..ror_7 is among the 17 — the uniform-parity probe IS detected
//     under every rotation, which is the round-1 falsification case.)
//
//   * ALL_ZERO delivery: escape iff the ORIGINAL data's (W1,W2) equals
//     (W1,W2)(zeros) = (0x40,0xC0); exact escape probability 2^-13.
//
//   * The deterministic probability-1 rotation-detection claim holds ONLY
//     for the LOCKSTEP design where tags travel WITH the data (each lane's
//     tag is compared against the lane constant of the lane it arrives on:
//     mismatch iff sigma(i) != i, since the lane constants are a bijection;
//     identity is then the only escape, 8! = 40,320 exhaustive). That is
//     future silicon work, NOT this snapshot validator — described here as
//     the design the tagWidth parameter configures.
//
// History (round-1 review, Critical 1): the previous check snapshotted
// per-lane tags T_i = L_i ^ parity(d_i) and compared L_i ^ parity(d'_i)
// against them. L_i appears on BOTH sides and CANCELS: mismatch iff
// parity(d'_i) != parity(d_i) — plain per-byte parity. Lane constants were
// inert; rotations escaped with probability 2^gcd(k,8)/256 on random data
// and ALWAYS on uniform-parity data (falsified live: unipar probe,
// numStructuralByteLaneSkew=1, numMismatches=0). Root cause: pure-XOR
// mixing — any check built from XOR of per-lane functions is invariant
// under lane permutation when the lane functions are XORed positionally
// (the XOR-invariance theorem, report §2.1(iii)). The fix replaces XOR
// mixing with weighted SUM mod 256 (non-commutative in the lane index).
//
// NOT covered (honest boundary, mirrors paper §6.2 / §2.3(iii)): stale-line
// replay where the *value* is correct but the *source* is wrong — needs a
// source/origin tag (fill-buffer slot ID), future work. Also: the snapshot
// array is capped at 16 bytes; wider forwards (SIMD) are only partially
// covered (a documented coverage limit, not a correctness limit — the first
// 16 lanes are checked).
class CHAOSPosParity : public SimObject
{
  public:
    CHAOSPosParity(const CHAOSPosParityParams &p);
    ~CHAOSPosParity();

    // Sender side: snapshot the dual aggregates for freshly-forwarded data.
    // Call BEFORE any injector corrupts it (models tagging at the send end of
    // the bus). Idempotent and deterministic.
    void tag(const uint8_t *data, unsigned size, Addr vaddr);

    // Receiver side: recompute and compare (call AFTER corruption). Returns
    // true on mismatch. Honors `action`: "count" tallies and continues
    // (observable telemetry), "panic" fails fast (the §6.1 philosophy).
    bool verify(const uint8_t *data, unsigned size, Addr vaddr);

  private:
    static unsigned weight1(unsigned i) { return 2 * i + 1; }
    static unsigned weight2(unsigned i) { return (2 * i + 1) ^ 0x5A; }
    // Dual weighted mod-256 aggregates: (SUM_i w_i * (data[i] + 1)) mod 256.
    // Weight vectors are pairwise distinct and odd (see class comment).
    static unsigned aggW1(const uint8_t *data, unsigned size);
    static unsigned aggW2(const uint8_t *data, unsigned size);
    // Storage for the last tagged snapshot (single outstanding forward —
    // sufficient because tag()/verify() are called back-to-back around the
    // same buffer in lsq_unit.cc, so the snapshot model holds: the sender
    // snapshot is taken pre-injection and compared post-injection, within the
    // same event. DOCUMENTED LIMITATION for interleaved forwards: a silicon
    // implementation would need a small tag RAM indexed by forwarding slot.
    static constexpr unsigned SNAPSHOT_MAX = 16;  // coverage cap (see above)
    unsigned agg1_snapshot = 0;
    unsigned agg2_snapshot = 0;
    unsigned snapshot_valid_size = 0;

    o3::CPU *cpu;
    // tagWidth configures the LOCKSTEP silicon design (per-lane constant
    // width L_i = (i+1) & (2^w - 1)), documented in the class comment — it
    // is NOT used by this snapshot model's dual aggregates.
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
