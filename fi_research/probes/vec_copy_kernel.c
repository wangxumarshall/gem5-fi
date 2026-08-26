/* Vector copy kernel: load vector, store it back (no FMA, no divergence).
 * A bit-flip in the live VecReg between load and store reads as SDC.
 * libc-only, vectorized. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define N 4096  /* 16KB, vectorized copy */

static uint32_t rng_state = 0x77665544u;
static inline uint32_t xorshift32(void){uint32_t x=rng_state;x^=x<<13;x^=x>>17;x^=x<<5;rng_state=x;return x;}

int main(int argc,char**argv){
    long iters = (argc>1)?atol(argv[1]):2000;
    uint32_t *src=malloc(N*sizeof(uint32_t));
    uint32_t *dst=malloc(N*sizeof(uint32_t));
    if(!src||!dst) return 2;
    for(int i=0;i<N;i++) src[i]=xorshift32();
    long fails=0;
    for(long it=0;it<iters;it++){
        if((it&255)==0){rng_state=(uint32_t)(0x9e3779b9u*(it+1));
            for(int i=0;i<N;i++) src[i]=xorshift32();}
        /* vectorized copy: compiler emits ldr q/str q (VecReg) */
        memcpy(dst, src, N*sizeof(uint32_t));
        if (memcmp(dst, src, N*sizeof(uint32_t))!=0){
            fails++;
            if(fails<=8){
                for(int i=0;i<N;i++) if(dst[i]!=src[i]){
                    fprintf(stderr,"SDC@it=%ld i=%d golden=%08x actual=%08x xor=%08x\n",
                        it,i,src[i],dst[i],src[i]^dst[i]); break;}
            }
        }
    }
    free(src); free(dst);
    printf("iters=%ld fails=%ld\n",iters,fails);
    return fails?1:0;
}
