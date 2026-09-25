#include "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "debug/CHAOSAddrPath.hh"
#include "params/CHAOSAddrPath.hh"
#include "sim/sim_exit.hh"        // registerExitCallback (W2 summary line)

namespace gem5
{

    CHAOSAddrPath *CHAOSAddrPath::f6Consumer = nullptr;

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
        if (p.lsuTier != "off") {
            lsuTrigger = new ChaOSLsuTrigger(tierFromString(p.lsuTier),
                                             rng_seed ? rng_seed : 1,
                                             p.lsuWarmupEvents,
                                             p.lsuSpanEvents,
                                             eventFromString(p.lsuF6Event));
        }
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

    ChaOSLsuTier
    CHAOSAddrPath::tierFromString(const std::string &s) {
        if (s == "F0") return ChaOSLsuTier::F0;
        if (s == "F1") return ChaOSLsuTier::F1;
        if (s == "F2") return ChaOSLsuTier::F2;
        if (s == "F3") return ChaOSLsuTier::F3;
        if (s == "F4") return ChaOSLsuTier::F4;
        if (s == "F5") return ChaOSLsuTier::F5;
        if (s == "F6") return ChaOSLsuTier::F6;
        panic("CHAOSAddrPath: unknown lsuTier '%s'\n", s);
    }

    ChaOSLsuEvent
    CHAOSAddrPath::eventFromString(const std::string &s) {
        if (s == "tlb_hit") return ChaOSLsuEvent::TlbHit;
        if (s == "dirty_eviction") return ChaOSLsuEvent::DirtyEviction;
        if (s == "cas_success") return ChaOSLsuEvent::CasSuccess;
        return ChaOSLsuEvent::SqForward;  // sq_forward / default
    }

    void
    CHAOSAddrPath::f6Thunk(ChaOSLsuEvent ev) {
        // Single-consumer F6 notify (chaos_lsu_trigger.hh). The trigger's
        // onF6Event() both filters the event type and enforces once-ever.
        if (f6Consumer && f6Consumer->lsuTrigger &&
            f6Consumer->lsuTrigger->f6_event == ev &&
            f6Consumer->lsuTrigger->onF6Event())
            f6Consumer->f6_pending = true;  // fire at the next eligible hook
    }

    bool
    CHAOSAddrPath::inWindow() {
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
    CHAOSAddrPath::maybeCorrupt(RequestPtr &req)
    {
        if (!cpu || probability <= 0.0f) return false;
        if (!req) return false;

        if (lsuTrigger) {
            // LSU W2 path (05 r2-r8): event-normalized trigger owns the
            // warm-up/repetition/max-faults semantics; the cycle window and
            // per-event probability roll do NOT apply on this path.
            lsuTrigger->onAttempt();
            bool go;
            if (lsuTrigger->tier == ChaOSLsuTier::F6) {
                go = f6_pending;
                f6_pending = false;
            } else {
                go = lsuTrigger->onEligible();
            }
            if (!go) return false;
        } else {
            // Legacy cycle-window path (KP track) — byte-identical.
            if (max_faults != 0 && faults_injected_count >= max_faults) return false;
            if (!inWindow()) return false;

            std::uniform_real_distribution<float> pd(0.0f, 1.0f);
            if (pd(rng) > probability) return false;
        }

        // §2.4 AGU address-path: corrupt the request vaddr BEFORE translateTiming.
        //   byte7_zero: clear byte 7 (canonical -> non-canonical kernel addr).
        //   low_bit_flip: XOR a low bit (sub-page address shift).
        // HONEST: SE-inert — SE phys mem from 0, only 512MiB, so byte7 zero still
        // lands in the mapped physical range (no fault). FS-only effective.
        Addr vaddr = req->getVaddr();
        Addr new_vaddr = vaddr;
        if (fi_mode == Mode::Byte7Zero) {
            new_vaddr = vaddr & ~((Addr)0xff << 56);  // clear byte 7
        } else if (lsuTrigger && lsuTrigger->tier == ChaOSLsuTier::F5) {
            // LSU F5 (05 r8): "每次运行仅选一个 bit/字段" — ONE fixed bit per
            // run, stuck from the first post-warm-up eligible event on. A
            // per-event random bit (the legacy path) instead aliases each
            // access unpredictably and trips packet-offset assertions.
            if (f5_bit == 64) f5_bit = rng() % 16;
            new_vaddr = vaddr ^ (1ULL << f5_bit);
        } else {
            new_vaddr = vaddr ^ (1ULL << (rng() % 16));  // low-bit flip
        }
        if (new_vaddr == vaddr) return false;
        req->setVaddr(new_vaddr);
        // W3 L0: register the injected item + local funnel accounting. The
        // trigger-mirrored counts are taken at EXIT (see the exit callback)
        // — mirroring at injection time would snapshot mid-run values.
        // activated: this hook corrupts the request that translateTiming
        // consumes next — count the item consumed (.hh approximation note).
        chaosL0Register(l0_item, new_vaddr);
        ++l0_funnel.injected;
        ++l0_funnel.activated;
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
        if (lsuTrigger) {
            if (lsuTrigger->tier == ChaOSLsuTier::F6) {
                f6Consumer = this;
                chaosLsuF6Notify = &CHAOSAddrPath::f6Thunk;
            }
            // W2 funnel summary (attempted/eligible/injected; activated is
            // the W3 L0 read-back layer's verdict — R2 ruling) + W3 L0 lines
            // (chaos_l0 discipline: to the LOG FILE, stdout stays stable).
            registerExitCallback([this]() {
                if (lsuTrigger) {
                    lsuTrigger->summary("CHAOSAddrPath");
                    // Mirror the trigger's FINAL counts here (exit time), so
                    // the funnel line and the summary line always agree.
                    l0_funnel.attempted = lsuTrigger->attempted;
                    l0_funnel.eligible  = lsuTrigger->eligible;
                } else {
                    l0_funnel.attempted = l0_funnel.injected;
                    l0_funnel.eligible  = l0_funnel.injected;
                }
                if (write_log && log_stream && log_stream->stream()) {
                    *(log_stream->stream()) << chaosL0Line("CHAOSAddrPath",
                                                           l0_item)
                                            << std::endl
                                            << l0_funnel.line("CHAOSAddrPath")
                                            << std::endl;
                }
            });
        }
    }

} // namespace gem5
