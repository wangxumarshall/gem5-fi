# Seed Semantics Audit (MMU formal samples)

Date: 2026-11-11
Status: audit complete; **no seed was generated, defaulted, hashed or
timestamped**. The authoritative Excel cell remains `NEEDS_AUTHORITATIVE_EXCEL`
until the researcher decides.

## 1. Question

The runner records `07_Sample_Matrix.Seed` but sets
`seed_used_by_gem5=false`. This audit answers, from the real source tree,
which random sources the MMU FS experiment actually uses and whether a seed
must be threaded into gem5.

## 2. Random-source inventory (source evidence)

| # | Source | Used by the MMU runs? | Consumes a seed? | Deterministic? | Evidence |
|---|---|---|---|---|---|
| 1 | gem5 global RNG `gem5::Random::globalSeed` | Only if a SimObject calls `Random::genRandom()` | Yes (global default 5489) | Yes, fixed default | `CHAOS/gem5/src/base/random.cc:79` (`globalSeed = 5489`), `random.hh:83,120,170` |
| 2 | Cache replacement policy | **No** — default `LRURP()` | No | Yes | `CHAOS/gem5/src/mem/cache/Cache.py:111-113`; the FS config never overrides `replacement_policy` (`grep replacement_policy configs/se/arm_chaos_fs.py` → no hits) |
| 3 | `RandomRP` / `BIPRP` / `BRRIPRP` | **No** — not instantiated | Would use (1) | n/a | `CHAOS/gem5/src/mem/cache/replacement_policies/{random_rp,bip_rp,brrip_rp}.hh`; not referenced by the config |
| 4 | Prefetcher | **No** — default `NULL` | No | Yes | `CHAOS/gem5/src/mem/cache/Cache.py:107` (`prefetcher = Param.BasePrefetcher(NULL, ...)`); no prefetcher in `configs/se/arm_chaos_fs.py` |
| 5 | Garnet synthetic traffic RNG | **No** — classic caches, not Garnet | Would use (1) | n/a | `CHAOS/gem5/src/cpu/testers/garnet_synthetic_traffic/GarnetSyntheticTraffic.cc:107`; not used by `lsu_b0_fs.py` |
| 6 | Workload randomness (W9/W10/W10S/W11-W14) | **No** | No | Yes | `grep -rn 'rand\\|srand\\|getrandom\\|urandom' workloads/mmu/...` → no hits. Workloads use deterministic fixed VAs, sentinels and fixed iteration counts |
| 7 | MMU fault injector (M01-M08, CHAOSPropagation) | **Yes, but deterministic** | No | Yes | Activation is gated by `mmuFaultModelIs`, explicit `--mmu_target_*`, `mmuTargetSeqMatch`, and the 1-based `mmuEligibleEvent` counter (`CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc`). No RNG call in the MMU path |
| 8 | Legacy CHAOS injectors (`--tlb_probability`, `--sysreg_probability`, `--ptw_probability`, ...) | **No** — defaults 0.0 and not attached by the MMU run command | Would use `chaosSampleLCG(rng)` | Yes only if enabled with a fixed `rngSeed` | `configs/se/arm_chaos_fs.py:109,145,167,181,302,313,432,464,486`; `CHAOS/gem5/src/cpu/o3/chaos_trigger.hh:31-86` |
| 9 | OS/guest-kernel randomness | Not a gem5 seed input | No | The guest kernel boot path is identical for every sample restored from the same checkpoint; the checkpoint fixes kernel state | `--restore-checkpoint runs/mmu_boot7/cpt.243261068760` |

## 3. Is there a gem5 CLI seed?

This tree exposes programmatic reseeding (`m5.core.seedRandom(seed)`,
`CHAOS/gem5/src/python/pybind11/core.cc:313-314`) but the MMU config does not
call it and no `--seed` CLI flag is defined in `configs/se/arm_chaos_fs.py`.
Therefore the runner's current behaviour (`seed_used_by_gem5=false`) is
factually correct for the current config.

## 4. Conclusion

For the 40 formal MMU samples, every source in the execution path is either

* absent (RandomRP/BIP/BRRIP, prefetcher, Garnet), or
* deterministic given the restored checkpoint and explicit fault target
  (LRU caches, fixed workloads, eligible-event MMU injectors, legacy
  injectors disabled at probability 0).

The experiment is therefore **deterministic** as configured. The honest
options are:

1. **Researcher-approved `N/A_DETERMINISTIC`** (recommended): the Seed cell is
   set to the literal `N/A_DETERMINISTIC` after review, and the runner records
   it without passing anything to gem5 (because nothing consumes it). The
   preflight treats this as a present, approved value only if the researcher
   adds it to the approved vocabulary.
2. **Explicit numeric seed threading** (only if a random source is later
   enabled): read the Excel seed and pass it to gem5 by calling
   `m5.core.seedRandom(<seed>)` before `simulator.run()` in
   `configs/se/arm_chaos_fs.py` (e.g. a new `--seed` argument), and set
   `seed_used_by_gem5=true` in the runner manifest. This is a config change,
   not made here.

No value was chosen. The Excel remains untouched and all 40 samples keep
`BLOCKED_MISSING_SEED` in addition to `BLOCKED_SAMPLE_ID_NOT_FROZEN`.

## 5. Runner behaviour today (verified)

`python3 tools/mmu_formal_runner.py --sample M06-F0-W10-S01-R01 --describe`
returns `BLOCKED_SAMPLE_ID_NOT_FROZEN` first (SampleID freeze gate), and after
the researcher freezes IDs it returns `BLOCKED_MISSING_SEED` (exit 3) until a
seed decision is recorded. The manifest field is
`"seed_used_by_gem5": false`.

## 6. Reproduce this audit

```bash
cd /home/sdc/gem5-fi-mmu-impl-v2
grep -n 'globalSeed' CHAOS/gem5/src/base/random.cc
sed -n '105,115p' CHAOS/gem5/src/mem/cache/Cache.py
grep -n 'replacement_policy\|prefetcher' configs/se/arm_chaos_fs.py
grep -rn 'rand\|srand\|getrandom\|urandom' workloads/mmu/W9 workloads/mmu/W10 \
    workloads/mmu/W10S workloads/mmu/W11 workloads/mmu/W12 \
    workloads/mmu/W13 workloads/mmu/W14
grep -n 'seedRandom' CHAOS/gem5/src/python/pybind11/core.cc
```
