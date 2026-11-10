# LQ04 Propagation Audit — v3.2.12 (re-adjudication of the packet-senderState masking path)

**Model:** LQ04  **SubUnit:** LQ  **Audit date:** 2026-11-10
**Tool:** `tools/lsu_12model_closure.py record` (reusing `tools/lsu_propagation_audit.audit_pilot`; not forked) + raw `trace_v31.jsonl` re-inspection
**Re-adjudication question (plan Task 4):** is the fault-effect chain — the LQ entry made
visibly invalid (`valid=0`, `_request=nullptr`) after `executeLoad`, and the still-in-flight
response resolved to the original request through the packet's `senderState` — **provable from
the runtime traces**, rather than inferred from source reading alone?

**Re-adjudicated verdict (frozen standard `LSU_Propagation_Acceptance_Standard_v3.2.12.md` §6,
computed by the closure tool, never hand-set):**

| Field | Value (5/5 pilots) |
|---|---|
| `FinalClassification` | **`LIFECYCLE_ONLY`** (rule 4: internal-only change) |
| `ObservedTerminal` | **`MASKED`** (`TARGET_COMMITTED_DATA_VALUE_PRESENT`) |
| `MaskingMechanism` (adjudicated in this report) | **`RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE`** — **proven at runtime**, recorded in every trace |
| `FaultEffectPropagationCoverage` | `LIFECYCLE_ONLY` (platform rule `STORE_OR_ENTRY_LIFECYCLE_ONLY`) |
| `FaultCausality` | `PROVEN` (v3.2.12 T2 upgrade from v3.2.11's `NO_VERIFIED_FORWARD_PATH`) |
| `ApplicationOracle` | `PASS` (raw `oracle.log` = frozen golden, all five) |
| `SupplementaryPilotRequired` | **no** — both runtime records (LQ-invalid event, senderState association) are present in all five traces |

The chain is proven end-to-end at runtime — and because it is proven, the classification is
`LIFECYCLE_ONLY`: the senderState association is exactly the mechanism that keeps the delivered
payload intact by construction, so no divergent hop exists to grade `COMPLETE` (§5 below).
This is not an upgrade-in-limbo: v3.2.11's `LIFECYCLE_ONLY` verdict is **confirmed**, now with
mechanism-level runtime proof instead of source-code inference.

---

## 1. Identity and provenance

| Pilot | SampleRunID | Seed | Ordinal | BinarySHA256 (recorded) | WorkloadSHA256 | Oracle golden |
|---|---|---|---|---|---|---|
| LQ04-R01 | LQ04-F0-W2-S01-R01 | 1842987246 | 1 | `f3c2a4423aab81ca…` | `fa25f785a4822eb5…` | `b097eb83f71545cb` |
| LQ04-R02 | LQ04-F0-W2-S01-R02 | 2188214204 | 2 | `f3c2a4423aab81ca…` | `fa25f785a4822eb5…` | `b097eb83f71545cb` |
| LQ04-R03 | LQ04-F0-W2-S01-R03 | 3953171871 | 3 | `f3c2a4423aab81ca…` | `fa25f785a4822eb5…` | `b097eb83f71545cb` |
| LQ04-R04 | LQ04-F0-W2-S01-R04 | 4153250964 | 4 | `f3c2a4423aab81ca…` | `fa25f785a4822eb5…` | `b097eb83f71545cb` |
| LQ04-R05 | LQ04-F0-W2-S01-R05 | 3410523942 | 5 | `f3c2a4423aab81ca…` | `fa25f785a4822eb5…` | `b097eb83f71545cb` |

Full SHAs: binary `f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694`,
workload `fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba`
(`lq_lifetime_ordinal`). All five pilots share one recorded binary and one workload, so the
per-model verdict is computed within a single `BinarySHA256` key — no cross-binary merge
(standard §6 invariant).

**Binary purity check (loud, as instructed).** The record run passed
`--binary-sha 3dccaa10ec5073ca90f2622bd37d5adac1b705bd9faf2497c2d13e46beadd4ed`
(the v3.2.11-round binary, `GIT_COMMIT_v3211.txt`). Every pilot flagged
`BINARY_SHA_MISMATCH`, because the raw manifests record the **v3.2.10-round** binary
`f3c2a442…` that actually produced them (`GIT_COMMIT_v3210.txt`: "LSU v3.2.10 (LQ04) …
Binary SHA256 … f3c2a4423aab81ca…", and the v3.2.11 audit `LQ04_verdict.json` recorded the
same). Adjudication: the raw artifact wins — the pilots are v3.2.10-round runs; the
"produced with the v3.2.11 binary" premise is off by one round. The mismatch is a provenance
labeling fact (missing-matrix `RequiredRunCount=0` per the tool's spec table: "the pilot
re-run under the expected binary, or an explicit per-binary split"), **not** a stage gap and
**not** evidence contamination: it changes no verdict field (all five share one recorded
binary) and no historical artifact was overwritten.

**Determinism controls (read-only inputs).** `LQ04-CONTROL-R01..R05`: 5/5 with
`injection_count=0`, `fault_activation_status=NOT_TRIGGERED`, and raw
`oracle.log` `expected=b097eb83f71545cb got=b097eb83f71545cb ORACLE_PASS`. Zero-injection
replications by design — not independent samples, never terminals (standard §5), excluded
from the five records per the plan's tool command.

---

## 2. Step 1 — the source mechanism (exact `file:line`)

The brief's `CHAOS/gem5/src/cpu/lsq.cc` is `CHAOS/gem5/src/cpu/o3/lsq.cc` in this gem5
vintage (v25.1.0.1); `lsq_unit.cc`/`lsq_unit.hh` are likewise under `src/cpu/o3/`.

**(a) The fault makes the LQ entry visibly invalid after `executeLoad` — and declares the
senderState binding untouched.** `LSQUnit::executeLoad` tail,
`CHAOS/gem5/src/cpu/o3/lsq_unit.cc:796-803`:

> `// LQ04 (LSU v3.2.10): the injection point, at the end of a successful`
> `// executeLoad round. The entry is live and owns its just-issued request`
> `// (LSQRequest::install ran inside initiateAcc); the ordinal-selected`
> `// target moves valid/request into the LQEntry side channel — visibly`
> `// valid=0, request=nullptr — until its commit/squash boundary`
> `// (LSQUnit::lq04Restore). No pop, no early free/reuse; the returned`
> `// fault, the response binding (pkt->senderState) and the data are`
> `// untouched.`

`LSQEntry::corruptLifetime()`, `CHAOS/gem5/src/cpu/o3/lsq_unit.hh:166-174`:
`_lq04Request = _request; _request = nullptr; _valid = false; _lq04Corrupt = true;`
— after the injection, `LQEntry::_valid=0` and `LQEntry::_request=nullptr`.

**(b) The packet carries the request identity in `senderState`, not in the LQ entry.**
`LSQ::SingleDataRequest::buildPackets`, `CHAOS/gem5/src/cpu/o3/lsq.cc:1289-1294`:

> `_packets.push_back(isLoad() ? Packet::createRead(req()) : Packet::createWrite(req()));`
> `_packets.back()->dataStatic(_inst->memData);`
> `_packets.back()->senderState = this;`

`this` is the `LSQRequest`, which holds `_inst` (the `DynInstPtr`) and the fragment
`Request`s. The same binding exists for split accesses, `LSQ::SplitDataRequest::buildPackets`,
`lsq.cc:1357` (`pkt->senderState = this;`), and for the reassembled split response,
`LSQ::SplitDataRequest::recvTimingResp`, `lsq.cc:1276` (`resp->senderState = this;`).
The packet's data destination is `_inst->memData` (`dataStatic`), i.e. the instruction's own
payload buffer — no pointer into the LQ entry is involved.

**(c) The response is resolved through `pkt->senderState`, never through the LQ entry.**
Response path, in call order:

- `LSQ::recvTimingResp`, `CHAOS/gem5/src/cpu/o3/lsq.cc:461-464`:
  `LSQRequest *request = dynamic_cast<LSQRequest*>(pkt->senderState);`
  `panic_if(!request, …); thread[cpu->contextToThread(request->contextId())].recvTimingResp(pkt);`
- `LSQ::completeDataAccess`, `lsq.cc:437-439`: the same `senderState` dynamic_cast, then
  dispatch to the owning `LSQUnit`.
- `LSQUnit::recvTimingResp`, `lsq_unit.cc:102-109`:
  `LSQRequest *request = dynamic_cast<LSQRequest*>(pkt->senderState);`
  with the liveness guard `if (!request->isReleased())`.
- `LSQUnit::completeDataAccess`, `lsq_unit.cc:115-116`:
  `LSQRequest *request = dynamic_cast<LSQRequest *>(pkt->senderState);`
  `DynInstPtr inst = request->instruction();` — **the instruction is recovered from the
  request object**, while the LQ entry at this moment holds `valid=0`, `_request=nullptr`
  (the corrupt window). `lsq_unit.cc:118-123` states this and records it:
  `// … The response is bound by pkt->senderState and never reads the LQ entry;`
  `// this records what the entry ACTUALLY holds when the response arrives`
  `// (expected inside the corrupt window: valid=0, request=nullptr).`
- `LSQ::SingleDataRequest::recvTimingResp`, `lsq.cc:1248-1254`:
  `flags.set(Flag::Complete); _port.completeDataAccess(pkt);` — the response becomes a
  completed data access for the original request.
- The writeback that turns the packet into the architectural register value:
  `LSQUnit::writeback`, `lsq_unit.cc:1393-1395` — `inst->completeAcc(pkt)` ("Complete
  access to copy data to proper place"), reached from `completeDataAccess` via
  `writeback(inst, request->mainPacket())` (`lsq_unit.cc:235`). Again the data source is the
  packet, whose payload buffer `_inst->memData` the packet wrote through `dataStatic`.
- On the retry path, `LSQUnit::trySendPacket`, `lsq_unit.cc:1524-1529`, also resolves the
  packet via `dynamic_cast<LSQRequest*>(data_pkt->senderState)`.

**(d) The boundary restore proves the window is bounded, not destructive.**
`LSQUnit::lq04Restore`, `lsq_unit.cc:928-943`: the stashed request moves back
(`entry.restoreLifetime()`, `lsq_unit.hh:180-188`) at the commit boundary
(`LSQUnit::commitLoad`, `lsq_unit.cc:948-950`) or squash boundary (`lsq_unit.cc:1238`),
after which the normal `clear()`/`freeLSQEntry()` path runs unchanged
(`lsq_unit.cc:966-970`).

**Conclusion of Step 1:** the source mechanism is exactly as the brief states — after
`_request=nullptr`, the response resolves to the original request through
`pkt->senderState` (`LSQ::recvTimingResp` → `LSQRequest` → `request->instruction()`), and
no code on the response path reads `LQEntry::_request` or `LQEntry::_valid` to deliver data.

---

## 3. Step 2 — the runtime facts, per pilot (all citations are `event_id`/`timestamp` in each pilot's `trace_v31.jsonl`)

Every one of the five traces contains **both** runtime records the plan requires: the
LQ-invalid event (injection detail + `response_probe`) and the senderState association
(`association=sender_state` on `memory_response` and `register_writeback`).

| Pilot | Injection (event, tick) | Entry invalid | Response identity (event, tick) | Writeback (event, tick, FNV) | First consumer (event, tick, input FNV) | Restore/Free (tick, entry/gen) | Commit | Final checksum |
|---|---|---|---|---|---|---|---|---|
| R01 | 3, 80080 (seq 3, lq 1/1, addr `0x41ffe8`) | `valid 1→0; request 1→0` | 8, 135520 (`request_id=1`, `response_id=1`, attempt 1/0) | 9, 135520, `c6d4496e17859d5` | 18, 203280, `c6d4496e17859d5`, matches=1 | 136675, lq 1/1 | 10/11, 136290, commit_seq 3 | `b097eb83f71545cb` PASS |
| R02 | 3, 80465 (seq 4, lq 2/2, addr `0x41fff0`) | `valid 1→0; request 1→0` | 8, 136290 (`request_id=2`, `response_id=1`, attempt 1/0) | 9, 136290, `46f9187bab44bc35` | 18, 203280, `46f9187bab44bc35`, matches=1 | 137445, lq 2/2 | 11/12, 137060, commit_seq 4 | `b097eb83f71545cb` PASS |
| R03 | 6, 133210 (seq 5, lq 3/3, addr `0x41fff8`) | `valid 1→0; request 1→0` | 8, 136291 (`request_id=3`, `response_id=1`, attempt 1/0) | 9, 136291, `14fe41788a431ad5` | 18, 203280, `14fe41788a431ad5`, matches=1 | 137830, lq 3/3 | 12/13, 137445, commit_seq 5 | `b097eb83f71545cb` PASS |
| R04 | 6, 133595 (seq 6, lq 4/4, addr `0x420000`) | `valid 1→0; request 1→0` | 12, 201740 (`request_id=4`, `response_id=1`, attempt 1/0) | 13, 201740, `4f8a555d540fe9f5` | 18, 203280, `4f8a555d540fe9f5`, matches=1 | 202895, lq 4/4 | 14/15, 202510, commit_seq 6 | `b097eb83f71545cb` PASS |
| R05 | 6, 133980 (seq 7, lq 5/5, addr `0x420008`) | `valid 1→0; request 1→0` | 12, 202510 (`request_id=5`, `response_id=1`, attempt 1/0) | 13, 202510, `f9468ffeedcb9ad5` | 19, 203665, `f9468ffeedcb9ad5`, matches=1 | 203665, lq 5/5 | 15/16, 203280, commit_seq 7 | `b097eb83f71545cb` PASS |

### 3.1 The six required facts, quoted (LQ04-R01 as the exemplar; the other four are identical in form)

1. **LQ entry invalid after `executeLoad`** — injection `event_id=3`, tick 80080, detail:
   `site=executeLoad_post;family=lq04;field=valid+request;valid_before=1;valid_after=0;request_before=1;request_after=0;lq_idx=1;lq_gen=1;request_id=3;addr=41ffe8;size=8;…;no_pop=1;no_reuse=1;data_unchanged=1`
   (`injection_status=INJECTED`, `activation_status=TRIGGERED`, `ptag=1`). Confirmed still
   invalid **at response time** by the `response_probe` lifecycle event `event_id=7`,
   tick 135520, lq 1/1: `valid_at_response=0;request_present_at_response=0`.
2. **The response's request identity** — `memory_response` `event_id=8`, tick 135520,
   `parent_event_id=3` (the injection), `dyn_inst_seq=3`, `ptag=1`, `lq_entry_id=1`,
   `entry_generation=1`, `execution_attempt_id=1`, `replay_generation=0` (identity rules
   §2.1/2.3/2.5 all present), detail:
   `family=lq04;data_fnv=c6d4496e17859d5;data_hex=0807060504030201;…;association=sender_state;entry_valid_at_response=0;entry_request_at_response=0;data_unchanged=1;request_tick=80080;response_tick=135520`
   — the runtime proof that the response was associated to the original request **via the
   packet senderState while the entry was visibly invalid**. Same record in all five traces.
3. **Writeback data** — `register_writeback` `event_id=9`, tick 135520, `parent_event_id=8`,
   `ptag=1`, detail: `data_corruption=0;association=sender_state;data_unchanged=1;phys_reg=44;arch_reg=2;writeback_value_fnv=c6d4496e17859d5;payload_fnv=c6d4496e17859d5;value_matches_payload=1;…`
   — the register value equals the response payload (data rule: `data_fnv` →
   `writeback_value_fnv`, both `c6d4496e17859d5`).
4. **First consumer input hash** — `consumer_commit` `event_id=18`, tick 203280,
   `dyn_inst_seq=8`, `ptag=1`, detail: `source_value_hash=c6d4496e17859d5;consumer_input_fnv=c6d4496e17859d5;consumer_input_matches_source=1;consumer_output_fnv=c6d4496e17859d5`
   — the consumer edge is hash-verified against the producer (data rule §3). The closure
   record confirms `WritebackValueFnv == ConsumerInputFnv` per pilot (see §4).
5. **Entry free tick/generation** — `lq_lifecycle` restore `event_id=12` then free
   `event_id=13`, both tick 136675, `lq_entry_id=1`, `entry_generation=1`,
   `reason=commit` (identical tick: restore-then-clear-then-pop within `commitLoad`).
6. **Final checksum** — raw `oracle.log`: `expected=b097eb83f71545cb got=b097eb83f71545cb`
   / `ORACLE_PASS` in all five pilots (raw artifact, golden
   `0xb097eb83f71545cb` = `GIT_COMMIT_v3210.txt`'s frozen golden); summary record:
   `run_status=COMPLETED`, `fault_activation_status=TRIGGERED`,
   `terminal_state=MASKED`, `terminal_state_reason=TARGET_COMMITTED_DATA_VALUE_PRESENT`.

### 3.2 Chain-wide integrity (all five pilots)

`chain_integrity=PASS`, `chain_reasons=[]`, `execution_attempt_link=SAME_ATTEMPT`,
`missing_stages=[]`, `taint_value_mismatch_records=0`, chain events 335/335/336/335/336,
consumer operand records 326/327/326/326/327 (R01: 325 of 326 consumer edges are
consumer→consumer re-taint edges, per `fault_effect_coverage._SOURCE_HASH_KEYS`), zero
validation errors, one summary record each. No taint value mismatch exists in any pilot —
the intact payload is proven, not assumed.

---

## 4. Step 3 — the closure-tool adjudication (real command, real output)

Command run from the repo root of worktree
`.claude/worktrees/lsu-platform-v3.2.12` (branch `lsu-platform-v3.2.12`), with the
instructed v3.2.11 binary SHA armed as the purity check:

```bash
python3 tools/lsu_12model_closure.py record --model LQ04 \
  --pilot-dir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R01 \
  --pilot-dir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R02 \
  --pilot-dir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R03 \
  --pilot-dir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R04 \
  --pilot-dir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R05 \
  --json docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LQ04_verdict_v3.2.12.json \
  --binary-sha 3dccaa10ec5073ca90f2622bd37d5adac1b705bd9faf2497c2d13e46beadd4ed
```

Observed output:

```
model=LQ04 pilots=5
  LQ04-R01: FinalClassification=LIFECYCLE_ONLY ObservedTerminal=MASKED missing=[BINARY_SHA_MISMATCH]
  LQ04-R02: FinalClassification=LIFECYCLE_ONLY ObservedTerminal=MASKED missing=[BINARY_SHA_MISMATCH]
  LQ04-R03: FinalClassification=LIFECYCLE_ONLY ObservedTerminal=MASKED missing=[BINARY_SHA_MISMATCH]
  LQ04-R04: FinalClassification=LIFECYCLE_ONLY ObservedTerminal=MASKED missing=[BINARY_SHA_MISMATCH]
  LQ04-R05: FinalClassification=LIFECYCLE_ONLY ObservedTerminal=MASKED missing=[BINARY_SHA_MISMATCH]
```

The five per-pilot records (`LQ04_verdict_v3.2.12.json`, emitted by the tool, never
hand-edited) are uniform:

| Pilot | RecordIntegrity | TraceCompleteness | StructuralChainCompleteness | FaultEffectPropagationCoverage | FaultCausality | ObservedTerminal | ApplicationOracle | FinalClassification | MissingEvidence |
|---|---|---|---|---|---|---|---|---|---|
| R01 | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | PROVEN | MASKED | PASS | LIFECYCLE_ONLY | BINARY_SHA_MISMATCH |
| R02 | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | PROVEN | MASKED | PASS | LIFECYCLE_ONLY | BINARY_SHA_MISMATCH |
| R03 | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | PROVEN | MASKED | PASS | LIFECYCLE_ONLY | BINARY_SHA_MISMATCH |
| R04 | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | PROVEN | MASKED | PASS | LIFECYCLE_ONLY | BINARY_SHA_MISMATCH |
| R05 | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | PROVEN | MASKED | PASS | LIFECYCLE_ONLY | BINARY_SHA_MISMATCH |

Per-pilot feature facts carried by the records: `InjectionVerified=yes`,
`ActivationVerified=yes`, `VerifiedChainCount=0`, `WritebackValueFnv == ConsumerInputFnv`
(`c6d4496e17859d5` / `46f9187bab44bc35` / `14fe41788a431ad5` / `4f8a555d540fe9f5` /
`f9468ffeedcb9ad5`), `ConsumerSourceLinked=True`, `CommitSeq == InjectionSeq` (3..7),
`OracleExpected == OracleActual == b097eb83f71545cb`.

**`SUPPLEMENTARY_PILOT_REQUIRED` is NOT the outcome:** the LQ-invalid event
(`valid_after=0;request_after=0` + `response_probe` `valid_at_response=0;request_present_at_response=0`)
and the senderState association (`association=sender_state` on `memory_response` and
`register_writeback`) are present in **all five** traces, so the conditions for a
supplementary run (plan Task 4 Step 3; ledger ruling "at most one SUPP-LQ04 pilot when the
existing trace lacks the LQ-invalid or senderState-association runtime evidence") do not
fire. **No supplementary pilot was run. No history was overwritten.**

---

## 5. Step 4 — the verdict

### 5.1 The masking chain is proven at runtime

Both facts the re-adjudication was asked to test are recorded in every trace, not inferred:

- the fault's effect is real and observable: for a bounded window (injection tick →
  restore tick: R01 80080→136675; R02 80465→137445; R03 133210→137830; R04 133595→202895;
  R05 133980→203665) the LQ entry holds `valid=0`, `_request=nullptr` while its load is
  still in flight (`response_probe`, all five pilots);
- the response is nonetheless resolved to the original request through the packet's
  `senderState` — recorded as `association=sender_state` on the `memory_response` and again
  on the `register_writeback`, alongside `entry_valid_at_response=0;
  entry_request_at_response=0` and `data_unchanged=1`.

Every hop of the path injection → response → writeback → consumer → commit is identity-linked
(`ptag`, `dyn_inst_seq`, `(lq_entry_id, generation)`, `(execution_attempt_id,
replay_generation)` — standard §2) and hash-verified (data rule §3: `data_fnv` =
`writeback_value_fnv` = `consumer_input_fnv`, `consumer_input_matches_source=1`,
`taint_value_mismatch_records=0`), and the terminal sits on the fault's own chain
(`TARGET_COMMITTED_DATA_VALUE_PRESENT`, `FaultCausality=PROVEN` — the v3.2.12 T2 field
that v3.2.11 expressed ad hoc as "direct dataflow evidence"). The masking mechanism is
therefore stated explicitly, as the plan requires when the chain is proven:

> **MaskingMechanism = `RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE`.**

### 5.2 Why the proven chain grades `LIFECYCLE_ONLY`, not `COMPLETE_CAUSAL_CHAIN`

The plan's Interfaces line offered two outcomes; the frozen standard decides which one
applies, through the closure tool's fixed order (§6) — never a hand pick:

- Rule 3 (`COMPLETE_CAUSAL_CHAIN`) requires `FaultEffectPropagationCoverage=COMPLETE`: "a
  **verified divergence** reached committed architectural state" (standard §1.4). No such
  divergence exists in any pilot: `data_unchanged=1`, `data_corruption=0`,
  `value_matches_payload=1`, `consumer_input_matches_source=1` on every hop,
  `taint_value_mismatch_records=0` chain-wide, `VerifiedChainCount=0`, oracle
  `got==expected`. The platform rule that fires is `STORE_OR_ENTRY_LIFECYCLE_ONLY`, and
  the platform module itself — unchanged this round, per standard §7 — says why:
  `docs/gem5-fi/lsu/implementation_v3_2/platform/fault_effect_coverage.py:10-14`
  ("A structurally complete chain can carry an intact payload end to end (LQ04 is the
  canonical case: the fault corrupts LQ-entry lifetime metadata, **the response is bound by
  senderState**, and the delivered data is unchanged by construction), so the honest effect
  grade for such a run is LIFECYCLE_ONLY, not COMPLETE.") and its `EFFECT_MARKERS["LQ04"]=()`
  (lines 61-65: "no control marker exists and intact LQ04 chains grade LIFECYCLE_ONLY").
- Rule 4 then fires: `FaultEffectPropagationCoverage=LIFECYCLE_ONLY`, injection TRIGGERED,
  `StructuralChainCompleteness=COMPLETE`, terminal `MASKED` (not a hard terminal) →
  `LIFECYCLE_ONLY`. This is the standard's own canonical case (§1.4: "Canonical: LQ04
  'structural chain complete, correct payload, no corruption propagation' — v3.2.11 audit
  §4").

**The missing link, named honestly:** there is **no missing runtime link** — both runtime
records the plan demanded are present in all five traces. What is absent — by construction,
not by missing evidence — is a **divergent value/control hop** (`FaultEffectPropagationCoverage`
is `LIFECYCLE_ONLY`, never `COMPLETE`) : the senderState association delivers the intact
payload across the invalid window, so the fault's effect never leaves the LQ entry
lifecycle. Writing `COMPLETE_CAUSAL_CHAIN` over the tool's deterministic `LIFECYCLE_ONLY`
would be a hand-set verdict (forbidden by the standard's "only path to a verdict") and
exactly the "upgrade on inference alone" the plan forbids. Conversely the verdict is also
**not** `PARTIAL` and **not** `UNRESOLVED`: nothing is missing, the chain is fully verified
— it simply proves an intact payload. v3.2.11's frozen line holds symmetrically: the
definition "must not be changed to obtain SDC" — nor to obtain COMPLETE.

### 5.3 What changed vs v3.2.11 (the substance of the re-adjudication)

| Field | v3.2.11 | v3.2.12 | Why |
|---|---|---|---|
| Structural completeness | COMPLETE | COMPLETE | unchanged |
| Effect coverage | LIFECYCLE_ONLY | LIFECYCLE_ONLY | confirmed by rule 4; the mechanism explains it |
| Terminal / oracle | MASKED / PASS | MASKED / PASS | unchanged (5/5, raw artifacts) |
| Causality | `NO_VERIFIED_FORWARD_PATH` (ad hoc) | **`PROVEN`** (frozen T2 field) | every hop identity+hash verified; terminal on the fault's own chain |
| Response→request association | inferred from source reading | **proven at runtime** (`association=sender_state`, `response_probe`) | this re-adjudication's finding |
| FinalClassification | LIFECYCLE_ONLY | **LIFECYCLE_ONLY** | confirmed; now mechanism-proven, not source-inferred |

**Model verdict: `LIFECYCLE_ONLY` (5/5), `ObservedTerminal=MASKED` (5/5),
`MaskingMechanism=RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE` (proven in all five).**

---

## 6. Missing evidence and supplementary-pilot adjudication

`MissingEvidence = BINARY_SHA_MISMATCH` (5/5) — the provenance finding of §1, adjudicated
there (raw manifests win; one recorded binary for all five pilots; `RequiredRunCount=0`:
no run closes it, it is a labeling split, and Task 16's closure matrix will key these
records under their recorded `BinarySHA256`). No stage-gap code fires:
`NO_*` / `TERMINAL_*` / `ORACLE_*` / `TRACE_*` codes are all absent — injection,
activation, early anomaly (memory_response), intermediate propagation, writeback,
consumer, commit, terminal and raw oracle are `yes` 5/5. **SupplementaryPilotRequired: no.**

## 7. Deviations from the brief, recorded

1. The brief's `CHAOS/gem5/src/cpu/lsq.cc` does not exist in this gem5 vintage; the LSQ
   implementation lives at `CHAOS/gem5/src/cpu/o3/lsq.cc` (+ `lsq_unit.cc/.hh` in the same
   directory). Quoted accordingly.
2. The instructed expected binary SHA (`3dccaa10…`, v3.2.11 round) does not match the
   pilots' recorded binary (`f3c2a442…`, v3.2.10 round that produced them); the mismatch
   was passed, fired loudly on all five records, and adjudicated in §1 rather than silenced.
3. The verdict JSON was emitted solely by the closure tool (`--json`); no field was
   hand-written or hand-edited.
