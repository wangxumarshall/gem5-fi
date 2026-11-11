# Agent D — Source-Hook & Injection-Semantics Audit (pre-formal v3.3)

**Date:** 2026-11-11 · **Worktree:** `lsu-platform-v3.2.12` · **Mode:** read-only.
**Scope:** the 12 models A01, A03, FW02, FW05, SQ01, SQ03, SP05, DA04, LP01, LQ04, RP01.
No source under `CHAOS/gem5/src` was modified, no gem5 build/run was performed.
Authoritative design: `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`
sheets **3.最终12模型矩阵** and **4.源码Hook审计** (dumped in full for this audit).

**Verdict tally:** CONFORMING 3 (SQ01, SQ03, LP01) · MINOR_RISK 8 (A01, A03,
FW05, DA04, SP05, LQ04, MD04, RP01) · MAJOR_RISK 1 (FW02) · UNIMPLEMENTED 0.
The machine-readable matrix is `LSU_12Model_Source_Hook_Audit.csv`.

Method: every model's mount flags were taken from the actual run commands
(`pilots_v3_2_12/*/command.txt` and `platform/run_pilot.py`), not from the
Excel prose; every hook claim below is a verified `file:line`.

---

## 1. Per-model findings

### A01 (AGU EA single-bit flip, F0) — MINOR_RISK
Hook is the **pushRequest PRE hook**, exactly the Sheet-4 "唯一正式Hook":
`LSQ::pushRequest` calls `cpu->chaosAddrPathPre->maybeCorruptPre(addr, size,
isLoad, ...)` at `lsq.cc:781-786`; the formal mode `a01_bit3_load` XORs
`addr ^= 0x8` at `CHAOSAddrPath.cc:378-384` and stages the golden/actual
record at `442-447`. Eligibility is load-only (op-class filter at
`CHAOSAddrPath.cc:262-271`), and the decision goes through the event-normalized
`ChaOSLsuTrigger` F0 (`CHAOSAddrPath.cc:129-137`; F0 case
`chaos_lsu_trigger.hh:167-181`). The fn is `isLoad`-filtered, single-shot
(`spent` + `maxFaults=1` from `run_pilot.py:551-556`), and mutates only the
by-value `addr` that this `pushRequest` is about to consume — no shared
Request, no other DynInst. The corrupted by-value EA is dropped when the
`savedRequest` reuse branch runs (`lsq.cc:808-819` records
`a01_ea_discarded`), which is honest but still counted as injected (SUPP-A01-R03
PARTIAL). Latent config risk: the older post-hook `Mode::A01Bit`
(`CHAOSAddrPath.cc:161-169`) still samples a random band and has **no**
load filter — it is not used by the formal pilot, but mounting
`--addrpath_mode a01_bit` instead of `--agu_pre_mode a01_bit3_load` would
violate the Sheet-4 requirement. Patch: `patches/A01_control_memory_nodes.diff`.

### A03 (AGU EA stuck-at, F5) — MINOR_RISK
Formal hook: `pre_mode=a03_bit3_stuck0_load` at `CHAOSAddrPath.cc:385-426`,
`addr = addr & ~0x8`, load-only, applied to **every** trigger-fired eligible
load. The F5 trigger arms at `warmup_events + event_ordinal` and fires on
every later eligible event (`chaos_lsu_trigger.hh:158-166`); `maxFaults=0` is
therefore unlimited because the trigger path never consults `max_faults`
(`CHAOSAddrPath.cc:252-280`). This is the Sheet-4/CFG01 **option A**
(per-event re-application, not a physical latch) and the reserved semantics
are implemented: `a03_activation` once, one `a03_stream` per fired load,
`STUCK_APPLIED` vs `ALREADY_STUCK` derived from `golden_ea^actual_ea`
(`a03_stream.hh:62-82,127-144,201-247`), sinks in `lsq.cc:821-838`. Gaps:
(a) `faults_injected_count` also increments on `ALREADY_STUCK` no-ops
(`CHAOSAddrPath.cc:404-426`), so the "injected" counter is not the
`s03 activated`口径 and the audit must subtract `affected=0` rows; (b) the
raised fault VA is not linked to the stream row inside the simulator — the E6
"panic VA == a03_stream.actual_ea" join is done offline by the regrade tool.
Latent config risk: two unused A03-ish paths remain (post-hook
`Mode::A03Stuck0/1` with a random 0-47 bit and no op filter,
`CHAOSAddrPath.cc:181-189`; and the legacy F5 XOR at `190-196`, which is a
**bit flip, not a stuck-at**). Neither is mounted by the formal pilot, but a
wrong `--addrpath_mode/--lsu_tier` combination would silently change the
model. Patch: `patches/A03_crash_addr_link.diff`.

### FW02 (false forwarding miss, F6) — MAJOR_RISK
Hook is the real full-coverage decision: `LSQUnit::read` calls
`cpu->lsqFwd->maybeSuppressForwarding(...)` at `lsq_unit.cc:1786-1807`; on a
true return it `break`s out of the store scan and the load falls through to
the normal memory access (`2052-2091`). `CHAOSLSQFwd::maybeSuppressForwarding`
(`CHAOSLSQFwd.cc:1019-1071`) suppresses exactly one real pair, records
`fw02_decision`/`noteForwarding`, and never mutates bytes. F6 is **hand-rolled**
(`f6_observed/f6_fired/f6_event_ordinal`), not `ChaOSLsuTrigger` — legitimate
because the trigger is a decision, not an event source, but it is a deviation
from the "use the LSU trigger" convention. The real defect is the
**probability contract**: the constructor self-attaches in `F6Fw02` mode even
at `probability==0` (`CHAOSLSQFwd.cc:81-87,134-148`) and
`maybeSuppressForwarding` never reads `probability`. Consequently a mounted
p=0 run still fires. This is confirmed empirically: `SUPP-FW02-C01`
(`--probability 0.0` + full mount) is the single annotated misfire in
`audit_v3_2_12/FINAL_INDEPENDENT_AUDIT_v3.2.12.md` ("SUPP-FW02-C01 is
annotated and visible (SQUASHED/PASS, fired identically to R01)"), while
`SUPP-FW02-C02` (injector omitted) is the clean control. **Answer to the
task question:** yes — the injector-omitted path is currently the only
reliable zero-injection control for FW02. Patch:
`patches/FW02_probability_guard.diff` (guards the decision; R runs use
probability 1.0, so frozen evidence is unaffected).

### FW05 (wrong-source forwarding, F6) — MINOR_RISK
Hook: the full-coverage forward decision at `lsq_unit.cc:1828-1884`;
`CHAOSLSQFwd::maybeSubstituteFW05` (`CHAOSLSQFwd.cc:780-873`) validates the
pair with `chaos_fw05::isEligible` (`fw05_rules.hh:163-191`: alt store older,
different, full-cover, bytes differ, load younger, no multi-store splice) and
`memcpy`s the alt store's bytes into `load_inst->memData`. This matches
CFG01 option A. `corrupt()` is explicitly inert in this mode
(`CHAOSLSQFwd.cc:320-322`), so there is no double injection. Triggering is
hand-rolled probability/`fw05_event_ordinal`, single-shot via `maxFaults=1`;
eligibility correctly rejects partial overlays. The open issue is evidential:
`noteFW05Injection` registers only the injected load
(`CHAOSPropagation.cc:1809-1873`) and `noteChainWriteback` emits taint_reg
from the PRF (`1405-1441`), but nothing binds a later **memory-path reload**
of the affected lane, so the native rows grade LIFECYCLE_ONLY 4/4 and
`ModelRuleRecord=null` (`FINAL_INDEPENDENT_AUDIT_v3.2.12.md`, FW05 blocker 1 /
M6). Patch: `patches/FW05_reload_consumer.diff`.

### SQ01 (SQ data byte0 flip, F0) — CONFORMING
Hook: `LSQUnit::write` after `memcpy` into the SQ entry
(`lsq_unit.cc:2111-2130`); `maybeCorruptStoreData` flips `data[0] ^= 0x08`
(`CHAOSLSQFwd.cc:934-970`). Store-only, data-only (entry/request/pointers
untouched), F0 event trigger one-shot. At `--probability 0` the ctor does
**not** attach to the CPU (Sq01Bit3 is absent from the attach gate at
`CHAOSLSQFwd.cc:81-127`), verified empirically: `SUPP-SQ01-C01` stdout shows
`CHAOS_LSU_TRIGGER: ... attempted=0 eligible=0 injected=0`. No material issue.

### SQ03 (SQ `_canWB` early, F0) — CONFORMING
Hook: `executeStore` (`lsq_unit.cc:884-909`) sets `storeQueue[idx].canWB()=true`
and `++storesToWB` after `maybeSetCanWB` (`CHAOSLSQFwd.cc:728-763`); the
paired increment keeps `writebackStores/completeStore` balanced. Store-only,
excludes SC/atomic, one-shot `sq03_fired`, watchdog aborts non-zero
(`496-512`). The early canWB deliberately defeats the SQ squash guard
("Instructions marked as can WB are already committed", `lsq_unit.cc:1298-
1300`) — that is the modelled effect, not an accident. Trigger is a
hand-rolled ordinal (deviation only). p=0 is safe because `maybeSetCanWB`
returns false at `734-735`.

### SP05 (store completion bookkeeping, F6) — MINOR_RISK
Two hooks: selection at `commitStores` (`lsq_unit.cc:1011-1016`) and
premature completion inside `writebackStores` before the cache send
(`1072-1094`); `maybeCompleteSP05` (`CHAOSLSQFwd.cc:571-603`) fires once for
the entry identity `(sq_idx, gen)`, calls the *real* `completeStore`, and
skips the send — the write is lost (the `sp05_rules.hh` `writeSkipped`
semantic). This matches CFG01 option A ("completion bookkeeping failure") and
keeps `storesToWB` paired. Risks are inherent: deadlock if the write is
required, mitigated by a fatal watchdog (`514-529`); no committed pilot
directories exist yet (MissingEvidenceMatrix: SP05 `PILOT` row). Trigger is
hand-rolled ordinal.

### DA04 (byte-enable bit0, F0) — MINOR_RISK
Hook: after `Request::_byteEnable` construction in `pushRequest`
(`lsq.cc:876-891`); `maybeCorruptStoreByteEnable` (`CHAOSLSQFwd.cc:972-1017`)
clears lane 0 only when `chaos_da04::eligible` (`size==4`, `be.size()==4`,
all true; `da04_byte_enable.hh:774-792`). Store-only, per-Request, address/size/
data untouched; the old const-ref obstacle is gone because the hook mutates
the vector after construction. Latent control hazard: the ctor attaches at
p=0 (`CHAOSLSQFwd.cc:128-133`) and the hook never reads `probability`, so a
future mounted p=0 DA04 control would fire; no DA04 control pilot exists
today, so the 12-model evidence is unaffected. Trigger F0 when mounted.

### LP01 (load response byte0, F0) — CONFORMING
Hook: `LSQUnit::completeDataAccess` before `writeback` (`lsq_unit.cc:208-235`);
`CHAOSL1DForward::maybeCorrupt` (`CHAOSL1DForward.cc:68-129`) applies a
size-bounded `data[0] ^= mask` (`lp01_bytewise.hh:947-957` — the v3.2.4
`uint64_t*` overrun is fixed). Eligibility is a real data-load response
(`hasData && !isWrite && is_load && !isInstFetch`, size>0); the mask is
forced into byte0 (`cc:99-110`); single-shot `maxFaults=1`; p=0 returns at
`73`. The only deviation is that the trigger is a hand-rolled cycle window +
probability rather than `ChaOSLsuTrigger`; semantics match CFG01.

### MD04 (violation-report miss, F6) — MINOR_RISK
Hook: `checkViolations` (`lsq_unit.cc:669-690`) calls
`cpu->chaosMD04->maybeSkipViolation(ld_inst, inst, ...)`; a true return
`break`s before the `M5PanicFault` and `memDepViolator` update, so one real
store→younger-load violation is not reported. Eligibility is strict
(`CHAOSMD04.cc:85-94` + `md04_rules.hh:835-858`: store_size==8, load_size>=8,
real byte overlap, same shifted-range predicate), probability is consulted
(`CHAOSMD04.cc:110-112`), one shot via `maxFaults=1`. Only the report is
suppressed — address/size/data are untouched (log line 136 asserts
`address_modified=0,size_modified=0,data_modified=0`). Hand-rolled trigger;
the intentional consequence is that the stale load may commit.

### LQ04 (LQ entry lifetime, F0) — MINOR_RISK
Hook: end of `executeLoad` (`lsq_unit.cc:804-828`) calls
`e.corruptLifetime()`, moving `_valid=0` / `_request` into the
`_lq04Request/_lq04Corrupt` side channel (`lsq_unit.hh:106-193`). Restore is
at `commitLoad` (`lsq_unit.cc:945-949`) and `squash` (`1237-1238`); the
response is bound by `pkt->senderState`, not the entry (`lsq_unit.cc:100-137`),
so data/response identity survives. Eligibility is valid+request+!squashed+
!executed, non-prefetch, target `(lq_idx,gen)`; one-shot with watchdog; p=0
controls omit the injector (`run_pilot.py:605-613`). Risk is structural: the
entry is deliberately invalid between execute and commit, so every reader of
the LQ must tolerate it; the tolerant paths asserted at `lsq_unit.cc:366` and
`980-981` are the enumerated ones. Literal semantics were accepted by the
researcher 2026-11-08.

### RP01 (partial-forward replay miss, F6) — MINOR_RISK
Hook: the `PartialAddrRangeCoverage` branch of `LSQUnit::read`
(`lsq_unit.cc:1990-2048`); `maybeSkipPartialReplay` (`CHAOSLSQFwd.cc:625-726`)
is consulted immediately before `iewStage->rescheduleMemInst(load_inst)` and
skips exactly that call for the ordinal-selected eligible event, leaving the
stall record, `++replayGeneration` (2012), `clearIssued`, `effAddrValid(false)`,
`request->discard()` and `setRequest(nullptr)` intact. The wake-up audit in
`rp01_rules.hh:208-228` documents why no other path re-issues the load; the
terminal is HANG or SQUASHED and the watchdog aborts non-zero (`605-623`).
The documented gap is causal metadata: both `noteSquash` calls pass only two
arguments (`lsq_unit.cc:1240-1241, 1318-1319`), so `triggering_seq` stays 0
and R02/R03 grade `fault_victim_unproven` / causality PARTIAL. Patch:
`patches/RP01_triggering_seq.diff`.

---

## 2. Four priority models in depth

### RP01 — triggering_seq at the lsq_squash site
`CHAOSPropagation::noteSquash` already accepts and records the boundary
(`CHAOSPropagation.cc:2213-2251`), and `chaos_fw02::classifySquash` implements
the intended rule (`fw02_rules.hh:106-120`): a recorded boundary equal to the
fault seq is `FaultCaused`; a recorded non-fault boundary is `Unrelated`; 0 is
the honest "unproven" state. `LSQUnit::squash(squashed_num)` has the value in
hand at both call sites (`lsq_unit.cc:1203`, calls at 1240 and 1318) but drops
it. Passing it is a two-line record-only change; it cannot alter replay,
squash victims, timing, or the fault decision. This is the highest
value-per-line correction found in this audit.

### A01 — control-mode read-only memory-node registration
Fault runs are conforming; the deficit is that the matched control produces
no reference. At `--probability 0.0`, `maybeCorruptPre` returns at
`CHAOSAddrPath.cc:250` before staging or calling `registerInjection`, so no
`addr_registry` entry exists and `noteMemRequest/noteMemResponse`
(`CHAOSPropagation.cc:700-780, 863-1231`) emit nothing for the control load.
The A01 golden-reference nodes (`a01_golden_req/resp`,
`CHAOSPropagation.cc:1003-1076`) only fire when `a01_registry` holds the seq
*and* `xor_delta != 0`, which a control by definition never has. The proposed
patch adds (i) `ChaOSLsuTrigger::onControlProbe()` that advances the eligible
space with the fault run's exact F0 ordinal selection but counts no injection,
(ii) `CHAOSAddrPath::probeA01Control`, entered only at p=0 for
`a01_bit3_load`, which stages a no-op EA record, and (iii)
`CHAOSPropagation::registerControlProbe`, which emits `probe` + `a01_ea`
(golden==actual, affected=0) and a `control_only` addr entry so the normal
request/response nodes appear, while `pending_chain_wb` is skipped
(`hit_control`) to avoid taint. Control execution is byte-identical.

### A03 — persistent semantics and the crash-address link
The persistent/activation semantics are already correct: F5 arms once
(`chaos_lsu_trigger.hh:158-166`), every later eligible load is re-applied
(`CHAOSAddrPath.cc:385-426`), activation/stream rows are recorded exactly once
(`a03_stream.hh:201-247`), and the no-change case is an explicit
`ALREADY_STUCK` row rather than a silent miss. Two honest deficits remain:
the injected counter includes no-ops, and the crash VA is joined only offline.
The proposed patch adds `noteA03FaultVA`, called at the existing A01
fault-VA site (`lsq.cc:928-933`), which emits `a03_fault`
{fault_va, golden_ea, actual_ea, bit, event_ordinal,
crash_addr_matches=(fault_va==actual_ea)} on the same ptag as the last
`a03_stream` row. Limitation: `ArmISA::getFaultVAddr` covers Arm AbortFault;
a raw gem5 panic bypasses the site and still needs the offline join.

### FW05 — reload consumer on the exact store lane
`FW05Entry` (`CHAOSPropagation.hh:589-603`) keeps the true/alt store identities
and hashes but has no reload field. A forwarded load has no memory response,
so the trace stops at the PRF writeback (`CHAOSPropagation.cc:1401-1441`) and
never shows what memory holds for the lane. The patch adds `reload_seq` /
`reload_hash` to `FW05Entry` and, in `noteMemResponse` before the no-hit
return (`CHAOSPropagation.cc:1077`), binds the first **later** load that (a)
covers `[load_addr, load_addr+load_size)` and (b) actually received a memory
response, emitting `fw05_reload` with `reads_true_store` / `reads_alt_store`
booleans. It is observation-only: the reload is never added to `fault_seqs`,
taint or any registry, and the injected load's rows are unchanged. This gives
the classifier the true-vs-alt memory bytes that the native row lacks, without
a new binary key.

### FW02 — zero-injection control (verified)
See §1 FW02. The defect is localized to the missing probability test in
`maybeSuppressForwarding`; the attach-at-p=0 in the ctor is intentional for
observation but the decision ignores the knob. The project's current
workaround (`run_pilot.py:618-641` omits the injector when `--probability 0.0`)
is correct and is what produced the clean `SUPP-FW02-C02`; it is the only
reliable zero control until `patches/FW02_probability_guard.diff` lands.

---

## 3. Cross-cutting findings

1. **Trigger-mode split.** Only A01/A03 (and SQ01/DA04 when mounted) route
   through `chaos_lsu_trigger.hh`; FW02/FW05/MD04/SQ03/SP05/LP01/RP01/LQ04
   hand-roll their own ordinal/probability selectors. This is defensible for
   decision-point models but means the F0–F6 semantics are not uniformly
   enforced; the CSV records `TriggerMode` per model.
2. **p=0 controls are not uniform.** A01/A03/LP01/MD04/FW05/SQ03/SP05/LQ04
   are clean at p=0 (early return, probability test, non-attach, or
   injector omission). FW02 (verified misfire), DA04 (latent) and RP01
   (latent, non-probability-gated) are not. Controls for those models must
   omit the injector or use the model's count-only mode.
3. **One-shot discipline is sound.** Every model has a fired flag, an
   identity key, or `maxFaults=1` plus asserts; no duplicate-injection path
   was found. A03's repeated application is the model, not a duplicate.
4. **Global-state edits are limited and paired.** SQ03/SP05 touch
   `storesToWB` but pair the change with the real `completeStore`; LQ04 edits
   LQEntry state via an explicit side channel; nothing else writes CPU state.
5. **Evidence gaps are mostly observational, not semantic.** RP01
   triggering_seq, A01 control reference, A03 crash VA and FW05 reload
   consumer are record-only gaps; only FW02's probability refusal is a
   control-semantics defect.

---

## 4. Prioritized patch list (proposals only, nothing applied)

| # | Model | File(s) | Change | Risk if not fixed |
|---|---|---|---|---|
| P1 | RP01 | `lsq_unit.cc:1240-1241, 1318-1319` | pass `squashed_num` as `noteSquash`'s `triggering_seq` | R02/R03 stay causality PARTIAL |
| P2 | A03 | `CHAOSPropagation.{hh,cc}`, `lsq.cc:928-933` | add `noteA03FaultVA` + `a03_fault` node | crash-address join remains offline |
| P3 | FW05 | `CHAOSPropagation.hh:589-603`, `.cc:1077` | add reload fields + `fw05_reload` binding | native edge stays LIFECYCLE_ONLY |
| P4 | A01 | `chaos_lsu_trigger.hh`, `CHAOSAddrPath.{hh,cc}:250`, `CHAOSPropagation.{hh,cc}` | control-only probe registration | control run has no DataDelta reference |
| P5 | FW02 | `CHAOSLSQFwd.cc:1019-1071` | consult `probability` before suppressing | p=0 mounted run keeps misfiring |

No patch changes SampleRunIDs, seeds, event ordinals or fault semantics. All
five pass `git apply --check` against this worktree (nothing was applied);
they are UNVERIFIED beyond applicability (no build/run was permitted). The
per-patch build-and-evidence validation commands are in
`patches/README.md` §"Validation commands after apply".

## 5. Limitations

- No compilation or execution was performed; claims are source + raw-artifact
  based, and the patch diffs are untested.
- The Excel "3.最终12模型矩阵" still shows pre-v3.2.12 statuses for several
  models (e.g. SQ01/SQ03/SP05/RP01 "NEEDS_HOOK"); this audit judges the
  **code as it exists in the worktree**, not those stale labels.
- xlsx text was read with `openpyxl` (`data_only=True`); cell values are the
  cached values of the v3.2.7 workbook.
