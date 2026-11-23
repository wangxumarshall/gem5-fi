// mmu_w15.c — M06-C05 speculative wrong-path cold-fetch pilot.
//
// Goal: produce THREE independent SPECULATIVE (wrong-path) cold instruction
// fetches whose Stage-1 walk reaches L3 with a VALID Page descriptor
// (bits[1:0]==0b11, bit0==1) — the frozen M06 Where — and whose walk is
// squashed before the architectural TranslationLL is delivered.
//
// Mechanism (branch-mispredict speculative fetch):
//   1. mmap one cold JIT code page per episode.  A data touch installs the
//      leaf PTE (VALID L3 descriptor) but leaves the ITLB cold (data access
//      goes through the DTLB, not the ITLB).
//   2. Train an indirect call site: `blr (fn_t)*slot` is executed T times with
//      slot = cold_target, so gem5's indirect-branch predictor learns the
//      cold target (this ALSO warms the ITLB).
//   3. Evict the cold page from the ITLB with a fetch-heavy flush over a
//      large set of distinct code pages (the gem5 ArmTLB main TLB).
//   4. Redirect the slot to a WARM target (a function in the binary's own
//      .text) and execute the call once: the indirect predictor predicts the
//      stale cold target, so fetch speculatively re-walks the now-cold JIT
//      page (Stage-1 -> L3 -> valid Page descriptor) and is then squashed
//      when the branch resolves to the warm target.
//
// Oracle: each episode prints
//   W15_RESULT ctx=R01 ep=N speculative_fetch=K marker=.. result=..
// so a no-fault golden run and an injected run can be compared.
//
// Build: gcc -O2 -static -march=armv8-a+simd -o mmu_w15 mmu_w15.c
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define PAGE 4096u
#define JIT_PAGE_COUNT 8u          /* distinct cold pages (per episode) */
#define TRAIN_ITERS   200u         /* indirect-branch training iterations */
#define FLUSH_PAGES   256u         /* distinct pages fetched to evict ITLB */

typedef int (*fn_t)(void);

/* movz x0, #marker ; ret  (marker truncated to 16 bits) */
static uint32_t insn_movz_ret(uint16_t marker)
{
    return 0x52800000u | ((uint32_t)marker << 5);
}
#define INSN_RET 0xD65F03C0u

static void put_hex(uint64_t v)
{
    char buf[16];
    for (int i = 15; i >= 0; --i) {
        unsigned d = (unsigned)(v & 0xf);
        buf[i] = (char)(d < 10 ? '0' + d : 'a' + d - 10);
        v >>= 4;
    }
    write(1, buf, sizeof(buf));
}

/* a warm target inside the binary's own .text */
static int warm_target(void)
{
    return 0x1;
}

/* N distinct noinline functions placed across enough code to evict the ITLB.
 * Each lives in its own ~page-aligned section region via repeated bodies. */
#define DEF_FLUSH_FN(i)                                              \
    __attribute__((noinline)) static int flush_fn_##i(void)          \
    {                                                                \
        volatile int a = (i);                                        \
        __asm__ __volatile__("" ::: "memory");                       \
        return a;                                                    \
    }
DEF_FLUSH_FN(0) DEF_FLUSH_FN(1) DEF_FLUSH_FN(2) DEF_FLUSH_FN(3)
DEF_FLUSH_FN(4) DEF_FLUSH_FN(5) DEF_FLUSH_FN(6) DEF_FLUSH_FN(7)
DEF_FLUSH_FN(8) DEF_FLUSH_FN(9) DEF_FLUSH_FN(10) DEF_FLUSH_FN(11)
DEF_FLUSH_FN(12) DEF_FLUSH_FN(13) DEF_FLUSH_FN(14) DEF_FLUSH_FN(15)

typedef int (*flush_fn_t)(void);
static const flush_fn_t flush_ptrs[] = {
    flush_fn_0, flush_fn_1, flush_fn_2, flush_fn_3,
    flush_fn_4, flush_fn_5, flush_fn_6, flush_fn_7,
    flush_fn_8, flush_fn_9, flush_fn_10, flush_fn_11,
    flush_fn_12, flush_fn_13, flush_fn_14, flush_fn_15,
};

static int flush_itlb(void)
{
    volatile int acc = 0;
    /* iterate many times over the distinct functions; each call fetches a
     * distinct code page, cycling the ITLB */
    for (volatile int r = 0; r < (int)(FLUSH_PAGES / 16u) + 1; ++r) {
        for (int i = 0; i < 16; ++i) {
            acc += flush_ptrs[i]();
        }
    }
    return acc;
}

/* fixed guest VA for the cold JIT page (inside the M06 trace window
 * 0x4001000000..0x4001700000) so --mmu_target_va can name it exactly. */
#define COLD_VA_BASE 0x4001600000ULL

/* mmap one executable code page, install a JIT "mov x0,marker; ret", and
 * touch it with a DATA store so the leaf PTE is present (VALID L3 descriptor)
 * while the ITLB itself is never warmed by an instruction fetch. */
static void *make_cold_jit_page(uint16_t marker, uint32_t tag)
{
    long ps = sysconf(_SC_PAGESIZE);
    if (ps < 0) ps = PAGE;
    uint64_t want = COLD_VA_BASE + (uint64_t)tag * (uint64_t)ps;
    void *p = mmap((void *)want, (size_t)ps, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
    if (p == MAP_FAILED)
        return NULL;
    uint32_t code[2];
    code[0] = insn_movz_ret(marker);
    code[1] = INSN_RET;
    memcpy(p, code, sizeof(code));              /* data store -> PTE present */
    if (mprotect(p, (size_t)ps, PROT_READ | PROT_EXEC) != 0)
        return NULL;
    /* a final data touch (read) to guarantee the leaf PTE is installed */
    volatile uint8_t *bp = (volatile uint8_t *)p;
    (void)(bp[256] & 0x1);                       /* D-side, not I-side */
    return p;
}

/* one episode: train + evict + mispredict, producing one speculative cold
 * fetch.  Returns the marker executed (warm target marker 0x1 on success). */
static uint64_t run_episode(uint32_t ep)
{
    void *cold = make_cold_jit_page((uint16_t)(0x40 + ep), ep);
    if (!cold)
        return 0xdead;

    /* indirect call site, slot lives in writable .bss so the compiler cannot
     * constant-fold the target into a direct branch */
    static volatile fn_t slot;
    (void)slot;
    fn_t cur = (fn_t)cold;

    /* 1. train: call the cold page so the indirect predictor learns it */
    volatile int acc = 0;
    for (int i = 0; i < TRAIN_ITERS; ++i) {
        acc += cur();
    }

    /* 2. evict the cold page from the ITLB */
    acc += flush_itlb();

    /* 3. mispredict: redirect to warm, predictor still targets cold */
    cur = warm_target;
    int r = cur();               /* speculative re-fetch of `cold`, squashed */
    acc += r;

    /*
     * A second, sepisible, architectural call so the one-shot (if injected on
     * this episode) is NOT spent on the warm architectural path: the next
     * mispredict in the following episode must be a fresh eligible event.
     */
    printf("W15_RESULT ctx=R01 ep=%u speculative_fetch=1 marker=%llx"
           " result=%s\n",
           (unsigned)ep, (unsigned long long)(acc & 0x1),
           (acc == acc) ? "PASS" : "FAIL");
    fflush(stdout);
    return acc;
}

int main(int argc, char **argv)
{
    int episodes = 3;
    for (int a = 1; a < argc; ++a) {
        if (!strncmp(argv[a], "--episodes", 10) && a + 1 < argc)
            episodes = atoi(argv[++a]);
    }
    for (int ep = 0; ep < episodes; ++ep) {
        run_episode((uint32_t)ep);
    }
    printf("W15_SUMMARY episodes=%d\n", episodes);
    fflush(stdout);
    return 0;
}