# CLOSURE_RUNBOOK_v3.2.12.md — Task 16/17 generation runbook (12-model closure matrix + diagnostic feature dataset)

Prepared 2026-11-10 for the Task 16/17 executor.
Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`, branch
`lsu-platform-v3.2.12` (runbook written at HEAD `512d937c`).
Inputs consumed: `CLOSURE_INPUTS_v3.2.12.md`, `tools/lsu_12model_closure.py` (record /
missing / matrix / features), `LSU_Propagation_Acceptance_Standard_v3.2.12.md`,
`audit_v3_2_12/pilot_record.schema.md`, `audit_v3_2_12/MissingEvidenceMatrix.csv` (+ its
`.md`), `audit_v3_2_12/SUPPLEMENTARY_ORACLE_MANIFEST_v3.2.12.csv`, plan Tasks 16–17.

Every command in this runbook was either run for real during preparation (the dry run,
§7 — outputs in `/tmp/lsu_closure_dryrun_3212/`) or is a mechanical transcription of the
verified pilot inventory (§1). All pilot-directory paths and binary SHAs below were read
from the committed `manifest.json` files with the tool's own `_find_sha` on 2026-11-10.

**Honest scope statement.** Task 16/17 generation is *blocked* until Tasks 7–15 have
produced their pilot directories and the final rebuilt binary exists (§6). The commands
in §2 cover the 92 already-committed pilot directories (78 historical + 14 SUPP); the
seven pending groups are given as exact templates. The dry run in §7 validates the whole
pipeline on the current evidence and must NOT be mistaken for the final verdict: it
covers 10 of 12 models and its verdicts reflect the pre-Task-7–15 evidence state.

All commands run from the worktree root. Tasks 16/17 are pure Python over committed
artifacts — **no gem5 execution is required or allowed** in these two tasks. Define once:

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
PL=docs/gem5-fi/lsu/implementation_v3_2          # pilot roots live here
AUD=$PL/audit_v3_2_12                            # all outputs land here
```

---

## 0. Preconditions (all must hold before the FINAL generation)

| # | Gate | How to check | State at runbook time |
|---|---|---|---|
| P1 | Tasks 7–15 pilot dirs committed (A01/A03/FW02/SQ01/SQ03/SP05 SUPP + controls; RP01 pilots + controls) | `ls $PL/pilots_v3_2_12/` shows `SUPP-A01-R01..R05` etc.; RP01 dirs exist per Task 15 | **NOT MET** — see §6 |
| P2 | Final binary rebuilt after ALL trace commits (`scons -j126`, publish to repo-root `build/ARM/gem5.opt`) and its SHA256 recorded in `GIT_COMMIT_v3212.txt` | `sha256sum build/ARM/gem5.opt` equals the recorded final SHA | **NOT MET** — current `build/ARM/gem5.opt` = `e527f26af7c2661995f456a2c96695ff6b366d5d787351172947ed259fad04ed` (verified 2026-11-10), which predates the A01 `3d7b11c5`/`672ce9ac`, A03 `ddaba767`, FWD-SQ `7c67fa99` and RP01 `512d937c` commits |
| P3 | Disk gate | `df -h /home` free ≥ 70.6 GiB | 72G available at prep time (CLOSURE_INPUTS §0) |
| P4 | Unaffected regression green on the final binary | `build/ARM/gem5.opt --outdir=/tmp/<d> configs/se/arm_chaos.py --cmd workloads/directed/reg_chain --cpu O3` → golden `f247ef3fe6f02cfd`, exit 0 | belongs to Task 18, not 16/17 |

Note on P2: the SUPP Task 5 records (DA04/LP01/MD04/FW05) are keyed to `e527f26a…` and
stay keyed to it after the rebuild — **never re-run or re-record them under the new
binary**; the per-binary split (§1) is what keeps the two vintages honest.

---

## 1. Binary discipline — which SHA applies to which directory group

`record --binary-sha` is a *purity check*: `audit_pilot` compares the flag against the
SHA recorded in the pilot's own `manifest.json` and, on mismatch, adds
`BINARY_SHA_MISMATCH` to that record's `MissingEvidence`; an unrecorded SHA adds
`BINARY_SHA_UNRECORDED` (`tools/lsu_propagation_audit.py:477-481`). It never blocks the
run — so a wrong `--binary-sha` silently pollutes the verdict columns.

**Rules (binding for Task 16):**

1. **One `record` invocation per (model, binary) group**, `--binary-sha` = that group's
   own recorded SHA (the tables below), so the purity check passes cleanly and the group
   is self-documenting. One record JSON per group:
   `$AUD/<MODEL>_records_v3.2.12.binary-<sha8>.json`.
2. **Never pass a single global `--binary-sha` across mixed-binary directories.**
   Real failure already on record: `audit_v3_2_12/LQ04_verdict_v3.2.12.json` (Task 4)
   carries `MissingEvidence=BINARY_SHA_MISMATCH` on every LQ04 fault pilot because the
   expected SHA used there was not the pilots' own `f3c2a442…`. The same mistake at Task
   16 scale would stamp a false missing-evidence code onto all 92 records.
3. **Never merge**: verdicts are never computed across binaries (standard §2 hard
   invariant). `matrix` enforces this itself — `_closure_rows` groups records by
   `BinarySHA256` and, when a model spans >1 binary, renames each row
   `MODEL@<sha8>` (`tools/lsu_12model_closure.py:1146-1169`). Per-binary recording (rule 1)
   additionally keeps the JSON inputs split so a single group can be regenerated without
   touching others.
4. Pilots produced by Tasks 7–15 run on the **final rebuilt binary**: their group takes
   `--binary-sha <FINAL_BINARY_SHA256>` (from `GIT_COMMIT_v3212.txt`, gate P2). If the
   binary is rebuilt more than once during Tasks 7–15, each rebuild SHA is its own group.
5. Out-of-scope directories (frozen from the Task 6 missing-matrix scan, which uses the
   same filter): nested `pilots_v3_2_1/failed_contexts/FW02-R02,R03`, meta-less
   `pilots_v3_2_9/SQ03-PROBE-F0-P00,P01`, `sweep/`, `REPLAY-PROBE-0`, and the four
   `REPLAY-RW01/RW02` dirs (no 12-model id — `record` would reject their model anyway).
   Do not add them to the record set.

### 1.1 Binary SHA → directory group map (verified from manifests, 2026-11-10)

| Binary SHA256 (full) | Directory group |
|---|---|
| `275111d805a71bc3defa5a44758810e4753d99ea55e46a423cdd741002f06bb4` | `pilots_v3_2_1/`: A01-R01..R05, A03-R01..R05, FW02-R01, R04, R05 |
| `0fa610c21b6a3c40e2e67dd5588956e06746b6d85ce6782a8ffce3429f232bab` | `pilots_v3_2_2/`: A01-R01, A01-R03, A03-R01 |
| `8eb7ce8d76ab63d90dbd00694efb90c7c2545da47ad07ecf5325399274a3b682` | `pilots_v3_2_3/`: SQ01-R01..R05 |
| `b1f7cf189d2be1e90b8f682d2be97c057c78cfb8b58290c3631bb04f99578bea` | `pilots_v3_2_4/`: FW02-R01, FW02-R05, SQ01-R01..R05 |
| `3e9148fc380c84917ddad84603e540b2e40e217918f392eb5659d32a56668297` | `pilots_v3_2_4/`: DA04-R01..R05 |
| `6808c56e22b44eab3e189a1c51e6b90ec1c95e0c66d0c0835d205575572d7645` | `pilots_v3_2_5/`: DA04-R04, DA04-R05 · `pilots_v3_2_6/SMOKE_LP01-R01_final_binary` |
| `69a1ca9c5b1cbfb160d0502a8cad8acf7d17101625228978ec79ede588b2287d` | `pilots_v3_2_5/`: LP01-R01..R05 |
| `0de2564468fd710bf1df22d2336acac0ea92f7bc1ef5780178f18f497a302d7d` | `pilots_v3_2_6/`: DA04-R04, DA04-R05, LP01-R01..R05, MD04-R01..R05 |
| `8377c011bb5916be67fa1132232440ae7f8be02351c3034624a339319a545bec` | `pilots_v3_2_7/`: FW05-R01..R05, MD04-R01..R05 |
| `b988b7503cdf1feab10b99d09ec85df84b42eb385396142e0b7be6a197c63a45` | `pilots_v3_2_8/`: SQ03-R01..R05 |
| `f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694` | `pilots_v3_2_10/`: LQ04-R01..R05, LQ04-CONTROL-R01..R05 |
| `e527f26af7c2661995f456a2c96695ff6b366d5d787351172947ed259fad04ed` | `pilots_v3_2_12/` SUPP (Task 5, raw-oracle runs): SUPP-DA04-R04,R05 · SUPP-LP01-R01..R05 · SUPP-MD04-R02,R03,R05 · SUPP-FW05-R02..R05 |
| `<FINAL_BINARY_SHA256>` (after gate P2) | Task 7–15 pilots: `SUPP-A01-*`, `SUPP-A03-*`, `SUPP-FW02-*`, `SUPP-SQ01-*`, `SUPP-SQ03-*`, `SUPP-SP05-*`, `RP01-*`, `RP01-CONTROL-*` (exact dir names fixed by those tasks) |

Twelve distinct historical/SUPP binaries + the final one. Same `PilotID` in two roots
(e.g. `A01-R01` in v3_2_1 and v3_2_2) is two records of two binaries — both are kept;
the closure-matrix corroboration keys on `SampleRunID`/`SupplementaryOf`, so a duplicated
context never counts as two contexts (standard §4).

---

## 2. Exact `record` commands (one per (model, binary) group)

Each invocation prints one line per pilot
(`PilotID: FinalClassification=… ObservedTerminal=… MaskingMechanism=… missing=[…]`) —
capture stdout to a log next to the JSON; it is the per-record evidence trail.

### 2.1 The 23 groups available today (78 historical + 14 SUPP = 92 records)

```bash
# A01 (2 groups)
python3 tools/lsu_12model_closure.py record --model A01 \
  --pilot-dir $PL/pilots_v3_2_2/A01-R01 --pilot-dir $PL/pilots_v3_2_2/A01-R03 \
  --json $AUD/A01_records_v3.2.12.binary-0fa610c2.json \
  --binary-sha 0fa610c21b6a3c40e2e67dd5588956e06746b6d85ce6782a8ffce3429f232bab
python3 tools/lsu_12model_closure.py record --model A01 \
  --pilot-dir $PL/pilots_v3_2_1/A01-R01 --pilot-dir $PL/pilots_v3_2_1/A01-R02 \
  --pilot-dir $PL/pilots_v3_2_1/A01-R03 --pilot-dir $PL/pilots_v3_2_1/A01-R04 \
  --pilot-dir $PL/pilots_v3_2_1/A01-R05 \
  --json $AUD/A01_records_v3.2.12.binary-275111d8.json \
  --binary-sha 275111d805a71bc3defa5a44758810e4753d99ea55e46a423cdd741002f06bb4

# A03 (2 groups)
python3 tools/lsu_12model_closure.py record --model A03 \
  --pilot-dir $PL/pilots_v3_2_2/A03-R01 \
  --json $AUD/A03_records_v3.2.12.binary-0fa610c2.json \
  --binary-sha 0fa610c21b6a3c40e2e67dd5588956e06746b6d85ce6782a8ffce3429f232bab
python3 tools/lsu_12model_closure.py record --model A03 \
  --pilot-dir $PL/pilots_v3_2_1/A03-R01 --pilot-dir $PL/pilots_v3_2_1/A03-R02 \
  --pilot-dir $PL/pilots_v3_2_1/A03-R03 --pilot-dir $PL/pilots_v3_2_1/A03-R04 \
  --pilot-dir $PL/pilots_v3_2_1/A03-R05 \
  --json $AUD/A03_records_v3.2.12.binary-275111d8.json \
  --binary-sha 275111d805a71bc3defa5a44758810e4753d99ea55e46a423cdd741002f06bb4

# FW02 (2 groups)
python3 tools/lsu_12model_closure.py record --model FW02 \
  --pilot-dir $PL/pilots_v3_2_1/FW02-R01 --pilot-dir $PL/pilots_v3_2_1/FW02-R04 \
  --pilot-dir $PL/pilots_v3_2_1/FW02-R05 \
  --json $AUD/FW02_records_v3.2.12.binary-275111d8.json \
  --binary-sha 275111d805a71bc3defa5a44758810e4753d99ea55e46a423cdd741002f06bb4
python3 tools/lsu_12model_closure.py record --model FW02 \
  --pilot-dir $PL/pilots_v3_2_4/FW02-R01 --pilot-dir $PL/pilots_v3_2_4/FW02-R05 \
  --json $AUD/FW02_records_v3.2.12.binary-b1f7cf18.json \
  --binary-sha b1f7cf189d2be1e90b8f682d2be97c057c78cfb8b58290c3631bb04f99578bea

# SQ01 (2 groups)
python3 tools/lsu_12model_closure.py record --model SQ01 \
  --pilot-dir $PL/pilots_v3_2_3/SQ01-R01 --pilot-dir $PL/pilots_v3_2_3/SQ01-R02 \
  --pilot-dir $PL/pilots_v3_2_3/SQ01-R03 --pilot-dir $PL/pilots_v3_2_3/SQ01-R04 \
  --pilot-dir $PL/pilots_v3_2_3/SQ01-R05 \
  --json $AUD/SQ01_records_v3.2.12.binary-8eb7ce8d.json \
  --binary-sha 8eb7ce8d76ab63d90dbd00694efb90c7c2545da47ad07ecf5325399274a3b682
python3 tools/lsu_12model_closure.py record --model SQ01 \
  --pilot-dir $PL/pilots_v3_2_4/SQ01-R01 --pilot-dir $PL/pilots_v3_2_4/SQ01-R02 \
  --pilot-dir $PL/pilots_v3_2_4/SQ01-R03 --pilot-dir $PL/pilots_v3_2_4/SQ01-R04 \
  --pilot-dir $PL/pilots_v3_2_4/SQ01-R05 \
  --json $AUD/SQ01_records_v3.2.12.binary-b1f7cf18.json \
  --binary-sha b1f7cf189d2be1e90b8f682d2be97c057c78cfb8b58290c3631bb04f99578bea

# DA04 (4 groups: 3 historical vintages + the SUPP raw-oracle vintage)
python3 tools/lsu_12model_closure.py record --model DA04 \
  --pilot-dir $PL/pilots_v3_2_4/DA04-R01 --pilot-dir $PL/pilots_v3_2_4/DA04-R02 \
  --pilot-dir $PL/pilots_v3_2_4/DA04-R03 --pilot-dir $PL/pilots_v3_2_4/DA04-R04 \
  --pilot-dir $PL/pilots_v3_2_4/DA04-R05 \
  --json $AUD/DA04_records_v3.2.12.binary-3e9148fc.json \
  --binary-sha 3e9148fc380c84917ddad84603e540b2e40e217918f392eb5659d32a56668297
python3 tools/lsu_12model_closure.py record --model DA04 \
  --pilot-dir $PL/pilots_v3_2_5/DA04-R04 --pilot-dir $PL/pilots_v3_2_5/DA04-R05 \
  --json $AUD/DA04_records_v3.2.12.binary-6808c56e.json \
  --binary-sha 6808c56e22b44eab3e189a1c51e6b90ec1c95e0c66d0c0835d205575572d7645
python3 tools/lsu_12model_closure.py record --model DA04 \
  --pilot-dir $PL/pilots_v3_2_6/DA04-R04 --pilot-dir $PL/pilots_v3_2_6/DA04-R05 \
  --json $AUD/DA04_records_v3.2.12.binary-0de25644.json \
  --binary-sha 0de2564468fd710bf1df22d2336acac0ea92f7bc1ef5780178f18f497a302d7d
python3 tools/lsu_12model_closure.py record --model DA04 \
  --pilot-dir $PL/pilots_v3_2_12/SUPP-DA04-R04 --pilot-dir $PL/pilots_v3_2_12/SUPP-DA04-R05 \
  --json $AUD/DA04_records_v3.2.12.binary-e527f26a.json \
  --binary-sha e527f26af7c2661995f456a2c96695ff6b366d5d787351172947ed259fad04ed

# LP01 (4 groups: 2 historical vintages + the same-context smoke run + SUPP)
python3 tools/lsu_12model_closure.py record --model LP01 \
  --pilot-dir $PL/pilots_v3_2_5/LP01-R01 --pilot-dir $PL/pilots_v3_2_5/LP01-R02 \
  --pilot-dir $PL/pilots_v3_2_5/LP01-R03 --pilot-dir $PL/pilots_v3_2_5/LP01-R04 \
  --pilot-dir $PL/pilots_v3_2_5/LP01-R05 \
  --json $AUD/LP01_records_v3.2.12.binary-69a1ca9c.json \
  --binary-sha 69a1ca9c5b1cbfb160d0502a8cad8acf7d17101625228978ec79ede588b2287d
python3 tools/lsu_12model_closure.py record --model LP01 \
  --pilot-dir $PL/pilots_v3_2_6/LP01-R01 --pilot-dir $PL/pilots_v3_2_6/LP01-R02 \
  --pilot-dir $PL/pilots_v3_2_6/LP01-R03 --pilot-dir $PL/pilots_v3_2_6/LP01-R04 \
  --pilot-dir $PL/pilots_v3_2_6/LP01-R05 \
  --json $AUD/LP01_records_v3.2.12.binary-0de25644.json \
  --binary-sha 0de2564468fd710bf1df22d2336acac0ea92f7bc1ef5780178f18f497a302d7d
python3 tools/lsu_12model_closure.py record --model LP01 \
  --pilot-dir $PL/pilots_v3_2_6/SMOKE_LP01-R01_final_binary \
  --json $AUD/LP01_records_v3.2.12.binary-6808c56e.json \
  --binary-sha 6808c56e22b44eab3e189a1c51e6b90ec1c95e0c66d0c0835d205575572d7645
python3 tools/lsu_12model_closure.py record --model LP01 \
  --pilot-dir $PL/pilots_v3_2_12/SUPP-LP01-R01 --pilot-dir $PL/pilots_v3_2_12/SUPP-LP01-R02 \
  --pilot-dir $PL/pilots_v3_2_12/SUPP-LP01-R03 --pilot-dir $PL/pilots_v3_2_12/SUPP-LP01-R04 \
  --pilot-dir $PL/pilots_v3_2_12/SUPP-LP01-R05 \
  --json $AUD/LP01_records_v3.2.12.binary-e527f26a.json \
  --binary-sha e527f26af7c2661995f456a2c96695ff6b366d5d787351172947ed259fad04ed

# MD04 (3 groups: 2 historical vintages + SUPP)
python3 tools/lsu_12model_closure.py record --model MD04 \
  --pilot-dir $PL/pilots_v3_2_6/MD04-R01 --pilot-dir $PL/pilots_v3_2_6/MD04-R02 \
  --pilot-dir $PL/pilots_v3_2_6/MD04-R03 --pilot-dir $PL/pilots_v3_2_6/MD04-R04 \
  --pilot-dir $PL/pilots_v3_2_6/MD04-R05 \
  --json $AUD/MD04_records_v3.2.12.binary-0de25644.json \
  --binary-sha 0de2564468fd710bf1df22d2336acac0ea92f7bc1ef5780178f18f497a302d7d
python3 tools/lsu_12model_closure.py record --model MD04 \
  --pilot-dir $PL/pilots_v3_2_7/MD04-R01 --pilot-dir $PL/pilots_v3_2_7/MD04-R02 \
  --pilot-dir $PL/pilots_v3_2_7/MD04-R03 --pilot-dir $PL/pilots_v3_2_7/MD04-R04 \
  --pilot-dir $PL/pilots_v3_2_7/MD04-R05 \
  --json $AUD/MD04_records_v3.2.12.binary-8377c011.json \
  --binary-sha 8377c011bb5916be67fa1132232440ae7f8be02351c3034624a339319a545bec
python3 tools/lsu_12model_closure.py record --model MD04 \
  --pilot-dir $PL/pilots_v3_2_12/SUPP-MD04-R02 --pilot-dir $PL/pilots_v3_2_12/SUPP-MD04-R03 \
  --pilot-dir $PL/pilots_v3_2_12/SUPP-MD04-R05 \
  --json $AUD/MD04_records_v3.2.12.binary-e527f26a.json \
  --binary-sha e527f26af7c2661995f456a2c96695ff6b366d5d787351172947ed259fad04ed

# FW05 (2 groups)
python3 tools/lsu_12model_closure.py record --model FW05 \
  --pilot-dir $PL/pilots_v3_2_7/FW05-R01 --pilot-dir $PL/pilots_v3_2_7/FW05-R02 \
  --pilot-dir $PL/pilots_v3_2_7/FW05-R03 --pilot-dir $PL/pilots_v3_2_7/FW05-R04 \
  --pilot-dir $PL/pilots_v3_2_7/FW05-R05 \
  --json $AUD/FW05_records_v3.2.12.binary-8377c011.json \
  --binary-sha 8377c011bb5916be67fa1132232440ae7f8be02351c3034624a339319a545bec
python3 tools/lsu_12model_closure.py record --model FW05 \
  --pilot-dir $PL/pilots_v3_2_12/SUPP-FW05-R02 --pilot-dir $PL/pilots_v3_2_12/SUPP-FW05-R03 \
  --pilot-dir $PL/pilots_v3_2_12/SUPP-FW05-R04 --pilot-dir $PL/pilots_v3_2_12/SUPP-FW05-R05 \
  --json $AUD/FW05_records_v3.2.12.binary-e527f26a.json \
  --binary-sha e527f26af7c2661995f456a2c96695ff6b366d5d787351172947ed259fad04ed

# SQ03 (1 group)
python3 tools/lsu_12model_closure.py record --model SQ03 \
  --pilot-dir $PL/pilots_v3_2_8/SQ03-R01 --pilot-dir $PL/pilots_v3_2_8/SQ03-R02 \
  --pilot-dir $PL/pilots_v3_2_8/SQ03-R03 --pilot-dir $PL/pilots_v3_2_8/SQ03-R04 \
  --pilot-dir $PL/pilots_v3_2_8/SQ03-R05 \
  --json $AUD/SQ03_records_v3.2.12.binary-b988b750.json \
  --binary-sha b988b7503cdf1feab10b99d09ec85df84b42eb385396142e0b7be6a197c63a45

# LQ04 (1 group: 5 fault pilots + 5 by-design determinism controls)
python3 tools/lsu_12model_closure.py record --model LQ04 \
  --pilot-dir $PL/pilots_v3_2_10/LQ04-CONTROL-R01 --pilot-dir $PL/pilots_v3_2_10/LQ04-CONTROL-R02 \
  --pilot-dir $PL/pilots_v3_2_10/LQ04-CONTROL-R03 --pilot-dir $PL/pilots_v3_2_10/LQ04-CONTROL-R04 \
  --pilot-dir $PL/pilots_v3_2_10/LQ04-CONTROL-R05 --pilot-dir $PL/pilots_v3_2_10/LQ04-R01 \
  --pilot-dir $PL/pilots_v3_2_10/LQ04-R02 --pilot-dir $PL/pilots_v3_2_10/LQ04-R03 \
  --pilot-dir $PL/pilots_v3_2_10/LQ04-R04 --pilot-dir $PL/pilots_v3_2_10/LQ04-R05 \
  --json $AUD/LQ04_records_v3.2.12.binary-f3c2a442.json \
  --binary-sha f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694
```

### 2.2 The 7 pending groups (add after their owning task lands; template)

Substitute `<FINAL_BINARY_SHA256>` (gate P2) and the exact dir names produced by the
task; `--model` is still required explicitly (SUPP name-based inference is used only by
the `missing` subcommand):

```bash
# Task 7  (A01 SUPP re-runs + matched controls)
python3 tools/lsu_12model_closure.py record --model A01 \
  --pilot-dir $PL/pilots_v3_2_12/SUPP-A01-R01 ... \
  --json $AUD/A01_records_v3.2.12.binary-<final-sha8>.json \
  --binary-sha <FINAL_BINARY_SHA256>
# Task 8  (A03): --model A03, dirs SUPP-A03-R01..R05 (+ controls)
# Task 9  (FW02): --model FW02, dirs SUPP-FW02-R01..R05
# Task 11 (SQ01, on sq_reload_v3212): --model SQ01, dirs SUPP-SQ01-R01..R05
# Task 12 (SQ03, on sq_reload_v3212): --model SQ03, dirs SUPP-SQ03-R01..R05
# Task 13 (SP05, on sq_reload_v3212): --model SP05, dirs SUPP-SP05-R01..R05
# Task 15 (RP01): --model RP01, dirs RP01-R01..R05 + RP01-CONTROL-R01..R05
```

Record JSONs are committed inputs (plan Task 16 Step 4 / Task 17 Step 3): they are the
only inputs `matrix`/`features` consume, and they embed each record's `EvidencePath` —
do not move or rename pilot directories between record and matrix.

---

## 3. Exact `matrix` / `features` invocations (Task 16 Step 1, Task 17 Step 1)

`--records` is `action="append"`: it must be repeated per file. A bare shell glob
**fails** (`argparse` treats the extra paths as positionals →
`error: unrecognized arguments` — verified 2026-11-10), so build the argument list with a
loop:

```bash
RECS=""
for f in $AUD/*_records_v3.2.12.binary-*.json; do RECS="$RECS --records $f"; done
python3 tools/lsu_12model_closure.py matrix $RECS \
  --out $AUD/LSU_12Model_Propagation_Closure_Matrix.csv
python3 tools/lsu_12model_closure.py features $RECS \
  --out $AUD/LSU_12Model_Diagnostic_Feature_Dataset.csv
```

Expected final outputs (file names frozen by the plan):

- `$AUD/LSU_12Model_Propagation_Closure_Matrix.csv` — 24 columns, one row per
  (model, binary) group: **≈30 rows expected** (23 groups of §2.1 + 7 groups of §2.2),
  12 distinct base model IDs after stripping `@<sha8>`.
- `$AUD/LSU_12Model_Diagnostic_Feature_Dataset.csv` — 39 columns, one `RowKind=PILOT`
  row per record plus one `RowKind=PATH_FRAGMENT` row per verified fragment in canonical
  chain order (dry run over 92 records: 92 + 288 = 380 rows).
- Task 16 also writes `$AUD/LSU_12Model_Propagation_Closure_Summary_v3.2.12.md` (per-model
  paragraphs; numbers derived from the matrix CSV, never from v3.2.11 summaries).

Both writers re-validate every record and raise (no partial CSV) on: any blank cell, a
bare `PASS` outside `ApplicationOracle`, or a complete verdict over
`InjectionVerified=no` / `ActivationVerified=no`.

---

## 4. Column mapping — brief §11 (24 matrix columns) and brief §12 (five feature groups)

Authority in-repo: `CLOSURE_INPUTS_v3.2.12.md` §1.2/§2 (transcription of the researcher
brief §11/§12; the verbatim brief itself is **not** in the repository — CLOSURE_INPUTS
§5 "open input"). Tool constants:

- `CLOSURE_MATRIX_COLUMNS` — `tools/lsu_12model_closure.py:141-151`
- `FEATURE_GROUP_COLUMNS` (= `FEATURE_DATASET_COLUMNS`) — `tools/lsu_12model_closure.py:156-176`

### 4.1 The 24 closure-matrix columns (brief §11 == tool constant, exact order)

`ModelID, SubUnit, FaultDefinition, PilotCount, InjectionVerified, ActivationVerified,
EarlyAnomalyVerified, IntermediatePropagationVerified, RegisterWritebackVerified,
ConsumerVerified, CommitVerified, TerminalVerified, OracleVerified, RecordIntegrity,
TraceCompleteness, StructuralChainCompleteness, FaultEffectPropagationCoverage,
ObservedTerminal, ApplicationOracle, FaultCausality, FinalClassification,
MissingEvidence, SupplementaryPilotRequired, EvidencePath`

Notes: the first 13 are the v3.2.11 audit-matrix columns (`EvidencePaths` renamed
`EvidencePath`); the 20 v3.2.11 columns plus the four standard fields
(`RecordIntegrity, TraceCompleteness, StructuralChainCompleteness,
FaultEffectPropagationCoverage`) and the closure additions
(`ObservedTerminal, ApplicationOracle, FaultCausality, FinalClassification,
MissingEvidence, SupplementaryPilotRequired, EvidencePath`). Stage columns aggregate
per group as `yes(n/n)` / `mixed(...)` (`_agg`); `SupplementaryPilotRequired` counts the
union of stage-gap codes in `STAGE_GAP_CODES`; `ModelID` becomes `MODEL@<sha8>` whenever a
model spans >1 binary.

### 4.2 The five feature groups (brief §12 == tool constant, 39 columns)

1. provenance/identity (13): `ModelID, PilotID, SampleRunID, Seed, EventOrdinal,
   BinarySHA256, WorkloadSHA256, EvidencePath, RowKind, FragmentOrdinal, FragmentStage,
   FragmentEventID, SupplementaryOf`
2. injection site (6): `PrimaryFaultModel, InjectionSeq, InjectionPC, InjectionTick,
   ActivationStatus, InjectionCount`
3. chain path (8): `ChainEventCount, ChainEdgeCount, EarliestAnomalyType,
   EarliestAnomalyEventID, WritebackValueFnv, ConsumerInputFnv, ConsumerSourceLinked,
   CommitSeq`
4. outcome (5): `ObservedTerminal, TerminalReason, ApplicationOracle, OracleExpected,
   OracleActual`
5. verdict (7): `RecordIntegrity, TraceCompleteness, StructuralChainCompleteness,
   FaultEffectPropagationCoverage, FaultCausality, FinalClassification, MissingEvidence`

### 4.3 Fields the tool does NOT yet emit in either CSV (flag)

No brief-§11/§12 column is missing from the two CSVs (the lists above are byte-equal to
the tool constants). But these tool-computed, standard-mandated **record** fields exist
only in the record JSON / record stdout and appear in **neither** CSV:

- `MaskingMechanism` (standard §10 exception E1 outcome field) — needed to show *why* the
  LQ04 complete verdicts are MASKED;
- `MemoryResponseAssociation`, `WritebackAssociation` (standard §10 E1 evidence fields);
- `AdjudicatedTerminal`, `VerifiedChainCount`, `ChainKinds`, `Stages`,
  `InjectionVerified`/`ActivationVerified` (raw yes/no; the matrix aggregates them).

If the verbatim brief §11/§12 (held by the main agent) requires any of these as a
matrix/dataset column, **the tool does not yet emit it there** — the executor must get a
tool patch approved (one-patch-per-unit) rather than hand-filling cells. Until then, the
Task 16 summary MD should quote `MaskingMechanism` from the record JSONs (it is
tool-computed, so quoting it is not a hand-set verdict). Re-check the column lists
against the verbatim brief before generating (§5 check 7).

---

## 5. Post-generation checks (Task 16 Step 2 / Task 17 Step 2; run all, quote real output)

```bash
# 0) writers completed (both print the record count)
#    expected final: matrix records = 92 + (Task 7-15 pilot count; RP01 adds 10)

# 1) 12 model IDs present (strip the @sha8 binary suffix; physical rows are ~30, NOT 12)
cut -d, -f1 $AUD/LSU_12Model_Propagation_Closure_Matrix.csv | tail -n +2 \
  | sed 's/@.*//' | sort -u
#   expected exactly: A01 A03 DA04 FW02 FW05 LQ04 LP01 MD04 RP01 SP05 SQ01 SQ03
#   FAILS today (dry run: only 10 — SP05/RP01 have no pilots until Tasks 13/15)

# 2) no blank cells in either CSV
python3 - <<'PY'
import csv
for name in ("LSU_12Model_Propagation_Closure_Matrix.csv",
            "LSU_12Model_Diagnostic_Feature_Dataset.csv"):
    rows = list(csv.reader(open(f"docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/{name}")))
    blanks = [(r[0], i) for r in rows[1:] for i, c in enumerate(r) if not c.strip()]
    print(name, "rows:", len(rows) - 1, "blank cells:", len(blanks))
PY
#   expected: blank cells: 0 in both (the writer also raises on any blank)

# 3) no COMPLETE verdict over InjectionVerified=no (record level; the writer raises too)
python3 - <<'PY'
import glob, json
bad = []
for f in glob.glob("docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/*_records_v3.2.12.binary-*.json"):
    for r in json.load(open(f))["records"]:
        if r["FinalClassification"] in ("COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT") \
           and (r["InjectionVerified"] != "yes" or r["ActivationVerified"] != "yes"):
            bad.append((r["PilotID"], r["BinarySHA256"][:8]))
print("complete-over-unverified defects:", bad)
PY
#   expected: [] (tool-enforced; this check is the belt to the writer's braces)

# 4) LQ04 complete/masked (E1): every LQ04 fault pilot MASKED + complete + named mechanism
python3 - <<'PY'
import json
recs = json.load(open("docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/"
                      "LQ04_records_v3.2.12.binary-f3c2a442.json"))["records"]
fault = [r for r in recs if not r["PilotID"].startswith("LQ04-CONTROL")]
ctrl   = [r for r in recs if r["PilotID"].startswith("LQ04-CONTROL")]
print("fault pilots:", [(r["PilotID"], r["ObservedTerminal"], r["FinalClassification"],
      r["MaskingMechanism"]) for r in fault])
print("controls:", {r["FinalClassification"] for r in ctrl},
      "terminals:", {r["ObservedTerminal"] for r in ctrl})
PY
#   expected: all five LQ04-R0x = MASKED + COMPLETE_CAUSAL_CHAIN +
#   RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE; controls = UNRESOLVED / NO_INJECTION
#   (by design — determinism replications). Matrix row (dry-run observed):
#   ObservedTerminal=mixed(MASKED=5;NO_INJECTION=5),
#   FinalClassification=mixed(COMPLETE_CAUSAL_CHAIN=5;UNRESOLVED=5).

# 5) SUPP-MD04-R05 per-binary split retained (never merged)
grep -c '^MD04@' $AUD/LSU_12Model_Propagation_Closure_Matrix.csv   # expected 3 rows:
#   MD04@0de25644 (originals incl. MD04-R05 MASKED), MD04@8377c011 (re-run vintage),
#   MD04@e527f26a (SUPP incl. SUPP-MD04-R05 SQUASHED/PARTIAL — the recorded
#   adjudication delta of MissingEvidenceMatrix_v3.2.12.md §4)
#   and confirm the record pair stayed split:
python3 - <<'PY'
import json
o = [r for r in json.load(open("docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/"
    "MD04_records_v3.2.12.binary-0de25644.json"))["records"] if r["PilotID"] == "MD04-R05"][0]
s = [r for r in json.load(open("docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/"
    "MD04_records_v3.2.12.binary-e527f26a.json"))["records"] if r["PilotID"] == "SUPP-MD04-R05"][0]
print("original :", o["BinarySHA256"][:8], o["ObservedTerminal"], o["FinalClassification"])
print("SUPP     :", s["BinarySHA256"][:8], s["ObservedTerminal"], s["FinalClassification"])
PY
#   expected (dry-run observed): original 0de25644 MASKED VERIFIED_SINGLE_CONTEXT
#                                (upgraded to COMPLETE_CAUSAL_CHAIN inside its binary
#                                group by the >=2-context rule, standard §4)
#                                SUPP e527f26a SQUASHED PARTIAL — two rows, never merged.

# 6) RP01 rows present after Task 15
grep '^RP01' $AUD/LSU_12Model_Propagation_Closure_Matrix.csv
#   expected: one RP01@<final-sha8> row, PilotCount=10 (RP01-R01..R05 + RP01-CONTROL-R01..R05).
#   Before Task 15 there is NO RP01 row at all — the closure matrix adds no rows for
#   models without records (the missing-evidence matrix carries the pilot-set row).

# 7) feature-dataset checks
python3 - <<'PY'
import csv
from collections import Counter
p = "docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LSU_12Model_Diagnostic_Feature_Dataset.csv"
rows = list(csv.reader(open(p))); hdr = rows[0]
ki = {n: hdr.index(n) for n in hdr}
data = rows[1:]
print("columns:", len(hdr), "rows:", len(data),
      "RowKind:", Counter(r[ki["RowKind"]] for r in data))
print("rows missing ModelID/PrimaryFaultModel/InjectionTick/ObservedTerminal:",
      sum(1 for r in data if any(not r[ki[c]].strip() for c in
          ("ModelID", "PrimaryFaultModel", "InjectionTick", "ObservedTerminal"))))
print("LIFECYCLE_ONLY rows with zeros (must be 0):",
      sum(1 for r in data if r[ki["FinalClassification"]] == "LIFECYCLE_ONLY"
          and ("0" in (r[ki["ConsumerInputFnv"]], r[ki["CommitSeq"]]))))
ordinals = {}
ok = True
for r in data:
    if r[ki["PilotID"]] in ordinals and r[ki["EventOrdinal"]] != ordinals[r[ki["PilotID"]]]:
        ok = False
    ordinals[r[ki["PilotID"]]] = r[ki["EventOrdinal"]]
print("EventOrdinal constant per pilot block:", ok)
PY
#   expected: every check green (dry-run observed values in §7).

# 8) acceptance arithmetic (Task 16 Step 2) — derive from the matrix CSV only:
#    count models with >=2 complete contexts; list the terminal distribution; flag any
#    model whose only complete chain is single-context (VERIFIED_SINGLE_CONTEXT must
#    not be hand-upgraded; the tool upgrades inside a binary group via the >=2-context
#    rule only). Quote the counts in the summary MD.
```

All check commands are read-only; quote their real output in the summary MD.

---

## 6. Evidence still missing at runbook time and which task produces it

| Model | Missing record set / evidence | Owning task | Status at 2026-11-10 |
|---|---|---|---|
| A01 | `SUPP-A01-R01..R05` + matched controls; closes the 4 open raw-oracle rows (A01-R01/R02/R04/R05, `RequiredRunCount=1`) and the A01 crash/squash attribution; needs the `a01_ea`/`a01_consumed` trace nodes (code committed `3d7b11c5`, `672ce9ac`) | **Task 7** | in progress |
| A03 | `SUPP-A03-R01..R05` + controls; F5 stuck-at stream (`a03_stream`/`a03_activation`, committed `ddaba767`); 19 open missing-evidence rows | **Task 8** | code ready, pilots not run |
| FW02 | `SUPP-FW02-R01..R05`; forwarding-decision chain (`fw02_decision`, committed `7c67fa99`); 9 open rows | **Task 9** | in progress |
| SQ01 | `SUPP-SQ01-R01..R05` on `sq_reload_v3212` (workload done, Task 10); 30 open rows | **Task 11** | pending |
| SQ03 | `SUPP-SQ03-R01..R05` on `sq_reload_v3212` (`sq03_effect`); 15 open rows | **Task 12** | pending |
| SP05 | `SUPP-SP05-R01..R05` on `sq_reload_v3212` (`sp05_stage`); **no pilot directory at all today** (only `evidence_v3_2_9` extracted rows) — model absent from any pre-Task-13 matrix | **Task 13** | pending |
| RP01 | `RP01_CountOnly_Preflight_v3.2.12.csv` (Task 14) + `RP01-R01..R05` and `RP01-CONTROL-R01..R05` (Task 15); selector + hooks committed (`778abce1`, `512d937c`), simulator wiring rebased in an isolated worktree | **Tasks 14–15** | pending |
| all | **Final rebuilt binary + SHA** (gate P2): every Task 7–15 pilot needs the new trace nodes that are not in `e527f26a…` | global | pending |

Downstream (not Task 16/17's to fix, listed to avoid scope creep): Task 18 W1–W8
baselines + full suite on the final binary; Task 19 Excel v3.2.7; Task 20 package/report
(needs the verbatim brief §15/§16 from the main agent).

---

## 7. Dry run — pipeline validation on currently available roots (real, executed 2026-11-10)

Purpose: validate the exact §2/§3 pipeline (record per binary group → matrix → features)
**without producing a final verdict** — everything writes to `/tmp`, nothing touches the
repo, and the output covers only 10 of 12 models with pre-Task-7–15 evidence.

```bash
DRY=/tmp/lsu_closure_dryrun_3212 && mkdir -p $DRY
# 1) record: the 23 commands of §2.1 with --json $DRY/<MODEL>_records.binary-<sha8>.json
#    (a ready-made script with the exact 23 commands is kept at
#     $DRY/record_commands.sh by this runbook's preparation run)
bash $DRY/record_commands.sh           # 23 invocations, all exit 0
# 2) matrix + features over the dry-run records
RECS=""; for f in $DRY/*_records.binary-*.json; do RECS="$RECS --records $f"; done
python3 tools/lsu_12model_closure.py matrix  $RECS --out $DRY/LSU_12Model_Propagation_Closure_Matrix_DRYRUN.csv
python3 tools/lsu_12model_closure.py features $RECS --out $DRY/LSU_12Model_Diagnostic_Feature_Dataset_DRYRUN.csv
```

**Real observed output (2026-11-10):**

```
record: 23 invocations over 92 pilot dirs → exit 0 (per-group stdout kept in $DRY/<MODEL>_<sha8>.stdout)
  e.g. LQ04 group:
  model=LQ04 pilots=10
    LQ04-CONTROL-R01: FinalClassification=UNRESOLVED ObservedTerminal=NO_INJECTION MaskingMechanism=NOT_APPLICABLE missing=[NO_INJECTION_EVENT;TERMINAL_UNRESOLVED]
    ...
    LQ04-R01: FinalClassification=COMPLETE_CAUSAL_CHAIN ObservedTerminal=MASKED MaskingMechanism=RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE missing=[none]

matrix  → closure matrix written to …DRYRUN.csv (records=92)     # 24 columns, 23 rows, 0 blank cells
features→ feature dataset written to …DRYRUN.csv (records=92)    # 39 columns, 380 rows
          RowKind: {'PATH_FRAGMENT': 288, 'PILOT': 92}, 0 blank cells,
          0 rows missing required fields, 0 LIFECYCLE_ONLY rows with zeros,
          EventOrdinal constant per pilot block: True
```

Dry-run matrix shape (the honest current state, **not** the final verdict): 23 rows over
10 base models (SP05, RP01 absent); per-binary splits exactly as §1.1, e.g.
`A01@275111d8` (5 pilots, `mixed(LIFECYCLE_ONLY=3;PARTIAL=1;UNRESOLVED=1)`),
`A03@275111d8` (`CRASH(5/5)` → `UNRESOLVED`), `SQ01@8eb7ce8d`/`b1f7cf18` and
`SQ03@b988b750` (`NO_INJECTION(5/5)` → `UNRESOLVED` — the open stage gaps Tasks 7–13
close), `DA04@e527f26a` (`SDC(2/2)`, oracle `FAIL(2/2)` — the SUPP vintage's own
observation, kept separate from the historical vintages), `LQ04` per §5 check 4, and the
`MD04@…` triple split per §5 check 5. These values will change only where Tasks 7–15 add
records; historical-vintage rows are stable by construction (committed artifacts,
deterministic tool).

---

## 8. Honesty notes for the Task 16/17 executor

1. Verdicts are tool-computed only; never hand-set or "corrected" in the CSVs. If a
   number looks wrong, fix the evidence or the tool (one patch per unit), regenerate.
2. `ConfigFrozen=NO`, formal `ExecutionStatus=NOT_STARTED` everywhere; no historical
   pilot, trace, golden, SampleRunID or Seed is modified; all outputs go to the
   `*_v3_2_12` namespace.
3. The dry run and every §5 check output are quoted in the summary MD with real output;
   a model below `COMPLETE_CAUSAL_CHAIN` is stated as such with the missing link named.
4. The matrix row count is ~30, not 12: the per-binary split is a feature (standard §2),
   not a defect; report both the 12 base models and the per-binary rows.
5. If a Task 7–15 pilot set lands on more than one binary (mid-round rebuild), record one
   group per binary — never fold them; the expected row count grows accordingly.
