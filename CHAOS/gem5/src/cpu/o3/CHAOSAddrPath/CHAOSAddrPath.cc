#include "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "debug/CHAOSAddrPath.hh"
#include "params/CHAOSAddrPath.hh"

namespace gem5
{

    CHAOSAddrPath::CHAOSAddrPath(const CHAOSAddrPathParams &p)
        : SimObject(p),
          cpu(p.cpu),
          fi_mode(stringToMode(p.mode)),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("addrpath_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSAddrPath: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        }
    }

    CHAOSAddrPath::~CHAOSAddrPath() {}

    CHAOSAddrPath::Mode
    CHAOSAddrPath::stringToMode(const std::string &s) {
        if (s == "low_bit_flip") return Mode::LowBitFlip;
        return Mode::Byte7Zero;  // default / unknown
    }

    bool
    CHAOSAddrPath::inWindow() {
        Tick now = curTick();
        Tick f = first_clock * 1000;
        if (now < f) return false;
        if (last_clock != 0 && now > last_clock * 1000) return false;
        return true;
    }

    bool
    CHAOSAddrPath::maybeCorrupt(RequestPtr &req)
    {
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (!req) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // §2.4 AGU address-path: corrupt the request vaddr BEFORE translateTiming.
        //   byte7_zero: clear byte 7 (canonical -> non-canonical kernel addr).
        //   low_bit_flip: XOR a low bit (sub-page address shift).
        // HONEST: SE-inert — SE phys mem from 0, only 512MiB, so byte7 zero still
        // lands in the mapped physical range (no fault). FS-only effective.
        Addr vaddr = req->getVaddr();
        Addr new_vaddr = vaddr;
        if (fi_mode == Mode::Byte7Zero) {
            new_vaddr = vaddr & ~((Addr)0xff << 56);  // clear byte 7
        } else {
            new_vaddr = vaddr ^ (1ULL << (rng() % 16));  // low-bit flip
        }
        if (new_vaddr == vaddr) return false;
        req->setVaddr(new_vaddr);
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: lsq_sendFragmentToTranslation"
                << ", mode=" << (fi_mode == Mode::Byte7Zero ? "byte7_zero" : "low_bit_flip")
                << ", old_vaddr=0x" << std::hex << vaddr
                << ", new_vaddr=0x" << new_vaddr << std::dec
                << ", faults_injected: " << faults_injected_count
                << " (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)"
                << std::endl;
        }
        return true;
    }

    void
    CHAOSAddrPath::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSAddrPath: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        o3cpu->setChaosAddrPath(this);
    }

} // namespace gem5
