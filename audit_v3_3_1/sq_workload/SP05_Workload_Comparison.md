# SP05 — Workload comparison: original W6 `store_path` vs `sq_reload_v3212`

**Agent:** Agent D (LSU v3.3.1 SQ01/SQ03/SP05 workload comparison)
**Date:** 2026-11-11
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Mode:** read-only audit. No gem5/scons invocation, no workload-mapping change, no
Excel/pilot/record edit. This file is the only artifact written for SP05.
**Pair (researcher decision B, approval pending):** original W6 `store_path` vs
`sq_reload_v3212`.

---

## 0. What was measured, and how

Static: `sha256sum`, `readelf -sW`, `objdump -d --disassemble=main`, `openpyxl`
over sheets 5 and 6. Dynamic: the cited pilots' `manifest.json`, `pilot_meta.json`,
`lsq_fwd_injections.log`, `oracle.log`, `stdout.log`; the model records
`audit_v3_2_12/SP05_records_v3.2.12.binary-720eb780.json` and
`SP05_verdict_elig_v3.2.12.json`; the preflight
`audit_v3_2_12/SQ_Ordinal_Eligibility_Preflight_v3.2.12.md`. Every number is quoted
from an artifact named in the text.

---

## 1. Static comparison

| Item | Original W6 `store_path` | `sq_reload_v3212` |
|---|---|---|
| Source / ELF SHA256 | `.c` `8b7076ddc3ff01b24c8ceea745983f2efab7273b7532bd478a4f0a1ca27e5016`; ELF `906b3798adc618f388c1988389dd67140afeba6c706456fdeebdd524dc55fbcf` | `.c` `abbb0dcd…4133`; ELF `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| Golden | `checksum=0x2543a2a60de01795` (`store_path.golden`) | `7df5034c23f3e703` |
| Array (`readelf -sW`) | `a.0` @ `0x491990`, 32768 B | `buf` @ `0x491990`, 2048 B (`volatile`) |
| Store instruction(s) | `str q0,[x0],#16` `0x400558`; `str q0,[x0],#16` `0x4005a0`; `str q0,[x0],#16` `0x4005d8`; `stp q1,q0,[x0]` `0x400620`; `strb w1,[x2,x0]` `0x400644`; `strb w1,[x0],#4` `0x400670` | `str x6,[x8,x0,lsl#3]` `0x40053c` |
| Reload consumer | **none per store**; a single end-of-program `ldrb w0,[x4],#1` `0x400698` loop over the whole 32 KiB | `dmb ish` `0x400540`, `ldr x4,[x8,x0,lsl#3]` `0x400544`, FNV over the reloaded value `0x400550-0x400560` |
| Store stream | five non-overlapping regions, byte/16/32/64-bit widths, vectorised by GCC `-O2`; final same-width byte update | 128 uniform 8-byte stores, each followed by a same-address reload |
| What the model needs to observe | the selected store's `completeStore` bookkeeping (`_completed`, `storesToWB`) and whether the skipped write is later read | exactly that: a same-address reload after the premature completion |
| Excel identity | sheet5 SP05 rows: `store_path`, `906b3798…`, oracle `2543a2a60de01795`, `TargetField SQEntry::_completed / storesToWB`, injection `F6`, `EventOrdinal 1..5` | not a W1–W8 row; supplementary (`CLOSURE_INPUTS_v3.2.12.md:169`) |

Model definition is unchanged: `SP05_Definition_Freeze_v3.2.8.md` and
`SP05_Implementation_v3.2.9.md` define "Premature Store Completion" — the target
selected in `commitStores` is completed early in `writebackStores` via the real
`completeStore`, `_completed` false→true, `storesToWB` −1, and the cache write is
skipped (`mem_sent=0`). The only difference between the workloads is whether any
later load reads the lane whose write was lost.

Disassembly note (real `objdump`): `store_path`'s half/word/64-bit loops were
vectorised into `STP Q`/`STR Q`, so no explicit `strh`/`str w` remains; the store
stream (the SP05 target) is still real. `sq_reload_v3212` has one explicit
`str x` + `dmb ish` + `ldr x`.

---

## 2. Dynamic evidence, original vs re-selected ordinals

### 2.1 True original W6 evidence (`store_path`)

`SP05_Implementation_v3.2.9.md:17-30` reports five pilots on `store_path`,
ordinals 1..5:

| Pilot | seq | sq idx/gen | storesToWB | inject tick | terminal | oracle |
|---|---:|---|---|---|---:|---|---|
| R01 | 18 | 1/1 | 4→3 | 150150 | MASKED | PASS |
| R02 | 19 | 2/2 | 4→3 | 150150 | MASKED | PASS |
| R03 | 23 | 3/3 | 4→3 | 150150 | MASKED | PASS |
| R04 | 24 | 4/4 | 4→3 | 150150 | MASKED | PASS |
| R05 | 28 | 5/5 | 6→5 | 150535 | MASKED | PASS |

The same document states all five have `consumer_instructions=0`, the checksum
equals the matched control `0x2543a2a60de01795`, and "no later load reads the target
address in `store_path`", so `PROPAGATION_VERIFIED` stays 0. The raw v3.2.9 pilot
directories are **absent from this worktree** (searched `pilots_v3_2_*` for
`store_path` manifests: none); the evidence here is the published table, and this gap
is stated rather than zeroed.

The same startup-store limitation applies: seq 18..28 are the static binary's
C-runtime startup stores (identical stream to the SQ01/SQ03 literal family), not
`store_path`'s `a.0`; Agent B §5 maps the W6 v3.2.9 PCs to
`__libc_start_main` prologue stack stores (`0x400a10/18/20/24`). The v3.2.9 table's
MASKED is therefore structural.

### 2.2 Literal Excel ordinals on `sq_reload_v3212`

`pilots_v3_2_12/SUPP-SP05-R01..R05` used `sq_reload_v3212` with
`event_ordinal_used=1..5`. Injection at `seq=18`…, `write_skipped=1`,
`reload_seq=0`, `stage_outcome=NO_RELOAD_OBSERVED`, MASKED, oracle PASS. Source:
`audit_v3_2_12/SP05_records_v3.2.12.binary-720eb780.json`.

### 2.3 Re-selected B ordinals on `sq_reload_v3212`

Preflight K* = 940 for SP05 (`SQ_Ordinal_Eligibility_Preflight_v3.2.12.md` §2),
`R01B..R05B` = ordinals 940..944, selected stores `buf[0..4]` at
`0x491990..0x4919b0`.

| Pilot | Ordinal | store_seq / vaddr | completion tick | storesToWB | mem_sent | write_skipped | reload_seq / reload_data_hash | terminal / oracle |
|---|---:|---|---:|---|---:|---:|---|---|
| `SUPP-SP05-R01B` | 940 | 12108 / `0x491990` | 15915900 | 1→0 | 0 | 1 | 12110 / `a8c7f832281a39c5` | SDC / FAIL (`c684efc7a0466440`) |
| `SUPP-SP05-R02B` | 941 | 12227 / `0x491998` | 16031015 | 1→0 | 0 | 1 | 12229 / `a8c7f832281a39c5` | SDC / FAIL |
| `SUPP-SP05-R03B` | 942 | 12423 / `0x4919a0` | 16090690 | 1→0 | 0 | 1 | 12425 / `a8c7f832281a39c5` | SDC / FAIL |
| `SUPP-SP05-R04B` | 943 | 12643 / `0x4919a8` | 16136890 | 1→0 | 0 | 1 | 12645 / `a8c7f832281a39c5` | SDC / FAIL |
| `SUPP-SP05-R05B` | 944 | 12776 / `0x4919b0` | 16162300 | 1→0 | 0 | 1 | 12778 / `a8c7f832281a39c5` | SDC / FAIL |

All five: `RecordIntegrity=VALID`, `TraceCompleteness=COMPLETE`,
`FaultCausality=PROVEN`, `stage_outcome=RELOAD_UNVERIFIABLE`, `store_data_fnv=null`,
`data_correct=null`, `MissingCodes=['NO_EARLY_ANOMALY_EVENT']`. Source:
`audit_v3_2_12/SP05_records_v3.2.12.binary-720eb780.json`,
`SP05_verdict_elig_v3.2.12.json`,
`audit_v3_2_12/SQ01_SQ03_SP05_Eligible_Run_Records_v3.2.12.csv`.

Injection log (real, `pilots_v3_2_12/SUPP-SP05-R01B/lsq_fwd_injections.log`):

```
Cycle: 41339, Site: commitStores_select, store_seq=12108, sq_idx=944, sq_gen=1294, eligible_ordinal=940
Cycle: 41340, Site: writebackStores_prematureComplete, store_seq=12108, sq_idx=944, sq_gen=1294, mem_sent=0, eligible_ordinal=940, faults_injected: 1
```

Controls: `SUPP-SP05-C01B` uses seed `1489155957`, ordinal `940`, same workload and
binary, `--probability 0.0`; `injection_count=0`, `control_valid=true`, oracle PASS.

The stored value for `buf[0]` is `v = 0x73715f72656c6f61` (`sq_reload_v3212.c:42-43`).
The B reload hash `a8c7f832281a39c5` is the FNV of the stale zero word the reload
read after the skipped write (the same constant appears for all five contexts because
the lane is zero-initialised); the correct value would hash differently, so the
checksum fails. `commit_tick=0`/`drain_tick=0` in the record are the honest
"trace node not bound" values (`FW02_SQ01_SQ03_SP05_Evidence_Audit_v3.2.12.md` §2.1),
not a claim that the store never committed.

---

## 3. The ten questions, answered explicitly

### Q1. Does the original workload actually trigger the designed fault site?

**Yes for the hook; no for the designed observation.** `store_path` is a real store
stream (five regions, vectorised `STR Q`/`STP Q`, `0x400558`…`0x400670`), and the
v3.2.9 pilots report one select + one premature complete per run
(`SP05_Implementation_v3.2.9.md:17-30`). But the selected stores are the C-runtime
startup stores `seq 18/19/23/24/28`, not `store_path`'s `a.0`; the workload never
reads the target lane (`consumer_instructions=0`). So the completed-state fault is
injected, but its consequence is unreachable.

### Q2. Does the new workload change the model's research semantics?

**No.** Same hook (`commitStores` selection, `writebackStores` premature
`completeStore`), same target (`SQEntry::_completed` / `storesToWB`), same
`mem_sent=0` / skipped-write mechanism, same clamps and watchdog. What changes is the
observable: the same-address reload turns the lost write into an architectural
checksum error. The workload/oracle identity changes (`store_path`/`2543a2a6…` →
`sq_reload_v3212`/`7df5034c…`) and the ordinals change (1..5 → 940..944). The model's
question ("is a prematurely completed store's write lost?") is preserved and made
observable.

### Q3. Is the target Store/Load/SQ state really formed?

**Yes on both; observable only on B.** On B the log shows `commitStores_select`
then `writebackStores_prematureComplete` for `store_seq=12108`, `sq_idx=944`,
`sq_gen=1294`, `stores_to_wb_before=1 → after=0`, `mem_sent=0`, `write_skipped=1`;
the record's `completion_tick=15915900`. The reload is the real
`ldr x4,[x8,x0,lsl#3]` at `0x400544`. On `store_path` the state is formed for the
startup stores, but no load observes it.

### Q4. Can the first divergence before/after activation be observed?

**Yes on B; no on the original.** B: the write is skipped at completion tick
`15915900`, the very next reload `12110` reads the stale zero word
(`a8c7f832281a39c5`) and the oracle fails. Original: no later load reads the target,
so there is no post-activation observation.

### Q5. Can corrupted data or wrong control state be shown consumed?

**Yes on B; no on the original.** B: the lost write is consumed by the reload and by
the byte-wise FNV-1a checksum, producing `ORACLE_FAIL` in all five contexts (SDC).
Original: `consumer_instructions=0`; the checksum equals the matched control
(`SP05_Implementation_v3.2.9.md:28-30`).

### Q6. Does it produce the model-expected terminal state?

**B does; the original does not.** For a lost write that a later load reads, the
model-expected terminal is SDC; B produces SDC in 5/5. The original produces MASKED
because the lane is never read, not because the fault was masked in the hardware
sense.

### Q7. Is the golden reliable (SHA, baseline, oracle sensitivity)?

**The goldens are reliable, with one workbook defect.** W6 `store_path` golden
`2543a2a60de01795` matches ELF SHA `906b3798…`; `FINAL_BASELINE_SUMMARY.csv` records
W6 PASS on final binary `68c6ce73` with that exact checksum. Workbook defect: sheet6
W6's `ExpectedGolden` field says `7284dc0b3f6c64cf`, which disagrees with the same
sheet's `Oracle` column and with `store_path.golden`
(`2543a2a60de01795`) — a stale field, not an ELF defect (Agent B §3 item 5 notes the
same class of golden-prefix/staleness issues). `sq_reload_v3212` golden
`7df5034c23f3e703` is verified by `.golden`, `host.out`, and the probability-0
controls on `720eb780`. Sensitivity is demonstrated by B (oracle FAIL in 5/5).
Gap: `sq_reload` has no W1–W8 baseline row and no final-binary no-fault baseline.

### Q8. Can Fault-Control be strictly matched?

**Yes for the B pair at config level; only one control exists.** `SUPP-SP05-C01B`
matches `SUPP-SP05-R01B` on seed `1489155957`, ordinal `940`, workload SHA
`bcab9cc5…`, binary `720eb780…`, config SHA `01f912de…`; only `--probability`
differs. `injection_count=0`, `control_valid=true`, oracle PASS. Gap: contexts 2–5
have no paired control. The original W6 pair has no matched control directory in this
worktree (the v3.2.9 doc compares against a no-fault checksum, not a control run).

### Q9. Can five ROI percentile contexts be stably constructed?

**Yes for both; the executed B series is not percentile spread.** `sq_reload_v3212`
has a 128-iteration loop (`N=128`) with one eligible store per iteration; the SP05
loop window is ordinals 940..1067
(`SQ_Ordinal_Eligibility_Preflight_v3.2.12.md` §3.4, with the mid-loop spot check
1006..1015 = `buf[66..75]`, confirming 1006−940=66). A stable five-percentile rule is
`K* + {0, 32, 64, 96, 127}`; the executed B series is `K*..K*+4` (five consecutive
stores). `store_path` has a deep stream (about 16k store operations across the five
regions), so percentile ordinals are constructible there too, but the observation
remains null (end-of-program read-back only). The SP05 total eligible-event count is
not printed by the captured stdout (recorded as n/a, not zero).

### Q10. Which option is better for the paper?

**ADOPT_SQ_RELOAD.** Decisive evidence: the original W6 workload produces MASKED with
`consumer_instructions=0` (a lost write nobody reads; raw v3.2.9 pilots not even
present in this worktree), whereas the re-selected pair produces SDC with the skipped
write consumed by a same-address reload in 5/5. The latter is the direct architectural
consequence the SP05 model is designed to test. Two prerequisites keep this honest:
wire `store_data_fnv` (currently null → `RELOAD_UNVERIFIABLE`) and add the
`NO_EARLY_ANOMALY_EVENT` binding, so the model record itself proves the lost value
rather than relying only on the oracle differential.

---

## 4. Recommendation

**ADOPT_SQ_RELOAD** (no switch is performed here; approval pending).

Conditions:

1. Freeze `sq_reload_v3212` and oracle `7df5034c23f3e703` in sheet5/sheet6.
2. Freeze K*=940 and ordinals 940..944 for R01..R05.
3. Wire `store_data_fnv` and the early-anomaly event so `stage_outcome` is
   verifiable, not `RELOAD_UNVERIFIABLE`.
4. Re-run on the frozen formal binary with a matched control for each context.
5. Fix sheet6 W6 `ExpectedGolden` (`7284dc0b3f6c64cf` → `2543a2a60de01795`).

If the researcher declines the workbook change, `KEEP_ORIGINAL_PLUS_ENHANCE` is the
fallback: keep W6 as the frozen identity and add `sq_reload_v3212` as the mechanism
demonstration.

---

## 5. Risks and impacts

**SampleRunID.** All five `SP05-F6-W6-S01-R01..R05` rows become
`DESIGN_CHANGE_REQUIRED` (Agent A §4.1/§4.3): workload override (`store_path`
`906b3798…` → `sq_reload_v3212` `bcab9cc5…`), oracle override (`2543a2a6…` →
`7df5034c…`), ordinal override (1..5 → 940..944). The B IDs are supplementary
reproductions of the same five rows, not new contexts.

**Oracle.** `2543a2a60de01795` → `7df5034c23f3e703`. B's oracle FAIL is the SDC
signal; a no-fault baseline on the frozen formal binary is still required.

**Propagation.** B's model record has `stage_outcome=RELOAD_UNVERIFIABLE` and
`store_data_fnv=null` (the shared-file request is unwired), plus
`MissingCodes=['NO_EARLY_ANOMALY_EVENT']` and `early_anomaly_verified=missing`; the
other stage checks are `yes`. The frozen closure tool's generic field still yields
`LIFECYCLE_ONLY`, while the model record and oracle show SDC. Resolve both before
quoting a model-level propagation verdict: bind the model hops and the early-anomaly
event; do not relabel the tool output. The SDC claim itself is supported by real
evidence (`ORACLE_FAIL` in 5/5, reload hash = stale zero word,
`write_skipped=1`, `mem_sent=0`).

**Binary provenance.** Pilots on `720eb780…`; final baseline on `68c6ce73…`; current
on-disk `build/ARM/gem5.opt` = `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2`
(`sha256sum`). One frozen binary for the formal rerun; no mixing.

**Controls.** One matched control (`C01B`), not five. The original W6 has no matched
control run in this worktree.

**ROI context construction.** Current B is five consecutive stores; percentile
spread needs the K*+{0,32,64,96,127} rule frozen before running, and the rule must be
applied to the model's own eligible stream (SP05 counts `commitStores` selectables,
not SQ01/SQ03 events).

**Workload shape.** `store_path` exercises more store widths (byte/16/32/64-bit,
vectorised) than `sq_reload_v3212`'s uniform 8-byte stores. For SP05's completion
bookkeeping this does not matter, but a reviewer may ask about width coverage; the
paper should say the SP05 claim is about completion state, not store width.

**Workbook hygiene.** sheet6 W6 `ExpectedGolden=7284dc0b3f6c64cf` is stale relative
to `Oracle=2543a2a60de01795` and `store_path.golden`.

---

## 6. Evidence not available (stated, not zeroed)

- No gem5 run by this audit.
- The raw v3.2.9 `store_path` pilot directories are absent from this worktree; the
  original SP05 evidence is the published table in `SP05_Implementation_v3.2.9.md`.
- The SP05 total eligible-event count is not printed by the captured stdout; K*=940
  and the 128-store loop window are the ordinal facts used.
- `store_data_fnv` and the early-anomaly event are unwired/null by design in the
  current trace code; this is quoted, not inferred.
