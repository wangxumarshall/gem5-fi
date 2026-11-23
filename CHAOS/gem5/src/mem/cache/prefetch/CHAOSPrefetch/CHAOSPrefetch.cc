// CHAOSPrefetch.cc — LSU W8 P-series prefetcher injector implementation.
// See CHAOSPrefetch.hh for mode semantics and honest boundary.

#include "mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetch.hh"

#include <sstream>
#include <string>

// [MDSPEC][H5] prefetch fault registration with the propagation tracer
// (static instance — CHAOSCache precedent; the prefetcher has no CPU ptr).
#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"
#include "sim/sim_exit.hh"        // registerExitCallback (W2 summary line)

namespace gem5
{

    CHAOSPrefetch *CHAOSPrefetch::f6Consumer = nullptr;
    CHAOSPrefetch *CHAOSPrefetch::fillMarkHook = nullptr;

    CHAOSPrefetch::CHAOSPrefetch(const CHAOSPrefetchParams &p)
        : SimObject(p),
          fi_mode(stringToMode(p.mode)),
          trigger(tierFromString(p.lsuTier),
                  p.rngSeed ? p.rngSeed : 1,
                  p.lsuWarmupEvents, p.lsuSpanEvents,
                  eventFromString(p.lsuF6Event)),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          line_size(p.lineSize),
          write_log(p.writeLog)
    {
        rng.seed(rng_seed ? rng_seed : rd());
        if (write_log) {
            log_stream = simout.create("prefetch_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSPrefetch: could not open prefetch_injections.log");
        }
        if (trigger.tier == ChaOSLsuTier::F6) {
            // Single-consumer F6 notify (chaos_lsu_trigger.hh).
            f6Consumer = this;
            chaosLsuF6Notify = &CHAOSPrefetch::f6Thunk;
        }
        // [MDSPEC][R4-5.4] P06-a: self-attach the fill-classification
        // hook (single consumer; Cache::serviceMSHRTargets consults it at
        // the setPrefetched gate). P06-mode only — every other run keeps
        // the gate byte-identical.
        if (fi_mode == Mode::P06AsDemand)
            fillMarkHook = this;
    }

    CHAOSPrefetch::~CHAOSPrefetch()
    {
        if (prefetch::Stride::chaosPrefetchHook == this)
            prefetch::Stride::chaosPrefetchHook = nullptr;
        if (f6Consumer == this) {
            f6Consumer = nullptr;
            chaosLsuF6Notify = nullptr;
        }
        if (fillMarkHook == this)
            fillMarkHook = nullptr;
    }

    CHAOSPrefetch::Mode
    CHAOSPrefetch::stringToMode(const std::string &s)
    {
        if (s == "p02_confidence_corrupt") return Mode::P02ConfidenceCorrupt;
        if (s == "p03_addr_subst")         return Mode::P03AddrSubst;
        if (s == "p05_drop_dup")           return Mode::P05DropDup;
        if (s == "p08_stride_stuck")       return Mode::P08StrideStuck;
        if (s == "p06_as_demand")          return Mode::P06AsDemand;
        return Mode::P01StrideBitflip;     // p01_stride_bitflip / default
    }

    ChaOSLsuTier
    CHAOSPrefetch::tierFromString(const std::string &s)
    {
        if (s == "F0") return ChaOSLsuTier::F0;
        if (s == "F1") return ChaOSLsuTier::F1;
        if (s == "F2") return ChaOSLsuTier::F2;
        if (s == "F3") return ChaOSLsuTier::F3;
        if (s == "F4") return ChaOSLsuTier::F4;
        if (s == "F5") return ChaOSLsuTier::F5;
        if (s == "F6") return ChaOSLsuTier::F6;
        panic("CHAOSPrefetch: unknown lsuTier '%s' (LSU-track-native "
              "injector: a tier is required, no legacy path)\n", s);
    }

    ChaOSLsuEvent
    CHAOSPrefetch::eventFromString(const std::string &s)
    {
        if (s == "tlb_hit") return ChaOSLsuEvent::TlbHit;
        if (s == "sq_forward") return ChaOSLsuEvent::SqForward;
        if (s == "cas_success") return ChaOSLsuEvent::CasSuccess;
        return ChaOSLsuEvent::DirtyEviction;  // dirty_eviction / default
    }

    void
    CHAOSPrefetch::startup()
    {
        // SELF-ATTACH (single consumer; one injector per run by grid
        // construction). Legacy behavior is byte-identical when unset.
        prefetch::Stride::chaosPrefetchHook = this;
        // W2 funnel summary at end of sim — the L5 classifier parses the
        // "CHAOS_LSU_TRIGGER: ... attempted= eligible= injected=" line.
        registerExitCallback([this]() { trigger.summary("CHAOSPrefetch"); });
    }

    void
    CHAOSPrefetch::f6Thunk(ChaOSLsuEvent ev)
    {
        // The trigger's onF6Event() both filters the event type and
        // enforces once-ever; the corruption happens at the next eligible
        // hook call (f6_pending).
        if (f6Consumer && f6Consumer->trigger.f6_event == ev &&
            f6Consumer->trigger.onF6Event())
            f6Consumer->f6_pending = true;
    }

    void
    CHAOSPrefetch::maybeCorrupt(prefetch::Stride::StrideEntry *entry,
                                std::vector<prefetch::Queued::AddrPriority>
                                    &addresses,
                                Addr pf_addr)
    {
        // [MDSPEC][R4-5.4] P06-a is NOT a generation-site mode: its event
        // source is the FILL site (maybeMarkFillAsDemand, the fill-
        // classification gate). This hook must stay fully inert here —
        // NOT even onAttempt (P06's attempt stream is the fill hook; a
        // second attempt stream would corrupt the funnel denominator).
        if (fi_mode == Mode::P06AsDemand) return;

        trigger.onAttempt();

        // [MDSPEC][H5] Observation-only continuation (2026-10-20 finding).
        // Once a training entry carries an active fault chain, EVERY later
        // call for that PC keeps joining its generated candidates to that
        // chain — the injector must not stop *observing* when its fault
        // budget is spent. Without this, a single F0 injection leaves the
        // corrupted stride's output unregistered and the spec chain's L2/L3
        // (queue/issue/fill) and L4 (demand) nodes are unreachable purely
        // because the injector returned early (verified empirically: the
        // hook ran exactly once, with an EMPTY candidate set).
        CHAOSPropagation *h5 = CHAOSPropagation::instance();
        const Addr h5_pc = entry ? entry->getTag() : 0;
        if (entry && h5 && corrupted_entries.count(h5_pc)) {
            const std::pair<uint64_t, uint64_t> ids = corrupted_entries[h5_pc];
            for (const auto &ap : addresses) {
                h5->registerPtagBlock(ids.first, ap.first,
                                      ap.first + line_size);
                h5->registerPtagPrefetch(ids.second, ap.first, line_size);
            }
        }

        // Eligibility (04 L0 funnel): the mode's target must exist.
        //   entry-target modes (P01/P02/P08): live table entry (hit-trained
        //     or miss-just-inserted)
        //   vector-target modes (P03/P05): non-empty generated set
        const bool entry_modes = fi_mode == Mode::P01StrideBitflip ||
                                 fi_mode == Mode::P02ConfidenceCorrupt ||
                                 fi_mode == Mode::P08StrideStuck;
        const bool eligible = entry_modes ? (entry != nullptr)
                                          : !addresses.empty();
        if (!eligible) return;

        bool go;
        if (trigger.tier == ChaOSLsuTier::F6) {
            go = f6_pending;
            f6_pending = false;
        } else {
            go = trigger.onEligible();
        }
        if (!go) return;
        if (max_faults != 0 && faults_injected >= max_faults) return;
        ++faults_injected;

        // [MDSPEC][H5] Register the prefetch fault with the propagation
        // tracer (the single injection funnel — every mode passes through
        // here) and allocate the request-level pf_request_id. The
        // whole-block registration [pf_addr, pf_addr+line_size) lets later
        // demand loads / cache events on the faulted line correlate
        // (correlateBlock / blk_registry). nullptr tracer = no-op (no
        // CHAOSPropagation attached).
        //
        // pf_request_id is a STABLE request-level identity (tracer-allocated,
        // shared by this request's train/queue/issue/fill/demand nodes) and
        // is deliberately NOT the fault_id/ptag (spec sheet 9 P01). The
        // pf_train node itself is emitted after the mutation below so that
        // before/after carry the real training-entry change.
        uint64_t h5_ptag = 0;
        uint64_t h5_pfid = 0;
        // h5_pc is computed once at the top of this function (also used by
        // the observation-only continuation above).
        // If this training entry already carries an active fault chain
        // (e.g. P01's corrupted stride keeps generating wrong addresses on
        // later calls), the candidates generated on THIS call belong to
        // that same request chain — reuse its ids.
        if (entry && corrupted_entries.count(h5_pc)) {
            h5_ptag = corrupted_entries[h5_pc].first;
            h5_pfid = corrupted_entries[h5_pc].second;
        } else if (CHAOSPropagation *h5 = CHAOSPropagation::instance()) {
            h5_ptag = h5->registerCacheFault(pf_addr, -1, line_size, "prefetch");
            if (h5_ptag)
                h5_pfid = h5->notePrefetchRequest(pf_addr, line_size);
        }
        const int h5_stride_before = entry ? entry->stride : 0;

        switch (fi_mode) {
          case Mode::P01StrideBitflip: {
              // P01: training-entry stride single-bit XOR. Bits 0-30 only
              // (bit 31 = sign of int — flipping it yields a negative
              // stride, which the generator clamps to -blkSize anyway;
              // excluding it keeps the sample space honest).
              const unsigned bit = rng() % 31;
              const int old_stride = entry->stride;
              entry->stride ^= (1 << bit);
              logInjection("P01_stride_bitflip", pf_addr,
                           "stride " + std::to_string(old_stride) + " -> " +
                           std::to_string(entry->stride) +
                           " (bit " + std::to_string(bit) + ")");
              break;
          }
          case Mode::P02ConfidenceCorrupt: {
              // P02: confidence clear (valid-dropped proxy) / fake-set
              // (fabricated confidence), 50/50. gem5 models confidence as
              // a SatCounter8 — the xlsx row's version/granule sub-fields
              // do not exist in this host structure (documented).
              if (rng() % 2) {
                  entry->confidence.reset();
                  logInjection("P02_confidence_clear", pf_addr,
                               "confidence -> initial (clear)");
              } else {
                  entry->confidence.saturate();
                  logInjection("P02_confidence_fake", pf_addr,
                               "confidence -> saturated (fake)");
              }
              break;
          }
          case Mode::P03AddrSubst: {
              // P03 negative control: substitute one generated prefetch
              // address with ANOTHER LEGAL aligned line in the SAME 4KiB
              // page (page interior arithmetic wraps at the boundary —
              // always a different line than pf_addr since line_size
              // divides 4096). Legal-but-wrong prefetch: bandwidth-only
              // effect expected; SDC means the injector polluted the fill
              // path (README §5.4 discipline).
              const Addr page_mask = ~Addr(0xfff);
              const Addr alt = (pf_addr & page_mask) |
                               ((pf_addr + line_size) & Addr(0xfff));
              const size_t idx = rng() % addresses.size();
              const Addr old_addr = addresses[idx].first;
              addresses[idx].first = alt;
              logInjection("P03_addr_subst", pf_addr,
                           "prefetch addr 0x" + std::to_string(old_addr) +
                           " -> 0x" + std::to_string(alt) + " (same page)");
              break;
          }
          case Mode::P05DropDup: {
              // P05: drop / duplicate one generated prefetch, 50/50. Also
              // the P04 queue-family approximation (missing/extra
              // generation = the observable queue-content effect).
              const size_t idx = rng() % addresses.size();
              if (rng() % 2) {
                  const Addr dropped = addresses[idx].first;
                  addresses.erase(addresses.begin() + idx);
                  logInjection("P05_drop", pf_addr,
                               "dropped prefetch 0x" +
                               std::to_string(dropped));
              } else {
                  addresses.push_back(addresses[idx]);
                  logInjection("P05_dup", pf_addr,
                               "duplicated prefetch 0x" +
                               std::to_string(addresses[idx].first));
              }
              break;
          }
          case Mode::P08StrideStuck: {
              // P08: stride stuck-at-0, re-applied on every eligible event
              // while the trigger keeps firing (F5 permanent nature; a
              // transient tier applies it once).
              const int old_stride = entry->stride;
              entry->stride = 0;
              logInjection("P08_stride_stuck", pf_addr,
                           "stride " + std::to_string(old_stride) +
                           " -> 0 (stuck)");
              break;
          }
        }

        if (h5_ptag && h5) {
            const bool already_chained = corrupted_entries.count(h5_pc) > 0;
            // [MDSPEC][H5] Join the candidate addresses generated on this
            // call to the request chain. The hook sits at calculatePrefetch's
            // TAIL, so for stride-affecting modes (P01/P08) the current
            // candidates were built with the OLD stride and the corrupted
            // output appears on the NEXT call for this PC — registering both
            // this call's candidates and (via corrupted_entries below) the
            // later ones is what makes queue→request→fill→demand reachable.
            // pf_request_id/mshr-fill then resolve on these lines.
            for (const auto &ap : addresses) {
                h5->registerPtagBlock(h5_ptag, ap.first, ap.first + line_size);
                h5->registerPtagPrefetch(h5_pfid, ap.first, line_size);
            }
            // pf_train node (L1) — emitted after the mutation so L0→L1 is a
            // real before/after edge. Carries the request-level
            // pf_request_id (≠ fault_id) plus the training-entry evidence
            // the spec requires for P01 (PC/tag, old/new stride, the
            // generated candidate address).
            if (!already_chained) {
                std::ostringstream h5_pc_hex, h5_addr_hex;
                h5_pc_hex << std::hex << h5_pc;
                h5_addr_hex << std::hex << pf_addr;
                h5->notePropEvt("pf_train", {
                    {"fault_id", std::to_string(h5_ptag)},
                    {"pf_request_id", std::to_string(h5_pfid)},
                    {"pc", h5_pc_hex.str()},
                    {"va", h5_addr_hex.str()},
                    {"before", std::to_string(h5_stride_before)},
                    {"after", std::to_string(entry ? entry->stride : 0)},
                    {"field", "stride"},
                });
                corrupted_entries[h5_pc] = {h5_ptag, h5_pfid};
            }
        }
    }

    // [MDSPEC][R4-5.4] P06-a prefetch-as-demand fill classification
    // (see CHAOSPrefetch.hh for the mode contract). Cache::
    // serviceMSHRTargets calls this at the setPrefetched gate for every
    // prefetch-involving fill (from_pref). The faulted VALUE is the
    // fill's demand/prefetch classification — the gate is where that
    // classification becomes the durable line state (CacheBlk::
    // Prefetched), the attribute every downstream classification
    // consumer reads: replacement-policy fill data (data_update.
    // hwPrefetched), the wasPrefetched useful/unused accounting on
    // demand hit / eviction, and the hasBeenPrefetched probes. A marked
    // fill skips setPrefetched — the line enters the cache exactly as a
    // demand fill ("demand" is a legal value from the same run: every
    // demand fill takes exactly that branch). The packet plumbing is
    // untouched (see .hh — rewriting pkt->cmd would push an unrequested
    // response up the CPU side via the FromCPU MSHR-target arm).
    //
    // Eligibility (legal-candidate discipline, spec 03 P06 row): the
    // classification must be LIVE at this fill — demand_merged fills
    // are already demand-classified (a mark there is a void value) and
    // a null blk has no line state to classify; both book attempted and
    // return. The gate condition itself is therefore the eligibility.
    bool
    CHAOSPrefetch::maybeMarkFillAsDemand(Addr line, unsigned blk_size,
                                         bool demand_merged, bool blk_valid)
    {
        // Belt and braces: the registry is only set in P06 mode.
        if (fi_mode != Mode::P06AsDemand) return false;
        // G5 single-fault cap, C11 convention (CHAOSCache
        // maybeCorruptMergeTarget): the cap check runs BEFORE onAttempt,
        // so attempted/eligible freeze exactly at fire time under the
        // campaign cap maxFaults=1 (post-fire fills return here).
        if (max_faults != 0 && faults_injected >= max_faults)
            return false;

        trigger.onAttempt();

        if (demand_merged || !blk_valid) return false;

        // F0-F5 sample the eligible stream; F6 rides the P-family W1
        // event machinery (f6Thunk sets f6_pending at the configured
        // event — dirty_eviction by default; the marking lands at the
        // next eligible fill, the same f6_pending shape maybeCorrupt
        // uses for P01-P08). onF6Event stays at its default-true thunk
        // site — it is NOT called inside this hook, so the R4-5.1-
        // review-I1 double-count shape cannot arise here.
        bool go;
        if (trigger.tier == ChaOSLsuTier::F6) {
            go = f6_pending;
            f6_pending = false;
        } else {
            go = trigger.onEligible();
        }
        if (!go) return false;

        ++faults_injected;

        // [MDSPEC][H5] Register the fault with the propagation tracer:
        // inj node (corr=origin; before/after = the classification pair
        // prefetch->demand, the faulted value of this model) + the whole
        // line in the faulted-byte registry (downstream joins by
        // overlap, corr=addr_fallback). The prefetch-request registry
        // entry allocated right after arms the pf_fill/pf_demand nodes
        // for this line: the queue/issue nodes predate the fault and
        // stay absent (honest gap — the fault happens at fill time, the
        // pf_request_id is request-level identity allocated at marking).
        if (CHAOSPropagation *h5 = CHAOSPropagation::instance()) {
            const uint64_t h5_ptag =
                h5->registerPfFillClassFault(line, blk_size);
            if (h5_ptag)
                h5->notePrefetchRequest(line, blk_size);
        }

        // L0 injection detail line — lsu_obs_core._INJ_RE contract
        // (Tick/Site/mode/old_/new_/faults_injected; unlike the P01
        // logInjection format this one is machine-parseable).
        if (write_log && log_stream && log_stream->stream()) {
            (*log_stream->stream())
                << "Tick: " << curTick()
                << ", Site: P06_fill_class_mark, mode=p06_as_demand"
                << ", old_class=prefetch, new_class=demand"
                << ", line=0x" << std::hex << line << std::dec
                << ", blk_size=" << blk_size
                << ", faults_injected: " << faults_injected
                << "\n";
        }
        return true;
    }

    void
    CHAOSPrefetch::logInjection(const char *site, Addr a,
                                const std::string &detail)
    {
        if (!write_log || !log_stream || !log_stream->stream()) return;
        (*log_stream->stream())
            << "Site: " << site << " Tick: " << curTick()
            << " pf_addr=0x" << std::hex << a << std::dec
            << " " << detail << "\n";
    }

} // namespace gem5
