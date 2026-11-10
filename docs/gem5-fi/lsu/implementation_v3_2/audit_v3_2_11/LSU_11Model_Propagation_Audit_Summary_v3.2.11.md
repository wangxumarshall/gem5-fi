# LSU 11-Model Propagation Audit — Summary (v3.2.11)

**Date:** 2026-11-10
**Scope:** A01, A03, FW02, SQ01, DA04, LP01, MD04, FW05, SQ03, SP05, LQ04 (RP01 excluded; not implemented)
**Evidence:** raw `trace_v31.jsonl`, `pilot_meta.json`, `manifest.json`, `oracle.log`/stdout, injection logs, archived package traces (SQ01/FW05/SQ03/SP05), plus the model-specific injection records. Historical reports were used only as cross-checks; every number below was re-derived from the artifacts in this round.
**Method:** `tools/lsu_propagation_audit.py` (streaming seven-stage extraction) plus a manual re-inspection of each model's injection/writeback/consumer records. The generic value-vs-payload check is necessary but not sufficient: LP01 and FW05 carry their fault-effect divergence in model-specific fields (`orig_data_*` vs `inj_data_*`, `true_data_fnv` vs `alt_data_fnv`). Those records were used explicitly and are quoted in each model report.

## 1. Headline answer

- **Four models have a verified fault-effect propagation chain: DA04, LP01, MD04, FW05.** A fifth, FW02, has one verified control-path chain (the suppressed forwarding changed the execution path but delivered identical data).
- **14 unique fault pilots reach `COMPLETE_CAUSAL_CHAIN` with a data-effect divergence** (DA04 2, LP01 5, MD04 3, FW05 4). Adding FW02-R04's control-path chain gives **15/55 unique pilots**.
- **Terminal split among the 14 data-effect pilots: SDC 6, MASKED 8, SQUASHED 0, CRASH 0.** Including FW02-R04: SDC 6, MASKED 9.
- **Seven models do not have a verified complete fault-effect chain**: A01 and A03 are `PARTIAL` (wrong EA reaches the response, but no reference-value comparison and no address-matched crash); SQ01, SQ03, SP05 and LQ04 are `LIFECYCLE_ONLY` (no downstream consumer of the corrupted state); FW02 is mixed (1 complete control-path pilot, 4 partial).
- **`PROPAGATION_VERIFIED=1` only for DA04, LP01, MD04, FW05.** LQ04 remains 0. A pilot run alone (IMPLEMENTED/COMPILED/UNIT_TESTED/PILOT_RUN) is never treated as propagation evidence.

## 2. Per-model verdict

| Model | Unit | Pilot count | Complete causal chain | Lifecycle only | Partial | Model verdict | Propagated? |
|---|---|---:|---:|---:|---:|---|---|
| A01 | AGU | 7 (5 v3.2.1 + 2 v3.2.2) | 0 | 0 | 7 | PARTIAL | no |
| A03 | AGU | 6 (5 v3.2.1 + 1 v3.2.2) | 0 | 0 | 6 | PARTIAL | no |
| FW02 | FWD | 5 | 1 (control path) | 0 | 4 | COMPLETE 1/5; PARTIAL 4/5 | pilot only |
| SQ01 | SQ | 5 | 0 | 5 | 0 | LIFECYCLE_ONLY | no |
| DA04 | SQ | 7 (2 v3.2.6 + 5 v3.2.4) | 2 | 2 | 3 | COMPLETE 2/5 unique | **yes** |
| LP01 | L1D | 5 | 5 | 0 | 0 | COMPLETE 5/5 | **yes** |
| MD04 | LSU | 5 | 3 | 0 | 2 | COMPLETE 3/5 | **yes** |
| FW05 | FWD | 5 | 4 | 0 | 1 | COMPLETE 4/5 | **yes** |
| SQ03 | SQ | 5 | 0 | 5 | 0 | LIFECYCLE_ONLY | no |
| SP05 | SQ | 5 | 0 | 5 | 0 | LIFECYCLE_ONLY | no |
| LQ04 | LQ | 5 | 0 | 5 | 0 | LIFECYCLE_ONLY | no (stays 0) |

## 3. Verified chains — the decisive evidence

### DA04 (byte-enable) — 2/5 complete, SDC
- **R04:** `old_be=0xf;new_be=0xe;store_data_hex=c114af81`; `store_mem_write` records `be_mask=0xe;lane0_packet=0xc1;lane0_before=0xa5;lane0_after=0xa5` (the disabled lane is not written); a later load returns `a514af81` (lane0 = stale `a5`), writes back `81af14a5`, and its consumer receives `0x81af14a5`; `DA04_v326_E2E_EVIDENCE.txt` records 1009 consumers, 0 mismatches, `terminal=SDC reason=ORACLE_FAIL oracle=FAIL`.
- **R05:** same structure with 7714 consumers. **Caveat:** the raw `oracle.log`/`stdout.log` for the v3.2.6 R04/R05 directories is absent; the oracle FAIL is recorded in `pilot_meta.json` and the E2E evidence file. `OracleVerified` is therefore `missing` at the raw-file level.
- R02/R03: the lane is never read (`STORE_COMMITTED_LANE_NOT_READ`) → `LIFECYCLE_ONLY`. R01: SQUASHED → `PARTIAL`. The older v3.2.4 R04/R05 carry an SDC terminal without a chain in that trace → `PARTIAL`; the v3.2.6 re-runs are the authoritative chain.

### LP01 (load response byte0) — 5/5 complete, MASKED
- Injection record (R01): `orig_data_hex=0100000000000000;inj_data_hex=0900000000000000;byte0_before=0x1;byte0_after=0x9;mask=0x8`; the response carries the injected data, the writeback value hash equals the injected payload hash, and the first consumer's input hash equals it (`consumer_input_matches_source=1`). R03 `0x10→0x18`, R05 `0x17→0x1f`.
- All five pilots commit with the correct application checksum (MASKED): the corrupted byte is not used in the final result. The chain is complete to the consumer; the application-level masking is explained.
- The generic payload-vs-writeback check alone would call this `LIFECYCLE_ONLY`; the model-specific `orig_*`/`inj_*` record is the decisive evidence. Raw `oracle.log` is absent in the v3.2.6 directories; the oracle PASS is meta-recorded.

### MD04 (violation-report suppression) — 3/5 complete, MASKED
- Injection record: `family=md04;load_seq=2251;store_seq=2239;addr=0x493990;violation_report_suppressed=1;load_complete=0`. The load nevertheless executes, receives data, writes back `0`, and commits; its consumers receive the correct data and the oracle PASSes (MASKED). The verified effect is the suppressed violation report, not a corrupted value.
- R01/R04 are SQUASHED; the trace does not prove the squash is fault-caused → `PARTIAL`.

### FW05 (wrong forwarding source) — 4/5 complete, SDC
- Injection record (R02): `true_store_seq=12155;alt_store_seq=12154;true_data_fnv=12446998b6871244;alt_data_fnv=a06ea71be9c5aa88;selected_source=alt_store`. The writeback and first consumer carry the alt data hash; the oracle prints `got=549c9e0347adaf23` (R03/f25, R04/f27, R05/f19) against golden `67afad307642983e` — SDC.
- R01 is SQUASHED before a consumer → `PARTIAL`.

### FW02 (suppressed forwarding) — 1/5 complete (control path), MASKED
- R04 (v3.2.1): `load_seq=397;store_seq=383;decision=suppressed;normal_decision=forwarded;fault_decision=suppressed;memory_path=1`. The load took the memory path, wrote back, and its consumer committed. The data is identical (store data 0, memory data 0), so this is a control-path chain, not a data-corruption chain.
- R01/R05: SQUASHED without proof that the squash is fault-caused; the v3.2.4 R01/R05 traces lack a consumer/commit record → `PARTIAL`.

## 4. Why the other models are not verified

- **A01 / A03 (AGU):** the wrong effective address is recorded and reaches the request/response; the consumer receives data from the wrong address. However, the trace has no reference value for the correct address, so it cannot prove the delivered value differs, and the crashes are not attributable: A01 v3.2.2 R01 panicked on VA `0` with injected EA `0x7ffffefda8`; A03 v3.2.2 R01 panicked at `0xffffffffffb73c50` with injected EA `0x7ffffefdb0`; the v3.2.1 stderr files have no fault address. Verdict `PARTIAL`, not `COMPLETE` and not `CRASH`.
- **SQ01 / SQ03 / SP05:** the corrupted store/lane/completion state is written, but no later load consumes the lane and no architectural consumer exists. `STORE_COMMITTED_LANE_NOT_READ` in all pilots. Verdict `LIFECYCLE_ONLY`.
- **LQ04:** structural chain complete, correct payload, no corruption propagation. Verdict `LIFECYCLE_ONLY`, `PROPAGATION_VERIFIED=0` (frozen).

## 5. Missing evidence (per model)

| Model | Missing |
|---|---|
| A01 | Reference value at the correct EA; address-matched crash evidence; raw oracle files for v3.2.1; truncated v3.2.1 traces lack commit/consumer in R03 |
| A03 | Writeback/consumer events in 5/6 pilots; address-matched crash; raw oracle files for v3.2.1 |
| FW02 | Consumer/commit in 4/5 pilots; proof that the R01/R05 squash is fault-caused |
| SQ01 | A later load of the corrupted lane (no consumer) |
| DA04 | Raw oracle.log/stdout for v3.2.6 R04/R05 (meta/E2E only); the v3.2.4 R04/R05 chain is absent |
| LP01 | Raw oracle.log in the v3.2.6 directories (meta-sourced PASS) |
| MD04 | Raw oracle.log in v3.2.6 (meta-sourced PASS); squash causality for R01/R04 |
| FW05 | Proof that the R01 squash is fault-caused |
| SQ03 | A later load of the lane (no consumer) |
| SP05 | Entry-free/drain event; consumer |
| LQ04 | none for the lifecycle verdict |

## 6. Methodological finding

The generic structural/effect classifier is deliberately conservative and uses the delivered payload as its reference. That is correct for LQ04 (correct payload) but **under-reports LP01 and FW05**, whose fault effect is encoded in model-specific injection fields (`orig_data_*`/`inj_data_*` and `true_data_fnv`/`alt_data_fnv`). The audit therefore does not adopt the tool's class blindly: each model report quotes the model-specific record and states the rule. Conversely, the tool does not upgrade a pilot to `COMPLETE` merely because a consumer exists; DA04's v3.2.4 R04/R05 (SDC terminal, no chain in that trace) are `PARTIAL`.

## 7. Answer to the brief's questions

1. **Complete causal chains:** DA04 (2/5), LP01 (5/5), MD04 (3/5), FW05 (4/5); FW02 has one control-path chain (1/5).
2. **Lifecycle/local evidence only:** SQ01, SQ03, SP05, LQ04 (all 5/5 pilots each).
3. **Propagation-chain gaps:** A01, A03 (PARTIAL; no reference value / no address-matched crash), FW02 (4/5 partial), DA04/MD04/FW05 partial pilots for the reasons listed.
4. **Terminal causality not yet proven:** A01 and A03 crashes (address mismatch); FW02 R01/R05 and MD04 R01/R04 squashes; DA04 v3.2.4 R04/R05 SDC terminal without a chain in that trace.
5. **Supplementary experiments needed:** A01, A03, FW02, DA04 (raw oracle), MD04 (squash reason), FW05 (R01 squash), SQ01, SQ03, SP05 — see `SUPPLEMENTARY_PILOT_PLAN_v3.2.11.md`. None executed.
6. **Models truly verified:** **4** (DA04, LP01, MD04, FW05). FW02 is control-path-only and is not counted as a data-effect verified model.
7. **Verified pilots:** **14/55** unique pilots with a data-effect complete chain; **15/55** including FW02-R04's control-path chain.
8. **Terminal split (14):** SDC **6**, MASKED **8**, SQUASHED **0**, CRASH **0**. Including FW02-R04: SDC 6, MASKED 9.

**Formal 60-sample experiment status: NOT_STARTED.** No formal pilot was launched in this round.
