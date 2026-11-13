# LSU v3.3.3 — Final Preservation Report

**Date:** 2026-11-13
**Campaign:** `LSU-V333-FINAL-20261112`
**Status:** preservation and verification round; **no deletion executed**.

## 1. Executive summary

The formal campaign is preserved as (a) one GitHub freeze branch based on the real formal source lineage, (b) one external raw-data archive with two independent on-host copies, and (c) a complete 120-run manifest with source, workload/context and per-run hashes. All deletion work is deferred to `LSU_Proposed_Deletion_Plan.md` and requires explicit approval.

## 2. Frozen identities

| Item | Value |
|---|---|
| Formal build source commit (C++ content) | `e329385616ba6c5f13bf44bc019e829d27e0c81f` |
| Final tooling commit / freeze base | `7067805d9d24b185872cc06e3768a1e4dc5fa475` |
| Binary SHA256 | `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd` |
| Config SHA256 | `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` |
| Results ZIP SHA256 | `cece176a894edf139209c21fd219d031f4c0ea99a60cc2664addd743ac2df235` |
| Freeze branch | `lsu-formal-v3.3.3-frozen` |
| Archive tag | `lsu-v3.3.3-formal-accepted` |
| C++ drift `e3293856..7067805d` | 0 files under `CHAOS/gem5/src/` |

## 3. Archive

Location: `/home/sdc/lsu-v333-archive/` (outside every git worktree).

| Component | Size | Verification |
|---|---|---|
| `raw/LSU_v3.3.3_Final_Formal_Results_Accepted.zip` | 400,982,936 B | SHA `cece176a…`; `unzip -t` OK |
| `raw_extracted/formal_v333_final_20261112/` | 6,666,122,615 B logical | `SHA256SUMS.raw_runs` 2193/2193 OK; `SHA256SUMS.deliverables` 22/22 OK |
| `binary/gem5.opt.v333-62e1b1be` | 1,149,269,352 B | SHA `62e1b1be…`; real copy (distinct inode) |
| `build/build.log` | 98,134 B | archived |
| `config/lsu_proxy.py` | 68,993 B | SHA `8309da72…` |
| `manifests/` | 230,023 B | `SOURCE_MANIFEST.sha256` 7/7 OK + `final_config/` |
| `packages/` | 276,250,941 B | 9 ZIPs + README, 10/10 hashes OK |
| `analysis/` reports + approval packet | small text/CSV | hashes recorded in the packet |
| **Total archive** | **8,493,366,604 B live at final report time** | grows by the approval packet |

Two independent recoverable copies exist on host: the worktree ZIP + archive ZIP/extracted tree; the formal binary exists in the worktree and as an archive byte copy. **No off-host copy was made** — the GitHub repo is public and publishing raw data needs explicit approval.

## 4. Formal data

- 120 runs: 60 fault + 60 control; 120 attempts, all `attempt_001`; 0 retries.
- Campaign index: 120 tasks — `COMPLETED` 77, `ORACLE_FAIL` 43 (terminal SDC evidence), `FAILED`/`TIMEOUT`/`HASH_MISMATCH`/`OUTPUT_INCOMPLETE` all 0.
- 43/43 `ORACLE_FAIL` are `terminal=SDC`, `crash_by_fault=0`, `parse_error=0`.
- Controls: 60/60 injection count 0. Faults: 60/60 injection count > 0.
- Frozen identity (`62e1b1be`, `8309da72`, `LSU-V333-FINAL-20261112`) verified in manifest/campaign/summary for all 120 runs.
- Trace coverage: 105 runs with `trace_v31.jsonl`; 15 direct-driver runs (A03 fault R01–R05; RP01 fault+control R01–R05) without it, all 120 with `prop_trace.csv.gz`. Documented design property, not loss.
- Non-run dirs preserved: `collector_full`, `collector_manifest`, `collector_manifest.stage2-failed-20261113` (marked `NON_CANONICAL`).
- Pilot/Pre-Formal evidence is separated in `LSU_Formal_vs_Pilot_Separation.csv` and never merged.

## 5. Workloads and contexts

- 12 models × 5 contexts × 2 roles; 60 unique SampleRunIDs; 60 unique seeds; every fault/control pair shares its SampleRunID and seed.
- 9 executed ELF SHA256 values, all 9 verified against `campaign_identity.json`.
- ROI/percentile/ordinal evidence present for all 60 contexts: percentiles 10/30/50/70/90, 5 distinct ordinals per model, ordinals inside ROI 120/120.
- `fw05_forward` has source + ELF but no compile script; source-to-ELF rebuild not performed.

## 6. Statistics

| Requested statistic | Value |
|---|---|
| Current server LSU historical data | `/home/sdc/gem5-fi-ding` = 106,654,468,899 B (99.36 GiB), including 71,859,291,930 B (66.90 GiB) of 37 worktrees and 26,584,078,529 B (24.77 GiB) of `runs/lsu` |
| Formal-required size | formal worktree 33,138,839,347 B (30.86 GiB) + archive 8.49 GB; minimum preserved copy = archive 8.49 GB |
| Archived and verified | 8,493,366,604 B (7.91 GiB) at final report time |
| Cleanup candidate size | 52,247,674,557 B (48.66 GiB) standalone (40 rows; duplicates excluded to avoid double counting) |
| Old LSU branches deletable | 35 local + 38 remote = 73, plus 36 stale tracking refs (metadata); pending approval |
| Branches that must be kept | 36 active-worktree + 8 unique-unarchived + 4 baseline + 2 formal-base + 1 tagged = 51; 46 non-LSU out-of-scope |
| Archive copies | 2 independent on-host (worktree ZIP + archive ZIP/extracted); binary 2 (worktree + archive) |
| Remote freeze branch pushed | **YES** — `origin/lsu-formal-v3.3.3-frozen`; verified at `45eb57c1…` before this verification commit |
| Remote reproduction | **PASS 9/10** — independent audit ACCEPT; check 5 test gate PARTIAL (state- and path-dependent failures documented) |
| Independent audit | `LSU_Independent_Acceptance_v333_Preservation.md` — ACCEPT, no blocking findings |
| Archive tag | `lsu-v3.3.3-formal-accepted`; tag object `fcb87d9a…`, target commit `510da9f3…`; tag message records the verified parent and the three identities |

## 7. Preservation warnings

- The stale `audit_v3_3_3/LSU_Final_Binary_Provenance.md` (`1126e0fd`) is superseded by `trace_closure/final_config/LSU_Final_Binary_Provenance.md` (`62e1b1be`); preserved, never cited as formal.
- `audit_v3_3_2/binary/gem5.opt.v332-070d68a6` is a hardlink to the formal binary despite its name; the real v3.3.2 `070d68a6` binary is not preserved under its own name.
- Main-repo `build/ARM/gem5.opt` (`6db026e7…`) is a different build; never substitute.

## 8. Reproduction result

- Fresh shallow clone from `origin/lsu-formal-v3.3.3-frozen`; HEAD matched the remote; `CHAOS/gem5/src` subtree `fdcf53f6…` identical to the freeze base; zero C++ drift.
- Source manifest 7/7, config `8309da72…`, binary `62e1b1be…` (supplied from the archive; the 1.1 GB binary is intentionally not in git).
- 120-task dry run: 120 tasks, 60 unique SampleRunIDs, 60 unique seeds, 9/9 ELF hashes, pairing OK, `READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES`.
- Raw archive: `SHA256SUMS.raw_runs` 2193/2193 OK; `SHA256SUMS.deliverables` 22/22 OK.
- Regenerated reports: 7 CSVs byte-identical; 3 path-bearing collector CSVs normalized-identical; both XLSX files cell-identical after path normalization; readiness 38/12/5/5; 60/60 control zero-injection.
- Test gate: **PARTIAL**. Clone 294 passed / 38 failed / 1 skipped; original worktree control 316 / 4 / 13. The 4 launch-acceptance failures are identical in both and caused by the now-existing campaign root (pre-launch tests); clone extras are path-hardcoded manifest tests and missing historical run fixtures. Path-insensitive subset: 145 passed, 1 skipped. No evidence of archive corruption.
- No experiment was rerun; no byte-identical binary rebuild is claimed.

## 9. Deletion status

No deletion was executed. The approval-gated plan is `LSU_Proposed_Deletion_Plan.md`; the machine-readable candidates are the two cleanup CSVs. D4 (25 worktrees, 24.52 GB) and D5 (pilot run data, 26.58 GB) are irreversible because that data is not archived.
