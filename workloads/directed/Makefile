# workloads/directed/Makefile — W6 artifact components
#
# Reproducible native builds (run as: make -C workloads/directed w6):
#   svd_iterative_kernel   existing iterative SVD (+ W6 element dump)
#   fft_radix2_kernel      fixed-input N=1024 radix-2 FFT
#   sparse_cg_kernel       fixed SPD 16x16 five-point Laplacian, CG solve
#
# The shared element-dump helper is the PolyBench W5 header; no copy is
# made here (one implementation on disk).
CC ?= gcc
CFLAGS ?= -O2 -static -Wall -Wextra
CPPFLAGS += -I../ooo/polybench/utilities
LDLIBS += -lm

W6_BINS := svd_iterative_kernel fft_radix2_kernel sparse_cg_kernel
ORACLE_HDR := ../ooo/polybench/utilities/gem5fi_oracle.h

.PHONY: all w6 clean
all: w6
w6: $(W6_BINS)

$(W6_BINS): %: %.c $(ORACLE_HDR)
	$(CC) $(CFLAGS) $(CPPFLAGS) -o $@ $< $(LDLIBS)

clean:
	rm -f $(W6_BINS)
