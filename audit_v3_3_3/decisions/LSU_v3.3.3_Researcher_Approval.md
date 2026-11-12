# LSU v3.3.3 — Researcher Approval Record

**Date:** 2026-11-12
**Packet:** `audit_v3_3_3/LSU_v3.3.3_Researcher_Decision_Packet.md`
**Decision channel:** one-shot AskUserQuestion, four grouped items (no per-model follow-ups).

## Decisions (verbatim selections)

| # | Item | Decision |
|---|---|---|
| 1 | Six candidate workloads (FW02 W4-v2, RP01 partial-overlap, MD04 violations, SQ01/SQ03/SP05 `sq_reload_v3212`) | **全部采用（推荐）** — all six adopted; SQ03 freezes the MASKED/visibility-timing label; SP05 finalizes after the `store_data_fnv` new-build verification. SampleRunID/Seed unchanged. |
| 2 | A01/A03 PRE-retry root-cause fix and five-context ordinal re-census | **批准根因修复+重算（推荐）** — guard the PRE block with `!inst->translationStarted()`, count skipped retries, re-census A01/A03 ROI and percentile ordinals on the new binary; fault semantics, SampleRunID and Seed unchanged; old ordinals retained as v3.3.2 history. |
| 3 | Evidence-based terminal labels | **采用证据标签（推荐）** — A03 = `SDC/ORACLE_FAIL` + `POST_ORACLE_SIM_HANG`; A01-R02 = `SQUASHED` + `UNRELATED_SQUASH_NO_ARCH_ENTRY`; SQ03 = `MASKED / VISIBILITY_TIMING_SHIFT` (4/5 moved + 1/5 lifecycle-only). |
| 4 | Config-freeze definition and EventOrdinal dual-column schema | **批准定义，验证后冻结 SHA（推荐）** — Warm-up=0; ROI = measured main-loop eligible window on the final binary; `Design_EventOrdinal` (1–5) and `Executed_EventOrdinal` (measured) as separate columns; final binary SHA recorded and frozen after validation. |

## Conditions carried forward

- The formal campaign is **not** started by this approval; the Ready Gate and a separate explicit authorization are still required.
- No SampleRunID/Seed change, no model merge/delete, no scope expansion, no frozen-workbook overwrite.
- If a post-build verification fails (A01 writeback, A03 checksum/watchdog, SP05 store-data hash), the affected model is not frozen and the failure is reported as a blocker rather than normalized.
- The A01/A03 re-census must use the fixed binary and must not reuse the old ordinals.

## Approval-independent work authorized to proceed in parallel

SP05 recording fix, control close-path gates, RP01 parsing/normalization, propagation generator, runner/report/provenance tooling, and the v3.3.3 workbook scaffold.
