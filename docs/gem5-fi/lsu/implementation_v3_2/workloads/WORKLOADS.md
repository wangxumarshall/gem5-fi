# LSU v3.2 workload package

All eight workloads compile with host `gcc -O2 -static` on aarch64 and were
re-run under the branch-root `build/ARM/gem5.opt` (gem5 v25.1.0.1, source
commit `6f98088a`) after any source change. Baselines and event proofs live in
`../baselines/<name>/`.

| ID | Workload | Source | Binary SHA256 | Golden | gem5 baseline | Target-event proof |
|---|---|---|---|---|---|---|
| W1 | AGU-AddrModes | `agu_addrmodes.c` | `90a19003…b49b` | `728e604ffcec539d` | exit 0, tick 19544525 | 6 `Read called` address formations + `Doing memory access` in `event_proof.log` |
| W2 | LQ-Lifetime | `lq_lifetime.c` | `7c69fd27…156d` | `1624d44faff77183` | exit 0, tick 37983715 | 6232 `Inserting load`, 756 `Load Instruction … squashed` |
| W3 | SQ-Drain | `sq_drain.c` | `d423539c…188f` | `ba3b3185e541ad03` | exit 0, tick 149995615 | 31092 `Writing back store` and 31092 `Completing store` |
| W4 | SQ-Forward | `sq_forward.c` | `132a84f7…f297` | `1f4cbf14327717df` | exit 0, tick 19112940 | 6 `Forwarding from store`, 1 `Load-store forwarding mis-match` |
| W5 | Load-Response | `load_response.c` | `3779e8ce…e711` | `99c106541150be0e` | exit 0, tick 55153560 | 18269 `Read called` + `Doing memory access` |
| W6 | Store-Path (rebuilt) | `store_path.c` | `906b3798…fbcf` | `2543a2a60de01795` | exit 0, tick 92581720 | 10609 `Completing store`; guard-page probe: old SIGSEGV, fixed `NO_FAULT` |
| W7 | Replay-Dependency | `replay_dependency.c` | `ca15390f…38f4` | `59fc61c040618747` | exit 0, tick 40653690 | 267 `forwLoads`, 5 `rescheduledLoads`, 7 `memOrderViolation`, 4 forwarding mis-match lines |
| W8 | Alignment (rebuilt) | `alignment.c` | `89ff937a…18c0` | `3f89eab79392ce69` | exit 0, tick 34556445 | unaligned addresses `0x…0a..0x…0f` in `Read called`; guard-page probe old SIGSEGV, fixed `NO_FAULT` |

## W6/W8 repair provenance

Original files are preserved under `_original_v31/`. The guard-page probe
(`tests/oob_probe.c`) places a `PROT_NONE` page immediately after a
32 KiB/4 KiB object and reproduces the original final offsets:

```
probe_store_path.log:   exit 139 (SIGSEGV)
probe_alignment.log:    exit 139 (SIGSEGV)
probe_store_path_fixed.log:   exit 0, NO_FAULT
probe_alignment_fixed.log:    exit 0, NO_FAULT
```

The fixed binaries and goldens above are the only valid post-fix baselines;
the old binaries/goldens are not used. The decisive logs are
`logs/probe_results.txt` and the four `logs/probe_*.log` files. On this host
clang ASan did not flag the W6 partially-out-of-bounds 8-byte store, so the
guard-page probe (not ASan) is the W6 evidence; W8's tail read/write is
additionally caught by ASan.

## Reproduction

```bash
./compile_<name>.sh          # gcc -O2 -static -o <name> <name>.c
./run_<name>.sh              # host run + oracle_check.py
../baselines/run_baselines.sh  # eight gem5 no-fault baselines
```

## v3.2.12 supplement: `sq_reload_v3212`

Added by the propagation-closure round (Task 10, shared by the SQ01/SQ03/SP05
store-side models). Not part of the W1–W8 suite; `compile_sq_reload_v3212.sh`
builds it the same way (`gcc -O2 -static`).

- **Purpose.** 128 iterations of `store -> dmb ish -> same-address load` on a
  `volatile uint64_t buf[256]`. On gem5 v25 O3 the aarch64 `dmb ish` decodes
  with `IsReadBarrier|IsWriteBarrier`: commit holds the barrier at the ROB
  head until `hasStoresToWB` clears (commit.cc `commitHead`), so the store has
  left the SQ and reached memory before the dependent younger load issues —
  the reload load is a real memory-visibility consumer, never a same-cycle SQ
  forward.
- **Detection surface.** SQ01 store-data (the drained write is the only source
  of the reloaded value), SQ03 SQ-state (drain/visibility timing), SP05 drain
  staging. The reloaded value feeds a byte-wise FNV-1a checksum and an
  equality-dependent branch (`cmp`+`b.ne`, verified in the disassembly, not a
  `csel`), so corruption lands in the checksum (SDC) or flips the control path.
- **Golden / SHA256 (frozen by host double-run, both identical).**
  - checksum: `checksum=0x7df5034c23f3e703` (`sq_reload_v3212.golden`)
  - ELF SHA256: `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6`
- **gem5 no-fault baseline** (branch-root `build/ARM/gem5.opt`, O3, exit 0):
  same `checksum=0x7df5034c23f3e703`, `simTicks 28387975`.
- **Drain→reload proof** (no-fault `--chaos_propagation`
  `--prop_trace_file /tmp/sq_reload_trace.csv.gz`): all 128 store→reload pairs
  show `sq_lifecycle free/complete` (drain) strictly before the paired load's
  `lq_lifecycle free/commit` (128/128; steady-state gap exactly 3850 ticks),
  and 0 of the 128 reload loads appear in any `fwd` row (0 `fwd` rows with a
  `buf` address, `buf` at `0x491990`). Full evidence in the round's
  task-10 report.
