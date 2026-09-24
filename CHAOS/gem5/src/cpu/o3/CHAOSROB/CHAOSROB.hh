#ifndef __CPU_O3_CHAOS_ROB_HH__
#define __CPU_O3_CHAOS_ROB_HH__

#include <random>
#include <string>
#include <vector>

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
    // cleared (NoFault) so a pending SError/DUE is swallowed. For the W5
    // stuck modes: retire-time read-back of the armed entry's field (the
    // "该 ROB 项存活期间持续带着这个缺陷" persistence evidence).
    // Returns true if an injection happened this call.
    bool maybeCorrupt(ThreadID tid, o3::DynInstPtr &head_inst);

    // W5.1-W5.3 (ooo 04-design-matrix D25-D31, Int Dispatch/ROB): called from
    // ROB::insertInst — the ROB-entry WRITE path (the TC'23 site: the fault is
    // in the entry's PC / dest-register-id field as the entry is written into
    // the ROB, before the instruction completes). Injects into the entry
    // being written (the inserting inst): pc_bitflip/pc_bitflip2 flip 1/2
    // random bits of the pcState pc address; destid_bitflip/destid_bitflip2
    // flip 1/2 random bits of a random integer dest physReg index;
    // destid_swap_active replaces it with the dest physReg of another
    // ROB-resident in-flight instruction; pc_stuck/destid_stuck arm ONE
    // stuck-at bit (F5 write-path mask, the f5_rat_stuck precedent) applied
    // to the armed entry's field at its write. Returns true on injection.
    bool maybeCorruptEntry(ThreadID tid, const o3::DynInstPtr &inst);

  private:
    enum class Mode {
        EntryBitflip, ExcSuppress,
        PcBitflip, PcBitflip2, PcStuck,
        DestIdBitflip, DestIdBitflip2, DestIdSwapActive, DestIdStuck
    };
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m);

    enum class Field { Result, Done, ExcStatus, DestPhys, Spec };
    static Field stringToField(const std::string &s);

    // W5 D30 destid_swap_active: one ROB-resident candidate dest.
    struct RobDestCand { int phys_idx; int dist; uint64_t sn; };

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

    // W5 stuck (D27/D31) state: ONE armed ROB entry (identified by its
    // seqNum — unique per instruction) + ONE bit + polarity. The write-path
    // mask applies at the armed entry's insert (the single write of a
    // ROB-resident entry's PC/destId field — gem5 never rewrites these
    // fields post-insert, so persistence = value permanence, verified by
    // the retire-time read-back in maybeCorrupt).
    bool stuck_armed = false;
    bool stuck_readback_done = false;
    uint64_t stuck_sn = 0;
    int stuck_bit = -1;
    int stuck_polarity = 0;
    int stuck_dest_slot = -1;   // destid_stuck: which renamedDestIdx slot
    uint64_t stuck_exposures = 0;

    // shared helpers
    int collectIntDestSlots(const o3::DynInstPtr &inst,
                            std::vector<int> &slots);
    int collectRobActiveDests(int cur_idx, uint64_t self_sn,
                              o3::CPU *o3cpu, ThreadID tid,
                              std::vector<RobDestCand> &cands);
    bool maybeStuckEntryWrite(ThreadID tid, const o3::DynInstPtr &inst);
    void checkStuckReadback(const o3::DynInstPtr &head_inst);
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_ROB_HH__
