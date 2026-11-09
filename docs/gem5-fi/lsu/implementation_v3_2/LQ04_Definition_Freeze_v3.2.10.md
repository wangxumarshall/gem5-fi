# LQ04 Definition Freeze — v3.2.10

**Date:** 2026-11-09
**Authority:** Excel v3.2.4
(`docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx`,
SHA256 `25e13e88e2c5a2881567d58d8dc6e6407659c20016746e93ff31bf45f1967214` —
byte-identical to both copies shipped in the v3.2.9 package zip under
`LSU_v3.2.9_PACKAGE/D_Global/excel/` and `LSU_v3.2.9_PACKAGE/C_FW05/excel/`),
sheets `3.最终12模型矩阵` row 4, `4.源码Hook审计` row 4, and
`5.60个样本执行矩阵` rows 12–16. All cells quoted below were re-read from the
workbook on 2026-11-09 with `openpyxl` (no formula cache involved).
**Binding spec:** `docs/superpowers/specs/2026-11-08-lsu-v3.2.10-lq04-design.md`
(approved by the researcher 2026-11-08).
**Companions:** `LSU_v3.2.10_Baseline_Verification.md` (baseline hashes),
`LQ04_Source_Audit_v3.2.10.md` (file:line evidence, gate conditions).

This document is the **frozen definition** every later v3.2.10 task cites. The
implementation must not silently widen or narrow it.

---

## 1. Frozen fault definition (Excel v3.2.4, sheet `3.最终12模型矩阵` row 4)

| Field | Value (cell) |
|---|---|
| FaultModelID | `LQ04` (A4) |
| Unit | `LQ` (B4) |
| Fault class | `Load Queue Entry 生命周期错误` (C4) |
| SubTaskID | `LQ04-F0-W2-S01` (D4) |
| RunID | `LQ04-F0-W2` (E4) |
| Frequency tier | `F0` (F4) |
| Workload slot | `W2` (G4) |
| Workload | `lq_lifetime` (H4) — superseded by D3 below |
| Location | `LQEntry生命周期：executeLoad后提前失效` (I4) |
| Target fields | `LQEntry::_valid / _request` (J4) |
| Research questions | `RQ1/RQ2` (K4) |
| Propagation focus | `LQ entry→request/response→replay/commit；错误可导致响应错配或丢失` (L4) |
| Hypothesis (falsifiable) | `错误响应/丢失/错配→Replay/Commit异常或SDC` (M4) |
| FaultConfigID | `LQ04-CFG01` (S4) |
| Config target key | `目标lqIdx；entry_generation` (T4) |
| Normal value | `valid=1，request在途` (U4) |
| Fault value | `executeLoad后清valid/request；不pop、不复用` (V4) |
| Status cells | `N4` VERIFIED, `O4` NEEDS_HOOK, `P4` READY, `Q4` BLOCKED_GATE3_NOT_STARTED |
| Risk note | `响应到达前释放会破坏request/response配对；W2缺失` (R4) |

Prose form (unchanged from the spec §1):

- Location: LQEntry lifetime management, after `executeLoad` and before the
  memory response.
- Target fields: `LQEntry::_valid` and `LQEntry::_request`.
- Normal: `valid=1`, `request=<in-flight request>`.
- Fault: `valid=0`, `request=nullptr`.
- Constraints: do not pop; do not free or reuse the entry early; the entry
  stays invalid until its original commit/squash lifetime ends; one target
  Load; one injection; addresses, access size and returned data are untouched.

### 1.1 Hook-audit row (sheet `4.源码Hook审计` row 4)

Key cells: `C4` "原'提前free+重用'子模型在gem5无安全pop任意entry接口；先做提前失效，重用子模型BLOCKED";
`E4`/`Y4` sources `CHAOS/gem5/src/cpu/o3/lsq_unit.cc; lsq_unit.hh`;
`F4` structures `LSQUnit::LSQEntry; LSQUnit`; `H4` target `LQEntry::_valid / _request`;
`I4` types `bool; LSQRequest*; CircularQueue<LQEntry>`; `L4` fault
`executeLoad后清valid/request；不pop、不复用`; `M4` boundary
`commitLoad/squash/释放路径`; `N4` `F0：单次；错误entry状态保留到重用/覆盖`;
`O4` `Load（lqIdx对应条目）`; `R4` `需新增Hook；当前无LQ字段注入`; `T4` `无`;
`X4` `NEEDS_HOOK`; `AH4` cross-ref `LSU_Source_Code_Evidence_v3.md §LQ04`.

Note: this row's `G4` line ranges are stale relative to the audited tree —
see `LQ04_Source_Audit_v3.2.10.md` §2 for the corrected, re-verified ranges
(insertLoad `:371-440`, commitLoad `:859-885`, squash `:1111-1161`).

### 1.2 Naming clarification (do not confuse)

- **`LQ04`** (this round) is the Experiment-Plan 12-model-matrix ID for the
  **entry-lifetime** fault defined above.
- The original research-plan workbook
  (`docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx`, sheet
  `3.位置x模型矩阵` row 34) defines a **different** model also labeled `L04`:
  response transaction-ID/目标指令 replacement (换值, "L04-a response
  transaction ID替换；L04-b 同周期load返回目标互换"). That plan-level `L04`
  is **not** the final 12-model `LQ04` and is not implemented by this round.
- The pre-existing "LSU W5 L04" comment at `lsq.cc:451-455` refers to the old
  response-pairing concept and is only an F6 event observation — no executable
  hook (see the source audit §2).

---

## 2. Frozen sample identity (Excel v3.2.4, sheet `5.60个样本执行矩阵` rows 12–16)

All five LQ04 rows share: SubTaskID `LQ04-F0-W2-S01`, RunID `LQ04-F0-W2`,
FaultModelID `LQ04`, FaultConfigID `LQ04-CFG01`, InjectionTiming
`executeLoad后、响应到达前` (L), FaultDuration `F0单次；目标entry保持无效到commit/squash`
(M), TargetInstruction `Load（目标lqIdx）` (N), EligibleEventCondition
`目标Load已分配LQ entry并发出request` (O), WorkloadPath
`…/implementation_v3_2/workloads/lq_lifetime` (S, superseded by D3),
BinarySHA256 `7c69fd27fabf406e00b5706469fabfa082be1dbe44ee2e8f49587e6839b0156d`
(T, superseded by D3), Oracle `1624d44faff77183` (V, superseded by D3),
gem5Commit `6f98088a7144d7f6fb22d985be3023ac5658e71b` (Y), ConfigScript
`configs/se/lsu_proxy.py` (AA), FullCommand `BLOCKED: no executable hook yet`
(AB), PreflightStatus `BLOCKED_NO_HOOK` (AF), ConfigFrozen `NO` (AL),
WarmUp/ROI `NEEDS_RESEARCHER_CONFIRMATION` (W/X).

| Row | SampleRunID (A) | Seed (D) | EventOrdinal (P) |
|---|---|---|---|
| 12 | `LQ04-F0-W2-S01-R01` | `1842987246` | `1` |
| 13 | `LQ04-F0-W2-S01-R02` | `2188214204` | `2` |
| 14 | `LQ04-F0-W2-S01-R03` | `3953171871` | `3` |
| 15 | `LQ04-F0-W2-S01-R04` | `4153250964` | `4` |
| 16 | `LQ04-F0-W2-S01-R05` | `3410523942` | `5` |

ContextDifferenceRule (R, all rows): "R01-R05同一故障配置；仅动态事件/上下文不同；
工作负载必须显式构造差异，禁止假设前5个eligible自然不同" — the rule that
motivates D3's explicit-anchor workload.

**Identity freeze (D6):** all 60 SampleRunIDs/RunIDs/SubTaskIDs/Seeds across
the 12 models stay unchanged. Only LQ04's workload path/SHA/Oracle/status
cells may change (workload identity per D3; status per pilot outcomes).

---

## 3. Implementation options and the researcher's choice

Excel sheet 3 row 4 `X4` (options) and `Y4` (choice); sheet
`11.风险与待确认事项` G45 records the same ruling as
"A仅提前失效(不free)/B提前pop复用BLOCKED":

- **A: 仅提前失效（推荐，可审计）** — early invalidation only, no free,
  no pop, no reuse. **Chosen (`Y4` = A).**
- B: 提前pop并复用（需结构性修改，BLOCKED） — early pop + reuse; gem5 has no
  safe pop-arbitrary-entry interface; **BLOCKED**.
- C: 正常commitLoad释放（不是故障） — normal release; **not a fault**.

---

## 4. Gate verdict

**IMPLEMENTABLE_WITH_CONDITIONS.**

No UAF and no dangling request (source audit answers A–C); but the literal
definition (i) violates the commit invariant (`lsq_unit.cc:862`, `:890`,
`:343`) and (ii) does not produce the Excel's hypothesized response loss —
the honest expected outcome is a trace-visible invalid-entry interval plus the
load's normal correct writeback (answer D). The conditions are D1 and D2
below; the negative propagation result is governed by D1 and D5.

---

## 5. Researcher decisions D1–D6 (frozen verbatim from the approved spec §3)

1. **D1 — Response semantics:** literal field fault. Do **not** call
   `discard()` and do **not** drop the response. Expected terminal is
   `MASKED` when the target commits; record the sender-state association as
   positive evidence. Do not manufacture SDC.
2. **D2 — Commit integrity:** keep `valid=0`/`request=nullptr` for the whole
   interval; preserve the request in an opaque `LQEntry` side channel and
   restore it exactly at the commit/squash boundary, then let the normal
   `clear()` free it. Do not pop early. The only invariant sites that may
   accept the explicitly corrupted entry are the `commitLoads()` pre-loop
   check (`lsq_unit.cc:890`) and `drainSanityCheck()` (`:343`); `commitLoad()`
   restores before its own `assert(front().valid())`. No other assertion is
   relaxed.
3. **D3 — Target events:** build a new workload `lq_lifetime_ordinal` whose
   first five eligible Loads are five explicitly constructed anchors (distinct
   PC, address, data, destination register and consumer). Record its SHA256 and
   re-validate the Oracle. The original `lq_lifetime` remains archived.
4. **D4 — Ordinal semantics:** `EventOrdinal` is the 1-based ordinal of the
   eligible Load stream (eligible = Load whose LQ entry is valid and whose
   request exists at the end of `executeLoad`). No seeded-tier selection and
   no fallback to another event.
5. **D5 — Trace honesty:** record injection, entry-state change, response
   association, writeback, commit, restore/free and consumer edges. Separate
   `RecordIntegrity`, `TraceCompleteness` and `PropagationCoverage`.
   `PROPAGATION_VERIFIED=1` requires a real consumer edge; a lifecycle-only
   chain must remain `PROPAGATION_COVERAGE=LIFECYCLE_ONLY`.
6. **D6 — Identity freeze:** keep all 60 SampleRunIDs/RunIDs/SubTaskIDs/Seeds.
   Only LQ04's workload path/SHA/Oracle/status cells change.

---

## 6. Non-goals (unchanged)

- No change to the other 11 models or their 55 SampleRunIDs.
- No formal 60-run campaign.
- No new generic trace system; reuse the existing `prop_trace.csv.gz` →
  `trace_v31.jsonl` converter and add only LQ04 binding/registry entries.
- No change to Warm-up/ROI (`NEEDS_RESEARCHER_CONFIRMATION`).
- No `git reset --hard`, `git clean -fd`, or `git add -A`.

---

## 7. Freeze statement

From this commit on, any v3.2.10 task that needs the LQ04 definition, the
sample identities, the option ruling, the gate verdict or decisions D1–D6
cites **this document** (and the spec it freezes), not ad-hoc restatements.
Changes to any frozen item require an explicit researcher decision recorded
the same way.
