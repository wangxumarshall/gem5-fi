// Snapshot player: driver process + harness child process (paper section 2.3).
#ifndef SILIFUZZ_PLAYER_HH_
#define SILIFUZZ_PLAYER_HH_

#include <sys/types.h>

#include <string>
#include <vector>

#include "silifuzz/snapshot.hh"

namespace silifuzz {

struct PlayerOptions {
  int core = -1;            // pin the harness to this core (-1 = no pinning)
  int timeout_ms = 3000;    // per-snapshot wall-clock limit (paper: 3 s CPU)
  std::string inject_fault; // synthetic defect injection (testing only)
};

struct Outcome {
  uint32_t signal = 0;
  uint64_t sig_addr = 0;
  RegState regs;
  std::vector<MemChecksum> checksums;
  bool timeout = false;
};

class Player {
 public:
  Player() = default;
  ~Player();
  Player(const Player&) = delete;
  Player& operator=(const Player&) = delete;

  bool Start(const PlayerOptions& options, std::string* err);
  void Stop();
  bool started() const { return started_; }
  int core() const { return options_.core; }

  // Maps `mappings`, executes `regs`, then checksums every mapping.
  // Return value is true iff the harness completed; out->timeout signals a
  // snapshot that exceeded the time limit.
  bool Run(const std::vector<MemoryMapping>& mappings, const RegState& regs,
           Outcome* out, std::string* err);

 private:
  bool EnsureStarted(std::string* err);
  bool Request(const std::string& request, std::string* payload,
               std::string* err);
  void Kill();

  PlayerOptions options_;
  pid_t pid_ = -1;
  int fd_ = -1;
  bool started_ = false;
};

// Harness main loop. Runs in the child process (same executable, no exec).
[[noreturn]] void HarnessMain(int fd, const PlayerOptions& options);

}  // namespace silifuzz

#endif  // SILIFUZZ_PLAYER_HH_
