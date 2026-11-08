# LSU v3.2.8 — FW05 Config Freeze + Workload Archive + SQ03 Safety/Pilots

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze `fw05_forward` as FW05's formal workload with a reproducible archive and no-fault baselines, publish Excel v3.2.3 with only the five FW05 rows changed, then harden SQ03 (one-shot + hard cap + watchdog + timeout) and run its five formal pilots with a real trace.

**Architecture:** Work on branch `lsu-platform-v3.2.8` in the existing `lsu-platform-v3.2` worktree (base `f26218f8`). Workflow A is configuration/archive/baseline work; Workflow B adds a one-shot guard, bounded injection, an in-simulator watchdog and runner timeout handling to SQ03, plus `inj_sq03`/`sq03_wb`/`sq03_complete` trace nodes and store-chain consumer attribution. Shared trace tools are modified once, in the task that owns the change.

**Tech Stack:** gem5 v25.1.0.1 AArch64 vendored tree, scons, C++17, Python 3.11, openpyxl, JSONL Trace v3.1, gzip CSV.

**Spec:** Researcher's v3.2.8 work order (quoted in `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.8_Work_Order.md`) plus `FW05_Definition_Freeze_v3.2.7.md` and `SQ03_Definition_Freeze_v3.2.7.md`.

## Global Constraints

- Base v3.2.7 (`f26218f8`); do not modify v3.2.7 branch/package/history.
- No 60-sample formal run.
- Do not change the 12 models, 60 SampleRunID/RunID/SubTaskID/Seed.
- Only FW05's five Excel rows may change in v3.2.3; other 11 models and all 60 identities stay cell-identical.
- `ConfigFrozen` stays `NO` for all 60 (Warm-up/ROI not confirmed).
- Keep historical W8 alignment configuration and all v3.2.7 pilots/traces.
- Never `git clean -fd`; never `git add -A`; stage explicit paths.
- One patch per unit; each task = one commit; verify with real commands before commit.
- Report `n/a`/`NOT_TRIGGERED`/`HANG`/`TIMEOUT` honestly; never a silent zero or fabricated pass.

## Review Focus

1. **Archive provenance.** The archive must contain the exact binary with SHA256 `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf` used by all five v3.2.7 pilots, and a rebuild script whose output is either byte-identical or explicitly documented as behaviorally equivalent (never silently different).
2. **Per-seed no-fault oracle.** R02–R05 fail the oracle only because of SDC; a no-fault run with the same seed/workload must pass. A golden copied from another seed is not acceptable if outputs differ.
3. **SQ03 unbounded injection.** `max_faults=0` means unlimited; SQ03 must clamp to 1 and have an independent one-shot flag. A hook that merely "was called" is not proof of one injection.
4. **HANG/TIMEOUT honesty.** A watchdog/timeout must preserve partial trace/logs and must never be reported as MASKED. Terminal classification must distinguish HANG/TIMEOUT/CRASH from a completed run.
5. **SQ03 trace identity.** Store allocation → canWB → writeback → completion → later load/consumer must be linked by real dyn seq / SQ entry / generation, not by address alone.

---

### Task 1: v3.2.8 branch, work-order copy, baseline

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.8_Work_Order.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/GIT_BASELINE_v328.txt`
- Modify: this plan file.

**Interfaces:** none.

- [x] **Step 1: Branch and baseline**

```bash
git checkout -b lsu-platform-v3.2.8
{ echo "base: f26218f8"; git rev-parse HEAD; sha256sum build/ARM/gem5.opt; } \
  > docs/gem5-fi/lsu/implementation_v3_2/GIT_BASELINE_v328.txt
```

- [x] **Step 2: Copy the researcher work order verbatim** into `LSU_v3.2.8_Work_Order.md` and add a one-line provenance note.

- [x] **Step 3: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.8_Work_Order.md \
        docs/gem5-fi/lsu/implementation_v3_2/GIT_BASELINE_v328.txt \
        docs/superpowers/plans/2026-11-08-lsu-v328-fw05-configfreeze-sq03.md
git commit -m "[LSU][MDSPEC][V3.2.8][DOCS] start v3.2.8 from v3.2.7 and record work order"
git push -u origin lsu-platform-v3.2.8
```

---

### Task 2: FW05 workload archive with exact SHA provenance

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/src/fw05_forward.c`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/bin/fw05_forward`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/build.sh`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/run_pilot.sh`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/golden/fw05_forward.golden`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/README.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/PROVENANCE.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/SHA256SUMS`
- Test: `tests/test_fw05_archive.py`

**Interfaces:**
- Produces: archive root; exact binary SHA `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf`.

- [x] **Step 1: Write the failing provenance test**

```python
import hashlib, json
from pathlib import Path

ROOT = Path("docs/gem5-fi/lsu/implementation_v3_2")
ARCH = ROOT / "FW05_Workload_Archive"
PILOTS = ROOT / "pilots_v3_2_7"

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def test_archive_binary_is_exact_pilot_binary():
    assert sha(ARCH / "bin/fw05_forward") == \
        "0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf"

def test_all_five_manifests_use_the_same_workload():
    shas = set()
    for d in sorted(PILOTS.glob("FW05-R0*")):
        shas.add(json.loads((d / "manifest.json").read_text())["workload"]["sha256"])
    assert shas == {"0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf"}

def test_archive_has_required_parts():
    for rel in ("src/fw05_forward.c", "bin/fw05_forward", "build.sh",
                "run_pilot.sh", "golden/fw05_forward.golden", "README.md",
                "PROVENANCE.md", "SHA256SUMS"):
        assert (ARCH / rel).is_file(), rel
```

- [x] **Step 2: Run it to verify failure**

Run: `python3 -m pytest tests/test_fw05_archive.py -q`
Expected: FAIL (archive missing).

- [x] **Step 3: Build the archive**

Copy the exact v3.2.7 source/binary/golden. `PROVENANCE.md` must state:
- all five v3.2.7 manifests record `0cf40509...` (full hash),
- current archive binary hash equals that exact value,
- source hash `c79b4be9ee11cffbc5ca986eb418bcc9aad439429191140f4c92ca9347dfdfa4`,
- compile command `gcc -O2 -static fw05_forward.c -o fw05_forward`, host `aarch64`, gcc version captured,
- input data: none (arrays are initialized in the source; no external input file),
- golden/checksum method: program prints `checksum=0x<16 hex>`; golden is `0x67afad307642983e`; host and gem5 outputs agree,
- the archive binary is the original; a rebuild may differ in build-id bytes, so behavior is verified by checksum and the SHA of the archived binary is authoritative.

`build.sh`:

```bash
#!/bin/sh
set -e
cd "$(dirname "$0")"
gcc -O2 -static src/fw05_forward.c -o fw05_forward.rebuilt
./fw05_forward.rebuilt
sha256sum fw05_forward.rebuilt || true
```

`run_pilot.sh`:

```bash
#!/bin/sh
set -e
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
"$ROOT/build/ARM/gem5.opt" --outdir="${1:?outdir}" \
  "$ROOT/configs/se/lsu_proxy.py" \
  --cmd="$ROOT/docs/gem5-fi/lsu/implementation_v3_2/workloads/fw05_forward" \
  --cpu O3 --variant B0 --probability=1.0 --chaos_propagation \
  --prop_trace_file prop_trace.csv.gz --chaos_lsqfwd \
  --lsq_struct_mode fw05_older_src --max_faults 1 \
  --rng_seed "${2:-1025137124}" --lsqfwd_event_ordinal "${3:-1}"
```

`SHA256SUMS` is generated with `find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum`.

- [x] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_fw05_archive.py -q`
Expected: 3 passed.

- [x] **Step 5: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive \
        tests/test_fw05_archive.py
git commit -m "[LSU][MDSPEC][V3.2.8][FW05] archive exact fw05_forward workload with SHA provenance"
git push
```

---

### Task 3: FW05 per-seed no-fault baselines

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/baselines/`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_8/FW05_no_fault_baselines.csv`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/FW05_No_Fault_Baselines_v3.2.8.md`

**Interfaces:**
- Consumes: Task 2 archive.
- Produces: one baseline row per FW05 R01–R05 seed.

- [x] **Step 1: Run five no-fault baselines** with the same workload, seed and injection disabled but the injector attached:

```bash
for pair in "R01 1025137124" "R02 1653118510" "R03 2442802213" \
            "R04 899944922" "R05 2836530945"; do
  set -- $pair
  out="docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/baselines/$1"
  rm -rf "$out"; mkdir -p "$out"
  build/ARM/gem5.opt --outdir="$out" configs/se/lsu_proxy.py \
    --cmd=$PWD/docs/gem5-fi/lsu/implementation_v3_2/workloads/fw05_forward \
    --cpu O3 --variant B0 --probability=0.0 --chaos_lsqfwd \
    --lsq_struct_mode byte_flip --max_faults 0 --rng_seed "$2" \
    > "$out/stdout.log" 2>&1
  echo "$1 exit=$? checksum=$(grep -o 'checksum=0x[0-9a-f]*' "$out/stdout.log")"
done
```

- [x] **Step 2: Build the CSV** with columns: pilot, sample_run_id, seed, workload_sha256, binary_sha256, exit_code, golden_checksum, actual_checksum, oracle_pass, stdout_path. Golden is `0x67afad307642983e`; all five must pass.

- [x] **Step 3: Compare with the five pilots** and record in the doc: the pilot workload SHA equals the archive SHA, so the historical pilot runs are reused; no pilot rerun is needed for provenance, but R02–R05 remain SDC and R01 MASKED.

- [x] **Step 4: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/baselines \
        docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_8/FW05_no_fault_baselines.csv \
        docs/gem5-fi/lsu/implementation_v3_2/FW05_No_Fault_Baselines_v3.2.8.md
git commit -m "[LSU][MDSPEC][V3.2.8][FW05] add per-seed no-fault baselines"
git push
```

---

### Task 4: Excel v3.2.3 with only the FW05 five rows changed

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.3.xlsx`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/excel/FW05_CONFIG_v3.2.3.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/excel/FW05_OLD_NEW_DIFF_v3.2.3.md`
- Create: `tools/build_lsu_v323_workbook.py`
- Test: `tests/test_lsu_v323_workbook.py`

**Interfaces:**
- Consumes: v3.2.2 workbook.
- Produces: authoritative v3.2.3 workbook + CSV.

- [x] **Step 1: Write the failing test**

```python
import openpyxl
SRC="docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.2.xlsx"
DST="docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.3.xlsx"

def test_only_fw05_rows_changed():
    a=openpyxl.load_workbook(SRC,data_only=True)["5.60个样本执行矩阵"]
    b=openpyxl.load_workbook(DST,data_only=True)["5.60个样本执行矩阵"]
    fw=[r for r in range(2,a.max_row+1) if str(a.cell(r,5).value)=="FW05"]
    assert len(fw)==5
    for r in range(2,a.max_row+1):
        for c in range(1,a.max_column+1):
            if a.cell(r,c).value!=b.cell(r,c).value:
                assert r in fw,(r,c)
    for r in range(2,a.max_row+1):
        for c in (1,2,3,4):
            assert a.cell(r,c).value==b.cell(r,c).value
    for r in fw:
        assert "fw05_forward" in b.cell(r,19).value
        assert b.cell(r,20).value=="0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf"
        assert b.cell(r,22).value=="67afad307642983e"
        assert b.cell(r,38).value=="NO"
```

- [x] **Step 2: Verify RED** (`FileNotFoundError`), then write `tools/build_lsu_v323_workbook.py` that:
  - loads v3.2.2 preserving styles,
  - updates only FW05 rows: FaultLocation, TargetField, BitEntryByteIndex, NormalValue, FaultValue, InjectionTiming, FaultDuration, TargetInstruction, EligibleEventCondition, WorkloadPath, BinarySHA256, Oracle, ExecutionStatus (`PILOT_RUN_ACCEPTED`), RunStatus (`PILOT_RUN`), FaultActivationStatus (`TRIGGERED`), TerminalState_v31 per pilot, TraceCompleteness_v31 (`COMPLETE`), DecisionStatus (`FROZEN_FW05_WORKLOAD`), v3.2_ConfigProvenance (append revision text),
  - updates the FW05 row of sheets 3/4,
  - adds `15.FW05配置冻结` with WorkloadName `fw05_forward`, all 11 required fields, old/new table and reasons 1–5,
  - appends sheet 12 change log,
  - writes the 60×43 CSV.

- [x] **Step 3: Generate and verify**

```bash
python3 tools/build_lsu_v323_workbook.py
python3 -m pytest tests/test_lsu_v323_workbook.py -q
```
Expected: pass.

- [x] **Step 4: Point the pilot runner at v3.2.3 (for future runs only; v3.2.7 results stay frozen)** in `run_pilot.py` `EXCEL`, and verify `config_parser` loads it.

- [x] **Step 5: Commit**

```bash
git add tools/build_lsu_v323_workbook.py tests/test_lsu_v323_workbook.py \
  docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.3.xlsx \
  docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv \
  docs/gem5-fi/lsu/implementation_v3_2/excel/FW05_CONFIG_v3.2.3.md \
  docs/gem5-fi/lsu/implementation_v3_2/excel/FW05_OLD_NEW_DIFF_v3.2.3.md \
  docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py
git commit -m "[LSU][MDSPEC][V3.2.8][EXCEL] publish v3.2.3 with fw05_forward frozen"
git push
```

---

### Task 5: SQ03 max_faults audit + one-shot + hard cap + watchdog

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py`
- Modify: `configs/se/lsu_proxy.py`
- Test: `tests/test_sq03_rules.cc`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/SQ03_Safety_Audit_v3.2.8.md`

**Interfaces:**
- Produces: `bool sq03Fired() const`; `uint64_t sq03_watchdog_cycles`; watchdog exit message `CHAOS_SQ03_WATCHDOG_EXPIRED`.

- [x] **Step 1: Audit `max_faults`** by `grep -n "max_faults" CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`; document that `max_faults==0` means unlimited and is unsafe in SQ03.

- [x] **Step 2: Extend the unit test**

```cpp
assert(!shouldSetCanWB(100, 100, 0, 1));
assert(shouldSetCanWB(100, 100, 0, 1));
assert(!shouldSetCanWB(100, 100, 1, 0)); // hard cap clamps 0 to 1
```

Update `shouldSetCanWB` to clamp `max_faults==0` to 1.

- [x] **Step 3: Implement one-shot and hard cap**

In `CHAOSLSQFwd`: add `bool sq03_fired=false;`. In `maybeSetCanWB`:

```cpp
const uint64_t cap = (max_faults == 0) ? 1 : 1;  // SQ03 is one-shot
if (sq03_fired || faults_injected_count >= cap) return false;
...
sq03_fired = true;
++faults_injected_count;
assert(faults_injected_count == 1);
```

In the constructor/startup, if `struct_mode == Sq03CanWB`:

```cpp
if (p.sq03WatchdogCycles)
    exitSimLoop("CHAOS_SQ03_WATCHDOG_EXPIRED", 1, 0, p.sq03WatchdogCycles);
```

Add param `sq03WatchdogCycles` default `500000000` and `--sq03_watchdog_cycles`.

- [x] **Step 4: Build and unit test**

```bash
g++ -std=c++17 -I CHAOS/gem5/src tests/test_sq03_rules.cc -o /tmp/t && /tmp/t
cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt
```
Expected: PASS / exit 0.

- [x] **Step 5: Commit**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh \
  CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc \
  CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py configs/se/lsu_proxy.py \
  tests/test_sq03_rules.cc docs/gem5-fi/lsu/implementation_v3_2/SQ03_Safety_Audit_v3.2.8.md
git commit -m "[LSU][MDSPEC][V3.2.8][SQ03] one-shot hard cap and watchdog"
git push
```

---

### Task 6: External timeout, HANG/TIMEOUT preservation and SQ03 trace

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/tools/prop_trace_to_v31.py`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/trace_completeness.py`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/terminal_rules.py`
- Test: `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_sq03_chain.py`

**Interfaces:**
- Produces: `noteSQ03Injection(...)`, `noteSQ03Writeback(...)`, `noteSQ03Complete(...)`; trace kinds `inj_sq03`, `sq03_wb`, `sq03_complete`.

- [x] **Step 1: Write the failing chain test** with a synthetic chain injection → sq03_wb → sq03_complete → memory_response → register_writeback → consumer_commit, asserting `trace_completeness=COMPLETE`, `chain=PASS`, `coverage=COMPLETE`.

- [x] **Step 2: Implement trace**

`inj_sq03` detail: store seq/PC/addr/size, sq idx/gen, canWB before/after, storesToWB before/after, tick, eligible ordinal, seed. Register the store in `fault_store_registry` with family `sq03_canwb`, byte range, and `written_tick` at writeback. `sq03_wb` at `writebackStores` for the target; `sq03_complete` at `completeStore`. Later loads covering the byte get the ptag via `noteMemResponse`, producing response/writeback/consumer edges.

- [x] **Step 3: Runner timeout handling**

Wrap `subprocess.run` in `try/except subprocess.TimeoutExpired`; write partial `stdout.log`/`stderr.log` from `exc.stdout`/`exc.stderr`; set `run_status=SIMULATOR_ERROR`, `terminal=TIMEOUT`, `completeness=INCOMPLETE`, `accepted=False`; never MASKED. If exit code 1 with `CHAOS_SQ03_WATCHDOG_EXPIRED`, terminal `HANG`.

- [x] **Step 4: Completeness/terminal profiles**

Add SQ03 SDC/MASKED/SQUASHED/CRASH profiles mirroring DA04/SQ01 (store-side). Add `run_reason` to PILOT meta.

- [x] **Step 5: Run tests, build, one smoke** and commit.

---

### Task 7: SQ03 five pilots and no-fault baselines

**Files:**
- Modify: `run_pilot.py` (`--model SQ03`, workload `sq_drain`, extra args, `_sq03_summary`, target proof)
- Create: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_8/SQ03-R01..R05`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_8/SQ03_v328_EVIDENCE.csv`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/SQ03_Implementation_v3.2.8.md`

**Interfaces:** consumes Task 5/6.

- [x] **Step 1: Add SQ03 runner support.** Extra args: `--chaos_lsqfwd --lsq_struct_mode sq03_canwb --max_faults 1 --rng_seed <seed> --lsqfwd_event_ordinal <ordinal> --sq03_watchdog_cycles 500000000`. Oracle from Excel (`ba3b3185e541ad03`).
- [x] **Step 2: Run five pilots**, capture: SampleRunID, seed, ordinal, target store seq/PC/addr/size, SQ idx/gen, canWB before/after, storesToWB before/after, injection tick, writeback tick, commit result, consumer relations, terminal, oracle, watchdog status, trace validity/coverage.
- [x] **Step 3: Run five no-fault baselines** with the same seeds, probability 0, and record checksums/timing.
- [x] **Step 4: Build evidence CSV and implementation doc.** Do not claim SDC unless the oracle changed with a causally linked consumer.
- [x] **Step 5: Commit.**

---

### Task 8: Status matrix, consistency check, status report

**Files:**
- Modify: `MODEL_STATUS_MATRIX.csv`
- Create: `LSU_v3.2.8_Status_Report.md`
- Create: `tools/check_v328_consistency.py`
- Test: `tests/test_v328_consistency.py`

- [x] **Step 1: Update matrix from real evidence.** FW05: DESIGNED/SOURCE_AUDITED/IMPLEMENTED/COMPILED/UNIT_TESTED/PILOT_RUN=1, PROPAGATION_VERIFIED=1 (R02–R05 SDC chain), evidence cites workload freeze/archive/baselines/five pilots. SQ03 only after safety+five pilots+coverage; never from compile alone.
- [x] **Step 2: Consistency check** across Excel v3.2.3, CSV, manifests, archive SHA, traces: FW05 workload path/SHA/Oracle identical; SampleRunID/Seed unchanged; only FW05 rows differ; SQ03 IDs/seeds unchanged; ConfigFrozen all NO.
- [x] **Step 3: Run tests and commit.**

---

### Task 9: Package and final report

**Files:**
- Create: `LSU_v3.2.8_FW05_ConfigFreeze_SQ03_Pilot_Package.zip` + `.sha256`
- Create: `DELIVERABLES_v3.2.8_SHA256.txt`, `GIT_STATUS/LOG/DIFF_v328.*`, `LSU_v3.2.8_Final_Report.md`

- [x] **Step 1: Provenance** (`git status/log/diff`, binary SHA).
- [x] **Step 2: Stage A/B/C contents** from the work order; include full SQ03/FW05 traces, archive, baselines, logs, HANG/TIMEOUT records.
- [x] **Step 3: SHA256 list and zip**; verify member count and hash.
- [x] **Step 4: Final report answers** the six FW05 and five SQ03 questions explicitly.
- [x] **Step 5: Commit and push.**

---

### Task 10: Start SP05

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/SP05_Definition_Freeze_v3.2.8.md`
- Create: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/sp05_rules.hh`
- Test: `tests/test_sp05_rules.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` (completeStore hook)

- [x] **Step 1: Freeze definition** from the v3.2.3 audit: one live store completion, entry-keyed one-shot, no `_completed`/`storesToWB` inconsistency, watchdog.
- [x] **Step 2: Rules + unit test** for one-shot/target selection.
- [ ] **Step 3: Hook + build + smoke.** If the hook creates an assert/underflow, stop and report the blocker; do not fabricate success.

> **Deferred to the next round (per the v3.2.8 work order: "本轮完成后继续SP05").** Only the definition freeze, `sp05_rules.hh`, and its unit test are committed; the live `completeStore` hook, build/smoke, trace and pilots are not implemented. `MODEL_STATUS_MATRIX.csv` therefore keeps SP05 `IMPLEMENTED=0`.
- [x] **Step 4: Commit.**

---

## Self-Review

- **Spec coverage:** archive (Task 2), baselines (Task 3), Excel v3.2.3 (Task 4), SQ03 safety (Task 5), timeout/HANG/trace (Task 6), SQ03 pilots/baselines (Task 7), matrix/consistency (Task 8), package/report (Task 9), SP05 (Task 10).
- **Placeholders:** none; code steps contain concrete code or commands.
- **Type consistency:** `sq03_fired`, `sq03WatchdogCycles`, `CHAOS_SQ03_WATCHDOG_EXPIRED`, `inj_sq03`/`sq03_wb`/`sq03_complete` names are used consistently.
- **Review Focus coverage:** archive SHA (Task 2 test), per-seed oracle (Task 3), unbounded injection (Task 5), HANG/TIMEOUT (Task 6), trace identity (Task 6 test).
