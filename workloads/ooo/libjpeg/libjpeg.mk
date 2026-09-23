# workloads/ooo/libjpeg/libjpeg.mk — W1.4b libjpeg-turbo workload build rules.
#
# Included from workloads/ooo/Makefile (kept per-directory, like coremark/
# keeps its own build logic, so the shared framework Makefile stays small:
# this workload carries a 117-object upstream source set).
#
# PROVENANCE: see libjpeg/PROVENANCE.md FIRST (upstream repo/commit, vendored
# file inventory, the checked-in cmake-generated headers under libjpeg/cfg/,
# the embedded-JPEG regeneration pipeline, and the honest deviations).
#
# Build recipe = a hand-rolled transcription of the upstream cmake build for
# aarch64 (WITH_SIMD=1 — NEON is mandatory on Armv8 and jsimdcpu.c enables
# it unconditionally, ENABLE_SHARED=0, CMAKE_BUILD_TYPE=Release; upstream's
# cmake replaces cmake's default -O2 with -O3).  Every object compiles with
# the exact flags captured from the cmake-generated flags.make:
#   "-Wall -Wextra -O3 -DNDEBUG" + -Icfg (library) / + -Icfg/simd/arm (NEON).
# Cross-checked against a real cmake build of the same commit: identical
# 117-member archive set (PROVENANCE.md "recipe verification").
#
# Upstream code-quality warning suppressions (any NEW warning class fails
# the build; full rationale in PROVENANCE.md):
#   -Wno-unused-parameter : 285 sites — libjpeg method callbacks with
#       API-fixed signatures (e.g. jccolor.c null_method) whose specific
#       methods legitimately ignore parameters.
#   -Wno-sign-compare     : 2 sites — jdphuff.c HUFF_EXTEND macro's
#       "s < 0 ? -s : s" changes signedness in the unsigned path.
LIBJPEG_DIR := libjpeg
LIBJPEG_CFG := libjpeg/cfg
LIBJPEG_OBJ := libjpeg/build
LIBJPEG_AR  := libjpeg/build/libjpeg.a

LIBJPEG_NOWARN  := -Wno-unused-parameter -Wno-sign-compare
LIBJPEG_CFLAGS  := -O3 -DNDEBUG -Wall -Wextra $(LIBJPEG_NOWARN)

# Decode rounds: the SE-budget knob (C3 SE <=60s hostSeconds, W1 Global
# Constraints).  FINAL depends on this value (the round index is folded
# into the hash), so the golden in README.md is for the default value.
# Calibration 2026-09-23: rounds=4 measured 61.26s hostSeconds (over
# budget) / 11.05M simInsts -> rounds=3 = 46.46s / 8,298,076 simInsts.
LIBJPEG_ROUNDS ?= 3

# The exact archive member set of upstream's cmake-built libjpeg.a
# ("ar t", 117 members: 101 src objects incl. the per-precision
# src/wrapper/ variants + 16 NEON/simd objects).  This list IS the audit
# of what gets built — every vendored .c that the build consumes appears
# here (or as an #include of one of these), everything else in src/ is
# not built (dead tool sources vendored for tree completeness).
LIBJPEG_LIB_MEMBERS := \
    simd/arm/aarch64/jchuff-neon.c.o \
    simd/arm/aarch64/jsimdcpu.c.o \
    simd/arm/jccolor-neon.c.o \
    simd/arm/jcgray-neon.c.o \
    simd/arm/jcphuff-neon.c.o \
    simd/arm/jcsample-neon.c.o \
    simd/arm/jdcolor-neon.c.o \
    simd/arm/jdmerge-neon.c.o \
    simd/arm/jdsample-neon.c.o \
    simd/arm/jfdctfst-neon.c.o \
    simd/arm/jfdctint-neon.c.o \
    simd/arm/jidctfst-neon.c.o \
    simd/arm/jidctint-neon.c.o \
    simd/arm/jidctred-neon.c.o \
    simd/arm/jquanti-neon.c.o \
    simd/jsimd.c.o \
    src/jaricom.c.o \
    src/jcapimin.c.o \
    src/jcarith.c.o \
    src/jchuff.c.o \
    src/jcicc.c.o \
    src/jcinit.c.o \
    src/jclhuff.c.o \
    src/jcmarker.c.o \
    src/jcmaster.c.o \
    src/jcomapi.c.o \
    src/jcparam.c.o \
    src/jcphuff.c.o \
    src/jctrans.c.o \
    src/jdapimin.c.o \
    src/jdarith.c.o \
    src/jdatadst.c.o \
    src/jdatasrc.c.o \
    src/jdhuff.c.o \
    src/jdicc.c.o \
    src/jdinput.c.o \
    src/jdlhuff.c.o \
    src/jdmarker.c.o \
    src/jdmaster.c.o \
    src/jdphuff.c.o \
    src/jdtrans.c.o \
    src/jerror.c.o \
    src/jfdctflt.c.o \
    src/jmemmgr.c.o \
    src/jmemnobs.c.o \
    src/jpeg_nbits.c.o \
    src/wrapper/jcapistd-12.c.o \
    src/wrapper/jcapistd-16.c.o \
    src/wrapper/jcapistd-8.c.o \
    src/wrapper/jccoefct-12.c.o \
    src/wrapper/jccoefct-8.c.o \
    src/wrapper/jccolor-12.c.o \
    src/wrapper/jccolor-16.c.o \
    src/wrapper/jccolor-8.c.o \
    src/wrapper/jcdctmgr-12.c.o \
    src/wrapper/jcdctmgr-8.c.o \
    src/wrapper/jcdiffct-12.c.o \
    src/wrapper/jcdiffct-16.c.o \
    src/wrapper/jcdiffct-8.c.o \
    src/wrapper/jclossls-12.c.o \
    src/wrapper/jclossls-16.c.o \
    src/wrapper/jclossls-8.c.o \
    src/wrapper/jcmainct-12.c.o \
    src/wrapper/jcmainct-16.c.o \
    src/wrapper/jcmainct-8.c.o \
    src/wrapper/jcprepct-12.c.o \
    src/wrapper/jcprepct-16.c.o \
    src/wrapper/jcprepct-8.c.o \
    src/wrapper/jcsample-12.c.o \
    src/wrapper/jcsample-16.c.o \
    src/wrapper/jcsample-8.c.o \
    src/wrapper/jdapistd-12.c.o \
    src/wrapper/jdapistd-16.c.o \
    src/wrapper/jdapistd-8.c.o \
    src/wrapper/jdcoefct-12.c.o \
    src/wrapper/jdcoefct-8.c.o \
    src/wrapper/jdcolor-12.c.o \
    src/wrapper/jdcolor-16.c.o \
    src/wrapper/jdcolor-8.c.o \
    src/wrapper/jddctmgr-12.c.o \
    src/wrapper/jddctmgr-8.c.o \
    src/wrapper/jddiffct-12.c.o \
    src/wrapper/jddiffct-16.c.o \
    src/wrapper/jddiffct-8.c.o \
    src/wrapper/jdlossls-12.c.o \
    src/wrapper/jdlossls-16.c.o \
    src/wrapper/jdlossls-8.c.o \
    src/wrapper/jdmainct-12.c.o \
    src/wrapper/jdmainct-16.c.o \
    src/wrapper/jdmainct-8.c.o \
    src/wrapper/jdmerge-12.c.o \
    src/wrapper/jdmerge-8.c.o \
    src/wrapper/jdpostct-12.c.o \
    src/wrapper/jdpostct-16.c.o \
    src/wrapper/jdpostct-8.c.o \
    src/wrapper/jdsample-12.c.o \
    src/wrapper/jdsample-16.c.o \
    src/wrapper/jdsample-8.c.o \
    src/wrapper/jfdctfst-12.c.o \
    src/wrapper/jfdctfst-8.c.o \
    src/wrapper/jfdctint-12.c.o \
    src/wrapper/jfdctint-8.c.o \
    src/wrapper/jidctflt-12.c.o \
    src/wrapper/jidctflt-8.c.o \
    src/wrapper/jidctfst-12.c.o \
    src/wrapper/jidctfst-8.c.o \
    src/wrapper/jidctint-12.c.o \
    src/wrapper/jidctint-8.c.o \
    src/wrapper/jidctred-12.c.o \
    src/wrapper/jidctred-8.c.o \
    src/wrapper/jquant1-12.c.o \
    src/wrapper/jquant1-8.c.o \
    src/wrapper/jquant2-12.c.o \
    src/wrapper/jquant2-8.c.o \
    src/wrapper/jutils-12.c.o \
    src/wrapper/jutils-16.c.o \
    src/wrapper/jutils-8.c.o

LIBJPEG_LIB_OBJS := $(addprefix $(LIBJPEG_OBJ)/,$(LIBJPEG_LIB_MEMBERS))

$(LIBJPEG_AR): $(LIBJPEG_LIB_OBJS)
	rm -f $@
	ar rcs $@ $(LIBJPEG_LIB_OBJS)

# Pattern rules: library objects (-Icfg for jconfig.h/jconfigint.h/
# jversion.h) and NEON objects (+ -Icfg/simd/arm for neon-compat.h).
# Object paths mirror source paths so GNU ar stores unique basenames.
$(LIBJPEG_OBJ)/src/%.c.o: $(LIBJPEG_DIR)/src/%.c \
                          $(LIBJPEG_CFG)/jconfig.h \
                          $(LIBJPEG_CFG)/jconfigint.h \
                          $(LIBJPEG_CFG)/jversion.h
	@mkdir -p $(@D)
	$(CC) $(LIBJPEG_CFLAGS) -I$(LIBJPEG_CFG) -c $< -o $@

$(LIBJPEG_OBJ)/simd/%.c.o: $(LIBJPEG_DIR)/simd/%.c \
                           $(LIBJPEG_CFG)/jconfig.h \
                           $(LIBJPEG_CFG)/jconfigint.h \
                           $(LIBJPEG_CFG)/jversion.h \
                           $(LIBJPEG_CFG)/simd/arm/neon-compat.h
	@mkdir -p $(@D)
	$(CC) $(LIBJPEG_CFLAGS) -I$(LIBJPEG_CFG) -I$(LIBJPEG_CFG)/simd/arm -c $< -o $@

# The workload binary: static AArch64 ELF printing FINAL=<16hex>.
# The .rounds-N stamp is a PREREQUISITE (not a rule that builds the
# binary, cf. coremark's .iterations): changing LIBJPEG_ROUNDS names a
# different stamp file, which is newer than the binary and forces a
# relink.  The stamp is touched BEFORE the link so the binary ends up
# newer than its own stamp (make would otherwise rebuild every time);
# a failed link leaves the binary older, which correctly retries.
# NB: the recipe must stay explicit — a recipe-less target would let
# make's built-in "%: %.c" implicit rule recompile jpeg_wl.c without
# the -I flags (observed and fixed).
libjpeg: $(LIBJPEG_DIR)/jpeg_wl

$(LIBJPEG_DIR)/.rounds-%:
	touch $@

$(LIBJPEG_DIR)/jpeg_wl: $(LIBJPEG_DIR)/jpeg_wl.c \
                        $(LIBJPEG_DIR)/embedded_jpg.h \
                        $(LIBJPEG_AR) \
                        $(LIBJPEG_DIR)/.rounds-$(LIBJPEG_ROUNDS)
	rm -f $(LIBJPEG_DIR)/.rounds-*
	touch $(LIBJPEG_DIR)/.rounds-$(LIBJPEG_ROUNDS)
	$(CC) -O2 -static -Wall -Wextra \
	    -I$(LIBJPEG_DIR)/src -I$(LIBJPEG_DIR)/cfg \
	    -DDECODE_ROUNDS=$(LIBJPEG_ROUNDS) -o $(LIBJPEG_DIR)/jpeg_wl \
	    $(LIBJPEG_DIR)/jpeg_wl.c $(LIBJPEG_AR)

# Regenerate the embedded JPEG header (NOT part of the default build):
# gen_img.c -> PPM -> PPM-only cjpeg (vendored sources + our libjpeg.a)
# -> xxd -i.  The committed embedded_jpg.h was produced by exactly this
# rule; the chain is deterministic (verified: two regens byte-identical).
# NB: regen cjpeg is built with -DPPM_SUPPORTED only (upstream cjpeg
# builds all readers; PNG would need the not-vendored src/spng).
.PHONY: libjpeg-regen
libjpeg-regen: $(LIBJPEG_AR)
	$(CC) -O2 -Wall -Wextra -o $(LIBJPEG_OBJ)/gen_img $(LIBJPEG_DIR)/gen_img.c
	mkdir -p $(LIBJPEG_OBJ)/tools
	set -e; for f in cjpeg.c cdjpeg.c rdswitch.c \
	    wrapper/rdppm-8.c wrapper/rdppm-12.c wrapper/rdppm-16.c; do \
	    $(CC) $(LIBJPEG_CFLAGS) -DPPM_SUPPORTED -I$(LIBJPEG_CFG) \
	        -c $(LIBJPEG_DIR)/src/$$f \
	        -o $(LIBJPEG_OBJ)/tools/`basename $$f .c`.o; \
	done
	$(CC) -o $(LIBJPEG_OBJ)/cjpeg $(LIBJPEG_OBJ)/tools/*.o $(LIBJPEG_AR)
	$(LIBJPEG_OBJ)/gen_img > $(LIBJPEG_OBJ)/embedded.ppm
	$(LIBJPEG_OBJ)/cjpeg -quality 80 -dct int -sample 2x2 \
	    -outfile $(LIBJPEG_OBJ)/embedded.jpg $(LIBJPEG_OBJ)/embedded.ppm
	# xxd -i mangles the whole PATH into the variable name, so cd into the
	# build dir and use the bare filename (symbols: embedded_jpg, _len).
	cd $(LIBJPEG_OBJ) && xxd -i embedded.jpg > $(CURDIR)/$(LIBJPEG_DIR)/embedded_jpg.h.new
	cmp $(LIBJPEG_DIR)/embedded_jpg.h.new $(LIBJPEG_DIR)/embedded_jpg.h \
	    && rm -f $(LIBJPEG_DIR)/embedded_jpg.h.new \
	    && echo "libjpeg-regen: embedded_jpg.h unchanged (deterministic)" \
	    || { mv -f $(LIBJPEG_DIR)/embedded_jpg.h.new $(LIBJPEG_DIR)/embedded_jpg.h; \
	         echo "libjpeg-regen: embedded_jpg.h UPDATED — re-verify golden"; }
