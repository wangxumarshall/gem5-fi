// SiliFuzz snapshot format (paper section 2.2) -- ARM64.
//
// A snapshot is a self-contained, single-threaded program: initial register
// state, memory mappings with permissions and data, expected end state(s), and
// metadata describing how it was produced. Addresses are absolute; snapshots
// are played one at a time.
#ifndef SILIFUZZ_SNAPSHOT_HH_
#define SILIFUZZ_SNAPSHOT_HH_

#include <cstdint>
#include <string>
#include <vector>

namespace silifuzz {

constexpr uint64_t kPageSize = 4096;
constexpr uint64_t kCodeBase = 0x10000000;
constexpr uint64_t kDataBase = 0x20000000;
constexpr uint64_t kStackBase = 0x30000000;
constexpr uint64_t kStackSize = 0x1000;
constexpr uint64_t kStackTop = kStackBase + 0x800;
constexpr uint32_t kArchAArch64 = 1;
constexpr uint32_t kFormatVersion = 1;

// Permission bits used in the on-disk format and in mmap/mprotect calls.
enum Perm : uint32_t { kPermRead = 1, kPermWrite = 2, kPermExec = 4 };

struct RegState {
  uint64_t x[31] = {};
  uint64_t sp = 0;
  uint64_t pc = 0;
  uint64_t pstate = 0;  // NZCV in bits 28..31 for EL0.
  uint64_t fpcr = 0;
  uint64_t fpsr = 0;
  uint8_t v[32][16] = {};
};

// A mapping is page-aligned. `data` may be shorter than `size`; the remainder
// is zero-filled (paper section 2.4.4: added pages are filled with zeroes).
struct MemoryMapping {
  uint64_t start = 0;
  uint64_t size = 0;
  uint32_t perms = 0;
  std::vector<uint8_t> data;
};

struct MemChecksum {
  uint64_t start = 0;
  uint64_t size = 0;
  uint64_t hash = 0;
};

struct EndState {
  uint32_t signal = 0;
  uint64_t sig_addr = 0;
  RegState regs;
  std::vector<MemChecksum> checksums;
};

struct Snapshot {
  uint32_t arch = kArchAArch64;
  uint32_t flags = 0;
  uint64_t id = 0;
  std::string meta;  // JSON object
  RegState regs;
  std::vector<MemoryMapping> mappings;
  std::vector<EndState> end_states;

  // Serializes to `path` (atomic replace). Returns false and sets *err.
  bool Save(const std::string& path, std::string* err) const;
  // Loads from `path` with strict bounds checking.
  static bool Load(const std::string& path, Snapshot* out, std::string* err);
  // Serializes into memory (id is included as stored).
  std::string Encode(std::string* err) const;
  static bool Decode(const uint8_t* data, size_t size, Snapshot* out,
                     std::string* err);
  // SHA-256 over the canonical encoding with id zeroed; fills *hex (64 chars)
  // and *id64 (first 8 bytes, little endian).
  std::string ContentHash(uint64_t* id64) const;
  // One-line JSON summary (for logs); does not include memory contents.
  std::string SummaryJson() const;
};

uint64_t Fnv1a64(const void* data, size_t size);
uint64_t ChecksumRegion(const uint8_t* data, size_t size);

// Exact end-state comparison (registers, signal, fault address, checksums).
bool SameEndState(const EndState& a, const EndState& b);
bool SameRegState(const RegState& a, const RegState& b);

std::string Hex64(uint64_t v);
std::string JsonEscape(const std::string& s);

}  // namespace silifuzz

#endif  // SILIFUZZ_SNAPSHOT_HH_
