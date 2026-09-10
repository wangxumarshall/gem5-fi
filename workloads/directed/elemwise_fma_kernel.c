/* elemwise_fma_kernel — v1.1 Phase 9 patch 1b (task_plan 1b).
 *
 * The per-element FP workload the FPU campaign needs (design doc §1.7):
 *   for i: c[i] = a[i]*b[i] + d[i]
 * — outputting the WHOLE c[] array (not a reduced scalar checksum), so a
 * single flipped mantissa bit in one element survives to the oracle:
 *   ARRAYHASH=<64hex>   (4-lane FNV-1a over the raw bytes of c[])
 *   ULP=<max_ulp_error> (max ULP distance of c[i] vs the golden array)
 * The golden copy is computed in the same run (identical deterministic
 * inputs — divergence comes only from an injected fault).
 *
 * Static AArch64, no libc. --n adjustable at compile time via -DN.
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#ifndef N
#define N 8192
#endif

static double a[N], b[N], d[N], c_golden[N], c_check[N];

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

/* ULP distance between two finite doubles (IEEE754 number-line repr
 * distance; opposite signs counted via the two-zero adjacency). */
static uint64_t ulp_dist(double x, double y){
    if(x==y) return 0;
    uint64_t ux, uy;
    memcpy(&ux,&x,8); memcpy(&uy,&y,8);
    if((ux>>63)!=(uy>>63)){
        uint64_t ax=ux&0x7fffffffffffffffULL, ay=uy&0x7fffffffffffffffULL;
        return ax+ay+1;
    }
    return ux>uy ? ux-uy : uy-ux;
}

int main(void){
    /* deterministic inputs (LCG) */
    uint64_t s=0x243F6A8885A308D3ULL;
    for(int i=0;i<N;i++){
        s=s*6364136223846793005ULL+1442695040888963407ULL;
        a[i]=(double)(s%1000)*0.001+0.5;
        b[i]=(double)((s>>17)%1000)*0.001+0.25;
        d[i]=(double)((s>>33)%1000)*0.001-0.5;
    }
    /* golden pass — the FMA the compiler emits here is the corruption
     * target's twin: same code path, separate data. */
    for(int i=0;i<N;i++) c_golden[i]=a[i]*b[i]+d[i];
    /* check pass — identical data; divergence = injected fault only. */
    for(int i=0;i<N;i++) c_check[i]=a[i]*b[i]+d[i];

    /* ARRAYHASH over c_check bytes (4-lane FNV-1a -> 64 hex). */
    put("ARRAYHASH=");
    const unsigned char *p=(const unsigned char*)c_check;
    unsigned total=sizeof(c_check), q=(total+3)/4;
    for(int lane=0; lane<4; lane++){
        uint64_t h=1469598103934665603ULL ^ (0x9e3779b9ULL*lane);
        for(unsigned i=lane*q; i<(lane+1)*q && i<total; i++){
            h^=p[i]; h*=1099511628211ULL;
        }
        put_hex64(h);
    }
    put("\n");

    /* ULP vs the golden array. */
    uint64_t maxulp=0;
    for(int i=0;i<N;i++){
        uint64_t u=ulp_dist(c_check[i],c_golden[i]);
        if(u>maxulp) maxulp=u;
    }
    put("ULP="); put_u64(maxulp); put("\n");
    return 0;
}
