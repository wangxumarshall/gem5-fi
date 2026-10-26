/*
 * tests/chaos_tlb_stuck_test.cc — 独立单测（gem5 构建之外）。
 * NOT part of the gem5 build; compiled directly:
 *
 *   g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
 *       tests/chaos_tlb_stuck_test.cc -o /tmp/tlb_stuck && /tmp/tlb_stuck
 */
#include <cstdint>
#include <cstdio>
#include "arch/arm/CHAOSArmTLB/chaos_tlb_stuck.hh"

using namespace gem5::chaos_tlb;
static int failures = 0;
#define CHECK(c, m) do { if (!(c)) { printf("FAIL: %s\n", m); ++failures; } } while (0)

int main() {
    // (1) StuckAtZero on an already-zero bit is a no_effect
    CHECK(!applyStuckMask(0x2ull, 0x81d74ull, StuckKind::StuckAtZero).effective,
          "stuck_at_zero on an already-zero bit must be no_effect");
    // (2) StuckAtZero on a set bit is effective and clears it
    { auto o = applyStuckMask(0x1ull, 0x81d75ull, StuckKind::StuckAtZero);
      CHECK(o.effective && o.new_pfn == 0x81d74ull, "stuck_at_zero must clear the bit"); }
    // (3) mask above the PA width leaves the frame unchanged -> no_effect
    CHECK(!applyStuckMask(0x8000000000000000ull, 0x81d75ull,
                          StuckKind::StuckAtZero).effective,
          "mask bit above PA width must be no_effect");
    // (4) StuckAtOne on an already-1 bit is a no_effect (idempotent)
    CHECK(!applyStuckMask(0x1ull, 0x81d75ull, StuckKind::StuckAtOne).effective,
          "stuck_at_one on an already-one bit must be no_effect");
    CHECK(applyStuckMask(0x2ull, 0x81d75ull, StuckKind::StuckAtOne).effective,
          "stuck_at_one on a zero bit must be effective");
    // (5) BitFlip always changes the frame
    CHECK(applyStuckMask(0x1ull, 0x81d74ull, StuckKind::BitFlip).effective,
          "bit_flip on any set bit must be effective");
    // (6) mask == 0 is never effective
    CHECK(!applyStuckMask(0ull, 0x81d75ull, StuckKind::StuckAtZero).effective,
          "mask==0 must be no_effect");
    // (7) latched mask is FIXED for the run (repeated calls return the same)
    { uint64_t latch = 0;
      const uint64_t a = latchStuckMask(0, latch, 0x100ull);
      const uint64_t b = latchStuckMask(0, latch, 0xdeadbeefull);
      CHECK(a == 0x100ull && b == 0x100ull, "latched mask must not be redrawn"); }
    // (8) an explicit user mask wins over the draw and is latched
    { uint64_t latch = 0;
      CHECK(latchStuckMask(0x8ull, latch, 0x100ull) == 0x8ull &&
            latchStuckMask(0, latch, 0x200ull) == 0x8ull,
            "explicit fault_mask must win and be latched"); }
    // (9) same input -> same output (determinism)
    CHECK(applyStuckMask(0x4ull, 0x10ull, StuckKind::BitFlip).new_pfn == 0x14ull,
          "bit_flip must be an exact xor");

    printf(failures ? "chaos_tlb_stuck_test: %d FAILURE(S)\n"
                    : "chaos_tlb_stuck_test: ALL PASS\n", failures);
    return failures ? 1 : 0;
}
