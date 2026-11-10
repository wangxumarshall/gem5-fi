# RUNBOOK v3.2.12 — FW02 / SQ01 / SQ03 / SP05 supplementary pilots + controls (Tasks 9 / 11 / 12 / 13)

**Status: PREPARED, NOT EXECUTED.** Nothing in this runbook has been run: no gem5
invocation, no pilot, no build. The main agent rebuilds the binary first (§0.2), pins
its SHA, then executes §4–§7 serially and audits per §8–§10.

Prepared 2026-11-10 in worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
(branch `lsu-platform-v3.2.12`, at prep time HEAD `512d937c`). Runner:
`docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py` (CLI verified this round
with `--help`; source read in full — every flag claim below cites it).

**Run count: 24** = 4 models × (5 FAULT contexts R01–R05 + 1 matched CONTROL C01).

---

## 0. Global conventions (define once, use everywhere)

```bash
WT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
PL=$WT/docs/gem5-fi/lsu/implementation_v3_2
RUNNER=$PL/platform/run_pilot.py
PILOTS=$PL/pilots_v3_2_12          # every new outdir lands under here
# THE binary variable — every command below takes it; nothing hardcodes the path:
GEM5=$WT/build/ARM/gem5.opt
cd "$WT"                            # run_pilot.py resolves --outdir against the caller's cwd
```

### 0.1 The binary is STALE until the main agent rebuilds

`sha256sum "$GEM5"` at prep time =
`e527f26af7c2661995f456a2c96695ff6b366d5d787351172947ed259fad04ed` — this binary
PREDATES the v3.2.12 trace commits (A01 `3d7b11c5`, A03 `ddaba767`, RP01 `512d937c`,
and the in-flight FW02/SQ01/SQ03/SP05 trace work whose files are currently uncommitted
in the worktree). It MUST NOT be used for these 24 runs. Required order:

1. Main agent lands/commits the Tasks 9/11/12/13 trace patches,
   `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt` (clean build; -j126 only for
   incremental), publish to the worktree-root `build/ARM/gem5.opt`,
2. record the new SHA: `sha256sum "$GEM5"` — this is the **pinned v3.2.12 pilot SHA**;
   every manifest produced below records the same value (asserted in §9),
3. only then start §4–§7.

### 0.2 Exit-code contract of run_pilot.py

`run_pilot.py` returns **0 iff the run is accepted** (`accepted` in `pilot_meta.json`;
`run_pilot.py:1028`). FAULT runs are accepted through the fault gate
(exit 0 + injection_count ≥ 1 + target-event proof + resolved terminal + validator
clean + trace COMPLETE); CONTROL runs through `run_roles.control_valid`
(exit 0 + oracle PASS + injection_count == 0 + COMPLETE + no validator errors).
Expected exit codes are per-run in §4–§7 (one control is expected to exit 1 — §7 note).

### 0.3 Workload-path resolution trap (read before editing any command)

`run_pilot.py:536-538` resolves a non-absolute `--workload` as
`WORKLOADS / <name>` where `WORKLOADS = $PL/workloads`. A repo-relative string such
as `docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212` would therefore
MIS-resolve to `$PL/workloads/docs/gem5-fi/.../sq_reload_v3212` (nonexistent). Use
either the **absolute path** (used in §5–§7) or the **bare name** `sq_reload_v3212`.
Never the repo-relative path.

Frozen workload identity (verified this round, in this worktree):

| artifact | sha256 | oracle (`.golden`) |
|---|---|---|
| `$PL/workloads/sq_reload_v3212` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` | `7df5034c23f3e703` |
| `$PL/workloads/sq_forward` (FW02's original workload) | `132a84f7f21be052bc1f2c9baf1c12d5bd3462aae03b1d42778c94e69b0af297` | `1f4cbf14327717df` |

The `sq_forward` SHA is byte-identical to the workload SHA recorded in every original
FW02 manifest — FW02 keeps its original workload with NO `--workload` override.

### 0.4 Seed and ordinal authority

Every seed/ordinal below was read this round from the **original pilots' own
`manifest.json` / `command.txt` / `pilot_meta.json`** (surviving copies inside the
round package zips, §1) and independently cross-checked against the frozen Excel
`gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx` (the runner's seed/ordinal
source, `run_pilot.py:48,516-524`) via `config_parser.load_config` — **all 20
seed/ordinal pairs agree in both sources**. The commands pass `--seed` and
`--event-ordinal` explicitly so the runs are pinned even if the Excel drifts later;
because the CLI value equals the Excel value, `manifest.seed_source` stays the Excel
provenance marker (no "pilot_cli_override" flag; `run_pilot.py:643-646`).

`--pilot-id` is deliberately the new SUPP id (`--preserve-sample-id` NOT used): the
manifest's `sample_run_id` becomes `SUPP-…`, the Excel row is retained inside the
manifest's sample copy, and no formal sample is overwritten (the A01-plan convention).

---

## 1. Original identities and where the evidence survives

`pilots_v3_2_1/ … pilots_v3_2_9/` no longer exist on disk (verified: `find` over
`/home/sdc/gem5-fi-ding` + `git log --all` — never committed). The originals survive
only inside the round packages in worktree
`.claude/worktrees/lsu-platform-v3.2`:

| model | surviving original (authoritative for seed/ordinal/flags) | also cross-confirmed by |
|---|---|---|
| FW02 | `LSU_v3.2.3_Propagation_Closure_Package.zip` → `package_staging_v323/evidence/pilots_v3_2_3/sweep/FW02-R01..R05/{command.txt,manifest.json,pilot_meta.json}` (all five contexts, run_pilot-generated) | v3.2.11 package `C_Audit/PILOT_EVIDENCE_INDEX.csv` (`pilots_v3_2_1/FW02-R01,R04,R05` seeds 2941542370/527667424/3622278636); v3.2.4 zip rejudge copies `pilots_v3_2_4/FW02-R01,R05` |
| SQ01 | `LSU_v3.2.4_DA04_Implementation_Package.zip` → `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/SQ01-R01..R05/` | v3.2.11 `PILOT_EVIDENCE_INDEX.csv` `SQ01_v3_2_3` extraction (same five seeds); v3.2.3 zip `pilots_v3_2_3/SQ01-R01..R05` |
| SQ03 | `LSU_v3.2.8_FW05_ConfigFreeze_SQ03_Pilot_Package.zip` → `LSU_v3.2.8_PACKAGE/B_SQ03/pilots/SQ03-R01..R05/` (original outdir was `pilots_v3_2_8/…`) | v3.2.11 index (`SQ03_v3_2_8`, binary `b988b750…`); v3.2.9 zip `B_SQ03/original/` copies |
| SP05 | `LSU_v3.2.9_SP05_Implementation_SQ03_Propagation_FW05_Closure_Package.zip` → `LSU_v3.2.9_PACKAGE/A_SP05/pilots/SP05-R01..R05/` (original outdir was `pilots_v3_2_9/…`) | v3.2.11 index (`SP05_v3_2_9`, binary `303c610d…`) |

**Honesty note on the task prompt's `pilots_v3_2_6/ (FW02)`:** no `pilots_v3_2_6`
directory survives anywhere (disk or git). The v3.2.11 supplementary plan shows
`pilots_v3_2_6/` held **DA04**-R04/R05 (raw-oracle gap), not FW02. The complete
five-context FW02 originals survive only as the v3.2.3-package copies quoted above
(their seeds/ordinals match the v3.2.1 evidence-index rows 1/4/5 and the v3.2.4
rejudge 1/5 exactly), so **FW02's original context is fully recoverable — no
NEEDS_ORIGINAL_CONTEXT entry is required for any of the four models.**

Original per-context identity (context index = Excel row = `--context-index`):

| ctx | FW02 seed / ordinal | SQ01 seed / ordinal | SQ03 seed / ordinal | SP05 seed / ordinal |
|---|---|---|---|---|
| R01 | 2941542370 / 1 | 591611458 / 1 | 2214819981 / 1 | 1489155957 / 1 |
| R02 | 2129071279 / 2 | 576447973 / 2 | 1486471869 / 2 | 1290498198 / 2 |
| R03 | 1336081385 / 3 | 1257175390 / 3 | 3102670938 / 3 | 2768710389 / 3 |
| R04 | 527667424 / 4 | 3116972755 / 4 | 3974203372 / 4 | 2741073922 / 4 |
| R05 | 3622278636 / 5 | 172636228 / 5 | 729970077 / 5 | 4098160626 / 5 |

Original flags reproduced 1:1 by `run_pilot.py`'s per-model `extra` list
(`run_pilot.py:550-620`; identical to each original `command.txt`):

- FW02 (`:618-620`): `--chaos_lsqfwd --lsq_struct_mode f6_fw02 --max_faults 1 --rng_seed <S> --lsqfwd_event_ordinal <N>`
- SQ01 (`:562-567`): `--chaos_lsqfwd --lsq_struct_mode sq01_bit3 --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 0 --lsqfwd_span_events 10 --max_faults 1 --rng_seed <S> --lsqfwd_event_ordinal <N>`
- SQ03 (`:589-594`): `--chaos_lsqfwd --lsq_struct_mode sq03_canwb --max_faults 1 --rng_seed <S> --lsqfwd_event_ordinal <N> --sq03_watchdog_cycles 500000000`
- SP05 (`:595-600`): `--chaos_lsqfwd --lsq_struct_mode sp05_complete --max_faults 1 --rng_seed <S> --sp05_event_ordinal <N> --sp05_watchdog_cycles 500000000`
- common (`:622-627`): `--cpu O3 --variant B0 --probability <P> --chaos_propagation --prop_trace_file prop_trace.csv.gz`

Original SampleRunIDs (for provenance tables in the audit docs): FW02 `PILOT-FW02-R0N`
(v3.2.3 sweep; v3.2.4 rejudge `FW02-R01/R05-v324`), SQ01 `SQ01-R0N-v324`,
SQ03 `SQ03-F0-W3-S02-R0N`, SP05 `SP05-F6-W6-S01-R0N`.

---

## 2. Run inventory (24)

| # | run id | model | role | ctx | seed | ordinal | workload | expected exit |
|---|---|---|---|---|---|---|---|---|
| 1–5 | SUPP-FW02-R01..R05 | FW02 | FAULT | 1–5 | see §1 | 1–5 | sq_forward (original, no override) | 0 |
| 6 | SUPP-FW02-C01 | FW02 | CONTROL | 1 | 2941542370 | 1 | sq_forward | **1 (expected misfire, §7n)** |
| 7–11 | SUPP-SQ01-R01..R05 | SQ01 | FAULT | 1–5 | see §1 | 1–5 | sq_reload_v3212 (override) | 0 |
| 12 | SUPP-SQ01-C01 | SQ01 | CONTROL | 1 | 591611458 | 1 | sq_reload_v3212 | 0 |
| 13–17 | SUPP-SQ03-R01..R05 | SQ03 | FAULT | 1–5 | see §1 | 1–5 | sq_reload_v3212 (override) | 0 |
| 18 | SUPP-SQ03-C01 | SQ03 | CONTROL | 1 | 2214819981 | 1 | sq_reload_v3212 | 0 |
| 19–23 | SUPP-SP05-R01..R05 | SP05 | FAULT | 1–5 | see §1 | 1–5 | sq_reload_v3212 (override) | 0 |
| 24 | SUPP-SP05-C01 | SP05 | CONTROL | 1 | 1489155957 | 1 | sq_reload_v3212 | 0 |

Control context: R01 for every model (the earliest activation/ordinal position; the
same convention as the accepted A01 plan's `SUPP-A01-C01`). A no-injection control
has no ordinal semantics — the carried seed only needs bookkeeping fidelity; the
main agent may substitute another context if the audits need the reference elsewhere,
keeping seed + workload matched to that context's fault run.

---

## 3. Pre-flight (all gates must pass BEFORE the first run; re-check per run)

**3.1 One-shot gates (before the batch):**

```bash
cd "$WT"
# (a) Disk red line: admission-guard line is 70.6 GiB free on the fs holding the outdirs
df -BG "$WT" | awk 'NR==2 {gsub("G","",$4); if ($4+0 < 70.6) {print "FAIL: only "$4"G free (<70.6G)"; exit 1} print "df OK: "$4"G free"}'
# (b) Binary is the rebuilt one, SHA recorded (§0.1): must NOT be e527f26a…
sha256sum "$GEM5" | tee "$PL/audit_v3_2_12/RUNBOOK_v3.2.12.binary_sha.txt"
# (c) Frozen workload identity intact:
sha256sum "$PL/workloads/sq_reload_v3212"          # expect bcab9cc5e1e4ed38...
sha256sum "$PL/workloads/sq_forward"               # expect 132a84f7f21be052...
cat "$PL/workloads/sq_reload_v3212.golden"          # expect 7df5034c23f3e703
```

**State at prep time (honest):** (a) FAILS — 67G free on `/home` (< 70.6G). The main
agent must free space (or get an explicit researcher waiver) before running; this is
the same admission line that refused the v3.2.9 claim-concurrency tests.

**3.2 Per-run pre-flight (repeat before EACH run):**

```bash
# (d) no >2 concurrent gem5 processes (hard cap 2 for this batch; CLAUDE.md's 4 is the
#     global ceiling, this runbook is stricter). Simplest compliance: run serially.
[ "$(pgrep -c -f gem5.opt || true)" -le 2 ] || { echo "FAIL: >2 gem5.opt running"; exit 1; }
# (e) new outdir — never reuse/overwrite (supplementary runs corroborate, never replace)
test ! -e "$PILOTS/<RUN-ID>" || { echo "FAIL: $PILOTS/<RUN-ID> already exists"; exit 1; }
# (f) binary unchanged since batch start:
sha256sum "$GEM5"   # must equal the value recorded in 3.1(b) for every one of the 24 runs
```

---

## 4. FW02 commands (Task 9) — original workload, contexts R01–R05 + control

Run serially, in order; each command is one `run_pilot.py` invocation (the runner
writes `command.txt`, `manifest.json`, `pilot_meta.json`, `stdout.log`, `stderr.log`,
`oracle.log`, `prop_trace.csv.gz`, `trace_v31.jsonl` into the outdir).

```bash
# --- FW02 FAULT runs (expected exit 0) -------------------------------------
python3 "$RUNNER" --model FW02 --context-index 1 --pilot-id SUPP-FW02-R01 \
  --seed 2941542370 --event-ordinal 1 \
  --outdir "$PILOTS/SUPP-FW02-R01" --gem5 "$GEM5"
python3 "$RUNNER" --model FW02 --context-index 2 --pilot-id SUPP-FW02-R02 \
  --seed 2129071279 --event-ordinal 2 \
  --outdir "$PILOTS/SUPP-FW02-R02" --gem5 "$GEM5"
python3 "$RUNNER" --model FW02 --context-index 3 --pilot-id SUPP-FW02-R03 \
  --seed 1336081385 --event-ordinal 3 \
  --outdir "$PILOTS/SUPP-FW02-R03" --gem5 "$GEM5"
python3 "$RUNNER" --model FW02 --context-index 4 --pilot-id SUPP-FW02-R04 \
  --seed 527667424 --event-ordinal 4 \
  --outdir "$PILOTS/SUPP-FW02-R04" --gem5 "$GEM5"
python3 "$RUNNER" --model FW02 --context-index 5 --pilot-id SUPP-FW02-R05 \
  --seed 3622278636 --event-ordinal 5 \
  --outdir "$PILOTS/SUPP-FW02-R05" --gem5 "$GEM5"

# --- FW02 matched control (see the §7 FW02 note — expected exit 1) ---------
python3 "$RUNNER" --model FW02 --context-index 1 --pilot-id SUPP-FW02-C01 \
  --seed 2941542370 --event-ordinal 1 --probability 0.0 \
  --outdir "$PILOTS/SUPP-FW02-C01" --gem5 "$GEM5"
```

Predicted terminals (same workload + unchanged fault semantics; the v3.2.12 changes
are read-only trace additions — **any drift is a regression to investigate**, not a
relabel): R01 `SQUASHED` (v3.2.4 rejudge), R02 `CRASH` (v3.2.3 sweep, oracle FAIL),
R03 `MASKED` (v3.2.3 sweep), R04 `MASKED` + the only COMPLETE_CAUSAL_CHAIN
(v3.2.11 adjudication), R05 `SQUASHED` (v3.2.4 rejudge). Expected evidence per the
task-9 brief: ≥2 contexts with `decision=suppressed, memory_path=1, consumer edge`;
every squash carries a recorded `squash_reason`; fault-caused squashes classify
`SQUASHED`, never `PARTIAL`.

## 5. SQ01 commands (Task 11) — workload override `sq_reload_v3212`

```bash
SQRELOAD=$PL/workloads/sq_reload_v3212     # absolute; see the §0.3 trap — never pass the repo-relative path

python3 "$RUNNER" --model SQ01 --context-index 1 --pilot-id SUPP-SQ01-R01 \
  --seed 591611458 --event-ordinal 1 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ01-R01" --gem5 "$GEM5"
python3 "$RUNNER" --model SQ01 --context-index 2 --pilot-id SUPP-SQ01-R02 \
  --seed 576447973 --event-ordinal 2 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ01-R02" --gem5 "$GEM5"
python3 "$RUNNER" --model SQ01 --context-index 3 --pilot-id SUPP-SQ01-R03 \
  --seed 1257175390 --event-ordinal 3 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ01-R03" --gem5 "$GEM5"
python3 "$RUNNER" --model SQ01 --context-index 4 --pilot-id SUPP-SQ01-R04 \
  --seed 3116972755 --event-ordinal 4 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ01-R04" --gem5 "$GEM5"
python3 "$RUNNER" --model SQ01 --context-index 5 --pilot-id SUPP-SQ01-R05 \
  --seed 172636228 --event-ordinal 5 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ01-R05" --gem5 "$GEM5"

# --- SQ01 matched control (expected exit 0) --------------------------------
python3 "$RUNNER" --model SQ01 --context-index 1 --pilot-id SUPP-SQ01-C01 \
  --seed 591611458 --event-ordinal 1 --probability 0.0 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ01-C01" --gem5 "$GEM5"
```

Expected evidence per the task-11 brief: exactly 1 `lsq_write_sq_entry` bit-3
injection per fault run; on the reload workload the store→drain→reload→consumer
chain must be completable — ≥2 contexts with `mem_write_hash == hash(data_after)`,
`reload_data_hash == mem_write_hash`, `consumer_hash == reload_data_hash`; terminal
honestly `SDC` or `MASKED` per the checksum; if no reload consumer exists for a
context, record `STORE_COMMITTED_LANE_NOT_READ` — never manufacture one. The manifest
records the new `WorkloadSHA256` (`bcab9cc5…`) and the oracle comes from
`sq_reload_v3212.golden` (`7df5034c23f3e703`; `run_pilot.py:634-642,668-674`).
Original terminals (old workload, for contrast only — the workload change is the
point): all five MASKED/PASS, LIFECYCLE_ONLY, no consumer.

## 6. SQ03 commands (Task 12) — workload override `sq_reload_v3212`

```bash
python3 "$RUNNER" --model SQ03 --context-index 1 --pilot-id SUPP-SQ03-R01 \
  --seed 2214819981 --event-ordinal 1 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ03-R01" --gem5 "$GEM5"
python3 "$RUNNER" --model SQ03 --context-index 2 --pilot-id SUPP-SQ03-R02 \
  --seed 1486471869 --event-ordinal 2 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ03-R02" --gem5 "$GEM5"
python3 "$RUNNER" --model SQ03 --context-index 3 --pilot-id SUPP-SQ03-R03 \
  --seed 3102670938 --event-ordinal 3 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ03-R03" --gem5 "$GEM5"
python3 "$RUNNER" --model SQ03 --context-index 4 --pilot-id SUPP-SQ03-R04 \
  --seed 3974203372 --event-ordinal 4 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ03-R04" --gem5 "$GEM5"
python3 "$RUNNER" --model SQ03 --context-index 5 --pilot-id SUPP-SQ03-R05 \
  --seed 729970077 --event-ordinal 5 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ03-R05" --gem5 "$GEM5"

# --- SQ03 matched control (expected exit 0) --------------------------------
python3 "$RUNNER" --model SQ03 --context-index 1 --pilot-id SUPP-SQ03-C01 \
  --seed 2214819981 --event-ordinal 1 --probability 0.0 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SQ03-C01" --gem5 "$GEM5"
```

Expected evidence per the task-12 brief: exactly 1 `inj_sq03` canWB 0→1 per fault
run (`assert(injected==1)` in-simulator); outcome is EITHER a real drain/visibility
difference with a reload consumer OR an honest `LIFECYCLE_ONLY` +
`reason=NO_DOWNSTREAM_EFFECT` (the v3.2.9 probe already showed early `_canWB` cannot
make data visible earlier: identical checksum + 136 identical forwarding decisions).
A field change alone is never propagation. Originals (old workload): all five
MASKED/PASS, LIFECYCLE_ONLY, `consumer_instructions=0`; R01 WB ~9,240 ticks early,
R05 ~385.

## 7. SP05 commands (Task 13) — workload override `sq_reload_v3212`

```bash
python3 "$RUNNER" --model SP05 --context-index 1 --pilot-id SUPP-SP05-R01 \
  --seed 1489155957 --event-ordinal 1 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SP05-R01" --gem5 "$GEM5"
python3 "$RUNNER" --model SP05 --context-index 2 --pilot-id SUPP-SP05-R02 \
  --seed 1290498198 --event-ordinal 2 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SP05-R02" --gem5 "$GEM5"
python3 "$RUNNER" --model SP05 --context-index 3 --pilot-id SUPP-SP05-R03 \
  --seed 2768710389 --event-ordinal 3 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SP05-R03" --gem5 "$GEM5"
python3 "$RUNNER" --model SP05 --context-index 4 --pilot-id SUPP-SP05-R04 \
  --seed 2741073922 --event-ordinal 4 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SP05-R04" --gem5 "$GEM5"
python3 "$RUNNER" --model SP05 --context-index 5 --pilot-id SUPP-SP05-R05 \
  --seed 4098160626 --event-ordinal 5 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SP05-R05" --gem5 "$GEM5"

# --- SP05 matched control (expected exit 0) --------------------------------
python3 "$RUNNER" --model SP05 --context-index 1 --pilot-id SUPP-SP05-C01 \
  --seed 1489155957 --event-ordinal 1 --probability 0.0 --workload "$SQRELOAD" \
  --outdir "$PILOTS/SUPP-SP05-C01" --gem5 "$GEM5"
```

Expected evidence per the task-13 brief: exactly 1 `sp05_complete` per fault run
(`completed_before=0`, `stores_to_wb` −1, `mem_sent=0`); commit ≠ visibility —
record both ticks; premature completion with correct data classifies `MASKED` with
`MaskingMechanism=DATA_WRITTEN_CORRECTLY`; a visibility change with a reload consumer
must produce a data chain. Originals (old workload `store_path`): all five
MASKED/PASS, LIFECYCLE_ONLY, `PROPAGATION_VERIFIED=0`.

**§7n — FW02 control note (the one expected exit-1).** Source-verified this round:
`F6Fw02` attaches **even at probability 0** on purpose (`CHAOSLSQFwd.cc:134-137`,
"this mode suppresses a forwarding match"), and `maybeSuppressForwarding`
(`CHAOSLSQFwd.cc:1020-1035`, called at `lsq_unit.cc:1786`) is gated ONLY by
`f6_event_ordinal`/`max_faults` — no probability check. The SUPP-FW02-C01 command
above will therefore suppress one forward, record `injection_count=1`,
`control_misfire: true`, and exit 1 (`run_roles.py`: "reachable for ordinal-gated
injectors run with --probability 0.0"). This is the platform's honest role-exclusive
rejection — **do not "fix" or relabel it**; keep the record as evidence that FW02 is
ordinal-gated. If the FW02 audit needs a true no-fault reference on `sq_forward`
(the memory-response/hash reference for the store data), take the A03/LQ04 control
precedent instead — a direct gem5 invocation with the injector mount omitted,
seed carried, e.g.:

```bash
mkdir -p "$PILOTS/SUPP-FW02-CONTROL-REF"   # reference run, NOT a run_pilot control record
"$GEM5" --outdir="$PILOTS/SUPP-FW02-CONTROL-REF" "$WT/configs/se/lsu_proxy.py" \
  --cmd="$PL/workloads/sq_forward" --cpu O3 --variant B0 --probability 0.0 \
  --chaos_propagation --prop_trace_file prop_trace.csv.gz
```

SQ01/SQ03/SP05 controls are structurally safe: SQ01's `cpu->lsqFwd` attach block
requires `probability > 0` for `Sq01Bit3` (`CHAOSLSQFwd.cc:81`; hook call guarded at
`lsq_unit.cc:2121-2125`), and SQ03/SP05 gate their selectors on
`probability <= 0.0f` explicitly (`CHAOSLSQFwd.cc:736-737`, `:538`). All three
controls must exit 0 with `control_valid: true` — a misfire there IS a defect.

---

## 8. Post-run acceptance (per run, after it finishes)

For every one of the 24 runs, all of the following must hold (all readable from
`pilot_meta.json`; run_pilot.py's exit code already encodes most of them):

1. **Exit code** — 0 for all runs except SUPP-FW02-C01 (expected 1, §7n).
2. **Injection count** — FAULT runs: `injection_count >= 1` (FW02: `suppressed == 1`;
   SQ01: one `lsq_write_sq_entry` event; SQ03: one `inj_sq03` row; SP05: one
   `sp05_complete` row). CONTROL runs: `injection_count == 0` (except SUPP-FW02-C01,
   which honestly records the misfire).
3. **Raw oracle evidence present on disk** — `oracle.log`, `stdout.log`,
   `stderr.log` exist and are non-empty in the outdir. These are git-ignored
   (`.gitignore:18`, `*.log`) — **force-add** them at commit time (§10).
4. **Trace complete** — `classification.trace_completeness == "COMPLETE"` and
   `trace.validator_errors == []`; `trace.truncated == false`.
5. **Terminal honest** — fault runs: a resolved terminal (`MASKED`/`SDC`/`SQUASHED`/
   `CRASH` per the adjudication, never `UNRESOLVED` without a reason); controls:
   honestly `UNRESOLVED`/`NO_INJECTION_EVENT`, never relabeled `MASKED`.
6. **Manifest identity** — `manifest.json.seed == §1 seed for that context` and
   `pilot_meta.json.excel_identity.event_ordinal_used == the context ordinal`
   (mechanized in §9).
7. **Control validity** (controls only) — `run_role == "CONTROL"`;
   `control_valid == true` (SQ01/SQ03/SP05); `control_misfire == false`;
   `oracle_pass == true` against the workload's `.golden`.

A run that fails its gate is NOT re-run silently: record the failure, diagnose (e.g.
watchdog expiry sets `SIMULATOR_ERROR`/`HANG`), fix, then re-run into a NEW outdir
(`SUPP-…-R0N-r2`) — never overwrite (§3.2e).

## 9. Seed/identity verification (mechanized check for ALL 24 runs)

Run after all 24 runs complete, from `$WT`. Verifies every produced manifest seed
against the original manifests' seeds (transcribed in §1 from the zips' own
`manifest.json` files this round), the control seed carriage, the ordinal actually
used, and the workload SHA for the override models. Exits non-zero on any mismatch.

```bash
python3 - <<'EOF'
import json, sys
from pathlib import Path
BASE = Path("docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12")
SEEDS = {  # run id -> (model, context, original seed, original event_ordinal)
 "SUPP-FW02-R01":("FW02",1,2941542370,1), "SUPP-FW02-R02":("FW02",2,2129071279,2),
 "SUPP-FW02-R03":("FW02",3,1336081385,3), "SUPP-FW02-R04":("FW02",4,527667424,4),
 "SUPP-FW02-R05":("FW02",5,3622278636,5), "SUPP-FW02-C01":("FW02",1,2941542370,1),
 "SUPP-SQ01-R01":("SQ01",1,591611458,1),  "SUPP-SQ01-R02":("SQ01",2,576447973,2),
 "SUPP-SQ01-R03":("SQ01",3,1257175390,3), "SUPP-SQ01-R04":("SQ01",4,3116972755,4),
 "SUPP-SQ01-R05":("SQ01",5,172636228,5),  "SUPP-SQ01-C01":("SQ01",1,591611458,1),
 "SUPP-SQ03-R01":("SQ03",1,2214819981,1), "SUPP-SQ03-R02":("SQ03",2,1486471869,2),
 "SUPP-SQ03-R03":("SQ03",3,3102670938,3), "SUPP-SQ03-R04":("SQ03",4,3974203372,4),
 "SUPP-SQ03-R05":("SQ03",5,729970077,5),  "SUPP-SQ03-C01":("SQ03",1,2214819981,1),
 "SUPP-SP05-R01":("SP05",1,1489155957,1), "SUPP-SP05-R02":("SP05",2,1290498198,2),
 "SUPP-SP05-R03":("SP05",3,2768710389,3), "SUPP-SP05-R04":("SP05",4,2741073922,4),
 "SUPP-SP05-R05":("SP05",5,4098160626,5), "SUPP-SP05-C01":("SP05",1,1489155957,1),
}
WLSHA = {"SQ01":"bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6",
         "SQ03":"bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6",
         "SP05":"bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6",
         "FW02":"132a84f7f21be052bc1f2c9baf1c12d5bd3462aae03b1d42778c94e69b0af297"}
bad = 0
binshas = set()
for rid, (model, ctx, seed, ordinal) in sorted(SEEDS.items()):
    d = BASE / rid
    mf = d / "manifest.json"
    if not mf.exists():
        print(f"MISSING {mf}"); bad += 1; continue
    m = json.loads(mf.read_text())
    pm = json.loads((d / "pilot_meta.json").read_text()) if (d/"pilot_meta.json").exists() else {}
    errs = []
    if m.get("seed") != seed:
        errs.append(f"manifest.seed={m.get('seed')} != original {seed}")
    if pm and pm.get("seed") != seed:
        errs.append(f"pilot_meta.seed={pm.get('seed')} != original {seed}")
    used = (pm.get("excel_identity") or {}).get("event_ordinal_used")
    if used is not None and used != ordinal:
        errs.append(f"event_ordinal_used={used} != original {ordinal}")
    wl = m.get("workload") or {}
    if wl.get("sha256") != WLSHA[model]:
        errs.append(f"workload.sha256={wl.get('sha256')} != frozen {WLSHA[model][:16]}…")
    if m.get("binary_sha256"): binshas.add(m["binary_sha256"])  # manifest.py:130 (top level; "binary" is the path string)
    print(("BAD " if errs else "OK  ") + rid + ("" if not errs else " :: " + "; ".join(errs)))
    bad += bool(errs)
if len(binshas) != 1:
    print(f"BAD  binary SHA not uniform across runs: {sorted(binshas)}"); bad += 1
else:
    print(f"OK   uniform binary SHA256: {binshas.pop()}")
print("SEED VERIFICATION:", "FAIL" if bad else "PASS (24/24)")
sys.exit(1 if bad else 0)
EOF
```

Optional deep cross-check of the §1 table itself against the zip originals (no pilots
needed; run from anywhere; the zips live in worktree `lsu-platform-v3.2`):

```bash
Z=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2
for r in 1 2 3 4 5; do
  unzip -p "$Z/LSU_v3.2.3_Propagation_Closure_Package.zip" \
    "package_staging_v323/evidence/pilots_v3_2_3/sweep/FW02-R0$r/manifest.json" \
    | python3 -c "import json,sys; m=json.load(sys.stdin); print('FW02-R0$r', m['seed'])"
  unzip -p "$Z/LSU_v3.2.4_DA04_Implementation_Package.zip" \
    "docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4/SQ01-R0$r/manifest.json" \
    | python3 -c "import json,sys; m=json.load(sys.stdin); print('SQ01-R0$r', m['seed'])"
  unzip -p "$Z/LSU_v3.2.8_FW05_ConfigFreeze_SQ03_Pilot_Package.zip" \
    "LSU_v3.2.8_PACKAGE/B_SQ03/pilots/SQ03-R0$r/manifest.json" \
    | python3 -c "import json,sys; m=json.load(sys.stdin); print('SQ03-R0$r', m['seed'])"
  unzip -p "$Z/LSU_v3.2.9_SP05_Implementation_SQ03_Propagation_FW05_Closure_Package.zip" \
    "LSU_v3.2.9_PACKAGE/A_SP05/pilots/SP05-R0$r/manifest.json" \
    | python3 -c "import json,sys; m=json.load(sys.stdin); print('SP05-R0$r', m['seed'])"
done
```

## 10. Recording and commit discipline (after §8/§9 pass)

```bash
# One record invocation per model, binary SHA = the pinned rebuilt SHA (§0.1 step 2):
B=$(sha256sum "$GEM5" | cut -d' ' -f1)
for M in FW02 SQ01 SQ03 SP05; do
  python3 tools/lsu_12model_closure.py record --model "$M" \
    --pilot-dir "$PILOTS/SUPP-$M-R01" --pilot-dir "$PILOTS/SUPP-$M-R02" \
    --pilot-dir "$PILOTS/SUPP-$M-R03" --pilot-dir "$PILOTS/SUPP-$M-R04" \
    --pilot-dir "$PILOTS/SUPP-$M-R05" --pilot-dir "$PILOTS/SUPP-$M-C01" \
    --json "$PL/audit_v3_2_12/${M}_pilot_records_v3.2.12.json" \
    --binary-sha "$B"
done
```

Commit source and evidence separately (one patch per unit, per repo discipline). The
pilot directories contain git-ignored `*.log` files — stage each run directory
explicitly with `git add -f` (force past `.gitignore:18`); never `git add -A`:

```bash
git add -f "$PILOTS/SUPP-FW02-R01"   # ... repeat per run directory
```

## 11. Concerns and honesty notes

1. **Disk below the red line at prep time**: 67G free on `/home` < 70.6G (§3.1a).
   Free space (or waive explicitly) before starting; SQ03/SP05 traces ran ~197 MB
   `trace_v31.jsonl` per pilot on the old workloads — budget ≥5 GiB for the batch.
2. **The named `pilots_v3_2_6/` (FW02) does not survive** — the complete FW02
   originals are the v3.2.3-package copies (§1); seeds/ordinals are corroborated by
   three independent records (v3.2.3 sweep, v3.2.11 evidence index, v3.2.4 rejudge).
3. **FW02's control is an expected misfire** (§7n) — keep the honest record; use the
   direct-gem5 reference run if the audit needs a no-fault baseline on `sq_forward`.
4. **Workload-relative-path trap** (§0.3): absolute path or bare name only.
5. **Outdir location**: this runbook puts all SUPP runs under
   `$PL/pilots_v3_2_12/` (what the committed-structure closure runbook's P1 gate and
   the A03 task-8 plan expect). The A01 pilot plan §3 instead wrote
   `<WT>/pilots_v3_2_12/…` (worktree root) — reconcile before running so all SUPP
   families (A01/A03/FW02/SQ01/SQ03/SP05/RP01) land in ONE place;
   `lsu_12model_closure.py record` takes explicit `--pilot-dir` args, so either root
   works mechanically, but Task 16's gate text names `$PL/pilots_v3_2_12/`.
6. **Terminal drift on FW02** (same workload) ⇒ investigate, never relabel (§4).
   On SQ01/SQ03/SP05 the workload CHANGED by design — terminals are expected to
   differ from the originals; the acceptance is the brief's chain rule, not the
   original terminal.
7. **Timeouts**: default 900 s per run is generous (originals: FW02 1.6–3.3 s,
   SQ03 ~7.7 s wall in pilot_meta).
8. **Concurrency**: run serially, or cap at 2 concurrent gem5 processes (§3.2d);
   the batch is 24 runs and each is short.
9. **Never overwrite**: a failed/repeated run goes to a NEW outdir (§8); historical
   pilots are read-only evidence (they survive only inside the zips).
10. **The sq_reload_v3212 ordinal space differs from the original workloads'** —
    `--event-ordinal N` still selects the Nth eligible event, but that is now the
    Nth event of the NEW workload's stream. That is the intended preserved-context
    semantics (same Excel row); it is NOT a reproduction of the original event site.
