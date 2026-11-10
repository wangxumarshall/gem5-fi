// libFuzzer target: Unicorn ARM64 emulator as the proxy (paper section 2.4.3).
//
// The input bytes are mapped at a fixed address and execution starts at the
// first byte for a bounded number of instructions, mirroring the upstream
// Unicorn fuzz target referenced by the paper.
#include <unicorn/unicorn.h>

#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {
constexpr uint64_t kBase = 0x10000000;
constexpr uint64_t kSize = 0x1000;
constexpr uint32_t kMaxInsns = 1000;
}  // namespace

extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
  if (size < 4) return 0;
  if (size > kSize) size = kSize;
  uc_engine* uc = nullptr;
  if (uc_open(UC_ARCH_ARM64, UC_MODE_ARM, &uc) != UC_ERR_OK) return 0;
  if (uc_mem_map(uc, kBase, kSize, UC_PROT_ALL) == UC_ERR_OK &&
      uc_mem_write(uc, kBase, data, size) == UC_ERR_OK) {
    uc_emu_start(uc, kBase, kBase + kSize, 0, kMaxInsns);
  }
  uc_close(uc);
  return 0;
}
