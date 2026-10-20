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
        "dyn_inst_seq", "commit_seq", "pc", "opcode", "lq_idx", "sq_idx",
        "request_id", "walk_id", "mshr_id", "fill_id", "pf_request_id",
        "va", "pa", "cache_line", "set", "way", "entry_index", "field",
        "before", "after", "state_before", "state_after", "arch_reg",
        "phys_reg", "detection_layer", "contained", "outcome", "oracle_diff",
        "evidence_status",
    };
    static constexpr int N_PROP_EVT_FIELDS =
        (int)(sizeof(PROP_EVT_FIELDS) / sizeof(PROP_EVT_FIELDS[0]));

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

    // Funnel row (attempted/eligible/injected as of NOW). Called by the
    // injectors at every successful injection AND at their exit callbacks
    // (final counts). Per-node Z_SYNC_FLUSH ⇒ abort-survivable.
    void noteFunnel(const char *site, uint64_t attempted, uint64_t eligible,
                    uint64_t injected);

    // ---- pipeline hooks (read-only w.r.t. CPU state) -----------------------
    // [MDSPEC][H1] Fault correlation for LSQ unified events: return the
    // ptag whose addr-registry entry matches (dyn_seq + range overlap) or
    // whose faulted-byte registry overlaps [addr, addr+size). 0 = no chain
    // (the request is not fault-correlated; PROP-EVT is a fault-propagation
    // stream, spec sheet 11 — non-correlated observations stay out).
    uint64_t correlateRequest(uint64_t dyn_seq, Addr addr, Addr size);

    // LSQ::LSQRequest::sendFragmentToTranslation: the fragment Request is
    // about to leave for translation/memory. Writes a mem_req node when it
    // matches the addr registry (addrpath) or the faulted-byte registry
    // (cache). Returns the FIRST matched ptag (0 = no match) so the H1
    // unified lsq_sendfrag event can carry the chain id.
    uint64_t noteMemRequest(const char *site, uint64_t dyn_inst_seq,
                            const RequestPtr &req);

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
    void writeNode(uint64_t ptag, const char *kind, uint64_t dyn_seq,
                   bool has_seq, uint64_t request_id, bool has_req_id,
                   Addr addr, bool has_addr, uint64_t phys_reg, bool has_phys,
                   uint64_t arch_reg, bool has_arch, const std::string &detail,
                   int tid = -1);

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
    std::map<uint64_t, uint64_t> ptag_last_event;

    static CHAOSPropagation *chaos_instance;

    uint64_t next_node_id = 0;
    uint64_t next_ptag = 0;        // 0 reserved ("no chain")
    bool errant_commit_seen = false;

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
    };
    std::map<std::pair<int, uint32_t>, TaintEntry> taint_set;
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_PROPAGATION_HH__
