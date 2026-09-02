#include "cpu/o3/CHAOSPosParity/CHAOSPosParity.hh"
#include "params/CHAOSPosParity.hh"

#include <cstring>

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
        if (tag_width < 3) {
            warn("CHAOSPosParity: tagWidth=%d < 3 cannot host 8 pairwise-"
                 "distinct lane constants; forcing 3.", tag_width);
            tag_width = 3;
        }
        memset(tag_snapshot, 0, sizeof(tag_snapshot));
        // Register with the CPU so lsq_unit.cc reaches this via cpu->posParity.
        cpu->posParity = this;
    }

    CHAOSPosParity::~CHAOSPosParity() = default;

    uint8_t
    CHAOSPosParity::laneConst(unsigned i, unsigned tag_width)
    {
        // Lane constants L_i = (i+1) mod 2^tag_width. For 8 lanes and
        // tag_width==3 this is a BIJECTION onto the whole 3-bit space:
        // {(i+1)&7 : i=0..7} = {1,2,3,4,5,6,7,0} = {0..7}, pairwise distinct.
        // Distinctness is the only property the rotation-detection argument
        // needs (mismatch iff L_i != L_sigma(i) iff i != sigma(i)); 0 is a
        // legal constant, so lane 7 mapping to 0 is correct, not a defect.
        // For lane counts > (2^w - 1)... with w==3 and 8 lanes the mapping is
        // exactly saturated (all 8 codewords used); more than 8 lanes would
        // need tagWidth >= ceil(log2(nch)) to keep constants distinct.
        return (uint8_t)((i + 1) & ((1u << tag_width) - 1));
    }

    uint8_t
    CHAOSPosParity::laneParity(uint8_t byte) const
    {
        // popcount mod 2 of one byte = 1 level of 7 XORs.
        byte ^= byte >> 4;
        byte ^= byte >> 2;
        byte ^= byte >> 1;
        return byte & 1;
    }

    void
    CHAOSPosParity::tag(const uint8_t *data, unsigned size, Addr vaddr)
    {
        if (stats) stats->numTagged++;
        if (size > sizeof(tag_snapshot)) size = sizeof(tag_snapshot);
        tag_snapshot_size = size;
        tag_snapshot_vaddr = vaddr;
        word_snapshot = 0;
        for (unsigned i = 0; i < size; i++) {
            tag_snapshot[i] = laneConst(i, tag_width) ^ laneParity(data[i]);
            word_snapshot ^= (uint8_t)(data[i] ^ (laneConst(i, tag_width) << 5));
        }
    }

    bool
    CHAOSPosParity::verify(const uint8_t *data, unsigned size, Addr vaddr)
    {
        if (stats) stats->numVerified++;
        // Mirror tag()'s truncation exactly: only the lanes the sender
        // snapshotted are comparable. vaddr is used for logs/panic text only
        // (it is not part of the check value).
        if (size > sizeof(tag_snapshot)) size = sizeof(tag_snapshot);
        if (size > tag_snapshot_size) size = tag_snapshot_size;
        bool mismatch = false;
        uint16_t w = 0;
        for (unsigned i = 0; i < size; i++) {
            uint8_t t = laneConst(i, tag_width) ^ laneParity(data[i]);
            if (t != tag_snapshot[i]) mismatch = true;
            w ^= (uint8_t)(data[i] ^ (laneConst(i, tag_width) << 5));
        }
        if (w != word_snapshot) mismatch = true;
        if (mismatch) {
            if (stats) stats->numMismatches++;
            DPRINTF(LSQUnit, "CHAOSPosParity: MISMATCH at vaddr=%#x size=%u\n",
                    vaddr, size);
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
