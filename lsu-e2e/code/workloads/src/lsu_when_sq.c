/* lsu_when_sq.c — SQ01/SQ03/SP05 When-v2 contexts (Sheet 15, W3).
 *
 * E2E instrumented variant.  Marker discipline: a store marker is emitted
 * only AFTER the reload that the original program performs next (and after
 * the dmb), so neither the forwarding window nor the drain/visibility
 * ordering is widened by observation code.
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
    uint64_t ev = 0;
    unsigned i;

    SW_EV(ev, SW_PHASE, 1, 4, 0, 0);

#if CONTEXT == 1
    /* C01: baseline store -> drain -> same-address reload -> checksum. */
    for (i = 0; i < N; i++) {
        uint64_t v = sq_value(i);
        buf[i] = v;
        __asm__ volatile("dmb ish" ::: "memory");
        uint64_t r = buf[i];
        SW_EV(ev, SW_LOAD, 3, (uint64_t)&buf[i], r, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 2, (uint64_t)&buf[i], v, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, r);
        SW_EV(ev, SW_HASH, 4, r, hb, s);
        path += (r == v);
        SW_EV(ev, SW_CHECK, 5, r, v, SW_AUX(i, path));
    }
#elif CONTEXT == 2
    /* C02: changed activation/occupancy conditions: a burst of stores
     * precedes the barrier and the reloads that follow it. */
    for (i = 0; i < N; i += 4) {
        uint64_t v0 = sq_value(i), v1 = sq_value(i + 1);
        uint64_t v2 = sq_value(i + 2), v3 = sq_value(i + 3);
        buf[i] = v0;
        buf[i + 1] = v1;
        buf[i + 2] = v2;
        buf[i + 3] = v3;
        __asm__ volatile("dmb ish" ::: "memory");
        uint64_t r0 = buf[i], r1 = buf[i + 1];
        uint64_t r2 = buf[i + 2], r3 = buf[i + 3];
        SW_EV(ev, SW_LOAD, 14, (uint64_t)&buf[i], r0, SW_AUX(i, 8));
        SW_EV(ev, SW_LOAD, 15, (uint64_t)&buf[i + 1], r1, SW_AUX(i, 8));
        SW_EV(ev, SW_LOAD, 16, (uint64_t)&buf[i + 2], r2, SW_AUX(i, 8));
        SW_EV(ev, SW_LOAD, 17, (uint64_t)&buf[i + 3], r3, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 10, (uint64_t)&buf[i], v0, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 11, (uint64_t)&buf[i + 1], v1, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 12, (uint64_t)&buf[i + 2], v2, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 13, (uint64_t)&buf[i + 3], v3, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, r0 ^ r1 ^ r2 ^ r3);
        SW_EV(ev, SW_HASH, 18, r0 ^ r1 ^ r2 ^ r3, hb, s);
        path += (r0 == v0) + (r1 == v1) + (r2 == v2) + (r3 == v3);
        SW_EV(ev, SW_CHECK, 19, r0 ^ r1 ^ r2 ^ r3, v0 ^ v1 ^ v2 ^ v3,
              SW_AUX(i, path));
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
        SW_EV(ev, SW_LOAD, 22, (uint64_t)&buf[i], r, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 20, (uint64_t)&buf[i], v, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 21, (uint64_t)&buf[i], good, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, r);
        SW_EV(ev, SW_HASH, 23, r, hb, s);
        path += (r == good);
        SW_EV(ev, SW_CHECK, 24, r, good, SW_AUX(i, path));
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
        SW_EV(ev, SW_LOAD, 31, (uint64_t)&buf[i], r, SW_AUX(i, 8));
        SW_EV(ev, SW_LOAD, 32, (uint64_t)&aux[j], w, SW_AUX(i, j));
        SW_EV(ev, SW_STORE, 30, (uint64_t)&buf[i], v, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 33, (uint64_t)&aux[j], w ^ r, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, r ^ w);
        SW_EV(ev, SW_HASH, 34, r ^ w, hb, s);
    }
#else
    /* C05: control dependency after the store has drained; the commit of
     * the store is never rolled back. */
    for (i = 0; i < N; i++) {
        uint64_t v = sq_value(i);
        buf[i] = v;
        __asm__ volatile("dmb ish" ::: "memory");
        uint64_t r = buf[i];
        if (r & 8ull) {
            SW_EV(ev, SW_LOAD, 41, (uint64_t)&buf[i], r, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 40, (uint64_t)&buf[i], v, SW_AUX(i, 8));
            uint64_t hb = path;
            path = when_fnv(path, r);
            SW_EV(ev, SW_HASH, 43, r, hb, path);
        } else {
            SW_EV(ev, SW_LOAD, 41, (uint64_t)&buf[i], r, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 40, (uint64_t)&buf[i], v, SW_AUX(i, 8));
            uint64_t hb = s;
            s = when_fnv(s, r ^ v);
            SW_EV(ev, SW_HASH, 44, r ^ v, hb, s);
        }
        SW_EV(ev, SW_BRANCH, 42, r, r & 8ull, SW_AUX(i, 0));
        uint64_t hb = s;
        s = when_fnv(s, path);
        SW_EV(ev, SW_HASH, 45, path, hb, s);
    }
#endif

    SW_EV(ev, SW_OUTPUT, 99, s ^ path, s, path);
    when_put_hex(s ^ path);
    return 0;
}
