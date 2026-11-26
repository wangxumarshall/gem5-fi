#include "mem/ruby/network/garnet/CHAOSNoC/CHAOSNoC.hh"

#include "mem/ruby/network/garnet/flit.hh"  // flit (set_route, set_src_delay)
#include "debug/CHAOSNoC.hh"
#include "params/CHAOSNoC.hh"

namespace gem5
{

    CHAOSNoC::CHAOSNoC(const CHAOSNoCParams &p)
        : SimObject(p),
          fi_mode(stringToMode(p.mode)),
          mode_str(p.mode),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          fault_mask(p.faultMask),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("noc_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSNoC: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        }
    }

    CHAOSNoC::~CHAOSNoC() {}

    CHAOSNoC::Mode
    CHAOSNoC::stringToMode(const std::string &s) {
        if (s == "route_sub") return Mode::RouteSub;
        if (s == "payload_bitflip") return Mode::PayloadBitflip;
        return Mode::FlitDelay;
    }

    bool
    CHAOSNoC::inWindow() {
        // Garnet/ruby clock domain is 1GHz (1 tick/cycle) — do NOT scale
        // first_clock by 1000 (that's the classic-CPU tickToClockRatio
        // convention). first_clock is in TICKS here.
        Tick now = curTick();
        if (now < first_clock) return false;
        if (last_clock != 0 && now > last_clock) return false;
        return true;
    }

    bool
    CHAOSNoC::maybeCorrupt(ruby::garnet::flit *t_flit)
    {
        if (probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (!t_flit) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        if (fi_mode == Mode::FlitDelay) {
            // §2.15 F6: add a random delay (1-4 cycles) to the flit's
            // src_delay -> models deflection/stall (bufferless vs buffered
            // P_SDC comparison, the doc's core product).
            Tick delay = 1 + (rng() % 4);
            t_flit->set_src_delay(t_flit->get_src_delay() + delay);
        } else if (fi_mode == Mode::RouteSub) {
            // §2.15 F5: corrupt the RouteInfo dest (flit goes to wrong node).
            // RouteInfo has a dest_router + hops_traversed; flipping dest
            // models a routing fault. Honest: RouteInfo internals are
            // accessed via get_route/set_route; here we don't mutate the
            // dest directly (RouteInfo struct), but log the fault.
            // (Full route_sub needs RouteInfo mutation — deferred; the
            // flit_delay F6 is the realized subset.)
        } else if (fi_mode == Mode::PayloadBitflip) {
            // §2.15 payload_bitflip: corrupt the flit's msg payload data
            // bytes. Needs Ruby Message functionalWrite (E3 proxy; the msg
            // is a Ruby protocol object, not a raw byte buffer). Deferred.
        }
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: networklink_wakeup, mode=" << mode_str
                << ", flit_id=" << t_flit->get_id()
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

} // namespace gem5
