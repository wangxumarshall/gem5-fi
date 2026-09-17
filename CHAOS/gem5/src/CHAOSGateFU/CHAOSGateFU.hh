/*
 * CHAOSGateFU — synthetic gate-level netlist FU fault injector (Task 5.3).
 * See CHAOSGateFU.py for the fault-model contract (the paper's gate-level
 * stuck-at protocol; gem5 has no RTL, so the datapath is a synthesized
 * structural netlist — an honest approximation, documented).
 *
 * Netlist model: a gate is (type, fanin0, fanin1) with types
 *   AND, OR, XOR  (two-input), and NOT (fanin1 unused).
 * Gates are numbered 0..N-1 in synthesis order; PIs are implicit
 * (negative ids index the primary-input vector). Stuck-at forces the
 * OUTPUT of gate `targetGate` to `stuckPolarity` before its fanouts
 * consume it — a faithful structural stuck-at.
 *
 * Synthesis:
 *  - Kogge-Stone 64b adder (IntAlu): a sparse-cell prefix network; gate
 *    count ~2k. The netlist computes a+b; the injector feeds the op's two
 *    source operands as PIs and replaces the writeback value.
 *  - Shift-add 64x64 multiplier (IntMult): 64 partial products AND-gated
 *    and summed through 63 adder instances (each a Kogge-Stone cell set).
 */
#ifndef __CHAOS_GATE_FU_CHAOSGATEFU_HH__
#define __CHAOS_GATE_FU_CHAOSGATEFU_HH__

#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"

#include <cstdint>
#include <vector>

namespace gem5
{

class CHAOSGateFUParams;
namespace o3 { class CPU; class DynInst; }

class CHAOSGateFU : public SimObject
{
  public:
    CHAOSGateFU(const CHAOSGateFUParams &p);
    ~CHAOSGateFU() override;

    static CHAOSGateFU *instance;

    // Oracle: recompute the op of `op_class` through the faulted netlist,
    // sourcing operands from the issuing instruction. Returns false (and
    // leaves `result` untouched) when this injector does not apply.
    bool evaluate(int op_class, o3::DynInst *inst, uint64_t &result);

    // Netlist introspection for stats/logging.
    unsigned numGates() const { return gates.size(); }

    // Gate-level primitives (public: unit-testable without SimObject).
    enum GateType { AND = 0, OR = 1, XOR = 2, NOT = 3 };
    struct Gate
    {
        GateType type;
        int in0;    // gate index, or -(pi_index+1) for primary input
        int in1;
    };
    // Evaluate the netlist on `pis`, with gate `stuck_gate` forced to
    // `stuck_val` (-1 = none). Returns the PO vector (bit i = gate
    // po_gates[i]).
    std::vector<bool> evalNet(const std::vector<bool> &pis,
                              int stuck_gate, int stuck_val) const;
    void synthesizeAdder(int width);          // Kogge-Stone
    void synthesizeMultiplier(int width);     // shift-add array
    int synthGate(GateType t, int in0, int in1);
    // Map: PI bit index -> meaning is documented per netlist (a bits,
    // then b bits; PIs: a[0..w-1], b[w..2w-1]).
    std::vector<Gate> gates;
    std::vector<int> po_gates;                // output bit i <- gate po[i]
    unsigned pi_width = 0;

  public:
    // oracle-facing state
    int target_opclass = -1;
    int stuck_gate = -1;
    int stuck_val = 1;
    uint64_t first_clock = 0;
    o3::CPU *cpu = nullptr;
    bool write_log = true;
    OutputStream *log_stream = nullptr;
    uint64_t eval_count = 0;
    uint64_t diff_count = 0;    // netlist output != architectural value

  protected:
    struct Stats : public statistics::Group
    {
        Stats(statistics::Group *parent);
        statistics::Scalar numEvals;
        statistics::Scalar numDiffs;
        statistics::Scalar numGates;
    } stats;
};

// Guard + oracle used by cpu/o3/dyn_inst.hh setRegOperand (Task 5.3).
// The oracle receives the issuing DynInst so it can read the two integer
// source operands (renamedSrcIdx -> cpu->getReg) and recompute the
// result through the faulted netlist.
namespace o3 { class DynInst; }
extern bool gatefu_enabled;
bool gatefu_evaluate(int op_class, o3::DynInst *inst, uint64_t &result);

} // namespace gem5

#endif // __CHAOS_GATE_FU_CHAOSGATEFU_HH__
