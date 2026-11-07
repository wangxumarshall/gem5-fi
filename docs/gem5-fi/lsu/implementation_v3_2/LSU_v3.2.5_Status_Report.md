# LSU v3.2.5 — LP01 implementation and propagation status (2026-11-08)

**Branch:** `lsu-platform-v3.2.5` (base `lsu-platform-v3.2.4` @ `d4b8276e`)
**Binary:** `69a1ca9c5b1cbfb160d0502a8cad8acf7d17101625228978ec79ede588b2287d`
**Scope:** LP01 implementation + five W5 pilots + the nine v3.2.4 DA04 trace
corrections. **No 60-sample formal run.** The 12 models and 60 SampleRunIDs
are unchanged.

## 1. What changed (one commit per unit)

- LP01 payload semantics: byte lane 0 only (`data[0] ^= mask & 0xff`), bounded
  by size; tests for 0/1/4/7/8/9/12/16 bytes.
- LP01 injector: data-load-only eligibility, unified `--l1dfwd_event_ordinal`,
  pre-fault payload capture, eligible-ordinal logging.
- LP01 trace chain: `inj_l1dfwd` (before/after hashes) → `memory_response`
  (post-fault data) → `register_writeback` (actual PRF value after
  `completeAcc`, `value_matches_payload`) → `consumer_commit` (input/output
  values) → `commit`.
- Consumer edges carry the destination register value hash; re-taint uses the
  consumer's output hash.
- DA04: load `mem_req` nodes with the real request tick; causality anchored at
  the load request tick; lossless synthesized edges; LP01 completeness
  profiles; edge/hash validation.
- Pilot runner supports W5/LP01.
- Nine DA04/v3.2.5 documentation corrections (below).

## 2. LP01 semantic ruling (from Excel, not the old code)

Sheet 3 `TargetField=Packet::data[0]`; Sheet 5 `BitEntryByteIndex=byte0 bit3`,
`FaultValue=data[0] ^= 0x08（严格按size逐字节）`, recommended option A. The
model is a **single-bit fault in response byte 0**. For sizes 1/4/7/8/9/12/16
exactly `data[0]` changes; bytes 1..N-1 never change. The v3.2.4 mask-repeat
over byte 8 is not part of LP01-CFG01. The pilot mask is `0x8`.

## 3. Five LP01 pilots (W5 `load_response`)

Excel SampleRunID/Seed are frozen; clinical ordinal chosen by the recorded
probe (Excel ordinal 5 had no consumer, so R05 uses 14). Full per-pilot
detail is in `pilots_v3_2_5/LP01_PILOTS.md`.

| Pilot | Excel ordinal | Clinical | dyn seq | tick | orig → inj (byte 0) | actual WB value | WB hash | first consumer input | consumers | oracle | terminal |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R01 | 1 | 1 | 5 | 172865 | `01…` → `09…` | 9 | `81a3697174a540ac` | 9 | 183 | PASS | MASKED |
| R02 | 2 | 2 | 48 | 226380 | `00…` → `08…` | 8 | `a09e307a7f948acd` | 8 | 1 | PASS | MASKED |
| R03 | 3 | 3 | 239 | 605221 | `10…` → `18…` | 18 | `904aa10b2e892cdd` | 18 | 6 | PASS | MASKED |
| R04 | 4 | 4 | 247 | 605990 | `fbf7d0cc00000000` → `f3f7d0cc00000000` | `0x00000000ccd0f7f3` | `e5704c2542d06b23` | `ccd0f7f3` | 1 | PASS | MASKED |
| R05 | 5 | 14 | 287 | 625625 | `17…` → `1f…` | 31 | `335a4bf00dbb4e7a` | 31 | 6 | PASS | MASKED |

All five: exactly one injection; address, access size and request identity
unchanged; `value_matches_payload=1` (8-byte payload = register value);
`consumer_input_fnv == writeback_value_fnv`; target commit present; validator
VALID; completeness COMPLETE; chain integrity PASS. All terminals are MASKED
(the committed wrong value does not change the W5 checksum). **No LP01 SDC
pilot in this round.**

## 4. DA04 / public-trace corrections (nine items)

| Item | Before | After |
|---|---|---|
| Load memory-request event + real request time | no load `mem_req`; response time only | 3 (R04) / 2 (R05) overlapping load `mem_req` nodes with `request_tick`, `store_write_tick`, `request_before_store_write`, `candidate` |
| Causality anchor | response tick | load request tick; R04/R05 have **0** causally attributable consumers |
| JSONL edges preserve hashes/type | 5 `store_wb` edges with null hash/type | every edge has `edge_type`; synthesized edges carry hashes when available; `missing_type=0` |
| Validator hash continuity | resp→taint only | writeback→consumer input; payload→writeback when `hash_basis=payload_equals_regval` |
| R05 oracle checksum | `0x40f219fae293ba25` | `0xb948f769e7d691f5` (from committed `oracle.log`) |
| R04 consumer count | 9,064 | **1,009** (counted from committed JSONL) |
| DA04 binary SHA | inconsistent header value | `3e9148fc…` (all five manifests; `DA04_BINARY_PROVENANCE.md`) |
| Git branch/HEAD/commit/diff | v3.2.4-only records | `GIT_COMMIT_v325.txt`, `GIT_STATUS_v325.txt`, `LSU_v3.2.5_Git_Diff.txt` |
| SE VA/PA description | “SE vaddr==paddr assumption” | SE has no MMU/PA; memory-side address documented (`LSU_v3.2.5_SE_Address_Semantics.md`) |

**Retraction:** the v3.2.4 R04/R05 SDC verdicts do not survive request-time
causality. R04’s previously attributed load requested at tick 2,286,900,
before the store wrote at 17,042,410 (R05: 13,118,105 < 17,157,910). The
v3.2.5 reruns are **UNRESOLVED / `ORACLE_FAIL_NO_CAUSAL_CONSUMER`** with zero
consumers. They do not overwrite the v3.2.4 directories
(`pilots_v3_2_5/DA04-R04`, `DA04-R05`; see
`LSU_v3.2.5_DA04_Trace_Fix_Evidence.md`). DA04’s
`PROPAGATION_VERIFIED` bit is therefore set to 0 in
`MODEL_STATUS_MATRIX.csv`.

## 5. Verification

- Build `scons -j16 build/ARM/gem5.opt` → exit 0, 0 errors.
- `LP01 byte-0 payload matrix … PASS`; `store-chain attribution
  (request-time) … PASS`; `DA04 byte-enable … PASS`.
- `pytest platform/tests/ -q` → 72 passed.
- W5 no-fault → `checksum=0x99c106541150be0e` (golden).
- All LP01 and DA04-rerun traces: validator VALID.

## 6. State ladder

| Item | State |
|---|---|
| LP01 semantic model | DESIGNED / SOURCE_AUDITED / IMPLEMENTED / COMPILED / UNIT_TESTED |
| LP01 trace chain | IMPLEMENTED / COMPILED / UNIT_TESTED / PILOT_RUN / PROPAGATION_VERIFIED (chain-level; all MASKED) |
| LP01 formal samples | NOT RUN (60-sample round not started) |
| DA04 byte-enable model | unchanged (0xF→0xE) |
| DA04 R04/R05 SDC | **RETRACTED** → UNRESOLVED |
| DA04 trace fixes | IMPLEMENTED / COMPILED / UNIT_TESTED / PILOT_RUN (R04/R05) |

## 7. Remaining problems

1. **SE VA alias matching.** `mem_req`/store-byte matching uses the Request VA;
   a different VA mapping to the same memory location is not matched. This
   does not restore the retracted DA04 claim.
2. **Non-8-byte payload continuity.** The unit matrix covers 1/4/7/8/9/12/16,
   but the pilots are all 8-byte loads; for other sizes the payload and the
   extended register value legitimately hash differently (`hash_basis`).
3. **Warm-up/ROI unfrozen.** The clinical ordinal is a temporary selection;
   the same ordinal can land on a different dynamic instruction under a
   different seed in this O3 configuration (recorded per pilot).
4. **No LP01 SDC pilot.** All five are MASKED; an SDC-observing target has
   not been demonstrated for LP01.
5. **Trace storage.** Each LP01 JSONL is ~43 MB; five traces dominate the
   repository growth for this round.
6. **Vector/matrix consumers.** Their register value hash is null by design;
   only scalar dataflow is hash-continuous.
7. **Formal grid.** No 60-sample run; no multi-cell LP01 grid.
