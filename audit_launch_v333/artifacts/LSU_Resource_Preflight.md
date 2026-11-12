# LSU v3.3.3 — Resource Preflight

**Date:** 2026-11-12
**Host:** native aarch64 openEuler 24.03; 126 cores.

| Item | Measured | Requirement | Status |
|---|---|---|---|
| Free space on `/home` | 51 GiB | ≥20 GiB floor; ~3.2 GiB raw output | PASS |
| RAM available | 25 GiB | gem5 SE O3 single process; no swap pressure observed | PASS |
| CPU | 126 cores | 1 gem5 process at a time; hard cap ≤4 concurrent | PASS |
| Running gem5 processes | 0 | 0 before launch | PASS |
| Output base | `runs/lsu/formal_v333` absent before dry-run | must be writable and new | PASS |
| Output collision | 120 unique dirs in the dry-run | 0 collisions | PASS |
| History protection | default out-base is the new formal base; `--force` required to overwrite | no `audit_v3_3_3` reference | PASS |
| Manifest post-step | `lsu_v333_launch.py --manifest-only` | 120 rows + per-run manifest | PASS |

## Runtime estimate

- Pre-formal measured gem5 elapsed sum: ~429 s.
- Rehearsal wall span: ~28.5 min (serial, including Python/run_pilot overhead).
- Realistic formal wall: 30–40 min.
- Worst case (every run at its timeout): ~12.9 h; the runner's per-run timeouts
  (A03 300 s, RP01 300 s, run_pilot 180 s) bound the total.
- Disk: final raw output ~3.2 GB (pre-formal set was 3.2 GB); the pre-correction
  archive is not duplicated.

## Source/binary resources

- Source HEAD `b5031bf7`; results HEAD `b8405580`.
- Final binary `build/ARM/gem5.opt` SHA256 `1126e0fd…`; config SHA `8309da72…`.
- 120/120 pre-formal summaries carry the final binary SHA.
- No rebuild is required for this preflight; the runner fixes are Python-only.
