# A03 Propagation Audit — v3.2.12 (supplementary runs)

**Model:** A03 (AGU effective-address bit-3 stuck-at-0, `a03_bit3_stuck0_load`, F5 persistent
tier — the stuck-at condition is applied on EVERY trigger-fired eligible load from the
activation start position)
**Audit date:** 2026-11-10
**Auditor:** A01/A03 evidence auditor (LSU v3.2.12 closure round)
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` (HEAD `f15fe483801db03004e88534aae320a6f93c1993`)
**Binary:** `build/ARM/gem5.opt`, SHA256 `720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070`
(verified with `sha256sum`)
**Standard:** `LSU_Propagation_Acceptance_Standard_v3.2.12.md` (FROZEN); all verdict fields
below are the deterministic output of `tools/lsu_12model_closure.py record`.
**Run set:** 5 fault runs (SUPP-A03-R01..R05, Excel seeds/ordinals 1–5) + 2 controls
(SUPP-A03-C01/C05, `--probability 0.0`).
**Record command actually executed:**

```
python3 tools/lsu_12model_closure.py record --model A03 \
  --pilot-dir .../SUPP-A03-R01 ... --pilot-dir .../SUPP-A03-C05 \
  --json .../audit_v3_2_12/A03_verdict_v3.2.12.json \
  --binary-sha 720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070
```

---

## 1. Headline finding — MISSING_TRACE_NODE: `a03_stream` / `a03_activation`

**No `a03_stream` and no `a03_activation` node exists in any of the seven A03 traces.**
Verified per run over `trace_v31.jsonl`: the non-lifecycle event kinds present are only
`injection`, `injection_nochange`, `address_formed`, `memory_request`, `memory_response`,
`register_writeback`, `consumer_commit`, `commit`, `errant_commit`, `squash`,
`taint_value_mismatch`, `funnel`, `forwarding_decision`, `simulator_abort`. Zero
`a03_*` nodes.

**Where the records stop.** The A03 evidence pipeline (plan Task 8) is staged end-to-end on
the CHAOSAddrPath side and **ends at the sink**:

- `CHAOSAddrPath.cc:520-573` `a03NoteEligibleLoad()` — stages the activation record
  (exactly once, via `chaos_a03::StreamRecorder::activate`, `a03_stream.hh:221-230`) and
  one `chaos_a03::StreamEvent` per fired eligible load, and writes the durable
  log-side copies to `addrpath_injections.log` (the `A03_ACTIVATION` / `A03_STREAM`
  lines, frozen detail format from `a03_stream.hh`).
- The staging accessors exist: `CHAOSAddrPath.hh:88-93` — `a03StreamStaged()`,
  `stagedA03Stream()`, `clearStagedA03Stream()`, `a03ActivationRecord()`.
- **The sink side does not exist anywhere in the binary**: there is no
  `noteA03Activation` / `noteA03Stream` method in
  `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{hh,cc}` and no call site in
  `CHAOS/gem5/src/cpu/o3/lsq.cc` (grep-verified: zero hits; the only staged-record sink
  call sites are the `noteA01EA` calls at lsq.cc:803-808 / 1230-1234). The emission was
  deferred to the main agent (the `a03_stream.hh` writer-discipline comment: "the sink side
  emits them (the a01_ea contract recorded in task-7-report.md)").

**Exact required emitter (the minimal remedy, owner: main agent).** Add to
`CHAOSPropagation.{hh,cc}` the a01-contract sink methods:

- `uint64_t noteA03Activation(uint64_t ptag, const chaos_a03::Activation &a)` —
  `writeNode(ptag, "a03_activation", 0, false, 0, false, 0, false, 0, false, 0, false,
  chaos_a03::activationDetail(a))`, emitted once per run (the recorder already rejects a
  second activation);
- `void noteA03Stream(uint64_t ptag, const chaos_a03::StreamEvent &e)` —
  `writeNode(ptag, "a03_stream", e.dyn_inst_seq, true, 0, false, e.actual_ea, true, 0,
  false, 0, false, chaos_a03::streamDetail(e))` (detail exactly the nine contracted
  fields: `event_ordinal;dyn_inst_seq;pc;eligible;affected;golden_ea;actual_ea;bit;reason`),

and call them from the `LSQ::pushRequest` PRE-site block in `lsq.cc` (immediately after
the `noteA01EA` call, ~lines 803-808), reading
`cpu->chaosAddrPathPre->a03StreamStaged() / stagedA03Stream() / a03ActivationRecord()`,
then `clearStagedA03Stream()`. Read-only trace emission only (no CPU-state change, no
data-path change — the `a03_stream.hh` "ADDITIVE ONLY" contract). The converter
(`platform/tools/prop_trace_to_v31.py`) passes unknown kinds through, so no tool change is
needed for the nodes to reach `trace_v31.jsonl`.

**Consequence for this round's evidence: the five A03 fault runs are
NOT_EVIDENCE_BEARING for the stream.** The v3.2.12 A03 questions — whether R01–R05 are
five ACTIVATION START positions of one persistent fault, and whether the ALREADY_STUCK
case is the masking path rather than a missing event (the exact v3.2.11 open question
quoted in `a03_stream.hh:13-17`) — can only be answered from the `a03_stream` /
`a03_activation` trace nodes. They are absent, so no stream-level verdict is recorded
here. Per the audit instructions, the stream was **not** inferred from injection counts;
the generic per-injection nodes are likewise not accepted as a stream proxy.

For provenance only (log-side facts, not trace evidence): `addrpath_injections.log`
survives complete in all five fault-run dirs (the crash of each run coincides with the
last recorded stream event, so the per-line-flushed log is complete to the crash point)
and carries the staged records in the frozen format, e.g. SUPP-A03-R03 line 1-2:

```
A03_ACTIVATION: tick=204820;bit=3;mode=a03_bit3_stuck0_load
A03_STREAM: event_ordinal=3;dyn_inst_seq=48;pc=0;eligible=1;affected=1;golden_ea=7ffffefda8;actual_ea=7ffffefda0;bit=3;reason=STUCK_APPLIED
```

with per-run first stream rows at ordinals 1/2/3/4/5 for R01/R02/R03/R04/R05
respectively (R01 seq 5 ALREADY_STUCK; R02 seq 48 STUCK_APPLIED; R03 seq 48 STUCK_APPLIED
@ tick 204820 — the same replayed pushRequest as SUPP-A01-R03, an independent
cross-model corroboration of the A01-R03 replay-discard root cause; R04 seq 245
ALREADY_STUCK; R05 seq 253 STUCK_APPLIED). These lines are what the sink nodes would carry;
they are recorded here as provenance, and the runs remain NOT_EVIDENCE_BEARING for the
stream until the sink lands and the pilots are re-run.

## 2. Per-run records (chain = the closure tool's chain, keyed on the crash injection)

All five fault runs crash; the tool's chain for each is the LAST injection — dyn seq 1014,
tick 1657040, golden EA `0xffffffffffb73c58` → actual EA `0xffffffffffb73c50`
(event ids: R01 inj 1313/mem_req 1315; R02 1311/1313; R03 1304/1306; R04 1300/1302;
R05 1298/1300 — earliest anomaly `address_formed` at 1314/1312/1305/1301/1299).

| run | seed/ord | inj count | stream (log-side) | crash chain | fault VA | match |
|---|---|---|---|---|---|---|
| R01 | 663646247 / 1 | 141 | act 80080, ord 1–141 (73 applied, 68 already) | inj 1313 → addr_form 1314 → mem_req 1315 (seq 1014); no resp/wb/commit | `0xffffffffffb73c50` | TRUE |
| R02 | 1626885462 / 2 | 140 | act 197890, ord 2–141 (73/67) | inj 1311 → 1312 → 1313; no resp/wb/commit | `0xffffffffffb73c50` | TRUE |
| R03 | 110775855 / 3 | 139 | act 204820, ord 3–141 (72/67) | inj 1304 → 1305 → 1306; no resp/wb/commit | `0xffffffffffb73c50` | TRUE |
| R04 | 2766846323 / 4 | 138 | act 517440, ord 4–141 (71/67) | inj 1300 → 1301 → 1302; no resp/wb/commit | `0xffffffffffb73c50` | TRUE |
| R05 | 1156093484 / 5 | 137 | act 518210, ord 5–141 (71/66) | inj 1298 → 1299 → 1300; no resp/wb/commit | `0xffffffffffb73c50` | TRUE |

Crash evidence quoted (R03, identical shape in all five): stderr
`panic: ... Page table fault when accessing virtual address 0xffffffffffb73c50`,
`Program aborted at tick 1672440`; summary
`terminal_state=CRASH;terminal_state_reason=page_table_fault_after_injection_address_match`;
`terminal_evidence.page_table_fault_addr=0xffffffffffb73c50`,
`last_injection_dyn_seq=1014`, `last_injection_new_value=0xffffffffffb73c50`,
`address_match=true`; raw oracle `ORACLE_FAIL: no checksum line` (no checksum was printed
before the abort); exit code −6. Run-wide trace content beyond the crash chain (per run):
~70 memory_request / ~63 memory_response / ~66 register_writeback nodes for earlier
stream loads, 30 `squash` nodes, 11 `taint_value_mismatch`, 51-52 `consumer_commit`,
39-40 `commit`, 1 `errant_commit`, 1 `simulator_abort` — these belong to the earlier
injections' chains and are superseded by the stream-node gap above.

Controls C01/C05: exit 0, zero injections (`NO_INJECTION_EVENT`, terminal honestly
UNRESOLVED, `control_misfire=false`), oracle PASS (`expected=728e604ffcec539d
got=728e604ffcec539d`).

## 3. Crash attribution — new evidence vs v3.2.11, and where the tool caps it

The v3.2.11 A03 verdict was PARTIAL with "the crashes are not attributable" (summary §4:
"A03 v3.2.2 R01 panicked at `0xffffffffffb73c50` with injected EA `0x7ffffefdb0`" — no
match). The v3.2.12 runs are the first A03 vintage with **`address_match=true`**: the
panic VA equals the injected actual EA of the crashing load
(`0xffffffffffb73c50 == actual EA of injection seq 1014`) — the standard §1.6
`DIRECT_ADDRESS_MATCH` condition for address-affecting models. The evidence is recorded
in each run's summary/`terminal_evidence` and quoted in §2 above.

The closure tool nevertheless computes, deterministically per the frozen rules:

- `FaultCausality=UNPROVEN` — the tool's CRASH rule requires the `simulator_abort`
  node to sit on the fault's own chain (identity-linked); the abort node carries no
  `ptag`/`dyn_inst_seq`, so it is off-chain. The address-match evidence lives in the
  run-side terminal_evidence, which the frozen chain-identity rules do not consume.
- `RecordIntegrity=TRUNCATED` — the abort cut the gz stream (the converter notes
  "gzip truncation observed"), so standard §6 rule 1 fires and the record grades
  `UNRESOLVED` regardless of the crash terminal (`ObservedTerminal=CRASH` is still
  recorded).

Honest statement: the strongest causal evidence of the round for A03 (five independent
activation contexts each ending in a directly address-matched crash at the same unmapped
load) exists at the run/summary level but is capped at UNRESOLVED by two frozen rules
(off-chain abort node; TRUNCATED record). Upgrading either is a standard revision (a
§10-style amend: e.g. letting the abort record carry the faulting dyn-seq identity, or
defining how a crash-cut stream grades), which only the researcher/standard can make —
this audit records the evidence and the cap, and does not relabel anything.

## 4. Closure-tool verdicts (the eight standard fields, deterministic output)

| Pilot | RecordIntegrity | TraceCompleteness | StructuralChain | Coverage | Causality | Terminal | Oracle | FinalClassification |
|---|---|---|---|---|---|---|---|---|
| R01 | TRUNCATED | COMPLETE | PARTIAL | LIFECYCLE_ONLY | UNPROVEN | CRASH | MISSING | UNRESOLVED |
| R02 | TRUNCATED | COMPLETE | PARTIAL | LIFECYCLE_ONLY | UNPROVEN | CRASH | MISSING | UNRESOLVED |
| R03 | TRUNCATED | COMPLETE | PARTIAL | LIFECYCLE_ONLY | UNPROVEN | CRASH | MISSING | UNRESOLVED |
| R04 | TRUNCATED | COMPLETE | PARTIAL | LIFECYCLE_ONLY | UNPROVEN | CRASH | MISSING | UNRESOLVED |
| R05 | TRUNCATED | COMPLETE | PARTIAL | LIFECYCLE_ONLY | UNPROVEN | CRASH | MISSING | UNRESOLVED |
| C01 | VALID | COMPLETE | NONE | NOT_APPLICABLE | UNPROVEN | NO_INJECTION | PASS | UNRESOLVED |
| C05 | VALID | COMPLETE | NONE | NOT_APPLICABLE | UNPROVEN | NO_INJECTION | PASS | UNRESOLVED |

MissingEvidence (tool): all five fault runs
`ORACLE_MALFORMED;NO_REGISTER_WRITEBACK_EVENT;NO_CONSUMER_EDGE;NO_COMMIT_EVENT` — the
crash-chain load never wrote back or committed (the access faulted), and the raw oracle
has no checksum line; controls `NO_INJECTION_EVENT;TERMINAL_UNRESOLVED` (by design).

Model-level picture under standard §4: **zero complete chains** (the crash chains are
unproven under the frozen identity rules and the records are TRUNCATED), and the
**stream evidence (five activation positions / ALREADY_STUCK masking path) is absent from
every trace** (§1) — so A03 carries no complete verdict and no stream verdict this round.

## 5. Identity preservation vs the original vintages

- Excel seeds/ordinals preserved (663646247/1 … 1156093484/5; the v3.2.11 identity table
  matches), workload golden `728e604ffcec539d` unchanged, controls PASS.
- v3.2.1 A03 terminals: all five CRASH (v3.2.11 seven-stage table) — the SUPP runs
  reproduce CRASH 5/5. The realized crash point moved (v3.2.1: injection seq 1146 @ tick
  1633555, per the v3.2.11 audit §3; v3.2.12: seq 1014 @ tick 1657040) with the same
  platform-drift caveats recorded for A01 (stack layout −0x10, replay-inclusive eligible
  stream). The crash address `0xffffffffffb73c50` is the same unmapped load the v3.2.2
  R01 crashed on — but in v3.2.12 the crashing injection's actual EA IS that address,
  which is what makes the attribution direct this round.
- What is NEW vs v3.2.11: (a) five runs carry the full persistent stuck-at application
  stream log-side (137–141 fired eligible events per run, of which 66–68 per run are
  ALREADY_STUCK no-change applications — the masking-path population); (b) the crashes
  are address-matched (§3). What is STILL OPEN: the stream as trace evidence (§1), the
  writeback/consumer grading of the stream loads (the v3.2.11 gap "writeback/consumer
  events in 5/6 pilots" — the trace-side events now exist run-wide but no per-context
  chain grading is possible while the crash caps the record and the stream nodes are
  absent), and the raw oracle for the crashing runs (no checksum line — recorded
  honestly, never fabricated).

## 6. Remedies (minimal, ordered; owners named; none applied by this audit)

1. **Land the A03 prop-trace sink (§1)** — `noteA03Activation`/`noteA03Stream` in
   CHAOSPropagation + the lsq.cc PRE-site call — then re-run the 5 fault pilots + 2
   controls under the new binary SHA. Only the re-run's traces can carry the stream
   evidence; the current runs stay NOT_EVIDENCE_BEARING for the stream.
2. **Standard revision (researcher's call, §10-style amend) for crash-cut records** —
   decide (a) whether a `simulator_abort` node gets chain identity (e.g. the faulting
   dyn-seq) so a DIRECT_ADDRESS_MATCH crash can grade `FaultCausality=PROVEN`, and
   (b) how a crash-truncated stream grades under §6 rule 1 (currently TRUNCATED →
   UNRESOLVED, which caps even the address-matched crash chains).
3. **A01 §4's golden-EA reference remedy** applies to A03 equally once the stream nodes
   exist (the control-vs-fault response comparison needs the same reference registration).

---

**Verdict files:** `audit_v3_2_12/A03_verdict_v3.2.12.json` (7 records, tool-written),
`audit_v3_2_12/A01_A03_Run_Records_v3.2.12.csv` (per-run evidence table, A03 stream
columns marked log-side).
