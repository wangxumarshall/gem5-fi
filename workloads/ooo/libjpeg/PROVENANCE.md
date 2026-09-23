# libjpeg workload — PROVENANCE (W1.4b)

Read this first: upstream identity, vendored inventory, build-recipe
provenance, the embedded-JPEG pipeline, and every honest deviation from
both upstream and the W1 task brief.

## Upstream identity

- Repository: https://github.com/libjpeg-turbo/libjpeg-turbo
- Commit: `2a8bd381b42664e72cfc0f652db6caf4c9e98117`
  (2026-09-22 11:33:51 -0400, "TJDecomp: Claim ICC profile extraction
  support" — master HEAD at vendoring time)
- Version: 3.2.1 (CMakeLists.txt `set(VERSION 3.2.1)`)
- LICENSE.md (upstream, IJG-style BSD-like) kept verbatim at
  `libjpeg/LICENSE.md`. No `.git` directory is vendored.
- Upstream self-validation at this commit on this host: `ctest` **332/332
  passed** (aarch64 NEON build; includes the official SIMD-vs-reference
  md5 comparison tests).

## What is vendored (255 files, ~3.7 MB)

| Path | Content | Why |
|---|---|---|
| `src/` | complete upstream `src/` minus `src/md5/` and `src/spng/` | tree completeness; the build consumes only the audited subset below |
| `simd/*.c`, `simd/*.h` | upstream simd top level (`jsimd.c` dispatcher + headers) | library NEON dispatch |
| `simd/arm/` | complete (both `aarch64/` and `aarch32/` subtrees) | NEON kernels; `simd/common/`, `i386/`, `x86_64/`, `mips64/`, `powerpc/`, `riscv64/`, `nasm/` are NOT vendored |
| `cfg/` | 4 **cmake-generated** headers, byte-identical copies from a real cmake configure of the same commit | see "Build recipe" |
| `LICENSE.md` | upstream license, verbatim | legal |
| `gen_img.c`, `jpeg_wl.c`, `embedded_jpg.h`, `libjpeg.mk`, `PROVENANCE.md` | gem5-fi files (this workload) | — |

Excluded top-level upstream dirs: `cmakescripts/ doc/ fuzz/ jna/ release/
sharedlib/ test/ testimages/ win/ CMakeLists.txt` (build tooling/docs,
not needed by the vendored recipe).

## Build recipe (hand-rolled, NOT cmake)

The upstream build requires cmake to generate `jconfig.h`,
`jconfigint.h`, `jversion.h` and `simd/arm/neon-compat.h` (from
`*.in` templates) — a plain `gcc` build of the raw sources is not
possible (verified: `jerror.c` fails on a missing `jversion.h`). The
task brief's cmake-blocker contingency therefore did not trigger
(host has cmake 3.27.9), but the in-repo build is nonetheless a
**hand-rolled transcription of the upstream cmake build**, so the W1
framework stays plain-make:

1. A reference cmake build of the same commit was configured on this
   host (`-G "Unix Makefiles"`, `CMAKE_BUILD_TYPE=Release`,
   `ENABLE_SHARED=0`; aarch64 auto-detected `WITH_SIMD=1`, no nasm
   needed — aarch64 NEON kernels are C intrinsics).
2. The generated headers were copied verbatim into `cfg/`.
3. Per-object compile flags were read out of the cmake-generated
   `flags.make`/`build.make` and transcribed into `libjpeg.mk`:
   `-Wall -Wextra -O3 -DNDEBUG` (upstream's Release policy replaces
   cmake's default `-O2` with `-O3`), `-Icfg` for library objects,
   plus `-Icfg/simd/arm` for NEON objects (for `neon-compat.h`).
   There are no other flags, defines or include paths (verified by
   reading every `flags.make`).
4. **Recipe verification**: the object set produced by the
   hand-rolled rules is member-for-member identical (117/117, `ar t`
   diff empty) to the reference cmake `libjpeg.a`: 101 `src/` objects
   (including the per-precision `src/wrapper/` variants) + 16 simd
   objects. `LIBJPEG_LIB_MEMBERS` in `libjpeg.mk` is that exact list
   and doubles as the build audit.

The generated headers in `cfg/` encode this host's configure results
(BITS_IN_JSAMPLE default 8, `WITH_SIMD 1`, `VERSION 3.2.1`, etc.).
They are stable for the vendored commit; if the commit is ever
bumped, regenerate them with a fresh cmake configure (or run
`libjpeg-regen`'s documented procedure) instead of hand-editing.

## The embedded JPEG (deterministic regeneration)

`embedded_jpg.h` (23,980-byte JPEG as a C array) was produced by the
`libjpeg-regen` make target, which chains:

1. `gen_img.c` (gem5-fi, pure integer math + fixed-seed LCG) writes a
   256x256 RGB **PPM** — byte-identical on any host/toolchain.
2. A **PPM-only cjpeg** built from the vendored sources (same
   `libjpeg.a`) compresses it with fixed switches:
   `-quality 80 -dct int -sample 2x2`.
3. `xxd -i embedded.jpg` emits the header.

Determinism verified: two full regenerations produced byte-identical
PPM and JPEG (`cmp` clean; JPEG md5
`49e44ba3f90d979acef5437f8f3dff39`). Re-running `libjpeg-regen` after
landing prints "unchanged (deterministic)".

## Honest deviations

1. **From the task brief**: the brief sketched "a PGM"; the workload
   uses a color **PPM** instead. A grayscale PGM would encode to a
   single-component JPEG whose decode skips the YCbCr->RGB conversion
   and chroma upsampling NEON kernels — the very code the north star
   assigns to this workload (FP/SIMD rename, vector register file
   pressure). Deviation is in the letter only; the intent
   (program-generated deterministic image, compressed once by the
   vendored cjpeg, embedded in the binary) is preserved exactly.
2. **From upstream cjpeg**: the regen-time cjpeg is built with
   `-DPPM_SUPPORTED` only (upstream builds BMP/GIF/PNG/PPM/Targa
   readers; PNG needs the non-vendored `src/spng`). The switches
   actually used exercise only the PPM reader.
3. **No source modifications at all**: every vendored `.c`/`.h` is
   byte-identical to the upstream commit (the `cfg/` headers are
   copies of *generated* files, not source edits). The gem5-fi surface
   is exactly two new files, `gen_img.c` and `jpeg_wl.c` (the
   `/* gem5-fi W1.4b */` FINAL line lives in `jpeg_wl.c` only).
4. **Warning suppressions (upstream code quality, documented)**:
   building the vendored sources with `-Wall -Wextra` yields 287
   warnings in 2 classes — 285x `-Wunused-parameter` (libjpeg
   method callbacks with API-fixed signatures whose specific methods
   legitimately ignore parameters, e.g. `jccolor.c null_method`) and
   2x `-Wsign-compare` (`jdphuff.c` `HUFF_EXTEND` macro, "operand of
   ?: changes signedness"). Both are suppressed via
   `-Wno-unused-parameter -Wno-sign-compare`; residual warning count
   is zero. Any NEW warning class still fails the build. (Same policy
   as embench/polybench in this framework.)
5. **12-bit/16-bit precision wrappers and arithmetic coding are
   compiled in** (they are part of the audited 117-object archive
   member set copied from upstream's default static library) but the
   embedded JPEG exercises only the 8-bit baseline Huffman path.
   This mirrors what a system libjpeg-turbo static archive contains.

## SE/runtime properties (measured)

- No runtime file I/O in the workload path: the JPEG is compiled in
  and decoded via `jpeg_mem_src` (`MEM_SRCDST_SUPPORTED` is
  unconditionally defined upstream). Backing store is `jmemnobs`
  (plain malloc/free). `grep` over the linked objects finds no
  `getenv`-at-runtime / `fopen` / `getauxval` / HWCAP paths: NEON is
  enabled unconditionally by `simd/arm/aarch64/jsimdcpu.c`
  (`return JSIMD_NEON` — "Armv8 architectures support Neon by
  default"), which also makes the SIMD path gem5-SE-safe (no auxv).
- SIMD activity evidence (C3 O3 run, rounds=4 calibration run):
  committed instruction mix contains SimdAdd 527,724 / SimdAlu
  564,880 / SimdMult 357,484 / SimdMultAcc 362,256 / SimdAddAcc
  163,840 / SimdShift 429,173 / SimdMisc 125,758 — 2.53M SIMD
  instructions = 21.3% of 11.86M commits; `rename.vecLookups` =
  6,147,886 (0.56x simInsts) vs ~182 for a no-vector workload (the
  W1.5b int-kernel baseline measured the CRT-only floor).
- Oracle: all rounds' decoded pixels fold into ONE running FNV-1a-64
  state (word-wise fold; see `jpeg_wl.c` header comment for the
  rationale — a byte-serial fold would rival the decode itself in
  instruction count). The round index is folded in ahead of each
  round's pixels.
