#include "cpu/o3/CHAOSLQ04/CHAOSLQ04.hh"

#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>

#include "base/output.hh"
#include "cpu/o3/CHAOSLQ04/lq04_rules.hh"  // LSU v3.2.10 LQ04 pure rules
#include "cpu/o3/cpu.hh"                   // o3::CPU (chaosLQ04 self-attach)
#include "debug/CHAOSLQ04.hh"
#include "params/CHAOSLQ04.hh"
#include "sim/cur_tick.hh"
#include "sim/eventq.hh"
#include "sim/sim_exit.hh"    // registerExitCallback / exitSimLoop

namespace gem5
{

    CHAOSLQ04::CHAOSLQ04(const CHAOSLQ04Params &p)
        : SimObject(p),
          cpu(p.cpu),
          event_ordinal(p.eventOrdinal),
          max_faults(p.maxFaults),
          count_only(p.countOnly),
          probe_first_n(p.probeFirstN),
          watchdog_cycles(p.watchdogCycles),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        // lq04_rules.hh clamps maxFaults==0 to one injection at decision
        // time; mirror the clamp on the member so the budget bookkeeping
        // and the log line agree.
        if (max_faults == 0)
            max_faults = 1;
        if (write_log) {
            log_stream = simout.create("lq04_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSLQ04: Could not open log file");
            }
        }
    }

    void
    CHAOSLQ04::startup()
    {
        SimObject::startup();
        // Self-attach (LQ04 is O3-only: it hooks the O3 LSQUnit and the
        // LQEntry side channel). A non-O3 cpu must fail loudly, not
        // silently no-op.
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            throw std::runtime_error(
                "CHAOSLQ04: cpu is not an O3CPU. CHAOSLQ04 only supports "
                "O3CPU (it hooks the O3 LSQUnit::executeLoad load-issue "
                "path and the LQEntry side channel). Cast failed.");
        }
        o3cpu->chaosLQ04 = this;

        // Watchdog: if the ordinal-selected injection has not fired within
        // watchdogCycles CPU cycles, the run is stuck (or the target never
        // became eligible). 0 = disabled.
        if (watchdog_cycles) {
            watchdog_event = new EventFunctionWrapper(
                [this]() { this->watchdog(); }, "LQ04 watchdog", true);
            schedule(watchdog_event,
                     o3cpu->clockEdge(Cycles(watchdog_cycles)));
        }
        // Normal exit: pull the watchdog off the event queue so a finished
        // run is never aborted by a stale event during teardown.
        registerExitCallback([this]() {
            if (watchdog_event && watchdog_event->scheduled())
                deschedule(watchdog_event);
        });
        // count-only dry-run: N_eligible at exit (CHAOSLSQFwd /
        // CHAOSL1DForward v1.1 Phase 8.2 family convention; the driver
        // parses the log).
        if (count_only) {
            registerExitCallback([this]() {
                if (write_log && log_stream && log_stream->stream()) {
                    *(log_stream->stream()) << "CHAOS_LQ04_ELIGIBLE_COUNT="
                        << eligible_count << std::endl;
                }
            });
        }
    }

    bool
    CHAOSLQ04::maybeSelect(uint64_t seq, Addr pc, int64_t lq_idx,
                           uint64_t lq_gen, uint64_t attempt_id, Addr addr,
                           unsigned size, uint64_t request_id,
                           bool is_prefetch)
    {
        // A hardware/data prefetch riding the LQ is not the modeled event
        // stream; it must not consume an eligible-Load ordinal.
        if (is_prefetch)
            return false;

        ++eligible_count;

        // Count-only dry-run or probe mode: log the first probeFirstN
        // eligible loads (std::endl flushes every line, so an aborted
        // prefix is salvageable).
        if (probe_logged < probe_first_n) {
            ++probe_logged;
            if (write_log && log_stream && log_stream->stream()) {
                *(log_stream->stream())
                    << "CHAOS_LQ04_ELIGIBLE_PROBE"
                    << ": seq=" << seq
                    << " pc=0x" << std::hex << pc << std::dec
                    << " lq_idx=" << lq_idx
                    << " gen=" << lq_gen
                    << " ordinal=" << eligible_count
                    << " tick=" << curTick() << std::endl;
            }
            DPRINTF(CHAOSLQ04, "CHAOSLQ04: eligible probe sn:%llu "
                    "lq_idx:%lld gen:%llu ordinal:%llu\n",
                    (unsigned long long)seq, (long long)lq_idx,
                    (unsigned long long)lq_gen,
                    (unsigned long long)eligible_count);
        }

        // Dry-run: count (and probe) only, never inject.
        if (count_only)
            return false;

        // F0 ordinal gate: only the eventOrdinal-th eligible load fires
        // (ordinal 0 disables selection).
        if (!chaos_lq04::shouldSelect(eligible_count, event_ordinal))
            return false;
        // Budget gate (0 clamped to 1 inside shouldInject).
        if (!chaos_lq04::shouldInject(injected_count, max_faults))
            return false;

        // Fire: record the target's LQ entry identity.
        target_selected = true;
        target_seq = seq;
        target_lq_idx = (uint64_t)lq_idx;
        target_lq_gen = lq_gen;
        target_request_id = request_id;
        target_attempt_id = attempt_id;
        ++injected_count;

        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream())
                << "CHAOS_LQ04_INJECTION"
                << ": seq=" << seq
                << " pc=0x" << std::hex << pc << std::dec
                << " lq_idx=" << lq_idx
                << " gen=" << lq_gen
                << " request_id=" << request_id
                << " addr=0x" << std::hex << addr << std::dec
                << " size=" << size
                << " eligible=" << eligible_count
                << " ordinal=" << event_ordinal
                << " injected=" << injected_count
                << " tick=" << curTick() << std::endl;
        }
        DPRINTF(CHAOSLQ04, "CHAOSLQ04: selected load sn:%llu lq_idx:%lld "
                "gen:%llu request_id:%llu ordinal:%llu\n",
                (unsigned long long)seq, (long long)lq_idx,
                (unsigned long long)lq_gen,
                (unsigned long long)request_id,
                (unsigned long long)eligible_count);
        return true;
    }

    bool
    CHAOSLQ04::isTarget(uint64_t seq, uint64_t lq_idx, uint64_t lq_gen) const
    {
        if (!target_selected)
            return false;
        // The LQ entry identity (index + generation) is the key; the seq is
        // a defensive cross-check (the entry's instruction is fixed for the
        // lifetime of one (idx, gen) pair).
        return seq == target_seq &&
               chaos_lq04::identityMatches(lq_idx, lq_gen,
                                           target_lq_idx, target_lq_gen);
    }

    void
    CHAOSLQ04::noteRestore(uint64_t seq, uint64_t lq_idx, uint64_t lq_gen,
                           const char *reason)
    {
        // Only the target's restore is interesting; other entries never
        // had a corrupt window.
        if (!isTarget(seq, lq_idx, lq_gen))
            return;
        target_restored = true;
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream())
                << "CHAOS_LQ04_RESTORE"
                << ": seq=" << seq
                << " lq_idx=" << lq_idx
                << " gen=" << lq_gen
                << " reason=" << (reason ? reason : "unknown")
                << " tick=" << curTick() << std::endl;
        }
        DPRINTF(CHAOSLQ04, "CHAOSLQ04: target restored sn:%llu reason=%s\n",
                (unsigned long long)seq, reason ? reason : "unknown");
    }

    void
    CHAOSLQ04::watchdog()
    {
        // The ordinal-selected injection never fired within
        // watchdogCycles: abort loudly so the run cannot be classified as a
        // normal MASKED completion. The line goes to the log file AND to
        // stdout (visible in the captured run output without opening the
        // log).
        std::ostringstream os;
        os << "CHAOS_LQ04_WATCHDOG_EXPIRED"
           << ": selected=" << (target_selected ? 1 : 0)
           << " injected=" << injected_count
           << " eligible=" << eligible_count
           << " ordinal=" << event_ordinal
           << " tick=" << curTick();
        if (write_log && log_stream && log_stream->stream())
            *(log_stream->stream()) << os.str() << std::endl;
        std::cout << os.str() << std::endl;
        exitSimLoop("lq04 watchdog expired", 1);
    }

} // namespace gem5
