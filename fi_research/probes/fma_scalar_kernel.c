/* Scalar (non-vectorized) AArch64 FMA probe — forces fmadd dN (FloatRegClass),
 * NOT fmla vN (VecRegClass). Validates P1's FloatRegClass injection path.
 * Accumulator kept in a single double to make the FPU arch reg hot. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define DIM 48

static uint32_t rng_state = 0x55AABBCDu;
static inline uint32_t xorshift32(void){ uint32_t x=rng_state; x^=x<<13; x^=x>>17; x^=x<<5; rng_state=x; return x; }
static inline double rng_d(void){
    union{uint64_t u; double d;} v;
    v.u = 0x3FF0000000000000ULL | ((uint64_t)xorshift32() << 21);  /* [1.0, 2.0) */
    return v.d;
}

int main(int argc, char**argv){
    long iters = (argc>1)?atol(argv[1]):30;
    int n=DIM;
    double *A=malloc(n*n*sizeof(double));
    double *B=malloc(n*n*sizeof(double));
    double *C=malloc(n*n*sizeof(double));
    double *golden=malloc(n*n*sizeof(double));
    if(!A||!B||!C||!golden) return 2;
    for(int i=0;i<n*n;i++){A[i]=rng_d();B[i]=rng_d();}
    for(int i=0;i<n;i++)for(int j=0;j<n;j++){double s=0.0; for(int k=0;k<n;k++)s+=A[i*n+k]*B[k*n+j]; golden[i*n+j]=s;}
    long fails=0;
    for(long it=0;it<iters;it++){
        if((it&15)==0){rng_state=(uint32_t)(0x9e3779b9u*(it+1));
            for(int i=0;i<n*n;i++){A[i]=rng_d();B[i]=rng_d();}
            for(int i=0;i<n;i++)for(int j=0;j<n;j++){double s=0.0; for(int k=0;k<n;k++)s+=A[i*n+k]*B[k*n+j];golden[i*n+j]=s;}}
        for(int i=0;i<n;i++)for(int j=0;j<n;j++){
            double s=0.0;
            /* volatile barrier forces compiler to keep s as a live fp scalar acc */
            for(int k=0;k<n;k++){ s += A[i*n+k]*B[k*n+j]; }
            C[i*n+j]=s;
        }
        if(memcmp(C,golden,n*n*sizeof(double))!=0){
            for(int idx=0;idx<n*n;idx++){
                if(C[idx]!=golden[idx]){
                    fails++;
                    union{double d;uint64_t u;}g,a; g.d=golden[idx]; a.d=C[idx];
                    if(fails<=8) fprintf(stderr,"SDC@it=%ld idx=%d golden=%016lx actual=%016lx xor=%016lx\n",
                        it,idx,g.u,a.u,g.u^a.u);
                    break;
                }
            }
        }
    }
    free(A);free(B);free(C);free(golden);
    printf("iters=%ld fails=%ld\n",iters,fails);
    return fails?1:0;
}
