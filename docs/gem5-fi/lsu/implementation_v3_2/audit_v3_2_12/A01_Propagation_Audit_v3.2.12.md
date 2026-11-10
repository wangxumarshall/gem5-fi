# A01 Propagation Audit — v3.2.12 (supplementary runs)

**Model:** A01 (AGU effective-address bit-3 flip, `a01_bit3_load`, F0 tier, 1 shot)
**Audit date:** 2026-11-10
**Auditor:** A01/A03 evidence auditor (LSU v3.2.12 closure round)
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` (HEAD `f15fe483801db03004e88534aae320a6f93c1993`)
**Binary:** `build/ARM/gem5.opt`, SHA256 `720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070` (verified with `sha256sum`; matches the manifest-side identity of every SUPP record below)
**Standard:** `LSU_Propagation_Acceptance_Standard_v3.2.12.md` (FROZEN). Every verdict field below is the deterministic output of `tools/lsu_12model_closure.py record` (§7); nothing is hand-set.
**Run set:** 5 fault runs (SUPP-A01-R01..R05, Excel seeds/ordinals 1–5) + 2 controls (SUPP-A01-C01/C02, `--probability 0.0`).
**Record command actually executed:**

```
python3 tools/lsu_12model_closure.py record --model A01 \
  --pilot-dir .../SUPP-A01-R01 ... --pilot-dir .../SUPP-A01-C02 \
  --json .../audit_v3_2_12/A01_verdict_v3.2.12.json \
  --binary-sha 720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070
```

Per-run record table: `audit_v3_2_12/A01_A03_Run_Records_v3.2.12.csv` (event ids and ticks
quoted per chain stage below were read from the raw `trace_v31.jsonl`).

---

## 1. Identity preservation vs the original vintages

The SUPP runs preserve the frozen Excel context identity (seed, event ordinal) and the
workload golden (`agu_addrmodes`, oracle expected `728e604ffcec539d`). Terminals reproduce
the v3.2.1 record (plan §2 table) for all five contexts:

| ctx | SUPP run | seed / ordinal | v3.2.1 terminal (doc) | SUPP terminal (summary record) | reproduced? |
|---|---|---|---|---|---|
| 1 | R01 | 2108120075 / 1 | CRASH, oracle FAIL (crash) | CRASH, `page_table_fault_after_injection_no_address_match`, exit −6, raw oracle `ORACLE_FAIL: no checksum line` | yes |
| 2 | R02 | 1113826800 / 2 | MASKED / COMPLETE / PASS | MASKED, `TARGET_COMMITTED_DATA_VALUE_PRESENT`, oracle PASS | yes |
| 3 | R03 | 1302709433 / 3 | UNRESOLVED / COMPLETE / PASS | UNRESOLVED, `UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE`, oracle PASS | yes |
| 4 | R04 | 2194451614 / 4 | MASKED / COMPLETE / PASS | MASKED, `TARGET_COMMITTED_DATA_VALUE_PRESENT`, oracle PASS | yes |
| 5 | R05 | 3228552887 / 5 | MASKED / COMPLETE / PASS | MASKED, `TARGET_COMMITTED_DATA_VALUE_PRESENT`, oracle PASS | yes |

Injection-target drift vs the on-disk originals (recorded honestly, not normalized away):

- **Uniform −0x10 stack shift.** The surviving v3.2.2 artifact
  (`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2/pilots_v3_2_2/A01-R01/addrpath_injections.log`)
  records ordinal 1 at tick 80080 as `old_addr=0x7ffffefda0 → new_addr=0x7ffffefda8`;
  SUPP-A01-R01 records the same event (same tick 80080, same funnel 1/1/1, same dyn seq 5,
  PC `0x400790`) as golden `0x7ffffefd90 → actual 0x7ffffefd98` — the same bit-3 SET
  application on an address shifted −0x10 by the changed SE stack layout of the v3.2.12
  platform. The v3.2.1 identity (injection seq 5 @ tick 80080, PC `0x400790`; R02 seq 48 @
  197890, PC `0x400ad0` — v3.2.11 audit §3) matches the SUPP targets exactly.
- **Context 3 realized a different load.** v3.2.1/v3.2.2 A01-R03 injected dyn seq 169 @
  tick 470085, PC `0x40c0f0` (v3.2.11 audit §3; the v3.2.2 A03-R01 log shows the same
  eligible stream position). SUPP-A01-R03 injects dyn seq 48 @ tick 204820 (the REPLAYED
  second execution of the context-2 load — see §3). Same seed/ordinal, same oracle PASS,
  same UNRESOLVED terminal class, different realized target: the v3.2.12 eligible-event
  stream contains the seq-48 replay, which the old platform's stream did not (its ordinal 3
  was the tick-470085 load). The SUPP runs are therefore *new evidence under the frozen
  v3.2.12 binary*, not a bit-reproduction of v3.2.1 — exactly what the standard's
  never-merge-across-binaries invariant (§6) presumes.

## 2. Per-run chain records (event ids / ticks quoted from `trace_v31.jsonl`)

### SUPP-A01-R01 (ctx 1, seed 2108120075, exit −6)

| stage | event | id / tick | detail |
|---|---|---|---|
| funnel | `funnel` | 2 / 80080 | `attempted=1;eligible=1;injected=1` |
| injection | `injection` | 3 / 80080 | seq 5, ptag 1, `old=0x7ffffefd90;new=0x7ffffefd98`, site `lsq_pushRequest_PRE`, TRIGGERED |
| earliest anomaly | `address_formed` | 4 / 80080 | va `0x7ffffefd98` |
| EA record | `a01_ea` | 5 / 80080 | `pc=400790;golden_ea=7ffffefd90;actual_ea=7ffffefd98;xor_delta=8;bit=3;access_size=8;affected=1;request_va=7ffffefd98;fault_va=NOT_APPLICABLE` |
| memory_request | `memory_request` | 6 / 80080 | site `lsq_sendFragmentToTranslation`, request_id 1, lq_entry 1 |
| memory_response | `memory_response` | 18 / 148225 | `data_hex=02fffeff7f000000;data_fnv=f971edcd05e4ccc2;pa=7efd98`; attempt 1 |
| register_writeback | `register_writeback` | 19 / 148225 | `writeback_value=7ffffeff02;writeback_value_fnv=f971edcd05e4ccc2;payload_fnv=f971edcd05e4ccc2;value_matches_payload=1`; phys r45/a1 |
| commit | `commit` | 20 / 148995 | `commit_seq=5`; attempt 1; `tracked=fault;is_load=1` |
| errant commit | `errant_commit` | 21 / 148995 | `trigger=faulting_load_commit` |
| consumer | `a01_consumed` | 23 / 149765 | `consumer_seq=25;consumer_kind=register_source;input_hash=f971edcd05e4ccc2` |
| consumer commits | `consumer_commit` ×12 | 24..155 | on-chain consumers seq 25, 31, 46, 47, 81, 82, 83, 95, 96, 98, 265, 270 (commit_seqs 21..131) |
| terminal | `simulator_abort` + summary | 1011; abort at tick 3829980 | stderr: `panic: ... Page table fault when accessing virtual address 0` (from `Commit::commitHead → GenericPageTableFault`); `page_table_fault_addr=0;address_match=False` |
| oracle | raw | — | `ORACLE_FAIL: no checksum line` (run aborted; no checksum line was ever printed) |

### SUPP-A01-R02 (ctx 2, seed 1113826800, exit 0) — full-chain MASKED

funnel `21/197890` (`attempted=15;eligible=2;injected=1`); injection `21/197890` (seq 48,
golden `0x7ffffefda8` → actual `0x7ffffefda0`, xor_delta 8, bit 3); `a01_ea` `23/197890`;
memory_request `24/197890` (request_id 14, va `0x7ffffefda0`); memory_response `33/205590`
(`data_hex=0000000000000000;data_fnv=a8c7f832281a39c5;pa=7eda0`, attempt 2);
register_writeback `34/205590` (`writeback_value=0;writeback_value_fnv=a8c7f832281a39c5`);
commit `35/206360` (commit_seq 44, attempt 2) + errant_commit `36`; LQ free `37/206745`
(entry 2, gen 2); a01_consumed `38/206745` (`consumer_seq=50;input_hash=a8c7f832281a39c5`);
consumer_commit `39/206745` (seq 50, commit_seq 46, `consumer_input_fnv=a8c7f832281a39c5`,
`consumer_input_matches_source=1`). Oracle `expected=728e604ffcec539d got=728e604ffcec539d →
ORACLE_PASS`.

### SUPP-A01-R03 (ctx 3, seed 1302709433, exit 0) — chain stops after a01_ea

funnel `21/204820` (`attempted=19;eligible=3;injected=1`); injection `22/204820` (seq 48,
golden `0x7ffffefda8` → actual `0x7ffffefda0`); address_formed `23/204820`; a01_ea `24/204820`
(`request_va=7ffffefda0;fault_va=NOT_APPLICABLE`); **no memory_request, no memory_response,
no register_writeback, no a01_consumed, no consumer_commit, no errant_commit in the entire
trace**; commit `32/206360` (seq 48, commit_seq 44, **execution_attempt_id=2**);
lq_lifecycle free `33/206745` (entry 2, gen 2, reason commit). Oracle PASS. Terminal
`UNRESOLVED / UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE`. Root cause in §3.

### SUPP-A01-R04 (ctx 4, seed 2194451614, exit 0) — full-chain MASKED

funnel `100/517440` (`attempted=46;eligible=4;injected=1`); injection `101/517440` (seq 245,
golden `0x7ffffefdb0` → actual `0x7ffffefdb8`); a01_ea `103/517440` (PC `40c0f0`);
memory_request `104/517440`; memory_response `111/518211`
(`data_hex=fbf7d0cc00000000;data_fnv=1505defdf2164c5b`); register_writeback `112/518211`
(`writeback_value=ccd0f7fb;writeback_value_fnv=1505defdf2164c5b`); commit `123/519365`
(commit_seq 126) + errant_commit `124`; a01_consumed `132/520520`
(`consumer_seq=250;input_hash=1505defdf2164c5b`); consumer_commits `133,134` (seq 250, 251)
+ `taint_value_mismatch` ×3 (seq 252, commit_seq 133). Oracle PASS.

### SUPP-A01-R05 (ctx 5, seed 3228552887, exit 0) — full-chain MASKED

funnel `106/518210` (`attempted=48;eligible=5;injected=1`); injection `107/518210` (seq 253,
golden `0x7ffffefdb8` → actual `0x7ffffefdb0`); a01_ea `109/518210` (PC `40c110`);
memory_request `110/518210`; memory_response `119/518980`
(`data_hex=1000000000000000;data_fnv=987468c2d70edbd5`); register_writeback `120/518980`
(`writeback_value=10;writeback_value_fnv=987468c2d70edbd5`); commit `124/520135`
(commit_seq 134) + errant_commit `125`; a01_consumed `127/520520`
(`consumer_seq=254;input_hash=987468c2d70edbd5`); consumer_commit `128/520520` (seq 254,
commit_seq 135). Oracle PASS.

### Controls C01/C02 (exit 0, zero injections by design)

Both traces carry only `forwarding_decision`/`lq_lifecycle`/`sq_lifecycle` events + summary
(`NO_INJECTION_EVENT`, terminal honestly UNRESOLVED per the v3.2.11 A4 ruling; never
relabeled MASKED). `control_misfire=false`. **Both control traces contain ZERO
memory_request / memory_response / register_writeback nodes** — determinative for §4 below.

## 3. SUPP-A01-R03 — the missing register-writeback edge: root cause

**Which node is absent.** The register-writeback node for the faulting load
(dyn_inst_seq 48), and with it the whole memory-side chain: no `memory_request` at the
actual EA, no `memory_response`, no `register_writeback`, no taint entry, no
`a01_consumed`, no `consumer_commit`, no `errant_commit`. What remains on the chain is
injection(22) → address_formed(23) → a01_ea(24), then the commit node (32, ptag 0,
dyn-seq identity) and the LQ free (33).

**It was NOT squashed and NOT a lost writeback.** The load committed (commit event 32,
`commit_seq=44`, COMMITTED) and the LQ entry freed with reason=commit at tick 206745 — the
writeback physically happened (the load completed and committed with data). What is absent
is the *trace node*, because the tracer is chain-scoped: `register_writeback` nodes are
emitted only out of `pending_chain_wb` entries created inside `noteMemResponse` after a
registry hit (`CHAOSPropagation.cc:968-969` returns before any node when `hit_ptag==0`;
`:1112-1121` creates the pending writeback only on a hit).

**Root cause (evidence-anchored).** The A01 PRE-hook injection for context 3 (event
ordinal 3) fired on the **replayed second execution attempt** of load seq 48 — at the
pushRequest of tick 204820 (attempt 1 was ordinal 2, tick ~197890, proven by R02 where
ordinal 2 fires there and its request is created in the same tick). The commit record
carries `execution_attempt_id=2` (the counter incremented by `LSQUnit::executeLoad`,
`lsq_unit.cc:723` — a replay). At that pushRequest `inst->translationStarted()` was
already true, so `LSQ::pushRequest` took the reuse branch (`lsq.cc:827-830`)
`request = inst->savedRequest` — the request built at attempt 1, whose vaddr is the
**golden** EA `0x7ffffefda8` — and the PRE hook's corrupted by-value addr
(`0x7ffffefda0`) was discarded before any Request was constructed. Consequences,
each verified in source:

1. No fragment with the actual EA ever reached `sendFragmentToTranslation`, so
   `noteMemRequest` (`CHAOSPropagation.cc:737-755`) never range-matched the registry entry
   `[0x7ffffefda0, +8)` → no `memory_request` node (whole trace: zero).
2. The golden-address request/response never matched the registry in `noteMemResponse`
   (`:877-891`: golden `0x...da8` is the exclusive end of `[0x...da0,+8)`) → no
   `memory_response` node, no `pending_chain_wb` → no `register_writeback` node.
3. Without a writeback hash there is no taint entry → no consumer chain at all.
4. The load served the **golden** EA's data; the fault diverged nothing. Oracle PASS is
   consistent with a genuinely inert injection.

Independent cross-model corroboration: **SUPP-A03-R03** — a different model (bit-3
stuck-at-0) selecting the same ordinal 3 — logs `A03_STREAM:
event_ordinal=3;dyn_inst_seq=48;...;golden_ea=7ffffefda8;actual_ea=7ffffefda0` at the same
tick 204820, and its trace likewise has no memory_request/response/writeback for seq 48
(its earliest response node belongs to seq 253, ordinal 5). Two models, one mechanism.

An honesty caveat this exposes: `a01_ea.request_va` is the *staged* EA the hook computed,
not an observed Request vaddr — in R03 no Request ever carried it. The plan §3 expectation
"request_va == actual_ea" holds only at the staging level.

**Verdict preserved.** The evidence is genuinely absent (the trace cannot show what value
the faulted load wrote back, by tracer design), so per the standard §1.6/§6 rule 1 the
record stays exactly as the tool computed: `ObservedTerminal=UNRESOLVED`,
`UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE`, `FinalClassification=UNRESOLVED`,
`MissingEvidence=NO_REGISTER_WRITEBACK_EVENT;NO_CONSUMER_EDGE;TERMINAL_UNRESOLVED`.
No upgrade, no hand-relabel.

**Minimal remedy (source-side, read-only trace change; owner: main agent — not applied by
this audit).** At the PRE-site block in `lsq.cc` (after the `noteA01EA` call, ~line 808),
when the hook injected but `inst->translationStarted()` is true, emit an explicit
read-only discard node (e.g. `a01_ea_discarded`, or an `a01_ea` detail flag
`applied_to_request=0`) stating that the corrupted EA was discarded by the savedRequest
reuse. That converts a silent structural absence into an honest on-chain fact ("fault
discarded before any request; the load served the golden EA") — the precondition for any
future standard revision (§10-style) to grade this case as an evidenced inert injection
instead of UNRESOLVED. The alternative — making replayed pushRequests ineligible for the
A01 PRE injection — changes the frozen ordinal/eligible-event semantics and must go
through the standard's revise path, not an audit. Fabricating the resp→writeback hash
link to satisfy §3 is forbidden and was not considered.

## 4. Reference-value comparison (plan §4 Step 2) — DataDelta NOT OBSERVABLE

The plan's numeric core: compare the fault run's response at the **actual** EA with the
matched control run's response at the **golden** EA for the same `dyn_inst_seq`; `DataDelta
= popcount(R XOR F)`.

**Result: the reference value R is not recorded in any of the 14 runs. DataDelta is
NOT_OBSERVABLE for every context, including both matched-control contexts (R01/C01 seq 5,
R02/C02 seq 48).**

Root cause (verified in the artifacts and source): the tracer records
`memory_request`/`memory_response` only for addresses in the fault addr registry, and the
registry is populated only by `registerInjection` at an injection site
(`CHAOSPropagation.cc:339-349`). A zero-injection control (`--probability 0.0`) registers
nothing — the C01/C02 traces contain **zero** memory nodes of any kind. Likewise, no fault
run ever reads a golden EA with a recorded response: the only registered address is the
actual EA, and the golden EAs (`0x7ffffefda8`, `0x7ffffefdb8`, bit 3 = 1) are never the
actual EA of any registered load (A03's stuck-at-0 clears bit 3; ALREADY_STUCK loads are
not registered; pre-activation loads are not registered).

**Consumer-hash match (the other half of the acceptance) is met in 4/5 fault contexts** —
`a01_consumed.input_hash == register_writeback.writeback_value_fnv`, both real hashes,
with the consumer committed (standard §3 data rule):

| run | writeback fnv (= resp data fnv) | a01_consumed input_hash | consumer seq | consumer_commit |
|---|---|---|---|---|
| R01 | `f971edcd05e4ccc2` | `f971edcd05e4ccc2` | 25 | yes (×12 on-chain) |
| R02 | `a8c7f832281a39c5` | `a8c7f832281a39c5` | 50 | yes |
| R04 | `1505defdf2164c5b` | `1505defdf2164c5b` | 250 | yes (250, 251) |
| R05 | `987468c2d70edbd5` | `987468c2d70edbd5` | 254 | yes |
| R03 | — | — | — | — |

**Cross-run memory-determinism corroboration (explicitly labeled: a cross-run observation,
NOT on-chain evidence, and NOT used for any verdict).** Load-address faults never write
memory, so the content of any address at a given program position is run-invariant:
- address `0x7ffffefda0` read by dyn seq 48 (attempt 1) delivered `0000000000000000` /
  `data_fnv=a8c7f832281a39c5` in **both** SUPP-A01-R02 and SUPP-A03-R02;
- address `0x7ffffefdb0` read by dyn seq 253 delivered `1000000000000000` /
  `data_fnv=987468c2d70edbd5` in **both** SUPP-A01-R05 and SUPP-A03-R03/R04/R05.
This validates determinism, but no run ever records the value at the golden EAs
(`0x7ffffefda8` / `0x7ffffefdb8`), so the plan's DataDelta leg cannot be evaluated.
The brief's acceptance ("at least two contexts with a non-zero DataDelta AND a consumer
edge") is therefore **not met on the DataDelta leg** — honestly recorded as
`no_reference_response` (the v3.2.11 gap named in standard §6 rule 5) — and met on the
consumer-edge leg in 4 contexts.

**Minimal remedy (owner: main agent).** Make the golden-EA response observable, read-only:
either (a) register the golden range `[old_addr, old_addr+size)` as an
observation/reference-only registry entry at injection time (registerInjection already
receives `old_addr`/`old_size`), so the *fault* run records the golden-EA request/response
of the same dyn seq when it exists; or (b) a control-mode registration flag so the matched
control registers the same dyn-seq golden range with `--probability 0.0` and its response
nodes are recorded. Then `DataDelta = popcount(R XOR F)` is computed from two recorded
responses. No data-path change; no verdict is hand-adjusted in the meantime.

## 5. Crash attribution — R01 (plan §4 Step 3)

The abort is **not attributable** per standard §1.6/§6 rule 5: the panic VA is `0`
(`stderr.log`: `Page table fault when accessing virtual address 0`, from
`Commit::commitHead → GenericPageTableFault`, abort tick 3829980), while the injected
actual EA is `0x7ffffefd98` → not `DIRECT_ADDRESS_MATCH`. The `a01_fault` fault-VA
completion (plan §1C3) did not fire because the fault surfaced at commit, not at the
load's own read. `CONSUMER_DERIVED` cannot be argued either: the 12 on-chain committed
consumers prove the corrupted value (`0x7ffffeff02`) propagated, but the aborting
instruction is not identified on the chain (the `simulator_abort` node carries no
dyn_inst_seq/ptag) and the fault VA `0` is not shown to be computed from the corrupted
value on-chain. That is `TEMPORAL_ASSOCIATION_ONLY` in the plan's terms; the v3.2.11
finding ("A01 v3.2.2 R01 panicked on VA 0 ... not attributable") is reproduced with richer
on-chain consumer evidence (12 committed consumers vs none recorded before). The closure
tool correspondingly grades `FaultCausality=UNPROVEN` for the CRASH, and the record
additionally lands `UNRESOLVED` via rule 1 because the aborted run's gz stream is cut
(`RecordIntegrity=TRUNCATED`, `simulator_abort` detail `gzip truncation observed`).

## 6. Closure-tool verdicts (the eight standard fields, deterministic output)

| Pilot | RecordIntegrity | TraceCompleteness | StructuralChain | Coverage | Causality | Terminal | Oracle | FinalClassification |
|---|---|---|---|---|---|---|---|---|
| R01 | TRUNCATED | COMPLETE | PARTIAL | LIFECYCLE_ONLY | UNPROVEN | CRASH | MISSING | UNRESOLVED |
| R02 | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | PROVEN | MASKED | PASS | LIFECYCLE_ONLY |
| R03 | VALID | COMPLETE | COMPLETE | NONE | PARTIAL | UNRESOLVED | PASS | UNRESOLVED |
| R04 | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | PROVEN | MASKED | PASS | LIFECYCLE_ONLY |
| R05 | VALID | COMPLETE | COMPLETE | LIFECYCLE_ONLY | PROVEN | MASKED | PASS | LIFECYCLE_ONLY |
| C01 | VALID | COMPLETE | NONE | NOT_APPLICABLE | UNPROVEN | NO_INJECTION | PASS | UNRESOLVED |
| C02 | VALID | COMPLETE | NONE | NOT_APPLICABLE | UNPROVEN | NO_INJECTION | PASS | UNRESOLVED |

Classification trace (standard §6 order), as computed: R01 → rule 1 (TRUNCATED);
R02/R04/R05 → rule 4 (coverage LIFECYCLE_ONLY, structurally complete chain, MASKED
terminal, oracle PASS); R03 → rule 1 (terminal UNRESOLVED); controls → rule 1
(NO_INJECTION by design — replication, never an independent sample).

Honesty notes on the tool's output:

- **`Coverage=LIFECYCLE_ONLY` for R02/R04/R05** is the frozen mapping of the platform's
  `fault_effect_coverage` (the delivered payload has no recorded reference, so no *value*
  divergence is verifiable; the address divergence IS recorded — `a01_ea.affected=1` —
  and the corrupted value reached committed consumers through verified writeback→consumer
  hashes). Per the standard's own §3/T4 the model-specific divergence record is mandatory
  evidence; the generic classifier does not consult `a01_ea`, and this audit does not
  hand-override the tool — if the researcher wants the A01 address divergence to count as
  the §1.4 divergence, that is a standard revision (§10-style), not an audit decision.
- **R01's raw oracle** grades MISSING at the artifact level (`ORACLE_FAIL: no checksum
  line` does not parse as expected/got; `OracleStatus=malformed` → `ORACLE_MALFORMED` in
  MissingEvidence) — an honest artifact-level statement, not a relabel of the recorded
  crash outcome.
- The **model-level** picture under standard §4: **zero complete chains** (no pilot
  verified a *value* divergence reaching commit), so A01 grades no complete verdict at
  all this round; the best-evidenced pilots are the three full-structural-chain MASKED
  contexts (R02/R04/R05).

## 7. Missing evidence (tool output, per pilot)

- R01: `ORACLE_MALFORMED` (raw oracle has no checksum line — crash artifact), crash not
  attributable (panic VA 0 ≠ actual EA), `RecordIntegrity=TRUNCATED` (abort-cut stream).
- R02/R04/R05: `none` at the tool level; the audit-level gap is the unobservable golden-EA
  reference value (§4) — named `no_reference_response` for any future PARTIAL reasoning.
- R03: `NO_REGISTER_WRITEBACK_EVENT;NO_CONSUMER_EDGE;TERMINAL_UNRESOLVED` (root cause §3).
- C01/C02: `NO_INJECTION_EVENT;TERMINAL_UNRESOLVED` — by design (controls), never gaps.

## 8. What changed vs v3.2.11 (A01)

1. The golden/actual EA coordinates are now recorded (`a01_ea` nodes) — the v3.2.11
   "wrong EA" evidence is now a structured, abort-survivable, chain-joined record.
2. The consumer edge is now recorded and hash-verified per context (`a01_consumed`
   input_hash == writeback fnv, 4/5 contexts) — v3.2.11 had `input_fnv=None` consumers.
3. Raw `oracle.log` files exist for all 7 runs (v3.2.11: all v3.2.1 A01 raw oracles
   missing; T3 closes that gap for the SUPP contexts).
4. The v3.2.11 named gaps that remain open: the **reference value at the correct EA**
   (still unobservable — §4) and the **attributable crash** (R01's panic VA still ≠ EA).
5. New this round: the R03 replay-discard case (§3) — a *newly characterized* honest
   UNRESOLVED with a precise, minimal remedy.

---

**Verdict files:** `audit_v3_2_12/A01_verdict_v3.2.12.json` (7 records, tool-written),
`audit_v3_2_12/A01_A03_Run_Records_v3.2.12.csv` (per-run evidence table).
