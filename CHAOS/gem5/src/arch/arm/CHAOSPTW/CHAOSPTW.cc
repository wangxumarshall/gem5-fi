#include "arch/arm/CHAOSPTW/CHAOSPTW.hh"
#include "params/CHAOSPTW.hh"
#include "arch/arm/mmu.hh"
#include "debug/CHAOSPTW.hh"
#include <iostream>
#include <fstream>
#include <cstring>

namespace gem5
{

    CHAOSPTW::CHAOSPTW(const CHAOSPTWParams &p)
        : SimObject(p),
          mmu(dynamic_cast<ArmISA::MMU *>(p.mmu)),
          probability(p.probability),
          num_bits(p.bitsToChange),
          fault_mask(p.faultMask),
          byte_offset(p.byteOffset),
          ptw_ecc(p.ptwEcc),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          rng(rng_seed != 0 ? rng_seed : [](){ std::random_device r; return r(); }()),
          log_stream(nullptr),
          stats(nullptr)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("ptw_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSPTW: Could not open log file");
            stats = std::make_unique<Stats>(this);
            if (mmu) mmu->setPtwInj(this);
            else warn("CHAOSPTW: no mmu attached; injector will be inert.");
        }
    }

    CHAOSPTW::~CHAOSPTW() {}

    int
    CHAOSPTW::generateRandomMask(int bits_to_change)
    {
        int mask = 0;
        std::uniform_int_distribution<int> bitDist(0, 7);
        while (bits_to_change-- > 0) mask |= (1 << bitDist(rng));
        return mask;
    }

    void
    CHAOSPTW::writeLog(Addr desc_addr, uint64_t orig, uint64_t corr,
                       bool became_invalid)
    {
        if (!write_log) return;
        *(log_stream->stream())
            << "Tick: " << curTick()
            << ", Site: ptw_descriptor_read"
            << ", DescAddr: 0x" << std::hex << desc_addr
            << ", Orig: 0x" << orig
            << ", Corrupted: 0x" << corr
            << ", BecameInvalid: " << (became_invalid ? 1 : 0)
            << ", EccModel: " << (ptw_ecc ? 1 : 0)
            << std::dec << std::endl;
    }

    static bool longDescInvalid(uint64_t v) { return (v & 0x3) == 0; }
    static bool shortDescInvalid(uint32_t v) { return (v & 0x1) == 0; }

    void
    CHAOSPTW::corruptDescriptor(uint8_t *data, unsigned size, Addr desc_addr)
    {
        if (probability <= 0.0f) return;
        Cycles cur = Cycles(curTick() >> 0);
        if (cur < first_clock) return;
        if (last_clock != Cycles(0) && cur > last_clock) return;
        if (max_faults != 0 && faults_injected_count >= max_faults) return;

        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return;
        if (size == 0) return;

        // H7: ECC corrects single-bit flips; only >=2-bit (uncorrectable) survive.
        if (ptw_ecc && num_bits < 2) {
            stats->numBenignFlips++;
            return;
        }

        int off = byte_offset;
        if (off < 0) {
            std::uniform_int_distribution<int> bd(0, (int)size - 1);
            off = bd(rng);
        }
        if (off >= (int)size) off = (int)size - 1;

        int mask = fault_mask ? (int)(fault_mask & 0xff)
                              : generateRandomMask(num_bits);

        uint64_t orig = 0;
        std::memcpy(&orig, data, size);
        data[off] ^= (uint8_t)mask;
        uint64_t corr = 0;
        std::memcpy(&corr, data, size);

        bool became_invalid = (size == 8) ? longDescInvalid(corr)
                                          : shortDescInvalid((uint32_t)corr);
        stats->numFaultsInjected++;
        ++faults_injected_count;
        if (became_invalid) stats->numSpuriousFaults++;
        else stats->numBenignFlips++;
        writeLog(desc_addr, orig, corr, became_invalid);
        DPRINTF(CHAOSPTW, "CHAOSPTW: flipped byte %d mask %#x of desc "
                "@%#x (%#lx->%#lx) invalid=%d\n", off, mask, desc_addr,
                orig, corr, became_invalid);
    }

    CHAOSPTW::Stats::Stats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total PTW descriptor faults injected (D3)"),
          ADD_STAT(numSpuriousFaults, statistics::units::Count::get(),
                   "Flips that produced an invalid PTE (-> spurious fault)"),
          ADD_STAT(numBenignFlips, statistics::units::Count::get(),
                   "Flips the PTE survived (ECC-corrected or no-op)")
    {}

} // namespace gem5
