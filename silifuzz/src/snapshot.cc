#include "silifuzz/snapshot.hh"

#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

#include <algorithm>

namespace silifuzz {
namespace {

constexpr char kMagic[8] = {'S', 'I', 'L', 'I', 'F', 'Z', '0', '1'};
constexpr size_t kMaxFileBytes = 16u << 20;
constexpr size_t kMaxMetaBytes = 64u << 10;
constexpr uint32_t kMaxMappings = 64;
constexpr uint32_t kMaxEndStates = 16;
constexpr uint32_t kMaxChecksums = 64;
constexpr uint64_t kMaxMappingSize = 1u << 20;

// ---- SHA-256 (small, self-contained; used for corpus ids) ------------------

struct Sha256 {
  uint32_t h[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                   0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
  uint8_t buf[64] = {};
  uint64_t bits = 0;
  size_t used = 0;

  static uint32_t Rotr(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }

  void Block(const uint8_t* p) {
    static const uint32_t k[64] = {
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
        0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
        0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
        0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
        0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
        0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
        0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
        0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};
    uint32_t w[64];
    for (int i = 0; i < 16; ++i) {
      w[i] = (uint32_t)p[i * 4] << 24 | (uint32_t)p[i * 4 + 1] << 16 |
             (uint32_t)p[i * 4 + 2] << 8 | p[i * 4 + 3];
    }
    for (int i = 16; i < 64; ++i) {
      uint32_t s0 = Rotr(w[i - 15], 7) ^ Rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
      uint32_t s1 = Rotr(w[i - 2], 17) ^ Rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
      w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    uint32_t a = h[0], b = h[1], c = h[2], d = h[3];
    uint32_t e = h[4], f = h[5], g = h[6], hh = h[7];
    for (int i = 0; i < 64; ++i) {
      uint32_t s1 = Rotr(e, 6) ^ Rotr(e, 11) ^ Rotr(e, 25);
      uint32_t ch = (e & f) ^ (~e & g);
      uint32_t t1 = hh + s1 + ch + k[i] + w[i];
      uint32_t s0 = Rotr(a, 2) ^ Rotr(a, 13) ^ Rotr(a, 22);
      uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
      uint32_t t2 = s0 + maj;
      hh = g;
      g = f;
      f = e;
      e = d + t1;
      d = c;
      c = b;
      b = a;
      a = t1 + t2;
    }
    h[0] += a;
    h[1] += b;
    h[2] += c;
    h[3] += d;
    h[4] += e;
    h[5] += f;
    h[6] += g;
    h[7] += hh;
  }

  void Update(const uint8_t* p, size_t n) {
    bits += (uint64_t)n * 8;
    while (n > 0) {
      size_t take = std::min(n, sizeof(buf) - used);
      std::memcpy(buf + used, p, take);
      used += take;
      p += take;
      n -= take;
      if (used == sizeof(buf)) {
        Block(buf);
        used = 0;
      }
    }
  }

  void Final(uint8_t out[32]) {
    uint64_t total_bits = bits;
    uint8_t pad = 0x80;
    Update(&pad, 1);
    uint8_t zero = 0;
    while (used != 56) Update(&zero, 1);
    uint8_t len[8];
    for (int i = 0; i < 8; ++i) len[7 - i] = (uint8_t)(total_bits >> (i * 8));
    Update(len, 8);
    for (int i = 0; i < 8; ++i) {
      out[i * 4] = (uint8_t)(h[i] >> 24);
      out[i * 4 + 1] = (uint8_t)(h[i] >> 16);
      out[i * 4 + 2] = (uint8_t)(h[i] >> 8);
      out[i * 4 + 3] = (uint8_t)h[i];
    }
  }
};

std::string Sha256Hex(const std::string& data) {
  Sha256 s;
  s.Update(reinterpret_cast<const uint8_t*>(data.data()), data.size());
  uint8_t digest[32];
  s.Final(digest);
  static const char* kHex = "0123456789abcdef";
  std::string out;
  out.resize(64);
  for (int i = 0; i < 32; ++i) {
    out[i * 2] = kHex[digest[i] >> 4];
    out[i * 2 + 1] = kHex[digest[i] & 15];
  }
  return out;
}

// ---- little-endian encoding helpers ---------------------------------------

void PutU32(std::string* b, uint32_t v) {
  for (int i = 0; i < 4; ++i) b->push_back((char)(v >> (i * 8)));
}
void PutU64(std::string* b, uint64_t v) {
  for (int i = 0; i < 8; ++i) b->push_back((char)(v >> (i * 8)));
}
void PutBytes(std::string* b, const void* p, size_t n) {
  b->append(reinterpret_cast<const char*>(p), n);
}

struct Reader {
  const uint8_t* p;
  const uint8_t* end;
  bool ok = true;
  bool Need(size_t n) {
    if (!ok || (size_t)(end - p) < n) {
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
};

void EncodeRegs(std::string* b, const RegState& r) {
  for (int i = 0; i < 31; ++i) PutU64(b, r.x[i]);
  PutU64(b, r.sp);
  PutU64(b, r.pc);
  PutU64(b, r.pstate);
  PutU64(b, r.fpcr);
  PutU64(b, r.fpsr);
  PutBytes(b, r.v, sizeof(r.v));
}

bool DecodeRegs(Reader* rd, RegState* r) {
  for (int i = 0; i < 31; ++i) r->x[i] = rd->U64();
  r->sp = rd->U64();
  r->pc = rd->U64();
  r->pstate = rd->U64();
  r->fpcr = rd->U64();
  r->fpsr = rd->U64();
  return rd->Bytes(r->v, sizeof(r->v));
}

std::string EncodeBody(const Snapshot& s, bool with_id, std::string* err) {
  if (s.meta.size() > kMaxMetaBytes) {
    if (err) *err = "metadata too large";
    return {};
  }
  if (s.mappings.size() > kMaxMappings || s.end_states.size() > kMaxEndStates) {
    if (err) *err = "too many mappings or end states";
    return {};
  }
  std::string b;
  b.reserve(1024 + s.mappings.size() * 8192);
  b.append(kMagic, 8);
  PutU32(&b, kFormatVersion);
  PutU32(&b, s.arch);
  PutU32(&b, s.flags);
  PutU64(&b, with_id ? s.id : 0);
  PutU32(&b, (uint32_t)s.meta.size());
  PutBytes(&b, s.meta.data(), s.meta.size());
  EncodeRegs(&b, s.regs);
  PutU32(&b, (uint32_t)s.mappings.size());
  for (const auto& m : s.mappings) {
    if (m.start % kPageSize != 0 || m.size == 0 || m.size % kPageSize != 0 ||
        m.size > kMaxMappingSize || m.data.size() > m.size) {
      if (err) *err = "invalid mapping";
      return {};
    }
    PutU64(&b, m.start);
    PutU64(&b, m.size);
    PutU32(&b, m.perms);
    PutU32(&b, m.data.empty() ? 0u : 1u);
    PutU32(&b, (uint32_t)m.data.size());
    PutBytes(&b, m.data.data(), m.data.size());
  }
  PutU32(&b, (uint32_t)s.end_states.size());
  for (const auto& e : s.end_states) {
    PutU32(&b, e.signal);
    PutU64(&b, e.sig_addr);
    EncodeRegs(&b, e.regs);
    if (e.checksums.size() > kMaxChecksums) {
      if (err) *err = "too many checksums";
      return {};
    }
    PutU32(&b, (uint32_t)e.checksums.size());
    for (const auto& c : e.checksums) {
      PutU64(&b, c.start);
      PutU64(&b, c.size);
      PutU64(&b, c.hash);
    }
  }
  return b;
}

}  // namespace

uint64_t Fnv1a64(const void* data, size_t size) {
  const uint8_t* p = static_cast<const uint8_t*>(data);
  uint64_t h = 14695981039346656037ULL;
  for (size_t i = 0; i < size; ++i) {
    h ^= p[i];
    h *= 1099511628211ULL;
  }
  return h;
}

uint64_t ChecksumRegion(const uint8_t* data, size_t size) {
  return Fnv1a64(data, size);
}

bool SameRegState(const RegState& a, const RegState& b) {
  if (std::memcmp(a.x, b.x, sizeof(a.x)) != 0) return false;
  if (a.sp != b.sp || a.pc != b.pc || a.fpcr != b.fpcr ||
      a.fpsr != b.fpsr)
    return false;
  // Only NZCV is writable by EL0 snapshot code.  Other PSTATE bits (SSBS,
  // PAN, SS, ...) are managed by the kernel and were observed to flip
  // non-reproducibly under full-machine load; they are not part of the
  // snapshot's architectural state.
  if (((a.pstate ^ b.pstate) & 0xF0000000ULL) != 0) return false;
  return std::memcmp(a.v, b.v, sizeof(a.v)) == 0;
}

bool SameEndState(const EndState& a, const EndState& b) {
  if (a.signal != b.signal || a.sig_addr != b.sig_addr) return false;
  if (!SameRegState(a.regs, b.regs)) return false;
  if (a.checksums.size() != b.checksums.size()) return false;
  for (size_t i = 0; i < a.checksums.size(); ++i) {
    if (a.checksums[i].start != b.checksums[i].start ||
        a.checksums[i].size != b.checksums[i].size ||
        a.checksums[i].hash != b.checksums[i].hash)
      return false;
  }
  return true;
}

std::string Hex64(uint64_t v) {
  char buf[19];
  std::snprintf(buf, sizeof(buf), "0x%016llx", (unsigned long long)v);
  return buf;
}

std::string JsonEscape(const std::string& s) {
  std::string out;
  out.reserve(s.size() + 8);
  for (unsigned char c : s) {
    switch (c) {
      case '"': out += "\\\""; break;
      case '\\': out += "\\\\"; break;
      case '\n': out += "\\n"; break;
      case '\r': out += "\\r"; break;
      case '\t': out += "\\t"; break;
      default:
        if (c < 0x20) {
          char buf[7];
          std::snprintf(buf, sizeof(buf), "\\u%04x", c);
          out += buf;
        } else {
          out.push_back((char)c);
        }
    }
  }
  return out;
}

std::string Snapshot::Encode(std::string* err) const {
  return EncodeBody(*this, true, err);
}

bool Snapshot::Decode(const uint8_t* data, size_t size, Snapshot* out,
                      std::string* err) {
  if (size < 8 + 4 * 4 + 8 + 4 || size > kMaxFileBytes) {
    if (err) *err = "bad size";
    return false;
  }
  Reader rd{data, data + size};
  char magic[8];
  if (!rd.Bytes(magic, 8) || std::memcmp(magic, kMagic, 8) != 0) {
    if (err) *err = "bad magic";
    return false;
  }
  uint32_t version = rd.U32();
  if (version != kFormatVersion) {
    if (err) *err = "unsupported version";
    return false;
  }
  out->arch = rd.U32();
  out->flags = rd.U32();
  out->id = rd.U64();
  uint32_t meta_len = rd.U32();
  if (!rd.ok || meta_len > kMaxMetaBytes) {
    if (err) *err = "bad metadata length";
    return false;
  }
  if (!rd.Need(meta_len)) {
    if (err) *err = "truncated metadata";
    return false;
  }
  out->meta.assign((const char*)rd.p, meta_len);
  rd.p += meta_len;
  if (!DecodeRegs(&rd, &out->regs)) {
    if (err) *err = "truncated registers";
    return false;
  }
  uint32_t nmap = rd.U32();
  if (nmap > kMaxMappings) {
    if (err) *err = "too many mappings";
    return false;
  }
  out->mappings.clear();
  for (uint32_t i = 0; i < nmap; ++i) {
    MemoryMapping m;
    m.start = rd.U64();
    m.size = rd.U64();
    m.perms = rd.U32();
    uint32_t kind = rd.U32();
    uint32_t len = rd.U32();
    if (!rd.ok || m.start % kPageSize != 0 || m.size == 0 ||
        m.size % kPageSize != 0 || m.size > kMaxMappingSize || len > m.size ||
        kind > 1) {
      if (err) *err = "bad mapping";
      return false;
    }
    if (kind == 1) m.data.resize(len);
    if (len && !rd.Bytes(m.data.data(), len)) {
      if (err) *err = "truncated mapping data";
      return false;
    }
    out->mappings.push_back(std::move(m));
  }
  uint32_t nend = rd.U32();
  if (nend > kMaxEndStates) {
    if (err) *err = "too many end states";
    return false;
  }
  out->end_states.clear();
  for (uint32_t i = 0; i < nend; ++i) {
    EndState e;
    e.signal = rd.U32();
    e.sig_addr = rd.U64();
    if (!DecodeRegs(&rd, &e.regs)) {
      if (err) *err = "truncated end-state registers";
      return false;
    }
    uint32_t ncs = rd.U32();
    if (ncs > kMaxChecksums) {
      if (err) *err = "too many checksums";
      return false;
    }
    for (uint32_t j = 0; j < ncs; ++j) {
      MemChecksum c;
      c.start = rd.U64();
      c.size = rd.U64();
      c.hash = rd.U64();
      e.checksums.push_back(c);
    }
    if (!rd.ok) {
      if (err) *err = "truncated end state";
      return false;
    }
    out->end_states.push_back(std::move(e));
  }
  if (rd.p != rd.end) {
    if (err) *err = "trailing bytes";
    return false;
  }
  return true;
}

bool Snapshot::Load(const std::string& path, Snapshot* out, std::string* err) {
  int fd = ::open(path.c_str(), O_RDONLY | O_CLOEXEC);
  if (fd < 0) {
    if (err) *err = "cannot open " + path;
    return false;
  }
  struct stat st;
  if (::fstat(fd, &st) != 0 || st.st_size < 0 ||
      (uint64_t)st.st_size > kMaxFileBytes) {
    ::close(fd);
    if (err) *err = "bad file " + path;
    return false;
  }
  std::string buf;
  buf.resize((size_t)st.st_size);
  size_t off = 0;
  while (off < buf.size()) {
    ssize_t n = ::read(fd, buf.data() + off, buf.size() - off);
    if (n <= 0) break;
    off += (size_t)n;
  }
  ::close(fd);
  if (off != buf.size()) {
    if (err) *err = "short read " + path;
    return false;
  }
  return Decode(reinterpret_cast<const uint8_t*>(buf.data()), buf.size(), out,
                err);
}

bool Snapshot::Save(const std::string& path, std::string* err) const {
  std::string body = EncodeBody(*this, true, err);
  if (body.empty()) return false;
  std::string tmp = path + ".tmp." + std::to_string((long)::getpid());
  int fd = ::open(tmp.c_str(), O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
  if (fd < 0) {
    if (err) *err = "cannot create " + tmp;
    return false;
  }
  size_t off = 0;
  while (off < body.size()) {
    ssize_t n = ::write(fd, body.data() + off, body.size() - off);
    if (n <= 0) break;
    off += (size_t)n;
  }
  if (::close(fd) != 0 || off != body.size()) {
    ::unlink(tmp.c_str());
    if (err) *err = "write failed " + tmp;
    return false;
  }
  if (::rename(tmp.c_str(), path.c_str()) != 0) {
    ::unlink(tmp.c_str());
    if (err) *err = "rename failed " + path;
    return false;
  }
  return true;
}

std::string Snapshot::ContentHash(uint64_t* id64) const {
  std::string body = EncodeBody(*this, false, nullptr);
  std::string hex = Sha256Hex(body);
  if (id64) {
    uint64_t v = 0;
    for (int i = 0; i < 16; ++i) {
      char c = hex[i];
      int d = (c >= '0' && c <= '9') ? c - '0' : c - 'a' + 10;
      v = (v << 4) | (uint64_t)d;
    }
    *id64 = v;
  }
  return hex;
}

std::string Snapshot::SummaryJson() const {
  std::string s = "{";
  s += "\"id\":\"" + Hex64(id) + "\"";
  s += ",\"arch\":" + std::to_string(arch);
  s += ",\"pc\":\"" + Hex64(regs.pc) + "\"";
  s += ",\"mappings\":" + std::to_string(mappings.size());
  s += ",\"end_states\":" + std::to_string(end_states.size());
  if (!end_states.empty()) {
    s += ",\"signal\":" + std::to_string(end_states[0].signal);
    s += ",\"sig_addr\":\"" + Hex64(end_states[0].sig_addr) + "\"";
  }
  s += "}";
  return s;
}

}  // namespace silifuzz
