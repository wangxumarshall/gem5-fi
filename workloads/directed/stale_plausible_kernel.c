/* stale_plausible_kernel — v1.2 Phase 13 patch 4 (task_plan 13 item 4).
 *
 * The F6 stale-value probe: two independent producer chains updating the
 * SAME architectural variables in a loop, with consumers reading them at
 * staggered points. Under CHAOSIQ src_ready_bitflip (wrong-source wakeup),
 * a consumer issues early and reads the producer's PREVIOUS value — a
 * stale-but-LEGAL result (the last iteration's output, not garbage). This
 * is the realistic F6 form: stale plausible data, which ECC/tag checks
 * cannot catch (the value was perfectly valid one iteration ago).
 *
 *   chain A: a = f(a);  chain B: b = g(b);   (independent, interleaved)
 *   consumer: out[i] = a ^ b;  (both read every iteration — an early wake
 *   reads the previous a or b)
 * Output: whole out[] (ARRAYHASH + ELEMDIFF vs in-run golden).
 * Static AArch64, no libc.
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#ifndef N
#define N 4096
#endif

static uint64_t out[N], out_golden[N];

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

static inline uint64_t step_a(uint64_t x){ return x ^ (x<<13) ^ (x>>7); }
static inline uint64_t step_b(uint64_t x){ return x + 0x9E3779B97F4A7C15ULL; }

int main(void){
    uint64_t a=0x1234567890abcdefULL, b=0xfedcba0987654321ULL;
    /* golden pass (records what the CONSUMERS should see per iteration) */
    {
        uint64_t ga=a, gb=b;
        for(int i=0;i<N;i++){
            ga=step_a(ga); gb=step_b(gb);
            out_golden[i]=ga^gb;
        }
    }
    /* check pass — same data; divergence = injected fault only. */
    {
        uint64_t ca=a, cb=b;
        for(int i=0;i<N;i++){
            ca=step_a(ca); cb=step_b(cb);
            out[i]=ca^cb;
        }
    }

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

    uint64_t n_diff=0, first=0;
    for(int i=0;i<N;i++)
        if(out[i]!=out_golden[i]){ if(!n_diff) first=i; n_diff++; }
    put("ELEMDIFF n="); put_u64(n_diff);
    put(" first=");     put_u64(first);
    put(" maxulp=");    put_u64(n_diff ? 1 : 0);
    put("\n");
    put("ULP="); put_u64(n_diff ? 1 : 0); put("\n");
    return 0;
}
