# W8.2/W8.3/W8.5 event-density table (event_coverage counting backfill)

Measured 2026-09-25 on branch fi-ding @ f3bb6b03 worktree, repo-root
build/ARM/gem5.opt, C3 `configs/se/ooo_proxy.py --cpu O3 --chaos_probe`,
PYTHONHASHSEED=0, no injectors attached (read-only W0.3a probe; every run
printed its golden FINAL checksum). 2 reps per binary (r1/r2): **all 18
binaries reproduced every stats+probe column EXACTLY (r1==r2)** — no
W1.3-style environment sensitivity observed in event counts.

Column semantics (per north-star 02-doc six families / tools/event_density.py):
- branch_mispred = commit.branchMispredicts (misprediction recoveries; D14/D23/D24)
- squash = commit.commitSquashedInsts (commit-stage squash; D36-D39)
- rat_writes = rename.renamedOperands (dest renames = RAT entry overwrites; D16/D66/D71)
- renamed_insts = rename.renamedInsts (dispatches; ROB/IQ slot overwrites; D40/D54/D91)
- robOver80/iqOver80 = probe cycles with occupancy>80% (gate == injector 5*occ>4*cap; D33/D35/D85, D49)
- flIntLe8 = probe cycles with int freelist<=8 (== D18 injector threshold)
- flVecLe0 = probe cycles with vec freelist==0 (== D75 injector threshold; separate runs with --probe_fl_vec_le 0)

| binary | branch_mispred | squash | rat_writes | renamed_insts | robOver80 | iqOver80 | flIntLe8 | fp_simd_committed (share) |
|---|---|---|---|---|---|---|---|---|
| branch_mispred | 490766 | 5091001 | 15739145 | 16937196 | 167542 | 48749 | 285035 | 26 (0.0%) |
| coremark | 73348 | 1677415 | 15377069 | 13209178 | 67194 | 309285 | 533971 | 12106 (0.1%) |
| crc32 | 848 | 6714 | 8919848 | 8921405 | 4475 | 0 | 4613 | 37 (0.0%) |
| matmult_int | 50346 | 801783 | 10601660 | 9482591 | 13727 | 9494 | 13331 | 927 (0.0%) |
| md5sum | 22987 | 214830 | 14611118 | 12615802 | 435 | 0 | 160 | 373409 (1.5%) |
| minver | 482 | 5451 | 12882538 | 9851322 | 674 | 0 | 165 | 1365528 (6.9%) |
| nbody | 504 | 5273 | 6229560 | 4091314 | 1514 | 0 | 1120 | 1687579 (20.7%) |
| wikisort | 49144 | 687919 | 8200505 | 6650652 | 23119 | 177 | 21818 | 121306 (1.1%) |
| dep_chain | 225 | 2980 | 21010348 | 17510520 | 137 | 7000882 | 6999912 | 26 (0.0%) |
| dep_chain_vec | 240 | 3315 | 10698835 | 6909884 | 266 | 527 | 258 | 4846534 (35.1%) |
| rob_fill | 237 | 7252 | 7999183 | 8798806 | 426601 | 383102 | 397444 | 1452420 (8.3%) |
| rob_fill_fp | 244 | 226727 | 7013389 | 8422877 | 275648 | 405279 | 46694 | 929373 (5.7%) |
| gap | 38936 | 1276484 | 9644477 | 8150927 | 2800014 | 2097113 | 197571 | 380944 (2.8%) |
| gemm | 8604 | 22691 | 8646629 | 6518760 | 124765 | 834 | 124016 | 1429078 (11.0%) |
| lu | 13609 | 45363 | 8975735 | 7303641 | 113412 | 59 | 112754 | 808220 (5.6%) |
| cholesky | 12061 | 41299 | 8951076 | 7272095 | 63092 | 59 | 56586 | 818747 (5.7%) |
| jacobi2d | 3124 | 10320 | 9347917 | 6587383 | 410280 | 503 | 409430 | 2150921 (16.4%) |
| jpeg_wl | 26875 | 941927 | 11702335 | 10017746 | 297706 | 238328 | 295127 | 1914180 (10.7%) |
| dep_chain_vec (le0 probe cfg) | flVecLe0 = 4954038 |

## Per-cell fill (46 stanzas; all measured nonzero — zero blocked cells)

| campaign family | event@binary | density (events/run) | ceil(2000/density) |
|---|---|---|---|
| D14/D23/D24 | branch_mispred@branch_mispred | 490766 | 1 |
| D16 x7 | rat_writes@coremark+crc32+matmult-int+md5sum+minver+nbody+wikisort | min 6229560 (nbody) .. max 21010348 (dep_chain) | all = 1 |
| D18 | flIntLe8@dep_chain | 6999912 | 1 |
| D75 | flVecLe0@dep_chain_vec | 4954038 | 1 |
| D33/D35 | robOver80@rob_fill | 426601 | 1 |
| D85 | robOver80@rob_fill_fp | 275648 | 1 |
| D36-D39 | squash@gap | 1276484 | 1 |
| D49 | iqOver80@rob_fill | 383102 | 1 |
| D40 x7 / D54 x7 / D91 x5 | renamed_insts@coremark+emb6+pb4+jpeg | min 4091314 (nbody) .. max 17510520 (dep_chain) | all = 1 |
| D66 x2 / D71 x5 | rat_writes@nbody+minver+pb4+jpeg | min 6229560 (nbody) .. max 21010348 (dep_chain) | all = 1 |

NOTE: every density >= 275,648 events/run, so campaign.py's
n_runs = ceil(target_events/density) = **1 run per event-coverage cell**.
If the production intent is 2000 single-injection event HITS
(limits.max_faults=1 lands ONE injection per run), the density formula
yields n=1 while the hit count would be 1 — flag to the orchestrator
before W8.2 launch (campaign.py frozen; coverage.json records actual
coverage honestly at run time).

Class-restriction bias (documented, not corrected): the vec/int-class
rows (D66/D71/D91 vec; D16/D54 int on FP-mixed binaries) use the
all-class columns. FP/SIMD committed shares: nbody 20.7%,
dep_chain_vec 35.1%, jacobi2d 16.4%, gemm 11.0%, jpeg 10.7%,
rob_fill 8.3%, minver 6.9%, cholesky 5.7%, rob_fill_fp 5.7%, lu 5.6%,
gap 2.8%, md5sum 1.5%, wikisort 1.1%, coremark 0.1%, pure-int rest ~0%.
For those rows the true class-restricted eligible set is SMALLER
(density overestimates -> n_runs underestimates); campaign.py's
coverage_shortfall check catches the actual shortfall at run time.
