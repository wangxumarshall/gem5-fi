/*
 * chaos_lsu_tier_cap_test.cc — standalone unit test for the
 * [R6-FIXCPP/T1] lookup-tier runtime capability marker. NOT part of the gem5
 * build; compiled directly:
 *
 *   g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
 *       tests/chaos_lsu_tier_cap_test.cc -o /tmp/tier_cap && /tmp/tier_cap
 *
 * Defect under test: the FIX-TOOLS lookup_tier_capability_gate
 * (tools/lsu_campaign.py ea17e3c9) refuses an F1-F6 ARM-TLB-lookup sample
 * unless the binary printed, once at startup, the CHAOS_LSU_TIER_CAP marker:
 *
 *   CHAOS_LSU_TIER_CAP: requested=<F0..F6|off> effective=<F0..F6|off>
 *                       lookup_tier_enabled=<0|1>
 *
 * This test drives the SAME resolve()/marker() functions CHAOSArmTLB.cc calls
 * (chaos_lsu_tier_cap.hh — one shared definition, no drift) and pins:
 *   [1] the marker line is byte-for-byte the frozen field contract;
 *   [2] F2/F6 (a real non-F0 lookup gate) => requested==effective==<F>,
 *       lookup_tier_enabled=1 (what the tool gate demands);
 *   [3] F0 (off / explicit F0 / no trigger) => F0/F0/0 — the legacy path is
 *       NOT lied about as enabled;
 *   [4] a non-F0 spelling that did NOT mount a non-F0 trigger mismatches
 *       (effective stays F0) => the gate refuses instead of silently
 *       accepting a degenerate F0 run;
 *   [5] every F1..F6 tier resolves consistently (no tier loses its identity).
 */
#include <cstdint>
#include <cstdio>
#include <string>

#include "cpu/o3/chaos_lsu_tier_cap.hh"

using gem5::chaos_lsu_tier_cap::Capability;
using gem5::chaos_lsu_tier_cap::marker;
using gem5::chaos_lsu_tier_cap::resolve;

static int failed = 0;

static void
check(const std::string &name, bool cond, const std::string &detail = "")
{
    if (cond) {
        std::printf("PASS %s\n", name.c_str());
    } else {
        std::printf("FAIL %s%s\n", name.c_str(),
                    detail.empty() ? "" : ("  [" + detail + "]").c_str());
        ++failed;
    }
}

// The tool's gate verdict, mirrored (tools/lsu_campaign.py
// lookup_tier_capability_gate): ok iff effective==requested AND enabled.
static bool
gateOk(const std::string &requested, const Capability &c)
{
    return c.effective == requested && c.enabled
        && (c.requested.empty() || c.requested == requested);
}

int
main()
{
    std::printf("[1] marker line is byte-for-byte the frozen field contract\n");
    {
        const Capability f0 = resolve("off", -1);
        const std::string line = marker(f0);
        std::printf("      %s\n", line.c_str());
        check("F0 line exact",
              line == "CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 "
                      "lookup_tier_enabled=0", line);
    }
    {
        const Capability f2 = resolve("F2", 2);
        const std::string line = marker(f2);
        std::printf("      %s\n", line.c_str());
        check("F2 line exact",
              line == "CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 "
                      "lookup_tier_enabled=1", line);
    }
    {
        const Capability f6 = resolve("F6", 6);
        const std::string line = marker(f6);
        std::printf("      %s\n", line.c_str());
        check("F6 line exact",
              line == "CHAOS_LSU_TIER_CAP: requested=F6 effective=F6 "
                      "lookup_tier_enabled=1", line);
    }
    // field ORDER is part of the contract (the parser is order-tolerant, but
    // the emitted line must stay recognizable with all three keys present).
    {
        const std::string line = marker(resolve("F3", 3));
        const size_t a = line.find("requested=");
        const size_t b = line.find("effective=");
        const size_t c = line.find("lookup_tier_enabled=");
        check("field order requested<effective<lookup_tier_enabled",
              a != std::string::npos && b != std::string::npos
              && c != std::string::npos && a < b && b < c, line);
    }

    std::printf("[2] a real non-F0 gate: effective==requested AND enabled=1\n");
    for (int t = 1; t <= 6; ++t) {
        const std::string name = std::string("F") + char('0' + t);
        const Capability c = resolve(name, t);
        check(name + " gate ok (effective==requested, enabled)",
              gateOk(name, c), marker(c));
        check(name + " requested/effective both " + name,
              c.requested == name && c.effective == name, marker(c));
    }

    std::printf("[3] F0 / off / no-trigger is the legacy path: F0/F0/0 "
                "(never lied as enabled)\n");
    for (auto [param, mounted] :
         std::initializer_list<std::pair<std::string, int>>{
             {"off", -1}, {"off", 0}, {"F0", 0}, {"", -1}}) {
        const Capability c = resolve(param, mounted);
        check("param='" + param + "' mounted=" + std::to_string(mounted)
              + " -> F0/F0/disabled",
              c.requested == "F0" && c.effective == "F0" && !c.enabled,
              marker(c));
    }
    // The legacy run must NOT be advertised as F1-F6 gate-ok.
    {
        const Capability c = resolve("off", -1);
        check("legacy run fails a hypothetical F2 gate", !gateOk("F2", c));
        check("legacy run fails a hypothetical F6 gate", !gateOk("F6", c));
    }

    std::printf("[4] a non-F0 spelling that mounted NO non-F0 trigger "
                "mismatches (refused, not silently F0)\n");
    {
        // e.g. an unknown spelling ("F7") or an F0-typed trigger under a
        // non-F0 param: effective stays F0 while requested is the raw text.
        const Capability c = resolve("F7", 0);
        check("requested reported verbatim (F7)", c.requested == "F7",
              marker(c));
        check("effective stays F0 (nothing non-F0 mounted)",
              c.effective == "F0", marker(c));
        check("gate for F7 refused (mismatch)", !gateOk("F7", c), marker(c));
        check("enabled is 0", !c.enabled, marker(c));
    }

    std::printf("[5] a trigger whose tier is F0 under an F0 param is the "
                "legacy path (no false positive)\n");
    {
        const Capability c = resolve("F0", 0);
        check("F0 trigger => enabled 0", !c.enabled, marker(c));
        check("F0 trigger => effective F0", c.effective == "F0", marker(c));
    }

    std::printf("\n");
    if (failed) {
        std::printf("FAILED (%d)\n", failed);
        return 1;
    }
    std::printf("ALL PASS\n");
    return 0;
}
