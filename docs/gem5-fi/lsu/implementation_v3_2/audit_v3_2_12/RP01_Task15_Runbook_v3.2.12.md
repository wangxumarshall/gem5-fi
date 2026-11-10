# RP01 Task 15 Runbook — v3.2.12 (five skip pilots + five matched controls)

Prepared 2026-11-10 by the Task 15 prep agent (read-only on evidence; no gem5
run, no build, no commit was made by the preparer). Every command below uses a
`$GEM5` variable so the executor pins the binary the main agent rebuilt.

Inputs consumed:
`RP01_CountOnly_Preflight_v3.2.12.md` (5/5 seeds PASS, 5 distinct events each,
seed flag `--rng_seed`, identical stream across seeds),
`task-14-audit-report.md` (wake-up paths: a skipped load is never re-issued;
only squash or HANG),
`RP01_Final_Design_Gate_v3.2.11.md` (HANG/TIMEOUT is the defining risk; never
MASKED),
`configs/se/lsu_proxy.py` (flags `--chaos_lsqfwd --lsq_struct_mode
rp01_skip_replay --rp01_event_ordinal --rp01_watchdog_cycles --rng_seed`),
plan Task 15 Steps 4–6,
`docs/superpowers/plans/2026-11-10-lsu-v3-2-12-propagation-closure.md`.

---

## 0. Preconditions (all must hold before the first pilot)

| # | Gate | Command | Requirement |
|---|---|---|---|
| P1 | Binary pinned | `sha256sum "$GEM5"` | The executor MUST pin the rebuilt binary's SHA and record it in every pilot's `manifest.json` (`gem5.binary_sha256`) and in the run record. Never mix binaries across the 10 runs. |
| P2 | RP01 patch present | `"$GEM5" --help 2>&1 \| grep -c rp01_event_ordinal` | `1` (the flag exists). The binary must contain commit `512d937c` (RP01 hooks) or its descendant. |
| P3 | Trace support | (P2 binary) | If a run passes `--chaos_propagation`, the binary must be the trace-enabled rebuild (the preflight's `720eb780…` line is trace-enabled; `lsu_proxy.py` aborts loudly on older binaries). |
| P4 | Workload | `sha256sum "$PL/workloads/replay_dependency"` | `ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4` (the frozen W7). |
| P5 | Disk | `df -h /home` | >= 20 GiB free before every run (the preflight gate). |
| P6 | Slot | `pgrep -a gem5` | Zero other gem5 processes; run the 10 commands **sequentially, one at a time** (preflight discipline). |
| P7 | Unit + selector | `g++ -O2 -std=c++17 -Wall -Wextra -I CHAOS/gem5/src tests/test_rp01_selector.cc -o /tmp/test_rp01_selector && /tmp/test_rp01_selector` | `RP01_SELECTOR_OK` (already green at the patch commit; re-run only if the selector changed). |

## 1. Environment (define once per shell)

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
# The main agent pins the rebuilt binary here (repo-root build path):
export GEM5=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/build/ARM/gem5.opt
sha256sum "$GEM5"   # record this SHA; it goes into every manifest below

PL=docs/gem5-fi/lsu/implementation_v3_2
W=$PWD/$PL/workloads/replay_dependency        # frozen W7 workload
PILOTS=$PWD/$PL/pilots_v3_2_12                # new outdirs land here
CONV=$PL/platform/tools/prop_trace_to_v31.py # prop trace -> trace_v31.jsonl
WDT=20000000        # in-simulator watchdog cycles (see §2 note)
EXT_TIMEOUT=1800    # external timeout, seconds (see §2 note)
GOLDEN=59fc61c040618747                       # W7 golden checksum
```

**Watchdog value (`--rp01_watchdog_cycles 20000000`) — why 20M.** The clean
count-only stream's last eligible event is at cycle 97,206 (tick 37,424,310;
tick/cycle ratio 385 — preflight §3), and the workload completes shortly after
it. 20M cycles is >200x that span, so a SQUASHED (or otherwise completing) run
can never hit the watchdog, while a stalled run — whose pipeline is empty and
therefore cheap per cycle — reaches 20M quickly. It is the same value as plan
Task 15 Step 4's smoke, so the smoke's wall time directly calibrates the
pilots'. The **external timeout 1800 s** is the backstop: whichever fires first
defines the terminal (in-simulator watchdog `fatal` → **HANG**; external kill
→ **TIMEOUT**). Both are accepted RP01 terminals.

**Why `--chaos_propagation --prop_replay_all` on every run.** The partial-
coverage branch emits its `noteReplay` record *before* the guarded call, so the
skipped load's replay marker IS recorded even when the reschedule is skipped;
`--prop_replay_all` is required because the skipped load's seq is not in
`fault_seqs` (the count-only preflight ran without these flags and got no trace
— it did not need one). The trace also retains the load's squash record
(`noteReplay` trace-tracks the seq for its final commit/squash). Known gap at
prep time: the committed RP01 hook prints `RP01_SKIP_REPLAY` to stdout/log but
emits **no injection record into the prop trace** (no `noteRP01*` call in
`CHAOSLSQFwd.cc`; no `inj_rp01`/`rp01_skip` kind in the converter map). The
`replay` marker still lands on the chain via `noteReplay`; if the main agent's
rebuilt binary adds a dedicated skip/injection record, the same commands below
capture it unchanged. Record which case applies per binary SHA.

## 2. The five frozen contexts (from the preflight; verify each skip against this)

| Pilot | Ordinal | Seed | dyn_inst_seq | load PC | Tick | lq_idx/lq_gen | store_seq |
|---|---:|---:|---:|---|---:|---|---:|
| RP01-R01 | 1 | 3135797961 | 69341 | 0x4015fc | 31072965 | 9201/9693 | 69334 |
| RP01-R02 | 2 | 226489823  | 71013 | 0x42a6d8 | 35427700 | 9349/9915 | 71007 |
| RP01-R03 | 3 | 1735144973 | 71014 | 0x42a6dc | 35428085 | 9350/9916 | 71003 |
| RP01-R04 | 4 | 2455796178 | 72018 | 0x422a58 | 36564990 | 9427/10049 | 72000 |
| RP01-R05 | 5 | 3984724524 | 72350 | 0x44e2ec | 37424310 | 9467/10096 | 72346 |

The stream is seed-invariant (count-only mode never draws RNG), so the five
pilots differ by **ordinal**, not by seed-driven stream variation; the seeds
stay frozen for protocol reproducibility (SampleRunIDs `RP01-F6-W7-S01-R01..R05`).

## 3. Pilot commands (RP01-R01..R05)

One pilot per invocation, sequentially. Each writes a fresh outdir under
`pilots_v3_2_12/` and captures stdout + the real exit code (`timeout` returns
124 only for the external kill; the watchdog `fatal` exits 1).

```bash
# ---- RP01-R01 (ordinal 1, seed 3135797961) ----
OUT=$PILOTS/RP01-R01; mkdir -p "$OUT"
timeout "$EXT_TIMEOUT" "$GEM5" --outdir="$OUT" configs/se/lsu_proxy.py \
  --cpu O3 --chaos_lsqfwd --lsq_struct_mode rp01_skip_replay \
  --rp01_event_ordinal 1 --rp01_watchdog_cycles "$WDT" \
  --rng_seed 3135797961 \
  --chaos_propagation --prop_replay_all --prop_trace_file "$OUT/prop_trace.csv.gz" \
  --cmd="$W" >"$OUT/stdout.log" 2>&1
echo "exit=$?" | tee "$OUT/exit_code.txt"

# ---- RP01-R02 (ordinal 2, seed 226489823) ----
OUT=$PILOTS/RP01-R02; mkdir -p "$OUT"
timeout "$EXT_TIMEOUT" "$GEM5" --outdir="$OUT" configs/se/lsu_proxy.py \
  --cpu O3 --chaos_lsqfwd --lsq_struct_mode rp01_skip_replay \
  --rp01_event_ordinal 2 --rp01_watchdog_cycles "$WDT" \
  --rng_seed 226489823 \
  --chaos_propagation --prop_replay_all --prop_trace_file "$OUT/prop_trace.csv.gz" \
  --cmd="$W" >"$OUT/stdout.log" 2>&1
echo "exit=$?" | tee "$OUT/exit_code.txt"

# ---- RP01-R03 (ordinal 3, seed 1735144973) ----
OUT=$PILOTS/RP01-R03; mkdir -p "$OUT"
timeout "$EXT_TIMEOUT" "$GEM5" --outdir="$OUT" configs/se/lsu_proxy.py \
  --cpu O3 --chaos_lsqfwd --lsq_struct_mode rp01_skip_replay \
  --rp01_event_ordinal 3 --rp01_watchdog_cycles "$WDT" \
  --rng_seed 1735144973 \
  --chaos_propagation --prop_replay_all --prop_trace_file "$OUT/prop_trace.csv.gz" \
  --cmd="$W" >"$OUT/stdout.log" 2>&1
echo "exit=$?" | tee "$OUT/exit_code.txt"

# ---- RP01-R04 (ordinal 4, seed 2455796178) ----
OUT=$PILOTS/RP01-R04; mkdir -p "$OUT"
timeout "$EXT_TIMEOUT" "$GEM5" --outdir="$OUT" configs/se/lsu_proxy.py \
  --cpu O3 --chaos_lsqfwd --lsq_struct_mode rp01_skip_replay \
  --rp01_event_ordinal 4 --rp01_watchdog_cycles "$WDT" \
  --rng_seed 2455796178 \
  --chaos_propagation --prop_replay_all --prop_trace_file "$OUT/prop_trace.csv.gz" \
  --cmd="$W" >"$OUT/stdout.log" 2>&1
echo "exit=$?" | tee "$OUT/exit_code.txt"

# ---- RP01-R05 (ordinal 5, seed 3984724524) ----
OUT=$PILOTS/RP01-R05; mkdir -p "$OUT"
timeout "$EXT_TIMEOUT" "$GEM5" --outdir="$OUT" configs/se/lsu_proxy.py \
  --cpu O3 --chaos_lsqfwd --lsq_struct_mode rp01_skip_replay \
  --rp01_event_ordinal 5 --rp01_watchdog_cycles "$WDT" \
  --rng_seed 3984724524 \
  --chaos_propagation --prop_replay_all --prop_trace_file "$OUT/prop_trace.csv.gz" \
  --cmd="$W" >"$OUT/stdout.log" 2>&1
echo "exit=$?" | tee "$OUT/exit_code.txt"
```

## 4. Matched control commands (RP01-CONTROL-R01..R05)

Matched = same workload, same seed, **no `--chaos_lsqfwd`** (no injector at
all). Expected: exit 0 and the golden checksum `checksum=0x59fc61c040618747`
on every control. The prop-trace flags stay on so each control dir carries the
same artifact set (its trace will contain zero injection events — the honest
NO_INJECTION control record; a control is a determinism replication, never an
independent sample).

```bash
# ---- RP01-CONTROL-R01 (seed 3135797961) ----
OUT=$PILOTS/RP01-CONTROL-R01; mkdir -p "$OUT"
timeout "$EXT_TIMEOUT" "$GEM5" --outdir="$OUT" configs/se/lsu_proxy.py \
  --cpu O3 --rng_seed 3135797961 \
  --chaos_propagation --prop_replay_all --prop_trace_file "$OUT/prop_trace.csv.gz" \
  --cmd="$W" >"$OUT/stdout.log" 2>&1
echo "exit=$?" | tee "$OUT/exit_code.txt"

# ---- RP01-CONTROL-R02 (seed 226489823) ----
OUT=$PILOTS/RP01-CONTROL-R02; mkdir -p "$OUT"
timeout "$EXT_TIMEOUT" "$GEM5" --outdir="$OUT" configs/se/lsu_proxy.py \
  --cpu O3 --rng_seed 226489823 \
  --chaos_propagation --prop_replay_all --prop_trace_file "$OUT/prop_trace.csv.gz" \
  --cmd="$W" >"$OUT/stdout.log" 2>&1
echo "exit=$?" | tee "$OUT/exit_code.txt"

# ---- RP01-CONTROL-R03 (seed 1735144973) ----
OUT=$PILOTS/RP01-CONTROL-R03; mkdir -p "$OUT"
timeout "$EXT_TIMEOUT" "$GEM5" --outdir="$OUT" configs/se/lsu_proxy.py \
  --cpu O3 --rng_seed 1735144973 \
  --chaos_propagation --prop_replay_all --prop_trace_file "$OUT/prop_trace.csv.gz" \
  --cmd="$W" >"$OUT/stdout.log" 2>&1
echo "exit=$?" | tee "$OUT/exit_code.txt"

# ---- RP01-CONTROL-R04 (seed 2455796178) ----
OUT=$PILOTS/RP01-CONTROL-R04; mkdir -p "$OUT"
timeout "$EXT_TIMEOUT" "$GEM5" --outdir="$OUT" configs/se/lsu_proxy.py \
  --cpu O3 --rng_seed 2455796178 \
  --chaos_propagation --prop_replay_all --prop_trace_file "$OUT/prop_trace.csv.gz" \
  --cmd="$W" >"$OUT/stdout.log" 2>&1
echo "exit=$?" | tee "$OUT/exit_code.txt"

# ---- RP01-CONTROL-R05 (seed 3984724524) ----
OUT=$PILOTS/RP01-CONTROL-R05; mkdir -p "$OUT"
timeout "$EXT_TIMEOUT" "$GEM5" --outdir="$OUT" configs/se/lsu_proxy.py \
  --cpu O3 --rng_seed 3984724524 \
  --chaos_propagation --prop_replay_all --prop_trace_file "$OUT/prop_trace.csv.gz" \
  --cmd="$W" >"$OUT/stdout.log" 2>&1
echo "exit=$?" | tee "$OUT/exit_code.txt"
```

## 5. Per-run acceptance procedure (each of the 10 runs, in order)

Run these checks on every pilot and control before starting the next run
(keep one gem5 slot free until the whole batch is done).

**5.1 Pilot evidence checks** (fault pilots only):

```bash
OUT=$PILOTS/RP01-R01   # ...per run

# (a) exactly one skip line, matching the frozen context table (§2)
grep -c RP01_SKIP_REPLAY "$OUT/stdout.log"        # expected: 1
grep RP01_SKIP_REPLAY "$OUT/stdout.log"          # ordinal/load_seq/load_pc/lq_idx/lq_gen/store_seq/tick must equal the table row

# (b) pre-skip eligible line for the selected ordinal exists
grep RP01_ELIGIBLE "$OUT/stdout.log" | grep "ordinal=<N> "   # identity must match the table

# (c) watchdog evidence (HANG case)
grep -E "CHAOS_RP01_WATCHDOG" "$OUT/stdout.log" "$OUT/lsq_fwd_injections.log"   # EXPIRED + fired=1 injected=1

# (d) exit code semantics
cat "$OUT/exit_code.txt"    # 1 = watchdog fatal -> HANG; 124 = external cut -> TIMEOUT; 0 = completed (see 5.3)

# (e) checksum (a HANG/TIMEOUT run has NONE — that absence is expected; a completed run's checksum goes to 5.3)
grep -c "checksum=" "$OUT/stdout.log"

# (f) injector exit status
grep CHAOS_RP01_STATUS "$OUT/lsq_fwd_injections.log"        # fired=1 injected=1 eligible=<n>
```

Accept (pilot) when: (a) is exactly 1 and its identity equals the frozen
context; (c) or exit 124 supplies the terminal evidence; no SIGSEGV/panic
other than the watchdog fatal; the `config.ini` in the outdir shows
`rp01EventOrdinal=<N>`, `rp01WatchdogCycles=20000000`,
`rngSeed=<seed>` and `structMode=rp01_skip_replay`.

**5.2 Control acceptance**: `exit=0`, `checksum=0x59fc61c040618747` in
`stdout.log`, zero `RP01_` lines, zero `lsq_fwd_injections.log` injector
records, and `config.ini` differs from its pilot only in the injector flags.

**5.3 If a PILOT completes (exit 0)**: this is the design-falsification branch
(design gate §6: "A run that ends MASKED or SDC would falsify the predicted
mechanism and must be investigated, not celebrated"). Do **not** record it as
PASS/MASKED and do not proceed to the next ordinal:
- Compare the checksum against golden: equal → the skip was recovered by some
  path the task-14 audit refuted (P1–P6) — re-run that ordinal once to
  distinguish a flake from a mechanism; if it reproduces, STOP and escalate to
  the main agent with the full outdir: the design gate is falsified.
- Checksum differs → a data path the design says cannot exist (no SDC
  mechanism on this path) — STOP and escalate; never claim it as RP01 SDC.

## 6. Classification procedure (per pilot, after its acceptance)

The classifier is `tools/lsu_12model_closure.py record` (it reuses
`audit_pilot` → `terminal_rules.adjudicate`; never a forked classifier). The
RP01 support it needs (PROFILES entries for HANG/TIMEOUT/SQUASHED/UNRESOLVED,
the `rp01_skip` stage, and the RP01-scoped TIMEOUT guard) is already merged
and tested in this worktree — see §8.

**6.1 Write the run's meta + manifest** into the pilot dir (adapt the JSON
fields per run; the observed terminal comes from §5.1(d)/(c)):

```bash
OUT=$PILOTS/RP01-R01; ORD=1; SEED=3135797961
SHA=$(sha256sum "$GEM5" | cut -d' ' -f1)
# terminal: "HANG" (watchdog fatal exit 1, OR external cut exit 124 — see below)
#          | "SQUASHED" (completed + squash evidence) | "COMPLETED" -> §5.3, do NOT use
TERMINAL=HANG
RUNSTATUS=TIMEOUT     # run_status for a cut run; COMPLETED only for a finished run
# NOTE on the external cut (exit 124): "TIMEOUT" is a run_status, NOT a
# terminal_state (the trace TERMINAL enum has no TIMEOUT), so the trace
# summary is written with terminal HANG + terminal_reason
# RP01_EXTERNAL_TIMEOUT + run_status TIMEOUT; the meta below records the raw
# observed_terminal=TIMEOUT. The closure tool maps an observed TIMEOUT to
# ObservedTerminal=TIMEOUT and terminal_rules returns
# ("TIMEOUT", "RP01_EXTERNAL_TIMEOUT") for RP01 whenever the meta is the
# observed source — both HANG and TIMEOUT are accepted RP01 terminals.

cat > "$OUT/pilot_meta.json" <<EOF
{
  "pilot_id": "RP01-F6-W7-S01-R01",
  "model": "RP01",
  "run_type": "pilot",
  "seed": $SEED,
  "excel_identity": {"run_id": "RP01-F6-W7", "sub_task_id": "RP01-F6-W7-S01",
                      "sample_run_id": "RP01-F6-W7-S01-R01", "seed": $SEED,
                      "event_ordinal": $ORD, "event_ordinal_used": $ORD},
  "exit_code": 1,
  "injection_count": 1,
  "trace": {"validator_errors": [], "truncated": <true iff the prop trace is a truncated gz stream>},
  "classification": {
    "run_status": "$RUNSTATUS",
    "fault_activation_status": "TRIGGERED",
    "observed_terminal": "$TERMINAL",
    "terminal_state": "$TERMINAL",
    "trace_completeness": "<trace_v31.jsonl's declared completeness>",
    "oracle_outcome": "NOT_APPLICABLE"
  }
}
EOF

cat > "$OUT/manifest.json" <<EOF
{
  "schema_version": "lsu-run-manifest-v3.2",
  "sample_run_id": "RP01-F6-W7-S01-R01",
  "run_id": "RP01-F6-W7", "sub_task_id": "RP01-F6-W7-S01",
  "model_id": "RP01", "seed": $SEED,
  "fault": {"location": "LSQUnit::read() PartialAddrRangeCoverage rescheduleMemInst (lsq_unit.cc:2016)",
            "target_field": "replay trigger (skip one ordinal-selected call)",
            "event_ordinal": $ORD},
  "workload": {"sha256": "ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4"},
  "gem5": {"binary": "$GEM5", "binary_sha256": "$SHA"}
}
EOF
```

For a **SQUASHED** pilot (completed run with a squash of the skipped load):
add `oracle.log` — `expected=59fc61c040618747 got=59fc61c040618747` +
`ORACLE_PASS` — and set `oracle_outcome: "PASS"`, `exit_code: 0`,
`run_status: "COMPLETED"`. For **controls**: no injection exists; set
`injection_count: 0`, `observed_terminal: "COMPLETED"`, `oracle_outcome:
"PASS"`, and write the same two-line `oracle.log` from the golden checksum.

**6.2 Convert the prop trace** (the converter refuses a truncated stream as
COMPLETE for anything but CRASH — for a watchdog-fatal run that is the honest
outcome; let it declare INCOMPLETE and record that):

```bash
# terminal/run-status flags mirror 6.1; completeness: COMPLETE only if the
# gz stream ended cleanly, else the converter declares INCOMPLETE itself.
python3 "$CONV" "$OUT/prop_trace.csv.gz" "$OUT/trace_v31.jsonl" \
  --sample-run-id RP01-F6-W7-S01-R01 --run-id RP01-F6-W7 \
  --sub-task-id RP01-F6-W7-S01 --fault-id RP01-CFG01 --fault-model-id RP01 \
  --run-status "$RUNSTATUS" --activation TRIGGERED \
  --terminal "$TERMINAL" --completeness COMPLETE
sha256sum "$OUT/trace_v31.jsonl" > "$OUT/trace_v31.jsonl.sha256"
```

**6.3 Build the closure record** (the same invocation Task 16 will re-run):

```bash
python3 tools/lsu_12model_closure.py record --model RP01 \
  --pilot-dir "$PILOTS/RP01-R01" \
  --binary-sha "$SHA" \
  --json "$PL/audit_v3_2_12/RP01_records_v3.2.12.binary-$(echo "$SHA" | cut -c1-8).json"
```

Expected per pilot (with the RP01 profiles in place):
- **HANG pilot**: `ObservedTerminal=HANG`, `FaultCausality=PROVEN` (the
  identity-linked `replay`/`rp01_skip` marker on the fault's own chain),
  `StructuralChainCompleteness=COMPLETE` when the chain carries injection +
  marker, `FinalClassification=VERIFIED_SINGLE_CONTEXT` per pilot (the matrix
  upgrades to `COMPLETE_CAUSAL_CHAIN` only with >= 2 distinct complete
  contexts). If the binary lacks a trace injection record, the record honestly
  reports `NO_INJECTION_EVENT` in `MissingEvidence` and the FinalClassification
  caps at `UNRESOLVED` — the ObservedTerminal stays HANG; record the gap, do
  not paper over it (see prep report concern C1).
- **TIMEOUT pilot**: `ObservedTerminal=TIMEOUT`,
  `TerminalReason=RP01_EXTERNAL_TIMEOUT` — never MASKED.
- **SQUASHED pilot**: `ObservedTerminal=SQUASHED`, `FaultCausality=PARTIAL`
  (frozen v3.2.11 line: an unproven squash is never a complete verdict),
  `FinalClassification=PARTIAL`.
- **Control**: `ObservedTerminal=NO_INJECTION`, `ApplicationOracle=PASS`,
  `FinalClassification=UNRESOLVED` (a control is a replication, never an
  independent sample).

## 7. Expected terminal per pilot and the fallback

| Run | Expected terminal | Rationale |
|---|---|---|
| RP01-R01..R05 | **HANG/TIMEOUT** (primary) or **SQUASHED** (accepted alternative) | The task-14 wake-up audit proved the skipped load is never re-issued (P1–P4, P6): no writeback → no commit → the ROB head blocks forever → HANG; only an older squash discards the entry (P5). No SDC mechanism exists on this path. |
| RP01-CONTROL-R01..R05 | **COMPLETED**, checksum `0x59fc61c040618747`, zero injections | No injector attached; same seed/workload as the matched pilot. |

**Fallback if a pilot completes (exit 0)**: investigate, never celebrate — §5.3.
A completed pilot with the golden checksum falsifies the no-recovery proof
(design gate §6); a completed pilot with a wrong checksum falsifies the
no-data-path claim. Both STOP the batch and escalate with the full outdir.
A MASKED or SDC grade for RP01 must never be recorded from these pilots; the
classifier support merged with this runbook (TIMEOUT guard + hard HANG) makes
HANG/TIMEOUT win over any passing oracle by construction.

## 8. What the prep agent already merged (all additive, all tested)

- `trace_completeness.py`: `("RP01","HANG"/"TIMEOUT")` profiles
  `[(injection, replay), (injection, rp01_skip)]`; `("RP01","SQUASHED")`
  `[(injection, squash)]`; `("RP01","UNRESOLVED")` `[(injection,)]`;
  `DEFAULT_PROFILE["RP01"]`; `rp01_skip` added to the stage display list.
- `terminal_rules.py`: RP01-scoped `TIMEOUT` guard — `observed_terminal ==
  "TIMEOUT"` returns `("TIMEOUT", "RP01_EXTERNAL_TIMEOUT")` before any chain
  adjudication (model-scoped; no other model changed). HANG was already a
  hard terminal that beats a passing oracle.
- `tests/test_rp01_classification.py` (14 tests): synthetic HANG with a skip
  record -> HANG; passing-oracle HANG still HANG; external TIMEOUT never
  MASKED (even with commit + consumer + passing-oracle chain state);
  model-scoping pinned (LQ04 TIMEOUT adjudication unchanged); SQUASHED ->
  SQUASHED; no-commit chain never MASKED; profile/coverage checks; and the
  end-to-end closure records for HANG/TIMEOUT/SQUASHED pilots.

## 9. After the ten runs

1. Commit order (per plan Task 15 Step 6): source commits first (if the main
   agent changed C++), then the evidence commit with the ten pilot dirs +
   `RP01_Propagation_Audit_v3.2.12.md` + the records JSON. Stage explicit
   paths only — never `git add -A`.
2. Record `DecisionStatus=APPROVED_BY_RESEARCHER_V3.2.12` with the brief §7 as
   authority (main agent's step).
3. Regenerate the closure matrix (Task 16) — the RP01 rows appear only now.
