// libFuzzer target: Capstone ARM64 disassembler as the "fuzzing by proxy"
// target (paper section 2.4.1 uses Intel XED for x86-64).
//
// Build against a Capstone static library instrumented with
// -fsanitize=fuzzer-no-link (see scripts/build_deps.sh), otherwise libFuzzer
// sees no coverage inside the proxy.
#include <capstone/capstone.h>

#include <cstddef>
#include <cstdint>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
  static csh handle = 0;
  if (handle == 0) {
    if (cs_open(CS_ARCH_ARM64, CS_MODE_ARM, &handle) != CS_ERR_OK) return 0;
  }
  cs_insn* insn = nullptr;
  // Decode at most one instruction; the proxy is the decoder itself, and the
  // corpus is a set of byte sequences that reach new decoder paths.
  size_t n = cs_disasm(handle, data, size, 0x1000, 1, &insn);
  if (n != 0) cs_free(insn, n);
  return 0;
}
