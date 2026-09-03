#include "cpu/o3/CHAOSL1DForward/CHAOSL1DForward.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "debug/CHAOSL1DForward.hh"
#include "params/CHAOSL1DForward.hh"

namespace gem5
{

    CHAOSL1DForward::CHAOSL1DForward(const CHAOSL1DForwardParams &p)
        : SimObject(p),
          cpu(p.cpu),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          fault_mask(p.faultMask),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("l1d_fwd_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSL1DForward: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
            // Sampling-bias fix: skip a geometrically-distributed number of
            // eligible load events before the first injection (mean ~10), so
            // the single fault (maxFaults=1) lands on a seed-dependent load
            // instead of always the first eligible one.
            std::geometric_distribution<uint64_t> skip_dist(0.1);
            events_to_skip = skip_dist(rng);
        }
    }

    CHAOSL1DForward::~CHAOSL1DForward() {}

    bool
    CHAOSL1DForward::inWindow() {
        // Frequency-correct: use the CPU's actual clock period for the
        // cycles->ticks conversion (C0 2GHz=500t/cyc, C2-KP 2.6GHz~385t/cyc).
        // The old *1000 assumed 1GHz and never opened the window on C2.
        if (!cpu) return false;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;
        Tick now = curTick();
        Tick period = o3cpu->clockPeriod();
        Tick f = first_clock * period;
        if (now < f) return false;
        if (last_clock != 0 && now > last_clock * period) return false;
        return true;
    }

    bool
    CHAOSL1DForward::maybeCorrupt(PacketPtr pkt)
    {
        if (!cpu || probability <= 0.0f) return false;
        // Sampling-bias fix (findings.md Phase 2.2): the OLD code corrupted
        // the FIRST eligible load after the window opened. With a
        // deterministic instruction stream, that is the SAME dynamic
        // instruction every rep (observed: addr=0x769a0, tick=97358415
        // across ALL seeds — a squashed wrong-path load whose corruption is
        // discarded), so a 384-rep formal measured one squashed load, not
        // the post-check-escape distribution. Skip a geometric(p=0.1)
        // number of eligible events before injecting so the single fault
        // lands on a seed-dependent random eligible load.
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (pkt && pkt->hasData() && !pkt->isWrite()) {
            if (events_to_skip > 0) {
                --events_to_skip;
                return false;
            }
        }
        if (!pkt || !pkt->hasData()) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // §2.7 post-check escape: XOR a bit of the response packet data
        // (post-L1D-read, post-ECC-check). The mask covers up to 8 bytes.
        uint64_t mask = fault_mask ? fault_mask : (1ULL << (rng() % 64));
        unsigned sz = pkt->getSize();
        if (sz == 0) return false;
        uint8_t *data = pkt->getPtr<uint8_t>();
        // XOR the low 8 bytes (or fewer) of the response data.
        uint64_t *p = reinterpret_cast<uint64_t*>(data);
        size_t n = sz / 8; if (n == 0) n = 1;
        for (size_t i = 0; i < n; i++) p[i] ^= mask;

        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: l1d_load_complete, addr=0x" << std::hex
                << pkt->getAddr() << std::dec
                << ", size=" << sz
                << ", mask=0x" << std::hex << mask << std::dec
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    void
    CHAOSL1DForward::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSL1DForward: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        o3cpu->setChaosL1DFwd(this);
    }

} // namespace gem5
