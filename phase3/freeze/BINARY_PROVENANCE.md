# MMU Binary Provenance (Phase 0.2)

Date: 2026-11-12 (UTC) / 2026-11-11 local
Workspace: `/home/sdc/gem5-fi-mmu-impl-v2` — branch `fsu`, HEAD `2a8422b4`.
Original workspace `/home/sdc/gem5-fi-mmu` is read-only and NOT used for runs.

## 1. The binary hashes in circulation (all real, distinct files)

| SHA256 | What it is | Evidence |
|---|---|---|
| `1f9d3de285ec1d9db477e961a5659f21fe7158dc0ece0c352f3a58ab5329686e` | `/home/sdc/gem5-fi-mmu/CHAOS/gem5/build/ARM/gem5.opt` — the ORIGINAL workspace binary (read-only). Never used by impl-v2 phase-3 pilots. | `docs/gem5-fi/mmu/MMU_Final_Review_Package/04_WORKSPACE_AND_VERSION/Binary_Manifest.txt` |
| `d80a52ad48241c258c2879991dbe935d48f9c2096dccbd0bbbcf1bbbaf9f2ca1` | Earlier impl-v2 pilot binary (M04/M05/M06/M07 R01 pilots in phase3, before the closure rebuild). | `phase3/m05/M05_PILOT_R01.md`, `phase3/m04/M04_PILOT_R01.md`, `phase3/m06/M06_PILOT_R01.md`, `phase3/m07/M07_PILOT_R01.md` |
| `3ec51b2cbfe1cbd743862eb4b260bb05da9bebc3b8e63e75578662b2ad3359e6` | Current final impl-v2 binary (`CHAOS/gem5/build/ARM/gem5.opt`, mtime 2026-11-11 15:31:39 +0800). Produced by `phase3_build_closure_final.log`. | `phase3/final_binary.sha256`; `sha256sum CHAOS/gem5/build/ARM/gem5.opt` |
| `9a78728a…`, `45a8b87a…`, `6f85cc7f…` | Phase-2.2 binaries used for the M01/M02 five-context evidence (older source tree). | `phase2_2/02_Build/Binary_SHA256.txt` |

The task brief's "two Binary SHA256" is therefore `1f9d3de…` (original
read-only workspace) vs `3ec51b2c…` (impl-v2 final), with `d80a52…` as the
earlier impl-v2 pilot binary still cited by several phase-3 R01 reports.

## 2. Which binary did each runner-produced pilot actually execute?

The runner manifest records `git_head` but NOT the binary hash (the
PROP-EVT `binary_hash=` field is empty in every phase-3 trace). It can still
be reconstructed from the binary rebuild time and the run start time:

- `3ec51b2c…` exists from 2026-11-11T07:31:39Z (15:31 +0800).
- Pilots started before that used `d80a52…`; after, `3ec51b2c…`.

Consequences (real, checked against `runs/*/sample_manifest.json`):

- M04 R01/R01B/R02/R03/R04/R05 (04:59–07:01Z) and M03 R01 (05:20Z) and
  M03 R02 (07:01Z) were run on `d80a52…`.
- M04-FR01..FR05 (10:32–11:15Z) are a final-binary rerun on `3ec51b2c…`.
- M03 R03/R04/R05 (10:03–10:22Z) are on `3ec51b2c…`.
- All M05/M06/M07/M08 pilots from 07:33Z onward are on `3ec51b2c…`,
  except that several R05B/R03-style runs have NO `sample_manifest.json`
  and were not produced by `mmu_formal_runner.py`.

**Therefore the claim "M03 five contexts on the final binary" is false as of
today: M03 R01/R02 were run on `d80a52…`.** M03 R01/R02 need a rerun on the
frozen binary (or a documented static-invariance argument, which is weaker).

## 3. Gaps this closes / leaves

- The final frozen binary will be a NEW hash after the M05–M08 source
  changes. Every formal-sample manifest must record it explicitly; the
  runner must embed the binary SHA256 into `sample_manifest.json` (the
  current runner does not).
- No historical run is deleted or overwritten. `runs/` keeps every failed
  run (e.g., `TEST-M06-R02B`, gem5 exit 124 timeout).
- Stale verdict race found: `runs/TEST-M06-R05B/Validation/verdict.json`
  (20:56:40) predates `prop_evt.txt.gz` (20:56:57); same for
  `TEST-M08-R03` (21:05:57 vs 21:06:38). Those runs have no
  `sample_manifest.json`; their verdicts were produced on a live file.
  Re-validated complete traces are in
  `phase3/freeze/evidence/reval/`.
