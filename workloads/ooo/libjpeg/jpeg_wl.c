/* gem5-fi W1.4b: libjpeg-turbo JPEG decode workload (OoO north star W1.4).
 *
 * Role (docs/gem5-fi/ooo/03-workloads.md): JPEG compression/decompression
 * built on libjpeg-turbo's hand-written NEON SIMD kernels; verification =
 * pixel-exact output hash; workload purpose = FP/SIMD rename (vector
 * register file pressure).
 *
 * The embedded JPEG (embedded_jpg.h; generated once by the documented
 * gen_img.c -> vendored cjpeg pipeline, see PROVENANCE.md) is decoded
 * DECODE_ROUNDS times from a fixed in-memory buffer via jpeg_mem_src --
 * no runtime file I/O, so the binary is pure deterministic compute under
 * gem5 SE (malloc/free only; jmemnobs backing store).
 *
 * Oracle: every round's decoded RGB pixels are folded into ONE running
 * FNV-1a-64 state, so a fault corrupting ANY round's output changes the
 * final checksum -- transient faults in early rounds cannot hide (each
 * round re-decodes the same pristine input bytes and would otherwise
 * recover).  The fold is word-wise (8 little-endian bytes per step,
 * h = (h ^ w) * FNV64_PRIME): every pixel byte is still covered exactly
 * once, but the fold costs ~1/8 of a byte-serial FNV-1a pass, which
 * would otherwise rival the decode itself in instruction count and
 * dominate the SE budget.  The round index is folded in ahead of each
 * round's pixels so rounds cannot be transposed unnoticed.
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "jpeglib.h"
#include "embedded_jpg.h"

#ifndef DECODE_ROUNDS
#define DECODE_ROUNDS 4
#endif

#define FNV64_BASIS 14695981039346656037ULL
#define FNV64_PRIME 1099511628211ULL

static uint64_t fnv1a_word(uint64_t h, uint64_t w)
{
    return (h ^ w) * FNV64_PRIME;
}

int main(void)
{
    struct jpeg_decompress_struct cinfo;
    struct jpeg_error_mgr jerr;
    unsigned char *pix;
    size_t row_stride, npix, i;
    JDIMENSION img_w = 0, img_h = 0;
    uint64_t h = FNV64_BASIS;
    int r;

    /* Probe pass: read the header once to size the output buffer. */
    cinfo.err = jpeg_std_error(&jerr);
    jpeg_create_decompress(&cinfo);
    jpeg_mem_src(&cinfo, embedded_jpg, (unsigned long)embedded_jpg_len);
    jpeg_read_header(&cinfo, TRUE);
    cinfo.out_color_space = JCS_RGB;
    jpeg_start_decompress(&cinfo);
    row_stride = (size_t)cinfo.output_width * cinfo.output_components;
    npix = row_stride * cinfo.output_height;
    img_w = cinfo.output_width;
    img_h = cinfo.output_height;
    jpeg_abort_decompress(&cinfo);
    jpeg_destroy_decompress(&cinfo);

    pix = malloc(npix);
    if (pix == NULL) {
        fprintf(stderr, "jpeg_wl: out of memory (%zu bytes)\n", npix);
        return EXIT_FAILURE;
    }

    for (r = 0; r < DECODE_ROUNDS; r++) {
        cinfo.err = jpeg_std_error(&jerr);
        jpeg_create_decompress(&cinfo);
        jpeg_mem_src(&cinfo, embedded_jpg, (unsigned long)embedded_jpg_len);
        jpeg_read_header(&cinfo, TRUE);
        cinfo.out_color_space = JCS_RGB;
        jpeg_start_decompress(&cinfo);
        while (cinfo.output_scanline < cinfo.output_height) {
            JSAMPROW row = pix + row_stride * cinfo.output_scanline;
            jpeg_read_scanlines(&cinfo, &row, 1);
        }
        jpeg_finish_decompress(&cinfo);
        jpeg_destroy_decompress(&cinfo);

        /* Fold this round's pixels into the running hash. */
        h = fnv1a_word(h, (uint64_t)r);
        for (i = 0; i + 8 <= npix; i += 8) {
            uint64_t w;
            memcpy(&w, pix + i, 8);
            h = fnv1a_word(h, w);
        }
        if (i < npix) {                 /* zero-padded tail word */
            uint64_t w = 0;
            memcpy(&w, pix + i, npix - i);
            h = fnv1a_word(h, w);
        }
    }

    free(pix);
    printf("jpeg_wl: image=%ux%u RGB, %zu bytes/round, rounds=%d\n",
           (unsigned)img_w, (unsigned)img_h, npix, DECODE_ROUNDS);
    /* gem5-fi W1.4b: FINAL line for the oracle chain (tools/classify.py
     * _CHECKSUM_RE); the no-injection value (native == gem5) is golden. */
    printf("FINAL=%016llx\n", (unsigned long long)h);
    return EXIT_SUCCESS;
}
