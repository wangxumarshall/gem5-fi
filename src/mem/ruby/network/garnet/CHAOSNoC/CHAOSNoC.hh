#ifndef __MEM_RUBY_NETWORK_GARNET_CHAOS_NOC_HH__
#define __MEM_RUBY_NETWORK_GARNET_CHAOS_NOC_HH__

#include <random>
#include <string>

#include "params/CHAOSNoC.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"

namespace gem5
{
namespace ruby { namespace garnet { class flit; } }

class CHAOSNoC : public SimObject
{
  public:
    CHAOSNoC(const CHAOSNoCParams &p);
    ~CHAOSNoC();

    // Called from NetworkLink::wakeup AFTER getTopFlit, BEFORE insert.
    // flit_delay: add a random delay to src_delay (F6). route_sub: corrupt
    // the RouteInfo (F5, destination). payload_bitflip: corrupt the msg
    // payload data bytes (raw SDC). Returns true if an injection happened.
    bool maybeCorrupt(ruby::garnet::flit *t_flit);

  private:
    enum class Mode { FlitDelay, RouteSub, PayloadBitflip };
    static Mode stringToMode(const std::string &s);

    Mode fi_mode;
    std::string mode_str;  // for logging
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t fault_mask;
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

#endif // __MEM_RUBY_NETWORK_GARNET_CHAOS_NOC_HH__
