#ifndef __CPU_O3_CHAOS_LSU_TIER_CAP_HH__
#define __CPU_O3_CHAOS_LSU_TIER_CAP_HH__

// [MDSPEC][R6-FIXCPP] lookup-tier runtime capability marker.
//
// The campaign's `lookup_tier_capability_gate` (tools/lsu_campaign.py,
// R6-FIXTOOLS ea17e3c9) refuses an F1-F6 ARM-TLB-lookup sample unless the
// landing binary PRINTED, once at startup, a CHAOS_LSU_TIER_CAP marker whose
// effective tier equals the requested one and whose lookup gate is enabled:
//
//   CHAOS_LSU_TIER_CAP: requested=<F0..F6|off> effective=<F0..F6|off>
//                       lookup_tier_enabled=<0|1>
//
// Missing marker            -> capability-missing   (old binary, no marker)
// A field missing/empty     -> capability-malformed
// effective != requested    -> capability-mismatch
// lookup_tier_enabled != 1  -> capability-disabled
// All four are LOUD blocks (blocked=True, admitted=False): a stale binary
// must never produce silent F0-degenerate data under an F2/F6 label.
//
// This header is dependency-free on purpose (same pattern as
// chaos_lsu_trigger.hh / chaos_tlb_chain.hh): CHAOSArmTLB.cc (inside the gem5
// build) and the standalone unit test (tests/chaos_lsu_tier_cap_test.cc,
// compiled with plain g++) share THIS ONE definition, so the marker under
// test is the marker the binary prints — no drift between the regression
// suite and the injector.

#include <string>

namespace gem5
{
namespace chaos_lsu_tier_cap
{

// The injector's Param default spelling for "no tier requested". It IS the
// legacy F0 semantics: NO --tlb_lsu_tier flag, the legacy maxFaults /
// probability gates unchanged. Reported as F0 so the marker reads
// requested=F0 effective=F0 lookup_tier_enabled=0 (F0 is NOT tiered).
static constexpr const char *OFF = "off";

inline bool
isKnownTier(const std::string &s)
{
    return s.size() == 2 && s[0] == 'F' && s[1] >= '0' && s[1] <= '6';
}

struct Capability
{
    std::string requested;   // what the command line asked for (F0..F6)
    std::string effective;   // what the run actually mounted (F0..F6)
    bool enabled = false;    // the lookup path really mounted a non-F0 gate
};

// Resolve the triple from the raw `lsuTier` Param and the tier the mounted
// trigger actually runs.
//   param        — the raw Param.String ("off" = no tier flag).
//   mounted_tier — the mounted trigger's tier as an int (F0=0 .. F6=6), or
//                  -1 when NO trigger object exists at all.
// `off` (or an empty param) is the legacy F0 path: requested=F0,
// effective=F0, enabled=false. A non-F0 spelling that did NOT mount a
// non-F0 trigger (unknown spelling / F0) yields effective=F0 / enabled=false,
// so the marker and the campaign gate disagree LOUDLY instead of the run
// being silently accepted as a degenerate F0 dataset under a tier label.
inline Capability
resolve(const std::string &param, int mounted_tier)
{
    Capability c;
    // "off"/empty is the legacy path — report it as F0 (the tier it is), so
    // F0 runs also carry a self-consistent marker. Any other spelling is
    // reported verbatim (an unknown spelling then mismatches effective and is
    // refused loudly by the gate — never silently downgraded to F0).
    c.requested = (param.empty() || param == OFF) ? std::string("F0") : param;
    if (mounted_tier >= 0 && mounted_tier <= 6)
        c.effective = std::string("F") + static_cast<char>('0' + mounted_tier);
    else
        c.effective = "F0";
    // A non-F0 trigger (F1..F6) means the lookup path polls a REAL tier gate.
    // F0 (and "no trigger") is the legacy path and is NOT tiered.
    c.enabled = (mounted_tier > 0);
    return c;
}

// The exact one-line startup marker (byte-for-byte what the campaign's
// parse_lsu_tier_capability / lookup_tier_capability_gate expect).
inline std::string
marker(const Capability &c)
{
    return std::string("CHAOS_LSU_TIER_CAP: requested=") + c.requested
         + " effective=" + c.effective
         + " lookup_tier_enabled=" + (c.enabled ? "1" : "0");
}

}  // namespace chaos_lsu_tier_cap
}  // namespace gem5

#endif // __CPU_O3_CHAOS_LSU_TIER_CAP_HH__
