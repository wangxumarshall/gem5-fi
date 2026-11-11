# SQ01 — Workload comparison: original W3 `sq_drain` vs `sq_reload_v3212`

**Agent:** Agent D (LSU v3.3.1 SQ01/SQ03/SP05 workload comparison)
**Date:** 2026-11-11
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Mode:** read-only audit. No gem5/scons invocation, no workload-mapping change, no
Excel/pilot/record edit. This file is the only artifact written for SQ01.
**Pair (researcher decision B, approval pending):** original W3 `sq_drain` vs
`sq_reload_v3212`.

---

## 0. What was measured, and how

Real commands used (static, no simulation):

- `sha256sum sq_drain.c sq_reload_v3212.c sq_drain sq_reload_v3212`
- `readelf -sW sq_drain sq_reload_v3212 | grep -E ' (a\.0|buf)$'`
- `objdump -d --disassemble=main sq_drain` and `... sq_reload_v3212`
- `python3` + `openpyxl` over sheet `5.60个样本执行矩阵` and sheet `6.工作负载及无故障基线`
- each pilot's `manifest.json`, `pilot_meta.json`, `lsq_fwd_injections.log`, `oracle.log`,
  `stdout.log` and `trace_v31.jsonl` of the cited pilots
- `audit_v3_2_12/SQ01_records_v3.2.12.binary-720eb780.json` and the `verdict_elig` JSON
- `audit_v3_2_12/SQ_Ordinal_Eligibility_Preflight_v3.2.12.md` (ordinal facts)

No dynamic claim below is inferred from code reading alone; every dynamic number is
quoted from a pilot artifact named in the text.

---

## 1. Static comparison

| Item | Original W3 `sq_drain` | `sq_reload_v3212` |
|---|---|---|
| Source | `workloads/sq_drain.c` | `workloads/sq_reload_v3212.c` |
| Source SHA256 | `23f93a3fb6041e3f901cb0e809374fdec4990495cead67f77a63c6fa8b7d0cc2` | `abbb0dcd3c22666a9b0e05a80743c32256d415e33a089b5755269d3db0614133` |
| ELF SHA256 | `d423539c68ec2b4f788f206d92cfaac8be9fb9b3bc9d0799dcab3031867f188f` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| Golden file | `sq_drain.golden` = `ba3b3185e541ad03` | `sq_reload_v3212.golden` = `7df5034c23f3e703` |
| Host output | `host.out` = `checksum=0xba3b3185e541ad03` | `host.out` = `checksum=0x7df5034c23f3e703` |
| Static array (`readelf -sW`) | `a.0` @ `0x491990`, 65536 B | `buf` @ `0x491990`, 2048 B (`volatile`) |
| Store site | `strb w0,[x1]` `0x400530`, `strb w3,[x1,#1]` `0x400538`, `stur w2,[x1,#-4]` `0x400540`, `strb w0,[x1],#16` `0x400560` | `str x6,[x8,x0,lsl#3]` `0x40053c` |
| Reload consumer | **none per store**; one bulk `ldrb w2,[x5],#1` `0x400590` over the whole 64 KiB at the end | `ldr x4,[x8,x0,lsl#3]` `0x400544`, immediately after `dmb ish` `0x400540`, then byte-wise FNV and `cmp x4,x6` `0x40056c` |
| Store stream | 8192 iterations x 3 stores + 4096 byte stores; SQ01 audit records 31,092 committed stores / 66,721 committed loads | 128 iterations, exactly one 8-byte store + one same-address reload per iteration (`N=128`, `sq_reload_v3212.c:23`) |
| Oracle sensitivity to the fault site | checksums the whole `a[]`, so a stored byte that survives to the end would change the checksum; but the ordinal-1..5 selected store is outside `a[]` (see §2) | checksums the reloaded value and branches on `r == v` (`sq_reload_v3212.c:41-52`); every stored lane is read back by construction |
| Excel identity | sheet5 SQ01 rows: `WorkloadPath .../sq_drain`, `BinarySHA256 d423539c…`, `Oracle ba3b3185e541ad03`, `EventOrdinal 1..5` | not a W1–W8 row; `CLOSURE_INPUTS_v3.2.12.md:169` calls it a supplementary workload |

Disassembly provenance: the two `objdump -d --disassemble=main` outputs above are
the tracked ELFs in
`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/docs/gem5-fi/lsu/implementation_v3_2/workloads/`.

Key structural difference: `sq_drain` is a **store stream with one end-of-program
read-back**; `sq_reload_v3212` is a **store → `dmb ish` → same-address reload** loop.
SQ01 is a store-data model; only the second shape gives a per-store data consumer.

---

## 2. Dynamic evidence, original vs re-selected ordinals

### 2.1 True original W3 evidence (sq_drain)

| Pilot | Binary SHA | Ordinal | Injection | Record outcome | Source of record |
|---|---|---:|---|---|---|
| `pilots_v3_2_3/SQ01-R01` (W3, sq_drain) | `8eb7ce8d76ab63d90dbd00694efb90c7c2545da47ad07ecf5325399274a3b682` | 1 | `seq=18`, `old=0x0`, `new=0x8`, MASKED | MASKED, oracle PASS; "the injected byte is overwritten by a later store in this workload; no SDC is observed, so the model is not marked PROPAGATION_VERIFIED" (`SQ01_Audit_and_Implementation.md:48-51`) | `pilots_v3_2_3/SQ01-R01/pilot_meta.json`; `SQ01_Audit_and_Implementation.md` |

Important honesty point: the frozen closure tool cannot re-grade this old trace.
`audit_v3_2_12/SQ01_records_v3.2.12.binary-8eb7ce8d.json` contains five records and
every one is `UNRESOLVED` / `TRACE_INCOMPLETE` (no `sq01_chain` node). So the
original W3 MASKED terminal rests on the v3.2.3 pilot_meta + audit text, not on a
current-tool record.

### 2.2 "Literal Excel ordinal" family on `sq_reload_v3212`

`pilots_v3_2_12/SUPP-SQ01-R01..R05` used `sq_reload_v3212` (not `sq_drain`) with
`event_ordinal_used=1..5`. They are a preserved-context reproduction, not the W3
workload. Injection `seq=18`, `PC=0x400910`, tick 140910, `old=0x0 → new=0x8`;
`reload_seq=0`, `consumer_seq=0`, `chain_verdict=STORE_COMMITTED_LANE_NOT_READ`,
terminal MASKED, oracle PASS, `FinalClassification=LIFECYCLE_ONLY` in all five.
Source: `audit_v3_2_12/SQ01_records_v3.2.12.binary-720eb780.json`; the audit explains
these are C-runtime startup stack stores (`FW02_SQ01_SQ03_SP05_Evidence_Audit_v3.2.12.md`
§2.1, quoted in §3 below).

### 2.3 Re-selected B ordinals on `sq_reload_v3212`

Preflight rule (frozen before any fault run): first ordinal whose selected store
vaddr lies in `[buf, buf+0x800)` = `[0x491990, 0x492190)`; K* = 1006 for SQ01
(`SQ_Ordinal_Eligibility_Preflight_v3.2.12.md` §1–2). `R01B..R05B` = ordinals
1006..1010.

| Pilot | Ordinal used | store_seq | vaddr | Injection (byte0) | mem_write_hash = reload_data_hash = consumer_hash | reload_seq / consumer_seq | Terminal / Oracle |
|---|---:|---:|---|---|---|---|---|
| `SUPP-SQ01-R01B` | 1006 | 12108 | `0x491990` | `0x61 → 0x69` (bit3) | `f86e18335679a771` | 12110 / 12113 | SDC / FAIL (`139d0907c41e080c`) |
| `SUPP-SQ01-R02B` | 1007 | 12227 | `0x491998` | `0x62 → 0x6a` | `2a7c881ab831bd95` | 12229 / 12232 | SDC / FAIL |
| `SUPP-SQ01-R03B` | 1008 | 12423 | `0x4919a0` | `0x63 → 0x6b` | `e6371a5feb48222d` | 12425 / 12428 | SDC / FAIL |
| `SUPP-SQ01-R04B` | 1009 | 12643 | `0x4919a8` | `0x64 → 0x6c` | `a74045b6b4580b81` | 12645 / 12648 | SDC / FAIL |
| `SUPP-SQ01-R05B` | 1010 | 12776 | `0x4919b0` | `0x65 → 0x6d` | `fff725544d920281` | 12778 / 12781 | SDC / FAIL |

All five: `InjectionCount=1`, `RecordIntegrity=VALID`, `TraceCompleteness=COMPLETE`,
`FaultCausality=PROVEN`, `Stages` all yes in the `verdict_elig` record. Source:
`audit_v3_2_12/SQ01_records_v3.2.12.binary-720eb780.json`,
`audit_v3_2_12/SQ01_SQ03_SP05_Eligible_Run_Records_v3.2.12.csv`,
`pilots_v3_2_12/SUPP-SQ01-R01B/{lsq_fwd_injections.log,oracle.log,pilot_meta.json}`.

Injection log for R01B (quoted):

```
Tick: 15914360, Site: lsq_write_sq_entry, FaultType: sq01_bit3_flip, seq: 12108, sq_idx: 944, entry_generation: 1294, old_byte0: 0x61, new_byte0: 0x69, faults_injected: 1
```

The trace itself contains the full chain
`memory_request → memory_response → register_writeback → consumer_commit`
(event_ids 5031..5037 in `pilots_v3_2_12/SUPP-SQ01-R01B/trace_v31.jsonl`).

Control: `SUPP-SQ01-C01B` uses the same seed `591611458`, same ordinal `1006`, same
workload SHA, same binary and config, `--probability 0.0`; `injection_count=0`,
`control_valid=true`, oracle PASS.

---

## 3. The ten questions, answered explicitly

### Q1. Does the original workload actually trigger the designed fault site?

**Partially.** The designed site is the SQ entry data write
(`LSQUnit::write`, `lsq_unit.cc:1818`, memcpy at `:1836-1839`;
`SQ01_Audit_and_Implementation.md`). W3 `sq_drain` contains real stores and the
v3.2.3 pilots did inject on a real store (`pilots_v3_2_3/SQ01-R01/pilot_meta.json`:
`seq=18`, `old=0x0 → new=0x8`, `injected=1`). So the **hook fires on a real store**.
But the selected store is a C-runtime startup store, not the workload's `a[]` lane:
the same ordinal-1 store on the shared startup stream is at
`0x7ffffefd00` (`audit_v3_2_12/FW02_SQ01_SQ03_SP05_Evidence_Audit_v3.2.12.md` §2.1),
while `sq_drain`'s `a.0` is at `0x491990`. The SQ01 audit states the corrupted byte
is overwritten and no SDC is observed. **Verdict: site yes; designed target lane no.**

### Q2. Does the new workload change the model's research semantics?

**No at the model level; yes at the evidence level.** The fault model is unchanged:
same F0 trigger, same `sq01_bit3` mode, same `LSQUnit::write` hook, same
`data[0] ^= 0x08`. What changes is the observable: `sq_drain` has no per-store
consumer, so the fault is structurally MASKED; `sq_reload_v3212` reloads every
stored lane after `dmb ish`, so the corrupted SQ data reaches an architectural
consumer. The workload and oracle identity do change (`sq_drain` →
`sq_reload_v3212`; golden `ba3b3185e541ad03` → `7df5034c23f3e703`), and the
ordinals change (1..5 → 1006..1010). The model's research question ("does SQ entry
data corruption propagate to a consumed value?") is preserved and made answerable.

### Q3. Is the target Store/Load/SQ state really formed?

**Yes on sq_reload, only partially on sq_drain.** On `sq_reload_v3212` the store is
`str x6,[x8,x0,lsl#3]` at `0x40053c` and the reload is `ldr x4,[x8,x0,lsl#3]` at
`0x400544` after the `dmb ish`; the preflight comment explains why the freed SQ
entry cannot forward the reload and it is served from L1D
(`sq_reload_v3212.c:1-19`). The B records show `sq_idx=944`, `gen=1294` and a real
`reload_seq` (`12110`). On `sq_drain`, SQ entries are formed for real stores, but no
per-store reload is formed; the only read is the end-of-program bulk FNV loop.

### Q4. Can the first divergence before/after activation be observed?

**Yes on sq_reload, no on sq_drain.** B: injection at tick `15914360` flips byte0
`0x61 → 0x69`; the drained write, the reload and the consumer all carry
`f86e18335679a771` (hash-equal: the corruption is the only source), and the oracle
fails. The trace carries the five-hop chain. Original: `reload_seq=0`,
`consumer_seq=0`, the record stops at `STORE_COMMITTED_LANE_NOT_READ`; no
post-activation divergence is observable.

### Q5. Can corrupted data or wrong control state be shown consumed?

**Yes on sq_reload, no on sq_drain.** B: `mem_write_hash == reload_data_hash ==
consumer_hash` in all five contexts, `ConsumerSourceLinked`-grade chain,
`ApplicationOracle=FAIL` (SDC). Original: the faulted startup lane is never read;
`reload_seq=0`. The SQ01 audit explicitly says the byte is overwritten and no SDC is
observed, which is why `PROPAGATION_VERIFIED` was not claimed.

### Q6. Does it produce the model-expected terminal state?

**sq_reload does; sq_drain does not.** For a consumed store-data corruption the
model-expected terminal is SDC (SQ01's coverage profile is `MASKED|SDC`), and the B
series produces SDC in 5/5. The original produces MASKED in 5/5 for a structural
reason, not a masking mechanism.

### Q7. Is the golden reliable (SHA, baseline, oracle sensitivity)?

**The goldens are reliable; the original workload's context does not exercise
them.** W3 `sq_drain` golden `ba3b3185e541ad03`: ELF SHA matches sheet6
`d423539c…`, and `logs_v3_2_12/baselines_w1_w8/FINAL_BASELINE_SUMMARY.csv` records
W3 PASS on the final binary `68c6ce73` with the exact checksum. The oracle does
checksum the whole `a[]`, so it is sensitive to a surviving corrupted store byte;
but the selected startup store is outside `a[]`, so the original runs never test
that sensitivity. `sq_reload_v3212` golden `7df5034c23f3e703`: `.golden` and
`host.out` agree, and the three probability-0 controls on binary `720eb780` print
the golden. Its sensitivity is demonstrated by SQ01 B itself (oracle FAIL in 5/5).
Gap: `sq_reload` has **no W1–W8 baseline row** and no no-fault baseline on the final
binary; the controls are on `720eb780`, not the final binary.

### Q8. Can Fault-Control be strictly matched?

**Yes for the re-selected pair, with a coverage gap.** `SUPP-SQ01-C01B` matches
`SUPP-SQ01-R01B` on seed (`591611458`), ordinal (`1006`), workload SHA
(`bcab9cc5…`), binary (`720eb780…`) and config SHA
(`01f912de3388aaf420aa69d5dd55098ddfb97851faf0269a6b009fcc389bf6e5`); only
`--probability` differs (0.0 vs 1.0). It fires 0 injections and the oracle passes.
Gap: only **one** matched control exists per model (context 1); contexts 2–5 have no
paired control. For the original W3 pair, no matched control directory exists in
this worktree, only the no-fault baseline.

### Q9. Can five ROI percentile contexts be stably constructed?

**Yes for both workloads in principle; the executed B series is not percentile
spread.** `sq_reload_v3212` has a fixed 128-iteration loop (`N=128`), exactly one
eligible store per iteration, and the loop-entry ordinal is K*=1006; the 128 store
window is therefore ordinals 1006..1133 (`SQ_Ordinal_Eligibility_Preflight_v3.2.12.md`
§3.2). A stable five-percentile construction is `K* + {0, 32, 64, 96, 127}`, each a
distinct store/reload context. The executed B series is K*..K*+4 (five consecutive
stores), which is distinct but not percentile spread. SQ01's whole eligible stream is
1604 events (`CHAOS_LSU_TRIGGER ... attempted=1604 eligible=1604`, quoted from
`pilots_v3_2_12/SUPP-SQ01-R01B/stdout.log`): 1005 pre-loop + 128 loop + 471
post-loop. `sq_drain` has a deep stream (12,288 stores in the two loops; 31,092
committed stores per the SQ01 audit), so percentile ordinals are constructible there
too, but they still carry no per-store consumer.

### Q10. Which option is better for the paper?

**ADOPT_SQ_RELOAD.** Decisive evidence: the original W3 workload yields
MASKED/LIFECYCLE_ONLY with `reload_seq=0` (no consumer) on an older binary whose
trace the current closure tool cannot re-grade; the re-selected pair yields
`COMPLETE_CHAIN` with `mem_write_hash == reload_data_hash == consumer_hash` and
SDC in 5/5 on a README-grade `VALID/COMPLETE` trace. For a propagation paper, the
second is the only one that shows the SQ01 defect reaching an architectural consumer.

---

## 4. Recommendation

**ADOPT_SQ_RELOAD** (subject to the researcher's approval; **no switch is performed
in this audit**).

Conditions that must be met before formal adoption (all are audit/process items, not
model changes):

1. Freeze `sq_reload_v3212` (SHA `bcab9cc5…`, oracle `7df5034c23f3e703`) as an
   authoritative workload row (either a new W9 or an explicit W3 override) in sheet5
   and sheet6.
2. Freeze the ordinal rule: K*=1006 for SQ01, R01..R05 = 1006..1010, recorded as
   `EventOrdinal`/`ordinal_used`; do not leave Excel `EventOrdinal=1..5`.
3. Re-run the five formal contexts, plus a matched control per context, on the
   frozen formal binary and record its SHA.
4. Resolve the closure-tool classification gap (§5) before quoting any model-level
   propagation verdict.

---

## 5. Risks and impacts

**SampleRunID.** All five SQ01 rows (`SQ01-F0-W3-S01-R01..R05`) become
`DESIGN_CHANGE_REQUIRED` exactly as Agent A records: Excel workload `sq_drain`
(`d423539c…`, golden `ba3b3185…`) is replaced by `sq_reload_v3212`
(`bcab9cc5…`, golden `7df5034c…`), and the event is K*+n, not EventOrdinal 1..5.
The `SUPP-SQ01-R01B..R05B` IDs are supplementary reproductions of the same five
Excel rows, not five extra contexts (Agent A §4.1). Adopting without a workbook
update would leave the authoritative sheet5 row false.

**Oracle.** The W3 oracle changes from `ba3b3185e541ad03` to `7df5034c23f3e703`.
The new golden is verified on `720eb780` (controls + literal runs + host.out) but not
on the final binary or the current on-disk binary; a formal no-fault baseline is
required.

**Propagation.** Two separate gaps must be reported honestly:
1. The frozen closure tool's generic `value_divergence` analysis reports
   `value_divergence_count=0` and therefore `FaultEffectPropagationCoverage=
   LIFECYCLE_ONLY` / `FinalClassification=LIFECYCLE_ONLY` for the B runs, even though
   the model-specific `sq01_chain` record is `COMPLETE_CHAIN` and the `verdict_elig`
   record reports all nine stages `yes`. The evidence must be quoted from
   `sq01_chain`/`verdict_elig`, not relabelled from the tool's generic field.
2. The B pilots are on binary `720eb780…`; the final baseline is on `68c6ce73…`; the
   current on-disk `build/ARM/gem5.opt` in this worktree is
   `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2` (checked with
   `sha256sum`). No evidence may be merged across these SHAs
   (`lsu_12model_closure.py --binary-sha`).

**Binary provenance.** As above: three distinct SHAs are in play. The formal rerun
must use one frozen binary and record it in every manifest.

**Controls.** One matched control per model (`C01B`), not five; add `C02B..C05B`
before claiming control parity for all contexts.

**ROI context construction.** The executed B series is five consecutive loop stores;
if the paper wants five ROI percentiles, the K*+{0,32,64,96,127} rule must be frozen
before any run, and the current B ordinals cannot be relabelled as percentiles.

**Workbook hygiene.** sheet6 W6's `ExpectedGolden` field is stale
(`7284dc0b3f6c64cf` vs the `Oracle`/`.golden` value `2543a2a60de01795`); this is a
W6 defect recorded in the SP05 file, not an SQ01 defect, but it shares the same sheet
edits.

---

## 6. Evidence not available (stated, not zeroed)

- No gem5 run was performed by this audit, by rule.
- The raw v3.2.9 SP05 `store_path` pilot directories are absent from this worktree;
  the SP05 original evidence is cited from `SP05_Implementation_v3.2.9.md`.
- The original W3 SQ01 trace cannot be re-graded by the frozen closure tool
  (`SQ01_records_v3.2.12.binary-8eb7ce8d.json` = `TRACE_INCOMPLETE`).
- The exact tick of the B reload/consumer is not printed in the model record; the
  chain is evidenced by `reload_seq`/`consumer_seq` and hash equality, and by the
  trace event_ids 5031..5037.
