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
WORKLOADS := smoke

.PHONY: all clean $(WORKLOADS)

all: $(WORKLOADS)

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

clean:
	rm -f $(foreach w,$(WORKLOADS),$(w)/$(w))
