# MMU Final Evidence Closure & Package Correction v2 — Plan (2026-11-12)

Workspace: `/home/sdc/gem5-fi-mmu-impl-v2` (original `/home/sdc/gem5-fi-mmu` is
read-only and is not touched). Branch `mmu-formal-freeze-2026-11-12`.
Baseline HEAD `965be468`, frozen binary
`CHAOS/gem5/build/ARM/gem5.opt` SHA256
`b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`
(source closure `60f1a876`, checkpoint `4aa1ba38`, FEAT_EPAN).

## Trigger

Independent review found that five instruction-side contexts were declared
`CONSUMED/FULL/COMPLETE` on evidence that is not actually joined:

| Context | Raw trace truth (verified this round) | Package claim |
|---|---|---|
| M03 R05 | `mmu_fault_summary consumed=0`; identity chain 253/51 -> PA 0x83543000 exists, no fetch response/commit | COMPLETE |
| M04 R05 | `consumed=0`; entry identity `itb:173:540` is reused by result 484, but not fault-tagged | COMPLETE |
| M05 R05 | `fault_entry_consume` 245 is real; partial base -> PTW -> result 255 -> request 256 exists | PARTIAL |
| M07 R04 | `required_kinds=[]`; activation 354 has no `translation_id`; result 355/request 356 are `fault_id=0` | COMPLETE |
| M07 R05 | same; activation 332 orphaned | COMPLETE |

Also stale: Excel M07 R04 TargetInstruction/OracleMethod (store text), Excel
M02 R02 PFN (`0x83480->0x83481`), Golden Control Report sentence
(`0x834b6`), and the v1 ZIP does not contain the authoritative Excel.

## Frozen decisions (unchanged)

- M01–M08, 40 SampleRunIDs, 5 contexts per model, no add/remove/renumber.
- Seed literal `N/A_DETERMINISTIC` for all 40; no numeric/alternate seed.
- M07 R03 = PROT_EXEC + EL0 load; M07 R05 = valid XN + indirect-branch fetch.
- No formal SampleRunID is launched. New runs, if any, use TEST IDs only.

## Version policy (decided before edits)

- **No C++ change, no rebuild.** The frozen binary stays
  `b3eb1559...`; all 40 existing pilots/controls remain the single version.
- Reuse the existing raw traces. The missing pieces are validator joins, not
  missing emitter sites, for the five contexts:
  - M03/M04/M05 fetch requests are already emitted as
    `translation_result` + `lsu_request(mode=Execute)` with real entry identity
    and PA.
  - M07 R04/R05 fetch requests exist on the same `translation_id` as the
    `permission_eval` that was inverted; only the activation row lacks the
    `translation_id` pointer (C++ `seq==0` fetch path). The join is made by
    same-cycle + same-VA + same-mode + same-transaction key match, verified
    against `mmu.cc:742-791`; it is never inferred from event order alone.
  - No `fetch_response` / `instruction_decode` / per-instruction `commit` is
    emitted for a synthetic IFU transaction. Execution is proven by the guest
    oracle marker tied to the exact fetched PA/code page. This documented
    instrumentation boundary is reported, not papered over.
- If the researcher later requires microarchitectural decode/commit events for
  the synthetic IFU identity, that is a new C++ hook + rebuild + re-run of all
  40 pilots/controls (out of scope this round).

## Units (one commit per unit; verify each before commit)

- [ ] U1 Plan (this file).
- [ ] U2 Authority metadata correction: Excel `07_Sample_Matrix`
      M07 R04 TargetInstruction/TargetVa/TargetEvent/OracleMethod/
      ExpectedPropagationPath and M02 R02 OracleMethod (`0x834b2->0x834b3`);
      `17_M07_Context_Change_Record` R04 rows; regenerate
      `MMU_40_Sample_Matrix.csv`, `MMU_Formal_Config.json`,
      `MMU_Formal_Config.yaml` from the corrected workbook; fix
      `10_MMU_Golden_Control_Report.md` stale `0x834b6` sentence.
      Verify: re-read all four artifacts and diff the 40 IDs/seeds.
- [x] U3 Validator strict evidence: new `tools/mmu_evidence_chain.py` with
      per-context identity joins for the five; `mmu_formal_validate.py`
      consumes it, removes the `consumed_at_activation` shortcut for
      M03/M04/M07, emits non-empty `required_kinds` for every model, and adds
      `Details.{ifu_lookup_identity_join,entry_lifetime,ptw_ifu_chain,
      permission_inversion_chain,fault_activation_basis,
      fault_consumption_basis,terminal_evidence_basis}`.
      Verify: validate all 40 runs; the five must show
      `ACTIVATED/CONSUMED/FULL/COMPLETE/SDC/FAIL` with non-empty required
      kinds and explicit identity evidence; no other run may regress.
- [x] U4 Causal slice tool: `tools/mmu_causal_slice.py` exports, for each of
      the five, the exact raw PROP-EVT lines + structured JSON
      (`entry_id/gen`, lookup id, fetch request id, dyn seq, PC, VA, PA,
      guest marker, commit/squash status or the honest absence).
      Verify: each slice JSON re-reads and every event id exists in the raw
      trace; SHA256 of the source trace recorded.
- [x] U5 Regenerate the five verdicts (and the other 35 if required by the
      strict rules) from existing traces; rerun 40/40 static preflight.
      Verify: `40/40 READY`, and the five verdicts are real.
- [ ] U6 Build `MMU_Final_Formal_Readiness_Package_v2.zip` with all 18
      required items incl. the authoritative Excel, five slices, five pilot
      manifests, five verdict JSONs, and a complete SHA256 manifest.
      Verify: unzip -l + extract and sha256sum -c.
- [ ] U7 Final report `MMU_FORMAL_READINESS = READY_FOR_RESEARCHER_APPROVAL`
      and stop (no formal run).

## Verification discipline

Every claim in the commit message / report must correspond to a command that
was actually run, with its output quoted. Never manufacture PASS by weakening
the validator. Unsatisfied identity joins are reported as blockers.
