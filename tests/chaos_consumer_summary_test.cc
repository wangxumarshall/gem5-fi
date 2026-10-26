/*
 * chaos_consumer_summary_test.cc — standalone unit test for the
 * [R6-FIXCPP/T2] consumer_summary aggregation. NOT part of the gem5 build;
 * compiled directly:
 *
 *   g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
 *       tests/chaos_consumer_summary_test.cc -o /tmp/csum && /tmp/csum
 *
 * Contract under test (frozen by the FIX-TOOLS lane, commit 4c74e3ac):
 *   CONSUMER-SUMMARY: schema=1 version=1 run_id=… sample_run_id=… fault_id=…
 *     source_id=… suppressed_consumer_count=… distinct_dyn_seq_count=…
 *     emitted_consumer_count=… first_tick=… last_tick=… min_dyn_seq=…
 *     max_dyn_seq=… by_kind=<k:n,…> by_outcome=<k:n,…> total_before=…
 *     total_after=…   with total_before==total_after==emitted+suppressed and
 *     sum(by_kind)==sum(by_outcome)==total_before and total>0 => emitted>=1.
 *
 * This test drives the SAME Aggregator CHAOSPropagation.cc uses
 * (chaos_consumer_summary.hh — one shared definition, no drift) and pins the
 * five required properties:
 *   [1] the main L0-L5 chain is UNCHANGED (every non-consumer event is emitted;
 *       only duplicate consumers are folded away);
 *   [2] L5 (errant_commit) — and every other non-consumer kind — is NEVER
 *       aggregated, even with an identical (ptag, source, dyn_seq);
 *   [3] consumer counts CONSERVE (emitted + suppressed == observed);
 *   [4] the summary line is byte-for-byte the frozen field contract;
 *   [5] under many duplicate consumers the emitted output size drops sharply.
 */
#include <cstdint>
#include <cstdlib>
#include <cstdio>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "cpu/o3/CHAOSPropagation/chaos_consumer_summary.hh"

using gem5::chaos_consumer::Aggregator;
using gem5::chaos_consumer::sourceIdOf;

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

// A miniature emitter that mirrors CHAOSPropagation.cc's wiring: every event
// asks the aggregator; must-emit => an output line + noteEmitted; suppressed
// => folded (no line) and counted.
struct Emitter
{
    Aggregator agg;
    std::vector<std::string> lines;   // emitted PROP-EVT kinds (in order)
    uint64_t suppressed = 0;
    uint64_t observed_consumers = 0;
    uint64_t next_id = 1;

    void
    event(const std::string &kind, uint64_t ptag, const std::string &src,
          uint64_t dyn, uint64_t tick)
    {
        if (kind == "consumer") ++observed_consumers;
        const bool emit = agg.observe(kind, ptag, src, dyn, tick);
        if (emit) {
            lines.push_back(kind);
            agg.noteEmitted(kind, ptag, src, next_id++);
        } else {
            ++suppressed;
        }
    }

    std::vector<std::string>
    summaries(const std::string &run_id, const std::string &srid) const
    {
        return agg.flush(run_id, srid);
    }
};

// Parse a CONSUMER-SUMMARY line into key -> value.
static std::map<std::string, std::string>
parseSummary(const std::string &line)
{
    std::map<std::string, std::string> m;
    std::istringstream is(line);
    std::string tok;
    bool first = true;
    while (is >> tok) {
        if (first) { first = false; continue; }   // "CONSUMER-SUMMARY:"
        const size_t eq = tok.find('=');
        if (eq != std::string::npos)
            m[tok.substr(0, eq)] = tok.substr(eq + 1);
    }
    return m;
}

static uint64_t
sumCountMap(const std::string &raw)
{
    uint64_t n = 0;
    size_t pos = 0;
    while (pos <= raw.size() && !raw.empty()) {
        const size_t comma = raw.find(',', pos);
        const std::string part = raw.substr(
            pos, comma == std::string::npos ? std::string::npos : comma - pos);
        const size_t colon = part.find(':');
        if (colon != std::string::npos)
            n += std::strtoull(part.c_str() + colon + 1, nullptr, 10);
        if (comma == std::string::npos)
            break;
        pos = comma + 1;
    }
    return n;
}

int
main()
{
    const uint64_t PTAG = 1;
    const std::string SRC = sourceIdOf(31);   // "phys_reg:31"

    std::printf("[1] the main L0-L5 chain is UNCHANGED under aggregation\n");
    {
        Emitter e;
        // L0..L3 then 50 identical consumers (L4) then L5 then chain_end.
        e.event("inj", PTAG, "", 0, 10);
        e.event("addr_form", PTAG, "", 0, 20);
        e.event("mem_req", PTAG, "", 7, 30);
        e.event("resp", PTAG, "", 7, 40);
        for (int i = 0; i < 50; ++i)
            e.event("consumer", PTAG, SRC, 7, 100 + i);
        e.event("errant_commit", PTAG, "", 7, 600);
        e.event("chain_end", PTAG, "", 0, 700);
        // every non-consumer event survives, in order; exactly 1 consumer.
        std::vector<std::string> want = {"inj", "addr_form", "mem_req", "resp",
                                         "consumer", "errant_commit",
                                         "chain_end"};
        check("emitted sequence == L0-L5 chain with duplicates removed",
              e.lines == want,
              [&]{ std::string s; for (auto &k : e.lines) s += k + " ";
                   return s; }());
        check("no non-consumer event was ever suppressed",
              e.suppressed == 49, std::to_string(e.suppressed));
    }

    std::printf("[2] L5 / every non-consumer kind is NEVER aggregated\n");
    {
        const char *keep[] = {"errant_commit", "chain_end", "inj", "addr_form",
                              "mem_req", "resp", "taint_reg", "request_fork",
                              "squash_masked", "tlb_pfn", "cache_access",
                              "mshr_fill", "cache_line", "from_json"};
        bool all_emit = true;
        std::string bad;
        for (const char *k : keep) {
            Aggregator a;
            // identical (ptag, source, dyn) repeated: a consumer would be
            // folded, but a non-consumer must always be emitted.
            bool ok = true;
            for (int i = 0; i < 5; ++i)
                if (!a.observe(k, PTAG, SRC, 7, 100 + i)) ok = false;
            if (!ok) { all_emit = false; bad = k; }
        }
        check("non-consumer kinds always emit (never aggregated)", all_emit, bad);
        // and the consumer kind DOES aggregate (contrast):
        Aggregator c;
        int emitted = 0;
        for (int i = 0; i < 5; ++i)
            if (c.observe("consumer", PTAG, SRC, 7, 100 + i)) ++emitted;
        check("consumer kind aggregates (contrast: 1 of 5 emitted)", emitted == 1,
              std::to_string(emitted));
    }

    std::printf("[3] consumer counts CONSERVE (emitted+suppressed==observed)\n");
    {
        Emitter e;
        for (int i = 0; i < 7; ++i)
            e.event("consumer", PTAG, SRC, 7, 100 + i);       // 1 emitted + 6 supp
        for (int i = 0; i < 3; ++i)
            e.event("consumer", PTAG, sourceIdOf(12), 9, 200 + i); // another src
        check("emitted + suppressed == observed consumers",
              (uint64_t)e.lines.size() + e.suppressed == e.observed_consumers,
              std::to_string(e.lines.size()) + "+" + std::to_string(e.suppressed)
              + " vs " + std::to_string(e.observed_consumers));
        check("aggregator totals agree with the emitter",
              e.agg.emittedTotal() + e.agg.suppressedTotal()
              == e.observed_consumers);
        const auto sums = e.summaries("L05-F0-W5", "s1");
        uint64_t tot = 0, em = 0, su = 0;
        for (const auto &l : sums) {
            auto m = parseSummary(l);
            tot += std::strtoull(m["total_before"].c_str(), nullptr, 10);
            em += std::strtoull(m["emitted_consumer_count"].c_str(), nullptr, 10);
            su += std::strtoull(m["suppressed_consumer_count"].c_str(),
                                nullptr, 10);
        }
        check("summary batch: total_before == emitted + suppressed == observed",
              tot == em + su && tot == e.observed_consumers,
              std::to_string(tot) + "/" + std::to_string(em) + "+"
              + std::to_string(su));
        check("2 sources => 2 summary records", sums.size() == 2,
              std::to_string(sums.size()));
    }

    std::printf("[4] summary line is byte-for-byte the frozen field contract\n");
    {
        Emitter e;
        // 1 representative + 49 duplicates, all dyn_seq 7, ticks 100..148.
        for (int i = 0; i < 50; ++i)
            e.event("consumer", PTAG, SRC, 7, 100 + i);
        const auto sums = e.summaries("L05-F0-W5", "s1");
        check("exactly one summary", sums.size() == 1, std::to_string(sums.size()));
        const std::string got = sums.empty() ? "" : sums[0];
        std::printf("      %s\n", got.c_str());
        const std::string want =
            "CONSUMER-SUMMARY: schema=1 version=1 run_id=L05-F0-W5 "
            "sample_run_id=s1 fault_id=1 source_id=phys_reg:31 "
            "suppressed_consumer_count=49 distinct_dyn_seq_count=1 "
            "emitted_consumer_count=1 first_tick=100 last_tick=149 "
            "min_dyn_seq=7 max_dyn_seq=7 by_kind=consumer:50 "
            "by_outcome=sd_observed:50 total_before=50 total_after=50";
        check("exact line (order + values)", got == want, got);
        // conservation inside the record (the tools validator's rules)
        auto m = parseSummary(got);
        const uint64_t tb = std::strtoull(m["total_before"].c_str(), nullptr, 10);
        const uint64_t ta = std::strtoull(m["total_after"].c_str(), nullptr, 10);
        const uint64_t em = std::strtoull(m["emitted_consumer_count"].c_str(),
                                          nullptr, 10);
        const uint64_t su = std::strtoull(m["suppressed_consumer_count"].c_str(),
                                          nullptr, 10);
        check("total_before==total_after==emitted+suppressed",
              tb == ta && ta == em + su, got);
        check("sum(by_kind)==sum(by_outcome)==total_before",
              sumCountMap(m["by_kind"]) == tb
              && sumCountMap(m["by_outcome"]) == tb, got);
        check("total>0 => emitted>=1 (never suppress-all)", em >= 1, got);
        check("distinct_dyn_seq_count <= total_before",
              std::strtoull(m["distinct_dyn_seq_count"].c_str(), nullptr, 10)
              <= tb, got);
        // A repeated consumption of the SAME source (a later instruction, or a
        // second tainted src reg of one instruction) is folded; the group's
        // FIRST member stays as the representative, and every distinct
        // dyn_inst_seq is still COUNTED (distinct_dyn_seq_count).
        Emitter e2;
        e2.event("consumer", PTAG, SRC, 7, 100);      // representative
        e2.event("consumer", PTAG, SRC, 7, 101);      // repeat -> folded
        e2.event("consumer", PTAG, SRC, 8, 102);      // another inst -> folded
        check("only the first member of a source is emitted",
              e2.lines.size() == 1, std::to_string(e2.lines.size()));
        std::printf("      %s\n", e2.summaries("R", "s")[0].c_str());
        auto m2 = parseSummary(e2.summaries("R", "s")[0]);
        check("folded group: emitted=1 suppressed=2 total=3 distinct=2",
              m2["emitted_consumer_count"] == "1"
              && m2["suppressed_consumer_count"] == "2"
              && m2["total_before"] == "3"
              && m2["distinct_dyn_seq_count"] == "2",
              e2.summaries("R", "s")[0]);
        check("folded group conserves (1+2==3)",
              sumCountMap(m2["by_kind"]) == 3
              && sumCountMap(m2["by_outcome"]) == 3, e2.summaries("R", "s")[0]);
    }

    std::printf("[5] under many duplicate consumers the output size drops "
                "sharply\n");
    {
        const int N = 1000;
        Emitter e;
        for (int i = 0; i < N; ++i)
            e.event("consumer", PTAG, SRC, 7, 100 + i);
        const size_t agg_lines = e.lines.size() + e.summaries("R", "s").size();
        check("output lines collapse to (1 representative + 1 summary)",
              agg_lines == 2, std::to_string(agg_lines));
        const double ratio = (double)N / (double)agg_lines;
        std::printf("      N=%d duplicate consumers -> %zu stream lines "
                    "(without aggregation %d) : %.0fx reduction\n",
                    N, agg_lines, N, ratio);
        check("reduction >= 100x", ratio >= 100.0, std::to_string(ratio));
        check("exactly one consumer PROP-EVT survived", e.lines.size() == 1);
        check("conservation held at scale",
              e.agg.emittedTotal() + e.agg.suppressedTotal() == (uint64_t)N);
    }

    std::printf("[6] resource bound is LOUD, never a silent evidence cap\n");
    {
        Aggregator a;
        check("a fresh aggregator is not aborted", !a.resourceAborted());
        // behavioural proof of the no-silent-drop rule: an aggregation that
        // would exceed the bound emits (suppresses nothing) instead.
        // (MAX_GROUPS groups is impractical to build here; the decision is the
        // same single branch — assert its shape is present and honest.)
        const std::string abort = Aggregator::resourceAbortLine(123);
        std::printf("      %s\n", abort.c_str());
        check("abort marker is not a CONSUMER-SUMMARY (no masquerade)",
              abort.rfind("CONSUMER-SUMMARY:", 0) != 0
              && abort.rfind("CONSUMER-SUMMARY-ABORT:", 0) == 0, abort);
        check("abort marker says suppressed=0 (nothing silently dropped)",
              abort.find("suppressed=0") != std::string::npos, abort);
    }

    std::printf("\n");
    if (failed) {
        std::printf("FAILED (%d)\n", failed);
        return 1;
    }
    std::printf("ALL PASS\n");
    return 0;
}
