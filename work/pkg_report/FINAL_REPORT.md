# MMU When/How 5×3 experiment — final report

Round: 0202 / `gem5-fi-mmu-when5x3`  
Authoritative plan: `inputs/gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx` (sheets 16–27)  
Execution window: 2026-11-16 18:20 → 19:43 UTC (campaign phase; setup/pilot excluded)  
No Git commit, push, branch or remote operation was performed.

## 1. Result at a glance

| Item | Result |
|---|---|
| Candidate conditions | **120** (8 models × 5 contexts × 3 timings) |
| COMPLETE | **117** |
| N/A | **3** (M06-C05 speculative wrong-path, T01–T03) |
| BLOCKED / FAILED / PARTIAL / NOT_RUN | **0** |
| Controls | **39 executed** no-fault pre-scans + 1 formally N/A; one per (Model, Context), reused by all three timings |
| Fault activations | **117/117 exactly one**; controls **0** |
| Timing alignment | **117/117 actual ordinal = ceil(p·N)** |
| Eligible denominator | every non-N/A (M,C) has **N ≥ 3**; T ordinals always distinct |
| Frozen Where | M01–M08 definitions unchanged; sheets 03/04/05 byte/cell-identical to the frozen authority |
| Historical workspace | `/home/sdc/gem5-fi-mmu-impl-v2` unchanged (manifest recheck identical) |

Terminal states are computed only from observed events and the faulted guest
output compared with the same-configuration no-fault control:

| Model | SDC | ACTIVATED_MASKED | DETECTED_CONTAINED | N/A |
|---|---:|---:|---:|---:|
| M01 | 8 | 7 | 0 | 0 |
| M02 | 12 | 3 | 0 | 0 |
| M03 | 6 | 9 | 0 | 0 |
| M04 | 12 | 3 | 0 | 0 |
| M05 | 12 | 3 | 0 | 0 |
| M06 | 0 | 0 | 12 | 3 |
| M07 | 13 | 2 | 0 | 0 |
| M08 | 11 | 4 | 0 | 0 |
| **Total** | **74** | **31** | **12** | **3** |

`ACTIVATED_MASKED` is a real observed result (the fault activated exactly once
but the faulted oracle line equals the no-fault control), mostly C03 weak
consumers. It is not a relabelled SDC, and no outcome was forced.

## 2. What was actually built

1. **Independent workspace** — source, configs, workloads, tools, frozen
   authority, kernel, disk template and checkpoint were copied into
   `/home/sdc/gem5-fi-mmu-when5x3`. The old workspace was only read.
2. **gem5 timing instrumentation** — added `--mmu_prescan` and
   per-event eligible-event emission; extended the 1-based
   `mmuEligibleEventIndex` gate to M01 (matching maintenance epoch) and M02
   (qualifying refill), which previously had no ordinal selector. A
   `MMU_ELIGIBLE_SUMMARY` census is written to stdout and to
   `prop_evt.txt.gz`.
3. **New contexts/episodes** — C03 weak-consumer variants implemented for
   M01–M08 (dead load / dead store with no oracle dependency); C01/C02/C04/C05
   map to the frozen R01/R05/R04/R03 semantics. Each guest script creates
   three independent episodes (W9 repeats its remap epoch in one ASID; W10/
   W11/W13/W14 run three sequential guest processes).
4. **Runtime** — workloads were linked against the guest image's own glibc
   2.31 (`/lib/aarch64-linux-gnu/libc-2.31.so`), reducing each embedded
   payload from ~600 KB to ~5 KB; W10 page count is 1024, preserving the
   PFN-XOR-1 property while removing the 4096-page overhead.
5. **Campaign driver** — `campaign/when5x3_runner.py`: resumable queue keyed
   by SampleRunID, one ControlID per (Model,Context), ceil(p·N) timing,
   per-run manifest and raw trace, fault/control oracle comparison.
6. **Analysis/acceptance** — `campaign/finalize.py`,
   `campaign/acceptance.py`, `campaign/export_evidence.py`.

## 3. Timing map (N and selected ordinals)

Full mapping is in `analysis/timing_map.csv`; the eligible-event stream for
every control is in `analysis/eligible_events/<ControlID>.csv`.

Representative N values (same for the three timings of a cell):

| Cell | N | T01 | T02 | T03 |
|---|---:|---:|---:|---:|
| M01 C01–C05 | 4 | 1 | 2 | 4 |
| M02 C01–C05 | 3 | 1 | 2 | 3 |
| M03 C01–C05 | 3 | 1 | 2 | 3 |
| M04 C01/C02/C04/C05 | 20005–20009 | 2001 | 10003 | ~18006 |
| M04 C03 | 12 | 2 | 6 | 11 |
| M05 C01–C05 | 3 | 1 | 2 | 3 |
| M06 C01/C03/C04 | 3 | 1 | 2 | 3 |
| M06 C02 | 5 | 1 | 3 | 5 |
| M07 C01/C03/C04/C05 | 3 | 1 | 2 | 3 |
| M07 C02 | 6 | 1 | 3 | 6 |
| M08 C01/C02/C03/C05 | 3 | 1 | 2 | 3 |
| M08 C04 | 6 | 1 | 3 | 6 |
| M06 C05 | — | N/A | N/A | N/A |

All 120 rows, their planned and actual ordinals, selected event IDs, status
and terminal state are in `experiment_status.csv` and
`analysis/per_condition.json`.

## 4. Evidence chain per fault

Every COMPLETE run has:

- `runs/W5X3/<SampleRunID>/Trace/prop_evt.txt.gz` (raw PROP-EVT stream),
- `Run_Log/board.terminal`, `Run_Log/gem5_stdout.log`,
  `Run_Log/command.txt`, `Run_Log/stats.txt`,
- `manifest.json` with gem5/rcS/disk/trace hashes, eligible census, selected
  ordinal, activation count and the observed event-kind census.

`analysis/propagation_chains.csv` records the first observed event for
`Activation → Mutation → Translation → Request → Response → Consumer →
Commit/Squash` per sample. Stages that the frozen binary does not emit are
left empty rather than invented. `analysis/fault_control_compare.csv` records
the faulted vs control oracle-line comparison.

Model-specific acceptance witnesses actually present in the activation
events:

- M01: `retained_entry_id`, `first_tlbi_id`, exact VA/ASID key; `tlbi_match`
  and `tlbi_suppressed` in the trace.
- M02: `old_pfn`, `new_pfn`, descriptor/PTE proof; persistent entry consume.
- M03: `candidate_asid ≠ asid`, same VA/VMID/regime/security key.
- M04: resident entry ID/generation and substituted PFN; same-hit or later
  reuse consume.
- M05: L2 partial next-table base change and decoy table evidence.
- M06: local descriptor `0b11 → 0b10`, PTE address, memory-PTE unchanged;
  `fault_state_consumed` + `fault_result_propagated`.
- M07: `permission_before=false → permission_after=true`, PA/PFN unchanged.
- M08: request PA XOR 0x1000, `old_pfn == new_pfn`, TLB entry unchanged.

## 5. Acceptance (A01–A22)

`final_acceptance.md` and `acceptance.json` contain the full table. Summary:

- **PASS**: A01, A02, A03, A04, A05, A06, A07, A08, A10, A11, A12, A14,
  A15, A16, A17, A18, A20, A21
- **PASS with declared boundary/gap**: A09 (only fields the frozen binary
  emits are recorded; queue/speculation counters are explicitly N/A),
  A13 (M04-C02 ITLB activation entry is consumed by the same hit; no later
  reuse edge exists), A19 (execute contexts have MMU Execute-request → guest
  oracle; IFU response/decode/commit is `NOT_EMITTED_BY_FROZEN_BINARY`),
  A22 (conclusions limited to the 117 observed cells; no probability claim).

A01 note: sheets **03/04/05** are identical to the frozen authority. Some
archive/status sheets (00, 07, 09, 11–13) differ from the older freeze copy
because the uploaded authoritative workbook is a later revision; this is
recorded per sheet in `provenance/A01_A02_A03_audit.json`.

## 6. Honest limitations

1. **M06-C05 is N/A.** The plan itself marks it
   `PILOT_FEASIBILITY_OR_N_A`: it requires a deterministic wrong-path cold walk
   that is squashed before the architectural fault. The frozen W10 dispatch
   has no workload-controlled mispredicted cold walk, and constructing one
   would change the Context workload/Where semantics. It was not run.
2. **Instruction-side boundary.** M03/M04/M05 C02 and M07 C05 join MMU
   translation → Execute request → guest oracle. The frozen binary emits no
   per-instruction IFU response/decode/commit, so end-to-end frontend
   propagation is not claimed.
3. **`ACTIVATED_MASKED` rows** are genuine no-oracle-change observations,
   not forced success. In particular, M01 T03 (the last maintenance epoch) and
   several C03 weak-consumer cells show activation without a software-visible
   value change.
4. **Persistent models** (M02/M04/M05) keep their original lifetime; the
   fault-run eligible census can stop at activation while the Control N
   remains the denominator. Timing is proven by the selected ordinal and
   event ID, not by a post-activation count.
5. **Determinism scope.** The runs are deterministic for the selected
   workload/context/seed (`N/A_DETERMINISTIC`); they are not a distribution
   over all possible microarchitectural timings.

## 7. Reproduce

```bash
cd /home/sdc/gem5-fi-mmu-when5x3
# frozen checkpoint + kernel + disk template are already staged
./resume.sh                 # re-runs only missing manifests, then finalizes
JOBS=24 ./resume.sh         # higher concurrency
```

`resume.sh` keeps every completed `runs/W5X3/<ID>/manifest.json` as an
idempotency marker and never overwrites a completed run. Raw data is under
`runs/W5X3/`; analysis under `analysis/`; provenance under `provenance/`.
