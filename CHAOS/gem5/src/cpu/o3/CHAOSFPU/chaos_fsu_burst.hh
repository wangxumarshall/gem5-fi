#ifndef __CPU_O3_CHAOS_FSU_BURST_HH__
#define __CPU_O3_CHAOS_FSU_BURST_HH__

// [FSU][FP05] Pure burst-episode model for the FSU result-side injector.
//
// The workbook (03-位置x模型矩阵.md FP05 row; 07-展开执行矩阵.md
// FSU-FP05-* rows) defines FP05 as:
//
//   "在 2–4 个连续 eligible 结果上污染同 lane 或相邻 lane；
//    不将 burst 事件当独立 Bernoulli 样本"
//
// A burst is therefore ONE episode over N consecutive ELIGIBLE results
// (N in {2,3,4}), not N independent Bernoulli faults.  FP05-BURST-PREP.md:26
// pre-registers the counting unit: "一次 F0 注入 = 一个 burst episode".
//
// This header deliberately depends only on the C++ standard library so the
// exact state machine / geometry / accounting used by CHAOSFPU can be
// unit-tested on the host (tests/test_chaos_fsu_burst_cpp.py), without a
// gem5 build.
//
// Fixed vs variable parameters (pre-registered)
// ---------------------------------------------
// Fixed for the whole run / episode:
//   * submodel (same_lane | adjacent_lane | cross_lane_mbu | lane_mask)
//   * burst_length N in {2,3,4}
//   * lane geometry: base lane, lane_width, adjacent step
//   * episode count (F0: max_faults == 1 episode per run)
//   * lane_mask submodel: the same pre-registered multi-bit mask every event
// Variable inside an episode (never changes the declared length/id):
//   * burst_ordinal 0..N-1 (strictly sequential, one per eligible event)
//   * the injected lane for adjacent_lane (base + ordinal*step)
//   * the exact bit inside the lane for same_lane/adjacent_lane when no
//     explicit faultMask is pinned (the mask is drawn per event)
//
// Non-eligible events never consume an ordinal.  An episode ends when:
//   * `completed`  : ordinal == length (the normal terminal),
//   * `run_exit`   : simulation ended with an active, incomplete episode,
//   * `lane_geometry`: the pre-registered geometry cannot fit the declared
//     length (fail closed, the episode is never armed).
// A squash is recorded per event but does NOT terminate the episode: the
// episode is defined over consecutive eligible *execution results*, and a
// post-execute squash does not remove the result from that eligible stream.

#include <cstdint>
#include <string>

namespace gem5
{
namespace chaos_fsu
{

enum class BurstSubmodel
{
    None = 0,
    SameLane,
    AdjacentLane,
    CrossLaneMbu,
    LaneMask,
};

inline bool
parseBurstMode(const std::string &mode, BurstSubmodel &out)
{
    if (mode.empty())          { out = BurstSubmodel::None;         return true; }
    if (mode == "same_lane")   { out = BurstSubmodel::SameLane;     return true; }
    if (mode == "adjacent_lane"){ out = BurstSubmodel::AdjacentLane; return true; }
    if (mode == "cross_lane_mbu"){ out = BurstSubmodel::CrossLaneMbu; return true; }
    if (mode == "lane_mask")   { out = BurstSubmodel::LaneMask;     return true; }
    return false;
}

inline const char *
burstModeName(BurstSubmodel m)
{
    switch (m) {
      case BurstSubmodel::SameLane:     return "same_lane";
      case BurstSubmodel::AdjacentLane: return "adjacent_lane";
      case BurstSubmodel::CrossLaneMbu: return "cross_lane_mbu";
      case BurstSubmodel::LaneMask:     return "lane_mask";
      default:                          return "none";
    }
}

// 2 <= N <= 4 is the workbook burst length.  A one-event "burst" is a
// per-event Bernoulli fault, never an FP05 episode.
inline bool
burstLengthValid(uint64_t length)
{
    return length >= 2 && length <= 4;
}

// Number of storage lanes a whole episode touches.
//   same_lane / lane_mask : 1
//   adjacent_lane         : 1 + (N-1)*step
//   cross_lane_mbu        : 2 (one write spans lane and lane+1 every event)
inline int
burstLaneSpan(BurstSubmodel mode, uint64_t length, int lane_step)
{
    switch (mode) {
      case BurstSubmodel::SameLane:
      case BurstSubmodel::LaneMask:
        return 1;
      case BurstSubmodel::AdjacentLane: {
        if (length == 0)
            return 0;
        const int step = lane_step > 0 ? lane_step : 1;
        return 1 + (int)(length - 1) * step;
      }
      case BurstSubmodel::CrossLaneMbu:
        // Two lanes are written by EACH event; the base lane is fixed across
        // the episode so the span is 2, independent of N.
        return 2;
      default:
        return 0;
    }
}

// Lane touched by the event at `ordinal`.  Returns -1 when the ordinal is
// outside the declared episode (callers must reject, never clamp).
inline int
burstLaneAt(BurstSubmodel mode, int base_lane, uint64_t ordinal, int lane_step)
{
    switch (mode) {
      case BurstSubmodel::SameLane:
      case BurstSubmodel::LaneMask:
      case BurstSubmodel::CrossLaneMbu:
        return base_lane;
      case BurstSubmodel::AdjacentLane: {
        const int step = lane_step > 0 ? lane_step : 1;
        return base_lane + (int)ordinal * step;
      }
      default:
        return -1;
    }
}

// Fail-closed geometry validation performed ONCE at episode arm.
//   lanes = 128 / lane_width
//   * base lane must be valid,
//   * the whole span must fit in the 128-bit vector register,
//   * cross_lane_mbu needs a second lane.
inline bool
burstLaneGeometryValid(BurstSubmodel mode, int base_lane, uint64_t length,
                       int lane_step, int lane_width, std::string &err)
{
    if (mode == BurstSubmodel::None) {
        err = "burst mode is not set";
        return false;
    }
    if (!burstLengthValid(length)) {
        err = "burst_length " + std::to_string(length) +
              " outside {2,3,4}";
        return false;
    }
    if (lane_width != 8 && lane_width != 16 && lane_width != 32 &&
        lane_width != 64) {
        err = "lane_width must be 8/16/32/64, got " +
              std::to_string(lane_width);
        return false;
    }
    const int lanes = 128 / lane_width;
    if (base_lane < 0 || base_lane >= lanes) {
        err = "burst base lane " + std::to_string(base_lane) +
              " outside [0," + std::to_string(lanes) + ")";
        return false;
    }
    if (lane_step <= 0 && mode == BurstSubmodel::AdjacentLane) {
        err = "adjacent_lane requires a positive lane_step, got " +
              std::to_string(lane_step);
        return false;
    }
    const int span = burstLaneSpan(mode, length, lane_step);
    if (span <= 0 || base_lane + span > lanes) {
        err = "burst span " + std::to_string(span) + " from base lane " +
              std::to_string(base_lane) + " exceeds " +
              std::to_string(lanes) + " lanes (lane_width " +
              std::to_string(lane_width) + ")";
        return false;
    }
    return true;
}

// ---------------------------------------------------------------------------
// Episode state machine.  Used verbatim by CHAOSFPU::maybeCorrupt().
//
//   arm(id, len, first_eligible_ordinal)   start one episode
//   currentOrdinal()                       next ordinal to apply (0-based)
//   applyOne()                             consume one APPLIED eligible event;
//                                          returns false when not active
//   completed()                            ordinal reached the declared length
//   finish()                               close the episode (id is not reused)
//
// The id counter is monotonic per run; `arm` never reuses an id.  A disabled
// tracker is a fail-closed terminal (lane-geometry rejection): it never arms
// again, so one bad pre-registration cannot silently turn into a stream of
// per-event faults.
// ---------------------------------------------------------------------------
struct BurstEpisodeTracker
{
    bool active = false;
    bool disabled = false;
    uint64_t next_id = 1;
    uint64_t id = 0;
    uint64_t length = 0;
    uint64_t ordinal = 0;
    uint64_t first_eligible_ordinal = 0;
    uint64_t last_eligible_ordinal = 0;

    // Returns true when the episode was armed.  A disabled tracker or an
    // invalid length fails closed.
    bool arm(uint64_t episode_id, uint64_t len,
             uint64_t first_eligible)
    {
        if (disabled || active || !burstLengthValid(len))
            return false;
        id = episode_id;
        length = len;
        ordinal = 0;
        first_eligible_ordinal = first_eligible;
        last_eligible_ordinal = first_eligible;
        next_id = episode_id + 1;
        active = true;
        return true;
    }

    uint64_t currentOrdinal() const
    {
        return active ? ordinal : length;
    }

    // Consume one applied eligible event.  Ordinal advances only here, so
    // non-eligible events (which never call applyOne) cannot consume one.
    bool applyOne(uint64_t &applied_ordinal)
    {
        if (!active || ordinal >= length)
            return false;
        applied_ordinal = ordinal++;
        return true;
    }

    bool completed() const
    {
        return active && ordinal >= length;
    }

    void finish()
    {
        active = false;
    }
};

// End-reason vocabulary (also written on the `burst_end` PROP event).
inline const char *
burstEndReason(bool completed, bool lane_geometry)
{
    if (lane_geometry)
        return "lane_geometry";
    if (completed)
        return "completed";
    return "run_exit";
}

// Episode/event accounting conservation, checked at exit and by the gate:
//   events_attempted >= events_applied == events_activated + not_activated
//   events_applied >= events_squashed (a squashed event was still applied)
//   episodes_attempted == episodes_applied + episodes_lane_rejected
//   episodes_attempted == episodes_completed + episodes_short + lane_rejected
inline bool
burstAccountingConserved(uint64_t events_attempted,
                         uint64_t events_applied,
                         uint64_t events_activated,
                         uint64_t events_squashed,
                         uint64_t episodes_attempted,
                         uint64_t episodes_applied,
                         uint64_t episodes_completed,
                         uint64_t episodes_short,
                         uint64_t episodes_lane_rejected)
{
    if (events_attempted < events_applied)
        return false;
    if (events_activated > events_applied)
        return false;
    if (events_squashed > events_applied)
        return false;
    if (episodes_attempted != episodes_applied + episodes_lane_rejected)
        return false;
    if (episodes_attempted != episodes_completed + episodes_short +
                             episodes_lane_rejected)
        return false;
    return true;
}

} // namespace chaos_fsu
} // namespace gem5

#endif // __CPU_O3_CHAOS_FSU_BURST_HH__
