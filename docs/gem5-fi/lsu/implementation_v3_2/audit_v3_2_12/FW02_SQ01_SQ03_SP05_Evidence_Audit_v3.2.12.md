# FW02 / SQ01 / SQ03 / SP05 evidence audit — LSU v3.2.12 supplementary pilots

**Round:** LSU v3.2.12 propagation closure (Tasks 9 / 11 / 12 / 13)
**Auditor worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` (HEAD `f15fe483`)
**Date:** 2026-11-10. Read-only audit of pilots/source; only audit outputs written.
No gem5/scons invocation, no commit, no relabeling of any pilot artifact.

**Inputs audited:** 24 run directories under
`docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/` (SUPP-FW02/SQ01/SQ03/SP05
R01–R05 + C01), each `command.txt` / `manifest.json` / `pilot_meta.json` /
`lsq_fwd_injections.log` / `oracle.log` / `stdout.log` / `stderr.log` /
`trace_v31.jsonl` / `prop_trace.csv.gz` / `stats.txt`; the frozen standard
`LSU_Propagation_Acceptance_Standard_v3.2.12.md`; `RUNBOOK_v3.2.12.md`;
source `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/{CHAOSLSQFwd.cc,hh,fw02_rules.hh,
sq01_rules.hh,sq03_rules.hh,sp05_rules.hh}`, `lsq_unit.cc`,
`chaos_lsu_trigger.hh`, `CHAOSPropagation.cc`, `platform/run_pilot.py`,
`platform/run_roles.py`, `platform/terminal_rules.py`, `tools/lsu_12model_closure.py`;
workload sources `workloads/sq_reload_v3212.c` and `workloads/sq_forward.c` plus
their ELF symbol tables.

**Identity verification (all 24 runs):**

- Uniform binary SHA `720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070`
  in every manifest, equal to the on-disk `build/ARM/gem5.opt` and
  `logs_v3_2_12/binary_v3212_trace.sha256`; the closure tool's purity check raised
  no `BINARY_SHA_MISMATCH` on any of the 24 records.
- Workload SHAs match the frozen values: `sq_forward` =
  `132a84f7f21be052bc1f2c9baf1c12d5bd3462aae03b1d42778c94e69b0af297` (FW02 family),
  `sq_reload_v3212` =
  `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` (SQ01/SQ03/SP05).
- Seeds/ordinals match the RUNBOOK §1 original-identity table for all 24 runs
  (checked against `pilot_meta.json.seed` and `excel_identity.event_ordinal_used`).
- Oracles: FW02 family expected `1f4cbf14327717df` (workload `.golden`), SQ-family
  expected `7df5034c23f3e703` (`sq_reload_v3212.golden`).

**Per-run records:** `FW02_SQ01_SQ03_SP05_Run_Records_v3.2.12.csv` (24 rows).
**Verdict JSONs:** `{FW02,SQ01,SQ03,SP05}_verdict_v3.2.12.json` produced by
`python3 tools/lsu_12model_closure.py record` (per model, six `--pilot-dir`s,
`--binary-sha 720eb780…`; all four invocations exited 0).

---

## 1. FW02 (Task 9) — sq_forward, contexts R01–R05 + control

Mechanism: `f6_fw02` suppresses one store→load forwarding match
(`maybeSuppressForwarding`, `CHAOSLSQFwd.cc:1019-1071`, called at
`lsq_unit.cc:1787`); the load then takes the memory path
(`fw02_decision … memory_path=1`). One injection per fault run
(`CHAOS_FW02_SUMMARY: observed=6 suppressed=1` in R01/R03/R04/R05; R02 died before
the exit callback printed its summary, its injection line is present).

| run | inj site (tick, load/store seq, vaddr) | memory path | writeback | commit / consumer | terminal | oracle | tool verdict |
|---|---|---|---|---|---|---|---|
| R01 | t556325, L397/S383, 0x7ffffefc28 (stack) | yes (e194, data_fnv a8c7f832281a39c5) | yes (e195) | none — target squashed | SQUASHED / TARGET_SQUASHED_NO_COMMIT | PASS | PARTIAL (NO_CONSUMER_EDGE;NO_COMMIT_EVENT) |
| R02 | t8639015, L6048/S6042, 0x496798 (bss) | yes | yes | commit chain present, then `panic: Page table fault when accessing virtual address 0x409c80` (`faults.cc:103`) — no address match to the injected 0x496798 | CRASH | FAIL (`no checksum line`) | UNRESOLVED (ORACLE_MALFORMED; VerifiedChainCount=1) |
| R03 | t12774685, L10011/S10008, 0x48fb70 | yes (e4155 @12775455, data_fnv a8c7f832281a39c5, data_hex 0000000000000000) | yes (e4156, hash-equal) | commit e4160 + errant_commit e4161 @12776225 (commit_seq 4720); consumer_commit e4164 @12776610 + e4165 @12777380, consumer_input_fnv a8c7f832281a39c5 == source hash | MASKED / TARGET_COMMITTED_DATA_VALUE_PRESENT | PASS | **VERIFIED_SINGLE_CONTEXT** (43-event chain) |
| R04 | t13002990, L11101/S11099, 0x48fb70 | yes | yes | commit/consumer_commit/errant_commit (11-event chain) | MASKED / TARGET_COMMITTED_DATA_VALUE_PRESENT | PASS | **VERIFIED_SINGLE_CONTEXT** |
| R05 | t13260555, L11203/S11192, 0x7ffffefcd0 (stack) | yes (e4707, data_fnv 9620ace31099cd5d) | yes (e4708) | none — target squashed | SQUASHED / TARGET_SQUASHED_NO_COMMIT | PASS | PARTIAL (NO_CONSUMER_EDGE;NO_COMMIT_EVENT) |
| C01 | misfire — identical to R01 (see §1.1) | yes | yes | none | SQUASHED | PASS (checksum unchanged) | PARTIAL (control_valid=false, control_misfire=true, accepted=false; run_pilot exit 1) |

Task-9 brief acceptance: **≥2 contexts with `decision=suppressed, memory_path=1` and
a consumer edge — met by R03 and R04** (2 of 5; R02 additionally carries a full
commit chain but its verdict stays UNRESOLVED because the crash aborted the
checksum). Every suppression carries a recorded decision
(`control_divergence: fw02_decision e*/forwarding_decision e* → "suppressed"`), and
the two fault-caused squashes classify SQUASHED/PARTIAL — never upgraded.

Terminal drift check (RUNBOOK §4): predicted R01 SQUASHED, R02 CRASH, R03 MASKED,
R04 MASKED, R05 SQUASHED — **all five observed terminals match**; no drift to
investigate. Coverage strengthened vs the v3.2.11 adjudication (which had R04 as
the only COMPLETE_CAUSAL_CHAIN): the v3.2.12 consumer-binding trace now verifies
R03's chain end-to-end too. Per the standard §4 single-context rule, R03+R04
(2 verified chains) would allow COMPLETE_CAUSAL_CHAIN at model level; the frozen
closure tool grades per-run, and the model-level rollup is Task 16's matrix — this
audit does not pre-empt it.

### 1.1 SUPP-FW02-C01 control misfire (root cause summary)

`--probability 0.0` was passed and recorded (manifest `command`), but the F6_fw02
injector is **ordinal-gated by design and never consults probability**:

- attach condition includes `struct_mode == StructMode::F6Fw02` as an alternative to
  `probability > 0.0f` (`CHAOSLSQFwd.cc:81-87`), with the explicit FW02 block
  "attach even with probability==0" (`:134-138`);
- `maybeSuppressForwarding` gates only on mode / `f6_fired` / `f6_event_ordinal` /
  `max_faults` (`:1023-1028`) — no probability check exists in the function;
- platform gap: `run_pilot.py` FW02 always mounts the injector (the `else` arm,
  `run_pilot.py:617-620`), unlike the LQ04 branch which omits it for controls
  because "the LQ04 selector is ordinal-gated … a mounted injector would still
  fire" (`run_pilot.py:612-616`).

The misfire fired byte-identically to R01 (t556325, L397/S383, 0x7ffffefc28) — the
control and the fault run are the same event stream at probability 0. This was the
RUNBOOK §7n *predicted* outcome; `run_roles.py` correctly rejected it
(role-exclusive acceptance). Full details and the corrected control command:
**`FW02_CONTROL_FIX_v3.2.12.md`** (same directory). The original misfire artifacts
are preserved untouched.

---

## 2. SQ01 / SQ03 / SP05 (Tasks 11/12/13) — workload override `sq_reload_v3212`

All 15 fault runs share one honest terminal pattern: injection TRIGGERED, workload
oracle PASS, `LIFECYCLE_ONLY` classification,
`terminal_reason=STORE_COMMITTED_LANE_NOT_READ`. All three controls are valid
(injection_count=0, control_valid=true, accepted=true). The central question the
brief asked: **is the ordinal-selected store one that the sq_reload workload later
reads?**

### 2.1 The finding: ordinals 1–5 select C-runtime startup stores, not workload lanes

The workload's detection surface is `static volatile uint64_t buf[256]`
(`sq_reload_v3212.c:25`), linked at **`buf = 0x491990`, size 0x800**
(`readelf -sW sq_reload_v3212`: `56: 0000000000491990 2048 OBJECT LOCAL DEFAULT 20 buf`)
— i.e. the workload stores/reloads live in `[0x491990, 0x492190)` (and every store
`buf[i]=v` is followed by the same-address reload `buf[i]` after `dmb ish`,
`sq_reload_v3212.c:41-52`, so any faulted store inside that range has a guaranteed
reload consumer by construction).

The ordinal-selected stores in all 15 fault runs are at
**`0x7ffffefd00, 0x7ffffefd08, 0x7ffffefd10, 0x7ffffefd18, 0x7ffffefd20`**
(store_seq 18/19/23/24/28, sq_idx 1–5, gens 1–5 — SQ01's `sq01_chain` records;
SQ03/SP05 select the same first five stores by their own eligible streams). These
are **stack-region addresses, not `buf`**: the same 0x7ffffefXXX region hosts
sq_forward's known stack locals (its `put_hex` `char buf[16]` pair appears at
0x7ffffefc28 in FW02-R01), and their byte0 values (0x00/0x30/0x00/0x00/0x00 —
SQ01's `data_before`) do not match the workload's stored pattern
(`v = 0x73715f72656c6f61 + i*0x0101…`, byte0 = 0x61+i). They are the static binary's
C-runtime startup stores (first stores of the stream), written before `main`'s
loop and **never read again by the workload**.

Consequently `reload_seq=0` in every SQ01/SQ03/SP05 detail record, and the
`STORE_COMMITTED_LANE_NOT_READ` verdict is **structural, not incidental**: with the
original ordinals (1–5 from the old workloads' Excel contexts) the ordinal-selected
store is always a startup store on the new workload's event stream. No consumer
edge can exist. The records stay honestly LIFECYCLE_ONLY/PARTIAL — nothing was
upgraded, and no consumer was manufactured.

Per-model detail-record evidence (all from `trace_v31.jsonl`):

- **SQ01** `sq01_chain` (e8016 @ t28334845, injection e7/e8): byte0 bit3 flip,
  `data_diverged=1`, store drained (`mem_write_hash` = a09e307a7f948acd for the
  0x00→0x08 lanes, eb69cdf06937695b for R02's 0x30→0x38), `reload_seq=0`,
  `consumer_seq=0`, `chain_verdict=STORE_COMMITTED_LANE_NOT_READ`
  (rule: `sq01_rules.hh:81-84` — drained but never reloaded).
- **SQ03** `sq03_effect`: canWB 0→1 (R01 @ Cycle 366 `executeStore_canWB`,
  eligible_ordinal=1), `canwb_state_changed=1`, writeback/commit/drain ticks
  present (R01: wb 140910, commit 149380, drain 200970), `reload_seq=0`,
  `effect_outcome=LIFECYCLE_ONLY`, `effect_reason=NO_DOWNSTREAM_EFFECT` — a field
  change with no downstream visibility difference, exactly the v3.2.9 probe's
  prediction. Note the SQ03-set canWB made the store drain *later* visible anyway
  (drain ticks equal across contexts); no early-visibility effect was possible on
  these startup stores.
- **SP05** `sp05_stage`: select @ Cycle 389 (`commitStores_select`,
  eligible_ordinal=1) + premature completion @ Cycle 390
  (`writebackStores_prematureComplete`, `mem_sent=0`);
  `completion_tick=writeback_tick=150150` (R05: 150535), `drain_tick=0`,
  `commit_tick=0`, `write_skipped=1` (rule `sp05_rules.hh:160-164`: completed
  without a drain — the write is lost), `reload_seq=0`,
  `stage_outcome=NO_RELOAD_OBSERVED`, `masking_mechanism=NOT_APPLICABLE`.
  `store_data_fnv=null` is an honestly-recorded unwired field
  (`CHAOSPropagation.cc:2561-2563`: "stays null until the shared-file request …
  is wired"); the verdict does not depend on it (`stageVerdict` returns
  NO_RELOAD_OBSERVED whenever `reload_seq==0`, `sp05_rules.hh:98-99`).
  The pilot_meta terminal is MASKED/`STORE_COMMITTED_LANE_NOT_READ` because SP05's
  store is committed-by-construction
  (`terminal_rules.py:52-59`) and no `consumer_commit` was observed; the
  `commit_tick=0` in the stage record is the honest "commit trace node not bound"
  value (`sp05_rules.hh:87`), not a claim that the store never committed.

### 2.2 Ordinal re-selection requirement (the brief's question 3, answered)

**Yes — the original ordinals target startup stores on the new workload. The
ordinals for SQ01/SQ03/SP05 must be re-selected by an eligibility preflight on
`sq_reload_v3212` before any propagation claim can be attempted.** The v3.2.12
runs are correct preserved-context reproductions (same Excel row → Nth eligible
event of the NEW stream, RUNBOOK §11.10), but for the closure question "does the
faulted store lane get re-read" the ordinal must land on a store the workload
actually reloads. Re-selection rules:

- **Predetermined, never outcome-driven:** the selection criterion is *address
  eligibility only* — the Nth eligible event's vaddr must lie in the workload's
  reload-consumed range `[buf, buf+0x800)` = `[0x491990, 0x492190)`. It must never
  be re-rolled based on SDC/MASKED outcomes of the fault runs; if a re-selected
  ordinal still yields no consumer, the run records LIFECYCLE_ONLY honestly.

**Exact preflight method** (uses only the frozen binary and existing flags; no
source change; each probe is a ~2 s run):

1. **Freeze the eligibility range from the workload ELF** (predetermined): the
   reload-consumed set is exactly `[0x491990, 0x492190)` — `buf` at 0x491990 size
   0x800 (`readelf -sW`), and `sq_reload_v3212.c:41-52` reloads every stored lane.
2. **Census probes with the model's own ordinal machinery.** Because the F0-tier
   trigger with `event_ordinal` set computes `next_fire = warmup_events +
   event_ordinal` (`chaos_lsu_trigger.hh:167-179`), `--lsqfwd_span_events` is inert
   when an ordinal is passed — any ordinal is reachable; the ordinal counts the
   model's *own* eligible stream:
   - SQ01: every store data-write passing the `lsq_unit.cc:2120-2122` guard
     (non-CACHE_BLOCK_ZERO / non-cache-maintenance / non-atomic), ordinal via
     `lsuTrigger` (`CHAOSLSQFwd.cc:941-947`);
   - SQ03: every store reaching `maybeSetCanWB`, ordinal via
     `eligible_count == f6_event_ordinal` (`CHAOSLSQFwd.cc:740-745`);
   - SP05: every `commitStores` store passing `chaos_sp05::isSelectable`
     (size>0, non-prefetch), ordinal via
     `chaos_sp05::shouldSelect(eligible_count, ordinal)`
     (`CHAOSLSQFwd.cc:540-546`).
   Run one probe per candidate ordinal K (direct `gem5.opt … lsu_proxy.py` with the
   model's mount flags, `--lsqfwd_event_ordinal K` / `--sp05_event_ordinal K`,
   `--max_faults 1`, scratch outdir, e.g. `PREFLIGHT-SQ01-K6`) and read the
   selected store's address **before any classification exists**:
   SQ01 → `pilot_meta.json:classification.terminal_evidence.last_injection_new_value`
   or the `sq01_chain` record's `new_value`/log vaddr; SQ03/SP05 → the model's
   select log line (`lsq_fwd_injections.log` gives `store_seq`; bind the address by
   the same probe's injection `new_value` in pilot_meta). The addresses of
   ordinals 1–5 are already known (0x7ffffefd00…20 — startup), so probe K = 6, 7, …
   (or binary-search between 5 and the total store count; the SQ01-C01 trace shows
   1509 stores total) until `vaddr(K) ∈ [0x491990, 0x492190)`. The first such K is
   `K*`; the addresses are monotone in program order, so the search terminates.
3. **Fix the new ordinals before the fault runs:** R01..R05 map to `K*+0 … K*+4`
   (five consecutive loop stores, each guaranteed a same-address reload), seeds
   carried unchanged, oracle still `sq_reload_v3212.golden`
   (`7df5034c23f3e703`). Record the preflight probes and the K→vaddr census table
   in the round evidence so the selection is auditable and demonstrably
   address-based.
4. **Probe-run hygiene:** preflight outdirs are census artifacts, never samples;
   they are not graded, not re-run for outcome, and their oracles are ignored.

---

## 3. Closure-tool verdict classes (per `tools/lsu_12model_closure.py record`)

| model | R01 | R02 | R03 | R04 | R05 | C01 |
|---|---|---|---|---|---|---|
| FW02 | PARTIAL | UNRESOLVED (ORACLE_MALFORMED) | VERIFIED_SINGLE_CONTEXT | VERIFIED_SINGLE_CONTEXT | PARTIAL | PARTIAL (control misfire, fault-path graded) |
| SQ01 | LIFECYCLE_ONLY | LIFECYCLE_ONLY | LIFECYCLE_ONLY | LIFECYCLE_ONLY | LIFECYCLE_ONLY | UNRESOLVED (valid control, NO_INJECTION) |
| SQ03 | LIFECYCLE_ONLY | LIFECYCLE_ONLY | LIFECYCLE_ONLY | LIFECYCLE_ONLY | LIFECYCLE_ONLY | UNRESOLVED (valid control, NO_INJECTION) |
| SP05 | LIFECYCLE_ONLY | LIFECYCLE_ONLY | LIFECYCLE_ONLY | LIFECYCLE_ONLY | LIFECYCLE_ONLY | UNRESOLVED (valid control, NO_INJECTION) |

All 24 records: `RecordIntegrity=VALID`, `TraceCompleteness=COMPLETE`,
`validator_errors=[]`, `truncated=false`, uniform binary SHA (no purity flags).
Per-model summary:

- **FW02:** 2/5 fault contexts reach a verified complete causal chain
  (VERIFIED_SINGLE_CONTEXT each; FaultCausality=PROVEN), 2/5 are honest
  fault-caused squashes (PARTIAL), 1/5 crashed after a downstream commit chain
  (UNRESOLVED — the crash aborted the checksum; the tool refuses a verdict over an
  absent oracle artifact). The control is an expected, preserved misfire.
- **SQ01 / SQ03 / SP05:** 5/5 LIFECYCLE_ONLY — the injection triggered and the
  structural path executed, but no reload consumer edge exists because the
  ordinal-selected stores are startup lanes the workload never reads (§2.1).
  3/3 controls valid. Per the standard §5 ("internal-only change →
  LIFECYCLE_ONLY"; "a field change alone is never propagation") these are the
  honest ceilings **for these ordinals**; a propagation-capable rerun requires the
  §2.2 preflight re-selection.

## 4. Honesty notes and concerns

1. **No conclusion was upgraded on inference.** SQ01/SQ03/SP05 stay LIFECYCLE_ONLY
   with the missing links named (`NO_REGISTER_WRITEBACK_EVENT;NO_CONSUMER_EDGE`,
   plus `NO_EARLY_ANOMALY_EVENT;NO_COMMIT_EVENT` for SP05); FW02 squashes stay
   PARTIAL; the crashed R02 stays UNRESOLVED.
2. **FW02-C01 is evidence, not garbage:** it proves FW02 is ordinal-gated (the
   misfire is byte-identical to R01 at probability 0). Preserve it; run the
   corrected no-injector reference (`FW02_CONTROL_FIX_v3.2.12.md` §3) only if the
   audit needs the no-fault memory reference on sq_forward.
3. **Runner gap worth a follow-up patch (main agent's call, one unit):**
   `run_pilot.py` needs the LQ04-style control guard for FW02
   (`--model FW02` + `probability==0.0` → `extra = []`, mirroring `:612-616`) so
   future FW02 controls are role-recorded instead of structurally misfiring. DA04
   (`da04_be_bit0`) sits in the same probability-independent attach list
   (`CHAOSLSQFwd.cc:82`) and deserves the same audit when its controls are next run.
4. **SP05 `store_data_fnv` is honestly null** (wiring not implemented,
   `CHAOSPropagation.cc:2561-2563`); no verdict in this round depended on it.
   The 2026-11-10 runs are consistent with that.
5. **FW02 R02's `CHAOS_FW02_SUMMARY` line is absent** because the process died at
   the page-table panic before the exit callback; the per-injection log line and
   the 15-event commit chain are present, so the injection itself is proven.
6. **sq_reload ordinal space:** total SQ-alloc stream is 1509 stores (SQ01-C01
   trace census); the preflight in §2.2 is cheap and bounded, but the exact K* was
   deliberately NOT probed in this audit (read-only mandate — probing would have
   executed gem5). The main agent should run the census before any rerun.
7. **Trace honesty of the SP05 commit stage:** `sp05_stage.commit_tick=0` (no
   bound commit node) coexists with the classifier's committed-by-construction
   ruling (`terminal_rules.py:52-59`). Both are recorded; neither was edited.
8. Terminal predictions from the RUNBOOK §4 all matched for FW02 — no drift, so
   nothing to investigate there; the SQ01/SQ03/SP05 terminals differ from their
   originals **by design** (workload change), and the acceptance is the brief's
   chain rule, which they honestly fail at these ordinals.
