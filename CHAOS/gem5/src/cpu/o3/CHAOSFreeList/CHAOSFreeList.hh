#ifndef __CPU_O3_CHAOS_FREE_LIST_HH__
#define __CPU_O3_CHAOS_FREE_LIST_HH__

#include <random>
#include <string>

#include "params/CHAOSFreeList.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class UnifiedFreeList; } }

namespace gem5
{

class CHAOSFreeList : public SimObject
{
  public:
    CHAOSFreeList(const CHAOSFreeListParams &p);
    ~CHAOSFreeList();

    void startup() override;  // self-attach to UnifiedFreeList.chaosFreeList

    // Called from UnifiedFreeList::getReg AFTER popping the front physReg.
    // `type` is the reg class; `popped` is the physReg that will be returned
    // to the caller (by ref — pop_wrong may mutate it). The injector may also
    // RE-ADD a currently-allocated physReg back to the free list (mark_free ->
    // history residue). Returns true if an injection happened this call.
    bool maybeCorrupt(int class_value, PhysRegIdPtr &popped);

  private:
    enum class Mode { MarkFree, PopWrong };
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m);

    BaseCPU *cpu;
    Mode fi_mode;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
    // mark_free: pick a currently-allocated (not-free) physReg of the class,
    // return its index or -1 (honest no-op if no candidate). Used to RE-ADD it
    // to the free list so it's re-handed-out while still held.
    int pickAllocatedPhysReg(int class_value, int num_phys, o3::CPU *o3cpu);
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_FREE_LIST_HH__
