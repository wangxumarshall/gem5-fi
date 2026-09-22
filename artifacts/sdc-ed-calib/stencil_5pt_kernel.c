/* stencil_5pt_kernel — v1.1 Phase 11 patch 3a (task_plan 3a).
 *
 * 5-point stencil over a W×W grid of uint64: out[i][j] =
 * in[i][j] + in[i-1][j] + in[i+1][j] + in[i][j-1] + in[i][j+1].
 * Working set = 2 * W*W * 8 bytes (in + out). Default W=160 -> 2*200KB =
 * 400KB ~ 6x L1 (64KB) and just under L2 (512KB) so a large fraction of
 * accesses hit L2; -DW=256 gives 2*512KB = 2x L2 (miss-heavy). The whole
 * out grid is hashed (ARRAYHASH, 64 hex) — an L2-data fault that flips a
 * byte the final pass reads is SDC; a clean run hashes to the golden.
 * Static AArch64, no libc. */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#ifndef W
#define W 160
#endif

static uint64_t grid_a[W][W], grid_b[W][W];

static void put(const char *s){ write(1, s, strlen(s)); }
static void put_hex64(uint64_t v){
    char buf[16];
    for(int i=15;i>=0;--i){ unsigned x=v&0xf; buf[i]=x<10?'0'+x:'a'+x-10; v>>=4; }
    write(1,buf,16);
}

int main(void){
    uint64_t s=0x243F6A8885A308D3ULL;
    for(int i=0;i<W;i++)
        for(int j=0;j<W;j++){
            s=s*6364136223846793005ULL+1442695040888963407ULL;
            grid_a[i][j]=s;
        }
    /* stencil pass: b = a + neighbors */
    for(int i=0;i<W;i++)
        for(int j=0;j<W;j++){
            uint64_t v = grid_a[i][j];
            if (i > 0)     v += grid_a[i-1][j];
            if (i+1 < W)   v += grid_a[i+1][j];
            if (j > 0)     v += grid_a[i][j-1];
            if (j+1 < W)   v += grid_a[i][j+1];
            grid_b[i][j] = v;
        }
    /* readback pass over the OUTPUT grid (the oracle surface): every
     * element is re-read after the stencil completes — a corrupted byte
     * anywhere in grid_b (or grid_a before its last consumer) surfaces. */
    uint64_t acc=0;
    for(int i=0;i<W;i++)
        for(int j=0;j<W;j++)
            acc ^= grid_b[i][j] * 0x9E3779B97F4A7C15ULL + (uint64_t)(i*W+j);
    put("FINAL=");
    put_hex64(acc);
    put("\n");
    return 0;
}
