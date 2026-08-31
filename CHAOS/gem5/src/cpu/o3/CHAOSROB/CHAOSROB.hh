#ifndef __CPU_O3_CHAOS_ROB_HH__
#define __CPU_O3_CHAOS_ROB_HH__

#include <random>
#include <string>

#include "params/CHAOSROB.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/o3/dyn_inst_ptr.hh"  // DynInstPtr

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class ROB; } }

namespace gem5
{

class CHAOSROB : public SimObject
{
  public:
    CHAOSROB(const CHAOSROBParams &p);
    ~CHAOSROB();

    void startup() override;  // self-attach to ROB.chaosROB

    // Called from ROB::retireHead AFTER popping the head DynInst (before
    // cpu->removeFrontInst). For entry_bitflip: the entry at distance D from
    // head has a field bit flipped. For exc_suppress: the head's fault is
    // cleared (NoFault) so a pending SError/DUE is swallowed.
    // Returns true if an injection happened this call.
    bool maybeCorrupt(ThreadID tid, o3::DynInstPtr &head_inst);

  private:
    enum class Mode { EntryBitflip, ExcSuppress };
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m);

    enum class Field { Result, Done, ExcStatus, DestPhys, Spec };
    static Field stringToField(const std::string &s);

    BaseCPU *cpu;
    Mode fi_mode;
    Field field;
    int distance_from_head;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t fault_mask;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_ROB_HH__
