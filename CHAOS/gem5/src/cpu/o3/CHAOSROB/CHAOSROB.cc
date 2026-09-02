#include "cpu/o3/CHAOSROB/CHAOSROB.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/rob.hh"           // ROB
#include "cpu/o3/dyn_inst.hh"      // DynInst, getFault, status
#include "debug/CHAOSROB.hh"
#include "params/CHAOSROB.hh"

namespace gem5
{

    CHAOSROB::CHAOSROB(const CHAOSROBParams &p)
        : SimObject(p),
          cpu(p.cpu),
          fi_mode(stringToMode(p.mode)),
          field(stringToField(p.field)),
          distance_from_head(p.distanceFromHead),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          fault_mask(p.faultMask),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("rob_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSROB: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        }
    }

    CHAOSROB::~CHAOSROB() {}

    CHAOSROB::Mode
    CHAOSROB::stringToMode(const std::string &s) {
        if (s == "entry_bitflip") return Mode::EntryBitflip;
        if (s == "exc_suppress") return Mode::ExcSuppress;
        return Mode::EntryBitflip;
    }

    const char*
    CHAOSROB::modeToString(CHAOSROB::Mode m) {
        switch (m) {
            case Mode::EntryBitflip: return "entry_bitflip";
            case Mode::ExcSuppress: return "exc_suppress";
        }
        return "entry_bitflip";
    }

    CHAOSROB::Field
    CHAOSROB::stringToField(const std::string &s) {
        if (s == "result") return Field::Result;
        if (s == "done") return Field::Done;
        if (s == "exc_status") return Field::ExcStatus;
        if (s == "dest_phys") return Field::DestPhys;
        if (s == "spec") return Field::Spec;
        return Field::ExcStatus;
    }

    bool
    CHAOSROB::inWindow() {
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
    CHAOSROB::maybeCorrupt(ThreadID tid, o3::DynInstPtr &head_inst)
    {
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;

        if (fi_mode == Mode::ExcSuppress) {
            // §2.3 exc_suppress: clear the head's fault -> a pending
            // SError/DUE is silently swallowed (DUE->SDC conversion).
            Fault &fref = head_inst->getFault();
            Fault old = fref;
            fref = NoFault;
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_retireHead, mode=exc_suppress, tid=" << (int)tid
                    << ", head_sn=" << head_inst->seqNum
                    << ", cleared_fault=" << (old ? "yes" : "none")
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        } else if (fi_mode == Mode::EntryBitflip) {
            // §2.3 entry_bitflip: flip a field of the entry at distance D
            // from head. exc_status/done: toggle CanCommit (clear => the
            // instruction can't commit -> stall/Crash; set => re-enable).
            int D = distance_from_head;
            if (D < 0) D = (int)(rng() % 4);
            o3::DynInstPtr target = o3cpu->o3ROB().getEntryAtDistance(tid, D);
            if (!target) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: rob_retireHead, mode=entry_bitflip"
                        << " — NO entry at D=" << D << " (skipped)." << std::endl;
                }
                return false;
            }
            // toggle CanCommit on the target (the done/exc_status proxy).
            if (target->readyToCommit()) target->clearCanCommit();
            else                          target->setCanCommit();
            faults_injected_count++;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Site: rob_retireHead, mode=entry_bitflip"
                    << ", field=" << (field == Field::ExcStatus ? "exc_status" : "done")
                    << ", tid=" << (int)tid << ", D=" << D
                    << ", target_sn=" << target->seqNum
                    << ", faults_injected: " << faults_injected_count
                    << std::endl;
            }
            return true;
        }
        return false;
    }

    // spec_leak (method1 speculative-state-leak) is DEFERRED — needs the
    // squash path edit (don't roll back a wrong-path µop's phys-reg write).
    // §2.3 patch 2.

    void
    CHAOSROB::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSROB: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        o3cpu->o3ROB().setChaosROB(this);
    }

} // namespace gem5
