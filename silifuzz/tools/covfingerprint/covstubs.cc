// No-op sanitizer-coverage runtime for the one-shot drivers.
// The instrumented libraries were built with -fsanitize=fuzzer-no-link, which
// also emits trace-cmp/trace-div/trace-switch calls.  We only care about the
// 8-bit block counters, so every other callback can be a no-op.
#include <cstdint>

extern "C" {
__thread uintptr_t __sancov_lowest_stack = 0;
void __sanitizer_cov_trace_pc_guard(uint32_t *) {}
void __sanitizer_cov_trace_pc_guard_init(uint32_t *, uint32_t *) {}
void __sanitizer_cov_trace_pc(void) {}
void __sanitizer_cov_trace_cmp1(uint8_t, uint8_t) {}
void __sanitizer_cov_trace_cmp2(uint16_t, uint16_t) {}
void __sanitizer_cov_trace_cmp4(uint32_t, uint32_t) {}
void __sanitizer_cov_trace_cmp8(uint64_t, uint64_t) {}
void __sanitizer_cov_trace_const_cmp1(uint8_t, uint8_t) {}
void __sanitizer_cov_trace_const_cmp2(uint16_t, uint16_t) {}
void __sanitizer_cov_trace_const_cmp4(uint32_t, uint32_t) {}
void __sanitizer_cov_trace_const_cmp8(uint64_t, uint64_t) {}
void __sanitizer_cov_trace_switch(uint64_t, uint64_t *) {}
void __sanitizer_cov_trace_div4(uint32_t) {}
void __sanitizer_cov_trace_div8(uint64_t) {}
void __sanitizer_cov_trace_gep(uintptr_t) {}
void __sanitizer_cov_trace_pc_indir(uintptr_t) {}
void __sanitizer_cov_load1(uint8_t *) {}
void __sanitizer_cov_load2(uint16_t *) {}
void __sanitizer_cov_load4(uint32_t *) {}
void __sanitizer_cov_load8(uint64_t *) {}
void __sanitizer_cov_load16(void *) {}
void __sanitizer_cov_store1(uint8_t *) {}
void __sanitizer_cov_store2(uint16_t *) {}
void __sanitizer_cov_store4(uint32_t *) {}
void __sanitizer_cov_store8(uint64_t *) {}
void __sanitizer_cov_store16(void *) {}
}
