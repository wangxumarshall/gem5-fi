// One-shot / batch coverage fingerprint for the Capstone proxy.
//
// The Capstone static library is built with -fsanitize=fuzzer-no-link, i.e. the
// same inline-8bit-counters instrumentation the libFuzzer proxy uses.  We link
// it without the fuzzer runtime and provide the two init callbacks ourselves,
// then report the indices of non-zero counters.  The index space is fixed for a
// given binary, so fingerprints are comparable across runs and immune to ASLR.
//
//   covdrv_capstone <input.bin>          fingerprint of decoding the first insn
//   covdrv_capstone --batch <words.bin>  one line per 4-byte word, counters
//                                        cleared between words
#include <capstone/capstone.h>

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>

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

static void ResetCounters() {
  for (size_t r = 0; r < g_ranges; ++r) memset(g_start[r], 0, g_stop[r] - g_start[r]);
}

static void Emit() {
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
}

static bool DecodeOne(csh handle, const uint8_t *buf, size_t n, const char **mnemonic) {
  cs_insn *insn = nullptr;
  size_t k = cs_disasm(handle, buf, n, 0x1000, 1, &insn);
  bool ok = k == 1;
  *mnemonic = ok ? insn[0].mnemonic : "-";
  if (k) cs_free(insn, k);
  return ok;
}

int main(int argc, char **argv) {
  if (argc < 2) return 2;
  static uint8_t buf[1 << 22];
  FILE *f = fopen(argv[argc - 1], "rb");
  if (!f) return 2;
  size_t n = fread(buf, 1, sizeof(buf), f);
  fclose(f);

  csh handle = 0;
  if (cs_open(CS_ARCH_ARM64, CS_MODE_ARM, &handle) != CS_ERR_OK) return 3;

  if (strcmp(argv[1], "--batch") == 0) {
    for (size_t off = 0; off + 4 <= n; off += 4) {
      ResetCounters();
      const char *mn = "-";
      bool ok = DecodeOne(handle, buf + off, 4, &mn);
      fprintf(stdout, "%c,%s,", ok ? '1' : '0', mn);
      Emit();
    }
  } else {
    ResetCounters();
    const char *mn = "-";
    bool ok = DecodeOne(handle, buf, n, &mn);
    fprintf(stdout, "%c,%s,", ok ? '1' : '0', mn);
    Emit();
  }
  cs_close(&handle);
  return 0;
}
