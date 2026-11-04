# FSU active-scope campaign gate regression tests + FR03 status correction

> Date: 2026-11-04. Branch `fsu` only. No registry edits, no new formal seeds.

## Context

The F0/F5 active-scope policy (`configs/fsu/ACTIVE_SCOPE.json`,
`tools/fsu_scope.py`) and the formal-run gate are already committed.
`tools/fsu_seed_runner.py` has positive/negative tests, but the equivalent
gate in `tools/campaign.py` (regex over the campaign YAML) has no automated
positive/negative test. `docs/gem5-fi/fsu/FR03-GENERATION-SEMANTICS.md` still
claims "真实 gem5 gate 与正式 seed 尚未运行", which is false after the gate
v3 and the FR03 F5 seeds.

## Task 1 — campaign gate helper + tests (one commit)

- [x] Factor the inline regex gate in `tools/campaign.py:1400-1406` into
      `fsu_scope.deferred_frequencies_in(obj)`; campaign calls it unchanged
      in behavior.
- [x] Add `tests/test_fsu_scope.py` cases:
      - F0/F5 → no deferred frequencies (accepted);
      - F1/F2/F3/F4 → deferred (rejected);
      - subprocess `campaign.py --dry` with an F1–F4 RunID exits non-zero,
        prints `frequency outside active scope`, and creates no run dir;
      - subprocess `campaign.py --dry` with an F0/F5 RunID does **not** print
        the scope error (it stops later at schema validation).
- [x] Verify: `python3 -m pytest tests/test_fsu_scope.py -q` and the full FSU
      suite.
- [x] Commit and push.

## Task 2 — FR03 status correction (one commit)

- [x] Replace the stale status paragraph in
      `docs/gem5-fi/fsu/FR03-GENERATION-SEMANTICS.md` with the disk-audited
      state: gate v3 PASS; W3 2/3 (seed3 protocol deviation, documented in
      `FR03-SEED3-PROTOCOL-REVIEW.md`); W5/W6 3/3; no claim of COMPLETE for
      W3.
- [x] Verify: `python3 -m pytest tests/test_fsu_doc_consistency.py -q`.
- [x] Commit and push.

## Non-goals

- No new formal F0/F5 seeds in this unit.
- No edits to `runids.json`, historical evidence, or `runs/fsu`.
- No F1–F4 work beyond the negative test.
