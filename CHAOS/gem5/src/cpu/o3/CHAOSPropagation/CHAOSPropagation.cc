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
#include "cpu/o3/CHAOSPropagation/store_chain_rules.hh"

// v3.2.12 propagation-closure round: pure, host-testable per-model rules
// (tests/test_fw02_decision.cc, test_sq01_chain.cc, test_sq03_effect.cc,
// test_sp05_stage.cc compile these same headers with plain g++).
#include "cpu/o3/CHAOSLSQFwd/fw02_rules.hh"   // FW02 decision/squash rules
#include "cpu/o3/CHAOSLSQFwd/sq01_rules.hh"    // SQ01 chain grading
#include "cpu/o3/CHAOSLSQFwd/sq03_rules.hh"    // SQ03 effect grading
#include "cpu/o3/CHAOSLSQFwd/sp05_rules.hh"    // SP05 stage grading

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
          replay_all(p.traceReplayAll),
          addr_expiry_ticks(p.addrExpiryTicks)
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

            // Normal-exit trailer: gzclose writes the gzip trailer. MUST be
            // an exit callback, not the destructor — gem5's exit path does
            // not reliably run SimObject destructors (CHAOSMicroSnap
            // measurement; CHAOSProbe exit-callback precedent). Aborted runs
            // never get here: they keep the Z_SYNC_FLUSH-ed truncated
            // stream, which tools/lsu_l3_propagation.py salvages.
            // v3.2.12: BEFORE closing, emit the deferred consolidated chain
            // records (sq01_chain / sq03_effect / sp05_stage) for fault
            // stores whose chain never closed — no reload, no consumer — so
            // the honest no-downstream-effect terminal exists on the trace.
            // This callback is registered FIRST, so anything registered
            // later still runs after the close; all deferred records must
            // be written here, inside this callback, before gzclose.
            registerExitCallback([this]() {
                if (gz_file) {
                    writeDeferredChainRecords();
                    gzclose(gz_file);
                    gz_file = nullptr;
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
    }

    uint64_t
    CHAOSPropagation::writeNode(uint64_t ptag, const char *kind,
                                uint64_t dyn_seq, bool has_seq,
                                uint64_t request_id, bool has_req_id,
                                Addr addr, bool has_addr,
                                uint64_t phys_reg, bool has_phys,
                                uint64_t arch_reg, bool has_arch,
                                const std::string &detail, Tick tick)
    {
        if (!write_log || !gz_file)
            return 0;
        const uint64_t node_id = next_node_id;
        // `tick` lets a request-time node carry the true request issue time;
        // 0 means "now".
        const Tick node_tick = tick ? tick : curTick();
        // Numeric fields without a value are EMPTY strings (pinned contract).
        std::ostringstream row;
        row << node_id << ',' << node_tick << ',' << ptag << ','
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
                  (unsigned long long)node_id, kind);
        // Crash durability (W2.1 contract): one flush per node — an aborted
        // run keeps every completed node readable (trailer-less prefix).
        gzflush(gz_file, Z_SYNC_FLUSH);
        ++next_node_id;
        return node_id;
    }

    std::string
    CHAOSPropagation::bytesToHex(const uint8_t *p, unsigned n) const
    {
        if (!p || n == 0)
            return "";
        // Keep JSONL bounded: full bytes for <=32B, length+hash otherwise.
        if (n > 32)
            return "len" + std::to_string(n);
        static const char *hx = "0123456789abcdef";
        std::string out;
        out.reserve(n * 2);
        for (unsigned i = 0; i < n; ++i) {
            out.push_back(hx[p[i] >> 4]);
            out.push_back(hx[p[i] & 0xf]);
        }
        return out;
    }

    std::string
    CHAOSPropagation::regValueHash(o3::DynInst *inst, PhysRegIdPtr phys,
                                   ThreadID tid, uint64_t *value_out,
                                   unsigned *bytes_out) const
    {
        if (!o3cpu || !inst || !phys || phys->classValue() < 0)
            return "";
        // PhysRegFile::getReg(PhysRegIdPtr) returns a single RegVal and only
        // supports the scalar classes below (regfile.hh). A vector/matrix
        // consumer is still a real edge; its value hash stays null instead of
        // panicking the simulator (FW02-R03 hit class type 2 = VecRegClass).
        const RegClassType rc = phys->classValue();
        if (rc != IntRegClass && rc != FloatRegClass &&
            rc != VecElemClass && rc != CCRegClass)
            return "";
        RegVal value = o3cpu->getReg(phys, tid);
        if (value_out) *value_out = (uint64_t)value;
        if (bytes_out) *bytes_out = sizeof(RegVal);
        const uint64_t h = fnv1a64(&value, sizeof(value));
        std::ostringstream out;
        out << std::hex << h << std::dec;
        return out.str();
    }

    std::string
    CHAOSPropagation::fnvHex(const uint8_t *p, unsigned n) const
    {
        std::ostringstream s;
        s << std::hex << fnv1a64(p, n) << std::dec;
        return s.str();
    }

    void
    CHAOSPropagation::writeEdgeRow(uint64_t ptag, uint64_t source_node,
                                   uint64_t destination_node,
                                   uint64_t producer_seq, uint64_t consumer_seq,
                                   const std::string &source_hash,
                                   const std::string &destination_hash,
                                   const char *edge_type)
    {
        if (!write_log || !gz_file)
            return;
        std::ostringstream d;
        d << "source_event_id=" << source_node
          << ";destination_event_id=" << destination_node
          << ";producer_inst_seq=" << producer_seq
          << ";consumer_inst_seq=" << consumer_seq
          << ";source_value_hash=" << (source_hash.empty() ? "null" : source_hash)
          << ";destination_value_hash="
          << (destination_hash.empty() ? "null" : destination_hash)
          << ";edge_type=" << edge_type;
        // A prop_edge row is a real edge record, not a ptag-order artifact.
        const uint64_t node_id = next_node_id++;
        std::ostringstream row;
        row << node_id << ',' << curTick() << ',' << ptag << ",prop_edge,";
        row << consumer_seq << ",,,";  // dyn_seq, request_id, addr
        row << ",,";                   // phys, arch
        row << d.str() << '\n';
        const std::string s = row.str();
        if (gzwrite(gz_file, s.data(), (unsigned)s.size()) != (int)s.size())
            panic("CHAOSPropagation: edge write failed (node %llu)",
                  (unsigned long long)node_id);
        gzflush(gz_file, Z_SYNC_FLUSH);
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
        fault_seqs.insert(dyn_seq);

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

    void
    CHAOSPropagation::noteNoChange(const char *site, uint64_t dyn_seq,
                                   Addr addr, const char *mode,
                                   uint64_t execution_attempt_id,
                                   uint64_t replay_generation)
    {
        if (!write_log)
            return;
        std::ostringstream d;
        d << "site=" << site << ";mode=" << mode
          << ";old_addr=" << std::hex << addr
          << ";new_addr=" << addr << std::dec
          << ";value_changed=0"
          << ";execution_attempt_id=" << execution_attempt_id
          << ";replay_generation=" << replay_generation;
        writeNode(0, "inj_nochange", dyn_seq, true, 0, false, addr, true,
                  0, false, 0, false, d.str());
    }

    void
    CHAOSPropagation::noteStoreDataInjection(uint64_t dyn_seq, uint64_t idx,
                                             uint64_t gen, Addr vaddr,
                                             unsigned size, uint8_t old_byte,
                                             uint8_t new_byte,
                                             const char *mode)
    {
        if (!write_log)
            return;
        const uint64_t ptag = ++next_ptag;
        fault_seqs.insert(dyn_seq);
        std::ostringstream d;
        d << "site=lsq_write_sq_entry;mode=" << mode
          << ";queue=SQ;index=" << idx
          << ";generation=" << gen
          << ";size=" << size
          << ";addr=0x" << std::hex << vaddr << std::dec
          << ";old_byte=0x" << std::hex << (unsigned)old_byte
          << ";new_byte=0x" << (unsigned)new_byte << std::dec
          << ";value_changed=1";
        writeNode(ptag, "inj_store_data", dyn_seq, true, 0, false,
                  vaddr, true, 0, false, 0, false, d.str());

        FaultStoreEntry e;
        e.ptag = ptag;
        e.dyn_seq = dyn_seq;
        e.base = vaddr;
        e.size = size;
        e.idx = idx;
        e.gen = gen;
        e.byte_begin = vaddr;
        e.byte_end = vaddr + 1;   // SQ01 corrupts data[0] (lowest byte)
        e.family = "store_data";
        e.registered = curTick();
        // v3.2.12: byte0 before/after feed the sq01_chain record's
        // data_before/data_after (the divergence evidence, brief task 11).
        e.data_byte_before = old_byte;
        e.data_byte_after = new_byte;
        fault_store_registry[dyn_seq] = e;
    }

    uint64_t
    CHAOSPropagation::chaosBeMask(const std::vector<bool> &be)
    {
        uint64_t m = 0;
        for (unsigned i = 0; i < be.size() && i < 64; ++i) {
            if (be[i])
                m |= (uint64_t)1 << i;
        }
        return m;
    }

    uint64_t
    CHAOSPropagation::noteStoreBEInjection(uint64_t dyn_seq, uint64_t idx,
                                           uint64_t gen, Addr vaddr,
                                           unsigned size, uint64_t old_mask,
                                           uint64_t new_mask,
                                           const uint8_t *store_data)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;
        fault_seqs.insert(dyn_seq);
        const uint64_t fnv = store_data ? fnv1a64(store_data, size) : 0;
        std::ostringstream fnh;
        if (store_data)
            fnh << std::hex << fnv << std::dec;
        std::ostringstream d;
        d << "site=lsq_pushRequest;family=byte_enable;fault_model=DA04"
          << ";size=" << size
          << ";old_be=0x" << std::hex << old_mask
          << ";new_be=0x" << new_mask << std::dec
          << ";changed_bit=0"
          << ";addr_before=0x" << std::hex << vaddr
          << ";addr_after=0x" << vaddr << std::dec
          << ";size_before=" << size << ";size_after=" << size
          << ";store_data_fnv=" << (store_data ? fnh.str() : "null")
          << ";store_data_hex="
          << (store_data ? bytesToHex(store_data, size) : "null")
          << ";sq_entry_id=" << idx
          << ";entry_generation=" << gen;
        writeNode(ptag, "inj_store_be", dyn_seq, true, 0, false,
                  vaddr, true, 0, false, 0, false, d.str());

        FaultStoreEntry e;
        e.ptag = ptag;
        e.dyn_seq = dyn_seq;
        e.base = vaddr;
        e.size = size;
        e.idx = idx;
        e.gen = gen;
        e.byte_begin = vaddr;
        e.byte_end = vaddr + 1;   // DA04 clears lane 0 (lowest byte) only
        e.family = "byte_enable";
        e.old_mask = "0x" + std::to_string(old_mask);
        e.new_mask = "0x" + std::to_string(new_mask);
        e.data_fnv = store_data ? fnh.str() : "";
        e.data_hex = store_data ? bytesToHex(store_data, size) : "";
        e.registered = curTick();
        fault_store_registry[dyn_seq] = e;
        return ptag;
    }

    void
    CHAOSPropagation::noteStoreWriteback(uint64_t dyn_seq, uint64_t idx,
                                         uint64_t gen, Addr vaddr,
                                         unsigned size,
                                         const std::vector<bool> &be,
                                         const uint8_t *data)
    {
        if (!write_log)
            return;
        auto it = fault_store_registry.find(dyn_seq);
        if (it == fault_store_registry.end())
            return;
        FaultStoreEntry &e = it->second;
        const uint64_t fnv = data ? fnv1a64(data, size) : 0;
        std::ostringstream d;
        d << "site=lsq_writebackStores;family=" << e.family
          << ";size=" << size
          << ";be_mask=";
        if (be.empty())
            d << "null";
        else
            d << "0x" << std::hex << chaosBeMask(be) << std::dec;
        d << ";data_fnv=" << (data ? fnv : 0)
          << ";data_hex=" << (data ? bytesToHex(data, size) : "null")
          << ";sq_entry_id=" << idx
          << ";entry_generation=" << gen
          << ";addr=0x" << std::hex << vaddr << std::dec;
        writeNode(e.ptag, "store_wb", dyn_seq, true, 0, false,
                  vaddr, true, 0, false, 0, false, d.str());
        // v3.2.12 (task 11): the drained bytes ARE the corrupted bytes —
        // this hash is the sq01_chain record's mem_write_hash (the hash of
        // the store data as it left the SQ, i.e. hash(data_after)).
        if (data && std::string(e.family) == "store_data") {
            std::ostringstream fh;
            fh << std::hex << fnv << std::dec;
            e.data_fnv = fh.str();
        }
    }

    void
    CHAOSPropagation::noteStoreMemWrite(const PacketPtr &pkt, Addr blk_addr,
                                        const uint8_t *packet_data,
                                        const std::vector<uint8_t> &before,
                                        const std::vector<uint8_t> &after,
                                        unsigned offset)
    {
        if (!write_log || !pkt || !pkt->req)
            return;
        if (!pkt->req->hasInstSeqNum())
            return;
        auto it = fault_store_registry.find(pkt->req->getReqInstSeqNum());
        if (it == fault_store_registry.end())
            return;
        FaultStoreEntry &e = it->second;
        const unsigned n = after.size();
        if (n == 0 || before.size() != n || !packet_data)
            return;
        const std::vector<bool> be = pkt->req->getByteEnable();
        bool enabled_written = true;
        bool disabled_unchanged = true;
        for (unsigned i = 0; i < n; ++i) {
            const bool en = i < be.size() ? be[i] : true;
            if (en && after[i] != packet_data[i])
                enabled_written = false;
            if (!en && after[i] != before[i])
                disabled_unchanged = false;
        }
        const uint64_t packet_fnv = fnv1a64(packet_data, n);
        std::ostringstream d;
        d << "site=BaseCache::updateBlockData;family=" << e.family
          << ";blk_addr=0x" << std::hex << blk_addr << std::dec
          << ";offset=" << offset << ";size=" << n
          << ";be_mask=0x" << std::hex << chaosBeMask(be) << std::dec
          << ";packet_data_fnv=" << packet_fnv
          << ";packet_data_hex=" << bytesToHex(packet_data, n)
          << ";before_hex=" << bytesToHex(before.data(), n)
          << ";after_hex=" << bytesToHex(after.data(), n)
          << ";enabled_written=" << (enabled_written ? 1 : 0)
          << ";disabled_unchanged=" << (disabled_unchanged ? 1 : 0)
          << ";lane0_packet=0x" << std::hex << (unsigned)packet_data[0]
          << ";lane0_before=0x" << (unsigned)before[0]
          << ";lane0_after=0x" << (unsigned)after[0] << std::dec;
        writeNode(e.ptag, "store_mem", e.dyn_seq, true, 0, false,
                  blk_addr, true, 0, false, 0, false, d.str());
        // v3.2.4 review fix: from this tick on, a later load can actually
        // observe the faulted byte in memory.
        e.written_tick = curTick();
    }

    void
    CHAOSPropagation::noteStoreWrite(const PacketPtr &pkt)
    {
        if (!write_log || !pkt || !pkt->req || !pkt->req->hasVaddr())
            return;
        const uint64_t seq = pkt->req->hasInstSeqNum()
            ? pkt->req->getReqInstSeqNum() : 0;
        const Addr a = pkt->req->getVaddr();
        const Addr a_end = a + (Addr)pkt->req->getSize();
        for (auto &kv : fault_store_registry) {
            FaultStoreEntry &e = kv.second;
            if (e.dyn_seq == seq || e.overwritten)
                continue;   // the fault store itself / already marked
            if (a < e.byte_end && e.byte_begin < a_end) {
                e.overwritten = true;
                std::ostringstream d;
                d << "fault_store_seq=" << e.dyn_seq
                  << ";overwrite_store_seq=" << seq
                  << ";addr=0x" << std::hex << a << std::dec
                  << ";size=" << pkt->req->getSize();
                // ptag=0: this is a boundary event, not part of the fault
                // store's propagation chain.
                writeNode(0, "store_overwrite", seq, true, 0, false,
                          a, true, 0, false, 0, false, d.str());
            }
        }
    }

    bool
    CHAOSPropagation::isFaultStore(uint64_t dyn_seq) const
    {
        return fault_store_registry.count(dyn_seq) != 0;
    }

    uint64_t
    CHAOSPropagation::faultStorePtag(uint64_t dyn_seq) const
    {
        auto it = fault_store_registry.find(dyn_seq);
        return it == fault_store_registry.end() ? 0 : it->second.ptag;
    }

    void
    CHAOSPropagation::noteLQLifecycle(uint64_t dyn_seq, uint64_t idx,
                                      uint64_t gen, const char *action,
                                      const char *reason)
    {
        if (!write_log) return;
        std::ostringstream d;
        d << "queue=LQ;action=" << action << ";index=" << idx
          << ";generation=" << gen << ";reason=" << reason;
        writeNode(0, "lq_lifecycle", dyn_seq, true, 0, false, 0, false,
                  idx, true, 0, false, d.str());
    }

    void
    CHAOSPropagation::noteSQLifecycle(uint64_t dyn_seq, uint64_t idx,
                                      uint64_t gen, const char *action,
                                      const char *reason)
    {
        if (!write_log) return;
        std::ostringstream d;
        d << "queue=SQ;action=" << action << ";index=" << idx
          << ";generation=" << gen << ";reason=" << reason;
        writeNode(0, "sq_lifecycle", dyn_seq, true, 0, false, 0, false,
                  idx, true, 0, false, d.str());
        // v3.2.12 (task 12): a completed fault store's SQ slot reallocated
        // to a later store — sq03_effect.resource_reuse_tick (the
        // resource-release observable; the "reuse" action is emitted by
        // LSQUnit::insertStore when the idx was allocated before).
        if (std::string(action) == "reuse") {
            for (auto &kv : fault_store_registry) {
                FaultStoreEntry &e = kv.second;
                if (e.idx == idx && e.complete_tick != 0
                        && e.resource_reuse_tick == 0)
                    e.resource_reuse_tick = curTick();
            }
        }
    }

    // ------------------------------------------------------------ pipeline

    void
    CHAOSPropagation::noteMemRequest(const char *site, uint64_t dyn_seq,
                                     const RequestPtr &req, int64_t lq_idx,
                                     int64_t sq_idx)
    {
        if (!write_log || !req || !req->hasVaddr())
            return;
        sweepExpired();
        // Real request identity: one request id per Request object, one
        // fragment id per sendFragmentToTranslation call. Not dyn_inst_seq.
        auto &rm = req_meta[req.get()];
        if (rm.request_id == 0) {
            rm.request_id = ++next_request_id;
        }
        if (rm.request_tick == 0) {
            rm.request_tick = curTick();      // first request-issue tick
            rm.vaddr = req->getVaddr();
            rm.size = req->getSize();
            rm.dyn_seq = dyn_seq;
            rm.lq_idx = lq_idx;
            rm.sq_idx = sq_idx;
        }
        // The fetch that produced a response is the most recent send, not the
        // first one: a re-sent Request discards the earlier attempt.
        rm.last_send_tick = curTick();
        rm.fragment_id = ++next_fragment_id;
        const uint64_t request_id = rm.request_id;
        const uint64_t fragment_id = rm.fragment_id;
        const Addr v = req->getVaddr();
        const Addr v_end = v + (Addr)req->getSize();

        // addrpath registry: range overlap + dyn-inst binding. The request
        // seq must be stamped (getReqInstSeqNum asserts otherwise — gem5
        // v25 request.hh); an unstamped request falls back to overlap-only
        // (documented: split _mainReq is not seq-stamped).
        const bool stamped = req->hasInstSeqNum();
        const uint64_t req_seq = stamped ? req->getReqInstSeqNum() : 0;
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
              << req->getSize() << ";request_id=" << request_id
              << ";fragment_id=" << fragment_id
              << ";lq_entry_id=" << lq_idx
              << ";sq_entry_id=" << sq_idx
              ;
            writeNode(e.ptag, "mem_req", dyn_seq, true,
                      request_id, true, v, true, 0, false, 0, false, d.str());
        }

        // cache faulted-byte registry: range overlap in the architectural
        // address space. SE note: Syscall Emulation has no MMU/page table, so
        // the CPU presents the virtual address directly to memory; there is
        // no separately translated physical address. The trace's `pa` field
        // is the memory-side (cache block-aligned) address, not an FS PA.
        for (const auto &kv : blk_registry) {
            const BlkEntry &e = kv.second;
            if (v >= e.byte_end || e.byte_begin >= v_end)
                continue;
            std::ostringstream d;
            d << "site=" << site << ";family=cache;size=" << req->getSize()
              << ";request_id=" << request_id
              << ";fragment_id=" << fragment_id
              << ";lq_entry_id=" << lq_idx
              << ";sq_entry_id=" << sq_idx;
            writeNode(e.ptag, "mem_req", dyn_seq, true,
                      request_id, true, v, true, 0, false, 0, false, d.str());
        }

        // DA04 (v3.2.5): a LOAD request whose range overlaps a registered
        // faulted store byte is a candidate consumer. This node records the
        // load's REAL request time; the final causal decision happens at the
        // response (Task 7) using request_tick, never the response tick.
        // lq_idx >= 0 identifies the load side at this hook (gem5 v25
        // Request has no isWrite()); instruction fetches are not data loads.
        if (lq_idx >= 0 && !req->isInstFetch()) {
            for (const auto &kv : fault_store_registry) {
                const FaultStoreEntry &e = kv.second;
                if (v >= e.byte_end || e.byte_begin >= v_end)
                    continue;
                // Emit for EVERY overlapping send, including sends before the
                // store write (written_tick == 0 or later tick): otherwise a
                // load whose only recorded sends precede the write leaves no
                // request-time evidence at all.
                // v3.2.12 (task 13): for an SP05 lost write there IS no
                // written_tick (the send was skipped); the candidate rule is
                // then "completed-without-send, not overwritten, younger" —
                // the same rule noteMemResponse binds the reload with.
                bool candidate = e.written_tick != 0
                    && chaos_store_chain::mayConsumeFaultByte(
                        dyn_seq, e.dyn_seq, e.overwritten, e.written_tick,
                        rm.last_send_tick);
                if (!candidate && std::string(e.family) == "sp05_complete"
                        && e.complete_tick != 0 && e.written_tick == 0
                        && !e.overwritten && dyn_seq > e.dyn_seq) {
                    candidate = true;
                }
                std::ostringstream sd;
                sd << "site=" << site << ";family=" << e.family
                   << ";candidate=" << (candidate ? 1 : 0)
                   << ";size=" << req->getSize()
                   << ";request_id=" << request_id
                   << ";fragment_id=" << fragment_id
                   << ";request_tick=" << rm.request_tick
                   << ";last_send_tick=" << rm.last_send_tick
                   << ";store_write_tick=" << e.written_tick
                   << ";last_send_before_store_write="
                   << (e.written_tick != 0
                       && rm.last_send_tick < e.written_tick ? 1 : 0)
                   << ";store_not_written_yet=" << (e.written_tick == 0 ? 1 : 0)
                   << ";overwritten=" << (e.overwritten ? 1 : 0)
                   << ";lq_entry_id=" << lq_idx
                   << ";sq_entry_id=" << sq_idx;
                writeNode(e.ptag, "mem_req", dyn_seq, true,
                          request_id, true, v, true, 0, false, 0, false,
                          sd.str(), rm.last_send_tick);
            }
        }
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

        // LP01: the response is observed AFTER maybeCorrupt, so data_* is the
        // delivered (injected) payload. Bind directly by instruction identity.
        auto lf = l1dfwd_registry.find(inst->seqNum);
        if (lf != l1dfwd_registry.end() && lf->second.resp_node == 0) {
            hit_ptag = lf->second.ptag;
            hit_family = "l1d_fwd";
        }
        // MD04: bind the load's response if it arrives after the suppressed
        // violation report. A late-bound load (response already consumed) is
        // handled at injection and never reaches here.
        auto md = md04_registry.find(inst->seqNum);
        if (!hit_ptag && md != md04_registry.end()
                && !md->second.load_complete
                && md->second.resp_node == 0) {
            hit_ptag = md->second.ptag;
            hit_family = "md04";
        }
        // FW05: bind the load's delivered data to the wrong-source injection.
        auto fw = fw05_registry.find(inst->seqNum);
        if (!hit_ptag && fw != fw05_registry.end()
                && fw->second.resp_node == 0) {
            hit_ptag = fw->second.ptag;
            hit_family = "fw05";
        }
        // LQ04 (v3.2.10): the target load's LQ entry lifetime was corrupted
        // after a successful executeLoad, but the in-flight response is
        // bound by pkt->senderState (the LSQRequest), NOT by the LQ entry,
        // so it still arrives here and still delivers the unchanged data.
        // Bind it to the chain so resp/writeback/consumer nodes carry the
        // LQ04 ptag.
        auto lq = lq04_registry.find(inst->seqNum);
        if (!hit_ptag && lq != lq04_registry.end()
                && lq->second.resp_node == 0) {
            hit_ptag = lq->second.ptag;
            hit_family = "lq04";
        }

        // addrpath: the response's own Request vaddr range vs the registry,
        // bound to this instruction (the faulting load itself).
        if (!hit_ptag && pkt->req && pkt->req->hasVaddr()) {
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
        // store family (DA04 byte-enable / SQ01 store data / SQ03 canWB): a
        // LOAD whose request range covers the faulted byte observes the
        // store's architectural effect. Use the Request VA/size
        // (Packet::getAddr is block-aligned and its size is not the access
        // size). Store responses are excluded (their dyn seq is the store's).
        FaultStoreEntry *hit_store_entry = nullptr;
        if (!hit_ptag && !pkt->isWrite() && inst->isLoad() && pkt->req &&
                pkt->req->hasVaddr()) {
            const Addr a = pkt->req->getVaddr();
            const Addr a_end = a + (Addr)pkt->req->getSize();
            // v3.2.5: causality is anchored at the load's REQUEST tick, not
            // the response tick. See store_chain_rules.hh.
            const Tick req_tick =
                (pkt->req && req_meta.count(pkt->req.get()))
                    ? req_meta[pkt->req.get()].request_tick : 0;
            const Tick send_tick =
                (pkt->req && req_meta.count(pkt->req.get()))
                    ? req_meta[pkt->req.get()].last_send_tick : 0;
            for (auto &kv : fault_store_registry) {
                FaultStoreEntry &e = kv.second;
                // The last send is the attempt whose response we are seeing.
                if (!chaos_store_chain::mayConsumeFaultByte(
                        inst->seqNum, e.dyn_seq, e.overwritten,
                        e.written_tick, send_tick))
                    continue;
                if (a < e.byte_end && e.byte_begin < a_end) {
                    hit_ptag = e.ptag;
                    hit_family = e.family;
                    hit_store_entry = &e;
                    break;
                }
            }
            // SP05 (v3.2.12 task 13): the fault store's cache write was
            // SKIPPED (completed without being sent), so written_tick stays
            // 0 and mayConsumeFaultByte can never match — by design, there
            // is no write to order against. A younger load whose range covers
            // the store's address reads whatever memory holds instead of the
            // store's bytes: bind it to the chain as the observer of the lost
            // write (the request-time candidate flag in noteMemRequest uses
            // the same rule). The would-be write tick is unknowable on this
            // run; the record states the request/response ticks and both
            // hashes, and the audit compares reload vs. store data.
            if (!hit_ptag) {
                for (auto &kv : fault_store_registry) {
                    FaultStoreEntry &e = kv.second;
                    if (std::string(e.family) != "sp05_complete")
                        continue;
                    if (e.complete_tick == 0 || e.written_tick != 0)
                        continue;   // not completed-skipped (or a later
                                    // response wrote it — not this fault)
                    if (e.overwritten)
                        continue;   // another store replaced the bytes
                    if (inst->seqNum <= e.dyn_seq)
                        continue;   // program order: the load is younger
                    if (a < e.byte_end && e.byte_begin < a_end) {
                        hit_ptag = e.ptag;
                        hit_family = e.family;
                        hit_store_entry = &e;
                        break;
                    }
                }
            }
        }
        if (!hit_ptag)
            return;

        // v3.2.12 (tasks 11/12/13): remember the first reload bound to a
        // store-family chain — it feeds the consolidated sq01_chain /
        // sq03_effect / sp05_stage record (reload_seq + reload_data_hash).
        // The hash is the same packet bytes the resp node below hashes.
        if (hit_store_entry && hit_store_entry->reload_seq == 0
                && std::string(hit_family) != "byte_enable") {
            const unsigned reload_len = pkt->hasData() ? pkt->getSize() : 0;
            hit_store_entry->reload_seq = inst->seqNum;
            hit_store_entry->reload_hash = reload_len
                ? fnvHex(pkt->getPtr<uint8_t>(), reload_len) : "";
        }

        // resp node: the memory response delivering the fault. Address and
        // data are separate: `addr` is the packet address (PA in this
        // tracer); `data_*` is the actual returned packet data.
        const uint64_t req_seq =
            (pkt->req && pkt->req->hasInstSeqNum())
                ? pkt->req->getReqInstSeqNum() : 0;
        if (pkt->req) {
            auto &rm = req_meta[pkt->req.get()];
            if (rm.request_id == 0) rm.request_id = ++next_request_id;
            if (rm.fragment_id == 0) rm.fragment_id = ++next_fragment_id;
        }
        const uint64_t request_id =
            (pkt->req && req_meta.count(pkt->req.get())) ? req_meta[pkt->req.get()].request_id : 0;
        const uint64_t fragment_id =
            (pkt->req && req_meta.count(pkt->req.get())) ? req_meta[pkt->req.get()].fragment_id : 0;
        const bool l1d_fwd = hit_ptag
            && std::string(hit_family) == "l1d_fwd";
        // LP01: injection and response are the same delivery; reuse the id
        // allocated at injection instead of inventing a second one.
        const uint64_t response_id = l1d_fwd
            ? lf->second.response_id : ++next_response_id;
        const unsigned data_len = pkt->hasData() ? pkt->getSize() : 0;
        // For LP01, use the bytes the injector actually wrote. This is the
        // same buffer writeback consumes; using the registry avoids a stale
        // packet view if gem5 delivered a different wrapper object.
        const std::string data_hash_str = l1d_fwd ? lf->second.inj_fnv
            : (data_len ? fnvHex(pkt->getPtr<uint8_t>(), data_len) : "");
        const std::string data_hex = l1d_fwd ? lf->second.inj_hex
            : (data_len ? bytesToHex(pkt->getPtr<uint8_t>(), data_len) : "");
        uint64_t resp_node = 0;
        {
            std::ostringstream d;
            d << "family=" << hit_family << ";size=" << pkt->getSize()
              << ";data_len=" << data_len
              << ";data_fnv=" << (data_len ? data_hash_str : "null")
              << ";data_hex=" << (data_hex.empty() ? "null" : data_hex)
              << ";request_id=" << request_id
              << ";response_id=" << response_id
              << ";fragment_id=" << fragment_id
              << ";lq_entry_id=" << inst->lqIdx
              << ";sq_entry_id=" << inst->sqIdx
              << ";entry_generation="
              << (inst->isLoad() ? inst->lqEntryGeneration
                                 : inst->sqEntryGeneration)
              << ";execution_attempt_id=" << inst->executionAttemptId
              << ";replay_generation=" << inst->replayGeneration;
            if (hit_family && std::string(hit_family) == "md04") {
                d << ";family=md04;late_binding=0"
                  << ";load_seq=" << inst->seqNum
                  << ";store_seq=" << md->second.store_seq
                  << ";eligible_ordinal=" << md->second.eligible_ordinal
                  << ";violation_report_suppressed=1";
            }
            if (hit_family && std::string(hit_family) == "fw05") {
                d << ";family=fw05;selected_source=alt_store"
                  << ";wrong_source_substitution=1"
                  << ";load_seq=" << inst->seqNum
                  << ";true_store_seq=" << fw->second.true_seq
                  << ";alt_store_seq=" << fw->second.alt_seq
                  << ";true_addr=0x" << std::hex << fw->second.true_addr
                  << ";alt_addr=0x" << fw->second.alt_addr
                  << ";load_addr=0x" << fw->second.load_addr << std::dec
                  << ";load_size=" << fw->second.load_size
                  << ";true_fnv=" << fw->second.true_fnv
                  << ";alt_fnv=" << fw->second.alt_fnv
                  << ";eligible_ordinal=" << fw->second.eligible_ordinal;
            }
            // LQ04: the response reached the CPU through the request's own
            // senderState while the LQ entry sat corrupted (valid=0,
            // request popped into the side channel). The entry_* fields are
            // the corrupt-window state: the response arrives strictly before
            // the commit/squash boundary restore (a load commits only after
            // this writeback), and the LIVE-observed values are recorded
            // independently by the completeDataAccess response_probe
            // lifecycle node (lsq_unit.cc). data_unchanged=1: LQ04 never
            // touches the payload.
            if (hit_family && std::string(hit_family) == "lq04") {
                d << ";association=sender_state"
                  << ";entry_valid_at_response=0"
                  << ";entry_request_at_response=0"
                  << ";data_unchanged=1";
            }
            if (l1d_fwd) {
                d << ";orig_data_fnv=" << lf->second.orig_fnv
                  << ";orig_data_hex=" << lf->second.orig_hex
                  << ";inj_data_fnv=" << lf->second.inj_fnv
                  << ";mask=0x" << std::hex << lf->second.mask << std::dec
                  << ";eligible_ordinal=" << lf->second.eligible_ordinal
                  << ";request_tick=" << lf->second.request_tick
                  << ";response_tick=" << curTick()
                  << ";payload_len=" << lf->second.size
                  << ";writeback_value=null;BEFORE_WB=1";
            } else {
                const Tick rt = (pkt->req && req_meta.count(pkt->req.get()))
                    ? req_meta[pkt->req.get()].request_tick : 0;
                d << ";request_tick=" << rt
                  << ";response_tick=" << curTick();
            }
            d << ";pa=" << std::hex << pkt->getAddr() << std::dec;
            if (inst->getFault() != NoFault)
                d << ";fault=" << inst->getFault()->name();
            resp_node = writeNode(hit_ptag, "resp", inst->seqNum, true,
                                  request_id, request_id != 0,
                                  pkt->getAddr(), true,
                                  0, false, 0, false, d.str());
            resp_node_by_ptag[hit_ptag] = resp_node;
            resp_hash_by_ptag[hit_ptag] = data_hash_str;
            if (l1d_fwd)
                lf->second.resp_node = resp_node;
            if (hit_family && std::string(hit_family) == "md04")
                md->second.resp_node = resp_node;
            if (hit_family && std::string(hit_family) == "fw05")
                fw->second.resp_node = resp_node;
            if (hit_family && std::string(hit_family) == "lq04")
                lq->second.resp_node = resp_node;
        }

        // LP01 writeback is emitted after LSQUnit::writeback reads the PRF
        // (noteL1DForwardWriteback); the pre-writeback taint loop below would
        // record the payload, not the actual register value.
        if (l1d_fwd)
            return;

        // v3.2.6: defer the register_writeback node until AFTER completeAcc.
        // The packet bytes are not the register value for size < 8
        // (endianness/extension), so hashing them here made the source hash
        // discontinuous with the consumer input (DA04's 4-byte load).
        if (!wb_to_reg || inst->getFault() != NoFault)
            return;
        ChainWbEntry w;
        w.ptag = hit_ptag;
        w.resp_node = resp_node;
        w.request_id = request_id;
        w.response_id = response_id;
        w.size = data_len;
        w.family = hit_family ? hit_family : "unknown";
        w.payload_fnv = data_hash_str;
        w.payload_hex = data_hex;
        pending_chain_wb[inst->seqNum] = w;
    }

    uint64_t
    CHAOSPropagation::noteL1DForwardInjection(o3::DynInst *inst, Packet *pkt,
                                              bool wb_to_reg,
                                              const uint8_t *before,
                                              unsigned size, uint64_t mask,
                                              uint64_t eligible_ordinal)
    {
        if (!write_log || !inst || !pkt || !before || size == 0)
            return 0;
        const uint64_t ptag = ++next_ptag;
        fault_seqs.insert(inst->seqNum);

        L1DFwdEntry e;
        e.ptag = ptag;
        e.size = size;
        e.mask = mask;
        e.eligible_ordinal = eligible_ordinal;
        if (pkt->req) {
            auto &rm = req_meta[pkt->req.get()];
            if (rm.request_id == 0)
                rm.request_id = ++next_request_id;
            e.request_id = rm.request_id;
            e.request_tick = rm.request_tick;
            e.fragment_id = rm.fragment_id;
        }
        e.response_id = ++next_response_id;
        const uint8_t *after = pkt->getPtr<uint8_t>();
        e.orig_fnv = fnvHex(before, size);
        e.orig_hex = bytesToHex(before, size);
        e.inj_fnv = fnvHex(after, size);
        e.inj_hex = bytesToHex(after, size);

        std::ostringstream d;
        d << "site=LSQUnit::completeDataAccess;family=l1d_fwd;model=LP01"
          << ";size=" << size
          << ";orig_data_fnv=" << e.orig_fnv
          << ";orig_data_hex=" << e.orig_hex
          << ";inj_data_fnv=" << e.inj_fnv
          << ";inj_data_hex=" << e.inj_hex
          << ";byte0_before=0x" << std::hex << (unsigned)before[0]
          << ";byte0_after=0x" << (unsigned)after[0] << std::dec
          << ";mask=0x" << std::hex << mask << std::dec
          << ";eligible_ordinal=" << eligible_ordinal
          << ";request_id=" << e.request_id
          << ";response_id=" << e.response_id
          << ";fragment_id=" << e.fragment_id
          << ";request_tick=" << e.request_tick
          << ";injection_tick=" << curTick()
          << ";lq_entry_id=" << inst->lqIdx
          << ";entry_generation=" << inst->lqEntryGeneration
          << ";execution_attempt_id=" << inst->executionAttemptId
          << ";replay_generation=" << inst->replayGeneration
          << ";wb_to_reg=" << (wb_to_reg ? 1 : 0)
          << ";addr=0x" << std::hex << pkt->getAddr() << std::dec
          << ";phys_regs=";
        for (int i = 0; i < (int)inst->numDestRegs(); ++i) {
            const PhysRegIdPtr p = inst->renamedDestIdx(i);
            if (p)
                d << (i ? "," : "") << regClassName(p->classValue())
                  << ":" << p->index();
        }
        writeNode(ptag, "inj_l1dfwd", inst->seqNum, true,
                  e.request_id, e.request_id != 0, pkt->getAddr(), true,
                  0, false, 0, false, d.str());
        l1dfwd_registry[inst->seqNum] = e;
        return ptag;
    }

    void
    CHAOSPropagation::noteL1DForwardWriteback(o3::DynInst *inst)
    {
        if (!write_log || !inst || !o3cpu)
            return;
        auto it = l1dfwd_registry.find(inst->seqNum);
        if (it == l1dfwd_registry.end())
            return;
        L1DFwdEntry &e = it->second;
        if (e.resp_node == 0)
            return;                 // response was squashed away: no WB claim

        // writeback() skips completeAcc when the instruction already carries a
        // fault (ReExec / partial translation). In that case the PRF keeps its
        // stale value; emitting value_matches_payload=0 would be a false
        // "hash discontinuity". Record the honest no-writeback condition.
        if (inst->getFault() != NoFault) {
            std::ostringstream d;
            d << "family=l1d_fwd;writeback_value=null;"
              << "writeback_value_fnv=null;payload_fnv=" << e.inj_fnv
              << ";hash_basis=no_writeback_fault;value_matches_payload=0"
              << ";source_value_hash=" << e.inj_fnv
              << ";source_event_id=" << e.resp_node
              << ";fault=" << inst->getFault()->name()
              << ";request_id=" << e.request_id
              << ";response_id=" << e.response_id
              << ";eligible_ordinal=" << e.eligible_ordinal
              << ";lq_entry_id=" << inst->lqIdx
              << ";entry_generation=" << inst->lqEntryGeneration
              << ";execution_attempt_id=" << inst->executionAttemptId
              << ";replay_generation=" << inst->replayGeneration
              << ";writeback_tick=" << curTick();
            writeNode(e.ptag, "taint_reg", inst->seqNum, true,
                      e.request_id, e.request_id != 0, 0, false, 0, false,
                      0, false, d.str());
            l1dfwd_registry.erase(it);
            return;
        }

        const int ndest = (int)inst->numDestRegs();
        for (int i = 0; i < ndest; ++i) {
            const PhysRegIdPtr phys = inst->renamedDestIdx(i);
            if (!phys)
                continue;
            uint64_t value = 0;
            unsigned bytes = 0;
            const std::string vhash = regValueHash(
                inst, phys, inst->threadNumber, &value, &bytes);
            std::ostringstream vb;
            vb << std::hex << value << std::dec;
            // A vector/matrix destination has no scalar PRF hash; do not call
            // that an extension mismatch or a continuity failure.
            const bool scalar8 = (e.size == 8 && bytes == 8
                                  && !vhash.empty());
            const bool basis_ok = scalar8 && vhash == e.inj_fnv;
            const char *basis = scalar8 ? "payload_equals_regval"
                : (vhash.empty() ? "no_scalar_regval" : "regval_extension");
            std::ostringstream d;
            d << "family=l1d_fwd;class=" << regClassName(phys->classValue())
              << ";dest_idx=" << i
              << ";phys_reg=" << phys->index()
              << ";arch_reg=" << inst->destRegIdx(i).index()
              << ";writeback_value=" << vb.str()
              << ";writeback_value_fnv=" << (vhash.empty() ? "null" : vhash)
              << ";payload_fnv=" << e.inj_fnv
              << ";payload_hex=" << e.inj_hex
              << ";payload_len=" << e.size
              << ";hash_basis=" << basis
              << ";value_matches_payload=" << (basis_ok ? 1 : 0)
              << ";source_value_hash=" << e.inj_fnv
              << ";source_event_id=" << e.resp_node
              << ";request_id=" << e.request_id
              << ";response_id=" << e.response_id
              << ";eligible_ordinal=" << e.eligible_ordinal
              << ";lq_entry_id=" << inst->lqIdx
              << ";entry_generation=" << inst->lqEntryGeneration
              << ";execution_attempt_id=" << inst->executionAttemptId
              << ";replay_generation=" << inst->replayGeneration
              << ";writeback_tick=" << curTick();
            const uint64_t wb_node = writeNode(
                e.ptag, "taint_reg", inst->seqNum, true,
                e.request_id, e.request_id != 0, 0, false,
                phys->index(), true,
                inst->destRegIdx(i).index(), true, d.str());
            TaintEntry te;
            te.ptag = e.ptag;
            te.taintor_seq = inst->seqNum;
            te.node_id = wb_node;
            te.value_hash = vhash;   // actual PRF value, not the payload
            taint_set[std::make_pair(phys->classValue(),
                                     phys->index())] = te;
            writeEdgeRow(e.ptag, e.resp_node, wb_node, inst->seqNum,
                         inst->seqNum, e.inj_fnv, vhash,
                         (basis_ok ? "payload_to_register"
                                   : "payload_to_register_extended"));
        }
        l1dfwd_registry.erase(it);
    }

    void
    CHAOSPropagation::noteChainWriteback(o3::DynInst *inst)
    {
        if (!write_log || !inst || !o3cpu)
            return;
        // FW05: a forwarded load has no memory response to bind. Emit the
        // register writeback directly from the PRF and taint downstream.
        auto fw = fw05_registry.find(inst->seqNum);
        if (fw != fw05_registry.end() && !fw->second.wb_emitted) {
            fw->second.wb_emitted = true;
            if (inst->getFault() != NoFault)
                return;
            for (int i = 0; i < (int)inst->numDestRegs(); ++i) {
                const PhysRegIdPtr phys = inst->renamedDestIdx(i);
                if (!phys)
                    continue;
                uint64_t value = 0;
                unsigned bytes = 0;
                const std::string vhash = regValueHash(
                    inst, phys, inst->threadNumber, &value, &bytes);
                if (vhash.empty())
                    continue;
                std::ostringstream vb;
                vb << std::hex << value << std::dec;
                std::ostringstream d;
                d << "family=fw05;class="
                  << regClassName(phys->classValue())
                  << ";dest_idx=" << i
                  << ";phys_reg=" << phys->index()
                  << ";arch_reg=" << inst->destRegIdx(i).index()
                  << ";writeback_value=" << vb.str()
                  << ";writeback_value_fnv=" << vhash
                  << ";payload_fnv=" << fw->second.alt_fnv
                  << ";payload_len=" << fw->second.load_size
                  << ";hash_basis="
                  << (vhash == fw->second.alt_fnv
                      ? "payload_equals_regval" : "regval_extension")
                  << ";value_matches_payload="
                  << (vhash == fw->second.alt_fnv ? 1 : 0)
                  << ";source_value_hash=" << fw->second.alt_fnv
                  << ";source_event_id=0"
                  << ";load_seq=" << inst->seqNum
                  << ";true_store_seq=" << fw->second.true_seq
                  << ";alt_store_seq=" << fw->second.alt_seq
                  << ";eligible_ordinal=" << fw->second.eligible_ordinal
                  << ";execution_attempt_id=" << inst->executionAttemptId
                  << ";replay_generation=" << inst->replayGeneration
                  << ";writeback_tick=" << curTick();
                const uint64_t wb_node = writeNode(
                    fw->second.ptag, "taint_reg", inst->seqNum, true, 0,
                    false, 0, false, phys->index(), true,
                    inst->destRegIdx(i).index(), true, d.str());
                TaintEntry te;
                te.ptag = fw->second.ptag;
                te.taintor_seq = inst->seqNum;
                te.node_id = wb_node;
                te.value_hash = vhash;
                taint_set[std::make_pair(phys->classValue(),
                                          phys->index())] = te;
            }
            return;
        }

        // LQ04 (v3.2.10): the response bound this chain in noteMemResponse
        // and registered the pending chain writeback there (the same
        // resp→pending mechanism as the cache/store/addrpath families; the
        // generic tail below would also fire, but LQ04 needs its own
        // detail). Emit the register writeback from the ACTUAL PRF value
        // with the honest data_corruption=0 marker — LQ04 corrupted only
        // the entry lifetime, the delivered and written-back data is
        // correct — and taint the dest so noteCommit emits consumer nodes
        // for later readers. No SDC may be claimed from these edges.
        auto lq = lq04_registry.find(inst->seqNum);
        if (lq != lq04_registry.end()) {
            auto it = pending_chain_wb.find(inst->seqNum);
            // Claim the pending writeback only when the LQ04-bound response
            // registered it (family lq04). A pending entry from another
            // family (cross-model mount corner, unreachable in the
            // single-model pilots) stays with the generic tail below; a
            // missing entry means no response-bound writeback to claim
            // (the generic tail would no-op too).
            if (it != pending_chain_wb.end()
                    && it->second.family == "lq04") {
                const ChainWbEntry w = it->second;
                pending_chain_wb.erase(it);
                if (inst->getFault() != NoFault)
                    return;   // completeAcc did not run; no register value
                for (int i = 0; i < (int)inst->numDestRegs(); ++i) {
                    const PhysRegIdPtr phys = inst->renamedDestIdx(i);
                    if (!phys)
                        continue;
                    uint64_t value = 0;
                    unsigned bytes = 0;
                    const std::string vhash = regValueHash(
                        inst, phys, inst->threadNumber, &value, &bytes);
                    if (vhash.empty())
                        continue;
                    const bool scalar8 = (w.size == 8 && bytes == 8);
                    const bool basis_ok = scalar8 && vhash == w.payload_fnv;
                    const char *basis = scalar8 ? "payload_equals_regval"
                        : "regval_extension";
                    std::ostringstream vb;
                    vb << std::hex << value << std::dec;
                    std::ostringstream d;
                    d << "family=lq04;data_corruption=0"
                      << ";association=sender_state;data_unchanged=1"
                      << ";class=" << regClassName(phys->classValue())
                      << ";dest_idx=" << i
                      << ";phys_reg=" << phys->index()
                      << ";arch_reg=" << inst->destRegIdx(i).index()
                      << ";writeback_value=" << vb.str()
                      << ";writeback_value_fnv=" << vhash
                      << ";payload_fnv=" << w.payload_fnv
                      << ";payload_hex=" << w.payload_hex
                      << ";payload_len=" << w.size
                      << ";hash_basis=" << basis
                      << ";value_matches_payload=" << (basis_ok ? 1 : 0)
                      << ";source_value_hash=" << w.payload_fnv
                      << ";source_event_id=" << w.resp_node
                      << ";request_id=" << w.request_id
                      << ";response_id=" << w.response_id
                      << ";lq_idx=" << lq->second.lq_idx
                      << ";lq_gen=" << lq->second.lq_gen
                      << ";eligible_ordinal=" << lq->second.eligible_ordinal
                      << ";execution_attempt_id=" << inst->executionAttemptId
                      << ";replay_generation=" << inst->replayGeneration
                      << ";writeback_tick=" << curTick();
                    const uint64_t wb_node = writeNode(
                        w.ptag, "taint_reg", inst->seqNum, true,
                        w.request_id, w.request_id != 0, 0, false,
                        phys->index(), true,
                        inst->destRegIdx(i).index(), true, d.str());
                    TaintEntry te;
                    te.ptag = w.ptag;
                    te.taintor_seq = inst->seqNum;
                    te.node_id = wb_node;
                    te.value_hash = vhash;   // actual PRF value
                    taint_set[std::make_pair(phys->classValue(),
                                             phys->index())] = te;
                    if (w.resp_node)
                        writeEdgeRow(w.ptag, w.resp_node, wb_node,
                                     inst->seqNum, inst->seqNum,
                                     w.payload_fnv, vhash,
                                     (basis_ok ? "payload_to_register"
                                               : "payload_to_register_extended"));
                }
                return;
            }
        }

        auto it = pending_chain_wb.find(inst->seqNum);
        if (it == pending_chain_wb.end())
            return;
        const ChainWbEntry w = it->second;
        pending_chain_wb.erase(it);
        if (inst->getFault() != NoFault)
            return;   // completeAcc did not run; no register value to claim

        const int ndest = (int)inst->numDestRegs();
        for (int i = 0; i < ndest; ++i) {
            const PhysRegIdPtr phys = inst->renamedDestIdx(i);
            if (!phys)
                continue;
            uint64_t value = 0;
            unsigned bytes = 0;
            const std::string vhash = regValueHash(
                inst, phys, inst->threadNumber, &value, &bytes);
            if (vhash.empty())
                continue;
            const bool scalar8 = (w.size == 8 && bytes == 8);
            const bool basis_ok = scalar8 && vhash == w.payload_fnv;
            const char *basis = scalar8 ? "payload_equals_regval"
                : "regval_extension";
            std::ostringstream vb;
            vb << std::hex << value << std::dec;
            std::ostringstream d;
            d << "family=" << w.family
              << ";class=" << regClassName(phys->classValue())
              << ";dest_idx=" << i
              << ";phys_reg=" << phys->index()
              << ";arch_reg=" << inst->destRegIdx(i).index()
              << ";writeback_value=" << vb.str()
              << ";writeback_value_fnv=" << vhash
              << ";payload_fnv=" << w.payload_fnv
              << ";payload_hex=" << w.payload_hex
              << ";payload_len=" << w.size
              << ";hash_basis=" << basis
              << ";value_matches_payload=" << (basis_ok ? 1 : 0)
              << ";source_value_hash=" << w.payload_fnv
              << ";source_event_id=" << w.resp_node
              << ";request_id=" << w.request_id
              << ";response_id=" << w.response_id
              << ";execution_attempt_id=" << inst->executionAttemptId
              << ";replay_generation=" << inst->replayGeneration
              << ";writeback_tick=" << curTick();
            const uint64_t wb_node = writeNode(
                w.ptag, "taint_reg", inst->seqNum, true,
                w.request_id, w.request_id != 0, 0, false,
                phys->index(), true,
                inst->destRegIdx(i).index(), true, d.str());
            TaintEntry te;
            te.ptag = w.ptag;
            te.taintor_seq = inst->seqNum;
            te.node_id = wb_node;
            te.value_hash = vhash;   // actual PRF value
            taint_set[std::make_pair(phys->classValue(),
                                     phys->index())] = te;
            if (w.resp_node)
                writeEdgeRow(w.ptag, w.resp_node, wb_node, inst->seqNum,
                             inst->seqNum, w.payload_fnv, vhash,
                             (basis_ok ? "payload_to_register"
                                       : "payload_to_register_extended"));
        }
    }

    void
    CHAOSPropagation::noteSQ03Injection(uint64_t dyn_seq, uint64_t pc,
                                        Addr addr, unsigned size,
                                        uint64_t sq_idx, uint64_t sq_gen,
                                        bool canwb_before, bool canwb_after,
                                        uint64_t stores_before,
                                        uint64_t stores_after,
                                        Tick inject_tick,
                                        uint64_t eligible_ordinal,
                                        uint64_t seed)
    {
        if (!write_log)
            return;
        const uint64_t ptag = ++next_ptag;
        fault_seqs.insert(dyn_seq);
        SQ03Entry e;
        e.ptag = ptag;
        e.dyn_seq = dyn_seq;
        e.addr = addr;
        e.size = size;
        e.sq_idx = sq_idx;
        e.sq_gen = sq_gen;
        e.canwb_before = canwb_before;
        e.canwb_after = canwb_after;
        e.stores_before = stores_before;
        e.stores_after = stores_after;
        e.inject_tick = inject_tick;
        e.eligible_ordinal = eligible_ordinal;
        sq03_registry[dyn_seq] = e;

        FaultStoreEntry fe;
        fe.ptag = ptag;
        fe.dyn_seq = dyn_seq;
        fe.base = addr;
        fe.size = size;
        fe.idx = sq_idx;
        fe.gen = sq_gen;
        fe.byte_begin = addr;
        fe.byte_end = addr + size;
        fe.family = "sq03_canwb";
        fe.registered = inject_tick;
        fault_store_registry[dyn_seq] = fe;

        std::ostringstream d;
        d << "site=executeStore_canWB;family=sq03;model=SQ03"
          << ";store_seq=" << dyn_seq
          << ";store_pc=0x" << std::hex << pc
          << ";store_addr=0x" << addr << std::dec
          << ";store_size=" << size
          << ";sq_entry_id=" << sq_idx
          << ";sq_entry_generation=" << sq_gen
          << ";canwb_before=" << (canwb_before ? 1 : 0)
          << ";canwb_after=" << (canwb_after ? 1 : 0)
          << ";stores_to_wb_before=" << stores_before
          << ";stores_to_wb_after=" << stores_after
          << ";inject_tick=" << inject_tick
          << ";eligible_ordinal=" << eligible_ordinal
          << ";event_ordinal=" << eligible_ordinal
          << ";seed=" << seed
          << ";address_modified=0;size_modified=0;data_modified=0";
        writeNode(ptag, "inj_sq03", dyn_seq, true, 0, false, addr, true,
                  0, false, 0, false, d.str());
    }

    void
    CHAOSPropagation::noteSQ03Writeback(uint64_t dyn_seq, Tick tick)
    {
        if (!write_log)
            return;
        auto it = sq03_registry.find(dyn_seq);
        if (it == sq03_registry.end() || it->second.wb_tick != 0)
            return;
        it->second.wb_tick = tick;
        auto fit = fault_store_registry.find(dyn_seq);
        if (fit != fault_store_registry.end())
            fit->second.written_tick = tick;
        std::ostringstream d;
        d << "site=lsq_writebackStores;family=sq03;model=SQ03"
          << ";store_seq=" << dyn_seq
          << ";writeback_tick=" << tick
          << ";inject_tick=" << it->second.inject_tick
          << ";canwb_after=" << (it->second.canwb_after ? 1 : 0)
          << ";stores_to_wb_after=" << it->second.stores_after;
        writeNode(it->second.ptag, "sq03_wb", dyn_seq, true, 0, false,
                  it->second.addr, true, 0, false, 0, false, d.str());
    }

    void
    CHAOSPropagation::noteSQ03Complete(uint64_t dyn_seq, Tick tick)
    {
        if (!write_log)
            return;
        auto it = sq03_registry.find(dyn_seq);
        if (it == sq03_registry.end() || it->second.complete_tick != 0)
            return;
        it->second.complete_tick = tick;
        // v3.2.12: mirror on the shared fault-store entry so the
        // sq03_effect record carries the completion stage tick.
        auto fit = fault_store_registry.find(dyn_seq);
        if (fit != fault_store_registry.end())
            fit->second.complete_tick = tick;
        std::ostringstream d;
        d << "site=lsq_completeStore;family=sq03;model=SQ03"
          << ";store_seq=" << dyn_seq
          << ";complete_tick=" << tick
          << ";writeback_tick=" << it->second.wb_tick
          << ";inject_tick=" << it->second.inject_tick;
        writeNode(it->second.ptag, "sq03_complete", dyn_seq, true, 0, false,
                  it->second.addr, true, 0, false, 0, false, d.str());
    }

    void
    CHAOSPropagation::noteSP05Injection(uint64_t dyn_seq, uint64_t pc,
                                        Addr addr, unsigned size,
                                        uint64_t sq_idx, uint64_t sq_gen,
                                        bool completed_before,
                                        bool completed_after,
                                        uint64_t stores_before,
                                        uint64_t stores_after,
                                        Tick inject_tick,
                                        uint64_t eligible_ordinal)
    {
        if (!write_log)
            return;
        std::ostringstream d;
        d << "site=writebackStores_prematureComplete;family=sp05;model=SP05"
          << ";store_seq=" << dyn_seq
          << ";store_pc=0x" << std::hex << pc
          << ";store_addr=0x" << addr << std::dec
          << ";store_size=" << size
          << ";sq_entry_id=" << sq_idx
          << ";sq_entry_generation=" << sq_gen
          << ";completed_before=" << (completed_before ? 1 : 0)
          << ";completed_after=" << (completed_after ? 1 : 0)
          << ";stores_to_wb_before=" << stores_before
          << ";stores_to_wb_after=" << stores_after
          << ";mem_sent=0"
          << ";inject_tick=" << inject_tick
          << ";eligible_ordinal=" << eligible_ordinal
          << ";event_ordinal=" << eligible_ordinal
          << ";address_modified=0;size_modified=0;data_modified=0";
        const uint64_t ptag = ++next_ptag;
        sp05_ptag[dyn_seq] = ptag;
        fault_seqs.insert(dyn_seq);
        FaultStoreEntry fe;
        fe.ptag = ptag;
        fe.dyn_seq = dyn_seq;
        fe.base = addr;
        fe.size = size;
        fe.idx = sq_idx;
        fe.gen = sq_gen;
        fe.byte_begin = addr;
        fe.byte_end = addr + size;
        fe.family = "sp05_complete";
        fe.registered = inject_tick;
        fault_store_registry[dyn_seq] = fe;
        writeNode(ptag, "inj_sp05", dyn_seq, true, 0, false, addr, true,
                  0, false, 0, false, d.str());
    }

    void
    CHAOSPropagation::noteSP05Complete(uint64_t dyn_seq, uint64_t sq_idx,
                                       uint64_t sq_gen, bool canwb,
                                       bool completed_before,
                                       uint64_t stores_to_wb_before,
                                       uint64_t stores_to_wb_after,
                                       bool mem_sent, Tick tick)
    {
        if (!write_log)
            return;
        std::ostringstream d;
        d << "site=lsq_completeStore;family=sp05;model=SP05"
          << ";store_seq=" << dyn_seq
          << ";sq_idx=" << sq_idx
          << ";sq_gen=" << sq_gen
          << ";canwb_before=" << (canwb ? 1 : 0)
          << ";completed_before=" << (completed_before ? 1 : 0)
          << ";stores_to_wb_before=" << stores_to_wb_before
          << ";stores_to_wb_after=" << stores_to_wb_after
          << ";mem_sent=" << (mem_sent ? 1 : 0)
          << ";complete_tick=" << tick;
        auto pit = sp05_ptag.find(dyn_seq);
        const uint64_t ptag = pit == sp05_ptag.end() ? 0 : pit->second;
        writeNode(ptag, "sp05_complete", dyn_seq, true, 0, false,
                  0, false, 0, false, 0, false, d.str());
        // v3.2.12 (task 13): record the completion stage tick on the fault
        // store entry — sp05_stage.completion_tick. drain_tick stays 0 (the
        // send was skipped): the honest record of a lost write.
        auto fit = fault_store_registry.find(dyn_seq);
        if (fit != fault_store_registry.end())
            fit->second.complete_tick = tick;
    }

    void
    CHAOSPropagation::noteFW05Injection(uint64_t load_seq, uint64_t load_pc,
                                        uint64_t true_seq, Addr true_addr,
                                        unsigned true_size,
                                        const std::string &true_fnv,
                                        uint64_t alt_seq, Addr alt_addr,
                                        unsigned alt_size,
                                        const std::string &alt_fnv,
                                        Addr load_addr, unsigned load_size,
                                        uint64_t sq_idx, uint64_t sq_gen,
                                        uint64_t lq_idx, uint64_t lq_gen,
                                        uint64_t load_attempt,
                                        uint64_t eligible_ordinal,
                                        uint64_t event_ordinal, uint64_t seed)
    {
        if (!write_log)
            return;
        const uint64_t ptag = ++next_ptag;
        fault_seqs.insert(load_seq);
        FW05Entry e;
        e.ptag = ptag;
        e.true_seq = true_seq;
        e.alt_seq = alt_seq;
        e.true_addr = true_addr;
        e.alt_addr = alt_addr;
        e.load_addr = load_addr;
        e.load_size = load_size;
        e.true_fnv = true_fnv;
        e.alt_fnv = alt_fnv;
        e.eligible_ordinal = eligible_ordinal;
        fw05_registry[load_seq] = e;

        std::ostringstream tp;
        tp << "FW05-L" << load_seq << "-T" << true_seq << "-A" << alt_seq
           << "-K" << curTick();
        std::ostringstream d;
        d << "site=store->load_forward_decision;family=fw05;model=FW05"
          << ";definition=FW05-DEF-v1"
          << ";target_pair_id=" << tp.str()
          << ";load_seq=" << load_seq
          << ";load_pc=0x" << std::hex << load_pc
          << ";true_store_seq=" << std::dec << true_seq
          << ";alt_store_seq=" << alt_seq
          << ";true_addr=0x" << std::hex << true_addr
          << ";alt_addr=0x" << alt_addr
          << ";load_addr=0x" << load_addr << std::dec
          << ";load_size=" << load_size
          << ";true_store_size=" << true_size
          << ";alt_store_size=" << alt_size
          << ";true_data_fnv=" << true_fnv
          << ";alt_data_fnv=" << alt_fnv
          << ";selected_source=alt_store;wrong_source_substitution=1"
          << ";data_differs=1"
          << ";sq_entry_id=" << sq_idx
          << ";sq_entry_generation=" << sq_gen
          << ";lq_entry_id=" << lq_idx
          << ";lq_entry_generation=" << lq_gen
          << ";eligible_ordinal=" << eligible_ordinal
          << ";eligible_forwarding_pair_ordinal=" << eligible_ordinal
          << ";event_ordinal=" << event_ordinal
          << ";seed=" << seed
          << ";address_modified=0;size_modified=0"
          << ";execution_attempt_id=" << load_attempt
          << ";replay_generation=0";
        writeNode(ptag, "inj_fw05", load_seq, true, 0, false, load_addr, true,
                  0, false, 0, false, d.str());
    }

    uint64_t
    CHAOSPropagation::noteLQ04Injection(o3::DynInst *inst, uint64_t lq_idx,
                                        uint64_t lq_gen, uint64_t request_id,
                                        Addr addr, unsigned size,
                                        uint64_t occ_before,
                                        uint64_t occ_after,
                                        uint64_t eligible_ordinal,
                                        uint64_t event_ordinal,
                                        uint64_t injected,
                                        uint64_t attempt_id,
                                        uint64_t replay_gen)
    {
        if (!write_log || !inst)
            return 0;
        const uint64_t ptag = ++next_ptag;
        fault_seqs.insert(inst->seqNum);
        LQ04Entry e;
        e.ptag = ptag;
        e.request_id = request_id;
        e.lq_idx = lq_idx;
        e.lq_gen = lq_gen;
        e.addr = addr;
        e.size = size;
        e.eligible_ordinal = eligible_ordinal;
        lq04_registry[inst->seqNum] = e;

        // The literal LQ04 field fault (plan-fixed detail fields): _valid
        // 1→0 and _request 1→0 — the request moved to the LQEntry side
        // channel, so it is neither freed nor reused early. Occupancy is
        // unchanged (no pop); address, size and response data are untouched.
        // corruptLifetime() asserts the before-state, so 1→0/1→0 is the
        // recorded real transition, not an assumption.
        std::ostringstream d;
        d << "site=executeLoad_post;family=lq04"
          << ";field=valid+request"
          << ";valid_before=1;valid_after=0"
          << ";request_before=1;request_after=0"
          << ";lq_idx=" << lq_idx
          << ";lq_gen=" << lq_gen
          << ";request_id=" << request_id
          << ";addr=" << std::hex << addr << std::dec
          << ";size=" << size
          << ";occ_before=" << occ_before
          << ";occ_after=" << occ_after
          << ";eligible_ordinal=" << eligible_ordinal
          << ";event_ordinal=" << event_ordinal
          << ";injected=" << injected
          << ";attempt_id=" << attempt_id
          << ";replay_gen=" << replay_gen
          << ";no_pop=1;no_reuse=1;data_unchanged=1";
        writeNode(ptag, "inj", inst->seqNum, true, request_id,
                  request_id != 0, addr, true, 0, false, 0, false, d.str());
        return ptag;
    }

    uint64_t
    CHAOSPropagation::noteA01EA(uint64_t ptag, const chaos_a01::EACoords &c)
    {
        // [LSU][V3.2.12][A01] the abort-survivable copy of the golden/actual EA
        // record. addr column = actual_ea so the existing mem_req/resp
        // range-match against the addr registry applies unchanged; golden_ea,
        // xor_delta, bit, access_size, request_va and fault_va ride in the
        // frozen detail (k=v;k=v, no commas — CSV last column).
        if (!write_log)
            return 0;
        writeNode(ptag, "a01_ea", c.dyn_inst_seq, true, 0, false,
                  c.actual_ea, true, 0, false, 0, false,
                  chaos_a01::eaDetail(c));
        auto &chain = a01_registry[c.dyn_inst_seq];
        chain.ptag = ptag;
        chain.coords = c;
        return ptag;
    }

    void
    CHAOSPropagation::noteA01FaultVA(uint64_t dyn_inst_seq, uint64_t fault_va)
    {
        // [LSU][V3.2.12][A01] complete the staged record with the raised fault
        // VA and re-emit as a01_fault (the formation-time a01_ea node stays in
        // the trace even when the run aborts before any exit callback; both
        // nodes carry the same frozen field set via recordFaultVA+eaDetail).
        auto it = a01_registry.find(dyn_inst_seq);
        if (it == a01_registry.end())
            return;
        chaos_a01::recordFaultVA(it->second.coords, fault_va);
        writeNode(it->second.ptag, "a01_fault", dyn_inst_seq, true, 0, false,
                  fault_va, true, 0, false, 0, false,
                  chaos_a01::eaDetail(it->second.coords));
    }

    void
    CHAOSPropagation::noteA01Consumed(uint64_t ptag,
                                      const chaos_a01::Consumed &c)
    {
        // [LSU][V3.2.12][A01] thin writer for the emit-once first-consumer
        // record; the emit-once guard (consumed_emitted) lives at the
        // noteCommit first-verified-consumer anchor. The emitted node is
        // identical to the plan's in-place writeNode call (same ptag, same
        // frozen consumedDetail — one formatter, no drift).
        if (!write_log)
            return;
        writeNode(ptag, "a01_consumed", c.dyn_inst_seq, true, 0, false,
                  0, false, 0, false, 0, false,
                  chaos_a01::consumedDetail(c));
    }

    void
    CHAOSPropagation::noteMD04Injection(o3::DynInst *inst,
                                        o3::DynInst *store_inst,
                                        const RequestPtr &load_req,
                                        Addr vaddr, unsigned size,
                                        uint64_t eligible_ordinal,
                                        uint64_t event_ordinal, uint64_t seed,
                                        bool load_complete)
    {
        if (!write_log || !inst)
            return;
        const uint64_t store_seq = store_inst ? store_inst->seqNum : 0;
        const uint64_t ptag = ++next_ptag;
        fault_seqs.insert(inst->seqNum);
        MD04Entry e;
        e.ptag = ptag;
        e.store_seq = store_seq;
        e.vaddr = vaddr;
        e.size = size;
        e.eligible_ordinal = eligible_ordinal;
        e.load_complete = load_complete;
        md04_registry[inst->seqNum] = e;

        // v3.2.7: explicit load-request identity so a cross-attempt response
        // can be linked to this injection by (seq, LQ entry, generation,
        // request_id) instead of a bare same-trace assumption.
        uint64_t load_request_id = 0;
        Tick request_tick = 0;
        if (load_req) {
            auto &rm = req_meta[load_req.get()];
            if (rm.request_id == 0)
                rm.request_id = ++next_request_id;
            if (rm.request_tick == 0)
                rm.request_tick = curTick();
            load_request_id = rm.request_id;
            request_tick = rm.request_tick;
        }
        e.request_id = load_request_id;
        md04_registry[inst->seqNum] = e;

        const uint64_t store_addr = store_inst ? store_inst->effAddr : 0;
        const unsigned store_size = store_inst ? store_inst->effSize : 0;
        const Addr store_pc = store_inst
            ? store_inst->pcState().instAddr() : 0;
        const Addr load_pc = inst->pcState().instAddr();
        const uint64_t sq_entry_id = store_inst ? (uint64_t)store_inst->sqIdx : 0;
        const uint64_t sq_gen = store_inst ? store_inst->sqEntryGeneration : 0;
        std::ostringstream tp;
        tp << "MD04-L" << inst->seqNum << "-S" << store_seq
           << "-T" << curTick();

        std::ostringstream d;
        d << "site=LSQUnit::checkViolations;family=md04;model=MD04"
          << ";definition=MD04-DEF-v2"
          << ";target_pair_id=" << tp.str()
          << ";load_seq=" << inst->seqNum
          << ";store_seq=" << store_seq
          << ";older_store_dyn_inst_seq=" << store_seq
          << ";younger_load_dyn_inst_seq=" << inst->seqNum
          << ";addr=0x" << std::hex << vaddr
          << ";load_addr=0x" << vaddr
          << ";store_addr=0x" << store_addr
          << ";load_pc=0x" << load_pc
          << ";store_pc=0x" << store_pc << std::dec
          << ";size=" << size
          << ";load_size=" << size
          << ";store_size=" << store_size
          << ";sq_entry_id=" << sq_entry_id
          << ";sq_entry_generation=" << sq_gen
          << ";violation_tick=" << curTick()
          << ";eligible_ordinal=" << eligible_ordinal
          << ";eligible_violation_pair_ordinal=" << eligible_ordinal
          << ";event_ordinal=" << event_ordinal
          << ";seed=" << seed
          << ";violation_report_suppressed=1"
          << ";address_modified=0;size_modified=0;data_modified=0"
          << ";load_complete=" << (load_complete ? 1 : 0)
          << ";load_lq_entry_id=" << inst->lqIdx
          << ";lq_entry_id=" << inst->lqIdx
          << ";load_entry_generation=" << inst->lqEntryGeneration
          << ";lq_entry_generation=" << inst->lqEntryGeneration
          << ";load_request_id=" << load_request_id
          << ";request_tick=" << request_tick
          << ";execution_attempt_id=" << inst->executionAttemptId
          << ";replay_generation=" << inst->replayGeneration
          << ";phys_regs=";
        for (int i = 0; i < (int)inst->numDestRegs(); ++i) {
            const PhysRegIdPtr p = inst->renamedDestIdx(i);
            if (p)
                d << (i ? "," : "") << regClassName(p->classValue())
                  << ":" << p->index();
        }
        writeNode(ptag, "inj_md04", inst->seqNum, true, load_request_id,
                  load_request_id != 0, vaddr, true,
                  0, false, 0, false, d.str());

        // The violation check runs at store execution; the load may already
        // have consumed its response. In that case the PRF already holds the
        // stale value: bind it late, explicitly labelled.
        if (!load_complete || !o3cpu || inst->getFault() != NoFault)
            return;
        for (int i = 0; i < (int)inst->numDestRegs(); ++i) {
            const PhysRegIdPtr phys = inst->renamedDestIdx(i);
            if (!phys)
                continue;
            uint64_t value = 0;
            unsigned bytes = 0;
            const std::string vhash = regValueHash(
                inst, phys, inst->threadNumber, &value, &bytes);
            if (vhash.empty())
                continue;
            std::ostringstream vb;
            vb << std::hex << value << std::dec;
            std::ostringstream wd;
            wd << "family=md04;late_binding=1;class="
               << regClassName(phys->classValue())
               << ";phys_reg=" << phys->index()
               << ";arch_reg=" << inst->destRegIdx(i).index()
               << ";writeback_value=" << vb.str()
               << ";writeback_value_fnv=" << vhash
               << ";source_value_hash=null;source_event_id=0"
               << ";load_seq=" << inst->seqNum
               << ";store_seq=" << store_seq
               << ";eligible_ordinal=" << eligible_ordinal
               << ";lq_entry_id=" << inst->lqIdx
               << ";entry_generation=" << inst->lqEntryGeneration
               << ";execution_attempt_id=" << inst->executionAttemptId
               << ";replay_generation=" << inst->replayGeneration
               << ";writeback_tick=" << curTick();
            const uint64_t wb_node = writeNode(
                ptag, "taint_reg", inst->seqNum, true, 0, false, vaddr, true,
                phys->index(), true, inst->destRegIdx(i).index(), true,
                wd.str());
            TaintEntry te;
            te.ptag = ptag;
            te.taintor_seq = inst->seqNum;
            te.node_id = wb_node;
            te.value_hash = vhash;
            taint_set[std::make_pair(phys->classValue(), phys->index())] = te;
        }
    }

    void
    CHAOSPropagation::noteReplay(o3::DynInst *inst, const char *reason)
    {
        if (!write_log || !inst)
            return;
        if (!replay_all && !fault_seqs.count(inst->seqNum))
            return;
        // A replayed instruction is trace-tracked from this point on, so its
        // final commit/squash can be recorded even when it never received a
        // fault (the replay mechanism pilot).
        replay_seqs.insert(inst->seqNum);
        // v3.2.12: per-seq replay counter feeding fw02_decision.replay_count.
        ++replay_count_by_seq[inst->seqNum];
        std::ostringstream d;
        d << "reason=" << reason
          << ";pc=" << std::hex << inst->pcState().instAddr() << std::dec
          << ";execution_attempt_id=" << inst->executionAttemptId
          << ";replay_generation=" << inst->replayGeneration
          << ";lq_entry_id=" << inst->lqIdx
          << ";sq_entry_id=" << inst->sqIdx
          << ";entry_generation="
          << (inst->isLoad() ? inst->lqEntryGeneration
                             : inst->sqEntryGeneration);
        writeNode(0, "replay", inst->seqNum, true, 0, false, 0, false,
                  0, false, 0, false, d.str());
    }

    void
    CHAOSPropagation::noteSquash(o3::DynInst *inst, const char *reason,
                                uint64_t triggering_seq)
    {
        if (!write_log || !inst)
            return;
        if (!replay_all && !fault_seqs.count(inst->seqNum))
            return;
        // v3.2.12 (task 9): the squash_reason record
        // {dyn_inst_seq, reason, triggering_seq}. triggering_seq is the
        // squash boundary (LSQUnit::squash(squashed_num)); 0 = the call
        // site did not record it (pre-wiring default) and the causality
        // verdict degrades to fault_victim_unproven per chaos_fw02 rules —
        // the squash is still recorded, never silently dropped.
        const bool fault_tracked = fault_seqs.count(inst->seqNum) != 0;
        const uint64_t fault_seq = fault_tracked ? inst->seqNum : 0;
        const chaos_fw02::SquashCause cause =
            chaos_fw02::classifySquash(inst->seqNum, triggering_seq,
                                       fault_seq);
        std::ostringstream d;
        d << "record=squash_reason"
          << ";dyn_inst_seq=" << inst->seqNum
          << ";reason=" << reason
          << ";triggering_seq=" << triggering_seq
          << ";triggering_seq_recorded=" << (triggering_seq != 0 ? 1 : 0)
          << ";fault_tracked=" << (fault_tracked ? 1 : 0)
          << ";squash_cause=" << chaos_fw02::squashCauseName(cause)
          << ";fault_caused="
          << (cause == chaos_fw02::SquashCause::FaultCaused ? 1 : 0)
          << ";pc=" << std::hex << inst->pcState().instAddr() << std::dec
          << ";execution_attempt_id=" << inst->executionAttemptId
          << ";replay_generation=" << inst->replayGeneration
          << ";lq_entry_id=" << inst->lqIdx
          << ";sq_entry_id=" << inst->sqIdx
          << ";entry_generation="
          << (inst->isLoad() ? inst->lqEntryGeneration
                             : inst->sqEntryGeneration);
        writeNode(0, "squash", inst->seqNum, true, 0, false, 0, false,
                  0, false, 0, false, d.str());
    }

    void
    CHAOSPropagation::noteForwarding(uint64_t ptag, uint64_t load_seq,
                                     uint64_t store_seq, Addr vaddr,
                                     unsigned size, const uint8_t *store_data,
                                     unsigned store_size,
                                     const uint8_t *fwd_data,
                                     unsigned fwd_size, bool suppressed,
                                     bool memory_path)
    {
        if (!write_log)
            return;
        // v3.2.4: a load that forwards from a registered faulted store joins
        // that store's chain. gem5's forwarding memcpy does not consult the
        // byte-enable, so a DA04-forwarded load receives the intended store
        // data; the detail records that boundary explicitly.
        if (ptag == 0)
            ptag = faultStorePtag(store_seq);
        const uint64_t store_hash = store_data
            ? fnv1a64(store_data, store_size) : 0;
        const uint64_t fwd_hash = fwd_data
            ? fnv1a64(fwd_data, fwd_size) : 0;
        std::ostringstream d;
        d << "unit=LSU;sub_unit=Store-to-Load Forwarding"
          << ";load_seq=" << load_seq
          << ";store_seq=" << store_seq
          << ";byte_begin=" << vaddr
          << ";byte_end=" << (vaddr + size)
          << ";size=" << size
          << ";store_data_fnv=" << std::hex << store_hash << std::dec
          << ";store_data_hex="
          << (store_data ? bytesToHex(store_data, store_size) : "null")
          << ";forward_data_fnv=" << std::hex << fwd_hash << std::dec
          << ";forward_data_hex="
          << (fwd_data ? bytesToHex(fwd_data, fwd_size) : "null")
          << ";decision=" << (suppressed ? "suppressed" : "forwarded")
          << ";normal_decision=forwarded"
          << ";fault_decision=" << (suppressed ? "suppressed" : "none")
          << ";fault_store_seq=" << store_seq
          << ";fault_store_family="
          << (fault_store_registry.count(store_seq)
                  ? fault_store_registry.at(store_seq).family : "none")
          << ";byte_enable_not_applied_in_forward="
          << (fault_store_registry.count(store_seq)
                  && std::string(fault_store_registry.at(store_seq).family)
                         == "byte_enable" ? 1 : 0)
          << ";store_data_forwarded="
          << (fault_store_registry.count(store_seq)
                  && std::string(fault_store_registry.at(store_seq).family)
                         == "store_data" ? 1 : 0)
          << ";memory_path=" << (memory_path ? 1 : 0);
        if (suppressed)
            fault_seqs.insert(load_seq);
        writeNode(ptag, "fwd", load_seq, true, 0, false, vaddr, true,
                  0, false, 0, false, d.str());
    }

    void
    CHAOSPropagation::noteFW02Decision(uint64_t ptag, uint64_t load_seq,
                                      uint64_t store_seq, Addr vaddr,
                                      unsigned size)
    {
        // v3.2.12 (task 9): the dedicated fw02_decision record. Read-only:
        // the decision was made by CHAOSLSQFwd; this node reports it with
        // the replay count of the suppressed load. memory_path=1 is a
        // property of the fault definition (a suppressed forward falls
        // through to the normal memory access, lsq_unit.cc read()).
        if (!write_log)
            return;
        std::ostringstream d;
        d << "record=fw02_decision;family=fw02;model=FW02"
          << ";load_seq=" << load_seq
          << ";store_seq=" << store_seq
          << ";normal_decision=" << chaos_fw02::normalDecision()
          << ";fault_decision=" << chaos_fw02::faultDecision(true)
          << ";memory_path=1"
          << ";replay_count=" << replayCount(load_seq)
          << ";vaddr=0x" << std::hex << vaddr << std::dec
          << ";size=" << size;
        writeNode(ptag, "fw02_decision", load_seq, true, 0, false,
                  vaddr, true, 0, false, 0, false, d.str());
    }

    uint64_t
    CHAOSPropagation::replayCount(uint64_t dyn_seq) const
    {
        auto it = replay_count_by_seq.find(dyn_seq);
        return it == replay_count_by_seq.end() ? 0 : it->second;
    }

    void
    CHAOSPropagation::noteCommit(ThreadID tid, o3::DynInst *head_inst)
    {
        if (!write_log || !head_inst)
            return;

        ++commit_seq;
        const uint64_t pc = head_inst->pcState().instAddr();

        // v3.2.12 (tasks 11/12/13): a registered fault store's own
        // architectural commit tick (sq03_effect.commit_tick /
        // sp05_stage.commit_tick; the sq01_chain store side has no tick
        // field but the same lookup keeps one code path).
        {
            auto fsi = fault_store_registry.find(head_inst->seqNum);
            if (fsi != fault_store_registry.end()
                    && fsi->second.store_commit_tick == 0)
                fsi->second.store_commit_tick = curTick();
        }

        // The fault instruction's own architectural commit is a real node.
        // For FW02 the suppressed load is registered in fault_seqs by
        // noteForwarding; A01/A03 faulting loads/stores are registered by
        // noteInjection.
        const bool fault_tracked = fault_seqs.count(head_inst->seqNum) != 0;
        const bool replay_tracked = replay_seqs.count(head_inst->seqNum) != 0;
        if (fault_tracked || replay_tracked) {
            std::ostringstream cd;
            cd << "trigger=fault_instruction_commit"
               << ";tracked=" << (fault_tracked ? "fault" : "replay")
               << ";pc=" << std::hex << pc << std::dec
               << ";commit_seq=" << commit_seq
               << ";execution_attempt_id=" << head_inst->executionAttemptId
               << ";replay_generation=" << head_inst->replayGeneration
               << ";is_load=" << (head_inst->isLoad() ? 1 : 0)
               << ";is_store=" << (head_inst->isStore() ? 1 : 0);
            writeNode(0, "commit", head_inst->seqNum, true, 0, false,
                      0, false, 0, false, 0, false, cd.str());
        }

        uint64_t first_consumed_ptag = 0;
        uint64_t last_consumer_node = 0;
        std::string last_consumer_hash;
        std::string first_consumer_input_hash;
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

            uint64_t ival = 0, oval = 0;
            unsigned ibytes = 0, obytes = 0;
            const std::string ihash =
                regValueHash(head_inst, phys, tid, &ival, &ibytes);
            const bool input_matches =
                !ihash.empty() && !it->second.value_hash.empty()
                && ihash == it->second.value_hash;

            // v3.2.5.1: only a value-identical operand is a real consumer
            // edge. A stale taint (phys-reg recycling, a later writer) or a
            // non-scalar (unhashable) operand is a diagnostic, never an edge,
            // and must not re-taint the destination.
            if (!input_matches) {
                std::ostringstream md;
                md << "class=" << regClassName(phys->classValue())
                   << ";src_idx=" << i << ";pc=" << std::hex << pc << std::dec
                   << ";source_event_id=" << it->second.node_id
                   << ";source_value_hash="
                   << (it->second.value_hash.empty() ? "null"
                                                     : it->second.value_hash)
                   << ";consumer_input_value=" << std::hex << ival << std::dec
                   << ";consumer_input_fnv="
                   << (ihash.empty() ? "null" : ihash)
                   << ";consumer_input_bytes=" << ibytes
                   << ";reason="
                   << (ihash.empty() || it->second.value_hash.empty()
                           ? "hash_unavailable" : "hash_mismatch")
                   << ";phys_reg=" << phys->index()
                   << ";arch_reg=" << head_inst->srcRegIdx(i).index()
                   << ";commit_seq=" << commit_seq
                   << ";execution_attempt_id=" << head_inst->executionAttemptId
                   << ";replay_generation=" << head_inst->replayGeneration;
                writeNode(it->second.ptag, "taint_value_mismatch",
                          head_inst->seqNum, true, 0, false, 0, false,
                          phys->index(), true,
                          head_inst->srcRegIdx(i).index(), true, md.str());
                continue;
            }

            any_consumer = true;
            if (!first_consumed_ptag)
                first_consumed_ptag = it->second.ptag;
            // v3.2.12: the FIRST verified consumer edge's input hash — the
            // consumer_hash of the consolidated chain record (§3: the
            // verified edge's input hash equals the producer's writeback).
            if (first_consumer_input_hash.empty())
                first_consumer_input_hash = ihash;

            // [LSU][V3.2.12][A01] a01_consumed: emit once per A01 chain at
            // the FIRST verified consumer. dyn_inst_seq = the taintor (the
            // faulted load), consumer_seq = this committing instruction;
            // input_hash = the verified edge's ihash (the same platform
            // FNV the taint entry carries — no second hash).
            {
                auto a01 = a01_registry.find(it->second.taintor_seq);
                if (a01 != a01_registry.end()
                        && !a01->second.consumed_emitted) {
                    chaos_a01::Consumed k;
                    k.dyn_inst_seq = it->second.taintor_seq;
                    k.consumer_seq = head_inst->seqNum;
                    k.consumer_kind = chaos_a01::ConsumerKind::RegisterSource;
                    // regValueHash returns lowercase bare hex (fnvHex);
                    // a verified edge guarantees it is non-empty.
                    k.input_hash = std::stoull(ihash, nullptr, 16);
                    noteA01Consumed(a01->second.ptag, k);
                    a01->second.consumed_emitted = true;
                }
            }

            std::string ohash;
            uint64_t out_phys = 0, out_arch = 0;
            if (head_inst->numDestRegs() > 0) {
                const PhysRegIdPtr dphys = head_inst->renamedDestIdx(0);
                if (dphys) {
                    ohash = regValueHash(head_inst, dphys, tid, &oval,
                                         &obytes);
                    out_phys = dphys->index();
                    out_arch = head_inst->destRegIdx(0).index();
                }
            }

            std::ostringstream d;
            d << "class=" << regClassName(phys->classValue())
              << ";src_idx=" << i << ";pc=" << std::hex << pc << std::dec
              << ";source_event_id=" << it->second.node_id
              << ";source_value_hash=" << it->second.value_hash
              << ";consumer_input_value=" << std::hex << ival << std::dec
              << ";consumer_input_fnv=" << ihash
              << ";consumer_input_bytes=" << ibytes
              << ";consumer_output_value=" << std::hex << oval << std::dec
              << ";consumer_output_fnv=" << (ohash.empty() ? "null" : ohash)
              << ";consumer_output_bytes=" << obytes
              << ";consumer_input_matches_source=1"
              << ";dest_phys_reg=" << out_phys
              << ";dest_arch_reg=" << out_arch
              << ";commit_seq=" << commit_seq
              << ";execution_attempt_id=" << head_inst->executionAttemptId
              << ";replay_generation=" << head_inst->replayGeneration;
            const uint64_t consumer_node = writeNode(
                it->second.ptag, "consumer", head_inst->seqNum, true,
                0, false, 0, false, phys->index(), true,
                head_inst->srcRegIdx(i).index(), true, d.str());
            last_consumer_node = consumer_node;
            last_consumer_hash = ohash;
            writeEdgeRow(it->second.ptag, it->second.node_id, consumer_node,
                         it->second.taintor_seq, head_inst->seqNum,
                         it->second.value_hash, ohash, "register_dataflow");
        }

        // v3.2.12 (tasks 11/12/13): the FIRST verified consumer edge on a
        // registered fault store's chain closes the consolidated record
        // (sq01_chain / sq03_effect / sp05_stage) with the consumer hash
        // filled. A chain that never closes is emitted by the exit callback
        // with the honest absent fields.
        if (any_consumer) {
            FaultStoreEntry *fe = faultStoreByPtag(first_consumed_ptag);
            if (fe && !fe->chain_record_emitted) {
                fe->consumer_seq = head_inst->seqNum;
                fe->consumer_hash = first_consumer_input_hash;
                emitChainRecord(fe->dyn_seq);
            }
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
              << ";pc=" << std::hex << pc << std::dec
              << ";commit_seq=" << commit_seq;
            writeNode(ptag, "errant_commit", head_inst->seqNum, true,
                      0, false, 0, false, 0, false, 0, false, d.str());
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
                te.node_id = last_consumer_node;
                // The destination now holds the consumer's OUTPUT value; the
                // next consumer's input hash must match THIS hash.
                te.value_hash = last_consumer_hash;
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

    // ---------------------------------------------- v3.2.12 chain records
    // Consolidated read-only records for the SQ01/SQ03/SP05 closure round
    // (tasks 11/12/13). Each record assembles, from the registries the
    // tracer itself observed, the brief-defined field set:
    //   sq01_chain  {store_seq, sq_idx, gen, data_before, data_after,
    //                mem_write_hash, reload_seq, reload_data_hash,
    //                consumer_hash}
    //   sq03_effect {sq_idx, gen, canwb_before, canwb_after, writeback_tick,
    //                drain_tick, reload_seq, reload_data_hash,
    //                resource_reuse_tick}
    //   sp05_stage  {store_seq, completion_tick, commit_tick, writeback_tick,
    //                drain_tick, reload_seq, reload_data_hash, data_correct}
    // The verdict mapping is the pure host-tested rule (sq01_rules.hh /
    // sq03_rules.hh / sp05_rules.hh) — never ad hoc string assembly.

    auto
    CHAOSPropagation::faultStoreByPtag(uint64_t ptag) -> FaultStoreEntry *
    {
        for (auto &kv : fault_store_registry)
            if (kv.second.ptag == ptag)
                return &kv.second;
        return nullptr;
    }

    void
    CHAOSPropagation::emitChainRecord(uint64_t dyn_seq)
    {
        auto it = fault_store_registry.find(dyn_seq);
        if (it == fault_store_registry.end())
            return;
        FaultStoreEntry &e = it->second;
        const std::string family(e.family);
        if (family != "store_data" && family != "sq03_canwb"
                && family != "sp05_complete")
            return;   // DA04 keeps its own audit records; nothing else here
        if (e.chain_record_emitted)
            return;
        e.chain_record_emitted = true;

        const std::string mem_hash = e.data_fnv.empty() ? "null" : e.data_fnv;
        const std::string reload_hash = e.reload_seq != 0
            ? (e.reload_hash.empty() ? "null" : e.reload_hash) : "null";
        const std::string consumer_hash = e.consumer_seq != 0
            ? (e.consumer_hash.empty() ? "null" : e.consumer_hash) : "null";

        if (family == "store_data") {
            chaos_sq01::Sq01Chain c;
            c.data_before = e.data_byte_before;
            c.data_after = e.data_byte_after;
            c.mem_write_hash = e.data_fnv;
            c.reload_seq = e.reload_seq;
            c.reload_data_hash = e.reload_seq ? e.reload_hash : "";
            c.consumer_hash = e.consumer_seq ? e.consumer_hash : "";
            const chaos_sq01::ChainVerdict v = chaos_sq01::grade(c);
            std::ostringstream d;
            d << "record=sq01_chain;family=store_data;model=SQ01"
              << ";store_seq=" << e.dyn_seq
              << ";sq_idx=" << e.idx
              << ";gen=" << e.gen
              << ";data_before=0x" << std::hex << (unsigned)c.data_before
              << ";data_after=0x" << (unsigned)c.data_after << std::dec
              << ";data_diverged=" << (c.data_after != c.data_before ? 1 : 0)
              << ";mem_write_hash=" << mem_hash
              << ";reload_seq=" << e.reload_seq
              << ";reload_data_hash=" << reload_hash
              << ";consumer_seq=" << e.consumer_seq
              << ";consumer_hash=" << consumer_hash
              << ";chain_verdict=" << chaos_sq01::verdictName(v);
            writeNode(e.ptag, "sq01_chain", e.dyn_seq, true, 0, false,
                      e.base, true, 0, false, 0, false, d.str());
            return;
        }

        if (family == "sq03_canwb") {
            auto sit = sq03_registry.find(dyn_seq);
            const bool have_sq03 = sit != sq03_registry.end();
            chaos_sq03::Sq03Effect eff;
            eff.canwb_before = have_sq03 && sit->second.canwb_before;
            eff.canwb_after = have_sq03 && sit->second.canwb_after;
            eff.writeback_tick = have_sq03 ? (uint64_t)sit->second.wb_tick : 0;
            eff.drain_tick = (uint64_t)e.written_tick;
            eff.commit_tick = (uint64_t)e.store_commit_tick;
            eff.reload_seq = e.reload_seq;
            eff.reload_data_hash = e.reload_seq ? e.reload_hash : "";
            const chaos_sq03::EffectOutcome o = chaos_sq03::effectVerdict(eff);
            std::ostringstream d;
            d << "record=sq03_effect;family=sq03_canwb;model=SQ03"
              << ";store_seq=" << e.dyn_seq
              << ";sq_idx=" << e.idx
              << ";gen=" << e.gen
              << ";canwb_before=" << (eff.canwb_before ? 1 : 0)
              << ";canwb_after=" << (eff.canwb_after ? 1 : 0)
              << ";canwb_state_changed="
              << (chaos_sq03::stateChanged(eff) ? 1 : 0)
              << ";writeback_tick=" << eff.writeback_tick
              << ";drain_tick=" << eff.drain_tick
              << ";commit_tick=" << eff.commit_tick
              << ";resource_reuse_tick=" << (uint64_t)e.resource_reuse_tick
              << ";reload_seq=" << e.reload_seq
              << ";reload_data_hash=" << reload_hash
              << ";visible_before_commit="
              << (chaos_sq03::visibleBeforeCommit(eff) ? 1 : 0)
              << ";phantom_drain="
              << (chaos_sq03::phantomDrain(eff) ? 1 : 0)
              << ";effect_outcome=" << chaos_sq03::effectOutcomeName(o)
              << ";effect_reason=" << chaos_sq03::effectReason(o);
            writeNode(e.ptag, "sq03_effect", e.dyn_seq, true, 0, false,
                      e.base, true, 0, false, 0, false, d.str());
            return;
        }

        // family == "sp05_complete"
        chaos_sp05::Sp05Stage st;
        st.completion_tick = (uint64_t)e.complete_tick;
        st.commit_tick = (uint64_t)e.store_commit_tick;
        st.writeback_tick = (uint64_t)e.registered;
        st.drain_tick = (uint64_t)e.written_tick;
        st.reload_seq = e.reload_seq;
        st.store_data_hash = e.data_fnv;
        st.reload_data_hash = e.reload_seq ? e.reload_hash : "";
        const chaos_sp05::StageOutcome o = chaos_sp05::stageVerdict(st);
        const char *data_correct = "null";
        if (o == chaos_sp05::StageOutcome::MASKED_DATA_WRITTEN_CORRECTLY)
            data_correct = "1";
        else if (o == chaos_sp05::StageOutcome::CHAIN_VISIBILITY_LOST)
            data_correct = "0";
        std::ostringstream d;
        d << "record=sp05_stage;family=sp05_complete;model=SP05"
          << ";store_seq=" << e.dyn_seq
          << ";sq_idx=" << e.idx
          << ";gen=" << e.gen
          << ";completion_tick=" << st.completion_tick
          << ";commit_tick=" << st.commit_tick
          << ";writeback_tick=" << st.writeback_tick
          << ";drain_tick=" << st.drain_tick
          << ";write_skipped=" << (chaos_sp05::writeSkipped(st) ? 1 : 0)
          << ";reload_seq=" << e.reload_seq
          << ";reload_data_hash=" << reload_hash
          // store_data_fnv stays null until the shared-file request
          // (noteSP05Injection needs the SQ entry's bytes) is wired;
          // data_correct honestly follows (null = unknown).
          << ";store_data_fnv="
          << (e.data_fnv.empty() ? "null" : e.data_fnv)
          << ";data_correct=" << data_correct
          << ";stage_outcome=" << chaos_sp05::stageOutcomeName(o)
          << ";masking_mechanism=" << chaos_sp05::maskingMechanism(o);
        writeNode(e.ptag, "sp05_stage", e.dyn_seq, true, 0, false,
                  e.base, true, 0, false, 0, false, d.str());
    }

    void
    CHAOSPropagation::writeDeferredChainRecords()
    {
        if (!write_log || !gz_file)
            return;
        for (auto &kv : fault_store_registry) {
            const std::string family(kv.second.family);
            if (family != "store_data" && family != "sq03_canwb"
                    && family != "sp05_complete")
                continue;
            if (!kv.second.chain_record_emitted)
                emitChainRecord(kv.first);
        }
    }

} // namespace gem5
