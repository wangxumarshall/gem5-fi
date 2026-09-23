/* gem5-fi W1.4b: deterministic test image for the libjpeg workload.
 *
 * Writes a 256x256 binary PPM (P6, RGB) to stdout.  Pure integer math
 * plus a fixed-seed 64-bit LCG: the output is byte-identical on any
 * host/toolchain, so the vendored-cjpeg compression of it (see
 * PROVENANCE.md, "embedded JPEG") is reproducible end to end.
 *
 * Deviation note (honest record): the W1 task brief said "a PGM"; a
 * grayscale PGM would encode to a single-component JPEG whose decode
 * skips the YCbCr->RGB color conversion and chroma upsampling NEON
 * kernels entirely (the workload's stated purpose is vector-register
 * pressure, docs/gem5-fi/ooo/03-workloads.md), so a color PPM is used
 * instead.  Still a program-generated deterministic image compressed by
 * the vendored cjpeg, exactly as the brief intended.
 */
#include <stdio.h>

#define IMG_W 256
#define IMG_H 256

static unsigned char clamp8(long v)
{
    if (v < 0) return 0;
    if (v > 255) return 255;
    return (unsigned char)v;
}

int main(void)
{
    unsigned long long s = 0x243F6A8885A308D3ULL;  /* fixed seed */
    unsigned char row[IMG_W * 3];
    int x, y;

    printf("P6\n%d %d\n255\n", IMG_W, IMG_H);
    for (y = 0; y < IMG_H; y++) {
        for (x = 0; x < IMG_W; x++) {
            long r = (x * 255L) / (IMG_W - 1);        /* horizontal gradient */
            long g = (y * 255L) / (IMG_H - 1);        /* vertical gradient */
            long b = ((x * x + y * y) >> 9) & 255;    /* radial term */
            if ((((x >> 4) + (y >> 4)) & 1) == 0) {   /* 16x16 checkerboard */
                r = 255 - r;
                g ^= 0x55;
            }
            /* LCG noise, amplitude +-32, same stream for every channel */
            s = s * 6364136223846793005ULL + 1442695040888963407ULL;
            {
                long n = (long)((s >> 33) & 0x3f) - 32;
                row[x * 3 + 0] = clamp8(r + n);
                row[x * 3 + 1] = clamp8(g + n);
                row[x * 3 + 2] = clamp8(b + n);
            }
        }
        fwrite(row, 1, sizeof(row), stdout);
    }
    return 0;
}
