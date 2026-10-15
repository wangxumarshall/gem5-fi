#include "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"

#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"  // [LSU][OBS-L3] funnel notify
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

    unsigned int
    CHAOSAddrPath::maybeCorruptPre(Addr& addr, unsigned int size, bool isLoad,
                               Request::Flags& flags)
    {
        // [LSU][OBS-L3] last-hook verdict for the pushRequest call site
        // (flag-only modes S06/L02 leave addr/size untouched).
        obs_pre_hook_injected = false;
        if (probability <= 0.0f) return size;

        if (lsuTrigger) {
            lsuTrigger->onAttempt();
            // [LSU][SEM-PRE] op-class filter BEFORE the trigger decision (F-049
            // phantom fix, user step 8 2026-10-10): the model's op class is part
            // of ELIGIBILITY (checklist 激活口径) — a trigger fire the mode
            // cannot write is not an injection. L01/L02 = loads only; S13/S04/
            // S05/S11 = stores only; eligible streams now exclude the opposite
            // class, so interval tiers (F1/F2/F4) count against the op-filtered
            // stream. The in-switch checks stay as belt-and-braces; OBS-2's
            // pre_opclass counter is the regression detector (must stay 0).
            const bool pre_load_only  = (pre_mode == "l01_load_addr" ||
                                         pre_mode == "l02_load_state");
            const bool pre_store_only = (pre_mode == "s13_store_addr" ||
                                         pre_mode == "s04_store_subst" ||
                                         pre_mode == "s05_store_size" ||
                                         pre_mode == "s11_store_lost" ||
                                         pre_mode == "a06s_store_size");
            if ((pre_load_only && !isLoad) || (pre_store_only && isLoad)) {
                // [LSU][P4-FIX-A06S] load 候选拒斥（不计 activated，2026-10-15
                // 审计根因 C：a06_size v2 = store-only）。F6 已 armed 状态下到达
                // 的 load 在旧语义下就是注入点——显式写 REJECT 日志留证；
                // f6_pending 保持 armed 等待下一个 store。普通逐事件拒斥只进
                // obs_pre_opclass 计数（不刷日志，与 F-049 其余模式一致）。
                if (pre_mode == "a06s_store_size" && f6_pending &&
                    write_log && log_stream && log_stream->stream()) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: lsq_pushRequest_PRE, mode=" << pre_mode
                        << ", REJECT: reason=load_candidate_under_store_only_model"
                        << ", isLoad=1, isStore=0"
                        << ", old_size=" << size
                        << ", new_size=" << size
                        << std::endl;
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
        } else if (pre_mode == "a06s_store_size") {
            // [LSU][P4-FIX-A06S] A06S (03, a06_size v2, 2026-10-15 审计根因
            // C 修复): store-only access-size substitution. Loads never reach
            // here on the trigger path (op-class filter above); this in-switch
            // check is the belt-and-braces for the legacy (no-trigger) path.
            // Store short writes are architecturally legal (memory writes
            // packet bytes); loads with a shrunken packet hit the fixed-width
            // completion assert (LDRX completeAcc getRaw<T>) and are retired.
            if (isLoad) { ++obs_pre_opclass; return size; }   // [LSU][OBS-2]
            if (agu_size_to == 1 || agu_size_to == 2 || agu_size_to == 4 ||
                agu_size_to == 8 || agu_size_to == 16)
                size = (unsigned)agu_size_to;
            else
                { ++obs_pre_invalid; return size; }  // [LSU][OBS-2] invalid target size — no-op, logged below
        } else if (pre_mode == "a06_size") {
            // RETIRED (2026-10-15 audit root cause C): the fixed-width load
            // completion path asserts on a shrunken packet (1,030 checklist
            // + 737 W1 samples). NEVER injects; one-time warn + one-time
            // REJECT log. lsu_proxy.py rejects the string at config time;
            // this branch only guards direct SimObject users. Historical
            // data (ITEM-022/023/024/025/026/027) is preserved as evidence.
            if (!a06s_retired_warned) {
                a06s_retired_warned = true;
                warn("CHAOSAddrPath: pre_mode 'a06_size' RETIRED "
                     "(2026-10-15 audit root cause C: load completion path "
                     "asserts on shrunken packets); use 'a06s_store_size'\n");
                if (write_log && log_stream && log_stream->stream())
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: lsq_pushRequest_PRE, mode=a06_size"
                        << ", REJECT: reason=a06_size_retired_use_a06s_store_size"
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
                << std::endl;
        }
        return size;
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
                // [LSU][OBS-L3] final funnel row (final counts; runs only on
                // normal exit — aborts keep the last injection-time node,
                // which is exactly why the per-injection rows exist).
                notifyFunnelAtInjection();
            });
        } else if (probability > 0.0f) {
            // [LSU][OBS-L3] legacy (non-trigger) path: final funnel row only.
            // The l0 lines above stay lsuTrigger-only, so the legacy log
            // output is otherwise byte-identical.
            registerExitCallback([this]() { notifyFunnelAtInjection(); });
        }
    }

} // namespace gem5
