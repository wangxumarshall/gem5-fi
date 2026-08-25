/* Minimal AArch64 FMA probe mirroring reproduce-method2 §8.4 eigen_gemm_float:
 * FMA matrix multiply with byte-exact self-check (no tolerance, single mantissa bit fails).
 * Exits 0 on pass, 1 on SDC detection. libc-only. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define DIM 64  /* 64x64 float = 16KB, fits L1D; cross-line writeback */

static uint32_t rng_state = 0x91028731u;
static inline uint32_t xorshift32(void) {
    uint32_t x = rng_state; x ^= x<<13; x ^= x>>17; x ^= x<<5;
    rng_state = x; return x;
}
static inline float rng_f(void) {
    /* uniform-ish float in [0.5, 2.0) from 32 bits */
    uint32_t u = xorshift32();
    union { uint32_t i; float f; } v;
    v.i = 0x3f000000u | (u >> 9);  /* [0.5, 1.0) */
    return v.f + 1.0f;
}

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 50;
    int n = DIM;
    float *A = malloc(n*n*sizeof(float));
    float *B = malloc(n*n*sizeof(float));
    float *C = malloc(n*n*sizeof(float));
    float *golden = malloc(n*n*sizeof(float));
    if (!A||!B||!C||!golden) return 2;

    for (int i=0;i<n*n;i++){ A[i]=rng_f(); B[i]=rng_f(); }
    /* golden once (no FI expected here; recomputed C must byte-match) */
    for (int i=0;i<n;i++) for (int j=0;j<n;j++){
        float s=0.0f;
        for (int k=0;k<n;k++) s += A[i*n+k]*B[k*n+j];  /* fmadd */
        golden[i*n+j]=s;
    }
    long fails=0;
    for (long it=0; it<iters; it++) {
        if ((it & 15)==0){ rng_state=(uint32_t)(0x9e3779b9u*(it+1));
            for(int i=0;i<n*n;i++){A[i]=rng_f();B[i]=rng_f();}
            for(int i=0;i<n;i++)for(int j=0;j<n;j++){float s=0.0f;
                for(int k=0;k<n;k++)s+=A[i*n+k]*B[k*n+j];golden[i*n+j]=s;}
        }
        for (int i=0;i<n;i++) for (int j=0;j<n;j++){
            float s=0.0f;
            for (int k=0;k<n;k++) s += A[i*n+k]*B[k*n+j];
            C[i*n+j]=s;
        }
        if (memcmp(C, golden, n*n*sizeof(float))!=0){
            for (int idx=0; idx<n*n; idx++){
                if (C[idx]!=golden[idx]){
                    fails++;
                    union{float f;uint32_t u;}g,a;
                    g.f=golden[idx]; a.f=C[idx];
                    if (fails<=8) fprintf(stderr,"SDC@it=%ld idx=%d golden=%08x actual=%08x xor=%08x\n",
                        it,idx,g.u,a.u,g.u^a.u);
                    break;
                }
            }
        }
    }
    free(A);free(B);free(C);free(golden);
    printf("iters=%ld fails=%ld\n", iters, fails);
    return fails ? 1 : 0;
}
