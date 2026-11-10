// sf_checker: run a corpus across many cores (paper section 2.5).
//
// sampled (default): group snapshots in batches, expand each batch into a
// random list of executions (50/1000 by default), distribute the list across
// one player per core.
// sweep: load a chunk of snapshots once, then every core executes every
// snapshot in the chunk (I/O amortized across cores).
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <filesystem>
#include <fstream>
#include <map>
#include <memory>
#include <mutex>
#include <random>
#include <set>
#include <string>
#include <thread>
#include <vector>

#include "silifuzz/player.hh"
#include "silifuzz/snapshot.hh"

namespace fs = std::filesystem;
using namespace silifuzz;
using Clock = std::chrono::steady_clock;

namespace {

struct Args {
  std::string corpus;
  std::string out;
  std::string found;
  std::string inject;
  std::vector<int> cores;
  int seconds = 120;
  std::string mode = "sampled";
  int batch_size = 50;
  int execs_per_batch = 1000;
  int limit_per_core = -1;
  int timeout_ms = 3000;
  uint64_t seed = 1;
  bool log_all = false;
};

struct Stats {
  std::atomic<uint64_t> executions{0};
  std::atomic<uint64_t> mismatches{0};
  std::atomic<uint64_t> timeouts{0};
  std::atomic<uint64_t> errors{0};
  std::atomic<uint64_t> batches{0};
  std::atomic<uint64_t> bytes_read{0};
  std::atomic<uint64_t> snapshot_loads{0};
  std::mutex mu;
  std::map<int, uint64_t> per_core;
  std::map<std::string, uint64_t> error_kinds;
};

std::vector<int> ParseCores(const std::string& spec) {
  std::vector<int> out;
  size_t pos = 0;
  while (pos < spec.size()) {
    size_t comma = spec.find(',', pos);
    std::string tok = spec.substr(pos, comma - pos);
    size_t dash = tok.find('-');
    if (dash == std::string::npos) {
      out.push_back(atoi(tok.c_str()));
    } else {
      int a = atoi(tok.substr(0, dash).c_str());
      int b = atoi(tok.substr(dash + 1).c_str());
      for (int i = a; i <= b; ++i) out.push_back(i);
    }
    if (comma == std::string::npos) break;
    pos = comma + 1;
  }
  return out;
}

std::string FirstDiff(const EndState& e, const Outcome& o) {
  if (e.signal != o.signal) return "signal";
  if (e.sig_addr != o.sig_addr) return "sig_addr";
  if (!SameRegState(e.regs, o.regs)) {
    for (int i = 0; i < 31; ++i) {
      if (e.regs.x[i] != o.regs.x[i]) return "x" + std::to_string(i);
    }
    if (e.regs.sp != o.regs.sp) return "sp";
    if (e.regs.pc != o.regs.pc) return "pc";
    if (e.regs.pstate != o.regs.pstate) return "pstate";
    if (e.regs.fpcr != o.regs.fpcr) return "fpcr";
    if (e.regs.fpsr != o.regs.fpsr) return "fpsr";
    for (int i = 0; i < 32; ++i) {
      if (memcmp(e.regs.v[i], o.regs.v[i], 16) != 0) return "v" + std::to_string(i);
    }
    return "regs";
  }
  if (e.checksums.size() != o.checksums.size()) return "checksum_count";
  for (size_t i = 0; i < e.checksums.size(); ++i) {
    if (e.checksums[i].hash != o.checksums[i].hash) {
      return "mem:" + Hex64(e.checksums[i].start);
    }
  }
  return "unknown";
}

struct Item {
  std::shared_ptr<Snapshot> snap;
  std::string path;
};

bool MatchesAny(const Snapshot& s, const Outcome& o) {
  for (const auto& e : s.end_states) {
    if (e.signal != o.signal || e.sig_addr != o.sig_addr) continue;
    if (!SameRegState(e.regs, o.regs)) continue;
    if (e.checksums.size() != o.checksums.size()) continue;
    bool ok = true;
    for (size_t i = 0; i < e.checksums.size(); ++i) {
      if (e.checksums[i].hash != o.checksums[i].hash) {
        ok = false;
        break;
      }
    }
    if (ok) return true;
  }
  return false;
}

class Queue {
 public:
  explicit Queue(size_t capacity) : capacity_(capacity) {}
  bool Push(Item item) {
    std::unique_lock<std::mutex> lock(mu_);
    while (q_.size() >= capacity_ && !closed_) {
      if (cv_not_full_.wait_for(lock, std::chrono::milliseconds(50)) ==
              std::cv_status::timeout &&
          q_.size() >= capacity_) {
        return false;
      }
    }
    if (closed_) return false;
    q_.push_back(std::move(item));
    cv_not_empty_.notify_one();
    return true;
  }
  bool Pop(Item* item, Clock::time_point deadline) {
    std::unique_lock<std::mutex> lock(mu_);
    while (q_.empty() && !closed_) {
      if (Clock::now() >= deadline) return false;
      cv_not_empty_.wait_for(lock, std::chrono::milliseconds(50));
    }
    if (q_.empty()) return false;
    *item = std::move(q_.front());
    q_.pop_front();
    cv_not_full_.notify_one();
    return true;
  }
  void Close() {
    std::lock_guard<std::mutex> lock(mu_);
    closed_ = true;
    cv_not_empty_.notify_all();
    cv_not_full_.notify_all();
  }

 private:
  size_t capacity_;
  std::deque<Item> q_;
  std::mutex mu_;
  std::condition_variable cv_not_empty_;
  std::condition_variable cv_not_full_;
  bool closed_ = false;
};

// Sweep: each worker executes every snapshot of the current chunk exactly once.
class SweepQueue {
 public:
  SweepQueue(int workers, size_t capacity) : workers_(workers), capacity_(capacity) {}
  bool Publish(std::vector<Item> items, Clock::time_point deadline) {
    std::unique_lock<std::mutex> lock(mu_);
    while (pending_ != 0) {
      if (Clock::now() >= deadline) return false;
      cv_.wait_for(lock, std::chrono::milliseconds(50));
    }
    if (closed_) return false;
    chunk_ = std::make_shared<const std::vector<Item>>(std::move(items));
    ++generation_;
    pending_ = workers_;
    cv_.notify_all();
    return true;
  }
  void Close() {
    std::lock_guard<std::mutex> lock(mu_);
    closed_ = true;
    cv_.notify_all();
  }
  std::shared_ptr<const std::vector<Item>> WaitChunk(uint64_t* seen) {
    std::unique_lock<std::mutex> lock(mu_);
    cv_.wait(lock, [&] { return generation_ != *seen || closed_; });
    if (generation_ == *seen) return nullptr;
    *seen = generation_;
    return chunk_;
  }
  void Done() {
    std::lock_guard<std::mutex> lock(mu_);
    if (pending_ > 0) --pending_;
    cv_.notify_all();
  }

 private:
  int workers_;
  size_t capacity_;
  std::mutex mu_;
  std::condition_variable cv_;
  std::shared_ptr<const std::vector<Item>> chunk_;
  uint64_t generation_ = 0;
  int pending_ = 0;
  bool closed_ = false;
};

bool LoadSnapshot(const std::string& path, std::shared_ptr<Snapshot>* out,
                  uint64_t* bytes, std::string* err) {
  std::error_code ec;
  auto sz = fs::file_size(path, ec);
  if (!ec) *bytes += (uint64_t)sz;
  auto s = std::make_shared<Snapshot>();
  if (!Snapshot::Load(path, s.get(), err)) return false;
  *out = std::move(s);
  return true;
}

std::string SummaryJson(const Args& args, const Stats& stats, double elapsed,
                        size_t corpus_files) {
  char buf[2048];
  snprintf(
      buf, sizeof(buf),
      "{\"mode\":\"%s\",\"corpus_files\":%zu,\"cores\":%zu,"
      "\"seconds\":%d,\"elapsed_s\":%.3f,\"executions\":%llu,"
      "\"exec_per_s\":%.1f,\"mismatches\":%llu,\"timeouts\":%llu,"
      "\"errors\":%llu,\"batches\":%llu,\"snapshot_loads\":%llu,"
      "\"bytes_read\":%llu,\"io_bytes_per_exec\":%.1f,"
      "\"batch_size\":%d,\"execs_per_batch\":%d,\"seed\":%llu}",
      args.mode.c_str(), corpus_files, args.cores.size(), args.seconds, elapsed,
      (unsigned long long)stats.executions.load(),
      elapsed > 0 ? stats.executions.load() / elapsed : 0.0,
      (unsigned long long)stats.mismatches.load(),
      (unsigned long long)stats.timeouts.load(),
      (unsigned long long)stats.errors.load(),
      (unsigned long long)stats.batches.load(),
      (unsigned long long)stats.snapshot_loads.load(),
      (unsigned long long)stats.bytes_read.load(),
      stats.executions.load()
          ? (double)stats.bytes_read.load() / stats.executions.load()
          : 0.0,
      args.batch_size, args.execs_per_batch, (unsigned long long)args.seed);
  return buf;
}

}  // namespace

int main(int argc, char** argv) {
  {
    int harness = HarnessModeMain(argc, argv);
    if (harness >= 0) return harness;
  }
  Args args;
  for (int i = 1; i < argc; ++i) {
    std::string k = argv[i];
    auto next = [&]() -> std::string {
      if (i + 1 >= argc) exit(2);
      return argv[++i];
    };
    if (k == "--corpus") args.corpus = next();
    else if (k == "--out") args.out = next();
    else if (k == "--found") args.found = next();
    else if (k == "--inject") args.inject = next();
    else if (k == "--cores") args.cores = ParseCores(next());
    else if (k == "--seconds") args.seconds = atoi(next().c_str());
    else if (k == "--mode") args.mode = next();
    else if (k == "--batch-size") args.batch_size = atoi(next().c_str());
    else if (k == "--execs-per-batch") args.execs_per_batch = atoi(next().c_str());
    else if (k == "--limit-per-core") args.limit_per_core = atoi(next().c_str());
    else if (k == "--timeout-ms") args.timeout_ms = atoi(next().c_str());
    else if (k == "--seed") args.seed = strtoull(next().c_str(), nullptr, 0);
    else if (k == "--log-all") args.log_all = true;
    else {
      fprintf(stderr, "unknown arg %s\n", k.c_str());
      return 2;
    }
  }
  if (args.corpus.empty() || args.cores.empty() ||
      (args.mode != "sampled" && args.mode != "sweep")) {
    fprintf(stderr,
            "usage: sf_checker --corpus DIR --cores 0-127 [--seconds 120]\n"
            "  --mode sampled|sweep --batch-size 50 --execs-per-batch 1000\n"
            "  --out DIR --found DIR --inject flip:REG:BIT:MOD:REM\n");
    return 2;
  }
  if (args.out.empty()) args.out = "work/checker-" + std::to_string(time(nullptr));
  std::error_code ec;
  fs::create_directories(args.out, ec);
  if (!args.found.empty()) fs::create_directories(args.found, ec);

  std::vector<std::string> files;
  for (auto it = fs::recursive_directory_iterator(args.corpus, ec);
       !ec && it != fs::recursive_directory_iterator(); it.increment(ec)) {
    if (it->is_regular_file() && it->path().extension() == ".sfs") {
      files.push_back(it->path().string());
    }
  }
  std::sort(files.begin(), files.end());
  if (files.empty()) {
    fprintf(stderr, "no snapshots under %s\n", args.corpus.c_str());
    return 1;
  }
  std::mt19937_64 rng(args.seed);

  const auto start_time = Clock::now();
  const auto deadline = start_time + std::chrono::seconds(args.seconds);
  Queue queue(std::max<size_t>(
      1024, (size_t)args.batch_size * 2 * (size_t)args.execs_per_batch));
  SweepQueue sweep((int)args.cores.size(), 4);
  Stats stats;

  std::thread producer([&]() {
    std::vector<std::string> shuffled = files;
    std::shuffle(shuffled.begin(), shuffled.end(), rng);
    if (args.mode == "sampled") {
      std::uniform_int_distribution<size_t> pick(0, files.size() - 1);
      while (Clock::now() < deadline) {
        std::vector<Item> batch;
        while (batch.size() < (size_t)args.batch_size &&
               Clock::now() < deadline) {
          const std::string& path = files[pick(rng)];
          std::shared_ptr<Snapshot> s;
          uint64_t bytes = 0;
          std::string err;
          if (!LoadSnapshot(path, &s, &bytes, &err)) continue;
          stats.bytes_read += bytes;
          stats.snapshot_loads++;
          batch.push_back(Item{std::move(s), path});
        }
        if (batch.empty()) break;
        std::uniform_int_distribution<size_t> idx(0, batch.size() - 1);
        for (int i = 0; i < args.execs_per_batch; ++i) {
          if (!queue.Push(batch[idx(rng)])) break;
        }
        stats.batches++;
      }
      queue.Close();
    } else {
      uint64_t cursor = 0;
      while (cursor < shuffled.size() && Clock::now() < deadline) {
        size_t end = std::min(shuffled.size(), (size_t)cursor + 50);
        std::vector<Item> items;
        for (size_t i = cursor; i < end; ++i) {
          std::shared_ptr<Snapshot> s;
          uint64_t bytes = 0;
          std::string err;
          if (!LoadSnapshot(shuffled[i], &s, &bytes, &err)) continue;
          stats.bytes_read += bytes;
          stats.snapshot_loads++;
          items.push_back(Item{std::move(s), shuffled[i]});
        }
        stats.batches++;
        cursor = end;
        if (items.empty()) continue;
        if (!sweep.Publish(std::move(items), deadline)) break;
      }
      sweep.Close();
    }
  });

  std::mutex mismatch_mu;
  std::ofstream mismatches;
  mismatches.open(args.out + "/mismatches.jsonl", std::ios::app);
  std::vector<std::thread> workers;
  for (int core : args.cores) {
    workers.emplace_back([&, core]() {
      PlayerOptions po;
      po.core = core;
      po.timeout_ms = args.timeout_ms;
      po.inject_fault = args.inject;
      Player player;
      std::string err;
      if (!player.Start(po, &err)) {
        stats.errors++;
        return;
      }
      uint64_t local = 0;
      auto execute = [&](const Item& item) {
        Outcome out;
        if (!player.Run(item.snap->mappings, item.snap->regs, &out, &err)) {
          if (out.timeout) {
            stats.timeouts++;
          } else {
            stats.errors++;
            std::lock_guard<std::mutex> lock(stats.mu);
            stats.error_kinds[err.substr(0, 80)]++;
          }
          return;
        }
        ++local;
        stats.executions++;
        if (MatchesAny(*item.snap, out)) return;
        stats.mismatches++;
        std::lock_guard<std::mutex> lock(mismatch_mu);
        std::string diff = item.snap->end_states.empty()
                               ? "no_expected"
                               : FirstDiff(item.snap->end_states[0], out);
        mismatches << "{\"snapshot\":\"" << JsonEscape(item.path)
                   << "\",\"core\":" << core << ",\"diff\":\""
                   << JsonEscape(diff) << "\",\"expected_signal\":"
                   << (item.snap->end_states.empty()
                           ? 0
                           : item.snap->end_states[0].signal)
                   << ",\"actual_signal\":" << out.signal << ",\"actual_pc\":\""
                   << Hex64(out.regs.pc) << "\",\"expected_pstate\":\""
                   << Hex64(item.snap->end_states.empty() ? 0
                              : item.snap->end_states[0].regs.pstate)
                   << "\",\"actual_pstate\":\"" << Hex64(out.regs.pstate)
                   << "\"}\n";
        mismatches.flush();
        if (!args.found.empty()) {
          std::error_code fec;
          fs::copy_file(item.path,
                        fs::path(args.found) / fs::path(item.path).filename(),
                        fs::copy_options::overwrite_existing, fec);
        }
      };

      if (args.mode == "sweep") {
        uint64_t seen = 0;
        while (Clock::now() < deadline &&
               (args.limit_per_core < 0 || (int)local < args.limit_per_core)) {
          auto chunk = sweep.WaitChunk(&seen);
          if (!chunk) break;
          for (const auto& item : *chunk) {
            if (Clock::now() >= deadline) break;
            if (args.limit_per_core >= 0 &&
                (int)local >= args.limit_per_core)
              break;
            execute(item);
          }
          sweep.Done();
        }
      } else {
        while (Clock::now() < deadline) {
          if (args.limit_per_core >= 0 && (int)local >= args.limit_per_core)
            break;
          Item item;
          if (!queue.Pop(&item, deadline)) break;
          execute(item);
        }
      }
      {
        std::lock_guard<std::mutex> lock(stats.mu);
        stats.per_core[core] = local;
      }
      player.Stop();
    });
  }
  producer.join();
  for (auto& t : workers) t.join();
  mismatches.close();

  double elapsed =
      std::chrono::duration<double>(Clock::now() - start_time).count();
  std::string summary = SummaryJson(args, stats, elapsed, files.size());
  printf("%s\n", summary.c_str());
  {
    std::ofstream f(args.out + "/summary.json");
    f << summary << "\n";
  }
  {
    std::ofstream f(args.out + "/errors.txt");
    std::lock_guard<std::mutex> lock(stats.mu);
    for (const auto& kv : stats.error_kinds) f << kv.second << " " << kv.first << "\n";
  }
  {
    std::ofstream f(args.out + "/per_core.csv");
    f << "core,executions\n";
    std::lock_guard<std::mutex> lock(stats.mu);
    for (const auto& kv : stats.per_core) f << kv.first << "," << kv.second << "\n";
  }
  return stats.mismatches.load() == 0 ? 0 : 3;
}
