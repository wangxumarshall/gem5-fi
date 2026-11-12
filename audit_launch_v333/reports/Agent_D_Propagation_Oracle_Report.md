# Agent D — Propagation CSV & Oracle Consistency Report (LSU v3.3.3)

**Auditor:** Preflight Agent D (Propagation CSV & Oracle consistency)
**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Mode:** read-only. No CSV / runner / source / Excel / gem5 / scons edit. The only file written is this report.
**Method:** every claim below was recomputed from raw artifacts with read-only Python/`gzip`/`sha256sum`; no summary table was trusted on its own.

Path abbreviations used in the tables (all resolve under the absolute worktree root):

```
F   = audit_v3_3_3/runs/<MODEL>-R<NN>-fault      (60 fault dirs; 60 matching control dirs also present)
trace   = F/trace_v31.jsonl                       (50 trace-bearing runs)
prop    = F/prop_trace.csv.gz                     (A03, RP01)
summary = F/summary.json
meta    = F/pilot_meta.json
oracle  = F/oracle.log
stdout  = F/stdout.log ; stderr = F/stderr.log
addr    = F/addrpath_injections.log               (A03)
lsq     = F/lsq_fwd_injections.log                (RP01)
```

---

## 0. Verdict

**The authoritative v3.3.3 propagation evidence is sound at the row level: 60/60 terminals are
supported by raw trace/oracle data (45 PASS, 15 QUALIFIED, 0 FAIL).** The terminal split
re-derives exactly: **SDC 43 / MASKED 12 / HANG_WATCHDOG 5**; all 60 faults inject
(`injection_count>0`), all 60 paired controls zero-inject and pass the oracle with the same
seed/ordinal.

**The file named in the brief (`.../_Final.csv`) is not, on evidence, the authoritative CSV.**
It is a lossier 14-column, older-schema regeneration: its `Activation` is the v3.3.2 tautology
`injection seq=N` (50 rows) and the global `RP01_ELIGIBLE ordinal=1` (5 RP01 rows, wrong target),
it labels all 12 MASKED rows `DIRECT_DATAFLOW_EVIDENCE`, and it blanks `pc/va/addr/lq` on 40 rows.
The current v3.3.3 generator (`tools/lsu_v333_propagation.py`, default output) writes the
**top-level** CSV, and the v3.3.3 independent acceptance treats the top-level CSV as the primary
causal table. See §5.

---

## 1. Identity, ROI, and Oracle pre-checks (all 60)

| Check | Real result |
|---|---|
| Unique identity per context | 60/60 unique `(ModelID, ContextID)`; no duplicate keys |
| `fault_model_id` / `fault_id` | 50/50 `trace_v31` injections carry `fault_model_id == ModelID` (`A01-CFG01` … `LQ04-CFG01`) and `sample_run_id == "<MODEL>-R<NN>-fault"`; A03 5/5 verified via `prop_trace a03_activation`, RP01 5/5 via `summary.model/context` |
| Context↔run-dir | 60 fault dirs + 60 control dirs; every CSV context maps 1:1 to its run dir |
| Target ordinal | `summary.ordinal` == `command.txt` `*_event_ordinal` == CSV `ROI…ordinal` for 60/60 |
| ROI arithmetic | 60/60 satisfy `N=end-start+1` and `absolute=start+ceil(p·N)-1` (all 12 models) |
| Distinctness | 5 distinct injection `dyn_inst_seq` per model, 12/12 models (SQ01/SQ03/SP05 share the same `sq_reload_v3212` seqs by design — distinctness is within-model) |
| Injection | 60/60 `injection_count>0` (A03 large bulk counts, all others 1) |
| Oracle | 43 FAIL, 12 PASS, 5 `NO_CHECKSUM` (RP01); matches `oracle.log` and `summary.oracle` |
| Controls | 60/60 control `injection_count==0`, `oracle==true`, same `seed`/`ordinal` as the fault |

Raw identity fields (pc/va/pa/lq/gen/tick) in the **top-level** CSV were compared to the raw
`trace_v31` rich fields for all 50 trace-backed rows: **0 mismatches** (e.g. A01-R01
`seq=12909;pc=400578;va=493028;pa=78028;lq=756;gen=1235;tick=15674890` all raw-backed by
`injection`/`a01_ea`/`memory_response`; LP01 full `lq_entry_id=2407…15719` not truncated).

---

## 2. 60-row PASS / QUALIFIED / FAIL table

`Verdict` is the verdict of the **top-level** CSV row against raw. `Inj/Act/Div` are the target
chain events verified in the raw trace. `C/S/R` is the commit/squash/replay/terminal witness.

### A01 (Load, addrpath) — 5 PASS
Evidence: `F/A01-R0n-fault/{trace,summary,meta,oracle}`.

| # | Ctx | Terminal | Oracle (got vs golden) | Inj→Act→Div | Consumer | C/S/R |
|---|---|---|---|---|---|---|
| 1 | R01 | SDC | FAIL `7218ee89e1894154` vs `728e604ffcec539d` | seq 12909 → `a01_ea` → `a01_ea` | `consumer_commit` seq 12911 (394 total) | `commit`, `errant_commit` |
| 2 | R02 | SDC | FAIL `047c569c9a8d8494` | seq 13424 → `a01_ea` | seq 13426 (342) | `commit`, `errant_commit` |
| 3 | R03 | SDC | FAIL `3823416f83232ff2` | seq 14572 → `a01_ea` | seq 14574 (272) | `commit`, `errant_commit` |
| 4 | R04 | SDC | FAIL `520f49e9b77baaa6` | seq 14972 → `a01_ea` | seq 14974 (220) | `commit`, `errant_commit` |
| 5 | R05 | SDC | FAIL `7ed294be594f4aa6` | seq 15128 → `a01_ea` | seq 15130 (168) | `commit`, `errant_commit` |

`register_writeback` present in all 5. The v3.3.2 SQUASHED (R02) / UNRESOLVED (R03) labels are gone;
R02 no longer squashes the target and R03 no longer emits `a01_ea_discarded` (PRE-retry exclusion
fix) — both now commit + oracle FAIL.

### A03 (AddrPath stream) — 5 QUALIFIED
Evidence: `F/A03-R0n-fault/{prop,addr,stdout,stderr,summary}`. `prop` gzip-valid (`gzip -t` OK);
`stats.txt` non-empty (256,600 B).

| # | Ctx | Terminal | Oracle | Activation / first affected | C/S/R | Qualifier |
|---|---|---|---|---|---|---|
| 6 | R01 | SDC / POST_ORACLE_SIM_HANG | FAIL `1cf7a5a9f11dab7e` vs `728e604ffcec539d` | act 1058 / first affected 1058 (seq 13204) | 51,196 `commit`, 1 `errant_commit`, watchdog tick 400,958,635 | no per-consumer record **as claimed** is false (422 consumer rows exist) |
| 7 | R02 | SDC / POST_ORACLE_SIM_HANG | FAIL `d48b947fc08d5a75` | 1094 / 1094 (seq 13718) | 51,211 `commit`, watchdog 401,170,385 | 335 consumer rows |
| 8 | R03 | SDC / POST_ORACLE_SIM_HANG | FAIL `bfccf156021968dd` | **act 1131 / first affected 1150** (seq 14594) | 51,243 `commit`, watchdog 401,461,060 | 308 consumer rows; act≠div is raw-backed (raw lifecycle states both) |
| 9 | R04 | SDC / POST_ORACLE_SIM_HANG | FAIL `e413c2be501846bc` | 1168 / 1168 (seq 14930) | 51,249 `commit`, watchdog 401,576,175 | 263 consumer rows |
| 10 | R05 | SDC / POST_ORACLE_SIM_HANG | FAIL `d5529b13a7c739dc` | 1204 / 1204 (seq 15146) | 51,238 `commit`, watchdog 401,626,995 | 173 consumer rows |

QUALIFIED because (a) the top-level CSV `Consumer` says "n/a (persistent stream; no per-consumer
record)" although `prop` contains 173–422 `consumer` rows per run with seq/pc/`consumer_input_fnv`,
and (b) all five runs exit 1 via `NotImplementedError: Exit event 'CHAOS_A03_WATCHDOG_EXPIRED' not
implemented` (`stderr`). The SDC oracle verdict itself is fully raw-supported.

### FW02 (L1D forward) — 5 PASS
Evidence: `F/FW02-R0n-fault/{trace,summary,meta,oracle}`.

| # | Ctx | Terminal | Oracle | Act/Div | Consumer | C/S/R |
|---|---|---|---|---|---|---|
| 11 | R01 | SDC | FAIL `676dff1818cbded5` vs `1f4cbf14327717df` | `fw02_decision` seq 12243 | seq 12244 (332) | commit |
| 12 | R02 | SDC | FAIL `29b16643211339f1` | seq 12479 | seq 12480 (308) | commit |
| 13 | R03 | MASKED | PASS `1f4cbf14327717df` | seq 12587; `normal_decision=forwarded;fault_decision=suppressed;replay_count=0` | seq 12588 (284) | commit |
| 14 | R04 | SDC | FAIL `5f1fdfa8a4f1fd1f` | seq 13344 | seq 13345 (250) | commit |
| 15 | R05 | SDC | FAIL `c1474304e3fb580f` | seq 13572 | seq 13573 (222) | commit |

R03 mechanism `SUPPRESSED_FORWARD_NORMAL_VALUE` verified in raw `fw02_decision`; oracle PASS.

### FW05 (forwarding) — 5 PASS
Evidence: `F/FW05-R0n-fault/{trace,summary,meta,oracle}`.

| # | Ctx | Terminal | Oracle | Act/Div | Consumer | C/S/R |
|---|---|---|---|---|---|---|
| 16 | R01 | SDC | FAIL `549c9e0347adad9f` vs `67afad307642983e` | `register_writeback` seq 16084 | seq 16085 (1803) | commit |
| 17 | R02 | SDC | FAIL `549c9e0347ada27f` | seq 23684 | seq 23685 (1403) | commit |
| 18 | R03 | SDC | FAIL `549c9e0347ada75f` | seq 31284 | seq 31285 (1003) | commit |
| 19 | R04 | SDC | FAIL `549c9e0347ada43f` | seq 38884 | seq 38885 (603) | commit |
| 20 | R05 | SDC | FAIL `549c9e0347adb91f` | seq 46484 | seq 46485 (203) | commit |

`pa=n/a` in the CSV is honest (the forward path emits no `memory_response` PA); `va` is raw-backed
(`load_addr`/`true_addr`).

### SQ01 (store-data) — 5 PASS
Evidence: `F/SQ01-R0n-fault/{trace,summary,meta,oracle}`.

| # | Ctx | Terminal | Oracle | Act/Div | Consumer | C/S/R |
|---|---|---|---|---|---|---|
| 21 | R01 | SDC | FAIL `7927a4e45a3271dc` vs `7df5034c23f3e703` | `store_writeback` seq 13328 | `errant_commit` seq 13330 (2039 consumer_commit) | commit |
| 22 | R02 | SDC | FAIL `580f7a29038389ac` | seq 15122 | seq 15124 (1597) | commit |
| 23 | R03 | SDC | FAIL `a372640bc071881c` | seq 16847 | seq 16849 (1172) | commit |
| 24 | R04 | SDC | FAIL `406db02f8dc2912c` | seq 18641 | seq 18643 (730) | commit |
| 25 | R05 | SDC | FAIL `1aea82f645a9ac9c` | seq 20435 | seq 20437 (288) | commit |

### SQ03 (store visibility) — 5 PASS
Evidence: `F/SQ03-R0n-fault/{trace,summary,meta,oracle}`.

| # | Ctx | Terminal | Oracle | Mechanism (raw `sq03_effect`) | Consumer |
|---|---|---|---|---|---|
| 26 | R01 | MASKED | PASS `7df5034c23f3e703` | `CHAIN_VISIBILITY_MOVED` / `DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER`; `visible_before_commit=1` | `errant_commit` seq 13330 (1883) |
| 27 | R02 | MASKED | PASS | `LIFECYCLE_ONLY` / `NO_DOWNSTREAM_EFFECT`; `visible_before_commit=0` | seq 15124 (1467) |
| 28 | R03 | MASKED | PASS | `CHAIN_VISIBILITY_MOVED`; reload hash `fde383c67ac034f1` | seq 16849 (1067) |
| 29 | R04 | MASKED | PASS | `CHAIN_VISIBILITY_MOVED`; reload hash `aa2be3d3d60e3c9d` | seq 18643 (651) |
| 30 | R05 | MASKED | PASS | `CHAIN_VISIBILITY_MOVED`; reload hash `c7d78aff5e06edf9` | seq 20437 (235) |

All five have `commit` for the store; oracle PASS. `VISIBILITY_TIMING_SHIFT` is the correct label
(not SDC); R02 is the only `LIFECYCLE_ONLY` case.

### SP05 (premature store complete) — 5 QUALIFIED
Evidence: `F/SP05-R0n-fault/{trace,summary,meta,oracle}`.

| # | Ctx | Terminal | Oracle | Act/Div | Consumer | C/S/R |
|---|---|---|---|---|---|---|
| 31 | R01 | SDC | FAIL `c7a1b3a591c68328` vs `7df5034c23f3e703` | `sp05_complete` seq 13328 | `errant_commit` seq 13330 | **no_commit_or_squash** |
| 32 | R02 | SDC | FAIL `34890178967da568` | seq 15122 | seq 15124 | no_commit_or_squash |
| 33 | R03 | SDC | FAIL `225c6839dd319a5c` | seq 16847 | seq 16849 | no_commit_or_squash |
| 34 | R04 | SDC | FAIL `d42d86ee46895884` | seq 18641 | seq 18643 | no_commit_or_squash |
| 35 | R05 | SDC | FAIL `c6e1c98b1480efd4` | seq 20435 | seq 20437 | no_commit_or_squash |

`sp05_stage` carries real binding: `store_data_fnv=b6180e0c195fd2e9` (R01; non-null, v3.3.3 fix),
`data_correct=0`, `write_skipped=1`, `stage_outcome=CHAIN_VISIBILITY_LOST`. SDC is supported by
store-data mismatch + oracle FAIL. QUALIFIED because there is **no `commit`/`squash`/replay node for
the target store** (the 60/60 "commit/squash/hang" phrasing overstates SP05).

### DA04 (byte-enable) — 5 PASS
Evidence: `F/DA04-R0n-fault/{trace,summary,meta,oracle}`.

| # | Ctx | Terminal | Oracle | Act/Div | Consumer | C/S/R |
|---|---|---|---|---|---|---|
| 36 | R01 | SDC | FAIL `3e59e830cae2994d` vs `3f89eab79392ce69` | `store_writeback` seq 14320 | `errant_commit` seq 19698 | commit |
| 37 | R02 | SDC | FAIL `0662cfc41d9f69c5` | seq 15345 | seq 20723 | commit |
| 38 | R03 | SDC | FAIL `438883f08de29ebd` | seq 16365 | seq 21743 | commit |
| 39 | R04 | SDC | FAIL `b3509db52b9c9bb1` | seq 17390 | seq 22768 | commit |
| 40 | R05 | SDC | FAIL `ceb55fc389a4e601` | seq 18415 | seq 23793 | commit |

### LP01 (L1D byte) — 5 PASS
Evidence: `F/LP01-R0n-fault/{trace,summary,meta,oracle}`.

| # | Ctx | Terminal | Oracle | Act/Div | Consumer | C/S/R |
|---|---|---|---|---|---|---|
| 41 | R01 | SDC | FAIL `45692737702410c6` vs `99c106541150be0e` | `memory_response` seq 34741 | seq 34743 (29956) | commit |
| 42 | R02 | SDC | FAIL `2403e0e3d8fa2df6` | seq 54709 | seq 54711 (23300) | commit |
| 43 | R03 | SDC | FAIL `a1438ad1e689f106` | seq 74677 | seq 74679 (16644) | commit |
| 44 | R04 | SDC | FAIL `1d4bc99bd20fe5d6` | seq 94645 | seq 94647 (9988) | commit |
| 45 | R05 | SDC | FAIL `3eef05b0e0f2d1f6` | seq 114613 | seq 114615 (3332) | commit |

### MD04 (dependency violation) — 5 PASS
Evidence: `F/MD04-R0n-fault/{trace,summary,meta,oracle}`.

| # | Ctx | Terminal | Oracle | Act/Div | Consumer | C/S/R |
|---|---|---|---|---|---|---|
| 46 | R01 | MASKED | PASS `22be5ae3364d0c9f` | `register_writeback` seq 125104; injection `load_complete=1;data_modified=0` | seq 125105 (6643) | commit |
| 47 | R02 | SDC | FAIL `b828f386364d0c9f` | seq 141725 | seq 141727 (5107) | commit |
| 48 | R03 | SDC | FAIL `52ad1266adaca05a` | seq 147152 | seq 147153 (4599) | commit |
| 49 | R04 | SDC | FAIL `ace925b2aa5f41e2` | seq 171530 | seq 171531 (2555) | commit |
| 50 | R05 | SDC | FAIL `e92c4d2296d3e7ca` | seq 188215 | seq 188216 (1025) | commit |

R01 `INERT_AFTER_COMPLETION` is backed by raw `load_complete=1; address_modified=0; data_modified=0`
(note: `data_modified=0` is a log literal per the prior D-18 finding; the completion-before-fault
timing is real).

### LQ04 (LQ lifetime) — 5 PASS
Evidence: `F/LQ04-R0n-fault/{trace,summary,meta,oracle}`.

| # | Ctx | Terminal | Oracle | Mechanism (raw) | Consumer | C/S/R |
|---|---|---|---|---|---|---|
| 51 | R01 | MASKED | PASS `b097eb83f71545cb` | `valid 1→0; request 1→0; data_unchanged=1; no_pop=1; no_reuse=1`; `lq_lifecycle action=restore` | seq 8 (326) | commit + restore |
| 52 | R02 | MASKED | PASS | same pattern, lq=2 | seq 9 (327) | commit + restore |
| 53 | R03 | MASKED | PASS | lq=3 | seq 10 (326) | commit + restore |
| 54 | R04 | MASKED | PASS | lq=4 | seq 11 (326) | commit + restore |
| 55 | R05 | MASKED | PASS | lq=5 | seq 12 (327) | commit + restore |

`ENTRY_INVALIDATED_RESTORED` verified in raw injection + `register_writeback` (`data_unchanged=1`)
+ `lq_lifecycle action=restore`.

### RP01 (skip-replay watchdog) — 5 QUALIFIED
Evidence: `F/RP01-R0n-fault/{summary,stderr,lsq,prop}`.

| # | Ctx | Terminal | Oracle | Target `RP01_SKIP_REPLAY` | Watchdog fatal (`stderr`) | C/S/R |
|---|---|---|---|---|---|---|
| 56 | R01 | HANG_WATCHDOG | NO_CHECKSUM | ordinal 26, load_seq 16293, tick 16,967,335 | `CHAOS_RP01_WATCHDOG_EXPIRED tick=7700000000 injected=1 eligible=26` | watchdog_expired |
| 57 | R02 | HANG_WATCHDOG | NO_CHECKSUM | ordinal 77, load_seq 23229 | … eligible=77 | watchdog_expired |
| 58 | R03 | HANG_WATCHDOG | NO_CHECKSUM | ordinal 128, load_seq 30165 | … eligible=128 | watchdog_expired |
| 59 | R04 | HANG_WATCHDOG | NO_CHECKSUM | ordinal 179, load_seq 37101 | … eligible=179 | watchdog_expired |
| 60 | R05 | HANG_WATCHDOG | NO_CHECKSUM | ordinal 230, load_seq 44037 | … eligible=230 | watchdog_expired |

The top-level CSV `CommitSquashReplay` reproduces the `stderr` fatal line verbatim; `Activation`
is the target skip (ordinal 26/77/128/179/230), not the baseline `RP01_ELIGIBLE ordinal=1`.
QUALIFIED: no `trace_v31.jsonl`, `prop` is gzip-truncated (`unexpected end of file`, all 5),
`stats.txt` 0 B; `PARTIAL_WATCHDOG` is honest. `summary.json` records
`terminal=HANG_WATCHDOG / INTERNAL_WATCHDOG_DEADLINE` (v3.3.3 fix).

---

## 3. Terminal distribution, MASKED mechanisms, A03, A01/A03 register-writeback, RP01

### 3.1 Terminal distribution — re-derived exactly
From `summary.json` over all 60 fault runs: `Counter({SDC: 43, MASKED: 12, HANG_WATCHDOG: 5})`.
The top-level CSV gives the same split; the `_Final.csv` also gives 43/12/5. Per model:
A01 5 SDC; A03 5 SDC; FW02 4 SDC + R03 MASKED; FW05 5 SDC; SQ01 5 SDC; SQ03 5 MASKED;
SP05 5 SDC; DA04 5 SDC; LP01 5 SDC; MD04 R01 MASKED + 4 SDC; LQ04 5 MASKED; RP01 5 HANG.
Oracle: 43 FAIL, 12 PASS, 5 `NO_CHECKSUM`.

### 3.2 MASKED mechanisms — 12/12 raw-backed
- **FW02-R03:** `fw02_decision normal_decision=forwarded; fault_decision=suppressed; replay_count=0`; oracle PASS.
- **SQ03-R01/R03/R04/R05:** `sq03_effect effect_outcome=CHAIN_VISIBILITY_MOVED; effect_reason=DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER`; `visible_before_commit=1`; reload consumer reads post-store data; oracle PASS.
- **SQ03-R02:** `effect_outcome=LIFECYCLE_ONLY; effect_reason=NO_DOWNSTREAM_EFFECT`; `visible_before_commit=0`.
- **MD04-R01:** `injection load_complete=1; address_modified=0; data_modified=0`; oracle PASS → inert-after-completion.
- **LQ04-R01–R05:** injection `valid 1→0; request 1→0; data_unchanged=1; no_pop=1; no_reuse=1`; `register_writeback data_unchanged=1`; `lq_lifecycle action=restore reason=commit`; oracle PASS.

### 3.3 A03 SDC/POST_ORACLE_SIM_HANG
Each A03 `stdout.log` ends with a bare 16-hex final checksum (R01 `1cf7a5a9f11dab7e`, R02
`d48b947fc08d5a75`, R03 `bfccf156021968dd`, R04 `e413c2be501846bc`, R05 `d5529b13a7c739dc`), all ≠
golden `728e604ffcec539d`, plus `A03_WATCHDOG_EXPIRED` (tick 400,958,635 / 401,170,385 /
401,461,060 / 401,576,175 / 401,626,995). `prop_trace.csv.gz` is gzip-valid and carries a direct
chain per stream: `a03_activation` ×1, `inj`/`addr_form`/`mem_req`/`resp`/`taint_reg`/`commit`
≈51k each, `consumer` 173–422, `errant_commit` ×1. So A03 is **SDC, not HANG** — the
`SDC / POST_ORACLE_SIM_HANG` label is correct.

### 3.4 A01 / A03 register-writeback
- **A01:** exactly one `register_writeback` event in every R01–R05 `trace_v31` (e.g. R01
  `writeback_value=5b05b05b05b15ab`, `value_matches_payload=1`) plus `a01_consumed` naming the
  consumer seq.
- **A03:** the prop trace's register-writeback node is `kind=taint_reg` (51,196–51,249 rows per
  context) with `writeback_value`/`writeback_value_fnv`/`source_value_hash`. It is not named
  `register_writeback`, but it is the register writeback evidence.

### 3.5 RP01 watchdog
All five `stderr.log` contain a fatal
`src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:627: fatal: CHAOS_RP01_WATCHDOG_EXPIRED tick=7700000000 injected=1 eligible=N`;
`lsq_fwd_injections.log` ends with `CHAOS_RP01_WATCHDOG=EXPIRED fired=1 injected=1 eligible=N tick=7700000000`
and contains the target `RP01_SKIP_REPLAY ordinal=N` line. `summary.rp01` records
`watchdog=true, checksum=null, terminal=HANG_WATCHDOG`. Raw-supported.

---

## 4. Defect ledger

### 4.1 Defects in the named `_Final.csv` (all rows metadata; verdicts unaffected)

| ID | Sev | Defect | Evidence | Root cause | Affected |
|---|---|---|---|---|---|
| DF-01 | **HIGH** | `Activation` is the tautology `injection seq=N` (50 rows); for RP01 it is the global `RP01_ELIGIBLE ordinal=1 …` (identical in all 5 contexts), not the target skip ordinal | raw `summary.rp01.first_eligible` vs `first_skip`; raw trace activation events | older v3.3.2 report schema (`tools/lsu_v332_report.py`-style); the v3.3.3 tool docstring says it replaces this tautology, but writes the top-level CSV | 50 non-A03/RP01 + RP01 ×5 |
| DF-02 | **HIGH** | all 12 MASKED rows labelled `EvidenceClass=DIRECT_DATAFLOW_EVIDENCE`; non-standard `A03=SDC_ORACLE_FAIL`, `RP01=DIRECT_SKIP_AND_WATCHDOG` | top-level CSV uses `MASKING_EVIDENCE` ×12, `DIRECT_DATAFLOW_EVIDENCE` ×43, `TERMINAL_WITNESS_EVIDENCE` ×5 | enum drift vs `tools/lsu_v333_propagation.evidence_class()` | 12 MASKED + 10 A03/RP01 |
| DF-03 | **MEDIUM** | blank/stale identity: `va=None` (A01/FW05/SQ01/SQ03/SP05/DA04/MD04/LQ04), `addr=None` (FW05/SP05), `pc=None` (SP05), `lq=None` (SQ01/SQ03/SP05) | raw trace has real va/pa/pc; top-level CSV carries them | old identity extractor reads only `addr`/`pa`; does not read `request_va`/`vaddr`/`load_addr`/`store_addr` | 40 rows |
| DF-04 | **MEDIUM** | `CommitSquashReplay="no"` on 50 rows (including rows with a real `commit`), `n/a` on A03/RP01 (10 rows); SQ01/SQ03 show `Downstream=commit` with `CommitSquashReplay=no` (self-contradiction); no replay/squash detail | raw `commit`/`errant_commit` events | old schema | 50 + 10 |
| DF-05 | **LOW** | A03 `Injection` = `A03_ACTIVATION` (arming record), not the `A03_STREAM` affected event; `TerminalReason` drops checksum/golden/`POST_ORACLE_SIM_HANG` | raw `addr`/`stdout` | old A03 branch | A03 ×5 |
| DF-06 | **LOW** | SP05 `Downstream=n/a` although `errant_commit seq=13330` exists; A01/FW02 `Downstream` collapses `errant_commit`/consumer fan-out | raw trace | old chain scoping | SP05 ×5, others |
| DF-07 | **MEDIUM** | The named file is not the output of the current v3.3.3 generator; the top-level CSV is | `tools/lsu_v333_propagation.py` `default_out()`; timestamps (Final 12:05, top-level 12:25); independent acceptance treats top-level as primary | packaging/version skew | whole file |

### 4.2 Defects in the authoritative top-level CSV (verdicts unaffected)

| ID | Sev | Defect | Evidence | Root cause | Affected |
|---|---|---|---|---|---|
| DM-01 | **MEDIUM** | A03 `Consumer` = "n/a (persistent stream; no per-consumer record)" is **false**: the prop trace has 173–422 `consumer` rows with seq/pc/`consumer_input_fnv`/`commit_seq` | `prop` kind counter; sample consumer rows | `a03_row()` hard-codes the string | A03 ×5 |
| DM-02 | **MEDIUM** | A03 runs exit 1 via `NotImplementedError: Exit event 'CHAOS_A03_WATCHDOG_EXPIRED' not implemented` (stderr); "terminates cleanly" in the acceptance report is inaccurate | `F/A03-*/stderr.log`, `summary.exit_code=1` | exit event not registered in `configs/se/lsu_proxy.py` | A03 ×5 |
| DM-03 | **LOW** | RP01 `prop_trace.csv.gz` is gzip-truncated (`unexpected end of file`) in all 5; `stats.txt` 0 B | `gzip -t` | fatal abort mid-flush | RP01 ×5 |
| DM-04 | **LOW** | SP05 has no commit/squash/replay node for the target (CSV honestly says `no_commit_or_squash`); the "60/60 commit/squash/hang" claim overstates SP05 | `trace` event kinds | SP05 hook runs at premature-complete and emits no store commit node | SP05 ×5 |
| DM-05 | **LOW (doc)** | Acceptance report §1 says A03 watchdog tick 400,963,640; raw stdout is 400,958,635 (R01), and the same report's F-06 row says 400,958,635 | `stdout`, report lines 27/147 | stale prose number | report §1 |
| DM-06 | **LOW** | `ApplicationOracle=NO_CHECKSUM` (CSV/readiness) vs `summary.oracle=false` and `oracle.log` "ORACLE_FAIL: no checksum line" | raw | semantic choice; honest but inconsistent across artifacts | RP01 ×5 |
| DM-07 | **LOW** | A03-R03 `Activation ordinal=1131` vs `FirstDivergence event_ordinal=1150` is not explained; both are raw-backed (`activation_ordinal` vs `first_affected_ordinal`, the 1131 event was `affected=0/ALREADY_STUCK`) | `summary.a03.lifecycle`; `prop` a03_stream row ordinal 1131 | no field distinguishes "arming ordinal" from "first affected ordinal" | A03-R03 |
| DM-08 | **LOW** | A03 `Downstream stream_injected=n/a` although `summary.a03.injected_applications=51310` / FUNNEL has the count | summary | generator reads `a03.injections`, key absent (it is `injected_applications`) | A03 ×5 |

No row's **terminal verdict** (SDC/MASKED/HANG) is contradicted by raw data in either CSV.

---

## 5. Authoritative propagation CSV — recommendation and archive list

### 5.1 Recommendation (single authoritative file)

**`audit_v3_3_3/LSU_60Context_Causal_Propagation.csv`** (SHA256
`4e53b424fb9f62ed86e160f958499903005a3baabe4b58124a96ee3a27371e1b`, 60 rows, 16 columns).

It is the only file generated by the current v3.3.3 tool
(`tools/lsu_v333_propagation.py → default_out()` when `--runs audit_v3_3_3/runs`), it is the newer
artifact (mtime 12:25 vs 12:05), it carries injection/activation/divergence/consumer/commit as
separate chain-scoped fields, and its identity fields matched raw 0/50 mismatches. The v3.3.3
independent acceptance (`LSU_Independent_Acceptance.md`) also treats this top-level CSV as the
primary causal table (`+ propagation/…_Final.csv` as a parenthetical add-on).

**Conflict with the brief, stated honestly:** the brief names
`LSU_60Context_Causal_Propagation_Final.csv` as authoritative. On evidence that file cannot be
authoritative as it stands (DF-01…DF-07). If the `_Final.csv` filename is contractually required,
it must be **regenerated from the top-level schema/tool** and the RP01 Activation / MASKED
`EvidenceClass` / blank-identity defects fixed first; otherwise it should be marked
`ARCHIVED / SUPERSEDED`, not authoritative. I do not recommend keeping two "authoritative" tables.

### 5.2 Archived versions (do not modify)

| Path | SHA256 | Status |
|---|---|---|
| `audit_v3_3_3/propagation/LSU_60Context_Causal_Propagation_Final.csv` | `c824f36febd3ceec202b2d68a8ffd9b4856b0f548afcfd267a55d432ada404b0` | ARCHIVED / SUPERSEDED (old schema, DF-01…07) |
| `audit_v3_3_2/propagation/LSU_60Context_Causal_Propagation_Final.csv` | `b98eeed3f4b14b431151f8f0843a69ca8cf3c52dec95f139f9328feb6661f548` | ARCHIVED (v3.3.2; stale A01 ordinals 1059…) |
| `audit_v3_3_2/pkg/propagation/LSU_60Context_Causal_Propagation_Final.csv` | `b98eeed3f4b14b431151f8f0843a69ca8cf3c52dec95f139f9328feb6661f548` | ARCHIVED (byte-identical duplicate of above) |
| `audit_v3_3_1/propagation/LSU_60Context_Causal_Chain_Reaudit.csv` | `b924f179d98573061cd5498d880c000d813578eba5d947ae4b33abb99c16c32f` | ARCHIVED (v3.3.1, 19-col re-audit) |
| `audit_v3_3_1/v33_package/B_Audits/LSU_Propagation_Closure_Final.csv` | `7903a4f6946115b9e7f81b820e17ea7eacbe8515f1235bab74191d24b33cc269` | ARCHIVED (pre-formal v3.3, 30-col) |
| `docs/gem5-fi/lsu/implementation_v3_2/preformal_v3_3/LSU_Propagation_Closure_Final.csv` | `7903a4f6946115b9e7f81b820e17ea7eacbe8515f1235bab74191d24b33cc269` | ARCHIVED (byte-identical duplicate) |

The top-level authorititative file for reference:
`audit_v3_3_3/LSU_60Context_Causal_Propagation.csv` = `4e53b424…` (60 rows, 16 cols).

---

## 6. Rows with unsupported verdict / stale-blank fields

- **Unsupported verdict:** none. All 60 terminal verdicts are raw-supported.
- **Stale/blank fields (top-level CSV):** A03 `Consumer` false n/a (DM-01, 5 rows); A03
  `stream_injected=n/a` (DM-08, 5 rows); A03-R03 activation/divergence ordinals unexplained
  (DM-07, 1 row).
- **Stale/blank fields (`_Final.csv`):** RP01 `Activation` wrong (DF-01, 5 rows); 40 rows with
  `va=None`/`addr=None`/`pc=None`/`lq=None` (DF-03); 49 rows `CommitSquashReplay=no` (DF-04);
  12 MASKED rows over-classified (DF-02); 5 A03 rows `Injection` mislabeled (DF-05); 5 SP05 rows
  `Downstream=n/a` (DF-06).
- **Cross-artifact inconsistency:** RP01 `NO_CHECKSUM` vs `summary.oracle=false` (DM-06, 5 rows);
  acceptance-report A03 watchdog tick 400,963,640 vs raw 400,958,635 (DM-05, doc).

---

## 7. Could not verify

1. **A03's full architectural path from the first affected load to the final checksum** — the
   `prop_trace` is a sampled stream trace (51k stream rows / 672k total), not a per-instruction
   architectural history; the first-load chain and the checksum FAIL are verified, the full
   end-to-end path is not reconstructable from the retained trace.
2. **A03 clean termination** — the run exits through an unimplemented gem5 exit event
   (`NotImplementedError`), so "clean in-simulator watchdog exit" cannot be confirmed; only the
   watchdog marker + checksum are verifiable.
3. **RP01 trace contents** — `prop_trace.csv.gz` is gzip-truncated in all 5, so the trace cannot be
   fully parsed; the HANG_WATCHDOG verdict rests on `stderr`/`lsq_fwd_injections.log`/`summary`.
4. **SP05 value-level correctness of the store** — `store_data_fnv` is present (v3.3.3 fix) and
   `data_correct=0`, but there is no store `commit`/writeback node and no golden read of the same
   address, so the SDC is oracle-level plus store-data-mismatch, not a fault-vs-control value diff.
5. **RP01 true deadlock** — a fixed 20M-cycle deadline proves non-completion; there is no
   progress-reset counter, so "hang" is inferred no-forward-progress.
6. **A01 R01/R04/R05 golden counterfactual** — no `a01_golden_resp` read of the faulted address in
   those runs; SDC rests on the independent application-oracle FAIL.
7. **Control-level value equality for MASKED mechanisms** — FW02-R03 / SQ03 / LQ04 mechanisms are
   verified inside the fault run (oracle PASS + mechanism fields); control traces do not carry the
   same value records for a paired value diff.

---

## 8. Bottom line

- **Row verdicts: 45 PASS, 15 QUALIFIED (A03 ×5, SP05 ×5, RP01 ×5), 0 FAIL.**
- **Terminal split re-derives exactly: SDC 43 / MASKED 12 / HANG_WATCHDOG 5.** MASKED mechanisms
  12/12 raw-backed; RP01 watchdog 5/5 raw-backed; A03 SDC/POST_ORACLE_SIM_HANG 5/5 raw-backed;
  A01 and A03 register-writeback verified (A03 as `taint_reg`).
- **The authoritative propagation artifact is the top-level
  `audit_v3_3_3/LSU_60Context_Causal_Propagation.csv`; the `_Final.csv` named in the brief is a
  lossy older-schema file with concrete defects and should be archived/superseded (or regenerated)
  before it can be called authoritative.**
- No CSV verdict is fabricated or contradicted by raw data; the defects are field/schema/provenance
  defects, plus one real evidence-citation gap (A03 `Consumer` falsely `n/a`) and two terminal-
  cleanliness issues (A03 `NotImplementedError` exit, RP01 truncated gzip).
