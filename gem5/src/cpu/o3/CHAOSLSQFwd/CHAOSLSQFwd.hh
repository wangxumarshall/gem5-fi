#ifndef __CPU_O3_CHAOS_LSQ_FWD_HH__
#define __CPU_O3_CHAOS_LSQ_FWD_HH__

#include <random>
#include <bitset>
#include <memory>
#include <functional>
#include <unordered_map>
#include <vector>

#include "base/output.hh"
#include "cpu/o3/chaos_l0.hh"           // LSU W3 L0 funnel
#include "cpu/o3/chaos_lsu_trigger.hh"  // LSU W2 event-normalized tiers
#include "cpu/o3/dyn_inst_ptr.hh"       // [LSU W5 L04] DynInstPtr (resp-pair)
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSLSQFwd.hh"
#include "sim/sim_object.hh"

namespace gem5
{

namespace o3 { class CPU; }

// [MDSPEC][R4-5.7] S10 StoreSet lazy candidate scan (L04 RespPairScan
// precedent): fills the live-SSID candidate set. Declared before the class
// because the S10 static hook bodies (private members below) reference it.
using S10SsidScan = std::function<void(std::vector<uint64_t> &)>;

// CHAOSLSQFwd — store-to-load forwarding-path fault injector for O3CPU.
//
// A load that hits a younger-pending store in the store queue gets its data
// via a memcpy (lsq_unit.cc FullAddrRangeCoverage branch). This injector
// corrupts that forwarded data with probability `probability` per forwarding
// event, modeling the store-buffer forwarding-path corruption localized by
// reproduce-method2 v3 (core 179's reload `ldr` of just-read input — multi-bit,
// mantissa-concentrated, sign-immune). Distinct from CHAOSPhysReg (which
// corrupts a physical register cell): this corrupts the *datapath* between
// store queue and load, which is invisible to a register-only injector.
class CHAOSLSQFwd : public SimObject
{
  public:
    CHAOSLSQFwd(const CHAOSLSQFwdParams &p);
    ~CHAOSLSQFwd();

    // [MDSPEC][R4-1] Seq/idx/request_id correlation keys for ONE
    // store->load forward (user ruling 2026-10-20: these are the PRIMARY
    // correlation keys; address-only correlation is a labeled fallback).
    // Filled by lsq_unit.cc at the forward site — raw values only, so
    // lsq_unit.cc needs no CHAOS types beyond this header.
    //   store_*: the producer store whose SQ data is the forward source
    //            (sq_idx = DynInst::sqIdx, same source as the sq_execute/
    //            sq_writeback/sq_complete events, so the keys join 1:1);
    //   load_*:  the consuming load whose memData gets corrupted
    //            (lq_idx = the read() load_idx parameter, same source as
    //            the lq_read events);
    //   *_request_id: the Request-stamped inst seq (getReqInstSeqNum),
    //            0 when the request is not seq-stamped (lsq_sendfrag
    //            convention).
    // store_dyn_inst_seq == 0 marks "seq genuinely unavailable" — the
    // emitted event then carries corr=addr_fallback.
    struct FwdCorrelKeys {
        uint64_t store_dyn_inst_seq = 0;
        long long sq_idx = -1;
        uint64_t store_request_id = 0;
        uint64_t load_dyn_inst_seq = 0;
        long long lq_idx = -1;
        uint64_t load_request_id = 0;
    };

    // Called from lsq_unit.cc after the forward memcpy, BEFORE the data is
    // packetized and written back to the load. If the RNG fires, this flips
    // bits in `data` (one byte selected by byteOffset). Hot-path: when
    // probability==0 or outside the [firstClock,lastClock] window, returns
    // immediately with no work.
    void corrupt(uint8_t *data, unsigned size, Addr vaddr,
                 const FwdCorrelKeys &keys);

    // §2.4 fwd_source_sub (F5, Phase 4.2 — method1 wrong-source forwarding):
    // called from lsq_unit.cc at the forwarding DECISION point, after a
    // store entry is selected as the forward source (FullAddrRangeCoverage)
    // and BEFORE the memcpy. If the RNG fires, the load's data is copied
    // from a DIFFERENT (older) SQ entry instead — the load receives the
    // wrong store's data (wrong-source forward, 张冠李戴). Parameters are
    // raw pointers/sizes so lsq_unit.cc doesn't need CHAOS types. Returns
    // true if the substitution happened (the caller skips its own memcpy).
    bool maybeSubstituteSource(uint8_t *load_data,
                               const uint8_t *true_src, unsigned copy_size,
                               const uint8_t *alt_src, unsigned alt_size,
                               Addr vaddr);

    // §2.4 F6 phase_offset (Phase 4.7, method3 forward-path phase): called
    // at the forward WritebackEvent schedule site (lsq_unit.cc:~1596).
    // If the RNG fires, returns the DELAY in CPU cycles to apply to this
    // forward's writeback (0 = no injection — the caller schedules at
    // curTick() as usual). Only active in PhaseOffset mode.
    Cycles maybeDelayForward(Addr vaddr, unsigned size);

    // LSU W5 L03: violation-detection address corruption. Called from
    // checkViolations before the overlap comparison. Returns true if the
    // comparison address was corrupted (caller logs it). The corruption
    // changes ONLY the violation check, not the actual memory access.
    bool violationCorrupt(Addr& cmp_addr);

    // [MDSPEC][R4-5.3] LSU W5 L04 — response-pairing target substitution
    // (model L04-b "同周期load返回目标互换", workbook 03/09 sheets; the
    // blocking phrase "consumer-side: response-pairing event source only"
    // is lifted by THIS injectable+traceable mapping). Called from
    // LSQUnit::completeDataAccess — the request->instruction() pairing
    // point the 09 sheet names ("L04在response配对点新增可注入且可观测
    // hook") — for EVERY response delivered there (loads, stores, atomics;
    // the attempt stream). Returns the DynInst the response shall be
    // DELIVERED to: `inst` (the request's own instruction — the correct
    // pairing) normally; the chosen candidate on an exchange half.
    //
    // Pairing key (PRIMARY, per the 09 sheet "lq_idx↔dyn_inst_seq↔
    // request_id" + user ruling 2026-10-20): the source/target loads'
    // dyn_inst_seq/lq_idx/request_id. Address-only joins are NOT
    // registered for L04 (no addr_fallback surface at all — stricter than
    // the labeled-fallback minimum).
    //
    //   RespPairKeys  — the response's own (source) load identity, filled
    //                   by lsq_unit.cc (raw values, no CHAOS types there).
    //   RespPairCand  — one in-flight candidate load B (valid, plain
    //                   register-writeback load, not squashed/executed,
    //                   savedRequest with a packet already outstanding,
    //                   SAME size and byte-enable as the source —
    //                   completeAcc reads the packet per B's own static
    //                   inst, so a size mismatch would read out of
    //                   bounds).
    //   scan          — lazy LQ scan callback (lsq_unit.cc side); invoked
    //                   only after the cheap shape gate passes, so
    //                   non-L04 and non-eligible responses never pay it.
    struct RespPairKeys {
        uint64_t seq = 0;             // source load DynInst::seqNum
        long long lq_idx = -1;        // source load DynInst::lqIdx
        uint64_t request_id = 0;      // Request-stamped seq (0 = unstamped)
        Addr vaddr = 0;               // the response's request vaddr
        unsigned size = 0;            // the request's access size
        bool eligible_shape = false;  // plain register-WB load, unsquashed
    };
    struct RespPairCand {
        o3::DynInstPtr inst;          // the candidate load B
        uint64_t seq = 0;
        long long lq_idx = -1;
        uint64_t request_id = 0;
        Addr vaddr = 0;
        unsigned size = 0;
    };
    using RespPairScan = std::function<void(std::vector<RespPairCand> &)>;
    o3::DynInstPtr maybeSwapResponseTarget(const o3::DynInstPtr &inst,
                                           const RespPairKeys &src,
                                           const RespPairScan &scan);

    // [MDSPEC][R4-5.7] S10 StoreSet SSIT-ID 换值 (workbook 07 matrix S10 row:
    // "SSIT的store-set ID换成另一合法ID"; blocking phrase "consumer-side:
    // StoreSet SSID corruption event source only" lifted by THIS mode).
    // Injection point = StoreSet::violation's new-SSID assignment arm (the
    // training event, workbook trigger "load/store alias训练后"; the W5
    // commit 7af6eed4 placed a count-only chaosLsuF6Observe there — the
    // "event source only"). Payload: the LOAD's freshly assigned SSIT SSID
    // is substituted with ANOTHER LEGAL live store-set ID chosen from the
    // current run (workbook 实施细则: no random bit strings — candidates
    // must be live values satisfying range/encoding/lifecycle constraints;
    // source/target + candidate count saved in the injection line). The
    // STORE entry keeps the true SSID: the trained pair splits and the
    // load aliases the target store set. S10-b (LFST target) / S10-c
    // (valid loss) / the other violation() merge arms are NOT landed
    // (lsu_runid_map SPEC_IMPL_LANDED pending list).
    //
    // Consumer observation (the model's monitor focus "预测依赖与replay"):
    //   ssit_consult (L1) — StoreSet::checkInst consulting the corrupted
    //     load PC's entry; before/after = counterfactual/actual predicted
    //     producing-store seq (the faulted VALUE of this model is the
    //     PREDICTION);
    //   ssit_violation (L2) — a memory-ordering violation detected on the
    //     corrupted load PC (the missed-dependence manifestation; sheet 09
    //     L2 rung literally names "violation/replay"), state_before = the
    //     SSID still mapped at violation time.
    // No addr/seq correlate surface exists for a PC-keyed predictor state:
    // chain members are the injector's own PC-keyed emissions (pf_train
    // precedent) — zero downstream registry registration, honestly.

    // [MDSPEC][R4-9-FSMC] O06 barrier-completion tracking. Node = the O3
    // MemDepUnit's barrier-SN bookkeeping — the ONLY barrier-completion
    // structure on this platform (chaos_barrier_hook.hh carries the
    // code-level proof: DMB/DSB themselves carry no memory access at all,
    // misc64.isa:229-233 / misc.isa:1216-1230). The spec's
    // "提前 done / 延后或丢失 done" map onto the two ends of that
    // bookkeeping:
    //   barrier_done=early (O06-a): the barrier's SN is NOT tracked at
    //     insertion, so later loads/stores issue straight past the barrier
    //     (the spec's "提前done会让后续访问越过屏障"; the observable effect is
    //     a litmus violation -> SDC);
    //   barrier_done=stuck (O06-b): the SN is never released, so every later
    //     memory op keeps waiting on it — the barrier never completes (the
    //     spec's 停顿 -> Timeout channel).
    // Registered into the chaosBarrierInsertHook/chaosBarrierReleaseHook
    // globals by the ctor when o06_mode (deregistered by the dtor); the
    // MemDepUnit call sites are in mem_dep_unit.cc.
    bool maybeCorruptBarrierInsert(uint64_t seq, bool is_read, bool is_write);
    int maybeCorruptBarrierRelease(uint64_t seq, bool is_read, bool is_write,
                                   uint64_t *subst);

    // [MDSPEC][R4-9-FSMC] O07 order-tag 换值 (workbook 07 O07 row: "交换两个
    // 在飞事务的 order tag"; eligibility "至少2个相关事务"). HONEST PROXY:
    // gem5 O3 has no explicit ordering queue with numbered tags — the closest
    // structural analogue is the barrier-SN set, where the InstSeqNum IS the
    // tag and the release point IS the handoff. The landed rule exchanges
    // WHICH in-flight transaction's tag gets released: the injector remembers
    // the live barrier SNs it has seen, so the substitute is always another
    // LEGAL live SN (no fabricated value — the spec's 实施细则). With no
    // other live SN the injection is honestly skipped (attempted, never
    // eligible). Returns 0 = no swap.
    uint64_t orderTagSubstitute(uint64_t seq);

  private:
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random };
    static FaultType stringToFaultType(const std::string &s);
    const char *faultTypeToString(FaultType f);

    // §2.4 structured fault mode (from fi-h6-h7 branch, H5 closed):
    //   byte_flip       (default): single/multi-byte XOR/OR/AND on one byte (orig)
    //   byte_lane_skew  : rotate the whole forwarded data by k bytes (rol_k) —
    //                     reproduces core179 D1 byte-lane phase signature (method2)
    //   all_zero        : zero the whole forwarded buffer (8 bytes)
    //   stale_line_replay: (deferred — needs older-line replay plumbing)
    //   fwd_source_sub (F5): DONE (Phase 4.2) — wrong-source forward from an
    //                     older SQ entry (maybeSubstituteSource hook in
    //                     lsq_unit.cc's forward-decision point)
    //   phase_offset (F6, Phase 4.7 — DONE): delay this forward's
    //     WritebackEvent by phaseOffset CPU cycles (the REAL method3
    //     forward-path phase proxy, unlike IQ's wake_phase which the
    //     E3 boundary analysis showed captures scheduler phase, not
    //     forward-path phase).
    enum class StructMode { ByteFlip, ByteLaneSkew, AllZero, FwdSourceSub,
                            PhaseOffset };
    static StructMode stringToStructMode(const std::string &s);

    o3::CPU *cpu;
    float probability;
    FaultType fault_type_enum;
    StructMode struct_mode;
    std::bitset<64> fault_mask;   // §2.4: 64-bit (was 32 — truncated bit>=32)
    int num_bits_to_change;
    int byte_offset;       // -1 = random byte within [0,size-1]
    int lane_skew_k;       // §2.4 byte_lane_skew: rotate by k bytes (default 1)
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;
    bool l03_mode = false;   // [LSU][SEM-B] W5 L03: violation-site only
    bool l04_mode = false;   // [MDSPEC][R4-5.3] W5 L04: response-pairing site
    bool s10_mode = false;   // [MDSPEC][R4-5.7] W5 S10: StoreSet SSIT-ID 换值
    // [MDSPEC][R4-5.7] S10 corrupted-entry table: corrupted load PC ->
    // (propagation ptag, true SSID, consumed flag). The consumption surface
    // is the injector's own PC-keyed match (StoreSet consults / violations
    // of that PC) — see the public S10 comment above. Under the campaign
    // cap (maxFaults=1) at most one entry exists; re-corruption of the
    // same PC (F5 unlimited) overwrites — the previous chain then has no
    // live consumption surface left (honest single-slot-per-PC limit,
    // recorded here rather than papered over with a multi-map).
    struct S10Entry {
        uint64_t ptag = 0;
        uint64_t true_ssid = 0;
        bool consumed = false;
    };
    std::unordered_map<Addr, S10Entry> s10_entries;
    uint64_t s10_activated_count = 0;  // entries with consumed=true
    // [MDSPEC][R4-5.7b] S10 FUNNEL FORK-POINT DIAGNOSTICS (observation only,
    // zero semantic effect). Root cause of the R4-5.7 census result
    // "attempted=4/5 eligible=0": the S10 hook lives ONLY in the
    // "brand-new store set" arm of StoreSet::violation
    // (store_set.cc `if (!valid_load_SSID && !valid_store_SSID)`), reached
    // through chaosS10SsidSubst -> s10SsidSubstCb. `eligible` can only
    // increment from there AND only when the live-SSIT candidate scan is
    // non-empty. These counters split that compound gate so ONE census run
    // decides between the four triage classes (docs R4-5.7b report §1):
    //   arm1_events         - times the assignment arm was ENTERED (hook
    //                         reached at all) => (c) if 0 with attempted>0
    //   arm1_cand_empty     - entered but the live SSIT held no OTHER live
    //                         SSID => (a)/(b)/(d), the observed predicate
    //   arm1_cand_ok        - entered with >=1 legal candidate (=> eligible)
    //   max_live_ssids      - widest distinct-live-SSID set seen => 1 means
    //                         "only one store-set in use" => (d)
    //   max_cands           - widest legal candidate set seen
    //   arm1_load_pcs       - DISTINCT load PCs entering the assignment arm
    //                         (dedup, insertion order); >1 means several
    //                         first-time training pairs existed.
    // Purely additive: printed once at teardown as CHAOS_LSU_S10_FORK.
    uint64_t s10_arm1_events = 0;
    uint64_t s10_arm1_cand_empty = 0;
    uint64_t s10_arm1_cand_ok = 0;
    uint64_t s10_max_live_ssids = 0;
    uint64_t s10_max_cands = 0;
    std::vector<Addr> s10_arm1_load_pcs;
    // [MDSPEC][R4-5.3] L04-b pending exchange: one injection swaps the
    // pairing-table entries of two loads; the halves complete at different
    // response arrivals. State: the source load (returned as the delivered-
    // to target when the partner's response arrives) + the partner's seq
    // (matches that response). maxFaults=1 campaign cap => one exchange.
    bool l04_pending = false;
    o3::DynInstPtr l04_pending_src;
    uint64_t l04_pending_tgt_seq = 0;
    // [MDSPEC][R4-9-FSMC] O06/O07 mode flags + the barrier-SN ledger. The
    // injector records every barrier SN the MemDepUnit tracked (it sees the
    // insert hook) and stops tracking it at the release, so
    // orderTagSubstitute can always return ANOTHER LEGAL LIVE SN (O07) and
    // never a fabricated value. barrier_* counters are the L0 read-back.
    bool o06_mode = false;
    bool o07_mode = false;
    bool o06_early = false;        // O06 sub-rule: early (a) vs stuck (b)
    std::vector<uint64_t> barrier_live_sns;
    uint64_t barrier_inserts_seen = 0;
    uint64_t barrier_releases_seen = 0;
    uint64_t barrier_injections = 0;
    // one-shot F6 "spent" bookkeeping is owned by lsuTrigger (onF6Event).
    // Sampling-bias fix (same as CHAOSL1DForward, findings.md Phase 2.2):
    // number of eligible forwarding events to skip before the first
    // injection — geometric(p=0.1) from the seed, so maxFaults=1 lands on a
    // seed-dependent forwarding event instead of always the first eligible
    // one (which is the same dynamic store->load pair every rep on a
    // deterministic stream).
    // LSU W2/W5: event-normalized trigger + L0 funnel (same wiring pattern
    // as CHAOSAddrPath; lsuTier != off routes the injection decision through
    // the trigger and the funnel prints at exit).
    ChaOSLsuTrigger *lsuTrigger = nullptr;
    ChaOSL0Funnel l0_funnel;
    ChaOSL0State l0_item;

    uint64_t events_to_skip = 0;
    // v1.1 Phase 8.2 uniform sampling (chaos_event_sample.hh): FIXED skip
    // from the driver overrides the legacy geometric(0.1) draw.
    bool count_only = false;         // consume + count, never corrupt
    uint64_t eligible_count = 0;     // CHAOS_ELIGIBLE_COUNT=<n> at teardown

    std::mt19937 rng;
    std::random_device rd;
    std::discrete_distribution<int> random_fault_distribution;
    OutputStream *log_stream;

    int generateRandomMask(int bits_to_change);  // 8-bit mask (per byte)
    void writeLog(const char *type, unsigned size, Addr vaddr, int byte_off,
                  int mask, const FwdCorrelKeys &keys);

    // [MDSPEC][R4-5.7] S10 static hook bodies (registered into the
    // chaosS10* globals below by the ctor when s10_mode; deregistered by
    // the dtor). The active instance is the single s10_active injector
    // (single-consumer, single-core-SE scoped — same scoping as
    // chaosLsuF6Notify, chaos_lsu_trigger.hh).
    static CHAOSLSQFwd *s10_active;
    static void s10ViolationCb(Addr store_pc, Addr load_pc,
                               uint64_t load_ssid_now, bool load_ssid_valid);
    static bool s10SsidSubstCb(Addr store_pc, Addr load_pc,
                               uint64_t true_ssid,
                               const S10SsidScan &scan, uint64_t *out_ssid);
    static bool s10CorruptedPcCb(Addr pc, uint64_t *true_ssid);
    static void s10ConsultCb(Addr pc, uint64_t actual_ssid,
                             uint64_t actual_dep, uint64_t counterfactual_dep);
    // [MDSPEC][R4-9-FSMC] O06/O07 static hook bodies (registered into the
    // chaosBarrier* globals by the ctor when o06_mode/o07_mode; cleared by
    // the dtor). Single consumer, same scoping as the s10 callbacks above.
    static bool barrierInsertCb(uint64_t seq, bool is_read, bool is_write);
    static int barrierReleaseCb(uint64_t seq, bool is_read, bool is_write,
                                uint64_t *subst);
    // The single armed instance the static callbacks above act through
    // (set by the ctor when o06_mode/o07_mode, cleared by the dtor).
    static CHAOSLSQFwd *barrier_active;

    struct CHAOSLSQFwdStats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numBitFlips;
        statistics::Scalar numStuckAtZero;
        statistics::Scalar numStuckAtOne;
        CHAOSLSQFwdStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSLSQFwdStats> stats;
};

} // namespace gem5

// [MDSPEC][R4-5.7-integration] 下列 S10 钩子函数指针必须**位于 namespace gem5
// 内**：它们以裸名 `Addr` / `S10SsidScan` 书写，而 namespace 已在上方关闭
// ——首次构建（SCONS_EXIT=2）即在 store_set.o / lsq_unit.o 报
// "'Addr' was not declared in this scope; did you mean 'gem5::Addr'?"。
// 重开 namespace（与文件其余部分风格一致），而非逐处限定 `gem5::`。
namespace gem5
{

// [MDSPEC][R4-5.7] S10 StoreSet hook bridge. StoreSet has no CPU/injector
// pointer (it is a plain sub-object of MemDepUnit inside InstQueue), so the
// S10-armed CHAOSLSQFwd self-registers these single-consumer callbacks
// (BaseCache::chaosMergeHook precedent, C11; the W1-thunk chaosLsuF6Notify
// scoping: single-core-SE, one LSU consumer per run by construction).
// store_set.cc includes this header — signatures carry raw values only.
//
//   chaosS10Violation — called at the TOP of StoreSet::violation (every
//     training event; the ATTEMPT stream) with the load's current SSIT
//     SSID (validity flag: the entry may be absent/invalid — the SSIT is
//     finite and cleared periodically). The callback (a) emits
//     ssit_violation when load_pc is a corrupted entry (the missed-
//     dependence manifestation — cap-INDEPENDENT, mechanical chain
//     evidence like L04's half-2), then (b) applies the maxFaults cap
//     BEFORE onAttempt (C11 convention: counters freeze at fire time) and
//     (c) books the attempt.
//   chaosS10SsidSubst — called in the new-SSID assignment arm with the
//     freshly computed true SSID; the LAZY scan fills the live-SSID
//     candidate set (valid SSIT entries' SSIDs). Eligibility = the arm
//     reached AND >= 1 OTHER live store set (workbook 实施细则: the
//     substituted value must be another legal live value; free/idle
//     entries excluded by construction — only present SSIT entries scan).
//     Trigger decision onEligible() / onF6Event(false) (the attempt was
//     already booked by chaosS10Violation — R4-5.1-review-I1 accounting).
//     On fire: target chosen uniformly among the candidates (seeded
//     mt19937), *out_ssid filled, injection logged + registered.
//   chaosS10CorruptedPc / chaosS10Consult — called from
//     StoreSet::checkInst: the former asks whether PC is a corrupted
//     entry (StoreSet then computes the counterfactual prediction from
//     the TRUE SSID's LFST slot — LFST is private to StoreSet), the
//     latter receives the consult (actual ssid/dep + counterfactual dep)
//     and emits the ssit_consult event.
inline void (*chaosS10Violation)(Addr store_pc, Addr load_pc,
                                 uint64_t load_ssid_now,
                                 bool load_ssid_valid) = nullptr;
inline bool (*chaosS10SsidSubst)(Addr store_pc, Addr load_pc,
                                 uint64_t true_ssid,
                                 const S10SsidScan &scan,
                                 uint64_t *out_ssid) = nullptr;
inline bool (*chaosS10CorruptedPc)(Addr pc, uint64_t *true_ssid) = nullptr;
inline void (*chaosS10Consult)(Addr pc, uint64_t actual_ssid,
                               uint64_t actual_dep,
                               uint64_t counterfactual_dep) = nullptr;

} // namespace gem5  [R4-5.7-integration] 关闭为 S10 钩子重开的 namespace

#endif // __CPU_O3_CHAOS_LSQ_FWD_HH__
