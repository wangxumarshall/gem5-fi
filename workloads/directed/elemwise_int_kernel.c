/* elemwise_int_kernel — v1.2 Phase 13 patch 3 (task_plan 13 item 3).
 *
 * The per-element INT workload the Exec campaign needs (the analog of
 * elemwise_fma for the FPU): mixed ALU/multiply work where every element's
 * result flows to the output array un-reduced:
 *   for i: c[i] = (a[i] * b[i]) ^ ((a[i] + b[i]) >> 3)
 * — an integer FMA-analog with a data-dependent shift so no two elements
 * share a mask pattern. Output = the whole c[] (ARRAYHASH 4-lane FNV +
 * ELEMDIFF self-diff vs an in-run golden copy). Static AArch64, no libc.
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#ifndef N
#define N 8192
#endif

static uint64_t a[N], b[N], c_golden[N], c_check[N];

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
    /* deterministic inputs (LCG) */
    uint64_t s=0x243F6A8885A308D3ULL;
    for(int i=0;i<N;i++){
        s=s*6364136223846793005ULL+1442695040888963407ULL;
        a[i]=s;
        b[i]=s^0x9E3779B97F4A7C15ULL;
    }
    /* golden pass */
    for(int i=0;i<N;i++)
        c_golden[i] = (a[i] * b[i]) ^ ((a[i] + b[i]) >> 3);
    /* check pass — identical data; divergence = injected fault only. */
    for(int i=0;i<N;i++)
        c_check[i] = (a[i] * b[i]) ^ ((a[i] + b[i]) >> 3);

    /* ARRAYHASH over c_check bytes. */
    put("ARRAYHASH=");
    const unsigned char *p=(const unsigned char*)c_check;
    unsigned total=sizeof(c_check), q=(total+3)/4;
    for(int lane=0; lane<4; lane++){
        uint64_t h=1469598103934665603ULL ^ (0x9e3779b9ULL*lane);
        for(unsigned j=lane*q; j<(lane+1)*q && j<total; j++){
            h^=p[j]; h*=1099511628211ULL;
        }
        put_hex64(h);
    }
    put("\n");

    /* ELEMDIFF vs the in-run golden copy. */
    uint64_t n_diff=0, first=0;
    for(int i=0;i<N;i++){
        if(c_check[i]!=c_golden[i]){
            if(!n_diff) first=i;
            n_diff++;
        }
    }
    put("ELEMDIFF n="); put_u64(n_diff);
    put(" first=");     put_u64(first);
    put(" maxulp=");    put_u64(n_diff ? 1 : 0);
    put("\n");
    put("ULP="); put_u64(n_diff ? 1 : 0); put("\n");
    return 0;
}
