/* Minimal single-accumulator kernel for SDC FI verification.
 * Accumulates into a register pinned via inline asm to x9, compares to a
 * golden recomputation. Injecting x9 (the live accumulator) during the loop
 * MUST produce SDC unless masked. libc-only, no vectorization. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

#define N 4096

static uint32_t rng_state = 0x5A5A1234u;
static inline uint32_t xorshift32(void){uint32_t x=rng_state;x^=x<<13;x^=x>>17;x^=x<<5;rng_state=x;return x;}

int main(int argc,char**argv){
    long iters = (argc>1)?atol(argv[1]):500;
    uint32_t *data = malloc(N*sizeof(uint32_t));
    uint32_t *gold = malloc(N*sizeof(uint32_t));
    if(!data||!gold) return 2;
    for(int i=0;i<N;i++){data[i]=xorshift32(); gold[i]=data[i];}
    long fails=0;
    for(long it=0;it<iters;it++){
        if((it&127)==0){rng_state=(uint32_t)(0x9e3779b9u*(it+1));
            for(int i=0;i<N;i++){data[i]=xorshift32(); gold[i]=data[i];}}
        /* accumulate data[i] into a single live register pinned to x9.
           Injecting x9 mid-loop changes the sum -> SDC. */
        register uint64_t acc __asm__("x9") = 0;
        for(int i=0;i<N;i++){
            uint64_t v = data[i];
            __asm__ volatile(
                "add %[acc], %[acc], %[val]\n"
                : [acc]"+r"(acc)
                : [val]"r"(v)
            );
        }
        uint64_t acc_out = acc;
        /* golden recompute over the SAME data (data not mutated) */
        uint64_t g = 0;
        for(int i=0;i<N;i++) g += data[i];
        if (acc_out != g){
            fails++;
            if(fails<=8) fprintf(stderr,"SDC@it=%ld golden=%016lx actual=%016lx xor=%016lx\n",
                it,g,acc_out,g^acc_out);
        }
    }
    free(data); free(gold);
    printf("iters=%ld fails=%ld\n",iters,fails);
    return fails?1:0;
}
