#include "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"

#include <string>

#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"  // [LSU][OBS-L3] funnel notify
#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // [MDSPEC][R4-5.8] A07 ready hook (DynInst)
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
          agu_size_to(p.aguSizeTo),
          agu_size_to_load(p.aguSizeToLoad),
          be_mode(p.beMode),
          agu_ready_mode(p.aguReadyMode),
          agu_ready_delay_cycles(p.aguReadyDelayCycles),
          aguResumeEvent([this] { this->resumeDeferredAgu(); },
                         name() + ".aguResume")
    {
        // [MDSPEC][R4-5.8] A07 config validation — LOUD refusals, no silent
        // fallback (C11/C12 discipline): the ready-delay mode is
        // LSU-trigger-native (the cycle-window legacy path has no event
        // denominator at the ready point), takes exactly one hook per run
        // (W1-⑦: agu_ready_mode and the PRE family are mutually
        // exclusive), and the delay is a positive bound (0 = no-op, the
        // spec's "延后1周期" is the default and the campaign-pinned value).
        if (agu_ready_mode != "off") {
            if (agu_ready_mode != "a07b_ready_delay")
                panic("CHAOSAddrPath: unknown agu_ready_mode '%s' "
                      "(off | a07b_ready_delay)\n", agu_ready_mode.c_str());
            if (p.lsuTier == "off")
                panic("CHAOSAddrPath: agu_ready_mode requires --addrpath_"
                      "lsu_tier (A07 is LSU-trigger-native; the legacy "
                      "cycle-window path is not offered at the ready "
                      "hook)\n");
            if (pre_mode != "off")
                panic("CHAOSAddrPath: agu_ready_mode and agu_pre_mode are "
                      "mutually exclusive (one hook per run, W1-⑦ "
                      "discipline)\n");
            if (agu_ready_delay_cycles < 1)
                panic("CHAOSAddrPath: agu_ready_delay_cycles must be >= 1 "
                      "(A07-b bounded delay; 0 is a no-op)\n");
        }
        if (p.lsuTier != "off") {
            lsuTrigger = new ChaOSLsuTrigger(tierFromString(p.lsuTier),
                                             rng_seed ? rng_seed : 1,
                                             p.lsuWarmupEvents,
                                             p.lsuSpanEvents,
                                             eventFromString(p.lsuF6Event));
        }
        // [LSU][P4-F6] F6 dual-track mode parse (unknown value = loud panic,
        // no silent fallback to either track).
        if (p.f6Mode == "early_stress") {
            f6_steady_state = false;
        } else if (p.f6Mode == "steady_state") {
            f6_steady_state = true;
        } else {
            panic("CHAOSAddrPath: unknown f6Mode '%s' "
                  "(early_stress | steady_state)\n", p.f6Mode);
        }
        // [MDSPEC][R4-6-A06] A06-b loud refusals (C11/C12 discipline: an
        // unknown selector must never silently degrade to "off"). The load
        // size leg needs no runtime validation here: agu_size_to_load is
        // validated per event by a06LoadSize (declines are counted, and
        // 0 = "disabled" is a legitimate configuration).
        if (be_mode != "off" && be_mode != "observe"
            && be_mode != "shift_mid") {
            panic("CHAOSAddrPath: unknown be_mode '%s' "
                  "(off | observe | shift_mid)\n", be_mode.c_str());
        }
        if (be_mode != "off" && pre_mode != "a06_size")
            panic("CHAOSAddrPath: be_mode requires pre_mode=a06_size (A06-b "
                  "is a sub-fault of the same A06 model, and one sample must "
                  "carry one fault — 03 sheet: 不在同一样本叠加)\n");
        if (probability > 0.0f) {
            log_stream = simout.create("addrpath_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSAddrPath: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        }
        // [LSU][P4-F6S] steady-state: pre-draw the target occurrence AFTER
        // seeding (one draw, fixed for the run -> same seed = same target).
        // warmup/span come from the trigger (lsuWarmupEvents/lsuSpanEvents);
        // a warmup beyond the run's event supply means NO injection ever.
        if (lsuTrigger && lsuTrigger->tier == ChaOSLsuTier::F6 &&
            f6_steady_state) {
            const uint64_t warmup = lsuTrigger->warmup_events;
            const uint64_t span =
                lsuTrigger->span_events ? lsuTrigger->span_events : 1;
            f6_target_occurrence = warmup + 1 + rng() % span;
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
            f6Consumer->lsuTrigger->f6_event == ev) {
            // [LSU][P4-F6S] steady_state: count matching events, skip the
            // golden-profiling warm-up, fire ONLY at the pre-drawn target
            // occurrence (see ctor). If the stream ends first, no injection
            // — NEVER falls back to early semantics. early_stress (default)
            // is byte-identical to the legacy first-occurrence behavior.
            if (f6Consumer->f6_steady_state) {
                ++f6Consumer->f6_events_matched;
                if (f6Consumer->f6_events_matched <
                    f6Consumer->f6_target_occurrence)
                    return;
            }
            if (f6Consumer->lsuTrigger->onF6Event()) {
                // early_stress fires at the 1st occurrence; steady_state at
                // the target occurrence. Freeze the occurrence AT fire time —
                // f6_events_matched keeps counting past it (more events can
                // occur before the next hook call consumes f6_pending).
                f6Consumer->f6_fired_occurrence =
                    f6Consumer->f6_steady_state
                        ? f6Consumer->f6_events_matched : 1;
                f6Consumer->f6_pending = true;  // fire at the next eligible hook
            }
        }
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
            ++obs_post_fired;   // [LSU][OBS-2]
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
        //
        // [LSU][P4-FIX-GEOM] cache-line geometry guard (2026-10-15 audit
        // root cause B): this hook runs AFTER the LSQ split the request into
        // <=64B fragments, so a flipped vaddr whose (offset + fragment size)
        // crosses a 64B line violates BaseCache::satisfyRequest's pkt
        // invariant (41 asserts in the batch). Random-bit modes resample
        // (<=16 draws, RNG order unchanged for a legal first draw); fixed-bit
        // modes (F5 per-run bit / A03 stuck) check once and decline this
        // event, preserving the one-fixed-bit-per-run contract. A decline is
        // NOT counted as injected/activated (the trigger already fired —
        // obs_post_geomreject counts the phantom, F-049 decline style).
        Addr vaddr = req->getVaddr();
        Addr new_vaddr = vaddr;
        const unsigned frag_sz = req->getSize();
        auto geomLegal = [frag_sz](Addr a) { return (a & 63) + frag_sz <= 64; };
        unsigned geom_candidates = 1, geom_rejects = 0;   // draws taken / illegal draws
        bool geom_failed = false;
        // [LSU][P4-FIX-GEOM] true mode label (E-class audit finding: the
        // translate-site log hardcoded "low_bit_flip" for every mode).
        const char *mode_name = "low_bit_flip";
        switch (fi_mode) {
          case Mode::Byte7Zero:     mode_name = "byte7_zero"; break;
          case Mode::LowBitFlip:    mode_name = "low_bit_flip"; break;
          case Mode::A01Bit:        mode_name = "a01_bit"; break;
          case Mode::A02DoubleBit:  mode_name = "a02_2bit"; break;
          case Mode::A03Stuck0:     mode_name = "a03_stuck0"; break;
          case Mode::A03Stuck1:     mode_name = "a03_stuck1"; break;
        }
        if (fi_mode == Mode::Byte7Zero) {
            new_vaddr = vaddr & ~((Addr)0xff << 56);  // clear byte 7 (low bits unchanged — always legal)
        } else if (fi_mode == Mode::A01Bit) {
            // A01 (03): single-bit flip, low/mid/high band sampling
            // (VA is 48-bit in SE: low 0-15 / mid 16-39 / high 40-47).
            for (geom_candidates = 0; geom_candidates < 16;
                 ++geom_candidates) {
                const uint64_t band = rng() % 3;
                const uint64_t bit = (band == 0) ? rng() % 16
                                   : (band == 1) ? 16 + rng() % 24
                                   : 40 + rng() % 8;
                new_vaddr = vaddr ^ (1ULL << bit);
                if (new_vaddr != vaddr && geomLegal(new_vaddr)) break;
                ++geom_rejects;
            }
            geom_failed = (geom_candidates == 16);
            if (!geom_failed) ++geom_candidates;   // draws taken (loop index -> count)
        } else if (fi_mode == Mode::A02DoubleBit) {
            // A02 (03): two bits in the SAME event, 50% adjacent / 50%
            // non-adjacent (covers both MBU and dispersed error spaces).
            for (geom_candidates = 0; geom_candidates < 16;
                 ++geom_candidates) {
                if (rng() % 2) {
                    const uint64_t b = rng() % 46;
                    new_vaddr = vaddr ^ ((1ULL << b) | (1ULL << (b + 1)));
                } else {
                    uint64_t b1 = rng() % 48, b2 = rng() % 48;
                    if (b1 == b2) b2 = (b2 + 1) % 48;
                    new_vaddr = vaddr ^ ((1ULL << b1) | (1ULL << b2));
                }
                if (new_vaddr != vaddr && geomLegal(new_vaddr)) break;
                ++geom_rejects;
            }
            geom_failed = (geom_candidates == 16);
            if (!geom_failed) ++geom_candidates;   // draws taken (loop index -> count)
        } else if (fi_mode == Mode::A03Stuck0 || fi_mode == Mode::A03Stuck1) {
            // A03 (03): one EA bit stuck-at-0/1, applied on EVERY event from
            // warm-up on (F5 semantics). A correct value already equal to
            // the stuck value is a NO-OP application — logged distinctly so
            // L5 can subtract it from injected (A03's activated 口径).
            if (f5_bit == 64) f5_bit = rng() % 48;
            const Addr mask = 1ULL << f5_bit;
            new_vaddr = (fi_mode == Mode::A03Stuck0) ? (vaddr & ~mask)
                                                     : (vaddr | mask);
            geom_failed = !geomLegal(new_vaddr);   // fixed bit: decline, never re-draw
        } else if (lsuTrigger && lsuTrigger->tier == ChaOSLsuTier::F5) {
            // LSU F5 (05 r8): "每次运行仅选一个 bit/字段" — ONE fixed bit per
            // run, stuck from the first post-warm-up eligible event on. A
            // per-event random bit (the legacy path) instead aliases each
            // access unpredictably and trips packet-offset assertions.
            if (f5_bit == 64) f5_bit = rng() % 16;
            new_vaddr = vaddr ^ (1ULL << f5_bit);
            geom_failed = !geomLegal(new_vaddr);   // fixed bit: decline, never re-draw
        } else {
            for (geom_candidates = 0; geom_candidates < 16;
                 ++geom_candidates) {
                new_vaddr = vaddr ^ (1ULL << (rng() % 16));  // low-bit flip
                if (new_vaddr != vaddr && geomLegal(new_vaddr)) break;
                ++geom_rejects;
            }
            geom_failed = (geom_candidates == 16);
            if (!geom_failed) ++geom_candidates;   // draws taken (loop index -> count)
        }
        if (geom_failed) {
            // No legal candidate: decline this injection (not counted).
            ++obs_post_geomreject;   // [LSU][OBS-2] phantom decline counter
            if (write_log && log_stream && log_stream->stream()) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: lsq_sendFragmentToTranslation"
                    << ", mode=" << mode_name
                    << ", REJECT: reason=block_geometry"
                    << ", old_vaddr=0x" << std::hex << vaddr
                    << ", frag_size=" << std::dec << frag_sz
                    << ", candidates=" << geom_candidates
                    << ", geom_rejects=" << geom_rejects
                    << ", last_cand_bitmask=0x" << std::hex
                    << (new_vaddr ^ vaddr) << std::dec
                    << std::endl;
            }
            return false;
        }
        if (new_vaddr == vaddr) { ++obs_post_nochange; return false; }   // [LSU][OBS-2]
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
        // [LSU][OBS-L3] abort-survivable funnel row (attempted/eligible/
        // injected as of NOW; the inj/addr_form nodes are registered by the
        // lsq.cc sendFragmentToTranslation call site, which sees the return
        // value and both vaddrs).
        notifyFunnelAtInjection();
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: lsq_sendFragmentToTranslation"
                << ", mode=" << mode_name
                << ", old_vaddr=0x" << std::hex << vaddr
                << ", new_vaddr=0x" << new_vaddr << std::dec
                << ", faults_injected: " << faults_injected_count
                << ", geom_candidates=" << geom_candidates
                << ", geom_rejects=" << geom_rejects
                << ", geom_bitmask=0x" << std::hex << (new_vaddr ^ vaddr)
                << std::dec
                << " (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)"
                << std::endl;
        }
        return true;
    }

    // [MDSPEC][R4-6-A06] A06-a/A06-b helpers ----------------------------------
    bool
    CHAOSAddrPath::isLegalAguSize(uint64_t s) {
        return s == 1 || s == 2 || s == 4 || s == 8 || s == 16;
    }

    // A06-a load leg: is THIS load writable by the mode, and to what size?
    // [MDSPEC][R4-8-A06] Success <=> target is ANOTHER LEGAL value in
    // {1,2,4,8,16} (widen OR shrink — the spec's "替换为另一合法组合" has no
    // direction restriction) that keeps the whole access inside one 64B line.
    // Everything else is a counted decline (never a silent no-op, never an
    // injection):
    //   NoTarget   agu_size_to_load == 0 (load leg not configured)
    //   Illegal    target not in {1,2,4,8,16}
    //   NoChange   target == original size (not a fault — nothing to write)
    //   Geometry   (addr&63)+target > 64 — would break
    //              BaseCache::satisfyRequest's packet-offset invariant.
    //
    // On the SHRINK direction and the fixed-width completion contract: the
    // AArch64 load completion is fixed-width per STATIC instruction
    // (LoadCompleteAcc getMemLE(pkt, Mem) -> Packet::getRaw<T>,
    // arch/generic/memhelpers.hh:87 reads sizeof(Mem) bytes), while the
    // destination buffer is sized by the (possibly faulted) request size
    // (lsq_unit.cc read()). A shrink would therefore read past the heap —
    // UNLESS the buffer is floored at the pre-fault static width. That floor
    // is exactly what LSQ::pushRequest hands to LSQUnit through
    // DynInst::chaosA06BufBytes (set only when this function's caller shrinks
    // a load) and what the two load-buffer allocation sites honour: the
    // shrunk load then completes as a faithful zero-extended TRUNCATION
    // (the spec's predicted load manifestation, 03-sheet A06 行 "load 可能
    // 表现为截断/符号扩展错误"), never as an out-of-bounds read.
    CHAOSAddrPath::A06LoadVerdict
    CHAOSAddrPath::a06LoadSize(Addr addr, unsigned size,
                               unsigned &target) const {
        if (agu_size_to_load == 0) return A06LoadVerdict::NoTarget;
        if (!isLegalAguSize(agu_size_to_load)) return A06LoadVerdict::Illegal;
        if (agu_size_to_load == (uint64_t)size)
            return A06LoadVerdict::NoChange;
        if ((addr & 63) + agu_size_to_load > 64)
            return A06LoadVerdict::Geometry;
        // [R4-8-INT] decline the shrink direction outright (see the enum
        // comment): the fixed-width completion asserts on the PACKET size,
        // so a shrunk load SIGABRTs regardless of the buffer floor.
        if (agu_size_to_load < (uint64_t)size)
            return A06LoadVerdict::ShrinkUnsafe;
        target = (unsigned)agu_size_to_load;
        return A06LoadVerdict::Success;
    }

    const char *
    CHAOSAddrPath::a06LoadVerdictReason(A06LoadVerdict v) {
        switch (v) {
          case A06LoadVerdict::NoTarget:
            return "load_size_target_unset";
          case A06LoadVerdict::Illegal:
            return "load_size_target_illegal";
          case A06LoadVerdict::NoChange:
            return "load_size_nochange";
          case A06LoadVerdict::Geometry:
            return "load_size_block_geometry";
          case A06LoadVerdict::ShrinkUnsafe:
            return "load_size_block_shrink_unsafe";
          default:
            return "load_size_ok";
        }
    }

    unsigned int
    CHAOSAddrPath::maybeCorruptPre(Addr& addr, unsigned int size, bool isLoad,
                               Request::Flags& flags, uint64_t dyn_inst_seq,
                               std::vector<bool>& byte_enable)
    {
        // [LSU][OBS-L3] last-hook verdict for the pushRequest call site
        // (flag-only modes S06/L02 leave addr/size untouched).
        obs_pre_hook_injected = false;

        // [MDSPEC][R4-5.8] A07 path: this hook serves ONLY as the EA
        // observation point (late binding) — NEVER a value fault and NEVER
        // a trigger attempt (the ready hook owns the attempt stream;
        // booking attempts here would double-count and the PRE op-class
        // filter would mis-shape the denominator). When the DELAYED
        // instruction's EA first materializes (pushRequest entry = the
        // AGU's raw output, W1-⑦), bind the fault chain to the real
        // address range so the very same request's lsq_push (emitted right
        // below this hook in LSQ::pushRequest), its mem_req/tlb_translate
        // fragments and every downstream node join by seq+overlap with
        // REAL va values (a precise range — no address-only fallback arm
        // is registered for A07; the fault follows the dynamic
        // instruction, not an address).
        if (agu_ready_mode != "off") {
            if (!agu_addr_bound && dyn_inst_seq != 0
                && dyn_inst_seq == agu_fault_seq && agu_fault_ptag) {
                CHAOSPropagation *prop = CHAOSPropagation::instance();
                if (prop)
                    prop->bindAguFaultAddr(agu_fault_ptag, dyn_inst_seq,
                                           addr, size);
                agu_addr_bound = true;
            }
            return size;
        }

        if (probability <= 0.0f) return size;

        // [LSU][MDSPEC][R4-6-A06] A06-a load-leg verdict. Eligibility ==
        // writability (F-049): decided here, BEFORE the trigger, so a load
        // the mode cannot write can never consume the F6 once-ever shot —
        // and the very same verdict drives the value write in the a06_size
        // branch below (computed once; no RNG, hence deterministic).
        A06LoadVerdict a06_load_v = A06LoadVerdict::Success;
        unsigned a06_load_tgt = 0;
        if (pre_mode == "a06_size" && isLoad)
            a06_load_v = a06LoadSize(addr, size, a06_load_tgt);
        const bool a06_load_declined =
            (pre_mode == "a06_size" && isLoad &&
             a06_load_v != A06LoadVerdict::Success);

        if (lsuTrigger) {
            lsuTrigger->onAttempt();
            // [LSU][SEM-PRE] op-class filter BEFORE the trigger decision (F-049
            // phantom fix, user step 8 2026-10-10): the model's op class is part
            // of ELIGIBILITY (checklist 激活口径) — a trigger fire the mode
            // cannot write is not an injection. L01/L02 = loads only; S13/S04/
            // S05/S11 = stores only; eligible streams now exclude the opposite
            // class, so interval tiers (F1/F2/F4) count against the op-filtered
            // stream. The in-switch checks stay as belt-and-braces; OBS-2's
            // pre_opclass counter is the regression detector — for the
            // opposite-class models it must stay 0. [MDSPEC][R4-6-A06] For
            // a06_size it is EXPECTED to be nonzero: the load leg admits
            // only widen-legal loads, so every non-widenable load is a
            // legitimate op-class decline (its per-reason counters below
            // classify it further).
            const bool pre_load_only  = (pre_mode == "l01_load_addr" ||
                                         pre_mode == "l02_load_state");
            const bool pre_store_only = (pre_mode == "s13_store_addr" ||
                                         pre_mode == "s04_store_subst" ||
                                         pre_mode == "s05_store_size" ||
                                         pre_mode == "s11_store_lost");
            // [LSU][MDSPEC][R4-8-A06] A06-a bisects by op class: stores take
            // any legal target; loads take any OTHER legal target (widen or
            // shrink — see a06LoadSize; a shrink is made safe by the floored
            // load buffer, DynInst::chaosA06BufBytes). Eligibility ==
            // writability (F-049), decided
            // BEFORE the trigger, so a load the mode cannot write can never
            // consume the F6 once-ever shot. The verdict was computed ONCE
            // above and is reused by the a06_size branch below.
            if ((pre_load_only && !isLoad) || (pre_store_only && isLoad)
                || a06_load_declined) {
                // [LSU][MDSPEC][A6] op-class 拒斥（不计 activated）。A06
                // 2026-10-19 裁决曾把全部 load 拒斥（store-only 安全路径）；
                // R4-6-A06 2026-10-22 load 侧放宽到 widen；R4-8-A06
                // 2026-10-22 起 load 侧 = **任意另一合法值**（widen 或
                // shrink），只有 NoChange / Geometry / 非法目标仍在这里被拒，
                // 且带明确理由。F6 已 armed 时显式写 REJECT 日志留证；f6_pending
                // 保持 armed 等待下一个合格事件。普通逐事件拒斥只进
                // obs_pre_opclass 计数（不刷日志，与 F-049 其余模式一致）。
                if (pre_mode == "a06_size" && f6_pending &&
                    write_log && log_stream && log_stream->stream()) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: lsq_pushRequest_PRE, mode=" << pre_mode
                        << ", REJECT: reason="
                        << (a06_load_declined
                                ? a06LoadVerdictReason(a06_load_v)
                                : "load_candidate_under_store_only_model")
                        << ", isLoad=" << (isLoad ? 1 : 0)
                        << ", isStore=" << (isLoad ? 0 : 1)
                        << ", old_size=" << size
                        << ", new_size=" << size
                        << ", widen_target=" << agu_size_to_load
                        << std::endl;
                }
                // [MDSPEC][R4-8-A06] per-reason observability under the TIER
                // route. These per-reason counters used to be reachable ONLY
                // through the legacy gating path (the a06_size branch below),
                // because this eligibility filter returns first — so an
                // F0/F2/F6 run could never report WHY an A06 load was
                // declined and the campaign's real route was blind to the
                // guardrail (that is exactly why R4-6-A06 could not reproduce
                // `load_shrink` with a tier config). Counted here now, once
                // per event; the legacy path counts in the a06_size branch,
                // and the two paths are mutually exclusive.
                if (pre_mode == "a06_size" && isLoad && a06_load_declined) {
                    switch (a06_load_v) {
                      case A06LoadVerdict::NoTarget:
                        ++obs_pre_a06_load_notarget; break;
                      case A06LoadVerdict::Illegal:
                        ++obs_pre_a06_load_illegal; break;
                      case A06LoadVerdict::NoChange:
                        ++obs_pre_a06_load_nochange; break;
                      case A06LoadVerdict::Geometry:
                        ++obs_pre_a06_load_geom; break;
                      default: break;
                    }
                }
                ++obs_pre_opclass;   // [LSU][OBS-2]
                return size;   // op class not eligible for this model
            }
            bool go;
            if (lsuTrigger->tier == ChaOSLsuTier::F6) {
                go = f6_pending;
                f6_pending = false;
            } else {
                go = lsuTrigger->onEligible();
            }
            if (!go) return size;
            ++obs_pre_fired;   // [LSU][OBS-2]
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
            // [LSU][MDSPEC][A6] A06-a access-size substitution. Per-op-class
            // legality envelope (2026-10-19 裁决 store-only；R4-6-A06
            // 2026-10-22 load 侧落地；R4-8-A06 2026-10-22 放开 load shrink):
            //   store: any legal target {1,2,4,8,16} — a short/wide store is
            //          architecturally legal (memory lands per packet byte).
            //   load : ANY other legal value {1,2,4,8,16} (a06LoadSize) —
            //          widen OR shrink. Both directions are faithful to the
            //          spec ("替换为另一合法组合"). The fixed-width
            //          completion contract (LoadCompleteAcc getMemLE(pkt,
            //          Mem) reads sizeof(Mem) STATIC bytes) is satisfied by
            //          floored buffers, not by forbidding the fault:
            //          LSQ::pushRequest records the pre-fault static width in
            //          DynInst::chaosA06BufBytes whenever it shrinks a load,
            //          and the two load-buffer allocation sites in lsq_unit.cc
            //          floor at that width + zero-fill — so a shrunk load
            //          completes as a zero-extended TRUNCATION instead of a
            //          heap over-read.
            // Amplifier/traceability (widen): the widen grows req_e =
            //   req_s+size, so LSQUnit::tryToForward's store_has_upper_limit
            //   (lsq_unit.cc:1657-1720) stops holding -> the full
            //   store->load forward is demoted/lost and the load re-reads
            //   memory (SDC-capable when the store has not drained).
            // Amplifier/traceability (shrink): the completion truncates to
            //   the faulted width, zero-extending the tail — a value-level
            //   SDC of the load's destination register. Either way the
            //   address is unchanged, so the L3 chain is bound by the inj
            //   node's old_size/new_size (registerInjection, lsq.cc) and the
            //   addr registry range [addr, addr+new_size).
            if (isLoad) {
                if (a06_load_declined) {
                    // Belt-and-braces: the trigger path already filtered
                    // this (eligibility == writability). The legacy
                    // (non-trigger) path lands here — count per reason,
                    // never write.
                    switch (a06_load_v) {
                      case A06LoadVerdict::NoTarget:
                        ++obs_pre_a06_load_notarget; break;
                      case A06LoadVerdict::Illegal:
                        ++obs_pre_a06_load_illegal; break;
                      case A06LoadVerdict::NoChange:
                        ++obs_pre_a06_load_nochange; break;
                      case A06LoadVerdict::Geometry:
                        ++obs_pre_a06_load_geom; break;
                      default: break;
                    }
                    ++obs_pre_opclass;   // [LSU][OBS-2]
                    return size;
                }
                // [MDSPEC][R4-8-A06] split the injection counter by direction
                // (target vs ORIGINAL size, before the write).
                if (a06_load_tgt > size) ++obs_pre_a06_load_widen;
                else                     ++obs_pre_a06_load_shrink;
                size = a06_load_tgt;
                // NOTE: the carrier's buffer floor (DynInst::
                // chaosA06BufBytes) is NOT set here — this hook has no
                // DynInst handle. LSQ::pushRequest compares the returned size
                // against its saved pre-fault size and sets the field on the
                // shrinking load, which covers the trigger and legacy paths
                // alike (lsq.cc).
            } else if (isLegalAguSize(agu_size_to)) {
                size = (unsigned)agu_size_to;
            } else {
                ++obs_pre_invalid; return size;   // [LSU][OBS-2] invalid target size — no-op, logged below
            }
        } else if (pre_mode == "a06s_store_size") {
            // REJECTED ALIAS (2026-10-19 MDSPEC §2 裁决): 规格定义 A06、无
            // A06S——旧名 a06s_store_size 是 83ff9265 引入的私改模型名，禁止
            // 用于新运行（不得私改模型 ID）。NEVER injects; one-time warn +
            // one-time REJECT log。lsu_proxy.py rejects the string at config
            // time; this branch only guards direct SimObject users。
            if (!a06s_retired_warned) {
                a06s_retired_warned = true;
                warn("CHAOSAddrPath: pre_mode 'a06s_store_size' is a rejected "
                     "alias (MDSPEC 2026-10-19 ruling: spec defines A06, not "
                     "A06S); use 'a06_size' (store-side safe path)\n");
                if (write_log && log_stream && log_stream->stream())
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: lsq_pushRequest_PRE, mode=a06s_store_size"
                        << ", REJECT: reason=a06s_store_size_alias_use_a06_size"
                        << std::endl;
            }
            ++obs_pre_invalid;
            return size;
        } else if (pre_mode == "s13_store_addr") {
            // S13 (03): SQ entry address/tag single-bit flip — STORES only.
            // The corrupted address affects forwarding comparison AND the
            // final writeback destination (both consume the SQ addr field).
            if (isLoad) { ++obs_pre_opclass; return size; }   // [LSU][OBS-2]   // L01's territory, not ours
            const uint64_t bit = rng() % 48;   // VA 48-bit
            addr = addr ^ (1ULL << bit);
        } else if (pre_mode == "s04_store_subst") {
            // S04 (03): SQ addr field substitution to another legal same-page
            // address — STORES only. Changes both forwarding comparison and
            // the final writeback destination.
            if (isLoad) { ++obs_pre_opclass; return size; }   // [LSU][OBS-2]
            const Addr page = addr & ~(Addr)0xFFF;
            Addr cand;
            do { cand = page | ((Addr)(rng() % 256) << 4); } while (cand == addr);
            addr = cand;
        } else if (pre_mode == "s05_store_size") {
            // S05 (03): SQ byte-enable/access-size substitution — STORES
            // only. Changes the partial-store coverage (which bytes get
            // written). Address unchanged.
            if (isLoad) { ++obs_pre_opclass; return size; }   // [LSU][OBS-2]
            const unsigned new_sizes[] = {1, 2, 4, 8, 16};
            const unsigned pick = rng() % 5;
            if (new_sizes[pick] != size) size = new_sizes[pick];
            else size = new_sizes[(pick + 1) % 5];
        } else if (pre_mode == "s06_store_state") {
            // S06 (03): SQ lifecycle state corruption — STORES only. Toggle
            // STRICT_ORDER on the store, which changes how it drains
            // (strictly-ordered stores bypass normal writeback path).
            // Honest approximation of the valid/committed/completed state.
            flags.set(Request::STRICT_ORDER);
        } else if (pre_mode == "s07_store_ptr") {
            // S07 (03): SQ head/tail pointer corruption — STORES only.
            // Honest approximation: alias the store to the PREVIOUS cache
            // line (64B shift), simulating a head/tail misalignment where
            // the wrong entry is selected for writeback.
            addr = (addr & ~(Addr)0x3F) - 0x40;
        } else if (pre_mode == "s11_store_lost") {
            // S11 (03): SQ drain handshake — STORES only. Set size=0
            // (simulating a lost/never-completed write request: the SQ
            // "thinks" it sent the write but nothing reaches L1D).
            if (isLoad) { ++obs_pre_opclass; return size; }   // [LSU][OBS-2]
            size = 0;
        } else if (pre_mode == "l02_load_state") {
            // L02 (03): LQ lifecycle state corruption — LOADS only. Toggle
            // STRICTLY_ORDERED flag, which changes how the load is handled
            // (strictly-ordered loads bypass forwarding and go to memory).
            // Honest approximation: the full valid/issued/completed state
            // machine is internal to LSQRequest; the flags are the
            // externally controllable lifecycle proxy at this hook.
            if (!isLoad) { ++obs_pre_opclass; return size; }   // [LSU][OBS-2]
            flags.set(Request::STRICT_ORDER);
        } else if (pre_mode == "l01_load_addr") {
            // L01 (03): LQ entry address/tag single-bit flip — LOADS only.
            // The corrupted address affects the conflict/violation check
            // against older stores AND the actual memory access.
            if (!isLoad) { ++obs_pre_opclass; return size; }   // [LSU][OBS-2]  // S13's territory, not ours
            const uint64_t bit = rng() % 48;
            addr = addr ^ (1ULL << bit);
        } else {
            { ++obs_pre_invalid; return size; }  // [LSU][OBS-2] unknown pre_mode — config validated in .py choices
        }

        // [MDSPEC][R4-6-A06] A06-b byte-enable observation / injection.
        // Runs AFTER the size substitution for two reasons: (1) the mask is
        // size-indexed, so it must be validated against the FINAL size;
        // (2) lsq.cc rebuilds _byteEnable all-true when the size changed
        // (mask/size consistency), so a mask substitution on the same event
        // as a size substitution would be silently discarded — declined
        // explicitly instead (obs_be_declined).
        unsigned be_ones = 0;
        const unsigned be_len = (unsigned)byte_enable.size();
        for (bool b : byte_enable) if (b) ++be_ones;
        ++obs_be_seen;
        const bool be_all_true = (be_ones == be_len);
        if (be_all_true) ++obs_be_all_true;
        bool be_substituted = false;
        if (be_mode == "shift_mid") {
            if (size != old_size) {
                // A06-a already owns this event (one fault per sample).
                ++obs_be_declined;
            } else if (!isLoad && be_len == size && size >= 2) {
                // "另一合法掩码": all-true with one INTERIOR byte cleared.
                // index (size-1)/2 satisfies 0 <= idx <= size-2, so the mask
                // has no inactive TAIL (LSQRequest::addReq / inactiveTailSize,
                // lsq.cc:1186-1197) => the request size is unchanged => the
                // fixed-width load completion contract is untouched, and
                // Request::isMasked() -> Packet::isMaskedWrite() ->
                // Packet::writeData (packet.hh:1320-1336) / MSHR::TargetList::
                // add / base.cc:1090 give the store a real partial write.
                byte_enable[(size - 1) / 2] = false;
                be_substituted = true;
                ++obs_be_substituted;
            } else {
                // size < 2 (no interior byte) or a LOAD: a load's mask has
                // no architectural consumer on this path (the ISA always
                // produces all-true — see the hh carrier note), and its only
                // functional lever is the tail trim == a size change, which
                // the load contract forbids. Declined, counted.
                ++obs_be_declined;
            }
        }

        chaosL0Register(l0_item, addr ? addr : size);
        ++l0_funnel.injected;
        ++l0_funnel.activated;
        ++faults_injected_count;
        // [LSU][OBS-L3] the PRE hook DID inject: the lsq.cc pushRequest call
        // site registers inj/addr_form with CHAOSPropagation through
        // lastPreHookInjected() (it sees the before/after addr/size for the
        // addr registry); here we only owe the abort-survivable funnel row.
        obs_pre_hook_injected = true;
        notifyFunnelAtInjection();
        if (write_log && log_stream && log_stream->stream()) {
            // [LSU][P4-F6] abort-survivable dual-track evidence: which F6
            // track fired and at which matching-event occurrence (the
            // CHAOS_LSU_F6MODE stdout line only prints on normal exit).
            std::string f6_fields;
            if (lsuTrigger && lsuTrigger->tier == ChaOSLsuTier::F6)
                f6_fields = std::string(", f6_mode=") +
                    (f6_steady_state ? "steady_state" : "early_stress") +
                    ", f6_occurrence=" + std::to_string(f6_fired_occurrence);
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: lsq_pushRequest_PRE"
                << ", mode=" << pre_mode
                << ", old_addr=0x" << std::hex << old_addr
                << ", new_addr=0x" << addr
                << ", old_size=" << std::dec << old_size
                << ", new_size=" << size
                << ", faults_injected: " << faults_injected_count
                // [LSU][P4-FIX-A06S] op-class 字段自描述（尾部追加，向后
                // 兼容既有 mode=/old_addr= 字段解析）；旧批次日志无此字段
                // ——离线拆分 load/store 只对新数据可行，历史数据不回填。
                << ", isLoad=" << (isLoad ? 1 : 0)
                << ", isStore=" << (isLoad ? 0 : 1)
                // [MDSPEC][R4-6-A06] A06 self-description (tail-appended,
                // same backward-compat rule): which FIELD the fault landed
                // on (addr / size / addr+size — computed, never asserted)
                // and the A06-b byte-enable evidence for this event.
                << ", fault_field="
                << (addr != old_addr
                        ? (size != old_size ? "addr+size" : "addr")
                        : (size != old_size ? "size" : "none"))
                << ", be_len=" << be_len
                << ", be_ones=" << be_ones
                << ", be_subst=" << (be_substituted ? 1 : 0)
                << f6_fields
                << std::endl;
        }
        return size;
    }

    // [MDSPEC][R4-5.8] A07-b AGU clean-ready delay (see .hh for the hook
    // contract). Called from IEW::executeInsts' isMemRef branch — the
    // ready/handshake point. Returns true = the caller MUST SKIP the normal
    // execute path this cycle (the resume event re-enters it at the delayed
    // tick); false = proceed normally.
    bool
    CHAOSAddrPath::maybeDelayAguReady(const o3::DynInstPtr &inst)
    {
        if (agu_ready_mode == "off" || !lsuTrigger)
            return false;
        if (!inst)
            return false;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;   // G5 single-fault cap (C11 discipline)

        lsuTrigger->onAttempt();

        // Eligibility (op-class filter BEFORE the trigger decision, F-049):
        // plain loads and plain stores — the AGU serves both queues;
        // atomics are the O-family RMW models' territory and prefetches the
        // P-family's; the spec binds ONE dynamic instruction. The
        // "连续相关访存" (consecutive dependent memory accesses) trigger
        // context is workload-realized (W3/W5 are dependent-chase probes)
        // — a true data-dependency gate needs producer tracking the ready
        // point does not expose (register producers are not carried on the
        // DynInst at execute time); honest registration, C11's same-page
        // proxy class.
        if (inst->isAtomic() || inst->isDataPrefetch()
            || inst->isInstPrefetch()
            || !(inst->isLoad() || inst->isStore())) {
            ++obs_agu_opclass;
            return false;
        }
        // Single-slot guard (C12 discipline): a second fire while one
        // resume is pending would overwrite the slot (the first
        // instruction's resume lost). Campaign maxFaults=1 makes this
        // unreachable; structural refusal under unlimited configs.
        if (aguResumeEvent.scheduled()) {
            ++obs_agu_slotbusy;
            return false;
        }

        bool go;
        if (lsuTrigger->tier == ChaOSLsuTier::F6) {
            // EIGHTH F6 event source (chaos_lsu_trigger.hh registry): A07's
            // specified event IS the AGU-ready handshake of an eligible
            // plain mem op. onF6Event(false): THIS invocation's attempt was
            // already booked by onAttempt() above — booking again here
            // would double-count ([MDSPEC][R4-5.1-review-I1]; the W1 thunk
            // sites keep the default because their event notification has
            // no onAttempt stream).
            go = lsuTrigger->onF6Event(false);
        } else {
            go = lsuTrigger->onEligible();
        }
        if (!go)
            return false;

        // Fire: stash the instruction and schedule the resume at the CPU's
        // clockEdge(delay). The AGU (initiateAcc) runs INSIDE the resume
        // re-entry, so every downstream value is the CORRECT one, only the
        // ready/execute tick shifts from ready_tick to delayed_tick (the
        // spec's "只改变一次事件的发生周期…数据载荷保持正确").
        const Tick ready_tick = curTick();
        const Tick delayed_tick =
            o3cpu_resolved
                ? o3cpu_resolved->clockEdge(Cycles(agu_ready_delay_cycles))
                : ready_tick;
        aguPendingInst = inst;
        agu_fault_seq = inst->seqNum;
        agu_addr_bound = false;
        agu_activated = false;
        schedule(aguResumeEvent, delayed_tick);
        ++faults_injected_count;
        chaosL0Register(l0_item, inst->seqNum);
        ++l0_funnel.injected;
        // Registration: inj node (corr=origin; before/after = the faulted
        // VALUE of this model, the ready tick before/after the delay — the
        // C12 delivery-tick precedent; delay_cycles/keys stay in the v1
        // detail). NO registry entry yet: the EA does not exist at the
        // ready point; bindAguFaultAddr (maybeCorruptPre, above) binds the
        // chain to the real address range when the delayed instruction's
        // EA enters the LSQ.
        if (CHAOSPropagation::instance())
            agu_fault_ptag = CHAOSPropagation::instance()->registerAguReadyFault(
                inst->seqNum,
                (long long)(inst->isLoad() ? inst->lqIdx : -1),
                (long long)(inst->isLoad() ? -1 : inst->sqIdx),
                ready_tick, delayed_tick, agu_ready_delay_cycles,
                inst->isLoad(), inst->pcState().instAddr());
        notifyFunnelAtInjection();
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "Tick: " << ready_tick
                << ", Site: iew_memRef_AGU_ready"
                << ", mode=" << agu_ready_mode
                << ", dyn_inst_seq=" << inst->seqNum
                << ", ready_tick=" << ready_tick
                << ", delayed_tick=" << delayed_tick
                << ", delay_cycles=" << agu_ready_delay_cycles
                << ", isLoad=" << (inst->isLoad() ? 1 : 0)
                << ", isStore=" << (inst->isLoad() ? 0 : 1)
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    // [MDSPEC][R4-5.8] A07-b resume thunk (aguResumeEvent, fires at the
    // delayed tick = the CPU's clockEdge(delay); EventFunctionWrapper's
    // Maximum_Priority runs it after that tick's CPU tick event, i.e. the
    // instruction executes "at" the delayed cycle). Squash-safe: the stashed
    // DynInstPtr keeps the instruction alive across the delay window; if a
    // younger-installed squash removed it in between, chaosAguResumeInst's
    // squashed branch retires it exactly like executeInsts does (the fault
    // then stays Injected-not-activated — l0_funnel.activated is only
    // bumped on a genuine resume consumption, a REAL read-back verdict,
    // stricter than the POST hook's near-tautological approximation).
    void
    CHAOSAddrPath::resumeDeferredAgu()
    {
        o3::DynInstPtr inst = aguPendingInst;
        aguPendingInst = nullptr;   // clear the slot BEFORE re-entry
        if (!inst)
            return;
        if (o3cpu_resolved) {
            agu_activated = true;
            ++l0_funnel.activated;
            o3cpu_resolved->o3IEW().chaosAguResumeInst(inst);
        }
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iew_memRef_AGU_ready_resume"
                << ", mode=" << agu_ready_mode
                << ", dyn_inst_seq=" << inst->seqNum
                << ", consumed=1, squashed=" << (inst->isSquashed() ? 1 : 0)
                << std::endl;
        }
    }

    void
    CHAOSAddrPath::notifyFunnelAtInjection()
    {
        // [LSU][OBS-L3] funnel row with the counts as of NOW. Trigger path:
        // mirror the trigger's own counters (the exit callback mirrors the
        // same way); legacy path: attempted=eligible=injected (the existing
        // non-trigger l0_funnel mirror convention, CHAOSAddrPath.cc exit
        // callback). stdout stays untouched (W2.1 discipline) — the FUNNEL
        // line goes to the injection log only, and the abort-survivable
        // copy is the prop-trace node (per-node gzflush).
        const uint64_t attempted =
            lsuTrigger ? lsuTrigger->attempted : faults_injected_count;
        const uint64_t eligible =
            lsuTrigger ? lsuTrigger->eligible : faults_injected_count;
        const uint64_t injected =
            lsuTrigger ? lsuTrigger->injected : faults_injected_count;
        if (o3cpu_resolved && o3cpu_resolved->chaosPropagation)
            o3cpu_resolved->chaosPropagation->noteFunnel(
                "CHAOSAddrPath", attempted, eligible, injected);
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "FUNNEL: attempted=" << attempted
                << " eligible=" << eligible
                << " injected=" << injected << std::endl;
        }
    }

    // [MDSPEC][R4-6-A06] A06 summary line (stdout, W2.1 discipline: a NEW
    // line, never a change to an existing one). Printed only for A06-shaped
    // runs (a06_size / the rejected a06s alias / a non-off be_mode) so every
    // other configuration's stdout stays byte-identical.
    void
    CHAOSAddrPath::a06Summary() {
        if (pre_mode != "a06_size" && pre_mode != "a06s_store_size"
            && be_mode == "off")
            return;
        printf("CHAOS_L0_A06: pre_mode=%s size_to=%lu load_size_to=%lu "
               "be_mode=%s load_widen=%lu load_shrink=%lu load_notarget=%lu "
               "load_illegal=%lu load_nochange=%lu load_geom=%lu "
               "be_seen=%lu be_all_true=%lu be_subst=%lu be_declined=%lu\n",
               pre_mode.c_str(),
               (unsigned long)agu_size_to,
               (unsigned long)agu_size_to_load,
               be_mode.c_str(),
               (unsigned long)obs_pre_a06_load_widen,
               (unsigned long)obs_pre_a06_load_shrink,
               (unsigned long)obs_pre_a06_load_notarget,
               (unsigned long)obs_pre_a06_load_illegal,
               (unsigned long)obs_pre_a06_load_nochange,
               (unsigned long)obs_pre_a06_load_geom,
               (unsigned long)obs_be_seen,
               (unsigned long)obs_be_all_true,
               (unsigned long)obs_be_substituted,
               (unsigned long)obs_be_declined);
    }

    void
    CHAOSAddrPath::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSAddrPath: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        // [LSU][OBS-L3] cache the resolved O3 CPU for the injection-time
        // funnel notify (dynamic_cast once, not per event).
        o3cpu_resolved = o3cpu;
        // W4: exactly one hook per run — the PRE family (A04/A05/A06/A08)
        // registers on the pushRequest-entry pointer; the post family
        // (legacy + A01-A03 + LSU tiers) keeps the sendFragment pointer.
        // [MDSPEC][R4-5.8] A07 third family: the ready hook owns the
        // injection; the PRE pointer is registered ONLY as the EA
        // observation point (maybeCorruptPre's top branch makes it a
        // non-injecting late binder — no attempts, no value fault), and
        // the POST (sendFragment) pointer stays UNREGISTERED so no value
        // fault path exists for A07 (timing-only model).
        if (agu_ready_mode != "off") {
            o3cpu->setChaosAguReady(this);
            o3cpu->setChaosAddrPathPre(this);
        } else if (pre_mode != "off") {
            o3cpu->setChaosAddrPathPre(this);
        } else {
            o3cpu->setChaosAddrPath(this);
        }
        if (lsuTrigger) {
            // [MDSPEC][R4-5.8] the W1 four-source F6 thunk registration is
            // for the POST family ONLY: A07's F6 event source IS the
            // AGU-ready handshake (booked at the hook via onF6Event(false),
            // chaos_lsu_trigger.hh EIGHTH source) — registering the thunk
            // here would make W1 events (sq_forward etc.) consume the F6
            // once-ever shot.
            if (lsuTrigger->tier == ChaOSLsuTier::F6
                && agu_ready_mode == "off") {
                f6Consumer = this;
                chaosLsuF6Notify = &CHAOSAddrPath::f6Thunk;
            }
            // W2 funnel summary (attempted/eligible/injected; activated is
            // the W3 L0 read-back layer's verdict — R2 ruling) + W3 L0 lines
            // (chaos_l0 discipline: to the LOG FILE, stdout stays stable).
            registerExitCallback([this]() {
                if (lsuTrigger) {
                    lsuTrigger->summary("CHAOSAddrPath");
                    // [LSU][P4-F6] dual-track evidence line: which track ran,
                    // its warm-up/span, the pre-drawn target occurrence and
                    // how many matching events were actually seen (matched <
                    // target = no injection, honest inj=0).
                    // [MDSPEC][R4-5.8] POST-family only: A07's F6 semantics
                    // is onF6Event(false) at the ready hook (the thunk track
                    // never runs — printing it would claim a mode that
                    // never fired).
                    if (lsuTrigger->tier == ChaOSLsuTier::F6
                        && agu_ready_mode == "off") {
                        printf("CHAOS_LSU_F6MODE: mode=%s warmup=%lu "
                               "span=%lu target_occurrence=%lu matched=%lu\n",
                               f6_steady_state ? "steady_state"
                                               : "early_stress",
                               (unsigned long)lsuTrigger->warmup_events,
                               (unsigned long)lsuTrigger->span_events,
                               (unsigned long)f6_target_occurrence,
                               (unsigned long)f6_events_matched);
                    }
                    // [LSU][OBS-2] post-trigger decline report (D-class):
                    // pre_opclass>0 with fault writes < trigger.injected is
                    // the phantom-activation signature (F-049).
                    printf("CHAOS_L0_DECLINE: pre_fired=%lu pre_opclass=%lu "
                           "pre_invalid=%lu post_fired=%lu post_nochange=%lu "
                           "post_geomreject=%lu trigger_injected=%lu\n",
                           (unsigned long)obs_pre_fired,
                           (unsigned long)obs_pre_opclass,
                           (unsigned long)obs_pre_invalid,
                           (unsigned long)obs_post_fired,
                           (unsigned long)obs_post_nochange,
                           (unsigned long)obs_post_geomreject,
                           (unsigned long)lsuTrigger->injected);
                    // [MDSPEC][R4-5.8] A07 ready-hook evidence line
                    // (agu_ready_mode runs only): the pending slot's final
                    // state — addr_bound=0 means the delayed instruction's
                    // EA never entered the LSQ (predicated-off / squashed
                    // before pushRequest: chain honestly stops at inj);
                    // activated counts resumes that actually executed the
                    // instruction (genuine read-back, 03 sheet's
                    // Injected-not-activated distinction).
                    if (agu_ready_mode != "off")
                        printf("CHAOS_AGU_READY: mode=%s delay_cycles=%lu "
                               "fault_seq=%lu addr_bound=%d activated=%d "
                               "obs_opclass=%lu obs_slotbusy=%lu\n",
                               agu_ready_mode.c_str(),
                               (unsigned long)agu_ready_delay_cycles,
                               (unsigned long)agu_fault_seq,
                               agu_addr_bound ? 1 : 0,
                               agu_activated ? 1 : 0,
                               (unsigned long)obs_agu_opclass,
                               (unsigned long)obs_agu_slotbusy);
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
                // [MDSPEC][R4-6-A06] A06 evidence line (A06-shaped runs
                // only — a06Summary() self-guards, so every other
                // configuration's stdout stays byte-identical).
                a06Summary();
                // [LSU][OBS-L3] final funnel row (final counts; runs only on
                // normal exit — aborts keep the last injection-time node,
                // which is exactly why the per-injection rows exist).
                notifyFunnelAtInjection();
            });
        } else if (probability > 0.0f) {
            // [LSU][OBS-L3] legacy (non-trigger) path: final funnel row only.
            // The l0 lines above stay lsuTrigger-only, so the legacy log
            // output is otherwise byte-identical.
            // [MDSPEC][R4-6-A06] the A06 counters matter on this path too (a
            // PRE-family mode can be driven by the legacy cycle window) —
            // a06Summary() is a new, self-guarded line, so runs that are not
            // A06-shaped remain byte-identical.
            registerExitCallback([this]() {
                a06Summary();
                notifyFunnelAtInjection();
            });
        }
    }

} // namespace gem5
