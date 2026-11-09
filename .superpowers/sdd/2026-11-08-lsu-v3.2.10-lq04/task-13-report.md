# Task 13 report — Package, provenance and SHA256 manifest

**Date:** 2026-11-09
**Branch:** `lsu-platform-v3.2.10`
**Packaging HEAD:** `a175559b57bfc8e4b37e1b1d1e880255114aa85e` (24 commits after base `37692d2beffcb73fc9303ad9de4c6bb341d5de71`)
**Package commit:** `7ce06f415bd7e83c431aa194ffe33bf1d3a053c7` (pushed to `origin/lsu-platform-v3.2.10`)

## Deliverables

- `LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip` — 12,355,786 bytes (11.8 MiB),
  225 entries (191 files + 34 directory entries), 355,674,595 bytes uncompressed.
- `LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip.sha256` — sidecar, verified
  with `sha256sum -c` (OK).
- `docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v3210.txt` — branch, full HEAD,
  base, 24-commit log, binary/workload/workbook SHA256s, packaging date.
- `docs/gem5-fi/lsu/implementation_v3_2/GIT_STATUS_v3210.txt` — `git status --short`
  captured at packaging time with honest annotations (see Omissions §3).
- `docs/gem5-fi/lsu/implementation_v3_2/GIT_DIFF_CODE_v3210.txt` — limited code diff
  (23 files, 3,175 lines): CHAOSLQ04/, CHAOSPropagation/, lsq_unit.hh/.cc, cpu.hh,
  configs/se/lsu_proxy.py, tests/, tools/build_lsu_v325_workbook.py,
  docs/superpowers/ (plan + spec), platform .py files.
- `docs/gem5-fi/lsu/implementation_v3_2/GIT_DIFF_STAT_v3210.txt` — full
  `git diff --stat 37692d2b..HEAD` (169 files, +239,599/−20, binaries listed).
- `docs/gem5-fi/lsu/implementation_v3_2/DELIVERABLES_SHA256_v3210.txt` — sorted
  SHA256 of all 190 packaged files (paths relative to package root; the manifest
  does not hash itself). Cross-checked: `comm -3` of staged files vs manifest
  entries = 0 differences.

## Verified identity values (re-verified at packaging time, 2026-11-09)

| Item | Value |
|---|---|
| Binary `build/ARM/gem5.opt` | `f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694` |
| Binary `CHAOS/gem5/build/ARM/gem5.opt` | `f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694` (identical) |
| Workload `lq_lifetime_ordinal` | `fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba` |
| Workload golden | `checksum=0xb097eb83f71545cb` |
| Excel v3.2.5 workbook (current SHA) | `1acb482dc163a5804b6654e2f0ae9c1c902fa4ef82575b59c18de6e7cbeacd45` |
| `MODEL_STATUS_MATRIX.csv` LQ04 row | `1,1,1,1,1,1,0` (stages 1–6 done, PROPAGATION_VERIFIED 0) |
| Package zip SHA256 | `a0b46928c350fe49097b9d91dbc3839255646154d282a10a3ffa247c29a0d082` |

## Section checklist (24/24 present, verified with `unzip -l`)

| # | Section | Contents | State |
|---|---|---|---|
| 01 | baseline_verification | `LSU_v3.2.10_Baseline_Verification.md` | OK |
| 02 | lq04_original_definition | `LQ04_Definition_Freeze_v3.2.10.md` | OK |
| 03 | source_audit | `LQ04_Source_Audit_v3.2.10.md` | OK |
| 04 | safety_analysis | `SAFETY_ANALYSIS_LOCATION.md` — pointer naming audit §1.8/§3/§4 + runtime evidence (pointer file per brief) | OK |
| 05 | implementability_verdict | `IMPLEMENTABILITY_VERDICT.md` — spec §3 / freeze §4 pointer with verbatim gate quote | OK |
| 06 | cpp_hook | CHAOSLQ04.{hh,cc,py}, SConscript, lq04_rules.hh, lsq_unit.{hh,cc}, CHAOSPropagation.{hh,cc} (9 files) | OK |
| 07 | config_parsing | `configs/se/lsu_proxy.py` (full file) | OK |
| 08 | eventordinal | lq04_rules.hh + CHAOSLQ04.cc + `executeLoad_hook_excerpt.cc` (lsq_unit.cc:795–830) | OK |
| 09 | git_diff | GIT_DIFF_CODE_v3210.txt + GIT_DIFF_STAT_v3210.txt | OK |
| 10 | unit_tests | test_lq04_rules.cc, test_lq04_platform.py, test_lsu_v325_workbook.py + fresh run logs: C++ host test `LQ04 ordinal/identity rules: PASS` exit=0; pytest **18 passed** exit=0 | OK |
| 11 | watchdog_timeout_tests | copies of the Task 5 watchdog run artifacts: stdout (line 23 `CHAOS_LQ04_WATCHDOG_EXPIRED: ... tick=385000`) + `lq04_injections.log` + provenance note | OK |
| 12 | build_log | build_lq04.log, binary_v3210.sha256, regression_lq04.txt | OK |
| 13 | five_pilots | LQ04-R01..R05 complete (65 files, incl. 5× lq04_injections.log) | OK |
| 14 | five_controls | LQ04-CONTROL-R01..R05 complete (60 files, no injections log by construction) | OK |
| 15 | trace_jsonl | 10 copies `LQ04-*.trace_v31.jsonl` (plus the 10 originals inside 13/14 → 20 jsonl in zip) | OK |
| 16 | propagation_audit | `LQ04_Propagation_Audit_v3.2.10.md` | OK |
| 17 | five_oracles | 10 copies `LQ04-*.oracle.log` | OK |
| 18 | workload | lq_lifetime_ordinal.{S,c,binary,.golden,.sha256} + compile script (6 files) | OK |
| 19 | excel_v325 | v3.2.5 workbook — SHA inside zip re-verified = `1acb482d…` (current) | OK |
| 20 | model_matrix | `MODEL_STATUS_MATRIX.csv` | OK |
| 21 | git_provenance | GIT_COMMIT_v3210.txt + GIT_STATUS_v3210.txt | OK |
| 22 | binary_sha256 | `BINARY_SHA256_v3210.txt` (both binary paths + final SHA) | OK |
| 23 | file_sha256_manifest | `DELIVERABLES_SHA256_v3210.txt` (190 entries) | OK |
| 24 | open_issues | `OPEN_ISSUES.md` (final report §5 extracted verbatim + packaging note) + `FINAL_REPORT.md` (full) | OK |

## Zip listing tail (real output)

```
$ unzip -l LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip | tail -5
    10111  11-09-2026 20:35   02_lq04_original_definition/LQ04_Definition_Freeze_v3.2.10.md
        0  11-09-2026 20:35   01_baseline_verification/
    11862  11-09-2026 20:35   01_baseline_verification/LSU_v3.2.10_Baseline_Verification.md
---------                     -------
355674595                     225 files
```

Section-dir check: `unzip -l … | awk` unique top-level dirs = exactly
`01_…` through `24_…` (24 dirs). Trace check: 20 `trace_v31.jsonl` entries
(10 pilot originals + 10 section-15 copies). Workbook extracted from the zip
and re-hashed → matches the current repo workbook SHA.

## Fresh verification runs (packaging time, quoted from real output)

```
$ g++ -std=c++17 -I CHAOS/gem5/src tests/test_lq04_rules.cc -o /tmp/test_lq04_rules_pkg && /tmp/test_lq04_rules_pkg
LQ04 ordinal/identity rules: PASS
exit=0

$ python3 -m pytest tests/test_lq04_platform.py tests/test_lsu_v325_workbook.py -v
============================== 18 passed in 3.00s ==============================
pytest exit=0

$ sha256sum -c LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip.sha256
LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip: 成功
```

## Commit and push

```
$ git commit -m "[LSU][MDSPEC][V3.2.10][PACKAGE] publish the LQ04 implementation and pilot package"
[lsu-platform-v3.2.10 7ce06f41] … 7 files changed, 3627 insertions(+)
$ git push origin lsu-platform-v3.2.10
To github.com:wangxumarshall/gem5-fi.git
   a175559b..7ce06f41  lsu-platform-v3.2.10 -> lsu-platform-v3.2.10
```

Staged files (explicit paths, no `git add -A`): the zip, the sidecar, and the
five provenance files (GIT_COMMIT / GIT_STATUS / GIT_DIFF_CODE / GIT_DIFF_STAT /
DELIVERABLES_SHA256). Zips are not gitignored (check-ignore exit 1), so plain
`git add` sufficed.

## Omissions and deviations (explicit)

1. **`cpu.hh` added to GIT_DIFF_CODE beyond the brief's literal path list.** The
   brief listed CHAOSLQ04/, lsq_unit.hh/.cc, chaos_lq04*, CHAOSPropagation/,
   lsu_proxy.py, tests/, build_lsu_v325_workbook.py, docs/superpowers/, platform
   .py — but `CHAOS/gem5/src/cpu/o3/cpu.hh` carries the `chaosLQ04` back-pointer
   (`cpu.hh:551-556`), a real code change of this round (final report §2). It is
   included so the code diff covers the full implementation surface; the
   inclusion is disclosed in the file header and here. The full stat file
   records every changed file regardless.
2. **The gem5.opt binary (1.1 GB) is not inside the zip.** Its identity is
   carried by the SHA256 records (sections 12 and 22) and the build log. This
   follows the round's provenance convention; nothing else is excluded from the
   pilots/controls (both directories are complete copies).
3. **GIT_STATUS content:** recorded at packaging time, it necessarily lists the
   Task 13 provenance files themselves as untracked (they were created by this
   task) plus `.superpowers/sdd/.../progress.md` (task tracker, modified during
   execution) and `.tmp_lsu_conc/` (a concurrent session's scratch, not part of
   the deliverables). Each line is annotated in the file; nothing was hidden.
4. **Sections 04 and 05 are pointer files, not duplicated analyses** — the brief
   explicitly permits this ("a pointer file is acceptable and must say where the
   analysis lives"); both name the exact sections (audit §1.8/§3/§4, freeze §4,
   spec §3) and the runtime evidence locations.
5. **Section 11 evidence is a copy of Task 5 scratch artifacts** (`/tmp/lq04_t5_wd.out`,
   `/tmp/lq04_t5_wd/lq04_injections.log`), which still existed on disk at
   packaging time; the copies are the packaged record since the scratch outdir
   is not a deliverable (open issue 6 of the final report). Stated in
   `WATCHDOG_EVIDENCE_NOTE.md` inside the section.
6. **Plan-file naming:** the plan's "Create: GIT_DIFF_v3210.txt" was implemented
   as the two files the packaging brief specified (GIT_DIFF_CODE + GIT_DIFF_STAT);
   both are committed and packaged in section 09.
7. **The SHA256 manifest does not hash itself** (self-reference impossible);
   stated in its header. All other 190 files are covered exactly (verified by
   `comm -3` = 0).
8. **No fabricated content:** every packaged artifact is a copy of a real repo
   or run artifact; the only authored files are the pointer/note files (04, 05,
   11 note, 22, 24 OPEN_ISSUES extraction) and the provenance records, each
   derived from real command output quoted above.
