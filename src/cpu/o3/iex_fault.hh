/*
 * IEX paper-experiment fault injection and propagation tracing.
 *
 * This header is deliberately light: the generated ARM ISA execute bodies
 * include it from includes.isa, so it must not pull in O3 headers.  All
 * DynInst-dependent work lives in iex_fault.cc.
 *
 * Configuration is per-process through environment variables so that the
 * exact same gem5 binary executes Fault and Control samples, with only
 * IEX_FAULT_ENABLED toggled (workbook RunPairPolicy).
 */

#ifndef __ARCH_ARM_IEX_FAULT_HH__
#define __ARCH_ARM_IEX_FAULT_HH__

#include <cstdint>

#include "base/types.hh"

namespace gem5
{

namespace o3 { class DynInst; }

namespace iex
{

/* ---- lifecycle / observation hooks (called from O3) ---- */
void noteExecuteBegin(o3::DynInst *inst);
void noteExecuteEnd(o3::DynInst *inst);
void noteInitiateAcc(o3::DynInst *inst);
void noteCompleteAcc(o3::DynInst *inst);
void noteRegWrite(o3::DynInst *inst, int idx, uint64_t val, uint64_t old);
void noteWriteback(o3::DynInst *inst, int dependents);
void noteCommit(o3::DynInst *inst, unsigned rob_entries);
void noteSquash(ThreadID tid, uint64_t branch_seq, uint64_t squashed_seq,
                const char *reason, unsigned rob_entries);
void noteSquashInfo(ThreadID tid, uint64_t squashed_seq, const char *reason,
                    unsigned rob_entries);
void noteBranchResolve(o3::DynInst *inst, uint64_t pred_npc,
                       uint64_t resolved_npc, bool predicted_taken,
                       bool mispredicted);

/* ---- M001 ADD 32-bit carry suppression ---- */
uint64_t m001_add(uint64_t pc, uint64_t a, uint64_t b, uint64_t normal);

/* ---- M002 LSLV effective shift-amount bit0 inversion ---- */
uint64_t m002_lslv_amt(uint64_t pc, uint64_t a, uint64_t b, uint64_t width);

/* ---- M003 UMULH L214 cross-term carry loss ---- */
uint64_t m003_l214(uint64_t pc, uint64_t op1h, uint64_t op1l,
                   uint64_t op2h, uint64_t op2l, uint64_t mid1,
                   uint64_t mid2, uint64_t result);
void m003_after215(uint64_t pc, uint64_t result);
void m003_after216(uint64_t pc, uint64_t result);
void m003_final(uint64_t pc, uint64_t op1h, uint64_t op2h,
                uint64_t result_before_hh, uint64_t xd);

/* ---- M004 UDIV zero-result selection ---- */
bool m004_force_zero(uint64_t pc, uint64_t a, uint64_t b);
void m004_result(uint64_t pc, uint64_t a, uint64_t b, uint64_t result);

/* ---- M005 B.cond execution-direction inversion ---- */
bool m005_bcond(uint64_t pc, bool taken, uint64_t nz, uint64_t c, uint64_t v,
                int cond, uint64_t target_npc, uint64_t fallthrough_npc);

/* ---- M006 SUBS Z generation inversion ---- */
uint64_t m006_iz(uint64_t pc, uint64_t res_temp, uint64_t iz, uint64_t in);
void m006_flags(uint64_t pc, uint64_t res_temp, uint64_t nz, uint64_t c,
                uint64_t v);
void m006_csel(uint64_t pc, bool eq, uint64_t op1, uint64_t op2,
               uint64_t selected, uint64_t result);

/* ---- M007 CLZ nonzero count bias ---- */
uint64_t m007_clz(uint64_t pc, uint64_t a, uint64_t width);

/* ---- generic model-neutral witness from an ISA site ---- */
void note_site(uint64_t pc, const char *site);

} // namespace iex
} // namespace gem5

#endif // __ARCH_ARM_IEX_FAULT_HH__
