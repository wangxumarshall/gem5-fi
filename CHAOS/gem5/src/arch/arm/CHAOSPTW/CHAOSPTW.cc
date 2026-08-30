#include "arch/arm/CHAOSPTW/CHAOSPTW.hh"
#include "params/CHAOSPTW.hh"
#include "arch/arm/mmu.hh"
#include "base/trace.hh"
#include "debug/CHAOSPTW.hh"
#include "sim/core.hh"  // curTick() (D1-style tick window)

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
          clear_valid_bit(p.clearValidBit),
          ptw_ecc(p.ptwEcc),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          rng([this]() {
              std::random_device local_rd;
              return rng_seed != 0 ? std::mt19937(rng_seed) : std::mt19937(local_rd());
          }()),
          log_stream(nullptr),
          stats(nullptr)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("ptw_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSPTW: Could not open log file");
            }
            stats = std::make_unique<Stats>(this);
            // SELF-ATTACH: register on the MMU so table_walker.cc can reach
            // this injector via mmu->getPtwInj(). mmu was passed as a Param.
            if (mmu) {
                mmu->setPtwInj(this);
            } else {
                warn("CHAOSPTW: no mmu attached; injector will be inert.\n");
            }
        }
    }

    void
    CHAOSPTW::startup()
    {
        // D1-style: snapshot firstClock/lastClock as SIM TICKS (curTick domain).
        // The table walker is not a ClockedObject; ticks are the only reachable
        // time base. last_clock==0 means unrestricted.
        first_tick = (Tick)first_clock;
        last_tick = (last_clock == Cycles(0)) ? (Tick)0 : (Tick)last_clock;
    }

    CHAOSPTW::~CHAOSPTW() {}

    uint64_t
    CHAOSPTW::generateRandomMask(int bits_to_change)
    {
        // 8-bit mask (applied to one byte of the descriptor).
        uint64_t mask = 0;
        std::uniform_int_distribution<int> bitDist(0, 7);
        while (bits_to_change-- > 0) mask |= (1ULL << bitDist(rng));
        return mask;
    }

    void
    CHAOSPTW::writeLog(Addr desc_addr, uint64_t orig, uint64_t corr,
                       bool became_invalid, bool ecc_corrected)
    {
        if (!write_log) return;
        *(log_stream->stream())
            << "Tick: " << curTick()
            << ", Site: ptw_descriptor_read"
            << ", DescAddr: 0x" << std::hex << desc_addr
            << ", Orig: 0x" << orig
            << ", Corrupted: 0x" << corr
            << ", BecameInvalid: " << (became_invalid ? 1 : 0)
            << ", EccCorrected: " << (ecc_corrected ? 1 : 0)
            << ", EccModel: " << (ptw_ecc ? 1 : 0)
            << ", ClearValidBit: " << (clear_valid_bit ? 1 : 0)
            << std::dec << std::endl;
    }

    static bool longDescInvalid(uint64_t v) { return (v & 0x3) == 0; }
    static bool shortDescInvalid(uint32_t v) { return (v & 0x1) == 0; }
    static int popcount64(uint64_t v) { return __builtin_popcountll(v); }

    void
    CHAOSPTW::corruptDescriptor(uint8_t *data, unsigned size, Addr desc_addr)
    {
        if (probability <= 0.0f) return;
        // D1-style tick window (curTick, NOT cpu->curCycle).
        Tick now = curTick();
        if (now < first_tick) return;
        if (last_tick != 0 && now > last_tick) return;
        if (max_faults != 0 && faults_injected_count >= max_faults) return;

        // Probability gate: per-descriptor-fetch Bernoulli. >= for D5 consistency.
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return;
        if (size == 0) return;

        uint64_t orig = 0;
        std::memcpy(&orig, data, size);

        // clearValidBit: force-clear descriptor valid bits (bits[1:0] for long,
        // bit[0] for short) — a 2-bit clear that is uncorrectable by ECC,
        // reliably manufacturing spurious translation faults (core179's 73
        // spurious ESR=0x96000044). Takes precedence over the bit-flip path.
        if (clear_valid_bit) {
            uint64_t clear_mask = (size == 8) ? 0x3ULL : 0x1ULL;
            uint64_t old_val = 0;
            std::memcpy(&old_val, data, size);
            uint64_t new_val = old_val & ~clear_mask;
            std::memcpy(data, &new_val, size);
            uint64_t corr = 0;
            std::memcpy(&corr, data, size);
            bool became_invalid = (size == 8) ? longDescInvalid(corr)
                                              : shortDescInvalid((uint32_t)corr);
            stats->numFaultsInjected++;
            ++faults_injected_count;
            if (became_invalid) stats->numSpuriousFaults++;
            else stats->numBenignFlips++;
            writeLog(desc_addr, orig, corr, became_invalid, false);
            DPRINTF(CHAOSPTW, "CHAOSPTW: clearValidBit desc @%#x "
                    "(%#lx->%#lx) invalid=%d\n", desc_addr, orig, corr,
                    became_invalid);
            return;
        }

        // Bit-flip path. Choose the byte to flip.
        int off = byte_offset;
        if (off < 0) {
            std::uniform_int_distribution<int> bd(0, (int)size - 1);
            off = bd(rng);
        }
        if (off >= (int)size) off = (int)size - 1;

        uint64_t mask = fault_mask ? (fault_mask & 0xff)
                                   : generateRandomMask(num_bits);
        if (mask == 0) return;

        // H7 self-variable: ECC corrects single-bit flips; only >=2-bit survive.
        int flips = popcount64(mask);
        if (ptw_ecc && flips < 2) {
            stats->numEccCorrected++;
            if (write_log) {
                *(log_stream->stream())
                    << "Tick: " << curTick()
                    << " ECC-corrected single-bit flip (mask=0x" << std::hex
                    << mask << std::dec << ") — no spurious.\n";
            }
            return;
        }

        data[off] ^= (uint8_t)mask;
        uint64_t corr = 0;
        std::memcpy(&corr, data, size);

        bool became_invalid = (size == 8) ? longDescInvalid(corr)
                                          : shortDescInvalid((uint32_t)corr);
        stats->numFaultsInjected++;
        ++faults_injected_count;
        if (became_invalid) stats->numSpuriousFaults++;
        else stats->numBenignFlips++;
        writeLog(desc_addr, orig, corr, became_invalid, false);
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
                   "Flips the PTE survived (no invalid)"),
          ADD_STAT(numEccCorrected, statistics::units::Count::get(),
                   "Single-bit flips corrected by ptwEcc (H7: ECC-on suppresses)")
    {}

} // namespace gem5
