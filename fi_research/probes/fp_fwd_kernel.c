/* Float store->load forwarding probe (method2 §8.5 minimal form).
 * Writes a double to memory via a volatile pointer, immediately loads the
 * SAME address (store->load forwarding through the store buffer), and
 * byte-exact self-checks. The volatile forces real str/ldr (no register
 * reuse), and same-address adjacency triggers the LSQ FullAddrRangeCoverage
 * forward path that CHAOSLSQFwd hooks. Produces IEEE754 (double) SDC so P6
 * can compute the mantissa/sign/exponent spectrum. libc-only, scalar.
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define N 2048   /* 16KB of doubles */

static uint32_t rng_state = 0x1BADC0DEu;
static inline uint32_t xorshift32(void){uint32_t x=rng_state;x^=x<<13;x^=x>>17;x^=x<<5;rng_state=x;return x;}
static inline double rng_d(void){
    union{uint64_t u; double d;} v;
    v.u = 0x3FF0000000000000ULL | ((uint64_t)xorshift32() << 21);
    return v.d;
}

int main(int argc, char**argv){
    long iters = (argc>1)?atol(argv[1]):500;
    volatile double *buf = (volatile double*)malloc(N*sizeof(double));
    double *golden = (double*)malloc(N*sizeof(double));
    if(!buf||!golden) return 2;
    long fails=0;
    for(long it=0; it<iters; it++){
        if((it&127)==0){ rng_state=(uint32_t)(0x9e3779b9u*(it+1));
            for(int i=0;i<N;i++) golden[i]=rng_d();
            for(int i=0;i<N;i++) buf[i] = golden[i];   /* seed buf == golden */
        }
        for(int i=0;i<N;i++){
            double w = golden[i];
            buf[i] = w;            /* str (volatile) */
            double r = buf[i];     /* ldr same addr -> store->load forward */
            if (r != w) {
                fails++;
                if(fails<=12){
                    union{double d;uint64_t u;}g,a; g.d=w; a.d=r;
                    fprintf(stderr,"SDC@it=%ld i=%d golden=%016lx actual=%016lx xor=%016lx\n",
                        it,i,g.u,a.u,g.u^a.u);
                }
            }
        }
    }
    free((void*)buf); free(golden);
    printf("iters=%ld fails=%ld\n", iters, fails);
    return fails?1:0;
}
