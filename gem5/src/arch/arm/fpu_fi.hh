#ifndef __ARCH_ARM_FPU_FI_HH__
#define __ARCH_ARM_FPU_FI_HH__

#include <cstdint>

namespace gem5
{
namespace fpu_fi
{

// Lightweight interface used by the ARM fplib/NEON semantic hooks.
// The implementation lives in cpu/o3/FPUInjector.cc and is driven by the
// FPU_FI_* environment variables for each run.
bool active(int model);
int model();
int lane();

void note_injection(const char *site, uint64_t old_value, uint64_t new_value,
                    int lane, uint64_t aux = 0);

} // namespace fpu_fi
} // namespace gem5

#endif
