#include "cpu/o3/CHAOSPosParity/CHAOSPosParity.hh"
#include "params/CHAOSPosParity.hh"

#include "base/logging.hh"
#include "cpu/o3/cpu.hh"
#include "debug/LSQUnit.hh"

namespace gem5
{

    CHAOSPosParity::CHAOSPosParity(const CHAOSPosParityParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          tag_width(p.tagWidth),
          action_enum(p.action == "panic" ? Action::Panic : Action::Count),
          rng_seed(p.rngSeed),
          stats(std::make_unique<CHAOSPosParityStats>(this))
    {
        if (!cpu) {
            throw std::runtime_error(
                "CHAOSPosParity: cpu is not an O3CPU. This validator hooks "
                "the O3 LSQ store->load forwarding path.");
        }
        // tagWidth configures the LOCKSTEP silicon variant (per-lane constant
        // width, see the class comment) — not this snapshot model's dual
        // aggregates. Kept for interface stability; validated for the
        // documented 8-lane lockstep design.
        if (tag_width < 3) {
            warn("CHAOSPosParity: tagWidth=%d < 3 cannot host 8 pairwise-"
                 "distinct lockstep lane constants; forcing 3.", tag_width);
            tag_width = 3;
        }
        // Register with the CPU so lsq_unit.cc reaches this via cpu->posParity.
        cpu->posParity = this;
    }

    CHAOSPosParity::~CHAOSPosParity() = default;

    // Weight vectors (see class comment for the full design and the honest
    // detection figures): w1_i = 2i+1 (1,3,5,7,9,11,13,15);
    // w2_i = (2i+1)^0x5A (0x5B,0x59,0x5F,0x5D,0x53,0x51,0x57,0x55).
    // Both are pairwise distinct AND odd — distinctness gives a nonzero
    // escape-hyperplane coefficient vector, oddness makes every odd weight
    // invertible mod 256 so single-byte corruptions cannot cancel.

    unsigned
    CHAOSPosParity::aggW1(const uint8_t *data, unsigned size)
    {
        // (SUM_i w1_i * (data[i] + 1)) mod 256
        unsigned acc = 0;
        for (unsigned i = 0; i < size; i++)
            acc += weight1(i) * (unsigned)(data[i] + 1);
        return acc & 0xFF;
    }

    unsigned
    CHAOSPosParity::aggW2(const uint8_t *data, unsigned size)
    {
        // (SUM_i w2_i * (data[i] + 1)) mod 256
        unsigned acc = 0;
        for (unsigned i = 0; i < size; i++)
            acc += weight2(i) * (unsigned)(data[i] + 1);
        return acc & 0xFF;
    }

    void
    CHAOSPosParity::tag(const uint8_t *data, unsigned size, Addr vaddr)
    {
        if (stats) stats->numTagged++;
        // Coverage cap: only the first SNAPSHOT_MAX lanes are checked (see
        // class comment — a documented coverage limit for wider forwards).
        if (size > SNAPSHOT_MAX) size = SNAPSHOT_MAX;
        snapshot_valid_size = size;
        agg1_snapshot = aggW1(data, size);
        agg2_snapshot = aggW2(data, size);
    }

    bool
    CHAOSPosParity::verify(const uint8_t *data, unsigned size, Addr vaddr)
    {
        if (stats) stats->numVerified++;
        // Mirror tag()'s truncation exactly: only the lanes the sender
        // snapshotted are comparable. vaddr is used for logs/panic text only
        // (it is not part of the check value).
        if (size > SNAPSHOT_MAX) size = SNAPSHOT_MAX;
        if (size > snapshot_valid_size) size = snapshot_valid_size;
        bool mismatch = false;
        if (aggW1(data, size) != agg1_snapshot) mismatch = true;
        if (aggW2(data, size) != agg2_snapshot) mismatch = true;
        if (mismatch) {
            if (stats) stats->numMismatches++;
            DPRINTF(LSQUnit, "CHAOSPosParity: MISMATCH at vaddr=%#x size=%u "
                    "(W1: %u vs snapshot %u, W2: %u vs snapshot %u)\n",
                    vaddr, size,
                    aggW1(data, size), agg1_snapshot,
                    aggW2(data, size), agg2_snapshot);
            if (action_enum == Action::Panic) {
                if (stats) stats->numMismatchesPanic++;
                panic("CHAOSPosParity: positional-parity mismatch on the "
                      "store->load forwarding path (vaddr=%#x) — fail-fast "
                      "(paper §6.1/§6.2: detection over silent correction)\n",
                      vaddr);
            }
        }
        return mismatch;
    }

    CHAOSPosParity::CHAOSPosParityStats::CHAOSPosParityStats(
            statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numTagged, statistics::units::Count::get(),
                   "Forwarding events tagged (sender side)"),
          ADD_STAT(numVerified, statistics::units::Count::get(),
                   "Forwarding events verified (receiver side)"),
          ADD_STAT(numMismatches, statistics::units::Count::get(),
                   "Positional-parity mismatches detected (D1-class "
                   "structural faults caught)"),
          ADD_STAT(numMismatchesPanic, statistics::units::Count::get(),
                   "Mismatches escalated to fail-fast panic")
    {}

} // namespace gem5
