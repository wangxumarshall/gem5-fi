#include "mem/CHAOSExMon/CHAOSExMon.hh"

#include "base/output.hh"
#include "base/types.hh"
#include "params/CHAOSExMon.hh"
#include "sim/sim_object.hh"

namespace gem5
{

  // namespace-level hook pointer (checked by arch/arm/isa.cc hooks)
  CHAOSExMon *chaos_exmon_g = nullptr;

  CHAOSExMon::CHAOSExMonStats::CHAOSExMonStats(statistics::Group *parent)
      : statistics::Group(parent, "CHAOSExMon"),
        ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                 "Total monitor state corruptions (G5-capped)"),
        ADD_STAT(numClearReservations, statistics::units::Count::get(),
                 "LDXR reservations dropped (clear_reservation mode)"),
        ADD_STAT(numStaleReservations, statistics::units::Count::get(),
                 "STXR false-successes granted (stale_reservation mode)"),
        ADD_STAT(numInWindowChecks, statistics::units::Count::get(),
                 "hook invocations inside the injection window"),
        ADD_STAT(numOutOfWindow, statistics::units::Count::get(),
                 "hook invocations before first_clock (skipped)")
  {
  }

  CHAOSExMon::CHAOSExMon(const CHAOSExMonParams &p)
      : SimObject(p),
        probability(p.probability),
        first_clock(p.firstClock), last_clock(p.lastClock),
        max_faults(p.maxFaults),
        faults_injected_count(0),
        write_log(p.writeLog),
        rng(p.rngSeed),
        stats(std::make_unique<CHAOSExMonStats>(this))
  {
      const std::string &m = p.mode;
      if (m == "clear_reservation")      mode = Mode::ClearReservation;
      else if (m == "stale_reservation") mode = Mode::StaleReservation;
      else
          panic("CHAOSExMon: unknown mode '%s' "
                "(clear_reservation|stale_reservation)", m);

      // Attach the namespace-level hook pointer (arch/arm/isa.cc checks
      // chaos_exmon_g). Single injector per simulation.
      chaos_exmon_g = this;

      if (write_log) {
          log_stream = simout.findOrCreate("exmon_injections.log");
          *(log_stream->stream())
              << "CHAOSExMon attached (ArmISA LOCKADDR/LOCKFLAG hook), mode="
              << m << " probability=" << probability
              << " first_clock=" << first_clock
              << " last_clock=" << last_clock
              << " max_faults=" << max_faults
              << " rng_seed=" << p.rngSeed << "\n";
      }
  }

  CHAOSExMon::~CHAOSExMon()
  {
      if (chaos_exmon_g == this)
          chaos_exmon_g = nullptr;
  }

  bool
  CHAOSExMon::shouldInject()
  {
      // Time window on curTick (1000 ticks/cycle SE convention — same
      // advisory as CHAOSArmTLB; honest limitation, no per-domain cycle
      // resolution).
      if (max_faults && faults_injected_count >= max_faults)
          return false;
      if (last_clock && curTick() > last_clock * 1000)
          return false;
      if (curTick() < first_clock * 1000) {
          stats->numOutOfWindow++;
          return false;
      }
      stats->numInWindowChecks++;
      if (probability >= 1.0f)
          return true;
      std::uniform_real_distribution<float> dist(0.0f, 1.0f);
      return dist(rng) < probability;
  }

  void
  CHAOSExMon::writeLog(const char *type, Addr paddr)
  {
      if (!write_log || !log_stream)
          return;
      *(log_stream->stream())
          << "Tick: " << curTick()
          << ", Site: exclusive_monitor"
          << ", Mode: " << type
          << ", Paddr: 0x" << std::hex << paddr << std::dec
          << ", Count: " << faults_injected_count
          << "\n";
  }

  bool
  CHAOSExMon::maybeClearReservationSC(Addr paddr)
  {
      if (mode != Mode::ClearReservation)
          return false;
      // Persistent-fault semantics: a physically stuck-clear monitor bit
      // fails EVERY store-conditional. The G5 single-fault cap does NOT
      // apply (a one-shot clear at LDXR time is unobservable under O3
      // squash-replay: the replayed LDXR re-establishes the flag before
      // the STXR checks it — verified empirically 2008/2008 lock_flag=1).
      // Window + probability still respected; numFaultsInjected records
      // the first injection (G5-style evidence), numClearReservations the
      // total suppressed STXRs.
      if (last_clock && curTick() > last_clock * 1000)
          return false;
      if (curTick() < first_clock * 1000) {
          stats->numOutOfWindow++;
          return false;
      }
      stats->numInWindowChecks++;
      if (probability < 1.0f) {
          std::uniform_real_distribution<float> dist(0.0f, 1.0f);
          if (dist(rng) >= probability)
              return false;
      }
      stats->numClearReservations++;
      if (faults_injected_count == 0)
          stats->numFaultsInjected++;
      faults_injected_count++;
      writeLog("clear_reservation", paddr);
      return true;
  }

  bool
  CHAOSExMon::maybeStaleReservation(Addr paddr)
  {
      if (mode != Mode::StaleReservation)
          return false;
      if (!shouldInject())
          return false;
      // Grant the STXR a false success: the caller (lockedWriteHandler)
      // returns true without a valid reservation — a lost-update race
      // window opens silently.
      faults_injected_count++;
      stats->numFaultsInjected++;
      stats->numStaleReservations++;
      writeLog("stale_reservation", paddr);
      return true;
  }

} // namespace gem5
