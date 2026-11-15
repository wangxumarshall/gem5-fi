# MMU Final Git Diff and Commit Log

Base freeze commit: 872953c2
Source closure: 60f1a8760410288128061d85582e5395b24c0106

## Commits from fsu to the final branch head
```
100f9ce3 [MMU][repro] add explicit rebuilt-binary waiver for independent replication
6a5dd8ca [MMU][repro] use archived control oracles when runs/ is absent
b68b8cf9 [MMU][report] add archive integrity and consolidation reports
0cf24a65 [MMU][provenance] record publication of mmu-final-reproducible
efbc0979 [MMU][audit] add 40/10 integrity tables and cleanup inventory
d919c24f [MMU][provenance] record final branch head and source closure
10663849 [MMU][final] bundle authoritative results archive and reproduction entry points
d520a316 [MMU][evidence] record post-freeze PFN correction and strict join multiplicity guards
5c305923 [MMU][repro] derive repo root from the clone instead of /home/sdc/gem5-fi-mmu-impl-v2
872953c2 [MMU][audit] MMU_FINAL_RUNNER_AUDIT=PASS for all 40 describe samples
a9aa7005 [MMU][runner] gate READY on formal parameter parity
b7d8255f [MMU][runner] pass the workload-owned M05 decoy VA explicitly
8fa0cf5a [MMU][runner] resolve exact M07 target VA from authoritative data
909ac5c5 [MMU][authority] add v3.0.2 parameter authority for M05 decoy VA and M07 exact VA
b6a5e4d5 [MMU][package] include the 10-question final report in the v2 ZIP
6c2e8a85 [MMU][package] build the v2 readiness package with the authoritative Excel
bb360f76 [MMU][preflight] regenerate all 40 verdicts from the frozen traces
0e6f1601 [MMU][evidence] export auditable causal slices for the five IFU contexts
dda332b7 [MMU][validator] strict identity chains for the five IFU contexts
10cb618f [MMU][authority] correct M07 R04 and W10 PFN metadata from raw evidence
6e1d0245 [MMU][docs] plan: final evidence closure v2 (no binary change, strict IFU joins)
965be468 [MMU][docs] mark final closure plan complete (40/40 READY)
3e31fd3d [MMU][freeze] final package: 321 files, 40/40 READY
60f1a876 [MMU][freeze] commit runtime validator/runner deps and canonical W9 workload
650ada2b [MMU][freeze] final readiness package (40/40 READY)
72139ff5 [MMU][freeze] final reports, source-hash commit note, seed audit closure
69f0a202 [MMU][freeze] 40/40 READY: authority, EPAN checkpoint, evidence index
a61812a3 [MMU][tools] final-binary provenance, per-context PFN, IFU/identity trace joins
ddcc2ced [MMU][workloads] per-context W10 VAs, W10S runtime target, W14 exec-only/XN contexts
0acb2a6a [MMU][closure] final entry/permission/PA hooks, EPAN and IFU trace joins
f24b6b77 [MMU][freeze] frozen authority, evidence, preflight and ready package
84e60011 [MMU][tools] deterministic-seed, frozen-authority, provenance and trace gates
46fda643 [MMU][workloads] fix scoped-VA selection and make the target events real
1a5ffeb6 [MMU][M08] do not spend the one-shot on an already-squashed translation
```

## Diffstat of the MMU closure vs fsu
```
 workloads/mmu/W12/mmu_w12                          |    Bin 0 -> 640712 bytes
 workloads/mmu/W12/mmu_w12.c                        |    272 +
 workloads/mmu/W13/mmu_w13                          |    Bin 0 -> 642208 bytes
 workloads/mmu/W13/mmu_w13.c                        |    589 +
 workloads/mmu/W14/install_rcS.sh                   |     57 +
 workloads/mmu/W14/mmu_w14                          |    Bin 0 -> 641832 bytes
 workloads/mmu/W14/mmu_w14.c                        |    637 +
 workloads/mmu/W9/mmu_w9                            |    Bin 0 -> 639504 bytes
 workloads/mmu/W9/mmu_w9.c                          |    221 +
 workloads/mmu/build_all.sh                         |     23 +
 workloads/mmu/install/mmu_install                  |    Bin 0 -> 1989400 bytes
 workloads/mmu/install/mmu_install.c                |    111 +
 workloads/mmu/install/mmu_install.prev.1794451661  |    Bin 0 -> 1989368 bytes
 workloads/mmu/install/w10_blob.o                   |    Bin 0 -> 709720 bytes
 workloads/mmu/install/w9_blob.o                    |    Bin 0 -> 640112 bytes
 workloads/mmu_rev/W10/Binary/mmu_w10               |    Bin 0 -> 709072 bytes
 workloads/mmu_rev/W10/mmu_w10.c                    |    359 +
 workloads/mmu_rev/W9/Binary/mmu_w9                 |    Bin 0 -> 639504 bytes
 workloads/mmu_rev/W9/mmu_w9.c                      |    235 +
 workloads/mmu_rev/install/W10/mmu_w10              |    Bin 0 -> 709072 bytes
 workloads/mmu_rev/install/W9/mmu_w9                |    Bin 0 -> 639504 bytes
 workloads/mmu_rev/install/mmu_install_rev          |    Bin 0 -> 1989368 bytes
 workloads/mmu_rev/install/w10_blob.o               |    Bin 0 -> 709688 bytes
 workloads/mmu_rev/install/w9_blob.o                |    Bin 0 -> 640112 bytes
 2147 files changed, 2487580 insertions(+), 18 deletions(-)
```

## Source diff across the freeze (must be empty)
```
$ git diff --stat 60f1a876..HEAD -- CHAOS/gem5/src
(empty output = identical binary source)
```
