#include "arch/arm/CHAOSPTW/CHAOSPTW.hh"

#include "arch/arm/table_walker.hh"   // WalkUnit, setChaosPTW
#include "debug/CHAOSPTW.hh"
#include "params/CHAOSPTW.hh"

namespace gem5
{

    CHAOSPTW::CHAOSPTW(const CHAOSPTWParams &p)
        : SimObject(p),
          walker(p.walker),
          fi_mode(stringToMode(p.mode)),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          fault_mask(p.faultMask),
          ptw_ecc(p.ptwEcc),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("ptw_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSPTW: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        }
    }

    CHAOSPTW::~CHAOSPTW() {}

    CHAOSPTW::Mode
    CHAOSPTW::stringToMode(const std::string &s) {
        if (s == "clear_valid") return Mode::ClearValid;
        return Mode::SingleBitXor;  // default / unknown
    }

    bool
    CHAOSPTW::inWindow() {
        Tick now = curTick();
        Tick f = first_clock * 1000;
        if (now < f) return false;
        if (last_clock != 0 && now > last_clock * 1000) return false;
        return true;
    }

    bool
    CHAOSPTW::maybeCorrupt(uint64_t &pte_data, unsigned lookup_level, Addr vaddr)
    {
        if (probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        uint64_t old = pte_data;
        // §2.10: bit-flip the PTE. single_bit_xor: random bit XOR.
        // clear_valid: clear the PTE valid bit (conditionalValidBit, H7).
        if (fi_mode == Mode::ClearValid) {
            pte_data &= ~((uint64_t)1);  // bit0 = valid (approx; AArch64 PTE)
        } else {
            uint64_t mask = fault_mask ? fault_mask : (1ULL << (rng() % 64));
            pte_data ^= mask;
        }
        // H7 ptwEcc: if ECC-on, the corrupted PTE is "detected" and the walk
        // re-fetches a clean PTE — so log but DON'T apply the corruption (the
        // ECC catches it). ECC-off: apply (spurious > 0). Honest model.
        bool applied = true;
        if (ptw_ecc) {
            pte_data = old;  // ECC catches it -> revert (spurious≈0)
            applied = false;
        }
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: ptw_doLongDescriptor, L" << lookup_level
                << ", vaddr=0x" << std::hex << vaddr
                << ", old_pte=0x" << old
                << ", new_pte=0x" << pte_data << std::dec
                << ", ptwEcc=" << (ptw_ecc ? "on" : "off")
                << ", applied=" << (applied ? "yes" : "no(ECC-caught)")
                << ", faults_injected: " << faults_injected_count
                << " (NOTE: FS-only — SE never calls doLongDescriptor)"
                << std::endl;
        }
        return applied;
    }

    void
    CHAOSPTW::startup() {
        SimObject::startup();
        // SELF-ATTACH: set the WalkUnit's chaosPTW pointer (Python config
        // passes walker=; here we wire it so doLongDescriptor reaches us).
        if (walker) {
            walker->setChaosPTW(this);
        }
    }

} // namespace gem5
