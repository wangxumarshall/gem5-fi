/*
 * [LSU][MDSPEC][R6-A3] A05-a/b/c real ISA operand hook — see the header.
 */

#include "arch/arm/insts/chaos_agu_operands.hh"

#include "cpu/exec_context.hh"

namespace gem5
{

namespace ArmISA
{

namespace
{

ChaosAguOperandHook operand_hook = nullptr;

} // anonymous namespace

void
setChaosAguOperandHook(ChaosAguOperandHook fn)
{
    operand_hook = fn;
}

ChaosAguOperandHook
chaosAguOperandHook()
{
    return operand_hook;
}

void
chaosAguRegOperands(ExecContext *xc, bool is_load, unsigned size,
                    unsigned base_reg, unsigned index_reg,
                    uint64_t &base_val, uint64_t &index_val,
                    ArmExtendType &type, uint64_t &shift)
{
    // Not installed: the generated EA code is byte-identical to baseline.
    if (!operand_hook)
        return;

    ChaosAguRegView v;
    v.is_load = is_load;
    v.size = size;
    v.base_reg = base_reg;
    v.index_reg = index_reg;
    v.base_val = base_val;
    v.index_val = index_val;
    v.type = type;
    v.shift = shift;
    v.new_base_val = base_val;
    v.new_index_val = index_val;
    v.new_type = type;
    v.new_shift = shift;
    v.applied = false;

    operand_hook(xc, v);

    // Read-only access when the hook declined: the operands stay real.
    if (!v.applied)
        return;
    base_val = v.new_base_val;
    index_val = v.new_index_val;
    type = v.new_type;
    shift = v.new_shift;
}

} // namespace ArmISA
} // namespace gem5
