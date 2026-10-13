# workloads/sdcshield — SVE/SME dual-channel FI kernels (clang: SME asm).
# Static aarch64 builds; see plan 2026-10-13-sve-sme-fi-eval.md.
CC = clang
CFLAGS = -static -O2 -march=armv9-a+sve+sme -Wall -Wextra

BINS = sve_sme_semantics

all: $(BINS)

%: %.c
	$(CC) $(CFLAGS) -o $@ $< -lm

clean:
	rm -f $(BINS)

.PHONY: all clean
