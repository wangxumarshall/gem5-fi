/*
 * CHAOSGateFU — synthetic gate-level netlist FU fault injector (Task 5.3).
 * Implementation: netlist synthesis (Kogge-Stone adder / shift-add
 * multiplier), structural stuck-at evaluation, and the writeback oracle.
 */
#include "CHAOSGateFU/CHAOSGateFU.hh"
#include "params/CHAOSGateFU.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/dyn_inst.hh"
#include "cpu/o3/dyn_inst_ptr.hh"
#include "enums/OpClass.hh"
#include "base/trace.hh"

#include <iostream>

namespace gem5
{

CHAOSGateFU *CHAOSGateFU::instance = nullptr;
bool gatefu_enabled = false;

// ---------------------------------------------------------------------------
// Netlist synthesis
// ---------------------------------------------------------------------------
// Helper adders on the flat gate list. PI encoding (pi_width = 2*w):
//   PI[i]        = a[i]   (i < w)
//   PI[w + j]    = b[j]
// Returns the gate index producing the sum/output bit.

int
CHAOSGateFU::synthGate(GateType t, int in0, int in1)
{
    gates.push_back({t, in0, in1});
    return (int)gates.size() - 1;
}

// Kogge-Stone prefix adder: standard sparse structure.
//   p[i] = a XOR b, g[i] = a AND b  (preprocess)
//   prefix: (g,p) o (G,P) = (g OR (p AND G), p AND P)
//   sum[i] = p[i] XOR carry[i-1]; carry[i] = g-prefix[i]
void
CHAOSGateFU::synthesizeAdder(int width)
{
    gates.clear();
    po_gates.clear();
    pi_width = 2 * width;
    // bit slices of intermediates, indexed [level][bit]
    std::vector<std::vector<int>> p(width), g(width);

    // Preprocess.
    for (int i = 0; i < width; i++) {
        int ai = -(i + 1);              // PI a[i]
        int bi = -(width + i + 1);      // PI b[i]
        p[i].push_back(synthGate(XOR, ai, bi));
        g[i].push_back(synthGate(AND, ai, bi));
    }
    // Prefix network (Kogge-Stone: distances 1,2,4,...).
    int level = 0;
    for (int d = 1; d < width; d <<= 1) {
        std::vector<int> np(width), ng(width);
        for (int i = 0; i < width; i++) {
            int pv = p[i].back(), gv = g[i].back();
            if (i - d >= 0) {
                int pg = p[i - d].back(), gg = g[i - d].back();
                int pand = synthGate(AND, pv, gg);      // p & G
                int gor  = synthGate(OR, gv, pand);      // g | (p & G)
                int pandp = synthGate(AND, pv, pg);      // p & P
                np[i] = pandp;
                ng[i] = gor;
            } else {
                np[i] = pv;
                ng[i] = gv;
            }
        }
        for (int i = 0; i < width; i++) {
            p[i].push_back(np[i]);
            g[i].push_back(ng[i]);
        }
        level++;
    }
    // Sum: sum[i] = p[i] XOR c[i-1], c[i-1] = g[i-1] (final prefix),
    // sum[0] = p[0]. Carry-out = g[width-1] (bit `width` of the PO).
    // sum[i] = p0[i] XOR carry[i-1]: p0 is the PREPROCESS propagate bit
    // (level 0), NOT the final prefix p — the standalone exhaustive tests
    // (W=4/8/12, 17M vectors) caught this.
    for (int i = 0; i < width; i++) {
        if (i == 0) {
            po_gates.push_back(p[0].front());
        } else {
            po_gates.push_back(synthGate(XOR, p[i].front(), g[i - 1].back()));
        }
    }
    // Carry-out as an extra PO (bit `width`); width+1 outputs total.
    po_gates.push_back(g[width - 1].back());
}

// Shift-add array multiplier, clean version.
// acc bits are represented as (gate_index, valid); a fresh AND-tied-to-0
// constant gate stands in for "bit is constant zero" so NO sentinel index
// is ever used (the earlier -1 sentinel collided with the PI encoding
// in0<0 -> PI, corrupting the netlist — equivalence test crashed).
// Structure: pp[i][j] = a[j] & b[i]; then 63 ripple adder rows
// accumulate (pp[i] << i). Each full adder is XOR/AND/OR primitives.
void
CHAOSGateFU::synthesizeMultiplier(int width)
{
    gates.clear();
    po_gates.clear();
    pi_width = 2 * width;
    auto PI = [&](int idx) { return -(idx + 1); };

    // Partial products.
    std::vector<std::vector<int>> pp(width, std::vector<int>(width));
    for (int i = 0; i < width; i++)
        for (int j = 0; j < width; j++)
            pp[i][j] = synthGate(AND, PI(j), PI(width + i));

    // Constant-zero gate: a[0] AND NOT a[0].
    int not_a0 = synthGate(NOT, PI(0), PI(0));
    int const0 = synthGate(AND, PI(0), not_a0);

    // Initial accumulator: row 0 (value = pp[0] << 0), 2w bits.
    std::vector<int> acc(2 * width, const0);
    for (int j = 0; j < width; j++)
        acc[j] = pp[0][j];

    // Ripple accumulation of rows 1..w-1.
    for (int i = 1; i < width; i++) {
        std::vector<int> sum(2 * width);
        int carry = const0;
        for (int k = 0; k < 2 * width; k++) {
            int x = acc[k];
            int j = k - i;                      // row contributes at bit k
            int y = (0 <= j && j < width) ? pp[i][j] : const0;
            int xyc = synthGate(XOR, x, y);       // x ^ y
            int xy  = synthGate(AND, x, y);       // x & y
            sum[k] = synthGate(XOR, xyc, carry);  // x ^ y ^ c
            int xc = synthGate(AND, xyc, carry);  // (x^y) & c
            carry = synthGate(OR, xy, xc);        // majority
        }
        acc = sum;
    }
    for (int k = 0; k < 2 * width; k++)
        po_gates.push_back(acc[k]);
}

// ---------------------------------------------------------------------------
// Evaluation
// ---------------------------------------------------------------------------
std::vector<bool>
CHAOSGateFU::evalNet(const std::vector<bool> &pis, int stuck_gate,
                     int stuck_val) const
{
    std::vector<bool> val(gates.size());
    auto read = [&](int in) -> bool {
        if (in < 0)
            return pis[-in - 1];
        return val[in];
    };
    for (size_t gi = 0; gi < gates.size(); gi++) {
        const Gate &g = gates[gi];
        bool v;
        switch (g.type) {
          case AND: v = read(g.in0) && read(g.in1); break;
          case OR:  v = read(g.in0) || read(g.in1); break;
          case XOR: v = read(g.in0) != read(g.in1); break;
          case NOT: v = !read(g.in0); break;
          default:  v = false;
        }
        // Structural stuck-at: force AFTER computing, before fanouts read.
        if ((int)gi == stuck_gate)
            v = (stuck_val != 0);
        val[gi] = v;
    }
    std::vector<bool> po(po_gates.size());
    for (size_t i = 0; i < po_gates.size(); i++)
        po[i] = po_gates[i] >= 0 ? val[po_gates[i]] : false;
    return po;
}

bool
CHAOSGateFU::evaluate(int op_class, o3::DynInst *inst, uint64_t &result)
{
    // No fault configured -> never touch the writeback (pure equivalence
    // mode: the injector is inert; earlier versions replaced val with the
    // netlist value even when fault-free, and imperfect operand capture
    // (MADD's Ra,Rm,Rn operand order) corrupted C-lib startup -> crash).
    if (stuck_gate < 0)
        return false;
    if (op_class != target_opclass)
        return false;
    if (cpu->curCycle() < Cycles(first_clock))
        return false;

    // Read two integer source operands (imperfect for 3-operand forms like
    // MADD — see above; the delta method below keeps the injection
    // structurally faithful: both nets see the SAME inputs).
    if (inst->numSrcRegs() < 2)
        return false;
    uint64_t a = 0, b = 0;
    int got = 0;
    for (size_t i = 0; i < inst->numSrcRegs() && got < 2; i++) {
        const PhysRegIdPtr reg = inst->renamedSrcIdx(i);
        if (reg->classValue() == IntRegClass) {
            RegVal v = cpu->getReg(reg, inst->threadNumber);
            if (got == 0) a = v; else b = v;
            got++;
        }
    }
    if (got < 2)
        return false;

    eval_count++;
    stats.numEvals++;

    std::vector<bool> pis(pi_width, false);
    for (int i = 0; i < 64; i++) {
        pis[i] = (a >> i) & 1;
        if (pi_width > (size_t)(64 + i))
            pis[64 + i] = (b >> i) & 1;
    }
    // Structural stuck-at delta: same inputs through clean and faulted
    // nets; the XOR of the two results is the fault signature applied to
    // the architectural value.
    std::vector<bool> po_clean = evalNet(pis, -1, 0);
    std::vector<bool> po_stuck = evalNet(pis, stuck_gate, stuck_val);
    uint64_t r_clean = 0, r_stuck = 0;
    for (size_t i = 0; i < po_clean.size() && i < 64; i++) {
        if (po_clean[i]) r_clean |= (1ULL << i);
        if (po_stuck[i]) r_stuck |= (1ULL << i);
    }
    if (r_stuck != r_clean) {
        diff_count++;
        stats.numDiffs++;
        if (write_log && log_stream && log_stream->stream()
            && eval_count <= 32) {
            *(log_stream->stream())
                << "Cycle: " << cpu->curCycle()
                << ", OpClass: " << enums::OpClassStrings[target_opclass]
                << ", gate: " << stuck_gate << "=" << stuck_val
                << ", a: 0x" << std::hex << a << ", b: 0x" << b
                << ", clean: 0x" << r_clean << ", stuck: 0x" << r_stuck
                << std::dec << std::endl;
        }
        // Apply the fault signature to the architectural result.
        result = 0;   // marker: caller XORs by (r_clean ^ r_stuck) below
        uint64_t delta = r_clean ^ r_stuck;
        // Return via result the delta to XOR into val — see oracle wrapper.
        result = delta;
        return true;
    }
    return false;
}

// Oracle used by cpu/o3/dyn_inst.hh setRegOperand. On true, `result`
// carries the XOR delta (fault signature) to apply to the architectural
// value — the netlist NEVER replaces the value wholesale.
bool
gatefu_evaluate(int op_class, o3::DynInst *inst, uint64_t &result)
{
    if (!CHAOSGateFU::instance)
        return false;
    return CHAOSGateFU::instance->evaluate(op_class, inst, result);
}

// ---------------------------------------------------------------------------
// SimObject plumbing
// ---------------------------------------------------------------------------
CHAOSGateFU::CHAOSGateFU(const CHAOSGateFUParams &p)
    : SimObject(p),
      cpu(dynamic_cast<o3::CPU *>(p.cpu)),
      write_log(p.writeLog),
      stats(this)
{
    if (!cpu)
        throw std::runtime_error("CHAOSGateFU: cpu is not an O3CPU");

    const std::string &n = p.targetOpClass;
    target_opclass = -1;
    for (int i = 0; i < enums::Num_OpClass; i++) {
        if (enums::OpClassStrings[i] == n) {
            target_opclass = i;
            break;
        }
    }
    if (target_opclass < 0)
        throw std::runtime_error(
            "CHAOSGateFU: unknown targetOpClass '" + n + "'");

    stuck_gate = p.targetGate;
    stuck_val = p.stuckPolarity;
    first_clock = p.firstClock;

    // Synthesize the netlist for this FU class.
    if (n == "IntAlu")
        synthesizeAdder(64);
    else if (n == "IntMult")
        synthesizeMultiplier(64);
    else
        throw std::runtime_error(
            "CHAOSGateFU: netlist available for IntAlu | IntMult (got '"
            + n + "'; FP netlists are Task 5.4)");

    if (instance)
        warn("CHAOSGateFU: multiple instances; last one wins\n");
    instance = this;
    gatefu_enabled = true;

    if (write_log) {
        log_stream = simout.create("gatefu_injections.log", false, true);
        if (!log_stream || !log_stream->stream())
            panic("CHAOSGateFU: could not open gatefu_injections.log");
    }
    // After synthesis (moved past the netlist construction above).
    stats.numGates = gates.size();
}

CHAOSGateFU::~CHAOSGateFU()
{
    if (instance == this) {
        instance = nullptr;
        gatefu_enabled = false;
    }
}

CHAOSGateFU::Stats::Stats(statistics::Group *parent)
    : statistics::Group(parent),
      ADD_STAT(numEvals, statistics::units::Count::get(),
               "Netlist evaluations (ops of the target class)"),
      ADD_STAT(numDiffs, statistics::units::Count::get(),
               "Netlist result differs from architectural value (fault "
               "manifestations)"),
      ADD_STAT(numGates, statistics::units::Count::get(),
               "Synthesized gate count of the FU netlist")
{
}

} // namespace gem5
