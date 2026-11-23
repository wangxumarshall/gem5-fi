#ifndef __CPU_O3_CHAOS_PROBE_HH__
#define __CPU_O3_CHAOS_PROBE_HH__

// CHAOSProbe — W0.3a read-only OoO occupancy/threshold event probe
// (docs/superpowers/plans/2026-09-22-ooo-w0-foundation.md Task 3;
//  docs/gem5-fi/ooo north-star W0.3). NOT an injector: it never writes
// architectural or µarch state (proof: the reg_chain golden checksum is
// unchanged with the probe attached). Every `sampleEvery` CPU cycles it
// samples:
//   - ROB occupancy          o3ROB().countInsts()          (rob.hh)
//   - IQ  occupancy (IEW)    o3IEW().instQueue.getCount(0) (inst_queue.hh)
//   - freelist remaining     physFreeList().numFreeRegs(Int/Float/VecRegClass)
// and bumps over/low-watermark counters; ONE summary line is printed at
// end of sim (see CHAOSProbe.cc report()). Self-attaches like CHAOSFreeList:
// startup() dynamic_casts p.cpu to o3::CPU — no gem5 source hook needed.

#include <cstdint>
#include <string>

#include "params/CHAOSProbe.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"

namespace gem5 { namespace o3 { class CPU; } }

namespace gem5
{

class CHAOSProbe : public SimObject
{
  public:
    CHAOSProbe(const CHAOSProbeParams &p);
    ~CHAOSProbe();

    // Self-attach (dynamic_cast O3CPU, CHAOSFreeList.cc:155-165 pattern),
    // derive capacities, register the exit callback, schedule first sample.
    void startup() override;

  private:
    void tick();                 // one sample: read 5 occupancies, bump counters
    void report() const;         // end-of-sim CHAOS_PROBE summary line
    std::string summaryLine() const;
    bool anyThreadActive() const; // halt detection (CHAOSPhysReg pattern)

    BaseCPU *cpu;
    o3::CPU *o3cpu = nullptr;    // resolved at startup(); nullptr = disabled

    uint64_t sample_every;
    uint64_t rob_threshold_pct;
    uint64_t iq_threshold_pct;
    uint64_t fl_int_le;
    uint64_t fl_float_le;
    uint64_t fl_vec_le;
    bool write_log;

    // Capacities derived at startup() from public invariants (queues are
    // empty then, so free == capacity): ROB = countInsts()+numFreeEntries()
    // (rob.cc numFreeEntries() = numEntries - numInstsInROB), IQ =
    // getCount(0)+numFreeEntries(). Avoids hardcoding numROBEntries / IQ=64
    // and avoids touching private members of ROB/InstructionQueue.
    uint64_t rob_capacity = 0;
    uint64_t iq_capacity = 0;
    uint64_t rob_threshold = 0;  // floor(rob_threshold_pct% * rob_capacity)
    uint64_t iq_threshold = 0;   // floor(iq_threshold_pct%  * iq_capacity)

    EventFunctionWrapper sampleEvent;  // CHAOSReg.hh:61 periodic-event pattern
    OutputStream *log_stream = nullptr;

    // Counters (all per-sample; mins init to "unseen").
    uint64_t samples = 0;
    uint64_t rob_over = 0;
    uint64_t iq_over = 0;
    uint64_t fl_int_le_hits = 0;
    uint64_t fl_float_le_hits = 0;
    uint64_t fl_vec_le_hits = 0;
    uint64_t rob_max = 0;
    uint64_t iq_max = 0;
    uint64_t fl_int_min = UINT64_MAX;
    uint64_t fl_float_min = UINT64_MAX;
    uint64_t fl_vec_min = UINT64_MAX;
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_PROBE_HH__
