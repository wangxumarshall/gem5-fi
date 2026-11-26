#ifndef __MEM_RUBY_CHAOS_CHI_HH__
#define __MEM_RUBY_CHAOS_CHI_HH__

#include <random>
#include <string>

#include "params/CHAOSCHI.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"

namespace gem5
{
namespace ruby { class MessageBuffer; }
namespace ruby { class Message; }
namespace ruby { class NetDest; }

class CHAOSCHI : public SimObject
{
  public:
    CHAOSCHI(const CHAOSCHIParams &p);
    ~CHAOSCHI();

    // Called from MessageBuffer::dequeue BEFORE the message is returned to
    // the controller. msg_delay: delay the message's time (arrives later).
    // msg_drop: return false to signal "drop" (the buffer dequeue proceeds
    //   but the msg is lost — the controller sees an empty/stale state).
    // Returns true if an injection happened (msg_delay); for msg_drop the
    // caller (MessageBuffer) needs to handle the drop separately.
    bool maybeCorrupt(ruby::MessageBuffer *buf);

  private:
    enum class Mode { MsgDelay, MsgDrop, CrossDieMsgDelay, PayloadBitflip };
    static Mode stringToMode(const std::string &s);

    Mode fi_mode;
    std::string mode_str;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
};

} // namespace gem5

#endif // __MEM_RUBY_CHAOS_CHI_HH__
