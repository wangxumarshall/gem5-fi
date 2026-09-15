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
          events_to_skip(p.eventsToSkip),
          skip_empty_pte(p.skipEmptyPte),
          kernel_walk_only(p.kernelWalkOnly),
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
        // v1.3 Phase 20 (H7 redesign)
        if (s == "two_bit_corrupt") return Mode::TwoBitCorrupt;
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

        // v1.2 Phase 17 (H7 fix): resident-PTE gate — clear_valid on an
        // EMPTY entry (0x0) is a no-op; the H7 arm needs resident PTEs.
        if (skip_empty_pte && pte_data == 0) return false;

        // v1.3 Phase 20 (H7 redesign): kernel-mode-walk filter — the
        // TTBR1 range (top bits all-ones, 0xffff... ) is the kernel
        // address space; its walks cannot take the user page-fault
        // refill path (the 0/30-panic self-heal from the v1.2 pilot).
        if (kernel_walk_only && (vaddr >> 40) != 0xffffffULL) return false;

        // v1.2 Phase 17 (H7 fix): fixed skip (driver-provided) so the
        // injection lands on a seed-dependent walk event — the pilot showed
        // 60/60 seeds hitting the SAME first-eligible (dead) event.
        if (events_to_skip > 0) { --events_to_skip; return false; }

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        uint64_t old = pte_data;
        // §2.10: bit-flip the PTE. single_bit_xor: random bit XOR.
        // clear_valid: clear the PTE valid bit (conditionalValidBit, H7).
        if (fi_mode == Mode::ClearValid) {
            pte_data &= ~((uint64_t)1);  // bit0 = valid (approx; AArch64 PTE)
        } else if (fi_mode == Mode::TwoBitCorrupt) {
            // v1.3 Phase 20 (H7 redesign): ADJACENT 2-bit corruption — the
            // SECDED detect-but-not-correct shape (a random 2-bit XOR is
            // usually non-adjacent; adjacent pairs are the realistic MBU).
            uint64_t mask = 0;
            if (fault_mask) {
                mask = fault_mask;
            } else {
                int start = (int)(rng() % 63);
                mask = (1ULL << start) | (1ULL << (start + 1));
            }
            pte_data ^= mask;
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
