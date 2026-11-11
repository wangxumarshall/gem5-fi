# LSU v3.3 binary provenance

Final candidate: `build/ARM/gem5.opt`
SHA256 `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2`
(size 1,149,087,848 bytes; build time 2026-11-11 12:33).

Build: `cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt`, exit 0, then copied
to the repo-root `build/ARM/gem5.opt`. `CHAOS/gem5/build/ARM/gem5.opt` is
byte-identical.

Source tree: branch `lsu-preformal-v3.3.0-20261111`, HEAD `c1846ae4`
(commits 5541648c, 364a6057, c8fc4353, c1846ae4 on top of `9e3d104c`).

## Build candidates in order

| # | SHA256 | Includes | Evidence produced |
|---|---|---|---|
| 1 | `aeb99f11…` | first application of the five reviewed patches | FW02 R01/C01, FW05 R02, A01 R02, A01 C02 (first, invalid control), A03 R01 (no crash link) |
| 2 | `f43c5ddf…` | + A01 ptag-0 control nodes, + A03 translation-finish fault hook | V33B-A01-C02 (control_valid), V33C-A03-R01 (first a03_fault), V33-RP01-R02 |
| 3 | `d3807fbe…` (FINAL) | + A03 0/0-match guard | V33F-A01-C02, V33F-A03-R01, V33F-FW02-C01, V33F-FW05-R02 |

The only difference between candidates 2 and 3 is the `fault_va==0 &&
actual_ea==0` guard in `CHAOSPropagation::noteA03FaultVA`; it removes a
meaningless 0/0 "crash_addr_matches=1" row. Candidate 3 is the frozen
candidate for this round. gem5 builds embed the compile timestamp, so the
SHA moves on every rebuild even with identical sources; the source identity
is the git HEAD above.

## Verification commands (all real, this tree)

- `sha256sum build/ARM/gem5.opt CHAOS/gem5/build/ARM/gem5.opt` → both
  `d3807fbe…`.
- `pytest tests/ -q` → `180 passed in 96.02s`.
- `pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests -q` →
  `107 passed in 3.70s`.
- `python3 tools/lsu_guard.py gate` → `ok: true`, disk 65.9 GiB free,
  MemAvailable 25.74 GiB, 0 gem5 processes.
