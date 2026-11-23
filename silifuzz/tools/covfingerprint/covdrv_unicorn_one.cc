// One-instruction Unicorn coverage fingerprint under a chosen initial state.
//
// The Unicorn proxy executes a whole input from a zeroed state, which is
// useless for describing "what does this single template instruction do in the
// emulator".  This driver runs exactly one instruction at 0x10000000 with a
// named scenario's register/memory setup and reports the emulator's
// inline-8bit-counters, so a template's execution region can be measured
// instruction by instruction (and per scenario).
//
//   covdrv_unicorn_one --batch <words.bin> --scenario <name>
//   covdrv_unicorn_one <code.bin> --scenario <name>
#include <unicorn/unicorn.h>

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>

namespace {
constexpr uint64_t kCode = 0x10000000;
constexpr uint64_t kData = 0x20000000;
constexpr uint64_t kStack = 0x30000000;
constexpr uint64_t kPage = 0x1000;

// Register numbers are kept explicit: Unicorn's arm64 enum is not guaranteed to
// be contiguous and we only need the general purpose + vector files.
struct RegX { int reg; };
}  // namespace

static uint8_t *g_start[4096];
static uint8_t *g_stop[4096];
static size_t g_ranges = 0;

extern "C" void __sanitizer_cov_8bit_counters_init(uint8_t *s, uint8_t *e) {
  if (g_ranges < 4096) {
    g_start[g_ranges] = s;
    g_stop[g_ranges] = e;
    ++g_ranges;
  }
}
extern "C" void __sanitizer_cov_pcs_init(const uintptr_t *, const uintptr_t *) {}

static void ResetCounters() {
  for (size_t r = 0; r < g_ranges; ++r) memset(g_start[r], 0, g_stop[r] - g_start[r]);
}

static void EmitCounters() {
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

// General purpose registers X0..X30 plus SP/LR.
static const int kGpr[] = {
    UC_ARM64_REG_X0,  UC_ARM64_REG_X1,  UC_ARM64_REG_X2,  UC_ARM64_REG_X3,
    UC_ARM64_REG_X4,  UC_ARM64_REG_X5,  UC_ARM64_REG_X6,  UC_ARM64_REG_X7,
    UC_ARM64_REG_X8,  UC_ARM64_REG_X9,  UC_ARM64_REG_X10, UC_ARM64_REG_X11,
    UC_ARM64_REG_X12, UC_ARM64_REG_X13, UC_ARM64_REG_X14, UC_ARM64_REG_X15,
    UC_ARM64_REG_X16, UC_ARM64_REG_X17, UC_ARM64_REG_X18, UC_ARM64_REG_X19,
    UC_ARM64_REG_X20, UC_ARM64_REG_X21, UC_ARM64_REG_X22, UC_ARM64_REG_X23,
    UC_ARM64_REG_X24, UC_ARM64_REG_X25, UC_ARM64_REG_X26, UC_ARM64_REG_X27,
    UC_ARM64_REG_X28, UC_ARM64_REG_X29, UC_ARM64_REG_X30,
};

static const int kVec[] = {
    UC_ARM64_REG_Q0,  UC_ARM64_REG_Q1,  UC_ARM64_REG_Q2,  UC_ARM64_REG_Q3,
    UC_ARM64_REG_Q4,  UC_ARM64_REG_Q5,  UC_ARM64_REG_Q6,  UC_ARM64_REG_Q7,
    UC_ARM64_REG_Q8,  UC_ARM64_REG_Q9,  UC_ARM64_REG_Q10, UC_ARM64_REG_Q11,
    UC_ARM64_REG_Q12, UC_ARM64_REG_Q13, UC_ARM64_REG_Q14, UC_ARM64_REG_Q15,
    UC_ARM64_REG_Q16, UC_ARM64_REG_Q17, UC_ARM64_REG_Q18, UC_ARM64_REG_Q19,
    UC_ARM64_REG_Q20, UC_ARM64_REG_Q21, UC_ARM64_REG_Q22, UC_ARM64_REG_Q23,
    UC_ARM64_REG_Q24, UC_ARM64_REG_Q25, UC_ARM64_REG_Q26, UC_ARM64_REG_Q27,
    UC_ARM64_REG_Q28, UC_ARM64_REG_Q29, UC_ARM64_REG_Q30, UC_ARM64_REG_Q31,
};

struct Scenario {
  const char *name;
  uint64_t gpr_base;   // all X regs point here
  uint64_t gpr_step;   // ... unless step != 0, then X_i = base + i*step
  uint64_t vec_lo, vec_hi;
  uint64_t sp;
};

static Scenario Pick(const std::string &name) {
  if (name == "fp1") return {"fp1", kData, 0, 0x3FF0000000000000ULL, 0, kStack + 0xFF00};
  if (name == "vec_sat") return {"vec_sat", kData, 0, 0xFFFFFFFFFFFFFFFFULL, 0xFFFFFFFFFFFFFFFFULL, kStack + 0xFF00};
  if (name == "mem_cross") return {"mem_cross", kData + kPage - 4, 0, 0, 0, kStack + 0xFF00};
  if (name == "mem_unmapped") return {"mem_unmapped", 0x21000000ULL, 0, 0, 0, kStack + 0xFF00};
  if (name == "branch") return {"branch", kCode, 0, 0, 0, kStack + 0xFF00};
  if (name == "small") return {"small", 8, 7, 0x3FF0000000000000ULL, 0, kStack + 0xFF00};
  return {"centered", kData, 0, 0, 0, kStack + 0xFF00};
}

static void ApplyScenario(uc_engine *uc, const Scenario &s) {
  for (int i = 0; i < 31; ++i) {
    uint64_t v = s.gpr_step ? s.gpr_base + (uint64_t)i * s.gpr_step : s.gpr_base;
    uc_reg_write(uc, kGpr[i], &v);
  }
  uint64_t lr = kCode + kPage - 4;
  uc_reg_write(uc, UC_ARM64_REG_LR, &lr);
  uc_reg_write(uc, UC_ARM64_REG_SP, &s.sp);
  uint64_t q[2] = {s.vec_lo, s.vec_hi};
  for (int i = 0; i < 32; ++i) uc_reg_write(uc, kVec[i], q);
  uint32_t fpcr = 0, fpsr = 0;
  uc_reg_write(uc, UC_ARM64_REG_FPCR, &fpcr);
  uc_reg_write(uc, UC_ARM64_REG_FPSR, &fpsr);
}

static bool RunOne(const uint8_t *code, size_t n, const Scenario &sc, const char **err) {
  uc_engine *uc = nullptr;
  if (uc_open(UC_ARCH_ARM64, UC_MODE_ARM, &uc) != UC_ERR_OK) {
    *err = "open";
    return false;
  }
  bool ok = false;
  if (uc_mem_map(uc, kCode, kPage, UC_PROT_ALL) == UC_ERR_OK &&
      uc_mem_map(uc, kData, kPage, UC_PROT_ALL) == UC_ERR_OK &&
      uc_mem_map(uc, kStack, 0x10000, UC_PROT_ALL) == UC_ERR_OK) {
    uint8_t buf[8] = {0, 0, 0, 0, 0x00, 0x00, 0x20, 0xD4};  // insn + brk #0
    memcpy(buf, code, n < 4 ? n : 4);
    if (uc_mem_write(uc, kCode, buf, sizeof(buf)) == UC_ERR_OK) {
      ApplyScenario(uc, sc);
      uint64_t pc = kCode;
      uc_reg_write(uc, UC_ARM64_REG_PC, &pc);
      // count = 1: exactly one guest instruction; a fault still yields coverage.
      uc_err r = uc_emu_start(uc, kCode, kCode + 8, 0, 1);
      ok = (r == UC_ERR_OK) || (r == UC_ERR_READ_UNMAPPED) || (r == UC_ERR_WRITE_UNMAPPED) ||
           (r == UC_ERR_FETCH_UNMAPPED) || (r == UC_ERR_EXCEPTION) || (r == UC_ERR_INSN_INVALID);
    }
  }
  uc_close(uc);
  if (!ok) *err = "emu";
  return ok;
}

int main(int argc, char **argv) {
  if (argc < 2) return 2;
  std::string scenario = "centered";
  const char *path = nullptr;
  bool batch = false;
  for (int i = 1; i < argc; ++i) {
    std::string a = argv[i];
    if (a == "--scenario" && i + 1 < argc) {
      scenario = argv[++i];
    } else if (a == "--batch") {
      batch = true;
    } else {
      path = argv[i];
    }
  }
  if (!path) return 2;

  static uint8_t buf[1 << 22];
  FILE *f = fopen(path, "rb");
  if (!f) return 2;
  size_t n = fread(buf, 1, sizeof(buf), f);
  fclose(f);
  Scenario sc = Pick(scenario);

  if (batch) {
    for (size_t off = 0; off + 4 <= n; off += 4) {
      ResetCounters();
      const char *err = "";
      bool ok = RunOne(buf + off, 4, sc, &err);
      fputs(ok ? "1," : "0,", stdout);
      EmitCounters();
    }
  } else {
    ResetCounters();
    const char *err = "";
    bool ok = RunOne(buf, n < 4 ? n : 4, sc, &err);
    fputs(ok ? "1," : "0,", stdout);
    EmitCounters();
  }
  return 0;
}
