# LSU v3.3.3 — 60-Context Final Classification Freeze

**Freeze date:** 2026-11-12
**Final source HEAD:** `c042d55d`
**Final binary:** `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
**Config:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`

## 1. Frozen counts

| Classification | Count | Notes |
|---|---:|---|
| `COMPLETE_CAUSAL_CHAIN` | **38** | SDC; fault dataflow reached the application terminal |
| `VALID_TERMINAL_CHAIN` | **12** | MASKED with mechanism/consumer witness; valid terminal, not an SDC dataflow |
| `QUALIFIED` | **5** | SP05 R01–R05; lost-writeback mechanism complete, frozen `writeback_event` absent by construction |
| `TRACE_INCOMPLETE` | **5** | RP01 R01–R05; internal-watchdog HANG, terminal metadata complete, trace partial by construction |
| `UNRESOLVED` | **0** | — |
| **Total** | **60** | |

These counts are frozen for the formal campaign. Any later change requires a new, explicitly
authorized round; this freeze document must not be silently edited.

## 2. Restricted-context status (11)

| Model | Contexts | Frozen status | Key evidence |
|---|---|---|---|
| A03 | R02 | `COMPLETE_CAUSAL_CHAIN` (SDC) | first affected 13718 squashed; causal anchor 13772; `d48b947fc08d5a75` |
| SP05 | R01–R05 | `QUALIFIED` | real `store_commit` + `store_writeback_suppressed` (`SUPPRESSED_BEFORE_SEND`); no fabricated writeback |
| RP01 | R01–R05 | `TRACE_INCOMPLETE` | three flush nodes; `MODEL_INTERNAL_WATCHDOG`; partial trace retained |

A03-R02 **remains** `COMPLETE_CAUSAL_CHAIN`; it is not reclassified as SQUASHED.
SP05 keeps the real negative evidence `SUPPRESSED_BEFORE_SEND`; it is not a writeback event.
RP01 keeps `TRACE_INCOMPLETE`; terminal metadata completeness is not normal-execution trace
completeness.

## 3. Provenance split (49 + 11)

| Evidence group | Count | Binary |
|---|---:|---|
| Historical Pre-Formal contexts | **49** | old binary `1126e0fd…` |
| Trace-closure re-run contexts | **11** | new binary `62e1b1be…` |

The final 60-context synthesis is **not** “60 runs of one binary”. Each row records its evidence
root and binary SHA. The formal campaign will re-run all 120 tasks with `62e1b1be…` as one batch;
historical evidence remains archived and must not be mixed into the formal result set.

## 4. Frozen artifact hashes

```console
c192ff290e1279b41da0ade1e2338084a526d21901bb2254d0297d62b856533e  LSU_60Context_Causal_Propagation_Final.csv
d8b3ccb59257dafb85789d482dfee3f776628b95a2a1e5d178cda150589e99ef  LSU_60Context_Final_Readiness.csv
7acf542be5ee484b88172f9389453ebd07c83b8c0e97f53bc6102bcf203e6793  LSU_11Context_Repair_Validation.csv
```

These files are the frozen classification source. The readiness CSV is reproduced unchanged in
the delivery package; the propagation CSV is the frozen 60-context causal table.
