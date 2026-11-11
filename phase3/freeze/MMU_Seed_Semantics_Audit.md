# MMU Formal Seed Semantics Audit (FROZEN AUTHORITY)

Date: 2026-11-12 (freeze decision dated 2026-11-11)
Workspace: `/home/sdc/gem5-fi-mmu-impl-v2`
Status: **audit complete; no real nondeterministic source found on the MMU
run path.** No seed was generated, hashed, timestamped or coerced; the
authoritative Seed is the literal text `N/A_DETERMINISTIC`.

Researcher decision (already approved): all 40 SampleRunIDs are FROZEN;
SeedPolicy=DETERMINISTIC; SeedSource=RESEARCHER_APPROVED;
SampleFreezeStatus=FROZEN. The literal is never parsed as an integer and is
never passed to gem5.

This file supersedes `phase3/formal/Seed_Semantics_Audit.md` and corrects one
factual error in it: the audit previously claimed the cache prefetcher was
`NULL`. The gem5-stdlib cache classes actually attach `StridePrefetcher`.
That prefetcher is still deterministic (it contains no RNG call), but the
evidence is recorded correctly below.

## 1. Actual FS config used by the MMU runner

The runner command (`--describe`, quoted in §5) uses
`configs/fs/lsu_b0_fs.py`. That file is a 25-line shim:

```
19:import os
20:import sys
24:exec(compile(open(os.path.join(_se_dir, "arm_chaos_fs.py")).read(),
25:             "arm_chaos_fs.py", "exec"))
```

It injects `--lsu_b0` and execs `configs/se/arm_chaos_fs.py`; all simulation
objects come from `arm_chaos_fs.py` and the gem5 stdlib it imports
(`m5`, `ArmBoard`, `PrivateL1PrivateL2CacheHierarchy`,
`DualChannelDDR4_2400`, `SimpleProcessor`, `Simulator`; lines 22-46). There is
**no `--seed` token in `lsu_b0_fs.py`** (`grep -nE "seed|random|rng"
configs/fs/lsu_b0_fs.py` -> no hits), and the runner command contains no
seed-bearing flag.

The MMU fault models are not the legacy `CHAOSArmTLB` / `CHAOSPTW` /
`CHAOSArmSysReg` injectors. They are fields of `CHAOSPropagation`
(`--mmu_fault_model M0x`, parsed at `arm_chaos_fs.py:203` and mounted at
`arm_chaos_fs.py:693-717`).

## 2. Per-source inventory

| # | Source | Used by MMU runs? | Consumes a seed? | Deterministic? | Evidence (file:line) |
|---|---|---|---|---|---|
| 1 | Sample `Seed` cell (`N/A_DETERMINISTIC`) | No — recorded only | No | Yes (literal) | `tools/mmu_formal_runner.py` `build_plan` rejects any `--*seed*` flag; manifest has `seed_used_by_gem5=false`, `seed_delivery=not_passed_to_gem5` |
| 2 | gem5 global RNG `Random::globalSeed` | Only via consumers below | Fixed default 5489 | Yes | `CHAOS/gem5/src/base/random.cc:79` (`globalSeed = 5489`) |
| 3 | O3 fetch SMT thread pick | Yes (single-thread range) | Uses global RNG | Yes — range `0..numThreads-1` is `0..0` with `num_cores=1` | `CHAOS/gem5/src/cpu/o3/fetch.hh:209`, `fetch.cc:886`; `configs/se/arm_chaos_fs.py:361` (`SimpleProcessor(..., num_cores=1, ...)`) |
| 4 | Default O3 branch predictor `TournamentBP` | Yes | No RNG call | Yes | `CHAOS/gem5/src/cpu/o3/BaseO3CPU.py:202-206`; `grep -n "random\|rng" CHAOS/gem5/src/cpu/pred/tournament.cc` -> none |
| 5 | TAGE / LTAGE / Multiperspective / loop predictors | No — not instantiated | Would use global RNG (TAGE/LTAGE/loop) | n/a | Default stdlib `SimpleProcessor` uses `O3CPU` defaults (§4); no `branchPred` override in `arm_chaos_fs.py` |
| 6 | Cache replacement policy | Yes — `LRURP` | No | Yes | `CHAOS/gem5/src/mem/cache/Cache.py:111-113`; no `replacement_policy` override in `arm_chaos_fs.py` |
| 7 | L1I/L1D/L2 prefetcher `StridePrefetcher` | **Yes** (stdlib default) | No RNG call | Yes | `caches/l1icache.py:56,67`, `caches/l1dcache.py:56,67`, `caches/l2cache.py:55,67`; instantiated in `private_l1_private_l2_cache_hierarchy.py:138-144`; `stride.cc:53` is an include only, `grep -n "genRandom\|rng->random" stride.cc` -> none |
| 8 | `RandomRP` / `BIPRP` / `BRRIPRP` | No | Would use global RNG | n/a | Not referenced by the config; default is `LRURP` (`Cache.py:111-113`) |
| 9 | Ruby / Garnet / CHI | No — classic cache hierarchy | n/a | n/a | `grep -niE "ruby|garnet" configs/se/arm_chaos_fs.py configs/fs/lsu_b0_fs.py` -> none |
| 10 | DVFS / thermal / clock randomness | No | No | Yes | `grep -niE "dvfs|thermal" configs/se/arm_chaos_fs.py configs/fs/lsu_b0_fs.py` -> none |
| 11 | Legacy CHAOS injectors (`--chaos_armtlb`, `--chaos_ptw`, `--chaos_sysreg`, `--chaos_phys`, `--chaos_addrpath`) | No — mount gate is false; runner passes none | Their `--*_rng_seed` defaults are fixed literals `20260825` | Yes if ever enabled | `arm_chaos_fs.py:402` mount gate; defaults at `146,170,181,307,318`; wiring at `437,469,491,510,531` |
| 12 | MMU fault models M01-M08 via `CHAOSPropagation` | Yes | No RNG call | Yes — explicit model/target/eligible index | `grep -rn "genRandom\|rng->random\|rand()" CHAOS/gem5/src/cpu/o3/CHAOSPropagation/ CHAOS/gem5/src/arch/arm/{mmu,table_walker,tlb}.cc` -> none |
| 13 | Checkpoint / restore | Yes | No | Yes — fixed checkpoint directory | `arm_chaos_fs.py:545-550` (`board._checkpoint`); `simulate/simulator.py:576-578`; `sim/serialize.cc:97` `time(NULL)` only writes a human-readable header comment |
| 14 | `m5.core.seedRandom` / `Random::reseedAll` | No — never called | Would reseed global RNG | n/a | `CHAOS/gem5/src/python/pybind11/core.cc:314`, `base/random.hh:168`; no call in `arm_chaos_fs.py` / `lsu_b0_fs.py` |
| 15 | Workload binaries W9/W10/W10S/W11-W14 | Yes | No | Yes | All static `ELF ... EXEC` (not PIE); `grep -nE "rand|srand|getrandom|urandom|clock_gettime|gettimeofday|time\(" workloads/mmu/W*/mmu_w*.c` -> no hits; W9 uses fixed `MAP_FIXED` VAs (`mmu_w9.c:31-32`) |
| 16 | Guest kernel / OS entropy | Restored from checkpoint | No host seed | Yes — checkpoint fixes kernel memory including its RNG state; workloads use fixed VAs | `arm_chaos_fs.py:545-550`; no virtio-rng in the config (`grep -ni "rng"` -> only injector names) |
| 17 | Host time / environment | Only checkpoint header text | No | Simulation not affected | `CHAOS/gem5/src/sim/serialize.cc:93-99` (header comment) |

## 3. Seed-flag check (real commands)

```
$ grep -n "seed" configs/fs/lsu_b0_fs.py
(no output)

$ grep -rn 'add_argument.*"--seed"\|"--seed"' configs/ CHAOS/gem5/src/python/
(no output)

$ grep -n "add_argument.*rng_seed" configs/se/arm_chaos_fs.py
146:  --tlb_rng_seed default=20260825
170:  --sysreg_rng_seed default=20260825
181:  --ptw_rng_seed default=20260825
307:  --phys_rng_seed default=20260825
318:  --addrpath_rng_seed default=20260825
```

Those `*_rng_seed` options belong to the legacy injectors, which the MMU
runner never mounts (`arm_chaos_fs.py:402` gate). The defaults are fixed
literals, not generated values. The runner additionally enforces a hard
guard: any command token that starts with `--` and contains `seed` raises
`BLOCKED_SEED_POLICY` instead of running.

## 4. Checkpoint / restore and workload binaries

* The runner restores a fixed checkpoint (`runs/mmu_boot7/cpt.243261068760` in
  the quoted `--describe`). `board._checkpoint` is set at
  `arm_chaos_fs.py:550`; stdlib restore is `simulate/simulator.py:576-578`.
  Checkpoint serialization contains a host-time comment
  (`serialize.cc:97`), which is not simulated state.
* The only global-RNG consumer reachable on this path is the O3 fetch SMT
  pick (`fetch.cc:886`). With `num_cores=1` (`arm_chaos_fs.py:361`) the
  requested range is `0..0`, so the draw is `0` regardless of RNG state.
* Workloads are static `ET_EXEC` binaries (checked with `readelf -h`) with
  fixed `MAP_FIXED` target VAs and no entropy/time calls in source. The
  generated rcS files embed the workload binary as base64; a naive
  `grep -n seed *.rcS` hit at
  `configs/fs/generated/mmu_w12_run_R0*.rcS:4840` is base64 payload text,
  not a seed option.

## 5. Real runner --describe output (frozen sample)

`python3 tools/mmu_formal_runner.py --sample M06-F0-W10-S01-R01 --describe`
(excerpt; full command in the JSON):

```
"status": "READY"
"run_id": "M06-F0-W10-S01-R01"
"sample_id_status": "FROZEN"
"seed": "N/A_DETERMINISTIC"
"seed_present": true
"seed_valid": true
"seed_policy": "DETERMINISTIC"
"seed_source": "RESEARCHER_APPROVED"
"seed_status": "VALID_DETERMINISTIC"
"seed_literal_deterministic": true
"seed_used_by_gem5": false
"seed_delivery": "not_passed_to_gem5"
"authority_excel_source": "FROZEN_AUTHORITY"
"authority_csv_source": "FROZEN_AUTHORITY"
```

The command contains only `--mmu_*` / `--prop_*` / runtime flags; the runner's
own check reports `seed-flag args: []`.

## 6. Conclusion

For the 40 frozen formal samples, every seed-bearing consumer is either
absent, or driven by the fixed global RNG seed 5489 with a degenerate
single-thread range, or has no RNG consumption at all. The experiment is
deterministic as configured. `N/A_DETERMINISTIC` is therefore a factual
description, not a placeholder: the literal is passed through the manifest as
metadata and never handed to gem5.
