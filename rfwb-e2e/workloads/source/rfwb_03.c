#include <stdint.h>
#include <stdio.h>
#include <string.h>

extern void c01_m003(uint64_t *);
extern void c02_m003(uint64_t *);
extern void c03_m003(uint64_t *);
extern void c04_m003(uint64_t *);
extern void c05_m003(uint64_t *);

int
main(int argc, char **argv)
{
    uint64_t out[8] = {0};
    const char *ctx = argc > 1 ? argv[1] : "C01";
    if (argc <= 1) {
        const char *q = strrchr(argv[0], '_');
        if (q && q[1] == 'C') ctx = q + 1;
    }
    printf("ROI_START %s\n", ctx);
    fflush(stdout);
    if (!strcmp(ctx, "C01")) c01_m003(out);
    else if (!strcmp(ctx, "C02")) c02_m003(out);
    else if (!strcmp(ctx, "C03")) c03_m003(out);
    else if (!strcmp(ctx, "C04")) c04_m003(out);
    else if (!strcmp(ctx, "C05")) c05_m003(out);
    else { printf("BAD_CONTEXT\n"); return 2; }
    printf("ROI_DONE %s\n", ctx);
    for (int i = 0; i < 8; i++)
        printf("OUT %d %016llx\n", i, (unsigned long long)out[i]);
    return 0;
}
