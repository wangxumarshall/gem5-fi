// Driver <-> harness command protocol (paper section 2.3).
#ifndef SILIFUZZ_PROTOCOL_HH_
#define SILIFUZZ_PROTOCOL_HH_

#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

#include "silifuzz/snapshot.hh"

namespace silifuzz {

// Requests. Responses use status 0 = ok, 1 = error, plus optional payload.
enum Op : uint8_t {
  kOpReset = 1,     // drop all snapshot mappings
  kOpMap = 2,       // u64 start, u64 size, u32 perms, u32 data_len, bytes
  kOpProtect = 3,   // u64 start, u64 size, u32 perms
  kOpChecksum = 4,  // u64 start, u64 size -> u64 hash
  kOpExec = 5,      // RegState -> u32 signal, u64 addr, RegState
  kOpQuit = 6,
  kOpRunAll = 7,  // maps + exec + checksums + reset in one round trip
};

inline void AppendU32(std::string* b, uint32_t v) {
  for (int i = 0; i < 4; ++i) b->push_back((char)(v >> (i * 8)));
}
inline void AppendU64(std::string* b, uint64_t v) {
  for (int i = 0; i < 8; ++i) b->push_back((char)(v >> (i * 8)));
}
inline void AppendRegs(std::string* b, const RegState& r) {
  for (int i = 0; i < 31; ++i) AppendU64(b, r.x[i]);
  AppendU64(b, r.sp);
  AppendU64(b, r.pc);
  AppendU64(b, r.pstate);
  AppendU64(b, r.fpcr);
  AppendU64(b, r.fpsr);
  b->append(reinterpret_cast<const char*>(r.v), sizeof(r.v));
}
inline void AppendBytes(std::string* b, const void* p, size_t n) {
  b->append(static_cast<const char*>(p), n);
}

struct BufReader {
  const uint8_t* p;
  const uint8_t* end;
  bool ok = true;
  size_t remaining() const { return (size_t)(end - p); }
  bool Need(size_t n) {
    if (!ok || remaining() < n) {
      ok = false;
      return false;
    }
    return true;
  }
  uint8_t U8() {
    if (!Need(1)) return 0;
    return *p++;
  }
  uint32_t U32() {
    if (!Need(4)) return 0;
    uint32_t v = 0;
    for (int i = 0; i < 4; ++i) v |= (uint32_t)p[i] << (i * 8);
    p += 4;
    return v;
  }
  uint64_t U64() {
    if (!Need(8)) return 0;
    uint64_t v = 0;
    for (int i = 0; i < 8; ++i) v |= (uint64_t)p[i] << (i * 8);
    p += 8;
    return v;
  }
  bool Bytes(void* out, size_t n) {
    if (!Need(n)) return false;
    std::memcpy(out, p, n);
    p += n;
    return true;
  }
  bool ReadRegs(RegState* r) {
    for (int i = 0; i < 31; ++i) r->x[i] = U64();
    r->sp = U64();
    r->pc = U64();
    r->pstate = U64();
    r->fpcr = U64();
    r->fpsr = U64();
    return Bytes(r->v, sizeof(r->v));
  }
};

}  // namespace silifuzz

#endif  // SILIFUZZ_PROTOCOL_HH_
