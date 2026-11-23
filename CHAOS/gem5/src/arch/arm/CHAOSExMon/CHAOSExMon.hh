#ifndef __ARCH_ARM_CHAOS_EX_MON_HH__
#define __ARCH_ARM_CHAOS_EX_MON_HH__

#include <optional>
#include <random>
#include <string>

#include "params/CHAOSExMon.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"  // BaseCPU (clockPeriod via ClockedObject), BaseISA forward

namespace gem5
{

namespace ArmISA { class ISA; }

class CHAOSExMon : public SimObject
{
  public:
    CHAOSExMon(const CHAOSExMonParams &p);
    ~CHAOSExMon();

    // Called from ISA::handleLockedWrite AFTER the lock_flag check decides
    // success/failure. `would_succeed` is the monitor's true verdict; the
    // injector may invert it (stxr_force_success: false->true; stxr_force_fail:
    // true->false). Returns the (possibly corrupted) verdict. FS-only is NOT
    // required here — handleLockedWrite fires in SE too (LDXR/STXR in SE).
    bool maybeCorrupt(const RequestPtr &req, bool would_succeed);

    // W8 O-series (03-design-matrix O01/O02), called from ISA::
    // handleLockedRead AFTER the monitor is placed. Returns the corrupted
    // monitor value when the fault fires (the call site writes LOCKADDR/
    // LOCKFLAG), nullopt otherwise:
    //   O01MonitorAddrBitflip  one architecturally-visible bit (>= 6:
    //     lockedWriteHandler masks both sides with cacheBlockMask, so bits
    //     <6 are don't-care and excluded from sampling) of the monitor
    //     address XORed — the reservation now mismatches the STXR block.
    //     Data untouched; a retry loop absorbs the transient failure =>
    //     Masked on a well-formed probe, livelock => Timeout.
    //   O02MonitorStateCorrupt 50% clear the flag (valid清零 — monitor
    //     lost), 50% repoint the reservation at the neighboring 64B block
    //     (伪造/version-旧值 proxy). HONEST: gem5 models the monitor as
    //     flag+addr misc regs only — the xlsx row's version/granule
    //     sub-fields do not exist in this host structure (documented).
    struct MonitorVal { Addr addr; bool flag; };
    std::optional<MonitorVal> maybeCorruptMonitor(const RequestPtr &req);

  private:
    enum class Mode { StxrForceSuccess, StxrForceFail,
                      O01MonitorAddrBitflip, O02MonitorStateCorrupt };
    static Mode stringToMode(const std::string &s);

    // isa (raw; SELF-ATTACH: ctor sets isa->chaosExMon = this, same pattern
    // as CHAOSArmSysReg). handleLockedWrite reaches us via isa->chaosExMon.
    ArmISA::ISA *isa = nullptr;
    BaseCPU *cpu = nullptr;  // for clockPeriod-correct inWindow (may be NULL)
    Mode fi_mode;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;
    // Sampling-bias fix (findings.md Phase 2.2/3.0): number of eligible
    // STXR events to skip before the first injection, drawn geometric(0.1)
    // from the seed, so maxFaults=1 lands on a seed-dependent event.
    uint64_t events_to_skip = 0;

    // [MDSPEC][H6] ptag of the currently-active monitor-side fault (0 =
    // none). The STXR-consumption event attaches to it: LDXR places the
    // (corrupted) monitor, the paired STXR consumes it — the LL-SC pairing
    // is the shared key across the two events.
    uint64_t active_monitor_ptag = 0;

    // [MDSPEC][H6] STXR attempts observed against the active monitor. The
    // LL-SC probe is a software retry loop: every failed STXR is retried,
    // so the consumption node is emitted per attempt carrying its 1-based
    // attempt number (spec sheet 9 O01: "成功/失败/重试"). Reset when a new
    // monitor fault is injected.
    uint64_t active_monitor_attempts = 0;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
};

} // namespace gem5

#endif // __ARCH_ARM_CHAOS_EX_MON_HH__
