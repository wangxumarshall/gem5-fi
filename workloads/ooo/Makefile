# workloads/ooo/Makefile — W1.0 OoO north-star workload build framework.
#
# Conventions (mirrors workloads/directed/: source + static ELF both kept
# in-repo):
#   * each workload <name> lives in <name>/<name>.c
#   * it builds to <name>/<name> — a static AArch64 ELF (host gcc, native
#     aarch64; no cross toolchain needed)
#   * the kernel prints a FINAL=<16hex> checksum line (tools/classify.py
#     _CHECKSUM_RE); the no-injection value (native == gem5) is the golden
#
# SE budget discipline (W1 plan Global Constraints, hard gate): every
# workload must fit gem5 SE (configs/se/ooo_proxy.py --cpu O3) within
# 60s stats.txt hostSeconds; measured values are recorded in README.md as
# each workload lands.
#
# Usage:
#   make -C workloads/ooo            # build all landed workloads
#   make -C workloads/ooo smoke      # build one workload
#   make -C workloads/ooo clean

CC      := gcc
CFLAGS  := -O2 -static -Wall -Wextra
LDFLAGS :=

# Landed workloads — append <name> here when its task completes:
#   smoke          W1.0  framework smoke kernel                  (Task 1)
#   branch_mispred W1.5a branch-mispred-dense probe              (Task 2)
#   dep_chain      W1.5b long dependency chain, int + vec        (Task 3)
#   rob_fill       W1.5c ROB-fill, int + fp                      (Task 4)
#   coremark       W1.1  EEMBC CoreMark posix port               (Task 5)
#   embench        W1.2  Embench-Io int+fp subset                (Task 6)
#   polybench      W1.3  PolyBench gemm/lu/cholesky/jacobi-2d    (Task 7)
#   gap, libjpeg   W1.4  GAP semantic proxy + libjpeg-turbo      (Task 8)
WORKLOADS := smoke branch_mispred dep_chain rob_fill gap

.PHONY: all clean $(WORKLOADS) dep_chain_vec rob_fill_fp coremark embench polybench

all: $(WORKLOADS) dep_chain_vec rob_fill_fp coremark embench polybench

# Per-workload pattern, instantiated once per name above: a phony alias
# target <name> plus the real rule <name>/<name> <- <name>/<name>.c.
# Workloads with richer source dirs (coremark/embench/polybench/...) add
# explicit rules below instead of extending WORKLOADS when they land.
define WORKLOAD_template
$(1): $(1)/$(1)
$(1)/$(1): $(1)/$(1).c
	$$(CC) $$(CFLAGS) $$(LDFLAGS) -o $$@ $$<
endef

$(foreach w,$(WORKLOADS),$(eval $(call WORKLOAD_template,$(w))))

# W1.5b dep_chain: the int binary comes from the pattern rule above
# (dep_chain/dep_chain <- dep_chain/dep_chain.c).  The NEON vec variant
# shares the directory but has its own name -> explicit rule here.
dep_chain_vec: dep_chain/dep_chain_vec
dep_chain/dep_chain_vec: dep_chain/dep_chain_vec.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $<

# W1.5c rob_fill: the int binary comes from the pattern rule above
# (rob_fill/rob_fill <- rob_fill/rob_fill.c).  The fp variant shares the
# directory but has its own name -> explicit rule here.
rob_fill_fp: rob_fill/rob_fill_fp
rob_fill/rob_fill_fp: rob_fill/rob_fill_fp.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $<

# W1.1 coremark — EEMBC CoreMark (posix port).
#
# PROVENANCE: vendored subset of https://github.com/eembc/coremark @
#   1f483d5b8316753a742cbf5590caf5bd0a4e4777 (2025-05-01, "Merge pull
#   request #55 from DeflateAwning/main - Fix typo (fixes #52)")
# Files kept: core_{list_join,main,matrix,state,util}.c coremark.h
#   posix/{core_portme.c,core_portme.h,core_portme.mak,
#   core_portme_posix_overrides.h} LICENSE.md Makefile README.md coremark.md5
#   (upstream Apache-2.0 LICENSE.md kept verbatim; no .git). NB: at this HEAD
#   upstream's port dirs are top-level (posix/), not the pre-2019 cores/.
#   Upstream coremark.md5 is STALE at this commit for coremark.h (pristine
#   git blob b0ec69b6... != manifest 8ca974c0...); git content is authoritative.
# ONLY local source deviation: coremark/core_main.c carries one gem5-fi hunk
#   printing the FINAL=<16hex> oracle line (see the "gem5-fi W1.1" comment
#   there); every other file is byte-identical to upstream.
#
# Build: delegating to the VENDORED UPSTREAM Makefile (chosen over listing
# sources by hand because it keeps upstream's flag plumbing intact — FLAGS_STR
# shell quoting, -Iposix includes, vpath). Our knobs ride the documented
# upstream hooks XCFLAGS / ITERATIONS:
#   -DSEED_METHOD=SEED_VOLATILE : posix default SEED_ARG reads seeds from
#       argv; our SE runner passes NO args (set_se_binary_workload), and a
#       no-arg SEED_ARG run calibrates iterations from a 1-second probe loop
#       that never converges under gem5 SE (clock_gettime returns simulated
#       time). SEED_VOLATILE is the upstream-sanctioned compile-time seed
#       path (core_portme.h #ifndef-guarded, zero file edits) and makes
#       -DITERATIONS live (feeds seed4_volatile).
#   -DPERFORMANCE_RUN=1 : canonical CoreMark performance seeds 0x0/0x0/0x66
#       (seedcrc 0xe9f5, known_id=3 "2K performance run" — self-check active).
#   ITERATIONS : calibration knob for the C3 SE <=60s hostSeconds budget.
# ITERATIONS calibrated 2026-09-23 for the C3 SE budget (W1 Global
# Constraints): 20 iters measured 30.67 s hostSeconds / 6190128 simInsts
# (~310k insts/iter, ~202 KIPS) -> 35 iters lands ~10.8M insts / ~53 s,
# inside the 30-60 s / 10-15M target window. (The task brief's "start from
# ITERATIONS=2000" overshot ~50x: 2000 iters ~ 620M insts ~ 35+ min.)
COREMARK_ITERATIONS ?= 35
coremark: coremark/coremark
coremark/coremark: coremark/.iterations-$(COREMARK_ITERATIONS)
# Stamp rule: rebuilds whenever sources change OR the requested ITERATIONS
# differs from the last build (stale stamps are removed first, so flipping
# COREMARK_ITERATIONS re-triggers the sub-make — upstream's own Makefile
# cannot see -DITERATIONS changes by itself).
coremark/.iterations-%: $(wildcard coremark/*.c coremark/*.h) \
                        $(wildcard coremark/posix/*) coremark/Makefile
	rm -f coremark/.iterations-*
	$(MAKE) -C coremark PORT_DIR=posix CC=$(CC) \
	    ITERATIONS=$* \
	    XCFLAGS="-static -Wall -Wextra -DSEED_METHOD=SEED_VOLATILE -DPERFORMANCE_RUN=1" \
	    load
	mv -f coremark/coremark.exe coremark/coremark
	touch $@

# W1.2 embench — Embench-IoT int+fp subset.  PROVENANCE (both vendored
# commits, the Embench-2.0 fp-benchmark removal that forced the
# qlsort/qrsolve/nbody substitutions, per-file source commit, the gem5-fi
# FINAL hunks and the -Wno-* rationale) is recorded in
# embench/PROVENANCE.md — read it first.
#
# Build = upstream's per-benchmark recipe (cf. sconstruct.py
# build_support_objects): <benchmark>.c + support/main.c + support/beebsc.c
# + boardsupport.c (vendored from examples/native/speed), -I support.
# HEAD-era benchmarks scale iterations as LOCAL_SCALE_FACTOR x
# GLOBAL_SCALE_FACTOR (two nested loops); the pre-2.0 fp benchmarks
# (nbody/minver) scale as LOCAL_SCALE_FACTOR x CPU_MHZ (their 1.0-era
# convention, removed from master at 09c2ed8c).
#
# EMBENCH_NOWARN: upstream sources are not -Wall -Wextra clean — dead
# locals (-Wunused-variable, -Wunused-but-set-variable), unused
# test-generator parameters (-Wunused-parameter), one provably-false
# -Wmaybe-uninitialized (crc32 r: the scale factors are compile-time >= 1
# so the loop always executes) and beebsc.h's float_eq_beebs macro called
# with a double constant (-Wabsolute-value, minver).  Sources are kept
# verbatim (only the /* gem5-fi W1.2 */ FINAL hunks differ from upstream);
# these five upstream code-quality classes are suppressed instead,
# documented in embench/PROVENANCE.md.  Any NEW warning class still fails
# the build.
EMBENCH_NOWARN := -Wno-unused-variable -Wno-unused-parameter \
                  -Wno-unused-but-set-variable -Wno-maybe-uninitialized \
                  -Wno-absolute-value
EMBENCH_SUPPORT := embench/support/main.c embench/support/beebsc.c \
                   embench/boardsupport.c
EMBENCH_INC := -I embench/support -I embench

# Scale factors calibrated 2026-09-23 for the C3 SE <=60 s hostSeconds
# budget (W1 Global Constraints); scale-1 measurements in
# workloads/ooo/README.md (W1.2 record).  FINAL is scale-invariant (every
# iteration recomputes the identical checked state), so re-calibrating
# these does NOT change the golden values.
EMBENCH_CRC32_GSF    ?= 3     # 170 x 3 iters -> ~9.0M insts
EMBENCH_MD5SUM_GSF   ?= 5     # 66 x 5 iters  -> ~12.2M insts
EMBENCH_MATMULT_GSF  ?= 3     # 39 x 3 iters  -> ~6.4M insts
EMBENCH_WIKISORT_GSF ?= 5     # 2 x 5 iters   -> ~7.1M insts
EMBENCH_NBODY_MHZ    ?= 120   # 1 x 120 reps  -> ~8.4M insts
EMBENCH_MINVER_MHZ   ?= 20    # 555 x 20 reps -> ~9.4M insts

EMBENCH_BINS := embench/crc32/crc32 embench/md5sum/md5sum \
                embench/matmult-int/matmult-int embench/wikisort/wikisort \
                embench/nbody/nbody embench/minver/minver
embench: $(EMBENCH_BINS)

embench/crc32/crc32: embench/crc32/crc_32.c $(EMBENCH_SUPPORT)
	$(CC) $(CFLAGS) $(EMBENCH_NOWARN) -DWARMUP_HEAT=1 \
	    -DGLOBAL_SCALE_FACTOR=$(EMBENCH_CRC32_GSF) $(EMBENCH_INC) \
	    -o $@ embench/crc32/crc_32.c $(EMBENCH_SUPPORT) -lm

embench/md5sum/md5sum: embench/md5sum/md5.c $(EMBENCH_SUPPORT)
	$(CC) $(CFLAGS) $(EMBENCH_NOWARN) -DWARMUP_HEAT=1 \
	    -DGLOBAL_SCALE_FACTOR=$(EMBENCH_MD5SUM_GSF) $(EMBENCH_INC) \
	    -o $@ embench/md5sum/md5.c $(EMBENCH_SUPPORT) -lm

embench/matmult-int/matmult-int: embench/matmult-int/matmult-int.c \
                                 $(EMBENCH_SUPPORT)
	$(CC) $(CFLAGS) $(EMBENCH_NOWARN) -DWARMUP_HEAT=1 \
	    -DGLOBAL_SCALE_FACTOR=$(EMBENCH_MATMULT_GSF) $(EMBENCH_INC) \
	    -o $@ embench/matmult-int/matmult-int.c $(EMBENCH_SUPPORT) -lm

embench/wikisort/wikisort: embench/wikisort/libwikisort.c $(EMBENCH_SUPPORT)
	$(CC) $(CFLAGS) $(EMBENCH_NOWARN) -DWARMUP_HEAT=1 \
	    -DGLOBAL_SCALE_FACTOR=$(EMBENCH_WIKISORT_GSF) $(EMBENCH_INC) \
	    -o $@ embench/wikisort/libwikisort.c $(EMBENCH_SUPPORT) -lm

embench/nbody/nbody: embench/nbody/nbody.c $(EMBENCH_SUPPORT)
	$(CC) $(CFLAGS) $(EMBENCH_NOWARN) -DWARMUP_HEAT=1 \
	    -DCPU_MHZ=$(EMBENCH_NBODY_MHZ) $(EMBENCH_INC) \
	    -o $@ embench/nbody/nbody.c $(EMBENCH_SUPPORT) -lm

embench/minver/minver: embench/minver/libminver.c $(EMBENCH_SUPPORT)
	$(CC) $(CFLAGS) $(EMBENCH_NOWARN) -DWARMUP_HEAT=1 \
	    -DCPU_MHZ=$(EMBENCH_MINVER_MHZ) $(EMBENCH_INC) \
	    -o $@ embench/minver/libminver.c $(EMBENCH_SUPPORT) -lm

# W1.3 polybench — PolyBench/C 4.2.1 subset (gemm/lu/cholesky/jacobi-2d).
# PROVENANCE (upstream repo/commit, cross-validation, the gem5-fi FINAL
# hunks and the -Wno-* rationale) is recorded in polybench/PROVENANCE.md
# — read it first.
#
# Build = upstream's own documented compile-time knobs only (polybench
# README "How to tune PolyBench"): zero source edits for sizes/types.
#   -DDATA_TYPE_IS_FLOAT : fp32 data (03-workloads.md assigns PolyBench
#       to FP/SIMD unit coverage; also the flFloatMin cross-check load).
#   -DNI/-DNJ/-DNK, -DN, -DTSTEPS+-DN : size knobs.  The kernel headers'
#       '#if !defined(...)' guards make -D on the command line override
#       the default dataset block entirely (all of a kernel's size
#       macros must be defined together), so the upstream LARGE_DATASET
#       defaults (e.g. gemm 1000x1100x1200, ~700x over budget) are
#       replaced without touching the vendored .h files.
#   No -DPOLYBENCH_TIME / -DPOLYBENCH_GFLOPS: polybench.h's
#   start/stop/print_instruments macros stay EMPTY (no gettimeofday —
#   gem5 SE returns simulated time), no 32MB cache-flush calloc, and
#   print_array stays behind the upstream 'argc > 40' DCE guard: the SE
#   binary is pure deterministic compute + the FINAL line.
#
# Size calibration 2026-09-23 for the C3 SE <=60 s hostSeconds budget
# (W1 Global Constraints): FP-heavy kernels simulate at ~125 KIPS on
# this host (vs ~200 KIPS for the int workloads), so the target window
# is ~6.0-7.0M simInsts.  First candidates (gemm 96^3 / lu 92 / cholesky
# 100 / jacobi T10 N160) measured 62-76 s -> rescaled below.  FINAL is
# size-dependent (a different problem computes different data); the
# golden values recorded in README.md are for these exact sizes.
POLYBENCH_NOWARN := -Wno-unknown-pragmas -Wno-unused-variable \
                    -Wno-misleading-indentation
POLYBENCH_INC := -I polybench/utilities
# polybench.c is a compile input; polybench.h rides along via -I and is
# a make prerequisite only (passing a .h on the gcc command line would
# make gcc try to precompile it).
POLYBENCH_UTIL_SRC := polybench/utilities/polybench.c
POLYBENCH_UTIL_DEP := polybench/utilities/polybench.h

POLYBENCH_GEMM_N  ?= 88     # NI=NJ=NK; 88^3  -> ~6.5M insts / ~50 s
POLYBENCH_LU_N    ?= 84     # N=84          -> ~6.6M insts / ~51 s
POLYBENCH_CHO_N   ?= 88     # N=88          -> ~6.5M insts / ~51 s
POLYBENCH_JAC_T   ?= 8      # TSTEPS=8
POLYBENCH_JAC_N   ?= 160    # N=160         -> ~6.4M insts / ~50 s

POLYBENCH_BINS := polybench/gemm/gemm polybench/lu/lu \
                  polybench/cholesky/cholesky polybench/jacobi-2d/jacobi-2d
polybench: $(POLYBENCH_BINS)

# Binaries land in flat polybench/<kernel>/ dirs (short runner paths);
# they are not next to the sources, so create the dir first.
define POLYBENCH_COMPILE
@mkdir -p $(@D)
$(CC) $(CFLAGS) $(POLYBENCH_NOWARN) -DDATA_TYPE_IS_FLOAT $(POLYBENCH_INC) \
    -o $@ $< $(POLYBENCH_UTIL_SRC) -lm
endef

polybench/gemm/gemm: polybench/linear-algebra/blas/gemm/gemm.c \
                     polybench/linear-algebra/blas/gemm/gemm.h $(POLYBENCH_UTIL_SRC) $(POLYBENCH_UTIL_DEP)
	$(POLYBENCH_COMPILE) -DNI=$(POLYBENCH_GEMM_N) -DNJ=$(POLYBENCH_GEMM_N) -DNK=$(POLYBENCH_GEMM_N)

polybench/lu/lu: polybench/linear-algebra/solvers/lu/lu.c \
                 polybench/linear-algebra/solvers/lu/lu.h $(POLYBENCH_UTIL_SRC) $(POLYBENCH_UTIL_DEP)
	$(POLYBENCH_COMPILE) -DN=$(POLYBENCH_LU_N)

polybench/cholesky/cholesky: polybench/linear-algebra/solvers/cholesky/cholesky.c \
                             polybench/linear-algebra/solvers/cholesky/cholesky.h $(POLYBENCH_UTIL_SRC) $(POLYBENCH_UTIL_DEP)
	$(POLYBENCH_COMPILE) -DN=$(POLYBENCH_CHO_N)

polybench/jacobi-2d/jacobi-2d: polybench/stencils/jacobi-2d/jacobi-2d.c \
                               polybench/stencils/jacobi-2d/jacobi-2d.h $(POLYBENCH_UTIL_SRC) $(POLYBENCH_UTIL_DEP)
	$(POLYBENCH_COMPILE) -DTSTEPS=$(POLYBENCH_JAC_T) -DN=$(POLYBENCH_JAC_N)

clean:
	rm -f $(foreach w,$(WORKLOADS),$(w)/$(w)) dep_chain/dep_chain_vec rob_fill/rob_fill_fp coremark/coremark coremark/.iterations-*
	$(MAKE) -C coremark PORT_DIR=posix clean || true
	rm -f $(EMBENCH_BINS)
	rm -f $(POLYBENCH_BINS)
