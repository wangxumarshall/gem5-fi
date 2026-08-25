/* Scalar integer RMW kernel (method2 §8.2 style), no vectorization.
 * Forces adjacent str->ldr of same address (store-to-load forwarding path)
 * through inline asm with memory clobber. Exits 0 on pass, 1 on SDC. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

#define N 1024   /* 8KB, cross-line */

static uint32_t rng_state = 0xC0FFEE11u;
static inline uint32_t xorshift32(void){uint32_t x=rng_state;x^=x<<13;x^=x>>17;x^=x<<5;rng_state=x;return x;}

int main(int argc,char**argv){
    long iters = (argc>1)?atol(argv[1]):2000;
    uint64_t *srcA=malloc(N*sizeof(uint64_t));
    uint64_t *srcB=malloc(N*sizeof(uint64_t));
    uint64_t *dst=malloc(N*sizeof(uint64_t));
    uint64_t *expected=malloc(N*sizeof(uint64_t));
    uint64_t *temp=malloc(N*sizeof(uint64_t));
    if(!srcA||!srcB||!dst||!expected||!temp) return 2;
    for(int i=0;i<N;i++){srcA[i]=((uint64_t)xorshift32()<<32)|xorshift32();
                         srcB[i]=((uint64_t)xorshift32()<<32)|xorshift32();}
    for(int i=0;i<N;i++){
        uint64_t a=srcA[i],b=srcB[i],r;
        switch(i&3){case 0:r=a+b;break;case 1:r=a-b;break;case 2:r=a^b;break;default:r=a&b;}
        expected[i]=r;
    }
    long fails=0;
    for(long it=0;it<iters;it++){
        if((it&255)==0){rng_state=(uint32_t)(0x9e3779b9u*(it+1));
            for(int i=0;i<N;i++){srcA[i]=((uint64_t)xorshift32()<<32)|xorshift32();
                                 srcB[i]=((uint64_t)xorshift32()<<32)|xorshift32();}
            for(int i=0;i<N;i++){uint64_t a=srcA[i],b=srcB[i],r;
                switch(i&3){case 0:r=a+b;break;case 1:r=a-b;break;case 2:r=a^b;break;default:r=a&b;}
                expected[i]=r;}
        }
        for(int i=0;i<N;i++){
            uint64_t a=srcA[i], b=srcB[i], res, t;
            switch(i&3){case 0:res=a+b;break;case 1:res=a-b;break;case 2:res=a^b;break;default:res=a&b;}
            /* store res to temp[i], immediately load temp[i] (forwarding),
               store to dst[i]. Same-address str->ldr adjacency via asm. */
            uint64_t idxv = (uint64_t)i;
            __asm__ volatile(
                "str %[val], [%[tmp], %[idx], lsl #3]\n"
                "ldr %[lvd], [%[tmp], %[idx], lsl #3]\n"
                "str %[lvd], [%[outp], %[idx], lsl #3]\n"
                : [lvd]"=r"(t)
                : [val]"r"(res), [tmp]"r"(temp), [outp]"r"(dst), [idx]"r"(idxv)
                : "memory");
            if (t != res) {
                fails++;
                if(fails<=8) fprintf(stderr,"SDC@it=%ld i=%d golden=%016lx actual=%016lx xor=%016lx\n",
                    it,i,res,t,res^t);
            }
        }
    }
    free(srcA);free(srcB);free(dst);free(expected);free(temp);
    printf("iters=%ld fails=%ld\n",iters,fails);
    return fails?1:0;
}
