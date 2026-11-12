# MMU Final Formal Readiness — v2 report

**MMU_FORMAL_READINESS = READY_FOR_RESEARCHER_APPROVAL**

## 1. What was fixed in the five instruction-side contexts

| Context | Fix |
|---|---|
| M03 R05 | The fault-tagged lookup hit 253/51 (ASID 236) is joined to the requester ASID 238; the same entry identity reaches translation_result 298 and `lsu_request(mode=Execute)` 299 at PA 0x83543000. The guest returns the foreign code marker 0xa5 instead of 0x5a. |
| M04 R05 | The activation mutates `itb:173:540`; a later translation_result names the same entry/generation and emits PA 0x8353c000, followed by `lsu_request(mode=Execute)` 485. The C++ entry-consumer counter is 0 for the synthetic fetch; the identity join is the real evidence. |
| M05 R05 | Faulted partial insert 230 -> `fault_entry_consume` 245 (source=230, lookup=244, entry 699/52) -> PTW 246 -> pte_read/decode -> decoy leaf -> translation_result 255 (PA 0x83544000) -> `lsu_request(mode=Execute)` 256. |
| M07 R04 | `permission_eval` 353 (Execute, deny) -> activation 354 (false->true inversion) -> translation_result 355 -> `lsu_request(mode=Execute)` 356, all on translation 7; the guest executes the XN/JIT code and returns marker 0xc7. |
| M07 R05 | `permission_eval` 331 -> activation 332 -> translation_result 333 -> `lsu_request(mode=Execute)` 334; the workload records `indirect_branch insn=br target=0x400d600180` and `executed marker=0x5a` on a valid UXN=1 leaf. |

## 2. Original traces or a new C++ hook?

Original frozen raw traces. No C++ hook was added.

## 3. Was gem5 rebuilt?

No.

## 4. Did the final binary SHA256 change?

No. `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`

## 5. Was the pilot regression widened?

No new gem5 run was launched. All 40 existing pilots and the 34 existing controls keep the same binary; the validator was re-run over the existing traces only.

## 6. Do M07 R04/R05 match the approved design?

Yes. R04 is EL0 execute from a read-only XN JIT page (marker 0xc7); R05 is a valid XN page entered by a runtime indirect branch (marker 0x5a). The Excel/JSON/YAML now describe R04 correctly.

## 7. Is the M02 R02 PFN unified?

Yes. The final control records target PFN `0x834b2` / neighbour `0x834b3`; the faulted trace event 4424 records old/new `0x834b2/0x834b3`; Excel, CSV, JSON and YAML all state `0x834b2->0x834b3`. The stale `0x834b6`/`0x83480` text is marked superseded.

## 8. Is the Excel physically in the ZIP?

Yes: `gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx` at the package root (SHA256 listed in `SHA256_MANIFEST.txt`).

## 9. Is the 40/40 preflight passing?

Yes: 40/40 READY, runtime evidence 40 PASS, seed gate 0 failures, binary/source provenance 40 PASS, trace schema OK.

## 10. Remaining blockers

None for the defined evidence. One documented instrumentation boundary remains: the frozen binary emits no per-instruction fetch-response/decode/commit row for a synthetic IFU transaction. Execution is proven by the guest oracle marker tied to the fetched PA/code page, and every causal slice states this explicitly. Adding such a row would require a new C++ hook, a rebuild and a full 40 pilot/control re-run; it is out of scope for this round.

No formal SampleRunID was launched. The next action is the researcher's approval to start the formal 40-run campaign.
