# SQ ordinal eligibility preflight — LSU v3.2.12 (SQ01 / SQ03 / SP05 re-selection)

**Round:** LSU v3.2.12 propagation closure — SQ ordinal re-selection before the
eligible-ordinal reruns (`SUPP-{SQ01,SQ03,SP05}-R01B..R05B` + `C01B`).
**Executor worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` (HEAD `e1b236c6`).
**Date:** 2026-11-10. Binary `build/ARM/gem5.opt` SHA
`720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070` (unchanged across
all probes/pilots — asserted before the batch and uniform in all 18 pilot manifests).
Workload `workloads/sq_reload_v3212` SHA
`bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6`, oracle
`7df5034c23f3e703`.

This preflight implements the re-selection method prescribed by
`FW02_SQ01_SQ03_SP05_Evidence_Audit_v3.2.12.md` §2.2, which found that the original
ordinals 1–5 select C-runtime startup stores on `sq_reload_v3212` (structural
`STORE_COMMITTED_LANE_NOT_READ`), never the workload's reload-consumed buffer.

---

## 1. The predetermined selection rule (frozen before any fault run)

> **Rule:** the eligible ordinal K\* is the FIRST ordinal whose ordinal-selected
> store's virtual address lies inside the workload's reload-consumed buffer
> range, `[buf, buf+0x800)` = **[0x491990, 0x492190)**, as measured by a census
> probe with the model's own ordinal machinery. The criterion is **address
> eligibility only** — never an SDC/terminal/verdict outcome. If a re-selected
> ordinal still yields no reload consumer, the run records that honestly.

Facts frozen before probing (no outcome input):

- `buf = 0x491990`, size 2048 (`readelf -sW sq_reload_v3212`:
  `56: 0000000000491990 2048 OBJECT LOCAL DEFAULT 20 buf`), i.e. the range is
  `[0x491990, 0x492190)`.
- Every `buf[i] = v` store is followed by a same-address reload `buf[i]` after
  `dmb ish` (`sq_reload_v3212.c:41-52`) — a guaranteed reload consumer for any
  in-range selected store.
- F0-tier ordinal semantics make any ordinal reachable: with `event_ordinal`
  set, `next_fire = warmup_events + event_ordinal` and `--lsqfwd_span_events` is
  inert (`chaos_lsu_trigger.hh:167-179`; verified by reading the trigger source
  before the first probe).

**Probe method** (census artifact, never a graded sample): one
`platform/run_pilot.py` invocation per candidate ordinal K per model,
`--pilot-id PROBE-<MODEL>-K<K>`, scratch outdir under `/tmp/sq_ordinal_probe`
(never under `pilots_v3_2_12/`), context 1 with the original R01 seed carried,
`--event-ordinal K`, absolute workload path. The selected store's vaddr is read
from the probe's own model record **before any classification is consulted**:
`sq01_chain` / `sq03_effect` / `sp05_stage` record's `new_value` field (the
selected store's vaddr) in `trace_v31.jsonl`, cross-checked against the
injection log line (`lsq_fwd_injections.log` gives `store_seq`). Probes are not
graded, their oracles are ignored, and their terminals/outcomes played no role
in the selection.

## 2. Finding: the three models have DIFFERENT ordinal spaces, one shared store stream

The audit §2.2 anticipated per-model census ("with the model's own ordinal
machinery"). The census confirms the three streams **diverge** at depth — they
count different eligible-event populations over the same dynamic store stream:

| model | eligible stream (source-audited) | pre-loop events | loop-entry ordinal |
|---|---|---|---|
| SQ01 | `lsq_write_sq_entry` store writes passing the `lsq_unit.cc:2119-2125` guard, **plus** the base `store->load_forward` matches that share the same F0 `lsuTrigger` (`CHAOSLSQFwd.cc:941-947` and `:346-351`) | 1005 | **K\* = 1006** |
| SQ03 | every store reaching `maybeSetCanWB` (executeStore), ordinal via `eligible_count == f6_event_ordinal` (`CHAOSLSQFwd.cc:740-745`) | 1008 | **K\* = 1009** |
| SP05 | every `commitStores` store passing `chaos_sp05::isSelectable`, ordinal via `shouldSelect` (`CHAOSLSQFwd.cc:540-546`) — squashed-before-commit stores never count | 939 | **K\* = 940** |

All three streams enter the workload loop at the **same dynamic store** —
`store_seq 12108` = `buf[0]` @ `0x491990` — so the pilot windows are aligned on
the same five workload stores even though the ordinals differ:

- **SQ01:** R01B..R05B = ordinals **1006..1010** → buf[0..4] (`0x491990`,
  `0x491998`, `0x4919a0`, `0x4919a8`, `0x4919b0`)
- **SQ03:** R01B..R05B = ordinals **1009..1013** → buf[0..4] (same addresses)
- **SP05:** R01B..R05B = ordinals **940..944** → buf[0..4] (same addresses)

Boundary evidence (all from census probes, address-only):

| model | last non-buf ordinal (probe evidence) | first in-range ordinal |
|---|---|---|
| SQ01 | K=1005 → `0x7ffffefbe8` (store_seq 12097, stack) | K=1006 → `0x491990` (buf[0]) |
| SQ03 | K=1008 → `0x7ffffefbe8` (store_seq 12097); also 1006→`0x7ffffefce0`, 1007→`0x7ffffefbe0` | K=1009 → `0x491990` |
| SP05 | K=939 → store_seq 12097 (same store as above; the SP05 premature-completion probe of it crashed gem5 — see §4), address cross-bound by the SQ01 census probe of the identical seq | K=940 → `0x491990` |

Because `buf[0]` is by construction the first store the workload makes inside
`buf`, and each boundary probe shows a non-buf store immediately before it,
these K\* are the first eligible ordinals — the rule's stopping points.

## 3. Census evidence (99 probes, all census artifacts)

The probes ran 2026-11-10 in `/tmp/sq_ordinal_probe/PROBE-<MODEL>-K<K>` (scratch
tmpfs; the tables below are the durable record). K=1..5 were already known from
the v3.2.12 audit (ordinals 1–5 → `0x7ffffefd00..20`, startup stack); the
scan continued from K=6.

### 3.1 SQ01 linear census K=6..60 — all C-runtime startup / stdio / printf-lane stores

| K | store_seq | vaddr | region (readelf) | record verdict |
|---|---|---|---|---|
| 6 | 29 | 0x7ffffefd28 | stack (startup) | STORE_COMMITTED_LANE_NOT_READ |
| 7 | 33 | 0x48ee58 | `__libc_stack_end` | COMPLETE_CHAIN (reloaded later by libc) |
| 8–13 | 35–42 | 0x7ffffefd30..58 | stack (startup) | STORE_COMMITTED_LANE_NOT_READ |
| 14 | 44 | 0x7ffffefd60 | stack | COMPLETE_CHAIN |
| 15 | 45 | 0x7ffffefd68 | stack | COMPLETE_CHAIN (probe run crashed post-injection — census artifact) |
| 16 | 47 | 0x496e90 | `__environ` | COMPLETE_CHAIN |
| 17–20 | 61–70 | 0x7ffffefb40..58 | stack | PARTIAL_HASH_MISMATCH |
| 21 | 73 | 0x496ed8 | `_dl_auxv` | STORE_COMMITTED_LANE_NOT_READ |
| 22–29 | 133–147 | 0x7ffffefb60..98 | stack (stdio) | mostly STORE_COMMITTED_LANE_NOT_READ (K=25: PARTIAL_RELOAD_NOT_CONSUMED) |
| 30–39 | 152–229 | 0x7ffffefcc0..f8 | stack (stdio) | mixed; K=38 PARTIAL_RELOAD_NOT_CONSUMED, K=39 COMPLETE_CHAIN |
| 40, 41 | — | — | **forwarding matches, not store writes** | NO_RECORD (see §4) |
| 42 | 234 | 0x7ffffefbe0 | stack | STORE_COMMITTED_LANE_NOT_READ |
| 43–54 | 246–268 | 0x4909a0..0x496f00 | loader bss (`_dl_pagesize`…`_dl_phnum`), `__libc_enable_secure` | PARTIAL_NO_DRAIN |
| 55–58 | 274–376 | 0x7ffffefc30..28 | stack (reloaded) | COMPLETE_CHAIN |
| 59, 60 | 388–389 | 0x4909a0/a8 | `_dl_pagesize`, `_dl_minsigstacksize` | PARTIAL_NO_DRAIN |

None in `[0x491990,0x492190)` — the first 60 SQ01-eligible events are all
C-runtime stores (the static-glibc startup sequence is ~1000 eligible events
long on this workload).

### 3.2 SQ01 bracket probes and descent to K\*

| K | store_seq | vaddr | note |
|---|---|---|---|
| 100 | 768 | 0x7ffffefc90 | stack |
| 200 | 2263 | 0x7ffffefc68 | stack |
| 300 | 3508 | 0x7ffffeec08 | stack (deep) |
| 400 | 3993 | 0x490430 | inside `main_arena` (malloc bss) |
| 500 | 4293 | 0x490750 | bss |
| 600 | 5778 | 0x7ffffeeaf0 | stack |
| 700 | 7212 | 0x48ee40 | `_dl_vdso_gettimeofday` |
| 800 | 8699 | 0x7ffffefc30 | stack |
| 900 | 10739 | 0x498f00 | bss (beyond buf) |
| 1000 | 12050 | 0x7ffffefcd0 | stack |
| **1005** | **12097** | **0x7ffffefbe8** | **stack — last pre-loop store** |
| **1006** | **12108** | **0x491990** | **BUF buf[0] — K\*** |
| 1007 | 12227 | 0x491998 | BUF buf[1] |
| 1008 | 12423 | 0x4919a0 | BUF buf[2] |
| 1009 | 12643 | 0x4919a8 | BUF buf[3] |
| 1010 | 12776 | 0x4919b0 | BUF buf[4] |
| 1100 | 18986 | 0x491c80 | BUF buf[94] (mid-loop spot check) |
| 1200 | 21576 | 0x7ffffef430 | stack (post-loop) |
| 1300 | 22696 | 0x7ffffef3b8 | stack |
| 1400 | 24046 | 0x7ffffef9e8 | stack |

The loop window for SQ01 is therefore ordinals 1006..1133 (buf[0..127],
`0x491990+8i`), bracketed by K=1005 (stack, before) and K=1100 (buf[94]) /
K=1200 (stack, after).

### 3.3 SQ03 census (its own stream)

| K | store_seq | vaddr | record verdict |
|---|---|---|---|
| 1006 | 12070 | 0x7ffffefce0 | LIFECYCLE_ONLY |
| 1007 | 12096 | 0x7ffffefbe0 | CHAIN_VISIBILITY_MOVED (stack store, reload-bound — honest, not a workload lane) |
| 1008 | 12097 | 0x7ffffefbe8 | LIFECYCLE_ONLY |
| **1009** | **12108** | **0x491990** | **BUF — K\***, CHAIN_VISIBILITY_MOVED |
| 1010 | 12227 | 0x491998 | BUF, CHAIN_VISIBILITY_MOVED |
| 1011 | 12423 | 0x4919a0 | BUF, CHAIN_VISIBILITY_MOVED |
| 1012 | 12643 | 0x4919a8 | BUF, CHAIN_VISIBILITY_MOVED |
| 1013 | 12776 | 0x4919b0 | BUF, CHAIN_VISIBILITY_MOVED |

### 3.4 SP05 census (its own stream)

| K | store_seq | vaddr | record verdict |
|---|---|---|---|
| 939 | 12097 | (crashed probe; seq cross-binds to 0x7ffffefbe8) | NO_RECORD — see §4 |
| **940** | **12108** | **0x491990** | **BUF — K\***, RELOAD_UNVERIFIABLE (reload bound; store-side hash null — §5) |
| 941 | 12227 | 0x491998 | BUF |
| 942 | 12423 | 0x4919a0 | BUF |
| 943 | 12643 | 0x4919a8 | BUF |
| 944 | 12776 | 0x4919b0 | BUF |
| 1006–1015 | 17054–17675 | 0x491ba0..e8 | BUF buf[66..75] (mid-loop spot check; 1006−940 = 66 ✓) |

## 4. Census artifacts and honest notes

1. **K=40/41 (SQ01) produced no sq01 record**: those two ordinals select
   `store->load_forward` matches, not store writes — the base forwarding path
   shares the SAME F0 `lsuTrigger` (`CHAOSLSQFwd.cc:346-351` calls
   `onAttempt()/onEligible()` before the SQ01 path at `:941-947`), so the
   SQ01 ordinal counts a merged store-write + forwarding-match stream. The
   probes honestly recorded `injection_count=0` for SQ01 (`NO_RECORD` in the
   census); their logs show the forwarding bit-flip site. The merged-stream
   fact is recorded here because it means a literal "ordinal 1006" is NOT
   interchangeable across models.
2. **K=15 and K=1005 (SQ01) probe runs crashed** (gem5 exit −6, SIGABRT): the
   corrupted startup stack byte fed a faulting path mid-run. Census artifacts —
   the selected-store address (the census datum) is still recorded in each
   probe's own trace before the crash point.
3. **SP05 K=939 crashed**: the premature completion of store_seq 12097
   (0x7ffffefbe8) aborts gem5. The store's address is cross-bound from the
   SQ01 census probe of the identical `store_seq` (12097 → 0x7ffffefbe8); the
   crash is itself the boundary datum (a non-buf store — the workload never
   touches that lane again).
4. **Probe hygiene:** every probe outdir is a census artifact under `/tmp`
   (tmpfs scratch); none was graded, none was re-run for outcome, their
   oracles were ignored per the audit §2.2 rule. The graded pilots are the 18
   `SUPP-*-R0xB/C01B` runs under `pilots_v3_2_12/`.

## 5. Pilots executed with the re-selected ordinals (summary; full records in the CSV)

All 18 runs used the frozen binary (SHA above, uniform across manifests), the
absolute workload path, the ORIGINAL per-context seeds (all 15 match the
RUNBOOK §1 table — verified), `--context-index` 1..5 for R01B..R05B, context 1
+ `--probability 0.0` for each C01B, and ordinals per model: SQ01 1006..1010,
SQ03 1009..1013, SP05 940..944 (C01B carries its model's K\* bookkeeping-only;
no control fired — `injection_count=0`, `control_valid=true` for all three).

| model | fault runs | selected vaddr | reload consumer | record verdict (model rules) | run terminal | closure-tool FinalClassification |
|---|---|---|---|---|---|---|
| SQ01 | R01B..R05B | 0x491990..b0 (buf[0..4]) | **yes** — `reload_seq` 12110..12778, `mem_write_hash == reload_data_hash == consumer_hash` (all three hops hash-equal per context) | **COMPLETE_CHAIN ×5** | SDC/ORACLE_FAIL ×5, accepted ×5 | LIFECYCLE_ONLY ×5 (MissingCodes=[]) |
| SQ03 | R01B..R05B | 0x491990..b0 (buf[0..4]) | **yes** — `reload_seq` 12110..12778, valid `reload_data_hash` | **CHAIN_VISIBILITY_MOVED ×5** (drain_tick < commit_tick by ~770 ticks, `visible_before_commit=1`) | MASKED/STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS ×5, accepted ×5 | LIFECYCLE_ONLY ×5 (MissingCodes=[]) |
| SP05 | R01B..R05B | 0x491990..b0 (buf[0..4]) | **yes** — `reload_seq` 12110..12778; `reload_data_hash = a8c7f832281a39c5` (the stale zero word the reload read after the skipped write) | **RELOAD_UNVERIFIABLE ×5** (`store_data_fnv=null` — unwired, so data_correct stays unknown; write_skipped=1, drain_tick=0) | SDC/ORACLE_FAIL ×5, accepted ×5 | LIFECYCLE_ONLY ×5 (MissingCodes=[NO_EARLY_ANOMALY_EVENT]) |
| all three | C01B ×3 | — | — | — | UNRESOLVED/NO_INJECTION_EVENT, oracle PASS, `control_valid=true` | UNRESOLVED (valid control) |

Why the frozen closure tool still grades the fault runs LIFECYCLE_ONLY even
with SDC terminals and hash-equal consumer evidence: its `FinalClassification`
follows `FaultEffectPropagationCoverage`, and the trace converter's generic
`value_divergence` analysis reports `value_divergence_count=0`
(`TRIGGERED_NO_DIVERGENCE`) for these chains — it does not bind the
model-record hops (memory_response → register_writeback → consumer_commit) into
its generic divergence list, so rule 4 ("internal-only change →
LIFECYCLE_ONLY") applies. The records nonetheless carry the stronger evidence:
`FaultCausality=PROVEN`, all nine `Stages=yes` (SQ01/SQ03), and e.g. SQ01-R01B
`WritebackValueFnv == ConsumerInputFnv = f86e18335679a771`,
`ConsumerSourceLinked=true`. The propagation claims therefore rest on the
model-specific chain records (sq01_rules/sq03_rules/sp05_rules), not on the
tool's generic coverage field — recorded here as concern #1 in the report, a
follow-up patch candidate for the main agent (do NOT relabel the tool output).

Artifacts of this round (all uncommitted, per the no-commit mandate):

- `pilots_v3_2_12/SUPP-{SQ01,SQ03,SP05}-{R01B..R05B,C01B}/` — 18 run dirs
  (each with `command.txt`, `manifest.json`, `pilot_meta.json`,
  `trace_v31.jsonl`, `lsq_fwd_injections.log`, `oracle.log`, `stdout.log`,
  `stderr.log`, `prop_trace.csv.gz`, `stats.txt`).
- `audit_v3_2_12/{SQ01,SQ03,SP05}_verdict_elig_v3.2.12.json` — frozen closure
  tool `record` output per model (6 pilots each; all three invocations exit 0,
  no `BINARY_SHA_MISMATCH`).
- `audit_v3_2_12/SQ01_SQ03_SP05_Eligible_Run_Records_v3.2.12.csv` — 18 per-run
  records (ordinal used, selected vaddr, buf-range flag, reload_seq, hashes,
  ticks, terminal, oracle, acceptance).
- The original `SUPP-{SQ01,SQ03,SP05}-R01..R05`/`C01` (startup-store ordinals)
  are preserved untouched — the B-series supplements, never replaces, them.
