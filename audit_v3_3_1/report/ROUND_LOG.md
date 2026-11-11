# LSU v3.3.1 — Round Log (append-only)

All commands below were executed in
`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`.

## Baseline

- `git checkout -b lsu-v3.3.1-context-workload-20261111`
- `sha256sum build/ARM/gem5.opt` → `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2`
- v3.3.0 package SHA256 → `c35c8d5f2b32e29bb4783bdd4f1ea5b3a3f623b1bbb63adb98d514443034e4d4`
- Extracted v3.3.0 package to `audit_v3_3_1/v33_package/`.

## Census tool and probes

- `tools/lsu_v331_census.py --model A01 --seed 2108120075 --ordinals ...`
- A01 coarse/boundary scan: K=100..1295, then 1030–1049 and 1230–1239.
  Result: ROI eligible ordinals **1040–1234** (N=195); first in-`main` PC
  `0x400558`, last `0x4006d0`; 1235 is libc `0x409928`.
- A01 percentiles 1059/1098/1137/1176/1215 (pc 0x400598/0x40068c/0x4006a8/
  0x4006d0/0x4006d0).
- Seed check: A01 K=1059 with seed 1113826800 reproduces seq 12978 / pc
  0x400598 / addr 0x493000.
- A03 percentiles 1059/1098/1137/1176/1215; activation seq 12978/13638/14049/
  14719/15086; reasons ALREADY_STUCK/STUCK_APPLIED/ALREADY_STUCK/
  ALREADY_STUCK/STUCK_APPLIED. F5 runs time out after activation; partial
  records retained (`timed_out=true`).
- FW05 coarse 1..4000; last eligible ordinal = 2000. Percentiles 200/600/1000/
  1400/1800; all load PC 0x400564; addresses 0x4919c8/0x491a48/0x491ac8/
  0x491b48/0x4919c8.
- DA04 coarse 1..1200; first in-buffer ordinal 33 (0x491991), last 1056
  (0x49298d). Percentiles 135/340/544/749/954.
- MD04 scan 1..1024: only ordinals 1–6 have events; only ordinal 3 is in
  `main` (PC 0x400530, addr 0x491990). N_ROI=1.
- SQ01 on W3 `sq_drain`: ordinals 1005–1600 all in buffer
  [0x491990,0x4a1990); loop end not pinned from the merged stream.
- SQ01/SQ03/SP05 on `sq_reload_v3212`: percentiles 1018/1044/1069/1095/1121,
  1021/1047/1072/1098/1124, 952/978/1003/1029/1055; store seq
  13328/15122/16847/18641/20435; addresses 0x4919f0…0x491d28.
- A seed check for FW05 (K=200, seed 1653118510) reproduces seq 16084 /
  pc 0x400564 / addr 0x4919c8.

## Disk incident (recorded honestly)

- `/tmp` is a 15 GiB tmpfs; the census initially wrote multi-MB traces there
  and filled it (`No space left on device`). The three SP05 probes that hit
  the full disk failed. Cleaned `/tmp/v331_census`, changed the scratch to
  `/home/sdc/.cache/v331_census`, and made the tool delete each probe's
  trace/stats after copying the small logs. SP05 percentiles were re-run
  successfully. No evidence was fabricated or silently dropped.

## Generated deliverables

- `audit_v3_3_1/roi/LSU_60Context_ROI_Percentile_Mapping.csv` (60 rows)
- `audit_v3_3_1/roi/LSU_60Context_Distinctness_Audit.csv` (60 rows)
- `audit_v3_3_1/propagation/LSU_60Context_Causal_Chain_Reaudit.csv` (60 rows)
- `audit_v3_3_1/controls/LSU_60Context_Control_Readiness.csv` (60 rows)
- `audit_v3_3_1/audits/LSU_12Model_Workload_Readiness.csv` (12 rows)
- `audit_v3_3_1/report/LSU_v3.3.1_Finalization_Report.md`
- `audit_v3_3_1/report/LSU_Researcher_Approval_Required.md`

## Regression (real output)

- `python3 -m pytest tests/ -q -p no:cacheprovider` -> **180 passed in 95.74s**
- `python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests -q -p no:cacheprovider` -> **107 passed in 3.45s**
- Package: `LSU_v3.3.1_Context_Workload_Finalization_Package.zip`, 719 KiB, 948 files,
  SHA256 is recorded in the adjacent `.sha256` sidecar (the ZIP cannot contain its own final hash).
