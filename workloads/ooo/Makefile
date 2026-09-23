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
WORKLOADS := smoke branch_mispred dep_chain rob_fill

.PHONY: all clean $(WORKLOADS) dep_chain_vec rob_fill_fp coremark

all: $(WORKLOADS) dep_chain_vec rob_fill_fp coremark

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

clean:
	rm -f $(foreach w,$(WORKLOADS),$(w)/$(w)) dep_chain/dep_chain_vec rob_fill/rob_fill_fp coremark/coremark coremark/.iterations-*
	$(MAKE) -C coremark PORT_DIR=posix clean || true
