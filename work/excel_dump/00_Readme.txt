SHEET 00_Readme dims=A1:B27 rows=27 cols=2
R1: Item | Value
R2: Project | ARM CPU-SDC MMU/TLB fault injection and propagation feature library
R3: Version | MMU Final Design v2.0
R4: Repository HEAD | 2a8422b42dcd4f2b3f388f2dee27a237d23a9242
R5: Vendored gem5 base | 62c7bf284864b83f7308f5e14ca9c80812621c29
R6: Selected models | 8
R7: Logical injection positions | 8
R8: Workload classes | 6
R9: Proposed samples | 40
R10: Contexts | 5 different dynamic contexts per model; R01-R05 are not repeats
R11: Verified baseline | W9 and W10 only; each 3 FS boots x 5 contexts = 15/15 PASS
R12: Proposed workloads | W11-W14; no binary/pilot claimed
R13: Seed | NEEDS_AUTHORITATIVE_EXCEL; none generated
R14: SampleRunID | PROPOSED only; not authoritative/frozen
R15: Design Complete | YES — source-based specification and full listed functional-area assessment
R16: Implementation Ready | NO — hooks/refinements and W11-W14 remain
R17: Experiment Complete | NO — no formal M01-M08 injection
R18: No source mutation | No C++ Hook, no formal injection, original workspace/LSU files untouched
R19: M01 | Targets W9-observed l2_shared complete 4 KiB entry; latch spans matching TLBI operations
R20: M02 | Changes local TlbEntry refill PFN, not memory-resident PTE
R21: M05 | Changes next-table base in partial entry, not final data PFN
R22: M06 | Changes local descriptor buffer only; PTE memory unchanged
R24: CURRENT WORKBOOK NOTICE | The 00-15 source worksheets are original v2.0 archive, not live formal completion status.
R25: MMU frozen 40 | See 17_Legacy_Formal40 (FORMAL_CAMPAIGN_20261113). 40 completed; source row 14 is historical only.
R26: New When 5x3 | See 16_CURRENT_Readme and 20_When_5x3_120 for proposed additional 120 experiment conditions.
R27: Where policy | M01–M08 Source/Hook/FaultOperation remain unchanged. 0202 frozen workspace never overwritten.
