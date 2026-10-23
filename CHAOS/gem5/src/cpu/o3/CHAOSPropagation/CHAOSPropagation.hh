#ifndef __CPU_O3_CHAOS_PROPAGATION_HH__
#define __CPU_O3_CHAOS_PROPAGATION_HH__

// CHAOSPropagation — [LSU][OBS-L3] real L3 propagation-chain tracer for LSU
// non-PRF faults (central correction directive 2026-10-13: L3 must be a REAL
// propagation correlation, not commit-divergence counting and not a PRF
// liveness proxy). Observation-only for architectural state: it READS the
// fault-injection call path, the LSQ request/response path and the commit
// stream, and never writes any CPU state. The only writes are to
// prop_trace.csv.gz and its own registries/taint set.
//
// COVERED FAMILIES (v1): addrpath (CHAOSAddrPath, both the sendFragment
// post hook and the pushRequest PRE family) and cache (CHAOSCache data /
// data_shift field faults). lsqfwd / prefetch / exmod families are NOT
// wired — the driver does not pass --chaos_propagation for them and
// tools/lsu_l3_propagation.py reports them unsupported (honest).
//
// ============================ prop_trace.csv.gz v1 =========================
// First line (comment, exactly):
//   # lsu-propagation v1: node_id,tick,ptag,kind,dyn_inst_seq,request_id,
//   (continued) addr,phys_reg,arch_reg,detail
// Every following line is one CSV node:
//   node_id      sequential node counter, starts at 0
//   tick         curTick()
//   ptag         propagation tag (per-fault chain id, 1-based; 0 = rows not
//                bound to one chain, i.e. funnel rows)
//   kind         inj | addr_form | mem_req | resp | taint_reg | consumer |
//                errant_commit | funnel
//   dyn_inst_seq DynInst::seqNum of the involved dynamic instruction
//                ("" when not applicable)
//   request_id   Request::getReqInstSeqNum() — the request→dyn-inst binding
//                gem5 v25 actually maintains (gem5 v25 Request has NO unique
//                id(); CONTRACT DEVIATION, documented in the design doc)
//                ("" when not applicable / not stamped)
//   addr         hex, lowercase, no 0x prefix ("" when not applicable)
//   phys_reg     physical register index within its class
//                ("" when not applicable; the class is in detail k=v)
//   arch_reg     architectural register index ("" when not applicable)
//   detail       compact "k=v;k=v" fields, NO commas; numeric values are
//                decimal, address-bearing values are bare hex (no 0x)
// Numeric columns with no value are EMPTY STRINGS (never placeholders).
//
// kind semantics:
//   inj            the fault was injected (injector call site); detail
//                  carries site=, family=, mode/field=, old/new addrs...
//   addr_form      the erroneous address was formed (addrpath): addr column
//                  = new (corrupted) address; detail carries old_addr/new_addr
//   mem_req        a memory Request carrying the fault left the LSQ toward
//                  translation/memory (sendFragmentToTranslation); matched
//                  against the addr registry (addrpath: range overlap +
//                  dyn_inst_seq match) or the faulted-byte registry (cache:
//                  range overlap, SE vaddr==paddr assumption)
//   resp           the memory response delivering the fault returned to the
//                  CPU (completeDataAccess, pre-writeback); detail carries
//                  data_fnv (FNV-1a-64 of the response bytes) and fault=
//                  when the inst carries a fault
//   taint_reg      a load destination physical register received data
//                  delivered through the fault path and entered the taint
//                  set (resp + register writeback, completeDataAccess)
//   consumer       a committed instruction read a source phys reg in the
//                  taint set (Commit::commitHead anchor)
//   errant_commit  the FIRST commit on a fault path — either the faulting
//                  load itself committing its tainted dest, or the first
//                  consumer. Field-level "first wrong architectural commit"
//                  remains L2 commit_diff.first_errant_commit (authoritative);
//                  this node is the propagation-view alignment point.
//   funnel         attempted/eligible/injected funnel row (one per injection
//                  + one final per injector at exit); ptag=0. Written
//                  Z_SYNC_FLUSH-per-node so ABORTED runs keep the funnel
//                  (central requirement: abort samples must carry
//                  attempted/eligible).
//
// Crash durability (W2.1/W2.4 contract, CHAOSMicroSnap/CHAOSCommitTrace
// pattern): raw zlib gzFile at simout.resolve(trace_file) — NOT
// simout.create's gz streambuf. EVERY node is followed by
// gzflush(Z_SYNC_FLUSH), so an aborted run leaves every completed node
// readable (the file then lacks only the gzip trailer; the Python parser
// salvages the prefix and flags truncated=true). The trailer is written by
// gzclose in an exit callback (destructor is a backstop only — gem5's exit
// path does not reliably run SimObject destructors).
//
// Attachment (setter pattern, CHAOSCommitTrace/CHAOSMicroSnap): startup()
// dynamic_casts p.cpu to o3::CPU and sets BOTH
//   cpu->setChaosPropagation(this)          (LSQ-side hooks: lsq.cc,
//                                            lsq_unit.cc read it via
//                                            cpu->chaosPropagation)
//   cpu->o3Commit().setChaosPropagation(this) (commit.cc commitHead hook)
// CHAOSCache has no CPU pointer, so it reaches the tracer through the
// static instance() (single-core campaign; BaseCache::chaosVictimHook /
// chaosLsuF6Notify static-hook precedent).
//
// ===================== registries / taint set (v1 rules) ===================
// addr registry (addrpath): map<new_addr_base, {ptag, dyn_seq, size, tick}>.
//   A Request matches when [vaddr, vaddr+size) overlaps [base, base+size)
//   AND req->getReqInstSeqNum() == dyn_seq (the faulted request belongs to
//   the faulting instruction; replays of the same inst via savedRequest
//   legitimately re-match — the corrupted vaddr/addr is baked into the
//   reused LSQRequest). Entries expire addrExpiryTicks after registration
//   (lazy sweep on insert/lookup) to bound address-reuse misattribution.
// faulted-byte registry (cache): map over [byte_addr, byte_end) ranges
//   (single byte for data faults; whole block for data_shift; metadata
//   field faults tag/valid/dirty/coh and the victim path register NO range —
//   their chain honestly stops at the inj node).
// taint set: map<(classValue, phys idx), {ptag, taintor_seq}>.
//   + taint_reg at completeDataAccess (resp hit + needWBToRegister +
//     NoFault + not squashed — exactly the condition under which
//     LSQUnit::writeback performs completeAcc and writes the PRF).
//   + consumer at commitHead when a source phys reg is tainted.
//   + dest re-taint when a consumer commits (its dests carry the wrong
//     value onward); clean-overwrite erase when an UNRELATED producer
//     commits onto a tainted phys cell (the cell is rewritten with a fresh,
//     untainted value — bounds stale taint after phys-reg recycling).
//   + the tainting load's own commit keeps its dest taint (taintor_seq
//     match) — that commit IS the first architectural materialization.
//   Squash-race residual (documented): a load tainted at writeback then
//     squashed before commit can leave stale taint on a recycled phys reg;
//     the clean-overwrite rule bounds it; no squash hook in v1.
// errant_commit: once per run (first overall). Single-fault campaign
//   (maxFaults=1) ⇒ one ptag; multi-fault runs attribute the node to the
//   first involved chain (detail says which).

#include <zlib.h>

#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "base/types.hh"
#include "mem/request.hh"          // RequestPtr (CHAOSAddrPath.hh precedent)
#include "params/CHAOSPropagation.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "cpu/base.hh"

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class DynInst; } }
namespace gem5 { class Packet; }

namespace gem5
{

class CHAOSPropagation : public SimObject
{
  public:
    CHAOSPropagation(const CHAOSPropagationParams &p);
    ~CHAOSPropagation();

    // CHAOSCache (no CPU pointer) reaches the tracer through this static
    // (single-instance assumption: single-core campaign; the static-hook
    // precedent is BaseCache::chaosVictimHook / chaosLsuF6Notify).
    static CHAOSPropagation *instance() { return chaos_instance; }

    void startup() override;

    // ============ PROP-EVT unified stream (spec sheet 11, plan Task H0) ====
    // prop_evt.txt.gz: one line per propagation event, ALL registry fields
    // in canonical order, empty values kept as "k=" (keys never omitted):
    //   PROP-EVT: kind=<v> run_id=<v> ... evidence_status=<v>
    // event_id shares the v1 node_id counter (PROP-EVT line N joins the v1
    // CSV row N 1:1). parent_event_id = previous event of the same fault
    // chain (root inj = ""), so propagation edges are explicit — no
    // offline guessing. The registry below is the single source of truth;
    // tools/lsu_prop_fields.py carries an identical copy, pinned equal by
    // tests/test_lsu_prop_fields.py (emit/parse same-source discipline).
    // "kind" leads the registry: spec sheet 11 lists 24 data fields but no
    // event type — without kind the stream is untyped (v1 precedent).
    static inline const char *const PROP_EVT_FIELDS[] = {
        "kind", "run_id", "sample_run_id", "fault_id", "event_id",
        "parent_event_id", "tick", "cycle", "core_id", "thread_id",
        "dyn_inst_seq", "store_dyn_inst_seq", "commit_seq", "pc", "opcode",
        "lq_idx", "sq_idx", "request_id", "walk_id", "mshr_id", "fill_id",
        "pf_request_id", "va", "pa", "cache_line", "set", "way",
        "entry_index", "field", "before", "after", "state_before",
        "state_after", "arch_reg", "phys_reg", "detection_layer",
        "contained", "outcome", "oracle_diff", "evidence_status", "corr",
    };
    static constexpr int N_PROP_EVT_FIELDS =
        (int)(sizeof(PROP_EVT_FIELDS) / sizeof(PROP_EVT_FIELDS[0]));

    // [MDSPEC][R6] T-series containment vocabulary, carried OUTSIDE the
    // shared PROP_EVT_FIELDS registry on purpose. That registry is mirrored
    // 1:1 by tools/lsu_prop_fields.py and pinned equal by
    // tests/test_lsu_prop_fields.py; the parser already keeps family keys
    // outside it ("注册表外的家族键…保留在 dict 中供家族消费" —
    // lsu_prop_fields.parse_line). Growing the SHARED registry is a
    // tools-lane change, so the TLB family records its disposition here
    // rather than half-routing a contract it does not own.
    //
    // Ruling: an unchanged-PA (Masked) / permission-denied / lost-walk
    // fault is CONTAINED. A contained chain must say WHERE it was contained
    // and WHY, so the offline checker can close it as detected_contained
    // instead of "provable_to_Ln_then_unknown" (beyond=Unknown). The layer
    // value is the L-number (e.g. "L2"); the reason reuses the L2 `field`
    // vocabulary (effective_pa_unchanged / translation_blocked /
    // walk_refill_lost).
    static inline const char *const PROP_EVT_EXT_FIELDS[] = {
        "containment_layer", "containment_reason",
    };
    static constexpr int N_PROP_EVT_EXT_FIELDS =
        (int)(sizeof(PROP_EVT_EXT_FIELDS) / sizeof(PROP_EVT_EXT_FIELDS[0]));

    // H1-H7 hook families (and any future observer): emit one unified
    // event. kv pairs use registry field names; unknown keys are warned
    // once and dropped (honest, never silently kept). Auto-filled when the
    // caller leaves them absent: event_id (next counter), parent_event_id
    // (chain of fault_id), tick, cycle, core_id, run_id / sample_run_id
    // (params), evidence_status ("observed").
    void notePropEvt(const std::string &kind,
                     const std::vector<std::pair<std::string, std::string>> &kv);


    // ---- injector-facing registration (fault-injection time) --------------
    // addrpath family: an AGU address fault just mutated a request address
    // (old_addr→new_addr; sizes as known at the site, 0 = unknown for the
    // post hook). Allocates a ptag, writes the inj + addr_form nodes and
    // registers [new_addr, new_addr+new_size) in the addr registry.
    // Returns the ptag (0 = tracer disabled / no-op).
    uint64_t registerInjection(const char *site, uint64_t dyn_inst_seq,
                               Addr old_addr, Addr new_addr, bool is_load,
                               unsigned old_size, unsigned new_size);

    // cache family: a CHAOSCache fault just landed on block_addr.
    //   byte_offset >= 0 : data fault on one byte (registry range =
    //                      [block+off, block+off+1))
    //   byte_offset == -1: whole-block fault (data_shift; registry range =
    //                      [block, block+block_size))
    //   byte_offset == -2: metadata field fault (tag/valid/dirty/coh) or the
    //                      victim path — inj node only, NO delivery tracking
    //                      (the chain honestly stops at inj).
    uint64_t registerCacheFault(Addr block_addr, int byte_offset,
                                Addr block_size, const char *field);

    // [MDSPEC][R4-5.1] C11 MSHR merge corruption (CHAOSCache
    // maybeCorruptMergeTarget): a demand-read target coalescing into an
    // outstanding MSHR just had ONE offset-domain bit of its address
    // flipped (old_addr -> new_addr, same line; `line` = the shared block
    // address). Writes the inj node (detail old_addr/new_addr/size/
    // block_addr — the dual-emit lifts them to before/after/cache_line;
    // addr column = the corrupted target address; corr=origin) and
    // registers the CORRUPTED target range [new_addr, new_addr+size) in
    // the faulted-byte (blk) registry so every downstream event on that
    // address/line joins the chain address-only (the labeled
    // addr_fallback arm — C-family faults have no seq primary at this
    // site): the H4 mshr_merge event at the same site (it correlates on
    // the corrupted address), mshr_fill/cache_fill/mshr_free on the line,
    // and noteMemResponse's cache arm (the response returns on the
    // corrupted address) -> resp / lq_complete / taint_reg. Returns the
    // ptag (0 = tracer disabled).
    uint64_t registerMshrMergeFault(Addr line, Addr old_addr, Addr new_addr,
                                    unsigned size);

    // [MDSPEC][R4-5.2] C12 fill-timing offset (CHAOSCache
    // maybeDeferFillTiming): a fill response on `line` just got DEFERRED —
    // its processing (handleFill + target service + MSHR free) runs at
    // `deferred_tick` instead of the arrival tick `arrival_tick` (the
    // offset = deferred_tick - arrival_tick = delay_cycles cache cycles).
    // Writes the inj node (corr=origin; addr column = the fill line;
    // before/after = the faulted VALUE for this model, the delivery tick
    // before/after the offset — registered fields, so the pair is
    // stream-visible; block_addr lifts to cache_line) and registers the
    // WHOLE fill line [line, line+block_size) in the faulted-byte (blk)
    // registry so every downstream event on that line joins the chain
    // address-only (the labeled addr_fallback arm — no seq primary at this
    // site): the DELAYED mshr_fill/cache_fill/mshr_free events
    // (correlateBlock), cache_access on later lookups, and
    // noteMemResponse's cache arm (the response is delivered on this very
    // line) -> resp / lq_complete / taint_reg, all at the shifted tick.
    // Returns the ptag (0 = tracer disabled).
    uint64_t registerFillTimingFault(Addr line, Addr block_size,
                                     Tick arrival_tick, Tick deferred_tick,
                                     uint64_t delay_cycles);

    // [MDSPEC][R4-5.5] C14-a MSHR busy/occupied stuck-at-1 (CHAOSCache
    // maybeStickMshrBusy at BaseCache::recvTimingResp's release point): an
    // MSHR entry that COMPLETED its fill was NOT released — it stays in the
    // queue's allocated list (busy/occupied stuck-at-1) and never returns
    // to the free list. `line` = the leaked entry's line; before/after =
    // the queue's in-service occupancy that the correct release would have
    // left vs. the occupancy with the release skipped (this model's
    // faulted VALUE — a 4th value type after C12's tick pair, L04's seq
    // pair and P06's classification pair). Writes the inj node
    // (corr=origin; addr column = the line) + the model-specific
    // `mshr_busy` node (the stuck state itself: mshr_id/entry_index/
    // state_before/state_after/field=busy) and registers the WHOLE line in
    // the faulted-byte (blk) registry so later events on that line join
    // address-only (corr=addr_fallback — the C-family site has no seq
    // primary). The entry's mshr_id is looked up (or minted) in the
    // propagator's line-keyed MSHR registry and deliberately NOT released
    // (the leak is the point). Returns the ptag (0 = tracer disabled).
    uint64_t registerMshrBusyFault(Addr line, Addr block_size,
                                   uint64_t occ_before, uint64_t occ_after,
                                   bool was_full);

    // [MDSPEC][R4-5.6] C15-b MSHR capacity-arbitration fake-free (CHAOSCache
    // noteMshrAllocAttempt, called from BaseCache::chaosMshrOccArbitrate):
    // the arbitration was widened by a fabricated free slot, and `line` is
    // the request whose over-capacity (reserve) allocation the fault
    // actually allowed. before/after = the queue's in-service occupancy
    // pair around the over-commit (the model's faulted VALUE is the
    // occupancy bookkeeping). Writes the inj node (corr=origin; addr
    // column = the over-committed request's line) + the model-specific
    // `mshr_arb` node (the arbitration observation: mshr_id/entry_index/
    // state_before=full_blocked -> state_after=over_commit_alloc/field=
    // capacity) and registers the WHOLE line in the faulted-byte (blk)
    // registry so later events on that line join address-only (corr=
    // addr_fallback — the C-family site has no seq primary). `materialized`
    // is recorded in the node detail (this API is only called on
    // materialization, so it is always true here — kept for symmetry with
    // the fire-side log line). Returns the ptag (0 = tracer disabled).
    uint64_t registerMshrArbFault(Addr line, Addr block_size,
                                  uint64_t occ_before, uint64_t occ_after,
                                  bool materialized);

    // [MDSPEC][R4-5.4] P06-a prefetch-as-demand fill classification fault
    // (CHAOSPrefetch maybeMarkFillAsDemand, called from Cache::
    // serviceMSHRTargets' setPrefetched gate — the site where a fill's
    // demand/prefetch classification becomes the durable line state). A
    // prefetch-owned fill on `line` just got its classification marked
    // demand: the CacheBlk::Prefetched bit is NOT set, so the line enters
    // the cache exactly as a demand fill (the faulted VALUE of this model
    // is the fill classification, before=prefetch -> after=demand — the
    // third per-model value type after C12's tick pair and L04's seq
    // pair; read it together with field=pf_fill_class). Writes the inj
    // node (corr=origin; addr column = the marked line; before/after =
    // the classification pair, registered fields so the pair is
    // stream-visible; block_addr lifts to cache_line) and registers the
    // WHOLE line [line, line+block_size) in the faulted-byte (blk)
    // registry so every downstream event on that line joins the chain
    // address-only (the labeled addr_fallback arm — no seq primary at
    // this site): cache_access on later lookups, cache_fill/mshr_fill/
    // mshr_free on refetches, cache_evict on eviction, and
    // noteMemResponse's cache arm (a demand load served on this line) ->
    // resp / lq_complete / taint_reg. The addr arm is the KNOWN
    // over-approximation (a correct response on the same line joins and
    // taints — C11 §5.1.6 precedent, corr=addr_fallback says so); the
    // oracle adjudicates. The PREFETCH-REQUEST registry entry
    // (notePrefetchRequest, called by the injector right after this)
    // additionally arms the pf_fill/pf_demand nodes for this line: the
    // injector's call site allocates the request-level pf_request_id at
    // marking time (the queue/issue nodes predate the fault and stay
    // absent — honest gap, the fault happens at fill). Returns the ptag
    // (0 = tracer disabled).
    uint64_t registerPfFillClassFault(Addr line, Addr block_size);
    // [MDSPEC][R4-5.8] A07-b AGU-ready delay (CHAOSAddrPath
    // maybeDelayAguReady at IEW::executeInsts' isMemRef branch — the
    // ready/handshake point). ONE plain load/store just had its
    // address-ready handshake delayed: the AGU (initiateAcc) runs at
    // `delayed_tick` instead of `ready_tick` (delay = delayed_tick -
    // ready_tick = delay_cycles CPU cycles). Writes the inj node
    // (corr=origin; before/after = the faulted VALUE of this model — the
    // ready tick before/after the delay, the C12 delivery-tick precedent;
    // delay_cycles / lq_idx / sq_idx / pc stay in the v1 detail) and
    // registers NOTHING yet: the EA does not exist at the ready point.
    // The address binding is LATE: bindAguFaultAddr (below) is called
    // from the LSQ::pushRequest PRE hook when the DELAYED instruction's
    // EA first materializes (the AGU raw output), binding the chain to
    // the real range [addr, addr+size) with the instruction's seq — the
    // very same request's lsq_push (emitted right after the PRE hook),
    // its mem_req/tlb_translate fragments and every downstream
    // seq/overlap-correlated node then join with corr=seq_primary and
    // REAL va values. NO address-only fallback arm exists for A07 (the
    // fault follows the dynamic instruction, not an address — L04's
    // stricter-than-minimum stance). If the delayed instruction never
    // reaches pushRequest (predicated-off / squashed in the delay
    // window), the chain honestly stops at the inj node.
    // Returns the ptag (0 = tracer disabled).
    uint64_t registerAguReadyFault(uint64_t dyn_seq, long long lq_idx,
                                   long long sq_idx, Tick ready_tick,
                                   Tick delayed_tick, uint64_t delay_cycles,
                                   bool is_load, Addr pc);

    // [MDSPEC][R4-5.8] A07 late address binding (see above): attach the
    // ALREADY-allocated ptag to [addr, addr+size) bound to dyn_seq in the
    // addr registry (the seq-primary arm). No-op for ptag == 0 or
    // dyn_seq == 0.
    void bindAguFaultAddr(uint64_t ptag, uint64_t dyn_seq,
                          Addr addr, unsigned size);

    // [MDSPEC][R4-1] SQ store->load forwarding fault, seq-PRIMARY
    // correlation (user ruling 2026-10-20: address-only correlation may
    // survive only as a labeled fallback). Allocates a ptag, writes the
    // inj node, and registers:
    //   PRIMARY   — addr-registry entry [vaddr, vaddr+size) bound to the
    //               PRODUCER STORE's dyn_inst_seq, so the store's later
    //               sq_writeback / sq_complete events (which correlate by
    //               correlateRequestBySeq) join this chain by SEQ;
    //   FALLBACK  — the same byte range in the faulted-byte (blk) registry
    //               for seq-less call sites (correlateBlock / the cache
    //               branch of noteMemResponse). Address-only by design;
    //               events that rely on it must carry corr=addr_fallback.
    // store_seq == 0 (seq genuinely unavailable at the call site) skips
    // the primary registration — the chain then joins by the labeled
    // address fallback only. Returns the ptag (0 = tracer disabled).
    uint64_t registerLSQForwardFault(uint64_t store_seq, long long sq_idx,
                                     uint64_t store_req_id,
                                     uint64_t load_seq, long long lq_idx,
                                     uint64_t load_req_id,
                                     Addr vaddr, Addr size,
                                     const char *field);

    // [MDSPEC][R4-5.3] L04-b response-pairing target exchange (CHAOSLSQFwd
    // maybeSwapResponseTarget, called from LSQUnit::completeDataAccess —
    // the request->instruction() pairing point). One in-flight load's
    // returning response just got its pairing-table entry exchanged with
    // another in-flight load's: the response for `src` is delivered to
    // `tgt` now (half 1), and tgt's own later response is delivered to src
    // (half 2) — two legal responses, each to the wrong consumer
    // ("两个响应数据各自合法但送错消费者"). PRIMARY correlation is SEQ-
    // BOUND on BOTH loads (the 09 sheet keys lq_idx↔dyn_inst_seq↔
    // request_id; user ruling 2026-10-20): the inj node carries the TARGET
    // (wrong consumer) seq — its resp/lq_complete/taint_reg share it — and
    // before/after = the pairing mapping source-seq -> target-seq (the
    // faulted VALUE of this model, dual-emit lifted from old_addr/new_addr
    // detail keys; value type is per-model, see the C12 tick-pair
    // precedent). The EXCHANGED pairing table is registered as TWO
    // seq-bound addr-registry entries: [src_va, +src_size) -> tgt_seq
    // (half 1's noteMemResponse: packet = src's response, inst = tgt) and
    // [tgt_va, +tgt_size) -> src_seq (half 2). NO address-only fallback is
    // registered for L04 (stricter than the labeled-fallback minimum: the
    // 09 sheet forbids address single-key chains). Address collision
    // (src_va == tgt_va — same-VA loads, common on the sq_forward probe):
    // one map key — the half-1 binding wins, half 2 then has no
    // seq-bound surface (honest gap, recorded here, never an addr join).
    // Returns the ptag (0 = tracer disabled).
    uint64_t registerRespPairFault(uint64_t src_seq, long long src_lq_idx,
                                   uint64_t src_req_id, Addr src_va,
                                   unsigned src_size,
                                   uint64_t tgt_seq, long long tgt_lq_idx,
                                   uint64_t tgt_req_id, Addr tgt_va,
                                   unsigned tgt_size);

    // [MDSPEC][R4-5.7] S10-a StoreSet SSIT-ID 换值 (CHAOSLSQFwd
    // --lsqfwd_s10, hooks at StoreSet::violation / checkInst — see
    // CHAOSLSQFwd.hh for the model ruling). A violation retrain just
    // assigned the load PC a fresh SSID and the injector substituted it
    // with ANOTHER LEGAL live store-set ID (candidates = valid SSIT
    // entries' SSIDs minus the true one; workbook 07 实施细则: no random
    // bit strings — the target came from the current run). Writes the inj
    // node (corr=origin; pc lifts to the unified pc field; before/after =
    // true/target SSID — the faulted VALUE of this model, the SSID
    // assignment; store_pc and the candidate-set size stay in the detail)
    // and registers NO downstream correlate surface: the fault lives in
    // PC-keyed predictor state, which has no addr/seq registry arm. The
    // chain's downstream members (ssit_consult / ssit_violation) are the
    // injector's own PC-keyed emissions — pf_train precedent (the
    // prefetcher's stride fault has the same no-correlate-surface shape).
    // Returns the ptag (0 = tracer disabled).
    uint64_t registerStoreSetFault(Addr store_pc, Addr load_pc,
                                   uint64_t true_ssid, uint64_t new_ssid,
                                   size_t candidate_count);

    // [MDSPEC][R4-4] ArmTLB pfn fault, seq-PRIMARY correlation (the TLB
    // twin of registerLSQForwardFault; replaces the pre-R4-4 address-only
    // registration, user ruling 2026-10-20). The injection site
    // (TLB::lookup) has no Request in the gem5 core signature, but
    // MMU::getTE publishes the in-flight translation's identity on the TLB
    // (chaosLookupReqSeq/Size) which CHAOSArmTLB forwards here:
    //   PRIMARY  — addr-registry entry [va, va+span) bound to req_seq, so
    //              the request's own later seq-keyed events (correlate-
    //              RequestBySeq / correlateRequest's seq arm) join by SEQ.
    //              req_seq == 0 (table-walker / functional lookups) skips
    //              the primary — labeled fallback only.
    //   FALLBACK — the WRONG physical page [new_pa_page, +pa_span) in the
    //              faulted-byte registry for the seq-less cache-side sites,
    //              ONLY when the corrupted pfn actually redirects the PA
    //              (old/new PA page differ — pfn bits at/above the PA width
    //              wrap out of the 64-bit Addr and are architecturally
    //              inert; measured: the T01 default draw pfn-bit-56). When
    //              the PA is unchanged NOTHING is registered downstream:
    //              the chain honestly ends at the TLB layer rather than
    //              fabricating cache/resp/taint joins from unrelated
    //              correct traffic on the unchanged page.
    // The unified tlb_pfn event carries corr (seq_primary | addr_fallback
    // | "" for the no-surface case) plus dyn_inst_seq/request_id ("0" =
    // unstamped, lsq_sendfrag convention). Returns the ptag (0 = disabled).
    uint64_t registerTlbFault(uint64_t req_seq, Addr va, Addr size,
                              Addr old_pfn, Addr new_pfn,
                              Addr old_pa, Addr new_pa, Addr pa_span,
                              const char *mode, int entry_way,
                              int candidate_way, uint64_t walk_id,
                              const std::string &entry_before,
                              const std::string &entry_after);

    // [MDSPEC][R4-10-T05/T06/T07] TLB entry-STATE / access-attribute faults
    // (valid / global / ASID / AP / memory-type / page-size). These mutate a
    // field of the hit entry that is NOT the pfn, so the PA is usually
    // unchanged and the tlb_pfn node (before/after pfn + PA) does not apply.
    // Emits the L0 `inj` anchor plus ONE L2 `tlb_state` node carrying
    // field + state_before/state_after (the mutated field's text before/after
    // the mutation). corr follows the same arms as registerTlbFault
    // (seq_primary when the in-flight request is published, else "" — honest
    // no-surface: the chain honestly stops at the TLB layer rather than
    // inventing a PA redirect). Returns the ptag (0 = disabled).
    uint64_t registerTlbStateFault(uint64_t req_seq, Addr va, Addr size,
                                   const char *field,
                                   const std::string &before,
                                   const std::string &after,
                                   Addr old_pa, Addr new_pa,
                                   int entry_way, int candidate_way,
                                   uint64_t walk_id,
                                   const std::string &entry_before,
                                   const std::string &entry_after);

    // Close a T-series lookup observation at the real MMU completion point,
    // after permission/alignment checks have produced the final Fault.
    void noteTlbTranslationResult(uint64_t req_seq, Addr va, bool has_pa,
                                  Addr pa, const char *fault);

    // [MDSPEC][R4-5.9] T08 walk/fill pairing (FS-only): register a PAIR of
    // nodes for ONE page-table walk — `tlb_walk` (the walk issued by
    // TableWalker::walk) and `tlb_refill` (the refill completion of that
    // same walk). Both carry the SAME walk_id and the SAME fault_id ⇒ the
    // pairing is provable by construction (two nodes, distinct ticks,
    // shared walk_id) — this is the "walk/fill pairing" the T08 blocker
    // named. fill_lost=true records the T08-a outcome honestly as
    // field=lost / outcome=lost (the refill that never arrived) rather
    // than fabricating a completed refill. corr=origin on both nodes (the
    // injector's own registration burst — no correlate* query, same shape
    // as registerTlbFault's inj node). Returns the ptag (0 = disabled).
    uint64_t registerTlbWalkPair(uint64_t walk_id, Addr va, uint64_t req_seq,
                                 uint64_t walk_start_tick,
                                 uint64_t refill_tick, unsigned level,
                                 bool fill_lost, const char *mode);

    // Funnel row (attempted/eligible/injected as of NOW). Called by the
    // injectors at every successful injection AND at their exit callbacks
    // (final counts). Per-node Z_SYNC_FLUSH ⇒ abort-survivable.
    void noteFunnel(const char *site, uint64_t attempted, uint64_t eligible,
                    uint64_t injected);

    // [MDSPEC][H5] prefetch request-level identity. pf_request_id must be a
    // STABLE request-level id shared by every node of one prefetch
    // request's chain (train→queue→issue→fill→demand) — it is NOT the
    // fault id (ptag) and NOT a per-site counter or a tick (spec sheet 9
    // P01: "为prefetch request分配pf_request_id并贯穿MSHR/fill/后续demand").
    // Allocates a fresh id (>=1) and registers [addr, addr+size) so the
    // later queue/issue/fill/demand events on the same prefetched line
    // resolve to the same id. 0 = tracer disabled.
    uint64_t notePrefetchRequest(Addr addr, Addr size);

    // [MDSPEC][H5] resolve the pf_request_id of the prefetch request whose
    // registered line overlaps [addr, addr+size); 0 = no prefetch request
    // (the site is not prefetch-driven → no pf_* node). Optionally returns
    // the registered base. Range overlap only — never a single-key guess.
    uint64_t prefetchRequestId(Addr addr, Addr size, Addr *base_out = nullptr);

    // [MDSPEC][H5] attach an ALREADY-allocated prefetch request to another
    // generated line. The prefetcher's fault (e.g. a corrupted training
    // stride) only shows up in the candidate addresses generated on later
    // calls, so this is how those candidates join the same request chain
    // (and how queue/issue/fill/demand on them resolve to that
    // pf_request_id). Requires a pfid >= PF_ID_BASE (from
    // notePrefetchRequest); no-op otherwise.
    void registerPtagPrefetch(uint64_t pfid, Addr addr, Addr size);

    // [MDSPEC][H4] MSHR lifecycle identity. One stable mshr_id per
    // in-flight miss line (spec sheet 9 C01: "mshr_id/fill_id/victim_id 及
    // event 父子关系"); a merge reuses the existing id of the same line,
    // a free releases it, and every fill allocates a fresh fill_id. These
    // are REAL allocated ids, not the hex block address.
    uint64_t noteMshrAlloc(Addr line);      // fresh id for a new miss line
    uint64_t noteMshrLookup(Addr line);     // existing id (merge); 0 = none
    uint64_t noteMshrFree(Addr line);       // release; returns the freed id
    uint64_t noteFill(Addr line);           // fresh fill_id

    // [MDSPEC][H6] attach an EXISTING ptag's chain to a faulted byte range
    // in the block registry, so cache-side events (cache_access /
    // cache_return / RMW) on that line correlate with the chain the
    // injector opened. Needed by injectors whose fault is architecturally
    // visible to the cache but whose site (e.g. the ARM exclusive monitor
    // in the ISA) is not the cache itself. No-op for ptag == 0.
    void registerPtagBlock(uint64_t ptag, Addr byte_begin, Addr byte_end);

    // ---- pipeline hooks (read-only w.r.t. CPU state) -----------------------
    // [MDSPEC][R4-1-review-I1] correlation-arm labels (user ruling 2026-10-20:
    // address-only correlation may survive ONLY as a labeled fallback —
    // consumers must be labeled too, not just the registration). Every
    // PROP-EVT event whose fault_id came from a correlate* lookup carries
    // corr=<one of these> saying WHICH arm matched:
    //   CORR_SEQ_PRIMARY   — the join is seq-bound (addr-registry entry
    //                        matched with dyn_seq, or correlateRequestBySeq)
    //   CORR_ADDR_FALLBACK — the join is address-only (faulted-byte / blk
    //                        registry overlap; no seq constraint)
    // [MDSPEC][R4-4-review-I1] the corr contract extends to EVERY event on
    // the stream, including the writeNode dual-emit kinds (inj / addr_form /
    // mem_req / resp / taint_reg / consumer / errant_commit) and chain_end:
    // where no correlate lookup ran, the marker must SAY so — an empty corr
    // on a chain member is a contract violation (it is indistinguishable
    // from an unlabeled address-domain join). Non-join markers:
    //   CORR_ORIGIN     — chain-opening registration event (inj / addr_form):
    //                     no join is attempted; this event CREATES the chain.
    //   CORR_TAINT_PROP — fault_id from taint-set membership (consumer /
    //                     errant_commit): no correlate lookup at this event;
    //                     membership propagates from the taint_reg that
    //                     established the taint (whose own corr records the
    //                     arm that admitted the chain).
    //   CORR_NONE       — chain lifecycle marker with no correlation
    //                     semantics (chain_end exit callback).
    // corr stays empty ONLY where an earlier approved family contract allows
    // the honest absence: tlb_pfn with no correlation surface (req_seq==0
    // AND PA page unchanged) and pf_fill/pf_demand with fault_id=0.
    static constexpr const char *CORR_SEQ_PRIMARY = "seq_primary";
    static constexpr const char *CORR_ADDR_FALLBACK = "addr_fallback";
    static constexpr const char *CORR_ORIGIN = "origin";
    static constexpr const char *CORR_TAINT_PROP = "taint_prop";
    static constexpr const char *CORR_NONE = "none";

    // [MDSPEC][H1] Fault correlation for LSQ unified events: return the
    // ptag whose addr-registry entry matches (dyn_seq + range overlap) or
    // whose faulted-byte registry overlaps [addr, addr+size). 0 = no chain
    // (the request is not fault-correlated; PROP-EVT is a fault-propagation
    // stream, spec sheet 11 — non-correlated observations stay out).
    // corr_out (optional) receives the matched arm's label above; it is
    // left untouched when nothing matched.
    uint64_t correlateRequest(uint64_t dyn_seq, Addr addr, Addr size,
                              const char **corr_out = nullptr);

    // [MDSPEC][H7] Seq-only correlation for LQ/SQ lifecycle sites that have
    // the DynInst but not a stable vaddr at hand (read()/executeStore()):
    // match the addr registry by dyn_seq alone; optionally return the
    // registered base via base_out (the event's va). The join is seq-bound
    // by construction → *corr_out = CORR_SEQ_PRIMARY on a hit.
    uint64_t correlateRequestBySeq(uint64_t dyn_seq,
                                   Addr *base_out = nullptr,
                                   const char **corr_out = nullptr);

    // [MDSPEC][H4] Block-address correlation for cache structural events
    // (access/fill/evict on a faulted block): return the ptag whose
    // faulted-byte registry overlaps [addr, addr+size); optionally return
    // the registered base. 0 = not fault-correlated (no event). The join
    // is address-only by construction → *corr_out = CORR_ADDR_FALLBACK on
    // a hit (the labeled fallback arm).
    uint64_t correlateBlock(Addr addr, Addr size, Addr *base_out = nullptr,
                            const char **corr_out = nullptr);

    // LSQ::LSQRequest::sendFragmentToTranslation: the fragment Request is
    // about to leave for translation/memory. Writes a mem_req node when it
    // matches the addr registry (addrpath) or the faulted-byte registry
    // (cache). Returns the FIRST matched ptag (0 = no match) so the H1
    // unified lsq_sendfrag event can carry the chain id; corr_out receives
    // the matched arm's label (seq-bound addr registry vs address-only blk
    // registry — [MDSPEC][R4-1-review-I1]).
    uint64_t noteMemRequest(const char *site, uint64_t dyn_inst_seq,
                            const RequestPtr &req,
                            const char **corr_out = nullptr);

    // LSQUnit::completeDataAccess (pre-writeback, squashed-guarded inside):
    // writes a resp node when the packet delivers a registered fault, and —
    // for register-writeback loads/SC/atomics with NoFault — taint_reg nodes
    // for the dest phys regs (added to the taint set).
    void noteMemResponse(o3::DynInst *inst, Packet *pkt, bool wb_to_reg);

    // Commit::commitHead (the W2.1/W2.4 anchor): commit-side taint
    // propagation. consumer nodes for tainted source phys regs, first
    // errant_commit, dest re-taint / clean-overwrite.
    void noteCommit(ThreadID tid, o3::DynInst *head_inst);

  private:
    // One CSV row: numeric fields with has_x=false print as "".
    // corr labels the PROP-EVT dual-emit ([R4-4-review-I1]): one of the
    // CORR_* constants above (or a correlate* arm label) — nullptr only for
    // kinds that are not dual-emitted (funnel); a nullptr corr on a
    // dual-emitted kind warns once and writes corr= (contract violation
    // guard, never silent).
    void writeNode(uint64_t ptag, const char *kind, uint64_t dyn_seq,
                   bool has_seq, uint64_t request_id, bool has_req_id,
                   Addr addr, bool has_addr, uint64_t phys_reg, bool has_phys,
                   uint64_t arch_reg, bool has_arch, const std::string &detail,
                   const char *corr = nullptr, int tid = -1);

    // Core PROP-EVT emitter: event_id is the caller-allocated (v1-shared)
    // counter value; ptag drives the parent_event_id chain. fields may
    // override auto values (tick/cycle/core_id/run_id/...).
    void emitPropEvt(const std::string &kind, uint64_t ptag, uint64_t event_id,
                     std::map<std::string, std::string> fields, int tid);

    // Parse a v1 detail "k=v;k=v" string into the map (used by the
    // dual-emit to lift old_addr/new_addr/pc/field/block_addr into the
    // unified before/after/pc/field/cache_line fields).
    static void parseDetail(const std::string &detail,
                            std::map<std::string, std::string> &out);

    uint64_t fnv1a64(const void *blob, size_t n) const;
    const char *regClassName(int class_value) const;

    // Lazy expiry sweep (called on insert/lookup; registries are tiny).
    void sweepExpired();

    BaseCPU *cpu;
    o3::CPU *o3cpu = nullptr;      // resolved at startup(); nullptr = disabled
    std::string trace_file;        // simout.resolve target (.gz, self-managed)
    bool write_log;                // gate ALL tracking + writing
    uint64_t addr_expiry_ticks;    // registry entry lifetime (0 = never expire)
    gzFile gz_file = nullptr;      // raw zlib stream; crash-durability note

    // PROP-EVT stream (H0): second crash-durable gz; event counter shared
    // with v1 (event_id == node_id). ptag_last_event gives each fault chain
    // its previous event id (parent_event_id edge).
    std::string evt_trace_file;    // simout.resolve target (.gz)
    std::string run_id;            // campaign RunID (param; "" = unset)
    std::string sample_run_id;     // sample index within the RunID
    gzFile evt_gz_file = nullptr;
    uint64_t clock_period = 0;     // captured at startup(); cycle = tick/period
    bool evt_unknown_key_warned = false;
    bool evt_corr_missing_warned = false;   // [R4-4-review-I1] guard above
    std::map<uint64_t, uint64_t> ptag_last_event;

    struct TlbPending {
        uint64_t ptag = 0;
        std::string corr;
        uint64_t walk_id = 0;
        int entry_way = -1;
        int candidate_way = -1;
        Addr clean_pa = 0;
        Addr lookup_pa = 0;
        std::string entry_before;
        std::string entry_after;
        // [R6-B/T08-bcd] walk-family faults have no clean-PA baseline (the
        // corrupted object is the walk handshake, not the entry pfn); the
        // completion must not claim containment on an unknown baseline.
        bool walk_fault = false;
    };
    // Request sequence plus VA disambiguates stage/functional lookups while
    // preserving a direct join with the MMU request that completes them.
    std::map<std::pair<uint64_t, Addr>, TlbPending> tlb_pending;

    static CHAOSPropagation *chaos_instance;

    uint64_t next_node_id = 0;
    uint64_t next_ptag = 0;        // 0 reserved ("no chain")
    bool errant_commit_seen = false;
    // [MDSPEC][R6] Per-chain record of the (single, first) errant commit.
    // The errant_commit node already carries the faulting chain's own ptag,
    // so WHICH chain reached the wrong architecturally-visible commit is
    // observable; the run-global flag above cannot say it, which forced the
    // L5 `chain_end` node to report a lifecycle-only outcome for every chain
    // (outcome=run_end / detection_layer=None) — rejected as L5 evidence.
    std::set<uint64_t> errant_ptags;

    // [MDSPEC][R6] Per-chain containment disposition (layer, reason), set
    // when a translation completes with the fault ABSORBED (effective PA
    // unchanged / permission-denied / lost walk) — i.e. the Masked case.
    // The exit callback lifts it onto the chain's chain_end node so the
    // chain closes as detected_contained (later layers justified
    // N/A(contained)) instead of falling back to an Unknown terminal.
    std::map<uint64_t, std::pair<std::string, std::string>> containment_ptags;

    struct AddrEntry {
        uint64_t ptag;
        uint64_t dyn_seq;
        Addr base;
        Addr size;                 // 0 = address-only marker (never matches)
        Tick registered;
    };
    std::map<Addr, AddrEntry> addr_registry;

    struct BlkEntry {
        uint64_t ptag;
        Addr byte_begin;           // inclusive
        Addr byte_end;             // exclusive
        Tick registered;
    };
    std::map<Addr, BlkEntry> blk_registry;

    struct TaintEntry {
        uint64_t ptag;
        uint64_t taintor_seq;      // DynInst::seqNum of the tainting inst
        // [MDSPEC][R6/A6] The event that ESTABLISHED this taint (the
        // taint_reg node, or the consumer node that re-tainted a dest).
        // Consumers of this taint name it as their parent_event_id, so the
        // chain is a real DAG (one source → many consumers) instead of the
        // degenerate "parent = previous event" linear list the single
        // ptag_last_event cursor produced.
        uint64_t src_event = 0;
    };
    std::map<std::pair<int, uint32_t>, TaintEntry> taint_set;

    // [MDSPEC][H5] prefetch-request registry: one entry per prefetch
    // request keyed by its line base, carrying the request-level
    // pf_request_id (independent of ptag) so every downstream node of the
    // same prefetch resolves the same id.
    struct PfEntry {
        uint64_t pf_request_id;
        Addr base;
        Addr size;
        Tick registered;
    };
    std::map<Addr, PfEntry> pf_registry;
    uint64_t next_pf_request_id = 0;   // 0 reserved ("no prefetch request")
    // pf_request_id lives in a DISJOINT numeric space from fault_id/ptag
    // (offset PF_ID_BASE) so a request-level id can never be mistaken for,
    // or coincide with, a fault-chain id (spec sheet 9 P01 requires them
    // to be different identities).
    static constexpr uint64_t PF_ID_BASE = 1ULL << 32;

    // [MDSPEC][H4] in-flight miss lines → allocated mshr_id (real ids).
    std::map<Addr, uint64_t> mshr_registry;
    uint64_t next_mshr_id = 0;         // 0 reserved ("no mshr")
    uint64_t next_fill_id = 0;         // 0 reserved ("no fill")
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_PROPAGATION_HH__
