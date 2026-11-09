# LQ04 Propagation Audit — v3.2.10

**Date:** 2026-11-09
**Branch / HEAD:** `lsu-platform-v3.2.10` @ `5adbb220` (audit base; pilots produced at this HEAD)
**Audited artifacts:** `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R01..R05/` (five fault pilots) and `LQ04-CONTROL-R01..R05/` (five matched no-fault controls)
**Frozen definition:** `LQ04_Definition_Freeze_v3.2.10.md` (Excel v3.2.4 row 4; researcher decisions D1–D6)
**Binary SHA256:** `f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694` (`build/ARM/gem5.opt`, re-hashed during this audit — matches every `pilot_meta.json`)
**Workload SHA256:** `fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba` (`workloads/lq_lifetime_ordinal`, re-hashed during this audit — matches every `pilot_meta.json`)
**Golden oracle:** `checksum=0xb097eb83f71545cb` (`workloads/lq_lifetime_ordinal.golden`; `oracle_source=workload_golden`)

---

## 0. Controller ruling (stated up front, governs every verdict below)

The propagation-trace tool records `propagation_coverage=COMPLETE` for the five
fault pilots because the **structural** chain injection → memory_response →
register_writeback → consumer_commit is fully present with value hashes. This
audit does **not** adopt that label for the research question. Per decision D5
(`LQ04_Definition_Freeze_v3.2.10.md` §5: "`PROPAGATION_VERIFIED=1` requires a
real consumer edge; a lifecycle-only chain must remain
`PROPAGATION_COVERAGE=LIFECYCLE_ONLY`") and the controller ruling for this
round:

- **`PropagationCoverage = LIFECYCLE_ONLY`** for LQ04-R01..R05.
- **`PROPAGATION_VERIFIED = 0`** for LQ04-R01..R05.
- Reason: the real consumer edges exist and carry value hashes, but they carry
  the **correct** payload (`data_corruption=0`, `value_matches_payload=1`,
  `consumer_input_matches_source=1` on every edge, `taint_value_mismatch_records=0`).
  The fault's corrupting effect — entry invalidation (`valid=0`,
  `request=nullptr`) — does **not** propagate into the data stream. The
  structural chain is still recorded in full and serves as positive evidence
  for response binding (§2.3), but it is **not** evidence of fault propagation.
- Consequence: **no SDC claim.** Terminal state is MASKED with a correct
  application checksum in all five fault pilots.

The three evidence dimensions are graded separately per pilot in §5 and are
never merged.

---

## 1. Grading dimensions (definitions used in this audit)

| Dimension | Question it answers | Sources |
|---|---|---|
| `RecordIntegrity` | Are the run records complete, self-consistent and validator-clean? | `pilot_meta.json` (`record_integrity`, `validator_errors`), artifact presence |
| `TraceCompleteness` | Does the trace contain every expected lifecycle stage of the fault chain? | `trace_v31.jsonl` stage census vs `expected_stages` |
| `PropagationCoverage` | Did the **fault's effect** reach a real consumer with a corrupted value? | writeback/response hashes, consumer-input hashes, oracle |

`n/a` is used for absent data (control-side fault fields); no silent zeros.

---

## 2. Per-pilot audit tables (fault pilots LQ04-R01..R05)

All values below were re-extracted from the artifacts during this audit
(commands in §6). Paths are relative to
`docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/` unless absolute.

### 2.1 Identity and fault-target fields

| Field | R01 | R02 | R03 | R04 | R05 | Evidence |
|---|---|---|---|---|---|---|
| SampleRunID | LQ04-F0-W2-S01-R01 | LQ04-F0-W2-S01-R02 | LQ04-F0-W2-S01-R03 | LQ04-F0-W2-S01-R04 | LQ04-F0-W2-S01-R05 | `pilot_meta.json` `excel_identity.sample_run_id` |
| RunID / SubTaskID | LQ04-F0-W2 / LQ04-F0-W2-S01 (all five) | | | | | `pilot_meta.json` `excel_identity` |
| Seed (identity cell) | 1842987246 | 2188214204 | 3953171871 | 4153250964 | 3410523942 | `pilot_meta.json` `seed`; frozen in Excel v3.2.4 sheet 5 rows 12–16 |
| EventOrdinal (requested = used) | 1 | 2 | 3 | 4 | 5 | `excel_identity.event_ordinal` / `event_ordinal_used` |
| FaultModelID / FaultConfigID | LQ04 / LQ04-CFG01 (all five) | | | | | `trace_v31.jsonl` `fault_model_id` / `fault_id` |
| FaultLocation (site) | `executeLoad_post` (all five) | | | | | injection record `detail` `site=` |
| DynamicInstSeqNum | 3 | 4 | 5 | 6 | 7 | injection record `dyn_inst_seq` |
| PC | 0x400338 | 0x40033c | 0x400340 | 0x400344 | 0x400348 | `lq04_injections.log` `pc=`; objdump: the five anchor `ldr` instructions at `0x400338/33c/340/344/348` loading x2–x6 from `tbl+0..32` |
| LQEntryID (index) | 1 | 2 | 3 | 4 | 5 | injection `lq_idx=`; `lq_lifecycle` `index=` |
| Entry generation | 1 | 2 | 3 | 4 | 5 | injection `gen=`; `lq_lifecycle` `generation=` |
| RequestID (LSQ-side, injector log) | 3 | 4 | 5 | 6 | 7 | `lq04_injections.log` `request_id=` |
| Trace request/response/fragment IDs | 1/1/1 | 2/1/2 | 3/1/3 | 4/1/4 | 5/1/5 | `memory_response` record `request_id`/`response_id`/`fragment_id` |
| Address (VA) | 0x41ffe8 | 0x41fff0 | 0x41fff8 | 0x420000 | 0x420008 | injection `addr=` |
| Physical addr (response) | 0x1fe8 | 0x1ff0 | 0x1ff8 | 0x2000 | 0x2008 | `memory_response` detail `pa=` |
| Access size | 8 bytes (all five) | | | | | injection `size=` |
| EventOrdinal observed (eligible stream) | 1 | 2 | 3 | 4 | 5 | injection detail `eligible_ordinal=` = `event_ordinal=` |
| InjectionTick | 80080 | 80465 | 133210 | 133595 | 133980 | injection `tick=` / `timestamp` |

The five targets are five distinct `(seq, pc, addr, lq_idx, gen)` tuples — one
anchor Load per run, no overlap (workload design D3; disassembly confirms the
five distinct anchor PCs and addresses).

### 2.2 Entry-state change, occupancy and request in-flight status

From each pilot's `injection` record (`trace_v31.jsonl`, first `record_type=event`,
`event_type=injection`; R01 line 3, R02 line 3, R03 line 6, R04 line 6, R05 line 6):

| Field | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| `valid_before` → `valid_after` | 1 → 0 | 1 → 0 | 1 → 0 | 1 → 0 | 1 → 0 |
| `request_before` → `request_after` | 1 → 0 | 1 → 0 | 1 → 0 | 1 → 0 | 1 → 0 |
| Occupancy before → after | 2 → 2 | 2 → 2 | 5 → 5 | 5 → 5 | 5 → 5 |
| `no_pop` / `no_reuse` | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |
| `data_unchanged` | 1 | 1 | 1 | 1 | 1 |
| `attempt_id` / `replay_gen` | 1 / 0 | 1 / 0 | 1 / 0 | 1 / 0 | 1 / 0 |
| Entry alloc tick (lq_lifecycle `action=alloc`) | 78540 (line 1) | 78925 (line 2) | 132440 (line 3) | 132440 (line 4) | 132440 (line 5) |
| Request in-flight during corrupt window | yes (`request_tick` < `response_tick`, entry fields null throughout) | yes | yes | yes | yes |

Verbatim (R01, `LQ04-R01/trace_v31.jsonl` line 3, `detail` field):

```
site=executeLoad_post;family=lq04;field=valid+request;valid_before=1;valid_after=0;request_before=1;request_after=0;lq_idx=1;lq_gen=1;request_id=3;addr=41ffe8;size=8;occ_before=2;occ_after=2;eligible_ordinal=1;event_ordinal=1;injected=1;attempt_id=1;replay_gen=0;no_pop=1;no_reuse=1;data_unchanged=1
```

Verbatim injector log (R01, `LQ04-R01/lq04_injections.log` line 1):

```
CHAOS_LQ04_INJECTION: seq=3 pc=0x400338 lq_idx=1 gen=1 request_id=3 addr=0x41ffe8 size=8 eligible=1 ordinal=1 injected=1 tick=80080
```

Occupancy is unchanged by the fault (the circular-queue slot count is
untouched; `occ_before == occ_after` in all five), confirming the "do not pop,
do not reuse" constraint at the trace level.

### 2.3 Memory response and sender-state association

From each pilot's `memory_response` record (R01 line 8, R02 line 8, R03 line 8,
R04 line 12, R05 line 12) and the `response_probe` `lq_lifecycle` record
(R01 line 7, R02 line 7, R03 line 7, R04 line 11, R05 line 11):

| Field | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| Response arrival tick | 135520 | 136290 | 136291 | 201740 | 202510 |
| Request tick (sent) | 80080 | 80465 | 133210 | 133595 | 133980 |
| `association` | `sender_state` (all five) | | | | |
| `entry_valid_at_response` | 0 (all five) | | | | |
| `entry_request_at_response` | 0 (all five) | | | | |
| `data_unchanged` | 1 (all five) | | | | |
| Payload `data_hex` | 0807060504030201 | 1817161514131211 | 2827262524232221 | 3837363534333231 | 4847464544434241 |
| Payload FNV-1a hash (`data_fnv`) | c6d4496e17859d5 | 46f9187bab44bc35 | 14fe41788a431ad5 | 4f8a555d540fe9f5 | f9468ffeedcb9ad5 |
| `response_probe` reason | `valid_at_response=0;request_present_at_response=0` (all five) | | | | |

Verbatim (R01 `memory_response` detail, line 8):

```
family=lq04;size=8;data_len=8;data_fnv=c6d4496e17859d5;data_hex=0807060504030201;request_id=1;response_id=1;fragment_id=1;lq_entry_id=1;sq_entry_id=-1;entry_generation=1;execution_attempt_id=1;replay_generation=0;association=sender_state;entry_valid_at_response=0;entry_request_at_response=0;data_unchanged=1;request_tick=80080;response_tick=135520;pa=1fe8
```

Verbatim (R01 `response_probe`, line 7):

```
queue=LQ;action=response_probe;index=1;generation=1;reason=valid_at_response=0;request_present_at_response=0
```

The response was **not dropped and not mis-bound**: it arrived while the entry
was visibly invalid with a null request field, was recovered through
`pkt->senderState` (source-audit fact: the response path never reads the
LQEntry), and delivered the anchor's correct payload. This is the D1 positive
evidence (sender-state association recorded).

### 2.4 Register writeback and data hash

From each pilot's `register_writeback` record (R01 line 10, R02 line 10,
R03 line 10, R04 line 14, R05 line 14):

| Field | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| Writeback tick | 135520 | 136290 | 136291 | 201740 | 202510 |
| Destination arch reg | x2 (arch_reg=2) | x3 (arch_reg=3) | x4 (arch_reg=4) | x5 (arch_reg=5) | x6 (arch_reg=6) |
| Destination phys reg | 44 | 45 | 46 | 47 | 48 |
| `writeback_value` | 0x0102030405060708 | 0x1112131415161718 | 0x2122232425262728 | 0x3132333435363738 | 0x4142434445464748 |
| `writeback_value_fnv` | c6d4496e17859d5 | 46f9187bab44bc35 | 14fe41788a431ad5 | 4f8a555d540fe9f5 | f9468ffeedcb9ad5 |
| `payload_fnv` (response) | c6d4496e17859d5 | 46f9187bab44bc35 | 14fe41788a431ad5 | 4f8a555d540fe9f5 | f9468ffeedcb9ad5 |
| `data_corruption` | 0 (all five) | | | | |
| `value_matches_payload` | 1 (all five) | | | | |
| `hash_basis` | `payload_equals_regval` (all five) | | | | |

Verbatim (R01, line 10, `detail` excerpt):

```
family=lq04;data_corruption=0;association=sender_state;data_unchanged=1;class=int;dest_idx=0;phys_reg=44;arch_reg=2;writeback_value=102030405060708;writeback_value_fnv=c6d4496e17859d5;payload_fnv=c6d4496e17859d5;...;value_matches_payload=1
```

In every pilot the writeback value hash equals the response payload hash: the
load wrote back the **correct** anchor data (little-endian payload → register
value, e.g. bytes `0807060504030201` → `0x0102030405060708`).

### 2.5 Replay, squash, commit and boundary restore

| Field | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| Replay count | 0 | 0 | 0 | 0 | 0 |
| `execution_attempt_id` | 1 (single attempt, all five) | | | | |
| `replay_generation` | 0 (all five) | | | | |
| Squash of target | no (all five) | | | | |
| Commit tick | 136290 | 137060 | 137445 | 202510 | 203280 |
| `commit_seq` | 3 | 4 | 5 | 6 | 7 |
| `commit_status` | COMMITTED (all five) | | | | |
| Restore tick (`reason=commit`) | 136675 | 137445 | 137830 | 202895 | 203665 |
| Free tick (`reason=commit`) | 136675 | 137445 | 137830 | 202895 | 203665 |

Trace line numbers — commit / errant_commit / restore / free:
R01 lines 13/14/16/17; R02 14/15/17/18; R03 15/16/18/19; R04 17/18/20/21;
R05 18/19/21/22.

Verbatim (R01):

```
# line 13 (commit)
trigger=fault_instruction_commit;tracked=fault;pc=400338;commit_seq=3;execution_attempt_id=1;replay_generation=0;is_load=1;is_store=0
# line 14 (errant_commit — the fault-tagged load's commit marker in the chain)
trigger=faulting_load_commit;pc=400338;commit_seq=3
# line 16 (restore) / line 17 (free)
queue=LQ;action=restore;index=1;generation=1;reason=commit
queue=LQ;action=free;index=1;generation=1;reason=commit
```

Verbatim injector log (R01, `LQ04-R01/lq04_injections.log` line 2):

```
CHAOS_LQ04_RESTORE: seq=3 lq_idx=1 gen=1 reason=commit tick=136675
```

The corrupt window closes exactly at the commit boundary: `lq04Restore()`
restores `valid=1`/`request=<stashed>` before `commitLoad()`'s
`assert(loadQueue.front().valid())` (`lsq_unit.cc:947-950`), and the normal
`clear()`/`freeLSQEntry()` then frees the request (the `free` record at the
same tick). No early free, no leak in the implemented configuration.

### 2.6 Consumer edges and input hashes

| Field | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| `register_dataflow` consumer edges | 326 | 327 | 326 | 326 | 327 |
| Chain edges (total) | 330 | 331 | 330 | 330 | 331 |
| Edge kinds | `resp` 1, `taint_reg` 1, `payload_to_register` 1, `errant_commit` 1, `register_dataflow` 326/327 | | | | |
| `consumer_input_matches_source=0` records | 0 | 0 | 0 | 0 | 0 |
| `taint_value_mismatch_records` (pilot_meta) | 0 | 0 | 0 | 0 | 0 |
| Distinct consumer PCs | 12 | 14 | 13 | 13 | 14 |
| First consumer (dyn seq / PC / input) | 8 / 0x40034c / 0x0102030405060708 | 9 / 0x400350 / 0x1112131415161718 | 10 / 0x400354 / 0x2122232425262728 | 11 / 0x400358 / 0x3132333435363738 | 12 / 0x40035c / 0x4142434445464748 |

Verbatim (R01 first `consumer_commit`, `trace_v31.jsonl` line 22, `detail` excerpt):

```
class=int;src_idx=0;pc=40034c;source_value_hash=c6d4496e17859d5;consumer_input_value=102030405060708;consumer_input_fnv=c6d4496e17859d5;...;consumer_input_matches_source=1;...;commit_seq=8
```

The five first-consumer PCs `0x40034c/0x400350/0x400354/0x400358/0x40035c`
are the `mov x0,x2` … `mov x4,x6` register shuffles in the disassembly — each
anchor's first consumer, each receiving exactly the value the target load
wrote back (`0x40034c` = `mov x0, x2` consumes A1's `0x0102030405060708`, and
so on through A5). Every one of the 326/327 edges per pilot carries
`consumer_input_matches_source=1` with the **correct** payload hash: the
dataflow graph is complete, but it transports the fault-free value (basis of
the §0 ruling).

### 2.7 Oracle, terminal state and run status

| Field | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| Oracle expected | `checksum=0xb097eb83f71545cb` (all five, `oracle_source=workload_golden`) | | | | |
| Oracle actual (stdout.log) | `checksum=0xb097eb83f71545cb` (all five) | | | | |
| Oracle verdict | PASS (all five; `oracle.log` ends `ORACLE_PASS`) | | | | |
| gem5 exit code | 0 (all five) | | | | |
| `run_status` | COMPLETED (all five) | | | | |
| `fault_activation_status` | TRIGGERED (all five) | | | | |
| `terminal_state` / `observed_terminal` | MASKED (all five) | | | | |
| `terminal_state_reason` | `TARGET_COMMITTED_DATA_VALUE_PRESENT` (all five) | | | | |
| `trace_completeness` (tool) | COMPLETE (all five) | | | | |
| `record_integrity` (tool) | VALID (all five) | | | | |
| `propagation_coverage` (tool, structural) | COMPLETE (all five) | | | | |
| `accepted` (record validity) | true (all five) | | | | |
| Crash evidence | none (all five; `crash_evidence: null`) | | | | |

Tool chain statistics (`pilot_meta.json` `trace.completeness`): chain_events
335/336/335/335/336; consumer_instructions 261/263/262/262/263; events
17401/17402/17401/17401/17402; edges 330/331/330/330/331; csv_rows
17728/17730/17728/17728/17730; `chain_integrity=PASS`;
`execution_attempt_link=SAME_ATTEMPT`; `validator_errors=[]`; `truncated=false`.

Note on `fault_causality=DIRECT_DATAFLOW_EVIDENCE` (pilot_meta): this is the
platform's structural label for a chain with direct dataflow edges;
`accepted_meaning` in the same file states it is "record validity; not a claim
that the fault caused the terminal". Under the §0 ruling the dataflow edges
carry the correct value, so this label must not be read as fault-effect
propagation.

---

## 3. Control runs (LQ04-CONTROL-R01..R05)

Matched identity per `manifest.json` / `pilot_meta.json`: same
SampleRunID/RunID/SubTaskID/seed/ordinal as the corresponding fault run, same
binary SHA `f3c2a442…`, same workload SHA `fa25f785…`, same golden oracle.
Command differs only by `--probability 0.0` and the absence of `--chaos_lq04`
(the injector is not mounted; `run_pilot.py` omits the flag at probability 0).

| Field | CONTROL-R01..R05 |
|---|---|
| Injections | 0 (all five; `injection_count=0`, `injection.events=[]`) |
| `lq04_injections.log` | absent by construction (SimObject never instantiated) — recorded as `n/a`, not zero-filled |
| `CHAOS_LQ04_*` lines in stdout.log | 0 (grep-verified per directory) |
| Trace record census | `lq_lifecycle` 8648 + `sq_lifecycle` 8420 + 1 summary per control; **no** injection/response/writeback/consumer records |
| `fault_activation_status` | NOT_TRIGGERED (all five) |
| `terminal_state` / reason | UNRESOLVED / `NO_INJECTION_EVENT` (all five) |
| `observed_terminal` | MASKED (all five) |
| Oracle | PASS, `checksum=0xb097eb83f71545cb` identical to fault runs and to each other (all five) |
| gem5 exit code | 0 (all five) |
| `run_pilot.py` exit code | 1 (`accepted=false`: record validity requires ≥1 injection) — expected control signature, by design |
| `propagation_coverage` (tool) | PARTIAL (`missing_stages=[injection]`, `chain_reasons=[no_injection_event]`) |

Control conclusion: with the injector absent, the workload reproduces the
golden checksum exactly; the fault runs' identical checksum is therefore not
attributable to run-to-run variance, and the MASKED terminals in the fault
runs are adjudicated against a clean matched baseline.

---

## 4. Quoted primary evidence (short, with paths)

1. `pilots_v3_2_10/LQ04-R01/lq04_injections.log` (2 lines, whole file):
   `CHAOS_LQ04_INJECTION: seq=3 pc=0x400338 lq_idx=1 gen=1 request_id=3 addr=0x41ffe8 size=8 eligible=1 ordinal=1 injected=1 tick=80080`
   `CHAOS_LQ04_RESTORE: seq=3 lq_idx=1 gen=1 reason=commit tick=136675`
2. `pilots_v3_2_10/LQ04-R05/lq04_injections.log` (line 1):
   `CHAOS_LQ04_INJECTION: seq=7 pc=0x400348 lq_idx=5 gen=5 request_id=7 addr=0x420008 size=8 eligible=5 ordinal=5 injected=1 tick=133980`
3. `pilots_v3_2_10/LQ04-R01/trace_v31.jsonl` line 3 (`injection` detail) — quoted in §2.2.
4. `pilots_v3_2_10/LQ04-R01/trace_v31.jsonl` line 7 (`response_probe`) and line 8 (`memory_response` detail) — quoted in §2.3.
5. `pilots_v3_2_10/LQ04-R01/trace_v31.jsonl` line 10 (`register_writeback` detail) — quoted in §2.4.
6. `pilots_v3_2_10/LQ04-R01/trace_v31.jsonl` lines 13/14/16/17 (commit / errant_commit / restore / free) — quoted in §2.5.
7. `pilots_v3_2_10/LQ04-R01/trace_v31.jsonl` line 22 (first `consumer_commit`) — quoted in §2.6.
8. `pilots_v3_2_10/LQ04-R01/oracle.log` (2 lines, whole file):
   `expected=b097eb83f71545cb got=b097eb83f71545cb`
   `ORACLE_PASS`
9. `pilots_v3_2_10/LQ04-R01/stdout.log` (last line): `checksum=0xb097eb83f71545cb`
10. `pilots_v3_2_10/LQ04-R01/trace_v31.jsonl` line 17732 (`summary`):
    `terminal_state=MASKED`, `terminal_state_reason=TARGET_COMMITTED_DATA_VALUE_PRESENT`,
    `counts={'events': 17401, 'edges': 330, 'injections': 1, 'activations': 330}`.
11. Implementation anchors (source, this worktree):
    `CHAOS/gem5/src/cpu/o3/lsq_unit.hh:166-174` `corruptLifetime()` (asserts
    `_valid && _request != nullptr`, then `_request=nullptr; _valid=false`);
    `:179-188` `restoreLifetime()`; `:110` `_lq04Request` side channel; `:114`
    `_lq04Corrupt`. `CHAOS/gem5/src/cpu/o3/lsq_unit.cc:801-827` injection hook
    at the end of `executeLoad`; `:124-135` response probe;
    `:928-944` `lq04Restore()`; `:947-950` commitLoad restore-before-assert;
    `:981` commitLoads pre-loop acceptance; `:1237-1238` squash boundary
    restore; `:366` drainSanityCheck acceptance.
12. Documented limitation (source audit answer B): the stale-translation flush
    `startStaleTranslationFlush()` (`CHAOS/gem5/src/cpu/o3/lsq_unit.cc:1566-1576`)
    guards `entry.valid() && entry.hasRequest()`, so an LQ04-corrupt entry is
    skipped by the flush and by `checkStaleTranslations()` — the entry's
    in-flight request does not receive `markAsStaleTranslation()` during the
    corrupt window. No pilot exercised a stale translation on a target entry
    (no squash, no translation invalidation in these runs), so this is a
    recorded structural limitation, not an observed failure.

---

## 5. Verdicts per pilot (three dimensions, graded separately)

### Fault pilots

| Pilot | RecordIntegrity | TraceCompleteness | PropagationCoverage (audit, per §0) | PROPAGATION_VERIFIED | SDC | Terminal |
|---|---|---|---|---|---|---|
| LQ04-R01 | VALID | COMPLETE | LIFECYCLE_ONLY | 0 | no | MASKED |
| LQ04-R02 | VALID | COMPLETE | LIFECYCLE_ONLY | 0 | no | MASKED |
| LQ04-R03 | VALID | COMPLETE | LIFECYCLE_ONLY | 0 | no | MASKED |
| LQ04-R04 | VALID | COMPLETE | LIFECYCLE_ONLY | 0 | no | MASKED |
| LQ04-R05 | VALID | COMPLETE | LIFECYCLE_ONLY | 0 | no | MASKED |

- **RecordIntegrity = VALID**: every artifact present and self-consistent
  (`pilot_meta.json` `record_integrity=VALID`, `validator_errors=[]`,
  `truncated=false`); injection log, trace, oracle and classification agree on
  seq/pc/lq_idx/gen/tick/ordinal in all five.
- **TraceCompleteness = COMPLETE**: expected stages
  `injection, memory_response, register_writeback, consumer_commit` all
  present (`missing_stages=[]`), plus the additional recorded stages
  `commit`, `errant_commit`, `lq_lifecycle` (alloc/response_probe/restore/free)
  and the consumer edges.
- **PropagationCoverage = LIFECYCLE_ONLY** (controller ruling §0): the
  fault's effect is confined to the entry lifecycle (invalid interval
  injection→restore at the commit boundary). The data path is structurally
  traced end-to-end but transports the correct payload, so the fault effect
  does not reach a consumer. The tool's structural label
  (`propagation_coverage=COMPLETE`) is retained in `pilot_meta.json` as-is;
  the audit does not rewrite artifacts.

### Control runs

| Pilot | RecordIntegrity | TraceCompleteness | PropagationCoverage | SDC | Terminal |
|---|---|---|---|---|---|
| LQ04-CONTROL-R01..R05 | VALID | COMPLETE | PARTIAL (tool: `missing_stages=[injection]`; audit: n/a — no fault present to propagate) | no (no fault) | UNRESOLVED / NO_INJECTION_EVENT |

---

## 6. Cross-check commands and results (re-run during this audit)

Working directory: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/`.

1. Binary/workload identity (from the worktree root):
   `sha256sum build/ARM/gem5.opt docs/gem5-fi/lsu/implementation_v3_2/workloads/lq_lifetime_ordinal`
   → `f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694  build/ARM/gem5.opt`
   → `fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba  docs/gem5-fi/lsu/implementation_v3_2/workloads/lq_lifetime_ordinal`
   (both equal to every `pilot_meta.json` `BinarySHA256`/`WorkloadSHA256` and to `LQ04_PILOT_SUMMARY.csv`).
2. Injection-log census (five fault pilots): `cat LQ04-R0*/lq04_injections.log`
   → exactly 2 lines per file (1 INJECTION + 1 RESTORE); five distinct
   `(seq,pc,addr,lq_idx,gen)` tuples; ordinals 1–5 each exactly once.
3. Trace record census per fault pilot (python `json` line scan, 17732/17734
   lines): `lq_lifecycle` 8650, `sq_lifecycle` 8420, `consumer_commit`
   326/327, and exactly 1 each of `injection`, `memory_response`,
   `register_writeback`, `commit`, `errant_commit`, `summary`; edge kinds
   `resp`/`taint_reg`/`payload_to_register`/`errant_commit` 1 each +
   `register_dataflow` 326/327. Special lifecycle actions per fault pilot:
   `response_probe` 1, `restore` 1 (target-gated), `reuse` 12 (other entries;
   the target itself is never popped or reused — `no_pop=1;no_reuse=1`).
4. Control census: `grep -c CHAOS_LQ04 LQ04-CONTROL-R0*/stdout.log` → 0 in all
   five; `ls LQ04-CONTROL-R0*/lq04_injections.log` → absent in all five;
   record census → only `lq_lifecycle`/`sq_lifecycle`/`summary`, no fault-chain
   records; `tail -1 …/oracle.log` → `ORACLE_PASS` in all five.
5. Hash agreement: per fault pilot, `memory_response.data_fnv` ==
   `register_writeback.payload_fnv` == `writeback_value_fnv` ==
   `consumer_commit.source_value_hash`/`consumer_input_fnv` (sampled first
   consumer) — verified programmatically for all five pilots;
   `consumer_input_matches_source=0` count = 0 in all five.
6. `LQ04_PILOT_SUMMARY.csv` (10 rows + header): every cell re-derived above
   matches the CSV (`InjectionCount` 1/0, `ResponseMatched=yes`, `RestoreReason=commit`,
   `ReplayCount=0`, `Squash=no`, `ConsumerEdges` 326/327/326/326/327,
   `TerminalState`, `TraceCompleteness`, `PropagationCoverage` as recorded by
   the tool; controls carry `n/a` in fault-only columns).
7. Anchor verification: `objdump -d ../workloads/lq_lifetime_ordinal` shows
   `ldr x2,[x1]` @0x400338, `ldr x3,[x1,#8]` @0x40033c, `ldr x4,[x1,#16]`
   @0x400340, `ldr x5,[x1,#24]` @0x400344, `ldr x6,[x1,#32]` @0x400348, and
   the first A1 consumer `mov x0,x2` @0x40034c — the five injected PCs and the
   first consumer PC in the traces.

---

## 7. Audit conclusion

The LQ04 literal definition was executed exactly as frozen: five ordinal-gated
one-shot injections of `valid=0`/`request=nullptr` at `executeLoad_post`, no
pop, no reuse, restore at the commit boundary. In all five pilots the memory
response arrived while the entry was visibly invalid, was bound via
`senderState`, delivered the correct payload, wrote the correct value to the
destination register, and the target committed; the application checksum
matched the golden oracle. The fault's effect stayed inside the entry
lifecycle. Verdict per the controller ruling: **RecordIntegrity VALID,
TraceCompleteness COMPLETE, PropagationCoverage LIFECYCLE_ONLY,
PROPAGATION_VERIFIED=0, SDC no (terminal MASKED)** — 5/5 fault pilots, with
5/5 matched zero-injection controls reproducing the same checksum.
