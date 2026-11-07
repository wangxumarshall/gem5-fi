# LSU v3.2.4 DA04 Delivery Package — README

**Package:** `LSU_v3.2.4_DA04_Implementation_Package.zip`
**Built:** 2026-11-07
**Branch:** `lsu-platform-v3.2.4` (base `7f54db8d`, HEAD at build time `81981fc3` plus this package refresh)
**Binary:** DA04 runs `3e9148fc…`; FW02/SQ01 runs `dae736b2…` (see `GIT_COMMIT_v324.txt`)

## Mandatory reading: Oracle PASS is not MASKED

`oracle=PASS` only means the workload's final checksum matched the golden
value. It is **not** a terminal-state verdict and it cannot prove a fault was
masked. In this package:

- R01 is **SQUASHED** with oracle PASS (the target store never committed);
- R02/R03 are **MASKED** with oracle PASS because the affected lane was never
  read (store writeback + actual cache write evidence present);
- R04/R05 are **SDC** with oracle FAIL.

Terminal state comes from the chain-scoped rules in
`platform/terminal_rules.py`, not from the oracle.

## Did DA04 actually affect the real memory write?

**Yes.** The `store_mem_write` node is emitted where `BaseCache::updateBlockData`
applies the packet to the cache block. For R04:

```text
be_mask=0xe
lane0 packet/before/after = 0xC1/0xA5/0xA5
disabled_unchanged=1
```

The disabled lane is byte-identical before and after the write, while the
enabled lanes carry the store data; the later load returns `0xA5` (the old
byte), not `0xC1`. See `DA04_PROPAGATION_EVIDENCE.txt` and the raw JSONL.

## Contents map (required items 1–12)

| # | Required item | File(s) |
|---|---|---|
| 1 | Source audit + real source mapping | `DA04_Source_Audit_v3.2.4.md`, `DA04_Implementation_v3.2.4.md` §2 |
| 2 | Modified C++ source + Git Diff | `CHAOS/gem5/src/...` (in zip), `LSU_v3.2.4_Git_Diff.txt` |
| 3 | Branch / Commit / Status | `GIT_COMMIT_v324.txt`, `GIT_STATUS_v324.txt` |
| 4 | Real 0xF→0xE records | `DA04_MASK_EVIDENCE.txt`, `pilots_v3_2_4/DA04-R0*/lsq_fwd_injections.log` |
| 5 | R01–R05 complete logs + JSONL | `pilots_v3_2_4/DA04-R01..R05/` (stdout, stderr, stats, oracle, prop CSV, `trace_v31.jsonl`) |
| 6 | SQ drain / store writeback / real memory write | `DA04_PROPAGATION_EVIDENCE.txt`, `store_writeback` and `store_mem_write` nodes in JSONL |
| 7 | Later load / register writeback / consumer | same evidence file + JSONL (`memory_response`, `register_writeback`, `consumer_commit`) |
| 8 | Five pilot terminals + Oracle | `DA04_PILOT_SUMMARY.csv`, `DA04_PILOTS.md`, each `pilot_meta.json` |
| 9 | Compile / unit / integration logs | `logs/build_v324*.log`, `logs/unit_tests_final.log`, `logs/pytest_final.log`, `logs/baseline_final_alignment.log`, `logs/trace_validator_final.log` |
| 10 | FW02/SQ01 trace fixes | `LSU_v3.2.4_FW02_Rejudge.md`, `LSU_v3.2.4_SQ01_Propagation.md`, `pilots_v3_2_4/FW02-R01/R05`, `SQ01-R01..R05` |
| 11 | 12-model progress | `MODEL_STATUS_MATRIX.csv`, `LSU_v3.2.4_Model_Progress.md` |
| 12 | Latest authoritative Excel | `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.1.xlsx` (latest plan), `...-v3.2.xlsx`, `final_paper_audit_v3_1/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.1.xlsx` (the file `config_parser.py` reads) — see `EXCEL_PROVENANCE.md` |

## Status ladder (terms used exactly)

`DESIGNED` → `SOURCE_AUDITED` → `IMPLEMENTED` → `COMPILED` → `UNIT_TESTED`
→ `PILOT_RUN` → `PROPAGATION_VERIFIED`.

- DA04: all seven levels reached, with PROPAGATION_VERIFIED based on R04/R05.
- SQ01: up to PILOT_RUN; store writeback + memory write proven, **no
  consumer**, so NOT PROPAGATION_VERIFIED.
- LP01: up to UNIT_TESTED; pilots next round.
- A01/A03/FW02: PILOT_RUN (v3.2.4 re-adjudicated); PROPAGATION_VERIFIED not
  re-asserted this round.
- MD04/FW05/SQ03/SP05/LQ04/RP01: DESIGNED only.

## Safety / scope

- The historical v3.2.3 and earlier delivery zips in the worktree are
  untouched.
- No 60-sample formal campaign was started; no other model's configuration
  changed; Warm-up/ROI remain unfrozen.
- SQ01 traces are 189 MB each; they are included in this zip (compressed) and
  kept on disk, but are not tracked by Git (sha256 sidecars are committed).
