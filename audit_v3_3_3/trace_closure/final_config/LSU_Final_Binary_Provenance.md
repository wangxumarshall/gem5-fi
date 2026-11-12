# LSU v3.3.3 Final Binary Provenance (Trace Closure)

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`
**HEAD at generation:** `78ac9ba730afb5bf9a5714568a8b8fa197cf0bbb`
**Config SHA256:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
**Previous frozen binary (superseded):** `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338` (backup: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/audit_v3_3_3/trace_closure/baseline/gem5.opt.v333-old-1126e0fd`)
**Final frozen binary:** `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
**Build log:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/audit_v3_3_3/trace_closure/baseline/build.log`

## Build and install (one build only)

```console
$ cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/CHAOS/gem5
$ scons -j16 build/ARM/gem5.opt
$ cp CHAOS/gem5/build/ARM/gem5.opt /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/build/ARM/gem5.opt
$ sha256sum /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/build/ARM/gem5.opt
62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd  /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/build/ARM/gem5.opt
```

The runner resolves `ROOT/build/ARM/gem5.opt` (the worktree root). The
main-repo binary `/home/sdc/gem5-fi-ding/build/ARM/gem5.opt`
(`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`) is
not this build and must never be used.

## Source changes in this build

CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc   |  65 ++++++-
 CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh   |  11 ++
 .../cpu/o3/CHAOSPropagation/CHAOSPropagation.cc    | 212 ++++++++++++++++++++-
 .../cpu/o3/CHAOSPropagation/CHAOSPropagation.hh    | 100 +++++++++-
 CHAOS/gem5/src/cpu/o3/lsq.cc                       |  14 ++
 CHAOS/gem5/src/cpu/o3/lsq.hh                       |   6 +
 CHAOS/gem5/src/cpu/o3/lsq_unit.cc                  |  35 +++-
 .../fixtures/lsu_v333_synthetic/build_fixtures.py  |   4 +-
 .../campaign/A01-R01-control/campaign.json         |   2 +-
 .../campaign/A01-R01-control/summary.json          |   2 +-
 .../campaign/A01-R01-fault/campaign.json           |   2 +-
 .../campaign/A01-R01-fault/summary.json            |   2 +-
 .../campaign/A01-R02-control/campaign.json         |   2 +-
 .../campaign/A01-R02-control/summary.json          |   2 +-
 .../campaign/A01-R02-fault/campaign.json           |   2 +-
 .../campaign/A01-R03-control/campaign.json         |   2 +-
 .../campaign/A01-R03-control/summary.json          |   2 +-
 .../campaign/A01-R03-fault/campaign.json           |   2 +-
 .../campaign/A01-R03-fault/summary.json            |   2 +-
 .../campaign/A01-R04-control/campaign.json         |   2 +-
 .../campaign/A01-R04-control/summary.json          |   2 +-
 .../campaign/A01-R04-fault/campaign.json           |   2 +-
 .../campaign/A01-R04-fault/summary.json            |   2 +-
 .../campaign/A01-R05-control/campaign.json         |   2 +-
 .../campaign/A01-R05-control/summary.json          |   2 +-
 .../campaign/A01-R05-fault/campaign.json           |   2 +-
 .../campaign/A01-R05-fault/summary.json            |   2 +-
 .../campaign/A03-R01-control/campaign.json         |   2 +-
 .../campaign/A03-R01-control/summary.json          |   2 +-
 .../campaign/A03-R02-control/campaign.json         |   2 +-
 .../campaign/A03-R02-control/summary.json          |   2 +-
 .../campaign/A03-R02-fault/campaign.json           |   2 +-
 .../campaign/A03-R02-fault/summary.json            |   2 +-
 .../campaign/A03-R03-control/campaign.json         |   2 +-
 .../campaign/A03-R03-control/summary.json          |   2 +-
 .../campaign/A03-R03-fault/campaign.json           |   2 +-
 .../campaign/A03-R03-fault/summary.json            |   2 +-
 .../campaign/A03-R04-control/campaign.json         |   2 +-
 .../campaign/A03-R04-control/summary.json          |   2 +-
 .../campaign/A03-R04-fault/campaign.json           |   2 +-
 .../campaign/A03-R04-fault/summary.json            |   2 +-
 .../campaign/FW02-R01-control/campaign.json        |   2 +-
 .../campaign/FW02-R01-control/summary.json         |   2 +-
 .../campaign/FW02-R01-fault/campaign.json          |   2 +-
 .../campaign/FW02-R01-fault/summary.json           |   2 +-
 .../campaign/RP01-R01-control/campaign.json        |   2 +-
 .../campaign/RP01-R01-control/summary.json         |   2 +-
 .../campaign/RP01-R01-fault/campaign.json          |   2 +-
 .../campaign/RP01-R01-fault/summary.json           |   2 +-
 .../campaign/SP05-R01-control/campaign.json        |   2 +-
 .../campaign/SP05-R01-control/summary.json         |   2 +-
 .../campaign/SP05-R01-fault/campaign.json          |   2 +-
 .../campaign/SP05-R01-fault/summary.json           |   2 +-
 .../campaign/campaign_identity.json                |   2 +-
 .../campaign_clean/A01-R01-control/campaign.json   |   2 +-
 .../campaign_clean/A01-R01-control/summary.json    |   2 +-
 .../campaign_clean/A01-R01-fault/campaign.json     |   2 +-
 .../campaign_clean/A01-R01-fault/summary.json      |   2 +-
 .../campaign_clean/SP05-R01-control/campaign.json  |   2 +-
 .../campaign_clean/SP05-R01-control/summary.json   |   2 +-
 .../campaign_clean/SP05-R01-fault/campaign.json    |   2 +-
 .../campaign_clean/SP05-R01-fault/summary.json     |   2 +-
 .../campaign_partial/A01-R01-control/campaign.json |   2 +-
 .../campaign_partial/A01-R01-control/summary.json  |   2 +-
 .../campaign_partial/A01-R01-fault/campaign.json   |   2 +-
 .../campaign_partial/A01-R01-fault/summary.json    |   2 +-
 .../campaign_partial/A01-R02-control/campaign.json |   2 +-
 .../campaign_partial/A01-R02-control/summary.json  |   2 +-
 .../campaign_partial/A01-R02-fault/campaign.json   |   2 +-
 .../design/CLEAN_ROI_MAPPING.csv                   |   6 +-
 .../design/CLEAN_SAMPLE_MATRIX.csv                 |   6 +-
 .../design/HISTORICAL_ROI_MAPPING.csv              |   4 +-
 .../design/HISTORICAL_SAMPLE_MATRIX.csv            |   4 +-
 .../design/PARTIAL_ROI_MAPPING.csv                 |   6 +-
 .../design/PARTIAL_SAMPLE_MATRIX.csv               |   6 +-
 .../design/SYNTH_ROI_MAPPING.csv                   |  26 +--
 .../design/SYNTH_SAMPLE_MATRIX.csv                 |  26 +--
 .../A01-R01-control/campaign.json                  |   2 +-
 .../A01-R01-control/summary.json                   |   2 +-
 .../A01-R01-fault/campaign.json                    |   2 +-
 .../historical_evidence/A01-R01-fault/summary.json |   2 +-
 tests/test_lsu_v333_workbook.py                    |   3 +-
 tools/lsu_v332_matrix.py                           |   2 +-
 tools/lsu_v332_report.py                           |   2 +-
 tools/lsu_v333_launch.py                           |   2 +-
 tools/lsu_v333_propagation.py                      |  91 ++++++++-
 tools/lsu_v333_qualified.py                        | 100 +++++++++-
 87 files changed, 708 insertions(+), 153 deletions(-)

The only C++ behavior changes are read-only observation hooks:
`CHAOSPropagation` (SP05 store-commit capture / writeback-suppressed record /
RP01 watchdog terminal flush), `CHAOSLSQFwd` (RP01 terminal snapshot and
last-eligible bookkeeping), `lsq_unit.cc` (post-completion suppression
record), and read-only `LSQ` accessors. No injection semantics, workload,
seed, SampleRunID, ROI percentile, dynamic context or Fault-Control pairing
was changed.

## Workload ELF SHA256 (unchanged)

| Workload | SHA256 |
|---|---|
| `agu_addrmodes` | `90a1900377d2499625bf401c6b8ce1a7d4a22c8327aeef98f11dc842b406b49b` |
| `sq_reload_v3212` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| `replay_partial_v332` | `3f880cba7b6d16b61a453c37c68d6dbaaf63980dba5c9231218cf8dd8fa42e42` |

The full frozen workload table remains in
`audit_launch_fix_v333/authorization/LSU_Final_Binary_Provenance.md`.

## Campaign identity

`LSU-V333-FINAL-20261112`. All 120 formal runs must use this binary and the config SHA
above; old-binary pilot traces are archived separately and must not be mixed
into the formal result set.
