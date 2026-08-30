#ifndef __CPU_O3_CHAOS_RENAME_MAP_HH__
#define __CPU_O3_CHAOS_RENAME_MAP_HH__

#include <random>
#include <map>
#include <memory>
#include <string>

#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "cpu/reg_class.hh"
#include "params/CHAOSRenameMap.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"  // Cycles, EventFunctionWrapper

namespace gem5
{

namespace o3 { class CPU; }

// CHAOSRenameMap — RAT (rename map) fault injector (plan §5.2, S1-2).
//
// method1 (Cholesky x[0]) core hypothesis: "映射张冠李戴/历史残留" — an arch
// reg's mapping is swapped to ANOTHER currently-allocated physReg, so a
// later read returns the value of a DIFFERENT live variable (history residue,
// popcount 21-32 multi-bit, not a single-bit SEU). This is F5 (legal-domain
// substitute) on the RAT — the MAPPING DECISION layer, invisible to a
// register-cell injector (CHAOSPhysReg).
//
// Drives faults from its own attackEvent (RAT is not a SimObject, so no
// self-attach — holds a cpu pointer, reaches frontRenameMap() like CHAOSPhysReg).
class CHAOSRenameMap : public SimObject
{
  public:
    CHAOSRenameMap(const CHAOSRenameMapParams &p);
    ~CHAOSRenameMap();

    void startup() override;  // arm attackEvent at firstClock

  private:
    enum class Mode { MapBitFlip, F5Substitute, F4FieldStuck };
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m);

    enum class RegClassSel { Integer, FloatingPoint, Vector };
    static RegClassSel stringToRegClassSel(const std::string &s);

    o3::CPU *cpu;
    float probability;
    Mode fi_mode;
    RegClassSel reg_target_class;
    int target_arch_idx;
    uint64_t fault_mask;
    int num_bits_to_change;
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;
    std::string semantic_role;

    // rng via lambda (not member order) — avoids rng_seed==0 -> rd() UB.
    std::mt19937 rng;
    std::random_device rd;
    std::geometric_distribution<unsigned> inter_fault_cycles_dist;
    OutputStream *log_stream;

    EventFunctionWrapper attackEvent;
    EventFunctionWrapper periodicCheck;  // for f4_field_stuck persistence

    void scheduleAttackEvent(Cycles delay);
    void attackCheck();
    void processFault(ThreadID tid);
    void writeLog(const std::string &type, ThreadID tid, int arch_idx,
                  int old_phys, int new_phys, uint64_t mask);

    // f4_field_stuck: {tid, arch_idx} -> stuck physRegIdx (persisted)
    struct StuckMapping { int arch_idx; int phys_idx; };
    std::map<std::pair<ThreadID, int>, StuckMapping> stuck_mappings;
    void checkPermanent();

    struct CHAOSRenameMapStats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numMapBitFlips;
        statistics::Scalar numF5Substitutes;
        statistics::Scalar numF4FieldStuck;
        statistics::Scalar numLegalityRejects;  // F5 targets rejected (free/invalid)
        CHAOSRenameMapStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSRenameMapStats> stats;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_RENAME_MAP_HH__
