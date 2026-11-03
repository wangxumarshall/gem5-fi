/* fft_radix2_kernel.c — fixed-input iterative radix-2 Cooley-Tukey FFT.
 *
 * Author : gem5-fi project contributors (2026).
 * License: original code authored for this repository; distributed under
 *          the same terms as the rest of gem5-fi (see CLAUDE.md).
 *
 * W6 artifact contract
 *   * N = 1024 complex points, fixed deterministic input, no rand()/time.
 *   * iterative radix-2 decimation-in-time FFT, no recursion.
 *   * live-out array: out[n] = |X[n]|^2 (fp32, row-major, count 1024).
 *   * prints "FINAL=<16hex>" = FNV-1a 64 over the raw fp32 bytes of `out`
 *     (same offset basis/prime as the PolyBench W1.3/W5 kernels).
 *   * optional raw little-endian dump of `out` via --array-dump=<path> (or
 *     POLYBENCH_ARRAY_DUMP); no-op otherwise. FINAL is unchanged.
 *
 * Build (reproducible):
 *   gcc -O2 -static -Wall -Wextra -I ../ooo/polybench/utilities \
 *       -o fft_radix2_kernel fft_radix2_kernel.c -lm
 */
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#include <gem5fi_oracle.h>

#define FFT_N 1024
#define FFT_PI 3.14159265358979323846f

static float re[FFT_N];
static float im[FFT_N];
static float out[FFT_N];

int main(int argc, char **argv)
{
    int i;

    /* Fixed input: integer-derived real samples in [-1, 1), imag = 0. */
    for (i = 0; i < FFT_N; i++) {
        re[i] = (float)(((i * 37 + 11) % 101) - 50) / 50.0f;
        im[i] = 0.0f;
    }

    /* Bit-reversal permutation. */
    {
        int j = 0;
        for (i = 1; i < FFT_N; i++) {
            int bit = FFT_N >> 1;
            for (; j & bit; bit >>= 1)
                j ^= bit;
            j ^= bit;
            if (i < j) {
                float tr = re[i], ti = im[i];
                re[i] = re[j]; im[i] = im[j];
                re[j] = tr;    im[j] = ti;
            }
        }
    }

    /* Iterative radix-2 butterflies. */
    {
        int len;
        for (len = 2; len <= FFT_N; len <<= 1) {
            int half = len >> 1;
            int j;
            float ang = -2.0f * FFT_PI / (float)len;
            for (j = 0; j < half; j++) {
                float wr = cosf(ang * (float)j);
                float wi = sinf(ang * (float)j);
                int k;
                for (k = j; k < FFT_N; k += len) {
                    int m = k + half;
                    float ur = re[k], ui = im[k];
                    float vr = re[m] * wr - im[m] * wi;
                    float vi = re[m] * wi + im[m] * wr;
                    re[k] = ur + vr;
                    im[k] = ui + vi;
                    re[m] = ur - vr;
                    im[m] = ui - vi;
                }
            }
        }
    }

    /* Live-out power spectrum. */
    for (i = 0; i < FFT_N; i++)
        out[i] = re[i] * re[i] + im[i] * im[i];

    {
        const unsigned char *p = (const unsigned char *)out;
        uint64_t h = 0xcbf29ce484222325ULL;
        unsigned long fi;
        for (fi = 0; fi < sizeof(float) * (unsigned long)FFT_N; fi++) {
            h ^= p[fi];
            h *= 0x100000001b3ULL;
        }
        printf("FINAL=%016llx\n", (unsigned long long)h);
    }

    gem5fi_oracle_dump_from_argv(argc, argv, out,
                                 (unsigned long)FFT_N, sizeof(float));
    return 0;
}
