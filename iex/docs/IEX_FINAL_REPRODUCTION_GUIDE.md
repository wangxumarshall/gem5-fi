# IEX final experiment reproduction guide

Applies to the frozen experiment **`IEX_WHEN_5x3_v3_2026-11-23`**.

The final source is gem5 branch `IEX`, experiment commit
`1e8214e25b0518836c9778fd710794c023b9ca7b` (tree
`e71ddd6af2facefca9a2c3891505fb35bcce912a`).  The branch is published at
`git@github.com:wangxumarshall/gem5-fi.git`.

## 1. What is being reproduced

| Item | Count | Notes |
|---|---:|---|
| Fault models | 7 | `IEX-M001` … `IEX-M007` |
| Execution contexts | 5 | `C01` … `C05` |
| Timing points | 3 | `T01`=10%, `T02`=50%, `T03`=90% |
| Fault conditions | 105 | 7 × 5 × 3 |
| Paired Controls | 35 | 7 × 5; same binary/workload/PC |
| Frozen terminal result | 84 SDC / 21 MASKED | all 105 gates PASS |

The experiment is **not** the old When-v2 T01–T05 design.  The old v2 and v1
trees are history archives, not inputs to this procedure.

## 2. Host environment used for the frozen run

- Server: `localhost0101` (0101), aarch64
- OS: openEuler 24.03 LTS-SP3, kernel 6.6.0-145.3.16.148.oe2403sp3.aarch64
- Compiler: `aarch64-openEuler-linux-gcc/g++` 12.3.1 (openEuler build)
- SCons: 4.5.2; Python 3.11.6; GNU tar 1.35; zstd 1.5.5
- gem5 target: `build/ARM/gem5.opt`, ArmO3CPU, 1 core / 1 thread, 2 GHz,
  timing memory, 32 KiB L1I/L1D, 256 KiB L2, DDR3_1600_8x8
- Runtime timeout: 600 s per run; campaign parallelism used: 12

The complete original environment record is `configs/environment.json`
(SHA256 `db96dec748632a3f1805f6eaa5311f19828134d807b1c806fbf27836841285e7`).

## 3. Layout and path rule

From a Git checkout:

```text
gem5/                       # repository root
├── src/                    # gem5 source, frozen at experiment commit
├── iex/
│   ├── gem5 -> ..          # relative symlink to the repository root
│   ├── scripts/            # run_campaign.py, iex_se.py, oracle, workloads
│   ├── workloads/v3/       # 35 .S sources + exact ELFs + manifests
│   ├── oracle/             # bigint oracle vectors
│   ├── inputs/             # authoritative experiment plan workbook
│   ├── configs/            # FU config, environment, sample config.ini
│   ├── evidence/           # 105/35 summary evidence + core evidence archive
│   └── source/             # exact v2→v3 patch
└── build/ARM/gem5.opt      # build output (git-ignored)
```

Every script computes `ROOT` as the parent of `scripts/`.  Running commands
from `iex/` therefore resolves:

- `ROOT/gem5` → repository root (through the symlink)
- `ROOT/workloads/v3`, `ROOT/oracle`, `ROOT/results`

On the original server the live experiment workspace is
`/home/sdc/gem5-fi-IEX/when_5x3_v3/` with `when_5x3_v3/gem5 -> ../gem5`;
the official results remain under `when_5x3_v3/results/`.

## 4. Build the frozen source

```bash
cd iex/gem5
CC=/usr/bin/aarch64-openEuler-linux-gcc \
CXX=/usr/bin/aarch64-openEuler-linux-g++ \
scons build/ARM/gem5.opt -j 24
```

Expected non-fatal configuration warnings are the same as the frozen build:
missing `capstone/capstone.h`, missing `png.h`, and no HDF5 C++ libraries.

Record the build:

```bash
git -C iex/gem5 rev-parse HEAD          # must be the IEX freeze commit
git -C iex/gem5 rev-parse HEAD^{tree}   # src tree must match e71ddd6...
sha256sum iex/gem5/build/ARM/gem5.opt
```

The binary used for the original runs had SHA256
`15913730eea5ebec7950dad991ca50130b0c816360acc0f93333ef9db695b2b5`.
A clean rebuild in a different absolute path may have a different hash because
debug paths and build-id are embedded; the authoritative identifier is the
source tree plus the experiment commit.

## 5. Regenerate the independent oracle and workloads

```bash
cd iex
python3 scripts/iex_oracle.py
python3 scripts/gen_workloads_v3.py
```

- `iex_oracle.py` reads `inputs/gem5-fi-IEX-Final-Paper-Experiment-Plan.xlsx`,
  checks the workbook vectors, and writes `oracle/oracle_vectors.json`.
  It must report zero mismatches.
- `gen_workloads_v3.py` assembles and links 35 freestanding AArch64 ELFs into
  `workloads/v3/build/` and rewrites `workloads/v3/manifest.json|csv` with ELF
  and symbol hashes.  It uses `aarch64-openEuler-linux-gcc`, `nm` and `objdump`.

Expected scale: 7 models × 5 contexts = 35 workloads, one ELF per
Model×Context.

## 6. Plan the 105 + 35 matrix (dry-run)

```bash
python3 scripts/run_campaign.py plan --jobs 12
```

Outputs under `results/IEX_WHEN_5x3_v3_2026-11-23/`:

- `manifest/manifest.json`
- `manifest/cases.csv` — exactly 105 unique CaseIDs
- `environment/environment.json`

The plan asserts 105 unique cases and that every `Model-Context` key exists in
the workload manifest.  It does **not** execute gem5.

## 7. Controls: freeze N and the three ordinals

```bash
python3 scripts/run_campaign.py control --jobs 12
```

Runs two independent attempts per Control context (35 contexts, 70 gem5 runs).
For each control it records:

- measured eligible event count `N`
- `T01_Ordinal`, `T02_Ordinal`, `T03_Ordinal`
- repeat-census equality and all-slots-golden status

Frozen examples:

| N | T01 | T02 | T03 |
|---:|---:|---:|---:|
| 128 | 13 | 64 | 116 |
| 129 | 13 | 65 | 117 |

No fault injection occurs in a Control (`IEX_FAULT_ENABLED=0`).

## 8. Pilot all seven models

```bash
python3 scripts/run_campaign.py pilot
```

21 runs: for each model, a C01 fault at T02, a zero-apply negative control, and
a C05 fault at T02.  Pilot output goes to `results/.../pilots/` and does not
replace official results.

## 9. Run the 105 Fault conditions

One case:

```bash
python3 scripts/run_campaign.py fault --case IEX-M001-C01-T01 --jobs 1
```

All 105:

```bash
python3 scripts/run_campaign.py fault --jobs 12
```

Each run is a fresh gem5 process:

```text
gem5.opt -d <attempt>/m5out --quiet scripts/iex_se.py <workload.elf>
```

with `IEX_*` environment variables selecting the model, context, target PC,
consumer PC, ROI, timing ID, selector mode, ordinal and calibrated N.
Fault and Control differ only in `IEX_FAULT_ENABLED` and the selected ordinal.

A fault attempt passes the runner gate only if:

- process return code is 0 and no timeout;
- `inject.applied == 1`;
- `run_end.timing_satisfied == 1`;
- `run_end.timing_selected_ordinal` equals the frozen `K`.

## 10. Analyze and build delivery tables

```bash
python3 scripts/run_campaign.py audit
python3 scripts/build_delivery.py
python3 scripts/verify_final.py
python3 scripts/build_final_packages.py
```

- `audit` reads the traces and writes propagation evidence under
  `results/.../audit/propagation/`, plus `fault_runs.csv` and `summary.json`.
- `build_delivery.py` writes the accepted delivery tables under
  `delivery/IEX_WHEN_5x3_v3_2026-11-23/`.
- `verify_final.py` independently checks all 105 faults and 35 controls and
  writes `verification_report.json`; it must print `"all_pass": true`.
- `build_final_packages.py` creates `final_package/` (core evidence zip, results
  workbook, reproduction info, workloads and authoritative raw traces).
  Raw traces are intentionally not committed to Git.

## 11. Trace and evidence semantics

Per run, `attempt-NNNN/` contains:

```text
stdout.txt, stderr.txt, meta.json, trace.jsonl, m5out/{config.ini,stats.txt}
```

`trace.jsonl` is the dynamic O3 trace.  Every event carries `EventID`,
`ParentEventIDs` and `FaultID`; rename-time allocation tags and generations
support producer→consumer edges.  Evidence files:

| File | Content |
|---|---|
| `injections.csv` | exact hook, PC, SeqNum, before/after value, guard state |
| `propagation_edges.csv` | dynamic producer→consumer tags and read values |
| `lifecycle.csv` | issue / execute begin-end / writeback / commit / squash |
| `oracle_comparison.csv` | selected-slot actual vs independent bigint oracle |
| `attempt_history.csv` | every attempt, with authoritative flag |
| `failures_and_anomalies.csv` | non-zero/missing attempts, retained |

C03 is `MASKED`: a real EOR consumes the fault and both values are overwritten
before the only fixed store.  All non-C03 contexts are expected `SDC`.
C05 eligibility additionally requires an older designed `CBNZ` to be unresolved
at the hook and resolved later; the v3 selector counts only such episodes.

## 12. Validate without touching official evidence

Copy `iex/` to an independent validation root, replace the `gem5` link with one
pointing at the built repository, and keep the frozen `controls.json`:

```bash
cp -a iex /path/to/validation
rm -f /path/to/validation/gem5
ln -s /home/sdc/gem5-fi-IEX/gem5 /path/to/validation/gem5
mkdir -p /path/to/validation/results/IEX_WHEN_5x3_v3_2026-11-23/audit
cp when_5x3_v3/results/IEX_WHEN_5x3_v3_2026-11-23/audit/controls.json \
   /path/to/validation/results/IEX_WHEN_5x3_v3_2026-11-23/audit/
cd /path/to/validation
python3 scripts/run_campaign.py plan --jobs 12
python3 scripts/run_campaign.py fault --case IEX-M001-C01-T02 --jobs 1
```

Never run a validation campaign with `ROOT` pointing at the official
`when_5x3_v3/results/` directory.

## 13. Reproduce from GitHub

```bash
git clone -b IEX git@github.com:wangxumarshall/gem5-fi.git gem5-fi-iex
cd gem5-fi-iex/iex
# follow sections 4–10
```

The raw-trace archives are not in Git.  They are delivered separately; verify
them against `docs/EVIDENCE_INDEX.md` and the delivery SHA256 list before use.

## 14. Validation record

This section is filled by the final freeze run (see
`IEX_FINAL_GIT_FREEZE_REPORT.md`): build commit/tree, rebuilt binary SHA256,
dry-run matrix counts, representative Fault/Control results, and trace/oracle
checks.  A dry-run is not reported as a full 105-case reproduction.
