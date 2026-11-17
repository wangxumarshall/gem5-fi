# LSU When v2 — Evidence Hardening (2026-11-17)

Status: in progress. Work tree: `/home/sdc/gem5-fi-LSU`, branch
`lsu-when-v2-20261116`, HEAD `ada7da89`. Frozen base `d8fcc14d`.
Pre-hardening archive: `archive_frozen_baseline_20261117/` (SHA256 verified,
2831 files OK). New outputs go to `results_hardened/` and `reports_hardened/`.

## Root causes found (evidence-based)

1. **Wrong event association** (`runner/postprocess.py`): injection =
   *first/last* injection row in the file; commit = first commit row; squash =
   first squash row. Measured result: **all 180/180 recorded squashes carry a
   non-target `dyn_inst_seq`**; 9 commits are bound to the wrong injection.
2. **82 INCOMPLETE traces are a naming bug, not data loss**: the 67
   `NO_VISIBLE_MISMATCH` + 15 `HANG_WATCHDOG` runs pass a terminal string that
   is not in the trace TERMINAL enum, so `TraceWriter.close()` raises and no
   summary is written. Source `prop_trace.csv.gz` files pass `gzip -t` and
   contain every event; re-conversion repairs them with no simulation.
3. **A03 9 PARTIAL**: target ordinal/seq has a complete chain (e.g. C02
   ordinal 39 seq 46096 at node 9076+), but postprocess selected the last
   injection (an `injection_nochange` on a later instruction) and the profile
   does not count `injection_nochange`. C05 T01/T02 are genuinely
   `ALREADY_STUCK` (affected=0) at the selected target — persistent F5, target
   value unchanged.
4. **RP01 15 PARTIAL**: the trace *does* carry the causal evidence:
   `RP01_SKIP_REPLAY ... in_instsToReplay_post=0` (only the target ordinal;
   95/95 others post=1), target LQ alloc event, store 110871 complete, no
   response/replay/commit for the target, `watchdog_terminal` with
   `lq_head_seq=target`, `last_commit_dyn_seq=target-1`,
   `silent_ticks≈7.66e9`, and a control with 946/946 post=1 that completes.
   The extractor ignores all of it.
5. **SQ01 C04 T01/T02**: `sq01_chain` says `STORE_COMMITTED_LANE_NOT_READ`,
   but a real `fwd` record shows load 7578 forwarding store 7577 with
   `store_data_forwarded=1` and the faulted hash, and load 7578's LQ entry is
   freed `reason=commit`. `memory_response` is N/A (forwarded, no memory
   path); downstream WB/checksum use is not instrumented. The SDC is real
   (C04 source: `s = when_fnv(s, r ^ w)`), the chain closes at the consumer
   load commit with a documented observation boundary.
6. **Loose gates**: G10 checks only that a verdict field exists, G11 only
   `edges>0`, G12 only that a classification label exists, G19 only that a
   verdict exists.

## Work list (one patch per unit)

- [ ] T1 Converter: add KIND_MAP/UNIT_MAP for model evidence kinds
      (`a03_stream`, `a03_activation`, `a01_ea`, `a01_consumed`,
      `store_commit`, `watchdog_terminal`, `sq01_chain`, `sp05_stage`,
      `sq03_effect`, `fwd` evidence, trace control).
- [ ] T2 Completeness: add optional target-aware mode
      (`check_completeness(path, target=..., hardened=True)`) with 7 explicit
      dimensions, schema terminal normalization, `injection_nochange`
      handling, model-path profiles (incl. SP05, RP01).
- [ ] T3 Postprocess: target-aware selection of injection/activation/
      commit/squash/replay/last-provable; schema terminal mapping; RP01 ledger
      bridge; expose chain_integrity/reasons; `--hardened` output root.
- [ ] T4 `runner/evidence_hardening.py`: re-convert 180 faults into
      `results_hardened/`, emit per-fault `evidence.json`, classify boundaries,
      build model-path status and A03/RP01/SQ01 special evidence.
- [ ] T5 Acceptance: strict G10/G11/G12/G19 (+G14) using evidence records;
      statuses PASS / PASS_WITH_DOCUMENTED_LIMITATION / PARTIAL / FAIL / N/A.
- [ ] T6 Tests: wrong-association rejection, missing-stage detection,
      terminal mapping, RP01 no-auto-pass, SQ01 N/A, G-gate false positives.
- [ ] T7 Regression: reproduce full suite, classify the 32 failures, fix
      portable path issues without touching frozen code/assertions.
- [ ] T8 Package: all required deliverables + SHA256, local commit, no push.

## Verification commands

```
python3 runner/evidence_hardening.py --all
python3 runner/acceptance.py --hardened
cd repo && python3 -m pytest -q tests/test_lsu_when_v2_evidence_hardening.py
cd repo && python3 -m pytest -q tests/
```
