# workloads/sdcshield — SVE/SME dual-channel FI kernels (clang: SME asm).
# Static aarch64 builds; see plan 2026-10-13-sve-sme-fi-eval.md.
CC = clang
CFLAGS = -static -O2 -march=armv9-a+sve+sme -Wall -Wextra
# sme_fmopa_dual REQUIRES -ffp-contract=off: its scalar golden must stay
# double-rounding (mul;add) to match gem5 FMOPA fplib semantics (F4).
FP_OFF = -ffp-contract=off

# sleef_vla_dual links the sdcshield vendored SLEEF 3.9.0 install — the SAME
# libsleef.a machine code the PR #286 tests_sve_vla library links (pure VLA:
# cntd/cntp/rdvl, zero pattern-immediate ptrue) — and mirrors that TU's march
# (armv8.2-a+sve, no -msve-vector-bits; the later -march wins over the global
# armv9-a+sve+sme). -isystem keeps sleef.h warnings out of the zero-warning
# budget (same is_system: true treatment as the sdcshield meson block).
SDCSHIELD_SLEEF = /home/sdc/wangxu/operator/sdcshield/third-party/sleef/install
SLEEF_CFLAGS = -march=armv8.2-a+sve -isystem $(SDCSHIELD_SLEEF)/include
SLEEF_LDFLAGS = -L$(SDCSHIELD_SLEEF)/lib -l:libsleef.a

BINS = sve_sme_semantics fpu_special_sve_dual stencil_axis_dual
BINS += sme_fmopa_dual sme_za_tileview_dual
BINS += sleef_vla_dual sleef_vla_semantics sve_rot_vla_dual
BINS += sve512_fma_dual sve_arith_bounds_dual

all: $(BINS)

%: %.c
	$(CC) $(CFLAGS) $(if $(filter sme_fmopa_dual,$@),$(FP_OFF),) \
	    $(if $(filter sleef_vla_dual sleef_vla_semantics,$@),$(SLEEF_CFLAGS),) -o $@ $< \
	    $(if $(filter sleef_vla_dual sleef_vla_semantics,$@),$(SLEEF_LDFLAGS),) -lm

clean:
	rm -f $(BINS)

.PHONY: all clean
