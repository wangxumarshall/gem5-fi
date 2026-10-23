# workloads/sdcshield — SVE/SME dual-channel FI kernels (clang: SME asm).
# Static aarch64 builds; see plan 2026-10-13-sve-sme-fi-eval.md.
CC = clang
GCC = gcc
CFLAGS = -static -O2 -march=armv9-a+sve+sme -Wall -Wextra
GCCFLAGS = -static -O2 -march=armv9-a+sve -Wall -Wextra
# sme_fmopa_dual REQUIRES -ffp-contract=off: its scalar golden must stay
# double-rounding (mul;add) to match gem5 FMOPA fplib semantics (F4).
FP_OFF = -ffp-contract=off

BINS = sve_sme_semantics fpu_special_sve_dual stencil_axis_dual
BINS += sme_fmopa_dual sme_za_tileview_dual

all: $(BINS) vl_api_probe sme_fmopa_za_dual

%: %.c
	$(CC) $(CFLAGS) $(if $(filter sme_fmopa_dual,$@),$(FP_OFF),) -o $@ $< -lm

# all-VL Phase 2 P1 探针 (gcc 构建, 镜像 sdcshield arm64_vl.h 查询层;
# .inst 定数编码只需 -march=armv9-a+sve, 无需 SME 助记符/clang)
vl_api_probe: vl_api_probe.c
	$(GCC) $(GCCFLAGS) -o $@ $< -lm

# all-VL Phase 2 P2 语义裁决 kernel (sme_fmopa_za_arm 重构的镜像;
# 含 SME 助记符 -> gcc +sme march, 无需 clang)
sme_fmopa_za_dual: sme_fmopa_za_dual.c
	$(GCC) -static -O2 -march=armv9-a+sve+sme -Wall -Wextra -o $@ $< -lm

clean:
	rm -f $(BINS) vl_api_probe sme_fmopa_za_dual

.PHONY: all clean
