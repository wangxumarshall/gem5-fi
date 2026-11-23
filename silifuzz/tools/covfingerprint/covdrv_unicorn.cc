// One-shot coverage fingerprint for the Unicorn proxy.
//
// Same technique as covdrv_capstone.cc: the Unicorn static library carries the
// proxy's inline-8bit-counters, and we read them back after one bounded run
// (map 4 KiB at 0x10000000, execute at most 1000 instructions), exactly like
// proxies/unicorn_fuzz.cc.
#include <unicorn/unicorn.h>

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <utility>
#include <vector>

namespace {
constexpr uint64_t kBase = 0x10000000;
constexpr uint64_t kSize = 0x1000;
constexpr uint32_t kMaxInsns = 1000;
}

// Static zero-initialised storage: sanitizer-coverage constructors run with the
// highest priority, i.e. before any C++ dynamic initialisation, so a std::vector
// here would be used before it is constructed.
static uint8_t *g_start[4096];
static uint8_t *g_stop[4096];
static size_t g_ranges = 0;

extern "C" void __sanitizer_cov_8bit_counters_init(uint8_t *start, uint8_t *stop) {
  if (g_ranges < 4096) {
    g_start[g_ranges] = start;
    g_stop[g_ranges] = stop;
    ++g_ranges;
  }
}
extern "C" void __sanitizer_cov_pcs_init(const uintptr_t *, const uintptr_t *) {}

int main(int argc, char **argv) {
  if (argc < 2) return 2;
  FILE *f = fopen(argv[1], "rb");
  if (!f) return 2;
  static uint8_t buf[1 << 16];
  size_t n = fread(buf, 1, sizeof(buf), f);
  fclose(f);
  if (n > kSize) n = kSize;

  uc_engine *uc = nullptr;
  if (n >= 4 && uc_open(UC_ARCH_ARM64, UC_MODE_ARM, &uc) == UC_ERR_OK) {
    if (uc_mem_map(uc, kBase, kSize, UC_PROT_ALL) == UC_ERR_OK &&
        uc_mem_write(uc, kBase, buf, n) == UC_ERR_OK) {
      uc_emu_start(uc, kBase, kBase + kSize, 0, kMaxInsns);
    }
    uc_close(uc);
  }

  std::string out;
  size_t idx = 0;
  for (size_t r = 0; r < g_ranges; ++r) {
    for (uint8_t *p = g_start[r]; p < g_stop[r]; ++p, ++idx) {
      if (*p) {
        out.append(std::to_string(idx));
        out.push_back(',');
      }
    }
  }
  fputs(out.c_str(), stdout);
  fputc('\n', stdout);
  return 0;
}
