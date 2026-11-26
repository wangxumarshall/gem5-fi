#include <stdint.h>
#include <stdio.h>
#include <string.h>

extern void c01_m002(uint8_t *);
extern void c02_m002(uint8_t *);
extern void c03_m002(uint8_t *);
extern void c04_m002(uint8_t *);
extern void c05_m002(uint8_t *);

int
main(int argc, char **argv)
{
    uint8_t out[8][16] = {{0}};
    const char *ctx = argc > 1 ? argv[1] : "C01";
    if (argc <= 1) {
        const char *q = strrchr(argv[0], '_');
        if (q && q[1] == 'C') ctx = q + 1;
    }
    printf("ROI_START %s\n", ctx);
    fflush(stdout);
    if (!strcmp(ctx, "C01")) c01_m002(out[0]);
    else if (!strcmp(ctx, "C02")) c02_m002(out[0]);
    else if (!strcmp(ctx, "C03")) c03_m002(out[0]);
    else if (!strcmp(ctx, "C04")) c04_m002(out[0]);
    else if (!strcmp(ctx, "C05")) c05_m002(out[0]);
    else { printf("BAD_CONTEXT\n"); return 2; }
    printf("ROI_DONE %s\n", ctx);
    for (int i = 0; i < 8; i++) {
        printf("OUT %d", i);
        for (int b = 0; b < 16; b++)
            printf(" %02x", out[i][b]);
        printf("\n");
    }
    return 0;
}
