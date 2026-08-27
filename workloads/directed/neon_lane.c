/* P0/P2 BM-NEON kernel: 128-bit ASIMD lane-separated accumulation.
   Each V register lane (4x32-bit) accumulates an independent value;
   a bit-flip on any lane corrupts ONLY that lane's checksum, so a
   lane-targeted FI is detectable per-lane. Prints 4 lane checksums
   concatenated = 64-hex, plus a 16-hex total (XOR of lane checksums)
   for the §9.1 classifier's 16-hex golden comparison.

   Native aarch64 ASIMD (NEON), NOT SVE (kunpeng 920 baseline = 128-bit
   ASIMD). -march=armv8-a is enough. */
#include <unistd.h>
#include <stdint.h>
#include <arm_neon.h>

static void put_hex(unsigned long v){ char b[16]; for(int i=15;i>=0;--i){unsigned d=v&0xf;b[i]=d<10?'0'+d:'a'+d-10;v>>=4;} write(2,b,16); write(2,"\n",1);}

int main(void){
    /* 4 independent lane accumulators, each a different seed so a flip
       on lane k only changes lane k's checksum. */
    uint32x4_t acc = {0x12345678u, 0x9abcdef0u, 0x0fedcba9u, 0x87654321u};
    uint32x4_t step = {0x9e3779b9u, 0x85ebca6bu, 0xc2b2ae35u, 0x27d4eb2fu};
    /* ROI: a long lane-parallel ASIMD dependency chain the compiler
       cannot fold away (uses FMA/ADD/EOR on whole vectors). */
    for (volatile unsigned long i=0; i<500000UL; ++i){
        acc = veorq_u32(acc, vshlq_n_u32(acc, 13));   /* lane-parallel xor<<13 */
        acc = veorq_u32(acc, vshrq_n_u32(acc, 7));    /* lane-parallel xor>>7  */
        acc = vaddq_u32(acc, step);                   /* lane-parallel add    */
        step = vaddq_u32(step, vdupq_n_u32(0x27d4eb2fu)); /* perturb step/lane */
    }
    /* per-lane checksums */
    uint32_t l0 = vgetq_lane_u32(acc,0);
    uint32_t l1 = vgetq_lane_u32(acc,1);
    uint32_t l2 = vgetq_lane_u32(acc,2);
    uint32_t l3 = vgetq_lane_u32(acc,3);
    /* total = XOR of the 4 lane checksums (a single 32-bit golden) */
    unsigned long total = (unsigned long)(l0 ^ l1 ^ l2 ^ l3);
    put_hex(total);
    return 0;
}
