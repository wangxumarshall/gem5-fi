#include "mem/ruby/CHAOSCHI/CHAOSCHI.hh"

#include "mem/ruby/network/MessageBuffer.hh"  // MessageBuffer
#include "mem/ruby/slicc_interface/Message.hh"  // Message, MsgPtr
#include "debug/CHAOSCHI.hh"
#include "params/CHAOSCHI.hh"

namespace gem5
{

    CHAOSCHI::CHAOSCHI(const CHAOSCHIParams &p)
        : SimObject(p),
          fi_mode(stringToMode(p.mode)),
          mode_str(p.mode),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("chi_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSCHI: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        }
    }

    CHAOSCHI::~CHAOSCHI() {}

    CHAOSCHI::Mode
    CHAOSCHI::stringToMode(const std::string &s) {
        if (s == "msg_drop") return Mode::MsgDrop;
        if (s == "cross_die_msg_delay") return Mode::CrossDieMsgDelay;
        if (s == "payload_bitflip") return Mode::PayloadBitflip;
        return Mode::MsgDelay;
    }

    bool
    CHAOSCHI::inWindow() {
        Tick now = curTick();
        Tick f = first_clock * 1000;
        if (now < f) return false;
        if (last_clock != 0 && now > last_clock * 1000) return false;
        return true;
    }

    bool
    CHAOSCHI::maybeCorrupt(ruby::MessageBuffer *buf)
    {
        if (probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (!buf) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // §2.9: the MessageBuffer carries CHI directory/response messages.
        // msg_delay: delay the front message's time (it arrives later —
        //   propagation latency corruption). msg_drop: signal a drop (the
        //   caller should skip this dequeue; modeled by logging only since
        //   MessageBuffer::dequeue doesn't support drop directly — the F6
        //   delay is the realized subset here).
        // payload_bitflip: needs Ruby Message functionalWrite (E3, deferred).
        if (fi_mode == Mode::MsgDelay || fi_mode == Mode::MsgDrop ||
            fi_mode == Mode::CrossDieMsgDelay) {
            // peek the front message for logging; the actual delay is applied
            // by re-enqueueing with a later time (the caller MessageBuffer
            // handles this via its delayHead mechanism). Here we log the fault
            // and the caller applies the delay if it calls delayHead.
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: messagebuffer_dequeue, mode=" << mode_str
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        }
        return false;
    }

} // namespace gem5
