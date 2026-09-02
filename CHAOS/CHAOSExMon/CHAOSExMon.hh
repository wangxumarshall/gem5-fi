#ifndef __MEM_CHAOSExMon_HH__
#define __MEM_CHAOSExMon_HH__

#include <random>
#include <string>
#include <cstdint>

#include "sim/sim_object.hh"
#include "base/types.hh"
#include "base/output.hh"
#include "mem/request.hh"
#include "params/CHAOSExMon.hh"
#include "sim/stats.hh"

namespace gem5
{

  // S3-7 (plan §5.4B): exclusive-monitor fault injector. The ARM local
  // exclusive monitor in gem5 SE is implemented in ArmISA as two misc
  // registers — MISCREG_LOCKADDR + MISCREG_LOCKFLAG (arch/arm/isa.cc:
  // handleLockedRead on LDXR, lockedWriteHandler on STXR). CacheBlk::
  // lockList / AbstractMemory::lockedAddrList are the no-ISA-monitor paths
  // (x86-style) and are NOT used on ARM. CHAOSExMon hooks the ISA points
  // via the namespace-level chaos_exmon_g pointer (lockedWriteHandler is a
  // free template with no object context):
  //   clear_reservation  — drop the reservation an LDXR just placed
  //                       (LOCKFLAG=false; chronic STXR failure)
  //   stale_reservation  — let a STXR succeed without a valid reservation
  //                       (SC false-success — lost-update SDC)
  class CHAOSExMon : public SimObject
  {
    public:
      CHAOSExMon(const CHAOSExMonParams &p);
      ~CHAOSExMon();

      enum class Mode {
          ClearReservation,
          StaleReservation
      };

      // Hook (ArmISA::lockedWriteHandler success path, at the SC
      // architectural decision point): clear_reservation makes this STXR
      // fail despite a valid reservation. Robust to O3 squash-replay
      // (a flag-clear at LDXR time is re-established by the replayed LDXR).
      bool maybeClearReservationSC(Addr paddr);

      // Hook 2 (lockedWriteHandler failure branch, BEFORE the SC is
      // rejected): stale_reservation overrides the failure. Returns true
      // when the STXR must falsely succeed.
      bool maybeStaleReservation(Addr paddr);

    private:
      Mode mode;
      float probability;
      uint64_t first_clock, last_clock;
      uint64_t max_faults;
      uint64_t faults_injected_count;
      bool write_log;
      std::mt19937 rng;
      OutputStream *log_stream = nullptr;

      bool shouldInject();
      void writeLog(const char *type, Addr paddr);

      struct CHAOSExMonStats : public statistics::Group
      {
          statistics::Scalar numFaultsInjected;
          statistics::Scalar numClearReservations;   // LDXR reservations dropped
          statistics::Scalar numStaleReservations;   // STXR false-successes
          statistics::Scalar numInWindowChecks;      // hook invocations in window
          statistics::Scalar numOutOfWindow;         // hook invocations pre-window

          CHAOSExMonStats(statistics::Group *parent);
      };

      std::unique_ptr<CHAOSExMonStats> stats;
  };

  // namespace-level hook pointer (checked by arch/arm/isa.cc hooks)
  extern CHAOSExMon *chaos_exmon_g;

} // namespace gem5

#endif // __MEM_CHAOSExMon_HH__
