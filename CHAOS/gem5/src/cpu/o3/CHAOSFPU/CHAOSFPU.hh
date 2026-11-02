#ifndef __CPU_O3_CHAOS_FPU_HH__
#define __CPU_O3_CHAOS_FPU_HH__

#include <map>
#include <random>
#include <string>
#include <utility>
#include <vector>

#include "params/CHAOSFPU.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/o3/dyn_inst_ptr.hh"

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class DynInst; } }

namespace gem5
{

class CHAOSFPU : public SimObject
{
  public:
    CHAOSFPU(const CHAOSFPUParams &p);
    ~CHAOSFPU();

    void startup() override;  // self-attach to CPU.chaosFPU

    // Called from DynInst::execute() AFTER staticInst->execute(). Filters by
    // opClass (FloatAdd/FloatMult/FloatMultAcc + SimdFloat*); XORs the FP
    // result blob. Returns true if an injection happened.
    bool maybeCorrupt(o3::DynInst *dyn_inst);

    // [FSU] Read-only propagation observers. Called from DynInst::execute()
    // (same anchor as maybeCorrupt) and Commit::commitHead(); they never
    // change architectural or microarchitectural state.
    void noteConsumerExecute(o3::DynInst *inst);
    void noteCommit(ThreadID tid, o3::DynInst *inst);

  private:
    BaseCPU *cpu;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t fault_mask;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;
    // Sampling-bias fix (findings.md Phase 2.2/3.0, same as CHAOSL1DForward
    // 7387649): skip a geometric(p=0.1) number of eligible events before
    // the first injection, so maxFaults=1 lands on a seed-dependent event
    // instead of always the first eligible one (same dynamic instruction
    // every rep on a deterministic stream).
    uint64_t events_to_skip = 0;
    // v1.1 Phase 8.2 uniform sampling (design doc §1.7 rule 4): the
    // geometric(p=0.1) skip has mean 10 / P(skip<=30)~=96% — the single
    // fault lands in the FIRST ~30 eligible events for nearly every rep.
    // The driver (campaign.py) dry-runs countOnlyMode to learn N_eligible,
    // then passes a FIXED uniform skip (chaosPickSkip(seed, N_eligible),
    // chaos_event_sample.hh) via eventsToSkip. Sentinel
    // UINT64_MAX (= param default -1) keeps the legacy geometric draw.
    bool fixed_skip_mode = false;
    bool count_only = false;         // consume + count, never corrupt
    uint64_t eligible_count = 0;     // CHAOS_ELIGIBLE_COUNT=<n> at teardown

    // v1.1 Phase 9 patch 1a mode 1 — bitseg field (empty = uniform).
    std::string bitseg;
    // mode 2 — fma_intermediate weighted proxy (E3).
    bool fma_weighted = false;
    // mode 3 — recurring_result_stuck: same fixed mask every event.
    bool recurring_stuck = false;
    uint64_t recurring_mask = 0;      // drawn once on the first event
    bool recurring_mask_drawn = false;
    // mode 4 — rounding_sub: one-ULP opposite-neighbor nudge.
    bool rounding_sub = false;
    // mode 5 — f3_data_dependent: exponent-window gate.
    bool f3_dependent = false;
    int exp_lo = -1, exp_hi = -1;
    // mode 6 — fpsr_suppress: logged count of cleared-flag events.
    bool fpsr_suppress = false;
    uint64_t suppressed_count = 0;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    // [FSU] Pilot identity (set from ooo_proxy CLI; empty = not reported).
    std::string fsu_model, fsu_freq, fsu_load, fsu_submodel;
    uint64_t fsu_eligible_total = 0;

    // [FSU] Faulted-result taint. A fault is "activated" only when a real
    // consumer instruction reads the faulted physical register; the root
    // fault_applied event therefore leaves activated empty, and the L2
    // operand_read event carries activated=1.
    struct FaultedReg {
        uint64_t fault_id = 0;
        uint64_t l0_id = 0, l1_id = 0;
        uint64_t producer_sn = 0;
        Tick tick = 0;
        int tid = 0, reg_class = 0, reg_index = 0;
        uint64_t before = 0, after = 0, mask = 0;
        std::string field;
        bool consumed = false;
    };
    struct TaintedConsumer {
        uint64_t fault_id = 0;
        uint64_t l2_id = 0, l3_id = 0, l4_id = 0;
        uint64_t consumer_sn = 0;
        std::string field;
        bool is_store = false;
        bool has_l3 = false, has_l4 = false, committed = false;
    };
    std::vector<FaultedReg> faulted_regs;
    std::map<uint64_t, TaintedConsumer> tainted_consumers;
    uint64_t next_fault_id = 1;

    void noteFaultApplied(o3::DynInst *inst, int reg_class, int reg_index,
                          uint64_t oldv, uint64_t newv, uint64_t mask);
    uint64_t emitFsu(const char *kind, uint64_t fault_id, uint64_t parent,
                     std::vector<std::pair<std::string, std::string>> kv);
    void noteNotActivated();
    static std::string hex64(uint64_t v);
    static std::string hash64(uint64_t v);

    bool inWindow();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_FPU_HH__
