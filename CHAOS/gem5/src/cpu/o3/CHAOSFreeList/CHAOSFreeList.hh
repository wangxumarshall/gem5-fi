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

    // W4 final D19 drop_release (ooo 04-design-matrix R20, 空闲表·丢失释放,
    // F1 "一次性触发持续影响"): called from UnifiedFreeList::addReg BEFORE
    // the push. Return true = SUPPRESS this one release — the freed physReg
    // is NOT re-added, the free pool permanently shrinks by one. Covers BOTH
    // runtime release paths (rename.cc removeFromHistory commit release +
    // freeingInProgress post-squash drain); construction-time init is safe
    // (chaosFreeList is nullptr while PhysRegFile::initFreeList runs).
    bool maybeDropRelease(int class_value, PhysRegIdPtr freed_reg);

    // W4 final D22 head_stuck (ooo 04-design-matrix R23, 空闲表头/尾指针·
    // 卡死, F5) — HONEST APPROXIMATION (spike B: gem5 SimpleFreeList is a
    // std::queue with NO explicit head/tail pointer registers): called from
    // SimpleFreeList::getReg BEFORE the pop. Armed once at the first
    // in-window eligible getReg (the ONLY faults_injected_count increment);
    // from then on EVERY getReg returns the SAME stuck id and the queue
    // NEVER advances (no pop) — the pre-approved "反复返回同项不真正 pop
    // （头卡死）" proxy. `front_reg` is in/out: on a true return it holds
    // the stuck id and the caller MUST NOT pop. Other modes: strict false.
    bool maybeStuckHead(int class_value, PhysRegIdPtr &front_reg);

  private:
    enum class Mode { MarkFree, PopWrong, MarkFreeEvent, DropRelease,
                      HeadBitflip, HeadBitflip2, HeadStuck };
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m);

    // W4 final D19/D22 end-of-run evidence: final free-pool sizes + (D22)
    // total head_stuck exposures. Registered via registerExitCallback in
    // the ctor (the CHAOSPhysReg.cc:77 ReadTraceFinal pattern). Comparing
    // an injected run against a zero-injection control (same seed, window
    // never reached) shows the D19 permanent -1 shrink.
    void finalSummary();

    BaseCPU *cpu;
    Mode fi_mode;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;

    // W4.5 D18 mark_free_event: trigger threshold — the injection is only
    // eligible while the INT free-list remaining count (post-pop, i.e. at
    // the getReg moment) is at or below this (04-design-matrix R19: 空闲表
    // 剩余项数低于阈值, 建议 ≤8).
    uint64_t event_threshold;

    // W4.5 D17/D18 evidence watcher: after a mark_free(_event) injection
    // re-adds an ALLOCATED idx to the free list, remember it and log the
    // first subsequent getReg pop of that idx — the SECOND allocation = the
    // duplicate the model creates (两条指令共享同一物理寄存器). -1 = idle.
    int dup_watch_idx = -1;

    // W4 final D22 head_stuck state: armed ONCE at the first in-window
    // eligible getReg (the fault's creation), permanent until end of run.
    // Every subsequent getReg hands out hs_stuck_idx without popping.
    // hs_bit/hs_polarity record the forced bit (the 04-matrix "指针寄存器
    // 一比特永久固定 0/1" flavor); hs_bit == -1 = raw freeze (forcing left
    // the valid index range).
    bool hs_armed = false;
    int hs_stuck_idx = -1;
    int hs_bit = -1;
    int hs_polarity = 0;
    uint64_t hs_exposures = 0;  // no-pop hand-outs (persistence evidence;
                                 // detailed logging capped at the first 10)

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
