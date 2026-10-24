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

all: $(BINS) vl_api_probe sme_fmopa_za_dual sve512_chain_dual sve512_gather_dual sleef_vla_dual sve_rot_dual

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

# all-VL Phase 2 P3 kernels (sve512 家族×10 重构的镜像; 纯 SVE intrinsics,
# gcc armv9-a+sve 即可; stencil_axis_dual.c 取 7bed7f0e 全 VL 版 + memcpy
# 告警修复, 四档 16 run 重验):
sve512_chain_dual: sve512_chain_dual.c
	$(GCC) $(GCCFLAGS) -o $@ $< -lm
sve512_gather_dual: sve512_gather_dual.c
	$(GCC) $(GCCFLAGS) -o $@ $< -lm
# stencil_axis_dual (all-VL 7bed7f0e form): pure intrinsics — build with
# gcc too (the clang pattern rule does not apply on this host):
stencil_axis_dual: stencil_axis_dual.c
	$(GCC) $(GCCFLAGS) -o $@ $< -lm

clean:
	rm -f $(BINS) vl_api_probe sme_fmopa_za_dual sve512_chain_dual sve512_gather_dual sleef_vla_dual sve_rot_dual

.PHONY: all clean

# all-VL Phase 2 P5 kernel (sleef VLA migration judgment; links the
# vendored SLEEF static lib — gitignored, absolute path dependency):
SLEEF_INSTALL = /home/sdc/wangxu/code-review/sdcshield-sve/third-party/sleef/install
sleef_vla_dual: sleef_vla_dual.c
	$(GCC) $(GCCFLAGS) -I$(SLEEF_INSTALL)/include -o $@ $< $(SLEEF_INSTALL)/lib/libsleef.a -lm

# all-VL Phase 2 P5 remediation kernel (adversarial review Important-2:
# the sve_rot family's VLA migration needs runtime evidence at all tiers):
sve_rot_dual: sve_rot_dual.c
	$(GCC) $(GCCFLAGS) -o $@ $<
