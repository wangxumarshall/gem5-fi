# LSU v3.2.10 — Final-review fix wave report

Date: 2026-11-09. Branch `lsu-platform-v3.2.10`, worktree
`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10`.
Wave start HEAD: `36929561`. Wave end HEAD (before this report's own commit):
`d182b8f5`. All commands below were actually run in this session; outputs are
quoted verbatim (abridged only where marked).

## Wave commits (one coherent unit each)

| Commit | Subject |
|---|---|
| 1331a9d0 | [DOCS] check off completed Tasks 1/3/7/9/10 plan steps |
| e562d00c | [LQ04] make control target_event_proof not-applicable on zero injections |
| d72ffc2d | [PILOT] re-run the five LQ04 controls with the corrected proof metadata |
| 7dc46b05 | [DOCS] fix the Final Report eligibility typo: not executed |
| d182b8f5 | [PACKAGE] rebuild the pilot package with the corrected control evidence |

## Important 1 — plan checkboxes (Tasks 1/3/7/9/10)

Verification before checking: each of the 19 unchecked steps was traced to its
per-task report (`.superpowers/sdd/2026-11-08-lsu-v3.2.10-lq04/task-{1,3,7,9,10}-report.md`)
and to the artifacts/commits:

- Task 1 steps 1–3: report §1 quotes the real baseline outputs (HEAD
  `37692d2b…`, both binaries `303c610d…`, diff touching only the five
  `GIT_*_v329.txt` files, pytest `2 failed, 40 passed`); the three audit docs +
  spec committed in `7f397e2f` (4 files, 826 insertions).
- Task 3 steps 1–4: `tests/test_lq04_rules.cc` written first; RED evidence is
  the real g++ output `致命错误：cpu/o3/CHAOSLQ04/lq04_rules.hh：No such file or
  directory … exit=1`; GREEN `LQ04 ordinal/identity rules: PASS exit=0`;
  commits `00bad521` + fix `8ff3d596` (squashed-branch pinning).
- Task 7 steps 1–5: registry verified (comma defect found and fixed inside the
  task's fix round, `9097213a`; current code `CHAOSPropagation.cc:1697` reads
  `;field=valid+request`); binding verified by a real chain run (validator
  `VALID`, 326 consumer_commit nodes, no SDC); commits `55ea6ee5` + `9097213a`.
- Task 9 steps 1–3: build log 1124 lines exit 0, binary
  `f3c2a442…af20694` identical at both paths, reg_chain
  `f247ef3fe6f02cfd` exit 0, anchor baseline `b097eb83f71545cb`; commit
  `ced05ae6`.
- Task 10 steps 1–4: 5/5 fault pilots and 5/5 controls run with the frozen
  identities; exactly 5 injection lines, five distinct tuples, ordinals 1–5
  each once; commit `5adbb220`.

No unperformed step was found: **all 19 boxes were checked off as performed.**
After the edit, the only remaining `- [ ]` string in the plan is the
instructional header on line 3 ("Steps use checkbox (`- [ ]`) syntax"), not a
step; 52 of 52 steps are checked.

Command and output:

```
$ grep -c '\- \[ \]' docs/superpowers/plans/2026-11-08-lsu-v3.2.10-lq04.md   # after edit
1
$ grep -c '\- \[x\]' docs/superpowers/plans/2026-11-08-lsu-v3.2.10-lq04.md
52
$ git diff --stat docs/superpowers/plans/2026-11-08-lsu-v3.2.10-lq04.md
 .../plans/2026-11-08-lsu-v3.2.10-lq04.md           | 38 +++++++++++-----------
 1 file changed, 19 insertions(+), 19 deletions(-)
```

Commit: `1331a9d0`.

## Important 2 — control manifests claiming transitions that did not happen

### Code change (commit e562d00c)

`docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`: extracted
`_lq04_target_proof(injections, event_ordinal)`. Fault runs (>=1 injection)
keep the construction-time proof fields with `"applicable": True`.
Zero-injection runs (matched controls; the LQ04 injector is ordinal-gated and
simply not mounted at `--probability 0.0`) now emit `null` for
`valid_1_to_0`, `request_1_to_0`, `no_pop_no_reuse`,
`address_size_data_unchanged` and the vacuously-true `ordinal_matches`, with
`"applicable": False`, an explicit `not_applicable_reason`,
`all_one_injection: false` and `events: 0`. The `accepted` gate is unchanged
(it already required `injected > 0`).

`tests/test_lq04_platform.py`: two new tests pin both shapes
(`test_lq04_target_proof_control_is_not_applicable`,
`test_lq04_target_proof_fault_run_claims_transitions`), including a JSON
round-trip asserting the n/a fields serialize to `null`.

Verification:

```
$ python3 -m pytest tests/test_lq04_platform.py tests/test_lsu_v325_workbook.py -q
....................                                                     [100%]
20 passed in 3.22s

$ python3 -m pytest tests/test_lsu_v324_workbook.py -q        # unaffected check
.....                                                    [100%]
5 passed in 1.51s

$ python3 -c "import ast; ast.parse(open('docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py').read()); print('run_pilot.py: syntax OK')"
run_pilot.py: syntax OK
```

### Control re-runs (commit d72ffc2d)

Command (exactly as specified by the wave brief), run once per i=1..5:

```
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py --model LQ04 --probability 0.0 \
  --context-index $i --preserve-sample-id --pilot-id LQ04-CONTROL-R0$i \
  --workload $PWD/docs/gem5-fi/lsu/implementation_v3_2/workloads/lq_lifetime_ordinal \
  --outdir $PWD/docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-CONTROL-R0$i \
  --timeout 900 --gem5 $PWD/build/ARM/gem5.opt
```

Observed exit codes (expected control signature — record validity requires
>=1 injection, so `run_pilot` exits 1 while gem5 itself exits 0):

```
CONTROL-R01 run_pilot exit=1
CONTROL-R02 run_pilot exit=1
CONTROL-R03 run_pilot exit=1
CONTROL-R04 run_pilot exit=1
CONTROL-R05 run_pilot exit=1
```

Post-run verification (all five):

```
LQ04-CONTROL-R01: stdout_injection_lines=0 lq04_log=no-log-file checksum=0xb097eb83f71545cb
LQ04-CONTROL-R02: stdout_injection_lines=0 lq04_log=no-log-file checksum=0xb097eb83f71545cb
LQ04-CONTROL-R03: stdout_injection_lines=0 lq04_log=no-log-file checksum=0xb097eb83f71545cb
LQ04-CONTROL-R04: stdout_injection_lines=0 lq04_log=no-log-file checksum=0xb097eb83f71545cb
LQ04-CONTROL-R05: stdout_injection_lines=0 lq04_log=no-log-file checksum=0xb097eb83f71545cb
```

- Zero injection lines: confirmed (no `lq04_injections.log` exists — the
  injector is not mounted; `command.txt` in each dir confirms no
  `--chaos_lq04`).
- Oracle PASS `0xb097eb83f71545cb`: `oracle.log` in every control reads
  `expected=b097eb83f71545cb got=b097eb83f71545cb / ORACLE_PASS`;
  `pilot_meta.json` `oracle_pass: true`, gem5 `exit_code: 0`.
- `target_event_proof` now not-applicable in every control (verbatim from
  pilot_meta.json, identical in all five):

```json
{
 "site": "executeLoad_post",
 "events": 0,
 "all_one_injection": false,
 "ordinal_matches": null,
 "applicable": false,
 "not_applicable_reason": "no injection event (matched no-fault control: injector not mounted); LQ04 lifetime proof fields are n/a",
 "valid_1_to_0": null,
 "request_1_to_0": null,
 "no_pop_no_reuse": null,
 "address_size_data_unchanged": null
}
```

- The five fault pilots are untouched (`git status --porcelain` on
  `LQ04-R01..R05` → 0 lines). Only `manifest.json` (timestamp + recomputed
  sha), `pilot_meta.json` (proof + elapsed), `stats.txt`, `stdout.log` changed
  per control dir (20 files, +84/−74).
- `LQ04_PILOT_SUMMARY.csv` control rows already used `n/a` for all
  injection-side fields — no stale claims, left unchanged.

## Minor — Final Report typo (commit 7dc46b05)

`docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.10_Final_Report.md:75`:

```
-load (entry valid, request present, not squashed, executed) is selected by
+load (entry valid, request present, not squashed, not executed) is selected by
```

(The eligibility conjunction is `valid && has_request && !squashed &&
!executed` — first execution round.)

## Package rebuild (commit d182b8f5)

Reused the existing staging tree `/tmp/lsu_v3210_pkg` (verified: the staged
control traces/oracles and the v3.2.5 workbook `1acb482d…` are byte-identical
to the repo). Updated in the staging tree: `14_five_controls` (five corrected
dirs), `24_open_issues/FINAL_REPORT.md`, `10_unit_tests/test_lq04_platform.py`,
`10_unit_tests/pytest_v3210.log` (re-run, 20 passed), `09_git_diff/*`,
`21_git_provenance/*`. Regenerated
`23_file_sha256_manifest/DELIVERABLES_SHA256_v3210.txt` (relative paths,
sorted, self-excluded; 191 files in tree, 190 manifest entries) and the
repo-root copy.

The GIT_DIFF_CODE pathspec was reconstructed and verified byte-exact against
the previous build's file list before regenerating at the new HEAD
(`RECONSTRUCTION EXACT MATCH`).

Verification of the rebuilt zip:

```
$ unzip -l LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip | tail -3
    17806  11-09-2026 22:10   24_open_issues/FINAL_REPORT.md
---------                     -------
355681540                     225 files
$ unzip -l … | <sections>            → 24 sections
$ unzip -l … | grep -c pilot_meta.json → 10
$ unzip -p … 14_five_controls/LQ04-CONTROL-R02/pilot_meta.json | python3 -c …
applicable: False | valid_1_to_0: None | events: 0
$ unzip -p … 24_open_issues/FINAL_REPORT.md | grep -c "not squashed, not executed"
1
```

Sidecar:

```
$ sha256sum LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip | tee LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip.sha256
078c9fe08cc6dc7650c6da2ef2f8115efb59fb8d8c952b2a572ceb1c2b17d9ac  LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip
$ sha256sum -c LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip.sha256
LSU_v3.2.10_LQ04_Implementation_Pilot_Package.zip: 成功
```

**New package SHA256:
`078c9fe08cc6dc7650c6da2ef2f8115efb59fb8d8c952b2a572ceb1c2b17d9ac`**
(12,346,387 bytes; first build was `a0b46928…`, 12,355,786 bytes).
Provenance updated to HEAD `7dc46b05` (30 commits since `37692d2b`); workbook
SHA unchanged (`1acb482d…`).

## Final test run (at HEAD d182b8f5)

```
$ python3 -m pytest tests/test_lq04_platform.py tests/test_lsu_v325_workbook.py -q
....................                                                     [100%]
20 passed in 3.01s
```

## Unchecked-step audit result

None. Every one of the 19 previously unchecked steps in Tasks 1/3/7/9/10 was
performed and evidenced in the per-task reports; all were checked off. The
single remaining `- [ ]` string in the plan file is the line-3 instruction
text, not a step.
