# MD04 workload amendment v2 — trace-size reduction (LSU v3.3.2)

The v1 candidate (`audit_v3_3_2/workloads/MD04_evidence.md`) produced eight
in-main violation pairs, but its 1 MiB late-data array and 8 rounds × 1024
elements made one `--chaos_propagation` run convert a 779 MB JSONL trace
(~47 s wall each, ~1.2 GB per fault/control pair). That is not sustainable
for 10 MD04 runs. The mechanism is unchanged; only the iteration scale is
reduced.

## Changes

| Constant | v1 | v2 |
|---|---:|---:|
| `SMALL` (store/load target) | 1024 | 256 |
| `BIG` (late-data source) | 131072 | 16384 |
| `rounds` per loop | 8 | 4 |

All eight loops, distinct store/load PCs, offsets and barriers are
unchanged.

## Re-verification (real output)

```
$ workloads/directed/compile_md04_violations_v332.sh
dd241c3097e61495141e614ce493ba4b2901a7df751baa95e69365bdf8f95c43  md04_violations_v332
9b1f57a901205ae8f855392f99b1f059c73d69d7c240adc1eae019747c7e6a6d  md04_violations_v332.c

$ ./workloads/directed/md04_violations_v332
checksum=0x22be5ae3364d0c9f
```

Golden updated to `0x22be5ae3364d0c9f`.

Count-only on the final binary (070d68a6…):

```
$ build/ARM/gem5.opt ... --chaos_md04 --md04_first_clock 0 \
    --md04_max_faults 0 --md04_probability 1.0 --md04_rng_seed 1 \
    --md04_event_ordinal 0 --md04_count_only
CHAOS_ELIGIBLE_COUNT=11
```

11 = 2 libc-startup pairs + 8 in-main pairs + 1 libc-printf pair, exactly
the v1 split; the in-main ROI is global ordinals 3–10 (N=8), so the five
percentile ranks `k=ceil(p*8)=1,3,4,6,8` map to ordinals 3,5,6,8,10.

Fault probe at ordinal 3 (real output):

```
Tick: 51902620, Site: checkViolations, load_seq=125104, store_seq=125103,
addr=0x491990, size=8, store_addr=0x491990, store_size=8,
load_pc=0x4005ec, store_pc=0x4005e8, ..., eligible_ordinal=3,
..., faults_injected: 1
```

Both PCs are inside main (`0x4004f0`–`0x4009bf`); the pair is 8B/8B with
real byte overlap. One run now takes 5.3 s of simulation and a 128 MB
output tree instead of 779 MB.

## Honest limitation

The PC offsets changed from v1 (constants affect code layout); the
*ordinal* mapping is unchanged because it is defined over the eligible
event stream, not over static PCs. The workload remains a **candidate**;
the frozen MD04 mapping (`replay_dependency`) is untouched.
