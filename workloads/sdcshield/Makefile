# workloads/sdcshield — SVE/SME dual-channel FI kernels (clang: SME asm).
# Static aarch64 builds; see plan 2026-10-13-sve-sme-fi-eval.md.
CC = clang
CFLAGS = -static -O2 -march=armv9-a+sve+sme -Wall -Wextra
# sme_fmopa_dual REQUIRES -ffp-contract=off: its scalar golden must stay
# double-rounding (mul;add) to match gem5 FMOPA fplib semantics (F4).
FP_OFF = -ffp-contract=off

BINS = sve_sme_semantics fpu_special_sve_dual stencil_axis_dual
BINS += sme_fmopa_dual sme_za_tileview_dual

all: $(BINS)

%: %.c
	$(CC) $(CFLAGS) $(if $(filter sme_fmopa_dual,$@),$(FP_OFF),) -o $@ $< -lm

clean:
	rm -f $(BINS)

.PHONY: all clean
