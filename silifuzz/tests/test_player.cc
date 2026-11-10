// End-to-end player tests on real ARM64 hardware.
#include <signal.h>
#include <stdio.h>
#include <string.h>

#include <string>
#include <vector>

#include "silifuzz/player.hh"
#include "silifuzz/snapshot.hh"

using namespace silifuzz;

namespace {

int g_failures = 0;

void Check(bool ok, const std::string& name, const std::string& detail = "") {
  if (ok) {
    printf("PASS %s\n", name.c_str());
  } else {
    printf("FAIL %s %s\n", name.c_str(), detail.c_str());
    ++g_failures;
  }
}

MemoryMapping Map(uint64_t start, uint32_t perms,
                  const std::vector<uint32_t>& code) {
  MemoryMapping m;
  m.start = start;
  m.size = kPageSize;
  m.perms = perms;
  m.data.resize(code.size() * 4);
  memcpy(m.data.data(), code.data(), m.data.size());
  return m;
}

Snapshot MakeSnapshot(const std::vector<uint32_t>& code, uint64_t x1 = 0) {
  Snapshot s;
  s.mappings.push_back(Map(kCodeBase, kPermRead | kPermExec, code));
  MemoryMapping stack;
  stack.start = kStackBase;
  stack.size = kStackSize;
  stack.perms = kPermRead | kPermWrite;
  s.mappings.push_back(stack);
  s.regs.pc = kCodeBase;
  s.regs.sp = kStackTop;
  s.regs.x[1] = x1;
  return s;
}

EndState Capture(const Outcome& o) {
  EndState e;
  e.signal = o.signal;
  e.sig_addr = o.sig_addr;
  e.regs = o.regs;
  e.checksums = o.checksums;
  return e;
}

}  // namespace

int main() {
  PlayerOptions options;
  options.core = 0;
  options.timeout_ms = 3000;
  Player player;
  std::string err;
  if (!player.Start(options, &err)) {
    printf("FAIL start: %s\n", err.c_str());
    return 1;
  }

  // 1. ALU: mov x0,#5; add x0,x0,x0; brk.
  {
    Snapshot s = MakeSnapshot({0xd28000a0, 0x8b000000, 0xd4200000});
    Outcome out;
    bool ok = player.Run(s.mappings, s.regs, &out, &err);
    Check(ok, "alu run", err);
    Check(out.signal == SIGTRAP, "alu ends with SIGTRAP",
          "signal=" + std::to_string(out.signal));
    Check(out.regs.x[0] == 10, "alu x0 == 10", Hex64(out.regs.x[0]));
    Check(out.regs.pc == kCodeBase + 8, "alu pc", Hex64(out.regs.pc));
    EndState e = Capture(out);
    Outcome again;
    bool ok2 = player.Run(s.mappings, s.regs, &again, &err);
    Check(ok2 && SameEndState(e, Capture(again)), "alu deterministic");
  }

  // 2. FP: fmov d0,#1.0; fadd d0,d0,d0; fmov x0,d0; brk.
  {
    Snapshot s = MakeSnapshot(
        {0x1e6e1000, 0x1e602800, 0x9e660000, 0xd4200000});
    Outcome out;
    bool ok = player.Run(s.mappings, s.regs, &out, &err);
    Check(ok, "fp run", err);
    Check(out.regs.x[0] == 0x4000000000000000ULL, "fp 1.0+1.0 == 2.0",
          Hex64(out.regs.x[0]));
  }

  // 3. Memory: store 7 at 0x20000000, load, add.
  {
    Snapshot s = MakeSnapshot(
        {0xd2a40001, 0xd28000e0, 0xf9000020, 0xf9400022, 0x8b000043,
         0xd4200000});
    MemoryMapping data;
    data.start = kDataBase;
    data.size = kPageSize;
    data.perms = kPermRead | kPermWrite;
    s.mappings.push_back(data);
    Outcome out;
    bool ok = player.Run(s.mappings, s.regs, &out, &err);
    Check(ok, "mem run", err);
    Check(out.regs.x[3] == 14, "mem load/store x3 == 14",
          Hex64(out.regs.x[3]));
    uint8_t zero_page[kPageSize] = {};
    bool data_changed = false;
    for (const auto& c : out.checksums) {
      if (c.start == kDataBase && c.hash != Fnv1a64(zero_page, kPageSize)) {
        data_changed = true;
      }
    }
    Check(data_changed, "mem data page checksum observed");
  }

  // 4. Fault: load from unmapped address.
  {
    Snapshot s = MakeSnapshot({0xf9400022}, 0xdead0000);
    Outcome out;
    bool ok = player.Run(s.mappings, s.regs, &out, &err);
    Check(ok, "fault run", err);
    Check(out.signal == SIGSEGV, "fault SIGSEGV",
          "signal=" + std::to_string(out.signal));
    Check(out.sig_addr == 0xdead0000, "fault address", Hex64(out.sig_addr));
  }

  // 5. Illegal instruction.
  {
    Snapshot s = MakeSnapshot({0x00000000, 0xd4200000});
    Outcome out;
    bool ok = player.Run(s.mappings, s.regs, &out, &err);
    Check(ok, "illegal run", err);
    Check(out.signal == SIGILL, "illegal SIGILL",
          "signal=" + std::to_string(out.signal));
  }

  // 6. Timeout and recovery.
  {
    PlayerOptions fast = options;
    fast.timeout_ms = 200;
    Player p2;
    Check(p2.Start(fast, &err), "timeout player start", err);
    Snapshot s = MakeSnapshot({0x14000000});  // b .
    Outcome out;
    bool ok = p2.Run(s.mappings, s.regs, &out, &err);
    Check(!ok && out.timeout, "loop timeout", err);
    Snapshot s2 = MakeSnapshot({0xd28000a0, 0xd4200000});
    Outcome out2;
    bool ok2 = p2.Run(s2.mappings, s2.regs, &out2, &err);
    Check(ok2 && out2.regs.x[0] == 5, "recovery after timeout", err);
  }

  // 7. Pinned to the requested core (sanity; harness is a child process).
  Check(player.core() == 0, "core option recorded");

  player.Stop();
  printf("%s failures=%d\n", g_failures == 0 ? "ALL PASS" : "TESTS FAILED",
         g_failures);
  return g_failures == 0 ? 0 : 1;
}
