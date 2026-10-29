# R6 propagation-path results layout normalization

Date: 2026-10-29
Branch: `fix/r6-results-layout-20261029`
Baseline: `origin/fi-ding` = `3f7c4ed6`

## Goal

One RunID = one directory under `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/`;
every seed doc is `<RunID>/<RunID>-seedN.md`. No top-level `*-seedN.md`.
T = 83, A = 90 (88 real chains + 2 SPEC_EXCLUDED/N/A), total = 173.
Doc bodies are byte-identical to the pre-move copies (verified by SHA-256
against `R6-PROP-MIGRATION-RECORD.json`).

This is a single structural unit (directory layout + index/consumer updates);
it is therefore one commit.

## Units

- [x] U1 — Move 83 T docs to `<RunID>/<RunID>-seedN.md` (content SHA unchanged).
- [x] U2 — Rename 90 A docs to `<RunID>/<RunID>-seedN.md` (content SHA unchanged).
- [x] U3 — Delete 9 stale top-level flat A copies (old duplicates).
- [x] U4 — Update INDEX-A.md / INDEX-V4.md / INDEX.md / INDEX.json to nested paths.
- [x] U5 — Update consumers: `tools/lsu_prop_doc_audit.py` (dir scan via INDEX.json,
      recursive fallback), `tools/r6_a3_prop_docs.py`, `tools/r6_a4_prop_docs.py`,
      `tests/test_lsu_prop_doc_audit.py`, `tests/test_lsu_r6a4_unit_close.py`,
      `runs/lsu/r6_reports/R6-A4-FINAL-REPORT.md`.
- [x] U6 — Add layout contract test `tests/test_lsu_results_layout.py`.
- [x] U7 — Repair `test_referenced_evidence_paths_exist`: command-line backtick
      spans are checked by their executable (first token); a missing path is
      accepted only when the same doc explicitly annotates it `ABSENT`/`缺失`.
      Unannotated missing paths still fail (negative control in
      `R6-RESULTS-REORG-PROGRESS.md` logs).

## Verification (all commands really run)

- `python3 -m pytest -q tests/test_lsu_results_layout.py` -> 20 passed.
- `python3 -m pytest -q tests/test_lsu_prop_doc_audit.py` -> 18 passed.
- `verify_phase2.py` -> PASS (173/83/90/2; SHA vs record; 4 indexes resolve;
  no bare/old seed refs; N/A honesty; success-doc evidence markers).
- Full non-slow regression `PYTEST_ADDOPTS='-m "not slow"' python3
  tools/lsu_test_runner.py` on current vs clean baseline checkout of
  `3f7c4ed6`: FAIL=24 == FAIL=24, **NEW FAIL = 0** (PASS 71 vs 70; the +1 is
  the new suite). gem5 binary absent -> gem5 suites are ENV, gem5 not launched.

## Non-goals

- No gem5 run, no RunID re-execution, no edit to raw evidence.
- No propagation-chain body edits (except the honest ABSENT annotations already
  present in T04/T10, which this patch does not change).
