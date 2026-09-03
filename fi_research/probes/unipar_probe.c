/* Uniform-byte-parity probe: every byte of the forwarded 64-bit value has
 * ODD parity (0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80). Under the OLD
 * (cancelled lane-constant) check every ror_k escaped; under the NEW dual
 * weighted-aggregate check rotations must be detected (except on the
 * measure-zero adversarial hyperplane). Guards the Critical-1 regression. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
/* volatile on BOTH the loop buffer and the sink: at -O2 GCC dead-store/
 * load-elimination deletes the whole loop body (verified by disassembly of
 * the pre-fix build: main had ZERO memory instructions, so no forward ever
 * traveled the LSQ path and the arm-7 "detections" were all loader/glibc
 * startup forwards). volatile forces the store AND the reload to memory. */
static volatile uint64_t buf[4];
volatile uint64_t sink;
int main(int argc, char **argv){
    long iters = (argc>1)?atol(argv[1]):1000;
    const uint64_t v = 0x0102040810204080ULL; /* all 8 bytes odd parity */
    long intact = 0;
    for (long i=0;i<iters;i++){
        buf[i&3] = v;                 /* store */
        uint64_t x = buf[i&3];        /* reload -> store->load forward */
        asm volatile("":::"memory");
        intact += (x==v);             /* no deref: cannot crash */
        sink = x;                     /* keep the reload live at any -O level */
    }
    printf("intact=%ld/%ld\n", intact, iters);
    return 0;
}
