# LSU v3.3.3 — Runner Dry-run Report

**Date:** 2026-11-12
**Runner:** `tools/lsu_v332_matrix.py` (verified live, not by filename)
**Dry-run command:**
```
python3 tools/lsu_v332_matrix.py --models all --roles fault,control --dry-run
```
**Output file:** `audit_launch_v333/artifacts/dry_run_final.log`

## Interface (live `--help`)

```
usage: lsu_v332_matrix.py [-h] [--models MODELS] [--roles ROLES]
                          [--contexts CONTEXTS] [--out-base OUT_BASE]
                          [--out-csv OUT_CSV] [--force] [--dry-run]
```

- Defaults: `--models all`, `--roles fault,control`, `--contexts 1,2,3,4,5`,
  `--out-base runs/lsu/formal_v333`,
  `--out-csv runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv`.
- `--force` is required to overwrite an existing run dir; the runner refuses
  otherwise (no more silent `rm -rf` of history).
- The runner serializes the set (one gem5 process at a time) and holds a
  process-wide `flock` on `runs/lsu/formal_v333/.lsu_v332_matrix.lock`.

## Dry-run result (real output)

```
dry-run: 120 commands; no run dirs written
```

Machine checks on `dry_run_final.log`:

| Check | Result |
|---|---|
| Commands | 120 |
| Fault / Control | 60 / 60 |
| Models × contexts | 12 × 5; every pair present, no duplicates |
| Unique output dirs | 120/120 (one per task) |
| History references (`audit_v3_3_3`) | 0 |
| `run_pilot` commands with frozen `--seed` and `--preserve-sample-id` | 105/105 |
| Direct A03/RP01 commands with frozen `--rng_seed`/`--addrpath_rng_seed` | 15/15 |
| Fault/control same ordinal | 60/60 pairs (A03 uses a different flag name; RP01 control omits the injector by design) |
| Target out-base | `runs/lsu/formal_v333` (absent before dry-run) |

Representative commands (real):

- A01 R01 fault:
  `... run_pilot.py --model A01 --context-index 1 --event-ordinal 597 ... --seed 2108120075 --preserve-sample-id`
- LQ04 R01 fault:
  `... run_pilot.py --model LQ04 --context-index 1 --event-ordinal 1 ... --seed 1842987246 --preserve-sample-id`
  and the inner gem5 command contains `--lq04_rng_seed 1842987246` (verified with
  `run_pilot.py --dry-run`). This closes the pre-formal LQ04 `rngSeed=0` defect.
- RP01 R01 fault:
  `... gem5.opt ... --chaos_lsqfwd --lsq_struct_mode rp01_skip_replay --max_faults 1 --rng_seed 3135797961 --rp01_event_ordinal 26 --rp01_watchdog_cycles 20000000`

## Manifest generation for the formal campaign

The historical v3.3.3 run manifests are pre-formal artifacts and are not
backfilled. The formal sequence generates the authoritative manifest after the
matrix:

```
# after the 120 runs
python3 tools/lsu_v333_launch.py --runs runs/lsu/formal_v333 \
  --out runs/lsu/formal_v333/manifests --manifest-only
```

This writes `LSU_120Run_Campaign_Manifest.csv`, the pair map, and one
`campaign_manifest.json` per run dir with the 21 required fields (RunID,
SampleRunID, Seed, Role, ROI, Warmup, Percentile, EligibleEventOrdinal,
DynInstSeq, PC, injection/terminal/oracle, binary/ELF/config SHA). The preflight
already exercised this path on the 120 pre-formal runs (120 rows, 60/60,
0 missing fault identities).

## Launch command (not executed)

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
python3 tools/lsu_v332_matrix.py --models all --roles fault,control \
  --contexts 1,2,3,4,5 \
  --out-base runs/lsu/formal_v333 \
  --out-csv runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv
python3 tools/lsu_v333_launch.py --runs runs/lsu/formal_v333 \
  --out runs/lsu/formal_v333/manifests --manifest-only
```

## Scheduling order and estimate

Built-in order is model-major: A01, A03, FW02, FW05, SQ01, SQ03, SP05, DA04,
LP01, MD04, LQ04, RP01; each R01→R05; fault then control. One gem5 process at
a time; 120 runs; measured pre-formal gem5 elapsed sum ~429 s, rehearsal wall
span ~28.5 min; realistic 30–40 min; worst case ~12.9 h if every run hits its
timeout. RP01 fault (~21 s/run) and A03 fault (~14 s/run) are the gem5 long
poles; MD04 is the disk pole (~1.2 GB).

## Residual dry-run caveats

- `--preserve-sample-id` makes `run_pilot` keep the v3.2.7 Excel SampleRunID;
  the frozen `60_SAMPLE_MATRIX.csv` and the workbook carry the same IDs. For
  A03/RP01 direct commands the SampleRunID is written by the manifest
  post-step, not the command line.
- A01's executed `dyn_inst_seq` (12909 at ordinal 597) differs from the
  count-only census (12752). This is the one unresolved launch blocker and is
  documented in `LSU_Final_Blockers.md`.
