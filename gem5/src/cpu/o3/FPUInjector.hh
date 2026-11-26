#ifndef __CPU_O3_FPU_INJECTOR_HH__
#define __CPU_O3_FPU_INJECTOR_HH__

#include <cstdint>

namespace gem5
{
namespace o3 { class DynInst; }

namespace fpu_fi
{

// O3 lifecycle hooks.  All functions are no-ops unless FI_TRACE/FI_ENABLE
// environment configuration was supplied.
void begin_exec(o3::DynInst *inst);
void end_exec(o3::DynInst *inst);
void trace_rename(o3::DynInst *inst);
void trace_issue(o3::DynInst *inst);
void trace_writeback(o3::DynInst *inst);
void trace_commit(o3::DynInst *inst, uint64_t commit_seq);
void trace_squash(o3::DynInst *inst);
void trace_branch(o3::DynInst *inst, bool pred_taken, bool actual_taken,
                  uint64_t pred_pc, uint64_t actual_pc);
void trace_squash_reason(uint64_t squashed_seq, const char *reason);

uint64_t eligible_count();
uint64_t applied_count();
bool is_target(uint64_t pc);

} // namespace fpu_fi
} // namespace gem5

#endif
