// Host unit test: FR03 permanent Vec physical-cell generation semantics.
//
// Build/run (no gem5, no workload):
//   g++ -O0 -std=c++17 -Wall -Wextra -Werror
//       -I CHAOS/gem5/src/cpu/o3/CHAOSPhysReg
//       tests/unit/chaos_physreg_generation_test.cc -o /tmp/x && /tmp/x
//
// Exit code 0 = all checks pass.
//
// What this pins (workbook table 3 FR03 + table 7/9 FR03):
//   * the permanent key is reg_class + phys_index + lane/bit/mask + polarity;
//   * generation is allocation/exposure identity, never a match/clear key;
//   * a freed/reallocated physical cell still sticks;
//   * a new generation restarts its exposure chain (exposure_id from 1);
//   * other phys indices / reg classes / lanes / bits are untouched;
//   * squash does not clear; only an explicit reset does.

#include <cstdint>
#include <cstdio>
#include <cstring>

#include "chaos_vec_stuck.hh"

using namespace gem5::chaos_vec_stuck;

static int failures = 0;

static void
check(const char *name, bool ok)
{
    if (ok) {
        std::printf("  PASS %s\n", name);
    } else {
        std::printf("  FAIL %s\n", name);
        ++failures;
    }
}

static uint64_t
laneOf(const uint8_t *v, int lane_width, int lane_offset)
{
    const int lane_bytes = lane_width / 8;
    const int base = lane_offset * lane_bytes;
    uint64_t x = 0;
    for (int b = 0; b < lane_bytes; ++b)
        x |= (uint64_t)v[base + b] << (8 * b);
    return x;
}

int
main()
{
    // ------------------------------------------------------------------
    // GenerationLedger: mirrors PhysRegFile::flat_generation.
    // ------------------------------------------------------------------
    GenerationLedger ledger(4);
    check("ledger starts at generation 0",
          ledger.generationOf(0) == 0 && ledger.generationOf(3) == 0);
    check("ledger out-of-range is 0", ledger.generationOf(9) == 0 &&
          ledger.generationOf(-1) == 0);
    check("noteFreed bumps only the freed slot",
          ledger.noteFreed(1) == 1 && ledger.generationOf(1) == 1 &&
          ledger.generationOf(0) == 0 && ledger.generationOf(2) == 0);
    check("repeated frees increment",
          ledger.noteFreed(1) == 2 && ledger.generationOf(1) == 2);
    ledger.reset();
    check("ledger reset clears generations", ledger.generationOf(1) == 0);

    // ------------------------------------------------------------------
    // PermanentCell: install (class=7 is an opaque VecRegClass value).
    // ------------------------------------------------------------------
    const int VEC = 7;
    const int INT = 0;
    const int FP = 1;
    const int IDX = 11;
    PermanentCell cell;
    check("install accepts valid geometry",
          cell.install(VEC, IDX, 32, 2, 0x1ULL, 0, 3));

    uint8_t v[16];
    // --- same generation: 8 consecutive writes stay stuck -----------------
    bool eight_ok = true;
    bool ids_ok = true;
    bool only_target_ok = true;
    for (int i = 0; i < 8; ++i) {
        // bit0 = 1 in the target lane, so SA0 is a real activation.
        std::memset(v, (uint8_t)(0x11 + 2 * i), sizeof(v));
        uint8_t before[16];
        std::memcpy(before, v, sizeof(v));
        WriteResult r = cell.writeVec16(v, VEC, IDX, 3);
        if (!r.matched || !r.applied || !r.activated)
            eight_ok = false;
        if (r.generation_exposure_id != (uint64_t)(i + 1))
            ids_ok = false;
        if ((laneOf(v, 32, 2) & 1ULL) != 0)
            eight_ok = false;
        if (!onlyMaskedBitsDiffer(before, v, 32, 2, 0x1ULL))
            only_target_ok = false;
    }
    check("same generation: 8 consecutive writes stay SA0", eight_ok);
    check("same generation: exposure_id increments 1..8", ids_ok);
    check("same generation: only the target bit changes", only_target_ok);

    // --- free/realloc: the SAME physical cell still sticks ----------------
    std::memset(v, 0xff, sizeof(v));
    WriteResult g4 = cell.writeVec16(v, VEC, IDX, 4);
    check("PERMANENT STUCK ACROSS GENERATIONS", g4.matched && g4.applied);
    check("free/realloc observed as generation change",
          g4.generation_changed && g4.old_generation == 3 &&
          g4.generation == 4 && g4.generation_changes == 1);
    check("GENERATION CHAIN RESTART: exposure_id back to 1",
          g4.generation_exposure_id == 1);
    check("new generation still forces the stuck bit",
          (laneOf(v, 32, 2) & 1ULL) == 0);
    WriteResult g4b = cell.writeVec16(v, VEC, IDX, 4);
    check("new generation exposure chain continues 1,2",
          g4b.generation_exposure_id == 2 && !g4b.generation_changed);
    check("lifetime exposure total is continuous",
          g4b.exposure_total == 10 && cell.exposuresTotal() == 10);
    check("generation change count is observable",
          cell.generationChanges() == 1);

    // --- other phys index / reg class / lane / bit are untouched ----------
    std::memset(v, 0xab, sizeof(v));
    WriteResult other_idx = cell.writeVec16(v, VEC, 12, 4);
    check("other phys index is not matched", !other_idx.matched);
    bool untouched = true;
    for (int i = 0; i < 16; ++i)
        if (v[i] != 0xab) untouched = false;
    check("other phys index bytes untouched", untouched);

    WriteResult int_hit = cell.writeVec16(v, INT, IDX, 4);
    WriteResult fp_hit = cell.writeVec16(v, FP, IDX, 4);
    check("int register class does not cross-talk",
          !int_hit.matched && !int_hit.applied);
    check("float register class does not cross-talk",
          !fp_hit.matched && !fp_hit.applied);
    untouched = true;
    for (int i = 0; i < 16; ++i)
        if (v[i] != 0xab) untouched = false;
    check("int/float writes leave the vec cell byte-identical", untouched);

    std::memset(v, 0xab, sizeof(v));
    uint8_t pre_lane[16];
    std::memcpy(pre_lane, v, sizeof(v));
    cell.writeVec16(v, VEC, IDX, 4);
    check("non-target lanes/bits of the target cell are preserved",
          onlyMaskedBitsDiffer(pre_lane, v, 32, 2, 0x1ULL));
    check("non-target lane 0 intact", v[0] == 0xab && v[3] == 0xab);
    check("non-target lane 3 intact", v[12] == 0xab && v[15] == 0xab);

    // --- squash must not clear the defect ---------------------------------
    // The model intentionally exposes no squash()/free() clear API: there is
    // no state transition for a squash, so the very next write still sticks.
    std::memset(v, 0x00, sizeof(v));
    WriteResult after_squash = cell.writeVec16(v, VEC, IDX, 4);
    check("SQUASH DOES NOT CLEAR: write after squash still stuck",
          after_squash.matched && after_squash.applied &&
          (laneOf(v, 32, 2) & 1ULL) == 0);
    check("squash did not alter attachment state", cell.active());

    // --- SA1 polarity also survives reallocation --------------------------
    PermanentCell sa1;
    check("SA1 install", sa1.install(VEC, 5, 16, 1, 0x8000ULL, 1, 0));
    std::memset(v, 0x00, sizeof(v));
    WriteResult sa1_gen0 = sa1.writeVec16(v, VEC, 5, 0);
    WriteResult sa1_gen1 = sa1.writeVec16(v, VEC, 5, 1);
    check("SA1 install generation sticks", sa1_gen0.applied &&
          (laneOf(v, 16, 1) & 0x8000ULL) != 0);
    check("SA1 new generation sticks and chain restarts",
          sa1_gen1.matched && sa1_gen1.applied &&
          sa1_gen1.generation_changed && sa1_gen1.generation_exposure_id == 1);

    // --- explicit reset (end of run) clears -------------------------------
    cell.clear();
    check("reset clears the cell", !cell.active());
    std::memset(v, 0x12, sizeof(v));
    WriteResult cleared = cell.writeVec16(v, VEC, IDX, 5);
    check("write after reset is not matched", !cleared.matched &&
          !cleared.applied);
    check("reset leaves the register bytes untouched", v[8] == 0x12);

    // --- invalid geometry fails closed ------------------------------------
    PermanentCell bad;
    check("bad lane width rejected", !bad.install(VEC, 1, 24, 0, 1, 0, 0));
    check("lane offset outside register rejected",
          !bad.install(VEC, 1, 32, 4, 1, 0, 0));
    check("zero mask rejected", !bad.install(VEC, 1, 32, 0, 0, 0, 0));
    check("mask wider than lane rejected",
          !bad.install(VEC, 1, 32, 0, 0x100000000ULL, 0, 0));

    if (failures) {
        std::printf("FAILED: %d check(s)\n", failures);
        return 1;
    }
    std::printf("ALL GENERATION CHECKS PASSED\n");
    return 0;
}
