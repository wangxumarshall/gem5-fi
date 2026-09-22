// CHAOSProbe.cc — W0.3a read-only OoO occupancy/threshold event probe.
// Four-piece SimObject family pattern (template: CHAOSFreeList/). See
// CHAOSProbe.hh for the contract. Nothing here mutates CPU state.

#include "cpu/o3/CHAOSProbe/CHAOSProbe.hh"

#include <iostream>
#include <sstream>

#include "cpu/o3/cpu.hh"          // o3::CPU: o3ROB()/o3IEW()/physFreeList()
#include "cpu/o3/rob.hh"          // ROB::countInsts / numFreeEntries
#include "cpu/o3/inst_queue.hh"   // InstructionQueue::getCount / numFreeEntries
#include "cpu/reg_class.hh"       // RegClassType: Int/Float/VecRegClass
#include "cpu/thread_context.hh"  // ThreadContext::Halted
#include "params/CHAOSProbe.hh"
#include "sim/sim_exit.hh"        // registerExitCallback

namespace gem5
{

    CHAOSProbe::CHAOSProbe(const CHAOSProbeParams &p)
        : SimObject(p),
          cpu(p.cpu),
          sample_every(p.sampleEvery),
          rob_threshold_pct(p.robThresholdPct),
          iq_threshold_pct(p.iqThresholdPct),
          fl_int_le(p.flIntLe),
          fl_float_le(p.flFloatLe),
          fl_vec_le(p.flVecLe),
          write_log(p.writeLog),
          sampleEvent([this] { this->tick(); }, name() + ".sample")
    {
        if (sample_every == 0) {
            // Cycles(0) would reschedule at the current tick -> livelock.
            warn("CHAOSProbe: sampleEvery=0 clamped to 1 (same-tick "
                 "reschedule would livelock the event queue).\n");
            sample_every = 1;
        }
        if (write_log) {
            log_stream = simout.create("chaos_probe.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSProbe: Could not open log file");
        }
    }

    CHAOSProbe::~CHAOSProbe() {}

    void
    CHAOSProbe::startup()
    {
        SimObject::startup();
        o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSProbe: cpu is not an O3CPU; probe disabled.\n");
            return;
        }

        // Derive ROB/IQ capacities from PUBLIC accessors only: both queues
        // are empty at startup, so occupancy + free == capacity. (ROB:
        // numFreeEntries() = numEntries - numInstsInROB, rob.cc; IQ:
        // numFreeEntries() sums the IQUnits' _freeEntries, inst_queue.cc.)
        // This tracks whatever --rob / IQUnit numEntries the config set —
        // no hardcoded 64/128 and no private-member access.
        rob_capacity = (uint64_t)o3cpu->o3ROB().countInsts()
                     + (uint64_t)o3cpu->o3ROB().numFreeEntries();
        iq_capacity  = (uint64_t)o3cpu->o3IEW().instQueue.getCount(0)
                     + (uint64_t)o3cpu->o3IEW().instQueue.numFreeEntries();
        rob_threshold = rob_threshold_pct * rob_capacity / 100;
        iq_threshold  = iq_threshold_pct  * iq_capacity  / 100;

        // End-of-sim summary via exit callback (CHAOSIQ.cc:186-192 pattern —
        // always fires, unlike the destructor which may run after output
        // teardown).
        registerExitCallback([this]() { this->report(); });

        // First sample one sampleEvery from now (CHAOSReg.hh:61 periodic
        // event pattern: EventFunctionWrapper + cpu clockEdge scheduling).
        schedule(sampleEvent, o3cpu->clockEdge(Cycles(sample_every)));
    }

    bool
    CHAOSProbe::anyThreadActive() const
    {
        for (ThreadID tid = 0; tid < cpu->numThreads; ++tid) {
            ThreadContext *tc = cpu->getContext(tid);
            if (tc && tc->status() != ThreadContext::Halted)
                return true;
        }
        return false;
    }

    void
    CHAOSProbe::tick()
    {
        if (!o3cpu)
            return;

        // ---- one READ-ONLY sample (no state is written) ----
        const uint64_t rob_occ = (uint64_t)o3cpu->o3ROB().countInsts();
        const uint64_t iq_occ =
            (uint64_t)o3cpu->o3IEW().instQueue.getCount(0);
        const uint64_t fl_int =
            (uint64_t)o3cpu->physFreeList().numFreeRegs(IntRegClass);
        const uint64_t fl_float =
            (uint64_t)o3cpu->physFreeList().numFreeRegs(FloatRegClass);
        const uint64_t fl_vec =
            (uint64_t)o3cpu->physFreeList().numFreeRegs(VecRegClass);

        ++samples;
        if (rob_occ > rob_threshold) ++rob_over;
        if (iq_occ > iq_threshold) ++iq_over;
        if (fl_int <= fl_int_le) ++fl_int_le_hits;
        if (fl_float <= fl_float_le) ++fl_float_le_hits;
        if (fl_vec <= fl_vec_le) ++fl_vec_le_hits;
        if (rob_occ > rob_max) rob_max = rob_occ;
        if (iq_occ > iq_max) iq_max = iq_occ;
        if (fl_int < fl_int_min) fl_int_min = fl_int;
        if (fl_float < fl_float_min) fl_float_min = fl_float;
        if (fl_vec < fl_vec_min) fl_vec_min = fl_vec;

        // Keep sampling while some thread is alive; when all halt, stop
        // rescheduling (the exit callback still prints the summary).
        if (anyThreadActive() && !sampleEvent.scheduled())
            schedule(sampleEvent, o3cpu->clockEdge(Cycles(sample_every)));
    }

    std::string
    CHAOSProbe::summaryLine() const
    {
        // Field names embed the ACTUAL thresholds so an override can never
        // make the label lie; the defaults reproduce the plan interface
        // verbatim: robOver80 iqOver80 flIntLe8 flFloatLe12 flVecLe6.
        // mins print 0 when nothing was sampled (sentinel UINT64_MAX).
        std::ostringstream os;
        os << "CHAOS_PROBE"
           << " samples=" << samples
           << " robOver" << rob_threshold_pct << "=" << rob_over
           << " iqOver" << iq_threshold_pct << "=" << iq_over
           << " flIntLe" << fl_int_le << "=" << fl_int_le_hits
           << " flFloatLe" << fl_float_le << "=" << fl_float_le_hits
           << " flVecLe" << fl_vec_le << "=" << fl_vec_le_hits
           << " robMax=" << rob_max
           << " iqMax=" << iq_max
           << " flIntMin=" << (samples ? fl_int_min : 0)
           << " flFloatMin=" << (samples ? fl_float_min : 0)
           << " flVecMin=" << (samples ? fl_vec_min : 0);
        return os.str();
    }

    void
    CHAOSProbe::report() const
    {
        // Primary machine-readable interface: ONE stdout line at end of sim
        // (tools/event_density.py parses it from the stdout capture). The
        // extra chaos_probe.log copy is provenance only (writeLog).
        std::cout << summaryLine() << std::endl;
        if (write_log && log_stream && log_stream->stream())
            *(log_stream->stream()) << summaryLine() << std::endl;
    }

} // namespace gem5
