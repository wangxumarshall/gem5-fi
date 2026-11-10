// Snapshot format unit tests: round-trip, bounds checks, hashes.
#include <stdio.h>
#include <string.h>

#include <string>

#include "silifuzz/snapshot.hh"

using namespace silifuzz;

namespace {
int g_failures = 0;
void Check(bool ok, const std::string& name) {
  printf("%s %s\n", ok ? "PASS" : "FAIL", name.c_str());
  if (!ok) ++g_failures;
}
}  // namespace

int main() {
  // FNV-1a 64 known answer for "abc".
  Check(Fnv1a64("abc", 3) == 0xe71fa2190541574bULL, "fnv1a64 abc");

  Snapshot s;
  s.meta = "{\"source\":\"unit-test\"}";
  s.regs.pc = kCodeBase;
  s.regs.sp = kStackTop;
  s.regs.x[0] = 0x1122334455667788ULL;
  s.regs.v[0][0] = 0xaa;
  MemoryMapping code;
  code.start = kCodeBase;
  code.size = 4096;
  code.perms = kPermRead | kPermExec;
  code.data = {0xa0, 0x00, 0x80, 0xd2, 0x00, 0x00, 0x00, 0xd4};
  s.mappings.push_back(code);
  EndState e;
  e.signal = 5;
  e.sig_addr = kCodeBase + 4;
  e.regs = s.regs;
  e.checksums.push_back({kCodeBase, 4096, 0x1234});
  s.end_states.push_back(e);

  uint64_t id = 0;
  std::string hex = s.ContentHash(&id);
  Check(hex.size() == 64 && id != 0, "content hash shape");
  Check(s.ContentHash(&id) == hex, "content hash stable");
  printf("sample_sha256=%s\n", hex.c_str());

  std::string err;
  std::string enc = s.Encode(&err);
  Check(!enc.empty() && err.empty(), "encode");

  Snapshot t;
  Check(Snapshot::Decode((const uint8_t*)enc.data(), enc.size(), &t, &err),
        "decode");
  Check(t.meta == s.meta && t.mappings.size() == 1 && t.end_states.size() == 1,
        "decoded fields");
  Check(SameEndState(t.end_states[0], e), "decoded end state identical");
  Check(t.regs.x[0] == s.regs.x[0] && t.regs.v[0][0] == 0xaa,
        "decoded registers");

  const std::string path = "work/sample.sfs";
  Check(s.Save(path, &err), "save");
  Snapshot u;
  Check(Snapshot::Load(path, &u, &err), "load");
  Check(u.id == s.id && u.meta == s.meta, "load fields");

  // Corruptions must be rejected without crashing.
  Snapshot bad;
  Check(!Snapshot::Decode((const uint8_t*)"short", 5, &bad, &err),
        "reject short");
  std::string str(enc.size(), '\0');
  memcpy(str.data(), enc.data(), enc.size());
  str[0] = 'X';
  Check(!Snapshot::Decode((const uint8_t*)str.data(), str.size(), &bad, &err),
        "reject bad magic");
  Check(!Snapshot::Decode((const uint8_t*)enc.data(), enc.size() - 3, &bad,
                          &err),
        "reject truncated");
  std::string trailing = enc + "x";
  Check(!Snapshot::Decode((const uint8_t*)trailing.data(), trailing.size(),
                          &bad, &err),
        "reject trailing bytes");

  // SameEndState must notice single-bit register changes.
  EndState e2 = e;
  e2.regs.x[3] ^= 1;
  Check(!SameEndState(e, e2), "end state bit sensitivity");
  EndState e3 = e;
  e3.checksums[0].hash ^= 1;
  Check(!SameEndState(e, e3), "checksum bit sensitivity");

  printf("%s failures=%d\n", g_failures == 0 ? "ALL PASS" : "TESTS FAILED",
         g_failures);
  return g_failures == 0 ? 0 : 1;
}
