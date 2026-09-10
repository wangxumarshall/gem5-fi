/* stream_triad_kernel — v1.1 Phase 11 patch 3a (task_plan 3a).
 *
 * STREAM triad: a[i] = b[i] + q * c[i], over three N-element uint64
 * arrays. Default N=262144 -> 3*2MB = 6MB working set = 12x L2 (512KB)
 * and 3x the L1+L2 combined — every streaming access is a genuine L2
 * MISS that fetches from DRAM (the backing store), so a CHAOSMem
 * backing-byte fault on a not-yet-consumed line can surface as SDC
 * (the writeback/readback path). The final array is hashed (FINAL=,
 * 16 hex). Static AArch64, no libc. */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#ifndef N
#define N 262144
#endif

static uint64_t arr_a[N], arr_b[N], arr_c[N];

static void put(const char *s){ write(1, s, strlen(s)); }
static void put_hex64(uint64_t v){
    char buf[16];
    for(int i=15;i>=0;--i){ unsigned x=v&0xf; buf[i]=x<10?'0'+x:'a'+x-10; v>>=4; }
    write(1,buf,16);
}

int main(void){
    uint64_t s=0x243F6A8885A308D3ULL;
    const uint64_t q=0x9E3779B97F4A7C15ULL;
    /* init pass (also streams — warms nothing for the triad: arrays are
     * 2MB each, far beyond L2) */
    for(uint64_t i=0;i<N;i++){
        s=s*6364136223846793005ULL+1442695040888963407ULL;
        arr_b[i]=s; arr_c[i]=s^0xDEADBEEFDEADBEEFULL;
    }
    /* triad pass — pure DRAM streaming */
    for(uint64_t i=0;i<N;i++)
        arr_a[i] = arr_b[i] + q * arr_c[i];
    /* readback/hash of a (the oracle surface) */
    uint64_t acc=0;
    for(uint64_t i=0;i<N;i++)
        acc ^= arr_a[i] + i;
    put("FINAL=");
    put_hex64(acc);
    put("\n");
    return 0;
}
