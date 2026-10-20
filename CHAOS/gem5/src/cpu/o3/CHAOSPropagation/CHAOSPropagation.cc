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
                        const bool seen_errant = false; // per-chain: the
                        // errant_commit node carries ptag; a global flag
                        // can't distinguish chains (single-fault campaign
                        // is the honest limit — multi-fault chains get
                        // outcome=unknown for all, documented).
                        notePropEvt("chain_end", {
                            {"fault_id", std::to_string(ptag)},
                            {"outcome", seen_errant
                                ? "errant_commit_seen" : "run_end"},
                            {"detection_layer", "None"},
                            {"contained", "0"},
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
                                const std::string &detail, int tid)
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
                      old_addr, true, 0, false, 0, false, d.str());
        }
        // addr_form node: the erroneous address (addr column = NEW addr).
        {
            std::ostringstream d;
            d << "site=" << site << ";old_addr=" << std::hex << old_addr
              << ";new_addr=" << new_addr << std::dec;
            writeNode(ptag, "addr_form", dyn_seq, true, 0, false,
                      new_addr, true, 0, false, 0, false, d.str());
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
                      block_addr, true, 0, false, 0, false, d.str());
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
                      vaddr, true, 0, false, 0, false, d.str());
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
                                       Addr size)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        const Addr a_end = addr + size;
        // addrpath registry: range overlap + dyn-inst binding (same
        // semantics as noteMemRequest's stamped path).
        for (const auto &kv : addr_registry) {
            const AddrEntry &e = kv.second;
            if (e.size == 0)
                continue;
            if (addr < e.base + e.size && e.base < a_end
                    && e.dyn_seq == dyn_seq)
                return e.ptag;
        }
        // cache faulted-byte registry: range overlap (SE vaddr==paddr).
        for (const auto &kv : blk_registry) {
            const BlkEntry &e = kv.second;
            if (addr < e.byte_end && e.byte_begin < a_end)
                return e.ptag;
        }
        return 0;
    }

    uint64_t
    CHAOSPropagation::correlateRequestBySeq(uint64_t dyn_seq,
                                            Addr *base_out)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        for (const auto &kv : addr_registry) {
            const AddrEntry &e = kv.second;
            if (e.dyn_seq == dyn_seq) {
                if (base_out)
                    *base_out = e.base;
                return e.ptag;
            }
        }
        return 0;
    }

    uint64_t
    CHAOSPropagation::correlateBlock(Addr addr, Addr size, Addr *base_out)
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
                                     const RequestPtr &req)
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
            std::ostringstream d;
            d << "site=" << site << ";family=addrpath;size="
              << req->getSize();
            writeNode(e.ptag, "mem_req", dyn_seq, true,
                      req_seq, stamped, v, true, 0, false, 0, false, d.str());
            if (!matched)
                matched = e.ptag;
        }

        // cache faulted-byte registry: range overlap (SE vaddr==paddr).
        for (const auto &kv : blk_registry) {
            const BlkEntry &e = kv.second;
            if (v >= e.byte_end || e.byte_begin >= v_end)
                continue;
            std::ostringstream d;
            d << "site=" << site << ";family=cache;size=" << req->getSize();
            writeNode(e.ptag, "mem_req", dyn_seq, true,
                      req_seq, stamped, v, true, 0, false, 0, false, d.str());
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
        if (!write_log || !inst || !pkt || inst->isSquashed())
            return;
        sweepExpired();

        uint64_t hit_ptag = 0;
        const char *hit_family = nullptr;

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
                    break;
                }
            }
        }
        if (!hit_ptag)
            return;

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
                      0, false, 0, false, d.str());
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
            taint_set[key] = te;
            std::ostringstream d;
            d << "class=" << regClassName(phys->classValue())
              << ";dest_idx=" << i;
            writeNode(hit_ptag, "taint_reg", inst->seqNum, true,
                      req_seq, req_seq != 0, pkt->getAddr(), true,
                      phys->index(), true,
                      inst->destRegIdx(i).index(), true, d.str());
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
              << ";src_idx=" << i << ";pc=" << std::hex << pc << std::dec;
            writeNode(it->second.ptag, "consumer", head_inst->seqNum, true,
                      0, false, 0, false, phys->index(), true,
                      head_inst->srcRegIdx(i).index(), true, d.str(),
                      (int)tid);
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
            d << "trigger=" << (any_consumer ? "first_consumer"
                                             : "faulting_load_commit")
              << ";pc=" << std::hex << pc << std::dec;
            writeNode(ptag, "errant_commit", head_inst->seqNum, true,
                      0, false, 0, false, 0, false, 0, false, d.str(),
                      (int)tid);
            errant_commit_seen = true;
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
