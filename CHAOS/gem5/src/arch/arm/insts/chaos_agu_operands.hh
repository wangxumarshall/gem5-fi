/*
 * [LSU][MDSPEC][R6-A3] A05-a/b/c real ISA operand hook.
 *
 * WHY THIS FILE EXISTS
 * --------------------
 * A05's submodels (base/index swap, UXTW<->SXTW, shift substitution) are
 * OPERAND-level faults. By the time LSQ::pushRequest runs, the generated
 * ISA code has already collapsed the operands into a single EA; the O3
 * microop source-operand slots are not a stable API (measured SIGSEGV,
 * R6-A2-STATUS §2.1). The only clean insertion point is the ISA address
 * generation itself, before `EA = XBase + extendReg64(...)` executes
 * (R6-A2-DIAG-B §1.4 "design A").
 *
 * CONTRACT
 * --------
 * The generated register-offset EA code snapshots the REAL decoded
 * operands into local copies and calls chaosAguRegOperands(). A single
 * process-wide callback (installed by CHAOSAddrPath::startup) may rewrite
 * the locals; the EA is then computed from them. The StaticInst members
 * type/shiftAmt are NEVER written (they are shared by every dynamic
 * instance of the class) and architectural registers are never touched.
 *
 * With no hook installed the call is one null-pointer test: baseline
 * configurations stay byte-identical.
 */

#ifndef __ARCH_ARM_INSTS_CHAOS_AGU_OPERANDS_HH__
#define __ARCH_ARM_INSTS_CHAOS_AGU_OPERANDS_HH__

#include <cstdint>

#include "arch/arm/types.hh"
#include "base/types.hh"

namespace gem5
{

class ExecContext;

namespace ArmISA
{

/// One REAL register-offset EA operand snapshot, in/out.
///
/// Identity fields (dyn_inst_seq/pc/static_inst) are filled by the hook
/// implementation from the O3 DynInst; they are what makes a decision
/// request-scoped: a descriptor may never be consumed by a different
/// dynamic instruction.
struct ChaosAguRegView
{
    // ---- identity (filled by the hook, stable per dynamic instruction) --
    uint64_t dyn_inst_seq = 0;
    Addr pc = 0;
    const void *static_inst = nullptr;

    // ---- instruction shape (from the generated EA code) ----------------
    bool is_load = false;
    unsigned size = 0;          // access width = sizeof(Mem)
    unsigned base_reg = 0;      // architectural base register index
    unsigned index_reg = 0;     // architectural index/offset register index

    // ---- REAL operand values (as read from the physical register file) --
    uint64_t base_val = 0;
    uint64_t index_val = 0;
    ArmExtendType type = UXTX;  // decoded option (UXTW/SXTW/LSL/SXTX)
    uint64_t shift = 0;         // decoded shift amount (0 or log2(size))

    // ---- output: transformed operands (only when applied) --------------
    uint64_t new_base_val = 0;
    uint64_t new_index_val = 0;
    ArmExtendType new_type = UXTX;
    uint64_t new_shift = 0;
    bool applied = false;

    /// Sub-model that produced the rewrite (a05a/a05b/a05c), for evidence.
    const char *submodel = nullptr;
};

using ChaosAguOperandHook = void (*)(ExecContext *xc, ChaosAguRegView &v);

/// Install (or clear, with nullptr) the process-wide operand hook.
void setChaosAguOperandHook(ChaosAguOperandHook fn);
ChaosAguOperandHook chaosAguOperandHook();

/// Called from the generated register-offset EA code BEFORE the EA is
/// computed. When no hook is installed, or the hook declines, the
/// operands are returned unchanged.
void chaosAguRegOperands(ExecContext *xc, bool is_load, unsigned size,
                         unsigned base_reg, unsigned index_reg,
                         uint64_t &base_val, uint64_t &index_val,
                         ArmExtendType &type, uint64_t &shift);

} // namespace ArmISA
} // namespace gem5

#endif // __ARCH_ARM_INSTS_CHAOS_AGU_OPERANDS_HH__
