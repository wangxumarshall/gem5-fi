# Strict E2E git status (true state)

## E2E workspace

* Path: `/home/sdc/gem5-fi-LSU/e2e_extension`
* Branch: `lsu-e2e-strict-20261117`
* HEAD: `e4405a6391098437b3f2646d74173685ee94af89`
* Local tag `LSU_E2E_Strict_Causal_Evidence_20261117` -> `3e772fbe63f1b9ded1ebbd6d9485211d8dfa5e50`
* Paper-final tag `LSU_E2E_PAPER_FINAL_20261118` -> `7fbe3668ebbd0c8e1ea5e8089f1733b804910c6b`
* Remote: `NONE`
* This file records the actual local state; no remote push exists.

```
(clean)
```

* The status block excludes `reports/STRICT_E2E_*`, which this delivery script regenerates from the raw evidence after the code commit; the tracked code state is the line shown above.

## gem5 source workspace

* Path: `/home/sdc/gem5-fi-LSU/repo`
* Branch: `lsu-e2e-strict-obs-20261117`
* HEAD: `2bbf2907668f78e0b67473caf5a63153b70bede3`
* Frozen tag: `LSU_When_v2_FINAL_FROZEN` -> `e8759972a8e65856b540629a0defdd7e744ff921` (unchanged; the observation commit is a child of it)
* Local observation tag: `LSU_E2E_Strict_Obs_20261117` -> `2bbf2907668f78e0b67473caf5a63153b70bede3`

```

```

Changed files for the RP01 observation build:

```
CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc | 198 +++++++++++++++++++++++
 CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh |  18 +++
 CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py |   9 ++
 CHAOS/gem5/src/cpu/o3/inst_queue.cc              |  31 ++++
 CHAOS/gem5/src/cpu/o3/inst_queue.hh              |   6 +
 CHAOS/gem5/src/cpu/o3/lsq_unit.cc                |  25 +++
 CHAOS/gem5/src/cpu/o3/lsq_unit.hh                |   7 +
 CHAOS/gem5/src/cpu/o3/mem_dep_unit.cc            |  10 ++
 CHAOS/gem5/src/cpu/o3/mem_dep_unit.hh            |   5 +
 9 files changed, 309 insertions(+)
```

* Observation binary: `e2e_extension/bin/gem5.opt.obs` SHA256 `ce8dfaf3ed3093c9b51616ef678ea496715dd8ae62015dc998b2bea643a75fcd`
* Original binary preserved: `e2e_extension/bin/gem5.opt.original` SHA256 `c84d0eb598566a89e5a853e9bf31bbdf747f5918b9b66fdb84b5b73ab064bc78`
* No GitHub push, no remote tag, no release. All commits are local.
