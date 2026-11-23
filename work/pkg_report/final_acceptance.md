# WHEN-5X3 MMU experiment — final acceptance (A01–A22)

Status counts: {"COMPLETE": 117, "N/A": 3, "BLOCKED": 0, "FAILED": 0, "PARTIAL": 0, "NOT_RUN": 0}

| Gate | Status | Evidence |
|---|---|---|
| A01 | PASS | provenance/A01_A02_A03_audit.json (03/04/05 cell hashes equal) |
| A02 | PASS | old workspace manifest recheck |
| A03 | PASS | frozen 40 IDs ∩ new 120 IDs = empty |
| A04 | PASS | 117 executed contexts; 3 N/A (M06-C05 speculative viability) |
| A05 | PASS | 120 unique rows; 40 (Model,Context) cells x 3 T |
| A06 | PASS | 40 (Model,Context) cells with N>=3 and three distinct ceil(p*N) ordinals |
| A07 | PASS | T01/T02/T03 command lines identical after normalizing run identity and eligible ordinal |
| A08 | PASS | 117 fault runs activation_count=1; 39 controls activation_count=0 |
| A09 | PASS_WITH_DECLARED_GAPS | activation-time state fields present: {"asid": 60, "dyn_inst_seq": 102, "mode": 102, "page_size_n": 102, "tlb_entry_id": 45, "tlb_instance": 45, "va": 117} |
| A10 | PASS | 117/117 actual ordinal == ceil(p*N) |
| A11 | PASS | one no-fault pre-scan/control reused by all three timings; command/config/binary hashes identical |
| A12 | PASS | 15/15 M01 activations carry TLBI+EntryID |
| A13 | PASS_WITH_DECLARED_GAP | M02/M04/M05 entry consume observed; 3 M04-C02 same-hit consumptions declared |
| A14 | PASS | 15/15 M03 activations show ASID-only mismatch |
| A15 | PASS | 12/12 M06 activations clear only the local L3 descriptor bit0 |
| A16 | PASS | 15/15 M07 activations show grant false->true |
| A17 | PASS | 15/15 M08 activations flip only the request PA by 0x1000 and keep the PFN |
| A18 | PASS | 117/117 activation shares tick and eligible ordinal with the selected eligible event |
| A19 | PASS_WITH_BOUNDARY | 12 execute-context boundaries (see JSON) |
| A20 | PASS | faulted oracle vs same-config control; M07 baseline denial is expected; terminal states computed only from observed lines/events |
| A21 | PASS | N<3/infeasible rows are explicitly N/A; no forced outcome; blocked_tasks.md |
| A22 | PASS_WITH_SCOPE | conclusions limited to the 117 observed 5x3 cells; no probability inference |

## Explicit boundaries

- M06-C05 (speculative wrong-path) is N/A: no generated workload can prove three independent speculative wrong-path cold walks squashed before the architectural fault in the frozen O3 model.
- Instruction-side contexts (M03/M04/M05 C02 and M07 C05) join MMU translation -> Execute request -> guest oracle. The frozen binary does not emit per-instruction IFU response/decode/IFU-commit events; those nodes are `NOT_EMITTED_BY_FROZEN_BINARY`.
- ACTIVATED_MASKED rows are real observed no-oracle-change outcomes (mostly C03 weak consumers). They are not forced to SDC.
