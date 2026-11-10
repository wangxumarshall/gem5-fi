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
//                  range overlap in the architectural address space; SE note
//                  below — there is no separately translated physical address)
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

#include "base/types.hh"
#include "mem/request.hh"          // RequestPtr (CHAOSAddrPath.hh precedent)
#include "params/CHAOSPropagation.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "cpu/base.hh"
#include "cpu/reg_class.hh"
#include "cpu/o3/CHAOSAddrPath/a01_coords.hh"  // [LSU][V3.2.12][A01]
#include "cpu/o3/CHAOSAddrPath/a03_stream.hh"  // [LSU][V3.2.12][A03]

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

    // Funnel row (attempted/eligible/injected as of NOW). Called by the
    // injectors at every successful injection AND at their exit callbacks
    // (final counts). Per-node Z_SYNC_FLUSH ⇒ abort-survivable.
    void noteFunnel(const char *site, uint64_t attempted, uint64_t eligible,
                    uint64_t injected);

    // F5 stuck-at application where the value already equals the stuck
    // value. This is a real condition application and must be counted even
    // though no address bit changes.
    void noteNoChange(const char *site, uint64_t dyn_seq, Addr addr,
                      const char *mode, uint64_t execution_attempt_id,
                      uint64_t replay_generation);

    // SQ01: store data was corrupted after it entered the SQ entry. The node is
    // a real injection with the SQ index, generation and both bytes; the store
    // is also registered for its real commit node. v3.2.4 adds the store
    // vaddr/size so the faulted byte can be matched by later loads.
    void noteStoreDataInjection(uint64_t dyn_seq, uint64_t idx, uint64_t gen,
                                Addr vaddr, unsigned size,
                                uint8_t old_byte, uint8_t new_byte,
                                const char *mode);

    // DA04 (LSU v3.2.4): byte-enable lane-0 fault on a store. Allocates a
    // ptag, writes the injection node with original/injected masks and the
    // store data hash, and registers [vaddr, vaddr+1) for later loads.
    uint64_t noteStoreBEInjection(uint64_t dyn_seq, uint64_t idx,
                                  uint64_t gen, Addr vaddr, unsigned size,
                                  uint64_t old_mask, uint64_t new_mask,
                                  const uint8_t *store_data);

    // SQ drain: the request (with its final byte-enable) leaves for the
    // cache. Emits store_writeback for a registered faulted store.
    void noteStoreWriteback(uint64_t dyn_seq, uint64_t idx, uint64_t gen,
                            Addr vaddr, unsigned size,
                            const std::vector<bool> &be,
                            const uint8_t *data);

    // BaseCache::updateBlockData: the actual block-byte update for a faulted
    // store. Records before/after bytes, enabled-written and
    // disabled-unchanged (the DA04 proof the mask reached the memory write).
    void noteStoreMemWrite(const PacketPtr &pkt, Addr blk_addr,
                           const uint8_t *packet_data,
                           const std::vector<uint8_t> &before,
                           const std::vector<uint8_t> &after,
                           unsigned offset);

    bool isFaultStore(uint64_t dyn_seq) const;
    uint64_t faultStorePtag(uint64_t dyn_seq) const;

    // v3.2.4 review fix: called for EVERY cache write. If a different dynamic
    // store writes over a registered faulted byte, the fault store can no
    // longer be the source of a later load; mark the entry overwritten and
    // emit a store_overwrite node so the trace is honest.
    void noteStoreWrite(const PacketPtr &pkt);

    // Real LQ/SQ entry lifecycle (alloc/reuse/free), from the circular queue
    // insert/commit/squash sites.
    void noteLQLifecycle(uint64_t dyn_seq, uint64_t idx, uint64_t gen,
                         const char *action, const char *reason);
    void noteSQLifecycle(uint64_t dyn_seq, uint64_t idx, uint64_t gen,
                         const char *action, const char *reason);

    // ---- pipeline hooks (read-only w.r.t. CPU state) -----------------------
    // LSQ::LSQRequest::sendFragmentToTranslation: the fragment Request is
    // about to leave for translation/memory. Writes a mem_req node when it
    // matches the addr registry (addrpath) or the faulted-byte registry
    // (cache).
    void noteMemRequest(const char *site, uint64_t dyn_inst_seq,
                        const RequestPtr &req, int64_t lq_idx = -1,
                        int64_t sq_idx = -1);

    // LSQUnit::completeDataAccess (pre-writeback, squashed-guarded inside):
    // writes a resp node when the packet delivers a registered fault, and —
    // for register-writeback loads/SC/atomics with NoFault — taint_reg nodes
    // for the dest phys regs (added to the taint set).
    void noteMemResponse(o3::DynInst *inst, Packet *pkt, bool wb_to_reg);

    // Commit::commitHead (the W2.1/W2.4 anchor): commit-side taint
    // propagation. consumer nodes for tainted source phys regs, first
    // errant_commit, dest re-taint / clean-overwrite.
    void noteCommit(ThreadID tid, o3::DynInst *head_inst);

    // Real LSQ lifecycle events. These are called only from actual
    // reschedule/squash sites, never inferred from ptag order.
    void noteReplay(o3::DynInst *inst, const char *reason);
    // v3.2.12 (task 9): triggering_seq is the squash boundary — the
    // squashed_num argument of LSQUnit::squash(), i.e. the youngest
    // surviving instruction; everything younger is squashed. 0 (the default
    // the pre-wiring call sites fall back to) means "not recorded". The
    // squash_reason record carries it and the causality verdict comes from
    // chaos_fw02::classifySquash (standard §5: a proven fault-caused squash
    // needs the boundary to BE the faulting instruction).
    void noteSquash(o3::DynInst *inst, const char *reason,
                    uint64_t triggering_seq = 0);

    // Store-to-load forwarding decision. ptag=0 for an unfaulted normal
    // forward; the FW02 injection passes its registered ptag so the
    // decision is attached to the fault chain.
    void noteForwarding(uint64_t ptag, uint64_t load_seq, uint64_t store_seq,
                        Addr vaddr, unsigned size,
                        const uint8_t *store_data, unsigned store_size,
                        const uint8_t *fwd_data, unsigned fwd_size,
                        bool suppressed, bool memory_path);

    // FW02 (v3.2.12 task 9): the dedicated fw02_decision record
    // {load_seq, store_seq, normal_decision, fault_decision, memory_path,
    // replay_count} written at the suppression point (read-only; the
    // decision itself was already made by CHAOSLSQFwd). replay_count is the
    // number of trace-recorded replays of load_seq so far (noteReplay
    // counting; a replay before the load became fault-tracked is not on the
    // chain and is not counted).
    void noteFW02Decision(uint64_t ptag, uint64_t load_seq,
                          uint64_t store_seq, Addr vaddr, unsigned size);

    // v3.2.12: replay count observed (and recorded) for a dynamic
    // instruction's seq — 0 when none.
    uint64_t replayCount(uint64_t dyn_seq) const;

    // LP01 (LSU v3.2.5): a load-response data fault at completeDataAccess.
    // `before` is the payload copied before the XOR; the packet already holds
    // the injected bytes. Emits inj_l1dfwd with BOTH hashes and binds the
    // chain to the instruction so noteMemResponse records delivered data.
    uint64_t noteL1DForwardInjection(o3::DynInst *inst, Packet *pkt,
                                     bool wb_to_reg, const uint8_t *before,
                                     unsigned size, uint64_t mask,
                                     uint64_t eligible_ordinal);

    // After LSQUnit::writeback completed completeAcc: read the ACTUAL PRF
    // value and emit the LP01 register_writeback node + taint entry.
    void noteL1DForwardWriteback(o3::DynInst *inst);

    // Generic post-writeback taint: noteMemResponse stores the response hit;
    // after LSQUnit::writeback (completeAcc) this reads the ACTUAL PRF value
    // and emits the register_writeback node + taint entry. This makes the
    // source hash continuous with consumer input for every access size and
    // endianness, not just 8-byte loads.
    void noteChainWriteback(o3::DynInst *inst);

    // MD04: one real 8-byte store->younger-load violation report was
    // suppressed. The load keeps its stale data. If the response was already
    // consumed (`load_complete`), the writeback is late-bound from the PRF.
    // v3.2.7: the complete target-pair identity is emitted (store seq/addr/
    // size/PC, load addr/size/PC, SQ/LQ entry+generation, request id,
    // violation tick, eligible ordinals, seed).
    void noteMD04Injection(o3::DynInst *inst, o3::DynInst *store_inst,
                           const RequestPtr &load_req, Addr vaddr,
                           unsigned size, uint64_t eligible_ordinal,
                           uint64_t event_ordinal, uint64_t seed,
                           bool load_complete);

    // FW05 (v3.2.7): one load was served from an older store instead of the
    // gem5-selected true source. The response is bound by load seq so its
    // delivered data hash can be checked against alt_fnv.
    // SQ03: one store got _canWB early. Registers the store so a later load
    // that consumes its bytes is attributed to the same ptag.
    void noteSQ03Injection(uint64_t dyn_seq, uint64_t pc, Addr addr,
                           unsigned size, uint64_t sq_idx, uint64_t sq_gen,
                           bool canwb_before, bool canwb_after,
                           uint64_t stores_before, uint64_t stores_after,
                           Tick inject_tick, uint64_t eligible_ordinal,
                           uint64_t seed);
    void noteSQ03Writeback(uint64_t dyn_seq, Tick tick);
    void noteSQ03Complete(uint64_t dyn_seq, Tick tick);

    // SP05 (v3.2.9): premature completion state change. canwb/completed are
    // the pre-call values; stores_to_wb is the post-call counter.
    void noteSP05Injection(uint64_t dyn_seq, uint64_t pc, Addr addr,
                           unsigned size, uint64_t sq_idx, uint64_t sq_gen,
                           bool completed_before, bool completed_after,
                           uint64_t stores_before, uint64_t stores_after,
                           Tick inject_tick, uint64_t eligible_ordinal);

    void noteSP05Complete(uint64_t dyn_seq, uint64_t sq_idx, uint64_t sq_gen,
                          bool canwb, bool completed_before,
                          uint64_t stores_to_wb_before,
                          uint64_t stores_to_wb_after, bool mem_sent,
                          Tick tick);

    void noteFW05Injection(uint64_t load_seq, uint64_t load_pc,
                           uint64_t true_seq, Addr true_addr,
                           unsigned true_size, const std::string &true_fnv,
                           uint64_t alt_seq, Addr alt_addr,
                           unsigned alt_size, const std::string &alt_fnv,
                           Addr load_addr, unsigned load_size,
                           uint64_t sq_idx, uint64_t sq_gen,
                           uint64_t lq_idx, uint64_t lq_gen,
                           uint64_t load_attempt,
                           uint64_t eligible_ordinal, uint64_t event_ordinal,
                           uint64_t seed);

    // LQ04 (LSU v3.2.10): a load's LQ entry just had its lifetime corrupted
    // at the end of a successful executeLoad — _valid 1→0 and _request 1→0,
    // with the request moved into the LQEntry side channel (no pop, no early
    // free/reuse; address, size and response data untouched). Allocates a
    // ptag, writes the inj node with the before/after field states and
    // registers the chain by dyn_inst_seq so the response/writeback/consumer
    // binding (v3.2.10 Task 7) can attach to it. occ_before/occ_after are
    // the LQ occupancy around the corruption (equal by construction: no
    // pop). Returns the ptag (0 = tracer disabled / no-op).
    uint64_t noteLQ04Injection(o3::DynInst *inst, uint64_t lq_idx,
                               uint64_t lq_gen, uint64_t request_id,
                               Addr addr, unsigned size,
                               uint64_t occ_before, uint64_t occ_after,
                               uint64_t eligible_ordinal,
                               uint64_t event_ordinal, uint64_t injected,
                               uint64_t attempt_id, uint64_t replay_gen);

    // [LSU][V3.2.12][A01] golden/actual EA coordinate record (a01_ea) and the
    // first-consumer record (a01_consumed), staged by CHAOSAddrPath at EA
    // formation. ptag = the injection's chain ptag (registerInjection's return
    // at the call site; 0 = tracer disabled / no chain). Return: the ptag used.
    uint64_t noteA01EA(uint64_t ptag, const chaos_a01::EACoords &c);
    // A fault was raised while the corrupted request was in flight: complete
    // the registered record with the fault VA (registry lookup by dyn_inst_seq;
    // no-op when the seq is not a registered A01 chain).
    void noteA01FaultVA(uint64_t dyn_inst_seq, uint64_t fault_va);
    // Emit-once first-consumer record, called from noteCommit's first verified
    // consumer edge (the emit-once guard, consumed_emitted, lives at the
    // noteCommit anchor).
    void noteA01Consumed(uint64_t ptag, const chaos_a01::Consumed &c);
    // [LSU][V3.2.12][A01] replay-discard coverage node (A01 audit §3 remedy):
    // the hook injected, but the pushRequest took the savedRequest reuse
    // branch (inst->translationStarted()), so the corrupted by-value EA never
    // reached a Request and no memory chain at the actual EA can exist —
    // the a01_ea_discarded node (detail: the frozen eaDetail + applied_to_
    // request=0 + discard_reason) converts that silent structural absence
    // into an on-chain fact. Read-only; the a01_ea node stays unchanged.
    void noteA01EADiscarded(uint64_t ptag, const chaos_a01::EACoords &c);
    // [LSU][V3.2.12][A03] the F5 stream sink (A03 audit §1 remedy): the
    // activation record (a03_activation, {tick,bit,mode} via the frozen
    // activationDetail — one per run; the recorder already rejects a
    // second activation, and the sink-side emit-once guard below covers
    // the call site, which sees a03Activated() on every later staged row)
    // and one a03_stream node per fired eligible load (the frozen nine
    // contracted fields via streamDetail). ptag = that load's chain ptag
    // (0 = the ALREADY_STUCK no-change path / tracer disabled — the
    // ptag=0 "not bound to one chain" convention). Return: the ptag used.
    uint64_t noteA03Activation(uint64_t ptag, const chaos_a03::Activation &a);
    void noteA03Stream(uint64_t ptag, const chaos_a03::StreamEvent &e);

    // SP05 (v3.2.9): injection ptag per target store, reused by completion.
    std::unordered_map<uint64_t, uint64_t> sp05_ptag;

  private:
    // One CSV row: numeric fields with has_x=false print as "".
    uint64_t writeNode(uint64_t ptag, const char *kind, uint64_t dyn_seq,
                   bool has_seq, uint64_t request_id, bool has_req_id,
                   Addr addr, bool has_addr, uint64_t phys_reg, bool has_phys,
                   uint64_t arch_reg, bool has_arch, const std::string &detail,
                   Tick tick = 0);

    void writeEdgeRow(uint64_t ptag, uint64_t source_node,
                      uint64_t destination_node, uint64_t producer_seq,
                      uint64_t consumer_seq, const std::string &source_hash,
                      const std::string &destination_hash,
                      const char *edge_type);

    std::string bytesToHex(const uint8_t *p, unsigned n) const;
    std::string regValueHash(o3::DynInst *inst, PhysRegIdPtr phys,
                             ThreadID tid, uint64_t *value_out,
                             unsigned *bytes_out) const;

    uint64_t fnv1a64(const void *blob, size_t n) const;
    std::string fnvHex(const uint8_t *p, unsigned n) const;
    const char *regClassName(int class_value) const;

    // Lazy expiry sweep (called on insert/lookup; registries are tiny).
    void sweepExpired();

    // v3.2.12 (tasks 11/12/13): consolidated read-only chain records.
    // emitChainRecord writes the sq01_chain / sq03_effect / sp05_stage node
    // for one registered fault store (family dispatch inside);
    // writeDeferredChainRecords is called from the exit callback BEFORE
    // gzclose so stores whose chain never closed (no reload / no consumer)
    // still get their honest record with the absent fields null.
    struct FaultStoreEntry;            // defined below
    void emitChainRecord(uint64_t dyn_seq);
    void writeDeferredChainRecords();
    FaultStoreEntry *faultStoreByPtag(uint64_t ptag);

    BaseCPU *cpu;
    o3::CPU *o3cpu = nullptr;      // resolved at startup(); nullptr = disabled
    std::string trace_file;        // simout.resolve target (.gz, self-managed)
    bool write_log;                // gate ALL tracking + writing
    bool replay_all;               // record every replay, not just fault seqs
    uint64_t addr_expiry_ticks;    // registry entry lifetime (0 = never expire)
    gzFile gz_file = nullptr;      // raw zlib stream; crash-durability note

    static CHAOSPropagation *chaos_instance;

    uint64_t next_node_id = 0;
    uint64_t next_ptag = 0;        // 0 reserved ("no chain")
    uint64_t next_request_id = 0;
    uint64_t next_response_id = 0;
    uint64_t next_fragment_id = 0;
    uint64_t commit_seq = 0;
    bool errant_commit_seen = false;

    struct RequestMeta {
        uint64_t request_id = 0;
        uint64_t fragment_id = 0;
        Tick request_tick = 0;   // first fragment's issue tick (v3.2.5)
        Tick last_send_tick = 0; // most recent translation-send tick
        Addr vaddr = 0;
        unsigned size = 0;
        uint64_t dyn_seq = 0;
        int64_t lq_idx = -1;
        int64_t sq_idx = -1;
    };
    std::map<const Request *, RequestMeta> req_meta;
    std::set<uint64_t> fault_seqs;   // dynamic insts that received a fault
    std::set<uint64_t> replay_seqs;  // dynamic insts observed to replay
    // v3.2.12: per-seq replay counter feeding fw02_decision.replay_count.
    std::map<uint64_t, uint64_t> replay_count_by_seq;
    std::map<uint64_t, uint64_t> resp_node_by_ptag;
    std::map<uint64_t, std::string> resp_hash_by_ptag;

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
        uint64_t node_id;          // taint_reg event node
        std::string value_hash;    // stable hash of the writeback value
    };
    std::map<std::pair<int, uint32_t>, TaintEntry> taint_set;

    // v3.2.4 store-fault registry: DA04 byte-enable and SQ01 store-data
    // faults share the same identity so SQ drain, the cache write and later
    // loads can all attach to one ptag chain.
    struct FaultStoreEntry {
        uint64_t ptag = 0;
        uint64_t dyn_seq = 0;
        Addr base = 0;
        unsigned size = 0;
        uint64_t idx = 0;
        uint64_t gen = 0;
        Addr byte_begin = 0;      // affected byte range [begin, end)
        Addr byte_end = 0;
        const char *family = "store";   // "byte_enable" | "store_data" |
                                        // "sq03_canwb" | "sp05_complete"
        std::string old_mask;
        std::string new_mask;
        std::string data_fnv;
        std::string data_hex;
        Tick registered = 0;
        Tick written_tick = 0;     // actual cache write applied
        bool overwritten = false;  // a different store rewrote the byte

        // v3.2.12 read-only chain-record assembly (tasks 11/12/13). These
        // fields only feed the consolidated sq01_chain / sq03_effect /
        // sp05_stage trace nodes; they never gate an injection.
        uint8_t data_byte_before = 0;  // SQ01: entry byte0 at injection
        uint8_t data_byte_after = 0;   // SQ01: after the bit3 flip
        Tick store_commit_tick = 0;    // the store's own architectural commit
        Tick complete_tick = 0;        // SQ entry completed (completeStore)
        Tick resource_reuse_tick = 0;  // SQ slot idx reallocated (reuse)
        uint64_t reload_seq = 0;       // first reload bound to this chain
        std::string reload_hash;      // that reload's response data hash
        uint64_t consumer_seq = 0;     // first verified consumer edge
        std::string consumer_hash;    // its verified input hash
        bool chain_record_emitted = false;
    };
    std::map<uint64_t, FaultStoreEntry> fault_store_registry;

    // LP01 chain, keyed by the faulting instruction's dyn_inst_seq.
    struct L1DFwdEntry {
        uint64_t ptag = 0;
        uint64_t request_id = 0;
        uint64_t response_id = 0;
        uint64_t fragment_id = 0;
        Tick request_tick = 0;
        uint64_t eligible_ordinal = 0;
        unsigned size = 0;
        uint64_t mask = 0;
        std::string orig_fnv, orig_hex, inj_fnv, inj_hex;
        uint64_t resp_node = 0;
    };
    std::map<uint64_t, L1DFwdEntry> l1dfwd_registry;

    struct MD04Entry {
        uint64_t ptag = 0;
        uint64_t store_seq = 0;
        Addr vaddr = 0;
        unsigned size = 0;
        uint64_t eligible_ordinal = 0;
        bool load_complete = false;
        uint64_t request_id = 0;
        uint64_t resp_node = 0;
    };
    std::map<uint64_t, MD04Entry> md04_registry;  // key: load dyn seq

    struct FW05Entry {
        uint64_t ptag = 0;
        uint64_t true_seq = 0;
        uint64_t alt_seq = 0;
        Addr true_addr = 0;
        Addr alt_addr = 0;
        Addr load_addr = 0;
        unsigned load_size = 0;
        std::string true_fnv;
        std::string alt_fnv;
        uint64_t eligible_ordinal = 0;
        uint64_t resp_node = 0;
        bool wb_emitted = false;
    };
    std::map<uint64_t, FW05Entry> fw05_registry;  // key: load dyn seq

    struct SQ03Entry {
        uint64_t ptag = 0;
        uint64_t dyn_seq = 0;
        Addr addr = 0;
        unsigned size = 0;
        uint64_t sq_idx = 0;
        uint64_t sq_gen = 0;
        bool canwb_before = false;
        bool canwb_after = false;
        uint64_t stores_before = 0;
        uint64_t stores_after = 0;
        Tick inject_tick = 0;
        Tick wb_tick = 0;
        Tick complete_tick = 0;
        uint64_t eligible_ordinal = 0;
    };
    std::map<uint64_t, SQ03Entry> sq03_registry;  // key: store dyn seq

    // LQ04 (LSU v3.2.10): one LQ entry lifetime fault, keyed by the target
    // load's dyn_inst_seq. noteMemResponse binds the response (sets
    // resp_node, registers the pending chain writeback) and the
    // noteChainWriteback lq04 branch emits the register writeback from the
    // actual PRF value (data_corruption=0) and taints the dest; the entry
    // fields below mirror the inj node identity.
    struct LQ04Entry {
        uint64_t ptag = 0;
        uint64_t request_id = 0;   // Request::getReqInstSeqNum() of req(0)
        uint64_t lq_idx = 0;
        uint64_t lq_gen = 0;
        Addr addr = 0;
        unsigned size = 0;
        uint64_t eligible_ordinal = 0;
        uint64_t resp_node = 0;    // 0 until the response binds it
    };
    std::map<uint64_t, LQ04Entry> lq04_registry;  // key: load dyn seq

    // [LSU][V3.2.12][A01] key: the faulting load's dyn_inst_seq (lq04_registry
    // precedent). Holds the joined ptag, the staged record (completed with
    // the fault VA by noteA01FaultVA) and the emit-once flags for the
    // first-consumer (a01_consumed) node and the golden-EA reference
    // observation nodes (a01_golden_req / a01_golden_resp below).
    struct A01Chain {
        uint64_t ptag = 0;
        chaos_a01::EACoords coords;
        bool consumed_emitted = false;
        // [LSU][V3.2.12][A01] golden-EA reference observation (A01 audit §4
        // remedy (a), read-only): coords already carries the golden interval
        // [golden_ea, golden_ea+access_size) — registered at injection time
        // with the record itself. noteMemRequest/noteMemResponse emit the
        // reference nodes when the SAME dyn seq's Request/response covers
        // the golden EA (the replay-discard path: the reused savedRequest
        // still carries the golden vaddr) — the reference value R for the
        // DataDelta leg, recorded in the fault run. Reference-only: no
        // addr_registry entry, no taint, no pending writeback, no verdict
        // change — a golden hit never binds a fault chain.
        bool golden_req_emitted = false;
        bool golden_resp_emitted = false;
    };
    std::map<uint64_t, A01Chain> a01_registry;

    // [LSU][V3.2.12][A03] sink-side emit-once guard for the a03_activation
    // node (the recorder-side guard lives in chaos_a03::StreamRecorder).
    bool a03_activation_emitted = false;

    struct ChainWbEntry {
        uint64_t ptag = 0;
        uint64_t resp_node = 0;
        uint64_t request_id = 0;
        uint64_t response_id = 0;
        unsigned size = 0;
        std::string family;
        std::string payload_fnv;
        std::string payload_hex;
    };
    std::map<uint64_t, ChainWbEntry> pending_chain_wb;  // key: inst seq

    static uint64_t chaosBeMask(const std::vector<bool> &be);
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_PROPAGATION_HH__
