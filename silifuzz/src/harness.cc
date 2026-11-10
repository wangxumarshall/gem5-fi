// Harness process: executes snapshot commands from the driver.
//
// Snapshot entry uses the kernel signal frame: a SIGTRAP handler edits the
// ucontext (all x0-x30/sp/pc/pstate plus the fpsimd_context record) and returns,
// so rt_sigreturn restores the full architectural state and jumps into the
// snapshot. This is the ARM64 equivalent of the paper's "harness runs the
// actual code" (section 2.3). glibc getcontext/setcontext only restore a
// caller-saved subset and cannot be used here.
//
// This file is compiled with -mgeneral-regs-only: the signal handler must not
// touch FP/SIMD before resetting FPCR/FPSR (a snapshot may enable FP traps).
#include <asm/sigcontext.h>
#include <errno.h>
#include <signal.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <setjmp.h>
#include <ucontext.h>
#include <unistd.h>

#include <cstdint>
#include <cstdio>
#include <cstdlib>

#include "silifuzz/player.hh"
#include "silifuzz/protocol.hh"


namespace silifuzz {
namespace {

constexpr int kMaxRegions = 64;
constexpr size_t kAltStackSize = 1 << 16;
constexpr uint64_t kTrampolineBase = 0x10001000;
constexpr uint64_t kAliasBase = 0x100000000000ULL;
constexpr int kArenaDataPages = 4;

// Long-lived arena for the common snapshot layout.  Reusing these mappings
// avoids mmap/munmap/mprotect on every execution, which otherwise dominates
// the kernel time at fleet scale.  The code page is mapped twice (RX at the
// snapshot address, RW at a far alias) so new code can be written without W+X.
struct Arena {
  bool ready = false;
  int fd = -1;
  uint8_t* code_rw = nullptr;
};
Arena g_arena;

struct Region {
  uint64_t start = 0;
  uint64_t size = 0;
  uint32_t perms = 0;
  bool used = false;
};

Region g_regions[kMaxRegions];
volatile sig_atomic_t g_phase = 0;  // 0 idle, 1 entering snapshot, 2 running
sigjmp_buf g_env;
ucontext_t g_uc;
int g_signal = 0;
uint64_t g_sig_addr = 0;
RegState g_init;
int g_entry_error = 0;
uint64_t g_exec_count = 0;
int g_inj_reg = -1;
int g_inj_bit = 0;
uint64_t g_inj_mod = 0;
uint64_t g_inj_rem = 0;

char* g_altstack = nullptr;

struct fpsimd_context* FindFpsimd(ucontext_t* uc) {
  struct _aarch64_ctx* h =
      reinterpret_cast<struct _aarch64_ctx*>(uc->uc_mcontext.__reserved);
  // __reserved is 4096 bytes; records are size-prefixed and terminated by 0.
  const char* base = reinterpret_cast<const char*>(uc->uc_mcontext.__reserved);
  while ((const char*)h - base < 4096 && h->magic != 0) {
    if (h->magic == FPSIMD_MAGIC && h->size >= sizeof(struct fpsimd_context)) {
      return reinterpret_cast<struct fpsimd_context*>(h);
    }
    if (h->size < sizeof(struct _aarch64_ctx)) break;
    h = reinterpret_cast<struct _aarch64_ctx*>((char*)h + h->size);
  }
  return nullptr;
}

void Handler(int sig, siginfo_t* si, void* ctx) {
  // Never let a snapshot's FPCR trap enables leak into harness code.
  asm volatile("msr fpcr, xzr\n\tmsr fpsr, xzr" ::: "memory");
  ucontext_t* uc = reinterpret_cast<ucontext_t*>(ctx);
  if (g_phase == 1) {
    RegState* r = &g_init;
    for (int i = 0; i < 31; ++i) uc->uc_mcontext.regs[i] = r->x[i];
    uc->uc_mcontext.sp = r->sp;
    uc->uc_mcontext.pc = r->pc;
    uc->uc_mcontext.pstate = r->pstate;
    struct fpsimd_context* fp = FindFpsimd(uc);
    if (fp == nullptr) {
      g_entry_error = 1;
      g_phase = 0;
      siglongjmp(g_env, 1);
    }
    fp->fpsr = (uint32_t)r->fpsr;
    fp->fpcr = (uint32_t)r->fpcr;
    memcpy(fp->vregs, r->v, sizeof(r->v));
    g_phase = 2;
    return;  // rt_sigreturn restores the edited frame and enters the snapshot
  }
  g_signal = sig;
  g_sig_addr = reinterpret_cast<uint64_t>(si->si_addr);
  g_uc = *uc;
  g_phase = 0;
  siglongjmp(g_env, 1);
}

void SetupSignals() {
  g_altstack = static_cast<char*>(mmap(nullptr, kAltStackSize,
                                       PROT_READ | PROT_WRITE,
                                       MAP_PRIVATE | MAP_ANONYMOUS, -1, 0));
  if (g_altstack == MAP_FAILED) _exit(111);
  stack_t ss;
  memset(&ss, 0, sizeof(ss));
  ss.ss_sp = g_altstack;
  ss.ss_size = kAltStackSize;
  if (sigaltstack(&ss, nullptr) != 0) _exit(112);

  struct sigaction sa;
  memset(&sa, 0, sizeof(sa));
  sa.sa_sigaction = Handler;
  sa.sa_flags = SA_SIGINFO | SA_NODEFER | SA_ONSTACK;
  sigemptyset(&sa.sa_mask);
  const int signals[] = {SIGTRAP, SIGSEGV, SIGILL, SIGFPE, SIGBUS, SIGSYS};
  for (int s : signals) {
    if (sigaction(s, &sa, nullptr) != 0) _exit(113);
  }
}

bool WriteAll(int fd, const void* data, size_t size) {
  const uint8_t* p = static_cast<const uint8_t*>(data);
  while (size > 0) {
    ssize_t n = write(fd, p, size);
    if (n < 0 && errno == EINTR) continue;
    if (n <= 0) return false;
    p += n;
    size -= (size_t)n;
  }
  return true;
}

bool ReadAll(int fd, void* data, size_t size) {
  uint8_t* p = static_cast<uint8_t*>(data);
  while (size > 0) {
    ssize_t n = read(fd, p, size);
    if (n < 0 && errno == EINTR) continue;
    if (n <= 0) return false;
    p += n;
    size -= (size_t)n;
  }
  return true;
}

bool SendResponse(int fd, uint8_t status, const std::string& payload) {
  std::string msg;
  AppendU32(&msg, (uint32_t)(payload.size() + 1));
  msg.push_back((char)status);
  msg.append(payload);
  return WriteAll(fd, msg.data(), msg.size());
}

void ParseInject(const std::string& spec) {
  // Format: flip:<reg 0..30|31=sp|32=pc>:<bit>:<mod>:<rem>
  if (spec.empty()) return;
  if (sscanf(spec.c_str(), "flip:%d:%d:%llu:%llu", &g_inj_reg, &g_inj_bit,
             (unsigned long long*)&g_inj_mod,
             (unsigned long long*)&g_inj_rem) != 4) {
    g_inj_reg = -1;
  }
}

bool ArenaMatches(const uint64_t* starts, const uint64_t* sizes,
                  const uint32_t* perms, uint32_t n) {
  if (!g_arena.ready || n != (uint32_t)(3 + kArenaDataPages)) return false;
  bool seen[3 + kArenaDataPages] = {};
  for (uint32_t i = 0; i < n; ++i) {
    bool found = false;
    if (starts[i] == kCodeBase && sizes[i] == 4096 &&
        perms[i] == (kPermRead | kPermExec)) {
      seen[0] = true;
      found = true;
    } else if (starts[i] == kTrampolineBase && sizes[i] == 4096 &&
               perms[i] == (kPermRead | kPermExec)) {
      seen[1] = true;
      found = true;
    } else if (starts[i] == kStackBase && sizes[i] == 4096 &&
               perms[i] == (kPermRead | kPermWrite)) {
      seen[2] = true;
      found = true;
    } else {
      for (int p = 0; p < kArenaDataPages; ++p) {
        if (starts[i] == kDataBase + p * 4096 && sizes[i] == 4096 &&
            perms[i] == (kPermRead | kPermWrite)) {
          seen[3 + p] = true;
          found = true;
        }
      }
    }
    if (!found) return false;
  }
  for (bool v : seen) {
    if (!v) return false;
  }
  return true;
}

bool SetupArena() {
  if (g_arena.ready) return true;
  int fd = (int)syscall(SYS_memfd_create, "sf-code", 1 /*MFD_CLOEXEC*/);
  if (fd < 0) return false;
  if (ftruncate(fd, 4096) != 0) {
    close(fd);
    return false;
  }
  void* rw = mmap((void*)kAliasBase, 4096, PROT_READ | PROT_WRITE,
                  MAP_SHARED | MAP_FIXED_NOREPLACE, fd, 0);
  if (rw == MAP_FAILED) {
    close(fd);
    return false;
  }
  void* rx = mmap((void*)kCodeBase, 4096, PROT_READ | PROT_EXEC,
                  MAP_SHARED | MAP_FIXED_NOREPLACE, fd, 0);
  if (rx == MAP_FAILED) {
    munmap(rw, 4096);
    close(fd);
    return false;
  }
  void* tr = mmap((void*)kTrampolineBase, 4096, PROT_READ | PROT_WRITE,
                  MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
  if (tr == MAP_FAILED) return false;
  *(uint32_t*)tr = 0xD4200000u;  // brk #0 (RET landing pad)
  mprotect(tr, 4096, PROT_READ | PROT_EXEC);
  for (int i = 0; i < kArenaDataPages; ++i) {
    void* d = mmap((void*)(kDataBase + i * 4096), 4096,
                   PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
    if (d == MAP_FAILED) return false;
  }
  void* st = mmap((void*)kStackBase, 4096, PROT_READ | PROT_WRITE,
                  MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
  if (st == MAP_FAILED) return false;
  g_arena.ready = true;
  g_arena.fd = fd;
  g_arena.code_rw = (uint8_t*)rw;
  return true;
}

void UnmapArena() {
  if (!g_arena.ready) return;
  munmap((void*)kCodeBase, 4096);
  munmap(g_arena.code_rw, 4096);
  munmap((void*)kTrampolineBase, 4096);
  for (int i = 0; i < kArenaDataPages; ++i) {
    munmap((void*)(kDataBase + i * 4096), 4096);
  }
  munmap((void*)kStackBase, 4096);
  close(g_arena.fd);
  g_arena = Arena{};
}

bool ResetMappings() {
  for (auto& r : g_regions) {
    if (r.used) {
      if (munmap(reinterpret_cast<void*>(r.start), r.size) != 0) return false;
      r.used = false;
    }
  }
  return true;
}

bool MapRegion(uint64_t start, uint64_t size, uint32_t perms,
               uint32_t data_len, const uint8_t* data) {
  if (start % 4096 != 0 || size == 0 || size % 4096 != 0 ||
      data_len > size) {
    return false;
  }
  for (auto& r : g_regions) {
    if (r.used && start < r.start + r.size && r.start < start + size) {
      return false;  // overlapping command
    }
  }
  void* p = mmap(reinterpret_cast<void*>(start), (size_t)size,
                 PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
  if (p == MAP_FAILED) return false;
  if (data_len > 0) memcpy(p, data, data_len);
  int prot = 0;
  if (perms & kPermRead) prot |= PROT_READ;
  if (perms & kPermWrite) prot |= PROT_WRITE;
  if (perms & kPermExec) prot |= PROT_EXEC;
  if (prot == 0) prot = PROT_NONE;
  if (mprotect(p, (size_t)size, prot) != 0) return false;
  if ((perms & kPermExec) != 0) {
    // ARM64 requires instruction cache maintenance after writing code to a
    // page that may have been executed before (snapshots reuse fixed
    // addresses inside one long-lived harness).
    __builtin___clear_cache((char*)start, (char*)(start + size));
  }
  for (auto& r : g_regions) {
    if (!r.used) {
      r.start = start;
      r.size = size;
      r.perms = perms;
      r.used = true;
      return true;
    }
  }
  return false;
}

const Region* FindRegion(uint64_t start, uint64_t size) {
  for (const auto& r : g_regions) {
    if (r.used && start >= r.start && start + size <= r.start + r.size) {
      return &r;
    }
  }
  return nullptr;
}

void CaptureRegs(RegState* out) {
  for (int i = 0; i < 31; ++i) out->x[i] = g_uc.uc_mcontext.regs[i];
  out->sp = g_uc.uc_mcontext.sp;
  out->pc = g_uc.uc_mcontext.pc;
  out->pstate = g_uc.uc_mcontext.pstate;
  struct fpsimd_context* fp = FindFpsimd(&g_uc);
  if (fp != nullptr) {
    out->fpsr = fp->fpsr;
    out->fpcr = fp->fpcr;
    memcpy(out->v, fp->vregs, sizeof(out->v));
  } else {
    memset(out->v, 0, sizeof(out->v));
    out->fpsr = 0;
    out->fpcr = 0;
  }
}

bool ExecCommand(BufReader* rd, std::string* payload, std::string* error) {
  RegState regs;
  if (!rd->ReadRegs(&regs)) {
    *error = "bad exec payload";
    return false;
  }
  g_init = regs;
  g_entry_error = 0;
  g_phase = 1;
  if (sigsetjmp(g_env, 1) == 0) {
    pid_t tid = (pid_t)syscall(SYS_gettid);
    syscall(SYS_tgkill, getpid(), tid, SIGTRAP);
    // The handler should have redirected execution into the snapshot.
    g_phase = 0;
    *error = "snapshot entry did not transfer control";
    return false;
  }
  if (g_entry_error != 0) {
    *error = "no fpsimd context in signal frame";
    return false;
  }
  RegState out;
  CaptureRegs(&out);
  if (g_inj_reg >= 0 && g_inj_mod > 0 &&
      (g_exec_count % g_inj_mod) == g_inj_rem) {
    uint64_t* target = nullptr;
    if (g_inj_reg >= 0 && g_inj_reg < 31) target = &out.x[g_inj_reg];
    else if (g_inj_reg == 31) target = &out.sp;
    else if (g_inj_reg == 32) target = &out.pc;
    if (target != nullptr && g_inj_bit >= 0 && g_inj_bit < 64) {
      *target ^= (1ULL << g_inj_bit);
    }
  }
  g_exec_count++;
  AppendU32(payload, g_signal);
  AppendU64(payload, g_sig_addr);
  AppendRegs(payload, out);
  return true;
}

}  // namespace

void HarnessMain(int fd, const PlayerOptions& options) {
  ParseInject(options.inject_fault);
  SetupSignals();
  while (true) {
    uint32_t len = 0;
    if (!ReadAll(fd, &len, sizeof(len))) _exit(0);
    if (len == 0 || len > (16u << 20)) _exit(0);
    std::string request;
    request.resize(len);
    if (!ReadAll(fd, request.data(), len)) _exit(0);
    BufReader rd{reinterpret_cast<const uint8_t*>(request.data()) + 1,
                 reinterpret_cast<const uint8_t*>(request.data()) + request.size()};
    uint8_t op = (uint8_t)request[0];
    std::string payload;
    std::string error;
    bool ok = true;
    switch (op) {
      case kOpReset:
        ok = ResetMappings();
        if (!ok) error = "reset failed";
        break;
      case kOpMap: {
        uint64_t start = rd.U64();
        uint64_t size = rd.U64();
        uint32_t perms = rd.U32();
        uint32_t data_len = rd.U32();
        if (!rd.ok || data_len > rd.remaining()) {
          ok = false;
          error = "bad map payload";
          break;
        }
        const uint8_t* data = rd.p;
        if (!MapRegion(start, size, perms, data_len, data)) {
          ok = false;
          error = "mmap failed";
        }
        break;
      }
      case kOpProtect: {
        uint64_t start = rd.U64();
        uint64_t size = rd.U64();
        uint32_t perms = rd.U32();
        const Region* r = FindRegion(start, size);
        int prot = 0;
        if (perms & kPermRead) prot |= PROT_READ;
        if (perms & kPermWrite) prot |= PROT_WRITE;
        if (perms & kPermExec) prot |= PROT_EXEC;
        if (r == nullptr || mprotect((void*)start, size, prot) != 0) {
          ok = false;
          error = "mprotect failed";
        }
        break;
      }
      case kOpChecksum: {
        uint64_t start = rd.U64();
        uint64_t size = rd.U64();
        const Region* r = FindRegion(start, size);
        if (r == nullptr) {
          ok = false;
          error = "checksum outside mapped region";
          break;
        }
        AppendU64(&payload, Fnv1a64((const void*)start, (size_t)size));
        break;
      }
      case kOpExec:
        ok = ExecCommand(&rd, &payload, &error);
        break;
      case kOpRunAll: {
        uint32_t n = rd.U32();
        if (!rd.ok || n == 0 || n > (uint32_t)kMaxRegions) {
          ok = false;
          error = "bad runall mapping count";
          break;
        }
        uint64_t starts[kMaxRegions];
        uint64_t sizes[kMaxRegions];
        uint32_t perms_arr[kMaxRegions];
        const uint8_t* datas[kMaxRegions];
        uint32_t lens[kMaxRegions];
        for (uint32_t i = 0; i < n; ++i) {
          starts[i] = rd.U64();
          sizes[i] = rd.U64();
          perms_arr[i] = rd.U32();
          lens[i] = rd.U32();
          if (!rd.ok || lens[i] > rd.remaining() || lens[i] > sizes[i]) {
            ok = false;
            break;
          }
          datas[i] = rd.p;
          rd.p += lens[i];
        }
        if (!ok) {
          error = "bad runall payload";
          break;
        }
        // Drop mappings left by a previous slow-path snapshot before reusing
        // the fixed arena addresses.
        if (!ResetMappings()) {
          ok = false;
          error = "reset failed";
          break;
        }
        if (!g_arena.ready && !SetupArena()) {
          ok = false;
          error = "arena setup failed";
          break;
        }
        if (ArenaMatches(starts, sizes, perms_arr, n)) {
          // Fast path: rewrite the arena in place.
          for (uint32_t i = 0; i < n; ++i) {
            if (starts[i] == kCodeBase) continue;  // handled below
            if (starts[i] == kTrampolineBase) continue;
            memset((void*)starts[i], 0, (size_t)sizes[i]);
            if (lens[i] > 0) memcpy((void*)starts[i], datas[i], lens[i]);
          }
          memset(g_arena.code_rw, 0, 4096);
          for (uint32_t i = 0; i < n; ++i) {
            if (starts[i] == kCodeBase && lens[i] > 0) {
              memcpy(g_arena.code_rw, datas[i], lens[i]);
            }
          }
          __builtin___clear_cache((char*)kCodeBase, (char*)(kCodeBase + 4096));
        } else {
          UnmapArena();
          for (uint32_t i = 0; i < n; ++i) {
            if (!MapRegion(starts[i], sizes[i], perms_arr[i], lens[i],
                           datas[i])) {
              ok = false;
              error = "mmap failed in runall";
              break;
            }
          }
          if (!ok) break;
        }
        if (!ExecCommand(&rd, &payload, &error)) {
          ok = false;
          break;
        }
        AppendU32(&payload, n);
        for (uint32_t i = 0; i < n; ++i) {
          AppendU64(&payload, Fnv1a64((const void*)starts[i], (size_t)sizes[i]));
        }
        break;
      }
      case kOpQuit:
        _exit(0);
      default:
        ok = false;
        error = "unknown opcode";
    }
    if (!SendResponse(fd, ok ? 0 : 1, ok ? payload : error)) _exit(0);
  }
}

}  // namespace silifuzz
