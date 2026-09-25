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
          write_log(p.writeLog),
          pre_mode(p.preMode),
          agu_size_to(p.aguSizeTo)
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
        // LSU W4 A-series (03-design-matrix A01-A03)
        if (s == "a01_bit") return Mode::A01Bit;
        if (s == "a02_2bit") return Mode::A02DoubleBit;
        if (s == "a03_stuck0") return Mode::A03Stuck0;
        if (s == "a03_stuck1") return Mode::A03Stuck1;
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
        } else if (fi_mode == Mode::A01Bit) {
            // A01 (03): single-bit flip, low/mid/high band sampling
            // (VA is 48-bit in SE: low 0-15 / mid 16-39 / high 40-47).
            const uint64_t band = rng() % 3;
            const uint64_t bit = (band == 0) ? rng() % 16
                               : (band == 1) ? 16 + rng() % 24
                               : 40 + rng() % 8;
            new_vaddr = vaddr ^ (1ULL << bit);
        } else if (fi_mode == Mode::A02DoubleBit) {
            // A02 (03): two bits in the SAME event, 50% adjacent / 50%
            // non-adjacent (covers both MBU and dispersed error spaces).
            if (rng() % 2) {
                const uint64_t b = rng() % 46;
                new_vaddr = vaddr ^ ((1ULL << b) | (1ULL << (b + 1)));
            } else {
                uint64_t b1 = rng() % 48, b2 = rng() % 48;
                if (b1 == b2) b2 = (b2 + 1) % 48;
                new_vaddr = vaddr ^ ((1ULL << b1) | (1ULL << b2));
            }
        } else if (fi_mode == Mode::A03Stuck0 || fi_mode == Mode::A03Stuck1) {
            // A03 (03): one EA bit stuck-at-0/1, applied on EVERY event from
            // warm-up on (F5 semantics). A correct value already equal to
            // the stuck value is a NO-OP application — logged distinctly so
            // L5 can subtract it from injected (A03's activated 口径).
            if (f5_bit == 64) f5_bit = rng() % 48;
            const Addr mask = 1ULL << f5_bit;
            new_vaddr = (fi_mode == Mode::A03Stuck0) ? (vaddr & ~mask)
                                                     : (vaddr | mask);
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

    unsigned int
    CHAOSAddrPath::maybeCorruptPre(Addr& addr, unsigned int size, bool isLoad)
    {
        if (probability <= 0.0f) return size;

        if (lsuTrigger) {
            lsuTrigger->onAttempt();
            bool go;
            if (lsuTrigger->tier == ChaOSLsuTier::F6) {
                go = f6_pending;
                f6_pending = false;
            } else {
                go = lsuTrigger->onEligible();
            }
            if (!go) return size;
        } else {
            // Legacy gating (same shape as the post hook).
            if (max_faults != 0 && faults_injected_count >= max_faults) return size;
            if (!inWindow()) return size;
            std::uniform_real_distribution<float> pd(0.0f, 1.0f);
            if (pd(rng) > probability) return size;
        }

        const Addr old_addr = addr;
        const unsigned old_size = size;

        if (pre_mode == "a04_subst" || pre_mode == "a08_subst") {
            // A04/A08 (03): substitute another LEGAL address in the same
            // 4KiB page (16B-aligned, != original). A04's "same allocated
            // object" needs the W9 oracle object table — same-page is the
            // honest decidable proxy (both must map; SE flat space).
            const Addr page = addr & ~(Addr)0xFFF;
            Addr cand;
            do {
                cand = page | ((Addr)(rng() % 256) << 4);
            } while (cand == addr);
            addr = cand;
        } else if (pre_mode == "a05_shift") {
            // A05 (03), shift-amount substitution submodel: rotate the low
            // byte of the EA by d in [1,7] — the observable effect of a
            // wrong LSL amount on the offset bits.
            const uint64_t d = 1 + rng() % 7;
            const Addr lo = addr & 0xFF;
            addr = (addr & ~(Addr)0xFF) | ((lo << d | lo >> (8 - d)) & 0xFF);
        } else if (pre_mode == "a06_size") {
            // A06 (03): access-size substitution to another legal value
            // {1,2,4,8,16}; address unchanged. byte_enable is const at
            // this hook — size only (documented, 09 §3-W4).
            if (agu_size_to == 1 || agu_size_to == 2 || agu_size_to == 4 ||
                agu_size_to == 8 || agu_size_to == 16)
                size = (unsigned)agu_size_to;
            else
                return size;  // invalid target size — no-op, logged below
        } else if (pre_mode == "s13_store_addr") {
            // S13 (03): SQ entry address/tag single-bit flip — STORES only.
            // The corrupted address affects forwarding comparison AND the
            // final writeback destination (both consume the SQ addr field).
            if (isLoad) return size;   // L01's territory, not ours
            const uint64_t bit = rng() % 48;   // VA 48-bit
            addr = addr ^ (1ULL << bit);
        } else if (pre_mode == "l01_load_addr") {
            // L01 (03): LQ entry address/tag single-bit flip — LOADS only.
            // The corrupted address affects the conflict/violation check
            // against older stores AND the actual memory access.
            if (!isLoad) return size;  // S13's territory, not ours
            const uint64_t bit = rng() % 48;
            addr = addr ^ (1ULL << bit);
        } else {
            return size;  // unknown pre_mode — config validated in .py choices
        }

        chaosL0Register(l0_item, addr ? addr : size);
        ++l0_funnel.injected;
        ++l0_funnel.activated;
        ++faults_injected_count;
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: lsq_pushRequest_PRE"
                << ", mode=" << pre_mode
                << ", old_addr=0x" << std::hex << old_addr
                << ", new_addr=0x" << addr
                << ", old_size=" << std::dec << old_size
                << ", new_size=" << size
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return size;
    }

    void
    CHAOSAddrPath::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSAddrPath: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        // W4: exactly one hook per run — the PRE family (A04/A05/A06/A08)
        // registers on the pushRequest-entry pointer; the post family
        // (legacy + A01-A03 + LSU tiers) keeps the sendFragment pointer.
        if (pre_mode != "off")
            o3cpu->setChaosAddrPathPre(this);
        else
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
