# MissingEvidenceMatrix v3.2.12 — per-model missing-evidence matrix (Task 6)

**Artifact:** `audit_v3_2_12/MissingEvidenceMatrix.csv` (194 rows, the ten brief-mandated
columns: `ModelID, PilotID, MissingStage, MissingEvent, MissingCausalEdge, RootCause,
RequiredHook, RequiredWorkloadChange, RequiredRunCount, ExpectedEvidence` — no blank cell).
**Tool:** `tools/lsu_12model_closure.py missing` (deterministic; every verdict is computed
from the raw per-pilot artifacts, reusing `tools.lsu_propagation_audit.audit_pilot`; no
status matrix or Excel cell overrides it).
**Population:** 92 pilot records — 78 historical pilot directories under
`pilots_v3_2_1`–`pilots_v3_2_10` plus the 14 v3.2.12 Task 5 SUPP raw-oracle pilots under
`pilots_v3_2_12/SUPP-*`. Pilot dirs without a 12-model id (three `REPLAY-*`) are skipped
loudly. Every pilot dir of a 12-model closure model contributes one row per missing item;
a model with no pilot at all contributes one missing-pilot-set row.

## 1. How a row is produced

For every record, `audit_pilot`'s missing codes map to a frozen row spec (`RootCause`,
`RequiredHook`, `RequiredWorkloadChange`, `RequiredRunCount`, `ExpectedEvidence`). Two
v3.2.12 additions:

- **`ORACLE_FILE_MISSING` rows close against the frozen context's real raw-oracle
  availability**, in a fixed standard-derived precedence (never per-model hand-routing):
  1. a Task 5 `SUPP-<MODEL>-<Rxx>` raw-oracle run of the same `(ModelID, Seed)` frozen
     context remediates the row — `RequiredRunCount=0`, the SUPP `oracle.log` named in
     `ExpectedEvidence` (it corroborates and never replaces the original verdict; a
     different binary, the two binaries' verdicts are never merged);
  2. another original vintage of the same context whose raw `oracle.log` parsed supplies
     it in-repo (`RequiredRunCount=0`);
  3. the pilot's own `stdout.log` raw checksum line supplies it in-repo (the raw artifact
     the v3.2.11 audit read for FW05/SQ01/SQ03; the audit tool itself parses only
     `oracle.log`);
  4. with no causally attributable consumer, no oracle outcome can adjudicate the verdict
     (a passing oracle never relabels a terminal and a failing oracle is not SDC without
     a consumer — standard §1.5/§1.7), so the row is **decision-moot**:
     `RequiredRunCount=0`, the decision-relevant stage gaps named;
  5. only otherwise does the frozen open row stand (`RequiredRunCount=1`: a SUPP run
     under the original seed and context is what closes it).
- **A model with no pilot at all** (SP05, RP01) carries its missing pilot set as an
  explicit `MissingStage=PILOT` row (`RequiredRunCount=5` — one run per frozen context
  R01–R05, plan Tasks 13–15), never a silent "nothing to report" zero.

A determinism control's zero-injection absence stays `RequiredRunCount=0` by design, and
a control never supplies another pilot's raw oracle (its golden-checksum artifact is not
the fault run's). No row is ever silently omitted: the three DA04 rows that no SUPP run
covers are kept as decision-moot rows, and each pilot's `ORACLE_FILE_MISSING` code stays
in its own `MissingEvidence` record field (the closure-matrix union of Task 16 keeps it).

## 2. Row counts per model (real generated output)

```
total rows: 194
per-model row counts: {'A01': 12, 'A03': 24, 'FW02': 13, 'SQ01': 35, 'DA04': 18,
 'LP01': 11, 'MD04': 34, 'FW05': 20, 'SQ03': 15, 'LQ04': 10, 'SP05': 1, 'RP01': 1}
```

| Model | Rows | Open rows (≥1 run) | Closed rows (0 runs) | Required runs (sum) |
|---|---|---|---|---|
| A01 | 12 | 11 | 1 | 11 |
| A03 | 24 | 19 | 5 | 19 |
| FW02 | 13 | 9 | 4 | 9 |
| SQ01 | 35 | 30 | 5 | 30 |
| DA04 | 18 | 9 | 9 | 9 |
| LP01 | 11 | 0 | 11 | 0 |
| MD04 | 34 | 29 | 5 | 29 |
| FW05 | 20 | 15 | 5 | 15 |
| SQ03 | 15 | 15 | 0 | 15 |
| SP05 | 1 | 1 | 0 | 5 |
| LQ04 | 10 | 5 | 5 | 5 |
| RP01 | 1 | 1 | 0 | 5 |

Row categories across the matrix: 117 open-gap rows (a supplementary/extended run each),
24 SUPP-remediated, 8 same-context-vintage-supplied, 1 stdout-supplied, 12 decision-moot,
30 determinism-control zero-injection rows, 2 missing-pilot-set rows.

- **LP01 is the first fully closed model**: all 11 of its rows are SUPP-remediated
  raw-oracle rows with `RequiredRunCount=0` — the v3.2.11 raw-oracle gap over
  `pilots_v3_2_5`/`pilots_v3_2_6` R01–R05 (plus the same-context `SMOKE_LP01-R01_final_binary`)
  is entirely remediated by `SUPP-LP01-R01..R05`; zero further runs required.
- **LQ04** contributes rows only from its five by-design `LQ04-CONTROL` replications
  (zero-injection rows closed at 0, plus their unresolvable-terminal rows); the five fault
  pilots `LQ04-R01..R05` contribute **no missing item at all**. The tool-computed LQ04
  verdict is used as-is (Task 4): all five grade
  `FinalClassification=COMPLETE_CAUSAL_CHAIN` with `ObservedTerminal=MASKED` and
  `MaskingMechanism=RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE` (standard §6 exception E1).
- **SP05 / RP01** have no committed pilot directories (the v3.2.9 SP05 runs exist only as
  `evidence_v3_2_9` extracted evidence rows; RP01 is unimplemented), so each carries its
  missing-pilot-set row — this is why both models appear with exactly one row.

## 3. The DA04/LP01/MD04/FW05 raw-oracle closure (the Task 5 follow-up)

The v3.2.11 gap — verified chains whose raw `oracle.log` never existed in the historical
dirs — is closed: **zero unresolved `ORACLE_FILE_MISSING` rows** remain for these four
models. The 30 `MissingStage=ORACLE` rows they contribute are all at `RequiredRunCount=0`:

```
DA04: ORACLE rows=9 unresolved=0 categories={'decision-moot': 3, 'SUPP-remediated': 6}
LP01: ORACLE rows=11 unresolved=0 categories={'SUPP-remediated': 11}
MD04: ORACLE rows=5 unresolved=0 categories={'vintage-supplied': 2, 'SUPP-remediated': 3}
FW05: ORACLE rows=5 unresolved=0 categories={'stdout-supplied': 1, 'SUPP-remediated': 4}
```

- **SUPP-remediated (24 rows):** DA04-R04/R05 in all three vintages (v3_2_4/v3_2_5/v3_2_6,
  same Excel seed per context), LP01-R01..R05 in both vintages plus the same-context smoke
  run, MD04-R02/R03/R05 (v3_2_6), FW05-R02..R05 (v3_2_7). Each names its supplying SUPP
  pilot, e.g. `ExpectedEvidence = supplied:
  docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-DA04-R04/oracle.log`.
- **Vintage-supplied (MD04-R01/R04, v3_2_6):** the v3.2.7 re-run vintage
  `pilots_v3_2_7/MD04-R01`,`-R04` is the same frozen context (same model, seed verified
  equal, fault run with `injection_count=1`) and keeps a parseable raw `oracle.log`
  (`expected=59fc61c040618747 got=59fc61c040618747 / ORACLE_PASS`), which supplies the
  v3.2.6 dirs' missing raw oracle.
- **stdout-supplied (FW05-R01, v3_2_7):** its own `stdout.log` records the raw application
  checksum `checksum=0x67afad307642983e` — the raw artifact the v3.2.11 audit read for the
  whole FW05 family (R02–R05 are additionally SUPP-remediated).
- **Decision-moot (DA04-R01/R02/R03, v3_2_4):** no SUPP run exists for these contexts and
  no in-repo raw artifact anywhere, but the oracle outcome cannot adjudicate any of their
  verdicts — R01 is SQUASHED-terminal PARTIAL and R02/R03 are MASKED-terminal
  LIFECYCLE_ONLY, all three without a causally attributable consumer (`NO_CONSUMER_EDGE`;
  a failing oracle is not SDC without one, a passing oracle never relabels a terminal).
  The v3.2.11 supplementary plan accordingly scoped DA04 raw-oracle re-runs to the two
  complete chains only. Their decision-relevant gaps (the missing early-anomaly,
  writeback, consumer and commit events) remain in the matrix as ordinary open rows
  (9 open rows / 9 required runs for DA04), so nothing is hidden by closing the oracle
  item.

## 4. The SUPP-MD04-R05 binary-adjudication delta (recorded, never merged)

`SUPP-MD04-R05` re-ran the frozen context MD04-F6-W7-S01-R05 (seed 1008734674, ordinal 5)
under the **current** binary `e527f26af7c2…`; the original `pilots_v3_2_6/MD04-R05` ran
under binary `0de2564468fd…`. The raw-oracle corroboration — the purpose of the SUPP run —
holds exactly: both record the golden checksum `59fc61c040618747`, and the SUPP raw
`oracle.log` is `ORACLE_PASS`. The chain-scoped adjudication, however, differs between
the two runs (tool output, `build_pilot_record`):

| Run | Binary | ObservedTerminal | TerminalReason | FinalClassification | Oracle |
|---|---|---|---|---|---|
| MD04-R05 (original, v3_2_6) | `0de2564468fd…` | MASKED | TARGET_COMMITTED_DATA_VALUE_PRESENT | VERIFIED_SINGLE_CONTEXT | MISSING (raw absent; meta-recorded PASS) |
| SUPP-MD04-R05 (v3_2.12) | `e527f26af7c2…` | SQUASHED | TARGET_SQUASHED_NO_COMMIT | PARTIAL | PASS (raw `expected=… got=59fc61c040618747`) |

The SUPP chain this time carries **no early-anomaly, no writeback, no consumer and no
commit event** (`missing=NO_EARLY_ANOMALY_EVENT;NO_INTERMEDIATE_PROPAGATION_EVENT;
NO_REGISTER_WRITEBACK_EVENT;NO_CONSUMER_EDGE;NO_COMMIT_EVENT`), so under the current
binary and the frozen `terminal_rules` the target never commits and the chain adjudicates
SQUASHED instead of the original MASKED. This is an **adjudication-time difference between
binaries/rules generations on the same frozen context**, recorded as observed:

- The raw-oracle corroboration (the SUPP run's purpose) is unaffected and passes.
- The original verdict is **never replaced or merged** — the matrix's SUPP-remediated
  MD04-R05 ORACLE row names `SUPP-MD04-R05` as corroboration only, and the SUPP pilot's
  own stage gaps appear as their own rows under `PilotID=SUPP-MD04-R05`
  (e.g. `MissingStage=EARLY_ANOMALY`, `RequiredRunCount=1`).
- The same-binary discipline holds everywhere: verdicts are keyed per `BinarySHA256` and
  the two runs above are two different binaries' observations of one context. The
  Task 16 closure matrix must keep them split (its `_closure_rows` already groups
  per binary and renames mixed rows `MODEL@<sha8>`).

## 5. Other models' oracle rows (context)

- **A01:** R01/R02/R04/R05 (v3_2_1) keep **open** rows (`RequiredRunCount=1`) — their
  chains have verified consumers, so the raw oracle genuinely adjudicates the verdict;
  the plan's Task 7 re-runs supply it. A01-R03 (v3_2_1) is vintage-supplied by
  `pilots_v3_2_2/A01-R03`'s parsed raw `oracle.log` (same context). `pilots_v3_2_2/A01-R01`
  keeps its frozen `ORACLE_MALFORMED` open row (the artifact exists but does not parse).
- **A03:** all five v3_2_1 pilots are decision-moot (crashed runs without consumers — the
  raw oracle cannot adjudicate a crash attribution); `pilots_v3_2_2/A03-R01` keeps its
  `ORACLE_MALFORMED` row.
- **FW02:** R04 (v3_2_1, the complete pair) keeps an **open** row; R01/R05 in both
  vintages are decision-moot (no consumer edge).
- **SQ01:** all five v3_2_4 ORACLE rows are vintage-supplied by the same-context v3_2_3
  vintage's raw `oracle.log` (seed-verified fault runs).
- **SQ03 / LQ04 fault pilots:** no oracle rows at all (raw artifacts present).

## 6. Verification (real commands, real output)

Generation (the plan's Step 1 command, 11 roots):

```
$ python3 tools/lsu_12model_closure.py missing --pilots-root …(11 roots)… \
    --out docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/MissingEvidenceMatrix.csv
missing-matrix rows written to …/MissingEvidenceMatrix.csv (records=92)
```

Audit of the output (the plan's Step 2 checks, all real observed output):

```
total rows: 194
rows without RootCause: 0
rows with non-integer/negative RequiredRunCount: 0
rows with blank MissingStage: 0
blank cells anywhere: 0
A01: rows=12 -> PASS    A03: rows=24 -> PASS    FW02: rows=13 -> PASS
SQ01: rows=35 -> PASS   SQ03: rows=15 -> PASS   SP05: rows=1 -> PASS
DA04: ORACLE rows=9  unresolved=0
LP01: ORACLE rows=11 unresolved=0
MD04: ORACLE rows=5  unresolved=0
FW05: ORACLE rows=5  unresolved=0
```

- Every row has a `RootCause`; every `RequiredRunCount` is an integer ≥ 0; no
  `MissingStage` is blank; no cell anywhere in the CSV is blank (the writer raises on
  any blank cell, a bare `PASS` outside the `ApplicationOracle` enum, or a complete
  verdict over an unverified injection).
- A01/A03/FW02/SQ01/SQ03/SP05 each have ≥ 1 row.
- DA04/LP01/MD04/FW05 have **zero unresolved `ORACLE_FILE_MISSING` rows** after Task 5:
  all 30 of their ORACLE rows are SUPP-remediated, vintage/stdout-supplied, or
  decision-moot, each with the supplying evidence path named.
- `pytest tests/test_lsu_12model_closure.py -v` — **15 passed** (11 prior + 4 new tests
  pinning the SUPP same-seed remediation, the vintage/stdout/moot closing precedence,
  the `SUPP-<MODEL>-<Rxx>` name-based model inference, and the missing-pilot-set row).
- Regression: `pytest tests/test_lsu_propagation_audit.py -q` — **12 passed** (the
  shared extractor is unchanged).

## 7. Honesty notes

1. The plan's interface line estimated "55 historical pilots"; the real deterministic
   scan of the eleven roots yields **92 records (78 historical + 14 SUPP)**. The scan is
   the source of truth; nothing was hand-selected.
2. The 30 `ORACLE` rows of the four models are **kept and categorized**, not deleted: a
   reader sees exactly which rows the SUPP archive closed (24), which were already
   supplied in-repo (3), and which are decision-moot (3) — with the standard citations in
   each `RootCause`. The three decision-moot rows (DA04-R01..R03, v3_2_4) describe a real
   absence of the raw artifact; they claim only that no run is *required* for closure,
   and their pilots' `MissingEvidence` field still carries the `ORACLE_FILE_MISSING`
   code.
3. The MD04-R05 binary delta (§4) is surfaced, not reconciled: both binaries' verdicts
   stand separately and are never merged (standard §4 single-context rule and the
   per-binary keying of `BinarySHA256`).
4. No historical pilot directory was modified; the matrix reads only committed artifacts.
