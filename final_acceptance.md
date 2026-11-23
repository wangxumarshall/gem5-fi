# WHEN-5X3 MMU experiment — final acceptance (A01–A22)

Status counts: {"COMPLETE": 117, "N/A": 3, "BLOCKED": 0, "FAILED": 0, "PARTIAL": 0, "NOT_RUN": 0}

## Terminal-state summary (granular, chain-based)

| State | Count |
|---|---|
| SDC | 74 |
| ACTIVATED_MASKED | 15 |
| PROPAGATED_BUT_SQUASHED | 9 |
| DETECTED_DELIVERED | 9 |
| ACTIVATED_UNCONSUMED | 5 |
| DETECTED_LOCALLY | 3 |
| N/A | 3 |
| SQUASHED_BEFORE_MEMORY_ACCESS | 2 |

| Gate | Status | Evidence |
|---|---|---|
| A01 | PASS | provenance/A01_A02_A03_audit.json (03/04/05 cell hashes equal) |
| A02 | PASS | old workspace manifest recheck |
| A03 | PASS | frozen 40 IDs ∩ new 120 IDs = empty |
| A04 | PASS | 117 executed contexts; 3 N/A (M06-C05) |
| A05 | PASS | 120 unique rows; 40 (Model,Context) cells x 3 T |
| A06 | PASS | 39 non-SPEC cells with N>=3 and three distinct ceil(p*N) ordinals; M06-SPEC is excluded (N=0, feasibility N/A — see A21/M06_C05_PILOT_EVIDENCE.md) |
| A07 | PASS | T01/T02/T03 command lines identical after normalizing run identity and eligible ordinal |
| A08 | PASS | 117 fault runs activation_count=1; 39 controls activation_count=0 |
| A09 | PASS_WITH_DECLARED_GAPS | activation-time state fields present: {"asid": 60, "dyn_inst_seq": 102, "mode": 102, "page_size_n": 102, "tlb_entry_id": 45, "tlb_instance": 45, "va": 117} |
| A10 | PASS | 117/117 actual ordinal == ceil(p*N) |
| A11 | PASS | one no-fault pre-scan/control reused by all three timings; command/config/binary hashes identical |
| A12 | PASS | 15/15 M01 activations carry TLBI+EntryID |
| A13 | PASS | M02/M04/M05 entry consumed via chain anchor or mutated-entry translation; 0 M04-C02 same-hit consumptions declared (no later reuse edge) |
| A14 | PASS | 15/15 M03 activations show ASID-only mismatch |
| A15 | PASS | 12/12 M06 activations clear only the local L3 descriptor bit0 |
| A16 | PASS | 15/15 M07 activations show grant false->true |
| A17 | PASS | 15/15 M08 activations flip only the request PA by 0x1000 and keep the PFN |
| A18 | PASS | 117/117 activation shares tick and eligible ordinal with the selected eligible event |
| A19 | PASS | execute-context chains verified on real ifu_response / ifu_decode / fault-tagged commit (Fetch-side DynInst build, not O3 Decode::tick) |
| A20 | PASS | fault vs build-matched control: gem5 build hash parity PLUS disk_sha256 / rcs_sha256 / config-kernel-bootloader-checkpoint / shared run-param parity (not build-hash-only). Fault-injection target params (mmu_m02_old_pfn, mmu_m04_decoy_pfn) are per-run calibration and excluded (recorded below). 117 completed samples, 0 build mismatch, 0 config mismatch, 0 declared injection-target diffs, 0 missing control |
| A21 | PASS | N<3/infeasible rows are explicitly N/A; no forced outcome; M06_C05_PILOT_EVIDENCE.md |
| A22 | PASS_WITH_SCOPE | conclusions limited to the 117 observed 5x3 cells; no probability inference |

## Causal-completeness (per model)

Four orthogonal dimensions: **file** (raw trace present), **edges** (every edge explicit, no UNKNOWN), **terminal** (an observed endpoint), **architecture** (every expected stage observed — no NOT_EMITTED boundary and no raw gap).  FULL = all four; PARTIAL = any deficit.

| Model | FULL | PARTIAL | partial reason (dimension) |
|---|---|---|---|
| M01 | 15 | 0 | — |
| M02 | 15 | 0 | — |
| M03 | 15 | 0 | — |
| M04 | 15 | 0 | — |
| M05 | 15 | 0 | — |
| M06 | 12 | 0 | — |
| M07 | 15 | 0 | — |
| M08 | 15 | 0 | — |
| **Total** | **117** | **0** | |

## Explicit boundaries

- M06-C05 (speculative wrong-path) is N/A — a **feasibility boundary of the frozen configuration, validated by the Pilot run**, not a global infeasibility claim.  The Pilot (self-contained load, indirect call site on a flushed ITLB cold page) did form 3 eligible M06 events, but all three are correct-path (architectural) cold-fetch walks; the frozen O3 fetch does not speculatively predict the indirect-branch target, so a non-sequential mmap'd page cannot be walked on the squashed path.  Producing a deterministic *speculative* cold walk would require a workload/context change (conditional-branch mispredict with the cold target within ±1 MB, or speculative fetch past a syscall into an adjacent cold page).
- M06-C01 is DETECTED_LOCALLY: fault_result_propagated carries exception_class=TranslationLL with exception_delivered=0 and no exception_delivery event; M06-C02/C03/C04 are DETECTED_DELIVERED (exception_delivery event + exception_delivered=1).
- Instruction-side contexts (M03/M04/M05 C02 and M07 C05) carry real IFU evidence: an `ifu_response` (Fetch::processCacheCompletion) and an `ifu_decode` (Fetch::buildInst, the Fetch-side DynInst build) bound to the same translation_id, then a fault-tagged commit/squash of the fetched line.  `ifu_decode` is NOT claimed as direct observation of the O3 `Decode::tick` stage.
- M05-C03/C04/C05 data path is fully reconstructed: partial_entry_insert -> partially-reused fault_entry_reuse -> PTW restart (ptw_start/pte_read/ptw_request/ptw_response/pte_decode/tlb_fill) -> complete tlb_entry_insert -> reuse -> memory_response -> rf_writeback -> data consumer (consumer_of=<producer dyn_inst_seq>) -> the consumer's own commit.  The producer Load's commit is never confused with the data consumer's commit.
- M07-C02-T01/T02 are SQUASHED_BEFORE_MEMORY_ACCESS (FULL, W5X3-OBS-0222): the permission grant inversion translated to NoFault and issued an LSU request; the translation response was then received by the LSQ and, because the load had already been squashed during its page walk, the request was discarded by `LSQ::SingleDataRequest::finish -> squashTranslation()` and blocked from cache.  This is now proven at runtime (not inferred from the absence of a cache_request) by the parent-chained events `translation_response_received -> squash_translation_decision(decision=discard_due_to_prior_squash, released=1) -> squash_translation_invoked -> translation_request_discarded(terminal_reason=prior_squash_before_translation_completion) -> cache_dispatch_decision(cache_dispatch_blocked_by_squash)`; see `M07_C02_T01_COMPLETE_PROPAGATION.md` / `M07_C02_T02_COMPLETE_PROPAGATION.md`.  Control (CTRL-OBS-M07-C02, same build) shows the same load get `translation_result(fault_status=Data)` with no `lsu_request`, proving the fault genuinely changed the microarch path but was consumed on a dead (squashed) instruction.  The faulted instruction did NOT deliver the SIGSEGV (`fault_status=NoFault`); the guest SIGSEGV is the architectural execute-only denial, not the faulted instruction.  PID/Episode: ep1/2/3 = pid 318/320/322 = asid 236/242/248 = observed ldrb seq 24118302/27030544/29694101.  M07-C02-T03 (original build) remains a genuine SDC.
- SDC causal terminals are verified on the multi-branch DAG: no SDC sample terminates on a squash.  Where the first consumer of a faulted state is squashed (M01/M05), the reconstruction follows the state's later committing consumers (M01 ~1000 reuses, terminal = first commit; M05 = the cross-dynamic alias consumer that commits the decoy PA).  A squash whose walk still completes (tracer's faulting_inst_squashed=0) is a replay artifact, not the terminal.
- ACTIVATED_UNCONSUMED (M01 T03) is the last maintenance epoch where the fault arms and no later access consumes the retained entry.
- PROPAGATED_BUT_SQUASHED (M03 C03/C04/C05) is a real observed outcome: the false hit reaches the LSU/cache but the consuming instruction is squashed before any architectural effect.
- ControlRunID uses the actual run-directory name (verified by ControlTraceSHA256 against sha256sum of each runs/*/CTRL*/Trace/prop_evt.txt.gz): M02 -> CTRL-M02-C0X-PFN, M04-C01/03/04/05 -> CTRL-M04-C0X-DECOY, M03-C02/M04-C02/M05-C02 -> CTRL2-*, M05-C03/04/05 -> CTRL2B-*, M07-C02-T01/T02 -> CTRL2-M07-C02 (T03 -> CTRL-M07-C02), M07-C05 -> CTRL2-M07-C05, M06-C05 -> empty (SPEC N/A).  ControlID (logical plan name) is unchanged.  Non-suffixed CTRL-M02-C0X / CTRL-M04-C0X dirs are superseded stubs whose manifests point at the -PFN/-DECOY trace (stale manifest), so they are excluded from the authoritative map.
