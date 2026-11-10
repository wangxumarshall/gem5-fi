#ifndef __CPU_O3_CHAOS_ADDR_PATH_A01_COORDS_HH__
#define __CPU_O3_CHAOS_ADDR_PATH_A01_COORDS_HH__

// [LSU][V3.2.12][A01] golden/actual EA coordinate math and the read-only
// trace-record shapes for the A01 propagation evidence (plan Task 7,
// LSU_Propagation_Acceptance_Standard_v3.2.12.md).
//
// PURE HEADER: no gem5 types (only <cstdint>/<string>/<sstream>), so the
// host unit test tests/test_addrpath_a01_coords.cc compiles it with plain
// g++ -O2 -std=c++17 -I CHAOS/gem5/src (the chaos_da04 precedent).
//
// WHAT THIS CLOSES: the v3.2.11 audit's A01 verdict was PARTIAL because
// "the trace has no reference value for the correct address, so it cannot
// prove the delivered value differs, and the crashes are not attributable".
// The a01_ea record carries BOTH coordinates — golden_ea (where the load
// should have read) and actual_ea (where it did read) — plus the raised
// fault VA, so a control run's response at golden_ea can be compared with
// the fault run's response at actual_ea for the same dyn_inst_seq, and a
// crash is attributable when fault_va matches (standard section 1.6 CRASH).
//
// WRITER DISCIPLINE: CHAOSPropagation is the SINGLE prop-trace writer
// (per-node Z_SYNC_FLUSH CSV nodes, the only abort-survivable copy). This
// header only computes + FORMATS the records; CHAOSAddrPath stages them at
// EA formation and the sink side emits them (task-7-report.md records the
// exact sink-side contract). The detail builders below freeze the field
// format in ONE place so the injection-log copy and the prop-trace node can
// never drift (detail dialect per CHAOSPropagation.hh: "k=v;k=v" fields,
// NO commas; addresses bare lowercase hex, counts decimal; absent values
// are the literal NOT_APPLICABLE, never silent zeros).
//
// IDENTITY (standard section 2): the record's dyn_inst_seq is the faulting
// DynInst::seqNum — the identity the addr registry and the commit-side
// chain join on. fault_id is the injector's 1-based fault ordinal at
// formation; the sink side joins the record to its chain ptag by
// dyn_inst_seq (a fresh ptag is allocated sink-side per injection).
// input_hash is the SAME FNV-1a-64 the taint set carries (the platform's
// fnv1a64 of the consumer's source value) — this header defines NO second
// hash (one classifier, no drift).

#include <cstdint>
#include <sstream>
#include <string>

namespace gem5
{
namespace chaos_a01
{

// bit index sentinel: no single-bit identity (masked / no-op application).
constexpr int kNoBit = -1;
// pc sentinel: the observing hook cannot see the faulting PC (the PRE
// hook receives dyn_inst_seq only; see task-7-report.md for the proposed
// call-site pass-through). Never fabricated.
constexpr uint64_t kPcUnknown = 0;

// a01_ea record: the golden/actual EA coordinates of one A01 fault,
// observed at EA formation and completed with the raised fault VA while
// the corrupted request is in flight.
struct EACoords {
    uint64_t fault_id = 0;      // injector fault ordinal (1-based)
    uint64_t dyn_inst_seq = 0;  // faulting DynInst::seqNum (chain identity)
    uint64_t pc = kPcUnknown;   // faulting PC (kPcUnknown = not observable)
    uint64_t golden_ea = 0;     // correct EA (pre-corruption)
    uint64_t actual_ea = 0;     // corrupted EA (post-corruption)
    uint64_t xor_delta = 0;     // golden_ea ^ actual_ea
    int bit = kNoBit;           // flipped bit index (kNoBit = not single-bit)
    unsigned access_size = 0;   // access size as pushed at EA formation
    uint64_t request_va = 0;    // VA of the corrupted Request (the identity
                                // the downstream mem_req node re-observes)
    bool fault_raised = false;  // fault raised while request in flight
    uint64_t fault_va = 0;      // raised fault VA (valid iff fault_raised)
};

// a01_consumed record: the FIRST committed consumer of the tainted
// destination register (standard section 3 data rule: the consumer edge is
// verified when consumer input hash equals the producer writeback hash).
enum class ConsumerKind : int {
    Unknown = 0,        // not yet classified
    RegisterSource = 1  // committed inst read the tainted phys reg
};

inline const char *
consumerKindName(ConsumerKind k)
{
    return (k == ConsumerKind::RegisterSource) ? "register_source" : "unknown";
}

struct Consumed {
    uint64_t dyn_inst_seq = 0;   // the tainted load's seqNum
    uint64_t consumer_seq = 0;   // first consumer's DynInst::seqNum
    ConsumerKind consumer_kind = ConsumerKind::Unknown;
    uint64_t input_hash = 0;    // platform fnv1a64 of the consumer's source
                                // value (hex-formatted; never re-hashed here)
};

// ---- pure coordinate math -------------------------------------------------

inline uint64_t
xorDelta(uint64_t golden_ea, uint64_t actual_ea)
{
    return golden_ea ^ actual_ea;
}

// A01 single-bit flip: actual = golden ^ (1 << bit).
inline uint64_t
applyBitFlip(uint64_t golden_ea, int bit)
{
    return golden_ea ^ (1ULL << bit);
}

// The single flipped bit index of a delta; kNoBit unless exactly one bit
// is set (an XOR flip always sets exactly one; a no-op sets none).
inline int
singleBitIndex(uint64_t delta)
{
    if (delta == 0 || (delta & (delta - 1)) != 0)
        return kNoBit;
    int bit = 0;
    while ((delta >> bit) != 1)
        ++bit;
    return bit;
}

// Number of EA bits the fault affected (the no-op rule: affected == 0).
inline unsigned
affectedBits(uint64_t delta)
{
    unsigned n = 0;
    while (delta) {
        n += (unsigned)(delta & 1);
        delta >>= 1;
    }
    return n;
}

// a01_ea at EA formation for a known single-bit flip (the a01_bit3_load PRE
// hook, bit fixed at 3; the A01Bit post hook with its sampled band bit).
// fault_va is NOT_APPLICABLE at formation: no fault is raised yet.
inline EACoords
eaCoordsForFlip(uint64_t fault_id, uint64_t dyn_inst_seq, uint64_t pc,
                uint64_t golden_ea, int bit, unsigned access_size)
{
    EACoords c;
    c.fault_id = fault_id;
    c.dyn_inst_seq = dyn_inst_seq;
    c.pc = pc;
    c.golden_ea = golden_ea;
    c.actual_ea = applyBitFlip(golden_ea, bit);
    c.xor_delta = xorDelta(c.golden_ea, c.actual_ea);
    c.bit = bit;
    c.access_size = access_size;
    c.request_va = c.actual_ea;
    c.fault_raised = false;
    c.fault_va = 0;
    return c;
}

// a01_ea for a masked / no-op application: the condition was applied but
// the EA did not change (xor_delta == 0, affected == 0, no bit identity).
inline EACoords
eaCoordsNoop(uint64_t fault_id, uint64_t dyn_inst_seq, uint64_t pc,
             uint64_t golden_ea, unsigned access_size)
{
    EACoords c;
    c.fault_id = fault_id;
    c.dyn_inst_seq = dyn_inst_seq;
    c.pc = pc;
    c.golden_ea = golden_ea;
    c.actual_ea = golden_ea;
    c.xor_delta = 0;
    c.bit = kNoBit;
    c.access_size = access_size;
    c.request_va = golden_ea;
    c.fault_raised = false;
    c.fault_va = 0;
    return c;
}

// a01_ea from an observed golden/actual pair (bit identity derived from the
// delta; kNoBit when the pair differs by zero or multiple bits).
inline EACoords
eaCoordsFromPair(uint64_t fault_id, uint64_t dyn_inst_seq, uint64_t pc,
                 uint64_t golden_ea, uint64_t actual_ea, unsigned access_size)
{
    EACoords c;
    c.fault_id = fault_id;
    c.dyn_inst_seq = dyn_inst_seq;
    c.pc = pc;
    c.golden_ea = golden_ea;
    c.actual_ea = actual_ea;
    c.xor_delta = xorDelta(golden_ea, actual_ea);
    c.bit = singleBitIndex(c.xor_delta);
    c.access_size = access_size;
    c.request_va = actual_ea;
    c.fault_raised = false;
    c.fault_va = 0;
    return c;
}

// Sink-side completion: a fault was raised while the corrupted request was
// in flight, at fault_va (lsq.cc read()/write() fault landing site).
inline void
recordFaultVA(EACoords &c, uint64_t fault_va)
{
    c.fault_raised = true;
    c.fault_va = fault_va;
}

// ---- frozen detail formatting (single format, no drift) -------------------

inline std::string
toHexField(uint64_t v)
{
    std::ostringstream os;
    os << std::hex << v;
    return os.str();
}

// a01_ea detail: exactly the task-7 record fields (fault_id, dyn_inst_seq,
// pc, golden_ea, actual_ea, xor_delta, bit, access_size) plus the affected
// count, the corrupted request VA and the raised fault VA. Addresses and
// the xor mask are bare lowercase hex; counts are decimal; bit and fault_va
// carry the literal NOT_APPLICABLE when they have no value.
inline std::string
eaDetail(const EACoords &c)
{
    std::ostringstream d;
    d << "fault_id=" << c.fault_id
      << ";dyn_inst_seq=" << c.dyn_inst_seq
      << ";pc=" << toHexField(c.pc)
      << ";golden_ea=" << toHexField(c.golden_ea)
      << ";actual_ea=" << toHexField(c.actual_ea)
      << ";xor_delta=" << toHexField(c.xor_delta)
      << ";bit=" << (c.bit == kNoBit ? "NOT_APPLICABLE"
                                     : std::to_string(c.bit))
      << ";access_size=" << c.access_size
      << ";affected=" << affectedBits(c.xor_delta)
      << ";request_va=" << toHexField(c.request_va)
      << ";fault_va=";
    if (c.fault_raised)
        d << toHexField(c.fault_va);
    else
        d << "NOT_APPLICABLE";
    return d.str();
}

// a01_consumed detail: the first-consumer edge record.
inline std::string
consumedDetail(const Consumed &c)
{
    std::ostringstream d;
    d << "dyn_inst_seq=" << c.dyn_inst_seq
      << ";consumer_seq=" << c.consumer_seq
      << ";consumer_kind=" << consumerKindName(c.consumer_kind)
      << ";input_hash=" << toHexField(c.input_hash);
    return d.str();
}

} // namespace chaos_a01
} // namespace gem5

#endif // __CPU_O3_CHAOS_ADDR_PATH_A01_COORDS_HH__
