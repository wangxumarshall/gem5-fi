#include "silifuzz/player.hh"

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <sched.h>
#include <signal.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include <chrono>
#include <string>

#include "silifuzz/protocol.hh"

namespace silifuzz {
namespace {

using Clock = std::chrono::steady_clock;

int64_t RemainingMs(Clock::time_point deadline) {
  auto now = Clock::now();
  if (now >= deadline) return 0;
  return std::chrono::duration_cast<std::chrono::milliseconds>(deadline - now)
      .count();
}

bool ReadExact(int fd, void* data, size_t size, Clock::time_point deadline) {
  uint8_t* p = static_cast<uint8_t*>(data);
  while (size > 0) {
    int64_t left = RemainingMs(deadline);
    if (left <= 0) return false;
    struct pollfd pfd = {fd, POLLIN, 0};
    int pr = poll(&pfd, 1, (int)left);
    if (pr < 0 && errno == EINTR) continue;
    if (pr <= 0) return false;
    if (pfd.revents & (POLLERR | POLLHUP | POLLNVAL)) return false;
    ssize_t n = read(fd, p, size);
    if (n < 0 && (errno == EINTR || errno == EAGAIN)) continue;
    if (n <= 0) return false;
    p += n;
    size -= (size_t)n;
  }
  return true;
}

bool WriteExact(int fd, const void* data, size_t size) {
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

}  // namespace

Player::~Player() { Stop(); }

void Player::Kill() {
  if (fd_ >= 0) {
    close(fd_);
    fd_ = -1;
  }
  if (pid_ > 0) {
    kill(pid_, SIGKILL);
    int status = 0;
    while (waitpid(pid_, &status, 0) < 0 && errno == EINTR) {
    }
    pid_ = -1;
  }
  started_ = false;
}

void Player::Stop() {
  if (fd_ >= 0) {
    std::string req;
    AppendU32(&req, 1);
    req.push_back((char)kOpQuit);
    WriteExact(fd_, req.data(), req.size());
  }
  Kill();
}

bool Player::Start(const PlayerOptions& options, std::string* err) {
  Stop();
  options_ = options;
  int sv[2];
  if (socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, sv) != 0) {
    if (err) *err = std::string("socketpair: ") + strerror(errno);
    return false;
  }
  pid_t pid = fork();
  if (pid < 0) {
    close(sv[0]);
    close(sv[1]);
    if (err) *err = std::string("fork: ") + strerror(errno);
    return false;
  }
  if (pid == 0) {
    close(sv[0]);
    prctl(PR_SET_PDEATHSIG, SIGKILL);
    if (options_.core >= 0) {
      cpu_set_t set;
      CPU_ZERO(&set);
      CPU_SET(options_.core, &set);
      sched_setaffinity(0, sizeof(set), &set);
    }
    HarnessMain(sv[1], options_);
    _exit(0);
  }
  close(sv[1]);
  pid_ = pid;
  fd_ = sv[0];
  started_ = true;
  return true;
}

bool Player::EnsureStarted(std::string* err) {
  if (started_ && fd_ >= 0) return true;
  return Start(options_, err);
}

bool Player::Request(const std::string& request, std::string* payload,
                     std::string* err) {
  auto deadline = Clock::now() + std::chrono::milliseconds(options_.timeout_ms);
  std::string framed;
  AppendU32(&framed, (uint32_t)request.size());
  framed.append(request);
  if (!WriteExact(fd_, framed.data(), framed.size())) {
    if (err) *err = "harness write failed";
    return false;
  }
  uint32_t len = 0;
  if (!ReadExact(fd_, &len, sizeof(len), deadline)) {
    if (err) *err = "harness response timeout";
    return false;
  }
  if (len == 0 || len > (16u << 20)) {
    if (err) *err = "bad response length";
    return false;
  }
  std::string body;
  body.resize(len);
  if (!ReadExact(fd_, body.data(), len, deadline)) {
    if (err) *err = "harness response read failed";
    return false;
  }
  uint8_t status = (uint8_t)body[0];
  if (status != 0) {
    if (err) *err = body.substr(1);
    return false;
  }
  payload->assign(body.data() + 1, body.size() - 1);
  return true;
}

bool Player::Run(const std::vector<MemoryMapping>& mappings,
                 const RegState& regs, Outcome* out, std::string* err) {
  out->timeout = false;
  if (!EnsureStarted(err)) return false;

  std::string payload;
  {
    std::string req;
    req.push_back((char)kOpReset);
    if (!Request(req, &payload, err)) {
      Kill();
      return false;
    }
  }
  for (const auto& m : mappings) {
    std::string req;
    req.push_back((char)kOpMap);
    AppendU64(&req, m.start);
    AppendU64(&req, m.size);
    AppendU32(&req, m.perms);
    AppendU32(&req, (uint32_t)m.data.size());
    AppendBytes(&req, m.data.data(), m.data.size());
    if (!Request(req, &payload, err)) {
      *err = "map " + Hex64(m.start) + ": " + *err;
      Kill();
      return false;
    }
  }
  {
    std::string req;
    req.push_back((char)kOpExec);
    AppendRegs(&req, regs);
    if (!Request(req, &payload, err)) {
      Kill();
      out->timeout = true;  // the only expected slow path is a looping snapshot
      return false;
    }
  }
  BufReader rd{reinterpret_cast<const uint8_t*>(payload.data()),
               reinterpret_cast<const uint8_t*>(payload.data()) + payload.size()};
  out->signal = rd.U32();
  out->sig_addr = rd.U64();
  if (!rd.ReadRegs(&out->regs)) {
    if (err) *err = "bad exec response";
    Kill();
    return false;
  }
  out->checksums.clear();
  for (const auto& m : mappings) {
    std::string req;
    req.push_back((char)kOpChecksum);
    AppendU64(&req, m.start);
    AppendU64(&req, m.size);
    if (!Request(req, &payload, err)) {
      Kill();
      return false;
    }
    BufReader cr{reinterpret_cast<const uint8_t*>(payload.data()),
                 reinterpret_cast<const uint8_t*>(payload.data()) +
                     payload.size()};
    MemChecksum c;
    c.start = m.start;
    c.size = m.size;
    c.hash = cr.U64();
    if (!cr.ok) {
      if (err) *err = "bad checksum response";
      Kill();
      return false;
    }
    out->checksums.push_back(c);
  }
  return true;
}

}  // namespace silifuzz
