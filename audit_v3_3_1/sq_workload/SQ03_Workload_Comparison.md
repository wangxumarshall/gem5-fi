# SQ03 — Workload comparison: original W3 `sq_drain` vs `sq_reload_v3212`

**Agent:** Agent D (LSU v3.3.1 SQ01/SQ03/SP05 workload comparison)
**Date:** 2026-11-11
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Mode:** read-only audit. No gem5/scons invocation, no workload-mapping change, no
Excel/pilot/record edit. This file is the only artifact written for SQ03.
**Pair (researcher decision B, approval pending):** original W3 `sq_drain` vs
`sq_reload_v3212`.

---

## 0. What was measured, and how

Static commands: `sha256sum`, `readelf -sW`, `objdump -d --disassemble=main`,
`openpyxl` over workbook sheets 5 and 6. Dynamic evidence: the cited pilots'
`manifest.json`, `pilot_meta.json`, `lsq_fwd_injections.log`, `oracle.log`,
`stdout.log`, plus `audit_v3_2_12/SQ03_records_v3.2.12.binary-720eb780.json`,
`SQ03_verdict_elig_v3.2.12.json`, and the preflight
`audit_v3_2_12/SQ_Ordinal_Eligibility_Preflight_v3.2.12.md`. No number below is
predicted; each is quoted from an artifact named in the text.

---

## 1. Static comparison

| Item | Original W3 `sq_drain` | `sq_reload_v3212` |
|---|---|---|
| Source / ELF SHA256 | `.c` `23f93a3f…d0cc2`; ELF `d423539c68ec2b4f788f206d92cfaac8be9fb9b3bc9d0799dcab3031867f188f` | `.c` `abbb0dcd…4133`; ELF `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| Golden | `ba3b3185e541ad03` | `7df5034c23f3e703` |
| Array (`readelf -sW`) | `a.0` @ `0x491990`, 65536 B | `buf` @ `0x491990`, 2048 B (`volatile`) |
| Store instruction | `strb w0,[x1]` `0x400530`; `strb w3,[x1,#1]` `0x400538`; `stur w2,[x1,#-4]` `0x400540`; `strb w0,[x1],#16` `0x400560` | `str x6,[x8,x0,lsl#3]` `0x40053c` |
| Reload / visibility probe | none until the end-of-program `ldrb w2,[x5],#1` `0x400590` bulk read over 64 KiB | `dmb ish` `0x400540`, then `ldr x4,[x8,x0,lsl#3]` `0x400544`; `cmp x4,x6` `0x40056c` |
| What the model needs to observe | the early `_canWB` permission and the drain/commit order of the selected store; a later load to the same address would expose visibility | exactly that: same-address reload after the drain, before/after commit |
| Excel identity | sheet5 SQ03 rows: `sq_drain`, `d423539c…`, oracle `ba3b3185e541ad03`, `EventOrdinal 1..5`, `TargetField SQEntry::_canWB`, hook `executeStore` | not a W1–W8 row; supplementary (`CLOSURE_INPUTS_v3.2.12.md:169`) |

Model definition is unchanged between the two: `SQ03_Definition_Freeze_v3.2.7.md`
and `SQ03_Implementation_v3.2.8.md` define "Premature Store Writeback Permission":
`_canWB` is set early for one selected real store at `executeStore`, with a paired
`storesToWB` increment; no address, size or data is changed. The only difference
between the workloads is whether a later load can observe the earlier visibility.

---

## 2. Dynamic evidence, original vs re-selected ordinals

### 2.1 True original W3 evidence (sq_drain)

`pilots_v3_2_8/SQ03-R01..R05`, binary
`b988b7503cdf1feab10b99d09ec85df84b42eb385396142e0b7be6a197c63a45`, ordinals 1..5.
Quoted from `pilots_v3_2_8/SQ03-R01/pilot_meta.json`:

```
store_seq=18, store_pc=0x4008d0, store_addr=0x7ffffefd10, store_size=8,
sq_entry_id=1, sq_entry_generation=1, canwb_before=0, canwb_after=1,
stores_to_wb_before=0, stores_to_wb_after=1, eligible_ordinal=1
```

The original W3 measurements are in `SQ03_Implementation_v3.2.8.md:28-36` and
`SQ03_Propagation_Analysis_v3.2.9.md:7-16`; the literal `SUPP-SQ03-R01` record on
`sq_reload_v3212` (`audit_v3_2_12/SQ03_records_v3.2.12.binary-720eb780.json`) selects
the same startup store and has the same shape:

| Metric | Original W3 R01 (sq_drain) |
|---|---|
| `canwb_before → after` | 0 → 1 |
| `storesToWB` | 0 → 1 |
| `writeback_tick` (permission point) | 140910 |
| actual `store_mem_write` | 198275 (R02–R05: 203665), 49,775–57,365 ticks later |
| `commit_tick` | 149380 |
| `visible_before_commit` | **0** |
| `reload_seq` | **0** |
| `effect_outcome` | `LIFECYCLE_ONLY` / `NO_DOWNSTREAM_EFFECT` |
| terminal / oracle | MASKED / PASS |

(The literal `sq_reload_v3212` reproduction records `drain_tick=200970` for R01 and
203665 for R02–R05; that is a supplementary run on a different workload, not the
original W3 measurement, so it is quoted separately here.)

`SQ03_Implementation_v3.2.8.md:38-45` states all five original pilots are exactly
this shape: one injection, `canWB 0→1`, `storesToWB +1`, no HANG, MASKED, oracle
PASS, and explicitly "no later load/consumer reads the target store; time shift alone
is not called SDC". `SQ03_Propagation_Analysis_v3.2.9.md:7-20` adds that the actual
`store_mem_write` happens 49,775–57,365 ticks after the permission point, i.e.
"permission is not visibility". As with SQ01, the old trace cannot be re-graded by
the current closure tool: `SQ03_records_v3.2.12.binary-b988b750.json` is five
`UNRESOLVED` / `TRACE_INCOMPLETE` records.

### 2.2 Literal Excel ordinals on `sq_reload_v3212`

`pilots_v3_2_12/SUPP-SQ03-R01..R05` used `sq_reload_v3212` with
`event_ordinal_used=1..5`. They inject at the C-runtime startup store `seq=18`
(`store_addr=0x7ffffefd00`…), `reload_seq=0`, MASKED, oracle PASS,
`effect_outcome=LIFECYCLE_ONLY` / `NO_DOWNSTREAM_EFFECT`. This is the same
startup-store defect documented in
`FW02_SQ01_SQ03_SP05_Evidence_Audit_v3.2.12.md` §2.1; it is not the workload's
`buf`.

### 2.3 Re-selected B ordinals on `sq_reload_v3212`

Preflight K* = 1009 for SQ03 (`SQ_Ordinal_Eligibility_Preflight_v3.2.12.md` §2),
`R01B..R05B` = ordinals 1009..1013, selected stores `buf[0..4]` at
`0x491990..0x4919b0`.

| Pilot | Ordinal | store_seq / vaddr | injection tick | drain_tick | commit_tick | visible_before_commit | reload_seq / hash | terminal / oracle |
|---|---:|---|---:|---:|---:|---|---|---|
| `SUPP-SQ03-R01B` | 1009 | 12108 / `0x491990` | 15914360 | 15914360 | 15915130 | **1** | 12110 / `f6a2a263b2e746b9` | MASKED / PASS |
| `SUPP-SQ03-R02B` | 1010 | 12227 / `0x491998` | 16029475 | 16029475 | 16030245 | 1 | 12229 / `69a6347498f3c2dd` | MASKED / PASS |
| `SUPP-SQ03-R03B` | 1011 | 12423 / `0x4919a0` | 16089150 | 16089150 | 16089920 | 1 | 12425 / `fbbcba348bb2aaf5` | MASKED / PASS |
| `SUPP-SQ03-R04B` | 1012 | 12643 / `0x4919a8` | 16135350 | 16135350 | 16136120 | 1 | 12645 / `781d22051fdb27f9` | MASKED / PASS |
| `SUPP-SQ03-R05B` | 1013 | 12776 / `0x4919b0` | 16160760 | 16160760 | 16161530 | 1 | 12778 / `849c6aba106027e9` | MASKED / PASS |

All five: `canwb_state_changed=1`, `storesToWB` delta +1 (R01B 2→3, quoted from
`pilots_v3_2_12/SUPP-SQ03-R01B/pilot_meta.json`), `effect_outcome=
CHAIN_VISIBILITY_MOVED`, `effect_reason=DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER`,
`RecordIntegrity=VALID`, `TraceCompleteness=COMPLETE`. Source:
`audit_v3_2_12/SQ03_records_v3.2.12.binary-720eb780.json`,
`SQ03_verdict_elig_v3.2.12.json`, `SQ01_SQ03_SP05_Eligible_Run_Records_v3.2.12.csv`.

The injection log (real, `pilots_v3_2_12/SUPP-SQ03-R01B/lsq_fwd_injections.log`):

```
Cycle: 41336, Site: executeStore_canWB, store_seq=12108, sq_idx=944, sq_gen=1294, eligible_ordinal=1009, faults_injected: 1
```

Control `SUPP-SQ03-C01B`: same seed `2214819981`, same ordinal `1009`, same workload
and binary, `--probability 0.0`, `injection_count=0`, `control_valid=true`, oracle
PASS.

---

## 3. The ten questions, answered explicitly

### Q1. Does the original workload actually trigger the designed fault site?

**Yes for the hook; no for the designed observation.** W3 `sq_drain` contains real
stores and the v3.2.8 pilots show `Site=executeStore_canWB`, `canWB 0→1`,
`storesToWB 0→1` on store `seq=18`
(`pilots_v3_2_8/SQ03-R01/pilot_meta.json`). But the selected store is a C-runtime
startup store at `0x7ffffefd10`, not the workload's `a.0` at `0x491990`; the
workload has no later load to that lane. So the `_canWB` state is formed and
perturbed, but the designed downstream observation is absent.

### Q2. Does the new workload change the model's research semantics?

**No.** The hook, target field (`SQEntry::_canWB`), the paired `storesToWB`
increment, the one-shot clamp, the watchdog, and the "no address/size/data change"
invariant are unchanged (`SQ03_Definition_Freeze_v3.2.7.md`,
`SQ03_Implementation_v3.2.8.md`). What changes is the observable: `sq_reload_v3212`
adds a same-address reload after `dmb ish`, so the earlier drain is visible before
commit. The workload/oracle identity changes (`sq_drain`/`ba3b3185…` →
`sq_reload_v3212`/`7df5034c…`) and the ordinals change (1..5 → 1009..1013). The
research question ("does early writeback permission move store visibility?") is
preserved; the new workload makes it measurable instead of null.

### Q3. Is the target Store/Load/SQ state really formed?

**Yes on sq_reload; yes but unobservable on sq_drain.** On B the selected store is
the real `str x6,[x8,x0,lsl#3]` at `0x40053c`; the record binds `sq_idx=944`,
`sq_gen=1294`, `canWB 0→1`, `storesToWB 2→3`. The reload is the real
`ldr x4,[x8,x0,lsl#3]` at `0x400544`. On the original the SQ entry is formed and the
state is changed, but no load observes it.

### Q4. Can the first divergence before/after activation be observed?

**Yes on sq_reload; no on sq_drain.** B: the injection happens at tick `15914360`
and the drain occurs at the **same tick**, 770 ticks before commit
(`15915130`); `visible_before_commit=1` and the reload `12110` consumes the lane.
Original: the permission point is `140910`, commit is `149380`, and the actual cache
write is `198275` (R02–R05: `203665`) — **after** commit — with
`visible_before_commit=0` and `reload_seq=0` (`SQ03_Propagation_Analysis_v3.2.9.md:9-16`).
The v3.2.9 analysis measured the cache write 49,775–57,365 ticks after the permission
point and found zero consumer instructions.

### Q5. Can corrupted data or wrong control state be shown consumed?

**Wrong control state: yes on B; data: no on either.** On B the early `_canWB`
permission is consumed as an early visibility: the reload reads the target lane
before commit, `reload_seq=12110`, `visible_before_commit=1`. The data itself is
correct (SQ03 changes no address/size/data), so the oracle passes; that is why the
terminal is MASKED. On the original, the state change has no downstream effect
(`NO_DOWNSTREAM_EFFECT`). The model is a control/state model, not a data model; a
paper must not call the B result SDC.

### Q6. Does it produce the model-expected terminal state?

**Yes on B, in the model's own terms.** The model-expected terminal for SQ03 is
MASKED (no architectural data change; `SQ03_Implementation_v3.2.8.md:44-45`). B
produces MASKED in 5/5 while carrying a real `CHAIN_VISIBILITY_MOVED` record. So B
matches the expected terminal and additionally shows a causal visibility effect.
The original also produces MASKED, but for the weaker reason that nothing downstream
happens at all.

### Q7. Is the golden reliable (SHA, baseline, oracle sensitivity)?

**The goldens are reliable; the oracle's PASS on SQ03 is by design, not a
sensitivity failure.** W3 `sq_drain` golden `ba3b3185e541ad03` matches ELF SHA
`d423539c…` and `FINAL_BASELINE_SUMMARY.csv` records W3 PASS on final binary
`68c6ce73`. `sq_reload_v3212` golden `7df5034c23f3e703` is verified by `.golden`,
`host.out`, and the probability-0 controls on `720eb780`. SQ03 B oracle PASS is
expected: the model changes no data, and `SQ03_Implementation_v3.2.8.md` and
`SQ03_Propagation_Analysis_v3.2.9.md` both say time shift alone is not called SDC.
The oracle is not shown to be insensitive to a data error here (that is not SQ03's
mechanism). Gap: `sq_reload` has no W1–W8 baseline row and no final-binary
no-fault baseline.

### Q8. Can Fault-Control be strictly matched?

**Yes for the B pair at config level; only one control exists.** `SUPP-SQ03-C01B`
matches `SUPP-SQ03-R01B` on seed `2214819981`, ordinal `1009`, workload SHA
`bcab9cc5…`, binary `720eb780…`, config SHA `01f912de…`; only `--probability`
differs. `injection_count=0`, `control_valid=true`, oracle PASS. Gap: contexts 2–5
have no paired control. The original W3 pair has no matched control directory in this
worktree (only the no-fault baseline).

### Q9. Can five ROI percentile contexts be stably constructed?

**Yes for both; the executed B series is not percentile spread.** `sq_reload_v3212`
has a 128-iteration loop (`N=128`) with one eligible store per iteration; the SQ03
loop window is ordinals 1009..1136 (`SQ_Ordinal_Eligibility_Preflight_v3.2.12.md`
§2). A stable five-percentile rule is `K* + {0, 32, 64, 96, 127}`; each is a
distinct store/reload context. The executed B series is `K*..K*+4` (five consecutive
stores). SQ03's total eligible stream count is not printed by the run summary
(recorded as n/a, not zero); the ordinal boundary and the 128-deep loop are what the
construction needs. `sq_drain` also has a deep store stream (12,288 stores in its two
loops), so percentile ordinals are constructible there, but the observation remains
null.

### Q10. Which option is better for the paper?

**ADOPT_SQ_RELOAD.** Decisive evidence: the original W3 workload produces MASKED with
`visible_before_commit=0` and `NO_DOWNSTREAM_EFFECT` (a null result whose old trace
the current closure tool cannot re-grade), whereas the re-selected pair produces
MASKED with `DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER`, `visible_before_commit=1`
and a real `reload_seq` in 5/5. That is the model's designed consequence (visibility
moved), with the honest terminal MASKED. If the researcher declines the workbook
change, `KEEP_ORIGINAL_PLUS_ENHANCE` is the fallback: keep W3 as the frozen identity
and add `sq_reload_v3212` as the mechanism demonstration.

---

## 4. Recommendation

**ADOPT_SQ_RELOAD** (no switch is performed here; approval pending).

Conditions:

1. Freeze `sq_reload_v3212` and oracle `7df5034c23f3e703` in sheet5/sheet6 (new W9
   or explicit W3 override).
2. Freeze K*=1009 and ordinals 1009..1013 for R01..R05.
3. Present the terminal honestly as MASKED / visibility-moved, **not SDC**.
4. Re-run on the frozen formal binary and add matched controls for contexts 2–5.

---

## 5. Risks and impacts

**SampleRunID.** All five `SQ03-F0-W3-S02-R01..R05` rows become
`DESIGN_CHANGE_REQUIRED` (Agent A §4.1/§4.3): workload override (`sq_drain`
`d423539c…` → `sq_reload_v3212` `bcab9cc5…`), oracle override (`ba3b3185…` →
`7df5034c…`), and ordinal override (1..5 → 1009..1013). The B IDs are supplementary
reproductions of the same five rows, not new contexts.

**Oracle.** `ba3b3185e541ad03` → `7df5034c23f3e703`. B's oracle PASS is expected and
must not be reported as a sensitivity failure. Need a no-fault baseline on the frozen
formal binary.

**Propagation.** The frozen closure tool again reports `LIFECYCLE_ONLY` because its
generic `value_divergence` field is 0, while the `sq03_effect` model record is
`CHAIN_VISIBILITY_MOVED`/`DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER` and
`verdict_elig` reports all stages yes. Quote the model record; do not relabel the
tool. The effect is a **time shift**, and the model's own documentation says time
shift alone is not SDC. The paper claim is "early `_canWB` permission makes the store
visible before commit", supported by drain==injection tick and commit 770 ticks
later.

**Binary provenance.** Pilots on `720eb780…`; final baseline on `68c6ce73…`; current
on-disk `build/ARM/gem5.opt` = `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2`
(`sha256sum`). One frozen binary for the formal rerun; no mixing.

**Controls.** One matched control (`C01B`), not five.

**ROI context construction.** Current B is five consecutive stores; percentile
spread needs the K*+{0,32,64,96,127} rule frozen before running.

---

## 6. Evidence not available (stated, not zeroed)

- No gem5 run by this audit.
- Old W3 SQ03 trace is `TRACE_INCOMPLETE` for the current closure tool
  (`SQ03_records_v3.2.12.binary-b988b750.json`).
- The SQ03 total eligible-event count is not printed by the captured stdout; the
  preflight gives K*=1009 and the 128-store loop window, which is sufficient for
  percentile construction.
- The reload/consumer exact tick is not in the model record; the record gives
  `reload_seq` and the drain/commit ticks.
