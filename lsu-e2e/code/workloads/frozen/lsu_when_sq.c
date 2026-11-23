/* lsu_when_sq.c — SQ01/SQ03/SP05 When-v2 contexts (Sheet 15, W3).
 *
 * The fault hooks are the original SQ data byte (SQ01), SQ _canWB state
 * (SQ03) and completeStore event (SP05).  Every context keeps real stores
 * (8-byte, aligned) and changes only consumption, overwrite, dependency or
 * control conditions.
 *
 * A dmb ish is used where a post-drain reload is intended; omitting it
 * preserves same-SQ forwarding for the C04 dependency chains.
 */
#include "when_common.h"

#define N 1024
#define NB 2048

static volatile uint64_t buf[NB] __attribute__((aligned(4096)));
static volatile uint64_t aux[NB] __attribute__((aligned(4096)));

static inline uint64_t
sq_value(unsigned i)
{
    return 0x73715f72656c6f61ULL + (uint64_t)i * 0x0101010101010101ULL;
}

int
main(void)
{
    uint64_t s = 0x5f1e4d7c9b0a8362ULL ^ (uint64_t)CONTEXT;
    uint64_t path = 0;
    unsigned i;

    /* The arrays are zero-initialised in .bss.  Deliberately no runtime
     * initialisation stores: the eligible stream must start in the designed
     * loop, not in an init loop whose stores would be overwritten later. */

#if CONTEXT == 1
    /* C01: baseline store -> drain -> same-address reload -> checksum. */
    for (i = 0; i < N; i++) {
        uint64_t v = sq_value(i);
        buf[i] = v;
        __asm__ volatile("dmb ish" ::: "memory");
        uint64_t r = buf[i];
        s = when_fnv(s, r);
        path += (r == v);
    }
#elif CONTEXT == 2
    /* C02: changed activation/occupancy conditions: a burst of stores
     * precedes the barrier and the reloads that follow it. */
    for (i = 0; i < N; i += 4) {
        uint64_t v0 = sq_value(i), v1 = sq_value(i + 1);
        uint64_t v2 = sq_value(i + 2), v3 = sq_value(i + 3);
        buf[i] = v0; buf[i + 1] = v1; buf[i + 2] = v2; buf[i + 3] = v3;
        __asm__ volatile("dmb ish" ::: "memory");
        uint64_t r0 = buf[i], r1 = buf[i + 1];
        uint64_t r2 = buf[i + 2], r3 = buf[i + 3];
        s = when_fnv(s, r0 ^ r1 ^ r2 ^ r3);
        path += (r0 == v0) + (r1 == v1) + (r2 == v2) + (r3 == v3);
    }
#elif CONTEXT == 3
    /* C03: overwrite: the faulted store is followed by a correct store to
     * the same address; only the later value is reloaded/consumed. */
    for (i = 0; i < N; i++) {
        uint64_t v = sq_value(i);
        buf[i] = v;
        __asm__ volatile("" ::: "memory");
        uint64_t good = v ^ 0xa5a5a5a5a5a5a5a5ULL;
        buf[i] = good;
        __asm__ volatile("dmb ish" ::: "memory");
        uint64_t r = buf[i];
        s = when_fnv(s, r);
        path += (r == good);
    }
#elif CONTEXT == 4
    /* C04: enhanced dependency: same-address forwarding feeds the address
     * of a second access and the checksum. */
    for (i = 0; i < N; i++) {
        uint64_t v = sq_value(i);
        buf[i] = v;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[i];              /* forwarded from the SQ */
        unsigned j = (unsigned)((r >> 5) & (NB - 1u));
        uint64_t w = aux[j];
        aux[j] = w ^ r;
        __asm__ volatile("" ::: "memory");
        s = when_fnv(s, r ^ w);
    }
#else
    /* C05: control dependency after the store has drained; the commit of
     * the store is never rolled back. */
    for (i = 0; i < N; i++) {
        uint64_t v = sq_value(i);
        buf[i] = v;
        __asm__ volatile("dmb ish" ::: "memory");
        uint64_t r = buf[i];
        if (r & 8ull)
            path = when_fnv(path, r);
        else
            s = when_fnv(s, r ^ v);
        s = when_fnv(s, path);
    }
#endif

    when_put_hex(s ^ path);
    return 0;
}
