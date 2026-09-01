/* ptr_chase.c — method2 (x10 garbage pointer) directed kernel (plan §5.1D).
 * A linked-list traversal where the chase pointer lives in a register
 * across an indirect-addressing loop (method2's __per_cpu_offset load-use
 * pattern). A PRF/AGU fault on the chase pointer dereferences garbage ->
 * segfault (DUE) or wrong data (SDC). Golden: deterministic chain walk.
 * Output: 16-hex checksum + iters/fails.
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

#define N 8192
typedef struct node { struct node *next; uint64_t val; } node_t;

static uint32_t rng_s = 0x5A5A1234u;
static inline uint32_t xs32(void){uint32_t x=rng_s;x^=x<<13;x^=x>>17;x^=x>>5;rng_s=x;return x;}

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 200;
    node_t *nodes = malloc(N * sizeof(node_t));
    if (!nodes) return 2;
    for (int i = 0; i < N; i++) { nodes[i].val = ((uint64_t)xs32()<<32)|xs32(); }
    for (int i = 0; i < N; i++) nodes[i].next = &nodes[(i + 1) % N];

    uint64_t acc = 0; long fails = 0;
    for (long it = 0; it < iters; it++) {
        /* chase: pointer crosses an indirect sub-loop (register-resident) */
        node_t *p = &nodes[it % N];
        uint64_t expect = 0;
        for (int k = 0; k < 64; k++) { expect += p->val; p = p->next; }
        /* recompute the same walk for the golden (data not mutated) */
        node_t *q = &nodes[it % N];
        uint64_t got = 0;
        for (int k = 0; k < 64; k++) { got += q->val; q = q->next; }
        if (got != expect) fails++;
        acc += got;
    }
    printf("%016lx\n", acc & 0xFFFFFFFFFFFFFFFFULL);
    fprintf(stderr, "iters=%ld fails=%ld variant=ptr_chase\n", iters, fails);
    return (fails > 0) ? 1 : 0;
}
