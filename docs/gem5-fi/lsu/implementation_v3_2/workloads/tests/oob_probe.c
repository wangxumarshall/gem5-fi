/* Diagnostic guard-page probe for the W6/W8 tail overflows.
 * Not a workload. It reproduces the exact final offset of each original
 * source on an mmap'd object whose next page is PROT_NONE. A SIGSEGV proves
 * the access leaves the declared array. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

static void *guarded(size_t n) {
    long ps = sysconf(_SC_PAGESIZE);
    size_t body = ((n + (size_t)ps - 1) / (size_t)ps) * (size_t)ps;
    uint8_t *base = mmap(NULL, body + (size_t)ps, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (base == MAP_FAILED) { perror("mmap"); exit(2); }
    if (mprotect(base + body, (size_t)ps, PROT_NONE) != 0) { perror("mprotect"); exit(2); }
    return base + body - n;   /* object ends exactly at the guard page */
}

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: %s store_path|alignment\n", argv[0]); return 2; }
    if (strcmp(argv[1], "store_path") == 0) {
        volatile uint8_t *a = guarded(32768);
        for (int i = 0; i < 4096; i++) {
            *(volatile uint64_t *)(a + 16384 + i * 4) = 1;  /* original W6 tail */
        }
    } else if (strcmp(argv[1], "alignment") == 0) {
        volatile uint8_t *a = guarded(4096);
        for (int i = 0; i < 1024; i++) {
            uint32_t v = (uint32_t)i;
            memcpy((void *)(a + i * 4 + 1), &v, 4);           /* original W8 tail */
        }
    } else if (strcmp(argv[1], "store_path_fixed") == 0) {
        volatile uint8_t *a = guarded(32768);
        for (int i = 0; i < 4096; i++) {
            uint16_t v = (uint16_t)i;
            memcpy((void *)(a + 4097 + i * 2), &v, 2);
        }
        for (int i = 0; i < 2048; i++) {
            uint32_t v = (uint32_t)i;
            memcpy((void *)(a + 12291 + i * 4), &v, 4);
        }
        for (int i = 0; i < 1024; i++) {
            uint64_t v = (uint64_t)i;
            memcpy((void *)(a + 20483 + i * 8), &v, 8);
        }
        for (int i = 0; i < 4093; i++) a[28675 + i] = (uint8_t)i;
    } else if (strcmp(argv[1], "alignment_fixed") == 0) {
        volatile uint8_t *a = guarded(4096);
        for (int i = 0; i < 1023; i++) {
            uint32_t v = (uint32_t)i;
            memcpy((void *)(a + i * 4 + 1), &v, 4);
        }
    } else {
        return 2;
    }
    printf("NO_FAULT\n");
    return 0;
}
