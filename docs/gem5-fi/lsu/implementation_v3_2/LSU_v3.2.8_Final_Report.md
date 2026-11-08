# LSU v3.2.8 — final report

**Branch:** `lsu-platform-v3.2.8` (from `f26218f8`, v3.2.7 tip)
**HEAD at report time:** `feff2505b115d8325181a1ae55e538b2450e0136`
**Final gem5 binary:** `build/ARM/gem5.opt` SHA256
`b988b7503cdf1feab10b99d09ec85df84b42eb385396142e0b7be6a197c63a45`
**No 60-sample formal run was started.** `ConfigFrozen` remains `NO` for all 60 rows.

This round has two workflows: A = FW05 formal-workload freeze + archive +
no-fault baselines + Excel v3.2.3; B = SQ03 safety hardening + five pilots.
SQ03's propagation chain ends at store completion with **zero consumers**, so
SQ03 is deliberately **not** marked `PROPAGATION_VERIFIED`.

---

## A. FW05 — answers

### A1. Is the workload truly archived?

Yes. `FW05_Workload_Archive/` contains:

| Part | File |
|---|---|
| source | `src/fw05_forward.c` (SHA `c79b4be9ee11cffbc5ca986eb418bcc9aad439429191140f4c92ca9347dfdfa4`) |
| binary (the exact pilot binary) | `bin/fw05_forward` (SHA `0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf`) |
| input data | `inputs/README.md` — none; static arrays initialized in source |
| build script + compiler | `build.sh`, `logs/compiler_version.txt` (gcc 12.3.1, aarch64) |
| reproduce check | `logs/rebuild_check.log` |
| gem5 run config | `run_pilot.sh`, `config/command_R01.txt`, `config/command_R02.txt` |
| golden | `golden/fw05_forward.golden` = `0x67afad307642983e` |
| provenance | `PROVENANCE.md` |
| checksums | `SHA256SUMS` (every member) |
| no-fault runs | `baselines/R01..R05/` (stdout, stats, config) |
| instructions | `README.md` |

The archived binary hash equals the full SHA256 recorded by **all five**
v3.2.7 pilot manifests (`0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf`),
not merely a filename or a short prefix.

### A2. Did all five pilots use the same workload version?

Yes. All five manifests (`pilots_v3_2_7/FW05-R01..R05/manifest.json`) record
the identical full hash above. They are therefore reused as-is; the historical
runs were not overwritten.

### A3. Do the no-fault baselines pass?

Yes. `evidence_v3_2_8/FW05_no_fault_baselines.csv`: five per-seed runs, same
seeds, injection disabled, same workload and oracle. All exit 0, all produce
`0x67afad307642983e`, all `PASS`. The oracle value is the same for all five
seeds because the workload's output is seed-independent; this was verified per
seed rather than copied from another row.

### A4. Are Excel, CSV, manifests and the archive consistent?

Yes, and this is machine-checked:

- `tests/test_v328_consistency.py` (4 passed): the five Excel FW05 rows carry
  `fw05_forward`, the archive SHA and Oracle `67afad307642983e`; SQ03
  seeds/manifests agree; `ConfigFrozen` is `NO` for all 60; the CSV mirrors
  sheet 5.
- `tests/test_fw05_archive.py` (3 passed): binary hash = pilot hash; all
  manifests agree; archive parts present.
- `tests/test_lsu_v323_workbook.py` (4 passed): only the five FW05 rows changed;
  identity columns unchanged; the other 11 models cell-identical.
- Independent diff of v3.2.2 vs v3.2.3: sheet 5 changes are exactly rows 42–46
  (the five FW05 samples), plus the FW05 rows of the model/hook sheets and a
  revision record. Sheet 15 `FW05配置冻结` is additive. The other 55 sample rows
  are cell-identical.

### A5. Can the four SDCs be independently reproduced?

Yes. Re-run on the **final** binary (which differs from the v3.2.7 pilot
binary), same seeds, ordinals and workload, into scratch outdirs:

| Pilot | workload SHA | seed | ordinal | oracle | checksum | historical |
|---|---|---|---|---|---|---|
| R01 | 0cf40509… | 1025137124 | 1 | PASS | `0x67afad307642983e` | SQUASHED/PASS |
| R02 | 0cf40509… | 1653118510 | 2 | FAIL | `0x549c9e0347adaf23` | SDC |
| R03 | 0cf40509… | 2442802213 | 3 | FAIL | `0x549c9e0347adaf25` | SDC |
| R04 | 0cf40509… | 899944922 | 4 | FAIL | `0x549c9e0347adaf27` | SDC |
| R05 | 0cf40509… | 2836530945 | 5 | FAIL | `0x549c9e0347adaf19` | SDC |

Every checksum is bit-identical to the historical pilot. R02's injection log
also reproduces exactly: `LoadSeq 12156, TrueSeq 12155, AltSeq 12154,
faults_injected: 1`, matching the historical `last_injection_dyn_seq=12156`.
Logs: `evidence_v3_2_8/recheck_final_binary/`,
`RECHECK_v328_FINAL_BINARY.csv`.

FW05 remains **wrong-source selection** (youngest matching store → an older,
still-eligible full-cover store). It is **not** multi-store splicing and must
not be described as such.

---

## B. SQ03 — answers

### B1. Is the HANG risk eliminated?

The unbounded path is removed. Source-verified semantics: in the general
`CHAOSLSQFwd` paths `max_faults == 0` meant **unlimited**
(`if (max_faults != 0 && faults_injected_count >= max_faults)`). For
`sq03_canwb` this is now clamped to 1 in
`chaos_sq03::shouldSetCanWB` **and** in the constructor, with an independent
`sq03_fired` one-shot checked before eligibility logic, and
`assert(faults_injected_count == 1)` after the increment. A `max_faults=0`
smoke still yields exactly one injection (`fired=1 injected=1 eligible=1`,
exit 0, checksum equals the baseline). An in-simulator watchdog
(`--sq03_watchdog_cycles`, default 500,000,000 ticks) logs
`CHAOS_SQ03_WATCHDOG=EXPIRED` and calls `fatal`, so expiry is exit 1 — never a
normal MAX_TICK exit and never MASKED. External `run_pilot.py --timeout`
preserves partial logs/trace and classifies `TIMEOUT/HANG/INCOMPLETE`.
Evidence: `evidence_v3_2_8/SQ03_safety/` (watchdog smoke exits 1 with the
EXPIRED line), `tests/test_sq03_rules.cc` PASS (`max_faults=0` clamp covered).

Residual: a host-level scheduler stall (not simulator ticks) is only covered by
the external timeout; on a loaded host, shell-level timeouts can fire even when
the simulation would finish in seconds (observed during this round's re-runs at
load average > 50; standalone re-runs exited 0 in ~3.3 s).

### B2. Did all five pilots run?

Yes. `pilots_v3_2_8/SQ03-R01..R05/`; Excel seeds and ordinals 1–5, workload
W3 `sq_drain`, all exit 0, `run_status=COMPLETED`.

### B3. Exactly one injection each?

Yes. `lsq_fwd_injections.log` every pilot: one `Cycle/Site` line and
`fired=1 injected=1 eligible=<n>`. `pilot_meta.json` `injection_count=1`,
`target_event_proof.all_one_injection=true`. `_canWB 0→1` and
`storesToWB 0→1` exactly once per pilot.

### B4. Is there real propagation evidence?

Partial, and reported as such. Trace v3.1 for each pilot is VALID/COMPLETE
(`record_integrity=VALID`, `trace_completeness=COMPLETE`,
`propagation_coverage=COMPLETE`), with the real store chain
`injection → store_writeback → store_mem_write → sq03_complete`, linked by
dynamic seq / SQ entry / generation. R01's target store writes back 9,240
ticks earlier than no-fault; R05 385 ticks earlier; R02–R04 at the baseline
tick. **However** `consumer_instructions=0` for all five: no later load reads
the target store, so the register-writeback/consumer-commit stages are absent.
Chain PASS here means the store-side chain is intact; it is not a
load-consumer chain.

### B5. Is there application-level SDC?

No. All five applications produce the golden `0xba3b3185e541ad03` and pass the
oracle. Terminal state is MASKED (`STORE_COMMITTED_LANE_NOT_READ`). The early
permission did not change the drained data. Time shift alone is explicitly not
called SDC. `PROPAGATION_VERIFIED=0` accordingly.

---

## C. Platform, versioning, verification

- Base `f26218f8`; branch `lsu-platform-v3.2.8`; eight one-patch-per-unit
  commits (work order → FW05 archive → FW05 baselines → Excel → SQ03 safety →
  SQ03 trace/pilots → matrix/consistency → SP05 definition).
- Final gem5 binary SHA `b988b750…c63a45` (recorded in
  `logs_v3_2_7/binary_final_v328.sha256`).
- Build log: `logs_v3_2_7/build_sq03_safety.log` (exit 0).
- Unit tests: FW05 rules PASS, SQ03 rules PASS, MD04 rules PASS, SP05 rules
  PASS; Python: archive+consistency+workbook 11 passed.
- v3.2.7 branch, package, pilots and traces untouched; historical W8 alignment
  configuration retained in the v3.2.2 workbook and in
  `excel/FW05_OLD_NEW_DIFF_v3.2.3.md`.
- Open issues: see `OPEN_ISSUES_v3.2.8.md`.
