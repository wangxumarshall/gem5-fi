# Reproduction entry

From the project root:

```bash
export GEM5_ROOT=/path/to/gem5-fi   # checkout of baseline 2f4e00b4 + RF/WB patch
./reproduction/reproduce_all.sh --check
./reproduction/reproduce_all.sh --smoke
./reproduction/reproduce_all.sh --all
```

`--all` performs 25 count-only prescans, computes T01/T02/T03, runs 75 Faults,
runs 25 Controls, and validates golden/classification/results.  It does **not**
rebuild gem5; run `scripts/build/build_gem5.sh` first if `gem5.opt` is absent.

`--smoke` uses a separate `runs/smoke/` directory and performs only:

- M005 C01 prescan + corrected timing comparison;
- 5 Controls (C01, one per model);
- 5 Faults (C01 T01, one per model);
- golden + partial classification/result checks.

Experimental parameters are fixed in `scripts/experiment/run_one.sh`:
`--cpu O3 --maxinsts=1000000 --max_ticks=50000000`, 120 s timeout.  Do not change
them when reproducing the frozen results.

Outputs go to `runs/` and are git-ignored.  To replace existing samples:

```bash
RFWB_FORCE=1 ./reproduction/reproduce_all.sh --controls
```

The authoritative 25-row timing table is
`configs/timing/frozen_timing_plan.tsv`; the new plan must match it, including
M005 corrected N = 6/6/8/6/8 and target sequences.
