// sf_fix: turn raw instruction sequences into validated SiliFuzz snapshots
// (paper section 2.4.4).
//
// Pipeline per candidate:
//   1. reject system-call encodings (SVC/HVC/SMC);
//   2. build an initial snapshot (code/data/stack pages, register state);
//   3. run in the player, adding zero pages for faults inside the data/stack
//      windows (mapping discovery), at most kMaxMappings pages;
//   4. require 3 identical runs on the reference core (determinism);
//   5. require identical end states on all reference cores (4 NUMA nodes);
//   6. record the end state and write the snapshot.
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <unordered_set>
#include <vector>

#include "silifuzz/player.hh"
#include "silifuzz/snapshot.hh"

namespace fs = std::filesystem;
using namespace silifuzz;

namespace {

constexpr uint32_t kBrk = 0xD4200000u;
constexpr size_t kMaxCodeBytes = 1024;
constexpr size_t kMaxMappings = 32;
constexpr uint64_t kTrampolineBase = 0x10001000;

struct Args {
  std::vector<std::string> in;
  std::string out;
  std::string rejected;
  std::string stats;
  std::string source = "unknown";
  std::vector<int> ref_cores = {0, 32, 64, 96};
  int jobs = 8;
  int limit = -1;
  int timeout_ms = 3000;
  int repeat = 3;
  int keep_rejected_limit = 200;
  bool spread = false;
};

struct Stats {
  std::atomic<uint64_t> candidates{0};
  std::atomic<uint64_t> accepted{0};
  std::atomic<uint64_t> duplicates{0};
  std::atomic<uint64_t> executions{0};
  std::mutex mu;
  std::map<std::string, uint64_t> reasons;
  void Reject(const std::string& reason) {
    std::lock_guard<std::mutex> lock(mu);
    reasons[reason]++;
  }
};

uint64_t SplitMix64(uint64_t* state) {
  uint64_t z = (*state += 0x9e3779b97f4a7c15ULL);
  z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
  z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
  return z ^ (z >> 31);
}

bool IsSyscall(uint32_t w) {
  uint32_t op = w & 0xFFE0001Fu;
  return op == 0xD4000001u || op == 0xD4000002u || op == 0xD4000003u;
}

RegState InitRegs(const std::vector<uint8_t>& code) {
  uint64_t s = Fnv1a64(code.data(), code.size());
  RegState r;
  r.pc = kCodeBase;
  r.sp = kStackTop;
  for (int i = 0; i < 31; ++i) {
    if (i % 2 == 0) {
      // Half of the registers point into the (zero-filled) data window so
      // loads/stores usually complete; the rest exerciseALU/FP values.
      r.x[i] = kDataBase + (SplitMix64(&s) % (4 * kPageSize));
    } else {
      r.x[i] = SplitMix64(&s) % 0x10000;
    }
  }
  r.x[30] = kTrampolineBase;  // RET lands on a BRK trampoline
  for (int i = 0; i < 32; ++i) {
    uint64_t lo = SplitMix64(&s);
    uint64_t hi = SplitMix64(&s);
    memcpy(r.v[i], &lo, 8);
    memcpy(r.v[i] + 8, &hi, 8);
  }
  r.pstate = 0;
  r.fpcr = 0;
  r.fpsr = 0;
  return r;
}

MemoryMapping Page(uint64_t start, uint32_t perms,
                   const std::vector<uint8_t>& data = {}) {
  MemoryMapping m;
  m.start = start;
  m.size = kPageSize;
  m.perms = perms;
  m.data = data;
  return m;
}

bool InWindow(uint64_t addr) {
  return (addr >= kDataBase && addr < kDataBase + 0x10000) ||
         (addr >= kStackBase && addr < kStackBase + 0x10000);
}

bool HasPage(const std::vector<MemoryMapping>& maps, uint64_t page) {
  for (const auto& m : maps) {
    if (page >= m.start && page < m.start + m.size) return true;
  }
  return false;
}

std::string NowUnix() {
  return std::to_string((long long)time(nullptr));
}

std::string MetaJson(const Args& args, uint64_t cand_hash, size_t code_bytes,
                     size_t mappings, size_t attempts) {
  char buf[512];
  snprintf(buf, sizeof(buf),
           "{\"source\":\"%s\",\"candidate\":\"0x%016llx\",\"code_bytes\":%zu,"
           "\"mappings\":%zu,\"attempts\":%zu,\"created_unix\":%s,"
           "\"fixer\":\"sf_fix\"}",
           JsonEscape(args.source).c_str(), (unsigned long long)cand_hash,
           code_bytes, mappings, attempts, NowUnix().c_str());
  return buf;
}

struct RejectWriter {
  std::mutex mu;
  std::map<std::string, int> counts;
  void Write(const std::string& dir, const std::string& reason,
             const std::vector<uint8_t>& data, uint64_t hash, int limit) {
    if (dir.empty() || limit <= 0) return;
    std::lock_guard<std::mutex> lock(mu);
    int& n = counts[reason];
    if (n >= limit) return;
    ++n;
    std::string rd = dir + "/" + reason;
    std::error_code ec;
    fs::create_directories(rd, ec);
    char name[64];
    snprintf(name, sizeof(name), "%016llx.bin", (unsigned long long)hash);
    std::string path = rd + "/" + name;
    FILE* f = fopen(path.c_str(), "wb");
    if (f != nullptr) {
      fwrite(data.data(), 1, data.size(), f);
      fclose(f);
    }
  }
};

struct Worker {
  std::vector<int> cores;
  std::vector<std::unique_ptr<Player>> players;
  bool Ensure(int idx, const std::vector<int>& cores, int timeout_ms,
              std::string* err) {
    if (players.empty()) players.resize(cores.size());
    if (players[idx]) return true;
    auto p = std::make_unique<Player>();
    PlayerOptions o;
    o.core = cores[idx];
    o.timeout_ms = timeout_ms;
    if (!p->Start(o, err)) return false;
    players[idx] = std::move(p);
    return true;
  }
};

bool EqualOutcome(const Outcome& a, const Outcome& b) {
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

EndState ToEndState(const Outcome& o) {
  EndState e;
  e.signal = o.signal;
  e.sig_addr = o.sig_addr;
  e.regs = o.regs;
  e.checksums = o.checksums;
  return e;
}

struct Fixer {
  Args args;
  Stats stats;
  RejectWriter rejected;
  std::mutex out_mu;
  std::unordered_set<uint64_t> seen;
  std::map<std::string, bool> created;
  std::atomic<uint64_t> done{0};

  bool MakeShard(const std::string& dir) {
    std::lock_guard<std::mutex> lock(out_mu);
    if (created.count(dir)) return true;
    std::error_code ec;
    fs::create_directories(dir, ec);
    created[dir] = true;
    return !ec;
  }

  void Process(const std::vector<uint8_t>& raw, Worker* w) {
    stats.candidates++;
    std::vector<uint8_t> code = raw;
    if (code.size() < 4 || code.size() > kMaxCodeBytes) {
      stats.Reject("size");
      return;
    }
    code.resize(code.size() & ~(size_t)3);  // 4-byte aligned ARM64 stream
    if (code.empty()) {
      stats.Reject("size");
      return;
    }
    for (size_t i = 0; i + 4 <= code.size(); i += 4) {
      uint32_t w32;
      memcpy(&w32, code.data() + i, 4);
      if (IsSyscall(w32)) {
        stats.Reject("syscall");
        rejected.Write(args.rejected, "syscall", code, Fnv1a64(code.data(), code.size()),
                       args.keep_rejected_limit);
        return;
      }
    }
    uint64_t cand_hash = Fnv1a64(code.data(), code.size());
    {
      std::lock_guard<std::mutex> lock(out_mu);
      if (!seen.insert(cand_hash).second) {
        stats.duplicates++;
        return;
      }
    }

    std::vector<MemoryMapping> maps;
    std::vector<uint8_t> page_data = code;
    uint32_t brk = kBrk;
    page_data.insert(page_data.end(), (uint8_t*)&brk, (uint8_t*)&brk + 4);
    maps.push_back(Page(kCodeBase, kPermRead | kPermExec, page_data));
    std::vector<uint8_t> tramp = {0x00, 0x00, 0x20, 0xd4};  // brk #0
    maps.push_back(Page(kTrampolineBase, kPermRead | kPermExec, tramp));
    maps.push_back(Page(kStackBase, kPermRead | kPermWrite));
    for (int i = 0; i < 4; ++i) {
      maps.push_back(Page(kDataBase + i * kPageSize, kPermRead | kPermWrite));
    }
    RegState regs = InitRegs(code);
    const bool debug = getenv("SF_DEBUG") != nullptr;

    if (!w->Ensure(0, w->cores, args.timeout_ms, nullptr)) {
      stats.Reject("harness_start");
      return;
    }
    Outcome out;
    std::string err;
    size_t attempts = 0;
    for (; attempts < kMaxMappings; ++attempts) {
      if (!w->players[0]->Run(maps, regs, &out, &err)) {
        stats.executions++;
        stats.Reject(out.timeout ? "timeout" : "harness_error");
        return;
      }
      stats.executions++;
      if (debug) {
        fprintf(stderr,
                "debug: cand=%016llx x0=%016llx maps=%zu run=%zu sig=%u "
                "pc=%016llx addr=%016llx\n",
                (unsigned long long)cand_hash,
                (unsigned long long)regs.x[0], maps.size(), attempts,
                out.signal, (unsigned long long)out.regs.pc,
                (unsigned long long)out.sig_addr);
      }
      if ((out.signal == SIGSEGV || out.signal == SIGBUS) &&
          InWindow(out.sig_addr) && !HasPage(maps, out.sig_addr & ~0xfffULL) &&
          maps.size() < kMaxMappings) {
        maps.push_back(Page(out.sig_addr & ~0xfffULL, kPermRead | kPermWrite));
        continue;
      }
      break;
    }
    if (out.signal == SIGSYS) {
      stats.Reject("syscall_runtime");
      return;
    }
    // Determinism: identical outcome on repeated runs of the reference core.
    EndState baseline = ToEndState(out);
    for (int i = 1; i < args.repeat; ++i) {
      Outcome again;
      if (!w->players[0]->Run(maps, regs, &again, &err)) {
        stats.executions++;
        stats.Reject(again.timeout ? "timeout" : "harness_error");
        return;
      }
      stats.executions++;
      if (!EqualOutcome(out, again)) {
        stats.Reject("nondeterministic");
        rejected.Write(args.rejected, "nondeterministic", code, cand_hash,
                       args.keep_rejected_limit);
        return;
      }
    }
    // Cross-core end-state agreement (4 NUMA nodes).
    for (size_t i = 1; i < args.ref_cores.size(); ++i) {
      if (!w->Ensure((int)i, w->cores, args.timeout_ms, nullptr)) {
        stats.Reject("harness_start");
        return;
      }
      Outcome other;
      if (!w->players[i]->Run(maps, regs, &other, &err)) {
        stats.executions++;
        stats.Reject(other.timeout ? "timeout" : "harness_error");
        return;
      }
      stats.executions++;
      if (!EqualOutcome(out, other)) {
        stats.Reject("multi_state");
        rejected.Write(args.rejected, "multi_state", code, cand_hash,
                       args.keep_rejected_limit);
        return;
      }
    }

    Snapshot s;
    s.meta = MetaJson(args, cand_hash, code.size(), maps.size(), attempts);
    s.regs = regs;
    s.mappings = std::move(maps);
    s.end_states.push_back(baseline);
    uint64_t id = 0;
    std::string hash = s.ContentHash(&id);
    s.id = id;
    std::string sub = args.out + "/" + hash.substr(0, 2);
    if (!MakeShard(sub)) {
      stats.Reject("io");
      return;
    }
    std::string out_path = sub + "/" + hash + ".sfs";
    if (!s.Save(out_path, &err)) {
      stats.Reject("io");
      return;
    }
    stats.accepted++;
    uint64_t n = done++;
    if (n % 1000 == 0) {
      fprintf(stderr, "progress: candidates=%llu accepted=%llu dup=%llu\n",
              (unsigned long long)stats.candidates.load(),
              (unsigned long long)stats.accepted.load(),
              (unsigned long long)stats.duplicates.load());
    }
  }

  void Run() {
    std::vector<std::string> files;
    for (const auto& dir : args.in) {
      std::error_code ec;
      for (auto it = fs::recursive_directory_iterator(dir, ec);
           !ec && it != fs::recursive_directory_iterator(); it.increment(ec)) {
        if (it->is_regular_file()) files.push_back(it->path().string());
      }
    }
    std::sort(files.begin(), files.end());
    if (args.limit >= 0 && (int)files.size() > args.limit) {
      files.resize(args.limit);
    }
    fprintf(stderr, "sf_fix: %zu candidate files, %zu ref cores, %d jobs\n",
            files.size(), args.ref_cores.size(), args.jobs);
    std::atomic<size_t> next{0};
    auto start = std::chrono::steady_clock::now();
    std::vector<std::thread> threads;
    for (int t = 0; t < args.jobs; ++t) {
      threads.emplace_back([&, t]() {
        Worker w;
        if (args.spread) {
          w.cores = {t % 32, 32 + t % 32, 64 + t % 32, 96 + t % 32};
        } else {
          w.cores = args.ref_cores;
        }
        while (true) {
          size_t idx = next.fetch_add(1);
          if (idx >= files.size()) break;
          std::string path = files[idx];
          std::string data;
          {
            FILE* f = fopen(path.c_str(), "rb");
            if (f == nullptr) {
              stats.Reject("io");
              continue;
            }
            fseek(f, 0, SEEK_END);
            long n = ftell(f);
            fseek(f, 0, SEEK_SET);
            if (n < 0 || n > 1 << 20) {
              fclose(f);
              stats.Reject("size");
              continue;
            }
            data.resize((size_t)n);
            if (n > 0 && fread(data.data(), 1, (size_t)n, f) != (size_t)n) {
              fclose(f);
              stats.Reject("io");
              continue;
            }
            fclose(f);
          }
          Process(std::vector<uint8_t>(data.begin(), data.end()), &w);
        }
        for (auto& p : w.players) {
          if (p) p->Stop();
        }
      });
    }
    for (auto& th : threads) th.join();
    double elapsed = std::chrono::duration<double>(
                         std::chrono::steady_clock::now() - start)
                         .count();
    std::string json = "{";
    json += "\"source\":\"" + JsonEscape(args.source) + "\"";
    json += ",\"candidates\":" + std::to_string(stats.candidates.load());
    json += ",\"accepted\":" + std::to_string(stats.accepted.load());
    json += ",\"duplicates\":" + std::to_string(stats.duplicates.load());
    json += ",\"executions\":" + std::to_string(stats.executions.load());
    char ebuf[64];
    snprintf(ebuf, sizeof(ebuf), "%.3f", elapsed);
    json += ",\"elapsed_s\":" + std::string(ebuf);
    json += ",\"reasons\":{";
    bool first = true;
    {
      std::lock_guard<std::mutex> lock(stats.mu);
      for (const auto& kv : stats.reasons) {
        if (!first) json += ",";
        first = false;
        json += "\"" + kv.first + "\":" + std::to_string(kv.second);
      }
    }
    json += "}}";
    printf("%s\n", json.c_str());
    if (!args.stats.empty()) {
      FILE* f = fopen(args.stats.c_str(), "w");
      if (f != nullptr) {
        fputs(json.c_str(), f);
        fputc('\n', f);
        fclose(f);
      }
    }
  }
};

int Usage() {
  fprintf(stderr,
          "usage: sf_fix --in DIR [--in DIR...] --out DIR --source TAG\n"
          "       [--rejected DIR] [--stats FILE] [--jobs N] [--limit N]\n"
          "       [--ref-cores 0,32,64,96] [--repeat 3] [--timeout-ms 3000]\n");
  return 2;
}

bool ParseArgs(int argc, char** argv, Args* a) {
  for (int i = 1; i < argc; ++i) {
    std::string k = argv[i];
    auto next = [&]() -> std::string {
      if (i + 1 >= argc) exit(2);
      return argv[++i];
    };
    if (k == "--in") a->in.push_back(next());
    else if (k == "--out") a->out = next();
    else if (k == "--rejected") a->rejected = next();
    else if (k == "--stats") a->stats = next();
    else if (k == "--source") a->source = next();
    else if (k == "--jobs") a->jobs = atoi(next().c_str());
    else if (k == "--limit") a->limit = atoi(next().c_str());
    else if (k == "--repeat") a->repeat = atoi(next().c_str());
    else if (k == "--timeout-ms") a->timeout_ms = atoi(next().c_str());
    else if (k == "--keep-rejected-limit")
      a->keep_rejected_limit = atoi(next().c_str());
    else if (k == "--spread") a->spread = true;
    else if (k == "--ref-cores") {
      a->ref_cores.clear();
      std::string v = next();
      size_t pos = 0;
      while (pos < v.size()) {
        size_t comma = v.find(',', pos);
        std::string tok = v.substr(pos, comma - pos);
        a->ref_cores.push_back(atoi(tok.c_str()));
        if (comma == std::string::npos) break;
        pos = comma + 1;
      }
    } else {
      return false;
    }
  }
  return !a->in.empty() && !a->out.empty();
}

}  // namespace

int main(int argc, char** argv) {
  {
    int harness = HarnessModeMain(argc, argv);
    if (harness >= 0) return harness;
  }
  Args args;
  if (!ParseArgs(argc, argv, &args)) return Usage();
  if (args.ref_cores.empty() || args.jobs < 1) return Usage();
  Fixer fixer;
  fixer.args = args;
  fixer.Run();
  return 0;
}
