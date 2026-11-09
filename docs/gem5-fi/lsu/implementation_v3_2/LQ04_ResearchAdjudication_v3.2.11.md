# LQ04 Research Adjudication — v3.2.11

**Date:** 2026-11-10
**Branch / base:** `lsu-platform-v3.2.11` @ `fb94ebae` (Task 2 tip; this record is the next commit)
**Adjudicated artifacts:** `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R01..R05/` (five fault pilots) and `LQ04-CONTROL-R01..R05/` (five matched no-fault controls) — read-only; no artifact under any `pilots_v3_2_*` was modified.
**Tooling (v3.2.11, Task 2):** `platform/trace_completeness.check_completeness` (returns `structural_chain_completeness`, the structural alias of `propagation_coverage`) and `platform/fault_effect_coverage.classify` (returns `fault_effect_propagation_coverage`), wired exactly as `platform/run_pilot.py` wires them: records from the closed `trace_v31.jsonl`, injection = last `injection`/`injection_nochange` event, terminal = the trace's own summary `terminal_state`.
**Cross-check (not source of truth):** `LQ04_Propagation_Audit_v3.2.10.md` — every number below was re-derived from the ten pilot directories in this worktree; where the v3.2.10 audit reports the same value it is noted in §7.
**Provenance:** binary SHA `f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694` and workload SHA `fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba` (verification in §6.1; `build/ARM/gem5.opt` is absent in this fresh worktree, so the binary SHA is cited from the ten run manifests, all identical); golden oracle `checksum=0xb097eb83f71545cb` (`oracle_source=workload_golden`).

---

## 0. Frozen verdict (applies to the five fault pilots LQ04-R01..R05)

```text
RecordIntegrity=VALID
TraceCompleteness=COMPLETE
StructuralChainCompleteness=COMPLETE
FaultEffectPropagationCoverage=LIFECYCLE_ONLY
PROPAGATION_VERIFIED=0
```

This block is the frozen LQ04 verdict quoted by the v3.2.11 model-status matrix, the Excel
workbook and the final report. It is the aggregate of the five fault pilots re-derived in §2;
each of the five rows independently reproduces every line of the block. The five matched
controls are adjudicated separately in §2 and §3.4 (their honest structural signature is
`PARTIAL` with `missing_stages=[injection]` — there is no fault to propagate by design).

## 1. What this record decides

v3.2.11 splits the question the v3.2.10 label `propagation_coverage=COMPLETE` used to answer
into two dimensions that must never be merged:

- **StructuralChainCompleteness** — did the expected stage kinds appear on the fault's own
  chain (injection → memory_response → register_writeback → consumer_commit), and are the
  chain's value hashes continuous? This is a claim about *trace structure*.
- **FaultEffectPropagationCoverage** — did the injected fault actually diverge a value or a
  control decision, and did that divergence reach a committed architectural outcome? This is
  a claim about *fault effect*.

For LQ04 the two answers differ, and the difference is the research result: the chain is
structurally complete end to end, and it transports the **correct** payload — the fault's
effect (entry-lifetime corruption: `valid 1→0`, `request 1→0`) never enters the data stream.

## 2. Per-pilot re-derivation (all ten runs)

Re-derived in this worktree with the §6.2 command (real output quoted there). Terminal is the
trace summary's own `terminal_state`, cross-checked equal to `pilot_meta.json`
`classification.terminal_state` in all ten runs.

### 2.1 Fault pilots

| Run | Identity (SampleRunID) | Injections | Activation | Terminal | Oracle | RecordIntegrity | TraceCompleteness | StructuralChain | FaultEffectCoverage | Effect reason |
|---|---|---|---|---|---|---|---|---|---|---|
| LQ04-R01 | LQ04-F0-W2-S01-R01 | 1 | TRIGGERED | MASKED | PASS | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | TRIGGERED_NO_DIVERGENCE |
| LQ04-R02 | LQ04-F0-W2-S01-R02 | 1 | TRIGGERED | MASKED | PASS | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | TRIGGERED_NO_DIVERGENCE |
| LQ04-R03 | LQ04-F0-W2-S01-R03 | 1 | TRIGGERED | MASKED | PASS | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | TRIGGERED_NO_DIVERGENCE |
| LQ04-R04 | LQ04-F0-W2-S01-R04 | 1 | TRIGGERED | MASKED | PASS | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | TRIGGERED_NO_DIVERGENCE |
| LQ04-R05 | LQ04-F0-W2-S01-R05 | 1 | TRIGGERED | MASKED | PASS | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | TRIGGERED_NO_DIVERGENCE |

Per-run classifier statistics (§6.2 output): chain events 335/336/335/335/336;
`value_divergence_count=0` and `control_divergence_count=0` in all five (LQ04 has no control
markers by design — its observable effect *is* the entry-lifecycle window);
`downstream_commit_types=[commit, consumer_commit, errant_commit]`; `missing_stages=[]`;
`chain_integrity=PASS`; propagation stages present: `injection, memory_response,
register_writeback, consumer_commit, errant_commit` (the profile for `(LQ04, MASKED)` is
satisfied by its first alternative). The five injection targets are five distinct
`(seq, pc, lq_idx, gen, addr)` tuples — ordinals 1–5 each exactly once (§6.3).

### 2.2 Matched no-fault controls

| Run | Identity (SampleRunID) | Injections | Activation | Terminal | Oracle | RecordIntegrity | TraceCompleteness | StructuralChain | FaultEffectCoverage | Effect reason |
|---|---|---|---|---|---|---|---|---|---|---|
| LQ04-CONTROL-R01 | LQ04-F0-W2-S01-R01 | 0 | NOT_TRIGGERED | UNRESOLVED | PASS | VALID | COMPLETE | PARTIAL | UNRESOLVED | NO_INJECTION_EVENT |
| LQ04-CONTROL-R02 | LQ04-F0-W2-S01-R02 | 0 | NOT_TRIGGERED | UNRESOLVED | PASS | VALID | COMPLETE | PARTIAL | UNRESOLVED | NO_INJECTION_EVENT |
| LQ04-CONTROL-R03 | LQ04-F0-W2-S01-R03 | 0 | NOT_TRIGGERED | UNRESOLVED | PASS | VALID | COMPLETE | PARTIAL | UNRESOLVED | NO_INJECTION_EVENT |
| LQ04-CONTROL-R04 | LQ04-F0-W2-S01-R04 | 0 | NOT_TRIGGERED | UNRESOLVED | PASS | VALID | COMPLETE | PARTIAL | UNRESOLVED | NO_INJECTION_EVENT |
| LQ04-CONTROL-R05 | LQ04-F0-W2-S01-R05 | 0 | NOT_TRIGGERED | UNRESOLVED | PASS | VALID | COMPLETE | PARTIAL | UNRESOLVED | NO_INJECTION_EVENT |

Control semantics (per the v3.2.10 audit §3, re-verified in §6.5): `lq04_injections.log`
absent by construction (injector not mounted; `--probability 0.0`, no `--chaos_lq04`);
`grep -c CHAOS_LQ04` on each control `stdout.log` = 0; terminal `UNRESOLVED /
NO_INJECTION_EVENT` is the honest no-fault signature, not a failure; the identical golden
checksum in all five controls means the fault runs' checksum is not run-to-run variance.

## 3. The evidence that separates the two dimensions

### 3.1 Structural chain complete (the STRUCTURAL side)

For each fault pilot the chain (events sharing the injection's `ptag` or `dyn_inst_seq`)
contains every expected stage — `injection`, `memory_response`, `register_writeback`,
`consumer_commit` — plus `commit`, `errant_commit` and the `lq_lifecycle` records
(alloc / response_probe / restore / free). `check_completeness` reports
`missing_stages=[]` and `chain_integrity=PASS` (its hash-continuity checks — response
`data_fnv` → writeback `source_value_hash`, writeback `writeback_value_fnv` → consumer
`consumer_input_fnv` — found no discontinuity). Re-derived hash agreement per pilot (§6.4):

- response `data_fnv` == writeback `writeback_value_fnv` == writeback `payload_fnv`:
  `c6d4496e17859d5` (R01), `46f9187bab44bc35` (R02), `14fe41788a431ad5` (R03),
  `4f8a555d540fe9f5` (R04), `f9468ffeedcb9ad5` (R05) — `True` in all five;
- first consumer `source_value_hash` == its `consumer_input_fnv` — `True` in all five.

The structural chain is therefore complete **and hash-continuous**. That is exactly what the
historical `propagation_coverage=COMPLETE` recorded (§4).

### 3.2 Fault effect confined to the entry lifecycle (the EFFECT side)

The same chain, graded for effect by `fault_effect_coverage.classify`, shows **zero
divergence** — `value_divergence_count=0`, `control_divergence_count=0`,
`fault_effect_reason=TRIGGERED_NO_DIVERGENCE` — hence `LIFECYCLE_ONLY`, not
`COMPLETE_CAUSAL_CHAIN`. The per-record flags behind that count (re-derived in §6.4):

- the single chained `register_writeback` per pilot carries `data_corruption=0` and
  `value_matches_payload=1` (5/5 pilots);
- every chained `consumer_commit` carries `consumer_input_matches_source=1`:
  326/326 (R01), 327/327 (R02), 326/326 (R03), 326/326 (R04), 327/327 (R05) —
  `consumer_input_matches_source=0` count is **0** in all five;
- `taint_value_mismatch_records=0` (pilot_meta, all five).

So the complete, hash-continuous dataflow graph transports the **correct** payload. The
fault's corrupting effect — `valid 1→0`, `request 1→0` at `executeLoad_post`, no pop, no
reuse, restore at the commit boundary — lives entirely inside the LQ-entry lifecycle window
(injection tick → restore tick), which is what `LIFECYCLE_ONLY` names.

### 3.3 No response loss, correct checksum (the OUTCOME side)

- Response binding (re-derived §6.6): `association=sender_state`,
  `entry_valid_at_response=0`, `entry_request_at_response=0`, `data_unchanged=1` in all five
  fault pilots — the in-flight response arrived while the entry was visibly invalid, was
  recovered through `pkt->senderState`, and delivered the anchor's correct payload. No
  response was dropped and none was mis-bound.
- Oracle (§6.3/§6.5): every one of the ten `oracle.log` files ends `ORACLE_PASS`; the last
  line of every one of the ten `stdout.log` files is `checksum=0xb097eb83f71545cb`, equal to
  the golden oracle. No application SDC.

### 3.4 Why the controls' `PARTIAL` is the honest value

A control has no injection event, so no chain identity exists and the expected-stage profile
for LQ04 cannot be satisfied (`missing_stages=[injection]`, `chain_integrity=UNKNOWN`,
`fault_effect=UNRESOLVED / NO_INJECTION_EVENT`). Reporting `COMPLETE` there would assert a
fault chain that does not exist. The control's job — reproducing the golden checksum with
the injector absent, five times — it fulfils exactly.

## 4. Historical artifacts are unchanged

The ten `pilots_v3_2_10/*/pilot_meta.json` (and every other file under `pilots_v3_2_*`)
are **not modified** by this record or by anything in the v3.2.11 round: all re-derivation
commands are read-only, and `git status --porcelain` was clean apart from this new document
(§6.7). The historical `propagation_coverage=COMPLETE` those files record for the five fault
pilots (and `PARTIAL` for the five controls) is the **structural label only** — stage
presence on the fault's own chain — produced by the pre-v3.2.11 tooling, which answered only
the structural question. It is retained verbatim as a historical record. The research
adjudication of fault-effect propagation is carried by this document's
`FaultEffectPropagationCoverage=LIFECYCLE_ONLY` / `PROPAGATION_VERIFIED=0`, not by rewriting
the pilots. The same applies to `fault_causality=DIRECT_DATAFLOW_EVIDENCE` in the fault
pilots' `pilot_meta.json`: it is the platform's structural label for a chain with direct
dataflow edges, and the same file's `accepted_meaning` states it is "record validity; not a
claim that the fault caused the terminal" — under §3.2 those edges carry the correct value,
so it must not be read as fault-effect propagation.

## 5. Preserved research conclusion

Unchanged from v3.2.10 and re-confirmed by this re-derivation:

- **5/5 injections** — one injection per fault pilot, five distinct targets, ordinals 1–5
  each exactly once (§6.3);
- **5/5 oracle PASS** — and 5/5 in the controls as well (§6.3, §6.5);
- **5/5 MASKED** — terminal `MASKED` / `TARGET_COMMITTED_DATA_VALUE_PRESENT`, target
  committed with the correct data value present (§6.2);
- **no response loss** — senderState binding recorded in all five (§3.3);
- **no wrong-data propagation** — zero diverged values, zero mismatched consumer edges
  (§3.2);
- **no application SDC** — checksum equals the golden oracle in all ten runs (§6.4, §6.5).

And the honesty boundary that motivates this record: **the fault definition was not changed
to obtain SDC.** LQ04 remains what the v3.2.10 freeze defined — corruption of LQ-entry
lifetime metadata (`LQEntry::_valid / _request`) after `executeLoad`, no pop, no reuse,
restore at the commit boundary. The `LIFECYCLE_ONLY` / `PROPAGATION_VERIFIED=0` verdict is
the truthful outcome of that definition under the implemented response path (senderState
binding), reported as such rather than relabelled.

## 6. Commands actually run (real output)

Working directory: worktree root
`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.11` unless stated otherwise.

### 6.1 Provenance

```
$ ls build/ARM/gem5.opt
ls: 无法访问 'build/ARM/gem5.opt': No such file or directory        # fresh worktree: binary absent, cite manifest SHAs
$ sha256sum docs/gem5-fi/lsu/implementation_v3_2/workloads/lq_lifetime_ordinal
fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba  docs/gem5-fi/lsu/implementation_v3_2/workloads/lq_lifetime_ordinal
```

Recorded SHAs extracted from all ten `manifest.json` (+ `pilot_meta.json` oracle/injection
fields) — identical in all ten runs:

```
LQ04-R01..R05          BinarySHA256=f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694 WorkloadSHA256=fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba oracle_expected=checksum=0xb097eb83f71545cb oracle_pass=true injection_count=1
LQ04-CONTROL-R01..R05  BinarySHA256=f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694 WorkloadSHA256=fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba oracle_expected=checksum=0xb097eb83f71545cb oracle_pass=true injection_count=0
```

### 6.2 The ten-pilot re-derivation (classify + check_completeness)

`python3 - <<'PY' … PY` looping over the ten dirs (imports
`platform/trace_completeness.check_completeness`, `platform/trace_validator.read_records`,
`platform/fault_effect_coverage.classify`; terminal = the trace's own summary
`terminal_state`, cross-checked against `pilot_meta.json`). Output, abridged to the two
lines per run (fault pilots verbatim for R01, then the differing fields):

```
LQ04-R01: sample_run_id=LQ04-F0-W2-S01-R01 injections=1 activation=TRIGGERED terminal=MASKED (meta=MASKED) record_integrity=VALID trace_completeness=COMPLETE structural_chain_completeness=COMPLETE propagation_stages=['injection', 'memory_response', 'register_writeback', 'consumer_commit', 'errant_commit'] missing_stages=[] chain_integrity=PASS
    fault_effect_propagation_coverage=LIFECYCLE_ONLY reason=TRIGGERED_NO_DIVERGENCE value_divergence_count=0 control_divergence_count=0 chain_events=335 downstream_commit_types=['commit', 'consumer_commit', 'errant_commit']
LQ04-R02: … terminal=MASKED (meta=MASKED) … structural_chain_completeness=COMPLETE … chain_events=336 …
    fault_effect_propagation_coverage=LIFECYCLE_ONLY reason=TRIGGERED_NO_DIVERGENCE value_divergence_count=0 control_divergence_count=0 …
LQ04-R03: … chain_events=335 … LIFECYCLE_ONLY / TRIGGERED_NO_DIVERGENCE / 0 / 0
LQ04-R04: … chain_events=335 … LIFECYCLE_ONLY / TRIGGERED_NO_DIVERGENCE / 0 / 0
LQ04-R05: … chain_events=336 … LIFECYCLE_ONLY / TRIGGERED_NO_DIVERGENCE / 0 / 0
LQ04-CONTROL-R01: sample_run_id=LQ04-F0-W2-S01-R01 injections=0 activation=NOT_TRIGGERED terminal=UNRESOLVED (meta=UNRESOLVED) record_integrity=VALID trace_completeness=COMPLETE structural_chain_completeness=PARTIAL propagation_stages=['sq_lifecycle'] missing_stages=['injection'] chain_integrity=UNKNOWN
    fault_effect_propagation_coverage=UNRESOLVED reason=NO_INJECTION_EVENT …
LQ04-CONTROL-R02..R05: identical to CONTROL-R01
```

### 6.3 Injection logs and oracle tails

```
$ grep -h "CHAOS_LQ04_INJECTION" pilots_v3_2_10/LQ04-R0*/lq04_injections.log | wc -l
5
$ grep -h "CHAOS_LQ04_INJECTION" pilots_v3_2_10/LQ04-R0*/lq04_injections.log
CHAOS_LQ04_INJECTION: seq=3 pc=0x400338 lq_idx=1 gen=1 request_id=3 addr=0x41ffe8 size=8 eligible=1 ordinal=1 injected=1 tick=80080
CHAOS_LQ04_INJECTION: seq=5 pc=0x400340 lq_idx=3 gen=3 request_id=5 addr=0x41fff8 size=8 eligible=3 ordinal=3 injected=1 tick=133210
CHAOS_LQ04_INJECTION: seq=4 pc=0x40033c lq_idx=2 gen=2 request_id=4 addr=0x41fff0 size=8 eligible=2 ordinal=2 injected=1 tick=80465
CHAOS_LQ04_INJECTION: seq=6 pc=0x400344 lq_idx=4 gen=4 request_id=6 addr=0x420000 size=8 eligible=4 ordinal=4 injected=1 tick=133595
CHAOS_LQ04_INJECTION: seq=7 pc=0x400348 lq_idx=5 gen=5 request_id=7 addr=0x420008 size=8 eligible=5 ordinal=5 injected=1 tick=133980

$ for d in LQ04-R01 LQ04-R02 LQ04-R03 LQ04-R04 LQ04-R05 LQ04-CONTROL-R01 LQ04-CONTROL-R02 LQ04-CONTROL-R03 LQ04-CONTROL-R04 LQ04-CONTROL-R05; do printf '%s: ' "$d"; tail -1 "$d/oracle.log"; done    # run from pilots_v3_2_10/
LQ04-R01: ORACLE_PASS
LQ04-R02: ORACLE_PASS
LQ04-R03: ORACLE_PASS
LQ04-R04: ORACLE_PASS
LQ04-R05: ORACLE_PASS
LQ04-CONTROL-R01: ORACLE_PASS
LQ04-CONTROL-R02: ORACLE_PASS
LQ04-CONTROL-R03: ORACLE_PASS
LQ04-CONTROL-R04: ORACLE_PASS
LQ04-CONTROL-R05: ORACLE_PASS
```

### 6.4 Effect-dimension census (fault pilots)

`python3 - <<'PY' … PY` over the five fault traces (chain-scoped, same identity rule as the
classifier):

```
LQ04-R01: wb=1 (data_corruption=0: 1, value_matches_payload=1: 1) consumers=326 (matches_source=1: 326, =0: 0) resp.data_fnv==wb.writeback_value_fnv==wb.payload_fnv: True (c6d4496e17859d5) first_consumer source_value_hash==consumer_input_fnv: True stdout_last_line='checksum=0xb097eb83f71545cb'
LQ04-R02: wb=1 (…0: 1, …1: 1) consumers=327 (matches_source=1: 327, =0: 0) … True (46f9187bab44bc35) … True … 'checksum=0xb097eb83f71545cb'
LQ04-R03: wb=1 … consumers=326 (…1: 326, =0: 0) … True (14fe41788a431ad5) … True … 'checksum=0xb097eb83f71545cb'
LQ04-R04: wb=1 … consumers=326 (…1: 326, =0: 0) … True (4f8a555d540fe9f5) … True … 'checksum=0xb097eb83f71545cb'
LQ04-R05: wb=1 … consumers=327 (…1: 327, =0: 0) … True (f9468ffeedcb9ad5) … True … 'checksum=0xb097eb83f71545cb'
```

### 6.5 Control cleanliness

```
$ grep -c "CHAOS_LQ04" LQ04-CONTROL-R0*/stdout.log        # from pilots_v3_2_10/
LQ04-CONTROL-R02/stdout.log:0
LQ04-CONTROL-R03/stdout.log:0
LQ04-CONTROL-R04/stdout.log:0
LQ04-CONTROL-R05/stdout.log:0
LQ04-CONTROL-R01/stdout.log:0
$ for d in LQ04-CONTROL-R0[1-5]; do printf '%s: ' "$d"; tail -1 "$d/stdout.log"; done    # run from pilots_v3_2_10/
LQ04-CONTROL-R01: checksum=0xb097eb83f71545cb
LQ04-CONTROL-R02: checksum=0xb097eb83f71545cb
LQ04-CONTROL-R03: checksum=0xb097eb83f71545cb
LQ04-CONTROL-R04: checksum=0xb097eb83f71545cb
LQ04-CONTROL-R05: checksum=0xb097eb83f71545cb
```

### 6.6 Response binding (fault pilots)

```
LQ04-R01: association=sender_state entry_valid_at_response=0 entry_request_at_response=0 data_unchanged=1 request_tick=80080  response_tick=135520
LQ04-R02: association=sender_state entry_valid_at_response=0 entry_request_at_response=0 data_unchanged=1 request_tick=80465  response_tick=136290
LQ04-R03: association=sender_state entry_valid_at_response=0 entry_request_at_response=0 data_unchanged=1 request_tick=133210 response_tick=136291
LQ04-R04: association=sender_state entry_valid_at_response=0 entry_request_at_response=0 data_unchanged=1 request_tick=133595 response_tick=201740
LQ04-R05: association=sender_state entry_valid_at_response=0 entry_request_at_response=0 data_unchanged=1 request_tick=133980 response_tick=202510
```

### 6.7 Historical labels and tree cleanliness

```
$ <python loop over the ten pilot_meta.json>
LQ04-R01..R05          meta.trace.propagation_coverage=COMPLETE meta.classification.propagation_coverage=COMPLETE terminal=MASKED reason=TARGET_COMMITTED_DATA_VALUE_PRESENT fault_causality=DIRECT_DATAFLOW_EVIDENCE
LQ04-CONTROL-R01..R05  meta.trace.propagation_coverage=PARTIAL  meta.classification.propagation_coverage=PARTIAL  terminal=UNRESOLVED reason=NO_INJECTION_EVENT fault_causality=UNKNOWN
$ git status --porcelain
(no output — tree clean before this document was written; the only v3.2.11 change is this file)
```

## 7. Cross-check against the v3.2.10 audit

Every value the v3.2.10 audit (`LQ04_Propagation_Audit_v3.2.10.md`) reports for these ten
runs was reproduced by this re-derivation: injection targets and ticks (§6.3), chain events
335/336/335/335/336 and consumer edges 326/327/326/326/327, per-pilot payload hashes, commit
and restore structure, oracle/checksum results, control census, and both historical
`propagation_coverage` labels. The two records differ only in vocabulary, not in substance:
what v3.2.10 called `PropagationCoverage=LIFECYCLE_ONLY` under its controller ruling is now
carried by the machine-graded `FaultEffectPropagationCoverage=LIFECYCLE_ONLY`
(`fault_effect_coverage.classify`, Task 2), while the tool label `COMPLETE` is retained
under its structural name `StructuralChainCompleteness`. The v3.2.10 §0 ruling and this
record's §0 verdict block state the same adjudication.
