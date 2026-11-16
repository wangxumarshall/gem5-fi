#include "cpu/o3/CHAOSL1DForward/CHAOSL1DForward.hh"
#include "cpu/o3/CHAOSL1DForward/lp01_bytewise.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // o3::DynInst: pcState()/seqNum/lqIdx
#include "debug/CHAOSL1DForward.hh"
#include "sim/sim_exit.hh"
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
            // v1.1 Phase 8.2: fixed uniform skip (driver-provided,
            // chaos_event_sample.hh) overrides the legacy geometric(0.1)
            // draw; UINT64_MAX sentinel keeps legacy behavior.
            if (p.eventsToSkip != ~0ULL)
                events_to_skip = p.eventsToSkip;
            else {
                std::geometric_distribution<uint64_t> skip_dist(0.1);
                events_to_skip = skip_dist(rng);
            }
            events_to_skip_initial = events_to_skip;
            count_only = p.countOnly;
        }
    }

    CHAOSL1DForward::~CHAOSL1DForward()
    {
        // v1.1 Phase 8.2 countOnlyMode: the driver's dry-run learns
        // N_eligible from this line (campaign.py parses the log).
        if (count_only && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT=" << eligible_count
                << std::endl;
        }
    }

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
    CHAOSL1DForward::maybeCorrupt(o3::DynInst *inst, PacketPtr pkt, bool is_load,
                                  std::vector<uint8_t> *before_out,
                                  uint64_t *mask_out)
    {
        if (!cpu || probability <= 0.0f) return false;
        // Sampling-bias fix (findings.md Phase 2.2): a single fault must land
        // on a seed/ordinal-selected eligible load, not always the first one.
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;

        // LP01 eligibility (Excel: "Load（目标lqIdx）", "目标Load响应到达"):
        // a data load response only. I-fetch, SC and atomic responses are not
        // the modeled target and must not consume the ordinal/RNG stream.
        const bool eligible = pkt && pkt->hasData() && !pkt->isWrite()
            && is_load && !(pkt->req && pkt->req->isInstFetch());
        if (!eligible) return false;
        // v1.1 Phase 8.2 countOnlyMode: count eligible loads, never corrupt.
        if (count_only) { ++eligible_count; return false; }
        if (events_to_skip > 0) {
            --events_to_skip;
            return false;
        }

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) {
            // This eligible event was declined; it still occupies an ordinal.
            ++post_skip_eligible;
            return false;
        }

        // LP01 models byte lane 0 only: a random mask must pick a bit inside
        // that lane (bits 8..63 would be silently discarded).
        uint64_t mask = fault_mask ? fault_mask : (1ULL << (rng() % 8));
        if ((mask & 0xffULL) == 0)
            return false;   // not a byte-0 fault; do not count it
        unsigned sz = pkt->getSize();
        if (sz == 0) return false;
        uint8_t *data = pkt->getPtr<uint8_t>();
        // Pre-fault copy for the propagation trace (taken before the XOR).
        if (before_out) before_out->assign(data, data + sz);
        // LP01-CFG01: byte lane 0 only, bounded by size (see lp01_bytewise.hh).
        if (!chaos_lp01::corruptByte0(data, sz, mask)) return false;

        last_eligible_ordinal = chaos_lp01::eligibleOrdinal(
            events_to_skip_initial, events_to_skip) + post_skip_eligible;
        if (mask_out) *mask_out = mask;
        faults_injected_count++;
        if (write_log) {
            // v3.3.2 LP01 identity: bind the injection to the dynamic
            // instruction (PC/virtual address/LQ entry), not only to the
            // physical address. `addr=` (PA) is kept for existing parsers.
            // request_id lives in CHAOSPropagation::req_meta and is assigned
            // by the paired noteL1DForwardInjection() row emitted right
            // after this call, so it is not reachable here: it is logged as
            // 0 and the authoritative value is in inj_l1dfwd.
            const Addr pc = inst ? inst->pcState().instAddr() : 0;
            const Addr va = (pkt->req && pkt->req->hasVaddr())
                ? pkt->req->getVaddr() : 0;
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: l1d_load_complete, addr=0x" << std::hex
                << pkt->getAddr()
                << ", pa=0x" << pkt->getAddr()
                << ", va=0x" << va
                << ", pc=0x" << pc << std::dec
                << ", size=" << sz
                << ", mask=0x" << std::hex << mask << std::dec
                << ", dyn_inst_seq=" << (inst ? inst->seqNum : 0)
                << ", lq_entry_id=" << (inst ? (int64_t)inst->lqIdx : -1)
                << ", entry_generation="
                << (inst ? inst->lqEntryGeneration : 0)
                << ", request_id=0"
                << ", eligible_ordinal=" << last_eligible_ordinal
                << ", byte0_changed=1"
                << ", addr_unchanged=1, size_unchanged=1"
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
        // v1.1 Phase 8.2: print CHAOS_ELIGIBLE_COUNT at sim exit (the
        // destructor may not run before gem5's exit path tears everything
        // down; the exit callback always fires).
        if (count_only) {
            registerExitCallback([this]() {
                if (log_stream && log_stream->stream())
                    *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT="
                        << eligible_count << std::endl;
            });
        }
    }

} // namespace gem5
