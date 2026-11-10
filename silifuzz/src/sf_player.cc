#include <signal.h>
// sf_player: play one snapshot or a corpus on one core (paper section 2.3).
#include <stdio.h>

#include <algorithm>
#include <cstring>
#include <filesystem>
#include <string>
#include <vector>

#include "silifuzz/player.hh"
#include "silifuzz/snapshot.hh"

namespace fs = std::filesystem;
using namespace silifuzz;

namespace {

struct Args {
  std::string snapshot;
  std::string corpus;
  int core = -1;
  int repeat = 1;
  int limit = -1;
  int timeout_ms = 3000;
  std::string inject;
  std::string capture;
  bool verbose = false;
};

std::string SignalName(uint32_t sig) {
  switch (sig) {
    case SIGTRAP: return "SIGTRAP";
    case SIGSEGV: return "SIGSEGV";
    case SIGILL: return "SIGILL";
    case SIGFPE: return "SIGFPE";
    case SIGBUS: return "SIGBUS";
    case SIGSYS: return "SIGSYS";
    default: return std::to_string(sig);
  }
}

std::string OutcomeJson(const Outcome& o) {
  char buf[512];
  snprintf(buf, sizeof(buf),
           "{\"signal\":%u,\"signal_name\":\"%s\",\"sig_addr\":\"%s\","
           "\"pc\":\"%s\",\"sp\":\"%s\",\"x0\":\"%s\",\"timeout\":%s}",
           o.signal, SignalName(o.signal).c_str(), Hex64(o.sig_addr).c_str(),
           Hex64(o.regs.pc).c_str(), Hex64(o.regs.sp).c_str(),
           Hex64(o.regs.x[0]).c_str(), o.timeout ? "true" : "false");
  return buf;
}

EndState ToEndState(const Outcome& o) {
  EndState e;
  e.signal = o.signal;
  e.sig_addr = o.sig_addr;
  e.regs = o.regs;
  e.checksums = o.checksums;
  return e;
}

bool RunOne(Player* player, const Snapshot& s, Outcome* out, std::string* err) {
  return player->Run(s.mappings, s.regs, out, err);
}

int Usage() {
  fprintf(stderr,
          "usage: sf_player --snapshot FILE [--core N] [--repeat K]\n"
          "       sf_player --corpus DIR [--core N] [--limit N]\n"
          "options: --timeout-ms MS --inject flip:REG:BIT:MOD:REM --capture FILE --verbose\n");
  return 2;
}

bool ParseArgs(int argc, char** argv, Args* a) {
  for (int i = 1; i < argc; ++i) {
    std::string k = argv[i];
    auto next = [&](const char* name) -> const char* {
      if (i + 1 >= argc) {
        fprintf(stderr, "missing value for %s\n", name);
        exit(2);
      }
      return argv[++i];
    };
    if (k == "--snapshot") a->snapshot = next("--snapshot");
    else if (k == "--corpus") a->corpus = next("--corpus");
    else if (k == "--core") a->core = atoi(next("--core"));
    else if (k == "--repeat") a->repeat = atoi(next("--repeat"));
    else if (k == "--limit") a->limit = atoi(next("--limit"));
    else if (k == "--timeout-ms") a->timeout_ms = atoi(next("--timeout-ms"));
    else if (k == "--inject") a->inject = next("--inject");
    else if (k == "--capture") a->capture = next("--capture");
    else if (k == "--verbose") a->verbose = true;
    else return false;
  }
  return !a->snapshot.empty() ^ !a->corpus.empty();
}

}  // namespace

int main(int argc, char** argv) {
  {
    int harness = HarnessModeMain(argc, argv);
    if (harness >= 0) return harness;
  }
  Args args;
  if (!ParseArgs(argc, argv, &args)) return Usage();
  PlayerOptions options;
  options.core = args.core;
  options.timeout_ms = args.timeout_ms;
  options.inject_fault = args.inject;
  Player player;
  std::string err;
  if (!player.Start(options, &err)) {
    fprintf(stderr, "player start failed: %s\n", err.c_str());
    return 1;
  }

  if (!args.snapshot.empty()) {
    Snapshot s;
    if (!Snapshot::Load(args.snapshot, &s, &err)) {
      fprintf(stderr, "load failed: %s\n", err.c_str());
      return 1;
    }
    if (!args.capture.empty()) {
      Outcome out;
      if (!RunOne(&player, s, &out, &err)) {
        fprintf(stderr, "capture run failed: %s\n", err.c_str());
        return 1;
      }
      EndState e = ToEndState(out);
      s.end_states.assign(1, e);
      uint64_t id = 0;
      s.ContentHash(&id);
      s.id = id;
      if (!s.Save(args.capture, &err)) {
        fprintf(stderr, "capture save failed: %s\n", err.c_str());
        return 1;
      }
      printf("{\"captured\":\"%s\",\"observed\":%s}\n",
             JsonEscape(args.capture).c_str(), OutcomeJson(out).c_str());
      return 0;
    }
    int failures = 0;
    for (int i = 0; i < args.repeat; ++i) {
      Outcome out;
      if (!RunOne(&player, s, &out, &err)) {
        printf("{\"run\":%d,\"ok\":false,\"error\":\"%s\",\"timeout\":%s}\n", i,
               JsonEscape(err).c_str(), out.timeout ? "true" : "false");
        ++failures;
        continue;
      }
      bool match = false;
      for (const auto& e : s.end_states) {
        if (SameEndState(e, ToEndState(out))) {
          match = true;
          break;
        }
      }
      printf("{\"run\":%d,\"ok\":%s,\"match\":%s,\"observed\":%s}\n", i,
             match ? "true" : "false", match ? "true" : "false",
             OutcomeJson(out).c_str());
      if (!match) ++failures;
    }
    return failures == 0 ? 0 : 1;
  }

  std::vector<std::string> files;
  std::error_code ec;
  for (auto it = fs::recursive_directory_iterator(args.corpus, ec);
       !ec && it != fs::recursive_directory_iterator(); it.increment(ec)) {
    if (it->is_regular_file() && it->path().extension() == ".sfs") {
      files.push_back(it->path().string());
    }
  }
  std::sort(files.begin(), files.end());
  if (args.limit >= 0 && (int)files.size() > args.limit) {
    files.resize(args.limit);
  }
  int failures = 0;
  int timeouts = 0;
  int loaded = 0;
  for (const auto& path : files) {
    Snapshot s;
    if (!Snapshot::Load(path, &s, &err)) {
      fprintf(stderr, "skip %s: %s\n", path.c_str(), err.c_str());
      ++failures;
      continue;
    }
    ++loaded;
    Outcome out;
    if (!RunOne(&player, s, &out, &err)) {
      if (out.timeout) ++timeouts;
      if (args.verbose) {
        fprintf(stderr, "run error %s: %s\n", path.c_str(), err.c_str());
      }
      ++failures;
      continue;
    }
    bool match = false;
    for (const auto& e : s.end_states) {
      if (SameEndState(e, ToEndState(out))) {
        match = true;
        break;
      }
    }
    if (!match) {
      ++failures;
      printf("{\"mismatch\":\"%s\",\"observed\":%s}\n", path.c_str(),
             OutcomeJson(out).c_str());
    }
  }
  printf("{\"corpus\":\"%s\",\"loaded\":%d,\"failures\":%d,\"timeouts\":%d}\n",
         args.corpus.c_str(), loaded, failures, timeouts);
  return failures == 0 ? 0 : 1;
}
