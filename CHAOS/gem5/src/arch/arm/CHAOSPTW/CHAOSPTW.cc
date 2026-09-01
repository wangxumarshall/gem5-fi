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
          clear_valid_bit(p.clearValidBit),
          conditional_valid_bit(p.conditionalValidBit),
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
        // Count every call to the hook once the injector is active, BEFORE any
        // gating (first_clock/max_faults/prob). This distinguishes "PTW walk
        // happened (hook called)" from "walk happened but prob did not select
        // it (numFaultsInjected=0)" — essential to diagnose H7's spurious rate
        // when PTW walk density is low (early FS, pre-MMU-on has few walks).
        stats->numHooksCalled++;
        // NOTE (adversarial-review finding, NOT fixed in code): the clock gating
        // below uses Cycles(curTick()) — raw ticks cast to Cycles, which on a
        // 1 GHz clock is ~1000x the true cycle count. This makes first_clock/
        // last_clock gate ~1000x too early vs D1/D2's cpu->curCycle(). All
        // H6/H7 experiments in this paper use first_clock=0 (gating inert),
        // so this does NOT affect any reported result. A proper fix requires
        // exposing a clock-domain accessor on CHAOSPTW (it has only an mmu
        // pointer, no cpu; SimObject::ticksToCycles is not accessible here)
        // — left as a known limitation for any first_clock>0 experiment.
        Cycles cur = Cycles(curTick() >> 0);
        if (cur < first_clock) return;
        if (last_clock != Cycles(0) && cur > last_clock) return;
        if (max_faults != 0 && faults_injected_count >= max_faults) return;

        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return;
        if (size == 0) return;

        // H7: ECC corrects single-bit flips; only >=2-bit (uncorrectable) survive.
        // clearValidBit (AND ~0x3) is a 2-bit clear -> uncorrectable, bypasses ECC.
        // conditionalValidBit is a SINGLE-bit XOR (bit0) -> ECC SHOULD correct it
        // (ECC-on -> benign/no spurious; ECC-off -> invalid/spurious). So
        // conditionalValidBit must NOT bypass ECC — only clear_valid_bit does.
        if (!clear_valid_bit && ptw_ecc && num_bits < 2) {
            stats->numBenignFlips++;
            return;
        }

        uint64_t orig = 0;
        std::memcpy(&orig, data, size);

        if (conditional_valid_bit) {
            // P3c: single-bit XOR bit0, ONLY on block descriptors (low2=0b01).
            // 0b01 ^ 0b01 = 0b00 (invalid) -> spurious. Single-bit so ECC-on
            // corrects it (no spurious), ECC-off leaves it invalid (spurious).
            // This is the faithful within-experiment H7 ECC contrast. Non-0b01
            // descriptors are skipped (no corruption) so we don't perturb tables.
            if (size >= 1 && (data[0] & 0x3) == 0x1) {
                data[0] ^= 0x1;
            } else {
                // Not a block descriptor — skip injection, count as benign (no
                // fault manufactured this walk).
                stats->numBenignFlips++;
                return;
            }
        } else if (clear_valid_bit) {
            // Force-clear descriptor type bits[1:0] (byte 0, low 2 bits) -> 0b00
            // (invalid). This RELIABLY manufactures an invalid PTE regardless of
            // the original descriptor type (0b01 block / 0b11 table -> 0b00),
            // unlike XOR which only invalidates one type. Models D3's transient
            // walk-failure (invalid readout -> fault -> retry reads correct value).
            if (size >= 1) data[0] &= (uint8_t)~0x3;
        } else {
            int off = byte_offset;
            if (off < 0) {
                std::uniform_int_distribution<int> bd(0, (int)size - 1);
                off = bd(rng);
            }
            if (off >= (int)size) off = (int)size - 1;

            int mask = fault_mask ? (int)(fault_mask & 0xff)
                                  : generateRandomMask(num_bits);
            data[off] ^= (uint8_t)mask;
        }
        uint64_t corr = 0;
        std::memcpy(&corr, data, size);

        bool became_invalid = (size == 8) ? longDescInvalid(corr)
                                          : shortDescInvalid((uint32_t)corr);
        stats->numFaultsInjected++;
        ++faults_injected_count;
        if (became_invalid) stats->numSpuriousFaults++;
        else stats->numBenignFlips++;
        writeLog(desc_addr, orig, corr, became_invalid);
        DPRINTF(CHAOSPTW, "CHAOSPTW: corrupted desc @%#x (%#lx->%#lx) "
                "invalid=%d clearValidBit=%d\n", desc_addr, orig, corr,
                became_invalid, clear_valid_bit ? 1 : 0);
    }

    CHAOSPTW::Stats::Stats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numHooksCalled, statistics::units::Count::get(),
                   "Times the PTW-read hook was called (D3; every descriptor "
                   "fetch while injector active, before prob/first-clock gating)"),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total PTW descriptor faults injected (D3)"),
          ADD_STAT(numSpuriousFaults, statistics::units::Count::get(),
                   "Flips that produced an invalid PTE (-> spurious fault)"),
          ADD_STAT(numBenignFlips, statistics::units::Count::get(),
                   "Flips the PTE survived (ECC-corrected or no-op)")
    {}

} // namespace gem5
