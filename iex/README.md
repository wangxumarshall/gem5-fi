# IEX — final 5×3 experiment implementation

This directory is the self-contained reproduction harness for the frozen IEX
experiment **`IEX_WHEN_5x3_v3_2026-11-23`**.  The gem5 source tree in the parent
repository is the authoritative final source (branch `IEX`, experiment commit
`1e8214e25b0518836c9778fd710794c023b9ca7b`).

## Frozen design

| Item | Value |
|---|---|
| Fault models | `IEX-M001` … `IEX-M007` (7) |
| Contexts | `C01` … `C05` (5) |
| Timing points | `T01` = 10%, `T02` = 50%, `T03` = 90% of eligible dynamic events |
| Fault conditions | 7 × 5 × 3 = **105** |
| Paired Controls | 7 × 5 = **35** |
| Terminal result | 84 SDC, 21 MASKED (all 105 gate PASS) |

`T01/T02/T03` use the frozen control pre-scan ordinals.  For example, a
context with `N = 128` uses ordinals `13 / 64 / 116`; with `N = 129`, `13 / 65 / 117`.

## Layout

```
iex/
├── gem5 -> ..                 # relative link to the gem5 repository root
├── scripts/                   # campaign, SE config, oracle, workloads, verify
├── workloads/v3/{src,build}   # 35 directed AArch64 workloads + exact ELFs
├── oracle/                    # independent bigint oracle vectors
├── inputs/                    # authoritative experiment plan workbook
├── configs/                   # CPU/FU config, environment record, sample config.ini
├── evidence/                  # 105/35 summary tables + accepted core evidence
├── source/                    # source.diff (exact v2→v3 delta) + full diff
├── docs/                      # reproduction guide, provenance, design sheets
└── SOURCE_PROVENANCE.json     # commit/tree/binary/script hashes
```

Raw traces are **not** committed.  The accepted portable archives live outside
Git and are indexed in `docs/EVIDENCE_INDEX.md` with SHA256 values.

## Build

```bash
cd iex/gem5
CC=/usr/bin/aarch64-openEuler-linux-gcc \
CXX=/usr/bin/aarch64-openEuler-linux-g++ \
scons build/ARM/gem5.opt -j 24
```

The original experiment binary (before this freeze) had SHA256
`15913730eea5ebec7950dad991ca50130b0c816360acc0f93333ef9db695b2b5`.
A clean rebuild at a different absolute path can differ in build-id/debug paths;
the frozen **source** is identified by tree `e71ddd6af2facefca9a2c3891505fb35bcce912a`.

## Run

All commands below are executed from `iex/` (the scripts derive `ROOT=iex/`):

```bash
# 1. independent oracle + frozen workloads
python3 scripts/iex_oracle.py
python3 scripts/gen_workloads_v3.py

# 2. 105/35 campaign
python3 scripts/run_campaign.py plan    --jobs 12
python3 scripts/run_campaign.py control --jobs 12
python3 scripts/run_campaign.py pilot
python3 scripts/run_campaign.py fault   --jobs 12
python3 scripts/run_campaign.py audit

# 3. delivery tables and independent verification
python3 scripts/build_delivery.py
python3 scripts/verify_final.py
python3 scripts/build_final_packages.py
```

A single case:

```bash
python3 scripts/run_campaign.py fault --case IEX-M001-C01-T01 --jobs 1
```

Outputs are written under `iex/results/IEX_WHEN_5x3_v3_2026-11-23/` and are
git-ignored.  Never repoint a validation campaign at the authoritative evidence
directory.

## Evidence policy

* Fault and Control differ only in `IEX_FAULT_ENABLED` and the selected ordinal.
* Data edges come from renamed physical tags and allocation generations, never
  from the final output.
* C03 is `MASKED`; all other contexts are `SDC`.
* Failed/anomalous attempts are retained in `attempt_history.csv`; they are not
  deleted to improve the result.

See `docs/IEX_FINAL_REPRODUCTION_GUIDE.md` and
`docs/IEX_FINAL_GIT_FREEZE_REPORT.md` for the full procedure and provenance.
