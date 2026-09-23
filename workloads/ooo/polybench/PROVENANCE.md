# PROVENANCE — workloads/ooo/polybench (W1.3)

## Upstream

- **Suite**: PolyBench/C **4.2.1 beta** (stamped May 10, 2016), by
  Louis-Noël Pouchet / Tomofumi Yuki (Ohio State University).
- **Vendored from**: GitHub mirror
  `https://github.com/MatthiasJReisinger/PolyBenchC-4.2.1` at commit
  **3e872547cef7e5c9909422ef1e6af03cf4e56072** (2016-06-10, the repo's
  single commit: "Initial commit with PolyBench/C 4.2.1 beta sources").
- **Why a mirror**: the canonical distribution points are dead from this
  host — netlib `polybench-c` path 404 (already recorded in the W1 plan),
  the Ohio State download URL redirects to a generic CSE directory page,
  SourceForge project 404. The plan's first candidate
  (`cavazos-lab/PolyBench` @ `70ea4ca9`, probed alive) turned out to be
  the *GPU-variants* suite (CUDA/OpenCL/OpenACC/OpenMP/HMPP kernels with
  a shared `common/`), not plain PolyBench/C, so it was not used.
- **Cross-validation of mirror fidelity**: `utilities/polybench.c`,
  `utilities/polybench.h` and all four kernel `.h` files are
  **byte-identical** to the copies inside
  `llvm/llvm-test-suite@4eee8855ad0dcf5683cb11822314401ea7ea1617`
  (`SingleSource/Benchmarks/Polybench`, also self-described 4.2.1 beta).
  The LLVM copy's kernel `.c` files carry LLVM-specific adaptations
  (`*_StrictFP` recompute + `check_FP` epsilon compare, `FMA_DISABLED`,
  `print_element` stderr dump) which are **absent** from the vendored
  pristine sources; the pristine text was preferred.
- **Files kept** (12, no `.git`; upstream `LICENSE.txt` and `README`
  verbatim): `LICENSE.txt`, `README`,
  `utilities/{polybench.c,polybench.h}`,
  `linear-algebra/blas/gemm/{gemm.c,gemm.h}`,
  `linear-algebra/solvers/lu/{lu.c,lu.h}`,
  `linear-algebra/solvers/cholesky/{cholesky.c,cholesky.h}`,
  `stencils/jacobi-2d/{jacobi-2d.c,jacobi-2d.h}`.

## Local deviations from upstream (all marked `/* gem5-fi W1.3 */`)

1. Each of the four kernel `.c` files gets exactly one
   `#include <stdint.h>` line and one FINAL block at the end of `main()`
   (between the `polybench_prevent_dce` reference and
   `POLYBENCH_FREE_ARRAY`), printing `FINAL=<16hex>` — an FNV-1a 64-bit
   hash over the live-out output array bytes, pattern copied from the
   W1.2 embench hunks. Hash domain = exactly what upstream
   `print_array` dumps: full `C` (ni×nj) for gemm, full `A` (n×n) for
   lu and jacobi-2d, lower triangle incl. diagonal (j<=i) for cholesky
   (its kernel only writes the lower triangle; the upper one is dead
   after init). Heap rows are contiguous because
   `POLYBENCH_PADDING_FACTOR` defaults to 0. Kernel/benchmark logic is
   untouched.
2. Nothing else. All other files are byte-identical to the upstream
   commit (verify with `diff -r` against the mirror).

## Determinism (prerequisite for native == gem5)

- No `rand()`/`srand()` anywhere in the vendored tree (grep-verified);
  all four `init_array` implementations use fixed integer formulas
  (`(i*j+1) % ni / ni`, `-j % n / n + 1`, PSD product `A*A^T`, …).
- No `gettimeofday`/`clock_gettime` in the build: without
  `-DPOLYBENCH_TIME`/`-DPOLYBENCH_GFLOPS`, `polybench.h`'s
  `polybench_start_instruments` / `polybench_stop_instruments` /
  `polybench_print_instruments` macros expand to **nothing**
  (`rtclock()` returns 0 without ever calling gettimeofday), so no
  timing is read and the 32 MB cache-flush `calloc` never runs.
- `print_array` (the DCE guard) sits behind upstream's
  `if (argc > 40 && ! strcmp(argv[0], ""))` and never executes in the
  SE runner (no args). The SE binary is pure deterministic compute plus
  the FINAL line.
- All FP ops are IEEE-754 exact-rounding (fmul/fmadd/fadd/fdiv/fsqrt);
  gem5 SE fplib has been proven bit-exact vs hardware on this platform
  for fp64 mul/div/add/sqrt and fp32 fused-multiply-add
  (workloads/ooo W1.5b/W1.5c/W1.2), so native == gem5 is expected and
  is verified per binary in the W1.3 record.

## Build knobs (documented upstream interfaces, zero source edits)

- `-DDATA_TYPE_IS_FLOAT` — fp32 (03-workloads.md assigns PolyBench to
  FP/SIMD unit coverage; also the W1.2 flFloatMin cross-check load).
- Sizes via `-DNI/-DNJ/-DNK`, `-DN`, `-DTSTEPS`+`-DN`: the headers'
  `#if !defined(...)` guards skip the default dataset block when the
  size macros are predefined on the command line (all of a kernel's
  size macros must be defined together). This replaces the upstream
  LARGE_DATASET defaults (gemm 1000×1100×1200 etc.) **without editing
  the vendored .h files**; the task brief's "调小尺寸参数" is realized
  through these compile-time overrides. Calibrated defaults in the
  Makefile: gemm 88³, lu 84, cholesky 88, jacobi-2d T=8/N=160.
- `-lm` (upstream `c.mk` links it too).

## Upstream warning classes suppressed (`POLYBENCH_NOWARN`)

Sources are kept verbatim, so three upstream code-quality warning
classes are suppressed at compile time (any NEW warning class still
fails the build; rationale per class):

1. `-Wno-unknown-pragmas` — `#pragma scop` / `#pragma endscop` are
   polyhedral-compiler region markers (PoCC/Pluto/etc.); gcc is not
   such a compiler and ignoring them is the intended fallback.
2. `-Wno-unused-variable` — `polybench.c`'s static
   `_polybench_alloc_table` is only used under
   `POLYBENCH_ENABLE_INTARRAY_PAD` (off by default).
3. `-Wno-misleading-indentation` — lu.c/cholesky.c `init_array`'s PSD
   block: the `for (r…)` copy loop is indented as if nested inside the
   `t` loop but actually runs after it (C semantics: the `t`-loop body
   is only the two inner loops). The misindentation is upstream text;
   the executed semantics (accumulate B fully, then copy B into A once)
   is the intended one — a fault-injection-relevant detail we verified
   by reading the code, not by "fixing" it.

## Golden / oracle usage

The no-injection `FINAL=<16hex>` value of each binary (at the
calibrated sizes above) is the golden (registered in `tools/runner.py`
GOLDEN_IDS as `polybenchgemm-golden-v1` etc.). FINAL is
size-dependent — a different `-D` size computes a different array — so
the Makefile's size variables and the golden values must be changed
together.
