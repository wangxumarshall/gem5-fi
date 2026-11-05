# R6-P Unit Takeover #2 — P07-a formal, P04-F5 correction, diagnostic and coverage audit

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish every remaining executable R6-P-unit item without inventing coverage:
certify the P07-a submodel on P07-F0-W6 if strict admission passes, replace the
P04-F5 “whole-queue valid field” expansion with a fixed-slot permanent model,
audit the P07-c/P09 diagnostics, and reconcile the whole-unit evidence ledger.

**Architecture:** The P RunIDs stay the authoritative unit. Submodels are recorded
against the same RunID (P07-a and P07-b both land on P07-F0-W6), so a successful
P07-a run adds submodel evidence, not a new RunID. P04-F5 keeps one physical fault
identity but only one fixed logical queue slot; old evidence is preserved and
labelled superseded. Diagnostics remain non-RunID evidence with oracle `n/a`.

**Tech Stack:** vendored gem5 v25.1.0.1 (C++ / scons), Python campaign + chain
checker, pytest, directed SE workloads under `workloads/directed/`.

**Spec:** `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-03-位置x模型矩阵.md`
(rows P04/P07/P09), `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md` (F5 row),
`docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CENSUS.md`, and
`docs/gem5-fi/lsu/evidence/R6-P-{P04,P07,P09}-EVIDENCE.md`.

## Global Constraints

- Worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-p-unit-20261104`,
  branch `fix/r6-p-unit-20261104`. Never merge into `origin/fi-ding`
  (`f5055a99`) this round. Push every commit to the P branch.
- One commit per unit. Never `git add -A`; stage explicit paths.
- Host has ~42 GiB free and a 4-process gem5 cap. Reuse existing evidence first;
  run new gem5 only where this plan says the evidence is missing or superseded.
- No fabricated L5/SDC. A chain that stops at L1/L2/L4 is recorded as such.
- Seeds 1/2/3 are independent RNG draws only where the trigger has a span draw;
  deterministic F5 replicas are labelled “determinism replications”.
- Build with `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`; a build warning
  introduced by the change is a failure. Freeze the resulting binary under
  `runs/lsu/r6_p_unit/binaries/` and record source HEAD + SHA-256.
- Campaign binary selection: `LSU_GEM5_BIN=<worktree>/CHAOS/gem5/build/ARM/gem5.opt`.
- Regression baseline: `pytest tests -q` = **309 passed / 10 failed**, failure set
  = `test_lsu_r6a4_repeat_census`, `test_lsu_results_layout`, 8 ×
  `test_lsu_s_prop_docs`. New failure = 0.
- Baseline snapshot: HEAD `f0c0dcad`, clean tree, origin P branch same,
  `origin/fi-ding f5055a99`, no gem5 processes, 42 GiB free (verified 2026-11-05).

## Review Focus

- **P07-a data composition:** the response bytes must land in the partner way and
  the fill way must keep the partner’s old bytes; tags must stay put. A test must
  read both ways’ data and prove the swap, not just the log line.
- **P04-F5 one-bit identity:** the latch must invalidate exactly one live entry
  (one slot) and future entries in that slot only; every other entry must still
  issue. A test must prove non-struck entries are untouched.
- **Submodel vs RunID counting:** P07-a success must not change the RunID count
  from 14; it changes the submodel count. Tests/docs must state both numbers.
- **Diagnostic binary identity:** every cited diagnostic must resolve to a frozen
  binary SHA; when the historical build is gone, re-run with the frozen current
  binary and keep the old directory.
- **Stale prose:** CENSUS/CLOSEOUT/INDEX/STATE must no longer say P07-a/c or
  P09-b/c are “not implemented” once they are.

---

### Task 1: Campaign P07 submodel selector

**Files:**
- Modify: `tools/lsu_campaign.py` (`resolve_cell` signature, `build_parser`,
  `main` resolution audit, `run_single_cell`)
- Test: `tests/test_lsu_hook_p07.py`

**Interfaces:**
- Produces: `resolve_cell(..., p07_mode=None)` where `p07_mode` is one of
  `None`/`"tag"`/`"data"`/`"stale"`; the selected flag replaces the mounted
  P07 `--prefetch_mode` value.
- Produces: CLI `--p07-mode {tag,data,stale}`.

- [x] **Step 1: Write the failing test.** Append to `tests/test_lsu_hook_p07.py`
  before the final summary:

```python
def _matrix_p07_row():
    import csv, pathlib
    p = pathlib.Path(__file__).resolve().parents[1] / \
        "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv"
    with p.open() as f:
        return next(r for r in csv.DictReader(f) if r["RunID"] == "P07-F0-W6")

row = _matrix_p07_row()
for sub, mode in (("tag", "p07_fill_tag_mispair"),
                  ("data", "p07_data_way"),
                  ("stale", "p07_stale_tag")):
    flags, _g, _r = LC.resolve_cell(row, p07_mode=sub)
    check(f"campaign --p07-mode {sub} -> {mode}",
          flags[flags.index("--prefetch_mode") + 1] == mode, str(flags))
flags, _g, _r = LC.resolve_cell(row)
check("campaign default P07 mode unchanged (tag)",
      flags[flags.index("--prefetch_mode") + 1] == "p07_fill_tag_mispair",
      str(flags))
check("campaign parser exposes --p07-mode",
      "p07_mode" in LC.build_parser().parse_args(
          ["--matrix", "x", "--p07-mode", "data"]).__dict__)
```

- [x] **Step 2: Run it and confirm it fails.**
  `python3 tests/test_lsu_hook_p07.py` → FAIL (`unexpected keyword p07_mode`).

- [x] **Step 3: Implement the selector.**
  In `resolve_cell` add `p07_mode=None` to the signature. After
  `flags += extra` in the SE branch add:

```python
    # [R6-P-P07-A 2026-11-05] Submodel selector.  The RunID is shared by
    # P07-a/b/c; this replaces the mounted mode (argparse last-wins) so the
    # authoritative RunID can be exercised per submodel without inventing
    # new RunIDs.
    if model == "P07" and p07_mode:
        _p07_mode_value = {"tag": "p07_fill_tag_mispair",
                           "data": "p07_data_way",
                           "stale": "p07_stale_tag"}[p07_mode]
        _i = flags.index("--prefetch_mode")
        flags[_i + 1] = _p07_mode_value
```

  In `build_parser` add:

```python
    p.add_argument("--p07-mode", choices=["tag", "data", "stale"],
                   default=None,
                   help="[R6-P-P07-A] P07 submodel for this run: tag=P07-b "
                        "(default mount), data=P07-a, stale=P07-c. The "
                        "RunID stays P07-F0-Wn; submodel coverage is "
                        "recorded separately.")
```

  Pass `p07_mode=getattr(a, "p07_mode", None)` in `main()`'s resolution-loop
  `resolve_cell(...)` and `p07_mode=getattr(args, "p07_mode", None)` in
  `run_single_cell(...)`.

- [x] **Step 4: Run the tests.**
  `python3 tests/test_lsu_hook_p07.py` → ALL PASS.
  `python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --cells P07-F0-W6 --phase trial --p07-mode data --dry-run` → `runnable=1`.

- [x] **Step 5: Commit and push.**

```bash
git add tools/lsu_campaign.py tests/test_lsu_hook_p07.py
git commit -m "[LSU][MDSPEC][R6-P-P07][TOOLS] add campaign P07 submodel selector"
git push origin fix/r6-p-unit-20261104
```

---

### Task 2: Freeze the current P07-a/P07-c binary and run P07-a seed1

**Files:**
- Evidence only: `runs/lsu/r6_p_unit/binaries/gem5.opt-5b26240c`,
  `runs/lsu/r6_p_unit/campaign_p07a_formal_20261105/`
- No repo source change.

**Interfaces:**
- Consumes Task 1’s `--p07-mode data`.
- Produces: `campaign_p07a_formal_20261105/P07-F0-W6/cell_results.json` and
  per-seed `chain_report.json`.

- [x] **Step 1: Verify the build is the P07-c/P07-a tree and freeze it.**

```bash
sha256sum CHAOS/gem5/build/ARM/gem5.opt    # expect 5b26240c...
cp CHAOS/gem5/build/ARM/gem5.opt \
   /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/binaries/gem5.opt-5b26240c
sha256sum /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/binaries/gem5.opt-5b26240c
```

- [x] **Step 2: Run the seed1 strict-admission pilot only.**

```bash
export LSU_GEM5_BIN=$PWD/CHAOS/gem5/build/ARM/gem5.opt
python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/campaign_p07a_seed1_20261105 \
  --cells P07-F0-W6 --phase trial --p07-mode data \
  --max-seeds-per-cell 1 --seed-start 1 --max-parallel 1
```

- [x] **Step 3: Inspect strict admission.**
  Read `campaign_p07a_seed1_20261105/P07-F0-W6/cell_results.json` and
  `P07-F0-W6/seed1/chain_report.json`. Record the real `outcome`, `activated`,
  `admitted`, `certified`, `terminal`, `event_count`, `truncated`, and the
  guest output hash from `run.out`. Do **not** run seeds 2/3 unless
  `admitted=True` and `certified=True` and the terminal is `full`/L5.
  If admission fails, stop this task and record the first failed criterion.

- [x] **Step 4: If admitted, run all three seeds into the formal directory.**

```bash
python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/campaign_p07a_formal_20261105 \
  --cells P07-F0-W6 --phase trial --p07-mode data \
  --max-seeds-per-cell 3 --seed-start 1 --max-parallel 1
```

  Verify: 3 seeds, all admitted/certified, oracle Masked, `fires == injected +
  no_effect` where applicable, gzip/stats/exit OK, no truncation, and the
  output hash stays `062e5124df3667f9` (no SDC claim). Confirm the injection
  ticks are the two W6 eligible points (34086360 / 34091365) and that the
  faults are independent RNG draws.

- [x] **Step 5: Run the no-fault control with the same mode.** Use the exact
  command from Task 2 Step 2 with `--p07-mode data` and a warm-up beyond the
  run (`--prefetch_warmup_events 1000000000`) into
  `campaign_p07a_control_20261105`; confirm `injected=0` and golden
  `062e5124df3667f9` (or the W8 golden if W8 is also checked).

- [x] **Step 6: Record evidence.** The run directories live outside the repo.
  No commit in this task; Task 3 records the results in docs.

---

### Task 3: P07-a formal evidence and submodel coverage record

**Files:**
- Modify: `docs/gem5-fi/lsu/evidence/R6-P-P07-EVIDENCE.md`
- Modify: `docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CENSUS.md`
- Modify: `docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CLOSEOUT.md`
- Modify: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/INDEX.md` and `.json`
  (via the same conventions used by earlier rounds)
- Create per-seed docs: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/P07-F0-W6/`
  (name them `P07-F0-W6-p07a-seed{1,2,3}.md` so the P07-b docs are untouched)

**Interfaces:**
- Consumes the real Task 2 outputs.
- Produces: a submodel table row `P07-F0-W6` with `P07-b` and (if admitted)
  `P07-a`, while the RunID-level count stays 14.

- [x] **Step 1: Write the P07-a formal section** with the real seed values:
  injection tick, fill/partner set/way, `pf_data` event, terminal, admission,
  certification, oracle, output hash, event count, and the explicit statement
  “submodel coverage, not a new RunID; RunID count unchanged at 14”.
- [x] **Step 2: Add the submodel coverage table** to CENSUS: columns
  RunID | submodel | seeds | admitted/certified | oracle | terminal | binary.
  Mark P07-a NOT CERTIFIED if seed1 admission failed, and do not add seeds 2/3.
- [x] **Step 3: Correct stale prose** that says P07-a is unimplemented in the
  P07 sections of CENSUS/CLOSEOUT/INDEX; keep P07-c statements accurate
  (implemented but B0 coverage-blocked).
- [x] **Step 4: Verify links and counts.**

```bash
python3 tests/test_lsu_prop_doc_audit.py
python3 - <<'EOF'
import json, pathlib
p = pathlib.Path("/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/INDEX.json")
d = json.load(p.open())
print("P07 entries:", [e for e in d.get("runs", d) if "P07" in str(e)][:3])
EOF
```

- [x] **Step 5: Commit and push.**

```bash
git add docs/gem5-fi/lsu/evidence/R6-P-P07-EVIDENCE.md \
        docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CENSUS.md \
        docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CLOSEOUT.md
git commit -m "[LSU][MDSPEC][R6-P-P07][DOCS] record P07-a formal submodel result"
git push origin fix/r6-p-unit-20261104
```

---

### Task 4: P04-F5 fixed-slot permanent correction (C++)

**Files:**
- Modify: `CHAOS/gem5/src/mem/cache/prefetch/queued.hh`
- Modify: `CHAOS/gem5/src/mem/cache/prefetch/queued.cc`
- Modify: `CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetch.cc`
- Modify: `tests/test_lsu_hook_p04.py`

**Interfaces:**
- Produces: `DeferredPacket::chaosSlot` (allocation ordinal mod queue capacity).
- Produces: `Queued::chaosLatchQueueValidStuck(uint64_t fault_id, uint64_t pfid,
  std::vector<std::pair<Addr, Addr>> &invalidated)` — latches exactly one live
  entry’s slot, invalidates only entries in that slot, returns the count and
  fills `invalidated`.
- Produces: `Queued::chaosStuckSlot()` for the behavior log.

- [x] **Step 1: Update the failing test first.** Replace the section `[6]`
  assertions in `tests/test_lsu_hook_p04.py` with the fixed-slot contract:

```python
check("Queued 暴露 fixed-slot latch / stuck-active / slot",
      "size_t chaosLatchQueueValidStuck(uint64_t fault_id, "
      "uint64_t pfid,\n" in qhh2
      or "chaosLatchQueueValidStuck(uint64_t fault_id, uint64_t pfid," in qhh2,
      "missing F5 API")
check("每个 ready-queue entry 获得物理 slot 身份",
      "uint64_t chaosSlot = 0;" in qhh2
      and "chaosSlot = chaosEnqueueSeq++ % queueSize" in qcc2,
      "slot identity missing")
check("latch 只失效所选 slot（不是整个队列）",
      "chaosStuckSlot = chosen->chaosSlot;" in qcc2
      and "d.chaosSlot == chaosStuckSlot" in qcc2
      and "dpp.chaosSlot != chaosStuckSlot" in qcc2,
      "global-field expansion still present")
```

  Keep the existing single-physical-fault-id and no-recovery assertions.

- [x] **Step 2: Run the test and confirm it fails.**
  `python3 tests/test_lsu_hook_p04.py` → FAIL on the new fixed-slot checks.

- [x] **Step 3: Implement the slot model.**

  `queued.hh`: add after `chaosQueueValid`:

```cpp
        // [MDSPEC][R6-P-P04-a-F5-v2] Physical slot identity: the entry's
        // allocation ordinal modulo the queue capacity.  gem5's ready queue
        // is a std::list without fixed slots; this is the documented logical
        // analogue of a circular FIFO slot.  Default 0 and unused unless the
        // fixed-slot F5 model is latched.
        uint64_t chaosSlot = 0;
```

  Change the latch signature and add the accessor:

```cpp
    size_t chaosLatchQueueValidStuck(
        uint64_t fault_id, uint64_t pfid,
        std::vector<std::pair<Addr, Addr>> &invalidated);
    uint64_t chaosStuckSlot() const { return chaosStuckSlot; }
```

  Add private state:

```cpp
    uint64_t chaosStuckSlot = 0;
    uint64_t chaosEnqueueSeq = 0;
```

  `queued.cc`: replace the latch body:

```cpp
size_t
Queued::chaosLatchQueueValidStuck(
    uint64_t fault_id, uint64_t pfid,
    std::vector<std::pair<Addr, Addr>> &invalidated)
{
    invalidated.clear();
    auto chosen = pfq.end();
    for (auto it = pfq.begin(); it != pfq.end(); ++it) {
        if (it->chaosQueueValid) { chosen = it; break; }
    }
    if (chosen == pfq.end()) {
        chaosQueueValidStuck = false;
        return 0;
    }
    chaosQueueValidStuck = true;
    chaosStuckFaultId = fault_id;
    chaosStuckPfid = pfid;
    chaosStuckSlot = chosen->chaosSlot;
    size_t n = 0;
    for (auto &d : pfq) {
        if (d.chaosSlot == chaosStuckSlot && d.chaosQueueValid) {
            d.chaosQueueValid = false;
            invalidated.emplace_back(d.pfInfo.getAddr(), d.pfInfo.getPC());
            ++n;
        }
    }
    return n;
}
```

  In `chaosApplyStuckValid` add the slot gate after the active check:

```cpp
    if (dpp.chaosSlot != chaosStuckSlot)
        return;
```

  In `addToQueue`, immediately before the insertion branches (after the
  queue-full eviction block), assign the slot:

```cpp
    if (&queue == &pfq)
        dpp.chaosSlot = chaosEnqueueSeq++ % queueSize;
```

  `CHAOSPrefetch.cc`: replace the F5 `live` snapshot/registration with the
  latch output:

```cpp
            std::vector<std::pair<Addr, Addr>> invalidated;
            const size_t n = queue->chaosLatchQueueValidStuck(
                f5_ptag, f5_pfid, invalidated);
```

  and iterate `invalidated` (not `live`) when registering `pf_queue` events;
  include `{"slot", std::to_string(queue->chaosStuckSlot())}` and
  `"latch_invalidated=" << n << " slot=" << queue->chaosStuckSlot()` in the
  behavior log.  Remove the old `chaosCollectLiveEntries(live)` call from the
  F5 path (the API may stay for observation).

- [x] **Step 4: Build clean and freeze.**

```bash
cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt 2>&1 | tee /tmp/p04f5v2_build.log
test ${PIPESTATUS[0]} -eq 0 && ! grep -Ei 'warning:|error:' /tmp/p04f5v2_build.log
sha256sum build/ARM/gem5.opt
cp build/ARM/gem5.opt \
  /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/binaries/gem5.opt-<first8>
```

- [x] **Step 5: Run the P04 hook test.**
  `python3 tests/test_lsu_hook_p04.py` → ALL PASS (source checks; evidence
  checks for the new run may SKIP until Task 5).

- [x] **Step 6: Commit and push.**

```bash
git add CHAOS/gem5/src/mem/cache/prefetch/queued.hh \
        CHAOS/gem5/src/mem/cache/prefetch/queued.cc \
        CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetch.cc \
        tests/test_lsu_hook_p04.py
git commit -m "[LSU][MDSPEC][R6-P-P04][F5] correct permanent queue-valid fault to one fixed slot"
git push origin fix/r6-p-unit-20261104
```

---

### Task 5: P04-F5 three-seed re-run and evidence

**Files:**
- Evidence: `runs/lsu/r6_p_unit/campaign_p04f5_v2_20261105/` and
  `campaign_p04f5_v2_seed23_20261105/`
- Modify: `docs/gem5-fi/lsu/evidence/R6-P-P04-EVIDENCE.md`
- Modify: `docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CENSUS.md`,
  `R6-P-UNIT-CLOSEOUT.md`, `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/INDEX.md`

- [x] **Step 1: Re-census the eligible stream** with the new binary (W2, W8,
  same exact absolute command, warm-up 1, span 1e9). Confirm `attempted/eligible`
  and that each latch reports `entries` and `latch_invalidated`.
- [x] **Step 2: Run seeds 1/2/3** for `P04-F5-W2` and `P04-F5-W8` with the new
  frozen binary, `--max-seeds-per-cell 3`, `--max-parallel 1`. Run no-fault
  controls with the same mode and warm-up beyond the run.
- [x] **Step 3: Verify the real behavior.** For each seed record: latch tick,
  selected slot, `entries`, `latch_invalidated` (must be 1), the number of
  non-struck entries that still issue, the skipped stuck-slot entry, the
  terminal chain, admitted/certified (expected False), oracle (expected Masked),
  and the output hash (expected golden). Do not invent L3/L5.
- [x] **Step 4: Update the evidence doc.** Keep the old global-field section
  but prepend a clear banner:
  `SUPERSEDED (2026-11-05): the whole-queue valid-field latch was a semantic
  expansion; the fixed-slot v2 result below is the authoritative P04-F5
  evidence. Old evidence retained at campaign_p04f5_20261105.`
  Add the new binary SHA/source HEAD and the slot-model rationale.
- [x] **Step 5: Update CENSUS/CLOSEOUT/INDEX** with the corrected P04-F5 status
  (implemented, behavior-verified, still NOT certified if the chain is L2/Masked;
  RunID count unchanged).
- [x] **Step 6: Run regression and commit.**

```bash
pytest tests -q    # expect 309 passed / 10 failed, same set
git add docs/gem5-fi/lsu/evidence/R6-P-P04-EVIDENCE.md \
        docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CENSUS.md \
        docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CLOSEOUT.md
git commit -m "[LSU][MDSPEC][R6-P-P04][DOCS] re-run P04-F5 with fixed-slot semantics"
git push origin fix/r6-p-unit-20261104
```

---

### Task 6: P07-c / P09 diagnostic audit and frozen identity

**Files:**
- Create: `docs/gem5-fi/lsu/evidence/R6-P-DIAGNOSTIC-AUDIT.md`
- Modify: `R6-P-P07-EVIDENCE.md`, `R6-P-P09-EVIDENCE.md`
- Evidence: re-run `p09c_diag_l2small_*_v2_20261105` and
  `p07c_diag_l2small_*_v2_20261105` with the frozen 5b26240c binary only if
  the cited build binary is no longer hash-verifiable.

- [x] **Step 1: For each diagnostic pair (P09-a, P09-c, P07-c) verify**
  (a) the exact command and gem5 build in `run.out`, (b) the binary SHA against
  a frozen copy, (c) a no-fault control with the golden hash, (d) raw
  `prop_evt.txt.gz` events (`pf_wb`/`pf_dirty`/`pf_stale_tag`), (e) the guest
  output hash and the oracle (`n/a`), and (f) the lineage from the real fill
  event to the real `errant_commit`. Record PASS/GAP per item.
- [x] **Step 2: If a cited binary is not frozen** (P09-c `c8b0e25f` was
  overwritten by the P07-c build; P07-c `5b26240c` is frozen in Task 2),
  re-run the diagnostic with `gem5.opt-5b26240c` and the same 16 KiB command,
  writing a new `*_v2_20261105` directory. Keep the old directory and label
  it `BINARY NOT FROZEN — provenance gap`.
- [x] **Step 3: Write the audit table** with columns: diagnostic | RunID? |
  binary path | SHA verified? | control hash | fault hash | raw events |
  lineage | oracle | status. Explicitly state that non-B0 diagnostics are not
  RunIDs and do not count toward the 14/42.
- [x] **Step 4: Commit and push.**

```bash
git add docs/gem5-fi/lsu/evidence/R6-P-DIAGNOSTIC-AUDIT.md \
        docs/gem5-fi/lsu/evidence/R6-P-P07-EVIDENCE.md \
        docs/gem5-fi/lsu/evidence/R6-P-P09-EVIDENCE.md
git commit -m "[LSU][MDSPEC][R6-P-UNIT][DOCS] audit P07-c/P09 diagnostic provenance"
git push origin fix/r6-p-unit-20261104
```

---

### Task 7: Whole-unit coverage rebuild and stale-document corrections

**Files:**
- Create: `docs/gem5-fi/lsu/mdspec/R6-P-UNIT-COVERAGE-AUDIT.md`
- Modify: `R6-P-UNIT-CENSUS.md`, `R6-P-UNIT-CLOSEOUT.md`,
  `docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.{md,json}`,
  `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/INDEX.{md,json}`,
  `runs/lsu/RESULTS/CATALOG.tsv` (back up first, matching the established
  `.bak-20261105` convention), `R6P_UNIT_STATE.json`, `R6P_UNIT_PROGRESS.md`.

- [x] **Step 1: Rebuild the per-RunID table** for the 23 F0/F5 RunIDs from the
  authoritative CSV and the actual evidence JSONs. Columns: RunID | submodel |
  implemented | behavior-verified | diagnostic pilot | certified 3/3 | seeds |
  workload coverage | model expressible | asset present | evidence dir |
  binary SHA | status.
- [x] **Step 2: Recompute the counts independently** (do not copy): certified
  RunIDs, certified seeds, submodel certifications, diagnostics, blocked
  categories. State RunID-level and submodel-level counts separately. Expected
  floor: 14 RunIDs / 42 seeds, plus P07-a submodel evidence if Task 2 passed.
- [x] **Step 3: Reconcile CATALOG/INDEX/STATUS against the table.** Fix:
  - “P07-a/c not implemented” → P07-a implemented/certified-or-not; P07-c
    implemented but B0 coverage-blocked.
  - “P09-b/c not implemented” → P09-c implemented; P09-b MODEL_NOT_EXPRESSIBLE.
  - “P04-F5 semantic not established” → fixed-slot v2 evidence.
  - Any wrong date/commit/binary SHA or “contaminated commit = numeric error”
    phrasing.
- [x] **Step 4: Check link integrity and counts.**

```bash
python3 tests/test_lsu_prop_doc_audit.py
python3 tests/test_lsu_results_layout.py
python3 - <<'EOF'
import csv
rows = csv.DictReader(open("runs/lsu/RESULTS/CATALOG.tsv"), delimiter="\t")
p = [r for r in rows if r.get("run_id", "").startswith("P")]
print("P catalog rows:", len(p))
EOF
```

- [x] **Step 5: Commit and push** (docs only; evidence dirs stay outside git).

```bash
git add docs/gem5-fi/lsu/mdspec/R6-P-UNIT-COVERAGE-AUDIT.md \
        docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CENSUS.md \
        docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CLOSEOUT.md \
        docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.md \
        docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.json
git commit -m "[LSU][MDSPEC][R6-P-UNIT][DOCS] rebuild coverage audit and correct stale status"
git push origin fix/r6-p-unit-20261104
```

---

### Task 8: Final regression, state/progress closeout

**Files:**
- Modify: `R6P_UNIT_STATE.json`, `R6P_UNIT_PROGRESS.md` (in
  `/home/sdc/gem5-fi-ding-cleanup-20261029/`; repo keeps a copy if the earlier
  rounds did), `docs/superpowers/plans/2026-11-05-r6-p-unit-continuation.md`
  (append the takeover #2 result), and the P-branch docs index.

- [x] **Step 1: Run the full regression** `pytest tests -q`; record the exact
  pass/fail numbers and failure set; compare to baseline 309/10.
- [x] **Step 2: Run the focused hooks**: `test_lsu_hook_p04.py`,
  `test_lsu_hook_p07.py`, `test_lsu_hook_p09.py`, chain script, P06 hook; record
  pre-existing failures separately.
- [x] **Step 3: Re-verify HEAD/remote/disk/processes** and write the final
  STATE/PROGRESS with: certified RunIDs/seeds, submodel count, key fault paths,
  remaining blocks (P03-W9 bridge, P09 B0 coverage, P09-W13 asset, P09-b model,
  P07-W8 consumer), and the explicit “full P unit 53 RunIDs not complete”.
- [x] **Step 4: Commit and push.**

```bash
git add docs/superpowers/plans/2026-11-05-r6-p-unit-continuation.md
git commit -m "[LSU][MDSPEC][R6-P-UNIT][DOCS] close takeover #2 with verified counts"
git push origin fix/r6-p-unit-20261104
```

---

## Self-Review Notes

- P07-a is deliberately capped at the W6 RunID; W8 stays a real
  workload-consumption block and is not re-targeted.
- P07-a cannot increase the RunID count; Task 3 and Task 7 both state the
  RunID/submodel split.
- P04-F5’s fixed slot is a documented logical abstraction for a list-based
  queue; the old global-field evidence is retained, not rewritten.
- P09-a/c and P07-c stay diagnostics with oracle `n/a`; Task 6 never assigns
  them RunID credit.
- Every task ends with a real regression or focused test; no “assumed pass”.

---

## Execution record (2026-11-05)

- **Task 1** commit `c4216b11`: `--p07-mode {tag,data,stale}`; tests verify
  tag/data/stale mapping and the unchanged default. `test_lsu_hook_p07.py`
  ALL PASS.
- **Task 2** frozen `gem5.opt-5b26240c`; seed1 pilot
  `campaign_p07a_seed1_20261105`: admitted/certified True, full L5, Masked,
  268 events, output `062e5124df3667f9`. Formal
  `campaign_p07a_formal_20261105`: 3/3 admitted/certified, full L5,
  Masked, 268 events, output golden; seeds 1/3 tick 34086360, seed 2
  34091365. Control `injected=0`, golden. W8 probe seed1:
  `provable_to_L1_then_unknown`, admitted False, output golden.
- **Task 3** commit `a7ebdbbd`: P07 evidence + per-seed docs +
  CENSUS/CLOSEOUT/INDEX record P07-a as a submodel, not a new RunID.
- **Task 4** commit `a00ab5c7`: fixed-slot P04-F5; build clean
  (`/tmp/p04f5v2_build3.log`, binary `b2bf0cd3…`). The first diagnostic
  exposed a two-bit pre-clear bug; fixed with `chaosPeekLiveQueueEntry`.
- **Task 5** commit `be1ad3e0`: v2 evidence W2 slot 11 tick 148525300,
  W8 slot 28 tick 107286025, `entries=1 latch_invalidated=1`, other live
  entries issue, terminal L2, Masked, output golden, controls `injected=0`;
  old v1 evidence marked SUPERSEDED.
- **Task 6** commit `95a6df2e`: diagnostic audit. P09-a/P07-c PASS with
  frozen binaries; P09-c original binary not frozen, v2 re-run with
  `5b26240c` reproduced the same outputs.
- **Task 7** commit `9589a66d`: coverage audit (23 RunIDs: 14 certified /
  42 seeds, 15 submodel certifications, 3 diagnostics, 9 uncertified);
  stale global status P rows marked.
- **Task 8** `pytest tests -q` = **309 passed / 10 failed** (255.75s),
  identical failure set to baseline => NEW FAIL=0. P04/P07/P09 hook tests
  ALL PASS. State/progress updated; branch pushed; no merge to fi-ding.
