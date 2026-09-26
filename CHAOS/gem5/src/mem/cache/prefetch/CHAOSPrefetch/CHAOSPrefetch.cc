// CHAOSPrefetch.cc — LSU W8 P-series prefetcher injector implementation.
// See CHAOSPrefetch.hh for mode semantics and honest boundary.

#include "mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetch.hh"

#include <string>

#include "sim/sim_exit.hh"        // registerExitCallback (W2 summary line)

namespace gem5
{

    CHAOSPrefetch *CHAOSPrefetch::f6Consumer = nullptr;

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
    }

    CHAOSPrefetch::~CHAOSPrefetch()
    {
        if (prefetch::Stride::chaosPrefetchHook == this)
            prefetch::Stride::chaosPrefetchHook = nullptr;
        if (f6Consumer == this) {
            f6Consumer = nullptr;
            chaosLsuF6Notify = nullptr;
        }
    }

    CHAOSPrefetch::Mode
    CHAOSPrefetch::stringToMode(const std::string &s)
    {
        if (s == "p02_confidence_corrupt") return Mode::P02ConfidenceCorrupt;
        if (s == "p03_addr_subst")         return Mode::P03AddrSubst;
        if (s == "p05_drop_dup")           return Mode::P05DropDup;
        if (s == "p08_stride_stuck")       return Mode::P08StrideStuck;
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
        trigger.onAttempt();

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
