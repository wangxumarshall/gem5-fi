# PROVENANCE — workloads/ooo/embench (W1.2)

Upstream: https://github.com/embench/embench-iot (Embench-IoT).

Two upstream commits are vendored here (reason below):

- **HEAD** `09c2ed8c3b7008c95d08b038de4a3f6dc103ed70`
  (I-mikan-I, 2024-08-29, "Remove CPU_MHZ references") — the current
  master. `git log -1` verbatim:

      commit 09c2ed8c3b7008c95d08b038de4a3f6dc103ed70
      Author: I-mikan-I <67881102+I-mikan-I@users.noreply.github.com>
      Date:   Thu Aug 29 12:25:16 2024 +0200

          Remove CPU_MHZ references

- **pre-2.0** `92da124bb8da825b2937abaaed2aca9bb9e50fc9`
  (I-mikan-I, 2024-03-08, "Remove legacy build script") — the last
  commit from which the floating-point benchmarks are taken. `git log -1`
  verbatim:

      commit 92da124bb8da825b2937abaaed2aca9bb9e50fc9
      Author: I-mikan-I <67881102+I-mikan-I@users.noreply.github.com>
      Date:   Fri Mar 8 11:29:22 2024 +0100

          Remove legacy build script

## Why two commits (honest deviation note)

The W1 plan brief named 6 programs: int crc32 / md5sum / qlsort /
matmult-int, fp nbody / qrsolve. Verified facts against the full
(unshallowed) upstream history:

- **qlsort** and **qrsolve** have *never existed* in embench-iot master
  (`git log --all -- src/qlsort src/qrsolve` is empty). The brief's
  candidate list also names `stoneman`, likewise never present. The
  north-star spec (docs/gem5-fi/ooo/03-workloads.md) only mandates
  "Embench: 公开的 22 个小程序，整数、浮点、乘除、哈希都有，每个自带结果校验"
  — no specific program names — so substitution inside the Embench
  subset stays within spec.
- **Embench-IoT 2.0 removed every floating-point benchmark**: nbody,
  cubic and primecount were deleted at `1b2731f` (2024-03-08, "Remove
  benchmarks"); minver and st at `fc72c8d` ("Add Depthconv; Remove
  minver; Remove st"). At HEAD the only benchmark whose source mentions
  `float` with real FP semantics is none — depthconv (the lone new
  addition) is *quantized* int8/int32 TFLite arithmetic; its
  `float_activation_min/max` struct fields are unused. So a fp subset
  cannot be built from HEAD at all.
- Replacements (recorded per the plan's substitution rule):
  - qlsort -> **wikisort** (sort-class workload at HEAD; WikiSort is an
    O(n log n) stable sort — closest semantic match to a quicksort
    benchmark).
  - qrsolve -> **minver** (3x3 float matrix inversion — closest
    linear-algebra match to a QR solver), vendored from `92da124b`.
  - nbody stays **nbody** (double-precision N-body energy kernel,
    sqrt/div-heavy), vendored from `92da124b`.

## File-by-file source

| file | upstream path | commit |
|---|---|---|
| `COPYING` | `COPYING` | 09c2ed8c (verbatim, GPL-3.0-or-later) |
| `support/main.c` | `support/main.c` | 09c2ed8c |
| `support/support.h` | `support/support.h` | 09c2ed8c |
| `support/beebsc.c` | `support/beebsc.c` | 09c2ed8c |
| `support/beebsc.h` | `support/beebsc.h` | 09c2ed8c |
| `boardsupport.c` | `examples/native/speed/boardsupport.c` | 09c2ed8c |
| `crc32/crc_32.c` | `src/crc32/crc_32.c` | 09c2ed8c |
| `md5sum/md5.c` | `src/md5sum/md5.c` | 09c2ed8c |
| `matmult-int/matmult-int.c` | `src/matmult-int/matmult-int.c` | 09c2ed8c |
| `wikisort/libwikisort.c` | `src/wikisort/libwikisort.c` | 09c2ed8c |
| `nbody/nbody.c` | `src/nbody/nbody.c` | 92da124b |
| `minver/libminver.c` | `src/minver/libminver.c` | 92da124b |

Support files are taken from HEAD only: the 1.0-era vs HEAD beebsc
diff is a seed-type fix (`long` -> `unsigned long`, avoiding signed
overflow UB), an `assert_beebs` semantics change and comment text; the
API used by the benchmarks (`*_eq_beebs`, `srand_beebs`, heap
functions) is identical, so the fp benchmarks build unchanged against
HEAD support.

## Local deviations from upstream (the ONLY ones)

Each benchmark source carries exactly one `/* gem5-fi W1.2 */`-marked
addition for the oracle chain (pattern copied from
workloads/ooo/coremark/core_main.c): on `verify_benchmark`'s success
path it prints `FINAL=<16hex>`, the FNV-1a 64-bit hash of the same
data upstream's verify checks. Benchmark logic is untouched; a verify
failure still exits 1 (Crash/DUE per tools/classify.py), a silent
corruption of the checked data changes FINAL (SDC). Hashed data per
benchmark:

| benchmark | hashed data | notes |
|---|---|---|
| crc32 | the verified CRC result `r` | `r` is upstream's `%32768` fold -> same 15-bit entropy as upstream's own check |
| md5sum | full 4-word digest {h0..h3} | strictly stronger than upstream's XOR fold |
| matmult-int | `ResultArray` (20x20 long) | same matrix the memcmp checks |
| wikisort | `array1` (400 Test elements) | same array the memcmp checks |
| nbody | `solar_bodies` (5 bodies x 8 doubles) | byte-level FP oracle; fplib proven bit-exact vs hardware (W1.5b/W1.5c) |
| minver | `c`, `d`, `det` (3x3 float each + det) | byte-level FP oracle, stricter than upstream epsilon compare |

Two files also gained `#include <stdio.h>` / `<stdint.h>` lines
(marked `/* gem5-fi W1.2 */`) for the printf/uint64_t used by the
FINAL block (crc_32.c, nbody.c, libminver.c; md5.c and libwikisort.c
already included them).

Upstream files otherwise byte-identical to the listed commits
(verify with `git show <commit>:<path>` in a fresh clone).

## Build

Clean-room recipe (upstream scons machinery replaced by the
workloads/ooo framework Makefile — upstream's per-benchmark compile is
simply `<benchmark>.c + support/main.c + support/beebsc.c +
boardsupport.c`, cf. sconstruct.py `build_support_objects`):

    gcc -O2 -static -Wall -Wextra <suppress> \
        -DWARMUP_HEAT=1 -DGLOBAL_SCALE_FACTOR=<gsf>   (HEAD-era benchmarks)
        [-DCPU_MHZ=<mhz>]                             (1.0-era nbody/minver) \
        -I embench/support -I embench \
        <benchmark>.c embench/support/main.c embench/support/beebsc.c \
        embench/boardsupport.c -o <benchmark>

`-Wno-*` set (documented deviation, sources kept verbatim): upstream
code carries dead-local warnings (`-Wunused-variable`,
`-Wunused-but-set-variable`), unused test-generator parameters
(`-Wunused-parameter`), one provably-false `-Wmaybe-uninitialized`
(crc32 `r`: the scale factors are compile-time >= 1 so the loop always
executes), and beebsc.h's `float_eq_beebs` macro triggers
`-Wabsolute-value` when called with a double constant (minver). All
five classes are upstream code-quality artifacts, not logic issues;
the FINAL hunks themselves are warning-clean under -Wall -Wextra.

Scale factors (W1 Global Constraints: C3 SE hostSeconds <= 60 s) are
per-benchmark Makefile variables — see workloads/ooo/Makefile and the
measured values in workloads/ooo/README.md.
