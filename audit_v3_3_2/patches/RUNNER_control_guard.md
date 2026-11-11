# RUNNER control guard — DA04 / MD04 zero-injection controls + `--dry-run`

Date: 2026-11-11 (LSU v3.3.2, Agent D, P0 control hazards)
Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
Branch at time of work: `fix/r6-s-w1-continuation-20261101` (not committed by this agent)

## Problem

Two matched no-fault controls were **not** truly zero-injection in v3.3.1:

| model | pre-fix command fragment at `--probability 0.0` | why it could fire |
|---|---|---|
| DA04 | always `--chaos_lsqfwd --lsq_struct_mode da04_be_bit0 ...` | DA04 byte-enable corruption is an ordinal-gated F0 selector on `lsq_pushRequest_byte_enable`; its decision never consults the global `--probability`, so `--probability 0.0` still fires. |
| MD04 | always `--chaos_md04 ... --md04_probability 1.0 ...` | CHAOSMD04 gates on its own `--md04_probability` (hard-coded `1.0` for fault runs) and never reads the global `--probability`; mounting the injector guarantees a fire. |

LQ04 and FW02 already had the correct pattern (omit the injector at p=0, keep
`--chaos_propagation`). The RP01 replay pilot also hard-coded
`--probability 1.0` with a mandatory `--chaos_lsqfwd` carrier.

## Change (3 files, no C++ / binary change)

### `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`

- **Extracted** the inline per-model `if/elif` flag chain into the pure helper
  `build_model_extra(model, probability, seed, ordinal) -> list[str]`.
  `main()` now calls it; every flag list for every model is copied verbatim,
  so **fault-on (p>0) commands are byte-identical** to before.
- **DA04**: `probability == 0.0` → `[]` (injector omitted).
- **MD04**: `probability == 0.0` → `[]` (injector and all `--md04_*` args
  omitted, including the hard-coded `--md04_probability 1.0`).
- LQ04 / FW02 omit branches preserved exactly; all other models unchanged
  (their attach is probability-gated in the injector, so the control keeps
  the mount — pinned by a regression test).
- Added `--dry-run`: after the command is built and `command.txt` is written,
  print the exact space-joined command and `return 0` **before**
  `build_manifest`/`subprocess.run`. No manifest, no `pilot_meta.json`, no
  `stdout/stderr.log` — a dry run cannot be mistaken for an executed run.

### `docs/gem5-fi/lsu/implementation_v3_2/platform/run_replay_pilot.py`

- New `build_replay_command(gem5, outdir, probability=1.0)`: identical argv,
  but at `probability == 0.0` the FW02 carrier
  (`--chaos_lsqfwd --lsq_struct_mode f6_fw02 ...`) is omitted while
  `--chaos_propagation --prop_replay_all` stay on.
- New `--probability` (default `1.0`, preserves old behavior) and
  `--dry-run` (print command + write `command.txt`, skip gem5, exit 0).

### `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_v332_control_guards.py` (new)

12 tests: DA04 p0/p1, MD04 p0/p1, LQ04 p0/p1, FW02 p0/p1, other models'
controls unchanged, RP01 replay p0/p1, and three `--dry-run` cases driving
`run_pilot.main` against a **nonexistent** `--gem5` path (proves gem5 is not
invoked, and that the printed line equals `command.txt`).

## Verification (real command output)

Tests written first; pre-implementation run failed as expected:

```
$ python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_v332_control_guards.py -q
...
12 failed in 0.87s
```

Post-implementation:

```
$ python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_v332_control_guards.py -q
............                                                             [100%]
12 passed in 0.98s
```

No collateral breakage (full platform suite; 107 pre-existing tests + 12 new):

```
$ python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests -q
........................................................................ [ 60%]
...............................................                          [100%]
119 passed in 4.15s
```

`py_compile` on all three files: `PY_COMPILE_OK`.

### Dry-run command lines (p=0, quoted from stdout)

DA04:

```
/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/build/ARM/gem5.opt --outdir=/tmp/v332_dry_da04c /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/configs/se/lsu_proxy.py --cmd=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/docs/gem5-fi/lsu/implementation_v3_2/workloads/alignment --cpu O3 --variant B0 --probability 0.0 --chaos_propagation --prop_trace_file prop_trace.csv.gz
```

MD04:

```
/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/build/ARM/gem5.opt --outdir=/tmp/v332_dry_md04c /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/configs/se/lsu_proxy.py --cmd=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/docs/gem5-fi/lsu/implementation_v3_2/workloads/replay_dependency --cpu O3 --variant B0 --probability 0.0 --chaos_propagation --prop_trace_file prop_trace.csv.gz
```

Both exit `rc=0`; the only artifacts written are `<outdir>/command.txt`
(no `pilot_meta.json`, no `manifest.json`, no logs). Neither line carries any
injector flag (`--chaos_lsqfwd`, `--lsq_struct_mode`, `--chaos_md04`,
`--md04_*`) — the control is zero-injection by construction.

### Dry-run command lines (p=1, fault behavior preserved)

DA04 (injector present, unchanged flags):

```
.../gem5.opt --outdir=/tmp/v332_dry_da04f .../lsu_proxy.py --cmd=.../workloads/alignment --cpu O3 --variant B0 --probability 1.0 --chaos_propagation --prop_trace_file prop_trace.csv.gz --chaos_lsqfwd --lsq_struct_mode da04_be_bit0 --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 0 --lsqfwd_span_events 10 --max_faults 1 --rng_seed 4185444934 --lsqfwd_event_ordinal 1
```

MD04 (injector present, `--md04_probability 1.0` preserved):

```
.../gem5.opt --outdir=/tmp/v332_dry_md04f .../lsu_proxy.py --cmd=.../workloads/replay_dependency --cpu O3 --variant B0 --probability 1.0 --chaos_propagation --prop_trace_file prop_trace.csv.gz --chaos_md04 --md04_first_clock 0 --md04_max_faults 1 --md04_probability 1.0 --md04_rng_seed 2595563470 --md04_event_ordinal 1
```

RP01 replay pilot p=0 (carrier omitted) / p=1 (carrier present):

```
.../gem5.opt --outdir=/tmp/v332_dry_rp01c .../lsu_proxy.py --cmd=.../workloads/replay_dependency --cpu O3 --variant B0 --probability 0.0 --chaos_propagation --prop_trace_file replay_prop.csv.gz --prop_replay_all
.../gem5.opt --outdir=/tmp/v332_dry_rp01f .../lsu_proxy.py --cmd=.../workloads/replay_dependency --cpu O3 --variant B0 --probability 1.0 --chaos_propagation --prop_trace_file replay_prop.csv.gz --prop_replay_all --chaos_lsqfwd --lsq_struct_mode f6_fw02 --max_faults 1 --rng_seed 3135797961 --lsqfwd_event_ordinal 1
```

## Scope / honesty

- **No gem5 pilot was run.** This patch only changes runner command
  construction; the quoted p=0/p=1 lines above are `--dry-run` output, not
  simulator results. Whether DA04/MD04 controls and faults then grade
  `accepted` must still be established by real pilots.
- No `git add/commit/push` was performed by this agent.
- Fault-run command strings are unchanged by construction (same flag lists,
  same ordering), verified by diff review and the p=1 dry-run output above.

## Residual risks

1. **Other ordinal-gated selectors.** The fix is limited to DA04/MD04 (plus
   the pre-existing LQ04/FW02). SQ01/SQ03/SP05/FW05 are believed
   probability-gated at injector attach (pinned by a test that they keep the
   mount at p=0), but that belief rests on the injector sources; if any of
   those attach paths later drop the probability gate, its control misfires
   silently and would be caught only by `control_misfire`. A per-injector
   audit of the attach gate for every `*_lsq_struct_mode` would be the
   durable fix.
2. **`--dry-run` bypasses manifest/validation.** It prints what *would* run;
   it does not check that the binary/workload/Excel row are usable beyond
   what `main()` already computes before the early return (config load,
   workload path resolution, command construction). A failed workload path
   shows up only as an `--cmd=` path that gem5 would later reject.
3. **`run_replay_pilot --probability`** is a new CLI surface: a control run
   at p=0 produces no injection, so the current post-run acceptance
   (`len(replays) > 0 and ... COMPLETE`) is unaffected, but the summary's
   `activation`/`fault` fields still describe the FW02 carrier. Control-mode
   labelling for the replay pilot was out of scope for this patch.
4. No real control pilot has been re-graded, so zero-injection remains a
   command-level property here, not yet an observed simulator fact.
