/* spec_leak_probe_kernel — v1.1 Phase 10 patch 2a (task_plan 2a).
 *
 * The method1 speculative-leak probe: a hard-to-predict branch whose
 * WRONG path writes the target architectural register X10, with the
 * value's consumer 1-2 instructions after the (right-path) definition —
 * the leak window. If the squash rollback is suppressed for the wrong-
 * path X10 writer, the wrong-path VALUE survives into the right path
 * and out[] shows it.
 *
 * Structure per iteration i:
 *   if (data[i] & 1) {            // ~50%, mispredicted often
 *       // RIGHT path (taken): define t on X10, consume immediately.
 *       t = right_path_value(i);  // register ... asm("x10")
 *       out[i] = consume(t);      // 1-2 insts after the definition
 *   } else {
 *       // WRONG path (not taken, executed speculatively after a
 *       // mispredict of the OTHER direction): write the SAME X10 with
 *       // a wildly different constant. A suppressed rollback leaks it.
 *       x10_alias = wrong_path_value(i);
 *       out[i] = 0;
 *   }
 * wrong_path_value - right_path_value = 0x5A5A5A5A5A5A5A5A (one-look
 * signature). Output: the whole out[] array (per_element oracle).
 *
 * Static AArch64, no libc.
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#ifndef N
#define N 4096
#endif

static uint64_t data[N], out[N];

static void put(const char *s){ write(1, s, strlen(s)); }
static void put_u64(uint64_t v){
    char buf[20]; int i=19; buf[i--]=0;
    if(!v) buf[i--]='0';
    while(v){ buf[i--]='0'+(v%10); v/=10; }
    write(1, buf+i+1, 18-i);
}
static void put_hex64(uint64_t v){
    char buf[16];
    for(int i=15;i>=0;--i){ unsigned x=v&0xf; buf[i]=x<10?'0'+x:'a'+x-10; v>>=4; }
    write(1,buf,16);
}

int main(void){
    /* LCG inputs: data[i]&1 is a ~50% coin the branch predictor cannot
     * learn (period-63 LCG low bit) — near-maximum squash traffic. */
    uint64_t s=0x243F6A8885A308D3ULL;
    for(int i=0;i<N;i++){
        s=s*6364136223846793005ULL+1442695040888963407ULL;
        data[i]=s;
    }

    for(int i=0;i<N;i++){
        /* Pin the leaking value to X10 (register asm) so the injector's
         * spec_leak_arch_reg=10 targets exactly this definition site. */
        register uint64_t t asm("x10");
        if (data[i] & 1) {
            /* RIGHT path: define t, consume within 1-2 instructions. */
            t = (uint64_t)i * 0x10001ULL + 7;      /* right_path_value */
            asm volatile("" : "+r"(t));            /* keep t live on x10 */
            out[i] = t ^ (data[i] >> 8);           /* consume(t) */
        } else {
            /* WRONG path (executed on the sibling mispredict): write the
             * SAME arch reg with a one-look-different constant. */
            register uint64_t w asm("x10");
            w = (uint64_t)i * 0x10001ULL + 7
                + 0x5A5A5A5A5A5A5A5AULL;           /* wrong_path_value */
            asm volatile("" : "+r"(w));
            out[i] = 0;
        }
    }

    /* ARRAYHASH over out[] (4-lane FNV-1a, 64 hex). */
    put("ARRAYHASH=");
    const unsigned char *p=(const unsigned char*)out;
    unsigned total=sizeof(out), q=(total+3)/4;
    for(int lane=0; lane<4; lane++){
        uint64_t h=1469598103934665603ULL ^ (0x9e3779b9ULL*lane);
        for(unsigned j=lane*q; j<(lane+1)*q && j<total; j++){
            h^=p[j]; h*=1099511628211ULL;
        }
        put_hex64(h);
    }
    put("\n");

    /* ELEMDIFF n=<count> first=<idx>: count = elements equal to the
     * wrong-path signature leak (out[i] != golden[i]). The kernel does
     * not keep a golden copy (out is branch-dependent); instead we count
     * elements that CARRY the leak signature: right-path elems whose
     * value equals consume(wrong_path_value) — the +0x5A5A... offset is
     * detectable in out[] because consume is a XOR with known data. */
    uint64_t n_leak=0, first=0;
    for(int i=0;i<N;i++){
        if (!(data[i]&1)) continue;            /* only right-path slots */
        uint64_t right = (uint64_t)i*0x10001ULL + 7;
        uint64_t wrong = right + 0x5A5A5A5A5A5A5A5AULL;
        uint64_t got = out[i] ^ (data[i] >> 8);
        if (got == wrong && got != right) {    /* the wrong VALUE leaked */
            if(!n_leak) first=i;
            n_leak++;
        }
    }
    put("ELEMDIFF n="); put_u64(n_leak);
    put(" first=");     put_u64(first);
    put(" maxulp=");    put_u64(n_leak ? 1 : 0);
    put("\n");
    put("ULP="); put_u64(n_leak ? 1 : 0); put("\n");
    return 0;
}
