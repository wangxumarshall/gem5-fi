// CHAOSPropagation.cc — [LSU][OBS-L3] real L3 propagation-chain tracer
// (central correction directive 2026-10-13). Four-piece SimObject family
// pattern (template: CHAOSMicroSnap/; setter-attach: CHAOSCommitTrace/).
// See CHAOSPropagation.hh for the pinned CSV contract and the v1
// registry/taint rules. Nothing here mutates CPU state: the only writes are
// to the trace file and the tracer's own registries/taint set.
//
// COMPILE-DEFERRED (source-level commit, 2026-10-13 directive): the AGU
// formal production batch is running and the guard gate forbids building;
// every C++ change in this series is verified against the
// CHAOSMicroSnap/CHAOSCommitTrace patterns item by item (see the commit
// message checklist) and compiled after the batch reaches terminal state
// (checklist in docs/gem5-fi/lsu/evidence/P4/obs_l3_propagation_design.md).

#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"

#include <cstring>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#include "cpu/o3/cpu.hh"          // o3::CPU: setChaosPropagation, o3Commit()
#include "cpu/o3/dyn_inst.hh"     // DynInst: seqNum/renamedSrcIdx/destRegIdx
#include "cpu/reg_class.hh"       // RegClassType values
#include "mem/packet.hh"          // Packet: getAddr/getSize/getPtr/req
#include "params/CHAOSPropagation.hh"
#include "sim/cur_tick.hh"        // curTick()
#include "sim/sim_exit.hh"        // registerExitCallback

namespace gem5
{

    CHAOSPropagation *CHAOSPropagation::chaos_instance = nullptr;

    CHAOSPropagation::CHAOSPropagation(const CHAOSPropagationParams &p)
        : SimObject(p),
          cpu(p.cpu),
          trace_file(p.traceFile),
          write_log(p.writeLog),
          addr_expiry_ticks(p.addrExpiryTicks),
          evt_trace_file(p.evtTraceFile),
          run_id(p.runId),
          sample_run_id(p.sampleRunId)
    {
        // CHAOSCache (no CPU pointer) reaches the tracer through the static
        // instance (single-core campaign; BaseCache::chaosVictimHook static
        // precedent). Last instance wins — one instance per run here.
        chaos_instance = this;

        if (write_log) {
            // Raw zlib gzFile at simout.resolve(trace_file) — NOT
            // simout.create's gz streambuf (that path only gzwrite()s and
            // zlib holds data until gzclose, so an aborted run loses the
            // file; CHAOSMicroSnap measured 0 bytes there). Every node
            // below is followed by gzflush(Z_SYNC_FLUSH) — the per-node
            // cost is irrelevant here (a handful of nodes per run).
            const std::string path = simout.resolve(trace_file);
            gz_file = gzopen(path.c_str(), "wb");
            if (!gz_file)
                panic("CHAOSPropagation: Could not open trace file %s",
                      path.c_str());
            const char *header =
                "# lsu-propagation v1: node_id,tick,ptag,kind,dyn_inst_seq,"
                "request_id,addr,phys_reg,arch_reg,detail\n";
            const int hlen = (int)strlen(header);
            if (gzwrite(gz_file, header, hlen) != hlen)
                panic("CHAOSPropagation: header write failed on %s",
                      path.c_str());
            gzflush(gz_file, Z_SYNC_FLUSH);

            // PROP-EVT unified stream (H0): same crash-durability contract
            // (raw gzFile + per-node Z_SYNC_FLUSH). The '#' header line
            // carries the registry; the Python parser rejects it as a
            // non-PROP-EVT line.
            const std::string epath = simout.resolve(evt_trace_file);
            evt_gz_file = gzopen(epath.c_str(), "wb");
            if (!evt_gz_file)
                panic("CHAOSPropagation: Could not open PROP-EVT file %s",
                      epath.c_str());
            std::ostringstream eh;
            eh << "# prop-evt v1:";
            for (int i = 0; i < N_PROP_EVT_FIELDS; ++i)
                eh << " " << PROP_EVT_FIELDS[i];
            // [R6] the family-extension columns are part of the row contract
            // too, so the header must list them (else the row would carry
            // keys the documented schema does not name).
            for (int i = 0; i < N_PROP_EVT_EXT_FIELDS; ++i)
                eh << " " << PROP_EVT_EXT_FIELDS[i];
            eh << "\n";
            const std::string ehs = eh.str();
            if (gzwrite(evt_gz_file, ehs.data(), (unsigned)ehs.size())
                    != (int)ehs.size())
                panic("CHAOSPropagation: PROP-EVT header write failed on %s",
                      epath.c_str());
            gzflush(evt_gz_file, Z_SYNC_FLUSH);

            // Normal-exit trailer: gzclose writes the gzip trailer. MUST be
            // an exit callback, not the destructor — gem5's exit path does
            // not reliably run SimObject destructors (CHAOSMicroSnap
            // measurement; CHAOSProbe exit-callback precedent). Aborted runs
            // never get here: they keep the Z_SYNC_FLUSH-ed truncated
            // stream, which tools/lsu_l3_propagation.py salvages.
            registerExitCallback([this]() {
                // [MDSPEC][L5] chain_end events: one per fault chain at
                // exit. The observable state (errant_commit seen or not,
                // outcome) is what gem5 alone knows; the FINAL checksum /
                // exit-code classification is the offline reclass join
                // (spec sheet 9: L5 = 检测与最终结局, joined offline).
                // outcome=unknown means "pending offline join" — the honest
                // default, never guessed (spec: 不得推断).
                if (evt_gz_file && write_log) {
                    for (const auto &kv : ptag_last_event) {
                        const uint64_t ptag = kv.first;
                        // [MDSPEC][R6] Per-chain evidence, not a run-global
                        // guess: the errant_commit node carries the faulting
                        // chain's own ptag, so this chain's L5 can say
                        // "the wrong value reached the architectural state"
                        // instead of falling back to the bare lifecycle
                        // marker (outcome=run_end) that the chain checker
                        // rejects as L5 evidence. Chains that did not commit
                        // errantly keep run_end — still honest.
                        const bool seen_errant = errant_ptags.count(ptag) > 0;
                        const auto cit = containment_ptags.find(ptag);
                        const bool contained = cit != containment_ptags.end();
                        // [R6] This node is a LIFECYCLE terminus, not L5
                        // evidence on its own: it never invents a detection
                        // layer. It REPORTS what the chain's own events
                        // proved — the errant commit (real L5 detection, the
                        // chain's `errant_commit` node) or the explicit
                        // containment recorded at L2 (Masked / refused /
                        // lost walk). A chain with neither stays honestly
                        // empty (no layer, outcome=run_end): a bare
                        // lifecycle marker must never be read as L5.
                        const char *outcome = seen_errant ? "errant_commit_seen"
                            : contained ? "detected_contained" : "run_end";
                        const char *layer = seen_errant ? "L5"
                            : contained ? cit->second.first.c_str() : "";
                        notePropEvt("chain_end", {
                            {"fault_id", std::to_string(ptag)},
                            {"outcome", outcome},
                            {"detection_layer", layer},
                            {"contained", (seen_errant || contained)
                                ? "1" : "0"},
                            {"containment_layer",
                                contained ? cit->second.first : ""},
                            {"containment_reason",
                                contained ? cit->second.second : ""},
                            // [R4-4-review-I1] explicit non-join marker:
                            // the exit summary correlates nothing (the
                            // per-event corr fields carry provenance).
                            {"corr", CORR_NONE},
                        });
                    }
                }
                if (gz_file) {
                    gzclose(gz_file);
                    gz_file = nullptr;
                }
                if (evt_gz_file) {
                    gzclose(evt_gz_file);
                    evt_gz_file = nullptr;
                }
            });
        }
    }

    CHAOSPropagation::~CHAOSPropagation()
    {
        // Backstop only (exit callback above is the primary closer).
        if (gz_file) {
            gzclose(gz_file);
            gz_file = nullptr;
        }
        if (evt_gz_file) {
            gzclose(evt_gz_file);
            evt_gz_file = nullptr;
        }
        if (chaos_instance == this)
            chaos_instance = nullptr;
    }

    void
    CHAOSPropagation::startup()
    {
        SimObject::startup();
        auto *o3 = dynamic_cast<o3::CPU *>(cpu);
        if (!o3) {
            warn("CHAOSPropagation: cpu is not an O3CPU; tracer disabled.\n");
            return;
        }
        o3cpu = o3;
        // PROP-EVT cycle field: tick / clockPeriod (integer division).
        clock_period = o3cpu->clockPeriod();
        // CHAOSCommitTrace/CHAOSMicroSnap setter pattern, both consumers:
        // (a) the CPU pointer the LSQ-side hooks (lsq.cc / lsq_unit.cc)
        //     read via cpu->chaosPropagation;
        // (b) the commit-stage pointer the commit.cc hook tests
        //     (cpu->o3Commit().setChaosPropagation — W2.1 anchor).
        o3cpu->setChaosPropagation(this);
        o3cpu->o3Commit().setChaosPropagation(this);
    }

    // ------------------------------------------------------------------ util

    uint64_t
    CHAOSPropagation::fnv1a64(const void *blob, size_t n) const
    {
        const uint8_t *p = static_cast<const uint8_t *>(blob);
        uint64_t h = 14695981039346656037ULL;  // FNV-1a 64-bit offset basis
        for (size_t i = 0; i < n; ++i) {
            h ^= p[i];
            h *= 1099511628211ULL;             // FNV-1a 64-bit prime
        }
        return h;
    }

    const char *
    CHAOSPropagation::regClassName(int class_value) const
    {
        // CHAOSCommitTrace.cc switch precedent (RegClassType values).
        switch ((RegClassType)class_value) {
          case IntRegClass:    return "int";
          case FloatRegClass:  return "float";
          case VecRegClass:    return "vec";
          case VecElemClass:   return "vecelem";
          case CCRegClass:     return "cc";
          case MatRegClass:    return "mat";
          default:             return "misc";
        }
    }

    void
    CHAOSPropagation::sweepExpired()
    {
        if (addr_expiry_ticks == 0)
            return;
        const Tick now = curTick();
        for (auto it = addr_registry.begin(); it != addr_registry.end(); ) {
            if (now > it->second.registered &&
                now - it->second.registered > (Tick)addr_expiry_ticks)
                it = addr_registry.erase(it);
            else
                ++it;
        }
        for (auto it = blk_registry.begin(); it != blk_registry.end(); ) {
            if (now > it->second.registered &&
                now - it->second.registered > (Tick)addr_expiry_ticks)
                it = blk_registry.erase(it);
            else
                ++it;
        }
        // [MDSPEC][H5] prefetch requests share the same lifetime policy as
        // the other address registries (no expiry when addr_expiry_ticks=0).
        for (auto it = pf_registry.begin(); it != pf_registry.end(); ) {
            if (now > it->second.registered &&
                now - it->second.registered > (Tick)addr_expiry_ticks)
                it = pf_registry.erase(it);
            else
                ++it;
        }
    }

    // ------------------------------------------------------ PROP-EVT (H0)

    void
    CHAOSPropagation::parseDetail(const std::string &detail,
                                  std::map<std::string, std::string> &out)
    {
        // v1 detail contract: "k=v;k=v", no commas. Keys that match a
        // unified field name (pc/field) land directly; others are lifted by
        // the caller where the schema has a home.
        size_t pos = 0;
        while (pos < detail.size()) {
            const size_t semi = detail.find(';', pos);
            const std::string tok = detail.substr(
                pos, semi == std::string::npos ? std::string::npos : semi - pos);
            const size_t eq = tok.find('=');
            if (eq != std::string::npos)
                out[tok.substr(0, eq)] = tok.substr(eq + 1);
            if (semi == std::string::npos)
                break;
            pos = semi + 1;
        }
    }

    void
    CHAOSPropagation::emitPropEvt(const std::string &kind, uint64_t ptag,
                                  uint64_t event_id,
                                  std::map<std::string, std::string> fields,
                                  int tid)
    {
        if (!write_log || !evt_gz_file)
            return;
        // Auto fields: caller-supplied non-empty values win.
        const Tick now = curTick();
        if (fields["tick"].empty())
            fields["tick"] = std::to_string(now);
        if (fields["cycle"].empty())
            fields["cycle"] = clock_period
                ? std::to_string(now / clock_period) : std::string("0");
        if (fields["core_id"].empty())
            fields["core_id"] = std::to_string(cpu ? cpu->cpuId() : 0);
        if (tid >= 0 && fields["thread_id"].empty())
            fields["thread_id"] = std::to_string(tid);
        fields["fault_id"] = std::to_string(ptag);
        fields["event_id"] = std::to_string(event_id);
        if (fields["parent_event_id"].empty()) {
            const auto it = ptag_last_event.find(ptag);
            if (it != ptag_last_event.end() && it->second != event_id)
                fields["parent_event_id"] = std::to_string(it->second);
        }
        if (!run_id.empty() && fields["run_id"].empty())
            fields["run_id"] = run_id;
        if (!sample_run_id.empty() && fields["sample_run_id"].empty())
            fields["sample_run_id"] = sample_run_id;
        if (fields["evidence_status"].empty())
            fields["evidence_status"] = "observed";   // spec sheet 11 default
        // kind is forced — the caller cannot retype an event.
        fields["kind"] = kind;

        std::ostringstream row;
        row << "PROP-EVT:";
        for (int i = 0; i < N_PROP_EVT_FIELDS; ++i) {
            const auto it = fields.find(PROP_EVT_FIELDS[i]);
            row << ' ' << PROP_EVT_FIELDS[i] << '='
                << (it == fields.end() ? "" : it->second);
        }
        // [R6] family-extension columns follow the shared registry (same
        // key=value shape; parser keeps them for the family that owns them).
        for (int i = 0; i < N_PROP_EVT_EXT_FIELDS; ++i) {
            const char *k = PROP_EVT_EXT_FIELDS[i];
            const auto it = fields.find(k);
            row << ' ' << k << '=' << (it == fields.end() ? "" : it->second);
        }
        row << '\n';
        const std::string s = row.str();
        if (gzwrite(evt_gz_file, s.data(), (unsigned)s.size()) != (int)s.size())
            panic("CHAOSPropagation: PROP-EVT write failed (event %llu)",
                  (unsigned long long)event_id);
        gzflush(evt_gz_file, Z_SYNC_FLUSH);
        if (ptag != 0)
            ptag_last_event[ptag] = event_id;
    }

    void
    CHAOSPropagation::notePropEvt(
        const std::string &kind,
        const std::vector<std::pair<std::string, std::string>> &kv)
    {
        if (!write_log || !evt_gz_file)
            return;
        std::map<std::string, std::string> fields;
        uint64_t ptag = 0;
        for (const auto &pair : kv) {
            bool known = false;
            for (int i = 0; i < N_PROP_EVT_FIELDS; ++i) {
                if (pair.first == PROP_EVT_FIELDS[i]) {
                    known = true;
                    break;
                }
            }
            // [R6] family-extension keys (containment_layer/_reason) are
            // legitimately emitted but live outside the shared registry.
            for (int i = 0; !known && i < N_PROP_EVT_EXT_FIELDS; ++i) {
                if (pair.first == PROP_EVT_EXT_FIELDS[i])
                    known = true;
            }
            if (!known) {
                if (!evt_unknown_key_warned) {
                    warn("CHAOSPropagation: PROP-EVT unknown field '%s' "
                         "(dropped; further drops are silent)\n",
                         pair.first.c_str());
                    evt_unknown_key_warned = true;
                }
                continue;
            }
            fields[pair.first] = pair.second;
        }
        const auto fp = fields.find("fault_id");
        if (fp != fields.end() && !fp->second.empty())
            ptag = strtoull(fp->second.c_str(), nullptr, 10);
        emitPropEvt(kind, ptag, next_node_id++, std::move(fields), -1);
    }

    // ------------------------------------------------------------------ util

    void
    CHAOSPropagation::writeNode(uint64_t ptag, const char *kind,
                                uint64_t dyn_seq, bool has_seq,
                                uint64_t request_id, bool has_req_id,
                                Addr addr, bool has_addr,
                                uint64_t phys_reg, bool has_phys,
                                uint64_t arch_reg, bool has_arch,
                                const std::string &detail, const char *corr,
                                int tid)
    {
        if (!write_log || !gz_file)
            return;
        // Numeric fields without a value are EMPTY strings (pinned contract).
        std::ostringstream row;
        row << next_node_id << ',' << curTick() << ',' << ptag << ','
            << kind << ',';
        if (has_seq) row << dyn_seq;
        row << ',';
        if (has_req_id) row << request_id;
        row << ',';
        if (has_addr) row << std::hex << addr << std::dec;
        row << ',';
        if (has_phys) row << phys_reg;
        row << ',';
        if (has_arch) row << arch_reg;
        row << ',' << detail << '\n';
        const std::string s = row.str();
        if (gzwrite(gz_file, s.data(), (unsigned)s.size())
                != (int)s.size())
            panic("CHAOSPropagation: node write failed (node %llu kind %s)",
                  (unsigned long long)next_node_id, kind);
        // Crash durability (W2.1 contract): one flush per node — an aborted
        // run keeps every completed node readable (trailer-less prefix).
        gzflush(gz_file, Z_SYNC_FLUSH);

        // PROP-EVT dual-emit (H0): same event in the unified sheet-11
        // schema; event_id == this node_id (1:1 join with the v1 CSV row).
        // Funnel rows are not propagation events — no dual-emit.
        if (strcmp(kind, "funnel") != 0) {
            std::map<std::string, std::string> f;
            parseDetail(detail, f);
            // [R4-4-review-I1] every dual-emitted event carries an explicit
            // corr provenance marker (join arm, or a non-join marker saying
            // HOW it belongs to the chain). nullptr = the caller forgot —
            // warn once and emit corr= so the gap is visible, never silent.
            if (!corr && !evt_corr_missing_warned) {
                warn("CHAOSPropagation: writeNode kind '%s' dual-emitted "
                     "without a corr label (corr= written; further "
                     "occurrences are silent)\n", kind);
                evt_corr_missing_warned = true;
            }
            f["corr"] = corr ? corr : "";
            if (has_seq)
                f["dyn_inst_seq"] = std::to_string(dyn_seq);
            if (has_req_id)
                f["request_id"] = std::to_string(request_id);
            if (has_addr) {
                std::ostringstream a;
                a << std::hex << addr;
                f["va"] = a.str();
            }
            if (has_phys)
                f["phys_reg"] = std::to_string(phys_reg);
            if (has_arch)
                f["arch_reg"] = std::to_string(arch_reg);
            // detail lifts: old_addr/new_addr → before/after; block_addr →
            // cache_line; pc=/field= already land on their unified names.
            const auto oa = f.find("old_addr");
            if (oa != f.end())
                f["before"] = oa->second;
            const auto na = f.find("new_addr");
            if (na != f.end())
                f["after"] = na->second;
            const auto ba = f.find("block_addr");
            if (ba != f.end())
                f["cache_line"] = ba->second;
            emitPropEvt(kind, ptag, next_node_id, std::move(f), tid);
        }
        ++next_node_id;
    }

    // ------------------------------------------------------- registration

    uint64_t
    CHAOSPropagation::registerInjection(const char *site, uint64_t dyn_seq,
                                        Addr old_addr, Addr new_addr,
                                        bool is_load, unsigned old_size,
                                        unsigned new_size)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node: the injection event (addr column = the ORIGINAL addr).
        {
            std::ostringstream d;
            d << "site=" << site << ";family=addrpath;is_load="
              << (is_load ? 1 : 0)
              << ";old_size=" << old_size << ";new_size=" << new_size
              << ";old_addr=" << std::hex << old_addr
              << ";new_addr=" << new_addr << std::dec;
            writeNode(ptag, "inj", dyn_seq, true, 0, false,
                      old_addr, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // addr_form node: the erroneous address (addr column = NEW addr).
        {
            std::ostringstream d;
            d << "site=" << site << ";old_addr=" << std::hex << old_addr
              << ";new_addr=" << new_addr << std::dec;
            writeNode(ptag, "addr_form", dyn_seq, true, 0, false,
                      new_addr, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // Addr registry: [new_addr, new_addr+size). size==0 (s11 lost-store
        // substitution) registers an address-only marker that never
        // range-matches — the chain then honestly stops at addr_form.
        sweepExpired();
        AddrEntry e;
        e.ptag = ptag;
        e.dyn_seq = dyn_seq;
        e.base = new_addr;
        e.size = new_size;
        e.registered = curTick();
        addr_registry[new_addr] = e;
        return ptag;
    }

    uint64_t
    CHAOSPropagation::registerCacheFault(Addr block_addr, int byte_offset,
                                         Addr block_size, const char *field)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the faulted block address).
        {
            std::ostringstream d;
            d << "family=cache;field=" << field
              << ";byte_offset=" << byte_offset
              << ";block_addr=" << std::hex << block_addr << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      block_addr, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        if (byte_offset >= 0) {
            // Single faulted byte (data faults).
            sweepExpired();
            BlkEntry e;
            e.ptag = ptag;
            e.byte_begin = block_addr + (Addr)byte_offset;
            e.byte_end = e.byte_begin + 1;
            e.registered = curTick();
            blk_registry[e.byte_begin] = e;
        } else if (byte_offset == -1) {
            // Whole-block fault (data_shift rotate corrupts every byte).
            sweepExpired();
            BlkEntry e;
            e.ptag = ptag;
            e.byte_begin = block_addr;
            e.byte_end = block_addr + block_size;
            e.registered = curTick();
            blk_registry[block_addr] = e;
        }
        // byte_offset == -2 (metadata field / victim path): NO registry —
        // the chain honestly stops at the inj node (see .hh).
        return ptag;
    }

    // [MDSPEC][R4-5.1] C11 MSHR merge corruption (see .hh for the full
    // contract). Address-only registration (the labeled addr_fallback arm):
    // this site has no Request seq binding for the MSHR entry itself — the
    // seq of the merging load belongs to the response side, which joins by
    // packet-address overlap instead.
    uint64_t
    CHAOSPropagation::registerMshrMergeFault(Addr line, Addr old_addr,
                                             Addr new_addr, unsigned size)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the corrupted target address; detail
        // keys old_addr/new_addr/block_addr are lifted by the writeNode
        // dual-emit into before/after/cache_line).
        {
            std::ostringstream d;
            d << "family=cache;field=mshr_merge"
              << ";old_addr=" << std::hex << old_addr
              << ";new_addr=" << new_addr
              << ";size=" << std::dec << size
              << ";block_addr=" << std::hex << line << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      new_addr, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // faulted-byte (blk) registry: the CORRUPTED target range. The
        // fill's readout serves the block at the corrupted offset and the
        // response returns on the corrupted address, so noteMemResponse's
        // cache arm (pkt->getAddr()) fires there; the H4 mshr_merge event
        // (correlateBlock on the corrupted address, same line) and the
        // line-level mshr_fill/cache_fill/mshr_free events join by overlap.
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = new_addr;
            b.byte_end = new_addr + (size ? (Addr)size : 1);
            b.registered = curTick();
            blk_registry[b.byte_begin] = b;
        }
        return ptag;
    }

    // [MDSPEC][R4-5.2] C12 fill-timing offset (see .hh for the full
    // contract). Address-only registration (the labeled addr_fallback arm):
    // the fill-response site has no Request seq binding — the delayed
    // fill's consumers join by line overlap instead.
    uint64_t
    CHAOSPropagation::registerFillTimingFault(Addr line, Addr block_size,
                                              Tick arrival_tick,
                                              Tick deferred_tick,
                                              uint64_t delay_cycles)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the deferred fill's line). before/after
        // carry the faulted VALUE for this model — the fill's delivery
        // tick before/after the offset (registered fields, so the pair is
        // stream-visible on the dual-emit; delay_cycles stays in the
        // detail for the v1 CSV node and is derivable as after-before).
        {
            std::ostringstream d;
            d << "family=cache;field=mshr_fill_timing"
              << ";before=" << arrival_tick
              << ";after=" << deferred_tick
              << ";delay_cycles=" << delay_cycles
              << ";block_addr=" << std::hex << line << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      line, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // faulted-byte (blk) registry: the WHOLE fill line. The delayed
        // mshr_fill/cache_fill/mshr_free events (correlateBlock on the
        // line), cache_access on later lookups, and noteMemResponse's
        // cache arm (the response delivery on this very line) all join by
        // overlap — at the shifted tick, so the trace itself witnesses the
        // offset (mshr_fill.tick - inj.tick = the delay + the normal fill
        // pipeline latency).
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = line;
            b.byte_end = line + (block_size ? block_size : 1);
            b.registered = curTick();
            blk_registry[b.byte_begin] = b;
        }
        return ptag;
    }

    // [MDSPEC][R4-5.5] C14-a MSHR busy/occupied stuck-at-1 (see .hh for the
    // full contract). Address-only registration (the labeled addr_fallback
    // arm): the release-point site has no Request seq binding — later
    // events on the leaked entry's line join by overlap instead.
    uint64_t
    CHAOSPropagation::registerMshrBusyFault(Addr line, Addr block_size,
                                            uint64_t occ_before,
                                            uint64_t occ_after, bool was_full)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the leaked entry's line). before/after =
        // the occupancy pair — this model's faulted VALUE: the in-service
        // occupancy that the correct release would have left (before) vs.
        // the occupancy with the release SKIPPED (after).
        {
            std::ostringstream d;
            d << "family=cache;field=mshr_busy_leak"
              << ";before=" << occ_before
              << ";after=" << occ_after
              << ";was_full=" << (was_full ? 1 : 0)
              << ";block_addr=" << std::hex << line << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      line, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // model-specific mshr_busy node (the stuck occupied state itself).
        // mshr_id: the propagator's line-keyed MSHR registry id for this
        // entry — looked up, and minted when it did not exist yet (the
        // fault is registered at the release point, which may precede any
        // H4 mshr_alloc observation of this line). Deliberately NOT
        // released here (no noteMshrFree): the leak is the point.
        {
            uint64_t mid = noteMshrLookup(line);
            if (!mid)
                mid = noteMshrAlloc(line);
            std::ostringstream h;
            h << std::hex << line;
            notePropEvt("mshr_busy", {
                {"fault_id", std::to_string(ptag)},
                {"corr", CORR_ORIGIN},
                {"mshr_id", std::to_string(mid)},
                {"entry_index", std::to_string(mid)},
                {"cache_line", h.str()},
                {"field", "busy"},
                {"state_before", "should_release"},
                {"state_after", "stuck_busy"},
            });
        }
        // faulted-byte (blk) registry: the WHOLE leaked line. Later events
        // on that line (a re-miss' mshr_alloc/mshr_merge, cache_access, a
        // response delivery) join by overlap — corr=addr_fallback.
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = line;
            b.byte_end = line + (block_size ? block_size : 1);
            b.registered = curTick();
            blk_registry[b.byte_begin] = b;
        }
        return ptag;
    }

    // [MDSPEC][R4-5.6] C15-b MSHR capacity-arbitration fake-free (see .hh
    // for the full contract). Address-only registration (the labeled
    // addr_fallback arm): the arbitration site has no Request seq binding —
    // later events on the over-committed request's line join by overlap.
    uint64_t
    CHAOSPropagation::registerMshrArbFault(Addr line, Addr block_size,
                                           uint64_t occ_before,
                                           uint64_t occ_after,
                                           bool materialized)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the over-committed request's line).
        // before/after = the occupancy pair — this model's faulted VALUE:
        // the in-service occupancy at the fire (before) vs. at the
        // over-capacity allocation (after).
        {
            std::ostringstream d;
            d << "family=cache;field=mshr_occupancy"
              << ";before=" << occ_before
              << ";after=" << occ_after
              << ";materialized=" << (materialized ? 1 : 0)
              << ";block_addr=" << std::hex << line << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      line, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // model-specific mshr_arb node (the arbitration observation: the
        // arbitration genuinely ALLOWED an allocation beyond capacity).
        {
            std::ostringstream h;
            h << std::hex << line;
            notePropEvt("mshr_arb", {
                {"fault_id", std::to_string(ptag)},
                {"corr", CORR_ORIGIN},
                {"mshr_id", std::to_string(noteMshrAlloc(line))},
                {"entry_index", std::to_string(occ_after)},
                {"cache_line", h.str()},
                {"field", "capacity"},
                {"state_before", "full_blocked"},
                {"state_after", "over_commit_alloc"},
            });
        }
        // faulted-byte (blk) registry: the over-committed request's line.
        // Later events on that line (cache_access, mshr_merge/fill/free,
        // the response delivery) join by overlap — corr=addr_fallback.
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = line;
            b.byte_end = line + (block_size ? block_size : 1);
            b.registered = curTick();
            blk_registry[b.byte_begin] = b;
        }
        return ptag;
    }

    // [MDSPEC][R4-5.4] P06-a prefetch-as-demand fill classification fault
    // (see .hh for the full contract). Address-only registration (the
    // labeled addr_fallback arm): the fill-classification site has no
    // Request seq binding — the marked line's later consumers join by
    // line overlap instead.
    uint64_t
    CHAOSPropagation::registerPfFillClassFault(Addr line, Addr block_size)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the marked line). before/after carry
        // the faulted VALUE for this model — the fill's demand/prefetch
        // classification before/after the marking (registered fields, so
        // the pair is stream-visible on the dual-emit; the string values
        // are the third per-model value type after C12's tick pair and
        // L04's seq pair — read them together with field=pf_fill_class).
        {
            std::ostringstream d;
            d << "family=prefetch;field=pf_fill_class"
              << ";before=prefetch"
              << ";after=demand"
              << ";block_addr=" << std::hex << line << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      line, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // faulted-byte (blk) registry: the WHOLE marked line. cache_access
        // on later lookups, cache_fill/mshr_fill/mshr_free on refetches,
        // cache_evict on eviction, and noteMemResponse's cache arm (a
        // demand load served on this line -> resp/lq_complete/taint_reg)
        // all join by overlap, each carrying corr=addr_fallback (the
        // labeled over-approximation: a correct response on the same
        // line also joins — C11 §5.1.6 precedent; the oracle adjudicates).
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = line;
            b.byte_end = line + (block_size ? block_size : 1);
            b.registered = curTick();
            blk_registry[b.byte_begin] = b;
        }
        return ptag;
    }


    // [MDSPEC][R4-5.8] A07-b AGU-ready delay (see .hh for the full
    // contract — the late-binding design and why NO registry entry is
    // made here). inj node only; the address binding arrives with the
    // delayed instruction's EA at LSQ::pushRequest (bindAguFaultAddr).
    uint64_t
    CHAOSPropagation::registerAguReadyFault(uint64_t dyn_seq,
                                            long long lq_idx,
                                            long long sq_idx,
                                            Tick ready_tick,
                                            Tick delayed_tick,
                                            uint64_t delay_cycles,
                                            bool is_load, Addr pc)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (dyn_seq = the delayed instruction — the fault IS its
        // ready timing). before/after carry the faulted VALUE for this
        // model: the ready tick before/after the bounded delay (the C12
        // delivery-tick precedent; value type is per-model, documented at
        // the registration point and lifted by the writeNode dual-emit).
        // delay_cycles / lq_idx / sq_idx / pc stay in the v1 detail.
        {
            std::ostringstream d;
            d << "family=addrpath;field=agu_ready_delay"
              << ";before=" << ready_tick
              << ";after=" << delayed_tick
              << ";delay_cycles=" << delay_cycles
              << ";is_load=" << (is_load ? 1 : 0)
              << ";lq_idx=" << lq_idx
              << ";sq_idx=" << sq_idx
              << ";pc=0x" << std::hex << pc << std::dec;
            writeNode(ptag, "inj", dyn_seq, true,
                      0, false, 0, false, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // NO registry entry: the EA does not exist at the ready point.
        // bindAguFaultAddr (called from the pushRequest PRE hook at the
        // delayed tick) binds the chain to the real address range.
        return ptag;
    }

    // [MDSPEC][R4-5.8] A07 late address binding: attach the ptag from
    // registerAguReadyFault to [addr, addr+size) bound to dyn_seq (the
    // seq-primary arm — same entry shape as registerLSQForwardFault's
    // PRIMARY, but the range is the DELAYED instruction's own access:
    // only its requests/events match, never another instruction's).
    void
    CHAOSPropagation::bindAguFaultAddr(uint64_t ptag, uint64_t dyn_seq,
                                       Addr addr, unsigned size)
    {
        if (!write_log || ptag == 0 || dyn_seq == 0)
            return;
        sweepExpired();
        AddrEntry e;
        e.ptag = ptag;
        e.dyn_seq = dyn_seq;
        e.base = addr;
        e.size = size ? size : 1;
        e.registered = curTick();
        addr_registry[addr] = e;
    }

    // [MDSPEC][R4-1] SQ store->load forwarding fault (seq-primary).
    uint64_t
    CHAOSPropagation::registerLSQForwardFault(
        uint64_t store_seq, long long sq_idx, uint64_t store_req_id,
        uint64_t load_seq, long long lq_idx, uint64_t load_req_id,
        Addr vaddr, Addr size, const char *field)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;
        const Addr span = size ? size : 1;

        // inj node: the consuming load's seq (the instruction whose
        // architectural state receives the corrupted data) + both sides'
        // keys in the detail for the v1 CSV.
        {
            std::ostringstream d;
            d << "family=lsqfwd;field=" << field
              << ";store_dyn_inst_seq=" << store_seq
              << ";sq_idx=" << sq_idx
              << ";store_request_id=" << store_req_id
              << ";load_dyn_inst_seq=" << load_seq
              << ";lq_idx=" << lq_idx
              << ";load_request_id=" << load_req_id
              << ";fwd_addr=" << std::hex << vaddr << std::dec;
            writeNode(ptag, "inj", load_seq, true,
                      load_req_id, load_req_id != 0,
                      vaddr, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }

        // PRIMARY: addr-registry entry bound to the producer store's
        // dyn_inst_seq. The store is definitionally still in the SQ at
        // forward time (the scan window ends at storeWBIt), so its
        // sq_writeback / sq_complete fire AFTER this registration and join
        // the chain by seq (correlateRequestBySeq).
        if (store_seq) {
            sweepExpired();
            AddrEntry e;
            e.ptag = ptag;
            e.dyn_seq = store_seq;
            e.base = vaddr;
            e.size = span;
            e.registered = curTick();
            addr_registry[vaddr] = e;
        }

        // FALLBACK (labeled, address-only): the forwarded byte range in
        // the faulted-byte registry for seq-less sites (correlateBlock /
        // noteMemResponse's cache branch). Same registration the pre-R4
        // registerCacheFault path made — now explicitly secondary.
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = vaddr;
            b.byte_end = vaddr + span;
            b.registered = curTick();
            blk_registry[vaddr] = b;
        }
        return ptag;
    }

    // [MDSPEC][R4-5.3] L04-b response-pairing target exchange (see .hh for
    // the ruling and the exchanged-pairing-table correlation design).
    uint64_t
    CHAOSPropagation::registerRespPairFault(
        uint64_t src_seq, long long src_lq_idx, uint64_t src_req_id,
        Addr src_va, unsigned src_size,
        uint64_t tgt_seq, long long tgt_lq_idx, uint64_t tgt_req_id,
        Addr tgt_va, unsigned tgt_size)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;
        const Addr src_span = src_size ? src_size : 1;
        const Addr tgt_span = tgt_size ? tgt_size : 1;

        // inj node (v1 CSV + dual-emit): dyn_inst_seq = the TARGET load (the
        // wrong consumer whose writeback materializes the fault — its
        // resp/lq_complete/taint_reg share this seq, so the L0->L1 edge
        // witness keys fault_id+dyn_inst_seq match); addr = the response's
        // own vaddr; before/after = the pairing mapping (source seq ->
        // target seq — the faulted VALUE of this model; value type is
        // per-model, interpreted with `field`, C12 tick-pair precedent).
        {
            std::ostringstream d;
            d << "family=lsqfwd;field=resp_pairing"
              << ";source_dyn_inst_seq=" << src_seq
              << ";source_lq_idx=" << src_lq_idx
              << ";source_request_id=" << src_req_id
              << ";source_va=" << std::hex << src_va
              << ";target_dyn_inst_seq=" << tgt_seq
              << ";target_lq_idx=" << tgt_lq_idx
              << ";target_request_id=" << tgt_req_id
              << ";target_va=" << tgt_va << std::dec
              << ";old_addr=" << src_seq      // lifted -> before
              << ";new_addr=" << tgt_seq;     // lifted -> after
            writeNode(ptag, "inj", tgt_seq, true,
                      tgt_req_id, tgt_req_id != 0,
                      src_va, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }

        // PRIMARY (seq-bound), the exchanged pairing table. Entry 1:
        // [src_va, +src_span) -> tgt_seq — half 1 joins here (the packet
        // IS src's response, noteMemResponse's inst is the target).
        {
            sweepExpired();
            AddrEntry e;
            e.ptag = ptag;
            e.dyn_seq = tgt_seq;
            e.base = src_va;
            e.size = src_span;
            e.registered = curTick();
            addr_registry[src_va] = e;
        }
        // Entry 2: [tgt_va, +tgt_span) -> src_seq — half 2 joins here (the
        // packet is tgt's response, inst is the source). Skipped on
        // address collision (one map key; the half-1 binding wins and half
        // 2 keeps no seq-bound surface — honest gap, see .hh).
        if (tgt_va != src_va) {
            sweepExpired();
            AddrEntry e2;
            e2.ptag = ptag;
            e2.dyn_seq = src_seq;
            e2.base = tgt_va;
            e2.size = tgt_span;
            e2.registered = curTick();
            addr_registry[tgt_va] = e2;
        }
        // NO blk-registry (address-only) fallback by design — L04's joins
        // are seq-bound only (the 09 sheet forbids address single-key
        // chains; stricter than the labeled-fallback minimum).
        return ptag;
    }

    // [MDSPEC][R4-5.7] S10-a StoreSet SSIT-ID 换值 (see .hh for the ruling:
    // inj node only, no correlate surface — PC-keyed predictor state).
    uint64_t
    CHAOSPropagation::registerStoreSetFault(Addr store_pc, Addr load_pc,
                                            uint64_t true_ssid,
                                            uint64_t new_ssid,
                                            size_t candidate_count)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (v1 CSV + dual-emit): no seq, no addr — the faulted
        // structure is the PC-indexed SSIT mapping. pc lifts to the
        // unified pc field (the corrupted LOAD's PC — the chain's key);
        // before/after = the faulted VALUE of this model, the SSID
        // assignment (true -> substituted; both legal live store-set IDs,
        // workbook 07 实施细则). store_pc and the candidate-set size stay
        // in the detail (the workbook's "保存 source/target 及候选集合").
        {
            std::ostringstream d;
            d << "family=lsqfwd;field=ssid"
              << ";pc=" << std::hex << load_pc << std::dec
              << ";store_pc=" << std::hex << store_pc << std::dec
              << ";ssid_candidates=" << candidate_count
              << ";old_addr=" << true_ssid      // lifted -> before
              << ";new_addr=" << new_ssid;      // lifted -> after
            writeNode(ptag, "inj", 0, false, 0, false,
                      0, false, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // NO addr/seq registry registration by design (see .hh): the
        // downstream chain members (ssit_consult / ssit_violation) are the
        // injector's own PC-keyed emissions, pf_train precedent.
        return ptag;
    }

    // [MDSPEC][R4-4] ArmTLB pfn fault (seq-primary; see .hh for the ruling
    // and the measured pre-R4-4 mis-association this replaces).
    uint64_t
    CHAOSPropagation::registerTlbFault(uint64_t req_seq, Addr va, Addr size,
                                       Addr old_pfn, Addr new_pfn,
                                       Addr old_pa, Addr new_pa,
                                       Addr pa_span, const char *mode,
                                       int entry_way, int candidate_way,
                                       uint64_t walk_id,
                                       const std::string &entry_before,
                                       const std::string &entry_after)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;
        const Addr span = size ? size : 1;
        // pa_span = the entry's page size (entry->size + 1 at the site);
        // pa_mask = its page mask. Fall back to 4 KiB when 0 (defensive —
        // the site always passes entry->size + 1, which is >= 0x1000).
        const Addr pa_span_eff = pa_span ? pa_span : (Addr)0x1000;
        const Addr pa_mask = pa_span_eff - 1;
        const Addr old_page = old_pa & ~pa_mask;
        const Addr new_page = new_pa & ~pa_mask;
        const bool pa_changed = new_page != old_page;

        // inj node (v1 CSV): the L0 injection. addr column = the VA whose
        // translation consumed the corrupted entry; seq columns carry the
        // in-flight request's identity ("" when unstamped).
        {
            std::ostringstream d;
            // [R6-C/GAP-1] The L0 node must say WHAT the injection changed,
            // not only name it. The faulted VALUE of the pfn model is the
            // pfn pair, and the unified emitter's documented lift is
            // old_addr/new_addr -> before/after (registerStoreSetFault /
            // registerInjection convention). Measured before this fix:
            //   kind=inj ... field=pfn_to_mapped_page before= after=
            // — an L0 that cannot say before/after is not evidence that an
            // injection happened. The pfn hex pair now rides BOTH the native
            // old_pfn/new_pfn keys and the lifted old_addr/new_addr keys.
            d << "family=tlb;field=" << mode
              << ";req_seq=" << req_seq
              << ";old_pfn=" << std::hex << old_pfn
              << ";new_pfn=" << new_pfn
              << ";old_addr=" << old_pfn
              << ";new_addr=" << new_pfn
              << ";old_pa=" << old_pa
              << ";new_pa=" << new_pa
              << ";pa_span=" << pa_span_eff
              << ";pa_changed=" << (pa_changed ? 1 : 0) << std::dec;
            writeNode(ptag, "inj", req_seq, req_seq != 0,
                      req_seq, req_seq != 0, va, true, 0, false, 0, false,
                      d.str(), CORR_ORIGIN);
        }

        // PRIMARY (seq-bound): the request whose translation consumed the
        // corrupted entry — its later seq-keyed events join by seq.
        if (req_seq) {
            sweepExpired();
            AddrEntry e;
            e.ptag = ptag;
            e.dyn_seq = req_seq;
            e.base = va;
            e.size = span;
            e.registered = curTick();
            addr_registry[va] = e;
        }

        // FALLBACK (labeled, address-only): the WRONG physical page, only
        // when the corrupted pfn actually redirects the PA. No VA-page
        // registration anymore (that was the pre-R4-4 mis-association
        // source: every later same-VA request joined regardless of seq).
        if (pa_changed) {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = new_page;
            b.byte_end = new_page + pa_span_eff;
            b.registered = curTick();
            blk_registry[new_page] = b;
        }

        // corr label: which arm downstream events join this chain by.
        //   seq_primary  — the seq-bound primary arm is registered
        //   addr_fallback — only the PA-page fallback exists (req_seq==0)
        //   ""           — no correlation surface at all (req_seq==0 AND
        //                  the PA page unchanged): the chain honestly
        //                  stops at this event.
        const char *corr = nullptr;
        if (req_seq)
            corr = CORR_SEQ_PRIMARY;
        else if (pa_changed)
            corr = CORR_ADDR_FALLBACK;

        // T-series L1: the faulted request has completed TLB lookup. The
        // snapshot preserves the selected entry's identity and every field
        // needed to explain why the translation did (or did not) change.
        // notePropEvt links parent_event_id through this ptag.
        std::ostringstream h_va, h_pfn_old, h_pfn_new, h_pa_old, h_pa_new;
        h_va << std::hex << va;
        h_pfn_old << std::hex << old_pfn;
        h_pfn_new << std::hex << new_pfn;
        h_pa_old << std::hex << old_pa;
        h_pa_new << std::hex << new_pa;
        notePropEvt("tlb_lookup", {
            {"fault_id", std::to_string(ptag)},
            {"corr", corr ? corr : ""},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"entry_index", std::to_string(entry_way)},
            {"way", std::to_string(candidate_way)},
            {"field", "post_lookup"},
            {"before", h_pfn_old.str()},
            {"after", h_pfn_new.str()},
            {"state_before", entry_before},
            {"state_after", entry_after},
        });

        // Do not guess the post-translation outcome here: permission and
        // alignment checks run later in MMU::translateMmuOn. Keep the lookup
        // evidence until that completion point reports the actual PA/Fault.
        tlb_pending[{req_seq, va}] = TlbPending{
            ptag, corr ? corr : "", walk_id, entry_way, candidate_way,
            old_pa, new_pa, entry_before, entry_after};

        // Unified L2 event (tlb_pfn): full pfn/pa old-new state. Address
        // fields are bare lowercase hex (registry convention); pfn values
        // hex; dyn_inst_seq/request_id "0" = unstamped (lsq_sendfrag
        // convention).
        notePropEvt("tlb_pfn", {
            {"fault_id", std::to_string(ptag)},
            {"corr", corr ? corr : ""},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"va", h_va.str()},
            {"pa", h_pa_new.str()},
            {"before", h_pfn_old.str()},
            {"after", h_pfn_new.str()},
            {"field", mode},
            {"state_before", h_pa_old.str()},
            {"state_after", h_pa_new.str()},
        });
        return ptag;
    }

    void
    CHAOSPropagation::noteTlbTranslationResult(uint64_t req_seq, Addr va,
                                               bool has_pa, Addr pa,
                                               const char *fault)
    {
        if (!write_log)
            return;
        auto it = tlb_pending.find({req_seq, va});
        if (it == tlb_pending.end())
            return;
        const TlbPending pending = it->second;
        tlb_pending.erase(it); // exactly one completion per injected lookup

        const std::string fault_name = fault ? fault : "NoFault";
        const bool translation_blocked = fault_name != "NoFault";
        // A walk-family fault corrupts the walk handshake, not the entry's
        // pfn, so there is no clean-PA baseline to compare against. Report
        // the real PA/fault honestly, but never claim containment for a
        // completed walk on the strength of an unknown baseline.
        const bool pa_unchanged = has_pa && pa == pending.clean_pa;
        const bool contained = translation_blocked
            || (!pending.walk_fault && pa_unchanged);
        std::ostringstream h_va, h_before, h_after;
        h_va << std::hex << va;
        // The walk family has no clean-PA baseline (the corrupted object is
        // the walk handshake, not an entry pfn). Leave the baseline EMPTY
        // rather than printing a fabricated 0 that would read as a real PA.
        if (!pending.walk_fault)
            h_before << std::hex << pending.clean_pa;
        if (has_pa)
            h_after << std::hex << pa;

        // [R6-A] The fault name rides `outcome` (the tlb_fault convention)
        // and the outcome reason rides `field`. Both are registry fields;
        // notePropEvt DROPS any key outside the emittable registry, so a
        // bespoke `fault=`/`detail=` key would be silently lost from the
        // stream (measured: the L2 Fault and the reason were invisible to
        // the pilot's chain checker before this fix).
        const char *field_reason = translation_blocked
            ? "translation_blocked"
            : pending.walk_fault ? "walk_result_reported"
            : pa_unchanged ? "effective_pa_unchanged"
                           : "effective_pa_changed";

        // [R6] A contained translation is the Masked case: the injected
        // fault was absorbed (effective PA unchanged), refused
        // (permission/alignment fault) or its walk never arrived. Record
        // WHERE (L2) and WHY explicitly, and remember it per chain so the
        // terminus can justify every later layer as N/A(contained) instead
        // of leaving the chain at an unresolvable terminal state.
        const char *reason = contained ? field_reason : "";
        if (contained)
            containment_ptags[pending.ptag] = {"L2", reason};

        notePropEvt("tlb_translate_result", {
            {"fault_id", std::to_string(pending.ptag)},
            {"corr", pending.corr},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"walk_id", std::to_string(pending.walk_id)},
            {"va", h_va.str()},
            {"pa", h_after.str()},
            {"entry_index", std::to_string(pending.entry_way)},
            {"way", std::to_string(pending.candidate_way)},
            {"field", field_reason},
            {"before", h_before.str()},
            {"after", h_after.str()},
            {"state_before", pending.entry_before},
            {"state_after", pending.entry_after},
            {"outcome", fault_name},
            {"detection_layer", contained ? "L2" : ""},
            {"contained", contained ? "1" : "0"},
            {"containment_layer", contained ? "L2" : ""},
            {"containment_reason", reason},
        });
    }

    // [MDSPEC][R4-5.9] T08 walk/fill pairing. Two PROP-EVT nodes for ONE
    // [MDSPEC][R4-10-T05/T06/T07] TLB entry-state / attribute fault. One L0
    // `inj` anchor + one L2 `tlb_state` node. The pfn/PA are not the fault
    // surface here (the mutated field is valid/global/asid/ap/mtype/page-size),
    // so the node carries field + state_before/state_after text instead of the
    // tlb_pfn before/after-pfn payload. corr = seq_primary when the in-flight
    // request is published (the request's later seq-keyed events join by seq);
    // else "" — no correlation surface, the chain honestly stops here (mirrors
    // registerTlbFault's no-surface arm; NO PA-page fallback is invented
    // because this fault does not change the PA).
    uint64_t
    CHAOSPropagation::registerTlbStateFault(uint64_t req_seq, Addr va, Addr size,
                                            const char *field,
                                            const std::string &before,
                                            const std::string &after,
                                            Addr old_pa, Addr new_pa,
                                            int entry_way, int candidate_way,
                                            uint64_t walk_id,
                                            const std::string &entry_before,
                                            const std::string &entry_after)
    {
        if (!write_log)
            return 0;
        (void)size;
        const uint64_t ptag = ++next_ptag;

        std::ostringstream d_inj;
        d_inj << "family=tlb;field=" << field << ";req_seq=" << req_seq
              << ";state_before=" << before << ";state_after=" << after;
        notePropEvt("inj", {
            {"fault_id", std::to_string(ptag)},
            {"corr", CORR_ORIGIN},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"field", field},
            // [R6-C/GAP-1] L0 must record WHAT changed, not only what was
            // injected. The faulted VALUE of the T05/T06/T07 state model is
            // the mutated entry field: `before`/`after` are that field's
            // text before/after the mutation (the injector computed them at
            // the site). Measured before this fix: before= after=.
            {"before", before},
            {"after", after},
            {"evidence_status", "observed"},
            {"detail", d_inj.str()},
        });

        std::ostringstream h_va;
        h_va << std::hex << va;
        const char *corr = req_seq ? CORR_SEQ_PRIMARY : "";
        notePropEvt("tlb_lookup", {
            {"fault_id", std::to_string(ptag)},
            {"corr", corr},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"entry_index", std::to_string(entry_way)},
            {"way", std::to_string(candidate_way)},
            {"field", "post_lookup"},
            {"before", before},
            {"after", after},
            {"state_before", entry_before},
            {"state_after", entry_after},
        });
        notePropEvt("tlb_state", {
            {"fault_id", std::to_string(ptag)},
            {"corr", corr},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"va", h_va.str()},
            {"field", field},
            {"state_before", before},
            {"state_after", after},
        });
        tlb_pending[{req_seq, va}] = TlbPending{
            ptag, corr, walk_id, entry_way, candidate_way,
            old_pa, new_pa, entry_before, entry_after};
        return ptag;
    }

    // walk, sharing walk_id (the pairing key) and ptag (the chain binding):
    //   tlb_walk   — tick = the walk's ISSUE tick (walker entry)
    //   tlb_refill — tick = the refill completion tick; field=lost and
    //                outcome=lost when the refill never arrived (T08-a)
    // The walk_id equality + the two distinct ticks are the pairing
    // evidence; a lost refill is recorded explicitly, never fabricated.
    uint64_t
    CHAOSPropagation::registerTlbWalkPair(uint64_t walk_id, Addr va,
                                          uint64_t req_seq,
                                          uint64_t walk_start_tick,
                                          uint64_t refill_tick,
                                          unsigned level, bool fill_lost,
                                          const char *mode)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;
        std::ostringstream h_va;
        h_va << std::hex << va;

        // [R4-6-T08] L0 anchor for the walk-issue model. The T08 drop IS an
        // injection performed at the page-table walk-issue decision point, so
        // the stream must carry its L0 node. Without it the local chain has no
        // L0 event at all and the chain checker can only report
        // no_l0_fault_applied even though tlb_walk/tlb_refill are in the
        // stream (measured on the R4-6 T08-F0-W9 pilot). Emitted first so the
        // event order is inj -> tlb_walk -> tlb_refill; part of the same
        // fault_id/ptag, so existing joins are unaffected.
        std::ostringstream d_inj;
        d_inj << "family=tlb;site=arm_tlb_walk_issue_drop;field=" << mode
              << ";walk_id=" << walk_id << ";level=L" << level
              << ";req_seq=" << req_seq;
        notePropEvt("inj", {
            {"fault_id", std::to_string(ptag)},
            {"corr", CORR_ORIGIN},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"field", mode},
            // [R6-C/GAP-1] L0 before/after for the walk-issue model: the
            // faulted VALUE is the walk handshake itself — the correct
            // machine issues the walk (before=walk_issued), the corrupted
            // handshake is named by the injector's own mode (after=<mode>,
            // e.g. walk_fill_dup / walk_done_early / walk_stale_result).
            // Measured before this fix: before= after=.
            {"before", "walk_issued"},
            {"after", mode},
            {"evidence_status", "observed"},
            {"detail", d_inj.str()},
        });

        // The walk family starts from a real post-lookup miss. There is no
        // selected entry/way yet, so preserve that absence explicitly.
        notePropEvt("tlb_lookup", {
            {"fault_id", std::to_string(ptag)},
            {"corr", CORR_ORIGIN},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"entry_index", "-1"},
            {"way", "-1"},
            {"field", "post_lookup"},
            {"state_before", "entry=miss"},
            {"state_after", "entry=miss"},
            {"outcome", "miss"},
        });

        std::ostringstream d_walk;
        d_walk << "family=tlb;site=tlb_walk;walk_id=" << walk_id
               << ";level=L" << level << ";start_tick=" << walk_start_tick
               << ";req_seq=" << req_seq;
        notePropEvt("tlb_walk", {
            {"fault_id", std::to_string(ptag)},
            {"corr", CORR_ORIGIN},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"tick", std::to_string(walk_start_tick)},
            {"field", mode},
        });

        // The refill node. field=lost marks the T08-a lost-refill outcome
        // (the refill that never arrived) so downstream joins can prove the
        // walk was unpaired rather than silently absent. [R4-10] the T08-b/c/d
        // sub-models label their outcome explicitly (duplicated / early_done /
        // stale) instead of a bare "refilled", so the pairing is self-describing.
        const std::string mode_s(mode);
        const char *refill_outcome =
            fill_lost ? "lost"
                      : (mode_s == "walk_fill_dup" ? "duplicated"
                         : mode_s == "walk_done_early" ? "early_done"
                         : mode_s == "walk_stale_result" ? "stale"
                                                         : "refilled");
        const char *refill_field = fill_lost ? "lost" : mode;
        std::ostringstream d_refill;
        d_refill << "family=tlb;site=tlb_refill;walk_id=" << walk_id
                 << ";level=L" << level
                 << ";outcome=" << refill_outcome
                 << ";refill_tick=" << refill_tick
                 << ";req_seq=" << req_seq;
        notePropEvt("tlb_refill", {
            {"fault_id", std::to_string(ptag)},
            {"corr", CORR_ORIGIN},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"field", refill_field},
            {"outcome", refill_outcome},
            {"tick", std::to_string(refill_tick)},
        });
        if (fill_lost) {
            // No MMU completion callback can occur after the walk is dropped;
            // close the DAG here with an observed translation block. The
            // reason rides `field` and the outcome rides `outcome` (both
            // registry fields) — a bespoke detail=/fault= key would be
            // dropped by notePropEvt before it ever reached the stream.
            notePropEvt("tlb_translate_result", {
                {"fault_id", std::to_string(ptag)},
                {"corr", CORR_ORIGIN},
                {"walk_id", std::to_string(walk_id)},
                {"va", h_va.str()},
                {"dyn_inst_seq", std::to_string(req_seq)},
                {"request_id", std::to_string(req_seq)},
                {"entry_index", "-1"},
                {"way", "-1"},
                {"field", "walk_refill_lost"},
                {"pa", ""},
                // No entry was ever selected and no PA was materialised: the
                // payload carries the honest empty baseline (same shape as
                // the MMU-completion L2 node) instead of omitting the keys.
                {"before", ""},
                {"after", ""},
                {"state_before", "entry=miss"},
                {"state_after", "entry=miss"},
                {"outcome", "translation_blocked"},
                {"detection_layer", "L2"},
                {"contained", "1"},
            });
        } else {
            // [R6-B/T08-bcd] The walk completed (duplicated / done-early /
            // stale result): the requesting translation still completes in
            // the MMU, so register the pending lookup exactly like the
            // pfn/state faults. The real L2 node (effective PA + Fault) is
            // then emitted by noteTlbTranslationResult at that completion.
            // Without this, the T08-b/c/d chain had no real-PA L2 node.
            tlb_pending[{req_seq, va}] = TlbPending{
                ptag, CORR_ORIGIN, walk_id, -1, -1, 0, 0,
                "entry=miss", "entry=miss", /*walk_fault=*/true};
        }
        return ptag;
    }

    void
    CHAOSPropagation::noteFunnel(const char *site, uint64_t attempted,
                                 uint64_t eligible, uint64_t injected)
    {
        if (!write_log)
            return;
        std::ostringstream d;
        d << "site=" << site << ";attempted=" << attempted
          << ";eligible=" << eligible << ";injected=" << injected;
        // ptag=0: funnel rows are not bound to one chain.
        writeNode(0, "funnel", 0, false, 0, false, 0, false,
                  0, false, 0, false, d.str());
    }

    // ------------------------------------------------------------ pipeline

    uint64_t
    CHAOSPropagation::correlateRequest(uint64_t dyn_seq, Addr addr,
                                       Addr size, const char **corr_out)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        const Addr a_end = addr + size;
        // addrpath registry: range overlap + dyn-inst binding (same
        // semantics as noteMemRequest's stamped path). Seq-bound arm.
        for (const auto &kv : addr_registry) {
            const AddrEntry &e = kv.second;
            if (e.size == 0)
                continue;
            if (addr < e.base + e.size && e.base < a_end
                    && e.dyn_seq == dyn_seq) {
                if (corr_out)
                    *corr_out = CORR_SEQ_PRIMARY;
                return e.ptag;
            }
        }
        // cache faulted-byte registry: range overlap (SE vaddr==paddr).
        // Address-only arm: the labeled fallback ([R4-1-review-I1]).
        for (const auto &kv : blk_registry) {
            const BlkEntry &e = kv.second;
            if (addr < e.byte_end && e.byte_begin < a_end) {
                if (corr_out)
                    *corr_out = CORR_ADDR_FALLBACK;
                return e.ptag;
            }
        }
        return 0;
    }

    uint64_t
    CHAOSPropagation::correlateRequestBySeq(uint64_t dyn_seq,
                                            Addr *base_out,
                                            const char **corr_out)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        for (const auto &kv : addr_registry) {
            const AddrEntry &e = kv.second;
            if (e.dyn_seq == dyn_seq) {
                if (base_out)
                    *base_out = e.base;
                if (corr_out)
                    *corr_out = CORR_SEQ_PRIMARY;
                return e.ptag;
            }
        }
        return 0;
    }

    uint64_t
    CHAOSPropagation::correlateBlock(Addr addr, Addr size, Addr *base_out,
                                     const char **corr_out)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        const Addr a_end = addr + size;
        for (const auto &kv : blk_registry) {
            const BlkEntry &e = kv.second;
            if (addr < e.byte_end && e.byte_begin < a_end) {
                if (base_out)
                    *base_out = e.byte_begin;
                if (corr_out)
                    *corr_out = CORR_ADDR_FALLBACK;
                return e.ptag;
            }
        }
        return 0;
    }

    // ------------------------------------------------ prefetch request id (H5)
    uint64_t
    CHAOSPropagation::notePrefetchRequest(Addr addr, Addr size)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        const Addr base = addr & ~(Addr)(size ? size - 1 : 0);
        const uint64_t pfid = PF_ID_BASE + (++next_pf_request_id);
        PfEntry e;
        e.pf_request_id = pfid;
        e.base = base;
        e.size = size;
        e.registered = curTick();
        pf_registry[base] = e;
        return pfid;
    }

    void
    CHAOSPropagation::registerPtagPrefetch(uint64_t pfid, Addr addr, Addr size)
    {
        if (!write_log || pfid < PF_ID_BASE || size == 0)
            return;
        sweepExpired();
        const Addr base = addr & ~(Addr)(size - 1);
        PfEntry e;
        e.pf_request_id = pfid;
        e.base = base;
        e.size = size;
        e.registered = curTick();
        pf_registry[base] = e;
    }

    uint64_t
    CHAOSPropagation::prefetchRequestId(Addr addr, Addr size, Addr *base_out)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        const Addr a_end = addr + (size ? size : 1);
        for (const auto &kv : pf_registry) {
            const PfEntry &e = kv.second;
            const Addr e_end = e.base + (e.size ? e.size : 1);
            if (addr < e_end && e.base < a_end) {
                if (base_out)
                    *base_out = e.base;
                return e.pf_request_id;
            }
        }
        return 0;
    }

    // ------------------------------------------------- MSHR lifecycle (H4)
    uint64_t
    CHAOSPropagation::noteMshrAlloc(Addr line)
    {
        if (!write_log)
            return 0;
        const uint64_t id = ++next_mshr_id;
        mshr_registry[line] = id;
        return id;
    }

    uint64_t
    CHAOSPropagation::noteMshrLookup(Addr line)
    {
        if (!write_log)
            return 0;
        const auto it = mshr_registry.find(line);
        return it == mshr_registry.end() ? 0 : it->second;
    }

    uint64_t
    CHAOSPropagation::noteMshrFree(Addr line)
    {
        if (!write_log)
            return 0;
        const auto it = mshr_registry.find(line);
        if (it == mshr_registry.end())
            return 0;
        const uint64_t id = it->second;
        mshr_registry.erase(it);
        return id;
    }

    uint64_t
    CHAOSPropagation::noteFill(Addr line)
    {
        (void)line;                    // reserved for per-line fill accounting
        if (!write_log)
            return 0;
        return ++next_fill_id;
    }

    void
    CHAOSPropagation::registerPtagBlock(uint64_t ptag, Addr byte_begin,
                                        Addr byte_end)
    {
        if (!write_log || ptag == 0 || byte_end <= byte_begin)
            return;
        sweepExpired();
        BlkEntry e;
        e.ptag = ptag;
        e.byte_begin = byte_begin;
        e.byte_end = byte_end;
        e.registered = curTick();
        blk_registry[byte_begin] = e;
    }

    uint64_t
    CHAOSPropagation::noteMemRequest(const char *site, uint64_t dyn_seq,
                                     const RequestPtr &req,
                                     const char **corr_out)
    {
        if (!write_log || !req || !req->hasVaddr())
            return 0;
        sweepExpired();
        const Addr v = req->getVaddr();
        const Addr v_end = v + (Addr)req->getSize();

        // addrpath registry: range overlap + dyn-inst binding. The request
        // seq must be stamped (getReqInstSeqNum asserts otherwise — gem5
        // v25 request.hh); an unstamped request falls back to overlap-only
        // (documented: split _mainReq is not seq-stamped).
        const bool stamped = req->hasInstSeqNum();
        const uint64_t req_seq = stamped ? req->getReqInstSeqNum() : 0;
        uint64_t matched = 0;
        for (const auto &kv : addr_registry) {
            const AddrEntry &e = kv.second;
            if (e.size == 0)
                continue;                       // address-only marker
            const Addr e_end = e.base + e.size;
            if (v >= e_end || e.base >= v_end)
                continue;                       // no overlap
            if (stamped && req_seq != e.dyn_seq)
                continue;                       // not the faulting inst
            if (corr_out && !*corr_out)
                *corr_out = CORR_SEQ_PRIMARY;   // seq-bound arm
            std::ostringstream d;
            d << "site=" << site << ";family=addrpath;size="
              << req->getSize();
            writeNode(e.ptag, "mem_req", dyn_seq, true,
                      req_seq, stamped, v, true, 0, false, 0, false, d.str(),
                      CORR_SEQ_PRIMARY);
            if (!matched)
                matched = e.ptag;
        }

        // cache faulted-byte registry: range overlap (SE vaddr==paddr).
        // Address-only arm: the labeled fallback ([R4-1-review-I1]).
        for (const auto &kv : blk_registry) {
            const BlkEntry &e = kv.second;
            if (v >= e.byte_end || e.byte_begin >= v_end)
                continue;
            if (corr_out && !*corr_out)
                *corr_out = CORR_ADDR_FALLBACK;
            std::ostringstream d;
            d << "site=" << site << ";family=cache;size=" << req->getSize();
            writeNode(e.ptag, "mem_req", dyn_seq, true,
                      req_seq, stamped, v, true, 0, false, 0, false, d.str(),
                      CORR_ADDR_FALLBACK);
            if (!matched)
                matched = e.ptag;
        }
        // [MDSPEC][H1] first matched chain id for the unified lsq_sendfrag
        // event emitted by the caller (lsq.cc sendFragmentToTranslation).
        return matched;
    }

    void
    CHAOSPropagation::noteMemResponse(o3::DynInst *inst, Packet *pkt,
                                      bool wb_to_reg)
    {
        if (!write_log || !inst || !pkt)
            return;
        sweepExpired();

        uint64_t hit_ptag = 0;
        const char *hit_family = nullptr;
        const char *hit_corr = nullptr;   // [R4-1-review-I1] matched arm

        // addrpath: the response's own Request vaddr range vs the registry,
        // bound to this instruction (the faulting load itself).
        if (pkt->req && pkt->req->hasVaddr()) {
            const Addr v = pkt->req->getVaddr();
            const Addr v_end = v + (Addr)pkt->req->getSize();
            for (const auto &kv : addr_registry) {
                const AddrEntry &e = kv.second;
                if (e.size == 0)
                    continue;
                if (v < e.base + e.size && e.base < v_end
                        && e.dyn_seq == inst->seqNum) {
                    hit_ptag = e.ptag;
                    hit_family = "addrpath";
                    hit_corr = CORR_SEQ_PRIMARY;
                    break;
                }
            }
        }
        // cache: the delivered byte range vs the faulted-byte registry.
        if (!hit_ptag) {
            const Addr a = pkt->getAddr();
            const Addr a_end = a + (Addr)pkt->getSize();
            for (const auto &kv : blk_registry) {
                const BlkEntry &e = kv.second;
                if (a < e.byte_end && e.byte_begin < a_end) {
                    hit_ptag = e.ptag;
                    hit_family = "cache";
                    hit_corr = CORR_ADDR_FALLBACK;
                    break;
                }
            }
        }
        if (!hit_ptag)
            return;

        // [MDSPEC][R6/A10] A load that received the wrong response but is
        // then SQUASHED has its result discarded and the instruction
        // replayed: the corruption is contained by the squash/replay
        // mechanism. This case used to emit NOTHING at all (the old
        // `isSquashed()` early-return fired before any emission), so a
        // contain-by-squash outcome could never fire and the chain looked
        // like it silently vanished. Record the containment explicitly.
        if (inst->isSquashed()) {
            std::ostringstream h_va, h_pa;
            if (pkt->req && pkt->req->hasVaddr())
                h_va << std::hex << pkt->req->getVaddr();
            h_pa << std::hex << pkt->getAddr();
            notePropEvt("squash_masked", {
                {"fault_id", std::to_string(hit_ptag)},
                {"corr", hit_corr ? hit_corr : ""},
                {"dyn_inst_seq", std::to_string(inst->seqNum)},
                {"va", h_va.str()},
                {"pa", h_pa.str()},
                {"field", "squashed_load"},
                {"outcome", "masked"},
                {"detection_layer", "L4"},
                {"contained", "1"},
                {"containment_layer", "L4"},
                {"containment_reason", "squash_replay"},
            });
            containment_ptags[hit_ptag] = {"L4", "squash_replay"};
            return;
        }

        // resp node: the memory response delivering the fault.
        const uint64_t req_seq =
            (pkt->req && pkt->req->hasInstSeqNum())
                ? pkt->req->getReqInstSeqNum() : 0;
        {
            std::ostringstream d;
            d << "family=" << hit_family << ";size=" << pkt->getSize();
            if (pkt->hasData()) {
                d << ";data_fnv=" << std::hex
                  << fnv1a64(pkt->getPtr<uint8_t>(), pkt->getSize())
                  << std::dec;
            }
            if (inst->getFault() != NoFault)
                d << ";fault=" << inst->getFault()->name();
            writeNode(hit_ptag, "resp", inst->seqNum, true,
                      req_seq, req_seq != 0, pkt->getAddr(), true,
                      0, false, 0, false, d.str(), hit_corr);
        }

        // [MDSPEC][H7] unified lq_complete event (spec sheet 9: LQ
        // lifecycle — the response returned for LQ entry lqIdx; L3).
        // Load-side discriminator = wb_to_reg (needWBToRegister — the SAME
        // condition gating taint_reg below). lqIdx alone is UNSOUND: stores
        // keep a stale lqIdx from DynInst-pool reuse (empirically hit on
        // sq_forward dyn133 store with residual lq_idx=3).
        if (wb_to_reg && inst->lqIdx >= 0) {
            std::ostringstream h7_va, h7_pa;
            if (pkt->req && pkt->req->hasVaddr())
                h7_va << std::hex << pkt->req->getVaddr();
            h7_pa << std::hex << pkt->getAddr();
            notePropEvt("lq_complete", {
                {"fault_id", std::to_string(hit_ptag)},
                {"dyn_inst_seq", std::to_string(inst->seqNum)},
                {"lq_idx", std::to_string((long long)inst->lqIdx)},
                {"va", h7_va.str()},
                {"pa", h7_pa.str()},
                {"request_id", req_seq ? std::to_string(req_seq)
                                       : std::string("0")},
                // [R4-1-review-I1] which correlate arm joined this event
                {"corr", hit_corr ? hit_corr : ""},
            });
        }

        // taint_reg: exactly the condition under which LSQUnit::writeback
        // performs completeAcc (needWBToRegister + NoFault) — the load's
        // dest phys regs receive the fault-delivered data.
        if (!wb_to_reg || inst->getFault() != NoFault)
            return;
        const int ndest = (int)inst->numDestRegs();
        for (int i = 0; i < ndest; ++i) {
            const PhysRegIdPtr phys = inst->renamedDestIdx(i);
            if (!phys)
                continue;
            const std::pair<int, uint32_t> key(phys->classValue(),
                                               phys->index());
            TaintEntry te;
            te.ptag = hit_ptag;
            te.taintor_seq = inst->seqNum;
            std::ostringstream d;
            d << "class=" << regClassName(phys->classValue())
              << ";dest_idx=" << i
              // [MDSPEC][R6/A4] The faulted VALUE of this node is the
              // physical cell's taint state: the cell held a legitimate
              // (clean) value and now holds fault-delivered data. The pair
              // rides the documented old_addr/new_addr → before/after lift
              // so the T-series stream can show WHAT changed (C12 tick pair
              // / L04 seq pair precedent). Measured before this fix:
              // kind=taint_reg ... before= after=.
              << ";old_addr=clean;new_addr=tainted";
            writeNode(hit_ptag, "taint_reg", inst->seqNum, true,
                      req_seq, req_seq != 0, pkt->getAddr(), true,
                      phys->index(), true,
                      inst->destRegIdx(i).index(), true, d.str(), hit_corr);
            // [MDSPEC][R6/A6] Remember WHICH event established this taint:
            // writeNode's dual-emit used event_id == next_node_id (pre-
            // increment), so the node just written is next_node_id - 1.
            te.src_event = next_node_id - 1;
            taint_set[key] = te;
        }
    }

    void
    CHAOSPropagation::noteCommit(ThreadID tid, o3::DynInst *head_inst)
    {
        if (!write_log || !head_inst)
            return;

        const uint64_t pc = head_inst->pcState().instAddr();
        uint64_t first_consumed_ptag = 0;
        bool any_consumer = false;
        bool self_taint = false;
        uint64_t self_taint_ptag = 0;
        // [MDSPEC][R6/A6] event_id of the last consumer node emitted above —
        // the taint source for the dests it re-taints (see below).
        uint64_t last_consumer_evt = 0;

        // Sources: a tainted source phys reg = this commit consumes a
        // fault-delivered value → consumer node.
        const int nsrc = (int)head_inst->numSrcRegs();
        for (int i = 0; i < nsrc; ++i) {
            const PhysRegIdPtr phys = head_inst->renamedSrcIdx(i);
            if (!phys)
                continue;
            const auto it = taint_set.find(
                std::make_pair(phys->classValue(), phys->index()));
            if (it == taint_set.end())
                continue;
            any_consumer = true;
            if (!first_consumed_ptag)
                first_consumed_ptag = it->second.ptag;
            std::ostringstream d;
            d << "class=" << regClassName(phys->classValue())
              << ";src_idx=" << i
              // [MDSPEC][R6/A6] A consumer does NOT descend from the previous
              // event of the chain: it descends from the event that
              // established the taint it consumed. Naming that event is what
              // turns the chain into a real DAG (one source → many
              // consumers) instead of the degenerate linear list the single
              // ptag_last_event cursor produced. parent_event_id is a
              // registry field, so the dual-emit honours this override.
              << ";parent_event_id=" << it->second.src_event
              << ";pc=" << std::hex << pc << std::dec;
            writeNode(it->second.ptag, "consumer", head_inst->seqNum, true,
                      0, false, 0, false, phys->index(), true,
                      head_inst->srcRegIdx(i).index(), true, d.str(),
                      CORR_TAINT_PROP, (int)tid);
            // The just-emitted consumer node is the taint source for any
            // dest it re-taints below.
            last_consumer_evt = next_node_id - 1;
        }

        // Dests: is this the faulting load itself committing its tainted
        // dest (taintor_seq == own seqNum)? That commit is the first
        // architectural materialization of the fault.
        const int ndest = (int)head_inst->numDestRegs();
        for (int i = 0; i < ndest; ++i) {
            const PhysRegIdPtr phys = head_inst->renamedDestIdx(i);
            if (!phys)
                continue;
            const auto it = taint_set.find(
                std::make_pair(phys->classValue(), phys->index()));
            if (it != taint_set.end()
                    && it->second.taintor_seq == head_inst->seqNum) {
                self_taint = true;
                if (!self_taint_ptag)
                    self_taint_ptag = it->second.ptag;
            }
        }

        // errant_commit: once per run — the first commit on a fault path
        // (the faulting load itself, or the first consumer). Field-level
        // "first wrong architectural commit" stays L2 commit_diff's
        // first_errant_commit (authoritative); this node is the
        // propagation-view alignment point (same seqNum space).
        if (!errant_commit_seen && (any_consumer || self_taint)) {
            const uint64_t ptag = any_consumer ? first_consumed_ptag
                                               : self_taint_ptag;
            std::ostringstream d;
            // [R6-C/GAP-2] This IS the observable L5 detection: the wrong
            // value reached architectural state (a committed instruction
            // consumed the tainted value, or the faulting load committed its
            // tainted dest). Measured before this fix:
            //   kind=errant_commit corr=taint_prop dyn_inst_seq=391
            //   detection_layer= outcome=
            // — the real detection event named neither its layer nor its
            // outcome, while the lifecycle chain_end node carried the only
            // (non-evidentiary) L5-ish fields. The ruling: L5 evidence must
            // be THIS event, so it must name its layer and outcome. Both keys
            // are registry fields, so the dual-emit lifts them verbatim.
            d << "trigger=" << (any_consumer ? "first_consumer"
                                             : "faulting_load_commit")
              << ";detection_layer=L5"
              << ";outcome=errant_commit"
              << ";pc=" << std::hex << pc << std::dec;
            writeNode(ptag, "errant_commit", head_inst->seqNum, true,
                      0, false, 0, false, 0, false, 0, false, d.str(),
                      CORR_TAINT_PROP, (int)tid);
            errant_commit_seen = true;
            // [MDSPEC][R6] Bind the observed errant commit to its own chain
            // so the L5 chain_end node can report it (see .hh).
            errant_ptags.insert(ptag);
        }

        // Propagation rules (see .hh):
        //  - consumer commits → its dests now carry the wrong value
        //    (re-taint under the consumed chain's ptag);
        //  - the tainting load's own commit → keep its dest taint;
        //  - an UNRELATED producer committing onto a tainted phys cell →
        //    clean overwrite, the stale taint dies (phys-recycling bound).
        if (any_consumer) {
            for (int i = 0; i < ndest; ++i) {
                const PhysRegIdPtr phys = head_inst->renamedDestIdx(i);
                if (!phys)
                    continue;
                TaintEntry te;
                te.ptag = first_consumed_ptag;
                te.taintor_seq = head_inst->seqNum;
                // [R6/A6] the re-taint is established by the consumer node.
                te.src_event = last_consumer_evt;
                taint_set[std::make_pair(phys->classValue(),
                                         phys->index())] = te;
            }
        } else if (!self_taint) {
            for (int i = 0; i < ndest; ++i) {
                const PhysRegIdPtr phys = head_inst->renamedDestIdx(i);
                if (!phys)
                    continue;
                taint_set.erase(std::make_pair(phys->classValue(),
                                               phys->index()));
            }
        }
    }

} // namespace gem5
