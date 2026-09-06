/* ptr_chase_long — §2.1 D method2 direction, long-lived-pointer variant.
 * ptr_chase_kernel (single 256-node pass) masks PRF X10 flips: the pointer
 * is consumed too fast for a single injection to land while it is live AND
 * matters. This variant keeps the SAME x10 chase semantics but repeats the
 * traversal (4096 rounds over a 4KiB-spanning 2048-node list) so the
 * pointer register stays live across a ~50K+ cycle window — the
 * find_busiest_group class (a scheduler-domain walk that runs continuously).
 * The checksum folds every round so ANY wrong-pointer round that survives
 * perturbs the output (SDC detectable).
 * Build: gcc -static -O2 -o ptr_chase_long ptr_chase_long.c
 */
#include <stdio.h>
#include <stdint.h>
#define N 2048
#define ROUNDS 4096
struct Node { struct Node *next; uint64_t val; };
static uint64_t cs = 0xcbf29ce484222325ULL;
int main(void) {
    static struct Node nodes[N];
    for (int i = 0; i < N; i++) {
        nodes[i].next = &nodes[(i * 7 + 1) % N];
        nodes[i].val = (uint64_t)i * 13 + 7;
    }
    struct Node *p = &nodes[0];
    uint64_t sum = 0;
    for (int r = 0; r < ROUNDS; r++) {
        for (int i = 0; i < N; i++) { sum ^= p->val; p = p->next; }
        cs ^= sum + (uint64_t)r;
    }
    cs *= 0x100000001b3ULL;
    printf("%016llx\n", cs & 0xffffffffffffffffULL);
    return 0;
}
