/*
 * vl_api_probe — all-VL Phase 2 P1: validates the sdcshield framework
 * arm64_vl.h query layer (rdvl/rdsvl .inst encodings + getauxval/prctl)
 * in gem5 at all four tiers (128/256/512/1024-bit). Same-source mirror of
 * framework/device/cpu/arm64/arm64_vl.h (encodings 0x04bf5020/0x04bf5820,
 * as+objdump derived 2026-10-23).
 * Spec: docs/superpowers/specs/2026-10-23-sve-sme-all-vl2-design.md §7
 * (sdcshield repo, PR feat/arm64-vl-api).
 *
 * Channel A: sanity — VL/SVL are 16-byte multiples in [16,256] → exit 0/3.
 * Channel B: FNV-1a 16-hex checksum over the reported values.
 * argv: [fixed|random] [seed] — deterministic probe (no seed-dependent
 * data); fixed and random must yield identical checksums per tier (checked
 * by comparing run records), checksums must differ across tiers.
 *
 * Build note: gcc, -march=armv9-a+sve — the .inst encodings need neither
 * SME mnemonics nor clang (unlike the sme_*_dual kernels). Like those
 * kernels, rdsvl executes unguarded: this is a gem5 workload, NOT a
 * sdcshield test — running it on non-SME hardware SIGILLs by design.
 * prctl results are reported as-is (gem5 SE syscall coverage is an honest
 * boundary, not a pass/fail input).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/auxv.h>
#include <sys/prctl.h>
#include <asm/hwcap.h>

#ifndef PR_SME_GET_VL
#define PR_SME_GET_VL 64
#endif

static uint64_t fnv1a(uint64_t h, const void *p, size_t n)
{
    const unsigned char *b = p;
    for (size_t i = 0; i < n; i++) {
        h ^= b[i];
        h *= 0x100000001b3ULL;
    }
    return h;
}

static long rdvl_bytes(void)
{
    register long vl __asm__("x0");
    asm volatile(".inst 0x04bf5020" : "=r"(vl)); /* rdvl x0, #1 */
    return vl;
}

static long rdsvl_bytes(void)
{
    register long vl __asm__("x0");
    asm volatile(".inst 0x04bf5820" : "=r"(vl)); /* rdsvl x0, #1 */
    return vl;
}

int main(int argc, char **argv)
{
    int mode_fixed = (argc < 2 || strcmp(argv[1], "fixed") == 0);
    (void)argv; /* seed unused: deterministic API probe */

    unsigned long hw = getauxval(AT_HWCAP), hw2 = getauxval(AT_HWCAP2);
    long vl = rdvl_bytes(), svl = rdsvl_bytes();
    int psg = prctl(PR_SVE_GET_VL);
    int pmg = prctl(PR_SME_GET_VL);

    printf("vl_api_probe: mode=%s hwcap_sve=%d hwcap2_sve2=%d hwcap2_sme=%d "
           "rdvl=%ld rdsvl=%ld prctl_sve_get=%d prctl_sme_get=%d\n",
           mode_fixed ? "fixed" : "random",
           !!(hw & HWCAP_SVE), !!(hw2 & HWCAP2_SVE2), !!(hw2 & HWCAP2_SME),
           vl, svl, psg, pmg);

    int bad = 0;
    if (vl < 16 || vl > 256 || (vl % 16)) {
        printf("FAIL: rdvl %ld not 16-aligned in [16,256]\n", vl);
        bad = 1;
    }
    if (svl < 16 || svl > 256 || (svl % 16)) {
        printf("FAIL: rdsvl %ld not 16-aligned in [16,256]\n", svl);
        bad = 1;
    }

    uint64_t h = 0xcbf29ce484222325ULL;
    h = fnv1a(h, &vl, sizeof vl);
    h = fnv1a(h, &svl, sizeof svl);
    h = fnv1a(h, &psg, sizeof psg);
    h = fnv1a(h, &pmg, sizeof pmg);
    printf("checksum=%016llx SDCSHIELD_FAILS=%d\n",
           (unsigned long long)h, bad);
    return bad ? 3 : 0;
}
